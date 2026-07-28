#!/usr/bin/env python3
"""Gera os dois mapas em flowchart a partir de `schemas.json`.

Ambos são a informação do `ERD.md` com os atributos jogados fora — sem a lista
de tabelas de cada dataset, sobra só o esqueleto: quem se liga a quê.

- `Flow.md`  — um diagrama por domínio (a mesma divisão do ERD);
- `temas.md` — um diagrama só, um `subgraph` por tema, todos ligados aos
  mesmos hubs: é a referência compartilhada que conecta um tema ao outro.

Nos dois: nó = dataset, cápsula = hub de referência agrupado por família num
`subgraph`, aresta = chave de join (cheia = nome canônico, pontilhada =
normalize antes).

No `Flow.md`, um diagrama único com os 195 datasets foi testado e descartado: as arestas
convergem em 18 hubs compartilhados e atravessam a tela toda, o que dá uma
imagem de 14.920×17.107px onde nada se lê. Quebrar por domínio derruba cada
diagrama para ~900px de largura — tamanho natural de leitura numa página — e
mantém as arestas curtas, porque os hubs são repetidos em cada diagrama em vez
de compartilhados entre todos. No `temas.md` é o contrário de propósito: os hubs
são compartilhados, já que a pergunta ali é justamente que temas se encontram na
mesma referência.

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

# Os hubs em famílias — viram um subgraph cada, do lado direito do diagrama.
HUB_GRUPOS = [
    ("Território", ["MUNICIPIO", "UF", "SETOR_CENSITARIO", "CEP"]),
    ("Pessoas e empresas", ["EMPRESA_CNPJ", "PESSOA_CPF", "CNAE", "CBO"]),
    ("Equipamentos", ["ESCOLA", "IES", "CNES", "CID10"]),
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
    return f"{prefixo}{re.sub(r'[^a-z0-9]', '_', nome.lower())}"


def rotulo(dataset):
    """`br_ms_sinan` vira `ms_sinan` — o prefixo `br_` está em todos, é ruído."""
    return re.sub(r"^br_", "", dataset)


def diagrama(datasets, info, prefixo):
    """Um flowchart: os datasets numa coluna à esquerda, os hubs que eles
    alcançam agrupados por família em subgraphs à direita, arestas curtas
    entre os dois.

    `LR` com os hubs à direita é o que mantém a largura em ~900px: os datasets
    empilham numa coluna só e cada aresta cruza um vão curto.

    Os datasets ficam soltos, sem um subgraph em volta, de propósito: o mermaid
    ignora o `direction` de um subgraph quando há aresta cruzando a borda dele,
    e como todo dataset aponta para um hub de fora, a caixa fazia os nós
    espalharem na horizontal — 8.042px de largura contra 900. Quem nomeia o
    grupo é o título da seção, que é mais legível que a moldura de qualquer
    jeito.
    """
    usados = {h for ds in datasets for h in info[ds]["hubs"]}
    linhas = ["flowchart LR"]

    for ds in datasets:
        linhas.append(f'    {nid(prefixo, ds)}["{rotulo(ds)}"]')

    for nome, hubs in HUB_GRUPOS:
        presentes = [h for h in hubs if h in usados]
        if not presentes:
            continue
        linhas.append(f'    subgraph {prefixo}g_{nid("", nome)}["{nome}"]')
        linhas.append("        direction TB")
        for h in presentes:
            linhas.append(f'        {prefixo}{h}(["{h}"])')
        linhas.append("    end")

    for ds in datasets:
        for hub, (label, dashed) in sorted(info[ds]["hubs"].items()):
            seta = "-.->" if dashed else "-->"
            linhas.append(f"    {nid(prefixo, ds)} {seta} {prefixo}{hub}")
    return "\n".join(linhas)


def interconectado(lista, info):
    """Um diagrama só: cada tema é um subgraph, e todos apontam para os *mesmos*
    hubs — é o compartilhamento das referências que liga um tema ao outro.

    A aresta sai do subgraph inteiro, não de cada dataset, e leva quantos
    datasets daquele tema carregam a chave. Isso corta as arestas de 378 para
    ~170 e, como nenhum nó de dentro tem aresta cruzando a borda, o mermaid
    respeita o `direction TB` e as caixas ficam compactas.
    """
    linhas, arestas, usados = ["flowchart LR"], [], set()

    for num, titulo, datasets in lista:
        datasets = sorted(d for d in datasets if d in info and info[d]["hubs"])
        if not datasets:
            continue
        curto = titulo.split(",")[0].split(" e ")[0].strip()[:28]
        linhas.append(f'    subgraph tema_{num}["{num} · {curto}"]')
        linhas.append("        direction TB")
        for ds in datasets:
            linhas.append(f'        {nid(f"t{num}_", ds)}["{rotulo(ds)}"]')
        linhas.append("    end")

        # agrega por hub: quantos datasets do tema chegam lá, e se algum chega
        # pelo nome canônico (aí a aresta é cheia)
        peso, direto = defaultdict(int), defaultdict(bool)
        for ds in datasets:
            for hub, (_, dashed) in info[ds]["hubs"].items():
                peso[hub] += 1
                direto[hub] |= not dashed
        for hub, n in sorted(peso.items()):
            seta = "-->" if direto[hub] else "-.->"
            arestas.append(f'    tema_{num} {seta}|"{n}"| {hub}')
            usados.add(hub)

    for nome, hubs in HUB_GRUPOS:
        presentes = [h for h in hubs if h in usados]
        if not presentes:
            continue
        linhas.append(f'    subgraph g_{nid("", nome)}["{nome}"]')
        linhas.append("        direction TB")
        for h in presentes:
            linhas.append(f'        {h}(["{h}"])')
        linhas.append("    end")

    return "\n".join(linhas + arestas)


def panorama(info):
    """Uma aresta por (domínio, hub), rotulada com quantos datasets a usam —
    o mapa de uma tela só, que o diagrama por dataset não consegue ser."""
    peso = defaultdict(int)
    for ds in info:
        for hub in info[ds]["hubs"]:
            peso[(domain_of(ds), hub)] += 1

    por_dom = defaultdict(list)
    for ds in info:
        por_dom[domain_of(ds)].append(ds)

    linhas = ["flowchart LR", '    subgraph doms["Domínios"]', "        direction TB"]
    for dom in DOMAIN_ORDER:
        if dom in por_dom:
            linhas.append(f'        D_{dom}["{DOMAIN_NAMES[dom]["pt"]}<br/>'
                          f'{len(por_dom[dom])} datasets"]')
    linhas.append("    end")

    usados = {h for _, h in peso}
    for nome, hubs in HUB_GRUPOS:
        presentes = [h for h in hubs if h in usados]
        if not presentes:
            continue
        linhas.append(f'    subgraph g_{nid("", nome)}["{nome}"]')
        linhas.append("        direction TB")
        for h in presentes:
            linhas.append(f'        {h}(["{h}"])')
        linhas.append("    end")

    # só as ligações com peso — abaixo de 3 datasets vira ruído visual
    for (dom, hub), n in sorted(peso.items()):
        if n >= 3:
            linhas.append(f'    D_{dom} -->|"{n}"| {hub}')
    return "\n".join(linhas)


LEGENDA = """- **caixa** = dataset; {agrupador};
- **cápsula** = hub de referência, agrupado por família num `subgraph` e
  repetido em cada diagrama para manter as arestas curtas;
- **seta cheia** (`-->`) = a chave está lá com o nome canônico, join direto;
- **seta pontilhada** (`-.->`) = a chave está com outro nome ou formato,
  normalize antes — receita em [`{doc}`]({doc});
- a lista de tabelas de cada dataset ficou de fora de propósito; está no
  [`ERD.md`](ERD.md).
"""


def cabecalho(titulo, intro, agrupador):
    return (f"# {titulo}\n\n{intro}\n\n"
            f"Gerado por `scripts/gera_flow.py` a partir de `schemas.json` em "
            f"{date.today().isoformat()} — não edite à mão, regenere.\n\n"
            + LEGENDA.format(agrupador=agrupador, doc=JOIN_KEYS_DOC) + "\n")


def bloco(texto):
    return f"```mermaid\n{texto}\n```\n\n"


def main():
    tables = load_schema()
    info = analyze(tables)

    # ---- Flow.md: panorama + um diagrama por domínio
    por_dom = defaultdict(list)
    for ds in sorted(info):
        por_dom[domain_of(ds)].append(ds)

    partes = [cabecalho(
        "Flow — o espelho por domínio",
        f"Os {len(info)} datasets do espelho e as chaves com que cada um alcança "
        f"os hubs de referência, um diagrama por domínio.",
        "um diagrama por domínio")]
    partes.append("## Panorama\n\nQuantos datasets de cada domínio chegam a cada "
                  "hub (ligações de 3 datasets para cima).\n\n")
    partes.append(bloco(panorama(info)))

    soltos = []
    for dom in DOMAIN_ORDER:
        dss = por_dom.get(dom)
        if not dss:
            continue
        nome = DOMAIN_NAMES[dom]["pt"]
        ligados = [d for d in dss if info[d]["hubs"]]
        soltos += [d for d in dss if not info[d]["hubs"]]
        partes.append(f"## {nome}\n\n{len(dss)} datasets"
                      + (f" · {len(dss) - len(ligados)} sem ligação documentada"
                         if len(ligados) != len(dss) else "") + "\n\n")
        if ligados:
            partes.append(bloco(diagrama(ligados, info, f"{dom}_")))

    if soltos:
        partes.append("## Sem ligação documentada\n\n"
                      f"{len(soltos)} datasets não têm nenhuma chave que chegue a "
                      "um hub — estão no espelho, mas nada documentado os liga a "
                      "mais nada:\n\n"
                      + "\n".join(f"- `{d}`" for d in sorted(soltos)) + "\n")
    DST_FLOW.write_text("".join(partes), encoding="utf-8")

    # ---- temas.md: um diagrama só, interconectado pelos hubs
    lista = temas(tables)
    cobertos = {d for _, _, ds in lista for d in ds}
    partes = [cabecalho(
        "Temas — que dados cada investigação usa",
        f"Os 43 temas do site e os datasets que cada um cita, "
        f"{len(cobertos)} dos {len(info)} do espelho. Os temas não se ligam\n"
        f"entre si diretamente: o que os conecta é chegarem às mesmas\n"
        f"referências — a aresta leva quantos datasets do tema carregam a chave.\n\n"
        "> A origem é o markdown de `docs/overview/`: os datasets que o próprio\n"
        "> texto de cada tema nomeia. Não é a lista completa do que a investigação\n"
        "> tocou — é o que está registrado. Dataset sem citação não aparece.",
        "cada `subgraph` é um tema, e a aresta sai do tema inteiro")]
    partes.append(bloco(interconectado(lista, info)))

    orfaos = [(num, titulo) for num, titulo, dss in lista
              if not [d for d in dss if d in info and info[d]["hubs"]]]
    if orfaos:
        partes.append("\n## Temas sem ligação\n\nNenhum dataset citado por estes "
                      "temas chega a um hub de referência:\n\n"
                      + "\n".join(f"- {n} · {t}" for n, t in orfaos) + "\n")
    DST_TEMAS.write_text("".join(partes), encoding="utf-8")

    for p in (DST_FLOW, DST_TEMAS):
        n = p.read_text().count("```mermaid")
        print(f"{p.relative_to(REPO)} — {n} diagramas, {p.stat().st_size / 1024:.1f} KB")
    print(f"  datasets : {len(info)} ({len(soltos)} sem hub)")
    print(f"  temas    : {len(lista)} ({len(cobertos)} datasets citados)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
