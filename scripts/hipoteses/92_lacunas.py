#!/usr/bin/env python3
"""Fecha as lacunas que 90_analise.py deixou nas hipoteses nomeadas.

Tres coisas que o painel principal nao respondeu:

1. **H13 (perna racial)** — `v_censo_raca.csv` sai em formato longo
   (municipio x cor x instrucao) e por isso nunca entrou no merge de
   `90_analise.py`. Aqui vira share por municipio e e' testado contra a lacuna
   de genero, que era a pergunta original: composicao racial preve D4 melhor
   que renda?
2. **H08 (condicao de falseamento)** — a hipotese so vale "depois de controlar
   o IVS inicial". O parcial padrao controla populacao e PIB, nao o ponto de
   partida. Sem isso mede convergencia, nao dose.
3. **H04 (a proporcao, nao a correlacao)** — correlacionar "credores que devem
   a PGFN" com "total de credores" e' subconjunto x conjunto. O que a hipotese
   pede e' a **fatia**, comparavel ao federal.

  python3 scripts/hipoteses/92_lacunas.py <dir_do_resultado>
"""
import os, sys
import numpy as np, pandas as pd

OUT = sys.argv[1]
P = lambda f: os.path.join(OUT, f)
d = pd.read_csv(P("painel.csv"), low_memory=False).replace([np.inf, -np.inf], np.nan)

uf = pd.get_dummies(d["sigla_uf"], drop_first=True).astype(float)
BASE = pd.concat([pd.DataFrame({"lp": np.log(d.populacao.clip(lower=1)),
                                "lpib": np.log(d.pib_pc.clip(lower=1)),
                                "c": 1.0}), uf], axis=1)

def parcial(a, b, extra=None, frame=None):
    x = frame if frame is not None else d
    C = BASE if extra is None else pd.concat([BASE, extra], axis=1)
    m = x[a].notna() & x[b].notna() & C.notna().all(axis=1)
    if m.sum() < 200: return np.nan, int(m.sum())
    X = C[m].values; r = []
    for col in (a, b):
        y = pd.Series(x.loc[m, col].values).rank().values
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r.append(y - X @ beta)
    return round(float(np.corrcoef(r[0], r[1])[0, 1]), 4), int(m.sum())

def bruto(a, b, x=None):
    x = d if x is None else x
    s = x[[a, b]].dropna()
    return round(s[a].rank().corr(s[b].rank()), 4), len(s)

print("=" * 72)
print("H13 · composicao racial (Censo 2022) x lacuna salarial de genero")
print("=" * 72)
raca = pd.read_csv(P("v_censo_raca.csv"))
piv = raca.pivot_table(index="id_municipio", columns=["cor_raca", "categoria_principal"],
                       values="valor", aggfunc="sum")
tot = piv[("Total", "Total")]
r = pd.DataFrame(index=piv.index)
r["share_negra"] = (piv[("Preta", "Total")].fillna(0) + piv[("Parda", "Total")].fillna(0)) / tot
r["sup_branca"]  = piv[("Branca", "Superior completo")] / piv[("Branca", "Total")]
r["sup_negra"]   = (piv[("Preta", "Superior completo")].fillna(0)
                    + piv[("Parda", "Superior completo")].fillna(0)) / \
                   (piv[("Preta", "Total")].fillna(0) + piv[("Parda", "Total")].fillna(0))
r["gap_sup_raca"] = r.sup_branca - r.sup_negra
r["sup_total"] = piv[("Total", "Superior completo")] / tot
r = r.reset_index()
dr = d.merge(r, on="id_municipio", how="left")
BASE = BASE.reindex(dr.index)  # mesmas linhas (merge 1:1 preserva a ordem)
for v in ["share_negra", "gap_sup_raca", "sup_total", "sup_branca", "sup_negra"]:
    rb, nb = bruto(v, "gap_sexo", dr); rp, npar = parcial(v, "gap_sexo", frame=dr)
    print(f"  {v:14s} x gap_sexo   bruto {rb:+.4f} (n {nb})   parcial {rp:+.4f} (n {npar})")
rb, nb = bruto("pib_pc", "gap_sexo", dr); rp, _ = parcial("pib_pc", "gap_sexo", frame=dr)
print(f"  {'pib_pc':14s} x gap_sexo   bruto {rb:+.4f} (n {nb})   parcial {rp:+.4f}   <- a perna de renda (D4)")

print()
print("=" * 72)
print("H08 · exposicao acumulada ao PBF x queda do IVS, controlando o IVS inicial")
print("=" * 72)
rb, nb = bruto("pbf_valor_acumulado", "d_ivs")
rp, npar = parcial("pbf_valor_acumulado", "d_ivs")
ivs0 = pd.DataFrame({"ivs0": d.ivs_2000.rank()})
rp2, npar2 = parcial("pbf_valor_acumulado", "d_ivs", extra=ivs0)
print(f"  bruto                          {rb:+.4f} (n {nb})")
print(f"  + log-pop, log-PIB pc, UF      {rp:+.4f} (n {npar})")
print(f"  + IVS 2000 (o falseador)       {rp2:+.4f} (n {npar2})   <- H08 so vale se sobrar aqui")
print(f"  convergencia pura: IVS 2000 x d_ivs  {bruto('ivs_2000','d_ivs')[0]:+.4f}")

print()
print("=" * 72)
print("H04 · fatia dos credores municipais que devem a PGFN")
print("=" * 72)
s = d[["mides_credores", "credores_devedores", "mides_valor", "pago_a_devedor"]].dropna()
share_n = s.credores_devedores / s.mides_credores
share_v = s.pago_a_devedor / s.mides_valor.replace(0, np.nan)
print(f"  municipios com pagamento no MIDES: {len(s)}")
print(f"  credores que sao devedores da PGFN — mediana {share_n.median():.3%}, "
      f"p10 {share_n.quantile(.1):.3%}, p90 {share_n.quantile(.9):.3%}")
print(f"  no agregado: {s.credores_devedores.sum():,.0f} de {s.mides_credores.sum():,.0f} "
      f"({s.credores_devedores.sum()/s.mides_credores.sum():.2%})")
print(f"  valor pago a devedor — mediana {share_v.median():.3%}, "
      f"agregado R$ {s.pago_a_devedor.sum()/1e9:,.1f} bi de R$ {s.mides_valor.sum()/1e9:,.1f} bi "
      f"({s.pago_a_devedor.sum()/s.mides_valor.sum():.2%})")

print()
print("=" * 72)
print("H14 · Garantia-Safra: o que da' para dizer sem o SCR")
print("=" * 72)
gs = pd.read_csv(P("v_garantia_safra.csv"))
print(f"  {gs.id_municipio.nunique()} municipios, anos {gs.ano.min()}-{gs.ano.max()}")
w = gs.pivot_table(index="id_municipio", columns="ano", values="gs_beneficiarios", aggfunc="sum")
tot_gs = w.sum(axis=1).rename("gs_total")
dg = d.merge(tot_gs.reset_index(), on="id_municipio", how="left")
dg["gs_share"] = dg.gs_total / dg.populacao
for v in ["nbf_share_dom", "credito_pc", "formalidade", "defeso_share"]:
    rb, nb = bruto("gs_share", v, dg)
    print(f"  gs_share x {v:16s} bruto {rb:+.4f} (n {nb})")
print("  por ano (beneficiarios):", {int(a): int(w[a].sum()) for a in sorted(w.columns)})
