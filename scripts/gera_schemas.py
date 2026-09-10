"""Generate schemas.json from beelink (fully local, no cloud storage).

Covers both storage layers: parquet directories, and the 8 `duckdb_native`
tables that live only inside `basedosdados.duckdb` with no parquet behind
them (see build_metadata_catalog.py's Phase 2/2b for the same
classification — `br_ms_sipni_microdados.vacinacao_2020` and friends).
Before this, schemas.json (and everything downstream reading it, including
describe_table) was silently blind to those tables.

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

# Fase 2: tabelas sem parquet cuja view le uma tabela nativa dentro do
# proprio basedosdados.duckdb (mesma classificacao de build_metadata_catalog.py,
# Fase 2/2b). `information_schema.columns` e `duckdb_columns()` falham com
# "Invalid unicode (byte sequence mismatch)" em qualquer consulta contra esta
# base — um metadado corrompido em algum lugar do catalogo (candidato:
# br_mjsp_ckan.infopen, ja documentado como tendo nomes de coluna em UTF-8
# invalido) envenena a enumeracao inteira, filtro de WHERE ou nao. `DESCRIBE`
# por tabela evita isso por resolver so a view alvo — mas e lento nas maiores
# (~90-100M linhas): `doses_agregadas` costuma responder em segundos,
# `vacinacao_2020` mediu ate ~280s numa corrida concorrente com outra sessao
# no beelink. O timeout aqui (bem abaixo do limite de 600s do Popen em
# run_via_ssh) e so uma rede de seguranca pra nao travar o regen inteiro se
# uma view ficar realmente presa — nao um limite pensado pra excluir nada.
DB_PATH = os.path.join(ROOT, "basedosdados.duckdb")
NATIVE_JUNK_SCHEMAS = SKIP_DATASETS | {"main", "information_schema", "pg_catalog"}

def list_views():
    try:
        r = subprocess.run(
            [DUCKDB, "-readonly", "-json", DB_PATH, "-c",
             "SET enable_progress_bar=false; "
             "SELECT table_schema, table_name FROM information_schema.tables "
             "WHERE table_type='VIEW';"],
            capture_output=True, text=True, timeout=30,
        )
        return [(row["table_schema"], row["table_name"])
                for row in json.loads(r.stdout.strip() or "[]")]
    except Exception:
        return []

def get_native_columns(ds, tbl):
    try:
        r = subprocess.run(
            [DUCKDB, "-readonly", "-json", DB_PATH, "-c",
             'SET enable_progress_bar=false; DESCRIBE "%s"."%s";' % (ds, tbl)],
            capture_output=True, text=True, timeout=300,
        )
        rows = json.loads(r.stdout.strip() or "[]")
        return [{"name": row["column_name"], "type": row["column_type"]} for row in rows]
    except Exception:
        return []

disk_keys = {(ds, tbl) for ds, tbl, _, _ in tables}
native_candidates = [
    (ds, tbl) for ds, tbl in list_views()
    if ds not in NATIVE_JUNK_SCHEMAS and (ds, tbl) not in disk_keys
]
n_native_ok = 0
for ds, tbl in native_candidates:
    key = f"{ds}.{tbl}"
    cols = get_native_columns(ds, tbl)
    if not cols:
        print(f"  [native] skip {key} — DESCRIBE travou ou falhou", file=sys.stderr)
        continue
    result[key] = {
        "path": f"beelink:{DB_PATH}#{key}",
        "file_count": 0,
        "source": "duckdb_native",
        "columns": cols,
    }
    n_native_ok += 1
    print(f"  [native {n_native_ok}] {key} ({len(cols)} cols)", file=sys.stderr)

print(json.dumps({
    "_meta": {
        "source": "beelink",
        "path": ROOT,
        "total_tables": len(tables) + n_native_ok,
        "native_tables": n_native_ok,
    },
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
    # Headroom for the slowest native-table DESCRIBE (measured up to ~280s for
    # vacinacao_2020, see BEELINK_PAYLOAD) plus the ~1000-table disk walk.
    stdout, stderr = proc.communicate(input=BEELINK_PAYLOAD, timeout=900)

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
    # Fallback path only (SMB mount). Does NOT pick up duckdb_native tables —
    # that needs shelling out to a local `duckdb` binary against
    # LOCAL_MOUNT/basedosdados.duckdb, same as run_via_ssh() now does. Not
    # worth duplicating here since the documented regen chain always uses
    # run_via_ssh(); add it if this path ever becomes primary.
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
