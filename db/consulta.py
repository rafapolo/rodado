"""Endpoint HTTP de SQL do db.rodado.xyz (para curl).

    curl -u rodado:SENHA --data-binary 'FROM br_bd_diretorios_brasil.uf' https://db.rodado.xyz/query
    curl -u rodado:SENHA 'https://db.rodado.xyz/query?formato=csv' --data-binary @consulta.sql
    curl -u rodado:SENHA -G https://db.rodado.xyz/query --data-urlencode 'q=SELECT 42'

A senha é cobrada pelo Caddy do mesmo container (finland); este servidor só escuta
em 127.0.0.1 dentro dele.
"""

import base64
import csv
import datetime
import decimal
import hashlib
import io
import json
import math
import os
import re
import threading
import time
import unicodedata
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import duckdb

import rodado_sql

PAGINA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
# /llm: guia público para agentes; o modelo em llm.md recebe os números e o índice de temas
GUIA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm.md")
# /contexto e o tema de cada dataset: a camada semântica de docs/context/ já fatiada por
# dataset (scripts/gera_contexto_db.py). Sem o arquivo, o resto do servidor segue de pé.
try:
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "contexto.json"), encoding="utf-8") as _f:
        CONTEXTO = json.load(_f)
except FileNotFoundError:
    CONTEXTO = {"temas": {}, "dataset_tema": {}, "datasets": {}, "falsos_amigos": {},
                "codificacao_diferente": {}, "metricas": {}, "hierarquias": {}}
SEM_TEMA = "outros"

# Link curto /q/<id>: o SQL salvo por quem tem senha fica em DIR_Q/<id>.sql, no volume.
# O id é o começo do sha256 do texto (o mesmo SQL dá sempre o mesmo link) e só cresce se
# colidir. /q/<id> é a página do terminal, que busca /q/<id>/sql e executa; o Caddy dá a
# quem abre um link que existe o mesmo acesso de quem tem o token.
DIR_Q = os.environ.get("RODADO_DIR_Q", "/dados/q")
ROTA_Q = re.compile(r"^/q/([A-Za-z0-9_-]{8,16})(/sql)?$")
_catalogo = {"em": 0.0, "json": b""}
_catalogo_trava = threading.Lock()
_guia = {"em": 0.0, "texto": b""}
_guia_trava = threading.Lock()
# /tabelas: o catálogo enxuto para LLM, um dataset por linha (o /catalogo.json tem ~460 KB,
# ~140 mil tokens, e é da árvore da página). A descrição é por dataset — as tabelas repetem a
# mesma —, sem a fonte que abre a frase ("IBGE — PIB municipal"), sem url, data nem arquivos.
_tabelas = {"em": 0.0, "linhas": []}
_tabelas_trava = threading.Lock()
SQL_TABELAS = r"""
SELECT dataset, max(CASE WHEN contains(description, ' — ') THEN split_part(description, ' — ', 2)
                         ELSE description END) AS descricao,
       list({'t': "table", 'n': coalesce(rows, 0)} ORDER BY "table") AS tabelas
FROM _rodado_metadata WHERE source <> 'view_only' AND dataset NOT LIKE '\_%' ESCAPE '\'
GROUP BY 1 ORDER BY 1
"""

SQL_GUIA_RESUMO = """
SELECT count(*), count(DISTINCT dataset), coalesce(sum(size_bytes), 0), count(DISTINCT source_name)
FROM _rodado_metadata WHERE source <> 'view_only'
"""
SQL_GUIA_DATASETS = """
SELECT dataset, count(*), coalesce(sum(rows), 0), mode(source_name)
FROM _rodado_metadata WHERE source <> 'view_only'
GROUP BY 1 ORDER BY 1
"""

SQL_CATALOGO = r"""
SELECT v.schema_name AS dataset, v.view_name AS tabela, m.rows AS linhas,
       coalesce(m.description, CASE WHEN v.schema_name = 'main' AND v.view_name LIKE '\_rodado\_%' ESCAPE '\'
         THEN 'catálogo do espelho: _rodado_metadata tem uma linha por tabela (linhas, fonte, data, status, '
           || 'procedência), _rodado_datasets uma por dataset' END) AS descricao,
       m.source_name AS fonte, nullif(m.source_url, '') AS url,
       nullif(m.scrape_date, '') AS atualizado, m.num_files AS arquivos,
       -- a view lê do SSD do finland (cópia em /dados/local, ver catalogo.py) ou do bucket
       contains(v.sql, '{LOCAL}') AS ssd
FROM duckdb_views() v
LEFT JOIN _rodado_metadata m ON m.dataset = v.schema_name AND m."table" = v.view_name
WHERE NOT v.internal AND v.schema_name NOT LIKE '\_%' ESCAPE '\'
ORDER BY v.schema_name <> 'main', 1, 2  -- o catálogo (main._rodado_*) primeiro na árvore
""".replace("{LOCAL}", rodado_sql.LOCAL.replace("'", "''"))

PORTA = int(os.environ.get("RODADO_PORTA_CONSULTA", "18081"))
LIMITE_PADRAO = 10_000
LIMITE_MAXIMO = 10_000
N_SIMULTANEAS = int(os.environ.get("RODADO_SIMULTANEAS", "4"))
SIMULTANEAS = threading.BoundedSemaphore(N_SIMULTANEAS)

USO = """\
Guia para agentes (comece por ele): https://db.rodado.xyz/llm
POST /query com o SQL no corpo (ou GET /query?q=...). Só leitura, um comando por vez.
Parâmetros: formato=json|csv|tsv|parquet, limite=N linhas (padrão e máximo 10000).
Sem formato, a resposta é {"linhas": [...], "avisos": [...], "contexto": [...], "truncado": ...}:
os avisos medidos das tabelas citadas vêm no corpo. formato=json devolve só a lista de linhas.
Cabeçalhos da resposta: X-Linhas, X-Truncado, X-Segundos, X-Avisos, X-Contexto.
Exemplo: curl -u usuario:senha --data-binary 'DESCRIBE br_bd_diretorios_brasil.municipio' https://db.rodado.xyz/query
"""


def _milhar(n):
    return f"{int(n):,}".replace(",", ".")


def _gb(n):
    return f"{n / 1e12:.1f} TB".replace(".", ",") if n >= 1e12 else f"{n / 1e9:.0f} GB"


def _linhas(n):
    for limite, nome in ((1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
        if n >= limite:
            return f"{n / limite:.1f} {nome} linhas".replace(".", ",")
    return f"{int(n)} linhas"


def _sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto.lower()) if not unicodedata.combining(c))


def _curto(n):
    for limite, nome in ((1e9, "bi"), (1e6, "mi"), (1e3, "mil")):
        if n >= limite:
            return f"{n / limite:.3g} {nome}".replace(".", ",")
    return str(int(n))


def _json_valor(v):
    if isinstance(v, decimal.Decimal):
        return float(v)
    if isinstance(v, (datetime.date, datetime.datetime, datetime.time)):
        return v.isoformat()
    if isinstance(v, datetime.timedelta):
        return str(v)
    if isinstance(v, (bytes, bytearray)):
        return v.hex()
    if isinstance(v, uuid.UUID):
        return str(v)
    return str(v)


def _tema(dataset):
    return CONTEXTO["dataset_tema"].get(dataset, SEM_TEMA)


def _indice_temas(datasets):
    """Uma linha por tema do atlas, com os maiores datasets dele: o mapa de entrada do /llm,
    no lugar da lista dos ~250 datasets, que um agente lê pela metade."""
    grupos = {}
    for d, _n, linhas, _f in datasets:
        if not d.startswith("_"):
            grupos.setdefault(_tema(d), []).append((linhas, d))
    nomes = CONTEXTO["temas"]
    saida = []
    for tema, lista in sorted(grupos.items(), key=lambda g: -len(g[1])):
        maiores = ", ".join(d for _, d in sorted(lista, reverse=True)[:6])
        saida.append(f"- `{tema}` · {nomes.get(tema, tema)} · {len(lista)} datasets — {maiores}…")
    return "\n".join(saida)


def _junta(v):
    return ", ".join(map(str, v)) if isinstance(v, list) else str(v)


def _contexto_geral():
    c = CONTEXTO
    partes = [f"# rodado · camada semântica (geral)\n\nGerado de docs/context/ em {c.get('gerado', '?')}. "
              "Por dataset: `/contexto?dataset=<dataset>` (e `&tabela=<tabela>`).\n",
              "## Temas\n", *(f"- `{k}` {v} — `/tabelas?tema={k}`" for k, v in c["temas"].items()),
              "\n## Falsos amigos — mesmo nome de coluna, coisas diferentes: nunca junte por eles\n",
              *(f"- `{k}`: {v}" for k, v in c["falsos_amigos"].items()),
              "\n## Mesmo conceito, códigos diferentes por dataset ou ano: decodifique em cada tabela\n",
              *(f"- `{k}`: {v}" for k, v in c["codificacao_diferente"].items()),
              "\n## Métricas nomeadas (use a expressão; não recalcule à mão)\n"]
    for nome, m in c["metricas"].items():
        linha = (f"- `{nome}` — {m.get('description', '')} [{m.get('unit', '?')}] · "
                 f"`{m.get('expression', '')}` em `{m.get('source_table', '?')}`")
        if m.get("required_filters"):
            linha += f" · filtro obrigatório: {_junta(m['required_filters'])}"
        if m.get("caveat"):
            linha += f" · atenção: {m['caveat']}"
        partes.append(linha)
    partes.append("\n## Hierarquias (subir de nível)\n")
    for nome, h in c["hierarquias"].items():
        partes.append(f"- `{nome}` — {h.get('description', '')}: {' → '.join(h.get('levels', []))}"
                      + (f" ({h['note']})" if h.get("note") else ""))
    return "\n".join(partes) + "\n"


def _contexto_dataset(dataset, tabela=""):
    ctx = CONTEXTO["datasets"].get(dataset, {})
    alvo = f"{dataset}.{tabela}" if tabela else ""
    partes = [f"# contexto · {alvo or dataset}\n",
              f"tema `{_tema(dataset)}` · tabelas em `/tabelas?dataset={dataset}` · "
              f"colunas em `/colunas?t={dataset}.<tabela>`\n"]
    gotchas = [g for g in ctx.get("gotchas", []) if not tabela or not g.get("tabelas") or tabela in g["tabelas"]]
    if gotchas:
        partes.append("## Armadilhas medidas — leia antes de consultar\n")
        for g in gotchas:
            onde = "; ".join(f"{k}: {_junta(g[k])}" for k in ("tabelas", "colunas") if g.get(k))
            partes.append(f"- **[{g.get('severidade', '?')}]** {g['resumo']}" + (f" ({onde})" if onde else ""))
            if g.get("detalhe"):
                partes.append(f"  {' '.join(g['detalhe'].split())}")
            partes.append(f"  medido: {g['verificado']}")
    # "não é código" sem nada a dizer só gasta linha
    codigos = [e for e in ctx.get("codigos", []) if (not alvo or e["tabela"] == alvo)
               and (e.get("status") != "nao_e_codigo" or e.get("nota"))]
    if codigos:
        partes.append("\n## Significado dos códigos de coluna\n")
        for e in codigos:
            linha = f"- `{e['tabela']}` · {_junta(e['colunas'])} — {e.get('status', '')}"
            if e.get("significado"):
                linha += f". {e['significado']}"
            if isinstance(e.get("valores"), dict):
                linha += " · valores: " + ", ".join(f"{k or '∅'}={v}" for k, v in e["valores"].items())
            if e.get("nota"):
                linha += f" · nota: {e['nota']}"
            partes.append(linha)
    pontes = [p for p in ctx.get("pontes", []) if not tabela or tabela in p["tabela"] or p["tabela"].endswith("*")]
    if pontes:
        partes.append("\n## Pontes — como ligar a outras tabelas (use o join dado, não a igualdade ingênua)\n")
        for p in pontes:
            linha = f"- `{p['tabela']}`.`{p['coluna']}` → {p['conceito']}"
            if p.get("referencia"):
                linha += f" (referência `{p['referencia']}`)"
            if p.get("join"):
                linha += f": `{p['join']}`"
            if p.get("nota"):
                linha += f" — {p['nota']}"
            partes.append(linha)
    notas = {t: c for t, c in ctx.get("notas", {}).items() if not alvo or t == alvo}
    if notas:
        partes.append("\n## Notas de coluna (erros já vistos, números conferidos)\n")
        for t, cols in notas.items():
            for col, nota in cols.items():
                partes.append(f"- `{t}`" + ("" if col == "*" else f".`{col}`") + f": {nota}")
    if ctx.get("codificacao"):
        partes.append("\n## Colunas cujo código muda entre datasets (decodifique aqui, não copie de outro)\n")
        partes.extend(f"- `{c}`: {CONTEXTO['codificacao_diferente'][c]}" for c in ctx["codificacao"])
    if ctx.get("metricas"):
        partes.append("\n## Métricas nomeadas deste dataset\n")
        for nome in ctx["metricas"]:
            m = CONTEXTO["metricas"][nome]
            partes.append(f"- `{nome}` — {m.get('description', '')}: `{m.get('expression', '')}` em "
                          f"`{m.get('source_table')}`" + (f" · atenção: {m['caveat']}" if m.get("caveat") else ""))
    if len(partes) == 2:
        partes.append("Nada medido ainda para este dataset. Ausência não quer dizer que não há armadilha: "
                      "amostre (`LIMIT 5`), confira os valores das colunas de código e procure uma tabela "
                      f"`{dataset}.dicionario`. Regras gerais em `/contexto`.")
    return "\n".join(partes) + "\n"


def _referencias(con, sql):
    """Tabelas (dataset, tabela) e nomes de coluna que a SQL cita, pela árvore do parser (sem
    ligar nada: funciona também na consulta que o binder recusou)."""
    try:
        arvore = json.loads(con.execute("SELECT json_serialize_sql(?)", [sql]).fetchone()[0])
    except (duckdb.Error, TypeError, ValueError):
        return [], set()
    tabelas, colunas, pilha = [], set(), [arvore]
    while pilha:
        no = pilha.pop()
        if isinstance(no, list):
            pilha.extend(no)
            continue
        if not isinstance(no, dict):
            continue
        if no.get("type") == "BASE_TABLE" and no.get("schema_name"):
            par = (no["schema_name"], no.get("table_name") or "")
            if par not in tabelas:
                tabelas.append(par)
        elif no.get("class") == "COLUMN_REF" and no.get("column_names"):
            colunas.add(no["column_names"][-1].lower())
        pilha.extend(no.values())
    return tabelas, colunas


def _particoes(con, dataset, tabela):
    """Partição hive de verdade: `/chave=valor/` no caminho dos arquivos da view."""
    sql = con.execute("SELECT sql FROM duckdb_views() WHERE schema_name = ? AND view_name = ?",
                      [dataset, tabela]).fetchone()
    return set(re.findall(r"/([A-Za-z_]\w*)=[^/']+/", sql[0] if sql else ""))


def _primeira_frase(texto, teto=240):
    frase = re.split(r"(?<=[.;])\s", " ".join(str(texto).split()), maxsplit=1)[0]
    return frase if len(frase) <= teto else frase[:teto - 1] + "…"


def _avisos(tabelas, colunas):
    """O que já se mediu sobre as tabelas e colunas desta consulta, em uma linha cada. A
    gotcha sem `colunas` vale para o dataset e entra sempre; a com `colunas`, só quando a
    consulta cita uma delas."""
    avisos = []
    for ds, t in tabelas:
        ctx = CONTEXTO["datasets"].get(ds, {})
        for g in ctx.get("gotchas", []):
            if g.get("tabelas") and t not in g["tabelas"]:
                continue
            if g.get("colunas") and not colunas & {c.lower() for c in g["colunas"]}:
                continue
            avisos.append(f"{ds}.{t} [{g.get('severidade', '?')}]: {g['resumo']}")
        for e in ctx.get("codigos", []):
            citadas = colunas & {c.lower() for c in e["colunas"]}
            if e["tabela"] == f"{ds}.{t}" and citadas and e.get("nota"):
                avisos.append(f"{ds}.{t}.{'/'.join(sorted(citadas))}: {_primeira_frase(e['nota'])}")
        for col, nota in (ctx.get("notas", {}).get(f"{ds}.{t}") or {}).items():
            if col != "*" and col.lower() in colunas:
                avisos.append(f"{ds}.{t}.{col}: {_primeira_frase(nota)}")
        for col in ctx.get("codificacao", []):
            if col in colunas:
                avisos.append(f"{ds}.{t}.{col}: o código muda entre datasets e anos; decodifique pelo "
                              f"dicionário deste dataset (ver /contexto?dataset={ds})")
    for col, razao in CONTEXTO["falsos_amigos"].items():
        if col in colunas:
            avisos.append(f"{col} (falso amigo): {_primeira_frase(razao)}")
    return list(dict.fromkeys(avisos))


def _bloqueios(tabelas, colunas):
    """As armadilhas `[erro]` presas a colunas que a consulta cita: o resultado sai plausível e
    errado (zero linhas, código trocado), então o /query recusa até o agente dizer `ciente=1`.
    A `[erro]` sem `colunas` vale para qualquer consulta do dataset e fica só no aviso."""
    bloqueios = []
    for ds, t in tabelas:
        for g in CONTEXTO["datasets"].get(ds, {}).get("gotchas", []):
            if g.get("severidade") != "erro" or not g.get("colunas"):
                continue
            if g.get("tabelas") and t not in g["tabelas"]:
                continue
            if colunas & {c.lower() for c in g["colunas"]}:
                bloqueios.append(f"{ds}.{t} [erro]: {g['resumo']}")
    return list(dict.fromkeys(bloqueios))


def _tamanho(con, tabelas, colunas):
    """Linhas e partição de cada tabela citada → (itens do /confere, problemas, avisos). Tabela
    grande particionada sem filtro na partição é problema; tabela grande sem partição é aviso:
    nenhum filtro poupa leitura (`sigla_uf = 'SP'` no SIM, 36 mi linhas, levou 73 s)."""
    itens, problemas, avisos = [], [], []
    for ds, t in tabelas:
        linhas = con.execute('SELECT rows FROM _rodado_metadata WHERE dataset = ? AND "table" = ?',
                             [ds, t]).fetchone()
        part = _particoes(con, ds, t)
        item = {"tabela": f"{ds}.{t}", "linhas": linhas[0] if linhas else None,
                "particoes": sorted(part), "filtra_particao": bool(part & colunas)}
        n = item["linhas"] or 0
        if part and not item["filtra_particao"] and n > 50_000_000:
            problemas.append(f"{ds}.{t} tem {_curto(n)} linhas e a consulta não cita "
                             f"a partição ({', '.join(sorted(part))}): vai ler tudo e estourar o tempo")
        elif not part and n > 20_000_000:
            avisos.append(f"{ds}.{t} tem {_curto(n)} linhas e não é particionada: nenhum filtro evita "
                          f"ler a tabela inteira (dezenas de segundos por consulta); agregue no servidor, "
                          f"cite só as colunas necessárias e evite count(DISTINCT) e SUMMARIZE")
        itens.append(item)
    return itens, problemas, avisos


def _ascii(texto):
    """Cabeçalho HTTP só leva latin-1 com segurança; o aviso vai sem acento."""
    return _sem_acento_mantem_caixa(texto).encode("ascii", "replace").decode()


def _sem_acento_mantem_caixa(texto):
    trocas = {"—": "-", "–": "-", "→": "->", "×": "x", "≥": ">=", "≤": "<=", "…": "...", "‘": "'", "’": "'",
              "“": '"', "”": '"', "·": "-"}
    texto = "".join(trocas.get(c, c) for c in texto)
    return "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))


_VAZIAS = set("""que qual quais quanto quantos quantas como onde quando entre para pelo pela pelos pelas
com sem nos nas dos das uma uns umas foi foram era eram tem houve havia ano anos mais menos maior menor
total segundo estado municipio municipios brasil""".split())


def _radicais(texto):
    """Palavras de 3+ letras sem acento, cortadas em 5 (suicídio ~ suicídios, óbito ~ óbitos)."""
    return {p[:5] for p in re.findall(r"[a-z0-9]+", _sem_acento(texto)) if len(p) >= 3 and p not in _VAZIAS}


_INDICE_EXEMPLOS = [(_radicais(e["texto"] + " " + e["tema"]), e) for e in CONTEXTO.get("exemplos", [])]
_IDF = {}
for _rads, _ in _INDICE_EXEMPLOS:
    for _r in _rads:
        _IDF[_r] = _IDF.get(_r, 0) + 1
_IDF = {r: math.log(1 + len(_INDICE_EXEMPLOS) / n) for r, n in _IDF.items()}


def _busca_exemplos(busca, n=6):
    """Os resultados conferidos que mais dividem palavras raras com a busca. Um caso resolvido
    parecido ensina mais o caminho (fontes, recorte, ordem de grandeza) que uma regra."""
    termos = _radicais(busca)
    pontuados = sorted(((sum(_IDF.get(t, 0) for t in termos & rads), e) for rads, e in _INDICE_EXEMPLOS),
                       key=lambda x: -x[0])
    # metade da nota do melhor: abaixo disso casou por uma palavra genérica
    return [e for p, e in pontuados[:n] if p > 0 and p >= pontuados[0][0] / 2]


def _cabecalhos_de_aviso(tabelas, avisos):
    extra = {}
    if tabelas:
        extra["X-Contexto"] = ", ".join(f"/contexto?dataset={d}&tabela={t}" for d, t in tabelas)
    if avisos:
        # quebra de linha no valor encerraria os cabeçalhos ali (o Caddy responderia 502)
        extra["X-Avisos"] = " ".join(_ascii(" || ".join(avisos)).split())[:6000]
    return extra


def _dica_de_erro(msg, tabelas):
    if "Referenced column" in msg or "not found in FROM clause" in msg or "does not have a column" in msg:
        return "confira os nomes das colunas: " + ", ".join(f"/colunas?t={d}.{t}" for d, t in tabelas)
    if "does not exist" in msg and ("Table" in msg or "Catalog" in msg):
        return "a tabela não existe com esse nome; procure em /tabelas?busca=<palavras> ou /tabelas?dataset=<dataset>"
    if "Could not convert" in msg or "Conversion Error" in msg:
        return "tipos diferentes: muitas colunas de código são VARCHAR ('1', '1.0'); compare como texto ou normalize"
    return None


class Handler(BaseHTTPRequestHandler):
    server_version = "rodado"

    def log_message(self, fmt, *args):
        # Sem o SQL no log: só método, caminho e status.
        print(f"{self.log_date_time_string()} {fmt % args}", flush=True)

    def _responde(self, status, corpo, tipo="text/plain; charset=utf-8", extra=None):
        dados = corpo.encode("utf-8") if isinstance(corpo, str) else corpo
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(dados)

    def _erro(self, status, msg, **extra):
        self._responde(status, json.dumps({"erro": msg, **{k: v for k, v in extra.items() if v}},
                                          ensure_ascii=False) + "\n",
                       "application/json; charset=utf-8")

    def _json(self, obj, status=200):
        self._responde(status, json.dumps(obj, ensure_ascii=False, default=_json_valor),
                       "application/json; charset=utf-8")

    def _catalogo(self):
        with _catalogo_trava:
            if time.time() - _catalogo["em"] > 600:
                con = rodado_sql.conecta()
                try:
                    rel = con.sql(SQL_CATALOGO)
                    cols = rel.columns
                    dados = [dict(zip(cols, l)) for l in rel.fetchall()]
                finally:
                    con.close()
                _catalogo["json"] = json.dumps(dados, ensure_ascii=False, default=_json_valor).encode()
                _catalogo["em"] = time.time()
            return _catalogo["json"]

    def _guia(self):
        with _guia_trava:
            if time.time() - _guia["em"] > 600:
                con = rodado_sql.conecta()
                try:
                    tab, ds, tamanho, fontes = con.sql(SQL_GUIA_RESUMO).fetchone()
                    datasets = con.sql(SQL_GUIA_DATASETS).fetchall()
                finally:
                    con.close()
                with open(GUIA, encoding="utf-8") as f:
                    modelo = f.read()
                valores = {
                    "resumo": f"{_milhar(tab)} tabelas · {_milhar(ds)} datasets · {_milhar(fontes)} fontes · "
                              f"{_gb(tamanho)}",
                    "gerado": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
                    "limite_padrao": _milhar(LIMITE_PADRAO), "limite_maximo": _milhar(LIMITE_MAXIMO),
                    "tempo": rodado_sql.TEMPO_LIMITE, "simultaneas": N_SIMULTANEAS,
                    "temas": _indice_temas(datasets),
                    "gerado_contexto": CONTEXTO.get("gerado", "?"),
                }
                for chave, valor in valores.items():   # format() quebraria nas chaves do SQL do guia
                    modelo = modelo.replace("{" + chave + "}", str(valor))
                _guia["texto"] = modelo.encode()
                _guia["em"] = time.time()
            return _guia["texto"]

    def _lista_tabelas(self, params):
        with _tabelas_trava:
            if time.time() - _tabelas["em"] > 600:
                con = rodado_sql.conecta()
                try:
                    dados = con.sql(SQL_TABELAS).fetchall()
                finally:
                    con.close()
                _tabelas["linhas"] = [
                    (ds, f"{ds} — {desc or '?'}: " + ", ".join(f"{t['t']} ({_curto(t['n'])})" for t in tabs))
                    for ds, desc, tabs in dados]
                _tabelas["em"] = time.time()
            linhas = _tabelas["linhas"]
        dataset = (params.get("dataset") or [""])[0].strip()
        busca = _sem_acento((params.get("busca") or [""])[0].strip())
        tema = (params.get("tema") or [""])[0].strip()
        if dataset:
            linhas = [l for l in linhas if l[0] == dataset]
        if tema:
            linhas = [l for l in linhas if _tema(l[0]) == tema]
        if busca:
            linhas = [l for l in linhas if all(p in _sem_acento(l[1]) for p in busca.split())]
        corpo = "".join(l[1] + "\n" for l in linhas) or "nenhum dataset casou (temas em /llm)\n"
        self._responde(200, corpo, extra={"Cache-Control": "private, max-age=600"})

    def _contexto(self, params):
        dataset = (params.get("dataset") or [""])[0].strip()
        tabela = (params.get("tabela") or [""])[0].strip()
        if not dataset:
            return self._responde(200, _contexto_geral(), "text/markdown; charset=utf-8",
                                  {"Cache-Control": "private, max-age=600"})
        return self._responde(200, _contexto_dataset(dataset, tabela), "text/markdown; charset=utf-8",
                              {"Cache-Control": "private, max-age=600"})

    def _exemplos(self, params):
        busca = (params.get("busca") or [""])[0].strip()
        if not busca:
            return self._erro(400, "use /exemplos?busca=<palavras da pergunta>")
        achados = _busca_exemplos(busca)
        if not achados:
            corpo = "nenhum resultado conferido casou; siga o fluxo do /llm\n"
        else:
            corpo = ("# resultados já conferidos parecidos com a busca\n\nMedidos no espelho, com data e "
                     "ressalvas no próprio texto. Servem de caminho (quais fontes, qual recorte) e de ordem "
                     "de grandeza para conferir o seu número; não copie: refaça a consulta.\n\n" +
                     "\n".join(f"- **{e['id']}** ({e['tema']}) {e['texto']}" for e in achados) + "\n")
        self._responde(200, corpo, "text/markdown; charset=utf-8", {"Cache-Control": "private, max-age=600"})

    def _confere(self, sql):
        """Confere a SQL sem executar: tabelas que existem, tamanho, partição filtrada ou não,
        colunas que nenhuma tabela citada tem e os avisos medidos. Custa milissegundos."""
        try:
            con = rodado_sql.conecta()
            try:
                comandos = rodado_sql.separa(con, sql)
                if len(comandos) != 1:
                    return self._erro(400, "um comando por requisição")
                tabelas, colunas = _referencias(con, comandos[0].query)
                existentes, conhecidas, problemas = [], set(), []
                for ds, t in tabelas:
                    cols = {c.lower() for (c,) in con.execute(
                        "SELECT column_name FROM duckdb_columns() WHERE schema_name = ? AND table_name = ?",
                        [ds, t]).fetchall()}
                    if not cols:
                        problemas.append(f"{ds}.{t} não existe; procure em /tabelas?busca=")
                        continue
                    conhecidas |= cols
                    existentes.append((ds, t))
                saida, grandes, lentas = _tamanho(con, existentes, colunas)
                problemas += grandes
                problemas += [f"{b} — o /query recusa até você repetir com ?ciente=1"
                              for b in _bloqueios(tabelas, colunas)]
                desconhecidas = sorted(colunas - conhecidas) if conhecidas else []
            finally:
                con.close()
        except rodado_sql.ConsultaRecusada as e:
            return self._erro(400, f"recusado: {e}")
        except duckdb.Error as e:
            return self._erro(400, str(e))
        self._json({"tabelas": saida, "problemas": problemas, "avisos": lentas + _avisos(tabelas, colunas),
                    "colunas_nao_achadas": desconhecidas,  # pode ser alias da própria consulta
                    "contexto": [f"/contexto?dataset={d}&tabela={t}" for d, t in tabelas]})

    def _colunas(self, alvo):
        partes = alvo.split(".")
        if len(partes) != 2 or not all(p.isidentifier() for p in partes):
            return self._json({"erro": "use dataset.tabela"}, 400)
        con = rodado_sql.conecta()
        try:
            # duckdb_columns() lê os nomes e tipos guardados no catálogo quando a view foi criada;
            # DESCRIBE religaria a view e releria do S3 o rodapé de cada arquivo (4 mil no CNPJ)
            linhas = con.execute("SELECT column_name, data_type FROM duckdb_columns() "
                                 "WHERE schema_name = ? AND table_name = ? ORDER BY column_index", partes).fetchall()
            if not linhas:
                return self._json({"erro": f"tabela {alvo} não existe"}, 400)
            sql = con.execute("SELECT sql FROM duckdb_views() WHERE schema_name = ? AND view_name = ?",
                              partes).fetchone()
        except duckdb.Error as e:
            return self._json({"erro": str(e)}, 400)
        finally:
            con.close()
        # partição hive de verdade: `/chave=valor/` no caminho dos arquivos da view
        hive = set(re.findall(r"/([A-Za-z_]\w*)=[^/']+/", sql[0] if sql else ""))
        self._json([{"coluna": l[0], "tipo": l[1], "particao": l[0] in hive} for l in linhas])

    def _salva_q(self):
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > 64_000:
            return self._erro(413, "SQL grande demais para link")
        sql = self.rfile.read(tamanho).decode("utf-8", errors="replace").strip()
        if not sql:
            return self._erro(400, "SQL vazio")
        try:
            con = rodado_sql.conecta()
            try:
                if len(rodado_sql.separa(con, sql)) != 1:
                    return self._erro(400, "um comando por link")
            finally:
                con.close()
        except rodado_sql.ConsultaRecusada as e:
            return self._erro(400, f"recusado: {e}")
        os.makedirs(DIR_Q, exist_ok=True)
        h = base64.urlsafe_b64encode(hashlib.sha256(sql.encode()).digest()).decode()
        for n in range(8, 17):
            caminho = os.path.join(DIR_Q, h[:n] + ".sql")
            try:
                with open(caminho, "x", encoding="utf-8") as f:   # "x": falha se já existe
                    f.write(sql)
                break
            except FileExistsError:
                with open(caminho, encoding="utf-8") as f:
                    if f.read() == sql:
                        break                                     # mesmo SQL, mesmo link
        else:
            return self._erro(500, "colisão de id")
        self._json({"id": h[:n], "url": f"/q/{h[:n]}"})

    def _q(self, ident, parte):
        caminho = os.path.join(DIR_Q, ident + ".sql")
        if not os.path.exists(caminho):
            return self._erro(404, "link não encontrado")
        if not parte:
            with open(PAGINA, "rb") as f:
                return self._responde(200, f.read(), "text/html; charset=utf-8", {"Cache-Control": "no-cache"})
        with open(caminho, encoding="utf-8") as f:
            return self._responde(200, f.read(), extra={"Cache-Control": "no-cache"})

    def do_GET(self):
        url = urlparse(self.path)
        rota = ROTA_Q.match(url.path)
        if rota:
            return self._q(rota.group(1), rota.group(2))
        if url.path == "/health":
            return self._responde(200, "ok\n")
        if url.path == "/ping":  # mede a ida e volta até o servidor Python (o /health o Caddy responde sozinho)
            return self._responde(200, "pong\n", extra={"Cache-Control": "no-store"})
        # / para quem pede markdown (agentes) e não HTML: o terminal da página não serve a eles
        aceita = self.headers.get("Accept", "")
        if url.path == "/" and not ("text/markdown" in aceita and "text/html" not in aceita):
            with open(PAGINA, "rb") as f:
                return self._responde(200, f.read(), "text/html; charset=utf-8",
                                      {"Cache-Control": "no-cache"})
        if url.path == "/catalogo.json":
            try:
                return self._responde(200, self._catalogo(), "application/json; charset=utf-8")
            except duckdb.Error as e:
                return self._json({"erro": str(e)}, 500)
        if url.path == "/robots.txt":
            # tudo liberado, como era com o 401: os robôs de prévia (Googlebot) leem o og.html
            return self._responde(200, "User-agent: *\nAllow: /\n"
                                       "# Agentes: o guia da API está em https://db.rodado.xyz/llms.txt\n",
                                  extra={"Cache-Control": "public, max-age=86400"})
        if url.path in ("/", "/llm", "/llm.md", "/llms.txt", "/.well-known/llms.txt"):
            try:
                return self._responde(200, self._guia(), "text/markdown; charset=utf-8",
                                      {"Cache-Control": "public, max-age=600"})
            except duckdb.Error as e:
                return self._json({"erro": str(e)}, 500)
        if url.path == "/tabelas":
            try:
                return self._lista_tabelas(parse_qs(url.query))
            except duckdb.Error as e:
                return self._json({"erro": str(e)}, 500)
        if url.path == "/colunas":
            return self._colunas((parse_qs(url.query).get("t") or [""])[0])
        if url.path == "/contexto":
            return self._contexto(parse_qs(url.query))
        if url.path == "/exemplos":
            return self._exemplos(parse_qs(url.query))
        if url.path == "/confere":
            sql = (parse_qs(url.query).get("q") or [""])[0]
            return self._confere(sql) if sql.strip() else self._erro(400, "mande o SQL no corpo do POST ou em ?q=")
        if url.path.rstrip("/") != "/query":
            return self._erro(404, "use /query; guia da API em /llm")
        params = parse_qs(url.query)
        sql = (params.get("q") or [""])[0]
        if not sql.strip():
            return self._responde(200, USO)
        self._executa(sql, params)

    def do_POST(self):
        url = urlparse(self.path)
        if url.path.rstrip("/") == "/q":
            return self._salva_q()
        if url.path.rstrip("/") not in ("/query", "/confere"):
            return self._erro(404, "use /query; guia da API em /llm")
        params = parse_qs(url.query)
        tamanho = int(self.headers.get("Content-Length") or 0)
        if tamanho > 512 * 1024:
            return self._erro(413, "SQL grande demais (máximo 512 KB)")
        corpo = self.rfile.read(tamanho).decode("utf-8", errors="replace")
        # curl -d 'q=...' manda formulário; --data-binary manda o SQL cru.
        if corpo.startswith("q=") and "form-urlencoded" in (self.headers.get("Content-Type") or ""):
            corpo = (parse_qs(corpo).get("q") or [""])[0]
        if url.path.rstrip("/") == "/confere":
            return self._confere(corpo)
        self._executa(corpo, params)

    def _executa(self, sql, params):
        # Sem `formato`, o JSON vem embrulhado com os avisos no corpo: o agente que só lê o corpo
        # (curl sem -i) via X-Avisos não via nada, e 163 das 189 armadilhas (as que não são [erro]) não recusam a consulta.
        # formato=json explícito continua a lista pura, que o MCP e scripts já leem.
        embrulha = not params.get("formato")
        formato = (params.get("formato") or ["json"])[0]
        if formato not in ("json", "csv", "tsv", "parquet"):
            return self._erro(400, "formato deve ser json, csv, tsv ou parquet")
        try:
            limite = min(int((params.get("limite") or [LIMITE_PADRAO])[0]), LIMITE_MAXIMO)
        except ValueError:
            return self._erro(400, "limite deve ser inteiro")

        if not SIMULTANEAS.acquire(timeout=60):
            return self._erro(429, "muitas consultas ao mesmo tempo; tente de novo")
        inicio = time.monotonic()
        try:
            con = rodado_sql.conecta()
            try:
                comandos = rodado_sql.separa(con, sql)
                if len(comandos) != 1:
                    return self._erro(400, "um comando por requisição")
                tabelas, colunas = _referencias(con, comandos[0].query)
                avisos = _avisos(tabelas, colunas)
                bloqueios = _bloqueios(tabelas, colunas)
                if bloqueios and (params.get("ciente") or [""])[0] != "1":
                    return self._erro(400, "a consulta cita coluna de armadilha medida que dá resultado "
                                           "errado sem erro: " + " || ".join(bloqueios),
                                      dica=("leia " + ", ".join(f"/contexto?dataset={d}&tabela={t}" for d, t in tabelas)
                                            + "; se a consulta já trata disso, repita com ?ciente=1"),
                                      avisos=avisos)
                try:
                    avisos = _tamanho(con, tabelas, colunas)[2] + avisos
                except duckdb.Error:  # tabela que não existe: o erro de verdade vem da consulta
                    pass
                with rodado_sql.Cronometro(con) as crono:
                    try:
                        rel = con.sql(comandos[0].query)
                        colunas = rel.columns
                        if formato == "parquet":
                            # Gravado pelo servidor (não pela SQL do usuário) dentro do
                            # temp_directory, a única pasta gravável da conexão travada.
                            arq = os.path.join(rodado_sql.TEMP, f"r_{uuid.uuid4().hex}.parquet")
                            try:
                                rel.limit(limite).write_parquet(arq, compression="zstd")
                                with open(arq, "rb") as f:
                                    dados = f.read()
                            finally:
                                if os.path.exists(arq):
                                    os.remove(arq)
                            linhas = None
                        else:
                            linhas = rel.fetchmany(limite + 1)
                    except duckdb.InterruptException:
                        if crono.estourou:
                            try:
                                dica = "; ".join(f"{d}.{t} é particionada por {', '.join(sorted(p))}"
                                                 for d, t in tabelas if (p := _particoes(con, d, t)))
                            except duckdb.Error:  # a conexão acabou de ser interrompida
                                dica = ""
                            return self._erro(504, f"tempo limite de {rodado_sql.TEMPO_LIMITE} s estourado",
                                              dica=(f"filtre na partição — {dica}" if dica else
                                                    "agregue numa fatia menor (um ano, uma UF) e confira com POST /confere"))
                        raise
                    except duckdb.Error as e:
                        return self._erro(400, str(e), dica=_dica_de_erro(str(e), tabelas), avisos=avisos)
            finally:
                con.close()
        except rodado_sql.ConsultaRecusada as e:
            return self._erro(400, f"recusado: {e}")
        except duckdb.Error as e:
            return self._erro(400, str(e))
        finally:
            SIMULTANEAS.release()

        if linhas is None:
            return self._responde(200, dados, "application/vnd.apache.parquet",
                                  {**_cabecalhos_de_aviso(tabelas, avisos),
                                   "X-Segundos": f"{time.monotonic() - inicio:.3f}"})
        truncado = len(linhas) > limite
        linhas = linhas[:limite]
        extra = {
            **_cabecalhos_de_aviso(tabelas, avisos),
            "X-Linhas": str(len(linhas)),
            "X-Truncado": "1" if truncado else "0",
            "X-Segundos": f"{time.monotonic() - inicio:.3f}",
        }
        if formato == "json":
            registros = [dict(zip(colunas, l)) for l in linhas]
            if embrulha:
                registros = {"linhas": registros, "avisos": avisos,
                             "contexto": [f"/contexto?dataset={d}&tabela={t}" for d, t in tabelas],
                             "truncado": truncado}
            corpo = json.dumps(registros, ensure_ascii=False, default=_json_valor) + "\n"
            return self._responde(200, corpo, "application/json; charset=utf-8", extra)
        saida = io.StringIO()
        w = csv.writer(saida, delimiter="\t" if formato == "tsv" else ",", lineterminator="\n")
        w.writerow(colunas)
        w.writerows(linhas)
        tipo = "text/tab-separated-values" if formato == "tsv" else "text/csv"
        self._responde(200, saida.getvalue(), f"{tipo}; charset=utf-8", extra)


if __name__ == "__main__":
    ThreadingHTTPServer.daemon_threads = True
    srv = ThreadingHTTPServer(("127.0.0.1", PORTA), Handler)
    print(f"escutando em 127.0.0.1:{PORTA}", flush=True)
    srv.serve_forever()
