#!/usr/bin/env python3
"""Extract CNPJ establishment points, precisely geolocated via CNEFE, for all 27 UFs.

Every active CNPJ establishment (br_me_cnpj.estabelecimentos, latest monthly
snapshot) is matched to a real building address in the 2022 census address
registry (br_ibge_censo_2022.cadastro_enderecos). Matching, in order:
  1. Exact (cep, street name, house number) after accent/article normalization.
  2. Same street, but the house number isn't in CNEFE — interpolate its position
     between the nearest known numbers below/above on that street (or use the
     nearest single known edge), trusted only within INTERP_MAX_GAP numbers.
  3. Street name itself isn't in CNEFE for that CEP — fuzzy-match it (Jaro-Winkler,
     CEP is trusted as the anchor so a CEP's handful of candidate streets is a safe
     search space) against CNEFE streets in the same CEP, then interpolate as above.
Establishments with no address resolvable this way are dropped — no CEP-centroid
fallback. Matched establishments collapsing onto the same resolved coordinate are
combined into a single weighted point.

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

import array
import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

DADOS_DIR = Path("docs/viz-uf/dados")
REPORT_PATH = Path("docs/viz-uf/generate_uf_map.md")
BEELINK = os.environ.get("BEELINK_HOST", "beelink")
DB_PATH = os.environ.get("DB_PATH", "~/rodado/basedosdados.duckdb")

# Struct-of-arrays layout, not array-of-structs: all n lngs (f32), then all n
# lats (f32), then all n weights (u16) — three homogeneous, contiguous, aligned
# blocks instead of interleaved 10-byte records. Record-level interleaving
# can't be read back as a zero-copy typed array in JS (10 isn't a multiple of
# 4, so most records start at a misaligned offset for Float32Array); SoA lets
# the browser read each block directly as a typed-array view with no parsing
# loop. `array.array` uses native byte order, which is little-endian on every
# real deployment target (x86/ARM) and matches the JS side's `true` (little-
# endian) DataView/TypedArray reads.
def write_points_soa(path, pontos):
    lngs = array.array("f", (p["lng"] for p in pontos))
    lats = array.array("f", (p["lat"] for p in pontos))
    weights = array.array("H", (min(p["weight"], 65535) for p in pontos))
    with gzip.open(path, "wb", compresslevel=9) as f:
        f.write(lngs.tobytes())
        f.write(lats.tobytes())
        f.write(weights.tobytes())


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

FUZZY_SIM_THRESHOLD = 0.70
INTERP_MAX_GAP = 100  # house numbers; caps both interpolation gaps and edge extrapolation

PONTOS_SQL = """
SET enable_progress_bar = false;
WITH latest AS (
  SELECT MAX(ano * 100 + mes) AS am FROM br_me_cnpj.estabelecimentos WHERE sigla_uf = '{uf}'
),
cnefe AS (
  SELECT
    cep,
    trim(regexp_replace(upper(trim(strip_accents(nome_logradouro))), '\\b(DA|DE|DO|DOS|DAS)\\b', '', 'g')) AS log_norm,
    TRY_CAST(regexp_replace(numero_logradouro, '[^0-9]', '') AS INTEGER) AS num_norm,
    AVG(TRY_CAST(latitude AS DOUBLE)) AS lat,
    AVG(TRY_CAST(longitude AS DOUBLE)) AS lng
  FROM br_ibge_censo_2022.cadastro_enderecos
  WHERE sigla_uf = '{uf}'
  GROUP BY 1, 2, 3
  HAVING num_norm IS NOT NULL
),
cnefe_streets AS (
  SELECT DISTINCT cep, log_norm FROM cnefe
),
estab AS (
  SELECT
    row_number() OVER () AS rid,
    cep,
    trim(regexp_replace(upper(trim(strip_accents(logradouro))), '\\b(DA|DE|DO|DOS|DAS)\\b', '', 'g')) AS log_norm,
    TRY_CAST(regexp_replace(numero, '[^0-9]', '') AS INTEGER) AS num_norm
  FROM br_me_cnpj.estabelecimentos
  WHERE sigla_uf = '{uf}'
    AND situacao_cadastral = '2'
    AND (ano * 100 + mes) = (SELECT am FROM latest)
),
-- tier 1: street name matches CNEFE exactly (after accent/article normalization)
street_ok AS (
  SELECT e.rid, e.cep, e.log_norm AS street_used, e.num_norm
  FROM estab e JOIN cnefe_streets cs ON e.cep = cs.cep AND e.log_norm = cs.log_norm
),
-- tier 2: CEP is trusted, but street name is fuzzy-matched (typos/variants) among
-- CNEFE streets in that same CEP, since a CEP only has a handful of candidate streets
street_fuzzy AS (
  SELECT e.rid, e.cep, cs.log_norm AS street_used, e.num_norm,
    row_number() OVER (PARTITION BY e.rid ORDER BY jaro_winkler_similarity(e.log_norm, cs.log_norm) DESC) AS rn,
    jaro_winkler_similarity(e.log_norm, cs.log_norm) AS sim
  FROM estab e
  LEFT JOIN street_ok so ON e.rid = so.rid
  JOIN cnefe_streets cs ON e.cep = cs.cep
  WHERE so.rid IS NULL
  QUALIFY rn = 1 AND sim >= {fuzzy_threshold}
),
candidates AS (
  SELECT rid, cep, street_used, num_norm FROM street_ok
  UNION ALL
  SELECT rid, cep, street_used, num_norm FROM street_fuzzy
),
-- for each candidate, find the nearest known house numbers below and above the
-- target on that (cep, street) — exact match if the number itself is known
interp AS (
  SELECT c.rid, c.num_norm AS target,
    lo.num_norm AS lo_num, lo.lat AS lo_lat, lo.lng AS lo_lng,
    hi.num_norm AS hi_num, hi.lat AS hi_lat, hi.lng AS hi_lng
  FROM candidates c
  LEFT JOIN LATERAL (
    SELECT num_norm, lat, lng FROM cnefe cn
    WHERE cn.cep = c.cep AND cn.log_norm = c.street_used AND cn.num_norm <= c.num_norm
    ORDER BY cn.num_norm DESC LIMIT 1
  ) lo ON true
  LEFT JOIN LATERAL (
    SELECT num_norm, lat, lng FROM cnefe cn
    WHERE cn.cep = c.cep AND cn.log_norm = c.street_used AND cn.num_norm >= c.num_norm
    ORDER BY cn.num_norm ASC LIMIT 1
  ) hi ON true
),
-- linearly interpolate position between the bracketing known numbers (or use the
-- single known edge point), only trusted within INTERP_MAX_GAP house numbers —
-- beyond that, house-number spacing is too irregular to assume a straight line
resolved AS (
  SELECT rid,
    CASE
      WHEN lo_num IS NOT NULL AND hi_num IS NOT NULL AND hi_num != lo_num AND (hi_num - lo_num) <= {interp_max_gap}
        THEN lo_lat + (hi_lat - lo_lat) * ((target - lo_num)::DOUBLE / (hi_num - lo_num))
      WHEN lo_num IS NOT NULL AND hi_num IS NOT NULL AND hi_num = lo_num THEN lo_lat
      WHEN lo_num IS NOT NULL AND (hi_num IS NULL OR hi_num - lo_num > {interp_max_gap}) AND (target - lo_num) <= {interp_max_gap} THEN lo_lat
      WHEN hi_num IS NOT NULL AND (lo_num IS NULL OR hi_num - lo_num > {interp_max_gap}) AND (hi_num - target) <= {interp_max_gap} THEN hi_lat
      ELSE NULL
    END AS lat,
    CASE
      WHEN lo_num IS NOT NULL AND hi_num IS NOT NULL AND hi_num != lo_num AND (hi_num - lo_num) <= {interp_max_gap}
        THEN lo_lng + (hi_lng - lo_lng) * ((target - lo_num)::DOUBLE / (hi_num - lo_num))
      WHEN lo_num IS NOT NULL AND hi_num IS NOT NULL AND hi_num = lo_num THEN lo_lng
      WHEN lo_num IS NOT NULL AND (hi_num IS NULL OR hi_num - lo_num > {interp_max_gap}) AND (target - lo_num) <= {interp_max_gap} THEN lo_lng
      WHEN hi_num IS NOT NULL AND (lo_num IS NULL OR hi_num - lo_num > {interp_max_gap}) AND (hi_num - target) <= {interp_max_gap} THEN hi_lng
      ELSE NULL
    END AS lng
  FROM interp
)
SELECT round(lng, 6) AS lng, round(lat, 6) AS lat, COUNT(*) AS weight
FROM resolved
WHERE lat IS NOT NULL AND lng IS NOT NULL
GROUP BY round(lng, 6), round(lat, 6);
"""


def extract_uf(uf, use_ssh):
    total_rows = run_query(TOTAL_ATIVOS_SQL.format(uf=uf), use_ssh)
    n_estab_ativos = total_rows[0]["total"] if total_rows else 0

    sql = PONTOS_SQL.format(uf=uf, fuzzy_threshold=FUZZY_SIM_THRESHOLD, interp_max_gap=INTERP_MAX_GAP)
    pontos = run_query(sql, use_ssh)

    n_estab_geolocalizados = sum(r["weight"] for r in pontos)
    n_points = len(pontos)

    if n_points:
        lngs = [r["lng"] for r in pontos]
        lats = [r["lat"] for r in pontos]
        bbox = [min(lngs), min(lats), max(lngs), max(lats)]
    else:
        bbox = None

    out_path = DADOS_DIR / f"{uf.lower()}.bin.gz"
    file_size = 0
    if n_points:
        write_points_soa(out_path, pontos)
        file_size = out_path.stat().st_size
    else:
        out_path.unlink(missing_ok=True)

    match_rate = (n_estab_geolocalizados / n_estab_ativos * 100) if n_estab_ativos else 0.0

    return {
        "uf": uf,
        "n_estab_ativos": n_estab_ativos,
        "n_estab_geolocalizados": n_estab_geolocalizados,
        "match_rate": match_rate,
        "n_points": n_points,
        "bbox": bbox,
        "file_size": file_size,
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
