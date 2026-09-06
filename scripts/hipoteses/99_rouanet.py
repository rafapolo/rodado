#!/usr/bin/env python3
"""Fecha H30 e H31 de tasks/hipoteses.md — Lei Rouanet (br_minc_salic), nunca
antes cruzada com sancao_integridade. Extracao em
scripts/hipoteses/71_rouanet.sql, sobre ~/rodado_hipoteses/rouanet/ no
beelink (copiado para .hipoteses/rouanet/ local, gitignorado).

H35 (SINAPI) NAO esta aqui — bloqueada por grao de fonte (so' tem UF, nao
municipio; diagnostico da sessao paralela, confirmado em basedosdados-schema.json).

  python3 scripts/hipoteses/99_rouanet.py
"""
import os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = lambda f: os.path.join(ROOT, ".hipoteses", "rouanet", f)

UF_REGIAO = {
    "AC": "Norte", "AP": "Norte", "AM": "Norte", "PA": "Norte", "RO": "Norte", "RR": "Norte", "TO": "Norte",
    "AL": "Nordeste", "BA": "Nordeste", "CE": "Nordeste", "MA": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "PI": "Nordeste", "RN": "Nordeste", "SE": "Nordeste",
    "DF": "Centro-Oeste", "GO": "Centro-Oeste", "MT": "Centro-Oeste", "MS": "Centro-Oeste",
    "ES": "Sudeste", "MG": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "RS": "Sul", "SC": "Sul",
}

def perm_test(x, g, stat="mediana", n_perm=5000, seed=0):
    fn = np.nanmedian if stat == "mediana" else np.nanmean
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    mask = np.asarray(g, dtype=bool).copy()
    obs = fn(x[mask]) - fn(x[~mask])
    diffs = np.empty(n_perm)
    work = mask.copy()
    for i in range(n_perm):
        rng.shuffle(work)
        diffs[i] = fn(x[work]) - fn(x[~work])
    p = (np.sum(np.abs(diffs) >= abs(obs)) + 1) / (n_perm + 1)
    return obs, p, float(np.std(diffs))

# =========================================================================
print("=" * 72)
print("H30 · funil Rouanet (solicitado -> aprovado -> captado) por regiao")
print("=" * 72)
proj = pd.read_csv(T("v_rouanet_projetos.csv"))
proj["regiao"] = proj.uf.map(UF_REGIAO)
print(f"  {len(proj)} projetos, {proj.uf.nunique()} UFs, {proj.regiao.notna().sum()} com regiao mapeada")

s = proj[(proj.solicitado > 0)].copy()
s["taxa_aprovacao"] = (s.aprovado / s.solicitado).clip(upper=2)
a = proj[(proj.aprovado > 0)].copy()
a["taxa_captacao"] = (a.apoiado / a.aprovado).clip(upper=2)

print("\n  taxa de APROVACAO (aprovado/solicitado) por regiao, mediana:")
print(s.groupby("regiao").taxa_aprovacao.median().sort_values(ascending=False).to_string())
print(f"  n por regiao: {s.groupby('regiao').size().to_dict()}")

print("\n  taxa de CAPTACAO (apoiado/aprovado, condicional a ter sido aprovado) por regiao, mediana:")
print(a.groupby("regiao").taxa_captacao.median().sort_values(ascending=False).to_string())
print(f"  n por regiao: {a.groupby('regiao').size().to_dict()}")

sudeste = a[a.regiao == "Sudeste"].taxa_captacao.dropna()
norte = a[a.regiao == "Norte"].taxa_captacao.dropna()
combo = pd.concat([sudeste, norte])
grp = np.array([True] * len(sudeste) + [False] * len(norte))
obs, p, sd = perm_test(combo.values, grp, stat="mediana")
print(f"\n  Sudeste (n={len(sudeste)}) x Norte (n={len(norte)}): "
      f"mediana {sudeste.median():.3f} x {norte.median():.3f}, diff={obs:+.4f}, p(permutacao)={p:.4f}")
print("  <- falseador: a taxa de conversao aprovado->captado ser igual entre regioes.")
print("     Se Sudeste captar sistematicamente mais do que aprova (rede de patrocinador",
      "\n     maior), a hipotese do funil regional desigual se sustenta.")

# =========================================================================
print()
print("=" * 72)
print("H31 · integridade dos proponentes/patrocinadores da Rouanet")
print("=" * 72)
ent = pd.read_csv(T("v_rouanet_integridade.csv"))
base = pd.read_csv(T("v_cnpj_baseline.csv")).iloc[0]
taxa_sanc_base = base.ativos_sancionados / base.total_ativos
taxa_pgfn_base = base.ativos_devedores_pgfn / base.total_ativos
print(f"  taxa-base (CNPJ ativo em br_me_cnpj.estabelecimentos, 2025-09, n={base.total_ativos:,}):")
print(f"    sancionado (CEIS/CNEP): {taxa_sanc_base:.4%}")
print(f"    devedor PGFN:           {taxa_pgfn_base:.4%}")
print("  (corrige a base 7.893/6,68mi do D7/H29 -- aquele 6,68mi e' o proprio")
print("   universo de devedores da PGFN, nao o total de empresas do pais;")
print("   6.673.698 de 67.640.763 CNPJ ativos SAO devedores PGFN aqui, o que bate")
print("   com o 6,68mi do D7 -- confirma que o denominador antigo estava errado)")

pj = ent[ent.doc_len == 14].copy()
for papel, col in [("proponente", "proponente"), ("patrocinador", "patrocinador")]:
    sub = pj[pj[col].fillna(0).astype(float) > 0]
    if len(sub) == 0:
        print(f"\n  [{papel}] nenhuma linha com flag > 0 -- checar codificacao do campo")
        continue
    n = len(sub)
    n_sanc = sub.sancionado.sum()
    n_pgfn = sub.devedor_pgfn.sum()
    taxa_sanc = n_sanc / n
    taxa_pgfn = n_pgfn / n
    esperado_sanc = n * taxa_sanc_base
    esperado_pgfn = n * taxa_pgfn_base
    print(f"\n  [{papel}] CNPJ únicos: {n:,}")
    print(f"    sancionado: {n_sanc} observado ({taxa_sanc:.4%}) x {esperado_sanc:.1f} esperado pelo acaso "
          f"({taxa_sanc/taxa_sanc_base:.2f}x a taxa-base)")
    print(f"    devedor PGFN: {n_pgfn} observado ({taxa_pgfn:.4%}) x {esperado_pgfn:.1f} esperado pelo acaso "
          f"({taxa_pgfn/taxa_pgfn_base:.2f}x a taxa-base)")
print("\n  <- falseador: a intersecao ser MENOR que o esperado pelo acaso.")
print("     Nota: sem controle de porte/setor (opcao 'b' descartada por custo) --")
print("     se o excesso existir, parte pode ser porte (proponente Rouanet nao e'")
print("     empresa media), nao so' integridade. Reportar como nao controlado.")
