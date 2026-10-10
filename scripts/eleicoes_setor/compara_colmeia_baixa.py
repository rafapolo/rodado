import csv, gzip, random, sys, os, urllib.request, concurrent.futures as cf
base, out = sys.argv[1], sys.argv[2]
UF = {'11':'RO','12':'AC','13':'AM','14':'RR','15':'PA','16':'AP','17':'TO','21':'MA','22':'PI','23':'CE','24':'RN','25':'PB','26':'PE','27':'AL','28':'SE','29':'BA','31':'MG','32':'ES','33':'RJ','35':'SP','41':'PR','42':'SC','43':'RS','50':'MS','51':'MT','52':'GO','53':'DF'}
pref = set()
for r in csv.DictReader(gzip.open(base, 'rt')): pref.add(r['id_setor_censitario'][:11])
pref = sorted(pref); random.seed(7)
alvo = [p for p in pref if p[:2] == '12'] + random.sample(pref, 700)
def pega(p):
    f = f"{out}/{p}.json"
    if os.path.exists(f): return 200
    try:
        d = urllib.request.urlopen(f"https://colmeiabrasil.github.io/colmeia/dados/setores/{UF[p[:2]]}/{p}.json", timeout=30).read()
        open(f, 'wb').write(d); return 200
    except Exception as e: return getattr(e, 'code', str(e))
with cf.ThreadPoolExecutor(8) as ex: res = list(ex.map(pega, set(alvo)))
import collections; print(len(pref), 'prefixos nossos;', collections.Counter(res))
