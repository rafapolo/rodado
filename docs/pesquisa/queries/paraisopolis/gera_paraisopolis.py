"""Presidente 2026 (1º turno) nos locais de votação de Paraisópolis, São Paulo.
Fonte: dados do mapa rodado.xyz/plataformas/eleicoes (secoes/locais.json + SP.json, TSE).
Paraisópolis = locais de votação a <= RAIO_MAX graus-L1 do centro da favela; todos caem na zona 408.
"""
import csv, json, os, sys
BASE = os.path.expanduser('~/Projetos/xyz/dataviz/eleicoes/secoes')
CENTRO = (-23.6228, -46.7295)
RAIO_MAX = 0.006
d = json.load(open(f'{BASE}/locais.json')); sp = json.load(open(f'{BASE}/SP.json'))
cands = d['c']; nc = len(cands)
nome = [f'{n} ({p})' for n, p in cands]
sps = d['ufs'].index('SP')
m = la = lo = 0; locais = {}; zona = [0]*nc; zona_n = 0
for i in range(len(d['u'])):
    m += d['m'][i]; la += d['lat'][i]; lo += d['lon'][i]
    if d['u'][i] != sps or d['muns'][m] != 'São Paulo': continue
    if d['z'][i] == 408:
        for k in range(nc): zona[k] += d['v'][k][i]
        zona_n += d['n'][i]
    if abs(la/1e5-CENTRO[0]) + abs(lo/1e5-CENTRO[1]) <= RAIO_MAX:
        locais[(d['z'][i], d['lv'][i])] = dict(lat=la/1e5, lon=lo/1e5, n=d['n'][i], v=[d['v'][k][i] for k in range(nc)])
mi = d['muns'].index('São Paulo')
nomes = {(r[0], r[1]): r[3] for r in sp if r[2] == mi}
cab = ['zona', 'local_num', 'local', 'lat', 'lon', 'secao'] + nome + ['votos_validos', 'pct_lula', 'pct_flavio', 'lula_2022_1t_pct', 'bolsonaro_2022_1t_pct']
rows = []; tot = {}
def pct(a, t): return round(100*a/t, 2) if t else ''
for (z, lv), L in sorted(locais.items()):
    for r in next(x for x in sp if x[0] == z and x[1] == lv and x[2] == mi)[4]:
        v = r[1:1+nc]; t = sum(v)
        rows.append([z, lv, nomes[(z, lv)], L['lat'], L['lon'], r[0]] + v + [t, pct(v[1], t), pct(v[0], t),
                     '' if r[1+nc] is None else r[1+nc]/100, '' if r[2+nc] is None else r[2+nc]/100])
with open('paraisopolis_secoes_presidente_2026.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(cab); w.writerows(rows)
# resumo por local + paraisópolis + zona 408
res = []
def lin(rot, z, num, loc, n, v):
    t = sum(v); res.append([rot, z, num, loc, n] + v + [t, pct(v[1], t), pct(v[0], t)])
for (z, lv), L in sorted(locais.items()): lin('local', z, lv, nomes[(z, lv)], L['n'], L['v'])
tv = [sum(L['v'][k] for L in locais.values()) for k in range(nc)]
lin('paraisopolis_total', 408, '', 'Paraisópolis (7 locais)', sum(L['n'] for L in locais.values()), tv)
lin('zona_408_total', 408, '', 'Zona 408 inteira', zona_n, zona)
with open('paraisopolis_locais_presidente_2026.csv', 'w', newline='') as f:
    w = csv.writer(f); w.writerow(['nivel', 'zona', 'local_num', 'local', 'secoes'] + nome + ['votos_validos', 'pct_lula', 'pct_flavio']); w.writerows(res)
for r in res: print(r[0], r[3], r[4], 'L', r[-2], 'F', r[-1], 'validos', r[-3])
print(len(rows), 'secoes')
