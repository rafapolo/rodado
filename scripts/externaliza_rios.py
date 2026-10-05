#!/usr/bin/env python3
"""Tira do HTML de /analises/os-rios-estao-secando/ o que vinha embutido em base64.

A página nasce autocontida no repositório rios-do-brasil (pipeline/monta_series.py
gera series.html, que é copiado para cá): duas séries em gzip+base64 dentro de
<script type="text/plain"> (~800 KiB) e as duas fontes variáveis em data: URI
(~80 KiB). Tudo isso entrava no HTML que o navegador precisa baixar e analisar
antes da primeira pintura, e base64 ainda pesa 33% a mais que o binário.

Aqui viram arquivos ao lado do index.html, baixados em paralelo e cacheáveis:
  dados-tendencia.bin, dados-paineis.bin  (gzip puro; .bin e não .gz para que
                                           nenhum servidor aplique
                                           Content-Encoding e descomprima antes
                                           do DecompressionStream da página)
  mono.woff2, serif.woff2

Idempotente: rodar de novo numa página já externalizada não muda nada. Depois de
copiar um series.html novo do rios-do-brasil, rode este script e o gera_seo.py.
"""

import base64
import re
import sys
from pathlib import Path

PASTA = Path(__file__).resolve().parent.parent / "pages" / "analises" / "os-rios-estao-secando"
HTML = PASTA / "index.html"

DADOS = {"d-tendencia": "dados-tendencia.bin", "d-paineis": "dados-paineis.bin"}
FONTES = {"Mono": "mono.woff2", "Serif": "serif.woff2"}

LEITOR_ANTIGO = """  async function abrir(id) {
    const b64 = document.getElementById(id).textContent.trim();
    const bin = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
    if (!('DecompressionStream' in window)) throw new Error('sem DecompressionStream');
    const fluxo = new Blob([bin]).stream().pipeThrough(new DecompressionStream('gzip'));"""

LEITOR_NOVO = """  // as séries ficam em arquivos ao lado (scripts/externaliza_rios.py no rodado)
  const ARQUIVOS = %s;
  async function abrir(id) {
    if (!('DecompressionStream' in window)) throw new Error('sem DecompressionStream');
    const resp = await fetch(ARQUIVOS[id]);
    if (!resp.ok) throw new Error(ARQUIVOS[id] + ': ' + resp.status);
    const fluxo = resp.body.pipeThrough(new DecompressionStream('gzip'));""" % (
    "{ " + ", ".join(f"'{k}': '{v}'" for k, v in DADOS.items()) + " }"
)


def main() -> int:
    s = HTML.read_text(encoding="utf-8")
    original = s

    for id_, nome in DADOS.items():
        m = re.search(rf'\n?<script type="text/plain" id="{id_}">\s*([A-Za-z0-9+/=\s]+?)\s*</script>', s)
        if m:
            (PASTA / nome).write_bytes(base64.b64decode(re.sub(r"\s", "", m.group(1))))
            s = s[: m.start()] + s[m.end() :]
            print(f"  {nome}: {(PASTA / nome).stat().st_size // 1024} KiB")

    if LEITOR_ANTIGO in s:
        s = s.replace(LEITOR_ANTIGO, LEITOR_NOVO)
    elif "ARQUIVOS[id]" not in s:
        print("! leitor das séries mudou no rios-do-brasil; ajuste LEITOR_ANTIGO", file=sys.stderr)
        return 1

    for familia, nome in FONTES.items():
        m = re.search(
            rf'(font-family: "{familia}";\s*src: url\()data:font/woff2;base64,([A-Za-z0-9+/=]+)(\))', s
        )
        if m:
            (PASTA / nome).write_bytes(base64.b64decode(m.group(2)))
            s = s[: m.start()] + m.group(1) + nome + m.group(3) + s[m.end() :]
            print(f"  {nome}: {(PASTA / nome).stat().st_size // 1024} KiB")

    # a fonte do texto corrido é a primeira a aparecer: adianta o download
    preload = '<link rel="preload" href="serif.woff2" as="font" type="font/woff2" crossorigin>'
    if preload not in s:
        s = s.replace("<style>", preload + "\n<style>", 1)

    # as séries começam a baixar junto com o HTML, não só quando o script roda
    for nome in DADOS.values():
        tag = f'<link rel="preload" href="{nome}" as="fetch" crossorigin>'
        if tag not in s:
            s = s.replace(preload, preload + "\n" + tag, 1)

    if s != original:
        HTML.write_text(s, encoding="utf-8")
    print(f"index.html: {len(original.encode()) // 1024} KiB -> {len(s.encode()) // 1024} KiB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
