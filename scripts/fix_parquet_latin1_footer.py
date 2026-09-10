#!/usr/bin/env python3
"""Fix latin-1 mojibake in a parquet file's schema metadata (column names),
without touching row data.

Motivating case: br_mjsp_ckan.infopen (fixed 2026-09-10, beelink) had its
whole footer's SchemaElement.name written in raw latin-1 instead of UTF-8
("Situa\xe7\xe3o" instead of "Situação"). DuckDB (and pyarrow) reject any
VARCHAR construction from invalid UTF-8, so this didn't just break
`DESCRIBE`/`SELECT` on the one table — it poisoned any catalog-wide
`information_schema.columns`/`duckdb_columns()` query against the *whole*
database, since those materialize every table's columns before any WHERE
filter applies. `COUNT(*)` still worked (no column binding needed); nothing
that named a column did.

Common in Brazilian government open-data exports: some pipeline stage wrote
Portuguese column names (ç, ã, é, í, ó...) through latin-1/cp1252 encoding
into a parquet writer that assumes UTF-8 (parquet's spec requires UTF-8 for
schema/metadata strings).

Usage:
    python3 scripts/fix_parquet_latin1_footer.py <path/to/file.parquet>              # dry run: report only
    python3 scripts/fix_parquet_latin1_footer.py <path/to/file.parquet> --apply      # backup + fix in place

What it touches and why that's safe:
    - SchemaElement.name              (column names)
    - ColumnMetaData.path_in_schema   (column name, duplicated per row group)
    Both are `required string` in parquet.thrift — always text, never
    ambiguous. Everything else, including data pages, is copied through
    byte-for-byte with ZERO inspection.

What it deliberately does NOT touch:
    - Statistics.min/max/min_value/max_value — `binary` in the Thrift IDL
      because for a numeric column it's a raw fixed-width encoded number,
      not text. An early version of this script blindly "fixed" any BINARY
      field that failed UTF-8 validation; that silently corrupted numeric
      min/max stats (random binary very often fails UTF-8 validation by
      chance, then gets wrongly latin-1-decoded into garbage). Caught in
      dry-run review before anything was written — see FIXABLE_PATH_PATTERNS.
    - Actual string column VALUES in the data pages. If a column has no
      UTF8 logical/converted-type annotation, DuckDB reads it as BLOB, and
      its cell content can independently hold latin-1 bytes even after this
      fix (infopen's free-text "Endereço"/"Outras Denominações" columns
      still do — "Av Getúlio Vargas" reads back with a literal \\xFA). Fixing
      that means decompressing and rewriting data pages, a different and
      much riskier job than this footer-only patch; this script does not
      attempt it.

Always run without --apply first and read the fix list before trusting it
on a new file — latin-1 is a strong prior for Brazilian government data but
this script doesn't try to detect the source encoding, it assumes latin-1.
"""
import re
import struct
import sys
from pathlib import Path

FIXABLE_PATH_PATTERNS = [
    re.compile(r"^FileMetaData\.f2\[\d+\]\.f4$"),                        # SchemaElement.name
    re.compile(r"^FileMetaData\.f4\[\d+\]\.f1\[\d+\]\.f3\.f3\[\d+\]$"),  # ColumnMetaData.path_in_schema[k]
]

def is_fixable_path(path):
    return any(p.match(path) for p in FIXABLE_PATH_PATTERNS)

STOP, BOOL_TRUE, BOOL_FALSE, BYTE, I16, I32, I64, DOUBLE, BINARY, LIST, SET, MAP, STRUCT = range(13)


class Reader:
    def __init__(self, data, pos=0):
        self.data = data
        self.pos = pos

    def byte(self):
        b = self.data[self.pos]
        self.pos += 1
        return b

    def raw(self, n):
        b = self.data[self.pos:self.pos + n]
        self.pos += n
        return b

    def varint(self):
        start = self.pos
        result = 0
        shift = 0
        while True:
            b = self.byte()
            result |= (b & 0x7F) << shift
            if not (b & 0x80):
                break
            shift += 7
        return result, self.data[start:self.pos]


def zigzag_decode(n):
    return (n >> 1) ^ -(n & 1)


def zigzag_encode(n):
    return (n << 1) ^ (n >> 63) if n < 0 else (n << 1)


def encode_varint(n):
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        if n:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)


FIXES = []  # collected (path, old_bytes, new_bytes) for reporting


def fix_string(raw_bytes, path):
    try:
        raw_bytes.decode("utf-8", errors="strict")
        return raw_bytes  # already valid, untouched
    except UnicodeDecodeError:
        fixed = raw_bytes.decode("latin-1").encode("utf-8")
        FIXES.append((path, raw_bytes, fixed))
        return fixed


def copy_value(r, out, ctype, path):
    if ctype in (BOOL_TRUE, BOOL_FALSE):
        return  # value is in the type nibble itself, nothing to copy
    elif ctype == BYTE:
        out += r.raw(1)
    elif ctype in (I16, I32, I64):
        _, raw = r.varint()
        out += raw
    elif ctype == DOUBLE:
        out += r.raw(8)
    elif ctype == BINARY:
        length, _ = r.varint()
        content = r.raw(length)
        fixed = fix_string(content, path) if is_fixable_path(path) else content
        out += encode_varint(len(fixed))
        out += fixed
    elif ctype in (LIST, SET):
        header = r.byte()
        size = (header >> 4) & 0x0F
        elem_type = header & 0x0F
        if size == 15:
            size, _ = r.varint()
            out += bytes([header])
            out += encode_varint(size)
        else:
            out += bytes([header])
        for i in range(size):
            copy_value(r, out, elem_type, f"{path}[{i}]")
    elif ctype == MAP:
        size, _ = r.varint()
        if size == 0:
            out += b"\x00"
            return
        out += encode_varint(size)
        kv_types = r.byte()
        out += bytes([kv_types])
        key_type = (kv_types >> 4) & 0x0F
        val_type = kv_types & 0x0F
        for i in range(size):
            copy_value(r, out, key_type, f"{path}.key[{i}]")
            copy_value(r, out, val_type, f"{path}.val[{i}]")
    elif ctype == STRUCT:
        copy_struct(r, out, path)
    else:
        raise ValueError(f"unknown compact type {ctype} at {path} pos {r.pos}")


def copy_struct(r, out, path):
    last_field_id = 0
    while True:
        header = r.byte()
        if header == 0:
            out.append(0)
            return
        delta = (header >> 4) & 0x0F
        ctype = header & 0x0F
        if delta == 0:
            zz, _ = r.varint()
            field_id = zigzag_decode(zz)
            out.append(header)
            out += encode_varint(zigzag_encode(field_id))
        else:
            field_id = last_field_id + delta
            out.append(header)
        last_field_id = field_id
        copy_value(r, out, ctype, f"{path}.f{field_id}")


def fix_footer(footer_bytes):
    """Returns (new_footer_bytes, [(path, old_bytes, new_bytes), ...])."""
    FIXES.clear()
    r = Reader(footer_bytes)
    out = bytearray()
    copy_struct(r, out, "FileMetaData")
    assert r.pos == len(footer_bytes), f"did not consume whole footer: {r.pos}/{len(footer_bytes)}"
    return bytes(out), list(FIXES)


def fix_file(path: Path, apply: bool):
    data = path.read_bytes()
    assert data[-4:] == b"PAR1", f"{path} doesn't look like a parquet file"
    footer_len = struct.unpack("<I", data[-8:-4])[0]
    footer = data[-8 - footer_len:-8]
    data_pages = data[:-8 - footer_len]

    new_footer, fixes = fix_footer(footer)

    print(f"{path}: {len(fixes)} field(s) would be fixed")
    for p, old, new in fixes[:20]:
        print(f"  {p}: {old!r} -> {new.decode('utf-8')!r}")
    if len(fixes) > 20:
        print(f"  ... and {len(fixes) - 20} more")

    if not fixes:
        print("nothing to do")
        return

    if not apply:
        print("\ndry run only — pass --apply to write the fix (a .bak of the original is kept)")
        return

    backup = path.with_suffix(path.suffix + f".pre-utf8fix.bak")
    if not backup.exists():
        backup.write_bytes(data)
        print(f"backed up original to {backup}")
    else:
        print(f"backup already exists at {backup}, not overwriting it")

    new_file = data_pages + new_footer + struct.pack("<I", len(new_footer)) + b"PAR1"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(new_file)
    tmp.rename(path)  # atomic on same filesystem
    print(f"wrote fixed {path} ({len(new_file)} bytes, was {len(data)})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    fix_file(Path(sys.argv[1]), apply="--apply" in sys.argv[2:])
