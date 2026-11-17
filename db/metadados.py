"""Catálogo de procedência do espelho, fora do SQL público.

Até 2026-11-17 o `_rodado_metadata` (catalog.parquet do build_metadata_catalog.py) era uma view
do db.rodado.xyz como outra qualquer: qualquer um lia `source_url` de cada tabela, inclusive os
endpoints de API que deram trabalho para achar. Agora o catalogo.py não cria mais as views
`main._rodado_*` (e por isso a pasta delas nem entra no allowed_directories) e grava aqui ao
lado do catálogo, fora de qualquer pasta que a consulta possa abrir, só o que o servidor usa:
linhas e tamanho (travas contra raspagem, /tabelas, guia) e nome da fonte e descrição (árvore
da página). Sem `source_url`.
"""
import json
import os
import re
import threading
from collections import Counter

import rodado_sql

ARQUIVO = os.environ.get("RODADO_METADADOS",
                         os.path.join(os.path.dirname(rodado_sql.BANCO), "metadados.json"))
CAMPOS = ("dataset", "table", "rows", "size_bytes", "source", "source_name", "description",
          "scrape_date", "num_files")
SQL_LEITURA = f"SELECT {', '.join(chr(34) + c + chr(34) for c in CAMPOS)} FROM read_parquet(?)"

_URL = re.compile(r"\s*(?:—\s*)?https?://\S+")
_TEXTO = ("source_name", "description")   # URL escrita no meio do texto também fica de fora

_cache = {"mtime": None, "linhas": [], "por_tabela": {}}
_trava = threading.Lock()


def grava(linhas: list, arquivo: str = ARQUIVO):
    """Grava a lista de dicts (só CAMPOS) de forma atômica."""
    linhas = [{c: (_URL.sub("", l[c]).strip() if c in _TEXTO and isinstance(l.get(c), str) else l.get(c))
               for c in CAMPOS} for l in linhas]
    tmp = arquivo + ".novo"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(linhas, f, ensure_ascii=False, default=str)
    os.replace(tmp, arquivo)


def linhas() -> list:
    """As linhas do catálogo (relidas quando o arquivo muda); [] se ainda não existe."""
    with _trava:
        try:
            mtime = os.path.getmtime(ARQUIVO)
        except OSError:
            return []
        if mtime != _cache["mtime"]:
            with open(ARQUIVO, encoding="utf-8") as f:
                dados = json.load(f)
            _cache.update(mtime=mtime, linhas=dados,
                          por_tabela={(d["dataset"], d["table"]): d for d in dados})
        return _cache["linhas"]


def da_tabela(dataset: str, tabela: str):
    linhas()
    return _cache["por_tabela"].get((dataset, tabela))


def n_linhas(dataset: str, tabela: str):
    d = da_tabela(dataset, tabela)
    return d["rows"] if d else None


def _com_dado():
    return [l for l in linhas() if l.get("source") != "view_only"]


def resumo():
    """(tabelas, datasets, bytes, fontes), sem as views sem dado."""
    ls = _com_dado()
    return (len(ls), len({l["dataset"] for l in ls}), sum(l.get("size_bytes") or 0 for l in ls),
            len({l["source_name"] for l in ls if l.get("source_name")}))


def por_dataset():
    """[(dataset, tabelas, linhas, fonte mais comum)] em ordem de dataset."""
    grupos = {}
    for l in _com_dado():
        grupos.setdefault(l["dataset"], []).append(l)
    saida = []
    for ds in sorted(grupos):
        ls = grupos[ds]
        fontes = Counter(l["source_name"] for l in ls if l.get("source_name"))
        saida.append((ds, len(ls), sum(l.get("rows") or 0 for l in ls),
                      fontes.most_common(1)[0][0] if fontes else None))
    return saida


def tabelas_por_dataset():
    """[(dataset, descrição sem a fonte que abre a frase, [{'t', 'n'}])], sem datasets `_*`."""
    grupos = {}
    for l in _com_dado():
        if not l["dataset"].startswith("_"):
            grupos.setdefault(l["dataset"], []).append(l)
    saida = []
    for ds in sorted(grupos):
        ls = sorted(grupos[ds], key=lambda l: l["table"])
        descs = [d.split(" — ", 1)[1] if " — " in d else d for d in (l.get("description") for l in ls) if d]
        saida.append((ds, max(descs) if descs else None,
                      [{"t": l["table"], "n": l.get("rows") or 0} for l in ls]))
    return saida
