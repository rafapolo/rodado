#!/usr/bin/env python3
"""Extract RAIS salary data + municipality geometries for Viz 28.

Usage:
  python scripts/extrai_viz28.py                  # via SSH beelink
  python scripts/extrai_viz28.py --local          # local DuckDB file
  BEELINK_HOST=custom-host python scripts/extrai_viz28.py

Output:
  docs/viz-28/dados/municipios.geojson  # GeoJSON FeatureCollection
  docs/viz-28/dados/salarios.json       # { ano: { setor: [{ id_municipio, ... }] } }
"""

import json, os, subprocess, sys, tempfile
from pathlib import Path

OUT_DIR = Path("docs/viz-28/dados")
BEELINK = os.environ.get("BEELINK_HOST", "beelink")
DB_PATH = os.environ.get("DB_PATH", "~/rodado/basedosdados.duckdb")
ANOS = "2020,2021,2022"

def ssh_duckdb(sql):
    cmd = [
        "ssh", BEELINK,
        f"~/bin/duckdb -json {DB_PATH}"
    ]
    proc = subprocess.run(
        cmd, input=sql.encode(), capture_output=True, timeout=600
    )
    if proc.returncode != 0:
        raise RuntimeError(f"SSH/DuckDB failed:\n{proc.stderr.decode()}")
    return proc.stdout

def local_duckdb(sql):
    proc = subprocess.run(
        ["duckdb", DB_PATH, "-json"],
        input=sql.encode(), capture_output=True, timeout=600
    )
    if proc.returncode != 0:
        raise RuntimeError(f"DuckDB failed:\n{proc.stderr.decode()}")
    return proc.stdout

def run_query(sql, use_ssh=True):
    raw = (ssh_duckdb if use_ssh else local_duckdb)(sql)
    return [json.loads(line) for line in raw.strip().splitlines() if line.strip()]

SALARY_SQL = f"""
SET enable_progress_bar = false;
LOAD spatial;

WITH salarios AS (
  SELECT id_municipio, sigla_uf, ano,
    CASE WHEN natureza_juridica NOT LIKE '1%' THEN 'privado' ELSE 'publico' END AS setor,
    valor_remuneracao_media
  FROM br_me_rais.microdados_vinculos
  WHERE ano IN ({ANOS}) AND vinculo_ativo_3112 = '1'
),
agg_por_setor AS (
  SELECT id_municipio, sigla_uf, ano, setor,
    ROUND(AVG(valor_remuneracao_media), 2) AS salario_medio,
    ROUND(STDDEV(valor_remuneracao_media), 2) AS salario_stddev,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_remuneracao_media), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_remuneracao_media), 2) AS p75,
    COUNT(*) AS n_vinculos
  FROM salarios
  GROUP BY id_municipio, sigla_uf, ano, setor
),
agg_total AS (
  SELECT id_municipio, sigla_uf, ano, 'todos' AS setor,
    ROUND(AVG(valor_remuneracao_media), 2) AS salario_medio,
    ROUND(STDDEV(valor_remuneracao_media), 2) AS salario_stddev,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY valor_remuneracao_media), 2) AS p25,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY valor_remuneracao_media), 2) AS p75,
    COUNT(*) AS n_vinculos
  FROM salarios
  GROUP BY id_municipio, sigla_uf, ano
)
SELECT * FROM agg_por_setor
UNION ALL
SELECT * FROM agg_total
ORDER BY ano, setor, id_municipio;
"""

GEO_SQL = f"""
SET enable_progress_bar = false;
LOAD spatial;

SELECT id_municipio,
  ST_AsGeoJSON(ST_GeomFromWKB(geometria), 6) AS geometria
FROM br_geobr_mapas.municipio;
"""


def build_salarios(rows):
    out = {}
    for r in rows:
        ano = str(r["ano"])
        setor = r["setor"]
        entry = {
            "id_municipio": r["id_municipio"],
            "salario_medio": r["salario_medio"],
            "salario_stddev": r["salario_stddev"],
            "p25": r["p25"],
            "p75": r["p75"],
            "n_vinculos": r["n_vinculos"],
        }
        out.setdefault(ano, {}).setdefault(setor, []).append(entry)
    return out


def build_geojson(rows):
    features = []
    for r in rows:
        geom = json.loads(r["geometria"])
        features.append({
            "type": "Feature",
            "properties": {"id_municipio": r["id_municipio"]},
            "geometry": geom,
        })
    return {"type": "FeatureCollection", "features": features}


def main():
    use_ssh = "--local" not in sys.argv
    mode = "SSH beelink" if use_ssh else "local"
    print(f"[viz28] Extracting from {mode}...")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[viz28]  SQL 1/2 — salaries + dispersion...")
    salary_rows = run_query(SALARY_SQL, use_ssh)
    print(f"          {len(salary_rows)} rows")

    print("[viz28]  SQL 2/2 — geometries...")
    geo_rows = run_query(GEO_SQL, use_ssh)
    print(f"          {len(geo_rows)} rows")

    salarios = build_salarios(salary_rows)
    geojson = build_geojson(geo_rows)

    salarios_path = OUT_DIR / "salarios.json"
    geojson_path = OUT_DIR / "municipios.geojson"

    with open(salarios_path, "w") as f:
        json.dump(salarios, f, ensure_ascii=False)
    with open(geojson_path, "w") as f:
        json.dump(geojson, f, ensure_ascii=False)

    print(f"[viz28]  Done!")
    print(f"  {salarios_path}  ({salarios_path.stat().st_size / 1e6:.1f} MB)")
    print(f"  {geojson_path}  ({geojson_path.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
