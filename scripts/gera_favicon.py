#!/usr/bin/env python3
"""Gera favicon e ícones de app de rodado.xyz.

Marca: "r" em Charter Bold, creme sobre ferrugem — as mesmas cores do site.
Saída: pages/assets/ (favicon.ico, PNGs) e pages/site.webmanifest.
"""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ACCENT = "#9c3b2e"
PAPER = "#f6f2ea"

CHARTER = "/System/Library/Fonts/Supplemental/Charter.ttc"
CHARTER_BOLD = 3

# Renderiza grande e reduz — bem mais nítido que desenhar direto no tamanho final.
SUPER = 512

ICO_SIZES = [16, 32, 48]
PNG_SIZES = {
    "favicon-16.png": 16,
    "favicon-32.png": 32,
    "icon-192.png": 192,
    "icon-512.png": 512,
}
APPLE_TOUCH = 180


def glyph(size: int, *, radius_ratio: float, padding_ratio: float) -> Image.Image:
    """Quadrado arredondado ferrugem com um 'r' creme centrado opticamente."""
    img = Image.new("RGBA", (SUPER, SUPER), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle(
        [0, 0, SUPER - 1, SUPER - 1],
        radius=int(SUPER * radius_ratio),
        fill=ACCENT,
    )

    box = SUPER * (1 - 2 * padding_ratio)
    font = ImageFont.truetype(CHARTER, int(box * 0.98), index=CHARTER_BOLD)

    # Centra pela caixa real do glifo, não pelas métricas da fonte:
    # o "r" tem muito espaço morto acima e à direita.
    l, t, r, b = d.textbbox((0, 0), "r", font=font)
    x = (SUPER - (r - l)) / 2 - l
    y = (SUPER - (b - t)) / 2 - t
    d.text((x, y), "r", font=font, fill=PAPER)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    root = Path(__file__).resolve().parent.parent / "pages"
    assets = root / "assets"
    assets.mkdir(parents=True, exist_ok=True)

    # favicon: cantos quase retos e pouca margem — a 16px o detalhe some
    for name, size in PNG_SIZES.items():
        icon = glyph(size, radius_ratio=0.16, padding_ratio=0.17)
        icon.save(assets / name, "PNG", optimize=True)
        print(f"{assets / name}")

    ico = glyph(SUPER, radius_ratio=0.16, padding_ratio=0.17)
    ico.save(assets / "favicon.ico", sizes=[(s, s) for s in ICO_SIZES])
    print(f"{assets / 'favicon.ico'}")

    # Apple aplica a própria máscara: fundo cheio, sem cantos arredondados
    apple = glyph(APPLE_TOUCH, radius_ratio=0.0, padding_ratio=0.19).convert("RGB")
    apple.save(assets / "apple-touch-icon.png", "PNG", optimize=True)
    print(f"{assets / 'apple-touch-icon.png'}")

    manifest = {
        "name": "rodado — Brasil em números",
        "short_name": "rodado",
        "description": "Dados públicos brasileiros cruzados em investigações sobre desigualdade, poder, economia, saúde e violência.",
        "start_url": "/",
        "display": "standalone",
        "background_color": PAPER,
        "theme_color": ACCENT,
        "icons": [
            {"src": "/assets/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/assets/icon-512.png", "sizes": "512x512", "type": "image/png"},
        ],
    }
    (root / "site.webmanifest").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{root / 'site.webmanifest'}")


if __name__ == "__main__":
    main()
