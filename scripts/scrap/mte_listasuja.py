#!/usr/bin/env python3
"""
MTE — Lista Suja do Trabalho Escravo (Cadastro de Empregadores que tenham
submetido trabalhadores a condições análogas à de escravo) e o CEAC (Cadastro
de Empregadores em Ajustamento de Conduta) -> Parquet -> beelink.

Fonte: página "Combate ao trabalho escravo e análogo ao de escravo" da
Inspeção do Trabalho no gov.br/MTE. Ela linka o cadastro corrente em
`areas-de-atuacao/cadastro_de_empregadores.{csv,pdf,txt,xlsx}` e o CEAC
corrente em `areas-de-atuacao/cadastro-de-empregadores-em-ajustamento-de-conduta/AAAA_NNNN.*`.

Os dois CSVs vêm em **cp1252** (não latin-1 puro: há travessão 0x96 e
apóstrofo 0x92), `;`, CRLF, sem CRLF na última linha. CPF e CNPJ vêm completos
e formatados (`000.000.000-00`, `00.000.000/0000-00`), sem máscara.

O CSV do cadastro não traz nem a data de atualização nem as notas de rodapé
(`(*1)` etc., inclusão por ordem judicial); o `.txt` traz as duas, e é lido só
para isso.

Tabelas (~/rodado/br_mte_listasuja/<tabela>/):
  - empregadores            o cadastro corrente (um parquet, sobrescrito)
  - empregadores_historico  o mesmo cadastro, um parquet por data de
                            atualização (`cadastro_AAAA-MM-DD.parquet`). O MTE
                            não publica versões antigas: a série começa na
                            primeira rodada deste script e cresce a cada uma
  - ceac                    o CEAC corrente (a versão listada na página)
  - ceac_historico          todas as versões `AAAA_NNNN.csv` ainda servidas.
                            A página só linka a corrente, mas as antigas
                            seguem no ar sem link: o script sonda os números.
                            Nas versões de 2025 (0001, 0004–0006) a fonte
                            põe as datas do CEAC na coluna "Inclusão no
                            Cadastro de Empregadores" e deixa "Inclusão no
                            CEAC" vazia; guardado como veio, então
                            `data_inclusao_ceac` fica nula nessas 9 linhas

Direto primeiro; se o gov.br der 403/timeout, cai para o proxy BR
(`_proxy_br.Pool`), sem sondar as versões antigas do CEAC (seriam dezenas de
requisições por proxy gratuito).

Uso:
    python3 scripts/scrap/mte_listasuja.py [TEMP_DIR]
"""

import datetime as dt
import io
import re
import subprocess
import sys
from pathlib import Path

import polars as pl
import requests

sys.path.insert(0, str(Path(__file__).parent))

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_mte_listasuja"
BASE = "https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/inspecao-do-trabalho/areas-de-atuacao"
PAGINA = f"{BASE}/combate-ao-trabalho-escravo-e-analogo-ao-de-escravo"
CEAC_DIR = f"{BASE}/cadastro-de-empregadores-em-ajustamento-de-conduta"
TEMP_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/mte_listasuja")
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
HOJE = dt.date.today()

_pool = None


def baixa(url: str, obrigatorio=True) -> bytes | None:
    """GET direto; se falhar, pelo proxy BR. 404 é resposta, não bloqueio."""
    global _pool
    if _pool is None:
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=60)
            if r.status_code == 404:
                return None
            if r.status_code < 400:
                return r.content
            print(f"  direto {r.status_code} em {url}; tentando proxy BR", flush=True)
        except requests.RequestException as e:
            print(f"  direto {type(e).__name__} em {url}; tentando proxy BR", flush=True)
        from _proxy_br import Pool

        _pool = Pool(PAGINA)
    r = _pool.get(url)
    if r.status_code == 404 and not obrigatorio:
        return None
    r.raise_for_status()
    return r.content


def decodifica(b: bytes) -> str:
    try:
        return b.decode("cp1252")
    except UnicodeDecodeError:
        return b.decode("latin-1")


def digitos(col: str) -> pl.Expr:
    return pl.col(col).str.replace_all(r"\D", "")


def data(expr: pl.Expr) -> pl.Expr:
    return expr.str.strptime(pl.Date, "%d/%m/%Y", strict=True)


def documento(df: pl.DataFrame) -> pl.DataFrame:
    """CPF/CNPJ como texto só de dígitos, com zero à esquerda. Aborta se algum
    não tiver 11 nem 14 dígitos (máscara ou padding perdido na fonte)."""
    df = df.with_columns(digitos("CNPJ/CPF").alias("cpf_cnpj"))
    ruins = df.filter(~pl.col("cpf_cnpj").str.len_chars().is_in([11, 14]))
    if ruins.height:
        raise SystemExit(f"CPF/CNPJ fora de 11/14 dígitos: {ruins['CNPJ/CPF'].to_list()[:10]}")
    n = pl.col("cpf_cnpj").str.len_chars()
    return df.with_columns(
        pl.when(n == 14).then(pl.lit("CNPJ")).otherwise(pl.lit("CPF")).alias("tipo_documento"),
        pl.when(n == 14).then(pl.col("cpf_cnpj")).alias("cnpj"),
        pl.when(n == 14).then(pl.col("cpf_cnpj").str.slice(0, 8)).alias("cnpj_basico"),
        pl.when(n == 11).then(pl.col("cpf_cnpj")).alias("cpf"),
    )


def le_csv(texto: str) -> pl.DataFrame:
    return pl.read_csv(io.StringIO(texto), separator=";", infer_schema=False)


# ---------------------------------------------------------------- cadastro

def cabecalho_txt(txt: str) -> tuple[dt.date, dict[str, str]]:
    """Do .txt: 'Cadastro atualizado em DD/MM/AAAA' e as notas '(*n) ...'."""
    m = re.search(r"Cadastro atualizado em (\d{2}/\d{2}/\d{4})", txt)
    if not m:
        raise SystemExit("data de atualização não achada no .txt do cadastro")
    atualizado = dt.datetime.strptime(m.group(1), "%d/%m/%Y").date()
    notas = {}
    for linha in txt.splitlines():
        linha = linha.strip()
        m = re.match(r"^((?:\(\*\d+\)[,\s]*)+)(.+)$", linha)
        if m:
            for k in re.findall(r"\*\d+", m.group(1)):
                notas[k] = m.group(2).strip()
    return atualizado, notas


def cadastro(csv_txt: str, atualizado: dt.date, notas: dict[str, str]) -> pl.DataFrame:
    df = documento(le_csv(csv_txt))
    inc = "Inclusão no Cadastro de Empregadores"
    # "05/04/2024 a 10/05/2024, 09/04/2025": saiu (liminar) e voltou; a última
    # data é a inclusão vigente, a primeira é a entrada original
    datas_inc = pl.col(inc).str.extract_all(r"\d{2}/\d{2}/\d{4}")
    marca = pl.col("Empregador").str.extract(r"\((\*\d+)\)\s*$")
    df = df.with_columns(
        pl.col("ID").cast(pl.Int32).alias("id"),
        pl.col("Ano da ação fiscal").cast(pl.Int16).alias("ano_acao_fiscal"),
        pl.col("UF").alias("sigla_uf"),
        pl.col("Empregador").str.replace(r"\s*\(\*\d+\)\s*$", "").alias("empregador"),
        pl.col("Estabelecimento").alias("estabelecimento"),
        pl.col("Trabalhadores envolvidos").cast(pl.Int32).alias("trabalhadores_envolvidos"),
        pl.col("CNAE").alias("cnae"),
        digitos("CNAE").alias("cnae_subclasse"),
        data(pl.col("Decisão administrativa de procedência")).alias("data_decisao_procedencia"),
        pl.col(inc).alias("periodos_inclusao"),
        data(datas_inc.list.first()).alias("data_primeira_inclusao"),
        data(datas_inc.list.last()).alias("data_inclusao"),
        (datas_inc.list.len() > 1).alias("reincluido"),
        marca.replace_strict(notas, default=None).alias("nota"),
        pl.lit(atualizado).alias("data_atualizacao_cadastro"),
        pl.lit(HOJE).alias("data_coleta"),
    )
    faltou = df.filter(marca.is_not_null() & pl.col("nota").is_null())
    if faltou.height:
        raise SystemExit(f"nota de rodapé sem texto: {faltou['Empregador'].to_list()}")
    return df.select(
        "id", "ano_acao_fiscal", "sigla_uf", "empregador", "tipo_documento", "cpf_cnpj",
        "cnpj", "cnpj_basico", "cpf", "estabelecimento", "trabalhadores_envolvidos", "cnae",
        "cnae_subclasse", "data_decisao_procedencia", "periodos_inclusao",
        "data_primeira_inclusao", "data_inclusao", "reincluido", "nota",
        "data_atualizacao_cadastro", "data_coleta",
    )


# ---------------------------------------------------------------- CEAC

def ceac(csv_txt: str, versao: str) -> pl.DataFrame:
    df = documento(le_csv(csv_txt))
    cad, cc = "Inclusão no Cadastro de Empregadores", "Inclusão no CEAC"
    # "26/05/2025 07/04/2026", "16/04/2026 a 21/05/2026, 14/08/2026": vários
    # períodos, separador inconsistente; a última data é a entrada vigente
    d_cc = pl.col(cc).str.extract_all(r"\d{2}/\d{2}/\d{4}")
    return df.with_columns(
        pl.col("ID").cast(pl.Int32).alias("id"),
        pl.col("Ano da ação fiscal").cast(pl.Int16).alias("ano_acao_fiscal"),
        pl.col("UF").alias("sigla_uf"),
        pl.col("Empregador").alias("empregador"),
        pl.col("Estabelecimento").alias("estabelecimento"),
        pl.col(cad).alias("periodos_cadastro_empregadores"),
        pl.col(cc).alias("periodos_ceac"),
        data(d_cc.list.first()).alias("data_primeira_inclusao_ceac"),
        data(d_cc.list.last()).alias("data_inclusao_ceac"),
        pl.col("Termo de Ajustamento de Conduta MTE").alias("termo_ajustamento_conduta"),
        pl.lit(versao).alias("versao"),
        pl.lit(HOJE).alias("data_coleta"),
    ).select(
        "versao", "id", "ano_acao_fiscal", "sigla_uf", "empregador", "tipo_documento",
        "cpf_cnpj", "cnpj", "cnpj_basico", "cpf", "estabelecimento",
        "periodos_cadastro_empregadores", "periodos_ceac", "data_primeira_inclusao_ceac",
        "data_inclusao_ceac", "termo_ajustamento_conduta", "data_coleta",
    )


def versoes_ceac(pagina: str) -> tuple[str, list[str]]:
    """A corrente vem do link da página; as antigas, por sondagem de
    AAAA_0001..AAAA_0040 (só em acesso direto)."""
    listadas = sorted(set(re.findall(r"ajustamento-de-conduta/(\d{4}_\d{4})\.csv", pagina)))
    if not listadas:
        raise SystemExit("nenhum CSV do CEAC linkado na página")
    corrente = listadas[-1]
    todas = set(listadas)
    if _pool is None:
        for ano in range(2025, HOJE.year + 1):
            for n in range(1, 41):
                v = f"{ano}_{n:04d}"
                if v in todas:
                    continue
                # HEAD leva 403 do gov.br; GET em stream, fechado sem ler o corpo
                try:
                    with requests.get(f"{CEAC_DIR}/{v}.csv", headers={"User-Agent": UA},
                                      timeout=20, stream=True) as r:
                        ok = r.status_code == 200 and "csv" in r.headers.get("content-type", "")
                except requests.RequestException:
                    continue
                if ok:
                    todas.add(v)
    return corrente, sorted(todas)


# ---------------------------------------------------------------- main

def grava(df: pl.DataFrame, tabela: str, nome: str) -> Path:
    d = TEMP_DIR / "out" / tabela
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{nome}.parquet"
    df.write_parquet(p, compression="zstd")
    return p


def main():
    raw = TEMP_DIR / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    pagina = baixa(PAGINA).decode("utf-8", errors="replace")
    link = f"{BASE}/cadastro_de_empregadores.csv"
    if link not in pagina:
        print(f"  aviso: a página não linka mais {link}; tentando mesmo assim")

    b_csv = baixa(link)
    b_txt = baixa(f"{BASE}/cadastro_de_empregadores.txt")
    (raw / "cadastro_de_empregadores.csv").write_bytes(b_csv)
    (raw / "cadastro_de_empregadores.txt").write_bytes(b_txt)
    csv_txt = decodifica(b_csv)
    atualizado, notas = cabecalho_txt(decodifica(b_txt))
    emp = cadastro(csv_txt, atualizado, notas)

    registros = len([l for l in csv_txt.splitlines() if l.strip()]) - 1
    if emp.height != registros:
        raise SystemExit(f"cadastro: {emp.height} linhas lidas, {registros} no CSV")
    grava(emp, "empregadores", "empregadores")
    grava(emp, "empregadores_historico", f"cadastro_{atualizado.isoformat()}")
    print(f"  ✓ empregadores: {emp.height} linhas (atualizado em {atualizado}, "
          f"{emp['cnpj'].is_not_null().sum()} CNPJ, {emp['cpf'].is_not_null().sum()} CPF)")

    corrente, versoes = versoes_ceac(pagina)
    hist = []
    for v in versoes:
        b = baixa(f"{CEAC_DIR}/{v}.csv", obrigatorio=False)
        if b is None:
            continue
        (raw / f"ceac_{v}.csv").write_bytes(b)
        df = ceac(decodifica(b), v)
        grava(df, "ceac_historico", v)
        hist.append(df)
        if v == corrente:
            grava(df, "ceac", "ceac")
        print(f"  ✓ ceac {v}: {df.height} linhas{' (corrente)' if v == corrente else ''}")

    for tabela in ["empregadores", "empregadores_historico", "ceac", "ceac_historico"]:
        remote = f"{DATASET_PATH}/{tabela}"
        subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p {remote}"], check=True)
        # sem --delete: o histórico acumula entre rodadas
        subprocess.run(["rsync", "-a", f"{TEMP_DIR}/out/{tabela}/", f"{BEELINK_HOST}:{remote}/"],
                       check=True)
        print(f"  ✓ push {tabela}")
    print(f"  proxy BR: {'sim' if _pool is not None else 'não'}; "
          f"ceac_historico: {sum(d.height for d in hist)} linhas em {len(hist)} versões")
    return 0


if __name__ == "__main__":
    sys.exit(main())
