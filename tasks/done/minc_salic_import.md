# SALIC/Lei Rouanet (MinC) — importado de ../Mostre

**Status: feito (parcial) — 2026-08-25.** Ver a linha correspondente em
[`done/datasets_to_scrap_done.md`](datasets_to_scrap_done.md) (tabela Tier 1a) para o
registro oficial de provenance que o `build_metadata_catalog.py` lê.

## O que é

Dados do SALIC (Sistema de Apoio às Leis de Incentivo à Cultura, Ministério da Cultura) —
projetos culturais aprovados via Lei Rouanet, patrocinadores, incentivos e recibos de
repasse. Não é um scrape deste projeto: os dados vêm já consolidados de um projeto pessoal
separado, `../Mostre`, que tem seu próprio pipeline (dump MySQL legado 2013–2016 + sync
contra a API viva `api.salic.cultura.gov.br`, atrás de Cloudflare — precisa de um browser
real pra resolver o desafio JS, ver `../Mostre/db/mostre.py`).

Este projeto só lê o SQLite já consolidado de Mostre (`storage/development.sqlite3`) e
empurra cada tabela como Parquet+zstd pra beelink. Sem fetch, sem API, sem auth daqui.

## Como rodar de novo

```bash
cd ../rodado
source .venv/bin/activate
python3 scripts/scrap/minc_salic.py
```

Lê direto de `/Users/polux/Projetos/Mostre/storage/development.sqlite3` (read-only) e faz
`rsync` de cada tabela pra `beelink:~/rodado/br_minc_salic/<tabela>/`. Idempotente — pode rodar
de novo a qualquer momento pra atualizar o mirror com o estado atual de Mostre.

## Tabelas no beelink

| Tabela | Linhas | O que é |
|---|---|---|
| `projetos` | 196.539 | 136.257 do dump antigo (2013–2016) + 60.282 da API viva (PRONACs 164380–266608, ~2024–2026) |
| `entidades` | 217.643 | Proponentes e patrocinadores; 152.793 marcadas `patrocinador=1` |
| `incentivos` | 173.754 | **Só dump antigo** — ver gap abaixo |
| `recibos` | 245.640 | **Só dump antigo** — ver gap abaixo |
| `areas` | 7 | Taxonomia oficial do MinC |
| `segmentos` | 106 | Subdivisões por área |
| `estados` | 28 | Dimensão geográfica |
| `cidades` | 5.599 | Dimensão geográfica |

`areas`/`segmentos`/`estados`/`cidades` são tabelas de dimensão pequenas incluídas pra este
dataset ser joinável sozinho (via `area_id`/`segmento_id`/`estado_id`/`cidade_id`) sem
precisar espelhar o schema inteiro de Mostre.

## Gap conhecido — incentivos/recibos não cobrem 2024–2026

`incentivos` e `recibos` só têm o dump antigo (2013–2016). Os 60.282 projetos novos da API
viva não têm captação/repasse ainda — isso precisa do endpoint `/projetos/{pronac}` por
projeto, muito mais lento e mais limitado por Cloudflare (`sync por_projeto` em Mostre,
resumível, ~5-10k projetos por sessão). Não rodado ainda nesta importação.

**Quando isso rodar em Mostre:** re-executar `scripts/scrap/minc_salic.py` aqui pra
atualizar `incentivos`/`recibos` (e as outras tabelas, sem custo — o script sempre reexporta
tudo).

## Pegadinha no PRONAC — não usar `numero` cegamente como PRONAC

`projetos.numero` mistura dois esquemas: PRONAC de verdade (6 dígitos) e um código de
edital não-PRONAC de 7 dígitos (`"Prêmio Pontos de Valor"` 2009, e uma faixa parecida
já na API viva) — 15.449 linhas ao todo. Não quebra a identidade da linha (`numero`
continua único), mas **não é um PRONAC válido** pra cruzar com outras fontes Lei Rouanet
por PRONAC. Filtrar por `length(numero) <= 6` quando isso importar.

## Depois de rodar

```bash
cd ../rodado
python3 scripts/build_metadata_catalog.py   # beelink -> catalog.parquet + views
```

Provenance já está em `done/datasets_to_scrap_done.md` — o catalog builder lê de lá
automaticamente, não precisa editar nada além disso se só os números de linhas mudarem.

---

## ✅ Arquivado em 2026-09-02

Import feito (parcial) em 2026-08-25, sem pendência acionável. O registro
oficial de provenance que `build_metadata_catalog.py` lê está na tabela
Tier 1a de [`datasets_to_scrap_done.md`](datasets_to_scrap_done.md).
