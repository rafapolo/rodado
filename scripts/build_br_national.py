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
  docs/pesquisa/viz-uf/dados/br.bin.gz   # same struct-of-arrays binary format as per-UF files
  docs/pesquisa/viz-uf/dados/meta.json   # gains a "BR" entry
"""

import array
import gzip
import json
import random
import struct
import sys
from pathlib import Path

DADOS_DIR = Path("docs/pesquisa/viz-uf/dados")
META_PATH = DADOS_DIR / "meta.json"
DEFAULT_CAP = 2_000_000


def read_points(path):
    """Read a RAW2/RAW3 struct-of-arrays .bin.gz (see extrai_estados_cnpj.py's
    write_points_soa): b"RAW2"/b"RAW3", u32 n, then n lngs (f32), n lats (f32),
    n weights (u16), n years-since-1900 (u8) and, in RAW3, n CNAE section
    masks (u32). RAW2 points get an empty mask."""
    with gzip.open(path, "rb") as f:
        data = f.read()
    if data[:4] not in (b"RAW2", b"RAW3", b"RAW4"):
        raise SystemExit(f"{path}: layout antigo, sem ano; rode extrai_estados_cnpj.py de novo")
    n = struct.unpack_from("<I", data, 4)[0]
    o = 8
    lngs = array.array("f")
    lngs.frombytes(data[o : o + 4 * n])
    lats = array.array("f")
    lats.frombytes(data[o + 4 * n : o + 8 * n])
    weights = array.array("H")
    weights.frombytes(data[o + 8 * n : o + 10 * n])
    years = array.array("B")
    years.frombytes(data[o + 10 * n : o + 11 * n])
    masks = array.array("I")
    if data[:4] in (b"RAW3", b"RAW4"):
        masks.frombytes(data[o + 11 * n : o + 15 * n])
    else:
        masks.extend([0] * n)
    esps = array.array("B")
    if data[:4] == b"RAW4":
        esps.frombytes(data[o + 15 * n : o + 16 * n])
    else:
        esps.extend([0] * n)
    return list(zip(lngs, lats, weights, years, masks, esps))


def main():
    cap = DEFAULT_CAP
    if "--cap" in sys.argv:
        cap = int(sys.argv[sys.argv.index("--cap") + 1])

    meta = json.loads(META_PATH.read_text())
    ufs = sorted(uf for uf in meta if uf != "BR")

    all_points = []
    n_estab_ativos = 0
    n_estab_geolocalizados = 0
    setores = {}
    especies = [0] * 8
    cruzado = [[0] * 8 for _ in range(21)]
    lngs_min = lats_min = float("inf")
    lngs_max = lats_max = float("-inf")

    for uf in ufs:
        path = DADOS_DIR / f"{uf.lower()}.bin.gz"
        pts = read_points(path)
        all_points.extend(pts)
        n_estab_ativos += meta[uf]["n_estab_ativos"]
        n_estab_geolocalizados += meta[uf]["n_estab_geolocalizados"]
        for sec, c in meta[uf].get("setores", {}).items():
            acc = setores.setdefault(sec, {"ativos": 0, "geo": 0})
            acc["ativos"] += c["ativos"]
            acc["geo"] += c["geo"]
        for k, c in enumerate(meta[uf].get("especies", [])):
            especies[k] += c
        for i, row in enumerate(meta[uf].get("cruzado", [])):
            for k, c in enumerate(row):
                cruzado[i][k] += c
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
    years = array.array("B", (p[3] for p in all_points))
    masks = array.array("I", (p[4] for p in all_points))
    esps = array.array("B", (p[5] for p in all_points))
    with gzip.open(out_path, "wb", compresslevel=9) as f:
        f.write(b"RAW4" + struct.pack("<I", len(all_points)))
        f.write(lngs.tobytes())
        f.write(lats.tobytes())
        f.write(weights.tobytes())
        f.write(years.tobytes())
        f.write(masks.tobytes())
        f.write(esps.tobytes())

    meta["BR"] = {
        "n_points": len(all_points),
        "n_estab_ativos": n_estab_ativos,
        "n_estab_geolocalizados": n_estab_geolocalizados,
        "bbox": [lngs_min, lats_min, lngs_max, lats_max],
    }
    if setores:
        meta["BR"]["setores"] = dict(sorted(setores.items()))
    if any(especies):
        meta["BR"]["especies"] = especies
        meta["BR"]["cruzado"] = cruzado
    META_PATH.write_text(json.dumps(meta, ensure_ascii=False))

    print(f"Done: {out_path} ({out_path.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
