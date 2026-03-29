#!/usr/bin/env bash
# =============================================================================
# export_basedosdados.sh
# Exports all basedosdados BigQuery tables → GCS (Parquet+zstd) → Hetzner Object Storage
#
# Prerequisites (run once before this script):
#   gcloud auth login
#   gcloud auth application-default login
#   gcloud config set project YOUR_PROJECT_ID
#   cp .env.example .env  # then fill in your values
#
# Usage:
#   chmod +x export_basedosdados.sh
#   ./export_basedosdados.sh              # full run (locally)
#   ./export_basedosdados.sh --dry-run    # list tables + estimated sizes, no export
#   ./export_basedosdados.sh --gcloud-run # create GCP VM → run there → delete VM
# =============================================================================

set -euo pipefail

# Add util-linux to PATH on macOS (provides flock)
[[ -d "/opt/homebrew/opt/util-linux/bin" ]] && export PATH="/opt/homebrew/opt/util-linux/bin:$PATH"

# Load .env if present
if [[ -f "$(dirname "$0")/.env" ]]; then
  set -a
  # shellcheck source=.env
  source "$(dirname "$0")/.env"
  set +a
fi

DRY_RUN=false
GCLOUD_RUN=false
SYNC_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=true
elif [[ "${1:-}" == "--gcloud-run" ]]; then
  GCLOUD_RUN=true
elif [[ "${1:-}" == "--sync" ]]; then
  SYNC_RUN=true
fi

# -----------------------------------------------------------------------------
# LOGGING
# -----------------------------------------------------------------------------
LOG_FILE="export_$(date +%Y%m%d_%H%M%S).log"
FAILED_FILE="failed_tables.txt"
DONE_FILE="done_tables.txt"
DONE_TRANSFERS_FILE="done_transfers.txt"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"; }
log_err() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2; }

# -----------------------------------------------------------------------------
# STEP 0 — Verify dependencies
# -----------------------------------------------------------------------------
log "Checking dependencies..."
if $GCLOUD_RUN; then
  for cmd in gcloud; do
    if ! command -v "$cmd" &>/dev/null; then
      log_err "'$cmd' not found. Install google-cloud-sdk."
      exit 1
    fi
  done
else
  for cmd in bq gcloud gsutil parallel rclone flock; do
    if ! command -v "$cmd" &>/dev/null; then
      log_err "'$cmd' not found. Install google-cloud-sdk, GNU parallel, and rclone."
      exit 1
    fi
  done
fi

# Validate S3 credentials
if [[ -z "${AWS_ACCESS_KEY_ID:-}" || -z "${AWS_SECRET_ACCESS_KEY:-}" ]]; then
  log_err "Credenciais S3 não encontradas. Preencha o .env com AWS_ACCESS_KEY_ID e AWS_SECRET_ACCESS_KEY."
  exit 1
fi

# Validate GCP project (needed for --sync)
if [[ -z "${GCP_PROJECT:-}" ]]; then
  if $SYNC_RUN; then
    if [[ -z "${YOUR_PROJECT:-}" ]]; then
      log_err "GCP_PROJECT não encontrado no .env. Adicione GCP_PROJECT ou YOUR_PROJECT."
      exit 1
    fi
    log "GCP_PROJECT not set, using YOUR_PROJECT: $YOUR_PROJECT"
    export GCP_PROJECT="$YOUR_PROJECT"
  fi
fi

# Configure rclone remotes via env vars — no rclone.conf or inline credentials needed.
# GCS remote (bd:) uses Application Default Credentials from gcloud auth application-default login.
# Hetzner S3 remote (hz:) uses the credentials from .env, kept out of the process command line.
export RCLONE_CONFIG_BD_TYPE="google cloud storage"
export RCLONE_CONFIG_BD_BUCKET_POLICY_ONLY="true"
export RCLONE_CONFIG_HZ_TYPE="s3"
export RCLONE_CONFIG_HZ_PROVIDER="Other"
export RCLONE_CONFIG_HZ_ENDPOINT="$HETZNER_S3_ENDPOINT"
export RCLONE_CONFIG_HZ_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID"
export RCLONE_CONFIG_HZ_SECRET_ACCESS_KEY="$AWS_SECRET_ACCESS_KEY"

# =============================================================================
# GCLOUD RUN — create a Compute Engine VM, run the export there, then clean up
# =============================================================================
if $GCLOUD_RUN; then
  VM_NAME="${GCP_VM_NAME:-bd-export-vm}"
  VM_ZONE="${GCP_VM_ZONE:-us-central1-a}"
  SCRIPT_PATH="$(realpath "$0")"
  ENV_PATH="$(dirname "$SCRIPT_PATH")/.env"

  log "=============================="
  log " GCLOUD RUN MODE"
  log "=============================="

  # ── Step 1/4: Create instance ───────────────────────────────────────────
  log "[1/4] Creating VM: $VM_NAME ($VM_ZONE) ..."
  if gcloud compute instances describe "$VM_NAME" \
      --zone="$VM_ZONE" --project="$YOUR_PROJECT" &>/dev/null; then
    log "  VM already exists, reusing it."
  else
    gcloud compute instances create "$VM_NAME" \
      --project="$YOUR_PROJECT" \
      --zone="$VM_ZONE" \
      --machine-type=e2-standard-4 \
      --image-family=debian-12 \
      --image-project=debian-cloud \
      --boot-disk-size=20GB \
      --scopes=cloud-platform
    log "  VM created."
  fi

  # ── Step 2/4: Wait for SSH + copy files ────────────────────────────────
  log "[2/4] Waiting for SSH and copying files..."
  for i in {1..18}; do
    if gcloud compute ssh "$VM_NAME" \
        --zone="$VM_ZONE" --project="$YOUR_PROJECT" \
        --command="echo ready" 2>/dev/null; then
      break
    fi
    log "  SSH not ready yet ($i/18), retrying in 10s..."
    sleep 10
  done

  gcloud compute scp "$SCRIPT_PATH" "$ENV_PATH" \
    "$VM_NAME:~/" \
    --zone="$VM_ZONE" \
    --project="$YOUR_PROJECT"
  log "  Files copied."

  # ── Step 3/4: Install dependencies ─────────────────────────────────────
  log "[3/4] Installing dependencies on VM (~2 min)..."
  gcloud compute ssh "$VM_NAME" \
    --zone="$VM_ZONE" \
    --project="$YOUR_PROJECT" \
    --command="bash -s" <<'REMOTE_SETUP'
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y apt-transport-https ca-certificates gnupg curl parallel rclone
curl -fsSL https://packages.cloud.google.com/apt/doc/apt-key.gpg \
  | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
  | sudo tee /etc/apt/sources.list.d/google-cloud-sdk.list >/dev/null
sudo apt-get update -qq
sudo apt-get install -y google-cloud-cli
chmod +x ~/roda.sh
echo "Dependencies installed."
REMOTE_SETUP
  log "  Dependencies ready."

  # ── Step 4/4: Run the export script interactively ──────────────────────
  log "[4/4] Launching roda.sh on VM — answer prompts as they appear."
  gcloud compute ssh "$VM_NAME" \
    --zone="$VM_ZONE" \
    --project="$YOUR_PROJECT" \
    -- bash ~/roda.sh

  # ── Cleanup: Delete VM ──────────────────────────────────────────────────
  echo ""
  echo "============================================================"
  echo "  CLEANUP"
  echo "============================================================"
  read -rp "Delete VM instance $VM_NAME? [y/N] " del_vm
  if [[ "$del_vm" =~ ^[Yy]$ ]]; then
    log "Deleting VM $VM_NAME ..."
    gcloud compute instances delete "$VM_NAME" \
      --zone="$VM_ZONE" \
      --project="$YOUR_PROJECT" \
      --quiet
    log "VM deleted."
  else
    log "VM kept. To delete manually:"
    log "  gcloud compute instances delete $VM_NAME --zone=$VM_ZONE --project=$YOUR_PROJECT"
  fi

  exit 0
fi

# =============================================================================
# SYNC — BigQuery → S3 direct (no GCS intermediary)
# =============================================================================
if $SYNC_RUN; then
  log "=============================="
  log " SYNC MODE — BigQuery → S3"
  log "=============================="

  # Check dependencies
  for cmd in python3; do
    if ! command -v "$cmd" &>/dev/null; then
      log_err "'$cmd' not found."
      exit 1
    fi
  done

  # Check Python dependencies (import name vs pip package name differs)
  PYTHON_CHECKS="google.cloud.bigquery:boto3:pandas:pyarrow"
  for check in $(echo "$PYTHON_CHECKS" | tr ':' '\n'); do
    module="${check}"
    if ! python3 -c "import ${module}" 2>/dev/null; then
      pip_pkg="${module}"
      log_err "Missing Python package: ${pip_pkg}. Run: pip install google-cloud-bigquery boto3 pandas pyarrow"
      exit 1
    fi
  done

  # Set GCP_PROJECT for the Python script
  export GCP_PROJECT="${GCP_PROJECT:-${YOUR_PROJECT}}"

  log "GCP project: $GCP_PROJECT"
  log "S3 bucket:   $HETZNER_S3_BUCKET"
  log "S3 endpoint: $HETZNER_S3_ENDPOINT"
  log ""

  if $DRY_RUN; then
    log "DRY RUN — listing tables only, no data will be transferred"
  fi

  # Run the sync script, filtering out --sync (roda.sh flag)
  SYNC_ARGS=()
  for arg in "$@"; do
    [[ "$arg" != "--sync" ]] && SYNC_ARGS+=("$arg")
  done
  python3 sync_bq_to_local.py "${SYNC_ARGS[@]+"${SYNC_ARGS[@]}"}"
  exit $?
fi

# -----------------------------------------------------------------------------
# STEP 1 — Create GCS bucket in US region (same as basedosdados)
# -----------------------------------------------------------------------------
if $DRY_RUN; then
  log "[DRY RUN] Would create GCS bucket: gs://$BUCKET_NAME in region $BUCKET_REGION"
else
  log "Creating GCS bucket: gs://$BUCKET_NAME in region $BUCKET_REGION"
  if gsutil ls "gs://$BUCKET_NAME" &>/dev/null; then
    log "Bucket already exists, skipping creation."
  else
    gsutil mb \
      -p "$YOUR_PROJECT" \
      -l "$BUCKET_REGION" \
      -b on \
      "gs://$BUCKET_NAME"
    log "Bucket created: gs://$BUCKET_NAME"
  fi

fi

# Resume support: load already-done tables/transfers
touch "$DONE_FILE" "$FAILED_FILE" "$DONE_TRANSFERS_FILE"

# -----------------------------------------------------------------------------
# STEP 2 — Build the full table list from the basedosdados project
#
# We auto-discover all datasets and tables via the BQ API so we don't rely
# on a hardcoded list. This also detects any new tables added since the
# tables-summary.md was written.
#
# Atomicity: we write to a .tmp file and mv it into place only on success,
# so an interrupted run never leaves a partial list behind.
# -----------------------------------------------------------------------------
log "Discovering all datasets in project: $SOURCE_PROJECT ..."
TABLE_LIST_FILE="all_tables.txt"
TABLE_LIST_TMP="${TABLE_LIST_FILE}.tmp"

if [[ ! -f "$TABLE_LIST_FILE" ]]; then
  bq ls --project_id="$SOURCE_PROJECT" --max_results=10000 --format=json 2>/dev/null \
    | python3 -c "
import json, sys
datasets = json.load(sys.stdin)
for ds in datasets:
    print(ds['datasetReference']['datasetId'])
" > /tmp/datasets.txt

  log "Found $(wc -l < /tmp/datasets.txt) datasets. Listing tables in parallel..."

  TMP_TABLE_DIR=$(mktemp -d)

  list_dataset_tables() {
    local dataset="$1"
    local source="$2"
    local tmp_dir="$3"
    bq ls \
      --project_id="$source" \
      --dataset_id="$source:$dataset" \
      --max_results=10000 \
      --format=json 2>/dev/null \
    | python3 -c "
import json, sys
data = sys.stdin.read()
if not data.strip():
    sys.exit(0)
for t in json.loads(data):
    ref = t.get('tableReference', {})
    if t.get('type') in ('TABLE', 'EXTERNAL'):
        print(ref['datasetId'] + '.' + ref['tableId'])
" > "$tmp_dir/$dataset.txt"
  }
  export -f list_dataset_tables

  parallel --jobs 16 list_dataset_tables {} "$SOURCE_PROJECT" "$TMP_TABLE_DIR" < /tmp/datasets.txt

  cat "$TMP_TABLE_DIR"/*.txt | sort > "$TABLE_LIST_TMP"
  rm -rf "$TMP_TABLE_DIR"
  mv "$TABLE_LIST_TMP" "$TABLE_LIST_FILE"
  log "Total tables discovered: $(wc -l < "$TABLE_LIST_FILE")"
else
  log "Reusing existing table list: $TABLE_LIST_FILE ($(wc -l < "$TABLE_LIST_FILE") tables)"
fi

# -----------------------------------------------------------------------------
# DRY RUN — show table count and exit
# -----------------------------------------------------------------------------
if $DRY_RUN; then
  TOTAL=$(wc -l < "$TABLE_LIST_FILE")
  log "[DRY RUN] $TOTAL tables found. No exports will run."
  log "[DRY RUN] Estimating total size via bq show in parallel (this may take a while)..."

  get_table_bytes() {
    local table="$1"
    local source="$2"
    local dataset table_id
    dataset=$(echo "$table" | cut -d. -f1)
    table_id=$(echo "$table" | cut -d. -f2)
    bq show --format=json "${source}:${dataset}.${table_id}" 2>/dev/null \
      | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('numBytes','0'))" 2>/dev/null \
      || echo 0
  }
  export -f get_table_bytes

  TOTAL_BYTES=$(parallel --jobs 16 get_table_bytes {} "$SOURCE_PROJECT" < "$TABLE_LIST_FILE" \
    | awk '{s+=$1} END{print s+0}')

  TOTAL_GB=$(echo "scale=2; $TOTAL_BYTES / 1073741824" | bc)
  # Parquet+zstd typically compresses structured data 5–10x vs BigQuery's raw numBytes
  COMPRESSED_LOW=$(echo "scale=2; $TOTAL_GB / 10" | bc)
  COMPRESSED_HIGH=$(echo "scale=2; $TOTAL_GB / 5" | bc)
  EGRESS_LOW=$(echo "scale=2; $COMPRESSED_LOW * 0.08" | bc)
  EGRESS_HIGH=$(echo "scale=2; $COMPRESSED_HIGH * 0.12" | bc)
  log "[DRY RUN] BigQuery raw size (uncompressed): ~${TOTAL_GB} GB"
  log "[DRY RUN] Estimated Parquet+zstd size:      ~${COMPRESSED_LOW}–${COMPRESSED_HIGH} GB"
  log "[DRY RUN] Estimated GCS→Hetzner egress cost: USD ${EGRESS_LOW}–${EGRESS_HIGH}"
  log "[DRY RUN] Done. Remove --dry-run to start the actual export."
  exit 0
fi

# -----------------------------------------------------------------------------
# COST WARNING — confirm before starting export
# -----------------------------------------------------------------------------
echo ""
echo "============================================================"
echo "  COST WARNING"
echo "  Transferring data from GCS to Hetzner costs ~\$0.08-0.12/GB"
echo "  in internet egress fees charged to: $YOUR_PROJECT"
echo "  Run with --dry-run first to estimate the total size."
echo "============================================================"
echo ""
read -rp "Press ENTER to start the export, or Ctrl+C to abort: "

# -----------------------------------------------------------------------------
# STEP 3 — Export function (called in parallel)
# -----------------------------------------------------------------------------
export_table() {
  local table="$1"
  local bucket="$2"
  local project="$3"
  local source="$4"
  local done_file="$5"
  local failed_file="$6"
  local log_file="$7"

  # Skip if already done
  if grep -qxF "$table" "$done_file" 2>/dev/null; then
    echo "[SKIP] $table (already exported)" >> "$log_file"
    return 0
  fi

  local dataset table_id gcs_prefix
  dataset=$(echo "$table" | cut -d. -f1)
  table_id=$(echo "$table" | cut -d. -f2)
  gcs_prefix="gs://$bucket/$dataset/$table_id"

  echo "[START] Exporting $source:$table → $gcs_prefix/*.parquet" >> "$log_file"

  # Run bq extract with retry (up to 3 attempts)
  # Skip retries immediately if the error is a known incompatible type
  local attempt=0
  local success=false
  local output
  while [[ $attempt -lt 3 ]]; do
    attempt=$((attempt + 1))
    output=$(bq extract \
        --project_id="$project" \
        --destination_format=PARQUET \
        --compression=ZSTD \
        --location=US \
        "${source}:${dataset}.${table_id}" \
        "${gcs_prefix}/*.parquet" \
        2>&1)
    local exit_code=$?
    echo "$output" >> "$log_file"

    if [[ $exit_code -eq 0 ]]; then
      success=true
      break
    fi

    # Detect permanently incompatible types — no point retrying
    if echo "$output" | grep -qi "not supported\|unsupported type\|GEOGRAPHY\|JSON type"; then
      echo "[SKIP_INCOMPATIBLE] $table — unsupported column type, skipping retries" >> "$log_file"
      flock "$failed_file" bash -c "echo '[INCOMPATIBLE] $table' >> '$failed_file'"
      return 0
    fi

    # Detect access/permission errors — no point retrying
    if echo "$output" | grep -qi "access denied\|permission denied\|not authorized\|403\|does not exist\|Not found"; then
      echo "[SKIP_ACCESS] $table — access denied or not found, skipping retries" >> "$log_file"
      flock "$failed_file" bash -c "echo '[ACCESS_DENIED] $table' >> '$failed_file'"
      return 0
    fi

    echo "[RETRY $attempt/3] $table" >> "$log_file"
    sleep $((attempt * 10))
  done

  if $success; then
    # flock prevents race condition when multiple workers write concurrently
    flock "$done_file" bash -c "echo '$table' >> '$done_file'"
    echo "[DONE] $table" >> "$log_file"
  else
    flock "$failed_file" bash -c "echo '$table' >> '$failed_file'"
    echo "[FAIL] $table after 3 attempts" >> "$log_file"
  fi
}

export -f export_table

# -----------------------------------------------------------------------------
# STEP 4 — Run exports in parallel
# -----------------------------------------------------------------------------
log "Starting parallel exports ($PARALLEL_EXPORTS workers)..."
log "Progress is logged to: $LOG_FILE"
log "Failed tables will be written to: $FAILED_FILE"

# Filter out already-done tables
comm -23 \
  <(sort "$TABLE_LIST_FILE") \
  <(sort "$DONE_FILE") \
| parallel \
    --jobs "$PARALLEL_EXPORTS" \
    --progress \
    --bar \
    export_table {} "$BUCKET_NAME" "$YOUR_PROJECT" "$SOURCE_PROJECT" \
                    "$DONE_FILE" "$FAILED_FILE" "$LOG_FILE" \
|| true  # failures are tracked in $FAILED_FILE; don't let parallel's exit code abort the script

TOTAL=$(wc -l < "$TABLE_LIST_FILE")
DONE=$(wc -l < "$DONE_FILE")
FAILED=$(wc -l < "$FAILED_FILE")
log "Export phase complete: $DONE/$TOTAL done, $FAILED failed"

if [[ $FAILED -gt 0 ]]; then
  log "Failed tables:"
  cat "$FAILED_FILE" | tee -a "$LOG_FILE"
  log "To retry failed tables only, run: bash $0 --retry-failed"
fi

# -----------------------------------------------------------------------------
# STEP 5 — Transfer GCS → Hetzner Object Storage via rclone (no local staging)
#
# rclone streams data directly between GCS and S3 through RAM only —
# no local disk required.
# -----------------------------------------------------------------------------
log "Starting transfer to Hetzner Object Storage ($HETZNER_S3_ENDPOINT)..."

TRANSFER_LOG_DIR=$(mktemp -d)

# Compute total datasets in GCS bucket once (used for progress display)
TRANSFER_TOTAL=$(gsutil ls "gs://$BUCKET_NAME/" | wc -l)
export TRANSFER_TOTAL

download_dataset() {
  local dataset="$1"
  local bucket="$2"
  local s3_bucket="$3"
  local s3_concurrency="$4"
  local done_transfers_file="$5"
  local log_dir="$6"
  local total="$7"
  local dataset_log="$log_dir/${dataset}.log"

  # Resume: skip datasets already transferred
  if grep -qxF "$dataset" "$done_transfers_file" 2>/dev/null; then
    echo "[SKIP_TRANSFER] $dataset (already transferred)" > "$dataset_log"
    return 0
  fi

  echo "[TRANSFER] gs://$bucket/$dataset/ → hz:$s3_bucket/$dataset/" > "$dataset_log"

  # Named remotes bd: (GCS) and hz: (Hetzner S3) are configured via RCLONE_CONFIG_* env vars
  if rclone copy \
      "bd:$bucket/$dataset/" \
      "hz:$s3_bucket/$dataset/" \
      --transfers "$s3_concurrency" \
      --s3-upload-concurrency "$s3_concurrency" \
      --progress \
      >> "$dataset_log" 2>&1; then
    flock "$done_transfers_file" bash -c "echo '$dataset' >> '$done_transfers_file'"
    echo "[TRANSFERRED] $dataset" >> "$dataset_log"
    local done_count
    done_count=$(wc -l < "$done_transfers_file")
    local pct=$(( done_count * 100 / total ))
    echo "[${done_count}/${total}] ${pct}% datasets transferidos"
  else
    echo "[TRANSFER FAIL] rclone failed for $dataset" >> "$dataset_log"
    return 1
  fi
}

export -f download_dataset

# Get list of exported datasets, skipping already-transferred ones
comm -23 \
  <(gsutil ls "gs://$BUCKET_NAME/" | sed 's|gs://[^/]*/||;s|/||' | sort -u) \
  <(sort "$DONE_TRANSFERS_FILE") \
| parallel \
    --jobs "$PARALLEL_UPLOADS" \
    download_dataset {} "$BUCKET_NAME" "$HETZNER_S3_BUCKET" "$S3_CONCURRENCY" "$DONE_TRANSFERS_FILE" "$TRANSFER_LOG_DIR" "$TRANSFER_TOTAL" \
|| true  # failures are tracked per-dataset; don't abort

# Merge per-dataset logs into main log in order
for f in $(ls "$TRANSFER_LOG_DIR"/*.log 2>/dev/null | sort); do
  cat "$f" >> "$LOG_FILE"
done
rm -rf "$TRANSFER_LOG_DIR"

log "Transfer complete."

# -----------------------------------------------------------------------------
# STEP 6 — Verify file counts on Hetzner Object Storage vs GCS
# -----------------------------------------------------------------------------
log "Verifying file counts..."
GCS_COUNT=$(gsutil ls -r "gs://$BUCKET_NAME/**" | grep '\.parquet$' | wc -l)
S3_COUNT=$(rclone ls "hz:$HETZNER_S3_BUCKET" 2>/dev/null | grep '\.parquet$' | wc -l)

log "GCS parquet files: $GCS_COUNT"
log "S3 parquet files:  $S3_COUNT"

if [[ "$GCS_COUNT" -eq "$S3_COUNT" ]]; then
  log "File counts match. Transfer verified."
else
  log_err "Count mismatch! GCS=$GCS_COUNT S3=$S3_COUNT"
  log_err "Re-run the script to resume failed datasets or check $LOG_FILE for errors."
fi

# -----------------------------------------------------------------------------
# STEP 7 — Clean up GCS bucket to stop storage charges
# -----------------------------------------------------------------------------
read -rp "Delete GCS bucket gs://$BUCKET_NAME to stop storage charges? [y/N] " confirm
if [[ "$confirm" =~ ^[Yy]$ ]]; then
  log "Deleting bucket gs://$BUCKET_NAME ..."
  gsutil -m rm -r "gs://$BUCKET_NAME"
  gsutil rb "gs://$BUCKET_NAME"
  log "Bucket deleted. Storage charges stopped."
else
  log "Bucket kept. Remember to delete it later: gsutil -m rm -r gs://$BUCKET_NAME && gsutil rb gs://$BUCKET_NAME"
fi

log "All done! Data is at s3://$HETZNER_S3_BUCKET/ ($HETZNER_S3_ENDPOINT)"
log "Total exported: $DONE tables | Failed: $FAILED tables"
log "See $LOG_FILE for full details."
