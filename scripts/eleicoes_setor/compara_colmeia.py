import csv, gzip, json, glob, sys, os, math, collections, statistics as st
base, dsetor, repo, basemun = sys.argv[1:5]
UF = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
nosso = {r['id_setor_censitario']: r for r in csv.DictReader(gzip.open(base, 'rt'))}
locais = {}
def loc(uf):
    if uf not in locais: locais[uf] = json.load(open(f'{repo}/dados/locais/{uf}.json'))
    return locais[uf]
c = collections.Counter(); ddist = []; dvm = []; dpot = []; ex = []; ex2 = []
for f in glob.glob(dsetor + '/*.json'):
    d = json.load(open(f))
    for cd, s in d.items():
        c['setores colmeia'] += 1
        n = nosso.get(cd)
        if not n: c['setor ausente do nosso'] += 1; continue
        L = loc(UF[cd[:2]])
        deles = {(round(L[i][2], 5), round(L[i][3], 5)) for i in s.get('lv', [])}
        meus = {tuple(round(float(x), 5) for x in p.split(',')) for p in n['pontos'].split(';')}
        if not deles: c['colmeia sem local'] += 1; continue
        c['comparados'] += 1
        perto = lambda a, B: any(abs(a[0]-b[0]) <= 3e-5 and abs(a[1]-b[1]) <= 3e-5 for b in B)
        so_deles = [a for a in deles if not perto(a, meus)]; so_meus = [a for a in meus if not perto(a, deles)]
        iguais = not so_deles and not so_meus
        if iguais: c['mesmos locais'] += 1
        elif len(so_deles) < len(deles) or len(so_meus) < len(meus):
            c['locais em parte iguais'] += 1
            c['  nós temos local a mais'] += bool(so_meus) and not so_deles
            c['  eles têm local a mais'] += bool(so_deles) and not so_meus
            c['  os dois lados têm local exclusivo'] += bool(so_deles) and bool(so_meus)
            if len(ex2) < 5: ex2.append((cd, s.get('dist'), n['dist'], so_deles[:2], so_meus[:2]))
        else:
            c['locais diferentes'] += 1
            if len(ex) < 6: ex.append((cd, s.get('dist'), n['dist'], sorted(deles)[:2], sorted(meus)[:2]))
        if s.get('dist') is not None:
            dd = float(n['dist']) - s['dist']; ddist.append(dd)
            if abs(dd) <= 1: c['dist igual (±1 m)'] += 1
            elif abs(dd) <= 0.01 * max(s['dist'], 100): c['dist difere <1%'] += 1
            else: c['dist difere mais'] += 1
        if iguais and n['vw'] and float(n['vw']) > 0:
            l, f_, v, apt = (float(n[k] or 0) for k in ('l', 'f', 'validos', 'aptos'))
            lw, fw, vw, abnw, aptw = (float(n[k] or 0) for k in ('lw', 'fw', 'vw', 'abnw', 'aptw'))
            dif = (fw - lw) / vw * v
            vm = int(dif // 2) + 1 if dif > 0 else 0
            pot = abnw / aptw * apt if aptw else None
            if s.get('vm') is not None:
                c['vm comparados'] += 1; e = vm - s['vm']; dvm.append(e)
                if abs(e) <= 1: c['vm igual (±1)'] += 1
                elif abs(e) <= 0.02 * max(s['vm'], 50): c['vm difere <2%'] += 1
                else: c['vm difere mais'] += 1
            if s.get('pot') is not None and pot is not None:
                c['pot comparados'] += 1; e = pot - s['pot']; dpot.append(e)
                if abs(e) <= 1: c['pot igual (±1)'] += 1
                elif abs(e) <= 0.02 * max(s['pot'], 50): c['pot difere <2%'] += 1
                else: c['pot difere mais'] += 1
for k, v in c.items(): print(f'{v:>8}  {k}')
q = lambda x: [round(v, 1) for v in st.quantiles(x, n=20)][::3] if len(x) > 20 else x
print('dist nosso-colmeia (m), quantis:', q(ddist)); print('vm nosso-colmeia, quantis:', q(dvm)); print('pot nosso-colmeia, quantis:', q(dpot))
print('exemplos parciais:'); [print('  ', e) for e in ex2]
print('exemplos de locais diferentes:'); [print('  ', e) for e in ex]
# municípios: resultado oficial
mun = {r['id_municipio']: r for r in csv.DictReader(gzip.open(basemun, 'rt'))}
cm = collections.Counter(); dl = []; exm = []
for f in glob.glob(f'{repo}/dados/municipios/*.json'):
    for ib, m in json.load(open(f)).items():
        n = mun.get(ib)
        if not n or m.get('l26') is None: cm['sem par'] += 1; continue
        v = float(n['validos']); l = 100 * float(n['l'] or 0) / v; fl = 100 * float(n['f'] or 0) / v
        ab = 100 * float(n['abst']) / float(n['aptos']); bn = 100 * float(n['bn']) / float(n['comp'])
        cm['municipios'] += 1
        ok = abs(l - m['l26']) <= 0.06 and abs(fl - m['f26']) <= 0.06
        cm['lula e flavio iguais (±0,05 pp)'] += ok
        cm['abstencao igual (±0,05 pp)'] += abs(ab - m['ab']) <= 0.06
        cm['brancos+nulos igual (±0,05 pp, base comparecimento)'] += abs(bn - m['bn']) <= 0.06
        dl.append(abs(l - m['l26']))
        if not ok and len(exm) < 12: exm.append((ib, m['n'], m['l26'], round(l,1), m['f26'], round(fl,1), int(v)))
for k, v in cm.items(): print(f'{v:>8}  {k}')
print('maior diferença de % Lula por município:', round(max(dl), 2))
print('municípios que diferem (ibge, nome, lula colmeia, lula nosso, flavio colmeia, flavio nosso, válidos nosso):'); [print('  ', e) for e in exm]
