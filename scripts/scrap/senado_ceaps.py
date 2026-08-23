#!/usr/bin/env python3
"""
CEAPS — Cota para o Exercício da Atividade Parlamentar dos Senadores.
Reembolsos de despesa por senador, com o CPF/CNPJ do fornecedor -> Parquet -> beelink.

Não confundir com `br_senado_dadosabertos`, que é outra coisa: aquele tem
senadores/comissoes/materias/votacoes, a atividade legislativa. Aqui é o gasto.

Fonte única:

    https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/despesas_ceaps/{ano}/csv

**Por que só ela.** Existe também o portal antigo de transparência
(`senado.leg.br/transparencia/LAI/verba/{ano}.csv`, latin-1, com uma linha de
preâmbulo antes do cabeçalho), e a versão anterior deste scraper usava ele para
2008-2021 e a API só de 2022 em diante. Isso estava errado: a API nova serve a
série inteira desde 2008, e serve MAIS linha que o portal em todo ano conferido
— 2012: 43.403 contra 30.180; 2021: 16.916 contra 1.100, porque o portal antigo
congelou em 2021-03-04 e nunca recebeu o resto do ano. Usar o portal para os anos
antigos importaria um 2021 truncado sem sintoma nenhum. Conferido em 2026-08-23.

Tipagem: `valor_reembolsado` vem com vírgula decimal ("122,62") e `data` em ISO.
Ambos são convertidos — deixar como string é o erro que encheu o espelho de
BYTE_ARRAY em 2026-07-05. `cpf_cnpj_fornecedor` fica **como veio**, com pontuação
("05.914.650/0001-66"), porque é o dado de origem; para juntar com
`br_me_cnpj.empresas` tire os separadores e complete com zero à esquerda.

Sem auth, sem WAF. ~20k linhas/ano.

Usage:
    python3 scripts/scrap/senado_ceaps.py                      # 2008 -> ano atual
    python3 scripts/scrap/senado_ceaps.py --ano-inicial 2024
    python3 scripts/scrap/senado_ceaps.py --sem-push           # não manda pro beelink
"""

import argparse
import io
import ssl
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import polars as pl

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_senado_ceaps/despesas"

URL = ("https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/"
       "despesas_ceaps/{ano}/csv")
ANO_INICIAL = 2008

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
TIMEOUT = 120
TEMP_DIR = Path(tempfile.gettempdir()) / "senado_ceaps"

# nome final -> nome no CSV de origem
COLUNAS = {
    "ano":                 "ANO",
    "mes":                 "MES",           # vem como "MÊS"; o acento cai no rename
    "cod_senador":         "COD_SENADOR",
    "nome_senador":        "NOME_SENADOR",
    "tipo_despesa":        "TIPO_DESPESA",
    "cpf_cnpj_fornecedor": "CPF_CNPJ_FORNECEDOR",
    "nome_fornecedor":     "NOME_FORNECEDOR",
    "documento":           "DOCUMENTO",
    "data":                "DATA",
    "detalhamento":        "DETALHAMENTO",
    "valor_reembolsado":   "VALOR_REEMBOLSADO",
    "tipo_documento":      "TIPO_DOCUMENTO",
    "id_documento":        "ID",
}

TEXTO = ("cod_senador", "nome_senador", "tipo_despesa", "cpf_cnpj_fornecedor",
         "nome_fornecedor", "documento", "detalhamento", "tipo_documento",
         "id_documento")


def baixa(url: str, tentativas: int = 3) -> bytes | None:
    """GET com retry. O endpoint corta a conexão no meio da leitura de vez em
    quando (`ssl.SSLError: [SYS] unknown error`), o que não é erro de HTTP e não
    é permanente — só reaparece se a gente desistir na primeira."""
    req = Request(url, headers={"User-Agent": UA})
    for n in range(1, tentativas + 1):
        try:
            with urlopen(req, timeout=TIMEOUT) as r:
                return r.read()
        except HTTPError as e:
            if e.code == 404:          # ano que não existe: não adianta insistir
                print(f"  ! {url}: {e}", file=sys.stderr)
                return None
            erro = e
        except (URLError, TimeoutError, ssl.SSLError, OSError) as e:
            erro = e
        if n < tentativas:
            time.sleep(2 * n)
        else:
            print(f"  ! {url}: {erro} (após {tentativas} tentativas)",
                  file=sys.stderr)
    return None


def le_ano(ano: int) -> pl.DataFrame | None:
    """Um ano de CEAPS, já com os nomes finais e tudo ainda como string."""
    bruto = baixa(URL.format(ano=ano))
    if not bruto:
        return None

    try:
        df = pl.read_csv(
            io.StringIO(bruto.decode("utf-8", errors="replace")),
            separator=";",
            infer_schema_length=0,   # tudo string; a conversão é explícita depois
            truncate_ragged_lines=True,
        )
    except Exception as e:
        print(f"  ! {ano}: falha ao parsear: {e}", file=sys.stderr)
        return None

    # o cabeçalho traz "MÊS" com acento
    df = df.rename({c: c.strip().upper().replace("Ê", "E") for c in df.columns})

    faltando = [o for o in COLUNAS.values() if o not in df.columns]
    if faltando:
        print(f"  ! {ano}: colunas ausentes na origem: {faltando}", file=sys.stderr)
        return None

    return df.select(
        [pl.col(origem).alias(final) for final, origem in COLUNAS.items()]
    )


def tipa(df: pl.DataFrame) -> pl.DataFrame:
    """String -> tipo. Vazio vira nulo; nada aqui pode virar 0 por acidente."""
    def limpo(col: str) -> pl.Expr:
        return pl.col(col).cast(pl.String).str.strip_chars().replace({"": None})

    return df.with_columns(
        limpo("ano").cast(pl.Int32, strict=False).alias("ano"),
        limpo("mes").cast(pl.Int8, strict=False).alias("mes"),
        limpo("data").str.to_date("%Y-%m-%d", strict=False).alias("data"),
        # vírgula decimal, e às vezes ponto de milhar
        limpo("valor_reembolsado")
        .str.replace_all(r"\.", "")
        .str.replace(",", ".")
        .cast(pl.Float64, strict=False)
        .alias("valor_reembolsado"),
        *[limpo(c).alias(c) for c in TEXTO],
    )


def push(parquet: Path) -> bool:
    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'",
                   shell=True, check=True)
    r = subprocess.run(
        f"rsync -av {parquet} {BEELINK_HOST}:{BEELINK_PATH}/{parquet.name}",
        shell=True,
    )
    if r.returncode != 0:
        print("rsync falhou", file=sys.stderr)
        return False
    print(f"  -> {BEELINK_HOST}:{BEELINK_PATH}/{parquet.name}")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ano-inicial", type=int, default=ANO_INICIAL)
    ap.add_argument("--ano-final", type=int, default=datetime.now().year)
    ap.add_argument("--sem-push", action="store_true")
    args = ap.parse_args()

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    partes = []
    for ano in range(args.ano_inicial, args.ano_final + 1):
        df = le_ano(ano)
        if df is None or df.height == 0:
            print(f"  {ano}: sem dados")
            continue
        print(f"  {ano}: {df.height} linhas")
        partes.append(df)

    if not partes:
        print("Nenhum ano baixado.", file=sys.stderr)
        return 1

    df = tipa(pl.concat(partes, how="vertical")).sort("ano", "mes")

    # valor e data são o motivo de existir da tabela; se vierem majoritariamente
    # nulos alguma coisa mudou no formato de origem e é melhor gritar que publicar
    for col in ("valor_reembolsado", "data"):
        nulos = df[col].null_count()
        if nulos > df.height * 0.05:
            print(f"{col}: {nulos}/{df.height} nulos — formato de origem mudou?",
                  file=sys.stderr)
            return 1

    parquet = TEMP_DIR / "despesas.parquet"
    df.write_parquet(parquet, compression="zstd")
    print(f"\n{df.height} linhas, {parquet.stat().st_size / 1e6:.2f} MB, "
          f"{df['ano'].min()}-{df['ano'].max()}")
    print(f"  valor nulo: {df['valor_reembolsado'].null_count()}, "
          f"data nula: {df['data'].null_count()}")

    if args.sem_push:
        print(f"--sem-push: parou em {parquet}")
        return 0
    if not push(parquet):
        return 1
    print("\nagora rode: python3 scripts/repara_views_beelink.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
