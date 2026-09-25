# `docs/context/` — a camada semântica do espelho

O espelho é parquet cru: não tem foreign key, não tem métrica nomeada e não
tem hierarquia declarada. É aqui que essas três coisas passam a existir como
**dado**, e não como prosa que o modelo tem que interpretar. `mcp_server.py`
lê esta pasta; `scripts/build_ask_web_assets.ts` (branch `ask-web`, remoto e não mesclado) lê o `metrics.json` para empacotar `web/static/index/semantica.json`. A TUI Rust que lia esse `.json` antes foi removida (`ask/` apagado em `58ab7c7`, 2026-08-23).

A regra que vale para tudo abaixo: **arquivo gerado não se edita à mão** — edite
a fonte e regenere. A coluna "Gerado por" diz qual é a fonte de cada um.

## Conhecimento escrito à mão

| Arquivo | O que é | Gerado por |
|---|---|---|
| `bridges.yaml` | **A fonte única do conhecimento de join.** 78 pontes (a coluna que significa a mesma coisa sob outro nome, com a expressão que converte uma ponta na outra), 60 conceitos-hub, 21 `false_friends`, 9 `coded_differently`, `concept_aliases` | — escrito à mão |
| `metrics.yaml` | 12 cálculos nomeados: expressão DuckDB, grain, unidade, sinônimos pt-BR, `required_filters`, `verified` | — escrito à mão |
| `hierarchies.yaml` | Rollup de município→UF→região, CNAE e CID-10. CNAE e CID são prefixais: o pai sai de `substr()`, sem join | — escrito à mão |

Três coisas destes arquivos valem mais que o resto:

1. **`resolve_join` antes de escrever join à mão.** Onde existe ponte, ela
   *substitui* a igualdade ingênua — `br_anp_combustiveis.precos` guarda `cnpj`
   sem padding, então `a.cnpj = b.cnpj` está errado e é exatamente o que um
   match por nome devolveria.
2. **`false_friends` são silenciosos e caros.** `valor` aparece em 91 tabelas de
   56 datasets significando coisas diferentes; juntar por ele dá resultado
   grande, plausível e errado.
3. **`verified` não é enfeite.** Toda ponte, métrica e `parent_expr` carrega o
   que casou quando foi rodado no beelink, com data. Sem isso a linha é
   aspiracional — trate como não conferida.

## Gerado

| Arquivo | O que é | Gerado por |
|---|---|---|
| `all_tables.txt` | 1050 `dataset.tabela`, uma por linha — a lista chapada, incluindo as 8 tabelas nativas do `.duckdb` que não têm parquet | `build_metadata_catalog.py` |
| `schemas.json` | Schema físico bruto do beelink (caminho, arquivos e tipos por tabela), 4 MB — a entrada de `sync_mcp_schema.py`, `gera_join_keys.py`, `gera_erd.py`, `gera_flow.py` e `gera_schema_graph.py`. Estava na raiz do repo até 2026-09-24 | `scripts/gera_schemas.py` (beelink) |
| `rodado-schema.json` | Schema completo que o `describe_table` do MCP lê (236 datasets, 1048 tabelas, 42.851 colunas) — inclui as 7 tabelas `duckdb_native` sem parquet (`br_ms_sipni_*`, `politicos.contato`; `_local_rais_cnpj` fica de fora, é infra), que `gera_schemas.py` não enxergava antes por só varrer diretório. Renomeado de `basedosdados-schema.json`: cobria só a porção espelhada, e o nome sobrou depois que o mecanismo passou a incluir tabela raspada e nativa também | `sync_mcp_schema.py`, a partir de `schemas.json` na raiz. Fora do git (`.gitignore`) — gerar localmente |
| `join_keys.md` | O render do `bridges.yaml` + as chaves auto-detectadas: 430 seções. `mcp_server.get_join_keys()` fatia este arquivo por `###`, então todo h3 tem que ser um nome de coluna de verdade | `gera_join_keys.py` |
| `metrics.json` | O `metrics.yaml` em JSON, consumido por `build_ask_web_assets.ts` no branch `ask-web`. O MCP lê o YAML direto | `gera_metrics_json.py` |
| `dicionario_coverage.json` | Quais colunas de quais tabelas têm decode chave→valor em `{dataset}.dicionario` — 45 datasets, 168 tabelas, 6.256 colunas | `gera_dicionario_coverage.py` |
| `schema_dict_status.json` | Estágios 1+2 de `tasks/generate-full-schema-dict.md` + uma passada de leitura humana/LLM (não regex): toda coluna STRING/INTEGER fora do `dicionario_coverage.json` etiquetada — 28.263 colunas: **8.690 `nao_verificado`** (sem fonte de significado em lugar nenhum — a etiqueta que importa), 15.842 `nao_e_codigo`, 2.442 `documentado_em_outro_lugar`, 1.289 `padrao_externo`. `describe_table` lê e expõe `nao_verificado_warning` por tabela | `gera_schema_dict_status.py` + `llm_triage_schema_dict_status.py` |

## Referência e apoio

| Arquivo | O que é |
|---|---|
| `schema_ddl.sql` | Snapshot DDL parcial (527 tabelas, 109 datasets) da porção espelhada do **Base dos Dados**. Serve de referência de procedência para `build_metadata_catalog.py` — cobre parte do mirror, não todo ele |
| `censo/` | 38 markdowns por tabela do censo IBGE, usados como contexto de prompt |

## Ordem do regen

Depois de qualquer sync que mude tabelas, nesta ordem, da raiz do repo:

```bash
python3 scripts/gera_schemas.py            # beelink        -> schemas.json (na raiz)
python3 scripts/sync_mcp_schema.py         # schemas.json   -> rodado-schema.json
python3 scripts/build_metadata_catalog.py  # beelink        -> catalog.parquet + views + all_tables.txt
python3 scripts/gera_join_keys.py          # bridges.yaml   -> join_keys.md
python3 scripts/gera_metrics_json.py       # metrics.yaml   -> metrics.json
python3 scripts/valida_metrics.py          # confere metrics.yaml + hierarchies.yaml
python3 scripts/gera_dicionario_coverage.py  # beelink      -> dicionario_coverage.json
python3 scripts/gera_schema_dict_status.py   # beelink + dicionario_coverage.json + bridges.yaml + hierarchies.yaml -> schema_dict_status.json
python3 scripts/llm_triage_schema_dict_status.py  # passada de leitura humana/LLM sobre o resultado acima — rodar sempre depois, não é automático
```

`sync_mcp_schema.py` é o passo que se esquece: sem ele o `mcp_server.py` segue
lendo o schema antigo e não enxerga nenhuma coluna nova — o `describe_table`
mente calado.
