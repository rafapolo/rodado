# Syncing beelink with the upstream BigQuery source

`beelink:~/rodado` is a **separate, local-parquet mirror** of the upstream BigQuery source,
independent from the S3-view-based `data/basedosdados.duckdb` this repo's live service
queries (see project CLAUDE.md — the live service never touches BigQuery, only Hetzner S3).

This doc is for **maintaining beelink's mirror only**. It intentionally goes straight
`BigQuery → beelink`, skipping Hetzner S3 entirely — beelink exists precisely so we don't
have to route through S3 for this.

⚠️ This uses `bq`/BigQuery, which the top-level CLAUDE.md forbids for querying the live
service. That rule is about how `ask`/`auth.py`/DuckDB serve production queries — it does
not cover this one-off mirror-maintenance workflow. Treat BigQuery usage here as scoped
strictly to this doc, never as precedent for touching BigQuery anywhere else in the repo.

## Current state (as of 2026-07-09, end of session)

- **Missing tables: effectively done.** 693/793 live source tables now on beelink (up from
  558 at session start). All 103 still absent are **confirmed broken/inaccessible on the
  source itself** (broken views, access-denied) — verified zero genuinely-untried tables
  remain. The full list of confirmed-broken `dataset/table` names lives in the union of
  `⊘ ...: fetch failed` / `no schema` lines across `/tmp/full_sync_run*.log` from this
  session — regenerate via Step 2 + a fresh `bq show` pass if picking this back up much
  later, don't assume it's still accurate indefinitely (a source table could theoretically
  be fixed upstream).
- **Row drift: barely started, by design.** Of ~5.04B rows of identified drift across 115
  tables, one pass closed **~4.79M rows** across 12 tables. 40 tables have no
  partition/cluster column (no cheap path, ever, without a different strategy). The biggest
  offenders (`br_ans_beneficiario` ~940M rows behind, `br_me_cnpj.estabelecimentos`/
  `empresas`, `br_rf_cno.*`) are still close to where they started — closing those fully
  will take many more monthly runs at the current 5M-row/3GB-per-table batch cap. This is
  the intended tradeoff of staying inside the free quota, not a bug.
- **To resume:** regenerate the missing-table list fresh (Step 2) and re-run Step 4, then
  Step 5 with the same `/tmp/drifted_tables.txt` (or regenerate that too via Step 3 if it's
  been a while — the delta amounts will have changed).
- **Known bug, not yet fixed:** in `sync_drifted_incremental.py`, when the real query
  (`fetch_and_append`) times out (300s), the table's final result is recorded as
  `no_new_rows` instead of `error`/`timeout` — `sync_one()` doesn't distinguish "genuinely
  caught up" from "query took too long." This happened 3 times in the 2026-07-09 run
  (`br_rf_cafir.imoveis_rurais`, `br_me_cnpj.socios`, `br_me_cnpj.estabelecimentos`) and
  means those tables will look "closed" in `drift_results.tsv` even though they weren't
  attempted successfully — don't trust that file at face value for those three without
  re-checking. Fix: have `fetch_and_append` return a distinct sentinel (not `0`) on timeout,
  and have `sync_one` propagate that instead of falling through to `no_new_rows`.
- **Fixed this session:** `get_table_meta()` in `sync_drifted_incremental.py` originally had
  no retry and no JSON-decode guard, so a transient `bq show` failure (all 115/115 tables
  failed once mid-session, almost certainly OAuth token refresh contention from running
  several concurrent manual `bq show` sweeps at the same time as the background job) got
  permanently misrecorded as `no_schema` for every table in that run. Now retries once after
  a 2s backoff and logs the real stderr on failure. **Lesson: don't run manual ad-hoc `bq`
  commands in parallel with an active background sync job** — it can starve/collide with the
  job's own calls.
- **Deprioritization note:** `br_me_cnpj/empresas` and `br_bd_diretorios_brasil/empresa` were
  explicitly pushed to the end of `/tmp/drifted_tables.txt` per a mid-session request to sync
  other tables first. If regenerating that file from scratch, redo this reordering if the
  same preference still holds — it's not persisted anywhere except that file's line order.
- **Script chaining gotcha:** if running Step 4 and Step 5 back-to-back via
  `cmd1 && cmd2`, killing the Step 4 process directly (not the parent `bash -c`) still lets
  bash proceed to Step 5 if the two were joined with plain newlines instead of `&&` — always
  use `&&` (not sequential lines) when chaining, and kill the top-level wrapper process, not
  just the inner `python3` child, when pausing.

## Why not `bq extract` / Hetzner S3

- `bq extract` requires a billing-enabled GCP project. Neither available project
  (`raspa-491716`, `project-40912138-177d-4e28-8d2`) has billing enabled, and both linked
  billing accounts are closed.
- `bq query` (interactive/on-demand SELECT) runs for free in **BigQuery Sandbox mode** —
  up to ~1TB scanned/month, no billing account needed at all. This is the only viable path
  without opening billing.
- Since we're going straight to beelink, there's no GCS staging bucket and no Hetzner
  egress cost either — just the query job itself (free under Sandbox) plus a plain
  `bq query --format=json` → Parquet → `rsync` to beelink.

## Prerequisites

```bash
which bq gcloud                      # from google-cloud-sdk
gcloud auth list                     # must show an ACTIVE account
gcloud projects list                 # confirms raspa-491716 is available as JOB_PROJECT
ssh beelink "echo ok"                # passwordless SSH must work
ssh beelink "~/bin/duckdb --version" # duckdb CLI on beelink (see setup below if missing)
```

If `~/bin/duckdb` isn't on beelink yet:
```bash
ssh beelink "curl -sL https://github.com/duckdb/duckdb/releases/latest/download/duckdb_cli-linux-amd64.zip -o /tmp/d.zip && cd /tmp && unzip -o d.zip && mkdir -p ~/bin && mv duckdb ~/bin/duckdb"
```

## The two-project trick (no billing account needed)

`basedosdados` (the public data project) does **not** grant `bigquery.jobs.create` to
external accounts — you cannot run a query job "in" that project. Instead:

- **`BQ_PROJECT = "basedosdados"`** — used only for metadata reads (`bq ls`, `bq show`).
  These aren't jobs, don't need billing, and work directly against the public project.
- **`JOB_PROJECT = "raspa-491716"`** — used to *run* the actual query job (Sandbox free
  tier). The table reference in the query is fully qualified
  (`` `basedosdados.<dataset>.<table>` ``) so the job reads the public data while executing
  under `raspa-491716`'s (billing-free) quota.

```bash
# Fails — basedosdados won't let us create a job there:
bq query --project_id=basedosdados --use_legacy_sql=false 'SELECT 1'

# Works — job runs under raspa-491716, reads from the public project:
bq query --project_id=raspa-491716 --use_legacy_sql=false \
  'SELECT * FROM `basedosdados.br_bd_diretorios_brasil.municipio` LIMIT 3'
```

## Step 1 — Get the live table list (don't trust `context/basedosdados-schema.json`)

That catalog file is stale — it has table names (e.g. `br_bcb_sicor.microdados_liberacao`)
that don't exist on the live source anymore (the real names are `liberacao`, `operacao`,
etc., no `microdados_` prefix). Always re-derive the list live:

```bash
bq ls --project_id=basedosdados --max_results=10000 --format=json \
  | python3 -c "import json,sys; [print(d['datasetReference']['datasetId']) for d in json.load(sys.stdin)]" \
  > /tmp/live_datasets.txt

# per-dataset table listing, parallelized
mkdir -p /tmp/bq_tables_dir
cat /tmp/live_datasets.txt | parallel --jobs 16 scripts/sync/list_dataset_tables.sh {}
cat /tmp/bq_tables_dir/*.txt | sort > /tmp/live_bq_tables.txt   # dataset/table<TAB>TYPE
```

## Step 2 — Diff against beelink to find genuinely missing tables

```bash
ssh beelink "find ~/rodado -mindepth 2 -maxdepth 2 -type d -printf '%P\n'" \
  | sort > /tmp/beelink_tables.txt
awk -F'\t' '{print $1}' /tmp/live_bq_tables.txt | sort > /tmp/live_bq_names.txt

comm -23 /tmp/live_bq_names.txt /tmp/beelink_tables.txt > /tmp/live_missing.txt   # whole tables to fetch
comm -12 /tmp/live_bq_names.txt /tmp/beelink_tables.txt > /tmp/overlap_tables.txt # existing — check for row drift
```

As of 2026-07-09: 793 live dataset/table pairs, 238 missing entirely, 555 overlapping
(candidates for row-drift check below). These numbers drift over time — always regenerate.

## Step 3 — Check row drift on existing tables (cheap, no query jobs)

Local row counts come from Parquet **footer metadata only** (no full scan) via DuckDB on
beelink itself:

```bash
ssh beelink "~/bin/duckdb -json -c \"SELECT sum(num_rows) as r FROM parquet_file_metadata('<dataset>/<table>/*.parquet');\""
```

BigQuery row counts come from `bq show` (metadata call, free, no job):

```bash
bq show --project_id=basedosdados --format=json <dataset>.<table> \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('numRows','0'), d.get('type'))"
```

Compare the two — where BigQuery's `numRows` > beelink's local count, the table is
**drifted** (beelink is behind). Note `numRows` is unreliable/`0` for `VIEW`-type tables;
those need the dry-run check in Step 4 instead of a row-count comparison.

Batch scripts for both sides:
- `scripts/sync/beelink_row_counts.sh` — copy to beelink and run there (`scp` + `ssh beelink
  bash ~/row_counts.sh`), loops over all `dataset/table` dirs, writes a
  `dataset/table<TAB>rows` TSV.
- `scripts/sync/get_table_rows.sh` — same for BigQuery via `bq show`, run locally:
  `cat /tmp/overlap_tables.txt | parallel --jobs 16 scripts/sync/get_table_rows.sh {} > /tmp/bq_row_counts.tsv`

## Quota tracking (`scripts/sync/bq_quota.py`)

Both Step 4 and Step 5 scripts share `scripts/sync/bq_quota.py`, a small on-disk tracker
(`~/.bq_sandbox_quota.json`) that:

- Records cumulative `bytes_processed` (from each query's dry-run estimate) against a
  **900GB** budget per calendar month — deliberately under the real ~1TB Sandbox cap to
  leave headroom for dry-run estimate error.
- Resets automatically the moment the wall-clock month changes — no manual reset needed.
- `reserve(bytes_needed)` returns `False` instead of running the query once the budget for
  the month is used up. Both sync scripts treat that as "stop the whole run, not just this
  table" and cleanly defer whatever's left to the next run/month.

```bash
python3 scripts/sync/bq_quota.py   # print current month's usage
```

This is what makes it safe to just re-run the same command repeatedly (e.g. via cron or
`/loop`) — each run picks up wherever the last one stopped, throttled to the free tier, no
manual bookkeeping.

## Step 4 — Fetch missing tables safely

Use `scripts/sync/gcp_to_beelink_sync.py <missing_list_file>`. It:

1. Looks up schema + `numRows` via `bq show` (metadata, free) — skips if `numRows` alone
   looks too large (`MAX_ROWS_SAFE`, currently 5M rows).
2. Runs `bq query --dry_run` first (also free, no job billed) to get a real byte-scan
   estimate, and skips anything over `MAX_DRY_RUN_BYTES` (3GB) per table.
3. **Also skips externally-backed tables** (Sheets/GCS-backed BigQuery tables report
   `tableType: EXTERNAL` in the dry-run's `referencedTables`, and their scan estimate is a
   meaningless `LOWER_BOUND` — often `0` even when the real query is slow/unbounded). These
   need manual handling, not automated sync.
4. Reserves the dry-run byte estimate against the shared monthly quota (see above) — if
   that fails, stops the whole run and logs every remaining table as `deferred_quota` for
   next time, rather than grinding through pointless dry-runs for the rest of the list.
5. Runs the real `bq query --format=json` with a hard 180s subprocess timeout (guards
   against anything the dry-run underestimated) under `JOB_PROJECT`, fully-qualified table
   ref against `BQ_PROJECT`.
6. Converts BigQuery JSON string values to real Arrow types per column (`bq show`
   schema → `_bq_tipos.para_arrow`), writes Parquet, and `rsync`s to
   `beelink:~/rodado/<dataset>/<table>/<NN>.parquet` — the destination name is
   resolved by `_bq_tipos.nome_destino` *before* the transfer, never left to rsync's
   basename preservation.
7. Writes progress to `~/.gcp_sync_progress` and a `skipped.txt` log of anything it
   couldn't pull (with a reason) for manual follow-up.

```bash
python3 scripts/sync/gcp_to_beelink_sync.py /tmp/live_missing.txt
```

Run it in the background and tail `~/.gcp_sync_progress` — some tables take a while even
within the safety limits, and a handful of the 238 "missing" ones are broken/inaccessible
views on the source side that will always skip (that's expected, not a bug). Since the
missing-table list is re-derived live from beelink's actual disk state (Step 2), simply
regenerating it before each re-run naturally excludes whatever already landed — no separate
resume bookkeeping needed here either.

## Step 5 — Incremental fetch for drifted (not missing) tables

Use `scripts/sync/sync_drifted_incremental.py <drifted_list_file>`. Per table it:

1. Reads `bq show` for `timePartitioning.field` → `rangePartitioning.field` → first
   `clustering` field, in that priority order, as the incrementing column. **No usable
   column → skipped and logged as `no_partition_column`, never a full re-pull.** This is a
   hard limit of the approach, not a bug: some tables (e.g. small IBGE index tables like
   `br_ibge_ipca.mes_brasil`) have no partition/cluster metadata at all and need a one-off
   manual decision.
2. Gets beelink's **current** local max on that column by querying the actual Parquet files
   live via `ssh beelink "~/bin/duckdb ... read_parquet(...)"` — never a cached/stored
   value. This is what makes reruns automatically incremental: whatever landed on disk last
   time raises the max, so the next run's `WHERE col > max` naturally starts past it.
3. Dry-runs `SELECT * WHERE <col> > <local_max> LIMIT 5,000,000`, applies the same
   external-table skip and quota-reservation gate as Step 4.
4. On success, writes the new rows as a **new part file** (`incr_<timestamp>.parquet`) into
   the existing table directory rather than overwriting anything — DuckDB reads `*.parquet`
   globs, so multiple part files coexist fine.
5. On quota exhaustion, stops the run and logs the remaining tables as `deferred_quota`,
   same as Step 4.

```bash
python3 scripts/sync/sync_drifted_incremental.py /tmp/drifted_tables.txt
```

The 5M-row batch cap means the handful of billion-row-delta tables (`br_ans_beneficiario`,
`br_me_cnpj`, `br_rf_cno`, `br_ms_sia`/`sih`, `br_me_rais`...) will *not* close in one run —
each pass chips away 5M rows (or less, if that batch alone exceeds the 3GB dry-run cap), and
catching fully up takes many months of the shared 900GB budget by design. That's the
intended "slowly, within quota" behavior, not a bug to fix by raising the batch size.

Re-run Step 3's row-count comparison periodically to see how much drift has actually closed.

## Known gotchas (hit these already, don't rediscover them)

- Some tables are BigQuery **VIEWs**, not TABLEs — `bq extract` can't touch them at all,
  and several of the upstream project's own views are themselves broken (access denied when
  queried, e.g. `br_anatel_banda_larga_fixa.{backhaul,pble}`). Skip and move on.
- `numRows` from `bq show` is `0`/meaningless for VIEWs — never gate solely on it, always
  dry-run before a real query.
- `context/basedosdados-schema.json` in this repo is a point-in-time snapshot and already
  has table names that don't exist on the source anymore — never use it as the sync target
  list, only `bq ls` live.
- One table (`br_ms_sia.producao_ambulatorial`, ~2.15TB as of 2026-07-05) is bigger than
  the entire Sandbox monthly free quota by itself — this and anything similar should stay
  permanently excluded from automated sync, not retried.
- Four superseded sync scripts were removed on 2026-08-23 (`fast_gcp_sync.py`,
  `quick_sync_bq.py`, `sync_bq_to_beelink.py`, `sync_via_bq_query.py`) — recuperáveis no
  histórico do git, em `8ce9aa8`. Estavam sem o `JOB_PROJECT`, sem o dry-run, sem o teto
  de scan do `bq_quota` e sem tipo no Parquet. O que sobra em `scripts/sync/`:
  `gcp_to_beelink_sync.py` (tabelas faltando) e `sync_drifted_incremental.py` (drift de
  linha) são os pontos de entrada testados; `ressincroniza_bq.py` é o caminho preferido
  para código novo, porque usa `QueryJob.to_arrow()` e o JSON não entra no caminho.
  `sync_bq_to_local.py` segue no repositório.
- `sync_stale_tables_incremental.py` removido em 2026-08-23, junto com os quatro acima: era
  stub inteiro. `get_stale_tables()` devolvia as 20 primeiras tabelas do BigQuery em
  ordem alfabética sem comparar contagem nenhuma (o docstring dizia "identify 147
  tables where beelink has < BigQuery rows"), e `get_max_id_on_beelink()` devolvia
  `(None, None)` sempre, o que colapsava o WHERE para `1=1` — cada execução anexaria
  as PRIMEIRAS linhas de cada tabela de novo, como shard duplicado. A única parte
  real era o caminho de escrita, que duplica `sync_drifted_incremental.py`. Para
  detectar tabela atrasada, compare `_rodado_metadata.rows` com o `numRows` do
  `bq show` e passe a lista para `sync_drifted_incremental.py`, que já aceita uma.
- Running Step 4 and Step 5 **concurrently** races on `~/.bq_sandbox_quota.json` (unlocked
  read-modify-write) and can silently over-spend the monthly budget. Run them sequentially
  (Step 4 to completion, then Step 5), not in parallel.
