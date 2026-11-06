"""Copia o cartão de cada tema do MCP para a coluna da direita da página do tema.

    python scripts/gera_card_temas.py

mcp.html → pages/temas/NN-*.html e mcp-en.html → pages/temas-en/NN-*.html. O
cartão é achado pelo link do título (href="temas/NN-....html") e entra logo
depois da abertura (p.lede ou p.dek), entre marcadores — no celular fica no alto; rodar de novo substitui o bloco, então editar o
cartão no mcp.html e rodar este script é o caminho para manter os dois iguais.
O estilo está em assets/server-card.css (o mesmo que o mcp.html usa).

Na página do tema o cartão perde o cabeçalho (ícone, título, contagem — a página
já tem o seu título) e a lista de tabelas vira uma tag por dataset, com link
para o atlas (/atlas/?db=...). Entram como tag os datasets do card-id e os
citados em <code> na descrição; nome de view legada sem dataset
(isp_taxa_evolucao_mensal_municipio) é resolvido pelo schema_graph.json do atlas.
"""

import html as H
import json
import re
from pathlib import Path

PAGES = Path(__file__).resolve().parent.parent / "pages"
INI, FIM = "<!-- mcp-card:start (gerado por scripts/gera_card_temas.py — não editar à mão) -->", "<!-- mcp-card:end -->"
CSS = '<link rel="stylesheet" href="../assets/server-card.css">'

ORIGENS = (
    ("mcp.html", "temas", "Cartão do tema no catálogo do MCP"),
    ("mcp-en.html", "temas-en", "Topic card in the MCP catalog"),
)
TEXTOS = {
    "temas": ("Datasets", "Abrir {n} no atlas", "Ver no catálogo do MCP"),
    "temas-en": ("Datasets", "Open {n} in the atlas", "See it in the MCP catalog"),
}

# nomes legados do mcp.html que não batem com nenhum dataset pelo nome; os que
# não têm dataset no espelho (br_stn_tesouro_orcamento, oe_indicadores_orcamentarios,
# world_bank_rd, fbsp_atlas_violencia) ficam fora das tags
APELIDOS = {
    "isp_taxa_evolucao_mensal_municipio": "br_rj_isp_estatisticas_seguranca",
    "anatel_ibc_municipio": "br_anatel_indice_brasileiro_conectividade",
    "br_cnj_improbidade": "br_cnj_improbidade_administrativa",
    "comex_pais": "br_me_comex_stat",
    "siconfi_orcamento": "br_me_siconfi",
    "tse_despesas_candidato": "br_tse_eleicoes",
}


def carrega_atlas() -> tuple[dict[str, str], dict[str, str]]:
    """dataset → descrição, e nome solto de tabela/view → dataset."""
    g = json.loads((PAGES / "atlas" / "schema_graph.json").read_text())
    ds = {d["n"]: d.get("de", "") for d in g["datasets"]}
    soltos: dict[str, set[str]] = {}
    for t in g["tables"]:
        d = g["datasets"][t["ds"]]["n"]
        partes = d.split("_")
        # a tabela pelo nome, e cada "<sufixo do dataset>_<tabela>" (isp_taxa_..., anp_precos_...)
        nomes = {t["n"]} | {"_".join(partes[i:]) + "_" + t["n"] for i in range(1, len(partes))}
        for nome in nomes:
            soltos.setdefault(nome, set()).add(d)
    return ds, {k: next(iter(v)) for k, v in soltos.items() if len(v) == 1}


def dataset_de(nome: str, ds: dict[str, str], soltos: dict[str, str]) -> str | None:
    nome = nome.strip()
    if "." in nome:
        nome = nome.split(".", 1)[0]
    nome = APELIDOS.get(nome, nome)
    if nome in ds:
        return nome
    if nome in soltos:
        return soltos[nome]
    # dataset citado com prefixo a mais/a menos (cgu_emendas_parlamentares ↔ br_cgu_emendas_parlamentares)
    for cand in ("br_" + nome, "world_" + nome, "global_" + nome):
        if cand in ds:
            return cand
    return None


def adapta(cartao: str, pasta: str, origem: str, ds: dict[str, str], soltos: dict[str, str]) -> str:
    rot, abrir, catalogo = TEXTOS[pasta]
    nomes = re.findall(r'<code class="card-id">([^<]*)</code>', cartao)
    desc = re.search(r'<p class="card-desc">.*?</p>', cartao, re.S)
    if desc:
        nomes += re.findall(r"<code>([a-z][a-z0-9_.]*)</code>", desc.group(0))
    vistos: list[str] = []
    for nome in nomes:
        d = dataset_de(H.unescape(nome), ds, soltos)
        if d is None:
            if "_" in nome and nome.strip().startswith(("br_", "world_", "global_")):
                print(f"  aviso: {pasta}: {nome.strip()} não está no atlas")
            continue
        if d not in vistos:
            vistos.append(d)
    tags = "".join(
        f'<li><a class="card-tag" href="/atlas/?db={d}" title="{H.escape(ds[d] or abrir.format(n=d))}"'
        f' aria-label="{H.escape(abrir.format(n=d))}">{d}</a></li>'
        for d in vistos)
    bloco = (f'<div class="card-tags-block"><div class="card-cruz-heading">{rot}'
             f' <span class="card-tags-n">{len(vistos)}</span></div>'
             f'<ul class="card-tags">{tags}</ul></div>')
    c = re.sub(r'\s*<div class="card-head">.*?</span>\s*</div>', "", cartao, count=1, flags=re.S)
    c = re.sub(r'<div class="card-id-row">.*?</div>', bloco, c, count=1, flags=re.S)
    rodape = f'<a class="card-mcp-link" href="../{origem}">{catalogo} <span aria-hidden="true">→</span></a>'
    return re.sub(r"\s*</section>\s*$", f"\n          {rodape}\n        </section>", c)


def main() -> None:
    total = 0
    ds, soltos = carrega_atlas()
    for origem, pasta, rotulo in ORIGENS:
        html = (PAGES / origem).read_text()
        cartoes = re.findall(r'[ \t]*<section class="server-card".*?</section>', html, re.S)
        for cartao in cartoes:
            m = re.search(rf'href="{pasta}/([^"]+\.html)"', cartao)
            if not m:
                raise SystemExit(f"{origem}: cartão sem link para {pasta}/")
            alvo = PAGES / pasta / m.group(1)
            if not alvo.exists():
                raise SystemExit(f"{origem}: {alvo} não existe")
            c = adapta(cartao, pasta, origem, ds, soltos).strip()
            bloco = (f'{INI}\n<aside class="tema-mcp" aria-label="{rotulo}">\n{c}\n'
                     f'</aside>\n{FIM}\n')
            t = alvo.read_text()
            t = re.sub(re.escape(INI) + r".*?" + re.escape(FIM) + r"\n?", "", t, flags=re.S)
            if t.count("</main>") != 1:
                raise SystemExit(f"{alvo}: esperava um </main>")
            # logo depois da abertura (lede, ou dek): na tela estreita o cartão
            # aparece no alto, não no fim; na larga é absoluto, à direita
            abertura = (re.search(r'[ \t]*<p class="lede">.*?</p>\n', t, re.S)
                        or re.search(r'[ \t]*<p class="dek">.*?</p>\n', t, re.S))
            if not abertura:
                raise SystemExit(f"{alvo}: sem p.lede nem p.dek para ancorar o cartão")
            t = t[:abertura.end()] + bloco + t[abertura.end():]
            t = re.sub(r"<main(?: class=\"[^\"]*\")?>", '<main class="com-card">', t, count=1)
            if CSS not in t:
                # fora do bloco head:start/end, que o gera_seo.py reescreve
                t = t.replace("<!-- head:end -->", "<!-- head:end -->\n" + CSS, 1)
            alvo.write_text(t)
            total += 1
        print(f"{origem}: {len(cartoes)} cartões → {pasta}/")
    print(f"{total} páginas de tema atualizadas")


if __name__ == "__main__":
    main()
