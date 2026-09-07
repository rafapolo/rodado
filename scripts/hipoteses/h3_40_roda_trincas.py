#!/usr/bin/env python3
"""As trincas de familia com o painel ESTENDIDO pelo lote h3.

  python3 scripts/hipoteses/h3_40_roda_trincas.py

Mesmo metodo de scripts/hipoteses/h2_10_roda_trincas.py -- Spearman, parcial
residualizando log-populacao, log-PIB pc, log-area e efeito fixo de UF, FDR de
Benjamini-Hochberg sobre todos os pares -- com duas diferencas:

  1. entra a familia `politica`, que nao tinha coluna nenhuma antes;
  2. as contagens cruas do lote (casos de dengue, matriculas, filiados) viram
     TAXA antes de entrar. Contagem crua correlaciona com o tamanho do
     municipio, e o achado sai falso.
"""
import itertools, math, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml

REPO = Path(__file__).resolve().parent.parent.parent
PAINEL = REPO/"tasks"/"hipoteses_resultado"/"hipoteses2"/"painel_mestre_h3.csv"
MAPA2  = REPO/"scripts"/"hipoteses"/"h2_familias_colunas.yaml"
MAPA3  = REPO/"scripts"/"hipoteses"/"h3_familias_colunas.yaml"
OUT    = REPO/"tasks"/"hipoteses_resultado"/"hipoteses3"
N_MIN, R_MIN, Q_MAX = 500, 0.10, 0.01

phi  = lambda x: 0.5*math.erfc(-x/math.sqrt(2))
rank = lambda a: pd.Series(a).rank().to_numpy()

def bh(ps):
    n=len(ps); o=np.argsort(ps); q=np.empty(n); menor=1.0
    for i in range(n-1,-1,-1):
        k=o[i]; menor=min(menor, ps[k]*n/(i+1)); q[k]=menor
    return q

def main():
    m2=yaml.safe_load(MAPA2.read_text(encoding="utf-8"))
    m3=yaml.safe_load(MAPA3.read_text(encoding="utf-8"))
    d=pd.read_csv(PAINEL, low_memory=False).replace([np.inf,-np.inf], np.nan)

    # --- deriva taxa a partir das contagens cruas do lote
    pop=d["populacao"].replace(0,np.nan)
    derivadas={}
    for crua, nova in m3["derivar_por_populacao"].items():
        if crua not in d: continue
        if nova.startswith("share_"):
            base={"share_60mais":"msp_populacao","share_fibra":"bl_acessos",
                  "share_classe_comum":"esp_matriculas","share_docente_rural":"docentes",
                  "share_obesidade":"sisvan_n"}[nova]
            d[nova]=d[crua]/d[base].replace(0,np.nan)
        else:
            mult=100000 if nova.endswith("100k") else (1000 if "1000hab" in nova else
                  (100 if "100hab" in nova else 1))
            d[nova]=d[crua]/pop*mult
        derivadas[nova]=crua
    print(f"{len(derivadas)} taxas derivadas das contagens cruas")

    # --- coluna -> familia, fundindo os dois mapas + as derivadas
    col_fam={}
    for m in (m2,m3):
        for fam,v in m["familias"].items():
            for c in v["intensivas"]: col_fam[c]=fam
    for nova,crua in derivadas.items():
        for m in (m2,m3):
            for fam,v in m["familias"].items():
                if crua in v.get("extensivas",[]) or crua in v.get("intensivas",[]):
                    col_fam[nova]=fam
    colunas=[c for c in col_fam if c in d.columns
             and d[c].notna().sum()>=N_MIN and d[c].nunique()>5]
    fams=sorted({col_fam[c] for c in colunas})
    print(f"{len(colunas)} colunas em {len(fams)} familias "
          f"(antes: 107 em 21) | familias novas: {set(fams)-set(yaml.safe_load(MAPA2.read_text(encoding='utf-8'))['familias'])}")

    # guardas: duplicata conceitual sai; metrica de registro fica marcada
    DUP={frozenset(par) for m in (m2,m3) for par in m.get("duplicatas_conceituais",[])}
    REG=set().union(*[set(m.get("metricas_de_registro",{})) for m in (m2,m3)])
    CONS=set()
    for m in (m2,m3):
        for grupo in m.get("mesmo_construto",{}).values():
            CONS |= {frozenset(x) for x in itertools.combinations(grupo,2)}
    print(f"guardas: {len(DUP)} pares de duplicata, {len(REG)} metricas de registro, "
          f"{len(CONS)} pares do mesmo construto")

    ctl=[np.log(d["populacao"].clip(lower=1)), np.log(d["pib_pc"].clip(lower=1)),
         np.log(d["area_total"].clip(lower=1))]
    ufs=pd.get_dummies(d["sigla_uf"], drop_first=True).astype(float)
    C=np.column_stack([np.ones(len(d))]+ctl+[ufs.to_numpy()])
    C_ok=np.isfinite(C).all(axis=1)
    OKS={c: d[c].notna().to_numpy() & C_ok for c in colunas}

    linhas=[]
    for a,b in itertools.combinations(colunas,2):
        if col_fam[a]==col_fam[b]: continue
        m=OKS[a]&OKS[b]; n=int(m.sum())
        if n<N_MIN: continue
        x,y=rank(d[a].to_numpy()[m]), rank(d[b].to_numpy()[m])
        bruto=float(np.corrcoef(x,y)[0,1])
        X=C[m]
        coef,*_=np.linalg.lstsq(X, np.column_stack([x,y]), rcond=None)
        rx,ry=(np.column_stack([x,y])-X@coef).T
        sx,sy=rx.std(), ry.std()
        if sx<=0 or sy<=0: continue
        parc=float((rx@ry)/(len(rx)*sx*sy)); k=X.shape[1]
        if not np.isfinite(parc) or n-k-3<=0: continue
        z=math.atanh(max(min(parc,.999999),-.999999))*math.sqrt(n-k-3)
        tipo=("duplicata" if frozenset((a,b)) in DUP
              else "construto" if frozenset((a,b)) in CONS
              else "registro" if (a in REG or b in REG) else "achado")
        linhas.append((col_fam[a],col_fam[b],a,b,n,round(bruto,4),round(parc,4),2*(1-phi(abs(z))),tipo))

    df=pd.DataFrame(linhas,columns=["fam_a","fam_b","col_a","col_b","n","r_bruto","r_parcial","p","tipo"])
    df["q"]=bh(df["p"].to_numpy())
    df["sobrevive"]=(df.q<Q_MAX)&(df.r_parcial.abs()>=R_MIN)&(~df.tipo.isin(["duplicata"]))
    df=df.sort_values("r_parcial",key=abs,ascending=False)
    OUT.mkdir(parents=True,exist_ok=True); df.to_csv(OUT/"pares_h3.csv",index=False)
    print(f"\n{len(df):,} pares testados | {int(df.sobrevive.sum()):,} sobrevivem".replace(",","."))
    print("   por tipo:", df[df.sobrevive].tipo.value_counts().to_dict(),
          "| duplicatas barradas:", int((df.tipo=="duplicata").sum()))

    viv=df[df.sobrevive]; melhor={}
    for _,r in viv.iterrows():
        ch=frozenset((r.fam_a,r.fam_b))
        if ch not in melhor or abs(r.r_parcial)>abs(melhor[ch].r_parcial): melhor[ch]=r
    tri=[]
    for t in itertools.combinations(fams,3):
        vivas=[melhor[p] for p in (frozenset(x) for x in itertools.combinations(t,2)) if p in melhor]
        tri.append({"familias":"+".join(t),"pernas_vivas":len(vivas),
                    "forca_min":round(min(abs(v.r_parcial) for v in vivas),3) if len(vivas)==3 else None,
                    "detalhe":" | ".join(f"{v.col_a}×{v.col_b} {v.r_parcial:+.2f}" for v in vivas)})
    tr=pd.DataFrame(tri).sort_values(["pernas_vivas","forca_min"],ascending=False)
    tr.to_csv(OUT/"trincas_h3.csv",index=False)
    print(f"{len(tr):,} trincas de familia (C({len(fams)},3))".replace(",","."))
    for k,v in tr.pernas_vivas.value_counts().sort_index(ascending=False).items():
        print(f"   {v:5d} com {k}/3 pernas vivas")

if __name__=="__main__":
    sys.exit(main())
