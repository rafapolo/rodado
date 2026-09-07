#!/usr/bin/env python3
"""Todos os pares de papel sobre o mesmo CNPJ -- o eixo que a cascata F0 nunca viu.

  python3 scripts/hipoteses/h3_20_matriz_cnpj.py

Por que a estatistica aqui NAO e correlacao
-------------------------------------------
No painel municipal a pergunta e "quando X sobe, Y sobe?" -- correlacao serve.
Aqui a pergunta e outra: "a empresa que faz A tambem faz B com que frequencia,
comparada a uma empresa qualquer?". Isso e co-ocorrencia, e a medida e o LIFT
contra a taxa-base:

    lift = P(B | A) / P(B)

Lift 1,0 significa que ser A nao diz nada sobre ser B. Lift 20 significa que a
empresa que faz A tem 20x mais chance de fazer B do que uma empresa qualquer.

Duas armadilhas, e as duas mudam o numero por ordens de grandeza:

1. O DENOMINADOR. P(B) depende do universo. Contra "empresas ativas no cadastro"
   (~20M) da um numero; contra "empresas que aparecem em algum papel" (~5M) da
   outro, muito menor. Este script reporta os dois, sempre, porque escolher um e
   esconder o outro e como se produz manchete falsa com dado verdadeiro.

2. O CONFUNDIMENTO DE PORTE E SETOR. Empresa grande aparece em tudo: se ela e
   fornecedora do governo E autuada pelo IBAMA, o lift sobe sem que exista
   relacao entre as duas coisas -- e so tamanho. O analogo da correlacao parcial
   aqui e o odds ratio de Mantel-Haenszel estratificado por divisao CNAE e por
   tercil de idade da empresa. Quando o MH desaba em relacao ao bruto, o achado
   era composicao, exatamente como o bruto vs parcial do painel municipal.

Significancia nao entra: com N na casa dos milhoes tudo e "significativo", e
p-valor vira decoracao. O que separa achado de ruido aqui e tamanho de efeito
mais um piso de contagem conjunta.
"""
import itertools, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml

REPO = Path(__file__).resolve().parent.parent.parent
LOTE = REPO / "tasks" / "hipoteses_resultado" / "h3_20260907"
OUT  = REPO / "tasks" / "hipoteses_resultado" / "hipoteses3"
N_MIN_PAR   = 30     # abaixo disso o lift e ruido de contagem
LIFT_MIN    = 2.0    # o dobro da taxa-base

def carrega_papeis():
    partes = []
    for suf in "abc":
        f = LOTE / f"h3_cnpj_papeis_{suf}.csv"
        if not f.exists():
            print(f"  AUSENTE {f.name}"); continue
        d = pd.read_csv(f, dtype={"cnpj": str, "raiz": str}, low_memory=False)
        partes.append(d); print(f"  {f.name}: {len(d):,} linhas".replace(",", "."))
    if not partes: sys.exit("nenhum CSV de papel encontrado -- rode os blocos 60-62 no beelink")
    return pd.concat(partes, ignore_index=True)

def mh_odds(a, b, c, d):
    """Mantel-Haenszel: odds ratio combinado entre estratos."""
    n = a + b + c + d
    ok = n > 0
    num = np.sum((a[ok] * d[ok]) / n[ok]); den = np.sum((b[ok] * c[ok]) / n[ok])
    return float(num / den) if den > 0 else np.nan

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    mapa = yaml.safe_load((REPO/"scripts"/"hipoteses"/"h3_familias_colunas.yaml")
                          .read_text(encoding="utf-8"))
    DEF = {frozenset(x) for x in mapa.get("pares_definicionais", [])}
    print(f"guarda: {len(DEF)} pares definicionais (a relacao existe por desenho do processo)")
    print("papeis:")
    p = carrega_papeis()
    p = p[p["raiz"].notna()]
    # a EMPRESA e a raiz (8 digitos), nao o CNPJ cheio: filial nao e outra empresa,
    # e o quadro societario (socios.cnpj_basico) so existe nesse grao.
    papel_raiz = p.groupby(["papel", "raiz"], observed=True).size().reset_index(name="n")
    papeis = sorted(papel_raiz["papel"].unique())
    conj = {k: set(v) for k, v in papel_raiz.groupby("papel")["raiz"]}
    print(f"\n{len(papeis)} papeis, {papel_raiz['raiz'].nunique():,} empresas distintas".replace(",", "."))

    # --- universo unico de raizes, como codigo inteiro. Tudo o que vem depois
    # trabalha com array de int, nao com set de string: o Mantel-Haenszel por
    # par vira bincount por estrato, e a corrida cai de horas para segundos.
    cad = LOTE / "h3_cnpj_cadastro.csv"
    cad_raiz, estrato_de, n_estratos = None, None, 0
    if cad.exists():
        c = pd.read_csv(cad, dtype={"raiz": str, "cnae_fiscal_principal": str},
                        usecols=["raiz", "cnae_fiscal_principal", "data_inicio_atividade"],
                        low_memory=False).drop_duplicates("raiz")
        cad_raiz = c["raiz"].to_numpy()
        print(f"cadastro: {len(cad_raiz):,} empresas (raiz)".replace(",", "."))
    else:
        print("AUSENTE h3_cnpj_cadastro.csv -- sem taxa-base do cadastro nem Mantel-Haenszel")

    todas = pd.Index(pd.unique(np.concatenate(
        [papel_raiz["raiz"].to_numpy()] + ([cad_raiz] if cad_raiz is not None else []))))
    cod = {r: i for i, r in enumerate(todas)}
    N_todas = len(todas)

    if cad_raiz is not None:
        div = c["cnae_fiscal_principal"].astype(str).str[:2]
        ano = pd.to_numeric(c["data_inicio_atividade"].astype(str).str[:4], errors="coerce")
        terc = pd.qcut(ano, 3, labels=["antiga", "media", "nova"], duplicates="drop").astype(str)
        chave = (div + "|" + terc)
        cats = pd.Categorical(chave)
        estrato_de = np.full(N_todas, -1, dtype=np.int32)
        estrato_de[[cod[r] for r in cad_raiz]] = cats.codes
        n_estratos = len(cats.categories) + 1          # +1 para o "-1" (fora do cadastro)
        estrato_de = estrato_de + 1
        tot_estrato = np.bincount(estrato_de, minlength=n_estratos).astype(float)
        print(f"estratos CNAE x idade: {n_estratos - 1}")

    idx = {pl: np.sort(np.fromiter((cod[r] for r in s), dtype=np.int64, count=len(s)))
           for pl, s in ((k, set(v)) for k, v in papel_raiz.groupby("papel")["raiz"])}
    universo_papel = papel_raiz["raiz"].nunique()
    universo_cadastro = len(cad_raiz) if cad_raiz is not None else None

    linhas = []
    for a, b in itertools.combinations(papeis, 2):
        A, B = idx[a], idx[b]
        inter = np.intersect1d(A, B, assume_unique=True)
        nab = len(inter)
        if nab < N_MIN_PAR: continue
        na, nb = len(A), len(B)
        reg = {"papel_a": a, "papel_b": b, "n_a": na, "n_b": nb, "n_ambos": nab,
               "p_b_dado_a": nab / na, "p_a_dado_b": nab / nb}
        for tag, N in (("papel", universo_papel), ("cadastro", universo_cadastro)):
            if N:
                reg[f"taxa_base_b_{tag}"] = nb / N
                reg[f"lift_{tag}"] = (nab / na) / (nb / N)
        if estrato_de is not None:
            a11 = np.bincount(estrato_de[inter], minlength=n_estratos).astype(float)
            a10 = np.bincount(estrato_de[A], minlength=n_estratos).astype(float) - a11
            a01 = np.bincount(estrato_de[B], minlength=n_estratos).astype(float) - a11
            a00 = np.maximum(tot_estrato - a11 - a10 - a01, 0)
            # estrato 0 = empresa fora do cadastro: nao entra, nao tem CNAE nem idade
            reg["or_mh_cnae_idade"] = mh_odds(a11[1:], a10[1:], a01[1:], a00[1:])
        reg["tipo"] = "definicional" if frozenset((a, b)) in DEF else "achado"
        linhas.append(reg)

    d = pd.DataFrame(linhas)
    if d.empty: sys.exit("nenhum par acima do piso de contagem")
    # o ranking usa lift_papel: o denominador do cadastro inteiro (64,5M raizes,
    # todo MEI e toda empresa morta ja registrada) infla o lift em ordens de
    # grandeza sem dizer nada. Os dois ficam gravados no CSV.
    chave = "lift_papel"
    d = d.sort_values("or_mh_cnae_idade" if "or_mh_cnae_idade" in d else chave,
                      ascending=False)
    d.to_csv(OUT / "cnpj_pares.csv", index=False)
    fortes = d[d[chave] >= LIFT_MIN]
    print(f"\n{len(d)} pares acima de {N_MIN_PAR} empresas em comum "
          f"| {len(fortes)} com lift >= {LIFT_MIN}")
    print(f"-> {(OUT / 'cnpj_pares.csv').relative_to(REPO)}")
    print(f"\n15 maiores, ja sem os definicionais:")
    for _, r in d[d.tipo == "achado"].head(15).iterrows():
        mh = f" | MH {r.get('or_mh_cnae_idade', float('nan')):.1f}" if "or_mh_cnae_idade" in d else ""
        print(f"  lift {r[chave]:7.1f}  {r.papel_a} x {r.papel_b}"
              f"  ({r.n_ambos:,} empresas, P(B|A)={r.p_b_dado_a:.1%}){mh}".replace(",", "."))

if __name__ == "__main__":
    sys.exit(main())
