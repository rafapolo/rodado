"""Generate schemas.json from beelink parquet files (fully local, no cloud storage).

Usage:
    python scripts/gera_schemas.py          # via SSH
    python scripts/gera_schemas.py --local  # if beelink is mounted at LOCAL_MOUNT
"""
import os
import sys
import json
import subprocess
import tempfile
import shutil
from pathlib import Path

BEELINK_DATA = "/home/polo/rodado"
BEELINK_HOST = "beelink"
DUCKDB = os.path.expanduser("~/bin/duckdb")
LOCAL_MOUNT = "/Volumes/homelab/rodado"
# Ancorado na raiz do repositorio, nao no cwd. Relativo, rodar de dentro de
# `scripts/` deixava uma copia morta em `scripts/schemas.json` — foi o que
# aconteceu (782 tabelas, julho, lida por ninguem). Todos os consumidores
# (`gera_join_keys`, `gera_erd`, `gera_schema_graph`, `gera_erd_poster`,
# `sync_mcp_schema`) leem `REPO / "schemas.json"`.
REPO = Path(__file__).resolve().parent.parent
OUTPUT = REPO / "schemas.json"


BEELINK_PAYLOAD = r"""import json, subprocess, os, sys

ROOT = "/home/polo/rodado"
DUCKDB = os.path.expanduser("~/bin/duckdb")

def get_schema(parquet_paths):
    cols = []
    for f in parquet_paths:
        try:
            r = subprocess.run(
                [DUCKDB, "-json", "-c",
                 "SELECT name, type FROM parquet_schema('%s') WHERE name NOT IN ('__index_level_0__', '__row_number__') AND type IS NOT NULL" % f],
                capture_output=True, text=True, timeout=30,
            )
            rows = json.loads(r.stdout.strip() or "[]")
            for row in rows:
                nm = row.get("name")
                if nm and nm not in {c["name"] for c in cols}:
                    cols.append({"name": nm, "type": row.get("type", "?")})
        except Exception:
            pass
        if cols:
            break
    return cols

# datasets de infraestrutura/teste que nao sao dado publico: nao entram no
# catalogo nem na contagem divulgada de tabelas
SKIP_DATASETS = {
    "logs",
    "test_dataset",
    "dataset_new_arch",
    "_local_rais_cnpj",
}

tables = []
for ds in sorted(os.listdir(ROOT)):
    dspath = os.path.join(ROOT, ds)
    if not os.path.isdir(dspath) or ds.startswith(".") or ds in SKIP_DATASETS:
        continue
    for tbl in sorted(os.listdir(dspath)):
        tblpath = os.path.join(dspath, tbl)
        if not os.path.isdir(tblpath) or tbl.startswith("."):
            continue
        parquets = sorted(
            os.path.join(tblpath, f) for f in os.listdir(tblpath)
            if f.endswith(".parquet")
        )
        # Tabela particionada em hive (`bacia=00/`, `ano=2020/`) nao tem
        # parquet no topo. Sem esta descida as 7 series do
        # `br_ana_telemetria` (160M+ linhas) ficavam fora de schemas.json e,
        # por tabela, fora do join_keys/ERD/atlas/describe_table — invisiveis
        # sem erro nenhum.
        part_keys = []
        if not parquets:
            for dirpath, dirnames, filenames in os.walk(tblpath):
                dirnames.sort()
                hits = sorted(
                    os.path.join(dirpath, f) for f in filenames
                    if f.endswith(".parquet")
                )
                if hits:
                    parquets = hits
                    rel = os.path.relpath(dirpath, tblpath)
                    part_keys = [
                        seg.split("=", 1)[0]
                        for seg in rel.split(os.sep)
                        if "=" in seg
                    ]
                    break
        if parquets:
            tables.append((ds, tbl, parquets, part_keys))

result = {}
for i, (ds, tbl, parquets, part_keys) in enumerate(tables):
    key = f"{ds}.{tbl}"
    cols = get_schema(parquets)
    # A coluna de particao vive no nome do diretorio, nao no parquet:
    # `parquet_schema` nao a enxerga, mas o `read_parquet` com
    # hive_partitioning a devolve — e e sempre chave de filtro/join.
    for pk in part_keys:
        if pk not in {c["name"] for c in cols}:
            cols.append({"name": pk, "type": "BYTE_ARRAY"})
    result[key] = {
        "path": f"beelink:{ROOT}/{ds}/{tbl}/",
        "file_count": len(parquets),
        "columns": cols,
    }
    print(f"  [{i+1}/{len(tables)}] {key} ({len(cols)} cols, {len(parquets)} files)", file=sys.stderr)

print(json.dumps({
    "_meta": {"source": "beelink", "path": ROOT, "total_tables": len(tables)},
    "tables": dict(sorted(result.items())),
}, ensure_ascii=False, indent=2))
"""


def run_via_ssh():
    print(f"Shipping schema extractor to {BEELINK_HOST}...", file=sys.stderr)
    proc = subprocess.Popen(
        ["ssh", BEELINK_HOST, "python3"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = proc.communicate(input=BEELINK_PAYLOAD, timeout=600)

    for line in stderr.strip().split("\n"):
        if line.strip():
            print(f"[beelink] {line}", file=sys.stderr)

    if proc.returncode != 0:
        print(f"Error: remote script failed (exit {proc.returncode})", file=sys.stderr)
        sys.exit(1)

    try:
        output = json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"Error parsing beelink output: {e}", file=sys.stderr)
        print(f"Raw stdout (first 1k): {stdout[:1000]}", file=sys.stderr)
        sys.exit(1)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    meta = output["_meta"]
    print(f"\nDone! {OUTPUT} written ({meta['total_tables']} tables)", file=sys.stderr)


def run_local():
    if not os.path.isdir(LOCAL_MOUNT):
        print(f"Local mount {LOCAL_MOUNT} not found", file=sys.stderr)
        sys.exit(1)

    try:
        import pyarrow.parquet as pq
    except ImportError:
        print("pyarrow required for local mode: pip install pyarrow", file=sys.stderr)
        sys.exit(1)

    tables = []
    for ds in sorted(os.listdir(LOCAL_MOUNT)):
        dspath = os.path.join(LOCAL_MOUNT, ds)
        if not os.path.isdir(dspath) or ds.startswith(".") or ds in SKIP_DATASETS:
            continue
        for tbl in sorted(os.listdir(dspath)):
            tblpath = os.path.join(dspath, tbl)
            if not os.path.isdir(tblpath) or tbl.startswith("."):
                continue
            parquets = sorted(
                os.path.join(tblpath, f) for f in os.listdir(tblpath)
                if f.endswith(".parquet")
            )
            # mesma descida em hive do caminho por SSH, ver BEELINK_PAYLOAD
            part_keys = []
            if not parquets:
                for dirpath, dirnames, filenames in os.walk(tblpath):
                    dirnames.sort()
                    hits = sorted(
                        os.path.join(dirpath, f) for f in filenames
                        if f.endswith(".parquet")
                    )
                    if hits:
                        parquets = hits
                        rel = os.path.relpath(dirpath, tblpath)
                        part_keys = [
                            seg.split("=", 1)[0]
                            for seg in rel.split(os.sep)
                            if "=" in seg
                        ]
                        break
            if parquets:
                tables.append((ds, tbl, parquets, part_keys))

    result = {}
    for i, (ds, tbl, parquets, part_keys) in enumerate(tables):
        key = f"{ds}.{tbl}"
        cols = []
        for f in parquets:
            try:
                schema = pq.read_schema(f)
                for field in schema:
                    if field.name not in {c["name"] for c in cols}:
                        cols.append({"name": field.name, "type": str(field.type)})
            except Exception:
                pass
            if cols:
                break
        for pk in part_keys:
            if pk not in {c["name"] for c in cols}:
                cols.append({"name": pk, "type": "string"})
        result[key] = {
            "path": f"{LOCAL_MOUNT}/{ds}/{tbl}/",
            "file_count": len(parquets),
            "columns": cols,
        }
        print(f"  [{i+1}/{len(tables)}] {key} ({len(cols)} cols, {len(parquets)} files)", file=sys.stderr)

    output = {
        "_meta": {"source": "local_mount", "path": LOCAL_MOUNT, "total_tables": len(tables)},
        "tables": dict(sorted(result.items())),
    }
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\nDone! {OUTPUT} written ({len(tables)} tables)", file=sys.stderr)


if __name__ == "__main__":
    if "--local" in sys.argv:
        run_local()
    else:
        run_via_ssh()
