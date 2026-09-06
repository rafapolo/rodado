#!/usr/bin/env python3
"""Fecha o Bloco I (H41-H45) — as pernas que 90_analise.py nao cobre.

Ver tasks/plan/bloco_i_pendencias.md para o roteiro completo. Tres coisas:

1. H41b — a hipotese e' de interacao (choque de exportacao move mais o PBF
   onde a pauta e' concentrada), nao de correlacao linear simples. Corte por
   quintil de HHI + termo de interacao residualizado.
2. H43 — a variavel e' binaria (troca_partido_2016_2020) e cai fora do scan
   de correlacao por desenho (nunique<5). O teste certo e' comparacao de
   grupo (troca vs. nao-troca), via diferenca de mediana + teste de
   permutacao em numpy puro (sem scipy, convencao do runner offline).
3. H44c/H45 — checagem de magnitude antes de promover a achados_fortes.md
   (regra do CLAUDE.md: ordem de grandeza esperada, flag de anomalia,
   verificacao por duas vias).

  python3 scripts/hipoteses/96_blocof_fechamento.py <dir_do_resultado>
"""
import os, sys
import numpy as np, pandas as pd

OUT = sys.argv[1] if len(sys.argv) > 1 else "."
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
    if len(s) < 30: return np.nan, len(s)
    return round(s[a].rank().corr(s[b].rank()), 4), len(s)

print("=" * 72)
print("H41b · choque de exportacao x PBF, interagido pelo HHI da pauta")
print("=" * 72)
sub = d[["comex_choque_pct", "comex_hhi_sh4_2019", "pbf_choque_pct"]].dropna()
sub = sub.copy()
sub["q_hhi"] = pd.qcut(sub.comex_hhi_sh4_2019, 5, labels=False, duplicates="drop")
print(f"  n total com as 3 pernas: {len(sub)}")
for q in sorted(sub.q_hhi.dropna().unique()):
    g = sub[sub.q_hhi == q]
    r = g.comex_choque_pct.rank().corr(g.pbf_choque_pct.rank())
    lo, hi = g.comex_hhi_sh4_2019.min(), g.comex_hhi_sh4_2019.max()
    print(f"  quintil HHI {int(q)+1}/5 (hhi {lo:.3f}-{hi:.3f}, n={len(g)}): "
          f"r(choque,pbf) = {r:+.4f}")
d2 = d.copy()
d2["inter_choque_hhi"] = d2.comex_choque_pct * d2.comex_hhi_sh4_2019
extra_mains = pd.DataFrame({
    "choque_rank": d2.comex_choque_pct.rank(),
    "hhi_rank": d2.comex_hhi_sh4_2019.rank(),
})
rp_i, n_i = parcial("inter_choque_hhi", "pbf_choque_pct", extra=extra_mains, frame=d2)
rb_i, _ = bruto("inter_choque_hhi", "pbf_choque_pct", d2)
print(f"  termo de interacao (choque x hhi) x pbf_choque_pct:")
print(f"    bruto                                    {rb_i:+.4f}")
print(f"    parcial (controla choque, hhi, log-pop, log-pib, UF)  {rp_i:+.4f} (n={n_i})")
print("  <- se |parcial| ficar perto de 0 como os quintis acima, H41b nao")
print("     sobrevive nem na forma de interacao: confirma H41 como nulo.")

print()
print("=" * 72)
print("H43 · troca de partido x sobreposicao/perfil de credores MIDES")
print("=" * 72)
print("  Nota de leitura: prefeito_partido_2016 != prefeito_partido_2020 mede")
print("  TROCA DE PARTIDO, nao troca de pessoa — sucessao pelo mesmo partido")
print("  conta como 'nao-troca' aqui. Distinguir reeleicao de sucessao exigiria")
print("  sequencial_candidato (nao extraido nesta rodada, ver plano de fechamento);")
print("  o teste abaixo responde a pergunta como o dado permite: partido, nao pessoa.")

def perm_test_mediana(x, g, n_perm=5000, seed=0):
    """Diferenca de mediana grupo1-grupo0 + teste de permutacao (numpy puro)."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, dtype=float)
    mask = np.asarray(g, dtype=bool).copy()
    obs = np.nanmedian(x[mask]) - np.nanmedian(x[~mask])
    diffs = np.empty(n_perm)
    work = mask.copy()
    for i in range(n_perm):
        rng.shuffle(work)
        diffs[i] = np.nanmedian(x[work]) - np.nanmedian(x[~work])
    p = (np.sum(np.abs(diffs) >= abs(obs)) + 1) / (n_perm + 1)
    return obs, p

for var in ["mides_jaccard_credor", "entrantes_share_nao_local", "entrantes_share_sancionado"]:
    s = d[["troca_partido_2016_2020", var]].dropna()
    g1 = s.troca_partido_2016_2020.astype(bool)
    n1, n0 = int(g1.sum()), int((~g1).sum())
    med1, med0 = s.loc[g1, var].median(), s.loc[~g1, var].median()
    obs, p = perm_test_mediana(s[var].values, g1.values)
    print(f"  {var:26s} troca(n={n1}) mediana {med1:.4f}  vs  "
          f"nao-troca(n={n0}) mediana {med0:.4f}   diff={obs:+.4f}  p(perm)={p:.4f}")

print()
print("=" * 72)
print("H44c · checagem de magnitude — maternidade adolescente (SINASC)")
print("=" * 72)
s = d[["sinasc_share_mae_adolescente", "sinasc_nascidos", "sinasc_mae_adolescente"]].dropna()
print(f"  n municipios: {len(s)}")
print(f"  media {s.sinasc_share_mae_adolescente.mean():.3%}  "
      f"mediana {s.sinasc_share_mae_adolescente.median():.3%}  "
      f"p10 {s.sinasc_share_mae_adolescente.quantile(.1):.3%}  "
      f"p90 {s.sinasc_share_mae_adolescente.quantile(.9):.3%}")
print(f"  agregado (soma mae_adolescente / soma nascidos): "
      f"{s.sinasc_mae_adolescente.sum()/s.sinasc_nascidos.sum():.3%}")
fora = s[(s.sinasc_share_mae_adolescente < 0.02) | (s.sinasc_share_mae_adolescente > 0.45)]
print(f"  fora da faixa plausivel [2%,45%]: {len(fora)} municipios "
      f"({len(fora)/len(s):.2%})")
print("  <- referencia externa: taxa nacional de mae adolescente (10-19 anos)")
print("     no SINASC/MS ronda ~15-18% dos nascidos vivos nos anos recentes;")
print("     o agregado acima deve cair nessa vizinhanca para nao ser erro de")
print("     denominador (ex.: nascidos vivos vs. total de registros SINASC).")

print()
print("=" * 72)
print("H45 · checagem de magnitude — razao CFEM 2022-25/2017-21")
print("=" * 72)
s = d[["cfem_razao_2225_1721", "cfem_valor", "cfem_valor_2017_2021"]].dropna()
print(f"  n municipios: {len(s)}")
print(f"  mediana {s.cfem_razao_2225_1721.median():.3f}  "
      f"p10 {s.cfem_razao_2225_1721.quantile(.1):.3f}  "
      f"p90 {s.cfem_razao_2225_1721.quantile(.9):.3f}  "
      f"max {s.cfem_razao_2225_1721.max():.1f}")
peq = s.cfem_valor_2017_2021.quantile(.05)
dominado = s[s.cfem_valor_2017_2021 <= peq]
print(f"  denominador (cfem_valor_2017_2021) p5 = R$ {peq:,.0f}")
print(f"  entre os 5% de menor denominador (n={len(dominado)}): "
      f"razao mediana {dominado.cfem_razao_2225_1721.median():.1f}, "
      f"max {dominado.cfem_razao_2225_1721.max():.1f}")
extremos = s[s.cfem_razao_2225_1721 > 10]
print(f"  municipios com razao > 10x: {len(extremos)} "
      f"({len(extremos)/len(s):.2%}) — candidatos a denominador quase-zero")
print("  <- se a razao explode so nesses poucos casos de denominador ínfimo,")
print("     a correlacao nula de H45 nao e' driven por outlier: e' nula no")
print("     grosso da distribuicao tambem. Se sumir ao excluir esses, o nulo")
print("     era so ruido de poucos municipios.")
d3 = d[d.cfem_valor_2017_2021 > peq] if "cfem_valor_2017_2021" in d.columns else d
rb2, nb2 = bruto("cfem_razao_2225_1721", "d_caged_mineracao_pc", d3)
rb3, nb3 = bruto("cfem_razao_2225_1721", "cauc_pendencias", d3)
print(f"  excluindo o p5 de menor denominador — reconfere o nulo original:")
print(f"    x CAGED   bruto {rb2:+.4f} (n={nb2})  (era {bruto('cfem_razao_2225_1721','d_caged_mineracao_pc')[0]:+.4f} no painel inteiro)")
print(f"    x CAUC    bruto {rb3:+.4f} (n={nb3})  (era {bruto('cfem_razao_2225_1721','cauc_pendencias')[0]:+.4f} no painel inteiro)")
