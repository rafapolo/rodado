#!/usr/bin/env python3
"""Fecha H05, H08, H14, H15 de tasks/hipoteses.md — as quatro que ficaram
abertas na primeira bateria por precisarem de RECORTE TEMPORAL, nao de mais
analise sobre o acumulado. Extracao em scripts/hipoteses/70_temporais.sql
(rodada sobre ~/rodado_hipoteses/temporais/ no beelink, copiada para
.hipoteses/temporais/ local, gitignorado).

  python3 scripts/hipoteses/98_temporais.py
"""
import os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = lambda f: os.path.join(ROOT, ".hipoteses", "temporais", f)
R = lambda f: os.path.join(ROOT, "tasks", "hipoteses_resultado", "20260906", f)

painel = pd.read_csv(os.path.join(ROOT, ".hipoteses", "20260906_blocof", "painel.csv"),
                      low_memory=False).replace([np.inf, -np.inf], np.nan)
painel = painel[painel.id_municipio.notna()].copy()
painel["id_municipio"] = painel.id_municipio.astype("int64")

uf_dum = pd.get_dummies(painel["sigla_uf"], drop_first=True).astype(float)
BASE = pd.concat([pd.DataFrame({
    "lp": np.log(painel.populacao.clip(lower=1)),
    "lpib": np.log(painel.pib_pc.clip(lower=1)),
    "c": 1.0}), uf_dum], axis=1)
BASE.index = painel.index

def parcial_generic(a, b, frame, base_extra=None):
    """Parcial de Spearman com log-pop/log-pib/UF, sobre um frame arbitrario
    (nao precisa ser o painel principal) desde que tenha as mesmas colunas
    base ja mescladas nele."""
    C = base_extra
    m = frame[a].notna() & frame[b].notna() & C.notna().all(axis=1)
    if m.sum() < 30: return np.nan, int(m.sum())
    X = C[m].values; r = []
    for col in (a, b):
        y = pd.Series(frame.loc[m, col].values).rank().values
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        r.append(y - X @ beta)
    return round(float(np.corrcoef(r[0], r[1])[0, 1]), 4), int(m.sum())

def bruto(a, b, frame):
    s = frame[[a, b]].dropna()
    if len(s) < 10: return np.nan, len(s)
    return round(s[a].rank().corr(s[b].rank()), 4), len(s)

def perm_test(x, g, stat="mediana", n_perm=5000, seed=0):
    """Teste de permutacao numpy puro. stat='mediana' ou 'media' — a mediana
    degenera quando a variavel tem muitos zeros exatos (ex.: fatia paga a
    sancionado em janela curta, onde a maioria dos municipios nao paga
    sancionado nem antes nem depois — usar 'media' nesse caso). Devolve
    tambem o desvio-padrao da distribuicao nula (para transformar "sem
    diferenca detectavel" num limite superior de efeito, em vez de deixar
    a leitura em aberto — nulo sem magnitude nao e' resultado, e' ausencia)."""
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
print("H05 · CGU FEF sorteio: pre x pos no pagamento MIDES a sancionado")
print("=" * 72)
fef = pd.read_csv(T("v_fef_evento.csv"))
mides = pd.read_csv(T("v_mides_sancionado_ano.csv"))
mides["share"] = np.where(mides.pag_total_valor.notna() & (mides.pag_total_valor > 0),
                           mides.pag_sancionado_valor.fillna(0) / mides.pag_total_valor, np.nan)

def janela_share(id_mun, ano_pivot, lo, hi):
    s = mides[(mides.id_municipio == id_mun) & (mides.ano.between(ano_pivot + lo, ano_pivot + hi))]
    return s.share.mean() if len(s) else np.nan

tratados = fef.id_municipio.unique()
placebo_ano = int(fef.ano_sorteio.median())
todos_mides = mides.id_municipio.unique()
controle = np.setdiff1d(todos_mides, tratados)
print(f"  tratados (sorteados ao menos 1x): {len(tratados)}")
print(f"  controle (nunca sorteados, com pagamento MIDES): {len(controle)}")
print(f"  ano placebo pro controle (mediana do ano_sorteio tratado): {placebo_ano}")

rows = []
for id_mun in tratados:
    ano0 = int(fef.loc[fef.id_municipio == id_mun, "ano_sorteio"].iloc[0])
    pre = janela_share(id_mun, ano0, -3, -1)
    pos = janela_share(id_mun, ano0, 1, 3)
    if pd.notna(pre) and pd.notna(pos):
        rows.append((id_mun, 1, pre, pos, pos - pre))
for id_mun in controle:
    pre = janela_share(id_mun, placebo_ano, -3, -1)
    pos = janela_share(id_mun, placebo_ano, 1, 3)
    if pd.notna(pre) and pd.notna(pos):
        rows.append((id_mun, 0, pre, pos, pos - pre))
did = pd.DataFrame(rows, columns=["id_municipio", "tratado", "pre", "pos", "delta"])
n_t, n_c = (did.tratado == 1).sum(), (did.tratado == 0).sum()
print(f"  com pre E pos observados: {n_t} tratados, {n_c} controle")
if n_t >= 20 and n_c >= 20:
    zero_share = (did.delta == 0).mean()
    print(f"  {zero_share:.1%} dos deltas sao exatamente 0 (sem pagamento a sancionado nem "
          f"antes nem depois em janela de 3 anos) — mediana degenera, usar media.")
    obs, p, sd_null = perm_test(did.delta.values, (did.tratado == 1).values, stat="media")
    print(f"  Delta medio tratado:  {did.loc[did.tratado==1,'delta'].mean():+.4%}")
    print(f"  Delta medio controle: {did.loc[did.tratado==0,'delta'].mean():+.4%}")
    print(f"  diff-in-diff (medias) = {obs:+.4%}   p(permutacao, 5000) = {p:.4f}")
    ic95 = 1.96 * sd_null
    media_fatia = mides.share.mean()
    print(f"  IC95%% do efeito ~ {obs:+.4%} +/- {ic95:.4%}  (desvio-padrao da distribuicao nula, 5000 permutacoes)")
    print(f"  fatia media paga a sancionado no painel: {media_fatia:.3%} — o IC descarta efeitos "
          f"maiores que ~{ic95/media_fatia:.0%} da media")
    print("  <- falseador: nao haver diferenca detectavel entre sorteados e nao-sorteados.")
    print("     Sinal esperado se H05 vale: tratado cai MAIS (delta mais negativo) que controle.")
    print("     Leitura correta: nao e' so 'sem diferenca' — o desenho quase-experimental")
    print("     descarta com poder um efeito de fiscalizacao maior que ~1/5 da fatia media.")
    print("     CAUC ficou fora (tabela e' foto unica, sem coluna de ano — ver 70_temporais.sql).")
else:
    print("  [n insuficiente para o teste]")

# =========================================================================
print()
print("=" * 72)
print("H08 · dose acumulada de PBF (2004-2020) x mortalidade infantil 2021-2024")
print("=" * 72)
sim = pd.read_csv(T("v_sim_obitos_pos2020.csv"))
sinasc = pd.read_csv(T("v_sinasc_nascidos_ano.csv"))
obitos_inf = (sim[(sim.idade >= 0) & (sim.idade <= 1)]
              .groupby("id_municipio").size().rename("obitos_infantis"))
nasc = sinasc.groupby("id_municipio")["nascidos"].sum().rename("nascidos_2124")
h08 = pd.concat([obitos_inf, nasc], axis=1).reset_index()
h08["mortalidade_infantil_2124"] = np.where(
    h08.nascidos_2124.notna() & (h08.nascidos_2124 > 0),
    h08.obitos_infantis.fillna(0) / h08.nascidos_2124 * 1000, np.nan)
d8 = painel.merge(h08[["id_municipio", "mortalidade_infantil_2124", "nascidos_2124"]],
                   on="id_municipio", how="left")
d8 = d8[d8.nascidos_2124.fillna(0) >= 100]  # mesma regra de volume que o resto do bloco (H43/H44)
print(f"  municipios com >=100 nascidos 2021-2024: {len(d8)}")
print(f"  mortalidade infantil (obitos<=1 ano / 1000 nascidos) mediana: "
      f"{d8.mortalidade_infantil_2124.median():.2f}  p10 {d8.mortalidade_infantil_2124.quantile(.1):.2f}  "
      f"p90 {d8.mortalidade_infantil_2124.quantile(.9):.2f}")
print("  <- referencia externa: TMI nacional do SINASC/MS ronda 11-13 por mil nos anos recentes.")

uf_dum8 = pd.get_dummies(d8["sigla_uf"], drop_first=True).astype(float)
BASE8 = pd.concat([pd.DataFrame({"lp": np.log(d8.populacao.clip(lower=1)),
                                 "lpib": np.log(d8.pib_pc.clip(lower=1)), "c": 1.0}), uf_dum8], axis=1)
BASE8.index = d8.index
rb, nb = bruto("pbf_valor_acumulado", "mortalidade_infantil_2124", d8)
rp, npp = parcial_generic("pbf_valor_acumulado", "mortalidade_infantil_2124", d8, BASE8)
ivs0 = pd.DataFrame({"ivs0": d8.ivs_2000.rank()}, index=d8.index)
BASE8b = pd.concat([BASE8, ivs0], axis=1)
rp2, npp2 = parcial_generic("pbf_valor_acumulado", "mortalidade_infantil_2124", d8, BASE8b)
print(f"  bruto                           {rb:+.4f} (n={nb})")
print(f"  + log-pop, log-pib, UF          {rp:+.4f} (n={npp})")
print(f"  + IVS 2000 (condicao inicial)   {rp2:+.4f} (n={npp2})")
print("  <- falseador: dose acumulada NAO prever mortalidade infantil pos-2020")
print("     mesmo controlando o ponto de partida. Sinal esperado se H08 vale: negativo")
print("     (mais PBF acumulado -> menos mortalidade infantil depois).")
print()
print("  AVISO: pbf_valor_acumulado e' valor PAGO, logo e' mecanicamente uma")
print("  medida de pobreza (mais familia pobre -> mais PBF pago) — mesma estrutura")
print("  do C4 (INSE do INEP e' indice de pobreza com outro nome, r=-0,90 com BF).")
print("  IVS 2000 fixa o ponto de PARTIDA, nao a pobreza CONTEMPORANEA que gerou")
print("  o valor pago ao longo de 2004-2020. Duas checagens para isolar o efeito:")
d8["pbf_valor_acumulado_pc"] = d8.pbf_valor_acumulado / d8.populacao.clip(lower=1)
rb_pc, nb_pc = bruto("pbf_valor_acumulado_pc", "mortalidade_infantil_2124", d8)
rp_pc, npp_pc = parcial_generic("pbf_valor_acumulado_pc", "mortalidade_infantil_2124", d8, BASE8b)
print(f"  (a) PBF acumulado PER CAPITA (tira o mecanico de tamanho de populacao):")
print(f"      bruto {rb_pc:+.4f} (n={nb_pc})   + controles+IVS0 {rp_pc:+.4f} (n={npp_pc})")
nbf0 = pd.DataFrame({"nbf0": d8.nbf_share_dom.rank()}, index=d8.index)
BASE8c = pd.concat([BASE8, nbf0], axis=1)
rp3, npp3 = parcial_generic("pbf_valor_acumulado", "mortalidade_infantil_2124", d8, BASE8c)
print(f"  (b) + cobertura do Bolsa Familia ATUAL no controle (proxy de pobreza")
print(f"      contemporanea, em vez de so o ponto de partida de 2000):")
print(f"      {rp3:+.4f} (n={npp3})")
print(f"  (c) especificacao decisiva (diagnostico da outra sessao, 2026-09-06):")
print(f"      pbf_valor_acumulado e' EXTENSIVO (r=+0,78 com populacao, mais forte")
print(f"      que com nbf_share_dom +0,60) — resid em rank de log-pop nao absorve")
print(f"      variavel extensiva, mesma armadilha que derrubou o D1 (CAFIR x")
print(f"      desmatamento). Teste que separa: exposicao PER CAPITA *e* pobreza")
print(f"      atual no MESMO controle — as duas juntas, nao uma de cada vez:")
BASE8d = pd.concat([BASE8, nbf0], axis=1)
rp4, npp4 = parcial_generic("pbf_valor_acumulado_pc", "mortalidade_infantil_2124", d8, BASE8d)
print(f"      per capita + log-pop/pib/UF + nbf_share_dom:  {rp4:+.4f} (n={npp4})")
print("  <- se cair perto de zero aqui, o residual inteiro era escala (extensiva)")
print("     disfarcada de dose — nao sobrevive nem ao confound mecanico nem ao de")
print("     tamanho juntos. Se NAO cair, o residual e' substantivo.")
print("     e a leitura correta de H08 vira 'este desenho nao pode falar sobre o")
print("     programa em nenhuma direcao', nao 'PBF nao funciona'.")

# =========================================================================
print()
print("=" * 72)
print("H14 · Garantia-Safra x inadimplencia rural do SCR, por UF (defasagem)")
print("=" * 72)
scr = pd.read_csv(T("v_scr_rural_uf.csv"), low_memory=False)
scr["inadimplencia"] = pd.to_numeric(scr.inadimplencia_raw, errors="coerce")
scr["ativa"] = pd.to_numeric(scr.ativa_raw, errors="coerce")
scr["ano"] = pd.to_datetime(scr.data_base, errors="coerce").dt.year
scr["mes"] = pd.to_datetime(scr.data_base, errors="coerce").dt.month
dez = scr[scr.mes == 12].groupby(["uf", "ano"], as_index=False)[["inadimplencia", "ativa"]].sum()
dez["razao_inad"] = np.where(dez.ativa > 0, dez.inadimplencia / dez.ativa, np.nan)
print(f"  UF-anos com dezembro observado: {len(dez)} ({dez.uf.nunique()} UFs, "
      f"{dez.ano.min()}-{dez.ano.max()})")

gs = pd.read_csv(R("v_garantia_safra.csv"))
mun_uf = painel[["id_municipio", "sigla_uf"]].rename(columns={"sigla_uf": "uf"})
gs = gs.merge(mun_uf, on="id_municipio", how="left")
gs_uf = gs.groupby(["uf", "ano"], as_index=False)["gs_beneficiarios"].sum()

# painel defasado: GS no ano t x Delta inadimplencia (t -> t+1)
dez = dez.sort_values(["uf", "ano"])
dez["razao_prox_ano"] = dez.groupby("uf")["razao_inad"].shift(-1)
dez["delta_inad_seguinte"] = dez.razao_prox_ano - dez.razao_inad
painel_h14 = dez.merge(gs_uf, on=["uf", "ano"], how="inner").dropna(subset=["delta_inad_seguinte", "gs_beneficiarios"])
print(f"  UF-anos com GS E par de inadimplencia consecutivo: {len(painel_h14)}")
if len(painel_h14) >= 30:
    rb = painel_h14.gs_beneficiarios.rank().corr(painel_h14.delta_inad_seguinte.rank())
    uf_dum14 = pd.get_dummies(painel_h14["uf"], drop_first=True).astype(float)
    C14 = pd.concat([pd.DataFrame({"c": 1.0}, index=painel_h14.index), uf_dum14], axis=1)
    X = C14.values
    y1 = painel_h14.gs_beneficiarios.rank().values
    y2 = painel_h14.delta_inad_seguinte.rank().values
    b1, *_ = np.linalg.lstsq(X, y1, rcond=None); r1 = y1 - X @ b1
    b2, *_ = np.linalg.lstsq(X, y2, rcond=None); r2 = y2 - X @ b2
    rp14 = np.corrcoef(r1, r2)[0, 1]
    print(f"  GS(t) x Delta_inadimplencia(t->t+1): bruto {rb:+.4f}   + efeito fixo de UF {rp14:+.4f}")
    print("  <- falseador: nao haver defasagem detectavel (correlacao ~0).")
else:
    print("  [n insuficiente]")

# =========================================================================
print()
print("=" * 72)
print("H15 · capital social do estabelecimento x queda de vinculos RAIS 2019->2020")
print("=" * 72)
rais = pd.read_csv(T("v_rais_vinculos_1920.csv"))
piv = rais.pivot_table(index="id_municipio", columns="ano", values="vinculos", aggfunc="sum")
piv.columns = [f"vinc_{c}" for c in piv.columns]
piv = piv.reset_index()
d15 = painel.merge(piv, on="id_municipio", how="left")
d15["delta_vinculos_pct"] = np.where(
    d15.vinc_2019.notna() & (d15.vinc_2019 > 0),
    d15.vinc_2020 / d15.vinc_2019 - 1, np.nan)
print(f"  municipios com vinculos 2019 e 2020: {d15.delta_vinculos_pct.notna().sum()}")
print(f"  queda mediana de vinculos 2019->2020: {d15.delta_vinculos_pct.median():+.2%}")
rb, nb = bruto("capital_social_mediano", "delta_vinculos_pct", d15)
rp, npp = parcial_generic("capital_social_mediano", "delta_vinculos_pct", d15, BASE)
porte = pd.DataFrame({"lvinc19": np.log(d15.vinc_2019.clip(lower=1))}, index=d15.index)
BASE15 = pd.concat([BASE, porte], axis=1)
rp2, npp2 = parcial_generic("capital_social_mediano", "delta_vinculos_pct", d15, BASE15)
print(f"  bruto                              {rb:+.4f} (n={nb})")
print(f"  + log-pop, log-pib, UF             {rp:+.4f} (n={npp})")
print(f"  + log(vinculos 2019) [porte]       {rp2:+.4f} (n={npp2})")
print("  <- falseador: capital social ser puro proxy de porte — some ao controlar")
print("     log(vinculos_2019) alem do padrao.")
