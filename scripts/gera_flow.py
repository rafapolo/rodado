#!/usr/bin/env python3
"""Gera os dois mapas em flowchart a partir de `schemas.json`.

Ambos são a mesma informação do `ERD.md` com os atributos jogados fora — sem a
lista de tabelas de cada dataset, os 825 nós viram 195 e o mapa inteiro cabe num
diagrama só, que é o que o `subgraph` permite mostrar:

- `Flow.md`  — um flowchart, um `subgraph` por domínio (a mesma divisão do ERD);
- `temas.md` — um flowchart, um `subgraph` por tema dos 43 do site.

Nos dois, nó = dataset, aresta = chave de join que chega a um hub de referência
(sólida = nome canônico, tracejada = precisa normalizar antes). As receitas de
join continuam em `docs/context/join_keys.md`.

Não edite os .md à mão — regenere.
"""

import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gera_erd import (  # noqa: E402
    DOMAIN_NAMES,
    DOMAIN_ORDER,
    JOIN_KEYS_DOC,
    analyze,
    domain_of,
    load_schema,
)

REPO = Path(__file__).resolve().parent.parent
DST_FLOW = REPO / "Flow.md"
DST_TEMAS = REPO / "temas.md"
OVERVIEW = REPO / "docs" / "overview"

# Os hubs, agrupados como aparecem no diagrama. Mesmos códigos do ERD.
HUB_GRUPOS = [
    ("Território", ["MUNICIPIO", "UF", "SETOR_CENSITARIO", "CEP"]),
    ("Pessoas e empresas", ["EMPRESA_CNPJ", "PESSOA_CPF", "CNAE", "CBO"]),
    ("Equipamentos públicos", ["ESCOLA", "IES", "CNES", "CID10"]),
    ("Estado e economia", ["ORGAO", "UNIDADE_GESTORA", "FUNCAO_PROGRAMA",
                           "PARTIDO", "NCM_SH", "PAIS"]),
]

# ---------------------------------------------------------------------------
# Tema -> datasets
# ---------------------------------------------------------------------------
# Não existe manifesto de "que dados cada tema usa": as páginas publicadas não
# nomeiam dataset nenhum. O que existe é o markdown de origem em
# `docs/overview/`, que cita as bases de três formas — daí os três padrões.
_QUALIFICADO = re.compile(r"\b((?:br|global|mundo|world)_[a-z0-9_]+)\.[a-z0-9_]+")
_SOLTO = re.compile(r"\b((?:br|global|mundo|world)_[a-z0-9_]+)\b")
_ENTIDADE = re.compile(r"^\s{4}([a-z][a-z0-9_]*)\s*\{", re.M)


def indice_de_tabelas(tables):
    """Resolve as entidades curtas dos mermaid do overview (`rais_microdados_
    vinculos`, `sim_microdados`) de volta para o dataset real."""
    idx = {}
    for tid in tables:
        ds, _, tb = tid.partition(".")
        idx.setdefault(f"{ds.split('_')[-1]}_{tb}", ds)
        idx.setdefault(tb, ds)
    return idx


def temas(tables):
    """[(numero, titulo, {datasets})] na ordem dos arquivos."""
    conhecidos = {t.partition(".")[0] for t in tables}
    idx = indice_de_tabelas(tables)
    out = []
    # `35_transporte_mobilidade.en.md` é tradução, não um 44º tema — entraria
    # com o mesmo número e daria id de subgraph duplicado.
    for f in sorted(OVERVIEW.glob("[0-9]*.md")):
        if f.name.endswith(".en.md"):
            continue
        texto = f.read_text(encoding="utf-8")
        achados = {d for d in _QUALIFICADO.findall(texto) if d in conhecidos}
        achados |= {d for d in _SOLTO.findall(texto) if d in conhecidos}
        achados |= {idx[e] for e in _ENTIDADE.findall(texto) if e in idx}
        titulo = texto.lstrip().split("\n", 1)[0].lstrip("# ").strip()
        out.append((f.name.split("_")[0], titulo, achados))
    return out


# ---------------------------------------------------------------------------
# Mermaid
# ---------------------------------------------------------------------------
def nid(prefixo, nome):
    """Id de nó válido em mermaid, único por subgraph."""
    return f"{prefixo}{re.sub(r'[^a-z0-9]', '_', nome.lower())}"


def rotulo(dataset):
    """`br_ms_sinan` vira `ms_sinan` — o prefixo `br_` é ruído, está em todos."""
    return re.sub(r"^br_", "", dataset)


def bloco_hubs():
    linhas = []
    for titulo, hubs in HUB_GRUPOS:
        linhas.append(f'    subgraph hubs_{nid("", titulo)}["{titulo}"]')
        linhas.append("        direction TB")
        for h in hubs:
            linhas.append(f'        {h}(["{h}"])')
        linhas.append("    end")
    return linhas


def arestas(prefixo, dataset, entry, usados):
    """dataset --> hub, sólida quando a chave está com o nome canônico."""
    linhas = []
    for hub, (label, dashed) in sorted(entry["hubs"].items()):
        seta = "-.->" if dashed else "-->"
        linhas.append(f'    {nid(prefixo, dataset)} {seta}|"{label}"| {hub}')
        usados.add(hub)
    return linhas


def render_flow(info):
    """Um flowchart, um subgraph por domínio."""
    por_dominio = defaultdict(list)
    for ds in sorted(info):
        por_dominio[domain_of(ds)].append(ds)

    corpo, arst, usados = [], [], set()
    for dom in DOMAIN_ORDER:
        datasets = por_dominio.get(dom)
        if not datasets:
            continue
        nome = DOMAIN_NAMES[dom]["pt"]
        corpo.append(f'    subgraph dom_{dom}["{nome} · {len(datasets)}"]')
        corpo.append("        direction TB")
        for ds in datasets:
            corpo.append(f'        {nid("d_", ds)}["{rotulo(ds)}"]')
        corpo.append("    end")
        for ds in datasets:
            arst += arestas("d_", ds, info[ds], usados)

    soltos = sorted(ds for ds in info if not info[ds]["hubs"])
    return corpo, arst, usados, soltos


def render_temas(info, lista):
    """Um flowchart, um subgraph por tema. O mesmo dataset reaparece em cada
    tema que o cita — em mermaid um nó só vive num subgraph, e aqui a repetição
    é o ponto: mostra de que bases cada tema depende."""
    corpo, arst, usados = [], [], set()
    for num, titulo, datasets in lista:
        datasets = sorted(d for d in datasets if d in info)
        if not datasets:
            continue
        curto = titulo.split(",")[0].split(" e ")[0].strip()
        corpo.append(f'    subgraph tema_{num}["{num} · {curto}"]')
        corpo.append("        direction TB")
        for ds in datasets:
            corpo.append(f'        {nid(f"t{num}_", ds)}["{rotulo(ds)}"]')
        corpo.append("    end")
        for ds in datasets:
            arst += arestas(f"t{num}_", ds, info[ds], usados)
    return corpo, arst, usados


CABECALHO = """# {titulo}

{intro}

Gerado por `scripts/gera_flow.py` a partir de `schemas.json` em {data} — não
edite à mão, regenere.

- **nó** = dataset; **cápsula** = hub de referência;
- **seta cheia** (`-->`) = a chave está no dataset com o nome canônico, join direto;
- **seta pontilhada** (`-.->`) = a chave está com outro nome ou formato, normalize
  antes — receita em [`{doc}`]({doc});
- os atributos (a lista de tabelas de cada dataset) ficaram de fora de propósito:
  é o que faz o mapa inteiro caber num diagrama só. Eles estão no [`ERD.md`](ERD.md).

"""


def escreve(path, titulo, intro, corpo, arst, usados, rodape=""):
    hubs = [ln for ln in bloco_hubs()
            if not re.match(r"^\s+[A-Z_]+\(\[", ln) or ln.split("(")[0].strip() in usados]
    # não deixa subgraph de hub vazio
    limpo, buf = [], []
    for ln in hubs:
        buf.append(ln)
        if ln.strip() == "end":
            if any(re.match(r"^\s+[A-Z_]+\(\[", x) for x in buf):
                limpo += buf
            buf = []
    texto = CABECALHO.format(titulo=titulo, intro=intro, data=date.today().isoformat(),
                             doc=JOIN_KEYS_DOC)
    texto += "```mermaid\nflowchart LR\n" + "\n".join(limpo + corpo + arst) + "\n```\n"
    texto += rodape
    path.write_text(texto, encoding="utf-8")
    return texto


def main():
    tables = load_schema()
    info = analyze(tables)

    corpo, arst, usados, soltos = render_flow(info)
    rodape = ""
    if soltos:
        rodape = ("\n## Sem ligação documentada\n\n"
                  f"{len(soltos)} datasets não têm nenhuma chave que chegue a um hub — "
                  "estão no espelho, mas nada documentado os liga a mais nada:\n\n"
                  + "\n".join(f"- `{d}`" for d in soltos) + "\n")
    escreve(DST_FLOW, "Flow — o espelho por domínio",
            f"Os {len(info)} datasets do espelho agrupados nos "
            f"{len({domain_of(d) for d in info})} domínios do `ERD.md`, "
            "e as chaves com que cada um alcança os hubs de referência.",
            corpo, arst, usados, rodape)

    lista = temas(tables)
    corpo, arst, usados = render_temas(info, lista)
    cobertos = len({d for _, _, ds in lista for d in ds})
    escreve(DST_TEMAS, "Temas — que dados cada investigação usa",
            f"Os 43 temas do site e os datasets que cada um cita, "
            f"{cobertos} dos {len(info)} do espelho.\n\n"
            "> A origem é o markdown de `docs/overview/`: os datasets que o próprio\n"
            "> texto de cada tema nomeia. Não é a lista completa do que a investigação\n"
            "> tocou — é o que está registrado. Dataset sem citação não aparece.",
            corpo, arst, usados)

    for p in (DST_FLOW, DST_TEMAS):
        print(f"{p.relative_to(REPO)} — {p.stat().st_size / 1024:.1f} KB")
    print(f"  datasets : {len(info)}")
    print(f"  temas    : {len(lista)} ({cobertos} datasets citados)")
    print(f"  sem hub  : {len(soltos)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
