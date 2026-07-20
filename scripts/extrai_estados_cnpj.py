#!/usr/bin/env python3
"""Extract CNPJ establishment points, precisely geolocated via CNEFE, for all 27 UFs.

Every active CNPJ establishment (br_me_cnpj.estabelecimentos, latest monthly
snapshot) is matched to a real building address in the 2022 census address
registry (br_ibge_censo_2022.cadastro_enderecos) by exact (cep, street name,
house number). Establishments with no exact address match are dropped (no
CEP-centroid fallback) — precision over completeness. Matched establishments
sharing one building coordinate are collapsed into a single weighted point.

Standalone: pure stdlib, no AI/internet dependency beyond `ssh beelink` (or
--local against a local DuckDB file) — safe to re-run later via cron.

Usage:
  python scripts/extrai_estados_cnpj.py                 # via SSH beelink
  python scripts/extrai_estados_cnpj.py --local          # local DuckDB file
  BEELINK_HOST=custom-host python scripts/extrai_estados_cnpj.py

Output:
  docs/viz-uf/dados/<uf>.bin.gz     # binary point cloud, per UF
  docs/viz-uf/dados/meta.json       # { uf: {n_points, n_estab_ativos, n_estab_geolocalizados, bbox} }
  docs/viz-uf/generate_uf_map.md    # per-UF geolocation coverage stats report
"""

import gzip
import json
import os
import struct
import subprocess
import sys
from pathlib import Path

DADOS_DIR = Path("docs/viz-uf/dados")
REPORT_PATH = Path("docs/viz-uf/generate_uf_map.md")
BEELINK = os.environ.get("BEELINK_HOST", "beelink")
DB_PATH = os.environ.get("DB_PATH", "~/rodado/basedosdados.duckdb")

POINT_STRUCT = struct.Struct("<ffH")  # lng: f32, lat: f32, weight: u16


def ssh_duckdb(sql):
    cmd = ["ssh", BEELINK, f"~/bin/duckdb -json {DB_PATH}"]
    proc = subprocess.run(cmd, input=sql.encode(), capture_output=True, timeout=600)
    if proc.returncode != 0:
        raise RuntimeError(f"SSH/DuckDB failed:\n{proc.stderr.decode()}")
    return proc.stdout


def local_duckdb(sql):
    proc = subprocess.run(
        ["duckdb", DB_PATH, "-json"], input=sql.encode(), capture_output=True, timeout=600
    )
    if proc.returncode != 0:
        raise RuntimeError(f"DuckDB failed:\n{proc.stderr.decode()}")
    return proc.stdout


def run_query(sql, use_ssh=True):
    raw = (ssh_duckdb if use_ssh else local_duckdb)(sql)
    text = raw.decode().strip()
    if not text:
        return []
    return json.loads(text)


UF_LIST_SQL = """
SET enable_progress_bar = false;
SELECT DISTINCT sigla_uf AS uf
FROM br_me_cnpj.estabelecimentos
WHERE situacao_cadastral = '2'
  AND sigla_uf IS NOT NULL AND sigla_uf != '' AND sigla_uf != 'EX'
  AND (ano * 100 + mes) = (SELECT MAX(ano * 100 + mes) FROM br_me_cnpj.estabelecimentos)
ORDER BY uf;
"""

TOTAL_ATIVOS_SQL = """
SET enable_progress_bar = false;
WITH latest AS (
  SELECT MAX(ano * 100 + mes) AS am FROM br_me_cnpj.estabelecimentos WHERE sigla_uf = '{uf}'
)
SELECT COUNT(*) AS total
FROM br_me_cnpj.estabelecimentos
WHERE sigla_uf = '{uf}'
  AND situacao_cadastral = '2'
  AND (ano * 100 + mes) = (SELECT am FROM latest);
"""

PONTOS_SQL = """
SET enable_progress_bar = false;
WITH latest AS (
  SELECT MAX(ano * 100 + mes) AS am FROM br_me_cnpj.estabelecimentos WHERE sigla_uf = '{uf}'
),
cnefe AS (
  SELECT
    cep,
    upper(trim(nome_logradouro)) AS log_norm,
    TRY_CAST(regexp_replace(numero_logradouro, '[^0-9]', '') AS INTEGER) AS num_norm,
    AVG(TRY_CAST(latitude AS DOUBLE)) AS lat,
    AVG(TRY_CAST(longitude AS DOUBLE)) AS lng
  FROM br_ibge_censo_2022.cadastro_enderecos
  WHERE sigla_uf = '{uf}'
  GROUP BY 1, 2, 3
  HAVING num_norm IS NOT NULL
),
estab AS (
  SELECT
    cep,
    upper(trim(logradouro)) AS log_norm,
    TRY_CAST(regexp_replace(numero, '[^0-9]', '') AS INTEGER) AS num_norm
  FROM br_me_cnpj.estabelecimentos
  WHERE sigla_uf = '{uf}'
    AND situacao_cadastral = '2'
    AND (ano * 100 + mes) = (SELECT am FROM latest)
)
SELECT cnefe.lng AS lng, cnefe.lat AS lat, COUNT(*) AS weight
FROM estab
JOIN cnefe ON estab.cep = cnefe.cep
          AND estab.log_norm = cnefe.log_norm
          AND estab.num_norm = cnefe.num_norm
GROUP BY cnefe.lng, cnefe.lat;
"""


def extract_uf(uf, use_ssh):
    total_rows = run_query(TOTAL_ATIVOS_SQL.format(uf=uf), use_ssh)
    n_estab_ativos = total_rows[0]["total"] if total_rows else 0

    pontos = run_query(PONTOS_SQL.format(uf=uf), use_ssh)

    n_estab_geolocalizados = sum(r["weight"] for r in pontos)
    n_points = len(pontos)

    if n_points:
        lngs = [r["lng"] for r in pontos]
        lats = [r["lat"] for r in pontos]
        bbox = [min(lngs), min(lats), max(lngs), max(lats)]
    else:
        bbox = None

    out_path = DADOS_DIR / f"{uf.lower()}.bin.gz"
    with gzip.open(out_path, "wb", compresslevel=9) as f:
        for r in pontos:
            weight = min(r["weight"], 65535)
            f.write(POINT_STRUCT.pack(r["lng"], r["lat"], weight))

    match_rate = (n_estab_geolocalizados / n_estab_ativos * 100) if n_estab_ativos else 0.0

    return {
        "uf": uf,
        "n_estab_ativos": n_estab_ativos,
        "n_estab_geolocalizados": n_estab_geolocalizados,
        "match_rate": match_rate,
        "n_points": n_points,
        "bbox": bbox,
        "file_size": out_path.stat().st_size,
    }


def write_report(stats):
    lines = [
        "# Cobertura de geolocalização — CNPJ x CNEFE, por UF",
        "",
        "Estabelecimentos ativos (Receita Federal, snapshot mensal mais recente) geolocalizados",
        "por casamento exato de endereço (CEP + logradouro + número) com o Cadastro Nacional de",
        "Endereços para Fins Estatísticos (CNEFE, Censo IBGE 2022). Sem geolocalização, o",
        "estabelecimento não aparece no mapa — não há fallback por centroide de CEP.",
        "",
        "| UF | Estab. ativos | Geolocalizados | % | Pontos (após dedup) | Tamanho (.bin.gz) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    total_ativos = total_geo = total_points = total_size = 0
    sem_cobertura = []
    for s in stats:
        flag = " ⚠️ sem cobertura no CNEFE" if s["n_points"] == 0 else ""
        lines.append(
            f"| {s['uf']} | {s['n_estab_ativos']:,} | {s['n_estab_geolocalizados']:,} | "
            f"{s['match_rate']:.1f}% | {s['n_points']:,} | {s['file_size'] / 1e6:.2f} MB{flag} |"
        )
        total_ativos += s["n_estab_ativos"]
        total_geo += s["n_estab_geolocalizados"]
        total_points += s["n_points"]
        total_size += s["file_size"]
        if s["n_points"] == 0:
            sem_cobertura.append(s["uf"])
    overall_rate = (total_geo / total_ativos * 100) if total_ativos else 0.0
    lines.append(
        f"| **Brasil** | **{total_ativos:,}** | **{total_geo:,}** | "
        f"**{overall_rate:.1f}%** | **{total_points:,}** | **{total_size / 1e6:.2f} MB** |"
    )
    lines.append("")
    if sem_cobertura:
        lines.append(
            f"⚠️ **{', '.join(sem_cobertura)}**: 0 pontos — `br_ibge_censo_2022.cadastro_enderecos` "
            "não tem nenhuma linha para essa(s) UF(s) no mirror atual (gap na fonte/sync, não um bug "
            "de join). Essas UFs são omitidas de `meta.json` e não geram página."
        )
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines))


def main():
    use_ssh = "--local" not in sys.argv
    mode = "SSH beelink" if use_ssh else "local"
    print(f"[extrai_estados_cnpj] Extracting from {mode}...")

    DADOS_DIR.mkdir(parents=True, exist_ok=True)

    ufs = [r["uf"] for r in run_query(UF_LIST_SQL, use_ssh)]
    print(f"[extrai_estados_cnpj] {len(ufs)} UFs: {', '.join(ufs)}")

    only = [a for a in sys.argv[1:] if a not in ("--local",)]
    if only:
        ufs = [u for u in ufs if u in only]
        print(f"[extrai_estados_cnpj] Filtered to: {', '.join(ufs)}")

    meta = {}
    stats = []
    for i, uf in enumerate(ufs, 1):
        print(f"[extrai_estados_cnpj]  ({i}/{len(ufs)}) {uf}...")
        s = extract_uf(uf, use_ssh)
        print(
            f"          {s['n_estab_ativos']:,} ativos, "
            f"{s['n_estab_geolocalizados']:,} geolocalizados ({s['match_rate']:.1f}%), "
            f"{s['n_points']:,} pontos, {s['file_size'] / 1e6:.2f} MB"
        )
        if s["n_points"] == 0:
            print(f"          WARNING: 0 pontos para {uf} (sem cobertura no CNEFE?) — omitido do meta.json")
        else:
            meta[uf] = {
                "n_points": s["n_points"],
                "n_estab_ativos": s["n_estab_ativos"],
                "n_estab_geolocalizados": s["n_estab_geolocalizados"],
                "bbox": s["bbox"],
            }
        stats.append(s)

    with open(DADOS_DIR / "meta.json", "w") as f:
        json.dump(meta, f, ensure_ascii=False)

    write_report(stats)

    print(f"[extrai_estados_cnpj] Done! Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
