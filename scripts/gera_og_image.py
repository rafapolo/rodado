#!/usr/bin/env python3
"""Gera as imagens de compartilhamento (Open Graph) de rodado.xyz.

Reproduz a identidade do site: papel creme, tipografia Charter, régua cor ferrugem.

Saída:
  pages/assets/og.png, og-en.png          o cartão do site
  pages/analises/img/og-<slug>.png        um cartão por análise, do manifest.json

As figuras das análises não servem como cartão: são gráficos de 1:1 a 1,5:1 que o
Twitter/WhatsApp cortam em 1,91:1, decapitando título e eixos. O cartão editorial
carrega o texto, que é o que se lê num feed.
"""

import json
import unicodedata
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630

BG = "#f6f2ea"
INK = "#201d18"
INK_SOFT = "#4a443a"
INK_FAINT = "#77705f"
ACCENT = "#9c3b2e"
RULE = "#d9d0bd"

CHARTER = "/System/Library/Fonts/Supplemental/Charter.ttc"
SANS = "/System/Library/Fonts/Supplemental/Arial.ttf"
SANS_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

PAD = 78

VARIANTS = {
    "og.png": {
        "eyebrow": "839 TABELAS PÚBLICAS · 43 TEMAS",
        "head": ["Brasil em números,", "retratos dos dados oficiais"],
        "dek": "Vínculos de emprego, óbitos, contratos públicos, resultados\neleitorais — cruzados por raça, classe, gênero e território.",
    },
    "og-en.png": {
        "eyebrow": "839 PUBLIC TABLES · 43 THEMES",
        "head": ["Brazil by the numbers,", "portraits from official data"],
        "dek": "Employment records, deaths, public contracts, election results —\ncross-referenced by race, class, gender and territory.",
    },
}


def load(path: str, size: int, index: int = 0) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size, index=index)
    except OSError:
        return ImageFont.load_default()


def tracked(draw: ImageDraw.ImageDraw, xy, text, font, fill, tracking: float):
    """Desenha texto com espaçamento entre letras (PIL não tem letter-spacing)."""
    x, y = xy
    for ch in text:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x


def build(spec: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # régua superior — assinatura visual do site
    d.rectangle([0, 0, W, 9], fill=ACCENT)

    f_eyebrow = load(SANS_BOLD, 21)
    f_head = load(CHARTER, spec.get("head_size", 68), index=3)   # Charter Bold
    f_dek = load(CHARTER, 27)
    f_brand = load(CHARTER, 33, index=3)
    f_url = load(SANS, 23)

    y = PAD + 14
    tracked(d, (PAD, y), spec["eyebrow"], f_eyebrow, INK_FAINT, 2.6)

    y += 62
    passo = spec.get("head_leading", 82)
    for line in spec["head"]:
        d.text((PAD, y), line, font=f_head, fill=INK)
        y += passo

    y += 16
    d.multiline_text((PAD, y), spec["dek"], font=f_dek, fill=INK_SOFT, spacing=13)

    # rodapé
    fy = H - PAD - 46
    d.line([PAD, fy, W - PAD, fy], fill=RULE, width=2)

    by = fy + 18
    bx = d.text((PAD, by), "rodado", font=f_brand, fill=ACCENT) or PAD
    brand_w = d.textlength("rodado", font=f_brand)
    d.text((PAD + brand_w + 16, by + 8), "rodado.xyz", font=f_url, fill=INK_FAINT)

    return img


# --- cartões das análises ---------------------------------------------------

LARGURA_UTIL = W - 2 * PAD
FOOTER_Y = H - PAD - 46  # onde entra o fio do rodapé; nada pode passar daqui
MESES = ("janeiro fevereiro março abril maio junho julho agosto setembro "
         "outubro novembro dezembro").split()

# Charter não tem nenhuma seta (U+2190-2193, U+2194), e os títulos/deks usam
# bastante "↔" e "→". Sem isto virariam tofu no cartão. O travessão serve para
# todas: "Evangélico↔direita" e "2010→2022" leem igual de bem com "–".
SUBSTITUTOS = {"↔": "–", "→": "–", "←": "–", "↑": "–", "↓": "–"}


def sanitiza(texto: str) -> str:
    """Troca o que a Charter não cobre, avisando — tofu silencioso é pior."""
    try:
        from fontTools.ttLib import TTCollection

        cmap = TTCollection(CHARTER).fonts[3].getBestCmap()
    except Exception:  # sem fontTools: aplica só o mapa conhecido
        cmap = None

    saida = []
    for ch in texto:
        cobre = ch in "\n" or (cmap is None and ch not in SUBSTITUTOS) or (
            cmap is not None and ord(ch) in cmap
        )
        if cobre:
            saida.append(ch)
            continue
        troca = SUBSTITUTOS.get(ch)
        if troca is None:
            print(f"  ! Charter não tem {ch!r} (U+{ord(ch):04X}) e não há substituto")
            troca = "?"
        saida.append(troca)
    return "".join(saida)


def quebra(texto: str, font: ImageFont.FreeTypeFont, largura: float) -> list[str]:
    """Quebra em linhas que cabem em `largura`, medindo de verdade."""
    d = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    linhas: list[str] = []
    atual = ""
    for palavra in texto.split():
        teste = f"{atual} {palavra}".strip()
        if atual and d.textlength(teste, font=font) > largura:
            linhas.append(atual)
            atual = palavra
        else:
            atual = teste
    if atual:
        linhas.append(atual)
    return linhas


def corta(linhas: list[str], maximo: int) -> list[str]:
    """Limita a `maximo` linhas, sinalizando o corte com reticências."""
    if len(linhas) <= maximo:
        return linhas
    cortadas = linhas[:maximo]
    cortadas[-1] = cortadas[-1].rstrip(" .,;:—-") + "…"
    return cortadas


def eyebrow_de(item: dict) -> str:
    data = item.get("date") or ""
    try:
        ano, mes = data.split("-")
        return f"ANÁLISE · {MESES[int(mes) - 1].upper()} {ano}"
    except (ValueError, IndexError):
        return "ANÁLISE"


def spec_da_analise(item: dict) -> dict:
    """Monta o spec, encolhendo a manchete até caber acima do rodapé."""
    titulo = sanitiza(item["title"])
    for tamanho, leading, max_linhas in ((68, 82, 2), (58, 70, 3), (50, 61, 3)):
        linhas = quebra(titulo, load(CHARTER, tamanho, index=3), LARGURA_UTIL)
        if len(linhas) <= max_linhas:
            break
    linhas = corta(linhas, max_linhas)

    # o que sobra de altura decide quantas linhas de dek cabem
    fim_head = PAD + 14 + 62 + len(linhas) * leading + 16
    cabem = max(1, int((FOOTER_Y - 24 - fim_head) // 40))
    dek = corta(quebra(sanitiza(item["dek"]), load(CHARTER, 27), LARGURA_UTIL),
                min(cabem, 3))

    return {
        "eyebrow": eyebrow_de(item),
        "head": linhas,
        "head_size": tamanho,
        "head_leading": leading,
        "dek": "\n".join(dek),
    }


def gera_analises(raiz: Path) -> int:
    manifest = raiz / "pages" / "analises" / "results" / "manifest.json"
    if not manifest.exists():
        return 0
    destino = raiz / "pages" / "analises" / "img"
    destino.mkdir(parents=True, exist_ok=True)

    n = 0
    for item in json.loads(manifest.read_text(encoding="utf-8")):
        path = destino / f"og-{item['slug']}.png"
        build(spec_da_analise(item)).save(path, "PNG", optimize=True)
        print(f"{path}  {path.stat().st_size // 1024} KB")
        n += 1
    return n


def main() -> None:
    raiz = Path(__file__).resolve().parent.parent
    out_dir = raiz / "pages" / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, spec in VARIANTS.items():
        path = out_dir / name
        build(spec).save(path, "PNG", optimize=True)
        print(f"{path}  {path.stat().st_size // 1024} KB")
    n = gera_analises(raiz)
    print(f"{len(VARIANTS)} cartões do site · {n} cartões de análise")


if __name__ == "__main__":
    main()
