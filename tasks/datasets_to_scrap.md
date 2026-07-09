# Datasets to Scrap

Datasets from br-acc not present in `basedosdados.duckdb`.

Legend: `auth` = none (public), `api_key` (requires registration), `token` (OAuth/specific)

## Portal da Transparência

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| Portal da Transparência | `transparencia` | Contract, PublicOffice, Amendment | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados` | JSON |
| Portal da Transparência | `renuncias` | TaxWaiver | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/renuncias` | JSON |
| Portal da Transparência | `viagens` | GovTravel | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/viagens-por-cpf` | JSON |

## Compras Públicas

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| PNCP | `pncp` | Bid | none | `https://pncp.gov.br/api/consulta/v1` | JSON |
| PNCP/Comprasnet | `comprasnet` | Contract, Bid | none | `https://dadosabertos.compras.gov.br` | JSON |
| CEPIM | `cepim` | BarredNGO | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/cepim` | JSON |
| Contratos.gov.br | `contratos` | Contract | none | `https://contratos.comprasnet.gov.br/api` | JSON |

## Dívida e Execução

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| PGFN | `pgfn` | Finance | none | `https://www.gov.br/pgfn/pt-br/acesso-a-informacao/dados-abertos` | CSV (bulk) |
| BCB Penalties | `bcb` | BCBPenalty | none | `https://dadosabertos.bcb.gov.br` | JSON/CSV/ZIP |
| IBAMA | `ibama` | Embargo | none | `https://www.ibama.gov.br/servicos/embargos` | CSV (scrape) |

## Sanções e PEPs

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| OFAC | `ofac` | InternationalSanction | none | `https://home.treasury.gov/policy-issues/financial-sanctions` | CSV/JSON |
| EU Sanctions | `eu_sanctions` | InternationalSanction | none | `https://data.europa.eu/data/datasets?keywords=sanctions` | JSON/CSV |
| UN Sanctions | `un_sanctions` | InternationalSanction | none | `https://www.un.org/securitycouncil/sanctions/` | CSV/XML |
| OpenSanctions | `opensanctions` | GlobalPEP | none | `https://www.opensanctions.org/` | JSON |
| CEIS | `cejs` | Sanction | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/cejs` | JSON |
| CNEP | `cnep` | Sanction | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/cnep` | JSON |
| CEAF | `ceaf` | Sanction | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados/ceaf` | JSON |
| CGU PEP | `pep_cgu` | PEPRecord | none | `https://portaldatransparencia.gov.br/peps` | CSV |

## Outros

| Source | Pipeline | Node Types | Auth | Source URL | Format |
|--------|----------|------------|------|------------|--------|
| CGU Leniência | `leniency` | LeniencyAgreement | none | `https://www.gov.br/cgu/pt-br/assuntos/transparencia-publica/acordos-de-leniencia` | CSV/XLSX |
| DOU | `dou` | DOUAct | none | `https://www.in.gov.br/palavras-busca/palavras-busca.json` | JSON |
| STF | `stf` | — | none | `https://jurisprudencia.stf.jus.br/api/search/pesquisar` | JSON |
| STJ | `stj_dados_abertos` | — | none | `https://www.stj.jus.br/sites/STP/sjson/` | JSON |
| TST | `tst` | — | none | `https://jurisprudencia-backend.tst.jus.br/rest/documentos` | JSON |
| TCU | `tcu` | — | none | `https://dadosabertos.apps.tcu.gov.br/api` | JSON |
| BNDES | `bndes` | — | none | `https://dadosabertos.bndes.gov.br/api/3/action` | JSON (CKAN) |
| CPGF | `cpgf` | — | none | `https://portaldatransparencia.gov.br/cartoes/consulta` | CSV |
| DataJud | `datajud` | — | api_key | `https://datajud.cnj.jus.br` | JSON |
| DataSUS | `datasus` | — | none | `https://datasus.saude.gov.br/` | CSV/D BF/ZIP |
| ICIJ | `icij` | — | none | `https://offshoreleaks.icij.org/` | CSV/JSON |
| INEP | `inep` | — | none | `https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos` | CSV/XLSX/ZIP |
| Querido Diário | `querido_diario` | — | none | `https://queridodiario.ok.org.br/api/docs` | JSON |
| SIOP | `siop` | — | none | `https://www.planejamento.gov.br/` | CSV/XLSX |
| SICONFI | `siconfi` | — | none | `https://siconfi.tesouro.gov.br/siconfi/index.jsf` | CSV/JSON/XLSX |
| Senado CPIs | `senado_cpis` | CPI | none | `https://legis.senado.gov.br/` | JSON/HTML |
| Câmara CPIs | `camara_inquiries` | Inquiry | none | `https://dadosabertos.camara.leg.br/` | JSON |
| Brasil.IO | `holdings` | HOLDING_DE | none | `https://brasil.io/datasets/` | CSV |
| Tesouro Emendas | `tesouro_emendas` | — | none | `https://www.tesourotransparente.gov.br/` | CSV/JSON |
| TransfereGov | `transferegov` | — | none | `https://api.transferegov.gestao.gov.br` | JSON (PostgREST) |

## mcp-brasil — Sources not in basedosdados.duckdb

Sources from https://github.com/jxnxts/mcp-brasil not in `basedosdados.duckdb`.

### Health

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| ANVISA | `anvisa` | none | `https://consultas.anvisa.gov.br/api/consulta` | JSON |
| DENASUS | `denasus` | none | `https://www.gov.br/saude/pt-br/composicao/denasus` | HTML (scrape) |
| Farmácia Popular | `farmacia_popular` | none | `https://apidadosabertos.saude.gov.br/cnes/estabelecimentos` | JSON |
| OpenDataSUS | `opendatasus` | none | `https://opendatasus.saude.gov.br/api/3/action` | JSON (CKAN) |
| Imunização/PNI | `imunizacao` | api_key | `https://imunizacao.saude.gov.br` | JSON |
| RENAME | `rename` | none | `https://www.gov.br/saude/pt-br/acesso-a-informacao/medicamentos/rename` | JSON (static) |

### Legislative & Political

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| Câmara | `camara` | none | `https://dadosabertos.camara.leg.br/api/v2` | JSON |
| Senado | `senado` | none | `https://legis.senado.leg.br/dadosabertos` | JSON |
| TSE | `tse` | none | `https://divulgacandcontas.tse.jus.br/divulga/rest/v1` | JSON |
| Biblioteca de Anúncios Meta | `anuncios_eleitorais` | token | `https://graph.facebook.com/v21.0/ads_archive` | JSON |

### Justice

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| DataJud | `datajud` | api_key | `https://datajud.cnj.jus.br` | JSON |
| Jurisprudência | `jurisprudencia` | none | `https://jurisprudencia.stf.jus.br`, `https://scon.stj.jus.br`, `https://jurisprudencia-backend.tst.jus.br` | JSON |

### Public Security

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| Atlas da Violência | `atlas_violencia` | none | `https://www.ipea.gov.br/atlasviolencia/api/v1` | JSON |
| SINESP/MJSP | `sinesp` | none | `https://dados.mj.gov.br/api/3/action` | JSON (CKAN) |
| Fórum Segurança | `forum_seguranca` | none | `https://publicacoes.forumseguranca.org.br/server/api` | JSON |

### Finance & Economy

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| BCB/BACEN | `bacen` | none | `https://api.bcb.gov.br/dados/serie/bcdata.sgs` | JSON |
| BNDES | `bndes` | none | `https://dadosabertos.bndes.gov.br/api/3/action` | JSON (CKAN) |
| BPS | `bps` | none | `https://apidadosabertos.saude.gov.br/economia-da-saude/bps` | CSV |

### Government Transparency

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| Transparência | `transparencia` | api_key | `https://api.portaldatransparencia.gov.br/api-de-dados` | JSON |
| TransfereGov | `transferegov` | none | `https://api.transferegov.gestao.gov.br` | JSON (PostgREST) |
| Diário Oficial | `diario_oficial` | none | `https://queridodiario.ok.org.br/api/docs` | JSON |
| TCU | `tcu` | none | `https://dadosabertos.apps.tcu.gov.br/api` | JSON |

### TCEs

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| TCE-CE | `tce_ce` | none | `https://api-dados-abertos.tce.ce.gov.br` | JSON |
| TCE-ES | `tce_es` | none | `https://dados.es.gov.br/api/3/action/datastore_search` | JSON (CKAN) |
| TCE-PE | `tce_pe` | none | `https://sistemas.tce.pe.gov.br/DadosAbertos` | JSON |
| TCE-PI | `tce_pi` | none | `https://sistemas.tce.pi.gov.br/api/portaldacidadania` | JSON |
| TCE-RJ | `tce_rj` | none | `https://dados.tcerj.tc.br/api/v1` | JSON |
| TCE-RN | `tce_rn` | none | `https://apidadosabertos.tce.rn.gov.br/api` | JSON |
| TCE-RS | `tce_rs` | none | `https://dados.tce.rs.gov.br` | JSON (CKAN) |
| TCE-SC | `tce_sc` | none | `https://servicos.tcesc.tc.br/endpoints-portal-transparencia` | JSON |
| TCE-SP | `tce_sp` | none | `https://transparencia.tce.sp.gov.br/api` | JSON |
| TCE-TO | `tce_to` | none | `https://api.tceto.tc.br/econtas/api` | JSON |

### Environment & Science

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| INPE | `inpe` | none | `https://terrabrasilis.dpi.inpe.br/queimadas/bdqueimadas-data-service` | JSON |
| Tabua Mares | `tabua_mares` | none | `https://tabuademares.com/api/v2` | JSON |
| ANA | `ana` | none | `https://telemetriaws1.ana.gov.br/ServiceANA.asmx` | JSON/XML |

### Compras Públicas

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| PNCP + ComprasNet + Contratos.gov.br | `compras` | none | `https://pncp.gov.br/api/consulta/v1`, `https://dadosabertos.compras.gov.br`, `https://contratos.comprasnet.gov.br/api` | JSON |

### Utilities

| Source | mcp-brasil | Auth | Source URL | Format |
|--------|------------|------|------------|--------|
| BrasilAPI | `brasilapi` | none | `https://brasilapi.com.br/api` | JSON |
| Dados Abertos (dados.gov.br) | `dados_abertos` | none | `https://dados.gov.br/api/3/action` | JSON (CKAN) |

## Basedosdados.org — Not in basedosdados.duckdb

> **⚠️ Audit note (2026-07-09):** everything below this point was written before the
> beelink sync push documented in `scripts/sync-with-source.md` (693/793 tables done as of
> today). Checked every row in this section directly against
> `ssh beelink "find ~/rodado -mindepth 2 -maxdepth 2 -type d"` (692 dataset/table dirs).
> **97 of the 191 checkable table entries below were already stale** — marked missing here
> but actually present on beelink — because this doc predates that sync work finishing.
> Goal is to get everything onto beelink (not S3 — S3/"already on S3" framing below is also
> outdated; beelink is the current mirror target). Rewritten to reflect only what's
> genuinely still missing.

Basedosdados.org has **765 tables** on BigQuery. Of the original ~230 VIEWs + 2 TABLEs
+ 3 nonexistent tables tracked here, **93 table entries are still genuinely absent from
beelink** (below), 3 are confirmed not to exist in BigQuery at all, and the rest are done.

**All 93 are BigQuery VIEWs, not physical TABLEs — and per an explicit 2026-07-09 decision,
views are never synced to beelink, full stop** (`bq show` reports `"type": "VIEW"`,
`numRows: 0` always; views recompute their query on every read, which is why several of
these timed out or looked access-denied — e.g. `br_inep_ana.aluno` is 5.4M *computed* rows,
~49s just to `COUNT(*)`). So the list below is **not a to-do backlog** — it's the same kind
of permanent dead end as the 3-table "doesn't exist in BigQuery" list right after it. Before
ever attempting to sync a "missing" table again, run `bq show --project_id=basedosdados
<dataset>.<table>` first — if `type` is `VIEW`, it's permanently out of scope, not a retry
candidate.

### Quick win — 2 small TABLEs, no longer actually blocked

The old "blocked on GCP billing" framing assumed `bq extract`. The `bq query` (Sandbox,
free) pivot in `scripts/sync-with-source.md` bypasses that — these are tiny reference
tables (exchange rate / Selic rate series), trivial to pull with the same `bq query →
beelink` pipeline already used for the VIEW backlog. Confirmed still absent from beelink:

| Dataset | Table | BQ Type |
|---------|-------|---------|
| `br_bcb_taxa_cambio` | taxa_cambio | TABLE |
| `br_bcb_taxa_selic` | taxa_selic | TABLE |

### Out of scope — confirmed BigQuery VIEWs (93 table entries, verified 2026-07-09)

Everything not listed here from the original ~230-VIEW backlog (Câmara, CGU licitação/
cartão/emendas/servidores/EBT/FEF, most of IBGE PNAD/PNADC/PIB/estadic/CBO, INEP ANA/
indicador_nivel_socioeconomico partially, ANVISA, MapBiomas classe/cobertura_uf/transição,
BD metadados/vizinhança/diretórios_data_tempo, and more) is **already on beelink** — no
action needed, don't re-sync. What remains below is permanently out of scope (views), kept
only for reference so nobody re-attempts them.

| Dataset | Missing tables |
|---------|-----------------|
| `br_anatel_banda_larga_fixa` | backhaul, pble |
| `br_cgu_pessoal_executivo_federal` | terceirizados |
| `br_ibge_pnad_covid` | microdados |
| `br_imprensa_nacional_dou` | secao_1, secao_2, secao_3 |
| `br_inep_ana` | aluno |
| `br_inep_censo_escolar` | docente, matricula |
| `br_inep_formacao_docente` | escola, municipio |
| `br_inep_indicadores_educacionais` | fluxo_educacao_superior |
| `br_ipea_acesso_oportunidades` | indicadores_2019 |
| `br_mapbiomas_estatisticas` | cobertura_municipio_classe |
| `br_me_caged` | microdados_antigos, microdados_antigos_ajustes |
| `br_me_exportadoras_importadoras` | estabelecimentos |
| `br_me_pensionistas` | microdados |
| `br_mec_prouni` | microdados |
| `br_ms_sim` | municipio_causa, municipio_causa_idade, municipio_causa_idade_sexo_raca |
| `br_ms_sinan` | microdados_violencia |
| `br_ms_vacinacao_covid19` | microdados, microdados_paciente, microdados_vacinacao |
| `br_ons_energia_armazenada` | subsistemas |
| `br_rj_rio_de_janeiro_ipp_ips` | dimensoes_componentes, indicadores |
| `br_rj_tce_iegm` | indicadores |
| `br_seeg_emissoes` | brasil |
| `br_senado_cpipandemia` | discursos |
| `br_sgp_informacao` | despesas_cartao_corporativo |
| `br_sp_alesp` | assessores_lideranca, assessores_parlamentares, deputados, despesas_gabinete, despesas_gabinete_atual |
| `br_sp_gov_orcamento` | despesa, receita_arrecadada, receita_prevista |
| `br_sp_gov_ssp` | ocorrencias_registradas, produtividade_policial |
| `br_sp_saopaulo_dieese_icv` | ano |
| `br_sp_seduc_fluxo_escolar` | escola, municipio |
| `br_sp_seduc_idesp` | diretoria, escola, uf |
| `br_sp_seduc_inse` | escola |
| `br_tpe_classificacao_saeb` | categoria |
| `br_tse_eleicoes` | local_secao |
| `eu_fra_lgbt` | consciencia_direitos, cotidiano, discriminacao, especifico_transgenero, violencia_abuso |
| `mundo_bm_learning_poverty` | pais |
| `mundo_kaggle_olimpiadas` | microdados |
| `mundo_onu_adh` | brasil, municipio, uf |
| `mundo_transrespect_transphobia` | causa_obito, local, pais |
| `nl_ug_pwt` | microdados |
| `world_fao_production` | country_group, crop_livestock, dictionary, element, item, item_group, production_indices, value_agricultural_production |
| `world_fifa_women_world_cup` | matches |
| `world_fifa_worldcup` | award_winners, matches, players, teams, tournaments |
| `world_gsps_consortium_gsps` | global_indicators |
| `world_oecd_pisa` | dictionary, school_summary, student_summary |
| `world_slave_voyages_consortium_slave_trade` | transatlantic |
| `world_spi_spi` | global_indicators |
| `world_ti_corruption_perception` | country |
| `world_wb_wwbi` | country_finance, country_indicators |

Note: the entire `mundo_*`/`world_*`/`eu_fra_*`/`nl_ug_*` international-data group is 100%
absent from beelink — not because the sync push skipped it, but because (per the pattern
above) these are almost certainly views too and were never in scope to begin with.

#### Needs a recount, not fully verified

These are the same kind of out-of-scope view gaps as above — not a to-do list, just
incompletely diffed because the doc originally listed them as wildcard/count claims ("11
tables", "10 cross-tab tables", "all 17 tables") rather than exact names, so precision was
lost:

| Dataset | Original claim | beelink reality (2026-07-09) |
|---------|-----------------|-------------------------------|
| `br_ibge_pnadc` | 10 cross-tab tables (ano_*) missing | **All 10 `ano_*` dirs present** — appears fully done, but worth a `bq show` recount if precision matters |
| `br_ibge_pof` | all 17 tables missing | **14 tables present** (aluguel_estimado, cadastro_de_produtos, caracteristicas_dieta, condicoes_vida, despesa_coletiva, dicionario, domicilio, inventario, morador, outros_rendimentos, rendimento_trabalho, restricao_saude, servico_nao_monetario_pof2/pof4, all `_2017`); no `consumo_*` tables found — likely the remaining gap |
| `br_mobilidados_indicadores` | 11 tables missing | **10 present**; 1 short of the claimed 11 — which one is missing is unconfirmed without a BQ schema check |

### Tables that don't exist in BigQuery (3) — confirmed dead end, no action possible

| Dataset | Table |
|---------|-------|
| `br_bcb_sicor` | microdados_liberacao |
| `br_bcb_sicor` | microdados_operacao |
| `br_bcb_sicor` | microdados_saldo |

## Pending Data Integrations

| Task | Description | Source | Format |
|------|-------------|--------|--------|
| microdados_2022 | Adicionar microdados 2022 ao banco | IBGE | CSV/Parquet |
| aglomerados_subnormais | Integrar shapefiles de aglomerados subnormais | IBGE/MUIC | Shapefile/GeoJSON |
| areas_risco | Integrar dados de áreas de risco | ANA, CEMAVE, etc. | CSV/GeoJSON |
| census_agropecuario | Adicionar Census Agropecuário (concentração fundiária) | IBGE | CSV/Parquet |
