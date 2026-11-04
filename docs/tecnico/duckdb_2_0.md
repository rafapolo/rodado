# DuckDB 2.0.0 (lançada em 2026-10-21): o que muda para o espelho

Auditoria feita em 2026-11-04, comparando 1.5.6 e 2.0.0 no beelink (`~/bin/duckdb-1.5.6` × `~/bin/duckdb`,
sempre `-readonly`, mesmas consultas, saída `-json`). Fontes: notas da versão no GitHub, a página
"Migrating to DuckDB 2.0" e o guia de migração do cliente Python em duckdb.org.

## Onde cada máquina está

| máquina | CLI | python | observação |
|---|---|---|---|
| Mac | n/a | 2.0.0 | testes: 127 passed; `db/testes/mascara_cpf.py` 11/11 |
| beelink | 2.0.0 (wrapper `~/bin/duckdb`, 1.5.6 guardada em `~/bin/duckdb-1.5.6`) | 2.0.0 | `ulimit -n 65536` no wrapper e no crontab |
| finland (host) | 2.0.0 em `/root/.duckdb/cli/2.0.0` (`latest` aponta para lá; 1.5.1 fica ao lado) | 2.0.0 | cron do `compacta.py` com `ulimit -n 65536` |
| container db.rodado.xyz | 2.0.0 (deploy à parte) | 2.0.0 | ver `db/README.md` |
| livre | sem DuckDB | n/a | só nginx |

Voltar atrás no finland: `pip install --break-system-packages duckdb==1.5.1` e
`ln -sfn /root/.duckdb/cli/1.5.1 /root/.duckdb/cli/latest`.

## Mudanças incompatíveis e se nos afetam

| mudança | afeta? |
|---|---|
| formato de armazenamento novo por padrão (`storage_compatibility_version = latest`): 1.5 não abre arquivo `.duckdb` criado pela 2.0 | só se criarmos `.duckdb` novo com a 2.0 para a 1.5 ler. `basedosdados.duckdb` (views) mantém a versão antiga ao ser regravado. Parquet não muda: um parquet escrito pela 2.0 abre na 1.5.6 e no pyarrow (testado) |
| lambda `x -> f(x)` desligada (usar `lambda x: f(x)`) | corrigido no db/ e no mcp (commits do dia 2026-11-04); sem outro uso no repo, no beelink e no finland |
| `//` e `%` por zero dão erro (1.5 dava NULL); `/` por zero segue `inf` | não há divisor possível de ser zero nas consultas do repo (`scripts/scrap/bcb_sicor_proagro.py` divide por 100); em consulta nova use `TRY(a // b)` ou `NULLIF` |
| `~` e `!~` fazem casamento parcial (antes, completo) | medido: `'abc' ~ 'b'` era false e agora é true. Nenhum uso de `~` no repo |
| `!` fatorial, `X'..'` e `B'..'` viram BLOB e BITSTRING | não usamos |
| erro dentro de transação aborta a transação | não usamos transação explícita |
| `MERGE INTO` com várias linhas de origem por alvo dá erro | não usamos |
| NULL sem tipo mantém o tipo "NULL" | sem efeito observado |
| `-json` do CLI | idêntico, mas o nome gerado de coluna sem alias mudou (ver abaixo) |
| settings `enable_http_logging`, `http_logging_output`, `custom_profiling_settings` removidos | não usamos |
| URL do S3 com parâmetros desligada | não usamos |
| ICU saiu do núcleo (vira extensão) | `icu` está instalada no beelink; fusos e calendário iguais nos testes |
| extensões precisam de INSTALL na 2.0 | httpfs, icu, json e spatial instaladas no beelink |
| CLI em "agent mode" quando `AI_AGENT` está no ambiente | wrapper do beelink faz `unset AI_AGENT` |
| Python >= 3.11 | beelink 3.14, finland 3.13, Mac 3.11+ |
| API python: `fetchone`/`fetchmany` em relação (`con.sql`), `fetch_record_batch`, `.arrow()`, `.pl()` no `execute`, `params=` | corrigido; varreduras AST (`acha_rel`/`acha_pendente`) limpas no repo |
| resultado de `execute()` não lido até o fim bloqueia o próximo `con.sql()` | corrigido em db/ (drena com `fetchall()`) |
| conexão compartilhada entre threads dá `ResourceInUseException` | os scrapers com thread abrem uma conexão por tarefa |
| 2.0 abre mais arquivos ao mesmo tempo | `ulimit -n 65536` |
| httpfs lê o bundle de CA do disco | `SET allowed_paths=['/etc/ssl/certs/ca-certificates.crt']` em db/rodado_sql.py e mcp/mcp_server.py |

## Diferenças de resultado medidas (1.5.6 × 2.0.0), no beelink

Iguais: métricas de `metrics.yaml` (população, óbitos, nascimentos, vínculos RAIS, saldo CAGED, contagem
por UF), `sum(hash(t))` de tabelas reais, `hash()` de texto, número, lista, struct e data, divisão inteira
e decimal, `ROUND`, ordenação de texto (maiúscula antes de minúscula, acento por último, NULL por último),
fuso e `strftime`, `read_csv` (tipos inferidos, `decimal_separator`), `read_json`, `read_parquet` com
`hive_partitioning` e `union_by_name`, `TRY_CAST`, saída `-json` de HUGEINT, DECIMAL, data, hora, lista, mapa.

Diferentes:

- **`approx_count_distinct` e `approx_quantile` mudaram de algoritmo.** Em `range(1, 100001)`:
  1.5.6 deu 96.025 (exato 100.000) e mediana aprox. 50.000; a 2.0 deu 99.442 e 49.913. Quem usa
  (`scripts/gera_schema_dict_status.py`, `scripts/gera_perfil.py`, `scripts/inventaria_tipos.py`,
  `scripts/hipoteses/h3_9*.sql`) vai ver números um pouco diferentes ao regerar; não comparar com
  saídas antigas como se fossem a mesma medida.
- `mode()` com empate escolhe outro valor (1 contra 5 num empate total). `20_conhecidos.sql` usa
  `mode(substancia)`: o resultado de empate pode mudar.
- Ponto flutuante nas últimas casas de `stddev`, `var_pop`, `corr`, `skewness`, `kurtosis`
  (diferença de 1e-15 a 1e-13). Nunca comparar com igualdade exata.
- **Nome de coluna gerado sem alias:** `CAST(sum(x) AS "HUGEINT")` virou `CAST(sum(x) AS HUGEINT)`,
  `main.list_value(...)` virou `list_value(...)`, `list(x ORDER BY x)` deixou de ser reescrito para
  `list_sort(list(x), ...)`. Código que lê o resultado por nome gerado quebra: sempre pôr alias.
- Mensagens de erro ganharam sublinhado de posição e uma dica sobre `-agent` no stderr.
- O CLI 2.0 grava `created_by = DuckDB version v2.0.0` nos parquet novos; o formato do parquet
  (versão 1, SNAPPY por padrão, PLAIN) é o mesmo, só entram campos extras de metadado de estatística.

## compacta.py (finland) na 2.0

`sum(hash(t))` deu o mesmo valor nas duas versões em dois arquivos reais (500.480 e 315.611 linhas),
e o compacta calcula o hash do original e do comprimido na mesma conexão, na mesma versão, então uma
diferença de hash entre versões nem chegaria a ser comparada. A recompressão zstd 19 pela 2.0 deu
tamanho 0,05% maior no arquivo testado (20.013.032 contra 20.003.275 bytes), sem importância.
