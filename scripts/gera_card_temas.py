"""Copia o cartão de cada tema do MCP para a coluna da direita da página do tema.

    python scripts/gera_card_temas.py

mcp.html → pages/temas/NN-*.html e mcp-en.html → pages/temas-en/NN-*.html. O
cartão é achado pelo link do título (href="temas/NN-....html") e entra antes de
</main>, entre marcadores; rodar de novo substitui o bloco, então editar o
cartão no mcp.html e rodar este script é o caminho para manter os dois iguais.
O estilo está em assets/server-card.css (o mesmo que o mcp.html usa).
"""

import re
from pathlib import Path

PAGES = Path(__file__).resolve().parent.parent / "pages"
INI, FIM = "<!-- mcp-card:start (gerado por scripts/gera_card_temas.py — não editar à mão) -->", "<!-- mcp-card:end -->"
CSS = '<link rel="stylesheet" href="../assets/server-card.css">'

ORIGENS = (
    ("mcp.html", "temas", "Cartão do tema no catálogo do MCP"),
    ("mcp-en.html", "temas-en", "Topic card in the MCP catalog"),
)


def main() -> None:
    total = 0
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
            # o título apontava para a própria página do tema; aqui leva ao catálogo do MCP
            c = cartao.replace(m.group(0), f'href="../{origem}"').strip()
            bloco = (f'{INI}\n<aside class="tema-mcp" aria-label="{rotulo}">\n{c}\n'
                     f'</aside>\n{FIM}\n')
            t = alvo.read_text()
            t = re.sub(re.escape(INI) + r".*?" + re.escape(FIM) + r"\n?", "", t, flags=re.S)
            if t.count("</main>") != 1:
                raise SystemExit(f"{alvo}: esperava um </main>")
            t = t.replace("</main>", bloco + "</main>")
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
