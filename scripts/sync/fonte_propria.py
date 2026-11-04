"""Trava dos syncs da Base dos Dados nas tabelas com arquivo de outra fonte.

Lista em docs/context/fonte_propria.yaml. `recusa("ds.tabela")` devolve o motivo
(texto) quando a tabela está na lista, ou None. Sem o YAML (clone parcial, cópia
de scripts no beelink sem docs/), não trava nada, mas avisa uma vez.
"""
import os
import sys
from pathlib import Path

_YAML = Path(__file__).resolve().parents[2] / "docs/context/fonte_propria.yaml"
_cache = None


def _lista():
    global _cache
    if _cache is None:
        if not _YAML.exists():
            print(f"aviso: {_YAML} não existe, sem trava de fonte própria", file=sys.stderr)
            _cache = {}
        else:
            import yaml
            _cache = (yaml.safe_load(_YAML.read_text()) or {}).get("tabelas") or {}
    return _cache


def recusa(alvo):
    if os.environ.get("IGNORA_FONTE_PROPRIA") == alvo:
        return None
    e = _lista().get(alvo)
    if not e:
        # último retrato + *_historico (br_rf_cno): ver retrato_novo.py
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import retrato_novo
        return retrato_novo.recusa(alvo)
    return (f"tem arquivo de outra fonte ({', '.join(e.get('arquivos') or [])}; {e.get('periodo', '')}): "
            f"ver docs/context/fonte_propria.yaml. Liberar só esta tabela: IGNORA_FONTE_PROPRIA={alvo}")
