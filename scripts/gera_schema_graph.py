#!/usr/bin/env python3
"""Build `docs/context/schema_graph.json` — the data behind the schema map.

    python3 scripts/gera_schemas.py       # beelink   -> schemas.json
    python3 scripts/build_metadata_catalog.py         # -> catalog.parquet
    python3 scripts/gera_schema_graph.py  # both      -> pages/atlas/schema_graph.json
    python3 scripts/build_atlas.py        # graph+page -> pages/atlas/index.html

The mirror has no foreign keys — it is parquet. What connects it is columns
that mean the same thing in more than one table, which `gera_join_keys.py`
already works out (curated hub keys, auto-detected shared identifiers, and the
bridges for sources that spell a key differently). This script reuses that
selection and emits it as a graph instead of a document.

The graph is bipartite on purpose: table -> key, never table -> table. Joining
every pair of tables that share a key is 89.598 edges and reads as a hairball;
routing through the key is 1.108 and says which key does the joining.

Everything is index-based (`ds`, `k` are offsets into `datasets` / `keys`) so
the file stays small enough to inline into a single self-contained page.
"""

import json
import math
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from gera_join_keys import (  # noqa: E402
    AUTO_DENY,
    CONCEPT_ALIASES,
    CURATED,
    KEYISH,
    MIN_DATASETS,
    TYPE_MAP,
    index_columns,
)
from gera_erd import DOMAIN_NAMES, TEMPORAL, domain_of  # noqa: E402

SCHEMAS = REPO_ROOT / "schemas.json"
CATALOG = REPO_ROOT / "_rodado_metadata" / "catalog.parquet"
# The graph is viz data, not LLM context — it lives beside the page that
# serves it, so there is exactly one copy of a 630 KB file in the repo.
OUTPUT = REPO_ROOT / "pages" / "atlas" / "schema_graph.json"

# Columns kept per table. The key columns are always emitted; this caps the
# rest, because br_mjsp_sisdepen.populacao_carceraria alone has 3.957 of them
# and no card is ever going to show that many.
MAX_COLS = 60

# Which hub a key belongs to. CURATED carries `cat` for its own columns; the
# auto-detected long tail is mostly a hub key wearing a role suffix, so resolve
# it by prefix the same way gera_join_keys.auto_desc() describes it.
PREFIX_CAT = [
    ("id_municipio", "municipio"), ("nome_municipio", "municipio"),
    ("id_uf", "uf"), ("sigla_uf", "uf"), ("nome_uf", "uf"),
    ("cnpj", "empresa"), ("cpf_cnpj", "empresa"), ("razao_social", "empresa"),
    ("cpf", "pessoa"), ("nome_", "pessoa"),
    ("cnae", "classificacao"), ("cid_", "classificacao"), ("cbo", "classificacao"),
    ("id_escola", "educacao"), ("id_curso", "educacao"), ("id_aluno", "educacao"),
    ("id_estabelecimento_cnes", "saude"), ("id_profissional", "saude"),
    ("id_orgao", "governo"), ("id_unidade_gestora", "governo"),
    ("id_candidato", "politica"), ("id_deputado", "politica"),
    ("id_setor_censitario", "geo"), ("id_distrito", "geo"), ("cep", "geo"),
    ("id_regiao", "geo"), ("id_mesorregiao", "geo"), ("id_microrregiao", "geo"),
]

CAT_NAMES = {
    "municipio": "Município", "uf": "UF", "geo": "Outra geografia",
    "tempo": "Tempo", "empresa": "Empresa (CNPJ)", "pessoa": "Pessoa (CPF)",
    "educacao": "Educação", "saude": "Saúde", "governo": "Governo",
    "politica": "Política", "classificacao": "Classificação",
    "outros": "Outras colunas compartilhadas",
}


def cat_of(col: str) -> str:
    if col in CURATED:
        return CURATED[col].get("cat", "outros")
    if col in TEMPORAL or col.startswith(("ano_", "mes_", "data_")):
        return "tempo"
    for prefix, cat in PREFIX_CAT:
        if col.startswith(prefix):
            return cat
    return "outros"


def load_row_counts() -> dict[str, dict]:
    """dataset.table -> {rows, size_bytes, source_name, status} from the catalog."""
    try:
        import pyarrow.parquet as pq
    except ImportError:
        print("! pyarrow missing — graph will carry no row counts", file=sys.stderr)
        return {}
    if not CATALOG.exists():
        print(f"! {CATALOG} missing — run build_metadata_catalog.py", file=sys.stderr)
        return {}
    t = pq.read_table(CATALOG).to_pydict()
    return {
        f"{d}.{tb}": {"rows": r, "bytes": b, "src": sn, "status": st}
        for d, tb, r, b, sn, st in zip(
            t["dataset"], t["table"], t["rows"], t["size_bytes"],
            t["source_name"], t["status"],
        )
    }


def select_keys(idx) -> list[str]:
    """The same set gera_join_keys.py documents: curated hubs + auto-detected."""
    curated = {c for c in CURATED if c in idx}
    auto = {
        c for c, i in idx.items()
        if c not in curated
        and len(i["datasets"]) >= MIN_DATASETS
        and KEYISH.match(c)
        and c not in AUTO_DENY
        and not re.fullmatch(r"v\d{3}", c)
    }
    return sorted(curated | auto)


def build():
    schema = json.loads(SCHEMAS.read_text())
    tables = schema["tables"]
    catalog = load_row_counts()
    idx = index_columns(tables)

    key_names = select_keys(idx)
    key_pos = {c: i for i, c in enumerate(key_names)}
    key_set = set(key_names)

    # ---- datasets -------------------------------------------------------
    ds_names = sorted({tid.split(".", 1)[0] for tid in tables})
    ds_pos = {d: i for i, d in enumerate(ds_names)}
    ds_rows = Counter()
    ds_tables = Counter()

    # ---- tables ---------------------------------------------------------
    out_tables = []
    key_tables = defaultdict(list)   # key index -> table indices
    key_datasets = defaultdict(set)

    for tid in sorted(tables):
        dataset, name = tid.split(".", 1)
        meta = tables[tid]
        cols = meta.get("columns", [])
        cat = catalog.get(tid, {})
        rows = cat.get("rows", 0) or 0

        ti = len(out_tables)
        my_keys = []
        seen = set()
        # O grafo liga por NOME de coluna, então um hub que renomeia a coluna sai do
        # mapa mesmo continuando a ligar. `concept_aliases` diz qual conceito a coluna
        # local representa — sem isso `br_bd_diretorios_mundo.pais` fica órfã depois do
        # rename de 2026-08-23 (sigla_pais_iso3 -> sigla_iso3), e o mesmo vale para
        # `br_bd_diretorios_brasil.uf.sigla`.
        alias_da_tabela = CONCEPT_ALIASES.get(tid, {})
        locais = set()          # nomes como estão NA tabela, para ordenar as colunas
        for col in cols:
            low = col["name"].lower()
            conceito = alias_da_tabela.get(col["name"], alias_da_tabela.get(low, low))
            if conceito in key_set and conceito not in seen:
                seen.add(conceito)
                locais.add(low)
                ki = key_pos[conceito]
                my_keys.append(ki)
                key_tables[ki].append(ti)
                key_datasets[ki].add(dataset)

        # key columns first, then the rest up to the cap
        ordered = [c for c in cols if c["name"].lower() in locais]
        rest = [c for c in cols if c["name"].lower() not in locais]
        shown = ordered + rest[: max(0, MAX_COLS - len(ordered))]

        out_tables.append({
            "n": name,
            "ds": ds_pos[dataset],
            "r": rows,
            "b": cat.get("bytes", 0) or 0,
            "nc": len(cols),
            "k": sorted(my_keys),
            "c": [[c["name"], TYPE_MAP.get(c.get("type", ""), c.get("type", "?"))]
                  for c in shown],
        })
        ds_rows[dataset] += rows
        ds_tables[dataset] += 1

    # ---- keys -----------------------------------------------------------
    out_keys = []
    for i, col in enumerate(key_names):
        info = idx[col]
        cur = CURATED.get(col, {})
        types = info["types"].most_common(2)
        entry = {
            "n": info["spellings"].most_common(1)[0][0],
            "cat": cat_of(col),
            "t": len(key_tables[i]),
            "d": len(key_datasets[i]),
            "ty": [t for t, _ in types],
            "sp": [s for s, _ in info["spellings"].most_common(4)],
        }
        if cur:
            # the curated paragraph is what makes a key node worth clicking;
            # strip the markdown backticks since it renders as plain text
            entry["desc"] = re.sub(r"`([^`]*)`", r"\1", cur["desc"])
            if cur.get("ref"):
                entry["ref"] = cur["ref"]
        out_keys.append(entry)

    # The zoomed-out map is 197 identical white cards unless each one carries
    # something. Its most specific key — the one reaching fewest tables — says
    # more about what a dataset is than its widest one ever could.
    GROUP_OF = {
        "empresa": "id", "pessoa": "id",
        "municipio": "geo", "uf": "geo", "geo": "geo",
        "saude": "dom", "educacao": "dom", "governo": "dom",
        "politica": "dom", "classificacao": "dom",
        "tempo": "axis", "outros": "axis",
    }
    ds_key_sets = defaultdict(set)
    for t in out_tables:
        ds_key_sets[t["ds"]].update(t["k"])

    out_datasets = []
    for di, d in enumerate(ds_names):
        keys_here = ds_key_sets.get(di, set())
        grp = ""
        if keys_here:
            best = min(keys_here, key=lambda ki: (out_keys[ki]["t"], ki))
            grp = GROUP_OF.get(out_keys[best]["cat"], "axis")
        out_datasets.append({
            "n": d,
            "dom": domain_of(d),
            "t": ds_tables[d],
            "r": ds_rows[d],
            "g": grp,
            "nk": len(keys_here),
        })

    edges = sum(len(t["k"]) for t in out_tables)
    graph = {
        "meta": {
            "generated": date.today().isoformat(),
            "tables": len(out_tables),
            "datasets": len(out_datasets),
            "keys": len(out_keys),
            "edges": edges,
            "rows": sum(t["r"] for t in out_tables),
            "source": "schemas.json + _rodado_metadata/catalog.parquet",
        },
        "domains": {k: v["pt"] for k, v in DOMAIN_NAMES.items()},
        "cats": CAT_NAMES,
        "datasets": out_datasets,
        "keys": out_keys,
        "tables": out_tables,
    }

    print("  layout: grade…", file=sys.stderr)
    grade = layout(out_datasets, out_keys, out_tables)
    print("  layout: temas…", file=sys.stderr)
    thm = layout_theme(out_datasets, out_keys, out_tables)
    graph["layout"] = {
        "cell": [CELL_W, CELL_H, PAD, HEADER],
        "grade": grade,
        "temas": thm,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(graph, ensure_ascii=False, separators=(",", ":")))
    size = OUTPUT.stat().st_size / 1024
    print(f"{OUTPUT.relative_to(REPO_ROOT)} — {len(out_tables)} tabelas, "
          f"{len(out_datasets)} datasets, {len(out_keys)} chaves, "
          f"{edges} arestas ({size:.0f} KB)")

    unconnected = [t for t in out_tables if not t["k"]]
    print(f"  {len(unconnected)} tabelas sem nenhuma chave de join")
    top = sorted(out_keys, key=lambda k: -k["t"])[:8]
    print("  maiores chaves: " + ", ".join(f"{k['n']}({k['t']})" for k in top))


# ---------------------------------------------------------------------------
# Layout — computed here so the page ships coordinates and renders instantly
# ---------------------------------------------------------------------------

# A dataset card holds its tables in a grid; the card is the unit the layout
# packs, and tables/columns are drawn inside it as the viewer zooms in.
CELL_W, CELL_H, PAD, HEADER = 118.0, 26.0, 10.0, 30.0


def card_cols(n_tables: int) -> int:
    """Aim for a square card. A cell is 118x26, so a naive sqrt grid produces
    cards nearly 4:1 wide — and wide flat rectangles pack terribly, which is
    what blew the world up to 6370x6740 and the fit zoom down to 13%."""
    return max(1, math.ceil(math.sqrt(n_tables * CELL_H / CELL_W)))


def card_size(n_tables: int) -> tuple[float, float]:
    cols = card_cols(n_tables)
    rows = math.ceil(n_tables / cols)
    return (cols * CELL_W + 2 * PAD, HEADER + rows * CELL_H + PAD)


def layout(datasets, keys, tables):
    """Force-directed placement of dataset cards around key hubs, then a
    separation pass so no two cards overlap.

    Datasets are attracted to the keys their tables use, weighted by 1/uses —
    `ano` touches 389 tables, so letting it pull as hard as `id_escola` would
    collapse everything onto one point."""
    import numpy as np

    rng = np.random.default_rng(7)
    nd, nk = len(datasets), len(keys)
    n = nd + nk

    sizes = np.zeros((n, 2))
    for i, d in enumerate(datasets):
        sizes[i] = card_size(d["t"])
    for j, k in enumerate(keys):
        w = 90 + 5.5 * len(k["n"])
        sizes[nd + j] = (w, 34.0)

    # dataset -> key adjacency, weighted by how specific the key is
    src, dst, wgt = [], [], []
    seen = set()
    for t in tables:
        for ki in t["k"]:
            pair = (t["ds"], ki)
            if pair in seen:
                continue
            seen.add(pair)
            src.append(t["ds"])
            dst.append(nd + ki)
            wgt.append(1.0 / math.sqrt(keys[ki]["t"]))
    src = np.array(src, dtype=int)
    dst = np.array(dst, dtype=int)
    wgt = np.array(wgt)

    # Datasets with no key at all only feel the origin pull, so the simulation
    # flings them into the void and the fit-to-screen zoom collapses to 13%.
    # Park them in a strip of their own once the rest has settled.
    connected = np.array([i for i, d in enumerate(datasets) if d["nk"]], dtype=int)
    isolated = np.array([i for i, d in enumerate(datasets) if not d["nk"]], dtype=int)
    live = np.concatenate([connected, np.arange(nd, n)])

    # seed keys on a ring by category, universal axes in the middle
    cat_order = ["tempo", "municipio", "uf", "geo", "empresa", "pessoa",
                 "saude", "educacao", "governo", "politica", "classificacao",
                 "outros"]
    inner = {"tempo", "municipio", "uf", "geo"}
    pos = rng.normal(0, 400, (n, 2))
    for j, k in enumerate(keys):
        c = k["cat"] if k["cat"] in cat_order else "outros"
        a = 2 * math.pi * cat_order.index(c) / len(cat_order)
        r = 300 if c in inner else 1900
        pos[nd + j] = (r * math.cos(a) + rng.normal(0, 220),
                       r * math.sin(a) + rng.normal(0, 220))

    area = float(np.sum(sizes[:, 0] * sizes[:, 1]))
    k_rep = math.sqrt(area / n) * 1.15

    for step in range(600):
        t_cool = 1.0 - step / 600
        sub = pos[live]
        disp = np.zeros((len(live), 2))

        # repulsion, O(n^2) but n is ~330
        delta = sub[:, None, :] - sub[None, :, :]
        dist2 = np.sum(delta ** 2, axis=-1) + 1e-6
        np.fill_diagonal(dist2, np.inf)
        disp += np.sum(delta * ((k_rep ** 2) / dist2)[..., None], axis=1)

        # attraction along dataset->key edges
        d = pos[src] - pos[dst]
        dist = np.sqrt(np.sum(d ** 2, axis=-1)) + 1e-6
        pull = (d / dist[:, None]) * (dist * wgt * 0.9)[:, None]
        edge_disp = np.zeros((n, 2))
        np.add.at(edge_disp, src, -pull)
        np.add.at(edge_disp, dst, pull)
        disp += edge_disp[live]

        # gentle pull to origin so islands do not drift off
        disp -= sub * 0.012

        norm = np.sqrt(np.sum(disp ** 2, axis=-1))[:, None] + 1e-9
        pos[live] = sub + (disp / norm) * np.minimum(norm, 90.0 * t_cool + 6.0)

    # The simulation only cares about relative placement, so squeeze the whole
    # thing down to a sane density before separating — otherwise the repulsion
    # equilibrium leaves a world 500x emptier than the cards need.
    # Squeeze to a 4:3 frame sized just above the total card area. The old
    # multiplier of 4.0 produced a 6370x6740 world, which fit-to-screen renders
    # at 13% — every dataset name below its legibility threshold.
    sub = pos[live]
    sub -= sub.mean(axis=0)
    span = np.maximum(sub.max(axis=0) - sub.min(axis=0), 1.0)
    live_area = float(np.sum(sizes[live, 0] * sizes[live, 1]))
    tw = math.sqrt(live_area * 2.1 * 4 / 3)
    sub *= np.array([tw / span[0], (tw * 3 / 4) / span[1]])
    pos[live] = sub

    # 10px of breathing room between cards; the pass below treats this as a
    # hard constraint, so keep it modest or the world inflates to satisfy it.
    half = sizes / 2 + 10.0
    order = live[np.argsort(-(sizes[live, 0] * sizes[live, 1]))]
    rank = {int(v): r for r, v in enumerate(order)}

    def overlaps():
        sub2 = pos[live]
        h = half[live]
        delta = sub2[:, None, :] - sub2[None, :, :]
        over = (h[:, None, :] + h[None, :, :]) - np.abs(delta)
        np.fill_diagonal(over[:, :, 0], -1)
        np.fill_diagonal(over[:, :, 1], -1)
        return delta, over, (over[:, :, 0] > 0) & (over[:, :, 1] > 0)

    # Separation only ever pushes apart, so on its own it preserves whatever
    # slack the force pass left — 20% occupancy, a 16% fit zoom, no readable
    # label anywhere. Over-compress instead and let separation expand back to
    # its own limit, which is the densest packing these positions allow.
    # Anisotropic on purpose: separation drifts the frame taller every cycle,
    # so start wider than 4:3 to land near it on a landscape screen.
    c = pos[live].mean(axis=0)
    pos[live] = c + (pos[live] - c) * np.array([0.62, 0.34])

    for cycle in range(30):
        for it in range(400):
            delta, over, hit = overlaps()
            if not hit.any():
                break
            # Bias toward resolving horizontally: unbiased, the pass drifts the
            # frame to a 0.63 aspect, and on a landscape screen the fit zoom is
            # then bounded by a height nobody has.
            use_x = over[:, :, 0] < over[:, :, 1] * 1.35
            amount = np.where(use_x, over[:, :, 0], over[:, :, 1]) * 0.5
            sign_x = np.where(delta[:, :, 0] >= 0, 1.0, -1.0)
            sign_y = np.where(delta[:, :, 1] >= 0, 1.0, -1.0)
            push = np.zeros((len(live), 2))
            push[:, 0] = np.sum(np.where(hit & use_x, amount * sign_x, 0.0), axis=1)
            push[:, 1] = np.sum(np.where(hit & ~use_x, amount * sign_y, 0.0), axis=1)
            pos[live] += np.clip(push * (0.55 if it < 250 else 0.3), -60, 60)

        delta, over, hit = overlaps()
        ii, jj = np.nonzero(hit)
        stuck = [(int(live[i]), int(live[j])) for i, j in zip(ii, jj) if i < j]
        if not stuck:
            break
        # a handful of pairs always deadlock; free them one at a time, moving
        # the smaller card so the big datasets keep their placement
        li = {int(v): q for q, v in enumerate(live)}
        for i, j in stuck:
            mover = i if rank[i] > rank[j] else j
            other = j if mover == i else i
            oi, oj = li[i], li[j]
            a = 0 if over[oi, oj, 0] < over[oi, oj, 1] else 1
            sign = 1.0 if pos[mover, a] >= pos[other, a] else -1.0
            pos[mover, a] += sign * (float(over[oi, oj, a]) + 1.0)

    # Pack the unconnected datasets into a tidy strip under the main body,
    # labelled in the UI as what they are: tables nothing else joins.
    if len(isolated):
        lo = pos[live].min(axis=0) - half[live].max(axis=0)
        hi = pos[live].max(axis=0) + half[live].max(axis=0)
        width = hi[0] - lo[0]
        cx, cy = lo[0], hi[1] + 150.0
        row_h = 0.0
        for i in isolated:
            w, h = sizes[i]
            if cx > lo[0] and cx + w > lo[0] + width:
                cx = lo[0]
                cy += row_h + 26.0
                row_h = 0.0
            pos[i] = (cx + w / 2, cy + h / 2)
            cx += w + 26.0
            row_h = max(row_h, h)

    # report real box overlaps, not the margin the pass aims for
    delta = pos[:, None, :] - pos[None, :, :]
    raw = (sizes[:, None, :] / 2 + sizes[None, :, :] / 2) - np.abs(delta)
    np.fill_diagonal(raw[:, :, 0], -1)
    np.fill_diagonal(raw[:, :, 1], -1)
    left = int(np.count_nonzero((raw[:, :, 0] > 0) & (raw[:, :, 1] > 0)) // 2)
    if left:
        print(f"  ! {left} cartoes ainda se sobrepoem", file=sys.stderr)

    pos -= pos.min(axis=0) - 60
    world = pos.max(axis=0) + sizes.max(axis=0) + 60

    return {
        "world": [round(float(world[0]), 1), round(float(world[1]), 1)],
        # cols travels with the card: deriving it again in the renderer once
        # let the two formulas diverge, and every table name spilled outside
        # its own card onto the neighbours.
        "ds": [[round(float(pos[i, 0]), 1), round(float(pos[i, 1]), 1),
                round(float(sizes[i, 0]), 1), round(float(sizes[i, 1]), 1),
                card_cols(datasets[i]["t"])]
               for i in range(nd)],
        "keys": [[round(float(pos[nd + j, 0]), 1), round(float(pos[nd + j, 1]), 1),
                  round(float(sizes[nd + j, 0]), 1)] for j in range(nk)],
    }


# ---------------------------------------------------------------------------
# Table-level layout — the unit is the table, not the dataset card
# ---------------------------------------------------------------------------
# The packed layout reads well but flattens affinity: a card sits where it fits,
# not where it belongs. This one puts the 833 tables in the field themselves.

def table_radius(rows: int) -> float:
    """Log scale — row counts span 0 to 6,6 bilhões, so a linear radius would
    render everything but a handful of tables as a dot."""
    return 3.2 + 1.35 * math.log10(max(rows, 1))


def key_radius(reach: int) -> float:
    return 9.0 + 3.4 * math.sqrt(reach)


def layout_theme(datasets, keys, tables):
    """One territory per theme, keys floating between the themes they bridge.

    Ten themes cannot each hold a free-floating hue — past four, colours stop
    being separable for pairs that land next to each other (the all-pairs gate
    fails at five). Clustering makes the theme a *place*, so position and a
    per-cluster label carry identity and colour only reinforces it."""
    import numpy as np

    nt, nk = len(tables), len(keys)
    rad = np.array([table_radius(t["r"]) for t in tables]
                   + [key_radius(k["t"]) for k in keys])
    pos = np.zeros((nt + nk, 2))

    theme_of = [datasets[t["ds"]]["dom"] for t in tables]
    members = {}
    for ti, th in enumerate(theme_of):
        members.setdefault(th, []).append(ti)

    # biggest territory first, spiralling out — keeps the dense themes central
    order = sorted(members, key=lambda th: -len(members[th]))
    centres, placed = {}, []
    for idx, th in enumerate(order):
        own = members[th]
        area = sum(math.pi * (rad[ti] + 4) ** 2 for ti in own)
        rr = math.sqrt(area / math.pi) * 1.5
        # nudge outward until this disc clears the ones already down
        step, ang = 0, idx * 2.399963
        while True:
            d = 0.0 if idx == 0 else (260 + step * 26)
            cx, cy = d * math.cos(ang), d * math.sin(ang)
            if all(math.hypot(cx - x, cy - y) > rr + r2 + 70 for x, y, r2 in placed):
                break
            step += 1
            if step > 400:
                break
        centres[th] = (cx, cy, rr)
        placed.append((cx, cy, rr))
        for m, ti in enumerate(sorted(own, key=lambda i: -tables[i]["r"])):
            a = m * 2.399963
            r = rr * math.sqrt((m + 0.5) / len(own))
            pos[ti] = (cx + r * math.cos(a), cy + r * math.sin(a))

    # a key belongs to no theme — park it at the centroid of what it joins, so
    # it sits between the territories it actually bridges
    for ki in range(nk):
        own = [ti for ti, t in enumerate(tables) if ki in t["k"]]
        if own:
            pos[nt + ki] = np.mean(pos[own], axis=0)
        else:
            pos[nt + ki] = (0.0, 0.0)

    # keys that join tables in one spot land on top of each other
    jitter = np.array([[math.cos(i * 2.399963), math.sin(i * 2.399963)]
                       for i in range(len(pos))]) * 0.4
    pos += jitter
    _separate_circles(pos, rad, rounds=420)
    out = _finish(pos, rad, nt, nk, keys)
    dx = out["_dx"]; dy = out["_dy"]
    out["themes"] = {th: [round(centres[th][0] + dx, 1),
                          round(centres[th][1] + dy, 1),
                          round(centres[th][2], 1)] for th in centres}
    del out["_dx"], out["_dy"]
    return out


def _separate_circles(pos, rad, rounds=340):
    """Push overlapping discs apart. Circles make this far cheaper than the
    rectangle case — one distance test, one direction."""
    import numpy as np

    gap = rad + 3.0
    need = gap[:, None] + gap[None, :]
    for _ in range(rounds):
        delta = pos[:, None, :] - pos[None, :, :]
        dist = np.sqrt(np.sum(delta ** 2, axis=-1))
        np.fill_diagonal(dist, 1e9)          # not inf: inf*0 is nan downstream
        over = need - dist
        hit = over > 0
        if not hit.any():
            break
        # Two bodies at exactly the same point give 0/0 — one NaN here spreads
        # to every position in the field within a single pass.
        unit = delta / np.maximum(dist, 1e-6)[..., None]
        push = np.sum(np.where(hit[..., None], unit * (over * 0.5)[..., None], 0.0), axis=1)
        pos += np.clip(push * 0.55, -40, 40)


def _finish(pos, rad, nt, nk, keys):
    import numpy as np

    shift = -(pos.min(axis=0) - rad.max() - 40)
    pos += shift
    world = pos.max(axis=0) + rad.max() + 40
    r1 = lambda v: round(float(v), 1)
    return {
        "_dx": float(shift[0]), "_dy": float(shift[1]),
        "world": [r1(world[0]), r1(world[1])],
        "tb": [[r1(pos[i, 0]), r1(pos[i, 1]), r1(rad[i])] for i in range(nt)],
        "keys": [[r1(pos[nt + j, 0]), r1(pos[nt + j, 1]),
                  r1(key_radius(keys[j]["t"]))] for j in range(nk)],
    }


if __name__ == "__main__":
    build()
