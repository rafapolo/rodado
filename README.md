# rodado — Operational Data Platform

> End-to-end data platform over 533 Brazilian government datasets: ontology-driven semantic layer, AI-powered natural-language query interface, automated ingestion pipelines, and a production query API — built and operated as a single-engineer project.

**533 tables · ~675 GB Parquet+zstd · DuckDB · LLM NL→SQL · Production since 2024**

---

## What this demonstrates

Mapped directly to the FDE competency model:

| Competency | How this project demonstrates it |
|-----------|----------------------------------|
| End-to-end delivery, prototype → production | Ingestion pipeline + semantic layer + API + UI, fully deployed and running |
| Data engineering & modeling | 533 tables normalized to a typed ontology with join-key graph |
| Ontology design | 8 business object types with explicit relationships and canonical keys |
| Application development | Query API + browser SQL shell + NL→SQL TUI, all production-deployed |
| AI/ML enablement | LLM-powered natural-language → SQL with semantic table selection |
| Access controls & auditability | HMAC-SHA256 auth, read-only enforcement, Caddy forward auth |
| Operational durability | Persistent DuckDB connection, resumable pipelines, Docker + haloy deploy |
| Sensitive data handling | CPF/CNPJ personal identifiers — read-only, no PII export, credential isolation |

---

## User Workflows

Three concrete analyst scenarios showing the full data → insight → decision arc.

---

### Workflow 1 — Compliance: company integrity check

**Situation:** A compliance team needs to verify whether companies awarded public contracts have directors appearing in other sanctioned or flagged entities.

**Query:**
```sql
-- Companies in SP with public contracts whose directors also appear in other entities
SELECT
    e.razao_social,
    e.cnpj,
    s.nome_socio,
    s.cnpj_cpf_socio AS cpf_director,
    COUNT(DISTINCT e2.cnpj) AS other_entities,
    SUM(c.valor_contrato)   AS total_contracts_brl
FROM br_me_cnpj.estabelecimentos e
JOIN br_me_cnpj.socios s
    ON e.cnpj_basico = s.cnpj_basico
JOIN br_me_cnpj.socios s2
    ON s.cnpj_cpf_socio = s2.cnpj_cpf_socio
    AND s2.cnpj_basico <> s.cnpj_basico
JOIN br_me_cnpj.estabelecimentos e2
    ON s2.cnpj_basico = e2.cnpj_basico
JOIN br_cgu_compras_governamentais.contratos c
    ON e.cnpj = c.cnpj_contratado
WHERE e.sigla_uf = 'SP'
  AND c.ano = 2023
GROUP BY 1,2,3,4
HAVING other_entities > 2
ORDER BY total_contracts_brl DESC
LIMIT 20
```

**Decision:** Flag companies for manual review; route to procurement governance team.

---

### Workflow 2 — Policy: infrastructure gap prioritization

**Situation:** A state health secretariat needs to identify municipalities with critically low hospital bed coverage to prioritize federal budget allocation.

**Query:**
```sql
-- Municipalities with low SUS beds AND poor education outcomes — dual deprivation index
SELECT
    m.nome                          AS municipio,
    m.sigla_uf,
    pop.populacao,
    ROUND(cnes.leitos_sus * 1000.0
          / NULLIF(pop.populacao, 0), 2) AS leitos_sus_por_mil,
    ideb.nota_media                 AS ideb_fundamental,
    pib.pib_per_capita_real         AS pib_per_capita
FROM br_bd_diretorios_brasil.municipio m
JOIN br_ibge_populacao.municipio pop
    ON m.id_municipio = pop.id_municipio AND pop.ano = 2022
JOIN (
    SELECT id_municipio, SUM(leitos) AS leitos_sus
    FROM br_ms_cnes.estabelecimento
    WHERE ano = 2023 AND tipo_gestao = 'M'
    GROUP BY id_municipio
) cnes ON m.id_municipio = cnes.id_municipio
JOIN br_inep_ideb.municipio ideb
    ON m.id_municipio = ideb.id_municipio AND ideb.ano = 2021
JOIN br_ibge_pib.municipio pib
    ON m.id_municipio = pib.id_municipio AND pib.ano = 2021
WHERE pop.populacao > 10000
ORDER BY leitos_sus_por_mil ASC, ideb_fundamental ASC
LIMIT 50
```

**Decision:** Ranked shortlist delivered to budget committee; top 10 municipalities flagged for emergency transfer.

---

### Workflow 3 — Journalism: electoral spending anomalies

**Situation:** An investigative journalist tracks whether campaign spending patterns correlate with post-election public contract awards in a given state.

**Query:**
```sql
-- Candidates with high campaign spend → companies they're linked to won contracts after election
SELECT
    cand.nome_candidato,
    cand.sigla_partido,
    cand.sigla_uf,
    SUM(desp.valor_despesa)    AS total_campaign_spend,
    SUM(cont.valor_contrato)   AS post_election_contracts,
    COUNT(DISTINCT cont.cnpj_contratado) AS linked_companies
FROM br_tse_eleicoes.candidatos cand
JOIN br_tse_eleicoes.despesas_candidato desp
    ON cand.id_candidato = desp.id_candidato
    AND cand.ano = desp.ano
JOIN br_me_cnpj.socios s
    ON cand.cpf_candidato = s.cnpj_cpf_socio
JOIN br_cgu_compras_governamentais.contratos cont
    ON s.cnpj_basico = SUBSTR(cont.cnpj_contratado, 1, 8)
    AND cont.ano > cand.ano
WHERE cand.ano = 2022
  AND cand.sigla_uf = 'SP'
  AND cand.descricao_cargo = 'DEPUTADO ESTADUAL'
GROUP BY 1,2,3
HAVING post_election_contracts > 1000000
ORDER BY post_election_contracts DESC
```

**Decision:** Shortlist of 12 candidates forwarded to editorial team with source data for verification.

---

## Domain Ontology

The platform models Brazilian public data as typed business objects with explicit relationships — the same mental model used in enterprise operational platforms.

```
┌──────────────────────┐          ┌──────────────────────┐
│      State (UF)      │─────────▶│     Municipality     │
│  sigla_uf (245 tbl)  │   1:N    │   id_municipio       │
│  id_uf    (22 tbl)   │          │   (195 tables)       │
└──────────────────────┘          └──────────┬───────────┘
                                             │ 1:N
             ┌───────────────────────────────┼──────────────────────┐
             │                              │                       │
             ▼                              ▼                       ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│    CensusSector      │  │   SocialIndicator    │  │   ElectoralZone      │
│ id_setor_censitario  │  │  health · education  │  │  id_municipio_tse    │
│      (27 tbl)        │  │  income · housing    │  │      (23 tbl)        │
└──────────────────────┘  │  ano/mes (261+ tbl)  │  └──────────────────────┘
                          └──────────────────────┘

┌──────────────────────┐          ┌──────────────────────┐
│       Company        │─────────▶│        Person        │
│   cnpj  (14-digit)  │   N:M    │   cpf                │
│   br_me_cnpj.*       │  socios  │   servidores · rais  │
└──────────┬───────────┘          └──────────────────────┘
           │ 1:N
           ▼
┌──────────────────────┐          ┌──────────────────────┐
│  EconomicActivity    │          │   PublicContract     │
│  cnae_2_subclasse    │          │   licitacoes         │
│      (6 tbl)         │          │   compras_gov        │
└──────────────────────┘          └──────────────────────┘

┌──────────────────────┐
│   OccupationClass    │   Temporal dimension:
│   cbo_2002 (6 tbl)  │     ano       (261 tbl)
│   RAIS/CAGED/CNES    │     mes        (94 tbl)
└──────────────────────┘     trimestre   (3 tbl)
```

**Canonical join keys** — from [`context/join_keys.md`](context/join_keys.md):

| Key | Tables | Object |
|-----|--------|--------|
| `id_municipio` | 195 | Municipality |
| `sigla_uf` | 245 | State |
| `cnpj` / `cnpj_basico` | 18 | Company |
| `id_setor_censitario` | 27 | CensusSector |
| `id_municipio_tse` | 23 | ElectoralZone |
| `cbo_2002` | 6 | OccupationClass |
| `cnae_2_subclasse` | 6 | EconomicActivity |
| `cpf` | varies | Person |
| `ano` | 261 | Temporal partition |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       USERS / WORKFLOWS                          │
│   Compliance analysts · Policy teams · Researchers · Journalists │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                       APPLICATION LAYER                          │
│                                                                  │
│   db.ミ.xyz        — browser SQL shell (ttyd + DuckDB)          │
│   ask.ミ.xyz       — AI natural-language query (Rust TUI)       │
│   POST /query      — programmatic SQL API (curl / scripts)       │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SEMANTIC / ONTOLOGY LAYER                     │
│                                                                  │
│   DuckDB views over partitioned datasets                         │
│   basedosdados-schema.json   — 533-table schema registry        │
│   join_keys.md               — entity relationship graph        │
│   table_embeddings.json      — semantic vectors for AI (11.4 MB)│
│   overview/ (34 files)       — domain narratives for LLM ctx    │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                     QUERY / ACCESS LAYER                         │
│                                                                  │
│   auth.py    — persistent DuckDB conn, HMAC-SHA256 auth         │
│   Caddy      — TLS termination, forward auth, access control    │
│   Read-only  — no writes enforced at engine level               │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                             │
│                                                                  │
│   Hetzner Object Storage, Helsinki (S3-compatible)              │
│   Partitioned Parquet + zstd · 533 tables · ~675 GB             │
│   DuckDB httpfs reads on demand — no local data import          │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                      INGESTION PIPELINE                          │
│                                                                  │
│   BigQuery (basedosdados project)                                │
│     → GCS export (Parquet + zstd, parallel jobs)               │
│     → Hetzner S3 (rclone streaming, no intermediate disk)      │
│   scripts/roda.sh — resumable, dry-run, GCP VM option          │
└──────────────────────────────────────────────────────────────────┘
```

---

## AI-Powered Query Layer

Natural-language queries over 533 datasets — an AI workflow layer, not just a search box.

```
User question (Portuguese/English)
    │
    ▼
Semantic table selection
    (cosine similarity over 11.4 MB embedding index → top-K tables)
    │
    ▼
Schema filtering
    (trim 3.8 MB schema to relevant tables only)
    │
    ▼
LLM SQL generation
    (Gemini Flash / OpenRouter / local Ollama sqlcoder)
    │
    ▼
DuckDB execution → results
```

**Example:**
```
> Qual o município com maior mortalidade infantil no Nordeste em 2021?
→ SELECT m.nome, m.sigla_uf, s.taxa_mortalidade_infantil
  FROM br_ms_sim.municipio s
  JOIN br_bd_diretorios_brasil.municipio m ON s.id_municipio = m.id_municipio
  WHERE m.sigla_uf IN ('BA','PE','CE','MA','PI','RN','PB','AL','SE')
    AND s.ano = 2021
  ORDER BY s.taxa_mortalidade_infantil DESC LIMIT 1
```

Configurable backends via `SQL_GENERATOR` env var. Table selection controlled by `TOP_K_TABLES` (default: 5). Interfaces: browser (`ask.ミ.xyz`) and CLI.

```bash
./ask/target/release/ask "Quantos municípios têm IDH abaixo de 0.6?"
```

---

## Data Quality & Governance

### Partition requirements

Large tables (100M+ rows) require partition filters to avoid scan timeouts. Always include at least one of:

| Partition key | Tables | Example |
|--------------|--------|---------|
| `ano` | 261 | `WHERE ano = 2023` |
| `sigla_uf` | 245 | `WHERE sigla_uf = 'SP'` |
| `mes` | 94 | `WHERE ano = 2023 AND mes = 6` |

### Sensitive identifiers

| Identifier | Description | Handling |
|-----------|-------------|----------|
| `cpf` | Brazilian individual tax ID (personal) | Read-only; present in public servant and electoral datasets |
| `cnpj` | Brazilian company tax ID | Read-only; 14-digit canonical identifier |
| `cnpj_basico` | Company base (8-digit, groups branches) | Use for company-level joins |

All access is read-only enforced at both the DuckDB engine level and the API layer. No PII export endpoints. Credentials isolated per service.

### Known limitations & assumptions

- **Data freshness varies**: CNPJ register updates monthly; census data is 2010/2022; some health datasets lag 12–18 months.
- **Join cardinality**: CPF-based joins across datasets can produce unexpectedly high cardinality — validate row counts before aggregating.
- **Null density**: Some survey microdata tables (PNAD, PNADC) have high null rates in optional columns; filter explicitly.
- **Monetary values**: Always verify order of magnitude before reporting contract/budget values — trillion-real totals indicate a missing GROUP BY or partition filter.
- **Sanity protocol**: Before reporting any number, (1) state expected order of magnitude, (2) flag any row exceeding it, (3) verify via two independent query paths.

### Access model

```
Public internet → Caddy (TLS + forward auth) → auth.py (HMAC-SHA256)
                                              → DuckDB (read-only, no writes)
                                              → Hetzner S3 (private bucket)
```

- Web UI access requires password authentication
- `/query` endpoint requires `X-Password` header
- S3 credentials never exposed to query layer
- All queries logged with timestamp and source IP

---

## Query API

The endpoint is collocated with Hetzner S3 — persistent warmed DuckDB connection, no cold-start latency.

```bash
# Inline query
curl -X POST https://db.xn--2dk.xyz/query \
  -H "X-Password: $BASIC_AUTH_PASSWORD" \
  --data-binary "SELECT sigla_uf, COUNT(*) FROM br_me_cnpj.estabelecimentos GROUP BY 1"

# From file
curl -X POST https://db.xn--2dk.xyz/query \
  -H "X-Password: $BASIC_AUTH_PASSWORD" \
  --data-binary @analysis.sql > result.csv

# Heredoc (useful in scripts)
curl -X POST https://db.xn--2dk.xyz/query \
  -H "X-Password: $BASIC_AUTH_PASSWORD" \
  --data-binary @- << 'SQL'
SELECT sigla_uf, SUM(valor_contrato) AS total
FROM br_cgu_compras_governamentais.contratos
WHERE ano = 2023
GROUP BY 1 ORDER BY 2 DESC
SQL
```

---

## Palantir Foundry Mapping

| rodado component | Foundry equivalent |
|-----------------|-------------------|
| BigQuery export scripts | External data connectors |
| Parquet files on Hetzner S3 | Foundry datasets |
| DuckDB engine + views | Foundry query engine |
| `basedosdados-schema.json` | Ontology schema registry |
| `join_keys.md` entity graph | Object type links / property mappings |
| `table_embeddings.json` | Semantic search index |
| `/query` HTTP endpoint | Foundry Functions |
| Browser SQL shell | Workshop application |
| `ask/` NL→SQL layer | AIP-powered application |
| `scripts/roda.sh` | Foundry pipeline |
| Caddy + auth.py | Access control + audit layer |
| `overview/` domain narratives | Business context / documentation |

---

## Services

| Port | Service | Endpoint |
|------|---------|----------|
| 7681 | DuckDB browser shell (ttyd) | db.ミ.xyz |
| 7682 | NL→SQL TUI (ttyd) | ask.ミ.xyz |
| 8081 | Query API (auth.py) | db.ミ.xyz/query |
| 8080 | Caddy reverse proxy + TLS | — |

---

## Stack

| Layer | Technology |
|-------|-----------|
| Query engine | DuckDB (httpfs, persistent in-memory connection) |
| Storage | Hetzner Object Storage, Parquet+zstd |
| NL→SQL | Rust (ratatui), Gemini / OpenRouter / Ollama |
| Semantic search | cosine similarity over `table_embeddings.json` |
| API / auth | Python, HMAC-SHA256, JSON responses |
| Proxy | Caddy (TLS, forward auth, routing by hostname) |
| Deploy | Docker (multi-stage), haloy |
| Pipeline | Bash + gcloud + rclone |

---

## Data Coverage

Each of the 533 tables belongs to one of 34 thematic domains, documented in [`overview/index.md`](overview/index.md). For every domain there is a curated narrative file describing the datasets available, the key variables, the analytical questions they support, and how the tables join to each other — written as context for LLM-assisted querying and as a reference for analysts onboarding to the platform.

| # | Domain |
|---|--------|
| 01 | Racial Inequality & Social Stratification |
| 02 | Education, Social Mobility & Inequality |
| 03 | Health, Service Access & Social Determinants |
| 04 | Labor Market, Informality & Stratification |
| 05 | Politics, Representation & Electoral Behavior |
| 06 | Crime, Violence & Public Security |
| 07 | Economy, Credit & Regional Development |
| 08 | Public Policy, Transfers & Social Protection |
| 09 | Gender, Family & Demographic Dynamics |
| 10 | Environment, Development & Sustainability |
| 11 | Infrastructure, Services & Quality of Life |
| 12 | Intersectionality & Compound Inequalities |
| 13 | Migration, Urbanization & Spatial Transformation |
| 14 | Consumption, Prices & Class Stratification |
| 15 | Power, Elites & Social Reproduction |
| 16 | Political Economy & Development |
| 17 | Agriculture, Land Structure & Agribusiness |
| 18 | Foreign Trade, Global Integration & Value Chains |
| 19 | Financial Markets, Investment Funds & Capital Structure |
| 20 | Science, Technology, Scholarships & Academic Output |
| 21 | Corruption, Administrative Misconduct & Public Oversight |
| 22 | Climate, Wildfires & Temperature Variation |
| 23 | Epidemiology, Infectious Diseases & Health Surveillance |
| 24 | Outpatient, Hospital & SUS Procedure Data |
| 25 | Federal Budget, Parliamentary Amendments & Budget Execution |
| 26 | Public Servants, Personnel Management & State Elites |
| 27 | Opinion Polls, Public Perception & Political Behavior |
| 28 | School Violence, Educational Security & Learning Environment |
| 29 | Detailed Electoral Data, Litigation & Supreme Court |
| 30 | Productive Structure, Companies, SMEs & Competitive Dynamics |
| 31 | Human Development, Social Vulnerability & Composite Indices |
| 32 | Connectivity, Digital Education & Telecom Infrastructure |
| 33 | Comparative International Data & Global Rankings |
| 34 | Atlas, Georeferenced Maps & Territorial Bases |

---

## Pipeline

```bash
./scripts/roda.sh --dry-run    # estimate size and export cost
./scripts/roda.sh              # run locally
./scripts/roda.sh --gcloud-run # spin up GCP VM, run, auto-delete
```

```
BigQuery → GCS (Parquet+zstd, parallel) → Hetzner S3 (rclone streaming, no local disk)
```

Auto-resumes if interrupted. Schema and embedding metadata auto-generated post-run.

---

## Deploy

```bash
docker build -t rodado .
haloy deploy -f haloy.yml
```

---

## Environment

```bash
AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY   # Hetzner S3
HETZNER_S3_ENDPOINT                         # S3 endpoint URL
BASIC_AUTH_PASSWORD                         # web UI + /query auth
GEMINI_API_KEY / OPENROUTER_API_KEY         # LLM backends
SQL_GENERATOR                               # gemini | openrouter | sqlcoder
TOP_K_TABLES                                # tables sent to LLM (default: 5)
```

See `.env.sample` for full list.
