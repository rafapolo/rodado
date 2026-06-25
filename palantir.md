# Palantir FDE — Application Strategy

Target role: **Forward Deployed Engineer / AI Native Engineer** (Data42, Basel, Switzerland)

---

## Training Track — Module Priority

Complete in this order for the FDE Data42 role specifically:

### S-tier (do first — map directly to JD)
| Module | Why it matters |
|--------|---------------|
| Deep Dive: Creating your first Ontology | Core FDE competency |
| Deep Dive: Building your first Application | Core FDE competency |
| Speedrun: Your first End-to-End Workflow | Shows pipeline thinking |
| Ontologize: Deep Dive Your first Ontology | Reinforces ontology model |
| Self-Guided Immersive Project | Single most important artifact |

### A-tier (operational workflow signal)
- Creating a dynamic inbox application for task tracking
- Write-back enabled Decision Support
- Embedding "What-if" Scenarios in Operations
- Speedrun: Your First Ontology Function
- Notify Alert Assignees Using Action Notifications

### B-tier (good supporting evidence)
- Build a Common Operating Picture with Geospatial Data
- Deploy and configure markers in maps
- Guided data entry form / Customizable Questionnaire
- Intro to Object Explorer

### C-tier (skip until everything above is done)
- Navigation Bar, Conditional Visibility, Conditional Formatting
- Layout Configuration, Intro to Charts
- Workshop Overview (docs/video), 3D Models

---

## Time Estimates

| Goal | Hours |
|------|-------|
| Complete all modules (exercises done carefully) | 25–40 h |
| S-tier + immersive project properly | 20–35 h |
| Build one serious portfolio project | 20–40 h |
| Interview-ready for FDE role | 80–120 h total |

**3-week plan for a working engineer:**
- Week 1: Speedruns + Ontology modules (~15 h)
- Week 2: Workshop + Application modules (~15 h)
- Week 3: Immersive project + own project (~20–30 h)

> Badges alone won't get you the role. One strong project beats 25 completed modules.

---

## This Project as a Portfolio Piece

### How to describe it (not as a data mirror — as an operational platform)

> "Operational data platform enabling natural-language and SQL-based exploration of 533 public Brazilian infrastructure datasets, with production-grade query API, reproducible ingestion pipelines, and semantic data modeling layer."

### Mapping to Palantir Foundry concepts

| baseldosdados component | Foundry equivalent |
|------------------------|-------------------|
| BigQuery export scripts | External data connectors |
| Parquet files on Hetzner S3 | Foundry datasets |
| DuckDB query engine | Foundry query engine |
| `basedosdados-schema.json` + views | Ontology / data model |
| `/query` HTTP endpoint | Foundry Functions |
| Web query interface (`db.xn--2dk.xyz`) | Workshop application |
| CLI / `ask` TUI | Internal tools / SDK |
| `scripts/roda.sh` pipeline | Foundry pipelines |
| `join_keys.md` + schema relationships | Object links / join graph |
| NL→SQL via LLM (`ask/`) | AI application layer |

**The sentence to say in interviews:**

> "This system is a lightweight analog of a Foundry stack — ingestion pipelines, partitioned dataset storage, a semantic modeling layer over 533 tables, and application-layer interfaces for both SQL and natural language queries."

---

## Architecture Diagram (Palantir Style)

Palantir diagrams are layered (not service-based), ontology-centric, and action-oriented at the top.

```
┌─────────────────────────────────────────────────────┐
│               USERS / WORKFLOWS                     │
│                                                     │
│  • Analysts querying data                           │
│  • Researchers exploring indicators                 │
│  • Developers building tools                        │
│  • Policy / infrastructure decisions                │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              OPERATIONAL OUTPUT LAYER               │
│                                                     │
│  • Data-driven decisions                            │
│  • Reproducible query workflows                     │
│  • Downstream integrations                          │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                APPLICATION LAYER                    │
│                                                     │
│  • SQL exploration interface (db.xn--2dk.xyz)       │
│  • Natural language TUI (ask/)                      │
│  • Programmatic analytics API (/query endpoint)     │
│  • Browser-accessible DuckDB shell (ttyd)           │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│             SEMANTIC / ONTOLOGY LAYER               │
│                                                     │
│  • Logical dataset modeling (DuckDB views)          │
│  • Schema definitions (basedosdados-schema.json)    │
│  • Join graph across 533 tables (join_keys.md)      │
│  • Business objects: municipality, company,         │
│    region, indicator, time series, CNPJ entity      │
│  • Semantic table embeddings for LLM selection      │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│               QUERY / ACCESS LAYER                  │
│                                                     │
│  • DuckDB engine (persistent connection)            │
│  • SQL query API (auth.py on :8081)                 │
│  • HMAC-SHA256 auth + X-Password header             │
│  • Caddy reverse proxy (access control)             │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│                  STORAGE LAYER                      │
│                                                     │
│  • Hetzner Object Storage (S3-compatible)           │
│  • Partitioned Parquet + zstd datasets              │
│  • 533 public tables, versioned                     │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│             INGESTION & PIPELINES                   │
│                                                     │
│  • BigQuery export (gcloud)                         │
│  • GCS → Hetzner S3 transfer (rclone)               │
│  • Schema normalization + metadata generation       │
│  • Resumable pipeline (scripts/roda.sh)             │
│  • GCP VM option for remote execution               │
└─────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│              EXTERNAL DATA SOURCES                  │
│                                                     │
│  • Base dos Dados (BigQuery mirror)                 │
│  • Brazilian public datasets (gov, infra, health)  │
│  • 533 curated tables across dozens of agencies    │
└─────────────────────────────────────────────────────┘
```

---

## What the Project Still Lacks (and how to close the gap)

The bottleneck is the **ontology layer** and **user workflow story** — the rest is already strong.

### 1. Make the ontology explicit
Add a section (or diagram) showing:
- **Objects**: `Municipio`, `Empresa`, `PessoaFisica`, `IndicadorSocial`, `ContratoLicitacao`
- **Links**: company → CNPJ → contracts, person → CPF → company
- **Properties**: relevant columns per object type

Even a markdown table achieves this. The `join_keys.md` file is already 80% of the way there — just frame it as an ontology.

### 2. Add one analyst workflow narrative
Pick a concrete use case, e.g.:
> "A compliance analyst investigates whether a company with public contracts has directors appearing in other flagged entities."

Show the 3 steps: data → query → decision. This is what FDEs do all day.

### 3. Optional: thin application UI
A minimal Streamlit or React page over the `/query` endpoint would close the "Workshop application" gap. Not required for application — but strong for interviews.

---

## Resume Bullet (use this, not "data mirror")

> Built ontology-driven public data platform in DuckDB with 533 Brazilian government datasets, production query API, NL→SQL interface, and automated ingestion pipelines — analogous to a Foundry deployment without the platform.

---

## Interview Script (30–60 seconds)

> "I built a production data platform that mirrors 533 Brazilian public datasets — think municipalities, companies, procurement contracts, health indicators. The system has a full ingestion pipeline from BigQuery to partitioned Parquet on object storage, a DuckDB semantic layer with a modeled join graph, and a query API with auth that analysts can hit directly. I also built a natural-language-to-SQL interface on top of it using LLMs. The architecture maps almost directly to Foundry: ingestion pipelines, a dataset layer, an ontology-like schema model, and application-layer interfaces. The main thing I'd do differently in Foundry is make the ontology explicit as first-class objects rather than implicit in the schema."

---

## Key Insight for the Role

The Data42 Basel FDE role is not primarily about passing certifications. It is about:

1. Modeling messy real-world data as usable business objects
2. Exposing that model as operational workflows users can act on
3. Deploying and operating it in a production environment

This project already demonstrates all three. The framing work above is worth more than additional badges.
