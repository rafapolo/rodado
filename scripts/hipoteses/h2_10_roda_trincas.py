#!/usr/bin/env python3
"""Roda TODAS as trincas de familia possiveis no painel-mestre, de uma vez.

A ideia que torna isto viavel: uma trinca de familias e um trio de colunas do
painel. Nao e preciso uma query por hipotese -- o painel ja esta extraido, e o
custo de mais uma hipotese e uma correlacao em numpy.

Metodo, igual ao das baterias H01-H62 para o resultado ser comparavel:
  * Spearman (rank), nunca Pearson cru -- as distribuicoes municipais tem cauda
    pesada e um outlier vira "achado".
  * parcial residualizando log(populacao), log(PIB per capita) e efeito fixo de
    UF. Sem isso metade das correlacoes e "municipio grande tem mais de tudo".
  * so colunas INTENSIVAS (taxa/share/per capita). Contagem crua entra na
    correlacao pelo tamanho do municipio e o achado e falso.
  * p por transformada z de Fisher com gl corrigido pelos controles, e
    Benjamini-Hochberg sobre TODOS os pares testados. Rodar 5 mil pares e
    reportar o maior |r| sem correcao seria garimpo de ruido.

  python3 scripts/hipoteses/h2_10_roda_trincas.py
"""
import itertools, json, math, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml

REPO = Path(__file__).resolve().parent.parent.parent
PAINEL = REPO / "tasks" / "hipoteses_resultado" / "hipoteses2" / "painel_mestre.csv"
MAPA   = REPO / "scripts" / "hipoteses" / "h2_familias_colunas.yaml"
OUT    = REPO / "tasks" / "hipoteses_resultado" / "hipoteses2"
N_MIN  = 500          # abaixo disso o parcial nao tem gl para nada
R_MIN  = 0.10         # piso do glifo 🟠 em docs/hipoteses/respostas.md
Q_MAX  = 0.01         # FDR

def phi(x):  # normal padrao acumulada, sem scipy
    return 0.5 * math.erfc(-x / math.sqrt(2))

def rank(a):
    return pd.Series(a).rank().to_numpy()

def bh(ps):
    """Benjamini-Hochberg: devolve q na ordem original."""
    n = len(ps); ordem = np.argsort(ps); q = np.empty(n); menor = 1.0
    for i in range(n - 1, -1, -1):
        k = ordem[i]
        menor = min(menor, ps[k] * n / (i + 1))
        q[k] = menor
    return q

def main():
    mapa = yaml.safe_load(MAPA.read_text(encoding="utf-8"))
    d = pd.read_csv(PAINEL, low_memory=False).replace([np.inf, -np.inf], np.nan)

    # --- controles: log-pop, log-PIB pc, efeito fixo de UF
    # log-area entra SEMPRE, nao so quando as duas pernas sao extensivas: metade
    # do painel e normalizada por hectare ou por area, e sem este controle o
    # "1/area" compartilhado vira correlacao sozinho.
    ctl = [np.log(d["populacao"].clip(lower=1)), np.log(d["pib_pc"].clip(lower=1)),
           np.log(d["area_total"].clip(lower=1))]
    ufs = pd.get_dummies(d["sigla_uf"], drop_first=True).astype(float)
    C = np.column_stack([np.ones(len(d))] + ctl + [ufs.to_numpy()])
    C_ok = np.isfinite(C).all(axis=1)

    # --- colunas intensivas por familia
    col_fam, colunas = {}, []
    for fam, v in mapa["familias"].items():
        for c in v["intensivas"]:
            if d[c].notna().sum() >= N_MIN and d[c].nunique() > 5:
                col_fam[c] = fam; colunas.append(c)
    fams = sorted(set(col_fam.values()))
    print(f"{len(colunas)} colunas intensivas em {len(fams)} familias")
    print(f"pares cruzando familias: {sum(1 for a,b in itertools.combinations(colunas,2) if col_fam[a]!=col_fam[b])}")

    DUPLICATAS = {frozenset(par) for par in mapa["duplicatas_conceituais"]}
    REGISTRO = set(mapa["metricas_de_registro"])
    R = {c: rank(d[c].to_numpy()) for c in colunas}
    OKS = {c: d[c].notna().to_numpy() & C_ok for c in colunas}

    linhas = []
    for a, b in itertools.combinations(colunas, 2):
        if col_fam[a] == col_fam[b]:
            continue
        m = OKS[a] & OKS[b]
        n = int(m.sum())
        if n < N_MIN:
            continue
        x, y = rank(d[a].to_numpy()[m]), rank(d[b].to_numpy()[m])   # rank no subconjunto
        bruto = float(np.corrcoef(x, y)[0, 1])
        X = C[m]
        coef, *_ = np.linalg.lstsq(X, np.column_stack([x, y]), rcond=None)
        rx, ry = (np.column_stack([x, y]) - X @ coef).T
        sx, sy = rx.std(), ry.std()
        parcial = float((rx @ ry) / (len(rx) * sx * sy)) if sx > 0 and sy > 0 else np.nan
        k = X.shape[1]
        if not np.isfinite(parcial) or n - k - 3 <= 0:
            continue
        z = math.atanh(max(min(parcial, 0.999999), -0.999999)) * math.sqrt(n - k - 3)
        p = 2 * (1 - phi(abs(z)))
        tipo = ("duplicata" if frozenset((a, b)) in DUPLICATAS
                else "registro" if (a in REGISTRO or b in REGISTRO) else "achado")
        linhas.append((col_fam[a], col_fam[b], a, b, n, round(bruto, 4), round(parcial, 4), p, tipo))

    df = pd.DataFrame(linhas, columns=["fam_a","fam_b","col_a","col_b","n","r_bruto","r_parcial","p","tipo"])
    df["q"] = bh(df["p"].to_numpy())
    df["sobrevive"] = ((df["q"] < Q_MAX) & (df["r_parcial"].abs() >= R_MIN)
                       & (df["tipo"] != "duplicata"))
    df = df.sort_values("r_parcial", key=abs, ascending=False)
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "pares.csv", index=False)
    print(f"\n{len(df)} pares testados | {int(df.sobrevive.sum())} sobrevivem "
          f"(|r_parcial| >= {R_MIN} e FDR q < {Q_MAX})")

    # --- trincas: as tres pernas precisam sobreviver entre si
    viv = df[df.sobrevive]
    print("   por tipo:", df[df.sobrevive].tipo.value_counts().to_dict())
    par_fam = {}
    for _, r in viv.iterrows():
        ch = frozenset((r.fam_a, r.fam_b))
        if ch not in par_fam or abs(r.r_parcial) > abs(par_fam[ch].r_parcial):
            par_fam[ch] = r
    trincas = []
    for t in itertools.combinations(fams, 3):
        pernas = [frozenset(p) for p in itertools.combinations(t, 2)]
        vivas = [par_fam[p] for p in pernas if p in par_fam]
        trincas.append({
            "familias": "+".join(t), "pernas_vivas": len(vivas),
            "forca_min": round(min(abs(v.r_parcial) for v in vivas), 3) if len(vivas) == 3 else None,
            "detalhe": " | ".join(f"{v.col_a}×{v.col_b} {v.r_parcial:+.2f}" for v in vivas),
        })
    tr = pd.DataFrame(trincas).sort_values(["pernas_vivas","forca_min"], ascending=False)
    tr.to_csv(OUT / "trincas.csv", index=False)
    c = tr.pernas_vivas.value_counts().sort_index(ascending=False)
    print(f"{len(tr)} trincas de familia possiveis (C({len(fams)},3))")
    for k, v in c.items(): print(f"   {v:5d} trincas com {k}/3 pernas vivas")

if __name__ == "__main__":
    sys.exit(main())
