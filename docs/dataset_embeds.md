## Goal

Build an intelligent SQL generator for Base dos Dados that uses semantic search (sentence-transformers) to select relevant tables from the schema before generating SQL, with the option to use local models (sqlcoder via Ollama) or external APIs.

## Instructions

- Use sentence-transformers (all-MiniLM-L6-v2) to embed table metadata and select relevant tables based on user question similarity
- Use similarity threshold (default 0.35) instead of fixed top-k to dynamically select tables
- Implement configurable SQL generator (sqlcoder/gemini/openrouter) via env vars
- Include column descriptions from basedosdados-schema.json in table embeddings
- Generate word clouds from schema attributes and dataset names for docs

## Discoveries

- **Schema format**: basedosdados-schema.json contains 765 tables with column names, types, and descriptions (~3.8MB)
- **Embeddings work**: Using all-MiniLM-L6-v2 (384-dim) to match questions to tables
- **Threshold tuning**: Default 0.35 threshold works best - lower returns too many tables (190+), higher may miss relevant ones
- **sqlcoder issues**: Returns JSON instead of SQL when using `format: "json"` - removing it helps but still generates imperfect SQL
- **Retry mechanism**: Already built into main.rs - helps fix SQL errors automatically
- **Top donation query works**: "deputados com mais doacoes" successfully returned top 10 candidates with donation amounts (R$3.7M, R$3.3M, etc.)

## Accomplished

1. ✅ Created embed_tables.py - generates embeddings from basedosdados-schema.json
2. ✅ Created table_embeddings.json (~2MB, 765 tables)
3. ✅ Created table_selector.rs - loads embeddings, computes cosine similarity, selects tables by threshold
4. ✅ Created schema_filter.rs - extracts filtered schema from full JSON
5. ✅ Created sql_generator.rs - trait with implementations for sqlcoder, gemini, openrouter
6. ✅ Modified main.rs - integrated table selection + configurable SQL generator
7. ✅ Fixed existing Rust compilation errors in main.rs (ratatui API changes)
8. ✅ Updated README.md with new architecture and env vars
9. ✅ Created wordcloud scripts and generated wordcloud_attributes.png, wordcloud_datasets.png in docs/

## Relevant files / directories

### Created/Modified
- `embed_tables.py` - Python script to generate table embeddings
- `context/table_embeddings.json` - Pre-computed embeddings (765 tables)
- `ask/src/table_selector.rs` - Table selection via embeddings
- `ask/src/schema_filter.rs` - Schema filtering module
- `ask/src/sql_generator.rs` - SQL generator trait + implementations
- `ask/src/main.rs` - Integrated all components
- `ask/Cargo.toml` - Added serde dependency
- `README.md` - Updated with new architecture
- `docs/wordcloud_attributes.png` - Word cloud from column names/descriptions
- `docs/wordcloud_datasets.png` - Word cloud from dataset names

### Configuration (env vars)
- `SQL_GENERATOR` - sqlcoder|gemini|openrouter
- `SIMILARITY_THRESHOLD` - 0.35 default
- `OLLAMA_MODEL` - sqlcoder:7b-q4_K_M
- `EMBEDDINGS_FILE`, `SCHEMA_JSON`

## Next Steps

- Increase similarity threshold (try 0.45) to reduce table count
- Improve sqlcoder prompt for better SQL generation
- Add fallback to increase threshold if too many tables selected
- Consider keyword matching as backup if embeddings fail
