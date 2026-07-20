#!/usr/bin/env python3
"""
Fetch the Censo Demografico 2022 "cor ou raca" x educacao/fecundidade SIDRA
tables (municipio level) -> Parquet -> beelink. Sibling of
ibge_censo2022_religiao_extra.py, same technique, different anchor
classification ("Cor ou raca" instead of "Religiao") -- built to feed
results/racas_fecundidade_2022.png, the 2022 equivalent of
results/racas_fecundidade_2010.png (which used 2010 microdata directly).

Two tables:
  - 10061: Pessoas de 18+ por nivel de instrucao, segundo grupo idade, sexo,
    cor ou raca -> "instrucao" (anchor: cor ou raca; primary: nivel de
    instrucao, kept broken out; sexo/grupo idade collapsed to Total)
  - 10078: Mulheres de 12+, total filhos nascidos vivos / filhos vivos hoje /
    filhos nascidos nos ultimos 12 meses, por grupo idade das mulheres,
    segundo nivel de instrucao e cor ou raca -> "fecundidade_idade" (anchor:
    cor ou raca; primary: grupo idade das mulheres, kept broken out --
    filtering to "45 a 49 anos" later gives completed fertility, same
    methodology as the 2010 chart's V6633-at-45-49 approach; nivel de
    instrucao collapsed to Total, we only need it split by raca here)

Both variables 13315 (Mulheres de 12+, the denominator) and 13316 (Filhos
tidos nascidos vivos, the numerator) are fetched together for 10078 --
learned the hard way on the religion scraper that grabbing only variaveis[0]
silently gets the wrong measure on multi-variable tables like this one.

Same municipio-code-chunking (300/request, avoids the ~4096-byte IIS
maxUrlLength that killed a naive n6/all or 500-code-chunk approach) and
primary/anchor-dimension batching (5 categories/request) as the religion
scraper -- see that script's docstring for the full story on both quirks.

Usage:
    python3 scripts/scrap/ibge_censo2022_raca.py
"""

import gzip
import subprocess
import sys
import time
from pathlib import Path

import requests

BEELINK_HOST = "beelink"
DATASET = "br_ibge_censo2022_raca"

BASE_VALUES_URL = "https://apisidra.ibge.gov.br/values"
BASE_META_URL = "https://servicodados.ibge.gov.br/api/v3/agregados"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/b46fb9a0-ca7b-48cf-bdb5-139cca3bae1b/scratchpad/censo2022_raca"
)

ANCHOR_NAME_SUBSTR = "cor ou raça"

# table id -> (output slug, explicit variable ids to fetch or None for var0)
TABLES = {
    10061: ("instrucao", None),
    10078: ("fecundidade_idade", [13315, 13316]),
}


def get_json(session: requests.Session, url: str, retries: int = 4, expect_list: bool = True):
    last_exc = None
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=120)
            resp.raise_for_status()
            raw = resp.content
            if raw[:2] == b"\x1f\x8b":
                raw = gzip.decompress(raw)
            import json

            data = json.loads(raw.decode("utf-8"))
            if expect_list and isinstance(data, dict):
                raise RuntimeError(f"SIDRA error payload: {data}")
            return data
        except (requests.exceptions.RequestException, RuntimeError) as exc:
            last_exc = exc
            wait = 2 ** attempt
            print(f"    retry {attempt + 1}/{retries} after error: {exc} (sleeping {wait}s)")
            time.sleep(wait)
    raise last_exc


def fetch_table_metadata(session: requests.Session, table_id: int) -> dict:
    return get_json(session, f"{BASE_META_URL}/{table_id}/metadados", expect_list=False)


def batched(seq: list, size: int):
    for i in range(0, len(seq), size):
        yield seq[i : i + size]


def fetch_municipio_codes(session: requests.Session) -> list[str]:
    resp = session.get("https://servicodados.ibge.gov.br/api/v1/localidades/municipios", timeout=60)
    resp.raise_for_status()
    return [str(m["id"]) for m in resp.json()]


def build_dim_plan(table_id: int, meta: dict, var_ids_override: list[int] | None) -> dict:
    classificacoes = meta["classificacoes"]
    anchor_idx = next(i for i, c in enumerate(classificacoes) if ANCHOR_NAME_SUBSTR in c["nome"].lower())
    non_anchor = [(i, c) for i, c in enumerate(classificacoes) if i != anchor_idx]
    if not non_anchor:
        primary_idx, primary_c = None, None
        secondary = []
    else:
        primary_idx, primary_c = non_anchor[0]
        secondary = non_anchor[1:]

    fixed_dims = []
    for _, c in secondary:
        total_cat = next((cat["id"] for cat in c["categorias"] if cat["nivel"] == 0), None)
        if total_cat is None:
            raise ValueError(f"table {table_id}: classificacao {c['id']} has no nivel-0 Total category")
        fixed_dims.append((c["id"], total_cat))

    var_ids = var_ids_override if var_ids_override else [meta["variaveis"][0]["id"]]

    return {
        "var_ids": var_ids,
        "anchor_idx": anchor_idx,
        "anchor_classif_id": classificacoes[anchor_idx]["id"],
        "anchor_cats": [cat["id"] for cat in classificacoes[anchor_idx]["categorias"]],
        "primary_idx": primary_idx,
        "primary_classif_id": primary_c["id"] if primary_c else None,
        "primary_classif_nome": primary_c["nome"] if primary_c else None,
        "primary_cats": [cat["id"] for cat in primary_c["categorias"]] if primary_c else [None],
        "fixed_dims": fixed_dims,
    }


def fetch_table(session: requests.Session, table_id: int, plan: dict, municipio_codes: list[str]) -> list[dict]:
    fixed_path = "".join(f"/c{cid}/{cat}" for cid, cat in plan["fixed_dims"])
    var_param = ",".join(str(v) for v in plan["var_ids"])

    rows = []
    mun_chunks = list(batched(municipio_codes, 300))
    anchor_chunks = list(batched(plan["anchor_cats"], 5))
    primary_chunks = list(batched(plan["primary_cats"], 5)) if plan["primary_classif_id"] else [None]
    total_calls = len(mun_chunks) * len(anchor_chunks) * len(primary_chunks)
    call_n = 0
    for mun_chunk in mun_chunks:
        mun_param = ",".join(mun_chunk)
        for anchor_batch in anchor_chunks:
            anchor_param = ",".join(str(c) for c in anchor_batch)
            for primary_batch in primary_chunks:
                call_n += 1
                primary_path = ""
                if plan["primary_classif_id"]:
                    primary_param = ",".join(str(c) for c in primary_batch)
                    primary_path = f"/c{plan['primary_classif_id']}/{primary_param}"
                url = (
                    f"{BASE_VALUES_URL}/t/{table_id}/n6/{mun_param}/v/{var_param}/p/2022"
                    f"/c{plan['anchor_classif_id']}/{anchor_param}{primary_path}{fixed_path}"
                )
                data = get_json(session, url)
                rows.extend(data[1:])
                if call_n % 10 == 0 or call_n == total_calls:
                    print(f"    {call_n}/{total_calls} requests, {len(rows)} rows so far")
                time.sleep(0.2)
    return rows


def to_records(raw_rows: list[dict], plan: dict) -> list[dict]:
    # D-index follows URL param order (anchor, primary, then fixed dims),
    # not metadata classificacoes order -- see the identical note in
    # ibge_censo2022_religiao_extra.py's to_records for how this was found.
    anchor_d = "D4"
    primary_d = "D5" if plan["primary_idx"] is not None else None
    records = []
    for r in raw_rows:
        v = r.get("V")
        try:
            value = int(v)
        except (TypeError, ValueError):
            value = None
        records.append(
            {
                "id_municipio": r["D1C"],
                "municipio": r["D1N"],
                "ano": int(r["D3C"]) if r.get("D3C") else 2022,
                "cor_raca": r.get(f"{anchor_d}N"),
                "id_cor_raca_sidra": r.get(f"{anchor_d}C"),
                "categoria_principal": r.get(f"{primary_d}N") if primary_d else None,
                "id_categoria_principal_sidra": r.get(f"{primary_d}C") if primary_d else None,
                "dimensao_principal": plan["primary_classif_nome"],
                "valor": value,
                "variavel": r.get("D2N"),
                "id_variavel": r.get("D2C"),
            }
        )
    return records


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    print("Fetching municipio code list...")
    municipio_codes = fetch_municipio_codes(session)
    print(f"  {len(municipio_codes)} municipios")

    failed = []
    for table_id, (slug, var_override) in TABLES.items():
        print(f"\n=== {table_id} -> {slug} ===")
        try:
            meta = fetch_table_metadata(session, table_id)
            print(f"  {meta['nome']}")
            plan = build_dim_plan(table_id, meta, var_override)
            print(f"  anchor: cor ou raça ({len(plan['anchor_cats'])} cats) | primary dim: {plan['primary_classif_nome']} ({len(plan['primary_cats'])} cats) | vars: {plan['var_ids']}")
            raw_rows = fetch_table(session, table_id, plan, municipio_codes)
            print(f"  {len(raw_rows)} rows")
            records = to_records(raw_rows, plan)
            if not records:
                print(f"  WARNING: no rows for {table_id}, skipping")
                failed.append(table_id)
                continue

            table = pa.Table.from_pylist(records)
            parquet_path = TEMP_DIR / f"{slug}.parquet"
            pq.write_table(table, str(parquet_path), compression="zstd")
            print(f"  Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.2f} MB, {table.num_rows} rows)")

            beelink_path = f"~/rodado/{DATASET}/{slug}"
            subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {beelink_path}'", shell=True, check=True)
            result = subprocess.run(f"rsync -av {parquet_path} {BEELINK_HOST}:{beelink_path}/", shell=True)
            if result.returncode != 0:
                print(f"  rsync FAILED for {slug}", file=sys.stderr)
                failed.append(table_id)
            else:
                print(f"  Pushed to {BEELINK_HOST}:{beelink_path}/{parquet_path.name}")
        except Exception as exc:
            print(f"  FAILED: {exc}", file=sys.stderr)
            failed.append(table_id)

    print(f"\n{'=' * 60}")
    print(f"Done: {len(TABLES) - len(failed)}/{len(TABLES)} tables OK")
    if failed:
        print(f"Failed: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
