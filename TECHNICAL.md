# rodado — Technical Reference

> This is the engineering documentation for **rodado**. For the public-facing project — a sociological reading of Brazilian public data, in Portuguese — see [README.md](README.md) and [rafapolo.github.io/rodado](https://rafapolo.github.io/rodado).

**1,024 tables · ~896 GB Parquet+zstd · DuckDB · LLM NL→SQL · Single-engineer end-to-end**

---

## Engineering competencies demonstrated

| Competency | How this project demonstrates it |
|-----------|----------------------------------|
| End-to-end delivery, prototype → production | Ingestion pipeline + semantic layer + 18-tool MCP interface, in daily use |
| Data engineering & modeling | 1,024 tables normalized to a typed ontology with join-key graph |
| Ontology design | 8 business object types with explicit relationships and canonical keys |
| Application development | `mcp_server.py` — 18 MCP tools over stdio (see `docs/MCP.md`); an earlier browser SQL shell + HTTP API is retired |
| AI/ML enablement | Semantic table selection over a doc2query embedding index (832 tables, 6,464 synthetic questions) |
| Read-only enforcement | Query type/keyword guard client-side before any SSH call reaches beelink |
| Operational durability | Resumable scraping pipelines, checkpointed ingestion |
| Sensitive data handling | CPF/CNPJ personal identifiers — read-only, no PII export |

---

## User Workflows

Three concrete analyst scenarios showing the full data → insight → decision arc.

### Workflow 1 — Compliance: company integrity check

**Situation:** A compliance team needs to verify whether companies awarded public contracts have directors appearing in other sanctioned or flagged entities.

```sql
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

### Workflow 2 — Policy: infrastructure gap prioritization

**Situation:** A state health secretariat needs to identify municipalities with critically low hospital bed coverage to prioritize federal budget allocation.

```sql
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

### Workflow 3 — Journalism: electoral spending anomalies

**Situation:** An investigative journalist tracks whether campaign spending patterns correlate with post-election public contract awards in a given state.

```sql
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

The platform models Brazilian public data as typed business objects with explicit relationships.

```
┌──────────────────────┐          ┌──────────────────────┐
│      State (UF)      │─────────▶│     Municipality     │
│  sigla_uf (322 tbl)  │   1:N    │   id_municipio       │
│  id_uf    (27 tbl)   │          │   (260 tables)       │
└──────────────────────┘          └──────────┬───────────┘
                                             │ 1:N
             ┌───────────────────────────────┼──────────────────────┐
             │                              │                       │
             ▼                              ▼                       ▼
┌──────────────────────┐  ┌──────────────────────┐  ┌──────────────────────┐
│    CensusSector      │  │   SocialIndicator    │  │   ElectoralZone      │
│ id_setor_censitario  │  │  health · education  │  │  id_municipio_tse    │
│      (27 tbl)        │  │  income · housing    │  │      (23 tbl)        │
└──────────────────────┘  │  ano/mes (389+ tbl)  │  └──────────────────────┘
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
│   cbo_2002 (8 tbl)  │     ano       (389 tbl)
│   RAIS/CAGED/CNES    │     mes       (117 tbl)
└──────────────────────┘     trimestre   (7 tbl)
```

Full map in [`docs/ERD.md`](docs/ERD.md) — pt-BR, English in [`docs/ERD_EN.md`](docs/ERD_EN.md) — one mermaid diagram per domain covering all 834 tables; join recipes in [`docs/context/join_keys.md`](docs/context/join_keys.md).

**Canonical join keys**:

| Key | Tables | Object |
|-----|--------|--------|
| `id_municipio` | 260 | Municipality |
| `sigla_uf` | 322 | State |
| `cnpj` / `cnpj_basico` | 23 | Company |
| `id_setor_censitario` | 27 | CensusSector |
| `id_municipio_tse` | 23 | ElectoralZone |
| `cbo_2002` | 8 | OccupationClass |
| `cnae_2_subclasse` | 6 | EconomicActivity |
| `cpf` | varies | Person |
| `ano` | 389 | Temporal partition |

---

## Architecture

Everything is local: partitioned Parquet+zstd on beelink, queried on-demand
by DuckDB over SSH. No live web service, no cloud object storage — an
earlier iteration (`db.xn--2dk.xyz`, a BigQuery → GCS → Hetzner Object
Storage pipeline behind `auth.py`/Caddy) has been retired; see "Previous
architecture" below for what it demonstrated while it ran.

```
┌──────────────────────────────────────────────────────────────────┐
│                       USERS / WORKFLOWS                          │
│   Compliance analysts · Policy teams · Researchers · Journalists │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                       AGENT LAYER                                │
│                                                                  │
│   Claude Desktop / Claude Code — mcp_server.py over stdio        │
│   18 tools: schema browse, semantic search, join resolution,     │
│   named metrics, read-only SQL, friendly per-theme lookups       │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SEMANTIC / ONTOLOGY LAYER                     │
│                                                                  │
│   basedosdados-schema.json   — 832-table schema registry        │
│   join_keys.md / bridges.yaml — join keys + cross-source bridges│
│   doc2query_index.json/.npy  — semantic vectors for AI (11 MB)  │
│   overview/ (34 files)       — domain narratives for LLM ctx    │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                     QUERY LAYER                                  │
│                                                                  │
│   ssh beelink '~/bin/duckdb -readonly -json ...' — single-stmt   │
│   No local DuckDB connection, no persistent server process      │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                        STORAGE LAYER                             │
│                                                                  │
│   Local disk on beelink                                          │
│   Partitioned Parquet + zstd · 1,024 tables · ~896 GB           │
│   DuckDB reads local files directly — no network, no import     │
└──────────────────────────────────────────────────────────────────┘
```

---

## Semantic Table Selection

`docs/context/doc2query_index.json` + `doc2query_vectors.npy` hold one vector per
*synthetic question* a table answers (~8/table, 6,464 questions over 832 tables,
384 dims, `paraphrase-multilingual-MiniLM-L12-v2`) — not one vector per table. An
earlier per-table index (one vector over column-name text) measured nearly
orthogonal to a real question (recall@5 1/15 on a single-table golden set) and was
replaced; see `tasks/done/mcp_search_refino.md` item 1. A table's score is the MAX
cosine similarity across its own questions, so query and index live in the same
space and no consumer has to reason over the full 1.8 MB schema.

```
Pergunta (pt-BR)
    │
    ▼
Embedding (384-d, multilingual)
    │
    ▼
Cosseno sobre 6.464 perguntas → MAX por tabela → top-K tabelas
    │
    ▼
Schema filtrado → gerador de SQL → DuckDB
```

`mcp_server.py` exposes this as the `search_tables` tool. The natural-language query
interface that consumed it is being rebuilt; this document will describe it when it ships.

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

All access is read-only, enforced client-side in `mcp_server.py` before any SSH call reaches beelink. No PII export endpoints.

### Known limitations & assumptions

- **Data freshness varies**: CNPJ register updates monthly; census data is 2010/2022; some health datasets lag 12–18 months.
- **Join cardinality**: CPF-based joins across datasets can produce unexpectedly high cardinality — validate row counts before aggregating.
- **Null density**: Some survey microdata tables (PNAD, PNADC) have high null rates in optional columns; filter explicitly.
- **Monetary values**: Always verify order of magnitude before reporting contract/budget values — trillion-real totals indicate a missing GROUP BY or partition filter.
- **Sanity protocol**: Before reporting any number, (1) state expected order of magnitude, (2) flag any row exceeding it, (3) verify via two independent query paths.

### Access model

```
Agent (Claude Desktop/Code) → mcp_server.py (stdio, read-only guard)
                             → ssh beelink → DuckDB → local Parquet
```

No public endpoint, no auth layer to manage — access is scoped to whoever
has SSH access to beelink and runs `mcp_server.py` locally.

---

## MCP server

`mcp_server.py` exposes the catalog and query layer as 18 [MCP](https://modelcontextprotocol.io)
tools for Claude Desktop/Claude Code, over stdio. Full tool inventory,
architecture diagrams and the retrieval/iteration mechanism: **[`docs/MCP.md`](docs/MCP.md)**.

```bash
pip install -r requirements-mcp.txt
claude mcp add rodado -- python3 mcp_server.py
```

Tests: `pytest tests/test_mcp_server.py` (the ssh subprocess and the embedding model are mocked — no network, no model download).

---

## Palantir Foundry mapping

Not a Foundry deployment — an open-source system that reproduces the same architectural layers, documented here for readers who know Foundry and want a quick translation.

| rodado component | Foundry equivalent |
|-----------------|-------------------|
| Parquet files on beelink | Foundry datasets |
| DuckDB engine + views | Foundry query engine |
| `basedosdados-schema.json` | Ontology schema registry |
| `join_keys.md`/`bridges.yaml` entity graph | Object type links / property mappings |
| `doc2query_index.json`/`doc2query_vectors.npy` | Semantic search index |
| `mcp_server.py` | AIP Agent tool actions |
| `overview/` domain narratives | Business context / documentation |

---

## Stack

| Layer | Technology |
|-------|-----------|
| Query engine | DuckDB, local, over SSH — no persistent server process |
| Storage | Local disk on beelink, Parquet+zstd |
| Semantic search | MAX cosine similarity over `doc2query_index.json`/`doc2query_vectors.npy` |
| Interface | `mcp_server.py`, stdio MCP tools for Claude Desktop/Code |

## Environment

```bash
BEELINK_HOST   # SSH hostname for beelink (default: beelink)
```

## Previous architecture

An earlier iteration of this project ran a public live-query service
(`db.xn--2dk.xyz`): BigQuery → GCS → Hetzner Object Storage, served by a
persistent `auth.py` DuckDB connection behind Caddy, with a browser SQL
shell and a `/query` HTTP API. That service is retired — the deployment
files it left behind (`auth.py`, `start.sh`, `Caddyfile`, `haloy.yml`,
`Dockerfile`) remain in the repo but describe infrastructure that no
longer runs. Everything today goes through beelink and `mcp_server.py`,
described above.
