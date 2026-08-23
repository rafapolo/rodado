#!/usr/bin/env python3
"""Generate `ERD.md` — the mirror's entity-relationship map, in Mermaid.

    python3 scripts/gera_schemas.py   # beelink -> schemas.json
    python3 scripts/gera_erd.py       # schemas.json -> ERD.md

825 tables in one `erDiagram` would render as a hairball nobody can read, so
the model is one level up: **an entity is a dataset**, its attributes are its
tables, and an edge is a join key that reaches a reference hub
(`MUNICIPIO`, `EMPRESA_CNPJ`, `ESCOLA`, …). Every table in `schemas.json`
appears exactly once, including the ones that join to nothing — those get a
standalone entity box and a listing at the end.

Edges come from the same knowledge as `docs/context/join_keys.md`:

    solid  ||--o{   the dataset carries the hub's key verbatim
    dashed ||..o{   it carries the key under another name or format, and needs
                    the normalization expression documented in join_keys.md

Row counts are read from beelink's `_rodado_metadata` (skip with --no-probe).
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "schemas.json"
# Os gerados vivem em `docs/`. Ficavam na raiz, foram movidos, e os geradores
# nao acompanharam — entao toda regeneracao caia na raiz e o `docs/` seguia
# velho. `docs/ERD.md` estava parado em 2026-07-27 por causa disso.
DST_PT = REPO / "docs" / "ERD.md"          # default: pt-BR
DST_EN = REPO / "docs" / "ERD_EN.md"
BEELINK_HOST = "beelink"
BEELINK_DB = "~/rodado/basedosdados.duckdb"
JOIN_KEYS_DOC = "docs/context/join_keys.md"

# ---------------------------------------------------------------------------
# Reference hubs
# ---------------------------------------------------------------------------
# code   short tag shown on each table's attribute line
# direct columns joined verbatim
# dashed columns that mean the same thing but need normalization first

# `br_ibge_munic` and friends are full of columns like
# `conselho_municipal_politica_urbana_paridade` — a survey answer about the
# municipality, not a key to it. Anything matching this is never a bridge.
_NOT_A_MUNICIPALITY_KEY = re.compile(
    r"conselho|fundo|plano|programa|iptu|parceria|servico|creche|ensino|"
    r"unidade_conservacao|arranjo|articulacao|percentual|populacao_|quantidade|"
    r"investimento|despesa|desp_|tx_|pct_|subsetor|subativ|indicador|"
    r"forma_contratacao|data_publicacao|contrato_municipio|conexao|dado_municipal|"
    r"registro_|existencia|size_municipalities|comunicacao", re.I)


# scraped sources that name the municipality something else entirely
_MUNICIPIO_ALIASES = {"MUNIC", "ID_MUNICIP", "territory_id", "territory_name",
                      "city", "Ente"}


def _municipio_bridge(col):
    if col in _MUNICIPIO_ALIASES:
        return True
    if col.startswith("id_municipio"):
        return False        # already a direct key
    return bool(re.search(r"munic|ibge", col, re.I)) and not _NOT_A_MUNICIPALITY_KEY.search(col)


HUBS = {
    "MUNICIPIO": dict(
        code="mun",
        direct=lambda c: c.startswith("id_municipio"),
        dashed=_municipio_bridge,
    ),
    "UF": dict(
        code="uf",
        direct=lambda c: c in ("sigla_uf", "id_uf") or c.startswith("sigla_uf"),
        dashed=lambda c: c.lower() in ("uf", "sg_uf", "ufsigla", "codigo_uf",
                                       "estado", "estadocodigo", "nmestado",
                                       "nome_uf", "sigla", "origem_uf",
                                       "destino_uf", "state", "state_code",
                                       # State of Data survey: every column is
                                       # coded, p1_i_1 holds the bare UF
                                       "p1_i_1"),
    ),
    "SETOR_CENSITARIO": dict(
        code="setor",
        direct=lambda c: c.startswith("id_setor_censitario"),
        dashed=lambda c: False,
    ),
    "CEP": dict(
        code="cep",
        direct=lambda c: c == "cep",
        dashed=lambda c: False,
    ),
    "EMPRESA_CNPJ": dict(
        code="cnpj",
        direct=lambda c: c.startswith("cnpj"),
        # CNPJ_FUNDO, CNPJCPFContratado, nrCnpjCpf… — same key, other spelling
        dashed=lambda c: (not c.startswith("cnpj")
                          and bool(re.search(r"cnpj", c, re.I))) or c == "documento",
    ),
    "PESSOA_CPF": dict(
        code="cpf",
        # cpf_cnpj holds either one: dashed, it needs a length check first
        direct=lambda c: c == "cpf" or (c.startswith("cpf_")
                                        and not c.lower().startswith("cpf_cnpj")),
        dashed=lambda c: (bool(re.search(r"cpf", c, re.I))
                          and not (c == "cpf" or (c.startswith("cpf_")
                                   and not c.lower().startswith("cpf_cnpj")))
                          ) or c.lower() in ("nis", "numero_familia"),
    ),
    "ESCOLA": dict(
        code="escola",
        direct=lambda c: c.startswith("id_escola"),
        dashed=lambda c: False,
    ),
    "IES": dict(
        code="ies",
        direct=lambda c: c == "id_ies",
        dashed=lambda c: c == "cnpj_mantenedora",
    ),
    "CNES": dict(
        code="cnes",
        direct=lambda c: c.startswith("id_estabelecimento_cnes"),
        dashed=lambda c: c in ("codigo_estabelecimento", "id_estabelecimento"),
    ),
    "CNAE": dict(
        code="cnae",
        direct=lambda c: c.startswith("cnae"),
        dashed=lambda c: c in ("codigoCnae", "id_subclasse", "subclasse"),
    ),
    "CBO": dict(
        code="cbo",
        direct=lambda c: c.startswith("cbo_"),
        dashed=lambda c: False,
    ),
    "CID10": dict(
        code="cid",
        direct=lambda c: c.startswith("cid_"),
        # the directories name them plainly (`categoria`) or in caps (`CAT`)
        dashed=lambda c: c in ("subcategoria", "categoria", "CAT"),
    ),
    "NCM_SH": dict(
        code="ncm",
        direct=lambda c: c in ("id_ncm", "id_sh4", "id_sh6", "id_sh2"),
        dashed=lambda c: bool(re.search(r"ncm|_sh[246]\b", c, re.I)) and not c.startswith("id_"),
    ),
    "PAIS": dict(
        code="pais",
        direct=lambda c: c in ("id_pais", "sigla_pais_iso3", "sigla_pais_iso2",
                               "id_pais_m49"),
        dashed=lambda c: c in ("country", "country_code", "pais"),
    ),
    "ORGAO": dict(
        code="orgao",
        direct=lambda c: c.startswith(("id_orgao", "codigo_orgao")),
        dashed=lambda c: c.startswith("nome_orgao"),
    ),
    "UNIDADE_GESTORA": dict(
        code="ug",
        # explicit: `id_unidade` is a unit of measure in comex, `id_unidade_
        # consumo` a POF sampling unit, `id_unidade_conservacao` a park
        direct=lambda c: c.startswith(("id_unidade_gestora", "codigo_unidade_gestora",
                                       "id_unidade_orcamentaria")),
        dashed=lambda c: c.startswith(("nome_unidade_gestora",
                                       "nome_unidade_orcamentaria")),
    ),
    "FUNCAO_PROGRAMA": dict(
        code="funcprog",
        direct=lambda c: c.startswith(("id_funcao", "id_subfuncao", "id_acao",
                                       "id_programa")),
        dashed=lambda c: c.startswith(("nome_funcao", "nome_subfuncao",
                                       "nome_acao", "nome_programa")),
    ),
    "PARTIDO": dict(
        code="partido",
        direct=lambda c: c in ("sigla_partido", "id_partido"),
        dashed=lambda c: c == "partido",
    ),
}

# Datasets where a hub's column name means something else entirely and must
# not become an edge: a Câmara `id_orgao` is a committee, an INEP one is a
# regional education board — neither is the SIAFI organ the CGU tables key on.
HUB_EXCLUDE = {
    "ORGAO": {"br_camara_dados_abertos", "br_inep_censo_escolar"},
}

# Hub relationships, for the overview diagram. Hand-written: these come from
# the directory tables, not from column-name matching.
HUB_MODEL = {
    "pt": """    UF ||--o{ MUNICIPIO : "id_municipio comeca com id_uf"
    MUNICIPIO ||--o{ SETOR_CENSITARIO : "7 primeiros digitos"
    MUNICIPIO ||--o{ CEP : "id_municipio"
    MUNICIPIO ||--o{ ESCOLA : "id_municipio"
    MUNICIPIO ||--o{ IES : "id_municipio"
    MUNICIPIO ||--o{ CNES : "id_municipio_6"
    MUNICIPIO ||--o{ EMPRESA_CNPJ : "id_municipio_rf"
    CEP ||--o{ EMPRESA_CNPJ : "cep"
    EMPRESA_CNPJ ||--o{ PESSOA_CPF : "socios"
    EMPRESA_CNPJ }o--|| CNAE : "cnae_fiscal_principal"
    PESSOA_CPF }o--o{ CBO : "vinculo RAIS/CAGED"
    PESSOA_CPF }o--o{ CID10 : "diagnostico SIH/SIM/SINAN"
    CNES ||--o{ CID10 : "diagnostico"
    PAIS ||--o{ NCM_SH : "comercio exterior"
    PARTIDO }o--o{ MUNICIPIO : "eleicoes, via id_municipio_tse"
    ORGAO ||--o{ UNIDADE_GESTORA : "id_orgao"
    UNIDADE_GESTORA }o--o{ FUNCAO_PROGRAMA : "classificacao do gasto"
""",
    "en": """    UF ||--o{ MUNICIPIO : "id_municipio starts with id_uf"
    MUNICIPIO ||--o{ SETOR_CENSITARIO : "first 7 digits"
    MUNICIPIO ||--o{ CEP : "id_municipio"
    MUNICIPIO ||--o{ ESCOLA : "id_municipio"
    MUNICIPIO ||--o{ IES : "id_municipio"
    MUNICIPIO ||--o{ CNES : "id_municipio_6"
    MUNICIPIO ||--o{ EMPRESA_CNPJ : "id_municipio_rf"
    CEP ||--o{ EMPRESA_CNPJ : "cep"
    EMPRESA_CNPJ ||--o{ PESSOA_CPF : "socios"
    EMPRESA_CNPJ }o--|| CNAE : "cnae_fiscal_principal"
    PESSOA_CPF }o--o{ CBO : "RAIS/CAGED job record"
    PESSOA_CPF }o--o{ CID10 : "SIH/SIM/SINAN diagnosis"
    CNES ||--o{ CID10 : "diagnosis"
    PAIS ||--o{ NCM_SH : "foreign trade"
    PARTIDO }o--o{ MUNICIPIO : "elections, via id_municipio_tse"
    ORGAO ||--o{ UNIDADE_GESTORA : "id_orgao"
    UNIDADE_GESTORA }o--o{ FUNCAO_PROGRAMA : "spending classification"
""",
}

HUB_KEYS_TABLE = [
    ("MUNICIPIO", "`br_bd_diretorios_brasil.municipio`",
     "`id_municipio` (7)",
     dict(pt="5.571 municípios; carrega também `id_municipio_6/_tse/_rf/_bcb`",
          en="5.571 municipalities; also carries `id_municipio_6/_tse/_rf/_bcb`")),
    ("UF", "`br_bd_diretorios_brasil.uf`", "`sigla_uf` / `id_uf`",
     dict(pt="27 unidades da federação", en="27 states")),
    ("SETOR_CENSITARIO", "`br_bd_diretorios_brasil.setor_censitario_2022`",
     "`id_setor_censitario` (15)",
     dict(pt="as malhas de 2010 e 2022 não são compatíveis",
          en="the 2010 and 2022 meshes are not compatible")),
    ("CEP", "`br_bd_diretorios_brasil.cep`", "`cep` (8)",
     dict(pt="905 mil CEPs — a única tabela de diretório sem duplicação",
          en="905k postal codes — the only directory table that is not duplicated")),
    ("EMPRESA_CNPJ", "`br_me_cnpj.estabelecimentos` / `.empresas`",
     "`cnpj` (14) / `cnpj_basico` (8)",
     dict(pt="43 snapshots mensais — fixe `ano`/`mes`",
          en="43 monthly snapshots — pin `ano`/`mes`")),
    ("PESSOA_CPF", "—", "`cpf` (11)",
     dict(pt="sem diretório; quase sempre mascarado",
          en="no directory; almost always masked")),
    ("ESCOLA", "`br_bd_diretorios_brasil.escola`", "`id_escola`",
     dict(pt="218 mil escolas", en="218k schools")),
    ("IES", "`br_bd_diretorios_brasil.instituicao_ensino_superior`", "`id_ies`",
     dict(pt="", en="")),
    ("CNES", "`br_ms_cnes.estabelecimento`", "`id_estabelecimento_cnes`",
     dict(pt="snapshots mensais; chaveado por `id_municipio_6`",
          en="monthly snapshots; keyed on `id_municipio_6`")),
    ("CNAE", "`br_bd_diretorios_brasil.cnae_2`", "`subclasse` (7)",
     dict(pt="", en="")),
    ("CBO", "`br_bd_diretorios_brasil.cbo_2002`", "`cbo_2002`", dict(pt="", en="")),
    ("CID10", "`br_bd_diretorios_brasil.cid_10`", "`categoria` / `subcategoria`",
     dict(pt="", en="")),
    ("NCM_SH", "`br_bd_diretorios_mundo.nomenclatura_comum_mercosul`",
     "`id_ncm`, `id_sh4`", dict(pt="", en="")),
    ("PAIS", "`br_bd_diretorios_mundo.pais`", "`sigla_pais_iso3`, `id_pais`",
     dict(pt="", en="")),
    ("ORGAO", "`br_cgu_licitacao_contrato.licitacao`", "`id_orgao`",
     dict(pt="órgão do SIAFI; `id_orgao_superior` é o nível acima. O `id_orgao` "
             "da Câmara é outra numeração (comissões) e não entra aqui",
          en="SIAFI organ; `id_orgao_superior` is the level above. The Câmara's "
             "`id_orgao` is a different numbering (committees) and is excluded")),
    ("UNIDADE_GESTORA", "`br_cgu_licitacao_contrato.licitacao`",
     "`id_unidade_gestora`",
     dict(pt="UG — o nível a que o gasto é efetivamente atribuído",
          en="the level spending is actually attributed to")),
    ("FUNCAO_PROGRAMA", "`br_cgu_orcamento_publico.orcamento`",
     "`id_funcao`, `id_subfuncao`, `id_acao`, `id_programa`",
     dict(pt="classificação funcional-programática do orçamento federal",
          en="functional/programmatic classification of the federal budget")),
    ("PARTIDO", "`br_tse_eleicoes.partidos`", "`sigla_partido`",
     dict(pt="siglas mudam entre eleições",
          en="abbreviations change between elections")),
]

# ---------------------------------------------------------------------------
# Domains — ordered rules, first match wins
# ---------------------------------------------------------------------------

DOMAIN_RULES = [
    (r"^br_bd_|^br_datasus_cid10|^br_ibge_cbo_2002|^br_brasilapi|^br_ibge_amc",
     "referencia"),
    (r"^br_ms_|^br_ans_|^br_anvisa_|^br_saude_|^br_ieps_", "saude"),
    (r"^br_inep_|^br_mec_|^br_capes_|^br_cnpq_|^br_simet_|^world_iea_|^world_oecd_pisa",
     "educacao"),
    (r"^br_tse_|^br_camara_|^br_senado_|^br_poder360_|^br_cgu_emendas", "politica"),
    (r"^br_cnj_|^br_stf_|^br_stj_|^br_mjsp_|^br_mj_|^br_pgfn_|^br_fbsp_|"
     r"^br_rj_isp_|^br_ipea_atlasviolencia|^br_ggb_|^br_tcu_inidoneos|"
     r"^br_bcb_penalidades|_sanctions$|^global_opensanctions|^global_icij_",
     "justica"),
    (r"^br_cgu_|^br_comprasgov_|^br_transferegov|^br_siop_|^br_tesouro_|^br_tcu_|"
     r"^br_tce_|^br_me_siconfi|^br_me_siape|^br_me_siorg|^br_mp_pep|^br_ok_|"
     r"^br_ba_feiradesantana|^br_me_estoque_divida",
     "governo"),
    (r"^br_me_|^br_rf_|^br_bcb_|^br_cvm_|^br_fipe_|^br_fgv_|^br_bndes_|"
     r"^br_brasilio_|^br_anp_|^br_mme_|^br_caixa_|^br_trase_|^br_ibge_ip|"
     r"^br_ibge_inpc|^br_ibge_pam|^br_ibge_pevs|^br_ibge_ppm|^br_ibge_pib|"
     r"^br_clp_|^br_firjan_|^br_mc_indicadores|^br_datahackers_",
     "economia"),
    (r"^br_ana_|^br_inpe_|^br_mapbiomas_|^br_sfb_|^br_ibama_|^br_seeg_|^br_mma_|"
     r"^br_mdr_|^br_inmet_|^br_geobr_|^world_wwf_|^global_ibge_tabua|^br_anatel_|"
     r"^br_anac_|^br_mobilidados_|^br_ipea_acesso",
     "territorio"),
    (r"^br_ibge_|^br_abrinq_|^br_ipea_|^br_ce_|^br_mg_|^br_sp_", "demografia"),
    (r"^world_|^us_|^mundo_|^global_", "internacional"),
]
DOMAIN_ORDER = ["referencia", "saude", "educacao", "economia", "governo",
                "politica", "justica", "territorio", "demografia",
                "internacional", "outros"]
DOMAIN_NAMES = {
    "referencia": dict(pt="Diretórios e tabelas de referência",
                       en="Directories and reference tables"),
    "saude": dict(pt="Saúde", en="Health"),
    "educacao": dict(pt="Educação e ciência", en="Education and science"),
    "economia": dict(pt="Trabalho, empresas e economia",
                     en="Labour, companies and the economy"),
    "governo": dict(pt="Governo, orçamento e compras",
                    en="Government, budget and procurement"),
    "politica": dict(pt="Política e eleições", en="Politics and elections"),
    "justica": dict(pt="Justiça, segurança e sanções",
                    en="Justice, security and sanctions"),
    "territorio": dict(pt="Território, ambiente e infraestrutura",
                       en="Territory, environment and infrastructure"),
    "demografia": dict(pt="Demografia e indicadores sociais",
                       en="Demographics and social indicators"),
    "internacional": dict(pt="Internacional, cultura e esporte",
                          en="International, culture and sport"),
    "outros": dict(pt="Outros", en="Other"),
}

TEMPORAL = {"ano", "mes", "data", "trimestre", "semestre", "year", "date"}


def domain_of(dataset):
    for pattern, name in DOMAIN_RULES:
        if re.search(pattern, dataset):
            return name
    return "outros"


# ---------------------------------------------------------------------------

def load_schema():
    if not SRC.exists():
        sys.exit(f"{SRC} not found — run scripts/gera_schemas.py first.")
    return json.loads(SRC.read_text(encoding="utf-8"))["tables"]


def probe_row_counts():
    sql = ('SET enable_progress_bar=false; '
           'SELECT dataset, "table" AS tbl, rows FROM _rodado_metadata')
    cmd = ["ssh", BEELINK_HOST, f"~/bin/duckdb -json -readonly {BEELINK_DB} -c {sql!r}"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        text = re.sub(r"\x1b\[[0-9;]*m", "", out.stdout)
        rows = json.loads(text[text.index("["):])
    except Exception as exc:                                  # noqa: BLE001
        print(f"  ! row-count probe failed: {exc}", file=sys.stderr)
        return {}
    return {f"{r['dataset']}.{r['tbl']}": r["rows"] for r in rows
            if r["rows"] is not None}


def human(n):
    if n is None:
        return ""
    for limit, suffix in ((1e9, "B"), (1e6, "M"), (1e3, "k")):
        if n >= limit:
            value = n / limit
            return f"{value:.1f}{suffix}".replace(".0", "")
    return str(n)


# the column an edge is labelled with when the dataset has several for the
# same hub (`id_municipio_residencia`, `_ocorrencia`, `_mae`, …)
CANONICAL = {
    "MUNICIPIO": "id_municipio", "UF": "sigla_uf",
    "SETOR_CENSITARIO": "id_setor_censitario", "CEP": "cep",
    "EMPRESA_CNPJ": "cnpj", "PESSOA_CPF": "cpf", "ESCOLA": "id_escola",
    "IES": "id_ies", "CNES": "id_estabelecimento_cnes",
    "CNAE": "cnae_2_subclasse", "CBO": "cbo_2002",
    "CID10": "cid_principal_categoria", "NCM_SH": "id_ncm",
    "PAIS": "sigla_pais_iso3", "PARTIDO": "sigla_partido",
    "ORGAO": "id_orgao", "UNIDADE_GESTORA": "id_unidade_gestora",
    "FUNCAO_PROGRAMA": "id_funcao",
}


def edge_label(hub, columns):
    """`id_municipio` when it is there, else the shortest variant + a count."""
    columns = sorted(set(columns))
    canonical = CANONICAL.get(hub)
    pick = canonical if canonical in columns else min(columns, key=lambda c: (len(c), c))
    extra = len(columns) - 1
    return f"{pick} +{extra}" if extra else pick


def analyze(tables):
    """dataset -> {tables: {name: {codes}}, hubs: {hub: (label, dashed)}}"""
    info = defaultdict(lambda: {"tables": {}, "hubs": {},
                                "hub_cols": defaultdict(set)})
    for tid, meta in sorted(tables.items()):
        dataset, _, table = tid.partition(".")
        cols = [c["name"] for c in meta.get("columns", [])]
        codes = []
        for hub, spec in HUBS.items():
            if dataset in HUB_EXCLUDE.get(hub, ()):
                continue
            direct = [c for c in cols if spec["direct"](c)]
            dashed = [c for c in cols if not spec["direct"](c) and spec["dashed"](c)]
            if not direct and not dashed:
                continue
            codes.append(spec["code"])
            entry = info[dataset]
            # a solid edge always wins over a dashed one
            was_dashed = entry["hubs"].get(hub, (None, True))[1]
            if direct:
                if was_dashed:
                    entry["hub_cols"][hub] = set()
                entry["hub_cols"][hub].update(direct)
                entry["hubs"][hub] = (None, False)
            elif was_dashed:
                entry["hub_cols"][hub].update(dashed)
                entry["hubs"][hub] = (None, True)
        lowered = {c.lower() for c in cols}
        codes += sorted({"ano" for c in lowered if c.startswith("ano")}
                        | {"mes" for c in lowered if c.startswith("mes")})
        info[dataset]["tables"][table] = {"codes": codes, "cols": len(cols)}

    for dataset, entry in info.items():
        for hub, (_, dashed) in entry["hubs"].items():
            entry["hubs"][hub] = (edge_label(hub, entry["hub_cols"][hub]), dashed)
    return info


# ---------------------------------------------------------------------------
# Prose, per language. ERD.md is pt-BR (the default); ERD_EN.md is English.
# Only prose is translated — column names, table names and the mermaid
# structure are identical in both files.
# ---------------------------------------------------------------------------

T = {
    "pt": dict(
        no_key="sem_chave", rows="linhas", empty="vazia",
        title="ERD — como o espelho se conecta",
        other_lang="🇬🇧 [English version](ERD_EN.md)",
        intro="Mapa de entidades e relações das {tables} tabelas ({datasets} "
              "datasets) do espelho. Gerado por `scripts/gera_erd.py` a partir "
              "de `schemas.json` em {date} — não edite à mão, regenere.",
        pointer="As expressões de join, o formato de cada chave e as pegadinhas "
                "estão em [`{doc}`]({doc}). Este arquivo é o mapa; aquele é o "
                "manual.",
        how_to_read="Como ler",
        how_intro="Um único `erDiagram` com {tables} tabelas seria ilegível, "
                  "então o modelo sobe um nível:",
        how_bullets=[
            "- **entidade = dataset**; **atributo = uma das tabelas** dele;",
            "- o *tipo* do atributo lista as chaves que aquela tabela carrega "
            "(`mun`, `uf`, `cnpj`, `cnes`, `escola`, `setor`, `cep`, `cpf`, "
            "`cnae`, `cbo`, `cid`, `ncm`, `pais`, `partido`, `orgao`, `ug`, "
            "`funcprog`, `ano`, `mes`), ou "
            "`sem_chave` quando não há nenhuma;",
            "- o comentário é a contagem de linhas do `_rodado_metadata`;",
            "- **aresta = chave de join** que chega a um hub de referência:",
        ],
        col_edge="aresta", col_meaning="significado",
        edge_solid="(sólida) a chave está lá com o nome canônico — join direto",
        edge_dashed="(tracejada) a chave está lá com outro nome ou formato — "
                    "normalize antes, receita em [`{doc}`]({doc})",
        loose="Dataset sem nenhuma aresta aparece como caixa solta no diagrama "
              "do seu domínio: está no espelho, mas nada documentado o liga a "
              "mais nada.",
        hubs_title="Os hubs",
        col_ref_table="tabela de referência", col_key="chave", col_note="observação",
        temporal_note="`ano`/`mes`/`data` são a dimensão temporal de quase toda "
                      "tabela — ficam como atributo, nunca como aresta, senão o "
                      "diagrama vira um novelo.",
        coverage="Cobertura",
        col_domain="domínio", col_tables="tabelas", col_connected="conectados",
        orphan_summary="{datasets} datasets não têm chave documentada alguma; "
                       "{tables} tabelas individuais não carregam chave nenhuma "
                       "(ambas as listas no fim).",
        no_link="Sem ligação documentada",
        orphan_ds_note="Nenhuma coluna reconhecida como chave de nenhum hub. "
                       "Alguns são séries nacionais sem recorte geográfico ou de "
                       "entidade (índices de preço, cotações, agregados "
                       "nacionais); o resto são fontes raspadas cujo "
                       "identificador ainda não foi mapeado — esses são os "
                       "candidatos às próximas pontes no `join_keys.md`.",
        orphan_tbl_note="Tabelas que não carregam chave alguma, inclusive dentro "
                        "de datasets que se conectam pelas outras tabelas "
                        "(dicionários, agregados nacionais, metadados):",
    ),
    "en": dict(
        no_key="no_key", rows="rows", empty="empty",
        title="ERD — how the mirror fits together",
        other_lang="🇧🇷 [Versão em português](ERD.md)",
        intro="Entity/relationship map of the {tables} tables ({datasets} "
              "datasets) in the mirror. Generated by `scripts/gera_erd.py` from "
              "`schemas.json` on {date} — do not edit by hand, regenerate.",
        pointer="The join expressions, the format of each key and the traps are "
                "in [`{doc}`]({doc}). This file is the map; that one is the "
                "manual.",
        how_to_read="How to read it",
        how_intro="One `erDiagram` with {tables} tables would be unreadable, so "
                  "the model sits one level up:",
        how_bullets=[
            "- **entity = dataset**; **attribute = one of its tables**;",
            "- the attribute *type* lists the keys that table carries (`mun`, "
            "`uf`, `cnpj`, `cnes`, `escola`, `setor`, `cep`, `cpf`, `cnae`, "
            "`cbo`, `cid`, `ncm`, `pais`, `partido`, `orgao`, `ug`, `funcprog`, "
            "`ano`, `mes`), or `no_key` "
            "when it has none;",
            "- the comment is the row count from `_rodado_metadata`;",
            "- **edge = a join key** reaching a reference hub:",
        ],
        col_edge="edge", col_meaning="meaning",
        edge_solid="(solid) the key is there under its canonical name — direct join",
        edge_dashed="(dashed) the key is there under another name or format — "
                    "normalize first, recipe in [`{doc}`]({doc})",
        loose="A dataset with no edge at all is drawn as a loose box in its "
              "domain diagram: it is in the mirror, but nothing documented links "
              "it to anything else.",
        hubs_title="The hubs",
        col_ref_table="reference table", col_key="key", col_note="note",
        temporal_note="`ano`/`mes`/`data` are the temporal dimension of nearly "
                      "every table — they stay attributes, never edges, or the "
                      "diagram turns into a hairball.",
        coverage="Coverage",
        col_domain="domain", col_tables="tables", col_connected="connected",
        orphan_summary="{datasets} datasets have no documented key at all; "
                       "{tables} individual tables carry no key (both listed at "
                       "the end).",
        no_link="No documented link",
        orphan_ds_note="Not one column recognized as a key to any hub. Some are "
                       "national series with no geographic or entity breakdown "
                       "(price indices, exchange rates, national aggregates); "
                       "the rest are scraped sources whose identifier has not "
                       "been mapped yet — those are the candidates for the next "
                       "bridges in `join_keys.md`.",
        orphan_tbl_note="Tables carrying no key at all, including ones inside "
                        "datasets that do connect through their other tables "
                        "(dictionaries, national aggregates, metadata):",
    ),
}


def mermaid_block(datasets, info, rows, lang):
    """One erDiagram: the hubs these datasets touch, plus the datasets."""
    t = T[lang]
    out = ["```mermaid", "erDiagram"]
    for ds in datasets:
        for hub, (col, dashed) in sorted(info[ds]["hubs"].items()):
            link = "||..o{" if dashed else "||--o{"
            out.append(f'    {hub} {link} {ds} : "{col}"')
    for ds in datasets:
        out.append(f"    {ds} {{")
        for table, meta in info[ds]["tables"].items():
            codes = "_".join(meta["codes"]) if meta["codes"] else t["no_key"]
            n = rows.get(f"{ds}.{table}")
            if n:
                comment = f' "{human(n)} {t["rows"]}"'
            elif n == 0:
                comment = f' "{t["empty"]}"'
            else:
                comment = ""
            out.append(f"        {codes} {table}{comment}")
        out.append("    }")
    out.append("```")
    return out


def render(tables, info, rows, lang):
    t = T[lang]
    total_tables = len(tables)
    by_domain = defaultdict(list)
    for ds in sorted(info):
        by_domain[domain_of(ds)].append(ds)

    connected = [ds for ds in info if info[ds]["hubs"]]
    orphan_ds = sorted(ds for ds in info if not info[ds]["hubs"])
    orphan_tbl = sorted(f"{ds}.{tbl}" for ds in info
                        for tbl, m in info[ds]["tables"].items() if not m["codes"])

    L = [f"# {t['title']}", "", t["other_lang"], "",
         t["intro"].format(tables=total_tables, datasets=len(info),
                           date=date.today().isoformat()), "",
         t["pointer"].format(doc=JOIN_KEYS_DOC), "",
         f"## {t['how_to_read']}", "",
         t["how_intro"].format(tables=total_tables), "",
         *t["how_bullets"], "",
         f"| {t['col_edge']} | {t['col_meaning']} |", "|---|---|",
         f"| `HUB \\|\\|--o{{ dataset` | {t['edge_solid']} |",
         f"| `HUB \\|\\|..o{{ dataset` | " + t["edge_dashed"].format(doc=JOIN_KEYS_DOC) + " |",
         "", t["loose"], "",
         f"## {t['hubs_title']}", "",
         f"| hub | {t['col_ref_table']} | {t['col_key']} | {t['col_note']} |",
         "|---|---|---|---|"]
    for hub, ref, key, note in HUB_KEYS_TABLE:
        L.append(f"| `{hub}` | {ref} | {key} | {note[lang]} |")
    L += ["", "```mermaid", "erDiagram", HUB_MODEL[lang].rstrip(), "```", "",
          t["temporal_note"], "", "---", "",
          f"## {t['coverage']}", "",
          f"| {t['col_domain']} | datasets | {t['col_tables']} | {t['col_connected']} |",
          "|---|---|---|---|"]
    for dom in DOMAIN_ORDER:
        dss = by_domain.get(dom, [])
        if not dss:
            continue
        n_tbl = sum(len(info[d]["tables"]) for d in dss)
        n_conn = sum(1 for d in dss if info[d]["hubs"])
        L.append(f"| {DOMAIN_NAMES[dom][lang]} | {len(dss)} | {n_tbl} | {n_conn} |")
    L += [f"| **total** | **{len(info)}** | **{total_tables}** | **{len(connected)}** |",
          "",
          t["orphan_summary"].format(datasets=len(orphan_ds), tables=len(orphan_tbl)),
          "", "---", ""]

    for dom in DOMAIN_ORDER:
        dss = by_domain.get(dom, [])
        if not dss:
            continue
        n_tbl = sum(len(info[d]["tables"]) for d in dss)
        L += [f"## {DOMAIN_NAMES[dom][lang]}", "",
              f"{len(dss)} datasets · {n_tbl} {t['col_tables']}", ""]
        # split oversized domains so no single diagram gets unreadable
        chunk, chunks, size = [], [], 0
        for ds in dss:
            n = len(info[ds]["tables"])
            if chunk and size + n > 60:
                chunks.append(chunk)
                chunk, size = [], 0
            chunk.append(ds)
            size += n
        if chunk:
            chunks.append(chunk)
        for i, part in enumerate(chunks):
            if len(chunks) > 1:
                L += [f"**{i + 1}/{len(chunks)}**", ""]
            L += mermaid_block(part, info, rows, lang)
            L.append("")

    L += ["---", "", f"## {t['no_link']}", "",
          f"### Datasets ({len(orphan_ds)})", "", t["orphan_ds_note"], ""]
    for ds in orphan_ds:
        tbls = ", ".join(f"`{tbl}`" for tbl in info[ds]["tables"])
        L.append(f"- `{ds}` — {tbls}")
    L += ["", f"### {t['col_tables'].capitalize()} ({len(orphan_tbl)})", "",
          t["orphan_tbl_note"], "",
          ", ".join(f"`{x}`" for x in orphan_tbl), ""]
    return "\n".join(L).rstrip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-probe", action="store_true",
                    help="skip the ssh probe for row counts")
    args = ap.parse_args()

    tables = load_schema()
    info = analyze(tables)
    rows = {} if args.no_probe else probe_row_counts()

    for lang, path in ((("pt"), DST_PT), (("en"), DST_EN)):
        path.write_text(render(tables, info, rows, lang), encoding="utf-8")
        diagrams = path.read_text().count("```mermaid")
        print(f"{path.relative_to(REPO)}  ({lang}) — {diagrams} diagrams, "
              f"{path.stat().st_size / 1024:.1f} KB")
    print(f"  datasets  : {len(info)}")
    print(f"  tables    : {len(tables)}")
    print(f"  row counts: {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
