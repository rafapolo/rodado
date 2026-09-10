# avaliacao_infra_pesada.md — Iceberg, Airflow, NiFi, CI/CD, Kafka: onde cabem (e onde não)

Avaliação pontual, pedida em conversa, contra a arquitetura real do projeto:
mirror local de Parquet em `beelink`, DuckDB via SSH, sem serviço live, sem
concorrência de escritor. Nenhuma decisão tomada — registro pra não perder o
raciocínio, com um item que já tem ação concreta pendente.

## Veredito por tecnologia

| Tech | Veredito | Por quê |
|---|---|---|
| **CI/CD** | 🟢 vale — ação concreta abaixo | Já existe e funciona (`pages.yml`, `repository_dispatch` cross-repo); falta só estender pra validação |
| **Airflow** | 🟡 só se a dor específica crescer | O único DAG real do projeto é a sincronização `BigQuery → beelink` (`scripts/sync-with-source.md`) — resumível por sentinela, com um bug documentado (timeout de 300s registrado como `no_new_rows` em vez de `error`/`timeout`). Isso é conserto de código, não motivo pra rodar scheduler+webserver+metadata DB 24/7 pra um projeto de uma pessoa, com sync sob demanda, não em cron |
| **Apache Iceberg** | 🔴 não serve | Resolve commit atômico multi-writer sobre object storage compartilhado — aqui é single-writer, single-machine, já em Parquet+zstd. O problema real que Iceberg resolveria por baixo dos panos (sync abortado deixando `tmp*.parquet` — já aconteceu em 2026-07-05, 80 arquivos, triados em 2026-08-23) tem solução mais barata: write-to-temp + `mv` atômico, sem trazer um catálogo (Hive/REST/Glue) pra uma árvore de diretório numa máquina só |
| **NiFi** | 🔴 não serve | Resolve roteamento/backpressure/provenance entre fontes *estruturalmente parecidas*. A raspagem daqui (SICAF, SINAN, sanções, etc.) é o oposto — Python sob medida por fonte (rotação de proxy pro geo-bloqueio gov.br, parsing ad-hoc) que acabaria dentro de um processor customizado mesmo assim, agora com um servidor JVM a mais rodando |
| **Kafka Streaming** | 🔴 não serve | Zero requisito de tempo real — um consumidor (quem roda a query DuckDB), atualização por sync/raspagem em dias-a-meses, não em sub-segundo. Resolve fan-out multi-consumidor que não existe aqui |

## Ação concreta pendente (CI/CD)

Estender `.github/workflows/` (hoje só `pages.yml`) com um `validate.yml` que
roda `scripts/valida_metrics.py` em todo PR que toque `docs/context/*.yaml`.

Conferido: **não precisa de acesso a beelink**. `valida_metrics.py` valida
`metrics.yaml`/`hierarchies.yaml` só contra o snapshot commitado
`docs/context/rodado-schema.json` — falha fechado se o snapshot estiver
ausente, nunca tenta SSH. `git checkout` + `pip install pyyaml` já é
suficiente em runner do GitHub.

Pega: typo em `source_table`, DML numa expressão de métrica, `verified`
ausente, sinônimo duplicado. Não pega (por design, fora do escopo de CI):
se a métrica ainda bate com o dado real — isso é o que `verified` já marca
como responsabilidade de quem rodou no beelink, não algo que CI possa
provar sem tocar dado ao vivo.

Nada implementado ainda — é só a recomendação, com a lacuna já resolvida
(schema faltando `duckdb_native`, ver `docs/context/README.md` e o commit
`0c3c286`) que motivou a checagem original.
