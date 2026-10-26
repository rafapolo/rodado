#!/usr/bin/env python3
"""br_mte_listasuja.empregadores_municipio: a Lista Suja com o município da ação fiscal.

    python3 scripts/sync/listasuja_municipio.py     # depois de cada coleta do mte_listasuja.py

O MTE não publica código de município, só o texto `estabelecimento` ("FAZENDA JATOBÁ, ZONA
RURAL, BARROLÂNDIA/TO"). As regras de casamento estão no listasuja_municipio.sql, ao lado. Uma
linha por caso (documento × estabelecimento × ano da ação fiscal), sem a repetição dos retratos
do histórico. Roda no beelink em -readonly (o COPY grava o parquet direto no espelho) e, na
primeira vez, cria a view com cria_views_novas.py.
"""
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).parent
DESTINO = "/home/polo/rodado/br_mte_listasuja/empregadores_municipio"
CONFERE = """
SELECT count(*) casos, sum(trabalhadores_envolvidos) trabalhadores, count(id_municipio) com_municipio,
       count(*) FILTER (left(cnae, 2) IN ('01', '02', '03')) campo,
       count(*) FILTER (left(cnae, 2) IN ('01', '02', '03') AND id_municipio IS NULL) campo_sem_municipio,
       count(*) FILTER (id_municipio_cnpj <> id_municipio) cnpj_diverge
FROM r;
"""


def main():
    sql = (AQUI / "listasuja_municipio.sql").read_text()
    corpo = (f"SET enable_progress_bar=false;\n{sql}\n"
             f"COPY (SELECT * FROM r ORDER BY ano_acao_fiscal, id_municipio, cpf_cnpj, estabelecimento) "
             f"TO '{DESTINO}/empregadores_municipio.parquet' (FORMAT parquet, COMPRESSION zstd);\n{CONFERE}")
    r = subprocess.run(["ssh", "beelink", f"mkdir -p {DESTINO} && ~/bin/duckdb -readonly -csv ~/rodado/basedosdados.duckdb"],
                       input=corpo, capture_output=True, text=True)
    if r.returncode or "Error" in r.stderr + r.stdout:
        sys.exit(r.stdout[-2000:] + r.stderr[-2000:])
    print(r.stdout.strip())
    lista = Path("/tmp/listasuja_view.txt")
    lista.write_text("br_mte_listasuja/empregadores_municipio\n")
    subprocess.run([sys.executable, str(AQUI / "cria_views_novas.py"), str(lista)], check=True)


if __name__ == "__main__":
    main()
