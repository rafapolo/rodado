import csv, re
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
rows = list(csv.DictReader(open('paraisopolis_locais_presidente_2026.csv')))
BG, INK, MUTED, GRID = '#faf7f2', '#1c1c1c', '#6b6660', '#e4dfd6'
L, F = '#c0392b', '#2166ac'
loc = sorted([r for r in rows if r['nivel'] == 'local'], key=lambda r: float(r['pct_lula']))
tot = next(r for r in rows if r['nivel'] == 'paraisopolis_total'); z = next(r for r in rows if r['nivel'] == 'zona_408_total')
fig = plt.figure(figsize=(12, 16), facecolor=BG)
fig.text(.06, .945, 'PARAISÓPOLIS VOTOU ASSIM', fontsize=34, weight='bold', color=INK, family='DejaVu Sans')
fig.text(.06, .915, 'Presidente 2026, 1º turno · 93 seções em 7 locais de votação da zona eleitoral 408 · São Paulo', fontsize=13, color=MUTED)
fig.text(.06, .845, f"{float(tot['pct_lula']):.1f}%", fontsize=64, weight='bold', color=L)
fig.text(.06, .825, 'Lula', fontsize=16, color=INK)
fig.text(.40, .845, f"{float(tot['pct_flavio']):.1f}%", fontsize=64, weight='bold', color=F)
fig.text(.40, .825, 'Flávio Bolsonaro', fontsize=16, color=INK)
fig.text(.70, .855, f"{int(tot['votos_validos']):,}".replace(',', '.'), fontsize=30, weight='bold', color=INK)
fig.text(.70, .835, 'votos válidos nos 7 locais', fontsize=13, color=MUTED)
fig.text(.70, .812, f"Zona 408 inteira: Lula {float(z['pct_lula']):.1f}% · Flávio {float(z['pct_flavio']):.1f}%", fontsize=11, color=MUTED)
ax = fig.add_axes([.31, .12, .62, .64], facecolor=BG)
items = [(r['local'].title().replace('Ceu', 'CEU').replace('Emef', 'EMEF').replace('Emei', 'EMEI').replace('Cei ', 'CEI ').replace('E.E.', 'E.E.').replace('Etec', 'ETEC'), float(r['pct_lula']), float(r['pct_flavio']), int(r['secoes'])) for r in loc]
items += [('PARAISÓPOLIS (7 locais)', float(tot['pct_lula']), float(tot['pct_flavio']), 93), ('Zona 408 inteira', float(z['pct_lula']), float(z['pct_flavio']), 474)]
for i, (n, l, f, s) in enumerate(items):
    y = i + (0.8 if i >= len(loc) else 0) + (0.8 if i == len(loc)+1 else 0)
    bold = i >= len(loc)
    ax.plot([f, l], [y, y], color=GRID, lw=5, solid_capstyle='round', zorder=1)
    ax.scatter([l], [y], s=170, color=L, zorder=3, edgecolor=BG, lw=2); ax.scatter([f], [y], s=170, color=F, zorder=3, edgecolor=BG, lw=2)
    ax.text(l+1.4, y, f'{l:.1f}', va='center', fontsize=12, color=INK, weight='bold' if bold else 'normal')
    ax.text(f-1.4, y, f'{f:.1f}', va='center', ha='right', fontsize=12, color=INK, weight='bold' if bold else 'normal')
    ax.text(-0.02, y, f'{n}\n{s} seções', transform=ax.get_yaxis_transform(), ha='right', va='center', fontsize=11, color=INK, weight='bold' if bold else 'normal', linespacing=1.3)
ax.set_xlim(15, 78); ax.set_ylim(-.8, len(items)+1.2); ax.invert_yaxis()
ax.set_yticks([]); ax.xaxis.tick_top(); ax.set_xticks([20, 30, 40, 50, 60, 70]); ax.set_xticklabels([f'{t}%' for t in (20, 30, 40, 50, 60, 70)], color=MUTED, fontsize=11)
ax.grid(axis='x', color=GRID, lw=1); ax.set_axisbelow(True); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.text(0.0, 1.075, '● Flávio Bolsonaro (PL)      ● Lula (PT)', transform=ax.transAxes, fontsize=0.1, color=BG)
fig.text(.31, .792, '●', color=F, fontsize=14); fig.text(.327, .793, 'Flávio Bolsonaro (PL)', fontsize=12, color=INK)
fig.text(.50, .792, '●', color=L, fontsize=14); fig.text(.517, .793, 'Lula (PT)', fontsize=12, color=INK)
fig.text(.06, .075, 'Locais de votação a menos de 500 m do centro de Paraisópolis, todos na zona 408. A zona 408 cobre também\n'
         'outros locais fora da comunidade. Percentuais sobre votos válidos; candidatura indeferida (nº 28) excluída.', fontsize=10, color=MUTED, linespacing=1.5)
fig.text(.06, .035, 'Fonte: TSE, votação por seção (1º turno 2026) · rodado.xyz/dataviz/eleicoes', fontsize=10, color=MUTED)
for t in fig.findobj(matplotlib.text.Text):
    x=t.get_text()
    if re.fullmatch(r'[\d.]+%?',x) and x.count('.')==1 and x!='24.761': t.set_text(x.replace('.',','))
    elif 'Zona 408 inteira:' in x: t.set_text(x.replace('.',','))
fig.savefig('cartaz_paraisopolis_presidente_2026.png', dpi=150, facecolor=BG)
