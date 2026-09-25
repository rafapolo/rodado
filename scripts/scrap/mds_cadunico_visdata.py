#!/usr/bin/env python3
"""
CadÚnico — indicadores municipais do VIS DATA 3 (MDS/SAGI) -> Parquet -> beelink.

O VIS DATA saiu de `aplicacoes.mds.gov.br` para
`aplicacoes.cidadania.gov.br/vis/data3/`, que só abre por IP brasileiro
(`_proxy_br.Pool`). O caminho até o dado, decifrado em 2026-09-24:

1. Busca: POST `vis/tabelas/busca_metadados_mis2.php` (q, str_prog, qt, p...)
   devolve HTML com um link `v.php?q[]=<token>` por indicador. O token é
   opaco (cifrado no servidor) e é o único jeito de apontar um indicador.
   `get_objetos_vis.php`, o autocomplete, devolve sempre 0: não serve.
2. Dado: POST `vis/data3/v.php?q[]=<token>&ag=m&wt=json&tp_funcao_consulta=0`
   com `start=0, length=3147483647, export=1, export_tipo=csv` — é a
   requisição do botão "Baixar CSV". Devolve o CSV inteiro (todos os
   municípios × todos os meses) em segundos. Sem `export=1` o servidor corta
   em 50 linhas qualquer que seja `start`/`length`/`rows`.
   `ag` = p (país), r (região), e (UF), m (município).

Saída: ~/rodado/br_mds_cadunico/indicadores_municipio/<slug>.parquet, formato
longo — id_municipio (7 dígitos, pelo diretório do espelho), referencia
(1º dia do mês/ano), indicador, variavel, valor. Mais
~/rodado/br_mds_cadunico/indicadores_catalogo/ com o nome, a unidade e a
coluna de origem de cada série.

Uso:
    python3 scripts/scrap/mds_cadunico_visdata.py lista  [TEMP_DIR]
    python3 scripts/scrap/mds_cadunico_visdata.py baixa  [TEMP_DIR]
    python3 scripts/scrap/mds_cadunico_visdata.py parse  [TEMP_DIR]
    python3 scripts/scrap/mds_cadunico_visdata.py push   [TEMP_DIR]
"""

import hashlib
import html
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from _proxy_br import UA, Pool, _proxies  # noqa: E402

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_mds_cadunico"
VIS = "https://aplicacoes.cidadania.gov.br/vis/"
PROGRAMA = "Cadastro Único para Programas Sociais"
TEMP_DIR = Path(sys.argv[2] if len(sys.argv) > 2 else "/tmp/cadunico")


def _pool():
    return Pool(VIS + "data3/data-explorer.php")


def _post(pool, url, data, timeout=(20, 180)):  # (conexão, leitura): proxy morto não prende 15 min
    erro = None
    for p in random.sample(pool.vivos, len(pool.vivos)):
        try:
            r = requests.post(url, data=data, proxies=_proxies(p), timeout=timeout,
                              verify=False, headers={"User-Agent": UA})
            if r.status_code == 200:
                return r
            erro = r.status_code
        except Exception as e:
            erro = type(e).__name__
            pool.descarta(p)
    raise RuntimeError(f"{url}: nenhum proxy respondeu ({erro})")


def lista():
    """Todos os indicadores do programa CadÚnico, com token e níveis de agregação."""
    pool = _pool()
    itens, p, qt = {}, 0, 30
    while True:
        r = _post(pool, VIS + "tabelas/busca_metadados_mis2.php", {
            "q": "", "cpo": "nome", "cpot": "asc", "qt": qt, "p": p,
            "str_prog": PROGRAMA, "str_unidade": "", "t": "", "sistemas": "", "wiki": "",
            "str_fonte": "", "fct": "", "palavras_chave": "", "olvy": 1,
        }, timeout=120)
        d = r.json()
        total = int(d.get("numFound") or 0)
        res = d.get("res") or ""
        # um card por indicador: título, token do v.php e níveis (data-ag)
        for card in re.split(r'(?=<div class="card card-shadow)', res):
            tok = re.search(r'v\.php\?q\[\]=([^"\' ]+)', card)
            if not tok:
                continue
            tok = html.unescape(tok.group(1))
            ag = re.search(r'data-ag="([^"]*)"', card)
            am = re.search(r'data-am="([^"]*)"', card)
            txt = [t.strip() for t in re.sub(r"<[^>]+>", "|", card).split("|") if t.strip()]
            nome = next((t for t in txt if len(t) > 15 and not t.startswith(("Unidade", "Programa"))), txt[0])
            itens[tok] = {"nome": html.unescape(nome), "token": tok,
                          "ag": ag.group(1) if ag else "", "am": am.group(1) if am else ""}
        p += qt
        print(f"  {len(itens)}/{total}")
        if p >= total:
            break
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    (TEMP_DIR / "indicadores.json").write_text(json.dumps(list(itens.values()), ensure_ascii=False, indent=1))
    mun = sum("Município" in i["ag"] for i in itens.values())
    print(f"{len(itens)} indicadores ({total} na busca), {mun} com nível municipal")


def slug(i):
    return hashlib.md5(i["token"].encode()).hexdigest()[:12]


def baixa():
    pool = _pool()
    inds = json.loads((TEMP_DIR / "indicadores.json").read_text())
    raw = TEMP_DIR / "raw"
    raw.mkdir(exist_ok=True)

    def um(n, i):
        dst = raw / f"{slug(i)}.csv"
        if dst.exists() or "Município" not in i["ag"]:
            return
        url = VIS + "data3/v.php?q[]=" + i["token"] + "&ag=m&wt=json&tp_funcao_consulta=0"
        t = time.time()
        try:
            r = _post(pool, url, {"draw": 1, "start": 0, "length": 3147483647,
                                  "export": 1, "export_tipo": "csv"})
        except Exception as e:
            print(f"  ✗ [{n}] {i['nome'][:70]}: {e}")
            return
        if "csv" not in r.headers.get("content-type", ""):
            print(f"  ✗ [{n}] {i['nome'][:70]}: resposta {r.headers.get('content-type')}")
            return
        dst.write_bytes(r.content)
        print(f"  ✓ [{n}] {len(r.content) / 1e6:.1f} MB {time.time() - t:.0f}s {i['nome'][:70]}", flush=True)

    # 2 por vez: com 4 o pool caiu inteiro (132 de 139 falharam), antes do descarta()
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(2) as ex:
        list(ex.map(lambda a: um(*a), enumerate(inds, 1)))


def parse():
    import csv
    import io

    import polars as pl

    proc = subprocess.run(
        ["ssh", BEELINK_HOST, "~/bin/duckdb -readonly -csv -noheader ~/rodado/basedosdados.duckdb"],
        input="SET enable_progress_bar=false;\nSELECT id_municipio FROM br_bd_diretorios_brasil.municipio;\n",
        capture_output=True, text=True, check=True)
    id7 = {l[:6]: l for l in proc.stdout.split()}

    inds = {slug(i): i for i in json.loads((TEMP_DIR / "indicadores.json").read_text())}
    out = TEMP_DIR / "out" / "indicadores_municipio"
    out.mkdir(parents=True, exist_ok=True)
    catalogo = []
    for f in sorted((TEMP_DIR / "raw").glob("*.csv")):
        i = inds[f.stem]
        rows = list(csv.reader(io.StringIO(f.read_bytes().decode("latin-1"))))
        cab, dados = rows[0], rows[1:]
        # Código, Unidade Territorial, UF, Referência, <variáveis...>
        i_ref = cab.index("Referência")
        variaveis = cab[i_ref + 1:]
        cod, ref, var, val = [], [], [], []
        for r in dados:
            if len(r) < len(cab):
                continue
            mes_ano = r[i_ref]
            m = re.fullmatch(r"(\d{2})/(\d{4})", mes_ano) or re.fullmatch(r"(\d{4})", mes_ano)
            if not m:
                continue
            referencia = f"{m.group(2)}-{m.group(1)}-01" if m.lastindex == 2 else f"{m.group(1)}-01-01"
            for k, v in enumerate(r[i_ref + 1:]):
                if v in ("", "-"):
                    continue
                cod.append(r[0])
                ref.append(referencia)
                var.append(k)
                val.append(v)
        df = pl.DataFrame({"codigo": cod, "referencia": ref, "k": var, "valor": val}).with_columns(
            pl.col("codigo").replace_strict(id7, default=None).alias("id_municipio"),
            pl.col("referencia").str.to_date(),
            pl.col("k").replace_strict(dict(enumerate(variaveis)), return_dtype=pl.Utf8).alias("variavel"),
            pl.col("valor").str.replace(",", ".").cast(pl.Float64, strict=False),
            pl.lit(i["nome"]).alias("indicador"),
            pl.lit(f.stem).alias("id_indicador"),
        ).select("id_municipio", "referencia", "id_indicador", "indicador", "variavel", "valor")
        sem_id = df.filter(pl.col("id_municipio").is_null()).height
        df.write_parquet(out / f"{f.stem}.parquet", compression="zstd")
        catalogo.append({"id_indicador": f.stem, "indicador": i["nome"], "niveis": i["ag"],
                         "periodicidade": i["am"], "variaveis": " || ".join(variaveis),
                         "linhas": df.height, "token_visdata": i["token"]})
        print(f"  ✓ {f.stem} {df.height:,} linhas, {len(variaveis)} variáveis, sem id: {sem_id}  {i['nome'][:60]}")
    d = TEMP_DIR / "out" / "indicadores_catalogo"
    d.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(catalogo).write_parquet(d / "catalogo.parquet", compression="zstd")
    print(f"{len(catalogo)} indicadores, {sum(c['linhas'] for c in catalogo):,} linhas")


def push():
    for tabela in ("indicadores_municipio", "indicadores_catalogo"):
        remote = f"{DATASET_PATH}/{tabela}"
        subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p {remote}"], check=True)
        subprocess.run(["rsync", "-a", f"{TEMP_DIR}/out/{tabela}/", f"{BEELINK_HOST}:{remote}/"], check=True)
        print(f"  ✓ push {tabela}")


if __name__ == "__main__":
    {"lista": lista, "baixa": baixa, "parse": parse, "push": push}[sys.argv[1]]()
