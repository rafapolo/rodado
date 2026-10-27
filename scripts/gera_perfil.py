#!/usr/bin/env python3
"""Perfil gerado das tabelas de um dataset -> docs/context/summaries/<dataset>.perfil.yml.

    python3 scripts/gera_perfil.py br_me_rais br_me_cnpj
    python3 scripts/gera_perfil.py --todos      # pula o dataset que já tem perfil; --refaz gera de novo

É a parte do cartão que estatística diz sozinha, ao lado do cartão escrito à mão
(`summaries/<dataset>.yml`: grão, o que se soma, use para). Por coluna: tipo, nulos, distintos
(aproximado), min e max, média e quartis se numérica, e os 10 valores mais frequentes quando a
coluna tem até 50 distintos. Foi o que a avaliação de 2026-10-26 mostrou faltar: sem ver que a
situação cadastral do CNPJ é '2', o modelo escreve '02' e conta zero.

Sai do `SUMMARIZE` do DuckDB, no beelink em -readonly. Tabela com mais de AMOSTRA linhas
lê uma amostra por bloco com semente fixa (`USING SAMPLE p% (system, 42)`), da última partição de
`ano` quando há; o arquivo diz qual. A contagem do top é da amostra, não da tabela.
Coluna com dado pessoal (nome, documento, endereço, telefone, e-mail) fica só com contagens: o
min, o max e o top dela seriam nomes e números de gente.

Arquivo gerado: não edite à mão; rode de novo.
"""
import datetime, json, re, subprocess, sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "context" / "summaries"
AMOSTRA = 2_000_000    # linhas lidas, no máximo aproximado, por tabela
PESSOAL = re.compile(r"nome|razao|cpf|cnpj(?!_basico$)|documento|telefone|fax|ddd|email|logradouro|numero|complemento|bairro|cep|representante|endereco|favorecid|beneficiari|titular|_nis|^nis$|pis_pasep|matricula|placa", re.I)
TOP_ATE = 50


def duck(sql, timeout=1800):
    r = subprocess.run(["ssh", "beelink", "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                       input="SET enable_progress_bar=false;\nSET threads=8;\n" + sql, capture_output=True, text=True, timeout=timeout)
    if r.returncode or "Error" in r.stderr:
        raise RuntimeError(r.stderr[-800:])
    out = r.stdout[r.stdout.find("["):] if "[" in r.stdout else "[]"
    return json.loads(out)


def tabelas(ds):
    return [(x["table"], int(x["rows"] or 0)) for x in duck(
        f"SELECT \"table\", rows FROM _rodado_metadata WHERE dataset = '{ds}' AND source <> 'view_only' "
        f"AND \"table\" NOT IN ('dicionario') ORDER BY 1;")]


def fonte(ds, tb, linhas):
    """A consulta que o perfil lê (amostra por bloco, semente fixa) e como ela é descrita."""
    nome = f"{ds}.{tb}"
    if linhas <= AMOSTRA:
        return nome, "tabela inteira"
    cols = {c["column_name"] for c in duck(f"DESCRIBE {nome};")}
    base, onde = nome, ""
    if "ano" in cols:
        ult = duck(f"SELECT max(ano) a FROM {nome};")[0]["a"]
        base, onde = f"(SELECT * FROM {nome} WHERE ano = {ult})", f" da última partição (ano = {ult})"
        linhas = duck(f"SELECT count(*) n FROM {base};")[0]["n"]
    pct = min(100.0, round(100 * AMOSTRA / max(linhas, 1), 3))
    if pct >= 100:
        return base, f"tabela inteira{onde}"
    return f"(SELECT * FROM {base} USING SAMPLE {pct}% (system, 42))", f"amostra de {str(pct).replace('.', ',')}%{onde}, ~{AMOSTRA:,} linhas".replace(",", ".").replace("de 0.", "de 0,")


def num(v):
    try:
        f = float(v)
        return int(f) if f.is_integer() and abs(f) < 1e15 else round(f, 4)
    except (TypeError, ValueError):
        return v


def perfil_tabela(ds, tb, linhas):
    q, como = fonte(ds, tb, linhas)
    resumo = duck(f"SUMMARIZE SELECT * FROM {q};", timeout=3600)
    colunas, poucas = {}, []
    for c in resumo:
        nome, tipo = c["column_name"], c["column_type"]
        p = {"tipo": tipo, "nulos_pct": num(c["null_percentage"]), "distintos_aprox": num(c["approx_unique"])}
        if PESSOAL.search(nome):
            p["pessoal"] = "só contagens: valores seriam dado pessoal"
        else:
            p["min"], p["max"] = c["min"], c["max"]
            if c.get("avg") is not None and re.match(r"(BIG|SMALL|TINY|U)?INT|DOUBLE|FLOAT|DECIMAL|HUGEINT", tipo):
                p["media"] = num(c["avg"])
                p["quartis"] = [num(c["q25"]), num(c["q50"]), num(c["q75"])]
            if (c["approx_unique"] or 0) <= TOP_ATE:
                poucas.append(nome)
        colunas[nome] = p
    if poucas:
        # os tops de todas as colunas de poucos valores numa consulta só, sobre a mesma amostra
        partes = [f"(SELECT '{c}' c, \"{c}\"::VARCHAR v, count(*) n FROM {q} GROUP BY 2 ORDER BY 3 DESC, 2 LIMIT 10)" for c in poucas]
        for t in duck(" UNION ALL ".join(partes) + ";", timeout=3600):
            colunas[t["c"]].setdefault("top", []).append([t["v"], t["n"]])
    return {"linhas": linhas, "fonte_do_perfil": como, "colunas": colunas}


def datasets():
    return [x["dataset"] for x in duck("SELECT DISTINCT dataset FROM _rodado_metadata WHERE source <> 'view_only' ORDER BY 1;")]


def main(args):
    SAIDA.mkdir(parents=True, exist_ok=True)
    refaz = "--refaz" in args
    dsets = datasets() if "--todos" in args else [a for a in args if not a.startswith("--")]
    for ds in dsets:
        dest = SAIDA / f"{ds}.perfil.yml"
        if dest.exists() and not refaz:
            continue
        doc = {"dataset": ds, "gerado_em": datetime.date.today().isoformat(),
               "gerado_por": "scripts/gera_perfil.py — não edite à mão", "tabelas": {}}
        for tb, n in tabelas(ds):
            print(f"{ds}.{tb} ({n:,} linhas)", flush=True)
            try:
                doc["tabelas"][tb] = perfil_tabela(ds, tb, n)
            except Exception as e:  # uma tabela quebrada não para o lote; o erro fica no arquivo
                print(f"  ! {e}", flush=True)
                doc["tabelas"][tb] = {"linhas": n, "erro": str(e).strip().splitlines()[-1][:300] if str(e).strip() else type(e).__name__}
        dest.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=140, default_flow_style=None))
        print(f"-> {dest.relative_to(RAIZ)}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1:])
