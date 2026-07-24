#!/usr/bin/env python3
"""Gera a imagem de compartilhamento (Open Graph) de rodado.xyz.

Reproduz a identidade do site: papel creme, tipografia Charter, régua cor ferrugem.
Saída: pages/assets/og.png (1200x630) e pages/assets/og-en.png.
"""

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
        "eyebrow": "778 TABELAS PÚBLICAS · 43 TEMAS",
        "head": ["Brasil em números,", "retratos dos dados oficiais"],
        "dek": "Vínculos de emprego, óbitos, contratos públicos, resultados\neleitorais — cruzados por raça, classe, gênero e território.",
    },
    "og-en.png": {
        "eyebrow": "778 PUBLIC TABLES · 43 THEMES",
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
    f_head = load(CHARTER, 68, index=3)   # Charter Bold
    f_dek = load(CHARTER, 27)
    f_brand = load(CHARTER, 33, index=3)
    f_url = load(SANS, 23)

    y = PAD + 14
    tracked(d, (PAD, y), spec["eyebrow"], f_eyebrow, INK_FAINT, 2.6)

    y += 62
    for line in spec["head"]:
        d.text((PAD, y), line, font=f_head, fill=INK)
        y += 82

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


def main() -> None:
    out_dir = Path(__file__).resolve().parent.parent / "pages" / "assets"
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, spec in VARIANTS.items():
        path = out_dir / name
        build(spec).save(path, "PNG", optimize=True)
        print(f"{path}  {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
