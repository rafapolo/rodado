#!/usr/bin/env python3
"""Funde os tres paineis municipais ja extraidos do beelink num painel unico.

  20260906/painel.csv        164 colunas  (bateria H01-H19)
  inedito/painel_inedito.csv 207 colunas  (bateria H20-H36)
  familias/painel_familias.csv 229 colunas (bateria H46-H62)

Nenhum e superconjunto dos outros. A fusao e por id_municipio, e coluna repetida
so entra uma vez -- conferindo antes que as duas versoes batem, porque duas
extracoes da mesma coluna em datas diferentes podem divergir e a divergencia
silenciosa seria pior que o erro.

  python3 scripts/hipoteses/h2_00_painel_mestre.py
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
SRC  = REPO / "tasks" / "hipoteses_resultado"
OUT  = SRC / "hipoteses2" / "painel_mestre.csv"
FONTES = ["20260906/painel.csv", "inedito/painel_inedito.csv", "familias/painel_familias.csv"]

def main():
    base = None
    for f in FONTES:
        d = pd.read_csv(SRC / f, low_memory=False)
        d = d[d["id_municipio"].notna()].copy()
        d["id_municipio"] = d["id_municipio"].astype("int64")
        d = d.drop_duplicates("id_municipio").set_index("id_municipio")
        if base is None:
            base = d; print(f"{f}: {d.shape[1]} colunas, {len(d)} municipios (base)")
            continue
        novas = [c for c in d.columns if c not in base.columns]
        repetidas = [c for c in d.columns if c in base.columns]
        # confere as repetidas: divergencia acima de 1% das linhas vira aviso
        diverg = []
        for c in repetidas:
            a, b = base[c].align(d[c], join="inner")
            if a.dtype.kind in "fi" and b.dtype.kind in "fi":
                dif = ~np.isclose(a.astype(float), b.astype(float), rtol=1e-6, equal_nan=True)
            else:
                dif = a.astype(str) != b.astype(str)
            if dif.mean() > 0.01:
                diverg.append((c, round(float(dif.mean()), 3)))
        base = base.join(d[novas], how="outer")
        print(f"{f}: +{len(novas)} colunas novas, {len(repetidas)} repetidas"
              + (f", DIVERGEM: {diverg}" if diverg else ", repetidas conferem"))
    base = base.sort_index()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    base.to_csv(OUT)
    print(f"\n{OUT.relative_to(REPO)}: {base.shape[0]} municipios x {base.shape[1]} colunas")

if __name__ == "__main__":
    sys.exit(main())
