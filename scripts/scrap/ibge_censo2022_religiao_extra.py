#!/usr/bin/env python3
"""
Fetch the rest of the Censo Demografico 2022 "Religioes" SIDRA package
(municipio level) -> Parquet -> beelink. Companion to
ibge_censo2022_religiao.py, which already covers the core table (9537:
population by religion/sex/age).

This grabs every other SIDRA table in the same release that (a) crosses
religion with something else and (b) publishes at municipio (N6) level --
13 tables covering education, fecundity, marital status, literacy,
school attendance, home internet, housing tenure, race, and indigenous
breakdowns. Table 10203 (religion x functional-disability type) is skipped:
its "tipo de dificuldade" dimension has no aggregate "Total" category (5
non-exclusive difficulty types, sumarizacao=false), which doesn't fit this
script's "fix every non-religion dimension to Total" simplification -- a
one-off if ever needed.

For every table: the Religiao classification (id 133, 9 or 10 categories
depending on table) is fetched in full, batched into groups of 5. Every
OTHER classification dimension on the table is pinned to its "Total"
(nivel 0) category -- this keeps each table to municipio x religiao
granularity (matching the core 9537 table) rather than exploding into
every cross-tab combination.

IMPORTANT quirk discovered the hard way: SIDRA's /values endpoint accepts
n6/all (every municipio) as a territorial filter, and that works fine for
a table with ONLY the religion classification pinned (see the core
script, table 9537). But for tables with 2+ *extra* classification
dimensions pinned (even when each is pinned to its single "Total"
category, as here), n6/all makes the backend hang indefinitely -- no
error, no timeout, just a connection that never completes (confirmed: a
single-municipio request for the identical table+dims returns in ~1.3s;
n6/all on the same query never returns, even after 5+ minutes). Passing
explicit municipio codes instead of the literal "all" sidesteps whatever
slow path "all" triggers on tables like this -- chunks of 500 codes (the
full list fetched from IBGE's localidades API) return in ~2-3s each. All
5571 codes in a single request 503s (URL too long for whatever's
fronting apisidra), so chunking by both municipio-codes (500 at a time)
and religion-categories (5 at a time) is required.

Usage:
    python3 scripts/scrap/ibge_censo2022_religiao_extra.py
"""

import gzip
import subprocess
import sys
import time
from pathlib import Path

import requests

BEELINK_HOST = "beelink"
DATASET = "br_ibge_censo2022_religiao"

BASE_VALUES_URL = "https://apisidra.ibge.gov.br/values"
BASE_META_URL = "https://servicodados.ibge.gov.br/api/v3/agregados"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/b46fb9a0-ca7b-48cf-bdb5-139cca3bae1b/scratchpad/censo2022_religiao"
)

RELIGIAO_CLASSIF_ID = 133

# table id -> output table slug
TABLES = {
    6417: "cor_raca",
    10085: "mulheres_filhos_numero_idade",
    10086: "mulheres_filhos_numero_instrucao",
    10087: "mulheres_fecundidade_idade_instrucao",
    10183: "estado_conjugal",
    10187: "uniao_conjugal_natureza",
    10198: "alfabetizacao_idade",
    10199: "instrucao",
    10200: "frequencia_escola_13_17",
    10201: "internet_domicilio",
    10202: "condicao_ocupacao_domicilio_cor_raca",
    10204: "indigenas_sexo",
    10205: "indigenas_condicao_ocupacao",
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
            # The /values endpoint returns a list on success, a dict/string error
            # payload on failure. The /metadados endpoint always returns a dict
            # (that IS the successful response) -- only apply the error check
            # where a dict would be unexpected.
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


def build_dim_plan(table_id: int, meta: dict) -> dict:
    """
    Decide, per table, which classification stays fully broken out (religiao,
    always; plus the "primary" dimension -- the first non-religiao
    classification, which is the one the table's title is actually about,
    e.g. "Nivel de instrucao" for table 10199) versus which get pinned to
    their aggregate "Total" category (every other, secondary dimension --
    typically Sexo and/or Grupo de idade used as a filter, not the point of
    the table).

    Collapsing the PRIMARY dimension to Total (an earlier version of this
    script's bug) silently throws away the entire cross-tab the table
    exists for -- e.g. table 10199 (education x religion) degenerates into
    a population-by-religion total, indistinguishable from the core 9537
    table. Only secondary dimensions are safe to collapse.
    """
    classificacoes = meta["classificacoes"]
    religiao_idx = next(i for i, c in enumerate(classificacoes) if c["id"] == RELIGIAO_CLASSIF_ID)
    non_religiao = [(i, c) for i, c in enumerate(classificacoes) if c["id"] != RELIGIAO_CLASSIF_ID]
    if not non_religiao:
        primary_idx, primary_c = None, None
        secondary = []
    else:
        primary_idx, primary_c = non_religiao[0]
        secondary = non_religiao[1:]

    fixed_dims = []
    for _, c in secondary:
        total_cat = next((cat["id"] for cat in c["categorias"] if cat["nivel"] == 0), None)
        if total_cat is None:
            raise ValueError(f"table {table_id}: classificacao {c['id']} has no nivel-0 Total category")
        fixed_dims.append((c["id"], total_cat))

    return {
        "var_id": meta["variaveis"][0]["id"],
        "religiao_idx": religiao_idx,
        "religiao_cats": [cat["id"] for cat in classificacoes[religiao_idx]["categorias"]],
        "primary_idx": primary_idx,
        "primary_classif_id": primary_c["id"] if primary_c else None,
        "primary_classif_nome": primary_c["nome"] if primary_c else None,
        "primary_cats": [cat["id"] for cat in primary_c["categorias"]] if primary_c else [None],
        "fixed_dims": fixed_dims,
    }


def fetch_table(session: requests.Session, table_id: int, plan: dict, municipio_codes: list[str]) -> list[dict]:
    fixed_path = "".join(f"/c{cid}/{cat}" for cid, cat in plan["fixed_dims"])
    var_id = plan["var_id"]

    rows = []
    # 300 codes/request keeps the URL (~2.5KB) safely under IIS's default
    # 4096-byte maxUrlLength (500/request hit 4130 bytes once the
    # primary-dimension batch was added on top of the municipio-code list --
    # confirmed via a plain IIS "File or directory not found" page, i.e. a
    # URL-length rejection, not a SIDRA-level error).
    mun_chunks = list(batched(municipio_codes, 300))
    religiao_chunks = list(batched(plan["religiao_cats"], 5))
    primary_chunks = list(batched(plan["primary_cats"], 5)) if plan["primary_classif_id"] else [None]
    total_calls = len(mun_chunks) * len(religiao_chunks) * len(primary_chunks)
    call_n = 0
    for mun_chunk in mun_chunks:
        mun_param = ",".join(mun_chunk)
        for religiao_batch in religiao_chunks:
            religiao_param = ",".join(str(c) for c in religiao_batch)
            for primary_batch in primary_chunks:
                call_n += 1
                primary_path = ""
                if plan["primary_classif_id"]:
                    primary_param = ",".join(str(c) for c in primary_batch)
                    primary_path = f"/c{plan['primary_classif_id']}/{primary_param}"
                url = (
                    f"{BASE_VALUES_URL}/t/{table_id}/n6/{mun_param}/v/{var_id}/p/2022"
                    f"/c{RELIGIAO_CLASSIF_ID}/{religiao_param}{primary_path}{fixed_path}"
                )
                data = get_json(session, url)
                rows.extend(data[1:])  # drop header row
                if call_n % 10 == 0 or call_n == total_calls:
                    print(f"    {call_n}/{total_calls} requests, {len(rows)} rows so far")
                time.sleep(0.2)
    return rows


def to_records(raw_rows: list[dict], plan: dict) -> list[dict]:
    # SIDRA's D4/D5/D6... response fields are assigned by the ORDER the c<id>
    # params appear in the request URL, not by each classification's position
    # in the table's metadata (a wrong assumption in an earlier version of
    # this function that silently swapped the religiao/categoria_principal
    # columns on every table where religiao wasn't already metadata-first --
    # confirmed by inspecting a raw response: a table queried as
    # /c133/{...}/c1568/{...}/c2/{...} comes back with D4=religiao,
    # D5=nivel-de-instrucao, D6=sexo, matching URL order exactly, regardless
    # of where those three classifications sit in meta["classificacoes"]).
    # fetch_table() always emits religiao first, then primary, then the
    # fixed/secondary dims in fixed_dims order -- so the response's D-index
    # is always sequential starting at D4, unconditionally.
    religiao_d = "D4"
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
                "religiao": r.get(f"{religiao_d}N"),
                "id_religiao_sidra": r.get(f"{religiao_d}C"),
                "categoria_principal": r.get(f"{primary_d}N") if primary_d else None,
                "id_categoria_principal_sidra": r.get(f"{primary_d}C") if primary_d else None,
                "dimensao_principal": plan["primary_classif_nome"],
                "valor": value,
                "variavel": r.get("D2N"),
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
    for table_id, slug in TABLES.items():
        print(f"\n=== {table_id} -> {slug} ===")
        try:
            meta = fetch_table_metadata(session, table_id)
            print(f"  {meta['nome']}")
            plan = build_dim_plan(table_id, meta)
            print(f"  primary dim: {plan['primary_classif_nome']} ({len(plan['primary_cats'])} cats)")
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
