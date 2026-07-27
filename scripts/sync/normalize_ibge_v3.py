#!/usr/bin/env python3
"""IBGE FTP normalization v3.

Fixes the problems found in the v2 pipeline (see tasks/normalization.plan):

1. Most source files have their real header shifted into row 0 of the data,
   because the original Excel export had a title row that pandas picked up
   as the column name. This makes ~86% of files look schema-incompatible
   when they are not. Phase A reconstructs the real header.
2. Geography (UF/municipio) is only correctly extracted for ~25% of files
   because it can be encoded in the filename prefix (SP__, 31_MINAS_GERAIS__),
   the filename suffix (UF 12, tab3_20), or the table title. Phase A checks
   all three and derives _uf/_municipio/_ano/_tabela_id/_titulo columns.
3. Grouping in v2 only stripped geography from the filename *suffix*, not
   the *prefix*, so 52.281 files only collapsed to 51.012 tables. Phase B's
   primary key is the table's own description with UF and year stripped out
   (`strip_year_and_uf`) — this merges the same survey question across both
   geography *and* census/PNAD editions, which a source-spreadsheet-number
   key never could (numbering gets rescoped release to release). Filename-
   based keys (`base_key_from_filename`) are only a fallback for files with
   no usable description.
4. `sorted(columns)` crashed on float column names (empty Excel header
   cells become NaN) and long titles produced filenames > 255 bytes.
   Both are fixed here (sort by str(), hash-truncate long names).

Pipeline:
    ~/ibge_ftp_parquet/<folder>/<file>.parquet         (raw, from Fase 2)
      -- Phase A (clean_file) -->
    ~/ibge_ftp_clean/<folder>/<file>.parquet           (1:1, headers fixed)
      -- Phase B (group_and_merge) -->
    ~/ibge_ftp_normalized_v3/<folder>/<table>.parquet  (merged across geography)
"""
import argparse
import hashlib
import logging
import re
import sys
import unicodedata
from collections import defaultdict
from multiprocessing import Pool
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

RAW_DIR = Path.home() / "ibge_ftp_parquet"
CLEAN_DIR = Path.home() / "ibge_ftp_clean"
OUT_DIR = Path.home() / "ibge_ftp_normalized_v3"
LOG_PATH = Path.home() / "ibge_ftp_normalize_v3.log"

META_COLS = ["_source_folder", "_original_file", "_download_date"]
NULL_TOKENS = {"", "-", "--", "...", "..", "x", "X", "*", "nan", "none", "na", "n/a", ".."}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_PATH, mode="a")],
)
log = logging.getLogger("normalize_v3")

STATE_CODES = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
    "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
    "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
    "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
    "52": "GO", "53": "DF",
}
SIGLAS = set(STATE_CODES.values())

UF_FULL_NAMES = {
    "rondonia": "RO", "acre": "AC", "amazonas": "AM", "roraima": "RR",
    "para": "PA", "amapa": "AP", "tocantins": "TO", "maranhao": "MA",
    "piaui": "PI", "ceara": "CE", "rio grande do norte": "RN",
    "paraiba": "PB", "pernambuco": "PE", "alagoas": "AL", "sergipe": "SE",
    "bahia": "BA", "minas gerais": "MG", "espirito santo": "ES",
    "rio de janeiro": "RJ", "sao paulo": "SP", "parana": "PR",
    "santa catarina": "SC", "rio grande do sul": "RS",
    "mato grosso do sul": "MS", "mato grosso": "MT", "goias": "GO",
    "distrito federal": "DF",
}
# longer names first so "rio grande do sul" doesn't get shadowed by a shorter partial match
UF_FULL_NAMES_SORTED = sorted(UF_FULL_NAMES.items(), key=lambda kv: -len(kv[0]))

REGIOES = {"norte", "nordeste", "sudeste", "sul", "centro oeste", "centro-oeste"}


def strip_accents(s):
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


def slugify(s, maxlen=None):
    s = strip_accents(str(s)).lower()
    s = re.sub(r"[^a-z0-9]+", "_", s).strip("_")
    s = re.sub(r"_+", "_", s)
    if not s:
        s = "col"
    if maxlen and len(s) > maxlen:
        h = hashlib.sha1(s.encode()).hexdigest()[:8]
        s = s[: maxlen - 9] + "_" + h
    return s


def dedupe_name(name, used):
    """Return a variant of `name` not already in `used`, and register it.

    Bumping a per-base-name counter isn't enough: a manually-suffixed name
    like "foo_1" can collide with another column whose *own* natural slug
    is already "foo_1" (e.g. pandas' own ".1" auto-dedup on a raw label
    slugifies to the same string as our "_1" suffix). Checking against the
    actual set of names already handed out avoids that collision.
    """
    if name not in used:
        used.add(name)
        return name
    i = 1
    while f"{name}_{i}" in used:
        i += 1
    final = f"{name}_{i}"
    used.add(final)
    return final


def safe_name(s, maxlen=140):
    """Filesystem/SQL-safe name, hash-truncated if the source string is too long."""
    return slugify(s, maxlen=maxlen)


# -- tab3_NN -> UF mapping is derived at runtime from the titles of
#    ufs__confronto_tab3_*.parquet files themselves (they carry the UF name
#    in row 0 of the shifted header), instead of being hardcoded.
_TAB3_UF_CACHE = {}


def build_tab3_uf_map(folder_path):
    mapping = {}
    for f in sorted(folder_path.glob("ufs__confronto_tab3_*.parquet")):
        m = re.search(r"tab3_(\d+)_", f.name)
        if not m:
            continue
        nn = m.group(1)
        if nn in mapping:
            continue
        try:
            df = pd.read_parquet(f)
        except Exception:
            continue
        other = [c for c in df.columns if c not in META_COLS]
        if not other:
            continue
        title = str(other[0])
        uf = find_uf_in_text(title)
        if uf:
            mapping[nn] = uf
    return mapping


def find_uf_in_text(text):
    if not isinstance(text, str):
        return None
    norm = strip_accents(text).lower()
    for name, sigla in UF_FULL_NAMES_SORTED:
        if name in norm:
            return sigla
    return None


TABELA_ID_RE = re.compile(r"(?i)^\s*tabela\s+([\d]+(?:\.[\d]+)*)")


def parse_title(title):
    """Extract _tabela_id, _titulo (description), _ano, _uf from a title string."""
    if not isinstance(title, str):
        return None, None, None, None
    m = TABELA_ID_RE.match(title)
    tabela_id = m.group(1) if m else None

    descricao = title
    if m:
        descricao = title[m.end():]
    descricao = re.sub(r"^\s*[-–]\s*", "", descricao)
    descricao = re.sub(r"\s+", " ", descricao).strip()

    years = re.findall(r"(?:19|20)\d{2}", title)
    ano = years[-1] if years else None

    uf = find_uf_in_text(title)

    return tabela_id, descricao or None, ano, uf


YEAR_OR_RANGE_RE = re.compile(r"\b(19|20)\d{2}(/(19|20)?\d{2,4})?\b")


def strip_year_and_uf(descricao):
    """Reduce a table description to its UF/year-independent semantic core,
    e.g. "Tratores existentes... - Rondônia - 2006" and "...- São Paulo -
    2017" both collapse to "tratores_existentes...". This is the real
    grouping signal — far more reliable than the source spreadsheet's own
    table numbering, which is rescoped (sometimes renumbered) release to
    release, so number-based keys can never merge the same survey question
    across census/PNAD editions the way this can.
    """
    t = strip_accents(descricao).lower()
    t = YEAR_OR_RANGE_RE.sub("", t)
    for name, _sigla in UF_FULL_NAMES_SORTED:
        t = re.sub(r"\b" + name.replace(" ", r"\s+") + r"\b", "", t)
    t = re.sub(r"[-–,]", " ", t)
    return slugify(t)


def is_title_shifted(col0, other_cols):
    if not isinstance(col0, str):
        return False
    if TABELA_ID_RE.match(col0):
        return True
    unnamed = sum(1 for c in other_cols[1:] if isinstance(c, str) and c.startswith("Unnamed"))
    if other_cols[1:] and unnamed / len(other_cols[1:]) > 0.5 and " - " in col0:
        return True
    return False


def _row_numeric_fraction(row):
    non_null = row.dropna()
    if len(non_null) == 0:
        return 0.0
    numeric = 0
    for v in non_null:
        if isinstance(v, (int, float)):
            numeric += 1
            continue
        try:
            float(str(v).strip().replace(" ", ""))
            numeric += 1
        except (ValueError, TypeError):
            pass
    return numeric / len(non_null)


def promote_header(df):
    """Reconstruct the real header for a title-shifted table.

    Returns (new_df, title) or (df, None) if no promotion was needed/possible.
    """
    meta_present = [c for c in META_COLS if c in df.columns]
    other_cols = [c for c in df.columns if c not in META_COLS]
    if not other_cols:
        return df, None

    col0 = other_cols[0]
    if not is_title_shifted(col0, other_cols):
        return df, None

    title = str(col0)
    sub = df[other_cols].reset_index(drop=True)

    max_scan = min(8, len(sub))
    data_start = max_scan
    for i in range(max_scan):
        frac = _row_numeric_fraction(sub.iloc[i])
        if frac >= 0.3:
            data_start = i
            break

    header_row_idx = [
        i for i in range(data_start) if sub.iloc[i].notna().sum() > 0
    ]

    if not header_row_idx:
        new_cols = [f"col_{i}" for i in range(len(other_cols))]
    else:
        filled_rows = []
        for i in header_row_idx:
            row = sub.iloc[i].ffill()
            filled_rows.append(row)
        new_cols = []
        used = set()
        for j in range(len(other_cols)):
            parts = []
            prev = None
            for row in filled_rows:
                v = row.iloc[j]
                if pd.isna(v):
                    continue
                v = re.sub(r"\s+", " ", str(v)).strip()
                if v and v != prev:
                    parts.append(v)
                    prev = v
            name = safe_name("_".join(parts), maxlen=60) if parts else f"col_{j}"
            new_cols.append(dedupe_name(name, used))

    data = sub.iloc[data_start:].reset_index(drop=True)
    data.columns = new_cols
    data = data.dropna(how="all")

    result = pd.concat(
        [df[meta_present].iloc[data_start:].reset_index(drop=True).loc[data.index], data],
        axis=1,
    )
    return result, title


def clean_null_tokens(series):
    """Blank Excel placeholders ('-', '...', 'X', ...) -> None. Safe to run
    per-file: it only ever turns a string into None, never changes a
    column's eventual type, so it can't create the cross-file type conflict
    that numeric coercion can (see coerce_numeric)."""
    if pd.api.types.is_numeric_dtype(series):
        return series
    return series.map(
        lambda v: None
        if (v is None or (isinstance(v, str) and v.strip().lower() in NULL_TOKENS))
        else v
    )


def coerce_numeric(series):
    """Only safe to call on a fully-merged column (post pd.concat across a
    whole table_key group), never per-file: different source files can each
    independently clear the 90% numeric threshold or not for "the same"
    column (e.g. a street-name column that happens to be mostly numbers in
    one municipality), and merging a coerced-float version of the column
    from one file with a left-as-string version from another produces a
    truly mixed-type column that pyarrow refuses to write.

    Vectorized (no per-cell Python calls): some merged groups run to
    millions of rows (e.g. the national CNEFE address table).
    """
    # Not `series.dtype != object`: pandas 3.x reads text columns as its
    # native "str" dtype, not the legacy numpy "object" — that check silently
    # skipped every column and left numbers stored as text.
    if pd.api.types.is_numeric_dtype(series):
        return series
    non_null = series.dropna()
    if len(non_null) == 0:
        return series

    s = series.astype("string")
    s = s.str.strip()
    s = s.str.replace(r"(?<=\d) (?=\d)", "", regex=True)  # thousand-separator space
    comma_decimal = s.str.count(",").eq(1) & ~s.str.contains(".", regex=False, na=False)
    s = s.mask(comma_decimal.fillna(False), s.str.replace(",", ".", regex=False))
    numeric = pd.to_numeric(s, errors="coerce")

    non_null_after = s.notna().sum()
    success = numeric.notna().sum()
    if non_null_after and success / non_null_after >= 0.9:
        return numeric
    return series


def extract_geo(filename, title, folder_name, tab3_uf_map):
    """Return (uf, municipio_code)."""
    name = filename.replace(".parquet", "")

    uf = find_uf_in_text(title) if title else None

    # 2-letter sigla prefix: "SP__...", "BA__..."
    if not uf:
        m = re.match(r"^([A-Za-z]{2})__", name)
        if m and m.group(1).upper() in SIGLAS:
            uf = m.group(1).upper()

    # "UF XX" pattern in filename
    if not uf:
        m = re.search(r"\bUF (\d{2})\b", name)
        if m:
            uf = STATE_CODES.get(m.group(1))

    # numeric-code + full-name prefix: "31_MINAS_GERAIS__..."
    if not uf:
        m = re.match(r"^(\d{2})_", name)
        if m:
            uf = STATE_CODES.get(m.group(1))

    # UF full name anywhere in filename
    if not uf:
        uf = find_uf_in_text(name.replace("_", " "))

    # tab3_NN encodes UF via a runtime-derived map
    if not uf:
        m = re.search(r"tab3_(\d+)_", name)
        if m:
            uf = tab3_uf_map.get(m.group(1))

    # 7-digit municipio code (first 2 digits must be a valid state code)
    municipio = None
    m = re.search(r"(?<!\d)(\d{7})(?!\d)", name)
    if m:
        code = m.group(1)
        if code[:2] in STATE_CODES:
            municipio = code
            if not uf:
                uf = STATE_CODES[code[:2]]

    return uf, municipio


def base_key_from_filename(filename, uf=None, municipio=None):
    """Grouping key from the filename: strip only the *specific* geography
    tokens already confirmed by extract_geo (the detected uf/municipio),
    never a blind digit-run regex — a stable non-geo sheet id (e.g. the
    "5614751" in "SP__5614751_tabela_1") must survive so files that share
    it (same source spreadsheet across every UF) end up in the same group,
    while a coincidentally-shaped id from an unrelated spreadsheet does not.
    """
    name = filename.replace(".parquet", "")
    parts = name.split("__", 1)
    prefix, tid = (parts[0], parts[1]) if len(parts) == 2 else (name, "")

    if uf and re.fullmatch(re.escape(uf), prefix, flags=re.I):
        prefix = ""
    elif uf and re.fullmatch(r"\d{2}_[A-Za-z_]+", prefix):
        prefix = ""
    prefix = re.sub(r"^ufs?$", "", prefix, flags=re.I)
    prefix = re.sub(r"^brasil(_xls)?$", "brasil", prefix, flags=re.I)

    tid = re.sub(r"\bUF \d+\b", "", tid)
    tid = re.sub(r"\bGR \d+\b", "", tid)
    tid = re.sub(r"\bBR\b", "", tid)
    if municipio:
        if re.fullmatch(re.escape(municipio) + r"_[A-Za-z_]+", tid):
            # "<code>_<municipality name>" and nothing else: pure geography,
            # the free-text place name isn't a table distinguisher either
            tid = ""
        else:
            tid = tid.replace(municipio, "")
    tid = re.sub(r"tab3_\d+_", "tab3_", tid)  # tab3_NN -> generic (UF already captured in _uf)

    combined = f"{prefix}_{tid}".strip("_")
    return slugify(combined) if combined.strip("_") else "sem_titulo"


def clean_one_file(args):
    folder_name, filepath_str, tab3_uf_map = args
    filepath = Path(filepath_str)
    try:
        df = pd.read_parquet(filepath)
    except Exception as e:
        return {"error": f"read error: {e}", "file": filepath.name}

    if df.empty:
        return {"error": "empty", "file": filepath.name}

    try:
        return _clean_one_file_inner(df, filepath, folder_name, tab3_uf_map)
    except Exception as e:
        import traceback
        return {"error": f"{type(e).__name__}: {e}\n{traceback.format_exc()}", "file": filepath.name}


def _clean_one_file_inner(df, filepath, folder_name, tab3_uf_map):
    df, title = promote_header(df)
    tabela_id, descricao, ano, title_uf = parse_title(title) if title else (None, None, None, None)
    uf, municipio = extract_geo(filepath.name, title, folder_name, tab3_uf_map)
    if not uf:
        uf = title_uf

    # Positional rename (not label-based .rename()): some source files have
    # genuine duplicate raw column labels, which would make df[c] return a
    # DataFrame instead of a Series under a dict-keyed rename.
    orig_cols = list(df.columns)
    new_cols = []
    used = set(META_COLS)
    for c in orig_cols:
        if c in META_COLS:
            new_cols.append(c)
            continue
        new_cols.append(dedupe_name(safe_name(c, maxlen=60), used))
    df.columns = new_cols
    data_cols = [c for c in new_cols if c not in META_COLS]

    for c in data_cols:
        df[c] = clean_null_tokens(df[c])

    df.insert(0, "_municipio", municipio)
    df.insert(0, "_uf", uf)
    if ano:
        df.insert(0, "_ano", ano)
    if descricao:
        df.insert(0, "_titulo", descricao)
    if tabela_id:
        df.insert(0, "_tabela_id", tabela_id)

    # Primary key: the description with UF/year stripped out. This is what
    # actually merges the same survey question across census/PNAD editions
    # (source spreadsheet numbering gets rescoped release to release, so it
    # can't do this). Only fall back to the old filename-based key when
    # there's no usable description (promote_header never triggered, e.g.
    # the CNEFE-style files that already had clean headers).
    title_key = strip_year_and_uf(descricao) if descricao else None
    loose_merge = bool(title_key)
    if title_key:
        table_key = safe_name(title_key, maxlen=100)
    elif tabela_id:
        prefix_key = base_key_from_filename(filepath.name, uf=uf, municipio=municipio)
        table_key = safe_name(f"{prefix_key}_tabela_{tabela_id}")
    else:
        table_key = safe_name(base_key_from_filename(filepath.name, uf=uf, municipio=municipio))

    df.insert(0, "_table_key", table_key)

    out_dir = CLEAN_DIR / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    # short hash of the *original* filename guarantees uniqueness even when
    # two distinct raw names collapse to the same slug after truncation
    name_hash = hashlib.sha1(filepath.name.encode()).hexdigest()[:6]
    out_name = f"{safe_name(filepath.stem, maxlen=100)}_{name_hash}.parquet"
    out_path = out_dir / out_name
    try:
        table = pa.Table.from_pandas(df, preserve_index=False)
        pq.write_table(table, out_path, compression="zstd")
    except Exception as e:
        return {"error": f"write error: {e}", "file": filepath.name}

    cols_sig = tuple(sorted((c for c in df.columns if c not in META_COLS and not c.startswith("_")), key=str))

    return {
        "folder": folder_name,
        "clean_path": str(out_path),
        "table_key": table_key,
        "cols_sig": cols_sig,
        "n_rows": len(df),
        "loose_merge": loose_merge,
    }


def phase_a(folder_filter=None, limit=None, workers=8):
    folders = sorted(
        d for d in RAW_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")
    )
    if folder_filter:
        folders = [d for d in folders if d.name == folder_filter]
        if not folders:
            log.error(f"folder not found: {folder_filter}")
            return []

    manifest = []
    for folder in folders:
        files = sorted(folder.glob("*.parquet"))
        if limit:
            files = files[:limit]
        log.info(f"[phase A] {folder.name}: {len(files)} files")

        tab3_uf_map = build_tab3_uf_map(folder)
        args = [(folder.name, str(f), tab3_uf_map) for f in files]

        n_ok = 0
        n_err = 0
        with Pool(workers) as pool:
            for res in pool.imap_unordered(clean_one_file, args, chunksize=32):
                if "error" in res:
                    n_err += 1
                    log.warning(f"  skip {res['file']}: {res['error']}")
                else:
                    n_ok += 1
                    manifest.append(res)
        log.info(f"[phase A] {folder.name}: {n_ok} ok, {n_err} errors")

    return manifest


def merge_group(folder_name, table_key, items):
    out_dir = OUT_DIR / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{table_key}.parquet"

    frames = []
    for path, _sig, _n in items:
        try:
            frames.append(pd.read_parquet(path))
        except Exception as e:
            log.warning(f"  merge read error {path}: {e}")

    if not frames:
        return 0, 0

    # reindex adds every missing column in one vectorized shot; doing it via
    # `f[c] = None` per-column instead (the previous approach) triggers
    # pandas' "highly fragmented DataFrame" internal reallocation once per
    # missing column, which turned title-based groups (loose union merges
    # across many more files/columns than the old strict-overlap groups)
    # into a multi-minute operation.
    all_cols = sorted({c for f in frames for c in f.columns}, key=str)
    aligned = [f.reindex(columns=all_cols) for f in frames]

    merged = pd.concat(aligned, ignore_index=True)
    merged = merged.dropna(how="all")
    if merged.empty:
        return 0, 0

    # IBGE sometimes republishes the exact same table under a different
    # sheet id (two different source files, identical title, identical
    # data) — e.g. SP/2017 "Condição legal do produtor..." appears under
    # both 5615458_TABELA_1.xls and 5616460_TABELA_1.xls. Since the
    # title-based key merges by content, not by sheet id, that duplication
    # would otherwise double every value. Drop exact content duplicates,
    # ignoring only the two provenance columns that are expected to differ.
    dedup_cols = [c for c in merged.columns if c not in ("_original_file", "_download_date")]
    before = len(merged)
    merged = merged.drop_duplicates(subset=dedup_cols, keep="first")
    if len(merged) < before:
        log.info(f"  dedup {table_key}: {before} -> {len(merged)} rows")

    data_cols = [c for c in merged.columns if c not in META_COLS and not c.startswith("_")]
    for c in data_cols:
        merged[c] = coerce_numeric(merged[c])

    try:
        table = pa.Table.from_pandas(merged, preserve_index=False)
        pq.write_table(table, out_path, compression="zstd")
    except Exception as e:
        log.warning(f"  merge write error {table_key}: {e}")
        return 0, 0

    return len(items), len(merged)


def jaccard(a, b):
    if not a or not b:
        return 0.0
    a, b = set(a), set(b)
    return len(a & b) / len(a | b)


def cluster_by_column_overlap(items, threshold=0.5):
    """Greedy single-linkage clustering: same table_key but slightly different
    column sets (extra/missing footnote column, stray blank column) still
    merge; genuinely different schemas split into separate clusters."""
    clusters = []  # list of {"ref": set(cols), "items": [...]}
    for path, cols_sig, n_rows in items:
        cols = set(cols_sig)
        best = None
        best_score = threshold
        for cl in clusters:
            score = jaccard(cols, cl["ref"])
            if score >= best_score:
                best = cl
                best_score = score
        if best is None:
            clusters.append({"ref": cols, "items": [(path, cols_sig, n_rows)]})
        else:
            best["items"].append((path, cols_sig, n_rows))
            best["ref"] = best["ref"] | cols
    return [cl["items"] for cl in clusters]


def phase_b(manifest):
    by_folder = defaultdict(lambda: defaultdict(list))
    for rec in manifest:
        by_folder[rec["folder"]][rec["table_key"]].append(
            (rec["clean_path"], rec["cols_sig"], rec["n_rows"])
        )

    total_tables = 0
    total_rows = 0
    for folder_name, groups in by_folder.items():
        n_tables = 0
        n_rows = 0
        for table_key, items in sorted(groups.items()):
            # Tried unconditional union merge for title-based keys (skip the
            # overlap check entirely) — wrong: IBGE sometimes gives two
            # genuinely different tables (different variable sets) the
            # *exact same* title text (e.g. "Condição legal do produtor..."
            # covers both a legal-condition breakdown and an unrelated
            # cooperative-association breakdown across two source sheets
            # that only share ~33-36% of columns). Unconditional merge
            # silently combined them, corrupting sums. The 0.5 threshold
            # correctly keeps that case split while still merging the same
            # table across UF/year when columns are substantially the same.
            clusters = cluster_by_column_overlap(items, threshold=0.5)
            for i, cluster_items in enumerate(clusters):
                key = table_key if i == 0 else f"{table_key}_v{i + 1}"
                n_files, n_merged = merge_group(folder_name, key, cluster_items)
                if n_files:
                    n_tables += 1
                    n_rows += n_merged
        log.info(f"[phase B] {folder_name}: {n_tables} tables, {n_rows} rows")
        total_tables += n_tables
        total_rows += n_rows

    log.info(f"=== DONE: {total_tables} tables, {total_rows} total rows ===")
    return total_tables, total_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", help="process a single folder (pilot mode)")
    ap.add_argument("--limit", type=int, help="cap files per folder (pilot mode)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--skip-a", action="store_true", help="skip Phase A, reuse ~/ibge_ftp_clean")
    args = ap.parse_args()

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.skip_a:
        manifest = rebuild_manifest_from_clean(args.folder)
    else:
        manifest = phase_a(folder_filter=args.folder, limit=args.limit, workers=args.workers)

    phase_b(manifest)


def rebuild_manifest_from_clean(folder_filter=None):
    folders = sorted(d for d in CLEAN_DIR.iterdir() if d.is_dir())
    if folder_filter:
        folders = [d for d in folders if d.name == folder_filter]
    manifest = []
    for folder in folders:
        for f in sorted(folder.glob("*.parquet")):
            try:
                schema = pq.read_schema(f)
            except Exception:
                continue
            cols = schema.names
            if "_table_key" not in cols:
                continue
            try:
                tk = pd.read_parquet(f, columns=["_table_key"])["_table_key"].dropna()
                table_key = tk.iloc[0] if len(tk) else None
            except Exception:
                table_key = None
            if not table_key:
                continue
            cols_sig = tuple(sorted((c for c in cols if c not in META_COLS and not c.startswith("_")), key=str))
            manifest.append({
                "folder": folder.name,
                "clean_path": str(f),
                "table_key": table_key,
                "cols_sig": cols_sig,
                "n_rows": pq.read_metadata(f).num_rows,
                "loose_merge": "_titulo" in cols,
            })
    return manifest


if __name__ == "__main__":
    main()
