#!/usr/bin/env python3
"""Carrega papeis de CNPJ + cadastro uma vez, grava cache compacto (.npz + .json).

  python3 scripts/hipoteses-cnpj/10_cache_universo.py

Por que separado do resto do pipeline
--------------------------------------
`h3_cnpj_cadastro.csv` tem 3,4 GB (todas as raizes de CNPJ do Brasil, so pra
tirar CNAE e idade). O pipeline de trincas (`20_apriori_itemsets.py`) vai
rodar varias vezes durante o debug -- recarregar e reprocessar esse CSV a
cada tentativa custa minutos por rodada, de graca. Este script paga esse
custo uma vez so e grava:

  - `universo.npz`  : para cada papel, o array ordenado de codigos inteiros
                       de raiz que o exerce (mesma tecnica do h3_20:
                       intersect1d entre arrays de int e muito mais rapido
                       que intersecao de set de string)
  - `estrato.npy`   : estrato CNAE(2 digitos) x idade(tercil) de cada raiz
                       codificada, na mesma ordem de codigo do universo
  - `meta.json`      : lista de papeis, universo_papel, universo_cadastro,
                       n_estratos

Entrada: os mesmos CSVs que h3_20_matriz_cnpj.py usa, no mesmo LOTE.
"""
import json, os, sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
# LOTE/OUT via env var primeiro -- roda tanto dentro do checkout completo do
# repo (default relativo a REPO) quanto standalone (ex: em ~/hipoteses-cnpj
# no beelink, so com os scripts, sem o resto do repo).
LOTE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
    os.environ.get("LOTE", str(REPO / "tasks" / "hipoteses_resultado" / "h3_20260907")))
OUT = Path(os.environ.get("OUT", str(REPO / "tasks" / "hipoteses_resultado" / "hipoteses-cnpj")))


def carrega_papeis():
    partes = []
    for suf in "abc":
        f = LOTE / f"h3_cnpj_papeis_{suf}.csv"
        if not f.exists():
            print(f"  AUSENTE {f.name}")
            continue
        d = pd.read_csv(f, dtype={"cnpj": str, "raiz": str}, low_memory=False)
        partes.append(d)
        print(f"  {f.name}: {len(d):,} linhas".replace(",", "."))
    if not partes:
        sys.exit("nenhum CSV de papel encontrado")
    return pd.concat(partes, ignore_index=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print(f"lote: {LOTE}")
    p = carrega_papeis()
    p = p[p["raiz"].notna()]
    papel_raiz = p.groupby(["papel", "raiz"], observed=True).size().reset_index(name="n")
    papeis = sorted(papel_raiz["papel"].unique())
    print(f"\n{len(papeis)} papeis, {papel_raiz['raiz'].nunique():,} empresas distintas".replace(",", "."))

    cad = LOTE / "h3_cnpj_cadastro.csv"
    cad_raiz = estrato_de = None
    n_estratos = 0
    if cad.exists():
        print(f"\ncarregando cadastro ({cad.stat().st_size/1e9:.1f} GB)...")
        c = pd.read_csv(
            cad, dtype={"raiz": str, "cnae_fiscal_principal": str},
            usecols=["raiz", "cnae_fiscal_principal", "data_inicio_atividade"],
            low_memory=False,
        ).drop_duplicates("raiz")
        cad_raiz = c["raiz"].to_numpy()
        print(f"cadastro: {len(cad_raiz):,} empresas (raiz)".replace(",", "."))
    else:
        print("AUSENTE h3_cnpj_cadastro.csv -- sem taxa-base do cadastro nem estrato")

    todas = pd.Index(pd.unique(np.concatenate(
        [papel_raiz["raiz"].to_numpy()] + ([cad_raiz] if cad_raiz is not None else []))))
    cod = {r: i for i, r in enumerate(todas)}
    N_todas = len(todas)

    if cad_raiz is not None:
        div = c["cnae_fiscal_principal"].astype(str).str[:2]
        ano = pd.to_numeric(c["data_inicio_atividade"].astype(str).str[:4], errors="coerce")
        terc = pd.qcut(ano, 3, labels=["antiga", "media", "nova"], duplicates="drop").astype(str)
        chave = div + "|" + terc
        cats = pd.Categorical(chave)
        estrato_de = np.full(N_todas, -1, dtype=np.int32)
        estrato_de[[cod[r] for r in cad_raiz]] = cats.codes
        n_estratos = len(cats.categories) + 1  # +1 para o "-1" (fora do cadastro)
        estrato_de = estrato_de + 1
        print(f"estratos CNAE x idade: {n_estratos - 1}")

    idx = {pl: np.sort(np.fromiter((cod[r] for r in s), dtype=np.int64, count=len(s)))
           for pl, s in ((k, set(v)) for k, v in papel_raiz.groupby("papel")["raiz"])}
    universo_papel = papel_raiz["raiz"].nunique()
    universo_cadastro = len(cad_raiz) if cad_raiz is not None else None

    npz = {f"papel__{pl}": arr for pl, arr in idx.items()}
    if estrato_de is not None:
        npz["estrato_de"] = estrato_de
    np.savez_compressed(OUT / "universo.npz", **npz)

    meta = {
        "papeis": papeis,
        "universo_papel": int(universo_papel),
        "universo_cadastro": universo_cadastro,
        "n_estratos": int(n_estratos),
        "n_todas": int(N_todas),
        "lote": str(LOTE),
    }
    (OUT / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"\n-> {OUT / 'universo.npz'}")
    print(f"-> {OUT / 'meta.json'}")


if __name__ == "__main__":
    main()
