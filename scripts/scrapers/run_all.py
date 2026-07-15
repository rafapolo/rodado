#!/usr/bin/env python3
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SCRIPTS = [
    "fetch_bndes.py",
    "fetch_tcu.py",
    "fetch_holdings.py",
    "fetch_senado.py",
    "fetch_ibama.py",
    "fetch_dou.py",
    "fetch_transferegov.py",
    "fetch_pncp.py",
]

HERE = Path(__file__).parent


def main():
    failed = 0
    for name in SCRIPTS:
        path = HERE / name
        logger.info("=" * 60)
        logger.info("Rodando: %s", name)
        logger.info("=" * 60)
        result = subprocess.run([sys.executable, str(path)], capture_output=False)
        if result.returncode != 0:
            logger.error("FALHOU: %s (exit %d)", name, result.returncode)
            failed += 1
        else:
            logger.info("OK: %s", name)

    logger.info("=" * 60)
    logger.info("Resumo: %d/8 OK, %d falhas", len(SCRIPTS) - failed, failed)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
