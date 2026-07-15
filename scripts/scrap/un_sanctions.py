#!/usr/bin/env python3
"""
Fetch UN Security Council Consolidated Sanctions List -> Parquet -> beelink.

Source: found via the real UN Security Council page
(https://main.un.org/securitycouncil/en/content/un-sc-consolidated-list),
which links to:

    https://scsanctions.un.org/resources/xml/en/consolidated.xml

This 302-redirects (short-lived, ~1h signed URL) to an Azure Blob Storage
object (unsolprodfiles.blob.core.windows.net/publiclegacyxmlfiles/...) that
serves the actual XML — no auth needed, just follow the redirect (curl -L /
urllib's default redirect handling). This supersedes the previously-guessed
static `scsanctions.un.org` XML path in this doc, which 404s directly; the
real access pattern is a redirect-minted signed URL, not a fixed path.

Note on overlap: OpenSanctions' consolidated feed (already on beelink at
global_opensanctions/entities, 1.3M rows) already includes un_sc_sanctions as
one of its source datasets (~2,887 entities per
opensanctions.org/datasets/un_sc_sanctions). This pipeline still pulls the
UN's own primary-source XML directly since the fetch is cheap and preserves
UN reference numbers / INTERPOL notice links not necessarily retained 1:1 in
a cross-source consolidated export.

The XML has two top-level record types (INDIVIDUALS/INDIVIDUAL and
ENTITIES/ENTITY), each with irregular nested sub-elements (aliases,
addresses, dates/places of birth, documents — which may repeat 0, 1, or many
times per record). Two tables are written: `individuals` and `entities`.
Scalar top-level fields become string columns as-is; nested/repeated
sub-elements are JSON-serialized into their own `<tag>` string column (e.g.
`individual_alias`, `entity_address`) rather than reshaped into separate
tables, to keep the pipeline simple for a one-off government XML export.

Usage:
    python3 scripts/scrap/un_sanctions.py
"""

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/un_sanctions/sanctions"
XML_URL = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/"
    "c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/un_sanctions"
)
UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
)


def fetch_xml() -> bytes:
    req = Request(XML_URL, headers={"User-Agent": UA})
    with urlopen(req, timeout=120) as resp:
        return resp.read()


def elem_to_obj(elem):
    children = list(elem)
    if not children:
        text = (elem.text or "").strip()
        return text if text else None
    groups = {}
    for c in children:
        groups.setdefault(c.tag, []).append(elem_to_obj(c))
    return {tag: (vals[0] if len(vals) == 1 else vals) for tag, vals in groups.items()}


def flatten_record(elem) -> dict:
    obj = elem_to_obj(elem)
    row = {}
    for k, v in obj.items():
        key = k.lower()
        if isinstance(v, (dict, list)):
            row[key] = json.dumps(v, ensure_ascii=False)
        else:
            row[key] = v
    return row


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Fetching {XML_URL} ...")
    raw = fetch_xml()
    print(f"  downloaded {len(raw) / 1e6:.2f} MB")

    xml_path = TEMP_DIR / "un_consolidated.xml"
    xml_path.write_bytes(raw)

    root = ET.fromstring(raw)
    date_generated = root.attrib.get("dateGenerated")
    print(f"  dateGenerated={date_generated}")

    individuals_el = root.find("INDIVIDUALS")
    entities_el = root.find("ENTITIES")

    individual_rows = [flatten_record(e) for e in (individuals_el.findall("INDIVIDUAL") if individuals_el is not None else [])]
    entity_rows = [flatten_record(e) for e in (entities_el.findall("ENTITY") if entities_el is not None else [])]

    for r in individual_rows:
        r["date_generated"] = date_generated
    for r in entity_rows:
        r["date_generated"] = date_generated

    print(f"Individuals: {len(individual_rows)}, Entities: {len(entity_rows)}")
    if not individual_rows and not entity_rows:
        print("No rows parsed — aborting, not pushing an empty file.")
        return 1

    # Write both tables locally first, so local artifacts exist even if the
    # beelink push below fails (e.g. transient SSH/network issue).
    written = []
    for name, rows in (("individuals", individual_rows), ("entities", entity_rows)):
        if not rows:
            print(f"  skipping {name}: no rows")
            continue
        table = pa.Table.from_pylist(rows)
        parquet_path = TEMP_DIR / f"{name}.parquet"
        pq.write_table(table, str(parquet_path), compression="zstd")
        print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.2f} MB, {table.num_rows} rows)")
        written.append(parquet_path)

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=True)

    ok = True
    for parquet_path in written:
        result = subprocess.run(
            f"rsync -av {parquet_path} {BEELINK_HOST}:{BEELINK_PATH}/",
            shell=True,
        )
        if result.returncode != 0:
            print(f"rsync failed for {parquet_path.name}", file=sys.stderr)
            ok = False
        else:
            print(f"Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
