#!/usr/bin/env python3
"""Fecha H38-H40 de tasks/hipoteses.md Bloco H (diagnosticos que a varredura
sinalizou, herdados da sessao paralela que rodou 93/95_inedito.py — ver o
acordo de divisao de trabalho de 2026-09-06). Roda sobre
tasks/hipoteses_resultado/20260906/painel.csv (OUT dir da outra sessao, so
leitura, nenhum arquivo dela e' reescrito). Nenhuma extracao nova.

Tres pares suspeitos de artefato, cada um com o falseador ja escrito em
tasks/hipoteses.md §5.2 Bloco H:

1. H38 (div_nomes x share_nome_top, parcial -0,40, maior supressao da
   varredura): as duas vem da MESMA tabela (br_ibge_nomes_brasil) e dividem o
   MESMO denominador (nascimentos = sum(quantidade_nascimentos_ate_2010) por
   municipio) — div_nomes = nomes_distintos/nascimentos, share_nome_top =
   max_nome/nascimentos. Correlacao espuria de razoes com denominador comum
   (Pearson 1897) e' o suspeito. Falseador: a relacao sumir ao acrescentar
   log(nascimentos) explicito no controle, alem do log-populacao que ja esta
   la (populacao correlaciona com nascimentos, mas nao e' a mesma coisa).
2. H39 (obras_1000dom x cresc_pop, parcial +0,33): falseador e' o efeito ser
   colinear com o proprio crescimento do PIB, nao so o nivel (que ja esta no
   controle padrao via log(pib_pc)).
3. H40 (trio MIDES x onomastica, incl. inversao de sinal em
   div_nomes x mides_valor_pc): falseador e' a relacao NAO se manter no
   subconjunto de municipios com cobertura MIDES mais completa (proxy:
   mides_pagamentos, contagem de registros de pagamento por municipio).

  python3 scripts/hipoteses/97_h38_h40.py [painel.csv]
"""
import os, sys
import numpy as np, pandas as pd

P = sys.argv[1] if len(sys.argv) > 1 else "tasks/hipoteses_resultado/20260906/painel.csv"
d = pd.read_csv(P, low_memory=False).replace([np.inf, -np.inf], np.nan)

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
    if len(s) < 30: return np.nan, len(s)
    return round(s[a].rank().corr(s[b].rank()), 4), len(s)

print("=" * 72)
print("H38 · div_nomes x share_nome_top — denominador comum (nascimentos)?")
print("=" * 72)
rb, nb = bruto("div_nomes", "share_nome_top")
rp0, np0 = parcial("div_nomes", "share_nome_top")
print(f"  bruto                                  {rb:+.4f} (n={nb})")
print(f"  parcial (log-pop, log-pib, UF)          {rp0:+.4f} (n={np0})  <- o -0,40 reportado")
if "nascimentos" in d.columns:
    lnasc = pd.DataFrame({"lnasc": np.log(d.nascimentos.clip(lower=1))})
    rp1, np1 = parcial("div_nomes", "share_nome_top", extra=lnasc)
    print(f"  + log(nascimentos) explicito             {rp1:+.4f} (n={np1})")
    print("  <- se cair perto de 0 aqui, e' correlacao espuria de razao com")
    print("     denominador comum (Pearson 1897): log-pop nao substitui")
    print("     log-nascimentos, que e' o denominador real das duas variaveis.")
else:
    print("  [pula] coluna 'nascimentos' ausente do painel")

print()
print("=" * 72)
print("H39 · obras_1000dom x cresc_pop — colinear com crescimento do PIB?")
print("=" * 72)
rb, nb = bruto("obras_1000dom", "cresc_pop")
rp0, np0 = parcial("obras_1000dom", "cresc_pop")
print(f"  bruto                                  {rb:+.4f} (n={nb})")
print(f"  parcial (log-pop, log-pib nivel, UF)    {rp0:+.4f} (n={np0})  <- o +0,33 reportado")
if "pib" in d.columns and "pib_2010" in d.columns:
    d2 = d.copy()
    d2["cresc_pib"] = np.where((d2.pib_2010.notna()) & (d2.pib_2010 != 0),
                                d2.pib / d2.pib_2010 - 1, np.nan)
    cresc_pib_rank = pd.DataFrame({"cresc_pib": d2.cresc_pib.rank()})
    rp1, np1 = parcial("obras_1000dom", "cresc_pop", extra=cresc_pib_rank, frame=d2)
    print(f"  + crescimento do PIB (pib/pib_2010-1)   {rp1:+.4f} (n={np1})")
    print("  <- se cair perto de 0, obras por domicilio segue o boom economico,")
    print("     nao o crescimento populacional em si — os dois costumam andar")
    print("     juntos (cidade que cresce economicamente atrai gente).")
else:
    print("  [pula] pib ou pib_2010 ausente do painel")

print()
print("=" * 72)
print("H40 · MIDES x onomastica — artefato do recorte de cobertura do MIDES?")
print("=" * 72)
pares = [("mides_valor_pc", "share_nome_top"), ("div_nomes", "mides_valor_pc")]
if "mides_pagamentos" in d.columns:
    cov = d[["mides_pagamentos"]].dropna()
    mediana_cov = cov.mides_pagamentos.median()
    print(f"  proxy de cobertura: mides_pagamentos (n registros de pagamento)")
    print(f"  municipios com MIDES: {len(cov)}  mediana de registros: {mediana_cov:.0f}")
    alta = d[d.mides_pagamentos >= mediana_cov]
    baixa = d[(d.mides_pagamentos < mediana_cov) & d.mides_pagamentos.notna()]
    print(f"  metade de cobertura ALTA (>= mediana): n={len(alta)}")
    print(f"  metade de cobertura BAIXA (< mediana): n={len(baixa)}")
    for a, b in pares:
        rb_full, nb_full = bruto(a, b)
        rp_full, np_full = parcial(a, b)
        rb_alta, nb_alta = bruto(a, b, alta)
        rp_alta, np_alta = parcial(a, b, frame=alta)
        rb_baixa, nb_baixa = bruto(a, b, baixa)
        rp_baixa, np_baixa = parcial(a, b, frame=baixa)
        print(f"  {a} x {b}:")
        print(f"    painel inteiro (n={nb_full}): bruto {rb_full:+.4f}  parcial {rp_full:+.4f} (n={np_full})")
        print(f"    cobertura ALTA  (n={nb_alta}): bruto {rb_alta:+.4f}  parcial {rp_alta:+.4f} (n={np_alta})")
        print(f"    cobertura BAIXA (n={nb_baixa}): bruto {rb_baixa:+.4f}  parcial {rp_baixa:+.4f} (n={np_baixa})")
    print("  <- se o sinal (incl. a inversao de div_nomes x mides_valor_pc)")
    print("     mudar ou sumir na metade de cobertura ALTA e ficar so na BAIXA,")
    print("     confirma que e' artefato do recorte, nao relacao real.")
else:
    print("  [pula] coluna 'mides_pagamentos' ausente do painel")
