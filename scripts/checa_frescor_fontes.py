#!/usr/bin/env python3
"""
Compara o dado mais recente da FONTE com o que o espelho tem. Só reporta.

    python3 scripts/checa_frescor_fontes.py            # todas as entradas
    python3 scripts/checa_frescor_fontes.py br_cgu_    # só as que começam assim
    python3 scripts/checa_frescor_fontes.py --md       # tabela em markdown

Lê docs/context/privado/source_freshness_checks.yaml (como perguntar à fonte) e, do
catálogo no beelink (`_rodado_metadata`), o `last_date` de cada tabela — a
data mais recente DENTRO do dado, que vem de dataset_freshness.yaml — ou, na
falta dele, o `updated_at` (parquet mais novo da tabela). Para cada entrada imprime o que a fonte diz, o
que o espelho tem e o comando do gate (scripts/scrap/atualiza_fonte.py) que
atualizaria. Não roda scraper e não grava nada: é a Fase 1 de
tasks/automatizar_atualizacao_fontes.md — automatizar a checagem, não a
correção.

Dois avisos de leitura:
  - `http_last_modified` diz quando o ARQUIVO da fonte mudou, não a data do
    dado; compara-se com o updated_at. Fonte regravada todo dia aparece
    sempre "à frente" — o que importa é a distância.
  - comparação é sempre entre datas, nunca entre strings: "31/12/2025" >
    "26/08/2026" alfabeticamente, e foi assim que uma checagem manual do BCB
    SGS deu gap falso em 2026-09-04.
"""
import datetime as dt
import email.utils
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
CHECKS = RAIZ / "docs/context/privado/source_freshness_checks.yaml"
BEELINK = os.environ.get("BEELINK_HOST", "beelink")
UA = "Mozilla/5.0 (rodado-scraper)"


def curl(args, timeout=90):
    r = subprocess.run(["curl", "-sS", "-L", "-m", str(timeout), "-A", UA, *args], capture_output=True, timeout=timeout + 10)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode(errors="replace").strip()[:120])
    return r.stdout


def le_data(texto, formato):
    d = dt.datetime.strptime(texto, formato)
    # formato sem ano (o mês de um diretório do ano corrente): assume o ano corrente
    return (d.replace(year=dt.date.today().year) if "%Y" not in formato else d).date()


def http_json(c):
    v = json.loads(curl([c["url"]]))
    for passo in c["json_path"]:
        v = v[passo]
    return le_data(str(v), c["formato"])


def http_last_modified(c):
    cab = curl(["-I", c["url"]], timeout=240).decode(errors="replace")   # o FTP do DATASUS leva minutos no HEAD
    achados = re.findall(r"(?im)^last-modified:\s*(.+?)\s*$", cab)
    if not achados:
        raise RuntimeError("sem Last-Modified")
    return email.utils.parsedate_to_datetime(achados[-1]).date()   # o último, depois dos redirects


def regex(c):
    txt = curl([c["url"]]).decode(errors="replace")
    achados = {"".join(m) if isinstance(m, tuple) else m for m in re.findall(c["padrao"], txt)}
    if not achados:
        raise RuntimeError("padrão não casou — a página mudou?")
    return max(le_data(a, c["formato"]) for a in achados)


TIPOS = {"http_json": http_json, "http_last_modified": http_last_modified, "regex": regex}


def catalogo():
    sql = ("SET enable_progress_bar=false; "
           "SELECT dataset || '.' || \"table\" AS t, last_date, scrape_date, "
           "CAST(updated_at AS VARCHAR) AS updated_at FROM _rodado_metadata;")
    out = subprocess.run(["ssh", BEELINK, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                         input=sql, capture_output=True, text=True, timeout=180).stdout
    return {r["t"]: r for r in json.loads(out[out.index("["):])}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    md = "--md" in sys.argv
    if not CHECKS.exists():
        print(f"{CHECKS} não existe — a pasta privado/ fica fora do git e não vem num clone novo", file=sys.stderr)
        return 1
    checks = yaml.safe_load(CHECKS.read_text())
    cat = catalogo()
    linhas = []
    for tabela, c in checks.items():
        if args and not any(tabela.startswith(a) for a in args):
            continue
        meta = cat.get(tabela, {})
        espelho = (meta.get("last_date") or "")[:10]
        # updated_at = parquet mais novo da tabela (quando regravamos); scrape_date é a 1ª coleta e não anda
        raspado = (meta.get("updated_at") or meta.get("scrape_date") or "")[:10]
        tipo = c["check"]
        fonte, estado = "", ""
        if tipo == "dead":
            estado = "morta"
        elif tipo == "manual":
            estado = "manual"
        else:
            try:
                d = TIPOS[tipo](c)
                fonte = d.isoformat()
                # last_modified fala do arquivo: compara com quando raspamos. Os outros falam do dado.
                ref = raspado if tipo == "http_last_modified" else (espelho or raspado)
                if not ref:
                    estado = "sem referência no catálogo"
                else:
                    atraso = (d - dt.date.fromisoformat(ref)).days
                    estado = "em dia" if atraso <= 0 else f"fonte +{atraso} d"
            except Exception as e:
                estado = f"ERRO: {str(e)[:60]}"
        comando = f"atualiza_fonte.py {c['scraper']} {c.get('gate', '')}".strip() if c.get("scraper") else ""
        linhas.append((tabela, tipo, fonte, espelho, raspado, estado, comando, c.get("nota", "")))

    if md:
        print("| tabela | fonte | espelho (dado) | regravado em | estado |\n|---|---|---|---|---|")
        for t, _, f, e, r, s, _, _ in linhas:
            print(f"| `{t}` | {f or '—'} | {e or '—'} | {r or '—'} | {s} |")
        return 0
    for t, tipo, f, e, r, s, cmd, nota in linhas:
        print(f"{s:<26} {t}\n{'':26} fonte={f or '—'} ({tipo})  espelho={e or '—'}  regravado={r or '—'}")
        if s.startswith("fonte +") and cmd:
            print(f"{'':26} $ python3 scripts/scrap/{cmd}")
        if nota and (s.startswith(("fonte +", "ERRO")) or tipo in ("manual", "dead")):
            print(f"{'':26} nota: {nota}")
    atras = sum(1 for l in linhas if l[5].startswith("fonte +"))
    erros = sum(1 for l in linhas if l[5].startswith("ERRO"))
    print(f"\n{len(linhas)} entradas: {atras} com a fonte à frente, {erros} com erro de checagem")
    return 0


if __name__ == "__main__":
    sys.exit(main())
