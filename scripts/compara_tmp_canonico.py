#!/usr/bin/env python3
"""Diff tipado entre o tmp*.parquet e o export canônico, tabela a tabela.

    python3 scripts/compara_tmp_canonico.py                    # todas as que têm tmp
    python3 scripts/compara_tmp_canonico.py br_bd_diretorios_brasil.municipio
    python3 scripts/compara_tmp_canonico.py --colunas br_bd_diretorios_brasil.municipio

O `triagem_tmp_parquet.py` compara por hash e, nos empates de contagem, acusa
"conteúdo diferente". Quase sempre é mentira: os tmp saíram de
`bq query --format=json` → `pa.Table.from_pylist()`, que devolve **toda** coluna como
string. Um hash sobre INT64 e sobre a string do mesmo número nunca bate.

Aqui os dois lados são normalizados antes de comparar:

  - o tmp é castado para o tipo do canônico, coluna por coluna, por NOME;
  - `TIME WITH TIME ZONE` e `TIMESTAMP WITH TIME ZONE` caem para a versão sem fuso
    nos DOIS lados. Sem isso o `evento` da Câmara acusa divergência em 100% das
    linhas só porque o canônico guarda `11:31:00+00` e o tmp guarda `11:31:00`.

O veredicto sai do `EXCEPT` nos dois sentidos:

  IDENTICO           o tmp é cópia string-tipada; apagar não perde nada
  canon SUBSET tmp   o tmp é um snapshot mais novo, estritamente maior
  tmp SUBSET canon   o canônico contém o tmp
  DIVERGEM           linhas mudaram de valor entre os dois snapshots
  SCHEMA DIFERENTE   nomes de coluna não batem — versões diferentes da tabela

Com `--colunas`, em vez do veredicto, imprime quais colunas divergem (comparadas
como VARCHAR, sobre a chave informada em `--chave` ou a primeira coluna).
"""
import argparse
import json
import subprocess
import sys

BEELINK = __import__("os").environ.get("BEELINK_HOST", "beelink")
ROOT = "/home/polo/rodado"


def duck(sql, timeout=3600):
    payload = "SET TimeZone='UTC'; SET enable_progress_bar=false;\n" + sql + "\n.quit\n"
    p = subprocess.run(["ssh", BEELINK, "~/bin/duckdb -json"], input=payload,
                       capture_output=True, text=True, timeout=timeout)
    body = p.stdout[p.stdout.index("["):] if "[" in p.stdout else ""
    if not body:
        return None, p.stderr.strip()[:300]
    return json.loads(body), None


def sh(cmd):
    return subprocess.run(["ssh", BEELINK, cmd], capture_output=True, text=True).stdout.split()


def sem_fuso(t):
    """O fuso é ruído de codificação aqui, não dado — some dos dois lados."""
    if "TIME WITH TIME ZONE" in t:
        return "TIME"
    if "TIMESTAMP WITH TIME ZONE" in t:
        return "TIMESTAMP"
    return t


def lados(d):
    files = sh(f"ls -1 {d}")
    tmp = [f for f in files if f.startswith("tmp") and f.endswith(".parquet")]
    real = [f for f in files if f.endswith(".parquet") and not f.startswith("tmp")]
    return tmp, real


def lista(paths):
    return "[" + ", ".join(f"'{p}'" for p in paths) + "]"


def compara(d, tbl):
    tmp, real = lados(d)
    if not real:
        print(f"{tbl:52} SEM CANONICO — o tmp é a tabela (ver triagem_tmp_parquet.py)")
        return
    c_desc, e = duck(f"DESCRIBE SELECT * FROM read_parquet(['{d}/{real[0]}']);")
    t_desc, e2 = duck(f"DESCRIBE SELECT * FROM read_parquet(['{d}/{tmp[0]}']);")
    if e or e2:
        print(f"{tbl:52} ERRO {e or e2}")
        return
    ctypes = {c["column_name"]: c["column_type"] for c in c_desc}
    if set(ctypes) != {c["column_name"] for c in t_desc}:
        so_t = sorted({c["column_name"] for c in t_desc} - set(ctypes))
        so_c = sorted(set(ctypes) - {c["column_name"] for c in t_desc})
        print(f"{tbl:52} SCHEMA DIFERENTE — só no tmp: {so_t}; só no canônico: {so_c}")
        return
    sel = ", ".join(f'try_cast("{c}" AS {sem_fuso(t)}) AS "{c}"' for c, t in ctypes.items())
    pr = lista(f"{d}/{f}" for f in real)
    pt = lista(f"{d}/{f}" for f in tmp)
    r, err = duck(f"""WITH c AS (SELECT {sel} FROM read_parquet({pr})),
     t AS (SELECT {sel} FROM read_parquet({pt}))
SELECT (SELECT count(*) FROM (SELECT * FROM c EXCEPT SELECT * FROM t)) so_canon,
       (SELECT count(*) FROM (SELECT * FROM t EXCEPT SELECT * FROM c)) so_tmp,
       (SELECT count(*) FROM c) n_canon, (SELECT count(*) FROM t) n_tmp;""")
    if err:
        print(f"{tbl:52} ERRO {err}")
        return
    r = r[0]
    v = ("IDENTICO" if not r["so_canon"] and not r["so_tmp"] else
         "canon SUBSET tmp" if not r["so_canon"] else
         "tmp SUBSET canon" if not r["so_tmp"] else "DIVERGEM")
    print(f"{tbl:52} canon={r['n_canon']:>9,} tmp={r['n_tmp']:>9,}  "
          f"só_canon={r['so_canon']:>7,} só_tmp={r['so_tmp']:>7,}  {v}")


def colunas(d, tbl, chave):
    """Quais colunas divergem, comparadas como texto e casadas pela chave."""
    tmp, real = lados(d)
    if not real:
        print(f"{tbl}: sem canônico")
        return
    c_desc, e = duck(f"DESCRIBE SELECT * FROM read_parquet(['{d}/{real[0]}']);")
    if e:
        print(f"{tbl}: ERRO {e}")
        return
    cols = [c["column_name"] for c in c_desc]
    chave = chave or cols[0]
    pr, pt = lista(f"{d}/{f}" for f in real), lista(f"{d}/{f}" for f in tmp)
    partes = [
        f'SELECT \'{c}\' col, count(*) FILTER (WHERE a."{c}"::VARCHAR '
        f'IS DISTINCT FROM b."{c}"::VARCHAR) difs '
        f"FROM read_parquet({pr}) a JOIN read_parquet({pt}) b USING (\"{chave}\")"
        for c in cols if c != chave
    ]
    r, err = duck("SELECT * FROM (" + "\nUNION ALL ".join(partes) +
                  ") WHERE difs > 0 ORDER BY difs DESC;")
    if err:
        print(f"{tbl}: ERRO {err}")
        return
    print(f"\n{tbl}  (casado por {chave})")
    if not r:
        print("  nenhuma coluna diverge como texto — a diferença era só de tipo")
    for row in r:
        print(f"  {row['col']:32} {row['difs']:>9,} linhas divergem")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tabelas", nargs="*", help="dataset.tabela (padrão: todas com tmp)")
    ap.add_argument("--colunas", action="store_true", help="mostra QUAIS colunas divergem")
    ap.add_argument("--chave", help="coluna de junção para --colunas")
    a = ap.parse_args()

    dirs = sh(f"find {ROOT} -maxdepth 3 -name 'tmp*.parquet' -printf '%h\\n' | sort -u")
    if not dirs:
        print("nenhum tmp*.parquet no espelho — nada a comparar.")
        return 0
    alvo = set(a.tabelas)
    achou = False
    for d in dirs:
        tbl = d.replace(ROOT + "/", "").replace("/", ".", 1)
        if alvo and tbl not in alvo:
            continue
        achou = True
        (colunas(d, tbl, a.chave) if a.colunas else compara(d, tbl))
    if alvo and not achou:
        sys.exit(f"nenhuma das tabelas pedidas tem tmp*.parquet: {sorted(alvo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
