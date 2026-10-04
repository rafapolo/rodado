#!/usr/bin/env python3
"""Extract CNPJ establishment points, precisely geolocated via CNEFE, for all 27 UFs.

Every active CNPJ establishment (br_me_cnpj.estabelecimentos, latest monthly
snapshot) is matched to a real building address in the 2022 census address
registry (br_ibge_censo_2022.cadastro_enderecos). Matching, in order:
  1. Exact (cep, street name, house number) after accent/article normalization.
  2. Same street, but the house number isn't in CNEFE — interpolate its position
     between the nearest known numbers below/above on that street (or use the
     nearest single known edge), trusted only within INTERP_MAX_GAP numbers.
  3. Street name itself isn't in CNEFE for that CEP — fuzzy-match it (Jaro-Winkler,
     CEP is trusted as the anchor so a CEP's handful of candidate streets is a safe
     search space) against CNEFE streets in the same CEP, then interpolate as above.
  Then, for what is still out, a second pass that always demands the exact
  house number (or lot), so every point it adds is a real CNEFE address
  (see SEGUNDA_PASSADA_SQL; rules learned from ArcGIS's exact-address answers):
  B. same CEP, full street name — CNEFE's title column (PROFESSORA, CORONEL…)
     joined to the name, Receita abbreviations spelled out, "(CJ …)" dropped;
  C. same CEP, both names without titles;
  D. same municipality, full name, CEP ignored (the Receita's is often a
     neighbour's, outdated, or a big-user CEP);
  E. same municipality and CEP5, names without titles;
  F. same municipality and CEP5, names without titles within Jaro-Winkler 0.92;
  G. block-and-lot addresses (DF's "QNP 14 CONJUNTO E" + LOTE 22, Goiânia's
     "QD 12 LT 5"): same CEP, same block name, same lot;
  H. no number or lot, but the name is a single building: every CNEFE address
     under it, in that CEP, sits within ~50 m ("SQN 411 BLOCO I").
  Candidates more than ~50 m apart are ambiguous and the row is dropped.
Establishments with no address resolvable this way are dropped — no CEP- or
street-centroid fallback. Matched establishments collapsing onto the same resolved coordinate are
combined into a single weighted point.

Standalone: pure stdlib, no AI/internet dependency beyond `ssh beelink` (or
--local against a local DuckDB file) — safe to re-run later via cron.

Usage:
  python scripts/extrai_estados_cnpj.py                 # via SSH beelink
  python scripts/extrai_estados_cnpj.py --local          # local DuckDB file
  BEELINK_HOST=custom-host python scripts/extrai_estados_cnpj.py

Output:
  docs/pesquisa/viz-uf/dados/<uf>.bin.gz     # binary point cloud, per UF
  docs/pesquisa/viz-uf/dados/meta.json       # { uf: {n_points, n_estab_ativos, n_estab_geolocalizados, bbox} }
  docs/pesquisa/viz-uf/generate_uf_map.md    # per-UF geolocation coverage stats report
"""

import array
import gzip
import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

DADOS_DIR = Path("docs/pesquisa/viz-uf/dados")
REPORT_PATH = Path("docs/pesquisa/viz-uf/generate_uf_map.md")
BEELINK = os.environ.get("BEELINK_HOST", "beelink")
DB_PATH = os.environ.get("DB_PATH", "~/rodado/basedosdados.duckdb")

# Struct-of-arrays layout, not array-of-structs: all n lngs (f32), then all n
# lats (f32), then all n weights (u16) — three homogeneous, contiguous, aligned
# blocks instead of interleaved 10-byte records. Record-level interleaving
# can't be read back as a zero-copy typed array in JS (10 isn't a multiple of
# 4, so most records start at a misaligned offset for Float32Array); SoA lets
# the browser read each block directly as a typed-array view with no parsing
# loop. `array.array` uses native byte order, which is little-endian on every
# real deployment target (x86/ARM) and matches the JS side's `true` (little-
# endian) DataView/TypedArray reads. Since RAW2 the file opens with b"RAW2" and
# u32 n, and a fourth block of n u8 years-since-1900 follows the weights.
# RAW3 adds a fifth block: n u32 masks, bit k set when the address has at
# least one establishment in CNAE section SECOES[k] (A..U).
def write_points_soa(path, pontos):
    lngs = array.array("f", (p["lng"] for p in pontos))
    lats = array.array("f", (p["lat"] for p in pontos))
    weights = array.array("H", (min(p["weight"], 65535) for p in pontos))
    # Year the point's oldest establishment opened, as years since 1900 (the
    # query floors it at 1900; DuckDB data tops out well under 1900 + 255).
    years = array.array("B", (min(max(p["yr"] - 1900, 0), 255) for p in pontos))
    masks = array.array("I", (p["mask"] for p in pontos))
    assert masks.itemsize == 4
    with gzip.open(path, "wb", compresslevel=9) as f:
        # RAW2 header: the legacy layout had none and was told apart from this
        # one by length alone, which is ambiguous once a fourth block exists.
        f.write(b"RAW3" + struct.pack("<I", len(pontos)))
        f.write(lngs.tobytes())
        f.write(lats.tobytes())
        f.write(weights.tobytes())
        f.write(years.tobytes())
        f.write(masks.tobytes())


def ssh_duckdb(sql):
    cmd = ["ssh", BEELINK, f"~/bin/duckdb -json {DB_PATH}"]
    proc = subprocess.run(cmd, input=sql.encode(), capture_output=True, timeout=7200)
    if proc.returncode != 0:
        raise RuntimeError(f"SSH/DuckDB failed:\n{proc.stderr.decode()}")
    return proc.stdout


def local_duckdb(sql):
    proc = subprocess.run(
        ["duckdb", DB_PATH, "-json"], input=sql.encode(), capture_output=True, timeout=7200
    )
    if proc.returncode != 0:
        raise RuntimeError(f"DuckDB failed:\n{proc.stderr.decode()}")
    return proc.stdout


def run_query(sql, use_ssh=True):
    raw = (ssh_duckdb if use_ssh else local_duckdb)(sql)
    text = raw.decode().strip()
    if not text:
        return []
    return json.loads(text)


UF_LIST_SQL = """
SET enable_progress_bar = false;
SELECT DISTINCT sigla_uf AS uf
FROM br_me_cnpj.estabelecimentos
WHERE situacao_cadastral = '2'
  AND sigla_uf IS NOT NULL AND sigla_uf != '' AND sigla_uf != 'EX'
  AND (ano * 100 + mes) = (SELECT MAX(ano * 100 + mes) FROM br_me_cnpj.estabelecimentos)
ORDER BY uf;
"""

# CNAE 2.0 sections, A..U, by the division (first two digits of the 7-digit
# subclass). Every division in the data falls in one (checked 2026-10-04 on
# snapshot 202509: 87 divisions, no null or short code). lpad guards against a
# dropped leading zero sending section A (01-03) elsewhere.
SECOES = "ABCDEFGHIJKLMNOPQRSTU"
SECAO_SQL = """CASE
      WHEN d <= 3 THEN 0 WHEN d <= 9 THEN 1 WHEN d <= 33 THEN 2 WHEN d = 35 THEN 3
      WHEN d <= 39 THEN 4 WHEN d <= 43 THEN 5 WHEN d <= 47 THEN 6 WHEN d <= 53 THEN 7
      WHEN d <= 56 THEN 8 WHEN d <= 63 THEN 9 WHEN d <= 66 THEN 10 WHEN d = 68 THEN 11
      WHEN d <= 75 THEN 12 WHEN d <= 82 THEN 13 WHEN d = 84 THEN 14 WHEN d = 85 THEN 15
      WHEN d <= 88 THEN 16 WHEN d <= 93 THEN 17 WHEN d <= 96 THEN 18 WHEN d = 97 THEN 19
      ELSE 20 END"""
DIVISAO_SQL = "TRY_CAST(left(lpad(cnae_fiscal_principal, 7, '0'), 2) AS INTEGER)"

TOTAL_ATIVOS_SQL = """
SET enable_progress_bar = false;
WITH latest AS (
  SELECT MAX(ano * 100 + mes) AS am FROM br_me_cnpj.estabelecimentos WHERE sigla_uf = '{uf}'
),
e AS (
  SELECT """ + DIVISAO_SQL + """ AS d
  FROM br_me_cnpj.estabelecimentos
  WHERE sigla_uf = '{uf}'
    AND situacao_cadastral = '2'
    AND (ano * 100 + mes) = (SELECT am FROM latest)
)
SELECT """ + SECAO_SQL + """ AS sec, COUNT(*) AS total
FROM e
GROUP BY 1;
"""

FUZZY_SIM_THRESHOLD = 0.70
INTERP_MAX_GAP = 100  # house numbers; caps both interpolation gaps and edge extrapolation

# Second pass, for what tiers 1-2 leave out. Learned (2026-10-04) by sending
# unmatched addresses to ArcGIS and looking up which CNEFE row sat under its
# exact-address answers: the row was there, missed because CNEFE keeps the
# street title in its own column (RUA / PROFESSORA / MARIA CLARA), the Receita
# abbreviates it (DR, PROF, N SRA), appends the housing project in parentheses
# ("RUA A (CJ CEARA)"), or carries a neighbouring, outdated or big-user CEP.
# Every second-pass tier requires the exact house number, so a point it adds is
# always a real CNEFE address, never an interpolated one.
SECOND_PASS_FUZZY = 0.92   # Jaro-Winkler on the title-less name, same CEP5 + number
SECOND_PASS_SPREAD = 0.0005  # degrees (~50 m): candidates further apart are ambiguous

ABREVIACOES = [
    (r"N S|N SRA|NS SRA|NSRA|NOSSA SRA|NSA SRA", "NOSSA SENHORA"),
    (r"DR", "DOUTOR"), (r"DRA", "DOUTORA"), (r"PROF", "PROFESSOR"), (r"PROFA|PROFª", "PROFESSORA"),
    (r"CEL", "CORONEL"), (r"PE", "PADRE"), (r"STA", "SANTA"), (r"STO", "SANTO"),
    (r"GAL|GEN", "GENERAL"), (r"MAL", "MARECHAL"), (r"TEN", "TENENTE"), (r"CAP|CAPT", "CAPITAO"),
    (r"MAJ", "MAJOR"), (r"SGT", "SARGENTO"), (r"ENG", "ENGENHEIRO"), (r"DEP", "DEPUTADO"),
    (r"DES", "DESEMBARGADOR"), (r"VER", "VEREADOR"), (r"PRES", "PRESIDENTE"), (r"GOV", "GOVERNADOR"),
    (r"SEN", "SENADOR"), (r"MONS", "MONSENHOR"), (r"ALM", "ALMIRANTE"), (r"BRIG", "BRIGADEIRO"),
    (r"PREF", "PREFEITO"), (r"MIN", "MINISTRO"), (r"COMEND", "COMENDADOR"), (r"JORN", "JORNALISTA"),
]
# Street types the Receita sometimes repeats at the start of the name.
TIPOS = ("RUA|R|AVENIDA|AV|AVEN|TRAVESSA|TV|TRAV|ALAMEDA|AL|ESTRADA|ESTR|EST|RODOVIA|ROD|"
         "PRACA|PCA|PC|LARGO|LGO|VIELA|BECO|LADEIRA|LAD")
TITULOS = ("NOSSA SENHORA|SENHORA|SENHOR|DOUTOR|DOUTORA|PROFESSOR|PROFESSORA|CORONEL|PADRE|SAO|"
           "SANTA|SANTO|DOM|DONA|VEREADOR|VEREADORA|MONSENHOR|CAPITAO|GENERAL|MARECHAL|TENENTE|"
           "SARGENTO|MAJOR|DESEMBARGADOR|ENGENHEIRO|DEPUTADO|DEPUTADA|SENADOR|PRESIDENTE|"
           "GOVERNADOR|PREFEITO|MINISTRO|FREI|IRMA|IRMAO|ALMIRANTE|BRIGADEIRO|COMENDADOR|"
           "JORNALISTA|MAESTRO|POETA|MADRE|CONEGO|CARDEAL|ARCEBISPO|BISPO|BARAO|VISCONDE|CONDE|"
           "DUQUE|PRINCESA|PRINCIPE|IMPERADOR|CABO|SOLDADO|DELEGADO|PASTOR|MESTRE")


def nome_cheio_sql(x):
    """SQL for a street name in comparable form: accents, punctuation and the
    parenthesized housing project out, abbreviated titles spelled out, a
    leading street type and the articles dropped. A name that is only a street
    type, or only a single letter ("RUA A"), keeps what it has."""
    s = f"upper(strip_accents(coalesce({x}, '')))"
    s = rf"regexp_replace({s}, '\([^)]*\)?', ' ', 'g')"
    s = f"' ' || regexp_replace({s}, '[^A-Z0-9]+', ' ', 'g') || ' '"
    for pat, rep in ABREVIACOES:
        s = f"regexp_replace({s}, ' ({pat}) ', ' {rep} ', 'g')"
    s = f"regexp_replace({s}, ' (DA|DE|DO|DOS|DAS) ', ' ', 'g')"
    s = f"regexp_replace({s}, ' (DA|DE|DO|DOS|DAS) ', ' ', 'g')"  # "DA DE" in a row
    s = rf"trim(regexp_replace({s}, '\s+', ' ', 'g'))"
    sem_tipo = f"regexp_replace({s}, '^(({TIPOS}) )+', '')"
    return f"CASE WHEN {sem_tipo} = '' THEN {s} ELSE {sem_tipo} END"


def nucleo_sql(x):
    """The name without its titles (CORONEL, SAO, NOSSA SENHORA…), for when one
    side has the title and the other doesn't. Never empties a name."""
    sem = rf"trim(regexp_replace(regexp_replace(' ' || {x} || ' ', ' (({TITULOS}) )+', ' ', 'g'), '\s+', ' ', 'g'))"
    return f"CASE WHEN {sem} = '' THEN {x} ELSE {sem} END"


QUADRA_ABREV = [(r"Q|QD|QDR", "QUADRA"), (r"CJ|CONJ", "CONJUNTO"), (r"BL", "BLOCO"),
                (r"LT", "LOTE"), (r"CS", "CASA"), (r"CH", "CHACARA")]


def nome_quadra_sql(x):
    """SQL for a block-and-lot name (DF's "QNP 14 CJ E", Goiânia's "RUA 5 QD 12"):
    accents and punctuation out, QD/CJ/BL/LT/CS spelled out, leading zeros of
    numbers dropped ("LOTE 09" = "LOTE 9")."""
    s = f"upper(strip_accents(coalesce({x}, '')))"
    s = f"' ' || regexp_replace({s}, '[^A-Z0-9]+', ' ', 'g') || ' '"
    for pat, rep in QUADRA_ABREV:
        s = f"regexp_replace({s}, ' ({pat}) ', ' {rep} ', 'g')"
    s = rf"regexp_replace({s}, ' 0+([0-9])', ' \1', 'g')"
    return rf"trim(regexp_replace({s}, '\s+', ' ', 'g'))"


SEGUNDA_PASSADA_SQL = r"""
-- Second pass (tiers B-F), exact house number only, for rows tiers 1-2 left out.
pendentes AS MATERIALIZED (
  SELECT e.rid, e.mun, e.cep, left(e.cep, 5) AS cep5, e.log_raw, e.num_norm AS num
  FROM estab e
  LEFT JOIN resolved r ON r.rid = e.rid AND r.lat IS NOT NULL
  WHERE r.rid IS NULL AND e.num_norm > 0
    AND NOT regexp_matches(upper(coalesce(e.numero_raw, '')), 'KM')
),
cn2_raw AS (
  SELECT id_municipio AS mun, cep, titulo_segmento_logradouro AS tit, nome_logradouro AS nome,
    TRY_CAST(regexp_replace(numero_logradouro, '[^0-9]', '') AS INTEGER) AS num,
    AVG(TRY_CAST(latitude AS DOUBLE)) AS lat,
    AVG(TRY_CAST(longitude AS DOUBLE)) AS lng
  FROM br_ibge_censo_2022.cadastro_enderecos
  WHERE sigla_uf = '{uf}'
  GROUP BY 1, 2, 3, 4, 5
  HAVING num > 0
),
-- names are normalized once per distinct name, not once per address
nomes_cn AS (
  SELECT tit, nome, """ + nome_cheio_sql("coalesce(tit, '') || ' ' || nome") + r""" AS cheio
  FROM (SELECT DISTINCT tit, nome FROM cn2_raw)
),
cn2 AS MATERIALIZED (
  SELECT c.mun, c.cep, left(c.cep, 5) AS cep5, n.cheio, """ + nucleo_sql("n.cheio") + r""" AS nucleo,
    c.num, c.lat, c.lng
  FROM cn2_raw c JOIN nomes_cn n ON n.nome = c.nome AND n.tit IS NOT DISTINCT FROM c.tit
),
nomes_e AS (
  SELECT log_raw, cheio, """ + nucleo_sql("cheio") + r""" AS nucleo
  FROM (SELECT log_raw, """ + nome_cheio_sql("log_raw") + r""" AS cheio
        FROM (SELECT DISTINCT log_raw FROM pendentes))
),
pend AS MATERIALIZED (
  SELECT p.*, n.cheio, n.nucleo FROM pendentes p JOIN nomes_e n USING (log_raw)
),
-- B: same CEP, full name  C: same CEP, title-less name
-- D: same municipality, full name, CEP ignored (the Receita's is often a
--    neighbour's, outdated, or a big-user CEP)
-- E: same municipality and CEP5, title-less name
-- F: same municipality and CEP5, title-less name close enough (spelling)
cand AS (
  SELECT p.rid, 'B' AS tier, 2.0 AS pri, c.lat, c.lng
  FROM pend p JOIN cn2 c ON c.cep = p.cep AND c.cheio = p.cheio AND c.num = p.num
  UNION ALL
  SELECT p.rid, 'C', 2.0, c.lat, c.lng
  FROM pend p JOIN cn2 c ON c.cep = p.cep AND c.nucleo = p.nucleo AND c.num = p.num
  UNION ALL
  SELECT p.rid, 'D', (c.cep = p.cep)::INT * 2 + (c.cep5 = p.cep5)::INT, c.lat, c.lng
  FROM pend p JOIN cn2 c ON c.mun = p.mun AND c.cheio = p.cheio AND c.num = p.num
  UNION ALL
  SELECT p.rid, 'E', (c.cep = p.cep)::INT * 2 + 1, c.lat, c.lng
  FROM pend p JOIN cn2 c ON c.mun = p.mun AND c.cep5 = p.cep5 AND c.nucleo = p.nucleo AND c.num = p.num
  UNION ALL
  SELECT p.rid, 'F', jaro_winkler_similarity(p.nucleo, c.nucleo), c.lat, c.lng
  FROM pend p JOIN cn2 c ON c.mun = p.mun AND c.cep5 = p.cep5 AND c.num = p.num
  WHERE length(p.nucleo) >= 5 AND jaro_winkler_similarity(p.nucleo, c.nucleo) >= """ + str(SECOND_PASS_FUZZY) + r"""
),
-- the first tier that found the row wins; within it, the best-placed
-- candidates, and they must all sit within SECOND_PASS_SPREAD of each other
cand_t AS (
  SELECT *, min(tier) OVER (PARTITION BY rid) AS t0 FROM cand
),
topo AS (
  SELECT * FROM cand_t WHERE tier = t0
  QUALIFY pri = max(pri) OVER (PARTITION BY rid)
),
segunda AS (
  SELECT rid, any_value(tier) AS tier, avg(lat) AS lat, avg(lng) AS lng,
    max(lat) - min(lat) <= """ + str(SECOND_PASS_SPREAD) + r""" AND max(lng) - min(lng) <= """ + str(SECOND_PASS_SPREAD) + r""" AS unico
  FROM topo GROUP BY rid
),
-- Third pass (tiers G-H), block-and-lot addresses: DF writes "QNP 14
-- CONJUNTO E" + LOTE 22 in the complement with house number 0, Plano Piloto
-- just "SQN 411 BLOCO I"; the Receita has the lot as the number, at the end of
-- the name ("... QUADRA 18 LOTE 09") or in its complement.
pend3 AS MATERIALIZED (
  SELECT e.rid, e.mun, e.cep, q.base AS qn,
    TRY_CAST(coalesce(
      nullif(regexp_extract(q.full_, ' (LOTE|CASA) ([0-9]+)$', 2), ''),
      CASE WHEN e.num_norm > 0 THEN e.num_norm::VARCHAR END,
      nullif(regexp_extract(""" + nome_quadra_sql("e.compl_raw") + """, '(LOTE|CASA) ([0-9]+)', 2), '')
    ) AS INTEGER) AS lote
  FROM estab e
  JOIN (SELECT log_raw, full_, trim(regexp_replace(full_, ' (LOTE|CASA)( [0-9]+)?$', '')) AS base
        FROM (SELECT log_raw, """ + nome_quadra_sql("log_raw") + """ AS full_
              FROM (SELECT DISTINCT log_raw FROM estab))) q
    ON q.log_raw = e.log_raw
  WHERE e.rid NOT IN (SELECT rid FROM resolved WHERE lat IS NOT NULL)
    AND e.rid NOT IN (SELECT rid FROM segunda WHERE unico)
    AND length(q.base) >= 4
),
cn3 AS MATERIALIZED (
  SELECT id_municipio AS mun, cep, """ + nome_quadra_sql("nome_logradouro") + """ AS qn,
    CASE WHEN TRY_CAST(regexp_replace(numero_logradouro, '[^0-9]', '') AS INTEGER) > 0
           THEN TRY_CAST(regexp_replace(numero_logradouro, '[^0-9]', '') AS INTEGER)
         WHEN complemento_elemento_1 IN ('LOTE', 'CASA')
           THEN TRY_CAST(regexp_replace(complemento_valor_1, '[^0-9]', '') AS INTEGER) END AS lote,
    TRY_CAST(latitude AS DOUBLE) AS lat, TRY_CAST(longitude AS DOUBLE) AS lng
  FROM br_ibge_censo_2022.cadastro_enderecos
  WHERE sigla_uf = '{uf}'
),
-- the CNEFE name may carry a sector prefix the Receita drops ("SETOR
-- TRADICIONAL Q 18 AVENIDA INDEPENDENCIA"); always within the same CEP
quadra_par AS (
  SELECT p.rid, p.lote, c.lote AS c_lote, c.lat, c.lng
  FROM pend3 p JOIN cn3 c ON c.cep = p.cep
  WHERE c.qn = p.qn OR ends_with(c.qn, ' ' || p.qn)
),
-- G: same block and lot
quadra_g AS (
  SELECT rid, 'G' AS tier, avg(lat) AS lat, avg(lng) AS lng,
    max(lat) - min(lat) <= """ + str(SECOND_PASS_SPREAD) + """ AND max(lng) - min(lng) <= """ + str(SECOND_PASS_SPREAD) + """ AS unico
  FROM quadra_par WHERE lote = c_lote GROUP BY rid
),
-- H: the Receita gives no number or lot, and every CNEFE address under that
-- name sits within SECOND_PASS_SPREAD — the name is a single building
-- ("SQN 411 BLOCO I"). A number or lot that CNEFE lacks never lands here.
quadra_h AS (
  SELECT rid, 'H' AS tier, avg(lat) AS lat, avg(lng) AS lng,
    max(lat) - min(lat) <= """ + str(SECOND_PASS_SPREAD) + """ AND max(lng) - min(lng) <= """ + str(SECOND_PASS_SPREAD) + """ AS unico
  FROM quadra_par WHERE lote IS NULL GROUP BY rid
),
resolved_all AS (
  SELECT rid, lat, lng, 'A' AS tier FROM resolved WHERE lat IS NOT NULL AND lng IS NOT NULL
  UNION ALL
  SELECT rid, lat, lng, tier FROM segunda WHERE unico
  UNION ALL
  SELECT rid, lat, lng, tier FROM quadra_g WHERE unico
  UNION ALL
  SELECT rid, lat, lng, tier FROM quadra_h WHERE unico
)
"""

RESOLVE_SQL = """
SET enable_progress_bar = false;
WITH latest AS (
  SELECT MAX(ano * 100 + mes) AS am FROM br_me_cnpj.estabelecimentos WHERE sigla_uf = '{uf}'
),
cnefe AS (
  SELECT
    cep,
    trim(regexp_replace(upper(trim(strip_accents(nome_logradouro))), '\\b(DA|DE|DO|DOS|DAS)\\b', '', 'g')) AS log_norm,
    TRY_CAST(regexp_replace(numero_logradouro, '[^0-9]', '') AS INTEGER) AS num_norm,
    AVG(TRY_CAST(latitude AS DOUBLE)) AS lat,
    AVG(TRY_CAST(longitude AS DOUBLE)) AS lng
  FROM br_ibge_censo_2022.cadastro_enderecos
  WHERE sigla_uf = '{uf}'
  GROUP BY 1, 2, 3
  HAVING num_norm IS NOT NULL
),
cnefe_streets AS (
  SELECT DISTINCT cep, log_norm FROM cnefe
),
estab AS MATERIALIZED (
  SELECT
    row_number() OVER () AS rid,
    cep,
    trim(regexp_replace(upper(trim(strip_accents(logradouro))), '\\b(DA|DE|DO|DOS|DAS)\\b', '', 'g')) AS log_norm,
    TRY_CAST(regexp_replace(numero, '[^0-9]', '') AS INTEGER) AS num_norm,
    id_municipio AS mun, logradouro AS log_raw, numero AS numero_raw, complemento AS compl_raw,
    GREATEST(year(data_inicio_atividade), 1900) AS yr,
    """ + DIVISAO_SQL + """ AS d
  FROM br_me_cnpj.estabelecimentos
  WHERE sigla_uf = '{uf}'
    AND situacao_cadastral = '2'
    AND (ano * 100 + mes) = (SELECT am FROM latest)
),
-- tier 1: street name matches CNEFE exactly (after accent/article normalization)
street_ok AS (
  SELECT e.rid, e.cep, e.log_norm AS street_used, e.num_norm
  FROM estab e JOIN cnefe_streets cs ON e.cep = cs.cep AND e.log_norm = cs.log_norm
),
-- tier 2: CEP is trusted, but street name is fuzzy-matched (typos/variants) among
-- CNEFE streets in that same CEP, since a CEP only has a handful of candidate streets
street_fuzzy AS (
  SELECT e.rid, e.cep, cs.log_norm AS street_used, e.num_norm,
    row_number() OVER (PARTITION BY e.rid ORDER BY jaro_winkler_similarity(e.log_norm, cs.log_norm) DESC) AS rn,
    jaro_winkler_similarity(e.log_norm, cs.log_norm) AS sim
  FROM estab e
  LEFT JOIN street_ok so ON e.rid = so.rid
  JOIN cnefe_streets cs ON e.cep = cs.cep
  WHERE so.rid IS NULL
  QUALIFY rn = 1 AND sim >= {fuzzy_threshold}
),
candidates AS (
  SELECT rid, cep, street_used, num_norm FROM street_ok
  UNION ALL
  SELECT rid, cep, street_used, num_norm FROM street_fuzzy
),
-- for each candidate, find the nearest known house numbers below and above the
-- target on that (cep, street) — exact match if the number itself is known
interp AS (
  SELECT c.rid, c.num_norm AS target,
    lo.num_norm AS lo_num, lo.lat AS lo_lat, lo.lng AS lo_lng,
    hi.num_norm AS hi_num, hi.lat AS hi_lat, hi.lng AS hi_lng
  FROM candidates c
  LEFT JOIN LATERAL (
    SELECT num_norm, lat, lng FROM cnefe cn
    WHERE cn.cep = c.cep AND cn.log_norm = c.street_used AND cn.num_norm <= c.num_norm
    ORDER BY cn.num_norm DESC LIMIT 1
  ) lo ON true
  LEFT JOIN LATERAL (
    SELECT num_norm, lat, lng FROM cnefe cn
    WHERE cn.cep = c.cep AND cn.log_norm = c.street_used AND cn.num_norm >= c.num_norm
    ORDER BY cn.num_norm ASC LIMIT 1
  ) hi ON true
),
-- linearly interpolate position between the bracketing known numbers (or use the
-- single known edge point), only trusted within INTERP_MAX_GAP house numbers —
-- beyond that, house-number spacing is too irregular to assume a straight line
resolved AS (
  SELECT rid,
    CASE
      WHEN lo_num IS NOT NULL AND hi_num IS NOT NULL AND hi_num != lo_num AND (hi_num - lo_num) <= {interp_max_gap}
        THEN lo_lat + (hi_lat - lo_lat) * ((target - lo_num)::DOUBLE / (hi_num - lo_num))
      WHEN lo_num IS NOT NULL AND hi_num IS NOT NULL AND hi_num = lo_num THEN lo_lat
      WHEN lo_num IS NOT NULL AND (hi_num IS NULL OR hi_num - lo_num > {interp_max_gap}) AND (target - lo_num) <= {interp_max_gap} THEN lo_lat
      WHEN hi_num IS NOT NULL AND (lo_num IS NULL OR hi_num - lo_num > {interp_max_gap}) AND (hi_num - target) <= {interp_max_gap} THEN hi_lat
      ELSE NULL
    END AS lat,
    CASE
      WHEN lo_num IS NOT NULL AND hi_num IS NOT NULL AND hi_num != lo_num AND (hi_num - lo_num) <= {interp_max_gap}
        THEN lo_lng + (hi_lng - lo_lng) * ((target - lo_num)::DOUBLE / (hi_num - lo_num))
      WHEN lo_num IS NOT NULL AND hi_num IS NOT NULL AND hi_num = lo_num THEN lo_lng
      WHEN lo_num IS NOT NULL AND (hi_num IS NULL OR hi_num - lo_num > {interp_max_gap}) AND (target - lo_num) <= {interp_max_gap} THEN lo_lng
      WHEN hi_num IS NOT NULL AND (lo_num IS NULL OR hi_num - lo_num > {interp_max_gap}) AND (hi_num - target) <= {interp_max_gap} THEN hi_lng
      ELSE NULL
    END AS lng
  FROM interp
),
""" + SEGUNDA_PASSADA_SQL

# rows per point and CNAE section: extract_uf folds them into a point with
# a section mask, and sums the per-section counts
PONTOS_SQL = RESOLVE_SQL + """
SELECT round(r.lng, 6) AS lng, round(r.lat, 6) AS lat, sec, COUNT(*) AS weight,
  MIN(yr) AS yr
FROM (SELECT rid, yr, """ + SECAO_SQL + """ AS sec FROM estab) e
JOIN resolved_all r USING (rid)
GROUP BY round(r.lng, 6), round(r.lat, 6), sec;
"""

# --camadas: how many establishments each tier resolves, without writing files
CAMADAS_SQL = RESOLVE_SQL + """
SELECT tier, COUNT(*) AS n FROM resolved_all GROUP BY tier
UNION ALL SELECT 'ambiguo', COUNT(*) FROM segunda WHERE NOT unico
UNION ALL SELECT 'pendente_com_numero', COUNT(*) FROM pendentes
UNION ALL SELECT 'total', COUNT(*) FROM estab
ORDER BY 1;
"""


def extract_uf(uf, use_ssh):
    total_rows = run_query(TOTAL_ATIVOS_SQL.format(uf=uf), use_ssh)
    n_estab_ativos = sum(r["total"] for r in total_rows)
    setores = {s: {"ativos": 0, "geo": 0} for s in SECOES}
    for r in total_rows:
        setores[SECOES[r["sec"]]]["ativos"] = r["total"]

    sql = PONTOS_SQL.format(uf=uf, fuzzy_threshold=FUZZY_SIM_THRESHOLD, interp_max_gap=INTERP_MAX_GAP)
    rows = run_query(sql, use_ssh)

    # Fold the (point, section) rows into points: the section mask, the
    # establishment count and the oldest year; and sum each section's count.
    by_point = {}
    for r in rows:
        key = (r["lng"], r["lat"])
        p = by_point.get(key)
        if p is None:
            p = by_point[key] = {"lng": r["lng"], "lat": r["lat"], "weight": 0, "yr": r["yr"], "mask": 0}
        p["weight"] += r["weight"]
        p["yr"] = min(p["yr"], r["yr"])
        p["mask"] |= 1 << r["sec"]
        setores[SECOES[r["sec"]]]["geo"] += r["weight"]
    pontos = list(by_point.values())

    n_estab_geolocalizados = sum(p["weight"] for p in pontos)
    n_points = len(pontos)

    if n_points:
        lngs = [r["lng"] for r in pontos]
        lats = [r["lat"] for r in pontos]
        bbox = [min(lngs), min(lats), max(lngs), max(lats)]
    else:
        bbox = None

    out_path = DADOS_DIR / f"{uf.lower()}.bin.gz"
    file_size = 0
    if n_points:
        write_points_soa(out_path, pontos)
        file_size = out_path.stat().st_size
    else:
        out_path.unlink(missing_ok=True)

    match_rate = (n_estab_geolocalizados / n_estab_ativos * 100) if n_estab_ativos else 0.0

    return {
        "uf": uf,
        "n_estab_ativos": n_estab_ativos,
        "n_estab_geolocalizados": n_estab_geolocalizados,
        "match_rate": match_rate,
        "setores": setores,
        "n_points": n_points,
        "bbox": bbox,
        "file_size": file_size,
    }


def write_report(stats):
    lines = [
        "# Cobertura de geolocalização — CNPJ x CNEFE, por UF",
        "",
        "Estabelecimentos ativos (Receita Federal, snapshot mensal mais recente) geolocalizados",
        "por casamento de endereço (logradouro + número, ou quadra + lote) com o Cadastro Nacional de",
        "Endereços para Fins Estatísticos (CNEFE, Censo IBGE 2022). Sem geolocalização, o",
        "estabelecimento não aparece no mapa — não há fallback por centroide de CEP.",
        "",
        "| UF | Estab. ativos | Geolocalizados | % | Pontos (após dedup) | Tamanho (.bin.gz) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    total_ativos = total_geo = total_points = total_size = 0
    sem_cobertura = []
    for s in stats:
        flag = " ⚠️ sem cobertura no CNEFE" if s["n_points"] == 0 else ""
        lines.append(
            f"| {s['uf']} | {s['n_estab_ativos']:,} | {s['n_estab_geolocalizados']:,} | "
            f"{s['match_rate']:.1f}% | {s['n_points']:,} | {s['file_size'] / 1e6:.2f} MB{flag} |"
        )
        total_ativos += s["n_estab_ativos"]
        total_geo += s["n_estab_geolocalizados"]
        total_points += s["n_points"]
        total_size += s["file_size"]
        if s["n_points"] == 0:
            sem_cobertura.append(s["uf"])
    overall_rate = (total_geo / total_ativos * 100) if total_ativos else 0.0
    lines.append(
        f"| **Brasil** | **{total_ativos:,}** | **{total_geo:,}** | "
        f"**{overall_rate:.1f}%** | **{total_points:,}** | **{total_size / 1e6:.2f} MB** |"
    )
    lines.append("")
    if sem_cobertura:
        lines.append(
            f"⚠️ **{', '.join(sem_cobertura)}**: 0 pontos — `br_ibge_censo_2022.cadastro_enderecos` "
            "não tem nenhuma linha para essa(s) UF(s) no mirror atual (gap na fonte/sync, não um bug "
            "de join). Essas UFs são omitidas de `meta.json` e não geram página."
        )
        lines.append("")
    REPORT_PATH.write_text("\n".join(lines))


def print_camadas(ufs, use_ssh):
    """Per UF, how many establishments each tier resolves (A = tiers 1-2,
    B-F = second pass), without touching the output files."""
    for uf in ufs:
        t = time.time()
        rows = {r["tier"]: r["n"] for r in run_query(
            CAMADAS_SQL.format(uf=uf, fuzzy_threshold=FUZZY_SIM_THRESHOLD, interp_max_gap=INTERP_MAX_GAP), use_ssh)}
        total, a = rows.pop("total"), rows.get("A", 0)
        novos = sum(rows.get(k, 0) for k in "BCDEFGH")
        camadas = "  ".join(f"{k} {rows.get(k, 0):,}" for k in "BCDEFGH")
        print(f"{uf}: {total:,} ativos | antes {a:,} ({a / total:.1%}) | +{novos:,} ({camadas}) "
              f"| depois {(a + novos) / total:.1%} | {novos / max(total - a, 1):.1%} das falhas | "
              f"ambíguos {rows.get('ambiguo', 0):,} | {time.time() - t:.0f}s", flush=True)


def main():
    use_ssh = "--local" not in sys.argv
    mode = "SSH beelink" if use_ssh else "local"
    print(f"[extrai_estados_cnpj] Extracting from {mode}...")

    DADOS_DIR.mkdir(parents=True, exist_ok=True)

    ufs = [r["uf"] for r in run_query(UF_LIST_SQL, use_ssh)]
    print(f"[extrai_estados_cnpj] {len(ufs)} UFs: {', '.join(ufs)}")

    only = [a for a in sys.argv[1:] if a not in ("--local", "--camadas")]
    if only:
        ufs = [u for u in ufs if u in only]
        print(f"[extrai_estados_cnpj] Filtered to: {', '.join(ufs)}")

    if "--camadas" in sys.argv:
        print_camadas(ufs, use_ssh)
        return

    meta = {}
    stats = []
    for i, uf in enumerate(ufs, 1):
        print(f"[extrai_estados_cnpj]  ({i}/{len(ufs)}) {uf}...")
        s = extract_uf(uf, use_ssh)
        print(
            f"          {s['n_estab_ativos']:,} ativos, "
            f"{s['n_estab_geolocalizados']:,} geolocalizados ({s['match_rate']:.1f}%), "
            f"{s['n_points']:,} pontos, {s['file_size'] / 1e6:.2f} MB"
        )
        if s["n_points"] == 0:
            print(f"          WARNING: 0 pontos para {uf} (sem cobertura no CNEFE?) — omitido do meta.json")
        else:
            meta[uf] = {
                "n_points": s["n_points"],
                "n_estab_ativos": s["n_estab_ativos"],
                "n_estab_geolocalizados": s["n_estab_geolocalizados"],
                "bbox": s["bbox"],
                "setores": s["setores"],
            }
        stats.append(s)

    with open(DADOS_DIR / "meta.json", "w") as f:
        json.dump(meta, f, ensure_ascii=False)

    write_report(stats)

    print(f"[extrai_estados_cnpj] Done! Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
