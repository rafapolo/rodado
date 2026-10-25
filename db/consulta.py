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
import html
import io
import json
import math
import os
import queue
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
# Ao lado de cada <id>.sql, <id>.json guarda o que /llm/index mostra: cliques (aberturas de
# /q/<id>), criado_em e quanto a consulta leva para rodar (segundos, medido por _mede_q logo
# depois de salvar e refeito a cada /query com o mesmo texto).
_meta_q_trava = threading.Lock()
_fila_q = queue.Queue()
BRT = datetime.timezone(datetime.timedelta(hours=-3))


def _meta_q(ident):
    try:
        with open(os.path.join(DIR_Q, ident + ".json"), encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, ValueError):
        return {}


def _anota_q(ident, **campos):
    """Mescla campos no <id>.json; cliques=1 soma em vez de substituir."""
    with _meta_q_trava:
        meta = _meta_q(ident)
        if campos.pop("clique", False):
            meta["cliques"] = meta.get("cliques", 0) + 1
        meta.update(campos)
        tmp = os.path.join(DIR_Q, f".{ident}.json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False)
        os.replace(tmp, os.path.join(DIR_Q, ident + ".json"))


def _id_salvo(sql):
    """O id de /q/ que guarda exatamente este SQL, ou None (o mesmo cálculo de _salva_q)."""
    sql = sql.strip()
    h = base64.urlsafe_b64encode(hashlib.sha256(sql.encode()).digest()).decode()
    for n in range(8, 17):
        try:
            with open(os.path.join(DIR_Q, h[:n] + ".sql"), encoding="utf-8") as f:
                if f.read() == sql:
                    return h[:n]
        except FileNotFoundError:
            return None
    return None


def _descricao_q(sql):
    """O bloco de comentários `--` que abre o SQL é a descrição (é como os links são escritos)."""
    linhas = []
    for l in sql.splitlines():
        l = l.strip()
        if not l.startswith("--"):
            break
        linhas.append(l.lstrip("-").strip())
    return " ".join(x for x in linhas if x)


def _mede_q():
    """Fila de um consumidor só: roda cada link salvo uma vez e anota os segundos. Ocupa uma
    das SIMULTANEAS, como qualquer consulta, e traz no máximo LIMITE_PADRAO linhas, o que o
    link mostra."""
    while True:
        ident = _fila_q.get()
        try:
            with open(os.path.join(DIR_Q, ident + ".sql"), encoding="utf-8") as f:
                sql = f.read()
        except FileNotFoundError:
            continue
        with SIMULTANEAS:
            inicio = time.monotonic()
            resultado = {}
            try:
                con = rodado_sql.conecta()
                try:
                    with rodado_sql.Cronometro(con) as crono:
                        try:
                            con.sql(rodado_sql.separa(con, sql)[0].query).fetchmany(LIMITE_PADRAO)
                        except duckdb.InterruptException:
                            if not crono.estourou:
                                raise
                            resultado["erro"] = f"estourou {rodado_sql.TEMPO_LIMITE} s"
                finally:
                    con.close()
            except Exception as e:   # o consumidor não pode morrer: os links seguintes ficariam sem tempo
                resultado["erro"] = (str(e).splitlines() or [type(e).__name__])[0][:200]
            if "erro" not in resultado:
                resultado["erro"] = None
                resultado["segundos"] = round(time.monotonic() - inicio, 3)
        _anota_q(ident, medido_em=datetime.datetime.now(BRT).isoformat(timespec="seconds"), **resultado)


def _lista_q():
    """Todos os links salvos, do mais novo para o mais antigo."""
    itens = []
    for nome in os.listdir(DIR_Q) if os.path.isdir(DIR_Q) else []:
        if not nome.endswith(".sql"):
            continue
        ident = nome[:-4]
        caminho = os.path.join(DIR_Q, nome)
        with open(caminho, encoding="utf-8") as f:
            sql = f.read()
        meta = _meta_q(ident)
        criado = meta.get("criado_em") or datetime.datetime.fromtimestamp(
            os.path.getmtime(caminho), BRT).isoformat(timespec="seconds")
        itens.append({"id": ident, "url": f"/q/{ident}", "descricao": _descricao_q(sql),
                      "criado_em": criado, "cliques": meta.get("cliques", 0),
                      "segundos": meta.get("segundos"), "erro": meta.get("erro"),
                      "medido_em": meta.get("medido_em"), "sql": sql})
    itens.sort(key=lambda i: i["criado_em"], reverse=True)
    return itens


# dataset.tabela citado no SQL: os prefixos dos datasets do espelho (br_, world_, ...), para não
# pegar alias.coluna (d.ano, s.cnpj_basico)
TABELA_NO_SQL = re.compile(r"\b((?:br|world|global|mundo|us|un|eu|politicos|_rodado|_local)[a-z0-9_]*\.[a-z_][a-z0-9_]*)\b(?!\s*\()")


def _pagina_q(itens):
    """Cards (padrão) ou tabela, montados no navegador a partir da lista embutida."""
    for i in itens:
        i["tabelas"] = sorted(set(TABELA_NO_SQL.findall(i["sql"].lower())))
    dados = json.dumps(itens, ensure_ascii=False, default=_json_valor).replace("</", "<\\/")
    return (PAGINA_Q.replace("__DADOS__", dados)
            .replace("__LIMITE__", f"{LIMITE_PADRAO:,}".replace(",", ".")))


PAGINA_Q = r"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>rodado — consultas salvas</title>
<meta name="theme-color" content="#1e1e2e">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap">
<style>
  :root { --base: #1e1e2e; --mantle: #181825; --crust: #11111b; --surface0: #313244; --surface1: #45475a;
    --overlay0: #6c7086; --overlay1: #7f849c; --subtext0: #a6adc8; --text: #cdd6f4;
    --blue: #89b4fa; --mauve: #cba6f7; --green: #a6e3a1; --yellow: #f9e2af; --peach: #fab387; --red: #f38ba8; }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--base); color: var(--text);
    font: 12px/1.5 "JetBrains Mono", ui-monospace, Menlo, Consolas, monospace; }
  a { color: var(--blue); text-decoration: none; }
  a:hover { text-decoration: underline; }
  header { position: sticky; top: 0; z-index: 2; background: color-mix(in srgb, var(--base) 92%, transparent);
    backdrop-filter: blur(6px); border-bottom: 1px solid var(--surface0); padding: 14px 16px 12px; }
  .topo { display: flex; align-items: baseline; gap: 12px; flex-wrap: wrap; max-width: 1400px; margin: 0 auto; }
  h1 { font-size: 14px; color: var(--mauve); margin: 0; }
  h1 a { color: inherit; }
  .resumo { color: var(--overlay1); }
  .controles { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; max-width: 1400px; margin: 10px auto 0; }
  input[type=search] { flex: 1 1 240px; min-width: 0; background: var(--mantle); color: var(--text);
    border: 1px solid var(--surface0); border-radius: 6px; padding: 7px 10px; font: inherit; }
  input[type=search]:focus { outline: none; border-color: var(--mauve); }
  .grupo { display: inline-flex; border: 1px solid var(--surface0); border-radius: 6px; overflow: hidden; }
  .grupo button { background: var(--mantle); color: var(--subtext0); border: 0; padding: 7px 10px; font: inherit; cursor: pointer; }
  .grupo button + button { border-left: 1px solid var(--surface0); }
  .grupo button[aria-pressed=true] { background: var(--surface0); color: var(--text); }
  main { max-width: 1400px; margin: 0 auto; padding: 16px; }
  .vazio { color: var(--overlay1); padding: 40px 0; text-align: center; }

  /* cards */
  .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 12px; }
  .card { background: var(--mantle); border: 1px solid var(--surface0); border-radius: 10px; padding: 14px;
    display: flex; flex-direction: column; gap: 10px; min-width: 0; transition: border-color .15s; }
  .card:hover { border-color: var(--surface1); }
  .card .desc { color: var(--text); font-weight: 700; line-height: 1.45; display: -webkit-box;
    -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
  a.desc:hover { color: var(--mauve); text-decoration: none; }
  .card .desc.sem { color: var(--subtext0); font-weight: 400; }
  .card.aberto .desc { -webkit-line-clamp: unset; }
  .mais { background: none; border: 0; color: var(--overlay1); font: inherit; padding: 0; cursor: pointer; align-self: flex-start; }
  .metricas { display: flex; flex-wrap: wrap; gap: 6px; }
  .chip { display: inline-flex; align-items: center; gap: 5px; padding: 2px 8px; border-radius: 99px;
    background: var(--base); border: 1px solid var(--surface0); color: var(--subtext0); white-space: nowrap; }
  .chip b { color: var(--text); font-weight: 700; }
  .t-rapido b { color: var(--green); } .t-medio b { color: var(--yellow); }
  .t-lento b { color: var(--peach); } .t-falhou b { color: var(--red); } .t-medindo b { color: var(--overlay1); }
  .tabelas { display: flex; flex-wrap: wrap; gap: 4px; }
  .tabelas a { color: var(--overlay1); background: var(--base); border-radius: 4px; padding: 1px 6px; font-size: 11px; max-width: 100%; overflow-wrap: anywhere; }
  .tabelas a:hover { color: var(--blue); text-decoration: none; }
  .btn { background: var(--surface0); color: var(--text); border: 0; border-radius: 6px; padding: 6px 10px;
    font: inherit; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
  .btn:hover { background: var(--surface1); text-decoration: none; }
  .btn.ok, .id.ok { color: var(--green); }
  .id { margin-left: auto; align-self: center; background: none; border: 0; padding: 2px 0; font: inherit; font-size: 11px;
    color: var(--overlay0); cursor: copy; white-space: nowrap; }
  .id:hover { color: var(--text); }

  /* tabela */
  .tabela { overflow-x: auto; border: 1px solid var(--surface0); border-radius: 10px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; vertical-align: top; padding: 8px 12px; border-bottom: 1px solid var(--surface0); }
  tbody tr:last-child td { border-bottom: 0; }
  tbody tr:hover { background: var(--mantle); }
  th { color: var(--overlay1); font-weight: 400; background: var(--mantle); white-space: nowrap; }
  th[data-ordem] { cursor: pointer; } th[data-ordem]:hover { color: var(--text); }
  td.n, th.n { text-align: right; white-space: nowrap; }
  td a.desc { display: block; min-width: 280px; color: var(--text); }
  td a.desc.sem { color: var(--subtext0); }
  td .t-rapido { color: var(--green); } td .t-medio { color: var(--yellow); }
  td .t-lento { color: var(--peach); } td .t-falhou { color: var(--red); } td .t-medindo { color: var(--overlay1); }
  @media (max-width: 420px) { .cards { grid-template-columns: 1fr; } }
</style></head><body>
<header>
  <div class="topo">
    <h1><a href="/">rodado</a> · consultas salvas</h1>
    <span class="resumo" id="resumo"></span>
  </div>
  <div class="controles">
    <input type="search" id="busca" placeholder="buscar na descrição, no SQL ou nas tabelas  ( / )" autocomplete="off">
    <div class="grupo" id="ordem" role="group" aria-label="ordenar">
      <button data-v="criado_em" aria-pressed="true">recentes</button>
      <button data-v="cliques">cliques</button>
      <button data-v="segundos">tempo</button>
    </div>
    <div class="grupo" id="vista" role="group" aria-label="vista">
      <button data-v="cards" aria-pressed="true">cards</button>
      <button data-v="tabela">tabela</button>
    </div>
    <a class="btn" href="/llm/index?formato=json" target="_blank" rel="noopener">json</a>
  </div>
</header>
<main id="lista"></main>
<script>
const ITENS = __DADOS__;
const $ = s => document.querySelector(s);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const semAcento = s => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
const rel = new Intl.RelativeTimeFormat("pt-BR", { numeric: "auto" });
const abs = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo" });
const num = new Intl.NumberFormat("pt-BR");
let estado = { busca: "", ordem: "criado_em", vista: "cards" };
try { Object.assign(estado, JSON.parse(localStorage.getItem("rodado.qindex") || "{}"), { busca: "" }); } catch (_) {}
for (const i of ITENS) i._busca = semAcento([i.descricao, i.sql, i.id, (i.tabelas || []).join(" ")].join(" "));

function quando(iso) {
  const d = new Date(iso), s = (d - Date.now()) / 1000;
  const [n, u] = Math.abs(s) < 3600 ? [s / 60, "minute"] : Math.abs(s) < 86400 ? [s / 3600, "hour"]
    : Math.abs(s) < 86400 * 45 ? [s / 86400, "day"] : [s / 86400 / 30, "month"];
  return { rel: rel.format(Math.round(n), u), abs: abs.format(d) };
}
function tempo(i) {
  if (i.segundos != null) {
    const s = i.segundos;
    return { txt: s < 1 ? `${Math.round(s * 1000)} ms` : s < 60 ? `${s.toFixed(1).replace(".", ",")} s` : `${(s / 60).toFixed(1).replace(".", ",")} min`,
             cls: s < 5 ? "t-rapido" : s < 30 ? "t-medio" : "t-lento", dica: `medido ${i.medido_em ? quando(i.medido_em).abs : ""}` };
  }
  return i.erro ? { txt: "falhou", cls: "t-falhou", dica: i.erro } : { txt: "medindo…", cls: "t-medindo", dica: "na fila de medição" };
}
const url = i => location.origin + i.url;
const descricao = i => i.descricao ? esc(i.descricao) : esc((i.sql.trim().split("\n")[0] || "").slice(0, 200));

function card(i) {
  const q = quando(i.criado_em), t = tempo(i);
  const tabs = (i.tabelas || []).map(n => `<a href="/?query=${btoa(unescape(encodeURIComponent("DESCRIBE " + n)))}" target="_blank" rel="noopener" title="abrir ${esc(n)} no terminal">${esc(n)}</a>`).join("");
  return `<article class="card" data-id="${i.id}">
    <a class="desc${i.descricao ? "" : " sem"}" href="${i.url}" target="_blank" rel="noopener" title="abrir a consulta">${descricao(i)}</a>
    ${i.descricao.length > 220 ? `<button class="mais" data-acao="mais">ler tudo</button>` : ""}
    <div class="metricas">
      <span class="chip" title="${esc(q.abs)}">criado <b>${esc(q.rel)}</b></span>
      <span class="chip" title="aberturas do link">cliques <b>${num.format(i.cliques)}</b></span>
      <span class="chip ${t.cls}" title="${esc(t.dica)}">tempo <b>${esc(t.txt)}</b></span>
      <button class="id" data-acao="copia" title="copiar o link">${i.id}</button>
    </div>
    ${tabs ? `<div class="tabelas">${tabs}</div>` : ""}
  </article>`;
}
function linha(i) {
  const q = quando(i.criado_em), t = tempo(i);
  return `<tr data-id="${i.id}">
    <td><button class="id" data-acao="copia" title="copiar o link">${i.id}</button></td>
    <td><a class="desc${i.descricao ? "" : " sem"}" href="${i.url}" target="_blank" rel="noopener" title="abrir a consulta">${descricao(i)}</a></td>
    <td class="n" title="${esc(q.abs)}">${esc(q.rel)}</td>
    <td class="n">${num.format(i.cliques)}</td>
    <td class="n"><span class="${t.cls}" title="${esc(t.dica)}">${esc(t.txt)}</span></td>
  </tr>`;
}

function ordena(a, b) {
  const k = estado.ordem;
  if (k === "criado_em") return b.criado_em.localeCompare(a.criado_em);
  if (k === "cliques") return b.cliques - a.cliques || b.criado_em.localeCompare(a.criado_em);
  return (b.segundos ?? -1) - (a.segundos ?? -1);
}
function desenha() {
  const termos = semAcento(estado.busca).split(/\s+/).filter(Boolean);
  const itens = ITENS.filter(i => termos.every(t => i._busca.includes(t))).sort(ordena);
  const total = ITENS.reduce((s, i) => s + i.cliques, 0);
  $("#resumo").textContent = (itens.length === ITENS.length ? `${ITENS.length} links` : `${itens.length} de ${ITENS.length} links`)
    + ` · ${num.format(total)} cliques · tempo = uma execução no servidor, até __LIMITE__ linhas`;
  for (const b of document.querySelectorAll("#ordem button")) b.setAttribute("aria-pressed", b.dataset.v === estado.ordem);
  for (const b of document.querySelectorAll("#vista button")) b.setAttribute("aria-pressed", b.dataset.v === estado.vista);
  if (!itens.length) { $("#lista").innerHTML = `<div class="vazio">nenhum link casa com “${esc(estado.busca)}”</div>`; return; }
  $("#lista").innerHTML = estado.vista === "cards"
    ? `<div class="cards">${itens.map(card).join("")}</div>`
    : `<div class="tabela"><table><thead><tr><th>link</th><th>descrição</th><th class="n" data-ordem="criado_em">criado</th>
       <th class="n" data-ordem="cliques">cliques</th><th class="n" data-ordem="segundos">tempo</th></tr></thead>
       <tbody>${itens.map(linha).join("")}</tbody></table></div>`;
}
function guarda() { try { localStorage.setItem("rodado.qindex", JSON.stringify({ ordem: estado.ordem, vista: estado.vista })); } catch (_) {} }

$("#busca").addEventListener("input", e => { estado.busca = e.target.value; desenha(); });
$("#ordem").addEventListener("click", e => { if (e.target.dataset.v) { estado.ordem = e.target.dataset.v; guarda(); desenha(); } });
$("#vista").addEventListener("click", e => { if (e.target.dataset.v) { estado.vista = e.target.dataset.v; guarda(); desenha(); } });
document.addEventListener("keydown", e => {
  if (e.key === "/" && document.activeElement !== $("#busca")) { e.preventDefault(); $("#busca").focus(); }
  if (e.key === "Escape" && document.activeElement === $("#busca")) { e.target.value = ""; estado.busca = ""; desenha(); }
});
$("#lista").addEventListener("click", async e => {
  const th = e.target.closest("th[data-ordem]");
  if (th) { estado.ordem = th.dataset.ordem; guarda(); desenha(); return; }
  const b = e.target.closest("[data-acao]");
  if (!b) return;
  const el = b.closest("[data-id]"), i = ITENS.find(x => x.id === el.dataset.id);
  if (b.dataset.acao === "copia") {
    try { await navigator.clipboard.writeText(url(i)); } catch (_) { return; }
    const antes = b.textContent; b.textContent = "copiado ✓"; b.classList.add("ok");
    setTimeout(() => { b.textContent = antes; b.classList.remove("ok"); }, 1400);
  } else if (b.dataset.acao === "mais") {
    el.classList.toggle("aberto"); b.textContent = el.classList.contains("aberto") ? "recolher" : "ler tudo";
  }
});
desenha();
</script>
</body></html>
"""
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
        if not _meta_q(h[:n]):
            _anota_q(h[:n], criado_em=datetime.datetime.now(BRT).isoformat(timespec="seconds"), cliques=0)
            _fila_q.put(h[:n])
        self._json({"id": h[:n], "url": f"/q/{h[:n]}"})

    def _q(self, ident, parte):
        caminho = os.path.join(DIR_Q, ident + ".sql")
        if not os.path.exists(caminho):
            return self._erro(404, "link não encontrado")
        if not parte:
            _anota_q(ident, clique=True)
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
        if url.path.rstrip("/") == "/llm/index":   # atrás da senha: cada link abre o site inteiro
            itens = _lista_q()
            if (parse_qs(url.query).get("formato") or [""])[0] == "json":
                return self._json(itens)
            return self._responde(200, _pagina_q(itens), "text/html; charset=utf-8", {"Cache-Control": "no-store"})
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
        if (ident := _id_salvo(sql)):   # o mesmo texto de um link: atualiza o tempo dele
            _anota_q(ident, segundos=round(time.monotonic() - inicio, 3), erro=None,
                     medido_em=datetime.datetime.now(BRT).isoformat(timespec="seconds"))
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
    # links salvos antes do <id>.json (ou ainda sem tempo): medidos em fila, um de cada vez
    if os.path.isdir(DIR_Q):
        for nome in sorted(os.listdir(DIR_Q)):
            if nome.endswith(".sql") and "segundos" not in _meta_q(nome[:-4]) and not _meta_q(nome[:-4]).get("erro"):
                _fila_q.put(nome[:-4])
    threading.Thread(target=_mede_q, daemon=True).start()
    print(f"escutando em 127.0.0.1:{PORTA}", flush=True)
    srv.serve_forever()
