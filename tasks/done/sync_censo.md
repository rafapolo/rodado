# Sync IBGE FTP — Plano e Status

Mirror completo do `ftp.ibge.gov.br` para `~/ibge_ftp_raw/` no beelink, via
`scripts/sync/sync_censo_ftp.sh`. Resumável: pastas concluídas são ignoradas na
próxima execução; parciais retomam com `lftp --continue`.

**Script:** `scripts/sync/sync_censo_ftp.sh`
**Destino:** `~/ibge_ftp_raw/`
**Log:** `~/ibge_ftp_raw/sync.log`
**Status:** `~/ibge_ftp_raw/.sync_status`

---

## Status atual

**67 / 68 pastas concluídas — SYNC COMPLETA** ✅
**Estatcart deletado** (12GB, não necessário)
**15 GB baixados no total**

---

## Conversão para Parquet

**Script:** `scripts/sync/convert_ibge_to_parquet.py`
**Destino:** `~/ibge_ftp_parquet/<folder>/<table>.parquet`
**Total:** 52.281 arquivos parquet, 2.6 GB

Converte CSV, TXT, XLS, XLSX (via ZIP) e tabelas de PDF (via pdfplumber).
Cada parquet tem colunas de metadata: `_source_folder`, `_original_file`, `_download_date`.

---

## DuckDB Consultável

**Banco:** `~/ibge_ftp.duckdb` (98 MB, apenas views)
**Views:** 52.281 views em 58 schemas

Para consultar:
```bash
ssh beelink '~/bin/duckdb ~/ibge_ftp.duckdb'
```

Exemplo:
```sql
-- Listar schemas disponíveis
SELECT table_schema, COUNT(*) as views
FROM information_schema.tables
WHERE table_type='VIEW' AND table_schema != 'main'
GROUP BY table_schema ORDER BY views DESC;

-- Listar tabelas de um schema
SELECT table_name FROM information_schema.tables
WHERE table_type='VIEW' AND table_schema='registro_civil';

-- Consultar dados
SELECT * FROM registro_civil.casamentos__casam201 LIMIT 5;
```

---

## Legenda

| Símbolo | Significado |
|---------|-------------|
| ✅ | Concluído |
| ❌ | Deletado (irrelevante) |

---

## Tier 1 — Alto valor temático

| # | Pasta | Status | Views |
|---|-------|--------|-------|
| 1 | pense_avaliacao_nutricional_2009 | ✅ | 2 |
| 2 | Caracteristicas_etnico_raciais_populacao | ✅ | 153 |
| 3 | Mobilidade_Socio_Ocupacional_2014 | ✅ | 12 |
| 4 | seguranca_alimentar_2004_2009 | ✅ | 1 |
| 5 | Tabuas_Abreviadas_de_Mortalidade | ✅ | 33 |
| 6 | vitimizacao_acesso_justica_2009 | ✅ | 1 |
| 7 | Aspectos_das_relacoes_de_trabalho_e_sindicalicacao | ✅ | 4 |
| 8 | Estatisticas_de_Genero | ✅ | 184 |
| 9 | Tabuas_Completas_de_Mortalidade | ✅ | 64 |
| 10 | seguranca_alimentar_2013 | ✅ | 1 |
| 11 | PNS | ✅ | 27 |
| 12 | seculoxx | ✅ | 2 |

---

## Tier 2 — Médio valor

| # | Pasta | Status | Views |
|---|-------|--------|-------|
| 13 | Contas_Regionais | ✅ | 1.143 |
| 14 | Registro_Civil | ✅ | 1.307 |
| 15 | Contas_Nacionais | ✅ | 3.180 |
| 16 | pense | ✅ | 2 |
| 17 | Censo_Agropecuario | ✅ | 29.343 |
| 18 | Matriz_insumo-produto | ✅ | 18 |
| 19 | Aspectos_e_cuidados_das_criancas | ✅ | 3 |
| 20 | Retroprojecao_da_populacao | ✅ | 4 |
| 21 | Educacao_e_qualificacao_profissional | ✅ | 3 |
| 22 | Economia_Turismo | ✅ | 33 |
| 23 | Meio_Ambiente | ✅ | 57 |
| 24 | Pratica_de_esporte_e_atividade_fisica | ✅ | 2 |
| 25 | acesso_ao_cadastro_unico_2014 | ✅ | 4 |
| 26 | Indices_de_Precos_Consumidor_Harmonizado | ✅ | 208 |
| 27 | Assistencia_Social_Privada_Sem_Fins_Lucrativos | ✅ | 197 |
| 28 | Demografia_das_Empresas_e_Estatisticas_de_Empreendedorismo | ✅ | 24 |
| 29 | Tecnologias_de_Informacao_e_Comunicacao_nas_Empresas | ✅ | 119 |
| 30 | Setor_Publico | ✅ | 175 |
| 31 | Economia_da_Saude | ✅ | 117 |
| 32 | Estatisticas_de_Empreendedorismo | ✅ | 50 |
| 33 | Demografia_das_Empresas | ✅ | 83 |
| 34 | panorama_saude_brasil_20032008 | ✅ | 1 |
| 35 | Estatisticas_Sociais | ✅ | 63 |
| 36 | Acesso_a_internet_e_posse_celular | ✅ | 572 |
| 37 | Estatisticas_Vitais | ✅ | 107 |
| 38 | Indicadores_Desenvolvimento_Sustentavel | ✅ | 0 |
| 39 | Fundacoes_Privadas_e_Associacoes | ✅ | 135 |

---

## Tier 3 — Menor valor / utilidade incerta

| # | Pasta | Status | Views |
|---|-------|--------|-------|
| 40 | Projecao_da_Populacao | ✅ | 34 |
| 41 | Contagem_da_Populacao | ✅ | 871 |
| 42 | Economia_Cadastro_de_Empresas | ✅ | 405 |
| 43 | Indicadores_Sociais | ✅ | 4.342 |
| 44 | Comercio_e_Servicos | ✅ | 4.213 |
| 45 | Industrias_Extrativas_e_de_Transformacao | ✅ | 2.950 |
| 46 | Pesquisa_de_Servicos_de_Tecnologia_da_Informacao | ✅ | 5 |
| 47 | Salario_Minimo | ✅ | 2 |
| 48 | Artigos_e_Apresentacoes | ✅ | 0 |
| 49 | Pesquisa_de_Esporte | ✅ | 10 |
| 50 | Audiencia_Publica | ✅ | 0 |
| 51 | Inovacao | ✅ | 26 |
| 52 | Micro_Empresa | ✅ | 22 |
| 53 | Dimensionamento_em_areas_indigenas_e_quilombolas | ✅ | 5 |
| 54 | Pulso_Empresa | ✅ | 6 |
| 55 | Programa_de_Comparacao_Internacional_PCI | ✅ | 0 |
| 56 | Estatisticas_dos_Cadastros_de_Microempreendedores_Individuais | ✅ | 4 |
| 57 | Atualizacao_Aplicativos | ✅ | 0 |
| 58 | Documentos | ✅ | 0 |
| 59 | englishpub | ✅ | 0 |
| 60 | Metodos_Alternativos_Censo | ✅ | 4 |
| 61 | Informacoes_Gerais_e_Referencia | ✅ | 111 |
| 62 | Precos_Custos_e_Indices_da_Construcao_Civil | ✅ | 65 |
| 63 | Estoque | ✅ | 72 |
| 64 | Dados_Genericos | ✅ | 587 |
| 65 | edital | ✅ | 41 |
| 66 | Programa | ✅ | 61 |
| 67 | Estatcart | ❌ | — |

---

## Log de decisões

| Data | Decisão |
|------|---------|
| 2026-07-24 | Ordem: tier 1 → tier 2 → tier 3, menor-primeiro dentro de cada tier. |
| 2026-07-24 | `lftp mirror --continue` com 3 transferências paralelas, timeout 20s, retry infinito com backoff 30s–10min. |
| 2026-07-24 | Status file em `~/.sync_status` — tab-separado, `pasta\tdone`. Seguro matar e reiniciar. |
| 2026-07-24 | Estatcart deletado (12GB, cartografia irrelevante para consultas). |
| 2026-07-24 | Conversão para Parquet: 52.281 arquivos, incluindo extração de tabelas de PDF via pdfplumber. |
| 2026-07-24 | DuckDB: 52.281 views em 58 schemas, consultável via `~/ibge_ftp.duckdb`. |
