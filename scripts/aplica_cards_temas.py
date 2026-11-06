"""Aplica propostas de cartão (JSON por tema) em pages/mcp.html e mcp-en.html.

    python scripts/aplica_cards_temas.py <pasta com NN.json>

Cada NN.json: {"card_id_add": ["dataset.tabela"], "cruz_add": [{"pt": [k, v], "en": [k, v]}],
"cruz_fix": [{"old_pt": "trecho do texto antigo", "pt": [k, v] ou null para remover, "en": ...}],
"card_id_remove": [...], "desc_pt"/"desc_en": "HTML da nova card-desc"}.
O cartão é achado pelo link do título (temas/NN- ou temas-en/NN-). Depois rodar
scripts/gera_card_temas.py para levar os cartões às páginas de tema.
"""

import html as H
import json
import re
import sys
from pathlib import Path

PAGES = Path(__file__).resolve().parent.parent / "pages"
ICON = '<i class="fa-solid fa-arrow-right-arrow-left card-cruz-icon"></i>'


def item(k: str, v: str) -> str:
    return f'<li class="card-cruz-item">{ICON}<span><strong>{H.escape(k)}:</strong> {H.escape(v)}</span></li>'


def lis(cartao: str) -> list[str]:
    return re.findall(r'<li class="card-cruz-item">.*?</li>', cartao)


def aplica(cartao: str, prop: dict, lang: str, fixes: list[int]) -> str:
    m = re.search(r'<ul class="card-id-tags">.*?</ul>', cartao, re.S)
    atuais = re.findall(r'<code class="card-id">([^<]*)</code>', m.group(0))
    fora = set(prop.get("card_id_remove", []))
    lista = [x for x in atuais if x not in fora]
    lista += [x for x in prop.get("card_id_add", []) if x not in lista]
    if lista != atuais:
        pilulas = "".join(f'<li><code class="card-id">{x}</code></li>' for x in lista)
        cartao = cartao.replace(m.group(0), f'<ul class="card-id-tags">{pilulas}</ul>')
    if prop.get(f"desc_{lang}"):  # HTML pronto (com <code>), escrito pelo agente que revisou o tema
        cartao = re.sub(r'<p class="card-desc">.*?</p>', lambda _: f'<p class="card-desc">{prop[f"desc_{lang}"]}</p>',
                        cartao, count=1, flags=re.S)
    itens = lis(cartao)
    for i, fix in zip(fixes, prop.get("cruz_fix", [])):
        if i >= 0:  # pt/en null = cruzamento removido
            cartao = cartao.replace(itens[i], item(*fix[lang]) if fix.get(lang) else "")
    add = "".join(item(*c[lang]) for c in prop.get("cruz_add", []))
    if add:
        cartao = re.sub(r"(</li>)(\s*</ul>)", lambda mm: mm.group(1) + add + mm.group(2), cartao, count=1)
    return cartao


def cartao_de(t: str, dirtema: str, nn: str) -> str:
    cs = [c for c in re.findall(r'<section class="server-card".*?</section>', t, re.S)
          if f'href="{dirtema}/{nn}-' in c]
    if len(cs) != 1:
        raise SystemExit(f"{dirtema}: {len(cs)} cartões para o tema {nn}")
    return cs[0]


def main() -> None:
    pasta = Path(sys.argv[1])
    pt, en = (PAGES / "mcp.html").read_text(), (PAGES / "mcp-en.html").read_text()
    for js in sorted(pasta.glob("[0-9][0-9].json")):
        nn, prop = js.stem, json.loads(js.read_text())
        cpt, cen = cartao_de(pt, "temas", nn), cartao_de(en, "temas-en", nn)
        # o índice do item a corrigir vem do texto pt; o en troca o item na mesma posição
        textos = [H.unescape(re.sub(r"<[^>]+>", "", li)) for li in lis(cpt)]
        fixes = [next((i for i, x in enumerate(textos) if H.unescape(f["old_pt"]) in x), -1) for f in prop.get("cruz_fix", [])]
        for f, i in zip(prop.get("cruz_fix", []), fixes):
            if i < 0:
                print(f"  aviso: tema {nn}: cruz_fix sem alvo: {f['old_pt']}")
        pt = pt.replace(cpt, aplica(cpt, prop, "pt", fixes))
        en = en.replace(cen, aplica(cen, prop, "en", fixes))
        print(f"tema {nn}: +{len(prop.get('card_id_add', []))} tabelas, +{len(prop.get('cruz_add', []))} cruzamentos")
    (PAGES / "mcp.html").write_text(pt)
    (PAGES / "mcp-en.html").write_text(en)


if __name__ == "__main__":
    main()
