#!/usr/bin/env python3
"""Politico -> sociedade -> papel da empresa. O caminho que motivou o eixo 2.

  python3 scripts/hipoteses/h3_30_politico_empresa.py

O casamento vem pronto do bloco 70 (nome normalizado + os 6 digitos visiveis do
CPF mascarado). Este script so cruza com a matriz de papeis e mede.

A ressalva manda no resultado, entao ela vem antes do numero
----------------------------------------------------------
O CPF do socio e MASCARADO no cadastro publico (`***123456**`). O par
(nome, 6 digitos) NAO e identificador unico: dois homonimos com os mesmos 6
digitos casam entre si. Por isso:

  * `n_homonimos > 1` sai do agregado por padrao (`--incluir-homonimos` mantem);
  * o resultado e uma LISTA PARA CONFERENCIA, nao um cadastro de fato;
  * a taxa-base e calculada sobre o MESMO metodo de casamento -- comparar um
    numero casado por nome com um numero casado por CNPJ exato inflaria o efeito
    pelo simples fato de o primeiro ter mais falso-positivo.

Comparar "politico" com "nao-politico" tambem exige cuidado: o candidato e, em
media, mais velho, mais rico e mais urbano que a populacao geral, e essas tres
coisas ja predizem ser socio de empresa. O corte honesto e DENTRO do conjunto de
socios: entre quem e socio, o socio-politico faz mais X que o socio comum?
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
LOTE = REPO / "tasks" / "hipoteses_resultado" / "h3_20260907"
OUT  = REPO / "tasks" / "hipoteses_resultado" / "hipoteses3"

def main(incluir_homonimos=False):
    f = LOTE / "h3_politico_socio.csv"
    if not f.exists(): sys.exit(f"AUSENTE {f.name} -- rode o bloco 70 no beelink")
    pol = pd.read_csv(f, dtype={"cpf": str, "raiz": str}, low_memory=False)
    print(f"casamentos brutos: {len(pol):,}".replace(",", "."))
    amb = int((pol.n_homonimos > 1).sum())
    print(f"  ambiguos (nome+6 digitos repetido): {amb:,} "
          f"({amb/len(pol):.1%}) -- {'mantidos' if incluir_homonimos else 'descartados'}"
          .replace(",", "."))
    if not incluir_homonimos:
        pol = pol[pol.n_homonimos == 1]

    partes = [pd.read_csv(LOTE / f"h3_cnpj_papeis_{s}.csv", dtype={"raiz": str}, low_memory=False)
              for s in "abc" if (LOTE / f"h3_cnpj_papeis_{s}.csv").exists()]
    if not partes: sys.exit("AUSENTE matriz de papeis -- rode os blocos 60-62")
    pap = pd.concat(partes, ignore_index=True)
    pap = pap[pap.raiz.notna()]

    emp_pol = set(pol.raiz.dropna())
    todas   = set(pap.raiz)
    print(f"\nempresas com socio-politico: {len(emp_pol):,}".replace(",", "."))
    print(f"empresas com algum papel:    {len(todas):,}".replace(",", "."))

    linhas = []
    for papel, g in pap.groupby("papel"):
        emp = set(g.raiz)
        inter = emp & emp_pol
        # taxa-base: entre TODAS as empresas com papel, quantas tem socio-politico
        base = len(emp_pol & todas) / len(todas)
        taxa = len(inter) / len(emp) if emp else 0
        linhas.append({"papel": papel, "empresas_papel": len(emp),
                       "com_socio_politico": len(inter),
                       "taxa": taxa, "taxa_base": base,
                       "lift": taxa / base if base else np.nan})
    d = pd.DataFrame(linhas).sort_values("lift", ascending=False)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "politico_papel.csv", index=False)
    print(f"\ntaxa-base: {d.taxa_base.iat[0]:.2%} das empresas com papel tem socio-politico\n")
    print(f"{'papel':32s} {'empresas':>10s} {'c/ politico':>12s} {'taxa':>7s} {'lift':>6s}")
    for _, r in d.iterrows():
        print(f"{r.papel:32s} {r.empresas_papel:10,} {r.com_socio_politico:12,} "
              f"{r.taxa:6.2%} {r.lift:6.2f}".replace(",", "."))
    print(f"\n-> {(OUT / 'politico_papel.csv').relative_to(REPO)}")

if __name__ == "__main__":
    sys.exit(main("--incluir-homonimos" in sys.argv))
