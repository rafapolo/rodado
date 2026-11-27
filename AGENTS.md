# AGENTS.md

Guia para agentes (Claude Code, Pi e outros) neste repositório. Detalhes, histórico e o porquê de cada regra: `docs/tecnico/agentes_detalhes.md`.

## O que é

Espelho de tabelas públicas brasileiras (Base dos Dados + fontes raspadas) em Parquet+zstd no beelink, `~/rodado/<dataset>/<tabela>/*.parquet`, consultado por DuckDB sob demanda. 2.184 tabelas · 352 datasets · 510 GB · 36,0 bilhões de linhas (2026-11-27). Procedência de cada fonte raspada: `tasks/done/datasets_to_scrap_done.md`.

## Consultar

```bash
ssh beelink '~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb' <<'SQL'
SET enable_progress_bar=false;
SELECT ...;
SQL
```

- Sempre `-readonly`: sem ele o DuckDB trava o arquivo para todas as outras sessões. Nunca mate quem segura o lock (é trabalho de outra sessão).
- Filtre partição (`ano`, `mes`, `sigla_uf`) em tabela grande. Dialeto DuckDB, não BigQuery.
- Antes de consultar um dataset, leia `docs/context/gotchas/<dataset>.yml`. Antes de escrever join, taxa ou per capita à mão, use `resolve_join()`/`get_metric()` (`docs/context/README.md`).
- `br_me_cnpj.estabelecimentos` já tem `nome_fantasia`: nunca junte com `.empresas` para classificar por nome.
- Antes de apresentar número: diga a ordem de grandeza esperada, marque o que passa dela e confira a contagem por duas vias.

## Proibido

- **BigQuery, GCP e `bq` para consultar dado: nunca.** A única exceção (manutenção do espelho) está em `docs/context/privado/bigquery_manutencao.md`; se o arquivo não existir na sua cópia, a exceção não vale.
- **S3/Hetzner direto: nunca.** Só o `db.rodado.xyz` (`db/`) lê `s3://baseldosdados`; o resto vai pelo beelink.
- Ferramenta nova que leia fora de `~/rodado` entra em `allowed_directories`; não desligue a trava (`enable_external_access=false`, `lock_configuration=true`).
- Endpoint ou URL de fonte em nada público (repo, página, db.rodado.xyz).

## Atualizar o espelho

- Fonte original por padrão: se a BD está atrás ou incompleta, raspe da fonte pelo gate (`scripts/scrap/atualiza_fonte.py`), no schema atual, conferido contra o espelho antes da troca.
- Depois de gravar dataset: skill `dataset-novo` (checklist em `docs/tecnico/housekeeping.md`, só local).
- Script que reescreve, ordena ou compacta parquet confere fonte x saída com `scripts/sync/confere_hash.py` antes da troca.
- Troca que tira ou muda linha antiga (recoleta, dedup, recarga) chama antes o registro de mudanças (`scripts/sync/historico.py`, no beelink `~/scripts/`): o que a fonte apagou ou alterou fica em `~/rodado/_historico/`. O gate, o `consolida` do PNCP e a recarga do TSE já chamam. Coluna que muda a cada download sem o dado mudar (carimbo de coleta, `last_seen`, `OGC_FID`) vai em `--ignora ds.tab=col` no gate, senão cada recoleta registra a tabela inteira (OpenSanctions: 681 MB de ruído em 2026-11-25).
- Toda troca promovida grava uma linha em `~/rodado/_historico/promocoes.jsonl` (`historico.py promocao`: quando, linhas antes/depois, o que saiu, hash do que foi baixado); o gate, o `consolida` do PNCP e a recarga do TSE já gravam, script novo que publica fora do gate chama também. A checagem do frescor grava `checagens.jsonl`. Consulta: views `_rodado_promocoes`, `_rodado_checagens`, `_rodado_mudancas` e colunas `ultima_promocao*`/`hash_logico` em `_rodado_metadata`.
- Hash lógico de cada tabela (`docs/integridade/`): calcula no beelink com `hash_logico.py`, exporta com `scripts/exporta_integridade.py`.
- `join_keys.md` e `metrics.json` são gerados: edite o YAML de origem.

## Só local (fora do git)

`scripts/scrap/`, `scripts/sync/`, `docs/context/privado/`, `docs/tecnico/{housekeeping,auto_atualizacao,mes_novo_cnpj,mes_novo_cno}.md` e `tasks/`. Apagar algo de `tasks/` é definitivo (sem histórico); `tasks/README.md` é o índice do que está em andamento. Lista completa e motivos: `docs/tecnico/agentes_detalhes.md`.

## Onde fica cada coisa

`docs/context/` (camada semântica: joins, métricas, gotchas, códigos) · `docs/mapa/ERD.md` (diagrama de join) · `_rodado_metadata/catalog.parquet` (catálogo, ver `docs/mapa/metadata_catalog.md`) · `mcp/MCP.md` (servidor MCP) · `db/README.md` (db.rodado.xyz) · `pages/atlas/` (rodado.xyz/atlas) · `docs/pesquisa/` (hipóteses e queries de exemplo).
