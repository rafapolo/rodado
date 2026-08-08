#!/usr/bin/env python3
"""Carga incremental do registro de candidaturas de 2026 — TSE dados abertos.

O ciclo de 2026 ainda está aberto: o prazo de registro se encerra em 15/08/2026
e o TSE republica os arquivos `consulta_cand_2026` e `bem_candidato_2026`
algumas vezes por dia, sempre completos, com todas as candidaturas protocoladas
até aquele instante. Este script roda quantas vezes for preciso até o prazo
fechar: a cada execução ele baixa o retrato mais recente, conforma ao schema da
Base dos Dados e substitui o arquivo do ano no espelho — full refresh de um ano
só, que é o que o formato do TSE permite.

Onde o dado cai
---------------
  ~/rodado/br_tse_eleicoes/candidatos/2026_tse_cdn.parquet
  ~/rodado/br_tse_eleicoes/bens_candidato/2026_tse_cdn.parquet
  ~/rodado/br_tse_eleicoes/carga_2026/snapshot_<data>.parquet

Os dois primeiros entram nas mesmas pastas do espelho da Base dos Dados e com o
mesmo schema, coluna por coluna. Isso é de propósito: todo consumidor já lê
`~/rodado/br_tse_eleicoes/candidatos/*.parquet`, e o `prepara_db_beelink.py`
monta as views por glob de pasta — ninguém precisa saber que 2026 veio por
outro caminho, basta filtrar `ano=2026`. O sufixo `_tse_cdn` no nome marca a
procedência e mantém o arquivo fora da faixa de nomes que os scripts de sync da
Base dos Dados usam (`000000000000.parquet`), para que um não sobrescreva o
outro. Quando a Base dos Dados publicar 2026, o script se recusa a rodar — ver
"Trava" abaixo.

`carga_2026` é a terceira tabela e não existe no espelho: um snapshot por
execução, com quantas candidaturas e quantos bens já estavam registrados
naquele momento. É o que permite ler a curva de protocolo até o prazo — e saber,
depois, quão incompleto estava o dado quando cada análise foi gerada.

Trava
-----
Antes de instalar, o script conta linhas de `ano=2026` nos arquivos numerados da
Base dos Dados. Se aparecer alguma, o espelho passou a trazer 2026 por conta
própria e continuar escrevendo aqui duplicaria o ano: o script aborta e pede a
remoção manual dos `2026_tse_cdn.parquet`.

Por que roda no beelink
-----------------------
`cdn.tse.jus.br` responde 403 para requisição saída daqui; do beelink, responde
200. Download, conversão e validação acontecem todos lá, por SSH — este script
é o driver.

Uso:
  python3 scripts/scrap/tse_eleicoes_2026.py            # só baixa se mudou na origem
  python3 scripts/scrap/tse_eleicoes_2026.py --force    # baixa de novo mesmo sem mudança
  python3 scripts/scrap/tse_eleicoes_2026.py --sem-instalar  # valida e não publica
"""
import argparse
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime

ANSI = re.compile(r"\x1b\[[0-9;]*m")

BEELINK_HOST = os.environ.get("BEELINK_HOST", "beelink")

DATASET_PATH = "~/rodado/br_tse_eleicoes"
# literal, não f-string: o sync_scraped_datasets.py descobre pipeline por regex
# no código-fonte e só reconhece BEELINK_PATH atribuído a uma string crua
BEELINK_PATH = "~/rodado/br_tse_eleicoes/candidatos"
PATH_BENS = f"{DATASET_PATH}/bens_candidato"
PATH_CARGA = f"{DATASET_PATH}/carga_2026"

ARQUIVO = "2026_tse_cdn.parquet"
TMP = "/tmp/tse2026"
MARCA = f"{PATH_CARGA}/.cdn_last_modified"

ANO = 2026
BASE_COMPARACAO = 2022          # ciclo geral anterior, para medir a cobertura
URL = "https://cdn.tse.jus.br/estatistica/sead/odsele/{f}/{f}_2026.zip"
ARQUIVOS = ("consulta_cand", "bem_candidato")

# Uma queda de mais de 5% no total de candidaturas entre duas execuções não é
# desistência em massa, é download truncado: o registro só cresce até o prazo.
QUEDA_MAX = 0.05


def remoto(script: str, check=True) -> str:
    """Roda bash no beelink e devolve o stdout."""
    res = subprocess.run(["ssh", BEELINK_HOST, "bash -s"],
                         input=script.encode(), capture_output=True, check=check)
    if res.stderr:
        sys.stderr.write(res.stderr.decode())
    return res.stdout.decode()


def duck(sql: str):
    """Roda SQL no DuckDB do beelink e devolve list[dict].

    SET enable_progress_bar=false é obrigatório: a barra de progresso sai no
    stdout e corrompe o JSON.
    """
    res = subprocess.run(["ssh", BEELINK_HOST, "~/bin/duckdb -json"],
                         input=("SET enable_progress_bar=false;\n" + sql).encode(),
                         capture_output=True, check=True)
    # o .duckdbrc do beelink imprime um aviso com escapes ANSI antes do JSON, e
    # COPY não devolve linha nenhuma — daí procurar a primeira linha que começa
    # o array em vez de confiar no início do stdout.
    linhas = ANSI.sub("", res.stdout.decode()).splitlines()
    for i, l in enumerate(linhas):
        if l.lstrip().startswith("["):
            return json.loads("\n".join(linhas[i:]))
    return []


# ── conformação ao schema da Base dos Dados ──────────────────────────────────
# O CSV do TSE vem em caixa alta e com sentinelas próprias ('#NULO#', '#NE'); a
# Base dos Dados guarda categoria em minúscula sem acento, nome em capitulares e
# ausência como NULL. As macros abaixo fazem essa tradução uma vez só.
MACROS = """
CREATE OR REPLACE MACRO lp(x) AS
  nullif(nullif(nullif(nullif(trim(x), ''), '#NULO#'), '#NE'), '#NE#');
CREATE OR REPLACE MACRO cat(x) AS strip_accents(lower(lp(x)));
CREATE OR REPLACE MACRO dt(x) AS try_strptime(lp(x), '%d/%m/%Y')::DATE;
CREATE OR REPLACE MACRO titulo(x) AS
  array_to_string(list_transform(string_split(lower(lp(x)), ' '),
    w -> CASE WHEN length(w) = 0 THEN w ELSE upper(w[1]) || w[2:] END), ' ');
"""

LER_CAND = (f"read_csv('{TMP}/consulta_cand_2026_BRASIL.csv', delim=';', "
            "header=true, encoding='latin-1', all_varchar=true, ignore_errors=true)")
LER_BENS = (f"read_csv('{TMP}/bem_candidato_2026_BRASIL.csv', delim=';', "
            "header=true, encoding='latin-1', all_varchar=true, ignore_errors=true)")

# id_municipio fica NULL: 2026 é eleição geral, a unidade eleitoral é a UF (ou
# 'BR'), não município. idade, nacionalidade, municipio_nascimento e email não
# existem no layout de 2026 do TSE — email a Base dos Dados também não preenche
# em ano nenhum, então sai NULL aqui pelo mesmo motivo.
SQL_CAND = f"""{MACROS}
COPY (
  SELECT
    CAST(ANO_ELEICAO AS BIGINT)                          AS ano,
    lp(CD_ELEICAO)                                       AS id_eleicao,
    cat(NM_TIPO_ELEICAO)                                 AS tipo_eleicao,
    dt(DT_ELEICAO)                                       AS data_eleicao,
    lp(SG_UF)                                            AS sigla_uf,
    CAST(NULL AS VARCHAR)                                AS id_municipio,
    CASE WHEN SG_UE SIMILAR TO '[0-9]+' THEN lp(SG_UE) END AS id_municipio_tse,
    lp(NR_TITULO_ELEITORAL_CANDIDATO)                    AS titulo_eleitoral,
    lp(NR_CPF_CANDIDATO)                                 AS cpf,
    lp(SQ_CANDIDATO)                                     AS sequencial,
    lp(NR_CANDIDATO)                                     AS numero,
    titulo(NM_CANDIDATO)                                 AS nome,
    titulo(NM_URNA_CANDIDATO)                            AS nome_urna,
    lp(NR_PARTIDO)                                       AS numero_partido,
    lp(SG_PARTIDO)                                       AS sigla_partido,
    cat(DS_CARGO)                                        AS cargo,
    cat(DS_SITUACAO_CANDIDATURA)                         AS situacao,
    dt(DT_NASCIMENTO)                                    AS data_nascimento,
    CAST(NULL AS BIGINT)                                 AS idade,
    cat(DS_GENERO)                                       AS genero,
    cat(DS_GRAU_INSTRUCAO)                               AS instrucao,
    cat(DS_OCUPACAO)                                     AS ocupacao,
    cat(DS_ESTADO_CIVIL)                                 AS estado_civil,
    CAST(NULL AS VARCHAR)                                AS nacionalidade,
    lp(SG_UF_NASCIMENTO)                                 AS sigla_uf_nascimento,
    CAST(NULL AS VARCHAR)                                AS municipio_nascimento,
    CAST(NULL AS VARCHAR)                                AS email,
    cat(DS_COR_RACA)                                     AS raca
  FROM {LER_CAND}
  WHERE ANO_ELEICAO = '{ANO}'
  -- o arquivo traz uma linha por turno; a tabela da Base dos Dados tem uma por
  -- candidatura, e antes da eleição só existe o 1º turno de qualquer forma
  QUALIFY row_number() OVER (PARTITION BY SQ_CANDIDATO ORDER BY NR_TURNO) = 1
) TO '{TMP}/candidatos.parquet' (FORMAT parquet, COMPRESSION zstd);
"""

# O arquivo de bens não traz título eleitoral; vem do de candidaturas pelo
# sequencial, que é a chave que liga os dois.
SQL_BENS = f"""{MACROS}
COPY (
  WITH tit AS (
    SELECT lp(SQ_CANDIDATO) AS sq, any_value(lp(NR_TITULO_ELEITORAL_CANDIDATO)) AS titulo
    FROM {LER_CAND} WHERE ANO_ELEICAO = '{ANO}' GROUP BY 1
  )
  SELECT
    CAST(b.ANO_ELEICAO AS BIGINT)                        AS ano,
    lp(b.SG_UF)                                          AS sigla_uf,
    lp(b.CD_ELEICAO)                                     AS id_eleicao,
    cat(b.NM_TIPO_ELEICAO)                               AS tipo_eleicao,
    dt(b.DT_ELEICAO)                                     AS data_eleicao,
    tit.titulo                                           AS titulo_eleitoral_candidato,
    lp(b.SQ_CANDIDATO)                                   AS sequencial_candidato,
    lp(b.DS_TIPO_BEM_CANDIDATO)                          AS tipo_item,
    lp(b.DS_BEM_CANDIDATO)                               AS descricao_item,
    CAST(replace(lp(b.VR_BEM_CANDIDATO), ',', '.') AS DOUBLE) AS valor_item
  FROM {LER_BENS} b
  LEFT JOIN tit ON tit.sq = lp(b.SQ_CANDIDATO)
  WHERE b.ANO_ELEICAO = '{ANO}'
) TO '{TMP}/bens_candidato.parquet' (FORMAT parquet, COMPRESSION zstd);
"""

SQL_VALIDA = f"""
SELECT
  (SELECT count(*) FROM read_parquet('{TMP}/candidatos.parquet'))                    AS cand,
  (SELECT count(DISTINCT sequencial) FROM read_parquet('{TMP}/candidatos.parquet'))  AS cand_seq,
  (SELECT count(*) FROM read_parquet('{TMP}/candidatos.parquet')
     WHERE cpf IS NULL OR length(cpf) <> 11)                                         AS cpf_ruim,
  (SELECT count(*) FROM read_parquet('{TMP}/candidatos.parquet') WHERE ano <> {ANO}) AS ano_ruim,
  (SELECT count(DISTINCT cargo) FROM read_parquet('{TMP}/candidatos.parquet'))       AS cargos,
  (SELECT count(*) FROM read_parquet('{TMP}/bens_candidato.parquet'))                AS bens,
  (SELECT count(DISTINCT sequencial_candidato) FROM read_parquet('{TMP}/bens_candidato.parquet')) AS bens_seq,
  (SELECT count(*) FROM read_parquet('{TMP}/bens_candidato.parquet') WHERE valor_item IS NULL)    AS valor_nulo,
  (SELECT max(valor_item) FROM read_parquet('{TMP}/bens_candidato.parquet'))         AS valor_max,
  (SELECT sum(valor_item) FROM read_parquet('{TMP}/bens_candidato.parquet'))         AS valor_total,
  (SELECT max(data_eleicao)::VARCHAR FROM read_parquet('{TMP}/candidatos.parquet'))  AS data_eleicao;
"""

# Só os arquivos numerados, que são os do espelho da Base dos Dados — o nosso
# fica de fora do glob de propósito.
SQL_TRAVA = f"""
SELECT count(*) AS ja_no_espelho
FROM read_parquet('{DATASET_PATH}/candidatos/0*.parquet') WHERE ano = {ANO};
"""


def sql_snapshot(quando: str) -> str:
    """Uma linha por cargo com o retrato de agora, mais a régua do ciclo anterior.

    Lê os arquivos já publicados, não os de /tmp: roda depois do mv, e assim o
    snapshot descreve exatamente o que ficou no espelho.
    """
    return f"""
COPY (
  -- os bens são agregados por candidatura ANTES do join: juntar item a item e
  -- contar depois multiplicaria cada candidatura pelo número de bens dela
  WITH bens AS (
    SELECT sequencial_candidato AS sq, count(*) AS itens,
           sum(valor_item) AS valor
    FROM read_parquet('{PATH_BENS}/{ARQUIVO}') GROUP BY 1
  ),
  agora AS (
    SELECT c.cargo, count(*) AS candidaturas,
           count(b.sq) AS com_declaracao,
           CAST(COALESCE(sum(b.itens), 0) AS BIGINT) AS itens,
           COALESCE(sum(b.valor), 0) AS valor_total
    FROM read_parquet('{BEELINK_PATH}/{ARQUIVO}') c
    LEFT JOIN bens b ON b.sq = c.sequencial
    GROUP BY 1
  ),
  antes AS (
    SELECT cargo, count(*) AS candidaturas
    FROM read_parquet('{DATASET_PATH}/candidatos/*.parquet')
    WHERE ano = {BASE_COMPARACAO} GROUP BY 1
  )
  SELECT TIMESTAMP '{quando}' AS run_at,
         DATE '{date.today().isoformat()}' AS data,
         a.cargo, a.candidaturas, a.com_declaracao, a.itens, a.valor_total,
         antes.candidaturas AS candidaturas_{BASE_COMPARACAO},
         CASE WHEN antes.candidaturas > 0
              THEN a.candidaturas::DOUBLE / antes.candidaturas END AS cobertura
  FROM agora a LEFT JOIN antes USING (cargo)
  ORDER BY a.candidaturas DESC
) TO '{PATH_CARGA}/snapshot_{date.today().isoformat()}.parquet'
  (FORMAT parquet, COMPRESSION zstd);
"""


BAIXA = f"""
set -euo pipefail
mkdir -p {TMP} {PATH_CARGA}
cd {TMP}
for f in {' '.join(ARQUIVOS)}; do
  curl -sSf --retry 3 --retry-delay 5 -o $f.zip \\
    "https://cdn.tse.jus.br/estatistica/sead/odsele/$f/${{f}}_2026.zip"
  unzip -o -q $f.zip
done
stat -c '%n %s' {TMP}/consulta_cand_2026_BRASIL.csv {TMP}/bem_candidato_2026_BRASIL.csv
"""


def cdn_last_modified() -> str:
    """Assinatura da origem: Last-Modified dos dois arquivos, concatenado."""
    script = "\n".join(
        f'curl -sSI "{URL.format(f=f)}" | tr -d "\\r" | '
        'awk -F": " "/^[Ll]ast-[Mm]odified/{print \\$2}"' for f in ARQUIVOS)
    return remoto(script).strip().replace("\n", " | ")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true",
                    help="rebaixa e reinstala mesmo se a origem não mudou")
    ap.add_argument("--sem-instalar", action="store_true",
                    help="baixa, converte e valida, mas não publica no espelho")
    args = ap.parse_args()

    agora = datetime.now().replace(microsecond=0).isoformat(sep=" ")

    # ── 1. a origem mudou? ───────────────────────────────────────────────────
    assinatura = cdn_last_modified()
    anterior = remoto(f"cat {MARCA} 2>/dev/null || true", check=False).strip()
    print(f"origem : {assinatura}", file=sys.stderr)
    if assinatura and assinatura == anterior and not args.force:
        print("sem novidade no TSE desde a última carga — nada a fazer",
              file=sys.stderr)
        return

    # ── 2. a Base dos Dados publicou 2026? ───────────────────────────────────
    ja = duck(SQL_TRAVA)[0]["ja_no_espelho"]
    if ja:
        sys.exit(f"abortado: o espelho da Base dos Dados já traz {ja} linhas de "
                 f"{ANO} em candidatos. Remova os {ARQUIVO} das pastas "
                 f"candidatos/ e bens_candidato/ antes de rodar de novo.")

    # ── 3. baixa ─────────────────────────────────────────────────────────────
    print("baixando do cdn.tse.jus.br…", file=sys.stderr)
    for linha in remoto(BAIXA).strip().splitlines():
        print(f"  {linha}", file=sys.stderr)

    # ── 4. converte ──────────────────────────────────────────────────────────
    print("conformando ao schema da Base dos Dados…", file=sys.stderr)
    duck(SQL_CAND)
    duck(SQL_BENS)

    # ── 5. valida ────────────────────────────────────────────────────────────
    v = duck(SQL_VALIDA)[0]
    print(f"  {v['cand']:,} candidaturas · {v['bens']:,} itens de bem · "
          f"R$ {v['valor_total']:,.0f} declarados".replace(",", "."),
          file=sys.stderr)

    erros = []
    if v["cand"] == 0 or v["bens"] == 0:
        erros.append("arquivo vazio")
    if v["cand"] != v["cand_seq"]:
        erros.append(f"sequencial repetido em candidatos "
                     f"({v['cand']} linhas, {v['cand_seq']} sequenciais)")
    if v["ano_ruim"]:
        erros.append(f"{v['ano_ruim']} linhas fora de {ANO}")
    if v["cpf_ruim"] > v["cand"] * 0.02:
        erros.append(f"{v['cpf_ruim']} CPFs fora do formato de 11 dígitos")
    if v["cargos"] < 5:
        erros.append(f"só {v['cargos']} cargos distintos — arquivo parcial?")
    if v["valor_nulo"]:
        erros.append(f"{v['valor_nulo']} valores de bem não converteram")

    # o registro só cresce até o prazo: encolher é sinal de download truncado.
    # read_parquet estoura se o glob não casa com nada, daí o ls antes.
    tem_snapshot = remoto(f"ls {PATH_CARGA}/snapshot_*.parquet 2>/dev/null | head -1",
                          check=False).strip()
    # o CAST não é decorativo: sum() de BIGINT vira HUGEINT e sai como string
    # no -json, o que faria a comparação estourar em vez de reprovar a carga
    ultimo = duck(f"SELECT CAST(sum(candidaturas) AS BIGINT) AS n FROM "
                  f"read_parquet('{PATH_CARGA}/snapshot_*.parquet') "
                  f"WHERE run_at = (SELECT max(run_at) FROM "
                  f"read_parquet('{PATH_CARGA}/snapshot_*.parquet'));"
                  ) if tem_snapshot else []
    if ultimo and ultimo[0]["n"]:
        antes = ultimo[0]["n"]
        if v["cand"] < antes * (1 - QUEDA_MAX):
            erros.append(f"queda de {antes:,} para {v['cand']:,} candidaturas "
                         f"— acima do tolerado de {QUEDA_MAX:.0%}")
        else:
            print(f"  eram {antes:,} na carga anterior".replace(",", "."),
                  file=sys.stderr)

    if erros:
        for e in erros:
            print(f"  ✗ {e}", file=sys.stderr)
        sys.exit("validação falhou — nada foi publicado")

    if args.sem_instalar:
        print(f"--sem-instalar: parquets ficaram em {TMP}/ e não foram publicados",
              file=sys.stderr)
        return

    # ── 6. publica (mv é atômico dentro do mesmo filesystem) ─────────────────
    remoto(f"""
set -euo pipefail
mkdir -p {PATH_CARGA}
mv {TMP}/candidatos.parquet {BEELINK_PATH}/{ARQUIVO}
mv {TMP}/bens_candidato.parquet {PATH_BENS}/{ARQUIVO}
""")
    duck(sql_snapshot(agora))
    remoto(f"printf '%s' {json.dumps(assinatura)} > {MARCA}")

    cob = duck(f"""
SELECT CAST(sum(candidaturas) AS BIGINT) AS n,
       CAST(sum(candidaturas_{BASE_COMPARACAO}) AS BIGINT) AS base
FROM read_parquet('{PATH_CARGA}/snapshot_{date.today().isoformat()}.parquet');""")[0]
    pct = 100 * cob["n"] / cob["base"] if cob["base"] else 0
    print(f"ok: {BEELINK_PATH}/{ARQUIVO} e {PATH_BENS}/{ARQUIVO} publicados · "
          f"{pct:.1f}% do total de {BASE_COMPARACAO}", file=sys.stderr)


if __name__ == "__main__":
    main()
