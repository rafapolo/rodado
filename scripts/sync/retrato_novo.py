"""Tabelas que vivem como último retrato + `*_historico` (docs/context/retratos_historico.yaml).

Para elas, retrato novo da Base dos Dados não entra em `~/rodado/<ds>/<tb>/`: cai em
`~/scrap_tmp/retrato_novo/<ds>/<tb>/` e passa por `gera_retrato_historico.py --anexa`.

    config("ds.tb")   -> {"chave": ..., "data": ...} ou None
    pasta("ds.tb")    -> diretório de trabalho (str, com `~` não expandido: serve no ssh)
    recusa("ds.tb")   -> motivo (texto) para os syncs que escrevem a tabela inteira, ou None
    comando("ds.tb")  -> linha de shell (beelink) que anexa o que está no diretório de trabalho
"""
import os
import sys
from pathlib import Path

_YAML = Path(__file__).resolve().parents[2] / "docs/context/retratos_historico.yaml"
_cache = None
PASTA = os.environ.get("RETRATO_NOVO", "/home/polo/scrap_tmp/retrato_novo")  # caminho do beelink (o ssh não expande ~ em argumento)
REPO_BEELINK = "~/scrap_tmp/repo"


def _lista():
    global _cache
    if _cache is None:
        if not _YAML.exists():
            print(f"aviso: {_YAML} não existe, sem rota de retrato novo", file=sys.stderr)
            _cache = {}
        else:
            import yaml
            _cache = (yaml.safe_load(_YAML.read_text()) or {}).get("tabelas") or {}
    return _cache


def config(alvo):
    return _lista().get(alvo)


def pasta(alvo):
    ds, tb = alvo.split(".", 1)
    return f"{PASTA}/{ds}/{tb}"


def comando(alvo, novo=None, extra=""):
    ds, tb = alvo.split(".", 1)
    return (f"flock ~/scrap_tmp/pesado.lock python3 {REPO_BEELINK}/scripts/sync/gera_retrato_historico.py "
            f"{ds} {tb} --anexa --novo {novo or pasta(alvo)} {extra}").strip()


def recusa(alvo):
    if not config(alvo):
        return None
    return ("guarda só o último retrato + *_historico: retrato novo não entra como parquet solto. "
            f"Use atualiza_particoes_bq/aplica_pouso_bq (caem em {pasta(alvo)} e anexam) ou, à mão, "
            f"`{comando(alvo)}`; ver docs/tecnico/mes_novo_cno.md. Liberar só esta tabela: IGNORA_FONTE_PROPRIA={alvo}")
