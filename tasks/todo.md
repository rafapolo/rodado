# TODO

Open threads left after the 2026-07-14 scraping finalization pass. Both are
blocked on external state, not on anything actionable locally right now.

The third item that used to live here — `_run_sql_ssh` leaving orphaned DuckDB
processes on beelink when a query hangs — is **fixed** (2026-08-25):
`mcp_server.py`'s `_run_sql_ssh` now runs the remote command under
`timeout -k 5 115 ...` instead of bare `~/bin/duckdb`, so the *remote* process
kills itself before the local 120s `subprocess.run` timeout ever fires —
tested live against a deliberately compute-bound query (killed cleanly at
exactly 3s under a shortened test timeout, exit 124, confirmed no orphaned
`duckdb` process left on beelink afterward via `ps aux`).

## Atlas da Violência (IPEA) — full pull ✅ RESOLVED (2026-08-27)

- **Previous state**: `br_ipea_atlasviolencia` shipped with only 10 series / 182
  national annual value rows on beelink — worse than the 11/5,591 this file
  used to claim. Cause found in the catalog's own `provenance_notes` (not
  something this pass caused): a 2026-08-23 parallel run's partial 182-row
  output overwrote the earlier good 5,591-row one *before* the regression
  guard existed. The guard is in place now, but the good data was already
  gone by the time it was added.
- **2026-08-25: `scripts/scrap/ipea_atlasviolencia.py` reworked to checkpoint
  incrementally** — each series' values are written to
  `/tmp/ipea_atlasviolencia_<mac>/checkpoint.json` as soon as they're fetched
  (not batched at the end), and a series already checkpointed is skipped on
  the next invocation.
- **2026-08-27: closed out in 2 chained runs** (local checkpoint had reset —
  no `/tmp/ipea_atlasviolencia_<mac>` dir existed on this machine — so both
  runs started from the full 152-series catalog, not a resumed one; the
  regression guard meant this was safe regardless):
  - Run 1 (`IPEA_DEADLINE_SECONDS=700`): 151/152 series covered, 1 series
    (id 158) failed with the known intermittent `curl rc=28`. Pushed 2,831
    annual value rows.
  - Run 2 (same command, resumed from checkpoint): picked up the 1 pending
    series, reached **152/152 series covered**. Pushed 2,854 annual value
    rows, 1979–2024.
  - Verified on beelink: `br_ipea_atlasviolencia.series` = 152 rows (1 per
    series, metadata only — matches "series covered" exactly);
    `br_ipea_atlasviolencia.valores_nacional` = 2,854 rows across 136
    distinct `serie_id`. The gap (152 metadata rows vs. 136 series with
    actual value rows) is real, not a bug: 16 series returned an empty
    `serie-chart` array from `dados-api` (checkpointed successfully as
    `[]`, so they count as "covered") — those series apparently don't
    publish a national annual time series via that endpoint. Not
    investigated further; out of scope for this pass.
- Sub-national (estado/município) breakdown is intentionally out of scope — see script docstring, `regiao_id`→name mapping was never confirmed.

## Consumidor.gov.br backfill — where the source lives now (research only, 2026-08-27)

- **Current state, unchanged**: 10,167,141 rows / 70 of 86 files pushed to `br_mj_consumidorgovbr` on beelink. **No scrape was run this pass** — this was research only, per instructions.
- **`dados.mj.gov.br` reconfirmed gone**: still `NXDOMAIN` locally (`dig`/`getent`, both empty) — not a temporary outage, the subdomain is retired. A Wayback Machine snapshot exists (`web.archive.org/web/20260308031133/https://dados.mj.gov.br/dataset/reclamacoes-do-consumidor-gov-br`, 200, from 2026-03-08) and lists the historical per-year/semester CSV download links (e.g. `.../resource/d3a05111-.../download/dadosgovbr---2014.csv`) — but every one of those links points back at `dados.mj.gov.br` itself, i.e. there is no separate storage/CDN subdomain to fall back to; the files are only reachable, if at all, through Wayback's own cached copies, not live.
- **`dados.gov.br` (the unified replacement portal) reconfirmed `401` — and it's a real, portal-wide API-key gate, not a fluke**:
  - Old CKAN-style API: `GET https://dados.gov.br/api/3/action/package_show?id=reclamacoes-do-consumidor-gov-br1` → `401`, header `www-authenticate: Bearer`.
  - New portal's own API (`GET https://dados.gov.br/v3/api-docs`, the live OpenAPI spec) shows the security scheme is `apiKey` in header `chave-api-dados-abertos` — and testing its endpoints directly (`GET /dados/api/publico/conjuntos-dados/{id}`, `GET /dados/api/publico/conjuntos-dados`, etc. — note "publico" in the path name) still returns `401` without that header. Tried with browser-mimicking `Referer`/`Origin`/`User-Agent` headers too — still `401`. This is a genuine backend gate, not a CSRF/session check curl happens to fail.
  - **Dataset located**: the "Dados Consumidor.gov.br" dataset exists on the new portal under slug **`reclamacoes-do-consumidor-gov-br1`** (note the trailing `1` — different from the old `dados.mj.gov.br` slug), org id in the old CKAN system was `0182f1bf-e73d-42b1-ae8c-fa94d9ce9451`. The dataset's human-facing page (`https://dados.gov.br/dados/conjuntos-dados/reclamacoes-do-consumidor-gov-br1`) loads (`200`) as a Vue SPA shell, but every actual data call it would make hits the same `401` gate — so this isn't just an API-only restriction, the whole portal (including anonymous browsing) now requires the key.
  - **How the key is obtained** (per the OpenAPI spec's own `securitySchemes` description, corroborated by the third-party `dados-gov-sdk` PyPI package's setup docs): log into `https://dados.gov.br/` with a gov.br account (CPF-based SSO login), then generate an access token from "Minha Conta" (for the "Consumidor" or "Gestor de Políticas de Dados Abertos" profile) — a separate "Tokens de organização" flow exists only for organization-admin accounts. This reads as **self-service** (no visible approval/review step beyond having a gov.br account and generating the token yourself) but **does require creating/using a real gov.br login**, which this pass did not do per instructions ("não crie conta").
- **Bottom line**: the dataset is not lost — it has a confirmed home at `dados.gov.br/dados/conjuntos-dados/reclamacoes-do-consumidor-gov-br1` — but resuming the scrape now requires a human to log into `dados.gov.br` with a gov.br account and mint a `chave-api-dados-abertos` token first; there is no token-free path found. Once a key exists, `scripts/scrap/mj_consumidorgovbr.py` would need: (1) `PACKAGE_API` repointed at `https://dados.gov.br/dados/api/publico/conjuntos-dados/reclamacoes-do-consumidor-gov-br1` (new response shape, not the old CKAN `package_show` JSON — schema not yet mapped), and (2) every request sending the `chave-api-dados-abertos` header. Not touched this pass.

## Otherwise

Everything else in `tasks/datasets_to_scrap.md` is resolved: all `pending-verify` rows cleared, all 5 blocked-recheck batches done, `deferred-api_key` rows correctly skipped by design, IBAMA embargos reconfirmed infra-blocked (unrelated SSL proxy issue, not fixable from here).
