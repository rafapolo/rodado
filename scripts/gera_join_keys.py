#!/usr/bin/env python3
"""Generate `docs/context/join_keys.md` from `schemas.json`.

    python3 scripts/gera_schemas.py     # beelink -> schemas.json
    python3 scripts/gera_join_keys.py   # schemas.json -> docs/context/join_keys.md

The previous version of the doc was written by hand (its header credited a
`schema_compiler.py` that does not exist in the repo) and covered 24 columns
whose names already matched across datasets. That misses most of what actually
connects the mirror: the independently-scraped sources name the same key
`UF`, `codIBGE`, `cód_ibge`, `MUNIC`, `CPF_CNPJ`, `nomeMunicipio`…, and the
Base dos Dados datasets carry role-qualified municipality columns
(`id_municipio_residencia`, `_ocorrencia`, `_trabalho`, …) that all resolve to
the same directory. Those are the joins an LLM cannot guess.

Three layers of content:

  1. CURATED   — hand-written sections for the hub keys: what the code is,
                 which table is canonical, and the gotchas.
  2. BRIDGES   — the non-standard columns, each with a tested normalization
                 recipe (see MUNICIPIO_BRIDGES / IDENTITY_BRIDGES). The
                 `verificado` field records what the recipe actually matched
                 when it was run on beelink, so a reader knows the recipe is
                 not aspirational.
  3. AUTO      — every remaining column shared by >= MIN_DATASETS datasets,
                 emitted with the same `### \\`col\\` — N tables` header so
                 `mcp_server.get_join_keys()` can serve it.

`mcp_server.py` parses this file with a regex on that h3 header and slices
until the next one, so every h3 must be a real column name and any prose that
is not part of a column's section must come before the first h3.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "schemas.json"
DST = REPO / "docs" / "context" / "join_keys.md"
BEELINK_HOST = "beelink"
BEELINK_ROOT = "/home/polo/rodado"

# A column has to show up in at least this many datasets to be auto-documented.
# Below that it is only in the file if it was curated or bridged by hand.
MIN_DATASETS = 2

# physical parquet type -> what you see in DuckDB
TYPE_MAP = {
    "BYTE_ARRAY": "VARCHAR",
    "FIXED_LEN_BYTE_ARRAY": "VARCHAR",
    "INT64": "BIGINT",
    "INT32": "INTEGER",
    "INT96": "TIMESTAMP",
    "DOUBLE": "DOUBLE",
    "FLOAT": "FLOAT",
    "BOOLEAN": "BOOLEAN",
}

# Columns that pass the name heuristic but are values, not keys.
AUTO_DENY = {
    "valor", "numero", "sigla", "data_extracao", "data_coleta", "data_atualizacao",
    "data_hora", "data_referencia", "anos_estudo", "id", "version", "id_estrato",
    "id_categoria_principal_sidra", "numero_ordem", "numero_lote", "numero_logradouro",
    "id_unidade", "id_item", "id_quadro", "id_categoria",
}

# ---------------------------------------------------------------------------
# Categories, in output order
# ---------------------------------------------------------------------------

CATEGORIES = [
    ("municipio", "Municipality — the hub key",
     "Every second table in the mirror is municipal. `id_municipio` is the "
     "canonical form; everything else in this section is a variant that has to "
     "be converted to it."),
    ("uf", "State (UF)", "The second most common axis, and the one most often "
     "renamed by scraped sources."),
    ("geo", "Other geography",
     "Region, census tract, district, postal code, country."),
    ("tempo", "Time", "Partition columns. Filter on these before anything else."),
    ("empresa", "Company identity (CNPJ)",
     "`br_me_cnpj` is the backbone: 60M+ establishments, joined by `cnpj` or "
     "`cnpj_basico`."),
    ("pessoa", "Person identity (CPF)",
     "Almost always masked in public data — read the note on each column "
     "before assuming a CPF join is possible."),
    ("educacao", "Education", "INEP school/course/student codes."),
    ("saude", "Health", "CNES, SUS and disease-notification codes."),
    ("governo", "Government, budget and procurement",
     "Organs, management units, tenders, contracts, budget lines."),
    ("politica", "Politics and elections", "TSE and Câmara dos Deputados codes."),
    ("classificacao", "Classification codes",
     "CNAE, CBO, CID, NCM — the code tables that decode microdata."),
    ("outros", "Other shared columns",
     "Auto-detected: columns that appear in two or more datasets and look like "
     "identifiers. Less curated, but real join surface."),
]

# ---------------------------------------------------------------------------
# Curated sections
# ---------------------------------------------------------------------------
# desc:  one paragraph. ref: canonical table. notes: bullet list. example: SQL.

CURATED = {
    # ---------------- municipality ----------------
    "id_municipio": dict(
        cat="municipio",
        desc="7-digit IBGE municipality code, stored as VARCHAR (zero-padding "
             "matters — `1100015`, never `1100015.0`). This is the join key to "
             "reach for; every other municipality column below exists to be "
             "converted into it.",
        ref="br_bd_diretorios_brasil.municipio",
        notes=[
            "The directory has 5.571 municipalities (5.570 + Brasília's district "
            "split), each stored twice — see the duplication warning at the top "
            "of this file. Join against a deduped subquery or you double every "
            "count.",
            "`id_municipio_6` is the same code without the check digit: "
            "`substr(id_municipio, 1, 6)`.",
            "Municipalities created after the directory snapshot (e.g. Boa "
            "Esperança do Norte/MT) have NULL `id_municipio_tse`, `_rf` and "
            "`_bcb` — 2 of 5.571.",
        ],
        example="""-- always dedupe the directory before joining
WITH mun AS (SELECT DISTINCT id_municipio, nome, sigla_uf
             FROM br_bd_diretorios_brasil.municipio)
SELECT m.nome AS municipio, m.sigla_uf, p.pib
FROM br_ibge_pib.municipio p
JOIN mun m USING (id_municipio)
WHERE p.ano = 2021
ORDER BY p.pib DESC
LIMIT 20""",
    ),
    "id_municipio_6": dict(
        cat="municipio",
        desc="IBGE municipality code without the check digit (6 digits). Used "
             "by DATASUS systems (CNES, SINAN, SIH) and by the older health "
             "aggregates.",
        ref="br_bd_diretorios_brasil.municipio.id_municipio_6",
        notes=[
            "Convert either way: `substr(id_municipio, 1, 6) = id_municipio_6`.",
            "In SINAN microdata the column arrives as a float-shaped string "
            "(`261640.0`) — normalize with "
            "`lpad(CAST(CAST(x AS DOUBLE) AS BIGINT)::VARCHAR, 6, '0')`.",
        ],
        example="""WITH mun AS (SELECT DISTINCT id_municipio_6, nome, sigla_uf
             FROM br_bd_diretorios_brasil.municipio)
SELECT m.nome, m.sigla_uf, count(*) AS estabelecimentos
FROM br_ms_cnes.estabelecimento e
JOIN mun m ON e.id_municipio_6 = m.id_municipio_6
WHERE e.ano = 2023 AND e.mes = 12
GROUP BY 1, 2
ORDER BY 3 DESC""",
    ),
    "id_municipio_tse": dict(
        cat="municipio",
        desc="TSE (Electoral Court) municipality code — a short sequential "
             "number, unique only inside a UF. Every electoral table keys on it.",
        ref="br_bd_diretorios_brasil.municipio.id_municipio_tse",
        notes=[
            "Not interchangeable with the IBGE code: `35` is Porto Velho in the "
            "TSE numbering. Always go through the directory.",
            "Also appears role-qualified: `id_municipio_tse_doador` (donor) and "
            "`id_municipio_tse_fornecedor` (supplier) in the campaign-finance "
            "tables.",
        ],
        example="""-- the TSE code repeats across states: always pair it with sigla_uf
WITH mun AS (SELECT DISTINCT id_municipio_tse, nome, sigla_uf
             FROM br_bd_diretorios_brasil.municipio
             WHERE id_municipio_tse IS NOT NULL)
SELECT m.nome, m.sigla_uf, sum(v.votos_nominais) AS votos
FROM br_tse_eleicoes.detalhes_votacao_municipio v
JOIN mun m ON v.id_municipio_tse = m.id_municipio_tse AND v.sigla_uf = m.sigla_uf
WHERE v.ano = 2022 AND v.turno = 1
GROUP BY 1, 2""",
    ),
    "id_municipio_rf": dict(
        cat="municipio",
        desc="Receita Federal municipality code (4 digits). This is the **only** "
             "municipality column in `br_me_cnpj.estabelecimentos` — geolocating "
             "any company in the CNPJ base goes through it.",
        ref="br_bd_diretorios_brasil.municipio.id_municipio_rf",
        notes=[
            "Verified: joining the distinct `id_municipio_rf` of "
            "`br_me_cnpj.estabelecimentos` against the directory matches 11.140 "
            "of 11.142 directory rows (i.e. all but the 2 municipalities with a "
            "NULL RF code).",
            "`7107` = São Paulo, `6001` = Rio de Janeiro — the codes are not "
            "IBGE-ordered, do not try to derive them.",
        ],
        example="""WITH mun AS (SELECT DISTINCT id_municipio_rf, id_municipio, nome, sigla_uf
             FROM br_bd_diretorios_brasil.municipio
             WHERE id_municipio_rf IS NOT NULL)
SELECT m.nome, m.sigla_uf, count(*) AS estabelecimentos
FROM br_me_cnpj.estabelecimentos e
JOIN mun m ON e.id_municipio_rf = m.id_municipio_rf
WHERE e.ano = 2025 AND e.mes = 9      -- one snapshot, see the cnpj section
  AND e.situacao_cadastral = '02'
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 20""",
    ),
    "id_municipio_bcb": dict(
        cat="municipio",
        desc="Banco Central municipality code. Present only in the directory — "
             "it is there so BCB extracts (ESTBAN, SICOR) that carry it can be "
             "brought back to IBGE codes.",
        ref="br_bd_diretorios_brasil.municipio.id_municipio_bcb",
        notes=["No table in the mirror currently keys on it; it is a crosswalk "
               "column, not a join surface."],
    ),
    "codigo_municipio_siafi": dict(
        cat="municipio",
        desc="SIAFI municipality code (4 digits), used by the CGU social-benefit "
             "extracts (Garantia-Safra, Pé-de-Meia, Seguro Defeso).",
        ref="— none in the mirror",
        notes=[
            "**There is no SIAFI column in the directory.** Join those datasets "
            "by name + UF instead; the CGU files carry `nome_municipio` and `uf` "
            "next to the SIAFI code.",
            "Verified: `upper(strip_accents(nome_municipio))` + `uf` against the "
            "directory matches 2.642 name/UF pairs of Garantia-Safra.",
        ],
        example="""-- br_cgu_garantia_safra has no view: read the parquet directly (gotcha 5),
WITH mun AS (SELECT DISTINCT id_municipio, nome, sigla_uf
             FROM br_bd_diretorios_brasil.municipio)
-- and its valor_parcela is VARCHAR with a comma decimal separator ('135,00')
SELECT m.id_municipio, m.nome,
       sum(CAST(replace(g.valor_parcela, ',', '.') AS DOUBLE)) AS total
FROM read_parquet('~/rodado/br_cgu_garantia_safra/garantia_safra/*.parquet') g
JOIN mun m ON upper(strip_accents(g.nome_municipio)) = upper(strip_accents(m.nome))
          AND g.uf = m.sigla_uf
GROUP BY 1, 2""",
    ),
    "municipio": dict(
        cat="municipio",
        desc="Municipality *name* (not a code), under the shortest possible "
             "name. Six datasets use it, and each one stores a different "
             "shape — slug, upper case, or name + UF in parentheses.",
        ref="br_bd_diretorios_brasil.municipio.nome",
        notes=[
            "`br_ibge_censo2022_raca.*` / `br_ibge_censo2022_religiao.*`: "
            "`Alta Floresta D'Oeste (RO)` — split the UF out of the parentheses.",
            "`br_tce_sp.municipios`: a slug (`aguas-de-lindoia`); the display "
            "name is in `municipio_extenso`.",
            "`br_anp_combustiveis.precos` and "
            "`br_cvm_administradores_carteira.pessoa_juridica`: upper case, "
            "unaccented, and CVM sometimes abbreviates (`POA`).",
            "See the bridge table under `id_municipio` for the exact expression "
            "per dataset.",
        ],
    ),
    "nome_municipio": dict(
        cat="municipio",
        desc="Municipality name as text. A fallback key — use it only when no "
             "code is available, and always normalize both sides.",
        ref="br_bd_diretorios_brasil.municipio.nome",
        notes=[
            "Normalize with `upper(strip_accents(x))`. Sources disagree on "
            "accents (`ITAJAÍ` vs `ITAJAI`), on case, and occasionally on "
            "abbreviations (`POA` for Porto Alegre in "
            "`br_cvm_administradores_carteira`).",
            "Names are not unique across UFs — 'Bom Jesus' exists in 8 states. "
            "Always pair the name with a UF column.",
        ],
    ),
    # ---------------- UF ----------------
    "sigla_uf": dict(
        cat="uf",
        desc="Two-letter state abbreviation (`SP`, `RJ`). The most widely shared "
             "column in the mirror and the safest geographic join.",
        ref="br_bd_diretorios_brasil.uf.sigla",
        notes=[
            "The directory `uf` table is also duplicated (54 rows for 27 states) "
            "— dedupe before joining.",
            "Scraped sources spell this `UF`, `uf`, `SG_UF`, `ufSigla`, `estado` "
            "or `sigla_uf` — see the bridge table below.",
        ],
        example="""WITH uf AS (SELECT DISTINCT sigla, nome FROM br_bd_diretorios_brasil.uf)
SELECT u.nome AS estado, count(*) AS obitos
FROM br_ms_sim.microdados s
JOIN uf u ON s.sigla_uf = u.sigla
WHERE s.ano = 2020
GROUP BY 1
ORDER BY 2 DESC""",
    ),
    "id_uf": dict(
        cat="uf",
        desc="2-digit IBGE state code (`35` = São Paulo). The first two digits "
             "of every `id_municipio`.",
        ref="br_bd_diretorios_brasil.uf.id_uf",
        notes=[
            "Derivable: `substr(id_municipio, 1, 2) = id_uf`.",
            "`br_ms_sinan_violencia.microdados_violencia` calls it `SG_UF` and "
            "stores the numeric code, not the abbreviation.",
        ],
    ),
    "uf": dict(
        cat="uf",
        desc="`sigla_uf` under a shorter name — what the independently-scraped "
             "sources call it, spelled `uf` or `UF` depending on the source. "
             "Usually the same two-letter code, so it joins `sigla_uf` directly.",
        ref="br_bd_diretorios_brasil.uf.sigla",
        notes=[
            "Two-letter code in `br_caixa_sinapi`, `br_cgu_garantia_safra`, "
            "`br_cgu_pe_de_meia`, `br_cgu_seguro_defeso`, `br_fbsp_absp`, "
            "`br_mjsp_sinesp`, `br_mj_consumidorgovbr`, `br_mjsp_ckan`, "
            "`br_tcu_inidoneos`, `br_tesouro_capag` — direct join.",
            "`br_mjsp_sisdepen.populacao_carceraria` stores `Acre (AC)` — "
            "extract with `regexp_extract(uf, '\\(([A-Z]{2})\\)$', 1)`.",
            "`br_siop_orcamento.localizadores` stores the **full state name, "
            "mojibake** (`EspÃ­rito Santo`) — re-encode before matching.",
        ],
    ),
    "estado": dict(
        cat="uf",
        desc="Full state name, in the two datasets that spell it out.",
        ref="br_bd_diretorios_brasil.uf.nome",
        notes=["`br_anp_combustiveis.precos`: unaccented upper case "
               "(`RONDONIA`), `-` when missing.",
               "`br_mjsp_procurados.procurados`: accents inconsistent "
               "(`GOIAS`, `PARÁ`). The neighbouring `nome_estado` column is "
               "mislabeled at the source — it holds the person's name."],
    ),
    "id_regiao": dict(
        cat="uf",
        desc="IBGE macro-region code (1 = Norte … 5 = Centro-Oeste).",
        ref="br_bd_diretorios_brasil.setor_censitario_2022 / br_geobr_mapas.regiao",
    ),
    # ---------------- other geography ----------------
    "id_setor_censitario": dict(
        cat="geo",
        desc="15-digit IBGE census tract code — the finest geography in the "
             "mirror. Its first 7 digits are the `id_municipio`.",
        ref="br_bd_diretorios_brasil.setor_censitario_2022",
        notes=[
            "The 2010 and 2022 tract meshes are **not** compatible: tracts were "
            "redrawn. Never join a 2010 tract to a 2022 tract; aggregate both to "
            "`id_municipio` instead.",
            "`substr(id_setor_censitario, 1, 7) = id_municipio` works in both "
            "vintages.",
        ],
    ),
    "id_distrito": dict(cat="geo", desc="IBGE district code (municipality "
                        "subdivision). Vintage-specific: 1991, 2000 and 2010 "
                        "meshes are separate directory tables.",
                        ref="br_bd_diretorios_brasil.distrito_2010"),
    "id_subdistrito": dict(cat="geo", desc="IBGE subdistrict code, one level "
                           "below the district.",
                           ref="br_bd_diretorios_brasil.setor_censitario_2022"),
    "id_mesorregiao": dict(cat="geo", desc="IBGE mesoregion code.",
                           ref="br_bd_diretorios_brasil.municipio"),
    "id_microrregiao": dict(cat="geo", desc="IBGE microregion code.",
                            ref="br_bd_diretorios_brasil.municipio"),
    "id_regiao_imediata": dict(cat="geo", desc="IBGE immediate region "
                               "(the 2017 replacement for microregions).",
                               ref="br_bd_diretorios_brasil.municipio"),
    "id_regiao_intermediaria": dict(cat="geo", desc="IBGE intermediate region "
                                    "(replaces mesoregions).",
                                    ref="br_bd_diretorios_brasil.municipio"),
    "id_regiao_metropolitana": dict(cat="geo", desc="Metropolitan region code.",
                                    ref="br_bd_diretorios_brasil.municipio"),
    "id_regiao_saude": dict(cat="geo", desc="SUS health region — the "
                            "administrative unit health policy is planned on.",
                            ref="br_bd_diretorios_brasil.municipio"),
    "cep": dict(
        cat="geo",
        desc="Brazilian postal code. The directory maps every CEP to "
             "`id_municipio`, so it is a usable bridge when a source has an "
             "address but no municipality code.",
        ref="br_bd_diretorios_brasil.cep",
        notes=[
            "905.210 rows, and — unusually for the directory — **not** "
            "duplicated.",
            "Stored as 8-digit VARCHAR without the hyphen. Strip punctuation "
            "before joining: `regexp_replace(cep, '[^0-9]', '', 'g')`.",
        ],
        example="""SELECT c.nome_municipio, c.sigla_uf, count(*) AS empresas
FROM br_me_cnpj.estabelecimentos e
JOIN br_bd_diretorios_brasil.cep c ON e.cep = c.cep
WHERE e.ano = 2025 AND e.mes = 9      -- one snapshot, see the cnpj section
  AND e.situacao_cadastral = '02'
GROUP BY 1, 2
ORDER BY 3 DESC
LIMIT 20""",
    ),
    "id_pais": dict(cat="geo", desc="Country code. `br_bd_diretorios_mundo.pais` "
                    "carries every common encoding (M49, FAO, GAUL, ISO2/ISO3, "
                    "COI, FIFA) — use it to reconcile international datasets.",
                    ref="br_bd_diretorios_mundo.pais"),
    "sigla_pais_iso3": dict(cat="geo", desc="ISO 3166-1 alpha-3 country code. "
                            "The join key for the `world_*` datasets.",
                            ref="br_bd_diretorios_mundo.pais"),
    # ---------------- time ----------------
    "ano": dict(
        cat="tempo",
        desc="Year. The primary partition column across the mirror — filter on "
             "it in every query against a large table.",
        ref="br_bd_diretorios_data_tempo.ano",
        notes=[
            "BIGINT in most tables but VARCHAR in a few scraped ones (see the "
            "type breakdown above) — cast explicitly when joining across "
            "datasets: `CAST(a.ano AS INT) = CAST(b.ano AS INT)`.",
        ],
        example="""-- densidade_municipio.ano is VARCHAR, ideb.ano is BIGINT: cast both sides
SELECT CAST(a.ano AS INT) AS ano, a.id_municipio, a.densidade AS banda_larga, b.ideb
FROM br_anatel_banda_larga_fixa.densidade_municipio a
JOIN br_inep_ideb.municipio b
  ON a.id_municipio = b.id_municipio AND CAST(a.ano AS INT) = b.ano
WHERE CAST(a.ano AS INT) BETWEEN 2015 AND 2021""",
    ),
    "mes": dict(cat="tempo", desc="Month (1–12). Always use together with `ano`; "
                "a few tables carry `mes` alone and are ambiguous without it.",
                ref="br_bd_diretorios_data_tempo.mes"),
    "data": dict(cat="tempo", desc="Full date. Event-level microdata tables use "
                 "it instead of ano/mes.",
                 ref="br_bd_diretorios_data_tempo.data",
                 notes=["DATE in most tables, VARCHAR in 7 — cast before "
                        "comparing, and beware of `DD/MM/YYYY` strings in the "
                        "scraped sources."]),
    "trimestre": dict(cat="tempo", desc="Quarter (1–4). PNAD Contínua and "
                      "quarterly economic series.",
                      ref="br_bd_diretorios_data_tempo.trimestre"),
    "semestre": dict(cat="tempo", desc="Semester (1–2).",
                     ref="br_bd_diretorios_data_tempo.semestre"),
    "year": dict(cat="tempo", desc="Year, English-named — the `world_*` and "
                 "`us_*` datasets use this instead of `ano`.",
                 ref="—"),
    # ---------------- company ----------------
    "cnpj": dict(
        cat="empresa",
        desc="14-digit company tax ID (8 base + 4 branch + 2 check digits). "
             "`br_me_cnpj.estabelecimentos` is the reference: every active and "
             "extinct establishment in Brazil.",
        ref="br_me_cnpj.estabelecimentos",
        notes=[
            "**`br_bd_diretorios_brasil.empresa` is empty (0 rows)** — the old "
            "version of this file used it as the CNPJ reference. Use "
            "`br_me_cnpj.estabelecimentos` (14-digit `cnpj`) or "
            "`br_me_cnpj.empresas` (8-digit `cnpj_basico`, one row per company).",
            "Formats differ wildly across sources. Normalize to bare 14 digits: "
            "`lpad(regexp_replace(CAST(cnpj AS VARCHAR), '[^0-9]', '', 'g'), 14, '0')`. "
            "In `br_anp_combustiveis.precos` only 875k of 2M rows already have "
            "14 characters; `br_brasilio_holdings.holdings` stores it as BIGINT, "
            "so leading zeros are gone.",
            "**`br_me_cnpj.empresas` and `estabelecimentos` are stacked monthly "
            "full snapshots** — 43 of them, 2021-11 to 2025-09, ~64M rows each. "
            "A join that does not pin `(ano, mes)` multiplies every company by "
            "43. Always add `WHERE ano = 2025 AND mes = 9` (or whichever "
            "snapshot you want) on the CNPJ side.",
        ],
        example="""-- normalize the outside key, and pin one CNPJ snapshot
WITH postos AS (
  SELECT DISTINCT lpad(regexp_replace(CAST(cnpj AS VARCHAR), '[^0-9]', '', 'g'), 14, '0') AS cnpj
  FROM br_anp_combustiveis.precos
)
SELECT e.razao_social, e.porte
FROM postos p
JOIN br_me_cnpj.empresas e
  ON substr(p.cnpj, 1, 8) = e.cnpj_basico
WHERE e.ano = 2025 AND e.mes = 9
LIMIT 20""",
    ),
    "cnpj_basico": dict(
        cat="empresa",
        desc="First 8 digits of the CNPJ — the company, without the branch. "
             "One row per company in `br_me_cnpj.empresas`.",
        ref="br_me_cnpj.empresas",
        notes=["Join `empresas` (company-level: razão social, capital, porte) to "
               "`estabelecimentos` (branch-level: address, CNAE, situation) on "
               "`cnpj_basico`, and to `socios` for ownership. `socios` names the "
               "partner columns `nome` and `qualificacao` (not `nome_socio`), "
               "and `cnae_fiscal_principal` lives on `estabelecimentos`, not on "
               "`empresas`.",
               "`substr(cnpj, 1, 8) = cnpj_basico`.",
               "All three tables are monthly snapshots — join them on "
               "`(cnpj_basico, ano, mes)`, never on `cnpj_basico` alone."],
        example="""SELECT e.razao_social, s.nome, s.qualificacao
FROM br_me_cnpj.empresas e
JOIN br_me_cnpj.socios s USING (cnpj_basico, ano, mes)
WHERE e.cnpj_basico = '13926231' AND e.ano = 2025 AND e.mes = 9""",
    ),
    "cnae_2_subclasse": dict(
        cat="classificacao",
        desc="CNAE 2.0 economic-activity subclass, 7 digits. Joins RAIS, CAGED "
             "and the CNPJ base to the activity description.",
        ref="br_bd_diretorios_brasil.cnae_2",
        notes=["The directory column is called `subclasse`, not "
               "`cnae_2_subclasse`.",
               "`br_me_cnpj.estabelecimentos` calls it `cnae_fiscal_principal` "
               "(plus `cnae_fiscal_secundaria`, a comma-separated list that has "
               "to be `unnest(string_split(...))`-ed before joining).",
               "The directory table is duplicated (2.712 rows for 1.356 "
               "subclasses) — dedupe."],
        example="""WITH cnae AS (SELECT DISTINCT subclasse, descricao_subclasse
              FROM br_bd_diretorios_brasil.cnae_2)
SELECT c.descricao_subclasse, count(*) AS vinculos
FROM br_me_rais.microdados_vinculos v
JOIN cnae c ON v.cnae_2_subclasse = c.subclasse
WHERE v.ano = 2020 AND v.sigla_uf = 'SP'
GROUP BY 1
ORDER BY 2 DESC
LIMIT 20""",
    ),
    "id_natureza_juridica": dict(cat="empresa", desc="Legal-nature code (whether "
                                 "an entity is a municipality, a foundation, an "
                                 "LTDA…). Essential to tell public bodies from "
                                 "private companies in the CNPJ base.",
                                 ref="br_bd_diretorios_brasil.natureza_juridica"),
    "id_cno": dict(cat="empresa", desc="CNO — construction-works registry ID, "
                   "links `br_rf_cno` tables to each other.",
                   ref="br_rf_cno.cnos"),
    # ---------------- person ----------------
    "cpf_cnpj": dict(   # displayed as CPF_CNPJ — the only spelling in the data
        cat="pessoa",
        desc="A single column holding either a CPF or a CNPJ, used by three "
             "scraped enforcement datasets (PGFN debt, BCB penalties, TCU "
             "disqualifications). Tell them apart by digit count after "
             "stripping punctuation: 11 = CPF, 14 = CNPJ.",
        ref="br_me_cnpj.estabelecimentos (for the CNPJ half)",
        notes=[
            "Formats differ per dataset — punctuated in "
            "`br_pgfn_dividaativa.divida` and partly in `br_tcu_inidoneos.*`, "
            "bare digits in `br_bcb_penalidades.penalidades`. Normalize with "
            "`regexp_replace(x, '[^0-9]', '', 'g')` before anything else.",
            "PGFN masks the CPF half (`XXX878.325XX`) — those rows cannot be "
            "joined to a person, only counted.",
        ],
        example="""-- companies with federal debt, resolved against the CNPJ base
WITH devedores AS (
  SELECT DISTINCT regexp_replace("CPF_CNPJ", '[^0-9]', '', 'g') AS doc
  FROM br_pgfn_dividaativa.divida
)
SELECT e.razao_social, e.porte
FROM devedores d
JOIN br_me_cnpj.empresas e ON substr(d.doc, 1, 8) = e.cnpj_basico
WHERE length(d.doc) = 14 AND e.ano = 2025 AND e.mes = 9
LIMIT 20""",
    ),
    "cpf": dict(
        cat="pessoa",
        desc="11-digit individual tax ID.",
        ref="—",
        notes=[
            "Public sources mask it, and they mask it *differently*: the CGU "
            "servidor files keep the middle 6 digits (`***123456**`), "
            "`br_pgfn_dividaativa.divida` stores `XXX878.325XX`. Two datasets "
            "masked the same way can be joined on the masked string; two masked "
            "differently cannot be joined at all.",
            "A masked CPF is not unique — never treat it as a person "
            "identifier on its own. Combine it with a name column before "
            "concluding two rows are the same person.",
        ],
    ),
    "data_nascimento": dict(cat="pessoa", desc="Date of birth. The usual "
                            "disambiguator when a masked CPF is not unique.",
                            ref="—"),
    "cbo_2002": dict(cat="classificacao", desc="Occupation code (CBO 2002). "
                     "Joins RAIS, CAGED and the CNES professional tables.",
                     ref="br_bd_diretorios_brasil.cbo_2002",
                     notes=["Duplicated directory table (5.624 rows for 2.812 "
                            "occupations) — dedupe.",
                            "`cbo_1994` is the previous vintage and is not "
                            "convertible one-to-one."]),
    # ---------------- education ----------------
    "id_escola": dict(
        cat="educacao",
        desc="INEP school code (8 digits). Joins the school census, IDEB, SAEB, "
             "the socioeconomic indicator and the school geolocation.",
        ref="br_bd_diretorios_brasil.escola",
        notes=["Duplicated directory table (436.234 rows for 218.117 schools) "
               "— dedupe.",
               "`br_geobr_mapas.escola` adds latitude/longitude on the same key."],
        example="""WITH esc AS (SELECT DISTINCT id_escola, nome, id_municipio, sigla_uf
             FROM br_bd_diretorios_brasil.escola)
SELECT e.nome, e.sigla_uf, i.ideb
FROM br_inep_ideb.escola i
JOIN esc e USING (id_escola)
WHERE i.ano = 2021 AND i.ensino = 'fundamental'
ORDER BY i.ideb DESC
LIMIT 20""",
    ),
    "id_ies": dict(cat="educacao", desc="Higher-education institution code.",
                   ref="br_bd_diretorios_brasil.instituicao_ensino_superior"),
    "id_curso": dict(cat="educacao", desc="Higher-education course code.",
                     ref="br_bd_diretorios_brasil.curso_superior"),
    "id_inscricao": dict(cat="educacao", desc="ENEM registration ID. Joins the "
                         "microdata to the year's socioeconomic questionnaire.",
                         ref="br_inep_enem.microdados",
                         notes=["Reissued every year — the same person gets a "
                                "different `id_inscricao` in a different `ano`. "
                                "It is **not** a person identifier across years."]),
    "id_aluno": dict(cat="educacao", desc="Student ID inside a survey wave.",
                     ref="—"),
    "id_turma": dict(cat="educacao", desc="Class ID in the school census.",
                     ref="br_inep_censo_escolar.turma"),
    # ---------------- health ----------------
    "id_estabelecimento_cnes": dict(
        cat="saude",
        desc="CNES health-establishment code (7 digits). The spine of the SUS "
             "datasets: it joins CNES's own 18 tables and reaches SIH/SIA "
             "production.",
        ref="br_ms_cnes.estabelecimento",
        notes=["CNES tables are monthly snapshots — join on "
               "`(id_estabelecimento_cnes, ano, mes)` or you get one row per "
               "month.",
               "`br_ms_cnes.estabelecimento` carries `id_municipio_6`, not "
               "`id_municipio`."],
    ),
    "cid_principal_categoria": dict(cat="saude", desc="ICD-10 category (3 "
                                    "characters) of the main diagnosis.",
                                    ref="br_bd_diretorios_brasil.cid_10",
                                    notes=["Directory columns are `categoria` "
                                           "and `subcategoria`; the table is "
                                           "duplicated (24.954 rows for 12.477 "
                                           "codes) — dedupe."]),
    "id_equipe": dict(cat="saude", desc="Primary-care team code (CNES equipe).",
                      ref="br_ms_cnes.equipe"),
    # ---------------- government ----------------
    "id_orgao": dict(cat="governo", desc="Government organ code. In the CGU "
                     "procurement datasets it pairs with `id_orgao_superior`; "
                     "in `br_camara_dados_abertos` it identifies committees.",
                     ref="br_cgu_licitacao_contrato.licitacao"),
    "id_unidade_gestora": dict(cat="governo", desc="Budget management unit "
                               "(UG) code — the level actual spending is "
                               "attributed to.",
                               ref="br_cgu_licitacao_contrato.licitacao"),
    "id_licitacao": dict(cat="governo", desc="Tender ID. Joins the tender to "
                         "its items, participants, empenhos and contracts.",
                         ref="br_cgu_licitacao_contrato.licitacao",
                         example="""SELECT l.objeto, p.nome_participante, i.valor_item
FROM br_cgu_licitacao_contrato.licitacao l
JOIN br_cgu_licitacao_contrato.licitacao_item i USING (id_licitacao)
JOIN br_cgu_licitacao_contrato.licitacao_participante p USING (id_licitacao)
WHERE l.ano = 2023
LIMIT 20"""),
    "id_contrato": dict(cat="governo", desc="Contract ID. Joins contract items, "
                        "amendments (`termo_aditivo`) and apostilamentos.",
                        ref="br_cgu_licitacao_contrato.contrato_compra"),
    "id_empenho": dict(cat="governo", desc="Budget commitment (empenho) ID — "
                       "the link between a tender and money actually committed.",
                       ref="br_cgu_licitacao_contrato.licitacao_empenho"),
    "numero_processo": dict(cat="governo", desc="Administrative process number. "
                            "Free-form text across sources — normalize digits "
                            "before joining.",
                            ref="—"),
    # ---------------- politics ----------------
    "sigla_partido": dict(cat="politica", desc="Party abbreviation. The join "
                          "between electoral results, party affiliation and "
                          "Câmara voting records.",
                          ref="br_tse_eleicoes.partidos",
                          notes=["Parties rename and merge (PMDB→MDB, "
                                 "PSDC→DC). Compare within a single election "
                                 "year, or map through "
                                 "`br_camara_dados_abertos.sigla_partido`."]),
    "id_deputado": dict(cat="politica", desc="Câmara dos Deputados member ID. "
                        "Joins the member to expenses, votes, committees and "
                        "parliamentary fronts.",
                        ref="br_camara_dados_abertos.deputado"),
    # ---------------- classification ----------------
    "id_ncm": dict(cat="classificacao", desc="Mercosur product code (8 digits). "
                   "The join key for foreign-trade data.",
                   ref="br_bd_diretorios_mundo.nomenclatura_comum_mercosul"),
    "id_sh4": dict(cat="classificacao", desc="Harmonized System heading (4 "
                   "digits) — the aggregation level above NCM.",
                   ref="br_bd_diretorios_mundo.sistema_harmonizado"),
    "cnae_1": dict(cat="classificacao", desc="CNAE 1.0 activity code — the "
                   "pre-2007 vintage, still used by older RAIS files.",
                   ref="br_bd_diretorios_brasil.cnae_1"),
}

# ---------------------------------------------------------------------------
# Bridges: columns that mean the same thing under a different name/format.
# `verificado` records what the recipe matched when run on beelink.
# ---------------------------------------------------------------------------

MUNICIPIO_BRIDGES = [
    dict(tabela="br_ms_sipni_doses_historicas.doses_agregadas", coluna="MUNIC",
         formato="7-digit IBGE code. This table lives *inside* "
                 "`basedosdados.duckdb`, not as parquet, so it is absent from "
                 "the table lists in this file",
         recipe="MUNIC = m.id_municipio", verificado="direct"),
    dict(tabela="br_tesouro_capag.municipios", coluna='"Código Município Completo"',
         formato="7-digit IBGE code",
         recipe='CAST("Código Município Completo" AS VARCHAR) = m.id_municipio',
         verificado="11.136 of 11.142 directory rows"),
    dict(tabela="br_mjsp_sinesp.ocorrencias", coluna='"cód_ibge"',
         formato="7-digit IBGE code stored as BIGINT",
         recipe='CAST("cód_ibge" AS VARCHAR) = m.id_municipio',
         verificado="22 municipalities — the table is a partial scrape (823 rows)"),
    dict(tabela="br_tce_pi.prefeituras", coluna="codIBGE",
         formato="7-digit IBGE code",
         recipe="CAST(codIBGE AS VARCHAR) = m.id_municipio", verificado="direct"),
    dict(tabela="br_transferegov.programas / planos_acao",
         coluna="codigo_ibge_fundo_programa, codigo_ibge_municipio_ente_recebedor_plano_acao, …",
         formato="7-digit IBGE code",
         recipe="CAST(codigo_ibge_… AS VARCHAR) = m.id_municipio", verificado="direct"),
    dict(tabela="br_trase_supply_chain.soy_beans / beef",
         coluna="municipality_id_production, municipality_id_logistics_hub",
         formato="7-digit IBGE code",
         recipe="CAST(municipality_id_production AS VARCHAR) = m.id_municipio",
         verificado="4.992 rows matched"),
    dict(tabela="br_mjsp_sisdepen.populacao_carceraria", coluna="codigo_ibge",
         formato="7-digit IBGE code written as a float string (`2927408.0`)",
         recipe="lpad(CAST(CAST(codigo_ibge AS DOUBLE) AS BIGINT)::VARCHAR, 7, '0') = m.id_municipio",
         verificado="2.328 rows matched"),
    dict(tabela="br_ms_sinan_violencia.microdados_violencia", coluna="ID_MUNICIP",
         formato="6-digit IBGE code",
         recipe="CAST(\"ID_MUNICIP\" AS VARCHAR) = m.id_municipio_6",
         verificado="10.970 rows matched"),
    dict(tabela="br_saude_farmaciapopular.estabelecimentos", coluna="codigo_municipio",
         formato="6-digit IBGE code",
         recipe="CAST(codigo_municipio AS VARCHAR) = m.id_municipio_6",
         verificado="direct"),
    dict(tabela="br_ms_sinan.microdados_influenza_srag / dengue",
         coluna="id_municipio_6_residencia, id_municipio_6_notificacao",
         formato="6-digit code written as a float string (`261640.0`)",
         recipe="lpad(CAST(CAST(x AS DOUBLE) AS BIGINT)::VARCHAR, 6, '0') = m.id_municipio_6",
         verificado="10.834 rows matched (ano = 2022)"),
    dict(tabela="br_ibge_censo2022_raca.* / br_ibge_censo2022_religiao.*",
         coluna="municipio",
         formato="name + UF in parentheses: `Alta Floresta D'Oeste (RO)`",
         recipe="upper(strip_accents(regexp_extract(municipio, '^(.*) \\(', 1))) = upper(strip_accents(m.nome))\n"
                "  AND regexp_extract(municipio, '\\(([A-Z]{2})\\)$', 1) = m.sigla_uf",
         verificado="11.096 of 11.142 directory rows"),
    dict(tabela="br_cgu_garantia_safra / pe_de_meia / seguro_defeso",
         coluna="nome_municipio + uf (SIAFI code has no crosswalk)",
         formato="upper-case name, unaccented",
         recipe="upper(strip_accents(nome_municipio)) = upper(strip_accents(m.nome)) AND uf = m.sigla_uf",
         verificado="2.642 name/UF pairs"),
    dict(tabela="br_comprasgov_sicaf.fornecedores", coluna="nomeMunicipio + ufSigla",
         formato="mixed-case accented name", recipe="upper(strip_accents(nomeMunicipio)) = upper(strip_accents(m.nome)) AND ufSigla = m.sigla_uf",
         verificado="name-based"),
    dict(tabela="br_anp_combustiveis.precos", coluna="municipio + estado",
         formato="upper-case unaccented name; `estado` is the full state name "
                 "(`RONDONIA`), `-` when missing",
         recipe="upper(strip_accents(municipio)) = upper(strip_accents(m.nome)) — pair with the `estado` bridge listed under `sigla_uf`",
         verificado="name-based"),
    dict(tabela="br_tce_sp.municipios", coluna="municipio / municipio_extenso",
         formato="`municipio` is a slug (`aguas-de-lindoia`), `municipio_extenso` "
                 "the display name",
         recipe="use municipio_extenso: upper(strip_accents(municipio_extenso)) = upper(strip_accents(m.nome)) AND m.sigla_uf = 'SP'",
         verificado="name-based"),
    dict(tabela="br_tce_es.obras_publicas", coluna="Municipio",
         formato="mixed-case accented name",
         recipe='upper(strip_accents("Municipio")) = upper(strip_accents(m.nome)) AND m.sigla_uf = \'ES\'',
         verificado="name-based"),
    dict(tabela="br_cnpq_bolsas.microdados", coluna="municipio_destino",
         formato="upper-case accented name",
         recipe="upper(strip_accents(municipio_destino)) = upper(strip_accents(m.nome))",
         verificado="name-based; ambiguous without a UF column"),
    dict(tabela="br_saude_bps.dados", coluna='"nome_do_munica\u00adpio_da_instituicao"',
         formato="upper-case unaccented name. **The column name itself contains a "
                 "soft hyphen (U+00AD)** — copy it verbatim and keep the quotes",
         recipe='upper(strip_accents("nome_do_munica\u00adpio_da_instituicao")) = upper(strip_accents(m.nome))',
         verificado="name-based"),
    dict(tabela="br_siop_orcamento.localizadores", coluna='"MunicÃ­pio"',
         formato="mojibake — the file was decoded as latin-1 twice, in the values "
                 "*and* in the column name",
         recipe="fix first: upper(strip_accents(decode(encode(\"MunicÃ­pio\"), 'utf-8')))",
         verificado="needs re-encoding, join not reliable as stored"),
    dict(tabela="br_ana_telemetria.estacoes", coluna="MunicipioCodigo / nmMunicipio",
         formato="`MunicipioCodigo` is an **ANA internal code, not IBGE** "
                 "(`3041000` = Tabatinga); the table also has foreign rows "
                 "(`PERU`)",
         recipe="join by name: upper(strip_accents(nmMunicipio)) = upper(strip_accents(m.nome)) AND nmEstado matched to the UF name",
         verificado="name-based only"),
    dict(tabela="br_tcu_inidoneos.*", coluna="MUNICIPIO",
         formato="mostly empty string", recipe="unusable — join via UF, or via "
                 "CPF_CNPJ to the CNPJ base and take the municipality from there",
         verificado="empty in the sampled rows"),
    dict(tabela="br_ok_queridodiario.diarios", coluna="territory_id",
         formato="7-digit IBGE code — Querido Diário's `territory` *is* the "
                 "municipality",
         recipe="CAST(territory_id AS VARCHAR) = m.id_municipio",
         verificado="524 of 524 distinct codes"),
    dict(tabela="br_brasilapi.ddd_cidades", coluna="city + state",
         formato="upper-case accented name",
         recipe="upper(strip_accents(city)) = upper(strip_accents(m.nome)) AND state = m.sigla_uf",
         verificado="5.449 of 5.565 rows"),
    dict(tabela="br_tce_rj.contratos_municipio / contratos_estado", coluna='"Ente"',
         formato="upper-case municipality name, RJ only",
         recipe='upper(strip_accents("Ente")) = upper(strip_accents(m.nome)) AND m.sigla_uf = \'RJ\'',
         verificado="90 of 91 distinct names"),
    dict(tabela="br_me_cnpj.estabelecimentos", coluna="id_municipio_rf",
         formato="Receita Federal 4-digit code",
         recipe="id_municipio_rf = m.id_municipio_rf",
         verificado="11.140 of 11.142 directory rows"),
]

UF_BRIDGES = [
    ("br_mj_consumidorgovbr.reclamacoes", '"UF"', "2-letter code — direct join to `sigla_uf`"),
    ("br_tcu_inidoneos.*", '"UF"', "2-letter code — direct"),
    ("br_mjsp_ckan.procon", '"UF"', "2-letter code — direct"),
    ("br_ms_sipni_doses_historicas.doses_agregadas", '"UF"', "2-letter code — direct"),
    ("br_caixa_sinapi.insumos", "uf", "2-letter code — direct"),
    ("br_cgu_garantia_safra / pe_de_meia / seguro_defeso", "uf", "2-letter code — direct"),
    ("br_fbsp_absp.violencia_escola", "uf", "2-letter code — direct"),
    ("br_mjsp_sinesp.ocorrencias_uf", "uf", "2-letter code — direct"),
    ("br_comprasgov_sicaf.fornecedores", "ufSigla", "2-letter code — direct"),
    ("br_ms_sinan_violencia.microdados_violencia", '"SG_UF"',
     "**numeric IBGE code** (21, 52…), joins `id_uf`, not `sigla_uf`"),
    ("br_saude_farmaciapopular.estabelecimentos", "codigo_uf",
     "numeric IBGE code — joins `id_uf`"),
    ("br_mjsp_sisdepen.populacao_carceraria", "uf",
     "`Acre (AC)` — extract with `regexp_extract(uf, '\\(([A-Z]{2})\\)$', 1)`"),
    ("br_anp_combustiveis.precos", "estado",
     "full state name, unaccented upper case (`RONDONIA`); `-` when missing"),
    ("br_mjsp_procurados.procurados", "estado",
     "full state name (`GOIAS`, `PARÁ`) — accents inconsistent. `nome_estado` "
     "in the same table is **not** a state: it holds the person's name plus the "
     "state, mislabeled at the source"),
    ("br_siop_orcamento.localizadores", '"UF"',
     "full state name, mojibake (`EspÃ­rito Santo`)"),
    ("br_ana_telemetria.estacoes", "EstadoCodigo / nmEstado",
     "ANA internal code plus the full state name; not IBGE"),
    ("br_ok_queridodiario.diarios", "state_code", "2-letter code — direct"),
    ("br_datahackers_state_data.microdados", "p1_i_1",
     "2-letter code — direct. Every column in this survey is a question code: "
     "`p1_i` is `São Paulo (SP)`, `p1_i_2` and `p1_k` the macro-region, "
     "`p1_i_1` the bare UF"),
    ("br_brasilapi.ddd_cidades", "state", "2-letter code — direct"),
]

IDENTITY_BRIDGES = [
    ("br_comprasgov_sicaf.fornecedores", "cnpj / cpf",
     "14-digit zero-padded — joins `br_me_cnpj.estabelecimentos.cnpj` directly. "
     "`cpf` is populated for individual suppliers."),
    ("br_bcb_penalidades.penalidades", '"CPF_CNPJ"',
     "14 bare digits for companies — direct join after `lpad(...,14,'0')`."),
    ("br_pgfn_dividaativa.divida", '"CPF_CNPJ"',
     "CNPJs are punctuated (`17.533.474/0001-00`) → strip with "
     "`regexp_replace(x, '[^0-9]', '', 'g')`. CPFs are masked (`XXX878.325XX`) "
     "and cannot be joined."),
    ("br_tcu_inidoneos.*", '"CPF_CNPJ"',
     "mixed: some rows punctuated, some bare. Normalize with "
     "`lpad(regexp_replace(x, '[^0-9]', '', 'g'), 14, '0')`."),
    ("br_anp_combustiveis.precos", "cnpj",
     "unpadded — 1.03M rows have 13 characters, 875k have 14. Always "
     "`lpad(..., 14, '0')`."),
    ("br_brasilio_holdings.holdings", "cnpj",
     "stored as BIGINT, leading zeros lost: "
     "`lpad(CAST(cnpj AS VARCHAR), 14, '0')`."),
    ("br_cvm_administradores_carteira.pessoa_juridica", "cnpj",
     "14 bare digits — direct."),
    ("br_cvm_fundos.fundos", '"CNPJ_FUNDO" / "CNPJ_ADMIN"',
     "punctuated — strip with `regexp_replace(x, '[^0-9]', '', 'g')`; yields "
     "41.106 distinct 14-digit CNPJs."),
    ("br_tce_rj.contratos_*", '"CNPJCPFContratado" / "CPFCNPJ"',
     "punctuated, and holds either a CPF or a CNPJ — strip, then branch on "
     "`length()` (11 vs 14)."),
    ("br_mdr_snis.prestador_agua_esgoto", "id_prestador",
     "SNIS operator code; the first 6 digits are the `id_municipio_6` of the "
     "operator's seat."),
]

# ---------------------------------------------------------------------------
# Auto-discovery
# ---------------------------------------------------------------------------

KEYISH = re.compile(
    r"^(id_|cod|cnpj|cpf|sigla|nome_|chave|nu_|cd_|co_|cnae|cbo|ncm|cid_|cep|"
    r"ano|mes|data|trimestre|semestre|year|month|date|matricula|inscricao|registro)",
    re.I,
)


def load_schema():
    if not SRC.exists():
        sys.exit(f"{SRC} not found — run scripts/gera_schemas.py first.")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    return data["_meta"], data["tables"]


def index_columns(tables):
    """lower(column) -> {tables, datasets, types, spellings}

    Keyed case-insensitively on purpose: DuckDB resolves unquoted identifiers
    that way, so `ano` and `Ano` are the same join key in practice — and
    `mcp_server` indexes this file by lowercased column name, so emitting both
    as separate sections would make one silently shadow the other.
    """
    idx = defaultdict(lambda: {"tables": [], "datasets": set(), "types": Counter(),
                               "spellings": Counter(),
                               "type_tables": defaultdict(list)})
    for tid, meta in tables.items():
        dataset = tid.split(".", 1)[0]
        for col in meta.get("columns", []):
            entry = idx[col["name"].lower()]
            typ = TYPE_MAP.get(col.get("type", ""), col.get("type", "?"))
            entry["tables"].append(tid)
            entry["datasets"].add(dataset)
            entry["types"][typ] += 1
            entry["type_tables"][typ].append(tid)
            entry["spellings"][col["name"]] += 1
    return idx


def probe_duplicated_tables():
    """Table dirs on beelink holding a leftover tmp*.parquet from an aborted sync.

    Both the generated DuckDB views and any `*.parquet` glob read the leftover
    alongside the real export, so those tables return every row twice.
    """
    cmd = ["ssh", BEELINK_HOST,
           f"find {BEELINK_ROOT} -maxdepth 3 -name 'tmp*.parquet' -printf '%h\\n'"]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    except Exception as exc:                                  # noqa: BLE001
        print(f"  ! duplicate probe failed: {exc}", file=sys.stderr)
        return None
    if out.returncode != 0:
        print(f"  ! duplicate probe failed: {out.stderr.strip()[:200]}", file=sys.stderr)
        return None
    prefix = BEELINK_ROOT.rstrip("/") + "/"
    dirs = sorted(
        line[len(prefix):].replace("/", ".", 1)
        for line in out.stdout.split("\n") if line.startswith(prefix)
    )
    return dirs


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def auto_desc(col):
    """One line for an auto-detected key, from the shape of its name.

    Most of the long tail is a hub key wearing a role suffix — saying which hub
    it resolves to is the whole value of listing it.
    """
    if col in ("chave", "id_tabela", "nome_coluna"):
        return ("Part of the `dicionario` composite key "
                "`(id_tabela, nome_coluna, chave) -> valor` that decodes coded "
                "columns inside a dataset — see gotcha 6 at the top of this file.")
    if col.startswith("id_municipio"):
        return ("Role-qualified `id_municipio` — same 7-digit IBGE code, joins "
                "`br_bd_diretorios_brasil.municipio` directly.")
    if col.startswith("sigla_uf"):
        return "Role-qualified `sigla_uf` — same two-letter state code."
    if col.startswith("cpf"):
        return ("A CPF under a role name — see `cpf` for the masking caveats "
                "before joining on it.")
    if col.startswith("cnpj") or col.startswith("cpf_cnpj"):
        return "A CNPJ under a role name — normalize as described under `cnpj`."
    if col.startswith("cnae"):
        return "A CNAE activity code — decode with `br_bd_diretorios_brasil.cnae_2`."
    if col.startswith("cid_"):
        return "An ICD-10 code — decode with `br_bd_diretorios_brasil.cid_10`."
    if col.startswith(("data_", "ano_", "mes_")):
        return "Date/period column. Shared name, but check the type before joining."
    if col.startswith("nome_"):
        return "Name column — usable as a fallback key after `upper(strip_accents(...))`."
    if col.startswith("id_"):
        return "Identifier shared across datasets."
    return "Shared column that looks like a key."


def fmt_types(types, type_tables):
    """`VARCHAR` in 321 tables · `BIGINT` in 1 (br_x.y) — the odd one out named.

    A single table storing the shared key under a different type is exactly the
    join that silently returns nothing, so it is worth naming.
    """
    ranked = types.most_common()
    parts = []
    for typ, n in ranked:
        part = f"`{typ}` in {n} table{'s' if n != 1 else ''}"
        if len(ranked) > 1 and n <= 3:
            part += " (" + ", ".join(f"`{t}`" for t in sorted(type_tables[typ])) + ")"
        parts.append(part)
    text = " · ".join(parts)
    if len(ranked) > 1:
        text += " — **cast explicitly when joining across them**"
    return text


def render_key(col, info, curated, level=3):
    """One `### \\`col\\` — N tables` section."""
    tables, datasets = info["tables"], sorted(info["datasets"])
    max_tables = 24 if curated else 12
    out = [f"{'#' * level} `{col}` — {len(tables)} table{'s' if len(tables) != 1 else ''}", ""]
    if curated:
        out += [curated["desc"], ""]
        ref = curated.get("ref")
        if ref:
            out.append(f"**Reference table:** {ref if ref.startswith('—') else '`' + ref + '`'}")
            out.append("")
    else:
        out += [auto_desc(col.lower()), ""]
    others = [s for s, _ in info["spellings"].most_common()[1:]]
    if others:
        out.append("**Also spelled:** " + ", ".join(f"`{s}`" for s in others)
                   + " — the same key; DuckDB matches unquoted identifiers "
                     "case-insensitively.")
        out.append("")
    out.append(f"**Type:** {fmt_types(info['types'], info['type_tables'])}")
    out.append("")
    out.append(f"**Datasets ({len(datasets)}):** " + ", ".join(f"`{d}`" for d in datasets))
    out.append("")
    shown = tables if len(tables) <= max_tables else tables[:max_tables]
    label = ("**Tables:** " if len(tables) <= max_tables
             else f"**Tables (first {max_tables} of {len(tables)}):** ")
    out.append(label + ", ".join(f"`{t}`" for t in shown))
    out.append("")
    for note in (curated or {}).get("notes", []):
        out.append(f"- {note}")
    if (curated or {}).get("notes"):
        out.append("")
    if (curated or {}).get("example"):
        out += ["```sql", curated["example"], "```", ""]
    return out


def render(meta, tables, idx, duplicated):
    total_tables = len(tables)
    total_datasets = len({t.split(".", 1)[0] for t in tables})
    curated_cols = {c for c in CURATED if c in idx}
    auto_cols = {
        c for c, i in idx.items()
        if c not in curated_cols
        and len(i["datasets"]) >= MIN_DATASETS
        and KEYISH.match(c)
        and c not in AUTO_DENY
        and not re.fullmatch(r"v\d{3}", c)
    }
    # display name = the spelling most tables use
    display = {c: idx[c]["spellings"].most_common(1)[0][0]
               for c in curated_cols | auto_cols}
    documented = curated_cols | auto_cols

    L = [
        "# Join Key Reference",
        "",
        f"How the {total_tables} tables of the mirror connect to each other: the "
        f"columns they share, the columns that mean the same thing under a "
        f"different name, and the conversion each one needs.",
        "",
        f"Generated by `scripts/gera_join_keys.py` from `schemas.json` "
        f"({total_datasets} datasets, {total_tables} tables, "
        f"{date.today().isoformat()}). Do not edit by hand — regenerate.",
        "",
        f"{len(documented)} join columns documented: {len(curated_cols)} curated, "
        f"{len(auto_cols)} auto-detected (shared by {MIN_DATASETS}+ datasets), "
        f"plus {len(MUNICIPIO_BRIDGES)} municipality bridges, {len(UF_BRIDGES)} "
        f"UF bridges and {len(IDENTITY_BRIDGES)} CNPJ/CPF bridges for sources "
        f"that name the key differently.",
        "",
        "## Read this before joining anything",
        "",
    ]

    if duplicated:
        dup_dirs = ", ".join(f"`{d}`" for d in duplicated)
        L += [
            f"**1. {len(duplicated)} tables return every row twice.** An aborted "
            "sync left a `tmp*.parquet` next to the real export, and both the "
            "generated views and any `*.parquet` glob read both files. This hits "
            "almost the whole `br_bd_diretorios_brasil` directory — the tables "
            "this file tells you to join against:",
            "",
            "| table | rows | distinct keys |",
            "|---|---|---|",
            "| `br_bd_diretorios_brasil.municipio` | 11.142 | 5.571 |",
            "| `br_bd_diretorios_brasil.uf` | 54 | 27 |",
            "| `br_bd_diretorios_brasil.escola` | 436.234 | 218.117 |",
            "| `br_bd_diretorios_brasil.cid_10` | 24.954 | 12.477 |",
            "| `br_bd_diretorios_brasil.cbo_2002` | 5.624 | 2.812 |",
            "| `br_bd_diretorios_brasil.cnae_2` | 2.712 | 1.356 |",
            "",
            "It is not only a join problem: fact tables are in the list too "
            "(`br_anatel_banda_larga_fixa.densidade_municipio`, "
            "`br_bndes_operacoes_contratadas.operacoes_nao_automaticas`, most "
            "of `br_camara_dados_abertos`), so a plain `count(*)` or `sum()` on "
            "those is already doubled. The affected names run alphabetically "
            "from `br_abrinq_oca` to `br_camara_dados_abertos`, which is what an "
            "interrupted sync looks like.",
            "",
            "Until the leftovers are removed, join against a deduped subquery "
            "(`SELECT DISTINCT …`) — every example in this file does. "
            "`br_bd_diretorios_brasil.cep` is *not* affected.",
            "",
            f"<details><summary>All {len(duplicated)} affected tables</summary>",
            "",
            dup_dirs,
            "",
            "</details>",
            "",
        ]
    else:
        L += [
            "**1. Check for duplicated tables.** An aborted sync can leave a "
            "`tmp*.parquet` next to the real export, and both the views and any "
            "`*.parquet` glob then read both files, returning every row twice. "
            "This probe did not run for this build "
            "(`find ~/rodado -name 'tmp*.parquet'` on beelink lists them).",
            "",
        ]

    L += [
        "**2. `br_bd_diretorios_brasil.empresa` is empty** (0 rows). It used to "
        "be this file's CNPJ reference. Use `br_me_cnpj.estabelecimentos` "
        "(14-digit `cnpj`, one row per branch) or `br_me_cnpj.empresas` "
        "(8-digit `cnpj_basico`, one row per company).",
        "",
        "**3. Codes are strings.** `id_municipio`, `cnpj`, `cep` and friends are "
        "VARCHAR with meaningful leading zeros. A source that stored them as a "
        "number (or as a float — `2927408.0`) has to be padded back before it "
        "will match. Every bridge below states the exact expression.",
        "",
        "**4. Filter partitions first.** `ano`, `mes` and `sigla_uf` are the "
        "partition columns; a join without them scans the whole table.",
        "",
        "**5. Six datasets have no view** in `basedosdados.duckdb` — "
        "`br_cgu_garantia_safra`, `br_cgu_pe_de_meia`, `br_cgu_seguro_defeso`, "
        "`br_cgu_viagens`, `br_ibama_embargos`, `br_mjsp_sisdepen`. Read them "
        "with `read_parquet('~/rodado/<dataset>/<table>/*.parquet')`. "
        "`br_ms_sipni_*` and `politicos` are the opposite case: native tables "
        "inside the `.duckdb` file with no parquet directory.",
        "",
        "**6. Every dataset with coded columns carries a `dicionario` table** "
        f"({sum(1 for t in tables if t.endswith('.dicionario'))} of them). It "
        "decodes any coded column of that dataset:",
        "",
        "```sql",
        "SELECT c.chave, c.valor, count(*)",
        "FROM br_me_caged.microdados_movimentacao m",
        "JOIN br_me_caged.dicionario c",
        "  ON c.id_tabela = 'microdados_movimentacao'",
        " AND c.nome_coluna = 'tipo_movimentacao'",
        " AND c.chave = CAST(m.tipo_movimentacao AS VARCHAR)",
        "WHERE m.ano = 2023",
        "GROUP BY 1, 2",
        "```",
        "",
    ]

    # ---- sections by category
    by_cat = defaultdict(list)
    for col in curated_cols:
        by_cat[CURATED[col].get("cat", "outros")].append(col)
    for col in auto_cols:
        by_cat["outros"].append(col)

    for cat, title, blurb in CATEGORIES:
        cols = sorted(by_cat.get(cat, []),
                      key=lambda c: (-len(idx[c]["tables"]), c))
        if not cols:
            continue
        L += [f"## {title}", "", blurb, ""]

        # `mcp_server.get_join_keys()` slices from one h3 to the next, so a
        # bridge table has to sit inside the section of the key it belongs to:
        # emitted right after that column, never at the end of the category.
        for col in cols:
            L += render_key(display[col], idx[col], CURATED.get(col))
            if col == "id_municipio":
                L += render_municipio_bridges()
            elif col == "sigla_uf":
                L += render_bridge_table(
                    "Same key, other names — UF",
                    ["table", "column", "format / conversion"],
                    [(f"`{t}`", f"`{c}`", d) for t, c, d in UF_BRIDGES],
                )
            elif col == "cnpj":
                L += render_bridge_table(
                    "Same key, other names — CNPJ / CPF",
                    ["table", "column", "format / conversion"],
                    [(f"`{t}`", f"`{c}`", d) for t, c, d in IDENTITY_BRIDGES],
                )

    return "\n".join(L).rstrip() + "\n"


def render_municipio_bridges():
    rows = [
        (f"`{b['tabela']}`", f"`{b['coluna']}`", b["formato"],
         f"`{b['recipe']}`" if "\n" not in b["recipe"] and not b["recipe"].startswith("unusable")
         else b["recipe"], b["verificado"])
        for b in MUNICIPIO_BRIDGES
    ]
    out = [
        "### Municipality columns under another name",
        "",
        "Sources scraped outside Base dos Dados rarely use `id_municipio`. Each "
        "row below is the expression that brings that column back to the "
        "directory (aliased `m`, and deduped — see gotcha 1). *verified* is what "
        "the expression actually matched when it was run on beelink; those are "
        "joined-row counts against the duplicated directory, so roughly twice "
        "the municipality count.",
        "",
        "| table | column | stored as | join expression | verified |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        cells = [c.replace("|", "\\|").replace("\n", "<br>") for c in r]
        out.append("| " + " | ".join(cells) + " |")
    out += [
        "",
        "Role-qualified municipality columns (same 7-digit IBGE code, different "
        "meaning) join to `id_municipio` directly — pick the one that answers "
        "the question:",
        "",
        "| dataset | columns |",
        "|---|---|",
        "| `br_ms_sim.microdados` | `id_municipio_residencia`, `id_municipio_ocorrencia`, `id_municipio_naturalidade`, `id_municipio_svo_iml` |",
        "| `br_ms_sinasc.microdados` | `id_municipio_residencia`, `id_municipio_nascimento`, `id_municipio_mae` |",
        "| `br_ms_sinan.microdados_dengue` | `id_municipio_notificacao`, `id_municipio_residencia`, `id_municipio_infeccao`, `id_municipio_internacao` |",
        "| `br_ms_sih.aihs_reduzidas` | `id_municipio_paciente`, `id_municipio_estabelecimento`, `id_municipio_gestor` |",
        "| `br_ms_sia.psicossocial` | `id_municipio_residencia_paciente` |",
        "| `br_inep_enem.microdados` | `id_municipio_residencia`, `id_municipio_escola`, `id_municipio_prova` |",
        "| `br_mec_sisu.microdados` | `id_municipio_candidato`, `id_municipio_campus` |",
        "| `br_me_rais.microdados_vinculos` | `id_municipio_trabalho` |",
        "| `br_cgu_emendas_parlamentares.microdados` | `id_municipio_gasto` |",
        "| `br_camara_dados_abertos.deputado` | `id_municipio_nascimento` |",
        "| `br_tse_eleicoes.receitas_*` | `id_municipio_tse_doador`, `id_municipio_tse_fornecedor` (TSE numbering) |",
        "| `br_bd_vizinhanca.municipio` | `id_municipio_1`, `id_municipio_2` — the adjacency pair |",
        "",
    ]
    return out


def render_bridge_table(title, headers, rows):
    out = [f"### {title}", "", "| " + " | ".join(headers) + " |",
           "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(c.replace("|", "\\|") for c in r) + " |")
    out.append("")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-probe", action="store_true",
                    help="skip the ssh check for duplicated (tmp*.parquet) tables")
    args = ap.parse_args()

    meta, tables = load_schema()
    idx = index_columns(tables)
    duplicated = None if args.no_probe else probe_duplicated_tables()

    DST.write_text(render(meta, tables, idx, duplicated), encoding="utf-8")

    print(f"{DST.relative_to(REPO)}")
    print(f"  source   : schemas.json ({meta.get('total_tables')} tables)")
    print(f"  sections : {sum(1 for line in DST.read_text().split(chr(10)) if line.startswith('### `'))}")
    if duplicated is not None:
        print(f"  duplicated tables on beelink: {len(duplicated)}")
    print(f"  size     : {DST.stat().st_size / 1024:.1f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
