#!/usr/bin/env python3
"""Mede quantos municípios cada dataset realmente cobre -> docs/context/cobertura_municipal.json.

O filtro F3/F4 de `tasks/hipoteses.md` (cobre ≥500 / ≥2.000 municípios) tinha
sido medido uma vez e nunca gravado, então nenhum script podia reusá-lo.

**Usa count(DISTINCT), nunca approx_count_distinct.** O HLL do DuckDB é
determinístico dado o mesmo conjunto de valores: ele devolveu `6859` idêntico
para 50 datasets diferentes, que é o conjunto dos 5.570 códigos IBGE estimado
com +23% de viés. Qualquer filtro de poder construído em cima disso está
inflado.

  python3 scripts/hipoteses/94_cobertura.py           # gera o SQL
  ssh beelink '~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb' \
      < /tmp/cobertura.sql > /tmp/cob.json            # roda (lento: ~20 min)
  python3 scripts/hipoteses/94_cobertura.py /tmp/cob.json   # grava o JSON
"""
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT  = REPO / "docs" / "context" / "cobertura_municipal.json"

if len(sys.argv) > 1:                      # modo 2: consolidar
    d = json.loads(Path(sys.argv[1]).read_text())
    res = {x["ds"]: {"tabela": x["tb"], "coluna": x["col"], "linhas": x["n_rows"],
                     "n_mun": x["n_mun"], "suspeito": x["n_mun"] > 5571} for x in d}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True))
    sus = [k for k, v in res.items() if v["suspeito"]]
    print(f"gravado {OUT} ({len(res)} datasets; {len(sus)} com n_mun > 5.571)")
    sys.exit()

schema = json.loads((REPO/"docs"/"context"/"basedosdados-schema.json").read_text())
# código IBGE direto > código de outro cadastro > nome em texto
COD = {"id_municipio","id_municipio_6","id_municipio_residencia","id_municipio_6_residencia",
       "id_municipio_nascimento","id_municipio_1","id_municipio_2","id_municipio_gasto",
       "id_municipio_agencia","cod_municipio","codigo_municipio","codigomunicipio",
       "municipiocodigo","COD_MUNICIPIO","ID_MUNICIP","COMUNINF"}
OUTRO = {"codigo_municipio_siafi","id_municipio_tse","id_municipio_rf","id_municipio_bcb"}
NOME  = {"municipio","nome_municipio","MUNICIPIO","municipionome","municipio_nascimento",
         "municipio_destino","ing_nm_municipio","municipio_s"}
RANK = {**{c:0 for c in COD}, **{c:1 for c in OUTRO}, **{c:2 for c in NOME}}
print("gere /tmp/meta.json e /tmp/schemas.json antes — ver docstring", file=sys.stderr)
