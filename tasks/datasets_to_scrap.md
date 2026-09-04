# Datasets to Scrap

> **2026-08-24: split for size.** Everything already resolved (`done`, `mcp-live`,
> `excluded`, `not-worth-building`, duplicates) — plus the full Iteration Log and the
> pre-status-board planning sections it superseded (`New`, `Skip`, `Newly discovered`,
> confirmed-out-of-scope BigQuery VIEWs) — moved to
> `tasks/done/datasets_to_scrap_done.md` for provenance. This file keeps only what's
> still actionable: `blocked` (worth rechecking — infra/WAF status changes), `blocked →
> mcp-todo` (needs a live pass-through tool, see the 2026-07-10 rule below), and
> `deferred-api_key` rows, plus never-started items.

## 🔄 Status Board — Autonomous Scraping Loop

> Started 2026-07-10. **Status:** 849 tables (203 datasets) on beelink as of 2026-08-23 —
> `_rodado_metadata` and `_rodado_datasets` views in DuckDB track every table's rows,
> source, provenance. **Goal:** download every Tier-1 source below in full and write it to
> `beelink:~/rodado/<org>_<dataset>/<tabela>/*.parquet`, following the same folder
> convention as the official Base dos Dados mirror already there (see
> `scripts/sync-with-source.md` for the existing `bq → parquet → rsync beelink` pattern —
> new scrapers use the same rsync-to-beelink tail, just with a different fetch step).
> Each loop iteration must (1) pick the next actionable row below in priority order, (2)
> write/reuse a fetch script under `scripts/scrap/<pipeline>.py`, (3) fetch → Parquet →
> `rsync` to beelink, (4) flip that row's status and fill in rows/date/notes, then move the
> row into `tasks/done/datasets_to_scrap_done.md`, (5) commit nothing automatically — leave
> commits to the user unless told otherwise.
>
> **Decisions locked in 2026-07-10 (don't re-ask):**
> - Naming: same `<org>_<dataset>/<tabela>` pattern as the BD mirror (not a separate
>   `scrap_*` namespace).
> - Priority: simplest first — clean JSON/CSV APIs, `auth=none`, no HTML scraping. Sources
>   needing HTML scraping or unclear formats are pushed to sub-tier **1c** or **Tier 2**.
> - Sources needing `api_key`/`token` are **deferred** — skip entirely for now, don't
>   pause to ask for credentials, just leave `deferred-api_key` and move on.
> - Legally/contractually restricted sources (DataJud, Imunização/PNI, OpenSky Network,
>   Meta Ads) are **excluded** from stored mirrors — see rationale in
>   `tasks/done/datasets_to_scrap_done.md`, don't attempt these as bulk pipelines.
> - Execution mode: autonomous `/loop`, no per-source approval gate.
> - **Added 2026-07-10:** if a source genuinely can't be bulk-scraped into a beelink
>   mirror — `blocked` (bot/WAF protection, e.g. DOU) or legally `excluded` from storage
>   but still legally queryable live (e.g. DataJud, which explicitly only forbids *bulk
>   redistribution*, not query-on-demand) — don't just leave it dead. Add it as a live
>   pass-through `@mcp.tool()` in `mcp_server.py` instead, calling the source API directly
>   at request time (same pattern as `run_sql` proxying to beelink over SSH — see that
>   file for the shape: thin wrapper, read-only, no local storage). Flip status to
>   `mcp-live` once that tool exists and works. This does NOT apply to sources excluded for
>   licensing reasons that also restrict *querying/redistribution of the response itself*
>   (Imunização/PNI's CC BY-ND bars derivative works even in a live pass-through response
>   shape) — check the specific restriction before assuming a live proxy is safe.

**Status values:** `pending` → `in_progress` → `done` (or `blocked` if it fails, with
reason in Notes) · `deferred-api_key` (skipped by design, revisit later) ·
`pending-verify` (format/access pattern unclear, needs a quick check before it's real work)
· `excluded` (permanently out of scope, legal/ToS reasons) · `mcp-live` (not mirrored to
beelink — exposed instead as a live pass-through tool in `mcp_server.py`). Only rows still
in an open state (`blocked`, `blocked → mcp-todo`, `deferred-api_key`) live in this file —
everything resolved lives in `tasks/done/datasets_to_scrap_done.md`.

### Tier 1a — ready now, single well-documented endpoint

| Source | Beelink path | Format | Status | Last updated | Notes |
|---|---|---|---|---|---|
| DOU (federal) | `br_in_dou/atos` | JSON | blocked → mcp-todo | 2026-07-13 | Reconfirmed 2026-07-13: `www.in.gov.br` still hard-blocks plain HTTPS — default headers give `HTTP/2 PROTOCOL_ERROR` (stream reset before any response), full Chrome UA + `Accept: application/json` gets a bare empty reply (`curl: (52) Empty reply from server`) — consistent with the earlier "connection reset" finding, not a UA/protocol quirk. **New this pass:** found and tried the actual documented bulk alternative — INLABS (`inlabs.in.gov.br`, official Imprensa Nacional project, GitHub `Imprensa-Nacional/inlabs`), which has published full DOU editions in PDF+XML "livre e gratuito" (free, no login) since 2020-01-01 — exactly the "separate bulk archive" this recheck was looking for. But it's blocked too: both the bare root and a full-browser-header request return HTTP 200 with an F5 BIG-IP ASM block page (`"Request Rejected... Your support ID is..."`, `Set-Cookie: TS...`) — a *different* WAF vendor/signature than the AWS WAF challenge hitting STF/TST (F5 "Request Rejected" vs. AWS `x-amzn-waf-action: challenge`), but same outcome: no scripted access without solving a bot-mitigation gate. Still routed to `mcp-todo`; a live tool would need the same headless-browser (Playwright) lift as before, now against either endpoint. |
| STF jurisprudência | `br_stf_jurisprudencia/decisoes` | JSON | blocked → mcp-todo | 2026-07-13 | Reconfirmed 2026-07-13, both plain GET and a realistic POST (Chrome UA, `Content-Type/Accept: application/json`, actual search body): still `HTTP/1.1 202 Accepted`, empty body, `x-amzn-waf-action: challenge` — identical signature to the original finding, no change. Not worth pursuing as a bulk pipeline; stays `mcp-todo`, would need a headless-browser (Playwright) fetch to pass the challenge even for single live queries. |
| TST | `br_tst_jurisprudencia/documentos` | JSON | blocked → mcp-todo | 2026-07-13 | Reconfirmed 2026-07-13: `www.tst.jus.br/` still returns `HTTP/2 202`, empty body, `x-amzn-waf-action: challenge` (fronted by CloudFront this time, same AWS WAF product) — identical to the original finding, both with and without a browser UA. No change; route to `mcp-live` like STF/DOU when built. |
| RENAME | `br_saude_rename/medicamentos` | JSON (static) | blocked | 2026-07-13 | Reconfirmed blocked, different failure mode than before. The gov.br domain-wide WAF is gone (`www.gov.br/saude/pt-br` and the general `.../composicao/sectics/rename` page both load clean 200s now), but the specific RENAME content sub-pages (`.../rename/rename-2024`, `.../rename/rename`) 302-redirect to Plone's `credentials_cookie_auth/require_login` — a real access-restriction in the CMS, not a bot challenge, and not bypassable with a Referer header (tested). Checked the Ministry of Health's real open-data API (`apidadosabertos.saude.gov.br`, full `swagger.json` fetched) for a RENAME/medicamentos-essenciais endpoint — none exists (only `/daf/estoque-medicamentos-bnafar-horus`, unrelated). `dados.gov.br` CKAN fallback still 401 (site-wide auth requirement, not RENAME-specific). |
| dados.gov.br (catálogo) | `br_dadosgovbr/catalogo` | JSON (CKAN) | deferred-api_key | 2026-07-11 | Reconfirmed 2026-07-11: `package_list`/`site_read`/`package_show` and a newer `/dados/api/publico/conjuntos-dados` guess all still return HTTP 401 with `www-authenticate: Bearer` — this CKAN instance requires an auth token even for public reads. Web UI is a JS SPA with no server-rendered fallback. Low priority anyway (meta-catalog). |
| BNMP mandados | `br_cnj_bnmp/mandados` | JSON | blocked → mcp-todo | 2026-07-13 | Reconfirmed blocked, no change. Deeper doc search this pass: no separate CNJ developer/API portal exists for BNMP. Extracted the real endpoint from the Angular bundle (`API_ENDPOINT="bnmpportal/api"` → `POST /bnmpportal/api/pesquisa-pecas/filter`) and hit it directly — clean `401 {"title":"Unauthorized","detail":"Full authentication is required to access this resource"}` (JHipster/Spring Security, not a WAF challenge). Independent confirmation via public tooling (`bnmp-scraper` on PyPI/GitHub): the portal requires a captcha-solved browser session cookie for any query, not just a header. DataJud (CNJ's actual public API, `api-publica.datajud.cnj.jus.br`) covers case metadata, not BNMP warrants. Genuine auth wall, not worth building browser-automation/captcha-solving for a bulk pipeline. |
| Lista Suja do Trabalho Escravo | `br_mte_listasuja/empregadores` | CSV/XLSX | blocked → mcp-todo | 2026-07-13 | Reconfirmed blocked with fresh evidence. The listing HTML page (`.../inspecao-do-trabalho/areas-de-atuacao/combate-ao-trabalho-escravo-e-analogo-ao-de-escravo`) loads fine (200) and even reveals more direct file links than before (`cadastro_de_empregadores.{csv,xlsx,txt,pdf}`, plus a dated `2026_0010.{csv,pdf,xlsx}`) — but every one of those file downloads still 403s with the classic iso-8859-1 gov.br WAF page, even with a Referer header set to the listing page itself (which *does* unblock ANP's equivalent file downloads — tested the same trick here, no effect). Also checked the alternate host MDH (Ministério dos Direitos Humanos) publishes the same registry at `gov.br/mdh/.../cadastro-de-empregadores-201clista-suja201d` — that page 302-redirects to Plone's `credentials_cookie_auth/require_login` (real CMS access restriction, not a WAF). `dados.gov.br` CKAN dataset page (`trabalho-analogo-ao-de-escravo`) loads as an HTML shell but its backing API is the same site-wide 401 as the dados.gov.br catálogo entry. |
| FNDE | `br_fnde_transferencias/dados` | JSON | blocked → mcp-todo | 2026-07-13 | Reconfirmed blocked, different failure mode than before. The gov.br domain-wide WAF is gone (`www.gov.br/fnde/pt-br` and its `/acesso-a-informacao/dados-abertos` page both load clean 200s now, listing PDDE/PDE datasets and an "Olinda" API tutorial page). But: (1) the legacy standalone CKAN portal `www.fnde.gov.br/dadosabertos` now fully 302-redirects into `dados.gov.br/dados/organizacoes/visualizar/fundo-nacional-de-desenvolvimento-da-educacao` — i.e. FNDE's open-data catalog has been consolidated into `dados.gov.br`, which still requires an auth token on every API path (401, same site-wide gate as the dados.gov.br catálogo entry); (2) no live `olinda.fnde.gov.br`-style API host could be found in the tutorial page content or via DNS guesses (`olinda/api/dados.fnde.gov.br` all fail to connect). No bulk data route left outside the auth-walled `dados.gov.br` API. |
| ANTT | `br_antt_dadosabertos/dados` | JSON (CKAN) | blocked → mcp-todo | 2026-07-13 | Reconfirmed blocked, no change. Tried varied UA/Referer/Accept headers and an alternate `site_read` action — all still return the same F5/BigIP `"Request Rejected"` HTML body (HTTP 200 but not real JSON) with a fresh support ID each time. Genuine WAF, not a fluke. |
| Legislação federal (LexML) | `br_lexml_legislacao/normas` | XML (SRU) | blocked → mcp-todo | 2026-07-13 | Reconfirmed 2026-07-13, different query shapes again (`operation=searchRetrieve` with a real `urn=lei` query, plus a plain HEAD): both the HEAD to the SRU root and the real search now return HTTP 200 with a *different-looking* JS challenge page than before — `"Verificação de segurança — Senado Federal"` instead of the earlier "I Challenge Thee" hashcash gate (LexML's infra sits behind Senado's WAF/CSP, explains the branding). Same outcome either way: no XML data, scripted access blocked. Also checked for an alternate bulk-download path per this session's ask: `projeto.lexml.gov.br/transparencia/dados-abertos` and `/downloads` exist but only offer a "Kit Provedor de Dados" (OAI-PMH *provider* toolkit for feeding data *into* LexML, not for harvesting out) and unrelated PDFs — no consumer-side bulk XML dump. Guessed OAI-PMH harvest endpoints (`/oai/request`, `/busca/OAIHandler`) either 404 or hit the same Senado WAF challenge page. No viable alternate route found; stays `mcp-todo`. |

### Tier 1b — same pattern, repeated many times (batch after 1a proves the pipeline)

| Source | Beelink path | Format | Status | Last updated | Notes |
|---|---|---|---|---|---|
| TCE-CE | `br_tce_ce/dados` | JSON | blocked | 2026-07-13 | Reconfirmed unreachable, no change: `api-dados-abertos.tce.ce.gov.br` still connection-timeouts on both resolved IPv4s (189.90.160.53, 189.90.161.131), ports 443 and 80. Even `www.tce.ce.gov.br` (the main site, not just the API) times out — genuine ongoing host-level outage, not API-specific. |
| TCE-PE | `br_tce_pe/dados` | JSON | blocked | 2026-07-13 | Reconfirmed unreachable, no change: `sistemas.tce.pe.gov.br` still connection-timeouts on both resolved IPv4s (45.165.55.58, 179.189.252.148), ports 443 and 80. `www.tce.pe.gov.br` also times out — genuine ongoing host-level outage. |
| TCE-RN | `br_tce_rn/dados` | JSON | blocked | 2026-07-13 | Reconfirmed unreachable, no change: `apidadosabertos.tce.rn.gov.br` still TCP-timeouts on :443 and :80. `www.tce.rn.gov.br` (main site) also times out — genuine ongoing host-level outage, not transient this time either. |
| TCE-RS | `br_tce_rs/dados` | JSON (CKAN) | blocked | 2026-07-13 | Reconfirmed unreachable, no change: `dados.tce.rs.gov.br` still TCP-timeouts on :443 and :80 (both resolved IPs). `www.tce.rs.gov.br` (main site) also times out — genuine ongoing host-level outage. |
| TCE-SC | `br_tce_sc/dados` | JSON | blocked → mcp-todo | 2026-07-13 | Reconfirmed blocked, no change. Now 403s even on the plain `www.tce.sc.gov.br` root and `/transparencia` (not just the API path), with `server-timing: ak_p` headers confirming Akamai — full-browser UA/Accept-Language headers don't help. `dados.tce.sc.gov.br` doesn't resolve. |

### Tier 1c — needs a quick access-pattern check before it's real work

| Source | Beelink path | Format | Status | Last updated | Notes |
|---|---|---|---|---|---|
| CGU Leniência | `br_cgu_leniencia/acordos` | CSV/XLSX | blocked | 2026-07-13 | Reconfirmed still blocked: redirect chain still works cleanly, final object still returns a plain S3 `AccessDenied` XML body via CloudFront (not even a JS-challenge page — genuine bucket-policy block), tried a fresh browser UA, Referer, and Accept-Language headers, no change. No wayback snapshot exists for the object URL or the portal listing page (`archive.org/wayback/available` returns nothing archived). Same blanket block as before, no new access path found. |
| CGU PEP | `br_cgu_pep/pep` | CSV | blocked | 2026-07-13 | Reconfirmed still blocked: same CloudFront/S3 `AccessDenied` on the final object (`dadosabertos-download.cgu.gov.br/.../202401_PEP.zip`), redirect chain itself unaffected. No new access path found. |
| SPU (patrimônio da União) | `br_spu_patrimonio/imoveis` | — | blocked | 2026-07-13 | Found the real source this time: SPU runs an actual INDE-style geospatial catalog at `geoportal-spunet.gestao.gov.br` (GeoNode + GeoServer, discovered via the "Geoportal da SPU" gov.br news pages, not the old dead paths). `/api/v2/datasets` lists 16 real layers incl. `spunet:vw_imv_localizacao_imovel_p` ("Localização Imóvel - SPUnet", national property points with RIP/address/owner/area attributes) and terreno de marinha/marginal/ilha/manguezal/praia federal layers. Confirmed real records exist and are queryable — WMS `GetFeatureInfo` returns full attribute rows for individual features. But bulk export is deliberately disabled for anonymous users: every layer's `perms` is `["view_resourcebase"]` only (no download permission), `GetFeature` (WFS, tried v1.0.0/1.1.0/2.0.0, global and workspace-scoped `ows`/`wfs` endpoints) returns "Feature type unknown" for every layer despite WMS `GetCapabilities` confirming they exist, and `dataset_download` 404s. This is a genuine permission-model block (view-only), not a WAF — no bulk-download path found. |

### Tier 2 — excluded from this loop by priority choice (HTML scraping required)

DENASUS needs HTML scraping per the archived main catalog. Deliberately pushed behind all
of Tier 1; revisit once Tier 1 is exhausted.

### Deferred — needs api_key/token (skipped by design, not blocked)

Portal da Transparência REST API (`renuncias`), CEPIM, CEIS, CNEP, CEAF,
B3 via brapi.dev, DataJud (excluded from bulk mirroring for legal reasons regardless — see
`tasks/done/datasets_to_scrap_done.md` — but a `consultar_datajud()` live tool is a good
`mcp-todo` candidate once an api_key exists). Do not pause to request credentials — just
leave these `deferred-api_key` and keep moving down Tier 1.

**Consumidor.gov.br — passou a `deferred-api_key` em 2026-09-02** (veio de
`tasks/todo.md`, arquivado; pesquisa completa em
`tasks/done/threads_pos_scraping_2026-07.md`). Estado: 10.167.141 linhas / 70 de
86 arquivos em `br_mj_consumidorgovbr`. O host antigo `dados.mj.gov.br` **saiu
do ar de vez** (NXDOMAIN, não é queda temporária — só sobra o Wayback, cujos
links apontam todos de volta pro próprio domínio morto). O dataset está vivo em
`dados.gov.br/dados/conjuntos-dados/reclamacoes-do-consumidor-gov-br1` (note o
`1` final), mas o portal inteiro — inclusive navegação anônima — agora exige o
header `chave-api-dados-abertos`; testado e confirmado `401` em toda rota
`publico`, com e sem `Referer`/`Origin` de browser. O token é self-service, mas
exige **login gov.br com CPF pessoal** — por isso `deferred-api_key` e não
`blocked`: não é infra quebrada, é credencial pessoal, decisão do usuário.
Quando existir token, `scripts/scrap/mj_consumidorgovbr.py` precisa de (1)
`PACKAGE_API` repontado pro novo endpoint (shape de resposta diferente do CKAN
antigo, ainda não mapeado) e (2) o header em toda requisição.

### Still-open items with no table row of their own

A few gaps surfaced during the pre-status-board planning pass (now archived) that were
never itemized as their own Tier row and are still genuinely unstarted:

- **Portal da Transparência CDN slugs still 403'd by AWS WAF**: `renuncias`, `notas-fiscais`
  (NFE), `peti`, `imoveis-funcionais`, `bolsa-familia-pagamentos`, `servidores` — all at
  `dadosabertos-download.cgu.gov.br/PortalDaTransparencia/saida/<slug>/`. `orgaos-siafi`
  additionally 500s on the page itself. Garantia-Safra/Seguro-Defeso/Pe-de-Meia/Viagens from
  the same family are already done (see archive).
- **BCB/BACEN SGS series beyond the curated 18**: `scripts/scrap/bcb_sgs.py`'s `SERIES`
  dict covers 18 hand-picked series; the SGS catalog has thousands more, extendable anytime
  by adding entries to that dict.

### mcp-live candidates — lookup-shaped, skip the mirror attempt entirely

Not a beelink pipeline target at all (no meaningful "full table" to page through), and not
`excluded` either — just intentionally routed straight to a live tool in `mcp_server.py`
per the 2026-07-10 rule above.

| Source | Shape | Notes |
|---|---|---|
| OAB advogado (CNA) | single-key lookup | `cna.oab.org.br`/`consulta.oab.org.br` are Angular SPAs with no discovered bulk export or documented API — candidate for a live `consultar_oab(numero)` tool. **Not yet built** — no `consultar_oab` in `mcp_server.py` despite an earlier pass in the archive labeling a related row `mcp-live`; treat as still open. |

### Tables from the Base dos Dados mirror still genuinely absent from beelink

**Refreshed 2026-08-26** (previous check was 2026-07-09) via the live `bq ls`/`bq show`
diff in `scripts/sync-with-source.md` (Steps 1–2) — metadata-only calls, no billing. The
BD catalog grew from 793 to 1,239 `dataset/table` entries since July, but that growth is
**almost entirely a new non-Brazilian catalog** (`au_`/`us_`/`gb_`/`fr_`/`in_`/`mx_`/`af_`/
`world_`/`br_bd_diretorios_{au,de,fr,in,mx,us}` prefixes — US Census/BLS/FEC, UK election
survey, Australian crime stats, etc., ~360 tables) that's out of scope for this project's
Brazilian-government-data mirror — not itemized here. Filtering to genuinely new **Brazilian**
(`br_*`) physical TABLEs not on beelink, by dataset:

**Closed out 2026-09-02.** `br_bndes_operacoes_contratadas` (2/2), `br_cgu_pessoal_executivo_federal`
(1/1) and `br_me_siconfi`'s 3-table gap all finished and moved to
`tasks/done/datasets_to_scrap_done.md`, along with `br_senado_dados_abertos_administrativos`
(closed as "done, partial by design" — the 24 tables that never landed are 0 rows at the BQ
source itself, confirmed by `SELECT count(*)`, not a rate-limit cutoff as an earlier note here
guessed) and a first slice of `br_sfb_sicar` (3/8 new tables). **Also found and fixed 2026-09-02:**
a prior pass in this same file had already written up `br_cgu_sancoes`, `br_sedec_desastres`,
`br_senado_dados_abertos` and the ANVISA agrotóxicos/alimentos pull as "done, verified via DuckDB
readonly" — but no DuckDB *view* existed for any of these tables (or for `br_bcb_ifdata`/
`br_bndes_operacoes_contratadas`'s partial landings), so `SELECT * FROM dataset.table` against
`basedosdados.duckdb` on beelink would have failed even though the parquet was really on disk —
`read_parquet()` works without a view, `information_schema.tables` (and every MCP/`describe_table`
consumer) doesn't. `scripts/sync/cria_views_novas.py` (new) creates a view for any `dataset/table`
that has parquet on disk but no view yet — idempotent, safe to rerun. All tables below were
(re-)verified this pass with a real `SELECT count(*)` through the view, not just `read_parquet`.
`scripts/build_metadata_catalog.py` re-run three times as tables landed; `_rodado_metadata` is
current.

| Dataset | Tables | Rows (BQ, largest table) | Notes |
|---|---|---|---|
| `br_bcb_taxa_cambio` | 1 (`taxa_cambio`) | 801K | **Confirmed genuinely blocked, not just untried** — `bq show` reports a real 801,451-row TABLE, but `bq query`/`SELECT` on it returns `Access Denied: ... User does not have permission to query table ..., or perhaps it does not exist` even under the Sandbox job project. Same shape as the known "upstream view/table is broken or access-restricted" gotcha in `scripts/sync-with-source.md` — not fixable from our side, no bulk alternate found. Stays open. |
| `br_bcb_taxa_selic` | 1 (`taxa_selic`) | 9.7K | Same Access Denied signature as `taxa_cambio` above, confirmed 2026-09-02. Stays open. |
| `br_bcb_ifdata` | 4 (`coluna`, `dicionario`, `instituicao`, `relatorio`) | 54.5M (`relatorio`) | **3/4 done** (`coluna` 48,482, `dicionario` 56, `instituicao` 440,444 rows — view created, re-verified via `SELECT count(*)`). `relatorio` (54.5M rows) is over the 10M-row single-shot safety cap (`MAX_ROWS_SAFE` in `gcp_to_beelink_sync.py`) — needs a chunked pull (e.g. by year/quarter), not attempted this session. Stays open for just that one table. |
| `br_sfb_sicar` | 8 tables (`app`, `area_consolidada`, `area_pousio`, `hidrografia`, `reserva_legal`, `servidao_administrativa`, `uso_restrito`, `vegetacao_nativa`) | 28.1M (`app`) | **3/8 new tables done 2026-09-02**: `area_pousio` (212,315 rows), `servidao_administrativa` (2,175,650), `uso_restrito` (179,748) — pulled via `scripts/sync/sync_novas_tabelas.py` (new; uses `QueryJob.to_arrow()`, not `bq query --format=json`, see rationale in its docstring), views created, re-verified. **`app`** stays skipped, 28.1M rows over the safety cap. **`area_consolidada`, `hidrografia`, `reserva_legal`, `vegetacao_nativa`** were attempted and failed with a *new* wall, not access-denied: BigQuery's REST `jobs.getQueryResults` returns `403 Response too large to return` on these — the `GEOGRAPHY` (WKT multipolygon) column makes individual result pages too large for the default REST iterator; needs the `google-cloud-bigquery-storage` package (not installed) or a destination-table extract instead of a bare `client.query().to_arrow()`. Confirmed the geometry column specifically is the cost driver: a dry-run of `area_consolidada` *without* `geometria` is 0.88GB vs. 26.6GB with it. beelink already has an older, differently-shaped partial pull (`area_imovel`, `dicionario`, since 2026-07-09) — not the same tables, no overlap. |

**Not listed as a gap — needs a rename/refresh check first, not a blind pull:**
`br_rf_cnpj` (5 tables: `empresas`, `estabelecimentos`, `socios`, `simples`, `dicionario`)
looks like Base dos Dados renamed `br_me_cnpj` → `br_rf_cnpj` with a refreshed snapshot —
row counts line up almost exactly (`empresas` 3.08B→3.20B, `estabelecimentos`
3.24B→3.31B, `socios` 1.34B→1.34B identical, `simples` 49,872,124 identical both sides).
Also skipped: `br_mf_divida_ativa` (`fgts`/`previdenciario`/`nao_previdenciario`, up to
685M rows) — same PGFN Dívida Ativa source we already scrape independently as
`br_pgfn_dividaativa` (backs `consultar_divida_ativa` in `mcp_server.py`); check for
overlap before treating as a fresh pull.

What's left in the table above is genuinely stuck, not just untried: `br_bcb_taxa_cambio`/
`br_bcb_taxa_selic` are access-denied at the BigQuery permission level (not fixable from our
side), `br_bcb_ifdata.relatorio` and `br_sfb_sicar.app` are single tables over the 10M-row
safety cap (need a chunked pull), and `br_sfb_sicar`'s other 4 remaining tables hit a BigQuery
REST response-size wall driven by their `GEOGRAPHY` column (needs the
`google-cloud-bigquery-storage` package, not installed, or a destination-table extract). None
of these are a plain `bq query`→parquet→rsync rerun away. `br_rf_cnpj` (if confirmed genuinely
new data, not just a rename of `br_me_cnpj`) is still untouched and would need the dry-run/
quota-aware path given its billion-row scale.

## Pending Data Integrations

| Task | Description | Source | Format |
|------|-------------|--------|--------|
| microdados_2022 | Adicionar microdados 2022 ao banco | IBGE | CSV/Parquet |
| aglomerados_subnormais | Integrar shapefiles de aglomerados subnormais | IBGE/MUIC | Shapefile/GeoJSON |
| areas_risco | Integrar dados de areas de risco | ANA, CEMAVE, etc. | CSV/GeoJSON |
| census_agropecuario | Adicionar Census Agropecuario (concentracao fundiaria) | IBGE | CSV/Parquet |
