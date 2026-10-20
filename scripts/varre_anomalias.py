#!/usr/bin/env python3
"""Varredura de anomalias no espelho pelos metadados dos parquet — sem ler os dados.

`parquet_metadata()` traz min, max e nulos de cada coluna por row group. Somados por
tabela, eles acusam em ~15 s, nas ~1.600 tabelas do beelink, o que só aparece
consultando: ano e mês trocados, data impossível, valor de quatrilhões, sentinela
(-999, 99999999), coluna 100% vazia, quantidade negativa. A lista é de candidatos:
cada um precisa ser medido de verdade antes de virar gotcha (docs/context/gotchas/).
Foi assim que saíram, em 2026-10-20, IGP com ano/mes trocados, CNJ com médias
corrompidas, ESTBAN 2025 quebrada, ONS em MWmed x 1e8 e PE/2009 com R$ 15 quatrilhões.

    python3 scripts/varre_anomalias.py              # roda no beelink e analisa
    python3 scripts/varre_anomalias.py --so-analisa # reaproveita /tmp/varre_meta.csv
"""
import csv, collections, datetime, os, re, subprocess, sys
HOJE = datetime.date.today().isoformat()

META = "/tmp/varre_meta.csv"
HOST = os.environ.get("BEELINK_HOST", "beelink")

# roda no beelink (python3 + duckdb), uma tabela por vez; só lê metadados
REMOTO = r'''
import duckdb, os, glob, csv, sys
con = duckdb.connect()  # sem arquivo: só lê parquet
con.execute("SET threads=4; SET memory_limit='4GB'")
R = os.path.expanduser("~/rodado")
w = csv.writer(sys.stdout)
for ds in sorted(os.listdir(R)):
    if ds.startswith(('_', '.')) or not os.path.isdir(f"{R}/{ds}"): continue
    for tb in sorted(os.listdir(f"{R}/{ds}")):
        p = f"{R}/{ds}/{tb}"
        if not glob.glob(f"{p}/**/*.parquet", recursive=True): continue
        try:
            rows = con.execute(f"""SELECT path_in_schema, any_value(type),
              min(TRY_CAST(stats_min_value AS DOUBLE)), max(TRY_CAST(stats_max_value AS DOUBLE)),
              min(stats_min_value), max(stats_max_value), sum(stats_null_count), sum(row_group_num_rows)
              FROM parquet_metadata('{p}/**/*.parquet') GROUP BY path_in_schema""").fetchall()
            for r in rows: w.writerow([f"{ds}.{tb}", *r])
        except Exception as e:
            print(f"ERRO {ds}.{tb}: {str(e)[:150]}", file=sys.stderr)
'''

if "--so-analisa" not in sys.argv:
    with open(META, "w") as f:
        subprocess.run(["ssh", HOST, "nice python3 -"], input=REMOTO, text=True, stdout=f, check=True)

import csv, re, collections
rows=[]
for t,c,ty,nmin,nmax,smin,smax,nul,lin in csv.reader(open(META)):
    f=lambda x: float(x) if x not in ('',None) else None
    rows.append(dict(t=t,c=c,ty=ty,nmin=f(nmin),nmax=f(nmax),smin=smin,smax=smax,nul=int(float(nul or 0)),lin=int(float(lin or 0))))
def show(title, items, n=60):
    print(f"\n### {title} ({len(items)})")
    for r in items[:n]: print(f"  {r['t']}.{r['c']} [{r['ty']}] min={r['smin'][:24]} max={r['smax'][:24]} nulos={r['nul']}/{r['lin']}")
low=lambda r: r['c'].lower()
show("ano fora de [1800,2027]", [r for r in rows if re.fullmatch(r'(ano|year|ano_\w+|\w+_ano)', low(r)) and r['nmin'] is not None and (r['nmin']<1800 or r['nmax']>2027) and r['nmin']!=0])
show("mes fora de [1,12]", [r for r in rows if re.fullmatch(r'(mes|month|mes_\w+)', low(r)) and r['nmin'] is not None and (r['nmin']<1 or r['nmax']>12) and 'ano' not in low(r)])
show(f"data no futuro (> {HOJE}) ou < 1900", [r for r in rows if re.match(r'\d{4}-\d{2}-\d{2}', r['smax'] or '') and r['ty'] in ('INT32','INT64','INT96') and (r['smax'][:10]>HOJE or r['smin'][:4]<'1900')])
show("valor >= 1e12", [r for r in rows if r['nmax'] and r['nmax']>=1e12 and re.search(r'valor|preco|saldo|capital|vl_|receita|despesa|montante|quantidade|populacao|area', low(r)) and r['ty'] in ('DOUBLE','FLOAT','INT64','INT32')], 80)
show("negativo onde não devia", [r for r in rows if r['nmin'] is not None and r['nmin']<0 and re.search(r'^(quantidade|qtd|qt_|populacao|idade|area|numero_|n_)', low(r)) and r['ty'] in ('DOUBLE','FLOAT','INT64','INT32')], 80)
SENT={999999999,9999999999,999999999999,99999999,9999999,-999,-9999,-99999,-99,99999}
show("sentinela", [r for r in rows if r['ty'] in ('DOUBLE','FLOAT','INT64','INT32') and ((r['nmax'] in SENT) or (r['nmin'] in SENT)) and not re.fullmatch(r'(ano|mes|id_\w+|codigo\w*|cod_\w+)',low(r))], 80)
vaz=collections.defaultdict(list)
for r in rows:
    if r['lin']>1000 and r['nul']==r['lin']: vaz[r['t']].append(r['c'])
print(f"\n### colunas 100% nulas: {sum(len(v) for v in vaz.values())} em {len(vaz)} tabelas")
for t,v in sorted(vaz.items(), key=lambda x:-len(x[1]))[:50]: print(f"  {t}: {len(v)} — {', '.join(v[:8])}")
