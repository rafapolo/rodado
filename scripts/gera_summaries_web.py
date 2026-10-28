#!/usr/bin/env python3
"""Gera os cartões das tabelas que o painel do atlas mostra ao abrir uma tabela.

`pages/assets/summaries.json` é o índice (data e nº de tabelas por dataset); os cartões ficam em
`pages/assets/summaries/<dataset>.json`, buscados só quando o dataset abre.

    python3 scripts/gera_summaries_web.py

Lê `docs/context/summaries/<dataset>.yml` (cartão), `<dataset>.perfil.yml` (só o `erro`; nenhum
valor medido, como min/max/top, vai para a página) e `_ultima_data.json` (data do dado
mais recente, de `gera_ultima_data.py`). O JSON usa chaves curtas, que `pages/atlas/_page.html`
expande: g grão, c chave, tp/te tempo e território, m medidas, f filtros, u use_para, nu
nao_use_para, v verificado, r campos em rascunho, rn notas em rascunho, d ultima_data, e erro.
`gera_schema_graph.py` lê os cartões publicados para o "dados até" do atlas.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

import yaml

# o atlas lê estes cartões e não cita o Base dos Dados: mesma troca do schema_graph.json
from gera_schema_graph import sem_bdd

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "docs" / "context" / "summaries"
SAIDA = RAIZ / "pages" / "assets" / "summaries.json"
POR_DATASET = RAIZ / "pages" / "assets" / "summaries"
CAMPOS = ("grao", "chave", "tempo", "territorio", "medidas", "filtros_tipicos", "use_para", "nao_use_para")
MESES = {"pt": "jan fev mar abr mai jun jul ago set out nov dez".split(),
         "en": "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()}
DATA = re.compile(r"^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$")
Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def chave_data(s):
    """Tupla (ano, mês, dia) para comparar datas de granularidades diferentes; None se não for data."""
    m = DATA.match(s or "")
    return tuple(int(x or 0) for x in m.groups()) if m else None


def formata_data(s, idioma):
    """'2026-09' vira 'set/2026' (pt) ou 'Sep 2026' (en); dia completo, '30/09/2026' ou '2026-09-30'."""
    m = DATA.match(s or "")
    if not m:
        return s or ""
    a, mes, dia = m.groups()
    if not mes:
        return a
    if not dia:
        return f"{MESES[idioma][int(mes) - 1]}{'/' if idioma == 'pt' else ' '}{a}"
    return f"{dia}/{mes}/{a}" if idioma == "pt" else s


def maior(datas):
    """A data mais recente de uma lista de strings de granularidades mistas."""
    validas = [d for d in datas if chave_data(d)]
    return max(validas, key=chave_data) if validas else None


def le_yaml(caminho):
    return yaml.load(caminho.read_text(), Loader=Loader) or {}


def medida(m):
    """[expressão ou coluna, o_que, unidade, 'nao' se não soma, nota] sem os vazios do fim."""
    if not isinstance(m, dict):
        return [str(m)]
    item = [m.get("expressao") or m.get("coluna") or "", m.get("o_que") or "", m.get("unidade") or "",
            "nao" if m.get("soma") == "nao" else "", m.get("nota") or ""]
    while item and not item[-1]:
        item.pop()
    return item


def tabela(nome, c, ultima, perfil):
    """Cartão enxuto de uma tabela; só entra o que a página usa."""
    t = {"n": nome, "g": c.get("grao") or ""}
    if c.get("chave"):
        t["c"] = str(c["chave"])
    tempo = c.get("tempo") or {}
    if tempo.get("natureza"):
        t["tp"] = [tempo["natureza"], str(tempo.get("coluna") or ""), str(tempo.get("cobertura") or "")]
    terr = c.get("territorio") or {}
    if terr.get("nivel"):
        t["te"] = [terr["nivel"]]
    if c.get("medidas"):
        t["m"] = [medida(m) for m in c["medidas"]]
    if c.get("filtros_tipicos"):
        t["f"] = [str(f) for f in c["filtros_tipicos"]]
    for curto, campo in (("u", "use_para"), ("nu", "nao_use_para"), ("v", "verificado")):
        if c.get(campo):
            t[curto] = str(c[campo])
    # rascunho: cada item nomeia um campo do cartão ("medidas.unidade") ou é uma nota solta
    campos, notas = [], []
    for item in c.get("rascunho") or []:
        base = re.split(r"[.\s(:]", str(item), maxsplit=1)[0]
        if base in CAMPOS:
            if base not in campos:
                campos.append(base)
        else:
            notas.append(str(item))
    if campos:
        t["r"] = campos
    if notas:
        t["rn"] = notas
    if ultima.get("ultima_data"):
        t["d"] = ultima["ultima_data"]
    p = perfil.get(nome) or {}
    if p.get("erro"):
        t["e"] = str(p["erro"]).split("\n")[0][:160]
    return t


def carregar():
    """{dataset: {'d': ultima_data do dataset ou None, 't': [tabelas]}} para os datasets com cartão."""
    bruto = json.loads((PASTA / "_ultima_data.json").read_text()) if (PASTA / "_ultima_data.json").exists() else {}
    saida = {}
    for arq in sorted(PASTA.glob("*.yml")):
        if arq.name.endswith(".perfil.yml"):
            continue
        ds = arq.stem
        cartoes = le_yaml(arq).get("tabelas") or {}
        if not cartoes:
            continue
        pf = PASTA / f"{ds}.perfil.yml"
        perfil = le_yaml(pf).get("tabelas") or {} if pf.exists() else {}
        tabelas = [tabela(n, c or {}, bruto.get(f"{ds}.{n}") or {}, perfil) for n, c in cartoes.items()]
        for t in tabelas:   # data muito no futuro é sentinela (9999-12-31), não dado recente
            if t.get("d") and chave_data(t["d"])[0] > date.today().year + 2:
                del t["d"]
        saida[ds] = {"d": maior([t.get("d") for t in tabelas]), "t": tabelas}
    return saida


def main():
    dados = carregar()
    # um JSON por dataset (o inteiro passa de 1,5 MB); o índice só diz a data e quantas tabelas
    POR_DATASET.mkdir(exist_ok=True)
    for antigo in POR_DATASET.glob("*.json"):
        if antigo.stem not in dados:
            antigo.unlink()
    for ds, d in dados.items():
        (POR_DATASET / f"{ds}.json").write_text(json.dumps(sem_bdd(d), ensure_ascii=False, separators=(",", ":")))
    indice = {ds: {"d": d["d"], "n": len(d["t"])} for ds, d in dados.items()}
    SAIDA.write_text(json.dumps(sem_bdd(indice), ensure_ascii=False, separators=(",", ":")))
    tamanhos = [f.stat().st_size for f in POR_DATASET.glob("*.json")]
    print(f"{SAIDA.relative_to(RAIZ)}: {len(dados)} datasets, {SAIDA.stat().st_size / 1e3:.0f} kB; "
          f"{POR_DATASET.relative_to(RAIZ)}/: {sum(tamanhos) / 1e6:.2f} MB, maior {max(tamanhos) / 1e3:.0f} kB")


if __name__ == "__main__":
    sys.exit(main())
