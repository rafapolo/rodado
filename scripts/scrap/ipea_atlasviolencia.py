#!/usr/bin/env python3
"""
Fetch IPEA "Atlas da Violência" indicator series -> Parquet -> beelink.

Prior research (tasks/datasets_to_scrap.md) marked this source
"blocked -> mcp-todo", claiming the site (ipea.gov.br/atlasviolencia) is a
Next.js App Router SPA with "no discoverable REST API" and that all guessed
`/api/v1/*` paths 404 -- concluding a headless browser would be required.

That claim was wrong. The rendered HTML has no `__NEXT_DATA__`/`_next/data`
JSON (true for App Router), but the client JS bundles
(`_next/static/chunks/app/page-*.js`, `app/tema/[id]/page-*.js`) reference two
real, unauthenticated backend APIs, both same-origin under
`www.ipea.gov.br` (so no WAF/Cloudflare edge in front of them):

  - `https://www.ipea.gov.br/cms/api/*`   -- Strapi v5 CMS, serves indicator
    *metadata* (series catalog, themes, units, periodicities, cross-project
    "projetos" catalog). E.g. `GET /cms/api/temas`, `GET /cms/api/series`.
    Relation filters like `filters[projetos][id][$eq]=3` are silently
    ignored by this Strapi instance (always returns the full unfiltered
    813-row series catalog shared across all IPEA micro-sites) -- so
    membership in the "Atlas da Violência" project (documentId "violencia",
    slug "atlasviolencia", numeric id 3) must be determined client-side via
    `?populate[projetos][fields][0]=slug` and filtering the response.

  - `https://www.ipea.gov.br/dados-api/*` -- a separate NestJS-style app
    serving actual indicator *values*. Confirmed working routes:
      GET /dados-api/chart/home              -- ~10 headline home-page charts
                                                 (national annual series)
      GET /dados-api/serie-chart/{serieId}   -- one series' national annual
                                                 time series (labels+data)
      GET /dados-api/series-values/{serieId}/{tipoRegiao} -- raw disaggregated
                                                 values (periodo, regiao_id,
                                                 valor) by region-type
                                                 (1=?, 2=regiões, 3=estados,
                                                 4=municípios per a front-end
                                                 label map found in the JS,
                                                 though row-count patterns
                                                 don't cleanly confirm tipo 1;
                                                 no lookup endpoint for
                                                 regiao_id -> name was found,
                                                 so that breakdown is left
                                                 for a future pass rather than
                                                 shipped with unverified
                                                 region labels)
      GET /dados-api/ultimos-valores         -- latest value per series id

This pipeline covers the ~100 series belonging to the "Atlas da Violência"
project via the safe, unambiguous path: series metadata (cms/api) + each
series' national-level annual time series (dados-api/serie-chart). Full
sub-national (estado/município) breakdown is available via
`/series-values/{id}/{tipoRegiao}` but was NOT pulled here -- it's ~90k rows
per series at the município level alone (100 series x that would be several
million rows) and the regiao_id -> name mapping could not be confirmed from
the client bundles, so shipping it now risked mislabeled data. Left as a
follow-up.

Resumable: each series' values are checkpointed to disk
(/tmp/ipea_atlasviolencia_<mac>/checkpoint.json) as soon as they're fetched,
and a series already checkpointed is skipped on the next invocation -- so a
157-series pull that can't finish in one bounded run (dados-api's sustained-
access flakiness usually prevents that) makes forward progress across
several. Chain bounded runs until "series covered overall" reaches the total:

    IPEA_DEADLINE_SECONDS=700 python3 scripts/scrap/ipea_atlasviolencia.py

Usage:
    python3 scripts/scrap/ipea_atlasviolencia.py
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_ipea_atlasviolencia"
CMS_BASE = "https://www.ipea.gov.br/cms/api"
DADOS_BASE = "https://www.ipea.gov.br/dados-api"
PROJECT_SLUG = "atlasviolencia"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
import uuid
TEMP_DIR = Path(f"/tmp/ipea_atlasviolencia_{uuid.getnode()}")


def get_json(url: str, timeout: int = 30, retries: int = 2) -> dict:
    # NOTE: `urllib.request.urlopen` against this host times out ~100% of
    # the time even with a full browser User-Agent and 1.5s+ spacing between
    # requests -- but plain `curl` with identical headers/spacing succeeds
    # reliably (confirmed with a controlled 5/5 test). Whatever's
    # discriminating (likely TLS/HTTP client fingerprinting on IPEA's edge,
    # not a simple UA or rate-limit check) singles out Python's stack
    # specifically, so shell out to curl instead of using urllib directly.
    # This host is also just generally flaky under sustained access (some
    # individual requests stall for 30s+ even via curl) -- retry a couple
    # times with a fresh connection before giving up on that URL.
    last_err = None
    for attempt in range(retries + 1):
        result = subprocess.run(
            ["curl", "-s", "--max-time", str(timeout), "-A", UA, "-H", "Accept: application/json", url],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0 and result.stdout:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                last_err = e
        else:
            last_err = RuntimeError(f"curl failed (rc={result.returncode}): {result.stderr.strip()[:200]}")
        time.sleep(1)
    raise last_err


def strip_html(s):
    if not s:
        return s
    return re.sub(r"<[^>]+>", " ", s).strip() or None


def _row_to_metadata(data: dict) -> dict:
    temas = data.get("temas") or []
    return {
        "id": data.get("id"),
        "document_id": data.get("documentId"),
        "titulo": data.get("Titulo"),
        "descricao": strip_html(data.get("Descricao")),
        "metadados": strip_html(data.get("Metadados")),
        "tema_id": data.get("tema_id"),
        "tema_nome": temas[0].get("titulo") if temas else None,
        "unidade_id": data.get("unidade_id"),
        "unidade_nome": (data.get("unidade") or {}).get("Titulo"),
        "periodicidade_nome": (data.get("periodicidade") or {}).get("Titulo"),
        "decimais": data.get("decimais"),
        "tipo_dados": data.get("tipo_dados"),
        "ativo": data.get("ativo"),
    }


def fetch_project_theme_ids() -> set:
    """`temas` (themes) is a small, well-behaved collection where the
    `projetos` relation genuinely discriminates -- e.g. "Assistência social"
    links to 6 unrelated micro-sites, "Covid-19"/"IDHm"/"Saúde" link to none,
    while themes like "Homicídios", "Suicídio", "Violência Sexual" link
    *only* to 'atlasviolencia'. This is the reliable way to scope the
    project (see fetch_project_series docstring for why the series-level
    `projetos` relation can't be trusted for this)."""
    data = get_json(f"{CMS_BASE}/temas?populate=*&pagination%5BpageSize%5D=200")
    ids = set()
    for t in data.get("data", []):
        projetos = t.get("projetos") or []
        if any(p.get("slug") == PROJECT_SLUG for p in projetos):
            ids.add(t["id"])
    return ids


def fetch_project_series() -> list:
    """Series catalog is shared across all IPEA micro-sites and relation
    filters are ignored server-side, so pull the full ~812-row catalog with
    full `populate=*` and filter to this project client-side by theme (see
    fetch_project_theme_ids).

    NOTE: several gotchas found by trial:
    - `pagination[pageSize]` is silently capped at 100 server-side (asking
      for 1000 just gets 100 back) -- must paginate through all pages.
    - The single-item route `/series/{id}` 404s whenever this Strapi v5
      instance's `documentId` for that series is non-numeric (e.g.
      "GAC_PIBCAP") -- it matches on documentId, not the numeric `id`. Doing
      one `filters[id][$eq]=...&populate=*` call per series to work around
      that took ~35s/call (a slow/rate-limited path) -- vs ~2s per 100-row
      page when populate=* is applied to the paginated collection endpoint
      directly. So pull full metadata for everything in one paginated pass
      instead of one call per series.
    - The per-series `projetos` relation (populated via `populate=*` on
      `/series`) is NOT trustworthy for scoping to a project: every single
      one of the 812 series in the shared catalog reports membership in
      'atlasviolencia' regardless of actual topic (confirmed by spot-checking
      series like "PIB per capita" and "Assistência social" indicators, both
      clearly unrelated to violence, both still tagged 'atlasviolencia').
      This looks like a CMS data/relation bug on the series side. The
      `temas` (theme) relation does NOT have this bug -- it correctly
      excludes unrelated series -- so theme membership is used instead.
    """
    theme_ids = fetch_project_theme_ids()

    page = 1
    all_rows = []
    while True:
        url = f"{CMS_BASE}/series?populate=*&pagination%5Bpage%5D={page}&pagination%5BpageSize%5D=100"
        # this populate=*+pageSize=100 call is heavier than any other cms/api
        # route and flakes out (curl rc=28) more often than plain get_json's
        # default retries=2/timeout=30 can absorb -- give it a wider budget
        # since restarting the whole paginated walk from page 1 on failure
        # (the caller's only recourse) is expensive.
        data = get_json(url, timeout=45, retries=5)
        rows = data.get("data") or []
        all_rows.extend(rows)
        meta = data.get("meta", {}).get("pagination", {})
        if page >= meta.get("pageCount", page):
            break
        page += 1
        time.sleep(0.2)

    matched = [
        _row_to_metadata(s) for s in all_rows if s.get("tema_id") in theme_ids
    ]
    return matched


def fetch_serie_chart(series_id: int) -> list:
    """National-level annual time series for one indicator."""
    url = f"{DADOS_BASE}/serie-chart/{series_id}"
    data = get_json(url)
    labels = data.get("labels") or []
    values = data.get("data") or []
    rows = []
    for label, valor in zip(labels, values):
        ano_match = re.search(r"(\d{4})", label)
        ano = int(ano_match.group(1)) if ano_match else None
        rows.append({"serie_id": series_id, "ano": ano, "valor": valor})
    return rows


CHECKPOINT_PATH = TEMP_DIR / "checkpoint.json"


def load_checkpoint() -> dict:
    """{"<series_id>": [rows...]} for every series already fetched by a prior
    run -- keyed by str(id) because JSON object keys are always strings.
    Lives under TEMP_DIR (keyed by this machine's MAC via uuid.getnode(), see
    top of file), so it survives across separate `python3` invocations on the
    same host -- that's what makes runs resumable instead of restarting the
    157-series sweep from zero every time the wall-clock deadline hits."""
    if CHECKPOINT_PATH.exists():
        try:
            return json.loads(CHECKPOINT_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_checkpoint(checkpoint: dict) -> None:
    # write-to-temp-then-rename so a process killed mid-write can't corrupt
    # the checkpoint the next run depends on.
    tmp = CHECKPOINT_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(checkpoint))
    tmp.replace(CHECKPOINT_PATH)


def beelink_row_count(remote_dir: str) -> int:
    """Check how many rows already exist on beelink for this table."""
    result = subprocess.run(
        ["ssh", BEELINK_HOST, "~/bin/duckdb", "-c",
         f"SELECT count(*) FROM read_parquet('{remote_dir}/*.parquet', union_by_name=true);"],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        return 0
    match = re.search(r"\|(\d+)\|", result.stdout)
    return int(match.group(1)) if match else 0


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("Fetching series catalog (paginated, populate=*) and filtering to Atlas da Violência project ...")
    metadata_rows = fetch_project_series()
    series_ids = [m["id"] for m in metadata_rows]
    print(f"  found {len(series_ids)} series linked to project '{PROJECT_SLUG}'")
    if not series_ids:
        print("No series found -- aborting.")
        return 1

    # Resumable across separate invocations: series already fetched by a
    # prior run are loaded from CHECKPOINT_PATH and skipped entirely, so a
    # 157-series sweep that needs several bounded runs to finish (dados-api's
    # sustained-access flakiness means one uninterrupted run rarely gets far)
    # makes forward progress each time instead of restarting from id 0. Each
    # successful fetch is written to the checkpoint immediately (not batched
    # at the end), so a kill mid-run -- deadline, Ctrl-C, or an external
    # `timeout` -- loses at most the one in-flight request, not the run.
    checkpoint = load_checkpoint()
    pending_ids = [sid for sid in series_ids if str(sid) not in checkpoint]
    print(f"  {len(checkpoint)}/{len(series_ids)} series already checkpointed from prior runs, "
          f"{len(pending_ids)} pending")

    deadline = time.time() + float(__import__("os").environ.get("IPEA_DEADLINE_SECONDS", "420"))
    stopped_early = False
    for i, sid in enumerate(pending_ids):
        if time.time() > deadline:
            print(f"  hit deadline after {i}/{len(pending_ids)} pending series -- stopping early, "
                  f"progress so far is already checkpointed")
            stopped_early = True
            break
        try:
            checkpoint[str(sid)] = fetch_serie_chart(sid)
            save_checkpoint(checkpoint)
        except Exception as e:
            print(f"  ✗ series {sid}: serie-chart fetch failed ({e})")
        if (i + 1) % 20 == 0:
            print(f"  ... {i + 1}/{len(pending_ids)} pending series processed this run")
        # NOTE: dados-api throttles bursts -- a 0.1s gap between requests
        # made ~100% of requests time out; curl calls spaced 1.5s apart
        # succeeded 5/5 in a control test. Keep this spacing.
        time.sleep(1.5)

    # dados-api's flakiness comes in multi-minute bursts (fully hanging, then
    # fully fine) rather than being tied to any individual series -- a series
    # that failed earlier in this run often succeeds if retried once the
    # burst has passed. Give still-pending ids one more pass this run before
    # leaving them for the next invocation.
    still_pending = [sid for sid in pending_ids if str(sid) not in checkpoint]
    if still_pending and not stopped_early and time.time() < deadline:
        print(f"  retrying {len(still_pending)} failed series after a cooldown ...")
        time.sleep(10)
        for sid in still_pending:
            if time.time() > deadline:
                break
            try:
                checkpoint[str(sid)] = fetch_serie_chart(sid)
                save_checkpoint(checkpoint)
            except Exception as e:
                print(f"  ✗ series {sid}: retry also failed ({e})")
            time.sleep(1.5)
        still_failed = [sid for sid in still_pending if str(sid) not in checkpoint]
        if still_failed:
            print(f"  {len(still_failed)} series still failed after retry, left pending for next run: {still_failed}")

    covered_ids = {int(k) for k in checkpoint}
    valores_rows = [row for rows in checkpoint.values() for row in rows]
    # keep only metadata for series we actually have values for, so the two
    # tables stay consistent (no metadata rows with zero values) -- matters
    # whenever coverage is partial, which resumable runs make the normal case.
    metadata_rows = [m for m in metadata_rows if m["id"] in covered_ids]

    print(f"Total: {len(metadata_rows)} series metadata rows, {len(valores_rows)} annual value rows"
          f" ({len(covered_ids)}/{len(series_ids)} series covered overall)")
    if not metadata_rows or not valores_rows:
        print("Missing data -- aborting, not pushing incomplete tables.")
        return 1

    written = {}

    meta_table = pa.Table.from_pylist(metadata_rows)
    meta_path = TEMP_DIR / "series.parquet"
    pq.write_table(meta_table, str(meta_path), compression="zstd")
    written["series"] = (meta_path, meta_table.num_rows)
    print(f"  ✓ series: {meta_table.num_rows} rows -> {meta_path.name}")

    valores_table = pa.Table.from_pylist(valores_rows)
    valores_path = TEMP_DIR / "valores_nacional.parquet"
    pq.write_table(valores_table, str(valores_path), compression="zstd")
    written["valores_nacional"] = (valores_path, valores_table.num_rows)
    print(f"  ✓ valores_nacional: {valores_table.num_rows} rows -> {valores_path.name}")

    for table_name, (parquet_path, rows) in written.items():
        remote_dir = f"{DATASET_PATH}/{table_name}"
        existing = beelink_row_count(remote_dir)
        if existing > rows:
            print(f"  ✗ SKIPPING {table_name}: beelink has {existing} rows, this run only got {rows} (regression guard)")
            continue
        subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir}'", shell=True, check=True)
        result = subprocess.run(
            f"rsync -av {parquet_path} {BEELINK_HOST}:{remote_dir}/",
            shell=True,
        )
        if result.returncode != 0:
            print(f"  ✗ rsync failed for {table_name}")
            return 1
        print(f"  ✓ pushed {table_name} ({rows} rows) to {BEELINK_HOST}:{remote_dir}/")

    print(f"\nDone: {len(written)} tables pushed to {BEELINK_HOST}:{DATASET_PATH}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
