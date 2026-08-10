#!/usr/bin/env python3
"""Une a série mensal do zip histórico da ANA com o que o SOAP devolveu.

Duas fontes, dois recortes, um buraco entre elas:

  * zip `hidro-dados-estacoes-convencionais` (via `ana_series_historicas.py`):
    1901-01 a **2023-09**, retrato de 04/08/2023. Traz método de obtenção, dia
    da máxima e da mínima, média anual — e a série diária, que o SOAP não dá.
  * SOAP `HidroSerieHistorica` (via `ana_soap_worker.py`): 1960 a **2026-04**.
    Só o mensal, e só media/maxima/minima.

O resultado é `series_vazao_mensal_completa`, que estende a cobertura em ~2,5
anos sem perder as colunas que só o zip tem.

Regra de conflito, na ordem:
  1. maior `nivel_consistencia` vence — consistido (2) sobre bruto (1), a mesma
     regra do `ana_series_historicas.py` e do `processa.py` no rios-do-brasil.
  2. empate resolve pelo zip, que carrega mais colunas e é o dado que a ANA
     publicou como release, não a base secundária do serviço.

A tabela original NÃO é tocada: o diário continua apontando para a janela do
zip, e comparar as duas mensais é o que permite auditar o que o SOAP mudou.

Uso (no beelink, depois do ana_soap_worker.py terminar):
    python3 ana_series_unifica_gap.py [--gap ~/soap_gap]
"""

import argparse
import subprocess
import sys
from pathlib import Path

LAKE = "~/rodado/br_ana_telemetria"

SQL = """
SET enable_progress_bar=false;

CREATE OR REPLACE TEMP VIEW zip AS
SELECT codigo, data, nivel_consistencia, metodo,
       media, maxima, minima, dia_maxima, dia_minima, media_anual,
       'zip' AS fonte
  FROM read_parquet('{lake}/series_vazao_mensal/**/*.parquet');

-- O worker grava uma linha só com `codigo` para estação viva mas sem série, e
-- essas linhas vêm sem a coluna `mes`; o filtro as descarta.
CREATE OR REPLACE TEMP VIEW soap AS
SELECT codigo,
       strptime(mes || '-01', '%Y-%m-%d')::DATE AS data,
       nivel_consistencia,
       NULL::TINYINT AS metodo,
       vazao_media AS media, vazao_maxima AS maxima, vazao_minima AS minima,
       NULL::TINYINT AS dia_maxima, NULL::TINYINT AS dia_minima,
       NULL::DOUBLE AS media_anual,
       'soap' AS fonte
  FROM read_parquet('{gap}/batch_*.parquet')
 WHERE mes IS NOT NULL AND vazao_media IS NOT NULL;

CREATE OR REPLACE TEMP VIEW juntas AS
SELECT * FROM zip UNION ALL BY NAME SELECT * FROM soap;

COPY (
  SELECT * EXCLUDE (rn)
    FROM (
      SELECT *, row_number() OVER (
               PARTITION BY codigo, data
               ORDER BY nivel_consistencia DESC,
                        CASE fonte WHEN 'zip' THEN 0 ELSE 1 END
             ) AS rn
        FROM juntas
    )
   WHERE rn = 1
) TO '{lake}/series_vazao_mensal_completa'
  (FORMAT PARQUET, COMPRESSION ZSTD,
   PARTITION_BY (bacia), OVERWRITE_OR_IGNORE 1);
"""

# `bacia` precisa existir como coluna para o PARTITION_BY; é derivada, não vem
# das fontes. Injetada nas duas views acima via este wrapper para não repetir.
SQL = SQL.replace(
    "SELECT * FROM zip UNION ALL BY NAME SELECT * FROM soap;",
    "SELECT *, substr(codigo, 1, 2) AS bacia FROM zip\n"
    "UNION ALL BY NAME\n"
    "SELECT *, substr(codigo, 1, 2) AS bacia FROM soap;",
)

RESUMO = """
SET enable_progress_bar=false;
SELECT fonte, count(*) AS linhas, count(DISTINCT codigo) AS estacoes,
       min(data) AS ini, max(data) AS fim
  FROM read_parquet('{lake}/series_vazao_mensal_completa/**/*.parquet')
 GROUP BY 1 ORDER BY 1;
"""


def duck(sql: str, host: str | None) -> str:
    if host:
        argv = ["ssh", host, "~/bin/duckdb"]
    else:
        # No beelink o binário mora em ~/bin, que não entra no PATH de shell
        # não-interativo — rodar só `duckdb` dá FileNotFoundError.
        local = Path("~/bin/duckdb").expanduser()
        argv = [str(local) if local.exists() else "duckdb"]
    out = subprocess.run(argv, input=sql, capture_output=True, text=True)
    if out.returncode != 0:
        print(out.stderr.strip(), file=sys.stderr)
        raise SystemExit(f"duckdb falhou ({out.returncode})")
    return out.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", default="~/soap_gap", help="pasta dos batch_*.parquet")
    ap.add_argument("--host", default=None,
                    help="rodar via ssh neste host (omita se já estiver no beelink)")
    a = ap.parse_args()

    if not a.host and not Path(a.gap).expanduser().is_dir():
        raise SystemExit(f"pasta do gap não encontrada: {a.gap}")

    print("unificando zip + SOAP...")
    duck(SQL.format(lake=LAKE, gap=a.gap), a.host)
    print(duck(RESUMO.format(lake=LAKE), a.host))
    print("pronto. rode scripts/build_metadata_catalog.py para registrar no catálogo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
