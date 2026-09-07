#!/usr/bin/env python3
"""Funde os CSV do lote h3 no painel-mestre municipal.

  scp -r beelink:~/rodado_hipoteses/h3_20260907 tasks/hipoteses_resultado/
  python3 scripts/hipoteses/h3_10_estende_painel.py

Tres chaves diferentes aparecem no lote, e misturar as tres e o erro classico
deste espelho:
  * `id_municipio`      IBGE de 7 digitos -- a maioria
  * `m6`                codigo do SUS de 6 digitos -- os SINAN crus do DATASUS
  * `municipiocodigo`   ANA telemetria, que nao se sabe de antemao se e 6 ou 7
                        (o script decide medindo, nao chutando)
As pontes vem do bloco 00 (h3_ponte_mun6.csv).
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd

REPO  = Path(__file__).resolve().parent.parent.parent
RES   = REPO / "tasks" / "hipoteses_resultado"
LOTE  = RES / "h3_20260907"
BASE  = RES / "hipoteses2" / "painel_mestre.csv"
SAIDA = RES / "hipoteses2" / "painel_mestre_h3.csv"

# arquivo -> (chave, colunas a trazer)  |  None = todas menos a chave
PLANO = {
    "h3_inep_inse":          ("id_municipio", None),
    "h3_inep_indicadores":   ("id_municipio", None),
    "h3_inep_docentes":      ("id_municipio", None),
    "h3_inep_especial":      ("id_municipio", None),
    "h3_inep_alfabetizacao": ("id_municipio", None),
    "h3_censo_escolar":      ("id_municipio", None),
    "h3_enem":               ("id_municipio", None),
    "h3_atencao_basica":     ("id_municipio", None),
    "h3_imunizacoes":        ("id_municipio", None),
    "h3_covid_estab":        ("id_municipio", None),
    "h3_gas_do_povo":        ("id_municipio", None),
    "h3_dirpf_fundos":       ("id_municipio", None),
    "h3_emendas":            ("id_municipio", None),
    "h3_seeg":               ("id_municipio", None),
    "h3_mapbiomas":          ("id_municipio", None),
    "h3_ms_populacao":       ("id_municipio", None),
    "h3_abrinq":             ("id_municipio", None),
    "h3_filiacao":           ("id_municipio", None),
    "h3_banda_larga":        ("id_municipio", None),
    "h3_ifgf":               ("id_municipio", None),
    "h3_sia":                ("id_municipio", None),
    "h3_ans":                ("id_municipio", None),
    "h3_bolsa_familia":      ("id_municipio", None),
    "h3_sisvan":             ("id_municipio", None),
}

def carrega(nome):
    f = LOTE / f"{nome}.csv"
    if not f.exists():
        print(f"  AUSENTE {nome}.csv"); return None
    return pd.read_csv(f, low_memory=False)

def por_municipio(d, chave="id_municipio"):
    d = d[d[chave].notna()].copy()
    d[chave] = pd.to_numeric(d[chave], errors="coerce").astype("Int64")
    return d[d[chave].notna()].drop_duplicates(chave).set_index(chave)

def main():
    if not BASE.exists():
        sys.exit(f"{BASE} nao existe -- rode 00_painel_mestre.py antes")
    base = pd.read_csv(BASE, low_memory=False)
    base["id_municipio"] = base["id_municipio"].astype("int64")
    base = base.set_index("id_municipio")
    print(f"painel-mestre: {base.shape[0]} municipios x {base.shape[1]} colunas")

    novas = 0
    for nome, (chave, cols) in PLANO.items():
        d = carrega(nome)
        if d is None: continue
        d = por_municipio(d, chave)
        cols = [c for c in (cols or d.columns) if c not in base.columns]
        if not cols:
            print(f"  {nome}: nada novo"); continue
        base = base.join(d[cols], how="left")
        novas += len(cols); print(f"  {nome}: +{len(cols)} colunas")

    # --- SINAN crus: chave m6, e a serie vem por ano -> soma dos 3 ultimos anos
    def chave6(s):
        """'320460.0' -> '320460'. O CSV vem com NaN em algumas linhas, entao o
        pandas le a coluna como float e str() deixa o '.0' -- que nao casa com
        nada e produz coluna inteira vazia em silencio."""
        return (pd.Series(s).astype(str)
                .str.replace(r"\.0$", "", regex=True).str.zfill(6))

    ponte = carrega("h3_ponte_mun6")
    if ponte is not None:
        ponte["m6"] = chave6(ponte["m6"])
        m6_para_7 = dict(zip(ponte["m6"], ponte["id_municipio"]))
        for nome, col in [("h3_sinan_chikungunya","chik_casos"),
                          ("h3_sinan_zika","zika_casos"),
                          ("h3_sinan_esquistossomose","esquisto_casos")]:
            d = carrega(nome)
            if d is None: continue
            d["ano_num"] = pd.to_numeric(d["ano"], errors="coerce")
            vazio = d["ano_num"].isna().sum()
            if vazio:
                # o mesmo NU_ANO vazio que faz um GROUP BY pular 2020 em silencio
                print(f"  AVISO {nome}: {vazio} linhas com ano nao numerico (mantidas na soma)")
            ult = d["ano_num"].max()
            rec = d[(d["ano_num"] >= ult - 2) | d["ano_num"].isna()]
            # traduz PRIMEIRO, agrega DEPOIS: varios codigos do SUS caem no
            # mesmo municipio IBGE, e somar antes deixa indice duplicado.
            rec = rec.assign(id_municipio=[m6_para_7.get(k) for k in chave6(rec["m6"])])
            s = (rec[rec.id_municipio.notna()]
                 .groupby("id_municipio")[col].sum())
            s.index = s.index.astype("int64")
            base[col] = s
            novas += 1; print(f"  {nome}: +1 coluna (soma dos 3 ultimos anos)")

    # dengue ja vem com id_municipio de 7 digitos, mas tambem por ano
    d = carrega("h3_sinan_dengue")
    if d is not None:
        d["ano_num"] = pd.to_numeric(d["ano"], errors="coerce")
        ult = d["ano_num"].max()
        s = d[d["ano_num"] >= ult - 2].groupby("id_municipio")["dengue_casos"].sum()
        s.index = s.index.astype("int64")
        base["dengue_casos_3a"] = s; novas += 1
        print("  h3_sinan_dengue: +1 coluna (soma dos 3 ultimos anos)")

    # ESTBAN vem longo (um valor por verbete) -> pivota os 8 verbetes maiores
    d = carrega("h3_estban")
    if d is not None:
        top = d.groupby("id_verbete")["valor"].sum().abs().nlargest(8).index
        pv = (d[d.id_verbete.isin(top)]
              .pivot_table(index="id_municipio", columns="id_verbete", values="valor", aggfunc="sum"))
        pv.columns = [f"estban_v{c}" for c in pv.columns]
        pv.index = pv.index.astype("int64")
        base = base.join(pv, how="left"); novas += pv.shape[1]
        print(f"  h3_estban: +{pv.shape[1]} colunas (8 maiores verbetes, pivotados)")

    # ANA telemetria FICA DE FORA, e o motivo importa: `municipiocodigo` nao e
    # codigo IBGE -- os valores sao '3037000', '2011000', de 7 e 8 digitos, e nao
    # existe UF 30 nem 20. E codigo interno da propria ANA, e o espelho nao tem
    # ponte para IBGE. Juntar por ele produziria coluna vazia (ou pior, casada
    # por acidente). Fica registrado como pendencia, nao como coluna morta.
    d = None
    if d is not None and ponte is not None:
        k = d["municipiocodigo"].astype(str).str.replace(r"\.0$", "", regex=True)
        comp = k.str.len().mode().iat[0]
        print(f"  h3_ana_telemetria: chave com {comp} digitos ->", "ponte m6" if comp == 6 else "join direto")
        if comp == 6:
            d["id_municipio"] = [m6_para_7.get(x.zfill(6)) for x in k]
        else:
            d["id_municipio"] = pd.to_numeric(k, errors="coerce")
        d = d[d["id_municipio"].notna()]
        d = por_municipio(d)
        cols = [c for c in d.columns if c.startswith("ana_")]
        base = base.join(d[cols], how="left"); novas += len(cols)
        print(f"  h3_ana_telemetria: +{len(cols)} colunas")

    base.to_csv(SAIDA)
    print(f"\n{SAIDA.relative_to(REPO)}: {base.shape[0]} municipios x {base.shape[1]} colunas (+{novas})")

if __name__ == "__main__":
    sys.exit(main())
