#!/usr/bin/env python3
"""Reduz PNGs de gráfico para paleta de 256 cores, no mesmo arquivo.

Por que existe: os plot_*.py gravam PNG truecolor de 400–650 KiB por gráfico, e
as páginas de análise carregam vários. Gráfico (texto, linhas, áreas chapadas)
cabe em 256 cores sem diferença visível e cai para 30–45% do tamanho. Foi feito à
mão uma vez (7,9 MB -> 3,6 MB); este script é o que impede a próxima rodada de
um plot_*.py de desfazer isso — o scripts/hooks/pre-commit roda-o em todo PNG
que entra no commit.

Só substitui quando a versão nova é ao menos 15% menor, então rodar de novo num
PNG já otimizado não muda nada (idempotente).
PNG que já é paleta é ignorado, e os cartões og-*.png também: o gera_og_image.py
os regrava a cada rodada, e só redes sociais os baixam.

    python3 scripts/otimiza_png.py                    # pages/analises/img/*.png
    python3 scripts/otimiza_png.py a.png b.png        # arquivos específicos
"""

import io
import sys
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
PADRAO = RAIZ / "pages" / "analises" / "img"
GANHO_MINIMO = 0.85


def otimiza(caminho: Path) -> tuple[int, int] | None:
    original = caminho.read_bytes()
    with Image.open(io.BytesIO(original)) as img:
        if img.format != "PNG" or img.mode == "P":
            return None
        if img.mode == "RGBA":
            reduzida = img.quantize(256, method=Image.Quantize.FASTOCTREE)
        else:
            reduzida = img.convert("RGB").quantize(256, method=Image.Quantize.MEDIANCUT)
        buf = io.BytesIO()
        reduzida.save(buf, "PNG", optimize=True)
    novo = buf.getvalue()
    if len(novo) > len(original) * GANHO_MINIMO:
        return None
    caminho.write_bytes(novo)
    return len(original), len(novo)


def main(args: list[str]) -> int:
    alvos = [Path(a) for a in args] if args else sorted(PADRAO.glob("*.png"))
    for caminho in alvos:
        if caminho.suffix.lower() != ".png" or caminho.name.startswith("og") or not caminho.is_file():
            continue
        r = otimiza(caminho)
        if r:
            print(f"  {caminho.name}: {r[0] // 1024} KiB -> {r[1] // 1024} KiB")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
