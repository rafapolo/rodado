import logging
import os
import subprocess
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)


def download_file(url: str, dest: Path, timeout: int = 600) -> bool:
    import httpx
    partial = dest.with_suffix(dest.suffix + ".partial")
    start_byte = partial.stat().st_size if partial.exists() else 0
    headers = {"User-Agent": "rodado-etl/1.0"}
    if start_byte > 0:
        headers["Range"] = f"bytes={start_byte}-"
        logger.info("Retomando %s de %.1f MB", dest.name, start_byte / 1e6)
    try:
        with httpx.stream("GET", url, follow_redirects=True, timeout=timeout, headers=headers) as r:
            if r.status_code == 416:
                if partial.exists():
                    partial.rename(dest)
                return True
            r.raise_for_status()
            mode = "ab" if start_byte > 0 else "wb"
            with open(partial, mode) as f:
                for chunk in r.iter_bytes(65536):
                    f.write(chunk)
            partial.rename(dest)
            logger.info("Download OK: %s", dest.name)
            return True
    except Exception as e:
        logger.warning("Falha ao baixar %s: %s", dest.name, e)
        return False


def write_parquet(df, dest: Path, schema: pa.Schema | None = None) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df, schema=schema, preserve_index=False)
    pq.write_table(table, dest, compression="zstd", row_group_size=50000)
    n = len(df)
    logger.info("Parquet escrito: %s (%d linhas)", dest, n)
    return n


def rsync_to_beelink(local_path: Path, dest_path: str) -> bool:
    host = os.environ.get("BEELINK_HOST", "beelink")
    base = os.environ.get("BEELINK_PATH", "~/rodado")
    full_dest = f"{host}:{base}/{dest_path}/"
    try:
        subprocess.run(
            ["rsync", "-avz", "--progress", f"{local_path}/", full_dest],
            check=True, capture_output=True, text=True, timeout=600,
        )
        logger.info("rsync OK: %s -> %s", local_path, full_dest)
        return True
    except subprocess.CalledProcessError as e:
        logger.warning("rsync falhou: %s", e.stderr[:500])
        return False
    except FileNotFoundError:
        logger.warning("rsync não encontrado. Instale com: brew install rsync")
        return False
