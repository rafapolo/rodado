#!/usr/bin/env python3
"""
SENATRAN (antigo DENATRAN) — frota de veículos por município e tipo, mensal.

Fonte: https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/
       frota-de-veiculos-<ano>  (uma página por ano, 2013 em diante)

Cada página lista ~100 planilhas por ano (CEP, cor, combustível, potência, ano
de fabricação, marca/modelo...). Este script pega só a de **município × tipo**,
a série que serve de denominador para taxa de acidente/veículo por município.
Os nomes de arquivo mudam de ano para ano (`frotamunic-jan-2013.zip`,
`frota_munic_modelo_marco_2020.xls`, `FrotaporMunicpioeTipoMAIO2024.xlsx`...),
então a seleção é por regex no nome e o mês sai do próprio nome.

Formatos: zip, rar (2015–2016), xls, xlsx, csv. O layout é largo — uma linha
por município, uma coluna por tipo — e o cabeçalho cai em linhas diferentes
conforme a época; o parser procura a linha que tem "UF" e "MUNIC".

Saída: ~/rodado/br_senatran_frota/municipio_tipo/ano=<a>/mes=<m>.parquet,
formato longo (sigla_uf, municipio, tipo_veiculo, quantidade). `municipio` é
o nome da planilha; `id_municipio` sai de um join por (UF, nome normalizado)
com `br_bd_diretorios_brasil.municipio`, feito na hora de escrever.

Uso:
    python3 scripts/scrap/senatran_frota.py download   # baixa tudo p/ TEMP_DIR
    python3 scripts/scrap/senatran_frota.py parse      # -> parquet em TEMP_DIR/out
    python3 scripts/scrap/senatran_frota.py push       # rsync ao beelink
"""

import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_senatran_frota"
TABLE = "municipio_tipo"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/senatran")
PAGE = "https://www.gov.br/transportes/pt-br/assuntos/transito/conteudo-Senatran/frota-de-veiculos-{ano}"
ANOS = range(2013, 2027)

MESES = {
    "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
    "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12,
}
# "Maro" é o "Março" que o Plone comeu o ç no slug
MES_RE = re.compile(r"(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)", re.I)
EXCLUI = re.compile(
    r"cep|_cor|cor_|combust|potenc|fab|especie|restri|marca|reg_?uf|reg-uf|uf_e_tipo|uf-e-tipo|porufe|demanda",
    re.I,
)


def fetch(url: str) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": UA}), timeout=120) as r:
        return r.read()


def links():
    """(ano, mes, url) de cada planilha município × tipo, uma por mês."""
    vistos = {}
    for ano in ANOS:
        html = fetch(PAGE.format(ano=ano)).decode("utf-8", "replace")
        for url in re.findall(r'href="([^"]+\.(?:xlsx?|zip|rar|csv))"', html, re.I):
            nome = url.rsplit("/", 1)[-1]
            if "munic" not in nome.lower() or EXCLUI.search(nome):
                continue
            m = MES_RE.search(re.sub(r"munic", "", nome, flags=re.I))
            if not m:
                print(f"  ? sem mês: {nome}")
                continue
            # a página de 2025 linka Frota_Munic_Modelo_Fevereiro_20241.xls
            # (o arquivo de fev/2024) ao lado do FrotaporMunicpioeTipoFevereiro2025
            # certo: o ano no nome, quando existe, manda sobre o da página
            anos_nome = re.findall(r"20\d\d", nome)
            if anos_nome and str(ano) not in anos_nome:
                print(f"  ? ano do nome ≠ {ano}: {nome}")
                continue
            mes = MESES[m.group(1).lower()]
            # csv e xlsx do mesmo mês (jul/2025): prefere a planilha
            chave = (ano, mes)
            # o link sem www (arquivos-denatran) dá 404; o www (arquivos-senatran) abre
            if chave in vistos and not vistos[chave].lower().endswith(".csv") \
                    and "://www." in vistos[chave]:
                continue
            vistos[chave] = url
    return sorted((a, m, u) for (a, m), u in vistos.items())


def download():
    raw = TEMP_DIR / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    for ano, mes, url in links():
        ext = url.rsplit(".", 1)[-1].lower()
        dest = raw / f"{ano}_{mes:02d}.{ext}"
        if dest.exists():
            continue
        try:
            dest.write_bytes(fetch(url))
            print(f"  ✓ {ano}-{mes:02d} {url.rsplit('/', 1)[-1]}")
        except Exception as e:
            print(f"  ✗ {ano}-{mes:02d} {url}: {e}")


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")


def planilha(path: Path) -> Path:
    """Desempacota zip/rar e devolve a planilha de dentro."""
    if path.suffix.lower() not in (".zip", ".rar"):
        return path
    out = path.with_suffix("")
    if not out.exists():
        out.mkdir()
        # 7zz não abre o RAR v4 de 2015–2016 ("Sub items Errors"); o unar abre
        subprocess.run(["unar", "-q", "-f", "-o", str(out), str(path)], check=True, capture_output=True)
    arqs = [p for p in out.rglob("*") if p.suffix.lower() in (".xls", ".xlsx", ".csv", ".txt")]
    if len(arqs) != 1:
        raise RuntimeError(f"{path.name}: {len(arqs)} planilhas dentro: {[a.name for a in arqs]}")
    return arqs[0]


def le_largo(path: Path):
    """Lê a planilha crua, sem cabeçalho, como lista de linhas de str."""
    import polars as pl

    if path.suffix.lower() in (".csv", ".txt"):
        raw = path.read_bytes()
        try:
            txt = raw.decode("utf-8")
        except UnicodeDecodeError:
            txt = raw.decode("latin-1")
        sep = ";" if txt.count(";") > txt.count(",") else ","
        return [line.split(sep) for line in txt.splitlines()]
    # 2013–2016: a primeira aba é "Termos e Definições"; os dados vêm noutra.
    # Devolve a primeira aba que tenha cabeçalho UF/MUNICÍPIO.
    import fastexcel

    for aba in fastexcel.read_excel(str(path)).sheet_names:
        df = pl.read_excel(path, engine="calamine", sheet_name=aba,
                           has_header=False, infer_schema_length=0)
        linhas = [[("" if v is None else str(v)) for v in row] for row in df.iter_rows()]
        if acha_cabecalho(linhas) is not None:
            return linhas
    return []


def acha_cabecalho(linhas):
    for i, row in enumerate(linhas[:40]):
        cab = [norm(c) for c in row]
        if "uf" in cab and any(c.startswith("munic") for c in cab):
            return i, cab
    return None


def parse_um(path: Path, ano: int, mes: int):
    linhas = le_largo(planilha(path))
    achado = acha_cabecalho(linhas)
    if achado is None:
        raise RuntimeError(f"{path.name}: cabeçalho UF/MUNICIPIO não achado")
    i, cab = achado
    i_uf = cab.index("uf")
    i_mun = next(j for j, c in enumerate(cab) if c.startswith("munic"))
    tipos = [(j, c) for j, c in enumerate(cab) if c and j not in (i_uf, i_mun)]
    out = []
    for row in linhas[i + 1:]:
        if len(row) <= max(i_uf, i_mun):
            continue
        uf, mun = row[i_uf].strip().upper(), row[i_mun].strip()
        if len(uf) != 2 or not mun:
            continue
        for j, tipo in tipos:
            v = row[j].strip() if j < len(row) else ""
            if not v:
                continue
            try:
                q = int(float(v.replace(".", "").replace(",", ".")) if "," in v else float(v))
            except ValueError:
                continue
            out.append((ano, mes, uf, mun, tipo, q))
    return out


# Grafia da SENATRAN -> nome oficial do IBGE, onde a normalização (sem acento,
# caixa alta) não basta. Conferido contra br_bd_diretorios_brasil.municipio em
# 2026-09-24. Os "MUNICIPIO NAO INFORMADO" e o distrito IBITIUVA (SP, 7 meses
# em 2024–25) ficam sem id_municipio de propósito.
ALIAS = {
    ("BA", "LAGEDO DO TABOCAL"): "Lajedo do Tabocal",
    ("BA", "MUQUEM DO SAO FRANCISCO"): "Muquém de São Francisco",
    ("CE", "ITAPAJE"): "Itapagé",
    ("GO", "BOM JESUS"): "Bom Jesus de Goiás",
    ("MG", "SAO TOME DAS LETRAS"): "São Thomé das Letras",
    ("MG", "BARAO D0 MONTE ALTO"): "Barão de Monte Alto",
    ("MG", "BRASOPOLIS"): "Brazópolis",
    ("MG", "AMPARO DA SERRA"): "Amparo do Serra",
    ("MG", "DONA EUZEBIA"): "Dona Eusébia",
    ("MG", "GOUVEA"): "Gouveia",
    ("MG", "QUELUZITA"): "Queluzito",
    ("MT", "VILA BELA DA SANTISSIMA TRINDA"): "Vila Bela da Santíssima Trindade",
    ("MT", "POXOREU"): "Poxoréo",
    ("PA", "ELDORADO DOS CARAJAS"): "Eldorado do Carajás",
    ("PB", "SAO DOMINGOS DE POMBAL"): "São Domingos",
    ("PB", "CAMPO DE SANTANA"): "Tacima",
    ("PB", "SANTAREM"): "Joca Claudino",
    ("PE", "LAGOA DO ITAENGA"): "Lagoa de Itaenga",
    ("PE", "BELEM DE SAO FRANCISCO"): "Belém do São Francisco",
    ("PI", "SAO FRANCISCO DE ASSIS DO PIAU"): "São Francisco de Assis do Piauí",
    ("PR", "PINHAL DO SAO BENTO"): "Pinhal de São Bento",
    ("PR", "BELA VISTA DO CAROBA"): "Bela Vista da Caroba",
    ("PR", "SANTA CRUZ DO MONTE CASTELO"): "Santa Cruz de Monte Castelo",
    ("PR", "MUNHOZ DE MELLO"): "Munhoz de Melo",
    ("RJ", "PARATI"): "Paraty",
    ("RJ", "ARMACAO DE BUZIOS"): "Armação dos Búzios",
    ("RJ", "TRAJANO DE MORAIS"): "Trajano de Moraes",
    ("RN", "ASSU"): "Açu",
    ("RN", "LAGOA DANTA"): "Lagoa d'Anta",
    ("RO", "NOVA DO MAMORE"): "Nova Mamoré",
    ("RS", "SANTANA DO LIVRAMENTO"): "Sant'Ana do Livramento",
    ("SC", "SAO MIGUEL D'OESTE"): "São Miguel do Oeste",
    ("SC", "LAGEADO GRANDE"): "Lajeado Grande",
    ("SC", "SAO LOURENCO D'OESTE"): "São Lourenço do Oeste",
    ("SC", "PRESIDENTE CASTELO BRANCO"): "Presidente Castello Branco",
    ("SC", "BALNEARIO DE PICARRAS"): "Balneário Piçarras",
    ("SE", "GRACCHO CARDOSO"): "Gracho Cardoso",
    ("SP", "SAO LUIZ DO PARAITINGA"): "São Luís do Paraitinga",
    ("SP", "FLORINEA"): "Florínia",
    ("SP", "EMBU"): "Embu das Artes",
    ("TO", "SAO VALERIO DA NATIVIDADE"): "São Valério",
    ("TO", "COUTO DE MAGALHAES"): "Couto Magalhães",
}


def chave_nome(s: str) -> str:
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().upper()
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", s)).strip()


def diretorio():
    """{(uf, nome normalizado): id_municipio} do diretório do espelho."""
    proc = subprocess.run(
        ["ssh", BEELINK_HOST, "~/bin/duckdb -readonly -csv -noheader ~/rodado/basedosdados.duckdb"],
        input="SET enable_progress_bar=false;\n"
              "SELECT sigla_uf, nome, id_municipio FROM br_bd_diretorios_brasil.municipio;\n",
        capture_output=True, text=True, check=True,
    )
    import csv
    d = {}
    for uf, nome, idm in csv.reader(proc.stdout.splitlines()):
        d[(uf, chave_nome(nome))] = idm
    faltam = [a for a in ALIAS.items() if (a[0][0], chave_nome(a[1])) not in d]
    if faltam:
        raise RuntimeError(f"ALIAS aponta para nome que o diretório não tem: {faltam}")
    for (uf, nome), oficial in ALIAS.items():
        d[(uf, chave_nome(nome))] = d[(uf, chave_nome(oficial))]
    return d


def parse():
    import polars as pl

    outdir = TEMP_DIR / "out"
    dirm = diretorio()
    falhas = []
    for f in sorted((TEMP_DIR / "raw").iterdir()):
        if f.is_dir():
            continue
        m = re.match(r"(\d{4})_(\d{2})\.", f.name)
        if not m:
            continue
        ano, mes = int(m.group(1)), int(m.group(2))
        try:
            rows = parse_um(f, ano, mes)
        except Exception as e:
            falhas.append(f"{f.name}: {e}")
            print(f"  ✗ {f.name}: {e}")
            continue
        df = pl.DataFrame(
            rows, orient="row",
            schema={"ano": pl.Int16, "mes": pl.Int8, "sigla_uf": pl.Utf8,
                    "municipio": pl.Utf8, "tipo_veiculo": pl.Utf8, "quantidade": pl.Int64},
        ).with_columns(
            pl.struct("sigla_uf", "municipio")
            .map_elements(lambda r: dirm.get((r["sigla_uf"], chave_nome(r["municipio"]))),
                          return_dtype=pl.Utf8)
            .alias("id_municipio")
        ).select("ano", "mes", "id_municipio", "sigla_uf", "municipio", "tipo_veiculo", "quantidade")
        d = outdir / f"ano={ano}"
        d.mkdir(parents=True, exist_ok=True)
        df.drop(["ano"]).write_parquet(d / f"mes_{mes:02d}.parquet", compression="zstd")
        tot = df.filter(pl.col("tipo_veiculo") == "total")["quantidade"].sum()
        sem_id = df.filter(pl.col("id_municipio").is_null())["municipio"].unique().to_list()
        print(f"  ✓ {ano}-{mes:02d}: {df['id_municipio'].n_unique()} id_municipio, "
              f"{df.height} linhas, total={tot}, sem id: {sem_id}")
    if falhas:
        print(f"\n{len(falhas)} falhas:\n  " + "\n  ".join(falhas))


def push():
    remote = f"{DATASET_PATH}/{TABLE}"
    subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p {remote}"], check=True)
    subprocess.run(["rsync", "-a", f"{TEMP_DIR}/out/", f"{BEELINK_HOST}:{remote}/"], check=True)


if __name__ == "__main__":
    {"download": download, "parse": parse, "push": push}[sys.argv[1]]()
