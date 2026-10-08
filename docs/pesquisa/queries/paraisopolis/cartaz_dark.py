"""Cartaz dark (1800x2400) — Paraisópolis, presidente 2026, 1º turno.

Lê só os CSVs gerados por gera_paraisopolis.py; não recalcula nada além de
diferenças em pontos percentuais. Desenha tudo num único eixo em coordenadas
de pixel (0..1800 × 0..2400, y para baixo) para controlar o layout.

Paleta validada (dataviz/validate_palette.js --mode dark --surface #1a1a19):
Lula #e66767 (slot vermelho, dark) · Flávio #3987e5 (slot azul, dark).
As cores das séries vão só em marcas; texto usa as tintas neutras.
"""
import csv
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AQUI = Path(__file__).resolve().parent
W, H, DPI = 1800, 2400, 150
PX = 72 / DPI  # pontos por pixel (para tamanhos de marcador)

# tokens (dark) — palette.md do skill dataviz
SURFACE, PANEL = '#1a1a19', '#232321'
INK, INK2, MUTED = '#ffffff', '#c3c2b7', '#898781'
GRID, BASE = '#2c2c2a', '#383835'
LULA, FLAVIO = '#e66767', '#3987e5'
CONNECT = '#4a4945'
FONT = 'DejaVu Sans'


def br(x, d=1):
    return f'{x:.{d}f}'.replace('.', ',')


def milhar(n):
    return f'{n:,}'.replace(',', '.')


def nome_bonito(s):
    t = s.title()
    for a, b in [('Ceu', 'CEU'), ('Emef', 'EMEF'), ('Emei', 'EMEI'), ('Cei ', 'CEI '),
                 ('Etec', 'ETEC'), (' De ', ' de '), (' Do ', ' do ')]:
        t = t.replace(a, b)
    return t


rows = list(csv.DictReader(open(AQUI / 'paraisopolis_locais_presidente_2026.csv', encoding='utf-8')))
locais = sorted([r for r in rows if r['nivel'] == 'local'], key=lambda r: -float(r['pct_lula']))
tot = next(r for r in rows if r['nivel'] == 'paraisopolis_total')
zona = next(r for r in rows if r['nivel'] == 'zona_408_total')
pl, pf = float(tot['pct_lula']), float(tot['pct_flavio'])
zl, zf = float(zona['pct_lula']), float(zona['pct_flavio'])

fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=SURFACE)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis('off'); ax.set_facecolor(SURFACE)


def txt(x, y, s, size, color=INK, weight='normal', ha='left', va='baseline', **kw):
    return ax.text(x, y, s, fontsize=size, color=color, weight=weight, ha=ha, va=va,
                   family=FONT, **kw)


def dot(x, y, color, d=26):
    ax.scatter([x], [y], s=(d * PX) ** 2, color=color, zorder=4,
               edgecolors=SURFACE, linewidths=3 * PX * 2)


M = 110                      # margem lateral
X0, X1 = M + 10, W - M - 10  # faixa do eixo de %
VMIN, VMAX = 15, 75


def X(p):
    return X0 + (p - VMIN) / (VMAX - VMIN) * (X1 - X0)


def haltere(y, f, l, bold=False, size=13, d=26):
    ax.plot([X(f), X(l)], [y, y], color=CONNECT, lw=6 * PX * 2, solid_capstyle='round', zorder=2)
    dot(X(f), y, FLAVIO, d); dot(X(l), y, LULA, d)
    w = 'bold' if bold else 'normal'
    txt(X(f) - d / 2 - 14, y, br(f), size, INK, w, ha='right', va='center_baseline')
    txt(X(l) + d / 2 + 14, y, br(l), size, INK, w, ha='left', va='center_baseline')


# ── título ────────────────────────────────────────────────────────────────
txt(M, 150, 'PARAISÓPOLIS VOTOU ASSIM', 40, INK, 'bold')
txt(M, 215, 'Presidente 2026, 1º turno · 93 seções em 7 locais de votação', 15, INK2)
txt(M, 252, 'da zona eleitoral 408 · São Paulo (SP)', 15, INK2)

# ── números-herói ─────────────────────────────────────────────────────────
HY = 330
heros = [
    (M, LULA, 'Lula (PT)', f'{br(pl)}%', 'dos votos válidos'),
    (M + 560, FLAVIO, 'Flávio Bolsonaro (PL)', f'{br(pf)}%', 'dos votos válidos'),
    (M + 1120, None, 'Votos válidos', milhar(int(tot['votos_validos'])), 'somados nos 7 locais'),
]
for x, cor, rot, num, sub in heros:
    if cor:
        dot(x + 11, HY - 8, cor, 22)
        txt(x + 34, HY, rot, 14, INK2)
    else:
        txt(x, HY, rot, 14, INK2)
    txt(x - 4, HY + 125, num, 58, INK, 'bold')
    txt(x, HY + 172, sub, 13, MUTED)
# fio separador entre os heróis
for x in (M + 530, M + 1090):
    ax.plot([x, x], [HY - 30, HY + 180], color=BASE, lw=1.5 * PX * 2)

# ── comparação com a zona 408 (painel em destaque) ────────────────────────
PY0, PY1 = 570, 1000
ax.add_patch(FancyBboxPatch((M - 30, PY0), W - 2 * M + 60, PY1 - PY0,
                            boxstyle='round,pad=0,rounding_size=22',
                            facecolor=PANEL, edgecolor=BASE, lw=1.5 * PX * 2, zorder=0))
txt(M, PY0 + 70, 'Paraisópolis × zona 408 inteira', 22, INK, 'bold')
dl, dfv = pl - zl, pf - zf
txt(M, PY0 + 122,
    f'Lula teve {br(abs(dl))} p.p. a mais e Flávio {br(abs(dfv))} p.p. a menos do que na zona como um todo',
    14, INK2)
for i, (rot, sub, f, l) in enumerate([
        ('Paraisópolis', f"7 locais · {tot['secoes']} seções · {milhar(int(tot['votos_validos']))} votos", pf, pl),
        ('Zona 408 inteira', f"{zona['secoes']} seções · {milhar(int(zona['votos_validos']))} votos", zf, zl)]):
    y = PY0 + 205 + i * 120
    txt(M, y, rot, 15, INK, 'bold')
    txt(W - M, y, sub, 12.5, INK2, ha='right')  # INK2: MUTED fica em 4,4:1 sobre o painel
    haltere(y + 55, f, l, bold=True, size=15, d=30)

# ── os 7 locais ───────────────────────────────────────────────────────────
SY = 1090
txt(M, SY, 'Os 7 locais, do maior para o menor % de Lula', 22, INK, 'bold')
# legenda sempre visível (marca colorida + texto neutro)
LY = SY + 58
dot(M + 11, LY - 7, LULA, 22); txt(M + 34, LY, 'Lula (PT)', 14, INK)
dot(M + 211, LY - 7, FLAVIO, 22); txt(M + 234, LY, 'Flávio Bolsonaro (PL)', 14, INK)
txt(W - M, LY, '% dos votos válidos', 13, MUTED, ha='right')

GY0 = SY + 130            # topo da área de plotagem (rótulos de eixo)
ROW = 122
GY1 = GY0 + 40 + ROW * len(locais)
for t in range(20, 75, 10):
    ax.plot([X(t), X(t)], [GY0 + 22, GY1], color=GRID, lw=1.2 * PX * 2, zorder=0)
    txt(X(t), GY0, f'{t}%', 12, MUTED, ha='center')
# referências: posição da zona 408 (fio sólido, não tracejado)
for v, rot in ((zl, f'Lula na zona 408: {br(zl)}'), (zf, f'Flávio na zona 408: {br(zf)}')):
    ax.plot([X(v), X(v)], [GY0 + 22, GY1], color='#6b6a64', lw=1.6 * PX * 2, zorder=1)
    txt(X(v), GY1 + 34, rot, 11.5, INK2, ha='center')

for i, r in enumerate(locais):
    y = GY0 + 40 + ROW * i
    nome = nome_bonito(r['local'])
    txt(M, y + 36, nome, 15, INK, 'bold')
    txt(W - M, y + 36, f"{r['secoes']} seções · {milhar(int(r['votos_validos']))} votos", 12.5, MUTED, ha='right')
    haltere(y + 84, float(r['pct_flavio']), float(r['pct_lula']), size=13.5)

# ── rodapé ────────────────────────────────────────────────────────────────
FY = GY1 + 110
ax.plot([M, W - M], [FY - 40, FY - 40], color=BASE, lw=1.2 * PX * 2)
txt(M, FY, 'Locais de votação a menos de 500 m do centro de Paraisópolis, todos na zona 408. A zona 408 cobre',
    11.5, MUTED)
txt(M, FY + 34, 'também locais fora da comunidade. Percentuais sobre votos válidos; candidatura indeferida (nº 28) excluída.',
    11.5, MUTED)
txt(M, FY + 84, 'Fonte: TSE, votação por seção (1º turno 2026) · rodado.xyz/dataviz/eleicoes', 11.5, MUTED)

fig.savefig(AQUI / 'cartaz_paraisopolis_presidente_2026_dark.png', dpi=DPI, facecolor=SURFACE)
print('ok', fig.get_size_inches() * DPI, 'rodapé em y =', FY + 84)
