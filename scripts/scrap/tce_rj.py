#!/usr/bin/env python3
"""
Fetch TCE-RJ (Tribunal de Contas do Estado do Rio de Janeiro) Portal de
Dados Abertos -> Parquet -> beelink.

API: https://dados.tcerj.tc.br/api/v1 -- a real, unauthenticated FastAPI
service (OpenAPI spec at /api/v1/openapi.json, ~40 documented endpoints).

Gotcha #1: `GET /api/v1` (no trailing slash) 307-redirects to
`http://localhost/api/v1/` -- a misconfigured absolute Location header. This
previously read as "server broken" but it's just that one exact path; every
concrete endpoint (`/api/v1/<nome>`, `/api/v1/docs`, `/api/v1/openapi.json`)
works fine and returns real data.

Gotcha #2: pagination via `inicio`/`limite` query params is inconsistent
across endpoints. Some (contratos_estado, contratos_municipio, licitacoes)
paginate correctly. Others (convenios_estado, penalidades_ressarcimento_estado,
gastos_com_pessoal) silently ignore `limite` and always return their full
table in one shot, even when limite=1. The generic paginator below handles
both: if a page returns more rows than requested, that's the whole dataset
in one response -- stop immediately (calling again would just re-fetch the
same full set and duplicate rows).

Endpoints also come in two response shapes:
  - plain JSON list                    (contratos_estado, convenios_estado, ...)
  - {"<Key>": [...], "Count": n}       (contratos_municipio, licitacoes, ...)
    where "Count" is just len() of that page, not a real total.

Gotcha #3: some pages 422 with a Pydantic validation error -- the server's own
response model rejects a `None` value in a field it declared non-nullable
(e.g. `CNPJCPFContratado`), so the *entire page* fails to serialize even
though the underlying row is real data. `jsonfull=true` bypasses the strict
model but also silently ignores `inicio`/`limite` (dumps the whole table --
far too slow over this connection). Instead: on a 422, parse the bad row's
index out of the error body's `loc` and recursively split the request range
around it, so only that one malformed row is skipped and everything else in
the page is kept.

Gotcha #4: pagination is not stable -- offset windows are not computed over a
deterministic ORDER BY, so consecutive pages can overlap and the same row can
come back more than once (observed ~35% duplicate rate on `licitacoes`
across a full paginated pull). `fetch_endpoint` dedups on exact-line equality
before returning; large-scale re-runs should keep that in place rather than
trust raw `inicio`/`limite` pagination to be a clean partition.

Usage:
    python3 scripts/scrap/tce_rj.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_tce_rj/dados"
BASE_URL = "https://dados.tcerj.tc.br/api/v1"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/"
    "c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/tce_rj"
)
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
LIMITE = 1000

# (endpoint name, dict list-key or None for plain-list responses)
TABLES = [
    ("contratos_estado", None),
    ("contratos_municipio", "Contratos"),
    ("licitacoes", "Licitacoes"),
    ("convenios_estado", None),
    ("penalidades_ressarcimento_estado", None),
    ("gastos_com_pessoal", "Gastos"),
]


class Validation422(Exception):
    def __init__(self, detail):
        self.detail = detail


def _fetch_page(endpoint: str, inicio: int, limite: int, retries: int = 3):
    url = f"{BASE_URL}/{endpoint}?inicio={inicio}&limite={limite}"
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            if e.code == 422:
                raise Validation422(json.loads(e.read()))
            print(f"  retry {attempt + 1}/{retries} after HTTP {e.code}: {e}")
            time.sleep(2 * (attempt + 1))
        except Exception as e:
            print(f"  retry {attempt + 1}/{retries} after error: {e}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url} after {retries} retries")


def _bad_index_from_detail(detail):
    try:
        for item in detail.get("detail", []):
            for part in item.get("loc", []):
                if isinstance(part, int):
                    return part
    except Exception:
        pass
    return None


def fetch_range(endpoint: str, list_key, inicio: int, limite: int):
    """Fetch up to `limite` rows starting at `inicio`. If the server 422s on
    a single malformed row within the range, split around it (recursively)
    so only that row is dropped and the rest of the page is kept.

    Returns (rows, reached_end) -- `reached_end` is True only when a real
    (non-error) response came back shorter than requested, i.e. the
    underlying dataset actually ran out at that position. It must NOT be set
    just because we skipped a bad row -- that would truncate the fetch early
    even though more valid data follows at the next offset."""
    if limite <= 0:
        return [], False
    try:
        data = _fetch_page(endpoint, inicio, limite)
    except Validation422 as e:
        bad_idx = _bad_index_from_detail(e.detail)
        if bad_idx is None or limite <= 1:
            print(f"  {endpoint}: skipping unrecoverable bad row at inicio={inicio} limite={limite}: {e.detail}")
            return [], False
        print(f"  {endpoint}: 422 at inicio={inicio} limite={limite}, bad row at relative idx={bad_idx} -- splitting around it")
        before_rows, before_end = fetch_range(endpoint, list_key, inicio, bad_idx)
        after_rows, after_end = fetch_range(endpoint, list_key, inicio + bad_idx + 1, limite - bad_idx - 1)
        return before_rows + after_rows, (before_end or after_end)
    rows = data if list_key is None else data.get(list_key, [])
    return rows, len(rows) < limite


def fetch_endpoint(endpoint: str, list_key):
    """Paginate through `endpoint`, checkpointing every page to a local
    JSONL file so a process that gets killed mid-run (timeout, etc.) can
    resume from where it left off on the next invocation instead of
    re-fetching from scratch."""
    state_path = TEMP_DIR / f"{endpoint}.checkpoint.json"
    data_path = TEMP_DIR / f"{endpoint}.checkpoint.jsonl"

    inicio = 0
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if state.get("done"):
            print(f"  {endpoint}: checkpoint already marked done, loading from disk")
            with open(data_path) as f:
                return [json.loads(line) for line in f]
        inicio = state.get("next_inicio", 0)
        print(f"  {endpoint}: resuming from inicio={inicio}")

    with open(data_path, "a") as f:
        while True:
            rows, reached_end = fetch_range(endpoint, list_key, inicio, LIMITE)
            n = len(rows)
            print(f"  {endpoint} inicio={inicio}: got {n} rows" + (" (end of data)" if reached_end else ""))
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
            f.flush()

            done = n > LIMITE or reached_end
            if n > LIMITE:
                print(f"  {endpoint}: server ignored limite ({n} > {LIMITE}) -- treating as complete, stopping")
            state_path.write_text(json.dumps({"next_inicio": inicio + LIMITE, "done": done}))
            if done:
                break
            inicio += LIMITE
            time.sleep(0.3)

    with open(data_path) as f:
        lines = f.readlines()

    # Gotcha #4: pagination is not stable -- the server doesn't apply a
    # deterministic ORDER BY before applying inicio/limite, so consecutive
    # offset windows can overlap and return the same row twice (observed:
    # ~35% duplicate rate on `licitacoes`). Dedup on exact-line equality
    # before returning; this is cheap and safe since a legitimate distinct
    # row would never serialize to an identical JSON line.
    seen = set()
    rows = []
    for line in lines:
        if line not in seen:
            seen.add(line)
            rows.append(json.loads(line))
    if len(rows) < len(lines):
        print(f"  {endpoint}: deduped {len(lines) - len(rows)} exact-duplicate rows ({len(lines)} -> {len(rows)})")
    return rows


def write_and_push(name: str, rows: list):
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not rows:
        print(f"{name}: no rows fetched, skipping")
        return 0

    table = pa.Table.from_pylist(rows)
    parquet_path = TEMP_DIR / f"{name}.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

    beelink_dir = f"{DATASET_PATH}/{name}"
    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {beelink_dir}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{beelink_dir}/",
        shell=True,
    )
    if result.returncode != 0:
        print(f"rsync failed for {name}", file=sys.stderr)
        return 0

    print(f"Pushed to {BEELINK_HOST}:{beelink_dir}/{parquet_path.name}")
    return table.num_rows


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    if sys.argv[1:2] == ["--only"]:
        only = sys.argv[2]
        tables = [(e, k) for e, k in TABLES if e == only]
        skip = set()
    else:
        tables = TABLES
        skip = set(sys.argv[1:])
        if skip:
            print(f"Skipping already-done tables: {sorted(skip)}")

    total_rows = 0
    tables_written = 0
    for endpoint, list_key in tables:
        if endpoint in skip:
            print(f"=== Skipping {endpoint} (already done) ===")
            continue
        print(f"=== Fetching {endpoint} ===")
        rows = fetch_endpoint(endpoint, list_key)
        print(f"{endpoint}: {len(rows)} total rows fetched")
        n = write_and_push(endpoint, rows)
        if n:
            total_rows += n
            tables_written += 1

    print(f"\nDone. {tables_written} tables written, {total_rows} total rows.")
    return 0 if tables_written else 1


if __name__ == "__main__":
    sys.exit(main())
