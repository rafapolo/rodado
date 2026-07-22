#!/usr/bin/env python3
"""Build a single national (all-Brazil) point file from the per-UF outputs of
extrai_estados_cnpj.py, for a "see all of Brazil at once" overview page.

Loading 26 separate files (10.5M+ points total) client-side and merging them
in the browser is slow and memory-heavy for every visitor. Instead, this
combines everything once, here, and randomly downsamples to a point-count
cap so the browser only ever has to load/parse one compact file.

Sampling is uniform-random across all points (not weighted towards dense
areas) — at national zoom, a representative random subset preserves the
country's shape and relative density just as well as the full set, since
many points already collapse onto the same handful of screen pixels anyway.

Standalone: pure stdlib, no network access beyond reading local files —
safe to re-run after any extrai_estados_cnpj.py run.

Usage: python3 scripts/build_br_national.py [--cap N]

Output:
  docs/viz-uf/dados/br.bin.gz   # same struct-of-arrays binary format as per-UF files
  docs/viz-uf/dados/meta.json   # gains a "BR" entry
"""

import array
import gzip
import json
import random
import sys
from pathlib import Path

DADOS_DIR = Path("docs/viz-uf/dados")
META_PATH = DADOS_DIR / "meta.json"
DEFAULT_CAP = 2_000_000


def read_points(path):
    """Read a struct-of-arrays .bin.gz (see extrai_estados_cnpj.py's
    write_points_soa): n lngs (f32), then n lats (f32), then n weights (u16),
    each block a whole multiple of its element size — total bytes always
    divisible by 10, so n = len(data) // 10 recovers the point count with no
    header needed."""
    with gzip.open(path, "rb") as f:
        data = f.read()
    n = len(data) // 10
    lngs = array.array("f")
    lngs.frombytes(data[0 : 4 * n])
    lats = array.array("f")
    lats.frombytes(data[4 * n : 8 * n])
    weights = array.array("H")
    weights.frombytes(data[8 * n : 10 * n])
    return list(zip(lngs, lats, weights))


def main():
    cap = DEFAULT_CAP
    if "--cap" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--cap") + 1])

    meta = json.loads(META_PATH.read_text())
    ufs = sorted(uf for uf in meta if uf != "BR")

    all_points = []
    n_estab_ativos = 0
    n_estab_geolocalizados = 0
    lngs_min = lats_min = float("inf")
    lngs_max = lats_max = float("-inf")

    for uf in ufs:
        path = DADOS_DIR / f"{uf.lower()}.bin.gz"
        pts = read_points(path)
        all_points.extend(pts)
        n_estab_ativos += meta[uf]["n_estab_ativos"]
        n_estab_geolocalizados += meta[uf]["n_estab_geolocalizados"]
        bbox = meta[uf]["bbox"]
        if bbox:
            lngs_min = min(lngs_min, bbox[0])
            lats_min = min(lats_min, bbox[1])
            lngs_max = max(lngs_max, bbox[2])
            lats_max = max(lats_max, bbox[3])
        print(f"  {uf}: {len(pts):,} points")

    total = len(all_points)
    print(f"Total points before sampling: {total:,}")

    if total > cap:
        random.seed(42)
        all_points = random.sample(all_points, cap)
        print(f"Sampled down to {cap:,} points ({cap / total * 100:.1f}%)")

    out_path = DADOS_DIR / "br.bin.gz"
    lngs = array.array("f", (p[0] for p in all_points))
    lats = array.array("f", (p[1] for p in all_points))
    weights = array.array("H", (p[2] for p in all_points))
    with gzip.open(out_path, "wb", compresslevel=9) as f:
        f.write(lngs.tobytes())
        f.write(lats.tobytes())
        f.write(weights.tobytes())

    meta["BR"] = {
        "n_points": len(all_points),
        "n_estab_ativos": n_estab_ativos,
        "n_estab_geolocalizados": n_estab_geolocalizados,
        "bbox": [lngs_min, lats_min, lngs_max, lats_max],
    }
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False))

    print(f"Done: {out_path} ({out_path.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
