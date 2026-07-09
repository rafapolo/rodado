#!/usr/bin/env python3
"""
Quick sync: use cached list or sample tables to avoid slow enumeration.
"""

import json
import subprocess
from pathlib import Path
from datetime import datetime
import os

PROGRESS_FILE = Path.home() / ".gcp_sync_progress"
BEELINK_HOST = "beelink"
BEELINK_PATH = "~/baseldosdados-data"

# Sample of known missing tables from previous run
MISSING_TABLES = [
    "br_anvisa_medicamentos_industrializados.microdados",
    "br_bcb_taxa_cambio.taxa_cambio",
    "br_bcb_taxa_selic.taxa_selic",
    "br_firjan_ifgf.ranking",
    "br_ggb_relatorio_lgbtqi.brasil",
    "br_ibge_amc.municipio_de_para",
    "br_ibge_cbo_2002.perfil_ocupacional",
]

def write_progress(status, pct, table="", message=""):
    """Write progress."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "timestamp": datetime.now().isoformat(),
        "status": status,
        "pct": pct,
        "table": table,
        "message": message,
    }
    with open(PROGRESS_FILE, "w") as f:
        json.dump(data, f)
    print(f"[{pct:3d}%] {status:8s} {table:50s} {message}")

def test_bq_query(dataset, table):
    """Test if we can query a table via bq."""
    query = f"SELECT COUNT(*) as cnt FROM `basedosdados.{dataset}.{table}` LIMIT 1"
    cmd = [
        "bq",
        "query",
        "--project_id=raspa-491716",
        "--format=json",
        "--nouse_legacy_sql",
        query,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result.returncode == 0

def main():
    write_progress("test", 0, "", "Testing BQ access...")

    # Test first table
    ds, tbl = MISSING_TABLES[0].split(".", 1)
    if test_bq_query(ds, tbl):
        write_progress("ready", 100, "", "✓ BigQuery queries work!")
        print(f"\n✓ Can query basedosdados tables via bq")
        print(f"  Sample missing tables: {len(MISSING_TABLES)}")
        for t in MISSING_TABLES:
            print(f"    - {t}")
    else:
        write_progress("error", 0, "", "✗ Cannot query BigQuery")
        print("✗ BQ queries failed")
        return 1

    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
