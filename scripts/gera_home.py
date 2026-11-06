#!/usr/bin/env python3
"""Preenche os blocos gerados da home (pages/index.html e pages/en.html).

A home é uma apresentação curta: oito plataformas escolhidas (HOME_PLATAFORMAS), o teaser do
DataViz (estático) e as análises mais recentes em cartões de notícia — no EN,
só as escritas em inglês. Os 43 temas saíram dela para
pages/temas/index.html (e temas-en/index.html) — leitores relataram que a
home anterior, com os 43 cartões, o teaser do DataViz e dois parágrafos
longos, afastava mais do que convidava.

O conteúdo vem das mesmas fontes que montam /analises/ e /plataformas/:
  pages/analises/results/manifest.json   → cartões de análise
  pages/plataformas/plataformas.json     → vitrine de plataformas

Só reescreve o que está entre <!-- home:<bloco>:start --> e
<!-- home:<bloco>:end -->; o resto da página é editado à mão. Roda sozinho ou
chamado pelo gera_analises.py (antes do gera_seo.py).
"""

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGES = RAIZ / "pages"
MANIFEST = PAGES / "analises" / "results" / "manifest.json"
PLATAFORMAS = PAGES / "plataformas" / "plataformas.json"

N_ANALISES = 8
# a vitrine da home mostra só estas, nesta ordem; /plataformas/ continua com todas
HOME_PLATAFORMAS = ["eleicoes", "brasilume", "templos-religiosos", "os-rios-estao-secando",
                    "datative", "viso", "fincrime", "religioes"]
LIMITE_DEK = 230

TEXTO = {
    "pt": {
        "analises_h2": "Análises recentes",
        "analises_todas": "Todas as {n} análises →",
        "plataformas_h2": "Plataformas",
        "plataformas_dek": "<a href=\"/plataformas/\">Painéis, mapas e redes</a> para explorar o dado inteiro, "
                           "não só o recorte de uma análise.",
        "plataformas_todas": "Ver as {n} plataformas →",
    },
    "en": {
        "analises_h2": "Analyses in English",
        "analises_todas": "All analyses (mostly in Portuguese) →",
        "plataformas_h2": "Platforms",
        "plataformas_dek": "<a href=\"/plataformas/en.html\">Dashboards, maps and networks</a> to explore the whole "
                           "data, not just the slice an analysis used. The "
                           "platforms themselves are in Portuguese.",
        "plataformas_todas": "See the {n} platforms →",
    },
}


def e(texto: str) -> str:
    return (texto.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def primeira_frase(texto: str) -> str:
    """O dek do manifest é um parágrafo inteiro; o cartão leva só a abertura."""
    frase = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9\"“])", texto.strip())[0]
    if len(frase) <= LIMITE_DEK:
        return frase
    corte = frase[:LIMITE_DEK].rsplit(" ", 1)[0].rstrip(",;:—– ")
    return corte + "…"


def data_br(item: dict, en: bool = False) -> str:
    # rodado_em é DD-MM-AAAA; sem ele, cai no ano-mês de "date"
    d = item.get("rodado_em")
    if d and re.fullmatch(r"\d{2}-\d{2}-\d{4}", d):
        dia, mes, ano = d.split("-")
        return f"{ano}-{mes}-{dia}" if en else f"{dia}/{mes}/{ano}"
    return item.get("date", "")


def chave_data(item: dict) -> str:
    d = item.get("rodado_em", "")
    if re.fullmatch(r"\d{2}-\d{2}-\d{4}", d):
        dia, mes, ano = d.split("-")
        return f"{ano}-{mes}-{dia}"
    return item.get("date", "")


def href_relativo(url: str) -> str:
    # links para o próprio site saem relativos à raiz: funcionam no preview local
    return re.sub(r"^https://rodado\.xyz", "", url)


def bloco_analises(itens: list[dict], lang: str) -> str:
    # tradução ("par" + "lang": "en") não conta como análise a mais no total
    """PT: as mais recentes em português. EN: só as escritas em inglês — sem
    nenhuma, o bloco sai vazio e a home EN fica só com plataformas e DataViz."""
    en = lang == "en"
    t = TEXTO[lang]
    escolhidas = [i for i in itens if (i.get("lang") == "en") == en]
    escolhidas.sort(key=chave_data, reverse=True)
    escolhidas = escolhidas[:N_ANALISES]
    if not escolhidas:
        return ""
    linhas = [f'  <h2 id="analises">{t["analises_h2"]}</h2>',
              '  <div class="noticias carrossel">']
    for it in escolhidas:
        href = href_relativo(it.get("url") or f"/analises/{it['slug']}/")
        fonte = (it.get("tags") or [""])[0]
        linhas.append(
            f'    <a class="noticia" href="{e(href)}">'
            f'<span class="noticia-data">{e(data_br(it, en))}</span>'
            f'<span class="noticia-titulo">{e(it["title"])}</span>'
            f'<span class="noticia-dek">{e(primeira_frase(it["dek"]))}</span>'
            + (f'<span class="noticia-fonte">{e(fonte)}</span>' if fonte else "")
            + "</a>"
        )
    # o "ver todas" é o último cartão do carrossel (assets/carrossel.js)
    n = sum(1 for i in itens if not (i.get("par") and i.get("lang") == "en"))
    linhas.append('    <a class="noticia ver-todas" href="/analises/">'
                  '<span class="ver-todas-seta" aria-hidden="true">→</span>'
                  f'<span class="noticia-titulo">{t["analises_todas"].format(n=n).rstrip(" →")}</span></a>')
    linhas.append("  </div>")
    return "\n".join(linhas)


def bloco_plataformas(itens: list[dict], lang: str) -> str:
    en = lang == "en"
    t = TEXTO[lang]

    def campo(it: dict, k: str) -> str:
        return (en and it.get(f"{k}_en")) or it.get(k) or ""

    linhas = [f'  <h2 id="plataformas">{t["plataformas_h2"]}</h2>',
              f'  <p class="secao-dek">{t["plataformas_dek"]}</p>',
              '  <div class="teaser vitrine carrossel">']
    por_slug = {it["slug"]: it for it in itens}
    faltam = [s for s in HOME_PLATAFORMAS if s not in por_slug]
    if faltam:
        sys.exit(f"HOME_PLATAFORMAS: {faltam} não estão em plataformas.json")
    for it in (por_slug[s] for s in HOME_PLATAFORMAS):
        href = href_relativo(it.get("url") or f"/plataformas/{it['slug']}/")
        titulo = campo(it, "title")
        alt = campo(it, "caption") or titulo
        linhas.append(
            f'    <a class="teaser-tile" href="{e(href)}">'
            f'<img src="plataformas/{e(it["screenshot"])}" alt="{e(alt)}" '
            f'width="640" height="480" loading="lazy">'
            f'<span>{e(titulo)}</span></a>'
        )
    # o "ver todas" é o último cartão do carrossel (assets/carrossel.js)
    destino = "/plataformas/en.html" if en else "/plataformas/"
    linhas.append(f'    <a class="teaser-tile ver-todas" href="{destino}">'
                  f'<span class="ver-todas-seta" aria-hidden="true">→</span>'
                  f'<span>{t["plataformas_todas"].format(n=len(itens)).rstrip(" →")}</span></a>')
    linhas.append("  </div>")
    return "\n".join(linhas)


def substitui(html: str, nome: str, conteudo: str, arquivo: str) -> str:
    padrao = re.compile(
        rf"(<!-- home:{nome}:start[^>]*-->\n).*?\s*(<!-- home:{nome}:end -->)",
        re.S)
    if not padrao.search(html):
        sys.exit(f"{arquivo}: marcador home:{nome} não encontrado")
    recheio = conteudo + "\n  " if conteudo else "  "
    return padrao.sub(lambda m: m.group(1) + recheio + m.group(2), html, count=1)


def main() -> None:
    analises = json.loads(MANIFEST.read_text(encoding="utf-8"))
    plataformas = json.loads(PLATAFORMAS.read_text(encoding="utf-8"))
    # ordem na página: plataformas, DataViz (estático, editado à mão), análises.
    # Análises: no EN só as escritas em inglês (bloco vazio se não houver).
    for arquivo, lang in (("index.html", "pt"), ("en.html", "en")):
        path = PAGES / arquivo
        html = path.read_text(encoding="utf-8")
        novo = substitui(html, "plataformas", bloco_plataformas(plataformas, lang), arquivo)
        novo = substitui(novo, "analises", bloco_analises(analises, lang), arquivo)
        if novo != html:
            path.write_text(novo, encoding="utf-8")
            print(f"  pages/{arquivo}")
        else:
            print(f"  pages/{arquivo} (sem mudança)")


if __name__ == "__main__":
    main()
