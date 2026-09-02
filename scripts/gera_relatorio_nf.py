#!/usr/bin/env python3
"""Levantamento semestral de atividades potencialmente geradoras de poluentes
atmosféricos em Nova Friburgo/RJ.

Roda as consultas no beelink, monta o dado e renderiza a página a partir de
`pages/analises/poluentes-do-ar-em-nova-friburgo/_page.html` (fonte única) em
dois destinos:

  index.html      página do site (nav + rodapé do rodado; gera_seo.py injeta o
                  bloco de <head> depois, pela linha do site.css)
  --artifact P    cópia autocontida, sem <html>/<head>/<body>, pro Artifact

Uso, no próximo semestre:

    python3 scripts/gera_relatorio_nf.py --ref 2026-03
    python3 scripts/gera_analises.py          # SEO + cartão

O `--ref` é a foto do cadastro (ano-mês de uma partição de
`br_me_cnpj.estabelecimentos`); sem ele, usa a partição mais recente que
existir. A série semestral usa março e setembro de cada ano.
"""

import argparse
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "pages" / "analises" / "poluentes-do-ar-em-nova-friburgo"
MOLDE = PASTA / "_page.html"
BEELINK = os.environ.get("BEELINK_HOST", "beelink")
MUNICIPIO = "3303401"  # Nova Friburgo (RJ)

# CNAE 2.3 -> categoria do pedido. A macro vive no SQL; aqui fica o texto.
CATS = [
    ("1", "Marmorarias",
     ["2391-5/03 Aparelhamento de placas e trabalhos em mármore, granito, ardósia e outras pedras",
      "2391-5/02 Aparelhamento de pedras para construção, exceto associado à extração"],
     "Emissão característica: material particulado do corte e polimento a seco de "
     "rochas ornamentais (sílica cristalina)."),
    ("2", "Metalúrgicas — metalurgia (CNAE divisão 24)",
     ["24 Metalurgia — fundição de ferro/aço e de não ferrosos, produção e laminação de metais"],
     "Núcleo da categoria: fusão e refino de metal. É a leitura estrita de “metalúrgica”."),
    ("2b", "Metalúrgicas — fabricação de produtos de metal (CNAE divisão 25)",
     ["25 Fabricação de produtos de metal, exceto máquinas e equipamentos — serralheria, "
      "esquadrias, usinagem, solda, tratamento e revestimento de metais"],
     "Leitura ampliada. É onde estão as fontes reais de fumos de solda, jateamento, "
     "decapagem, galvanoplastia e pintura industrial em Nova Friburgo — e onde as empresas "
     "que se chamam “metalúrgica” estão de fato cadastradas."),
    ("3", "Torrefação e moagem de café",
     ["1081-3/02 Torrefação e moagem de café", "1081-3/01 Beneficiamento de café"],
     "Emissão característica: material particulado e compostos orgânicos voláteis da torra; odor."),
    ("4", "Fabricação de produtos químicos",
     ["20 Fabricação de produtos químicos — inorgânicos, orgânicos, resinas, defensivos, "
      "sabões e detergentes, cosméticos, tintas e vernizes, aditivos"],
     "Divisão inteira da CNAE, conforme o pedido (“fabricação de produtos químicos”, sem recorte)."),
    ("5", "Olaria e artefatos de cerâmica",
     ["2341-9/00 Produtos cerâmicos refratários", "2342-7/01 Azulejos e pisos",
      "2342-7/02 Artefatos de cerâmica e barro cozido para construção",
      "2349-4/01 Material sanitário de cerâmica",
      "2349-4/99 Produtos cerâmicos não refratários n.e."],
     "Emissão característica: queima em forno. Atenção: em Nova Friburgo a 2349-4/99 "
     "concentra ateliês de cerâmica artística, não olaria industrial."),
    ("6", "Gesso e produtos à base de gesso",
     ["2392-3/00 Fabricação de cal e gesso",
      "2330-3/99 Outros artefatos de concreto, cimento, fibrocimento, gesso e materiais semelhantes"],
     "A CNAE específica de fabricação de gesso (2392-3/00) não tem nenhum registro no "
     "município. A 2330-3/99 é uma classe agregada que mistura concreto, cimento, "
     "fibrocimento e gesso — não permite isolar o gesso."),
    ("7", "Produção de gorduras vegetais e animais",
     ["1041-4/00 Óleos vegetais em bruto", "1042-2/00 Óleos vegetais refinados",
      "1043-1/00 Margarina e outras gorduras vegetais e óleos não comestíveis de animais",
      "1013-9/02 Preparação de subprodutos do abate (graxaria)"],
     "A 1013-9/02 foi incluída porque é onde se cadastra a graxaria — o processamento de "
     "sebo e subprodutos animais, a fonte de odor e particulado da categoria."),
    ("8", "Extração de minerais não metálicos",
     ["08 Extração de minerais não metálicos — areia, argila, saibro, granito, mármore, "
      "ardósia, calcário, basalto, gemas e britamento associado",
      "2391-5/01 Britamento de pedras, exceto associado à extração"],
     "Cobre areia, argila, pedras, brita e demais minerais não metálicos, como pedido. "
     "O britamento fora da lavra (2391-5/01) entra aqui porque é a mesma emissão."),
]

MACRO = """
CREATE OR REPLACE TEMP MACRO cat(c) AS
  CASE
    WHEN c IN ('2391503','2391502') THEN '1'
    WHEN c LIKE '24%' THEN '2'
    WHEN c LIKE '25%' THEN '2b'
    WHEN c IN ('1081302','1081301') THEN '3'
    WHEN c LIKE '20%' THEN '4'
    WHEN c IN ('2341900','2342701','2342702','2349401','2349499') THEN '5'
    WHEN c IN ('2392300','2330399') THEN '6'
    WHEN c IN ('1041400','1042200','1043100','1013902') THEN '7'
    WHEN c LIKE '08%' OR c = '2391501' THEN '8'
  END;
"""


def duck(sql: str):
    """Uma consulta -> lista de dicts. Sempre -readonly (o beelink tem sessões
    concorrentes; conexão de escrita trava todo mundo)."""
    saida = subprocess.run(
        ["ssh", BEELINK, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
        input="SET enable_progress_bar=false;\n" + sql,
        capture_output=True, text=True, check=True).stdout.strip()
    return json.loads(saida) if saida else []


def ultima_particao():
    r = duck("SELECT max(ano*100+mes) AS p FROM br_me_cnpj.estabelecimentos;")
    p = int(r[0]["p"])
    return p // 100, p % 100


def semestres(ano_fim, mes_fim):
    """Pontos da série: março e setembro de cada ano, até a referência."""
    disp = {(r["ano"], r["mes"]) for r in
            duck("SELECT DISTINCT ano, mes FROM br_me_cnpj.estabelecimentos;")}
    pts = [(a, m) for a in range(2022, ano_fim + 1) for m in (3, 9)
           if (a, m) in disp and (a * 100 + m) <= (ano_fim * 100 + mes_fim)]
    return pts[-7:]


def coleta(ano, mes):
    onde = (f"ano={ano} AND mes={mes} AND sigla_uf='RJ' AND id_municipio='{MUNICIPIO}'")

    estab = duck(MACRO + f"""
WITH e AS (SELECT * FROM br_me_cnpj.estabelecimentos WHERE {onde}),
prin AS (SELECT e.cnpj, cat(e.cnae_fiscal_principal) AS categoria,
                e.cnae_fiscal_principal AS cnae, 'principal' AS papel
         FROM e WHERE cat(e.cnae_fiscal_principal) IS NOT NULL),
sec AS (SELECT e.cnpj, cat(c.subclasse) AS categoria, c.subclasse AS cnae, 'secundaria' AS papel
        FROM e JOIN br_bd_diretorios_brasil.cnae_2 c
          ON ',' || replace(e.cnae_fiscal_secundaria,' ','') || ',' LIKE '%,' || c.subclasse || ',%'
        WHERE cat(c.subclasse) IS NOT NULL AND c.indicador_cnae_2_3 = 1),
dedup AS (SELECT cnpj, categoria, min(papel) AS papel,
                 any_value(cnae) FILTER (WHERE papel='principal') AS cnae_p,
                 any_value(cnae) AS cnae_any
          FROM (SELECT * FROM prin UNION ALL SELECT * FROM sec) GROUP BY 1,2)
SELECT d.categoria, d.papel, coalesce(d.cnae_p, d.cnae_any) AS cnae, e.cnpj,
       emp.razao_social, e.nome_fantasia,
       CASE e.situacao_cadastral WHEN '1' THEN 'Nula' WHEN '2' THEN 'Ativa'
            WHEN '3' THEN 'Suspensa' WHEN '4' THEN 'Inapta' WHEN '8' THEN 'Baixada' END AS situacao,
       e.data_situacao_cadastral, e.data_inicio_atividade,
       trim(coalesce(e.tipo_logradouro,'') || ' ' || coalesce(e.logradouro,'') || ', '
            || coalesce(e.numero,'S/N')
            || CASE WHEN e.complemento IS NOT NULL AND e.complemento <> ''
                    THEN ' - ' || e.complemento ELSE '' END) AS endereco,
       e.bairro, e.cep,
       CASE emp.porte WHEN '1' THEN 'Microempresa' WHEN '3' THEN 'Pequeno porte'
            WHEN '5' THEN 'Demais' ELSE 'Não informado' END AS porte,
       CASE WHEN s.opcao_mei = 1 THEN 1 ELSE 0 END AS mei
FROM dedup d
JOIN e ON e.cnpj = d.cnpj
LEFT JOIN (SELECT * FROM br_me_cnpj.empresas WHERE ano={ano} AND mes={mes}) emp
  ON emp.cnpj_basico = e.cnpj_basico
LEFT JOIN br_me_cnpj.simples s ON s.cnpj_basico = e.cnpj_basico
ORDER BY d.categoria, e.situacao_cadastral, emp.razao_social;""")

    pts = semestres(ano, mes)
    filtro = " OR ".join(f"(ano={a} AND mes={m})" for a, m in pts)
    serie = duck(MACRO + f"""
SELECT ano, mes, cat(cnae_fiscal_principal) AS categoria,
       count(*) FILTER (WHERE situacao_cadastral='2') AS ativas, count(*) AS total
FROM br_me_cnpj.estabelecimentos
WHERE sigla_uf='RJ' AND id_municipio='{MUNICIPIO}' AND ({filtro})
  AND cat(cnae_fiscal_principal) IS NOT NULL
GROUP BY 1,2,3 ORDER BY 3,1,2;""")

    rais = duck(MACRO + f"""
SELECT ano, cat(cnae_2_subclasse) AS categoria, count(*) AS estabs,
       sum(quantidade_vinculos_ativos) AS vinculos
FROM br_me_rais.microdados_estabelecimentos
WHERE sigla_uf='RJ' AND id_municipio='{MUNICIPIO}' AND ano >= 2018
  AND cat(cnae_2_subclasse) IS NOT NULL
GROUP BY 1,2 ORDER BY 2,1;""")

    total_mun = duck(f"SELECT count(*) n FROM br_me_cnpj.estabelecimentos WHERE {onde};")[0]["n"]
    ano_rais = max(r["ano"] for r in rais)
    return estab, serie, rais, total_mun, ano_rais


def limpa(t):
    """O cadastro da RFB traz bytes quebrados em alguns endereços; U+FFFD não
    passa no publish do Artifact. Vira '?' — o caractere é ilegível na fonte,
    não some."""
    return t.replace("\ufffd", "?") if isinstance(t, str) else t


def monta(estab, serie, rais, total_mun, ano_rais, ano, mes):
    linhas = [[r["categoria"], 1 if r["papel"] == "principal" else 0, r["cnae"], r["cnpj"],
               limpa((r.get("razao_social") or r.get("nome_fantasia") or "—").strip()),
               limpa(r.get("nome_fantasia") or ""), r["situacao"],
               r.get("data_inicio_atividade") or "", r.get("data_situacao_cadastral") or "",
               limpa(r.get("endereco") or ""), limpa(r.get("bairro") or ""), r.get("cep") or "",
               r.get("porte") or "", r.get("mei") or 0] for r in estab]

    def per(a, m):
        return f"{a}-S{1 if m <= 6 else 2}"

    vistos, unicos = set(), []
    for r in estab:
        if r["cnpj"] not in vistos:
            vistos.add(r["cnpj"])
            unicos.append(r)
    ab, bx = Counter(), Counter()
    for r in unicos:
        if r.get("data_inicio_atividade"):
            ab[int(r["data_inicio_atividade"][:4])] += 1
        if r["situacao"] == "Baixada" and r.get("data_situacao_cadastral"):
            bx[int(r["data_situacao_cadastral"][:4])] += 1
    fluxo = [{"ano": a, "aberturas": ab.get(a, 0), "baixas": bx.get(a, 0)}
             for a in range(2000, ano + 1)]

    resumo = []
    for cid, nome, cnaes, nota in CATS:
        r = [x for x in estab if x["categoria"] == cid]
        cnt = Counter((x["papel"], x["situacao"]) for x in r)
        resumo.append({
            "id": cid, "nome": nome, "cnaes": cnaes, "nota": nota,
            "ativa_p": cnt[("principal", "Ativa")], "ativa_s": cnt[("secundaria", "Ativa")],
            "ativa": cnt[("principal", "Ativa")] + cnt[("secundaria", "Ativa")],
            "inapta": sum(v for (p, s), v in cnt.items() if s == "Inapta"),
            "suspensa": sum(v for (p, s), v in cnt.items() if s == "Suspensa"),
            "baixada": sum(v for (p, s), v in cnt.items() if s == "Baixada"),
            "nula": sum(v for (p, s), v in cnt.items() if s == "Nula"),
            "total": len(r)})

    ativos = {x["cnpj"] for x in estab if x["situacao"] == "Ativa"}
    uniq_at = [x for x in unicos if x["cnpj"] in ativos]
    meses = {3: "1º semestre", 9: "2º semestre"}
    meta = {
        "municipio": "Nova Friburgo", "uf": "RJ", "id_municipio": MUNICIPIO,
        "ref": f"{ano}-{mes:02d}",
        "ref_label": f"{['','janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro'][mes]}/{ano}"
                     + (f" ({meses[mes]} de {ano})" if mes in meses else ""),
        "ref_rais": ano_rais,
        "gerado": subprocess.run(["date", "+%Y-%m-%d"], capture_output=True,
                                 text=True).stdout.strip(),
        "estab_municipio": total_mun, "cnpj_ativos": len(ativos),
        "cnpj_total": len(vistos), "linhas": len(estab),
        "mei_ativos": sum(1 for x in uniq_at if x.get("mei") == 1),
        "porte_ativos": dict(Counter(x.get("porte") or "—" for x in uniq_at)),
        "bairros": Counter(x.get("bairro") or "—" for x in uniq_at).most_common(15),
    }
    cnpjs = {r["cnpj"] for r in estab}
    cruz, negativos = cruzamentos(cnpjs, ano, mes)
    meta["cruzamentos"] = {
        "com_rais": sum(1 for v in cruz.values() if "rais" in v),
        "vinculos_rais": sum(v["rais"][0] for v in cruz.values() if "rais" in v),
        "com_contrato": sum(1 for v in cruz.values() if v.get("contratos")),
        "com_sicaf": sum(1 for v in cruz.values() if "sicaf" in v),
        **negativos}
    return {"meta": meta, "cruz": cruz,
            "fontes": procedencia(ano, mes, ano_rais),
            "cats": [{"id": c[0], "nome": c[1], "cnaes": c[2], "nota": c[3]} for c in CATS],
            "resumo": resumo,
            "serie": [{"per": per(s["ano"], s["mes"]), "cat": s["categoria"],
                       "ativas": s["ativas"], "total": s["total"]} for s in serie],
            "rais": [{"ano": r["ano"], "cat": r["categoria"], "estabs": r["estabs"],
                      "vinculos": int(r["vinculos"])} for r in rais],
            "fluxo": fluxo, "estab": linhas}


# ── cruzamentos por CNPJ: emprego, contrato público, sanção ──────────────────
# Tudo casa por CNPJ. Contrato e sanção casam pela RAIZ do CNPJ (8 primeiros
# dígitos), porque o contrato é assinado pela pessoa jurídica e o levantamento
# lista o estabelecimento — filial e matriz compartilham a raiz.

def cruzamentos(cnpjs, ano, mes):
    lista = ",".join(f"('{c}')" for c in sorted(cnpjs))
    alvo = (f"CREATE OR REPLACE TEMP TABLE alvo AS "
            f"SELECT c AS cnpj, substr(c,1,8) AS bas FROM (VALUES {lista}) t(c);\n")

    # RAIS identificada só vai até 2021 e traz o CNPJ completo; o filtro por
    # município é o que faz a consulta caber no tempo (36M linhas sem ele).
    rais = duck(alvo + f"""
SELECT a.cnpj, max(r.ano) AS ano, max_by(r.quantidade_vinculos_ativos, r.ano) AS vinculos
FROM br_me_rais_identificada.estabelecimentos r
JOIN alvo a ON r.cnpj_basico = a.bas
WHERE r.id_municipio = '{MUNICIPIO}'
  AND regexp_replace(r.cnpj_completo,'[^0-9]','','g') = a.cnpj
GROUP BY 1;""")

    contratos = duck(alvo + """
WITH tce AS (
  SELECT a.cnpj, 'tce' AS fonte, count(*) AS n, round(sum(c."ValorContrato")) AS valor,
         max(c."Ente") AS onde, max(c."AnoContrato"::VARCHAR) AS ano
  FROM br_tce_rj.contratos_municipio c JOIN alvo a
    ON substr(regexp_replace(c."CNPJCPFContratado",'[^0-9]','','g'),1,8) = a.bas
  GROUP BY 1),
cgu AS (
  SELECT a.cnpj, 'cgu' AS fonte, count(*) AS n, round(sum(c.valor_inicial_compra)) AS valor,
         max(c.nome_orgao) AS onde, max(c.ano::VARCHAR) AS ano
  FROM br_cgu_licitacao_contrato.contrato_compra c JOIN alvo a
    ON substr(regexp_replace(c.cpf_cnpj_contratado,'[^0-9]','','g'),1,8) = a.bas
  GROUP BY 1),
sic AS (
  SELECT DISTINCT a.cnpj, 'sicaf' AS fonte, 1 AS n, NULL::DOUBLE AS valor,
         f."habilitadoLicitar"::VARCHAR AS onde, NULL::VARCHAR AS ano
  FROM br_comprasgov_sicaf.fornecedores f JOIN alvo a
    ON regexp_replace(f.cnpj,'[^0-9]','','g') = a.cnpj)
SELECT * FROM tce UNION ALL SELECT * FROM cgu UNION ALL SELECT * FROM sic;""")

    # negativos conferidos: valem como resultado, não como ausência de consulta
    # br_ibama_embargos_novo substitui br_ibama_embargos (2026-09-02): o antigo
    # tinha 113.878 linhas com zero não-vazias — o CSV foi parseado errado na
    # raspagem e os bytes nunca chegaram. Por isso a versão anterior desta query
    # precisava de str_split(x,';') sobre uma coluna única; agora são colunas.
    embargo = duck(alvo + """
SELECT count(*) AS n
FROM read_parquet('~/rodado/br_ibama_embargos_novo/termo_embargo/*.parquet') e
JOIN alvo a ON substr(regexp_replace(e.cpf_cnpj_embargado,'[^0-9]','','g'),1,8) = a.bas;""")[0]["n"]
    inidoneo = duck(alvo + """
SELECT count(*) AS n FROM br_tcu_inidoneos.empresas e JOIN alvo a
  ON substr(regexp_replace(e."CPF_CNPJ",'[^0-9]','','g'),1,8) = a.bas;""")[0]["n"]

    por_cnpj = {}
    for r in rais:
        if r["vinculos"] is not None:
            por_cnpj.setdefault(r["cnpj"], {})["rais"] = [int(r["vinculos"]), r["ano"]]
    for r in contratos:
        d = por_cnpj.setdefault(r["cnpj"], {})
        if r["fonte"] == "sicaf":
            d["sicaf"] = r["onde"] == "true"
        else:
            d.setdefault("contratos", []).append(
                [r["fonte"], r["n"], r["valor"], r["onde"], r["ano"]])
    return por_cnpj, {"embargos_ibama": embargo, "inidoneos_tcu": inidoneo}


DATASETS = [
    ("br_me_cnpj.estabelecimentos", "Receita Federal · CNPJ (estabelecimentos)", "{ref}"),
    ("br_me_cnpj.empresas", "Receita Federal · CNPJ (empresas)", "{ref}"),
    ("br_me_cnpj.simples", "Receita Federal · Simples e MEI", "situação corrente"),
    ("br_bd_diretorios_brasil.cnae_2", "IBGE/Concla · CNAE 2.3", "classificação vigente"),
    ("br_me_rais.microdados_estabelecimentos", "MTE · RAIS estabelecimentos", "até {rais}"),
    ("br_me_rais_identificada.estabelecimentos", "MTE · RAIS identificada (por CNPJ)", "2010–2021"),
    ("br_ibge_munic.meio_ambiente", "IBGE · MUNIC, suplemento Meio Ambiente", "2004–2020"),
    ("br_ibama_embargos_novo.termo_embargo", "IBAMA · áreas embargadas", "base completa"),
    ("br_tce_rj.contratos_municipio", "TCE-RJ · contratos municipais", "até 2025"),
    ("br_cgu_licitacao_contrato.contrato_compra", "CGU · contratos federais", "até 2024"),
    ("br_comprasgov_sicaf.fornecedores", "Compras.gov · SICAF", "cadastro corrente"),
    ("br_tcu_inidoneos.empresas", "TCU · inidôneos e suspensos", "cadastro corrente"),
]


def procedencia(ano, mes, ano_rais):
    """Quando cada base foi espelhada — pra quem lê saber o que está velho."""
    nomes = ",".join(f"'{t}'" for t, _, _ in DATASETS)
    linhas = {r["dataset"] + "." + r["table"]: r for r in duck(f"""
SELECT dataset, "table", scrape_date, rows FROM _rodado_metadata
WHERE dataset || '.' || "table" IN ({nomes});""")}
    ref = f"{mes:02d}/{ano}"
    saida = []
    for tabela, nome, cobertura in DATASETS:
        r = linhas.get(tabela, {})
        saida.append({"tabela": tabela, "nome": nome,
                      "cobertura": cobertura.format(ref=ref, rais=ano_rais),
                      "espelhada": r.get("scrape_date") or "—",
                      "linhas": r.get("rows")})
    return saida


# ── uma folha A4, preto e branco, pra anexar no relatório impresso ──────────
A4 = """<!doctype html>
<html lang="pt-br"><head><meta charset="utf-8"><title>{titulo}</title>
<style>
@page {{ size: A4 portrait; margin: 11mm 12mm 9mm; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; padding: 0; }}
body {{ font: 7.6pt/1.34 "Helvetica Neue", Helvetica, Arial, sans-serif;
  color: #000; background: #fff; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
h1 {{ font-size: 13pt; line-height: 1.1; margin: 0; letter-spacing: -0.2pt; }}
h2 {{ font-size: 7.4pt; text-transform: uppercase; letter-spacing: 0.8pt; margin: 3.6mm 0 1.4mm;
  padding-bottom: 0.6mm; border-bottom: 0.5pt solid #000; }}
.cab {{ display: flex; justify-content: space-between; align-items: flex-end; gap: 6mm;
  border-bottom: 1.4pt solid #000; padding-bottom: 1.8mm; }}
.cab .ref {{ text-align: right; font-size: 6.6pt; line-height: 1.5; color: #333; white-space: nowrap; }}
.linha1 {{ font-size: 6.8pt; color: #333; margin: 0.8mm 0 0; }}
.tot {{ display: flex; gap: 0; margin: 2.6mm 0 0; border: 0.5pt solid #000; }}
.tot div {{ flex: 1; padding: 1.4mm 2mm; border-right: 0.5pt solid #bbb; }}
.tot div:last-child {{ border-right: 0; }}
.tot b {{ display: block; font-size: 11pt; line-height: 1; letter-spacing: -0.3pt; }}
.tot span {{ font-size: 6.2pt; color: #333; }}
table {{ width: 100%; border-collapse: collapse; font-size: 6.9pt; }}
th {{ text-align: left; font-weight: 700; font-size: 6.1pt; text-transform: uppercase;
  letter-spacing: 0.3pt; border-bottom: 0.5pt solid #000; padding: 0.9mm 1.2mm; }}
td {{ padding: 0.85mm 1.2mm; border-bottom: 0.4pt solid #ccc; vertical-align: top; }}
tr:last-child td {{ border-bottom: 0.5pt solid #000; }}
.n {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
th.n {{ text-align: right; }}
td.a {{ font-weight: 700; }}
.cnae {{ font-size: 5.8pt; color: #555; }}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0 6mm; }}
.cols3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 0 5mm; }}
p {{ margin: 0 0 1.3mm; }}
.it {{ font-size: 6.7pt; line-height: 1.4; }}
.it b {{ font-weight: 700; }}
ul {{ margin: 0; padding-left: 3.2mm; font-size: 6.7pt; line-height: 1.4; }}
li {{ margin-bottom: 0.9mm; }}
.rod {{ margin-top: 3mm; padding-top: 1.4mm; border-top: 0.5pt solid #000;
  font-size: 5.9pt; line-height: 1.45; color: #333; }}
.barra {{ display: inline-block; height: 2.4pt; background: #000; vertical-align: middle;
  margin-left: 1.2mm; }}
</style></head><body>
{corpo}
</body></html>
"""


def folha_a4(d):
    m, res = d["meta"], d["resumo"]
    curto = {"1": "Marmorarias", "2": "Metalurgia (CNAE 24)", "2b": "Produtos de metal (CNAE 25)",
             "3": "Torrefação e moagem de café", "4": "Fabricação de produtos químicos",
             "5": "Olaria e artefatos de cerâmica", "6": "Gesso e produtos à base de gesso",
             "7": "Gorduras vegetais e animais", "8": "Extração de minerais não metálicos"}
    ser = {(x["cat"], x["per"]): x["ativas"] for x in d["serie"]}
    pers = sorted({x["per"] for x in d["serie"]})
    ult, pen = pers[-1], pers[-2]
    rais = {r["cat"]: r["vinculos"] for r in d["rais"] if r["ano"] == m["ref_rais"]}
    n = lambda v: f"{v:,}".replace(",", ".")
    maxi = max(r["ativa"] for r in res)

    def var(a, b):
        if a is None or b is None:
            return "—"
        if not a:
            return "0,0%" if not b else "novo"
        return f"{(b - a) / a * 100:+.1f}".replace(".", ",") + "%"

    linhas = "".join(
        f'<tr><td>{r["nome"].split(" — ")[0] if r["id"] not in ("2","2b") else curto[r["id"]]}'
        f'<br><span class="cnae">{" · ".join(c.split(" ")[0] for c in r["cnaes"])}</span></td>'
        f'<td class="n a">{n(r["ativa"])}'
        f'<span class="barra" style="width:{max(1.0, r["ativa"] / maxi * 13):.1f}mm"></span></td>'
        f'<td class="n">{n(r["ativa_p"])}</td><td class="n">{n(r["ativa_s"])}</td>'
        f'<td class="n">{n(r["inapta"] + r["suspensa"])}</td>'
        f'<td class="n">{n(r["baixada"] + r["nula"])}</td>'
        f'<td class="n">{n(rais.get(r["id"], 0))}</td>'
        f'<td class="n">{n(ser.get((r["id"], pen), 0))}</td>'
        f'<td class="n a">{n(ser.get((r["id"], ult), 0))}</td>'
        f'<td class="n">{var(ser.get((r["id"], pen)), ser.get((r["id"], ult)))}</td></tr>'
        for r in res)

    x = m["cruzamentos"]
    fontes = " · ".join(f"{f['nome']} (espelho {f['espelhada'][8:10]}/{f['espelhada'][5:7]}/"
                        f"{f['espelhada'][:4]})" for f in d["fontes"] if f["espelhada"] != "—")

    corpo = f"""
<div class="cab">
  <div>
    <h1>Atividades potencialmente geradoras de poluentes atmosféricos</h1>
    <p class="linha1">Levantamento cadastral semestral — Nova Friburgo/RJ (IBGE {m['id_municipio']})</p>
  </div>
  <div class="ref">Referência do cadastro: <b>{m['ref_label']}</b><br>
    Vínculos: RAIS {m['ref_rais']} · Gerado em {m['gerado'][8:10]}/{m['gerado'][5:7]}/{m['gerado'][:4]}</div>
</div>

<div class="tot">
  <div><b>{n(m['cnpj_ativos'])}</b><span>estabelecimentos ativos nas 8 atividades, sem dupla contagem</span></div>
  <div><b>{round(m['mei_ativos'] / m['cnpj_ativos'] * 100)}%</b><span>são MEI ({n(m['mei_ativos'])} dos {n(m['cnpj_ativos'])}) — fora do licenciamento estadual</span></div>
  <div><b>{n(sum(rais.values()))}</b><span>vínculos formais (RAIS {m['ref_rais']})</span></div>
  <div><b>{n(m['cnpj_total'])}</b><span>CNPJs no histórico, em qualquer situação</span></div>
</div>

<h2>Quadro-resumo por atividade</h2>
<table>
<thead><tr><th>Atividade / subclasses CNAE 2.3</th><th class="n">Ativos</th><th class="n">CNAE<br>princ.</th>
<th class="n">CNAE<br>sec.</th><th class="n">Inaptos</th><th class="n">Baixados</th>
<th class="n">Vínculos</th><th class="n">{pen}</th><th class="n">{ult}</th><th class="n">Δ sem.</th></tr></thead>
<tbody>{linhas}</tbody></table>
<p class="it" style="margin-top:1.2mm;color:#444">Ativos = situação cadastral “Ativa” na Receita Federal, somando CNAE principal e secundário; um CNPJ nunca é contado duas vezes na mesma atividade. A soma das linhas passa de {n(m['cnpj_ativos'])} porque um mesmo CNPJ pode ter atividade em duas categorias. As colunas {pen} e {ult} e o Δ contam apenas CNAE principal, critério reproduzível em qualquer mês da série.</p>

<div class="cols">
<div>
<h2>O que os números mostram</h2>
<ul>
<li><b>A cidade é metal-mecânica, não metalúrgica.</b> {n(ser[('2b', ult)])} estabelecimentos ativos de fabricação de produtos de metal — serralheria, esquadria, usinagem, solda — com {n(rais.get('2b', 0))} empregos formais. Metalurgia no sentido estrito, quem funde metal, são {ser[('2', ult)]}. As empresas com “metalúrgica” no nome estão quase todas em CNAE de serralheria.</li>
<li><b>Uma torrefação de café ativa.</b> As outras ~35 empresas com “café” no nome são cafeterias e lanchonetes.</li>
<li><b>Nenhum fabricante de gesso.</b> A CNAE 2392-3/00 tem zero registros no município; as quatro empresas com “gesso” no nome instalam drywall ou vendem material.</li>
<li><b>Extração mineral estável e esvaziando.</b> {ser[('8', ult)]} ativos, sem variação em sete semestres, mas o emprego caiu de 53 (2018) para {rais.get('8', 0)} ({m['ref_rais']}).</li>
<li><b>Concentração territorial.</b> {n(m['bairros'][0][1])} dos {n(m['cnpj_ativos'])} ativos ({round(m['bairros'][0][1] / m['cnpj_ativos'] * 100)}%) estão em {m['bairros'][0][0].title()}.</li>
</ul>
<h2>Cruzamentos por CNPJ</h2>
<p class="it">Empregados por empresa (RAIS identificada, até 2021): <b>{n(x['com_rais'])}</b> empresas, {n(x['vinculos_rais'])} vínculos somados. Contrato com o poder público (TCE-RJ municipal e CGU federal): <b>{x['com_contrato']}</b> empresas — uma com a prefeitura de Nova Friburgo, duas com Bom Jardim, uma com Quissamã, duas federais. Cadastro de fornecedor SICAF: <b>{x['com_sicaf']}</b>. Embargo ambiental do IBAMA em qualquer município do país: <b>{x['embargos_ibama']}</b>. Inidôneos ou suspensos no TCU: <b>{x['inidoneos_tcu']}</b>. Os dois últimos são resultados conferidos, não campos em branco.</p>
</div>
<div>
<h2>O que não pôde ser confirmado</h2>
<ul>
<li><b>Situação do licenciamento (LP/LI/LO), número do processo e da licença.</b> Não existem em nenhuma base pública consultada. A situação relatada aqui é a <b>situação cadastral na Receita Federal</b>: diz se o CNPJ existe e está ativo, não se a atividade está licenciada. Preencher exige consulta ao INEA e à Secretaria de Meio Ambiente de Nova Friburgo. Nenhum número foi estimado.</li>
<li><b>Órgão responsável</b> — por competência, não por cadastro: INEA/RJ para o que não é de impacto local; o município para o impacto local. O IBGE MUNIC registra que Nova Friburgo assumiu o licenciamento de impacto local (2012 e 2015, com LP, LI e LO concedidas) e tem legislação sobre poluição do ar desde 2009.</li>
<li><b>Quantos dos 12 ativos em 2330-3/99 trabalham gesso</b> — a classe agrega concreto, cimento, fibrocimento e gesso e não permite separar.</li>
<li><b>Empreendimentos sem CNPJ</b> — extração informal de areia e argila, olaria e oficina de fundo de quintal não aparecem em nenhuma base usada.</li>
</ul>
<h2>Comparação entre semestres</h2>
<p class="it">A série usa a foto do cadastro em março (1º semestre) e setembro (2º semestre) de cada ano — {len(pers)} pontos, de {pers[0]} a {ult}. Cada ponto é uma foto, não um acumulado: a comparação entre semestres é direta, mesmo recorte e mesmo critério, seis meses depois. Aumento, redução, entradas, saídas e variação percentual saem da mesma série.</p>
</div>
</div>

<div class="rod">
<b>Fontes.</b> {fontes}. Todas públicas e oficiais, consultadas em espelho local; a data entre parênteses é quando a cópia foi puxada da fonte.<br>
<b>Aviso.</b> Este documento é um inventário cadastral: diz quem existe e o que declara fazer. Não é um cadastro de licenciamento e não substitui consulta ao órgão licenciador. Versão navegável, com a lista completa dos {n(m['cnpj_total'])} CNPJs: rodado.xyz/analises/poluentes-do-ar-em-nova-friburgo/
</div>
"""
    return A4.format(titulo="Poluentes atmosféricos — Nova Friburgo/RJ", corpo=corpo)


CABECA = """<!doctype html>
<html lang="pt-br">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<!-- gerado por scripts/gera_relatorio_nf.py — editar _page.html, não este arquivo -->
<title>{titulo} — rodado</title>
<meta name="description" content="{dek}">
<link rel="stylesheet" href="../../assets/site.css">
<link rel="stylesheet" href="../analises.css">
</head>
<body>

<nav class="site-nav">
  <div class="nav-inner">
    <a class="brand" href="/">rodado</a>
    <div class="nav-right">
      <div class="links">
        <a href="/#temas">Temas</a>
        <a href="/analises/">Análises</a>
        <a href="../../mcp.html">MCP</a>
        <a href="https://xn--2dk.xyz/dataviz/">DataViz Hub</a>
      </div>
      <div class="nav-controls">
        <button id="themeToggle" class="theme-toggle" aria-label="Alternar tema claro/escuro" type="button"><i class="fa-solid fa-moon"></i></button>
      </div>
    </div>
  </div>
</nav>

<main class="wide" style="max-width:none;padding:0">
  <div style="max-width:1180px;margin:0 auto;padding:1.4rem 1.5rem 0">
    <a class="voltar" href="../">&larr; voltar às análises</a>
  </div>
"""

RODAPE = """</main>

<footer>
  <div class="footer-inner">
    <a href="/">Índice temático</a>
    <span>Dados: fontes públicas oficiais / DuckDB</span>
  </div>
</footer>

<script src="../../assets/theme-toggle.js"></script>
</body>
</html>
"""

DEK = ("Levantamento cadastral das oito atividades potencialmente geradoras de emissões "
       "atmosféricas em Nova Friburgo/RJ, com a série semestral para comparar entre "
       "períodos e a lista completa dos empreendimentos.")


def renderiza(dados, artefato=None):
    molde = MOLDE.read_text(encoding="utf-8")
    bruto = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    # o payload vai dentro de <script type="application/json">: só </script> precisa fugir
    corpo = molde.replace("/*DADOS*/", bruto.replace("</", "<\\/"))

    (PASTA / "dados.json").write_text(
        json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")

    titulo = "Poluentes do Ar em Nova Friburgo"
    sem_titulo = corpo.split("</title>", 1)[1]
    (PASTA / "index.html").write_text(
        CABECA.format(titulo=titulo, dek=DEK) + sem_titulo + RODAPE, encoding="utf-8")
    print(f"  {PASTA.relative_to(RAIZ)}/index.html")
    print(f"  {PASTA.relative_to(RAIZ)}/dados.json")
    if artefato:
        Path(artefato).write_text(corpo, encoding="utf-8")
        print(f"  {artefato}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", help="foto do cadastro, AAAA-MM (padrão: partição mais recente)")
    ap.add_argument("--artifact", help="caminho da cópia autocontida pro Artifact")
    ap.add_argument("--offline", help="pula o beelink e usa este dados.json")
    ap.add_argument("--a4", help="caminho do HTML de uma folha A4 (preto e branco) pra virar PDF")
    args = ap.parse_args()

    if args.offline:
        dados = json.loads(Path(args.offline).read_text(encoding="utf-8"))
    else:
        if args.ref:
            ano, mes = (int(x) for x in args.ref.split("-"))
        else:
            ano, mes = ultima_particao()
        print(f"referência: {ano}-{mes:02d}")
        dados = monta(*coleta(ano, mes), ano, mes)
        m = dados["meta"]
        print(f"  {m['cnpj_ativos']} ativos · {m['cnpj_total']} CNPJs · {m['linhas']} linhas")
    renderiza(dados, args.artifact)
    if args.a4:
        Path(args.a4).write_text(folha_a4(dados), encoding="utf-8")
        print(f"  {args.a4}")


if __name__ == "__main__":
    sys.exit(main())
