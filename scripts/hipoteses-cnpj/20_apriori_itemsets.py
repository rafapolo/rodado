#!/usr/bin/env python3
"""Espaco inteiro de trincas/quadras/... de papel de CNPJ, via Apriori.

  python3 scripts/hipoteses-cnpj/20_apriori_itemsets.py [--k-max 5] [--n-min 30]

Por que Apriori e nao "gerar todas as combinacoes"
----------------------------------------------------
Com 41 papeis, C(41,3) = 10.660 trincas ainda e barato -- mas C(41,5) ja passa
de 700 mil, e nada garante que o eixo pare em 5. Gerar TODAS as combinacoes de
tamanho k e testar cada uma e desperdicio: se o par (A,B) tem so 3 empresas em
comum, nenhuma trinca (A,B,X) pode ter mais de 3 -- o suporte so cai quando se
adiciona papel. Essa e a propriedade antimonotonica que sustenta o algoritmo
Apriori (Agrawal & Srikant 1994, o mesmo de "cesta de compras"): so estende um
itemset de tamanho k-1 que ja passou no piso de contagem (`N_MIN_PAR`, o
"suporte minimo"), porque nenhum superconjunto de um itemset raro pode ser
frequente. Aqui, "item" = papel de cadastro, "transacao" = uma raiz de CNPJ,
"itemset frequente" = combinacao de papeis que N ou mais empresas exercem
simultaneamente.

O que cada itemset frequente de tamanho >= 2 recebe
-----------------------------------------------------
- `lift`: P(itemset) / prod(P(cada papel)), contra dois universos (papel e
  cadastro), generalizacao padrao do lift de regra de associacao para k > 2 --
  nao e invencao deste script, e a mesma definicao do h3_20 para pares
  (lift_papel = (n_ab/n_a) / (n_b/N)) escrita na forma simetrica.
- `razao_obs_esp_estratificada`: para cada estrato CNAE x idade, conta quantas
  empresas do estrato tem o itemset inteiro (observado) contra quantas teriam
  se os papeis fossem independentes DENTRO do estrato (esperado = tamanho do
  estrato x produto das proporcoes marginais no estrato); soma observado e
  esperado por estrato e divide. Isso GENERALIZA o odds ratio de
  Mantel-Haenszel do h3_20 (que so vale para 2x2) para k papeis -- mas e uma
  razao observado/esperado agregada por estrato, nao um odds ratio de
  Mantel-Haenszel propriamente dito. Nomeada assim de proposito, para nao
  emprestar peso estatistico que a formula k>2 nao tem.
- `tipo`: "definicional" se QUALQUER par dentro do itemset esta em
  `pares_definicionais` do h3_familias_colunas.yaml (a relacao existe por
  desenho do cadastro, nao e descoberta) -- herdado dos pares pro itemset
  inteiro, senao um itemset de 3 que so repete um par obvio mais um papel
  qualquer passaria por achado.

Sem significancia (p-valor): com contagem na casa dos milhoes, tudo e
"significativo" estatisticamente. O que separa achado de ruido de contagem
aqui e tamanho de efeito (lift) e piso de contagem conjunta (N_MIN_PAR), como
ja documentado no h3_20.
"""
import argparse, itertools, json, os, sys
from pathlib import Path
import numpy as np, pandas as pd, yaml

REPO = Path(__file__).resolve().parent.parent.parent
OUT = Path(os.environ.get("OUT", str(REPO / "tasks" / "hipoteses_resultado" / "hipoteses-cnpj")))
FAMILIAS_YAML = Path(os.environ.get(
    "FAMILIAS_YAML", str(REPO / "scripts" / "hipoteses" / "h3_familias_colunas.yaml")))


def carrega_cache():
    meta = json.loads((OUT / "meta.json").read_text())
    npz = np.load(OUT / "universo.npz")
    idx = {pl: npz[f"papel__{pl}"] for pl in meta["papeis"]}
    estrato_de = npz["estrato_de"] if "estrato_de" in npz.files else None
    return meta, idx, estrato_de


def carrega_definicionais():
    d = yaml.safe_load(FAMILIAS_YAML.read_text(encoding="utf-8"))
    return {frozenset(x) for x in d.get("pares_definicionais", [])}


def candidatos_apriori(chaves_ordenadas, frequentes, k):
    """Juncao Apriori por PREFIXO, nao por comparacao par a par.

    A versao ingenua (comparar todo par de itemsets de tamanho k-1, O(F^2))
    trava quando F passa de alguns milhares -- foi o que aconteceu na
    primeira tentativa deste script: papeis grandes (sicaf_habilitado tem
    744 mil empresas) fazem quase todo par/trinca sobreviver ao piso de 30,
    entao F cresce rapido e o loop duplo em Python puro nao escala.

    A correcao padrao (Agrawal & Srikant 1994): ordena cada itemset de
    tamanho k-1, agrupa pelos primeiros k-2 elementos (o "prefixo"), e so
    junta dentro do mesmo grupo -- dois itemsets so podem formar um
    candidato valido de tamanho k se concordam em todos os elementos menos
    o ultimo. Isso derruba o custo de O(F^2) para ~O(F x papeis), porque
    cada grupo tem no maximo `len(papeis)` membros, nao F inteiro.
    """
    grupos = {}
    for it in chaves_ordenadas:
        grupos.setdefault(it[:-1], []).append(it[-1])
    candidatos = set()
    for prefixo, ultimos in grupos.items():
        ultimos.sort()
        for i in range(len(ultimos)):
            for j in range(i + 1, len(ultimos)):
                uniao = frozenset(prefixo + (ultimos[i], ultimos[j]))
                if uniao in candidatos:
                    continue
                # poda antimonotonica: todo subconjunto de tamanho k-1 do
                # candidato precisa ja ser frequente
                if all(frozenset(sub) in frequentes
                       for sub in itertools.combinations(sorted(uniao), k - 1)):
                    candidatos.add(uniao)
    return candidatos


def razao_obs_esp(inter, membros, estrato_de, n_estratos, tot_estrato):
    """Observado/esperado por estrato, somado, para o itemset cuja intersecao
    completa (todas as raizes que tem TODOS os papeis) e `inter`, e cujos
    papeis individuais (para as proporcoes marginais) tem arrays `membros`."""
    if estrato_de is None:
        return np.nan
    obs = np.bincount(estrato_de[inter], minlength=n_estratos).astype(float)
    # proporcao marginal de cada papel, por estrato
    props = np.ones(n_estratos, dtype=float)
    for m in membros:
        cont = np.bincount(estrato_de[m], minlength=n_estratos).astype(float)
        with np.errstate(divide="ignore", invalid="ignore"):
            props *= np.where(tot_estrato > 0, cont / np.maximum(tot_estrato, 1), 0.0)
    esp = props * tot_estrato
    # estrato 0 = fora do cadastro (sem CNAE/idade) -- nao entra na razao
    o, e = obs[1:].sum(), esp[1:].sum()
    return float(o / e) if e > 0 else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--k-max", type=int, default=6)
    ap.add_argument("--n-min", type=int, default=30)
    ap.add_argument("--lift-min", type=float, default=2.0)
    args = ap.parse_args()

    meta, idx, estrato_de = carrega_cache()
    papeis = meta["papeis"]
    universo_papel, universo_cadastro = meta["universo_papel"], meta["universo_cadastro"]
    n_estratos = meta["n_estratos"]
    DEF = carrega_definicionais()
    tot_estrato = (np.bincount(estrato_de, minlength=n_estratos).astype(float)
                   if estrato_de is not None else None)
    print(f"{len(papeis)} papeis carregados do cache | universo_papel={universo_papel:,} "
          f"| universo_cadastro={universo_cadastro:,}".replace(",", "."), flush=True)

    tam = {p: len(idx[p]) for p in papeis}

    # nivel 1: cada papel sozinho e "frequente" por definicao (ja e o universo
    # do proprio papel); guarda so o array de raizes pra estender depois.
    frequentes = {frozenset({p}): idx[p] for p in papeis}
    todos_registros = []

    k = 1
    while frequentes and k < args.k_max:
        k += 1
        chaves_ordenadas = sorted(tuple(sorted(s)) for s in frequentes.keys())
        candidatos = candidatos_apriori(chaves_ordenadas, frequentes, k)

        print(f"nivel {k}: {len(candidatos)} candidatos (pos-poda, de {len(chaves_ordenadas)} "
              f"frequentes no nivel {k - 1})", flush=True)
        if not candidatos:
            break
        if len(candidatos) > 300_000:
            print(f"  AVISO: {len(candidatos)} candidatos e muito -- parando em k={k-1} "
                  f"pra nao estourar tempo/memoria. Suba --n-min pra podar mais.", flush=True)
            break

        novos_frequentes = {}
        for uniao in candidatos:
            membros = sorted(uniao)
            # reaproveita a intersecao ja calculada de um (k-1)-subconjunto
            base = membros[:-1]
            extra = membros[-1]
            inter_base = frequentes.get(frozenset(base))
            if inter_base is None:
                # fallback: nenhum (k-1)-subconjunto guardado com essa ordem
                # exata -- calcula do zero a partir dos papeis individuais
                arrs = [idx[m] for m in membros]
                inter = arrs[0]
                for a in arrs[1:]:
                    inter = np.intersect1d(inter, a, assume_unique=True)
            else:
                inter = np.intersect1d(inter_base, idx[extra], assume_unique=True)
            n = len(inter)
            if n < args.n_min:
                continue
            novos_frequentes[uniao] = inter

            reg = {"k": k, "papeis": " + ".join(membros), "n_itemset": n}
            prod_papel = 1.0
            prod_cad = 1.0
            for m in membros:
                prod_papel *= tam[m] / universo_papel
                if universo_cadastro:
                    prod_cad *= tam[m] / universo_cadastro
            p_itemset_papel = n / universo_papel
            reg["lift_papel"] = p_itemset_papel / prod_papel if prod_papel > 0 else np.nan
            if universo_cadastro:
                p_itemset_cad = n / universo_cadastro
                reg["lift_cadastro"] = p_itemset_cad / prod_cad if prod_cad > 0 else np.nan
            reg["razao_obs_esp_estratificada"] = razao_obs_esp(
                inter, [idx[m] for m in membros], estrato_de, n_estratos, tot_estrato)
            reg["tipo"] = ("definicional"
                           if any(frozenset(par) in DEF for par in itertools.combinations(membros, 2))
                           else "achado")
            todos_registros.append(reg)

        frequentes = novos_frequentes
        print(f"  -> {len(frequentes)} frequentes (>= {args.n_min} empresas)", flush=True)

    if not todos_registros:
        sys.exit("nenhum itemset de tamanho >= 2 passou no piso de contagem")

    d = pd.DataFrame(todos_registros).sort_values(
        "razao_obs_esp_estratificada" if "razao_obs_esp_estratificada" in
        pd.DataFrame(todos_registros) else "lift_papel", ascending=False)
    OUT.mkdir(parents=True, exist_ok=True)
    d.to_csv(OUT / "cnpj_itemsets.csv", index=False)
    print(f"\n{len(d)} itemsets (tamanho 2 a {d.k.max()}) gravados")
    for kk in sorted(d.k.unique()):
        sub = d[d.k == kk]
        print(f"  tamanho {kk}: {len(sub)} itemsets, {(sub.tipo == 'achado').sum()} nao-definicionais")

    fortes = d[(d.tipo == "achado") & (d.lift_papel >= args.lift_min)]
    print(f"\n{len(fortes)} achados (nao-definicional, lift_papel >= {args.lift_min}), top 20:")
    for _, r in fortes.sort_values("razao_obs_esp_estratificada", ascending=False).head(20).iterrows():
        oe = r.get("razao_obs_esp_estratificada", float("nan"))
        print(f"  k={r.k}  lift {r.lift_papel:8.1f}  obs/esp {oe:8.1f}  "
              f"n={r.n_itemset:6.0f}  {r.papeis}")
    print(f"\n-> {OUT / 'cnpj_itemsets.csv'}")


if __name__ == "__main__":
    main()
