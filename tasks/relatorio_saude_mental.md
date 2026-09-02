# Relatório de saúde mental — dados disponíveis no espelho

> Aberto em 2026-09-01, a partir de um levantamento do que o espelho tem para
> relatórios sobre questões psiquiátricas e psicológicas. Ainda não é um
> relatório — é o mapa do que dá para responder e do que falta, antes de
> escolher um recorte (município, período, tema) e escrever
> `pages/analises/results/*.md`.

## Tabelas já mapeadas

| Tabela | O que dá | Chave/filtro |
|---|---|---|
| `br_ms_sia.psicossocial` | Atendimentos em CAPS/serviços psicossociais do SUS, mensal, por município. `cid_principal_categoria/subcategoria` (diagnóstico), `tipo_droga`, `indicador_situacao_rua`, idade/sexo/raça | `ano`, `id_municipio` |
| `br_ms_cnes.leito` | Leitos de psiquiatria por estabelecimento/município — capacidade instalada, não atendimento | `id_municipio`, especialidade |
| `br_ms_sih.aihs_reduzidas` | Internações SUS (AIH); não é específica de psiquiatria, mas `especialidade_leito` + `cid_principal_categoria/subcategoria` (e 9 diagnósticos secundários) permitem filtrar por CID F00-F99. Tem custo (`valor_aih`), permanência, óbito (`indicador_obito`) | `cid_principal_categoria` LIKE 'F%' |
| `br_ms_sim.microdados` | Óbitos (SIM). `causa_basica` em CID-10 isola suicídio (X60-X84) e transtorno mental como causa (F00-F99); cruza com `circunstancia_obito`, idade, sexo, escolaridade, município | `causa_basica`, `id_municipio_residencia` |
| `br_ms_sinan_violencia.microdados_violencia` | Notificação de violência interpessoal/autoprovocada (SINAN). Colunas específicas: `LES_AUTOP` (lesão autoprovocada), `CONS_SUIC` (ideação/tentativa de suicídio), `CONS_MENT` (transtorno mental como consequência), `TRAN_MENT`/`TRAN_COMP` (transtorno preexistente), `DEF_MENTAL`, `AUTOR_ALCO` | `ID_MUNICIP`, `NU_ANO` |
| `br_datasus_cid10.codigos` | Referência CID-10 — monta a lista de códigos F00-F99 (transtornos mentais) e X60-X84 (suicídio) usada nos filtros acima | lookup |

**Cuidado ao decodificar:** `sexo`, `raca_cor`, `estado_civil` em `br_ms_sim.microdados` têm código que **diverge por tabela** — sempre decodificar via `br_ms_sim.dicionario`, nunca reusar código de outra fonte (ver `coded_value_warning` do `describe_table`).

## Ainda não explorado

- `br_ms_pns.microdados_2013` / `microdados_2019` (Pesquisa Nacional de Saúde) — checar se o módulo de saúde mental autorreferida (diagnóstico de depressão, etc.) está nas colunas.
- `br_ms_cnes.estabelecimento` — para localizar CAPS especificamente por tipo de estabelecimento (hoje só temos leito por especialidade, não o estabelecimento em si).
- `resolve_join` entre `psicossocial`/`aihs_reduzidas`/`sim` — nenhuma ponte foi conferida ainda; se o recorte cruzar duas dessas tabelas, rodar `resolve_join` antes de juntar por `id_municipio` à mão.

## Lacunas conhecidas

- Nenhuma tabela dá **prevalência de transtorno mental na população geral** — só atendimento (demanda que chegou ao SUS) ou óbito. Sub-representa quem não busca/consegue atendimento.
- Sem cobertura de rede privada/planos de saúde — todas as fontes são SUS (SIA, SIH, CNES) ou vigilância (SIM, SINAN).

## Próximos passos

1. Escolher o recorte do relatório (nacional? um município como os outros `pages/analises/`? um tema — CAPS, suicídio, internação por transtorno mental?).
2. Rodar `describe_table` em `br_ms_pns.microdados_2013/2019` para fechar a lacuna de prevalência autorreferida.
3. Conferir `resolve_join` entre as tabelas antes de qualquer cruzamento.
4. Seguir o padrão de `pages/analises/results/*.md` — citar a fonte do dado (SIA/SIM/SINAN/CNES), nunca a ferramenta (ver `feedback_analises_sem_detalhe_tecnico` em memória).
