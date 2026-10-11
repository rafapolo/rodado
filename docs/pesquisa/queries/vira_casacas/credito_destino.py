#!/usr/bin/env python3
"""Para onde vai o crédito rural dos municípios vira-casaca e dos que se mantiveram.

    python3 docs/pesquisa/queries/vira_casacas/credito_destino.py            # mostra, não grava
    python3 docs/pesquisa/queries/vira_casacas/credito_destino.py --grava    # regrava credito_destino.csv
    python3 docs/pesquisa/queries/vira_casacas/credito_destino.py --de sicor.csv   # reagrega um extrato salvo

É a consulta que gerou `credito_destino.csv` (lido por scripts/plot_vira_casacas_cartaz.py),
rodada em 2026-10-08. Dois passos:

1. No beelink: operações de crédito rural de 2020 a 2024 (`ano_emissao`), somando
   `valor_parcela_credito` por grupo do município e por finalidade, atividade, modalidade e
   produto do empreendimento. O município não está na operação: sai do CAR da propriedade
   financiada (`recurso_publico_propriedade.id_car`, caracteres 3 a 9 = código IBGE de 7
   dígitos), então operação sem propriedade com CAR fica de fora. O grupo (vira, mantido,
   outro) vem de `municipios.csv`, nesta pasta.
2. Aqui: cada linha vira um destino. Modalidade que começa com MÁQUINAS é "Máquinas e
   equipamentos" (e, dentro dela, o produto TRATOR é somado à parte); os produtos SOJA,
   BOVINOS, MILHO, TRIGO e CAFÉ ficam com o próprio nome; o resto é "Outros". `fatia` é a
   parte do valor do grupo.

O SICOR do espelho foi ressincronizado em 2026-10-09, depois do cartaz: rodar de novo dá
valores um pouco diferentes dos publicados. Por isso o padrão é não gravar.
"""
import argparse
import csv
import io
import subprocess
from pathlib import Path

import polars as pl

AQUI = Path(__file__).resolve().parent
SQL = """SET enable_progress_bar=false;
CREATE TEMP TABLE g(id_municipio BIGINT, grupo VARCHAR); INSERT INTO g VALUES {grupos};
COPY (
SELECT g.grupo, e.finalidade, e.atividade, e.modalidade, e.produto,
       sum(o.valor_parcela_credito) valor, count(*) n
FROM br_bcb_sicor.recurso_publico_propriedade p
JOIN br_bcb_sicor.operacao o ON o.id_referencia_bacen=p.id_referencia_bacen AND o.numero_ordem=p.numero_ordem
JOIN g ON g.id_municipio = TRY_CAST(substr(p.id_car,3,7) AS BIGINT)
LEFT JOIN br_bcb_sicor.empreendimento e ON e.id_empreendimento=o.id_empreendimento
WHERE p.ano_emissao BETWEEN 2020 AND 2024 AND p.id_car IS NOT NULL
GROUP BY ALL) TO '/dev/stdout' (FORMAT csv, HEADER);"""


def extrai() -> pl.DataFrame:
    with open(AQUI / "municipios.csv") as f:
        grupos = ",".join(f"({r['id_municipio']},'{r['grupo']}')" for r in csv.DictReader(f))
    r = subprocess.run(["ssh", "beelink", "~/bin/duckdb -readonly ~/rodado/basedosdados.duckdb"],
                       input=SQL.format(grupos=grupos), capture_output=True, text=True, check=True)
    texto = r.stdout[r.stdout.index("grupo,"):]
    return pl.read_csv(io.StringIO(texto))


def agrega(d: pl.DataFrame) -> pl.DataFrame:
    d = d.filter(pl.col("grupo") != "outro")
    maq = pl.col("modalidade").str.starts_with("MÁQUINAS")
    d = d.with_columns(
        pl.when(maq).then(pl.lit("Máquinas e equipamentos"))
          .when(pl.col("produto").is_in(["SOJA", "BOVINOS", "MILHO", "TRIGO", "CAFÉ"])).then(pl.col("produto").str.to_titlecase())
          .otherwise(pl.lit("Outros")).alias("destino"),
        (pl.col("produto") == "TRATOR").alias("trator"))
    o = (d.group_by("grupo", "destino")
          .agg(pl.col("valor").sum(), pl.col("valor").filter(pl.col("trator")).sum().alias("valor_trator"))
          .sort("grupo", "valor", descending=[False, True]))
    return o.with_columns((pl.col("valor") / pl.col("valor").sum().over("grupo")).round(4).alias("fatia"),
                          (pl.col("valor_trator") / pl.col("valor").sum().over("grupo")).round(4).alias("fatia_trator"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--de", help="extrato do passo 1 já salvo (csv), em vez de consultar o beelink")
    ap.add_argument("--grava", action="store_true")
    a = ap.parse_args()
    o = agrega(pl.read_csv(a.de) if a.de else extrai())
    print(o)
    if a.grava:
        o.write_csv(AQUI / "credito_destino.csv")


if __name__ == "__main__":
    main()
