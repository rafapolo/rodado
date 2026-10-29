# `_rodado_metadata/catalog.parquet` — o catálogo

Gerado por `scripts/build_metadata_catalog.py`, que também recria as views
`_rodado_metadata` (1 linha por tabela) e `_rodado_datasets` (1 linha por
dataset) no beelink. Rode-o depois de qualquer sync que mude tabelas — nunca
edite o parquet à mão. `docs/mapa/catalog.md` (a versão em markdown, com
descrições) é gerado a partir deste parquet por `scripts/gera_catalog_md.py`.

| Coluna | O que é |
|---|---|
| `dataset`, `table` | identificação; `dataset.table` é o caminho DuckDB |
| `source_name` / `source_url` / `source_type` | procedência. `Base dos Dados` + `mirror` para o espelho; nome do órgão + formato para o que o projeto raspa |
| `rows`, `num_files`, `size_bytes` | medidos via `parquet_metadata`, incluindo tabelas particionadas; para `duckdb_native` o `rows` vem de um `count(*)` no DuckDB |
| `scrape_date` | data do `done/datasets_to_scrap_done.md`, ou o mtime do parquet mais recente |
| `status` | `mirrored`, `done`, `blocked → mcp-todo`, `view_orfa`… |
| `source` | `disk` (parquet local, contado por `parquet_metadata`), `duckdb_native` (sem parquet, mas a view lê tabela nativa dentro do `.duckdb` — contado pelo próprio DuckDB) ou `view_only` (sem parquet **e** sem linhas) |
| `provenance_notes` | notas do `done/datasets_to_scrap_done.md`, truncadas em 500 chars |

Ao contar tabelas ou linhas, filtre **`source <> 'view_only'`** — nunca
`source = 'disk'`.

As 8 tabelas que eram registradas como `view_orfa` com `rows=0` não têm
parquet local, e `duckdb_native` descreve só uma delas direito. Conferido em
2026-09-24: há uma única tabela nativa dentro de `basedosdados.duckdb`, de uso
local. As 6 do SIPNI (`br_ms_sipni_dicionarios.*`,
`br_ms_sipni_doses_historicas.doses_agregadas`,
`br_ms_sipni_microdados.vacinacao_2020` — ~196M linhas no catálogo de 04/09)
são views sobre **`s3://healthbr-data/...` no Cloudflare R2**, um bucket
público de terceiros ([healthbr-data](https://github.com/SidneyBissoli/healthbr-data),
CC-BY 4.0) com token de leitura publicado no próprio README. O
`~/.duckdbrc` o lê pelo `SECRET healthbr` (restrito a esse bucket), e a trava
de arquivo libera só o prefixo `s3://healthbr-data/`. Leitura remota é lenta
(minutos num `count(*)` da `vacinacao_2020`); espelhar em disco está em
[`tasks/plans/espelhar_healthbr_data.md`](../../tasks/plans/espelhar_healthbr_data.md),
adiado por falta de HD (217,9 GiB).
