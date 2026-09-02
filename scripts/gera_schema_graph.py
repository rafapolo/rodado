#!/usr/bin/env python3
"""Build `docs/context/schema_graph.json` — the data behind the schema map.

    python3 scripts/gera_schemas.py       # beelink   -> schemas.json
    python3 scripts/build_metadata_catalog.py         # -> catalog.parquet
    python3 scripts/gera_schema_graph.py  # both      -> pages/atlas/schema_graph.json
    python3 scripts/build_atlas.py        # graph+page -> pages/atlas/index.html

The mirror has no foreign keys — it is parquet. What connects it is columns
that mean the same thing in more than one table, which `gera_join_keys.py`
already works out (curated hub keys, auto-detected shared identifiers, and the
bridges for sources that spell a key differently). This script reuses that
selection and emits it as a graph instead of a document.

The graph is bipartite on purpose: table -> key, never table -> table. Joining
every pair of tables that share a key is 89.598 edges and reads as a hairball;
routing through the key is 1.108 and says which key does the joining.

Everything is index-based (`ds`, `k` are offsets into `datasets` / `keys`) so
the file stays small enough to inline into a single self-contained page.
"""

import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gera_join_keys import (  # noqa: E402
    CONCEPT_ALIASES,
    CURATED,
    TYPE_MAP,
    index_columns,
    select_join_columns,
)
from gera_erd import TEMPORAL  # noqa: E402

SCHEMAS = REPO_ROOT / "schemas.json"
CATALOG = REPO_ROOT / "_rodado_metadata" / "catalog.parquet"
# The graph is viz data, not LLM context — it lives beside the page that
# serves it, so there is exactly one copy of a 630 KB file in the repo.
OUTPUT = REPO_ROOT / "pages" / "atlas" / "schema_graph.json"

# Columns kept per table. The key columns are always emitted; this caps the
# rest, because br_mjsp_sisdepen.populacao_carceraria alone has 3.957 of them
# and no card is ever going to show that many.
MAX_COLS = 60

# Which hub a key belongs to. CURATED carries `cat` for its own columns; the
# auto-detected long tail is mostly a hub key wearing a role suffix, so resolve
# it by prefix the same way gera_join_keys.auto_desc() describes it.
PREFIX_CAT = [
    ("id_municipio", "municipio"), ("nome_municipio", "municipio"),
    ("id_uf", "uf"), ("sigla_uf", "uf"), ("nome_uf", "uf"),
    ("cnpj", "empresa"), ("cpf_cnpj", "empresa"), ("razao_social", "empresa"),
    ("cpf", "pessoa"), ("nome_", "pessoa"),
    ("cnae", "classificacao"), ("cid_", "classificacao"), ("cbo", "classificacao"),
    ("id_escola", "educacao"), ("id_curso", "educacao"), ("id_aluno", "educacao"),
    ("id_estabelecimento_cnes", "saude"), ("id_profissional", "saude"),
    ("id_orgao", "governo"), ("id_unidade_gestora", "governo"),
    ("id_candidato", "politica"), ("id_deputado", "politica"),
    ("id_setor_censitario", "geo"), ("id_distrito", "geo"), ("cep", "geo"),
    ("id_regiao", "geo"), ("id_mesorregiao", "geo"), ("id_microrregiao", "geo"),
]

CAT_NAMES = {
    "municipio": "Município", "uf": "UF", "geo": "Outra geografia",
    "tempo": "Tempo", "empresa": "Empresa (CNPJ)", "pessoa": "Pessoa (CPF)",
    "educacao": "Educação", "saude": "Saúde", "governo": "Governo",
    "politica": "Política", "classificacao": "Classificação",
    "outros": "Outras colunas compartilhadas",
}


def cat_of(col: str, hub: dict[str, str] | None = None) -> str:
    if col in CURATED:
        return CURATED[col].get("cat", "outros")
    if col in TEMPORAL or col.startswith(("ano_", "mes_", "data_")):
        return "tempo"
    for prefix, cat in PREFIX_CAT:
        if col.startswith(prefix):
            return cat
    # PREFIX_CAT only matches at the start, so the role variants that read
    # backwards (`destino_uf`, `uf_devedor`, `pais_infeccao`) fell through to
    # "outros" and lost their colour. The hub they resolve to already carries a
    # category — bridges.yaml and PREFIX_CAT share the id namespace.
    hub_of = (hub or {}).get(col)
    if hub_of:
        return CURATED.get(hub_of, {}).get("cat", "outros")
    return "outros"


# ---------------------------------------------------------------------------
# Atlas themes — a classification of its own, used only by this script.
#
# docs/ERD.md keeps gera_erd.py's ten prefix-matched domains (referencia,
# saude, educacao, economia, governo, politica, justica, territorio,
# demografia, internacional, outros): coarse buckets good enough for a
# document skimmed top to bottom. The atlas is browsed, not read start to
# end, so it earns a finer split — twelve subject themes plus an "outros"
# catch-all, assigned per dataset by what it actually contains rather than
# by name prefix, because a handful of prefixes (br_ibge_*, br_cgu_*, br_me_*,
# world_*...) span several of these themes on their own.
# Biggest theme first, "outros" always last — same convention _page.html's
# THEMES array follows for its legend order and hue-slot assignment.
ATLAS_THEME_ORDER = [
    "governo", "economia", "educacao", "seguranca", "saude", "meio_ambiente",
    "infraestrutura", "politica", "populacao", "territorio", "ciencia_tec",
    "cultura_arte", "outros",
]
ATLAS_THEME_NAMES = {
    "governo": "Governo e Finanças Públicas",
    "economia": "Economia",
    "educacao": "Educação",
    "seguranca": "Segurança, Crime, Violência e Conflito",
    "saude": "Saúde",
    "meio_ambiente": "Meio Ambiente",
    "infraestrutura": "Infraestrutura e Transportes",
    "politica": "Política",
    "populacao": "População",
    "territorio": "Organização Territorial",
    "ciencia_tec": "Ciência, Tecnologia e Inovação",
    "cultura_arte": "Cultura e Arte",
    "outros": "Outros",
}

# One entry per dataset (schemas.json has 199, 2026-08-26) — hand-classified,
# not prefix-matched, because e.g. br_ibge_* alone spans economia (pib, ipca,
# caged-adjacent surveys), populacao (censo, estimativas), governo (munic,
# estadic) and territorio (amc). A dataset absent here falls back to "outros"
# with a stderr warning at build time, so a new dataset is never silently
# miscategorized — it just needs a line added below.
ATLAS_DATASET_THEME = {
    "_obsoleto": "outros",
    "br_abrinq_oca": "educacao",
    "br_ana_atlas_esgotos": "infraestrutura",
    "br_ana_bho": "meio_ambiente",
    "br_ana_outorgas": "meio_ambiente",
    "br_ana_reservatorios": "meio_ambiente",
    "br_ana_telemetria": "meio_ambiente",
    "br_anac_dadosabertos": "infraestrutura",
    "br_anatel_banda_larga_fixa": "infraestrutura",
    "br_anatel_indice_brasileiro_conectividade": "infraestrutura",
    "br_anm": "meio_ambiente",
    "br_anp_combustiveis": "economia",
    "br_anp_precos_combustiveis": "economia",
    "br_ans_beneficiario": "saude",
    "br_anvisa_cmed": "saude",
    "br_anvisa_consultas": "saude",
    "br_anvisa_medicamentos_industrializados": "saude",
    "br_ba_feiradesantana_camara_leis": "politica",
    "br_bcb_desenrola": "economia",
    "br_bcb_estban": "economia",
    "br_bcb_ifdata": "economia",
    "br_bcb_penalidades": "seguranca",
    "br_bcb_scrdata": "economia",
    "br_bcb_sgs": "economia",
    "br_bcb_sicor": "economia",
    "br_bd_diretorios_brasil": "territorio",
    "br_bd_diretorios_data_tempo": "outros",
    "br_bd_diretorios_mundo": "territorio",
    "br_bd_diretorios_us": "territorio",
    "br_bd_metadados": "outros",
    "br_bd_vizinhanca": "territorio",
    "br_bndes_operacoes_contratadas": "economia",
    "br_brasilapi": "outros",
    "br_brasilio_holdings": "economia",
    "br_caixa_sinapi": "infraestrutura",
    "br_caixa_sorteios": "outros",
    "br_camara_dados_abertos": "politica",
    "br_capes_bolsas": "ciencia_tec",
    "br_ce_fortaleza_sefin_iptu": "governo",
    "br_cgu_beneficios_cidadao": "governo",
    "br_cgu_cartao_pagamento": "governo",
    "br_cgu_dados_abertos": "governo",
    "br_cgu_ebt": "governo",
    "br_cgu_emendas_parlamentares": "governo",
    "br_cgu_fef": "governo",
    "br_cgu_garantia_safra": "governo",
    "br_cgu_gas_do_povo": "governo",
    "br_cgu_licitacao_contrato": "governo",
    "br_cgu_novo_bolsa_familia": "governo",
    "br_cgu_orcamento_publico": "governo",
    "br_cgu_pe_de_meia": "educacao",
    "br_cgu_pessoal_executivo_federal": "governo",
    "br_cgu_receitas_publicas": "governo",
    "br_cgu_sancoes": "seguranca",
    "br_cgu_seguro_defeso": "governo",
    "br_cgu_servidores_executivo_federal": "governo",
    "br_cgu_viagens": "governo",
    "br_clp_ranking_competitividade": "economia",
    "br_cnj_estatisticas_poder_judiciario": "seguranca",
    "br_cnj_improbidade_administrativa": "seguranca",
    "br_cnpq_bolsas": "ciencia_tec",
    "br_comprasgov_catmatcatser": "governo",
    "br_comprasgov_sicaf": "governo",
    "br_cvm_administradores_carteira": "economia",
    "br_cvm_fundos": "economia",
    "br_cvm_oferta_publica_distribuicao": "economia",
    "br_datahackers_state_data": "ciencia_tec",
    "br_datasus_cid10": "saude",
    "br_fbsp_absp": "seguranca",
    "br_fgv_igp": "economia",
    "br_fipe_veiculos": "economia",
    "br_firjan_ifgf": "governo",
    "br_geobr_mapas": "territorio",
    "br_ggb_relatorio_lgbtqi": "seguranca",
    "br_ibama_autos": "meio_ambiente",
    "br_ibama_ctf": "meio_ambiente",
    "br_ibama_embargos": "meio_ambiente",
    "br_ibama_embargos_novo": "meio_ambiente",
    "br_ibge_amc": "territorio",
    "br_ibge_cbo_2002": "economia",
    "br_ibge_censo2022_raca": "populacao",
    "br_ibge_censo2022_religiao": "populacao",
    "br_ibge_censo_2022": "populacao",
    "br_ibge_censo_demografico": "populacao",
    "br_ibge_cnefe": "territorio",
    "br_ibge_estadic": "governo",
    "br_ibge_inpc": "economia",
    "br_ibge_ipca": "economia",
    "br_ibge_ipca15": "economia",
    "br_ibge_ipp": "economia",
    "br_ibge_munic": "governo",
    "br_ibge_nomes_brasil": "populacao",
    "br_ibge_pam": "economia",
    "br_ibge_pevs": "economia",
    "br_ibge_pib": "economia",
    "br_ibge_pnad": "economia",
    "br_ibge_pnad_covid": "saude",
    "br_ibge_pnadc": "economia",
    "br_ibge_pof": "economia",
    "br_ibge_populacao": "populacao",
    "br_ibge_ppm": "economia",
    "br_ieps_saude": "saude",
    "br_inea_boletim": "meio_ambiente",
    "br_inep_ana": "educacao",
    "br_inep_avaliacao_alfabetizacao": "educacao",
    "br_inep_censo_educacao_superior": "educacao",
    "br_inep_censo_escolar": "educacao",
    "br_inep_educacao_especial": "educacao",
    "br_inep_enem": "educacao",
    "br_inep_formacao_docente": "educacao",
    "br_inep_ideb": "educacao",
    "br_inep_indicador_nivel_socioeconomico": "educacao",
    "br_inep_indicadores_educacionais": "educacao",
    "br_inep_saeb": "educacao",
    "br_inep_sinopse_estatistica_educacao_basica": "educacao",
    "br_inmet_bdmep": "meio_ambiente",
    "br_inpe_deter": "meio_ambiente",
    "br_inpe_prodes": "meio_ambiente",
    "br_inpe_queimadas": "meio_ambiente",
    "br_inpe_sisam": "meio_ambiente",
    "br_ipea_acesso_oportunidades": "infraestrutura",
    "br_ipea_atlasviolencia": "seguranca",
    "br_ipea_avs": "populacao",
    "br_mapbiomas_estatisticas": "meio_ambiente",
    "br_mc_indicadores": "governo",
    "br_mdr_snis": "infraestrutura",
    "br_me_caged": "economia",
    "br_me_clima_organizacional": "governo",
    "br_me_cno": "infraestrutura",
    "br_me_cnpj": "economia",
    "br_me_comex_stat": "economia",
    "br_me_estoque_divida_publica": "governo",
    "br_me_exportadoras_importadoras": "economia",
    "br_me_rais": "economia",
    "br_me_rais_identificada": "economia",
    "br_me_siape": "governo",
    "br_me_sic": "governo",
    "br_me_siconfi": "governo",
    "br_me_siorg": "governo",
    "br_mec_prouni": "educacao",
    "br_mec_sisu": "educacao",
    "br_mg_belohorizonte_smfa_iptu": "governo",
    "br_minc_salic": "cultura_arte",
    "br_mj_consumidorgovbr": "economia",
    "br_mjsp_ckan": "seguranca",
    "br_mjsp_procurados": "seguranca",
    "br_mjsp_sinesp": "seguranca",
    "br_mjsp_sisdepen": "seguranca",
    "br_mma_extincao": "meio_ambiente",
    "br_mme_consumo_energia_eletrica": "infraestrutura",
    "br_mobilidados_indicadores": "infraestrutura",
    "br_mp_pep": "governo",
    "br_ms_atencao_basica": "saude",
    "br_ms_cnes": "saude",
    "br_ms_imunizacoes": "saude",
    "br_ms_pns": "saude",
    "br_ms_populacao": "populacao",
    "br_ms_sia": "saude",
    "br_ms_sih": "saude",
    "br_ms_sim": "saude",
    "br_ms_sinan": "saude",
    "br_ms_sinan_chikungunya": "saude",
    "br_ms_sinan_esquistossomose": "saude",
    "br_ms_sinan_febre_amarela": "saude",
    "br_ms_sinan_malaria": "saude",
    "br_ms_sinan_violencia": "seguranca",
    "br_ms_sinan_zika": "saude",
    "br_ms_sinasc": "saude",
    "br_ms_sisvan": "saude",
    "br_ms_vacinacao_covid19": "saude",
    "br_ok_queridodiario": "governo",
    "br_ok_queridodiario_texto": "governo",
    "br_pgfn_dividaativa": "governo",
    "br_pncp": "governo",
    "br_poder360_pesquisas": "politica",
    "br_rf_arrecadacao": "governo",
    "br_rf_cafir": "territorio",
    "br_rf_cno": "infraestrutura",
    "br_rf_dirpf": "governo",
    "br_rj_isp_estatisticas_seguranca": "seguranca",
    "br_saude_bps": "saude",
    "br_saude_farmaciapopular": "saude",
    "br_sedec_desastres": "meio_ambiente",
    "br_seeg_emissoes": "meio_ambiente",
    "br_senado_ceaps": "politica",
    "br_senado_dadosabertos": "politica",
    "br_senado_dados_abertos": "politica",
    "br_senado_dados_abertos_administrativos": "politica",
    "br_sfb_sicar": "meio_ambiente",
    "br_simet_educacao_conectada": "educacao",
    "br_siop_orcamento": "governo",
    "br_sp_saopaulo_geosampa_iptu": "governo",
    "br_stf_corte_aberta": "seguranca",
    "br_stj_dadosabertos": "seguranca",
    "br_tce_es": "governo",
    "br_tce_pi": "governo",
    "br_tce_rj": "governo",
    "br_tce_sp": "governo",
    "br_tce_to": "governo",
    "br_tcu_dadosabertos": "governo",
    "br_tcu_inidoneos": "seguranca",
    "br_tesouro_capag": "governo",
    "br_tesouro_cauc": "governo",
    "br_transferegov": "governo",
    "br_transferegov_siconv": "governo",
    "br_trase_supply_chain": "meio_ambiente",
    "br_tse_eleicoes": "politica",
    "br_tse_filiacao_partidaria": "politica",
    "eu_sanctions": "seguranca",
    "global_ibge_tabua_mares": "meio_ambiente",
    "global_icij_offshoreleaks": "seguranca",
    "global_ofac_sanctions": "seguranca",
    "global_opensanctions": "seguranca",
    "mundo_transfermarkt_competicoes": "outros",
    "mundo_transfermarkt_competicoes_internacionais": "outros",
    "un_sanctions": "seguranca",
    "us_harvard_ned": "politica",
    "world_ampas_oscar": "cultura_arte",
    "world_iea_pirls": "educacao",
    "world_iea_timss": "educacao",
    "world_imdb_movies": "cultura_arte",
    "world_oecd_pisa": "educacao",
    "world_oecd_public_finance": "governo",
    "world_olympedia_olympics": "outros",
    "world_sofascore_competicoes_futebol": "outros",
    "world_wb_mides": "governo",
    "world_wwf_hydrosheds": "meio_ambiente",
}


def atlas_domain_of(dataset: str) -> str:
    theme = ATLAS_DATASET_THEME.get(dataset)
    if theme is None:
        print(f"  ! tema do atlas não mapeado para {dataset!r} — usando 'outros' "
              f"(adicione uma linha em ATLAS_DATASET_THEME)", file=sys.stderr)
        return "outros"
    return theme


def load_row_counts() -> dict[str, dict]:
    """dataset.table -> {rows, size_bytes, source_name, status} from the catalog."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        print("! pyarrow missing — graph will carry no row counts", file=sys.stderr)
        return {}
    if not CATALOG.exists():
        print(f"! {CATALOG} missing — run build_metadata_catalog.py", file=sys.stderr)
        return {}
    t = pq.read_table(CATALOG).to_pydict()
    return {
        f"{d}.{tb}": {"rows": r, "bytes": b, "src": sn, "status": st}
        for d, tb, r, b, sn, st in zip(
            t["dataset"], t["table"], t["rows"], t["size_bytes"],
            t["source_name"], t["status"],
        )
    }


def select_keys(idx) -> list[str]:
    """The set gera_join_keys.py documents, minus the keys that connect nothing.

    `select_join_columns` is shared with the doc so the two never drift, but the
    doc and the map want different cuts of it. The doc lists a role-qualified
    column that lives in a single table (`sigla_uf_conselho_prescritor`) because
    a reader looking that column up still needs to be told it is a state code.
    The map is bipartite table→key and exists to show what *connects*: a key
    reaching one table draws an edge to nothing and just adds a dangling node to
    a picture whose whole job is adjacency. Curated hubs stay regardless — they
    are the anchors, and they carry the descriptions the panel shows.
    """
    curated, shared, hub = select_join_columns(idx)
    connecting = {c for c in shared | set(hub) if len(idx[c]["tables"]) >= 2}
    return sorted(curated | connecting)


def build():
    schema = json.loads(SCHEMAS.read_text())
    tables = schema["tables"]
    catalog = load_row_counts()
    idx = index_columns(tables)

    key_names = select_keys(idx)
    _, _, hub_map = select_join_columns(idx)
    key_pos = {c: i for i, c in enumerate(key_names)}
    key_set = set(key_names)

    # ---- datasets -------------------------------------------------------
    ds_names = sorted({tid.split(".", 1)[0] for tid in tables})
    ds_pos = {d: i for i, d in enumerate(ds_names)}
    ds_rows = Counter()
    ds_tables = Counter()

    # ---- tables ---------------------------------------------------------
    out_tables = []
    key_tables = defaultdict(list)   # key index -> table indices
    key_datasets = defaultdict(set)

    for tid in sorted(tables):
        dataset, name = tid.split(".", 1)
        meta = tables[tid]
        cols = meta.get("columns", [])
        cat = catalog.get(tid, {})
        rows = cat.get("rows", 0) or 0

        ti = len(out_tables)
        my_keys = []
        seen = set()
        # O grafo liga por NOME de coluna, então um hub que renomeia a coluna sai do
        # mapa mesmo continuando a ligar. `concept_aliases` diz qual conceito a coluna
        # local representa — sem isso `br_bd_diretorios_mundo.pais` fica órfã depois do
        # rename de 2026-08-23 (sigla_pais_iso3 -> sigla_iso3), e o mesmo vale para
        # `br_bd_diretorios_brasil.uf.sigla`.
        alias_da_tabela = CONCEPT_ALIASES.get(tid, {})
        locais = set()          # nomes como estão NA tabela, para ordenar as colunas
        for col in cols:
            low = col["name"].lower()
            conceito = alias_da_tabela.get(col["name"], alias_da_tabela.get(low, low))
            if conceito in key_set and conceito not in seen:
                seen.add(conceito)
                locais.add(low)
                ki = key_pos[conceito]
                my_keys.append(ki)
                key_tables[ki].append(ti)
                key_datasets[ki].add(dataset)

        # key columns first, then the rest up to the cap
        ordered = [c for c in cols if c["name"].lower() in locais]
        rest = [c for c in cols if c["name"].lower() not in locais]
        shown = ordered + rest[: max(0, MAX_COLS - len(ordered))]

        out_tables.append({
            "n": name,
            "ds": ds_pos[dataset],
            "r": rows,
            "b": cat.get("bytes", 0) or 0,
            "nc": len(cols),
            "k": sorted(my_keys),
            "c": [[c["name"], TYPE_MAP.get(c.get("type", ""), c.get("type", "?"))]
                  for c in shown],
        })
        ds_rows[dataset] += rows
        ds_tables[dataset] += 1

    # ---- keys -----------------------------------------------------------
    out_keys = []
    for i, col in enumerate(key_names):
        info = idx[col]
        cur = CURATED.get(col, {})
        types = info["types"].most_common(2)
        entry = {
            "n": info["spellings"].most_common(1)[0][0],
            "cat": cat_of(col, hub_map),
            "t": len(key_tables[i]),
            "d": len(key_datasets[i]),
            "ty": [t for t, _ in types],
            "sp": [s for s, _ in info["spellings"].most_common(4)],
        }
        if cur:
            # the curated paragraph is what makes a key node worth clicking;
            # strip the markdown backticks since it renders as plain text
            entry["desc"] = re.sub(r"`([^`]*)`", r"\1", cur["desc"])
            if cur.get("ref"):
                entry["ref"] = cur["ref"]
        out_keys.append(entry)

    # The zoomed-out map is 197 identical white cards unless each one carries
    # something. Its most specific key — the one reaching fewest tables — says
    # more about what a dataset is than its widest one ever could.
    GROUP_OF = {
        "empresa": "id", "pessoa": "id",
        "municipio": "geo", "uf": "geo", "geo": "geo",
        "saude": "dom", "educacao": "dom", "governo": "dom",
        "politica": "dom", "classificacao": "dom",
        "tempo": "axis", "outros": "axis",
    }
    ds_key_sets = defaultdict(set)
    for t in out_tables:
        ds_key_sets[t["ds"]].update(t["k"])

    out_datasets = []
    for di, d in enumerate(ds_names):
        keys_here = ds_key_sets.get(di, set())
        grp = ""
        if keys_here:
            best = min(keys_here, key=lambda ki: (out_keys[ki]["t"], ki))
            grp = GROUP_OF.get(out_keys[best]["cat"], "axis")
        out_datasets.append({
            "n": d,
            "dom": atlas_domain_of(d),
            "t": ds_tables[d],
            "r": ds_rows[d],
            "g": grp,
            "nk": len(keys_here),
        })

    edges = sum(len(t["k"]) for t in out_tables)
    graph = {
        "meta": {
            "generated": date.today().isoformat(),
            "tables": len(out_tables),
            "datasets": len(out_datasets),
            "keys": len(out_keys),
            "edges": edges,
            "rows": sum(t["r"] for t in out_tables),
            "source": "schemas.json + _rodado_metadata/catalog.parquet",
        },
        "domains": {k: ATLAS_THEME_NAMES[k] for k in ATLAS_THEME_ORDER},
        "cats": CAT_NAMES,
        "datasets": out_datasets,
        "keys": out_keys,
        "tables": out_tables,
    }

    print("  layout: grade…", file=sys.stderr)
    grade = layout(out_datasets, out_keys, out_tables)
    print("  layout: temas…", file=sys.stderr)
    thm = layout_theme(out_datasets, out_keys, out_tables)
    graph["layout"] = {
        "cell": [CELL_W, CELL_H, PAD, HEADER],
        "grade": grade,
        "temas": thm,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(graph, ensure_ascii=False, separators=(",", ":")))
    size = OUTPUT.stat().st_size / 1024
    print(f"{OUTPUT.relative_to(REPO_ROOT)} — {len(out_tables)} tabelas, "
          f"{len(out_datasets)} datasets, {len(out_keys)} chaves, "
          f"{edges} arestas ({size:.0f} KB)")

    unconnected = [t for t in out_tables if not t["k"]]
    print(f"  {len(unconnected)} tabelas sem nenhuma chave de join")
    top = sorted(out_keys, key=lambda k: -k["t"])[:8]
    print("  maiores chaves: " + ", ".join(f"{k['n']}({k['t']})" for k in top))


# ---------------------------------------------------------------------------
# Layout — computed here so the page ships coordinates and renders instantly
# ---------------------------------------------------------------------------

# A dataset card holds its tables in a grid; the card is the unit the layout
# packs, and tables/columns are drawn inside it as the viewer zooms in.
CELL_W, CELL_H, PAD, HEADER = 118.0, 26.0, 10.0, 30.0


def card_cols(n_tables: int) -> int:
    """Aim for a square card. A cell is 118x26, so a naive sqrt grid produces
    cards nearly 4:1 wide — and wide flat rectangles pack terribly, which is
    what blew the world up to 6370x6740 and the fit zoom down to 13%."""
    return max(1, math.ceil(math.sqrt(n_tables * CELL_H / CELL_W)))


def card_size(n_tables: int) -> tuple[float, float]:
    cols = card_cols(n_tables)
    rows = math.ceil(n_tables / cols)
    return (cols * CELL_W + 2 * PAD, HEADER + rows * CELL_H + PAD)


def layout(datasets, keys, tables):
    """Force-directed placement of dataset cards around key hubs, then a
    separation pass so no two cards overlap.

    Datasets are attracted to the keys their tables use, weighted by 1/uses —
    `ano` touches 389 tables, so letting it pull as hard as `id_escola` would
    collapse everything onto one point."""
    import numpy as np

    rng = np.random.default_rng(7)
    nd, nk = len(datasets), len(keys)
    n = nd + nk

    sizes = np.zeros((n, 2))
    for i, d in enumerate(datasets):
        sizes[i] = card_size(d["t"])
    for j, k in enumerate(keys):
        w = 90 + 5.5 * len(k["n"])
        sizes[nd + j] = (w, 34.0)

    # dataset -> key adjacency, weighted by how specific the key is
    src, dst, wgt = [], [], []
    seen = set()
    for t in tables:
        for ki in t["k"]:
            pair = (t["ds"], ki)
            if pair in seen:
                continue
            seen.add(pair)
            src.append(t["ds"])
            dst.append(nd + ki)
            wgt.append(1.0 / math.sqrt(keys[ki]["t"]))
    src = np.array(src, dtype=int)
    dst = np.array(dst, dtype=int)
    wgt = np.array(wgt)

    # Datasets with no key at all only feel the origin pull, so the simulation
    # flings them into the void and the fit-to-screen zoom collapses to 13%.
    # Park them in a strip of their own once the rest has settled.
    connected = np.array([i for i, d in enumerate(datasets) if d["nk"]], dtype=int)
    isolated = np.array([i for i, d in enumerate(datasets) if not d["nk"]], dtype=int)
    live = np.concatenate([connected, np.arange(nd, n)])

    # seed keys on a ring by category, universal axes in the middle
    cat_order = ["tempo", "municipio", "uf", "geo", "empresa", "pessoa",
                 "saude", "educacao", "governo", "politica", "classificacao",
                 "outros"]
    inner = {"tempo", "municipio", "uf", "geo"}
    pos = rng.normal(0, 400, (n, 2))
    for j, k in enumerate(keys):
        c = k["cat"] if k["cat"] in cat_order else "outros"
        a = 2 * math.pi * cat_order.index(c) / len(cat_order)
        r = 300 if c in inner else 1900
        pos[nd + j] = (r * math.cos(a) + rng.normal(0, 220),
                       r * math.sin(a) + rng.normal(0, 220))

    area = float(np.sum(sizes[:, 0] * sizes[:, 1]))
    k_rep = math.sqrt(area / n) * 1.15

    for step in range(600):
        t_cool = 1.0 - step / 600
        sub = pos[live]
        disp = np.zeros((len(live), 2))

        # repulsion, O(n^2) but n is ~330
        delta = sub[:, None, :] - sub[None, :, :]
        dist2 = np.sum(delta ** 2, axis=-1) + 1e-6
        np.fill_diagonal(dist2, np.inf)
        disp += np.sum(delta * ((k_rep ** 2) / dist2)[..., None], axis=1)

        # attraction along dataset->key edges
        d = pos[src] - pos[dst]
        dist = np.sqrt(np.sum(d ** 2, axis=-1)) + 1e-6
        pull = (d / dist[:, None]) * (dist * wgt * 0.9)[:, None]
        edge_disp = np.zeros((n, 2))
        np.add.at(edge_disp, src, -pull)
        np.add.at(edge_disp, dst, pull)
        disp += edge_disp[live]

        # gentle pull to origin so islands do not drift off
        disp -= sub * 0.012

        norm = np.sqrt(np.sum(disp ** 2, axis=-1))[:, None] + 1e-9
        pos[live] = sub + (disp / norm) * np.minimum(norm, 90.0 * t_cool + 6.0)

    # The simulation only cares about relative placement, so squeeze the whole
    # thing down to a sane density before separating — otherwise the repulsion
    # equilibrium leaves a world 500x emptier than the cards need.
    # Squeeze to a 4:3 frame sized just above the total card area. The old
    # multiplier of 4.0 produced a 6370x6740 world, which fit-to-screen renders
    # at 13% — every dataset name below its legibility threshold.
    sub = pos[live]
    sub -= sub.mean(axis=0)
    span = np.maximum(sub.max(axis=0) - sub.min(axis=0), 1.0)
    live_area = float(np.sum(sizes[live, 0] * sizes[live, 1]))
    tw = math.sqrt(live_area * 2.1 * 4 / 3)
    sub *= np.array([tw / span[0], (tw * 3 / 4) / span[1]])
    pos[live] = sub

    # 10px of breathing room between cards; the pass below treats this as a
    # hard constraint, so keep it modest or the world inflates to satisfy it.
    half = sizes / 2 + 10.0
    order = live[np.argsort(-(sizes[live, 0] * sizes[live, 1]))]
    rank = {int(v): r for r, v in enumerate(order)}

    def overlaps():
        sub2 = pos[live]
        h = half[live]
        delta = sub2[:, None, :] - sub2[None, :, :]
        over = (h[:, None, :] + h[None, :, :]) - np.abs(delta)
        np.fill_diagonal(over[:, :, 0], -1)
        np.fill_diagonal(over[:, :, 1], -1)
        return delta, over, (over[:, :, 0] > 0) & (over[:, :, 1] > 0)

    # Separation only ever pushes apart, so on its own it preserves whatever
    # slack the force pass left — 20% occupancy, a 16% fit zoom, no readable
    # label anywhere. Over-compress instead and let separation expand back to
    # its own limit, which is the densest packing these positions allow.
    # Anisotropic on purpose: separation drifts the frame taller every cycle,
    # so start wider than 4:3 to land near it on a landscape screen.
    c = pos[live].mean(axis=0)
    pos[live] = c + (pos[live] - c) * np.array([0.62, 0.34])

    for cycle in range(30):
        for it in range(400):
            delta, over, hit = overlaps()
            if not hit.any():
                break
            # Bias toward resolving horizontally: unbiased, the pass drifts the
            # frame to a 0.63 aspect, and on a landscape screen the fit zoom is
            # then bounded by a height nobody has.
            use_x = over[:, :, 0] < over[:, :, 1] * 1.35
            amount = np.where(use_x, over[:, :, 0], over[:, :, 1]) * 0.5
            sign_x = np.where(delta[:, :, 0] >= 0, 1.0, -1.0)
            sign_y = np.where(delta[:, :, 1] >= 0, 1.0, -1.0)
            push = np.zeros((len(live), 2))
            push[:, 0] = np.sum(np.where(hit & use_x, amount * sign_x, 0.0), axis=1)
            push[:, 1] = np.sum(np.where(hit & ~use_x, amount * sign_y, 0.0), axis=1)
            pos[live] += np.clip(push * (0.55 if it < 250 else 0.3), -60, 60)

        delta, over, hit = overlaps()
        ii, jj = np.nonzero(hit)
        stuck = [(int(live[i]), int(live[j])) for i, j in zip(ii, jj) if i < j]
        if not stuck:
            break
        # a handful of pairs always deadlock; free them one at a time, moving
        # the smaller card so the big datasets keep their placement
        li = {int(v): q for q, v in enumerate(live)}
        for i, j in stuck:
            mover = i if rank[i] > rank[j] else j
            other = j if mover == i else i
            oi, oj = li[i], li[j]
            a = 0 if over[oi, oj, 0] < over[oi, oj, 1] else 1
            sign = 1.0 if pos[mover, a] >= pos[other, a] else -1.0
            pos[mover, a] += sign * (float(over[oi, oj, a]) + 1.0)

    # Pack the unconnected datasets into a tidy strip under the main body,
    # labelled in the UI as what they are: tables nothing else joins.
    if len(isolated):
        lo = pos[live].min(axis=0) - half[live].max(axis=0)
        hi = pos[live].max(axis=0) + half[live].max(axis=0)
        width = hi[0] - lo[0]
        cx, cy = lo[0], hi[1] + 150.0
        row_h = 0.0
        for i in isolated:
            w, h = sizes[i]
            if cx > lo[0] and cx + w > lo[0] + width:
                cx = lo[0]
                cy += row_h + 26.0
                row_h = 0.0
            pos[i] = (cx + w / 2, cy + h / 2)
            cx += w + 26.0
            row_h = max(row_h, h)

    # report real box overlaps, not the margin the pass aims for
    delta = pos[:, None, :] - pos[None, :, :]
    raw = (sizes[:, None, :] / 2 + sizes[None, :, :] / 2) - np.abs(delta)
    np.fill_diagonal(raw[:, :, 0], -1)
    np.fill_diagonal(raw[:, :, 1], -1)
    left = int(np.count_nonzero((raw[:, :, 0] > 0) & (raw[:, :, 1] > 0)) // 2)
    if left:
        print(f"  ! {left} cartoes ainda se sobrepoem", file=sys.stderr)

    pos -= pos.min(axis=0) - 60
    world = pos.max(axis=0) + sizes.max(axis=0) + 60

    return {
        "world": [round(float(world[0]), 1), round(float(world[1]), 1)],
        # cols travels with the card: deriving it again in the renderer once
        # let the two formulas diverge, and every table name spilled outside
        # its own card onto the neighbours.
        "ds": [[round(float(pos[i, 0]), 1), round(float(pos[i, 1]), 1),
                round(float(sizes[i, 0]), 1), round(float(sizes[i, 1]), 1),
                card_cols(datasets[i]["t"])]
               for i in range(nd)],
        "keys": [[round(float(pos[nd + j, 0]), 1), round(float(pos[nd + j, 1]), 1),
                  round(float(sizes[nd + j, 0]), 1)] for j in range(nk)],
    }


# ---------------------------------------------------------------------------
# Table-level layout — the unit is the table, not the dataset card
# ---------------------------------------------------------------------------
# The packed layout reads well but flattens affinity: a card sits where it fits,
# not where it belongs. This one puts the 833 tables in the field themselves.

def table_radius(rows: int) -> float:
    """Log scale — row counts span 0 to 6,6 bilhões, so a linear radius would
    render everything but a handful of tables as a dot."""
    return 3.2 + 1.35 * math.log10(max(rows, 1))


def key_radius(reach: int) -> float:
    return 9.0 + 3.4 * math.sqrt(reach)


def layout_theme(datasets, keys, tables):
    """One territory per theme, keys floating between the themes they bridge.

    Ten themes cannot each hold a free-floating hue — past four, colours stop
    being separable for pairs that land next to each other (the all-pairs gate
    fails at five). Clustering makes the theme a *place*, so position and a
    per-cluster label carry identity and colour only reinforces it."""
    import numpy as np

    nt, nk = len(tables), len(keys)
    rad = np.array([table_radius(t["r"]) for t in tables]
                   + [key_radius(k["t"]) for k in keys])
    pos = np.zeros((nt + nk, 2))

    theme_of = [datasets[t["ds"]]["dom"] for t in tables]
    members = {}
    for ti, th in enumerate(theme_of):
        members.setdefault(th, []).append(ti)

    # biggest territory first, spiralling out — keeps the dense themes central
    order = sorted(members, key=lambda th: -len(members[th]))
    centres, placed = {}, []
    for idx, th in enumerate(order):
        own = members[th]
        area = sum(math.pi * (rad[ti] + 4) ** 2 for ti in own)
        rr = math.sqrt(area / math.pi) * 1.5
        # nudge outward until this disc clears the ones already down
        step, ang = 0, idx * 2.399963
        while True:
            d = 0.0 if idx == 0 else (260 + step * 26)
            cx, cy = d * math.cos(ang), d * math.sin(ang)
            if all(math.hypot(cx - x, cy - y) > rr + r2 + 70 for x, y, r2 in placed):
                break
            step += 1
            if step > 400:
                break
        centres[th] = (cx, cy, rr)
        placed.append((cx, cy, rr))
        for m, ti in enumerate(sorted(own, key=lambda i: -tables[i]["r"])):
            a = m * 2.399963
            r = rr * math.sqrt((m + 0.5) / len(own))
            pos[ti] = (cx + r * math.cos(a), cy + r * math.sin(a))

    # a key belongs to no theme — park it at the centroid of what it joins, so
    # it sits between the territories it actually bridges
    for ki in range(nk):
        own = [ti for ti, t in enumerate(tables) if ki in t["k"]]
        if own:
            pos[nt + ki] = np.mean(pos[own], axis=0)
        else:
            pos[nt + ki] = (0.0, 0.0)

    # keys that join tables in one spot land on top of each other
    jitter = np.array([[math.cos(i * 2.399963), math.sin(i * 2.399963)]
                       for i in range(len(pos))]) * 0.4
    pos += jitter
    _separate_circles(pos, rad, rounds=420)
    out = _finish(pos, rad, nt, nk, keys)
    dx = out["_dx"]; dy = out["_dy"]
    out["themes"] = {th: [round(centres[th][0] + dx, 1),
                          round(centres[th][1] + dy, 1),
                          round(centres[th][2], 1)] for th in centres}
    del out["_dx"], out["_dy"]
    return out


def _separate_circles(pos, rad, rounds=340):
    """Push overlapping discs apart. Circles make this far cheaper than the
    rectangle case — one distance test, one direction."""
    import numpy as np

    gap = rad + 3.0
    need = gap[:, None] + gap[None, :]
    for _ in range(rounds):
        delta = pos[:, None, :] - pos[None, :, :]
        dist = np.sqrt(np.sum(delta ** 2, axis=-1))
        np.fill_diagonal(dist, 1e9)          # not inf: inf*0 is nan downstream
        over = need - dist
        hit = over > 0
        if not hit.any():
            break
        # Two bodies at exactly the same point give 0/0 — one NaN here spreads
        # to every position in the field within a single pass.
        unit = delta / np.maximum(dist, 1e-6)[..., None]
        push = np.sum(np.where(hit[..., None], unit * (over * 0.5)[..., None], 0.0), axis=1)
        pos += np.clip(push * 0.55, -40, 40)


def _finish(pos, rad, nt, nk, keys):
    import numpy as np

    shift = -(pos.min(axis=0) - rad.max() - 40)
    pos += shift
    world = pos.max(axis=0) + rad.max() + 40
    r1 = lambda v: round(float(v), 1)
    return {
        "_dx": float(shift[0]), "_dy": float(shift[1]),
        "world": [r1(world[0]), r1(world[1])],
        "tb": [[r1(pos[i, 0]), r1(pos[i, 1]), r1(rad[i])] for i in range(nt)],
        "keys": [[r1(pos[nt + j, 0]), r1(pos[nt + j, 1]),
                  r1(key_radius(keys[j]["t"]))] for j in range(nk)],
    }


if __name__ == "__main__":
    build()
