#!/usr/bin/env python3
"""
Fetch per-deputy contact/biographical detail from the Camara dos Deputados
"Dados Abertos" REST API -> Parquet -> beelink.

Source: https://dadosabertos.camara.leg.br/api/v2 (no auth). The existing
mirrored table `br_camara_dados_abertos.deputado` (synced from Base dos
Dados' BigQuery copy) has no `email`/`cpf`/gabinete fields -- those only show
up on the per-deputy detail endpoint `/deputados/{id}`, not on the list
endpoint or the BQ mirror. This script builds a NEW table, `deputado_contato`,
alongside (not replacing) the mirrored `deputado` table.

Two-phase pipeline:
  1. Walk every legislatura (1..last, Camara's history goes back to 1826) via
     `/deputados?idLegislatura=N&itens=100`, paginating, to collect the set of
     unique deputy IDs who ever held a seat. ~57 legislaturas, a few thousand
     unique IDs total.
  2. For each unique ID, call `/deputados/{id}` and flatten the response
     (including the nested `gabinete` block, which is where the institutional
     email actually lives -- `ultimoStatus.email` is usually null,
     `ultimoStatus.gabinete.email` is the real field) into one row.

Historical deputies (pre-CPF-era, pre-email-era) will have null cpf/email --
that's expected, not a bug: CPF didn't exist as a national ID before 1968,
and institutional email is a modern-legislature-only concept.

`cpf` is the highest-value field here: it's a join key against every other
CPF-keyed dataset already mirrored in this project (sanctions, CNPJ/socios,
TSE candidaturas/bens, SICAF, etc).

Usage:
    python3 scripts/scrap/camara_deputados_contato.py
"""

import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen
import json

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_camara_dados_abertos"
TABLE_NAME = "deputado_contato"
BEELINK_PATH = f"{DATASET_PATH}/{TABLE_NAME}"

BASE = "https://dadosabertos.camara.leg.br/api/v2"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/0d00a083-606e-4622-a2a8-d202b160331d/scratchpad/camara"
)

MAX_WORKERS = 8


def fetch_json(url: str, timeout: int = 30):
    req = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json",
            "Accept-Language": "pt-BR,pt;q=0.9",
        },
    )
    for attempt in range(3):
        try:
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if attempt == 2:
                print(f"  {url}: giving up ({e})", flush=True)
                return None
            time.sleep(1 + attempt)
    return None


def fetch_legislatura_ids():
    """Every legislatura ID that exists, oldest first."""
    data = fetch_json(f"{BASE}/legislaturas?ordem=ASC&ordenarPor=id&itens=100")
    if not data:
        return []
    return [row["id"] for row in data["dados"]]


def fetch_deputy_ids_for_legislatura(leg_id: int):
    """All unique deputy IDs who sat in a given legislatura, paginated."""
    ids = set()
    page = 1
    while True:
        url = f"{BASE}/deputados?idLegislatura={leg_id}&itens=100&pagina={page}"
        data = fetch_json(url)
        if not data:
            break
        for row in data["dados"]:
            ids.add(row["id"])
        if not any(link["rel"] == "next" for link in data.get("links", [])):
            break
        page += 1
    return ids


def collect_all_deputy_ids():
    legislaturas = fetch_legislatura_ids()
    print(f"{len(legislaturas)} legislaturas found (1826-present)", flush=True)
    all_ids = set()
    for i, leg_id in enumerate(legislaturas, 1):
        ids = fetch_deputy_ids_for_legislatura(leg_id)
        all_ids |= ids
        print(f"  legislatura {leg_id} ({i}/{len(legislaturas)}): +{len(ids)} -> total unique {len(all_ids)}", flush=True)
    return sorted(all_ids)


def fetch_deputy_detail(dep_id: int):
    data = fetch_json(f"{BASE}/deputados/{dep_id}")
    if not data or "dados" not in data:
        return None
    d = data["dados"]
    status = d.get("ultimoStatus") or {}
    gabinete = status.get("gabinete") or {}
    rede_social = d.get("redeSocial") or []
    return {
        "id_deputado": d.get("id"),
        "nome_civil": d.get("nomeCivil"),
        "cpf": d.get("cpf"),
        "sexo": d.get("sexo"),
        "url_website": d.get("urlWebsite"),
        "rede_social": "; ".join(rede_social) if rede_social else None,
        "data_nascimento": d.get("dataNascimento"),
        "data_falecimento": d.get("dataFalecimento"),
        "uf_nascimento": d.get("ufNascimento"),
        "municipio_nascimento": d.get("municipioNascimento"),
        "escolaridade": d.get("escolaridade"),
        "nome": status.get("nome"),
        "nome_eleitoral": status.get("nomeEleitoral"),
        "sigla_partido": status.get("siglaPartido"),
        "sigla_uf": status.get("siglaUf"),
        "id_legislatura": status.get("idLegislatura"),
        "email": gabinete.get("email"),
        "situacao": status.get("situacao"),
        "condicao_eleitoral": status.get("condicaoEleitoral"),
        "gabinete_nome": gabinete.get("nome"),
        "gabinete_predio": gabinete.get("predio"),
        "gabinete_sala": gabinete.get("sala"),
        "gabinete_andar": gabinete.get("andar"),
        "gabinete_telefone": gabinete.get("telefone"),
        "data_status": status.get("data"),
        "url_foto": status.get("urlFoto"),
    }


def fetch_all_details(dep_ids):
    rows = []
    total = len(dep_ids)
    done = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_deputy_detail, dep_id): dep_id for dep_id in dep_ids}
        for fut in as_completed(futures):
            done += 1
            row = fut.result()
            if row:
                rows.append(row)
            if done % 200 == 0 or done == total:
                print(f"  {done}/{total} deputies fetched ({len(rows)} ok)", flush=True)
    return rows


def write_and_push(rows, table_name: str):
    import pyarrow as pa
    import pyarrow.parquet as pq

    if not rows:
        print(f"[{table_name}] No rows fetched -- skipping push.")
        return False

    table = pa.Table.from_pylist(rows)
    parquet_path = TEMP_DIR / f"{table_name}.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"[{table_name}] Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

    remote_dir = f"{DATASET_PATH}/{table_name}"
    mkdir_result = subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {remote_dir}'", shell=True)
    if mkdir_result.returncode != 0:
        print(f"[{table_name}] ssh mkdir failed (beelink unreachable?) -- parquet kept locally at {parquet_path}, not pushed.", file=sys.stderr)
        return False
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{remote_dir}/",
        shell=True,
    )
    if result.returncode != 0:
        print(f"[{table_name}] rsync failed -- parquet kept locally at {parquet_path}", file=sys.stderr)
        return False

    print(f"[{table_name}] Pushed to {BEELINK_HOST}:{remote_dir}/{parquet_path.name}")
    return True


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print("=== collecting unique deputy IDs across all legislaturas ===")
    dep_ids = collect_all_deputy_ids()
    print(f"\n{len(dep_ids)} unique deputies total\n")

    print("=== fetching per-deputy detail (cpf, email, gabinete, situacao...) ===")
    rows = fetch_all_details(dep_ids)

    ok = write_and_push(rows, TABLE_NAME)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
