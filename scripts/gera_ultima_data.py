#!/usr/bin/env python3
"""Data do dado mais recente de cada tabela -> campo `ultima_data` em summaries/<dataset>.yml.

    python3 scripts/gera_ultima_data.py            # retoma: pula a tabela que já tem resultado
    python3 scripts/gera_ultima_data.py --refaz
    python3 scripts/gera_ultima_data.py --so-faltam   # remede só as tabelas que ficaram sem data

Quando a expressão direta não acha data (ano com outro nome, `aaaamm` em VARCHAR, milissegundos
desde 1970, `dd-mm-aaaa`, `2026_trimestre_03`, texto com o ano), `sonda()` lê uma amostra dos
valores, escolhe o formato que casa com 80% dela e mede com ele.

Não é a data do arquivo (`last_update` do catálogo diz quando o parquet foi escrito): é o maior
valor da coluna de tempo, sem datas no futuro (a exclusão agendada do MEI vai a 2026-12-31). A
coluna sai do cartão (`tempo.coluna` em `summaries/<dataset>.yml`); sem ela, de `ano`/`mes`,
`data`, `date` ou da primeira coluna DATE/TIMESTAMP do perfil. Granularidade: dia quando a coluna
é data, mês com `ano` e `mes` (ou `aaaamm`), ano com só `ano`. Tabela sem coluna de tempo fica
de fora. Lê no beelink em -readonly, 4 tabelas por vez.

Resultado bruto em `summaries/_ultima_data.json` (é o que permite retomar); no cartão vira uma
linha `ultima_data:` logo abaixo do nome da tabela, inserida como texto para não reescrever o
resto do arquivo escrito à mão.
"""
import datetime, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
PASTA = RAIZ / "docs" / "context" / "summaries"
SAIDA = PASTA / "_ultima_data.json"
HOJE = datetime.date.today()
NOMES = ("data", "date", "dt_refer", "data_referencia", "din_instante", "din_referencia", "data_extracao", "competencia")


def duck(sql, timeout=900):
    r = subprocess.run(["ssh", "beelink", f"timeout {timeout} ~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                       input="SET enable_progress_bar=false;\nSET threads=4;\n" + sql, capture_output=True, text=True,
                       errors="replace", timeout=timeout + 60)
    if r.returncode or "Error" in r.stderr:
        erro = [l for l in r.stderr.splitlines() if "Error" in l]
        raise RuntimeError(erro[0].split("\x1b[00m")[-1] if erro else f"duckdb saiu com {r.returncode}")
    return json.loads(r.stdout[r.stdout.find("["):]) if "[" in r.stdout else []


# Formatos reconhecidos na amostra (`sonda`): (nome, regex do valor, SQL sobre `s`, granularidade).
# `s` é o valor como texto, sem espaços e sem a aspa simples que alguns CSVs trazem na frente.
FORMATOS = [
    ("ms", r"\d{12,13}(\.0+)?", "to_timestamp(try_cast(s AS DOUBLE) / 1000)::DATE", "dia"),
    ("aaaammdd", r"(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])", "try_strptime(s, '%Y%m%d')::DATE", "dia"),
    ("aaaamm", r"(19|20)\d{2}(0[1-9]|1[0-2])", "try_strptime(s, '%Y%m')::DATE", "mes"),
    ("ano", r"(1[89]|20)\d{2}(\.0+)?", "make_date(try_cast(try_cast(s AS DOUBLE) AS INT), 1, 1)", "ano"),
    ("iso", r"\d{4}-\d{2}-\d{2}([ T].*)?", "try_cast(left(s, 10) AS DATE)", "dia"),
    ("dmy", r"\d{2}/\d{2}/\d{4}( .*)?", "try_strptime(left(s, 10), '%d/%m/%Y')::DATE", "dia"),
    ("dmy_traco", r"\d{2}-\d{2}-\d{4}( .*)?", "try_strptime(left(s, 10), '%d-%m-%Y')::DATE", "dia"),
    ("aaaa-mm", r"\d{4}[-/](0[1-9]|1[0-2])", "try_strptime(replace(s, '/', '-'), '%Y-%m')::DATE", "mes"),
    ("mm/aaaa", r"(0[1-9]|1[0-2])/\d{4}", "try_strptime(s, '%m/%Y')::DATE", "mes"),
    ("trimestre", r"\d{4}[_ -]?(trimestre|T|t)[_ -]?0?[1-4]",
     "make_date(try_cast(left(s, 4) AS INT), try_cast(right(s, 1) AS INT) * 3, 1)", "mes"),
    ("ano_prefixo", r"(19|20)\d{2}[_-]\d+", "make_date(try_cast(left(s, 4) AS INT), 1, 1)", "ano"),
    ("ano_no_texto", r".*\b(19|20)\d{2}\b.*",
     r"make_date(try_cast(regexp_extract(s, '\b((19|20)\d{2})\b', 1) AS INT), 1, 1)", "ano"),
]
ORDEM_GRAO = {"dia": 0, "mes": 1, "ano": 2}


def _sub(sql, c):
    """Troca a variável `s` do SQL de FORMATOS pela coluna como texto limpo."""
    texto = "trim(ltrim(trim(\"" + c + "\"::VARCHAR), ''''))"
    return re.sub(r"\bs\b", lambda _: texto, sql)


def classifica(c, vals):
    """Formato que casa com >= 80% da amostra; 'mes_num' para coluna de mês 1..12."""
    vals = [str(v).strip().lstrip("'").strip() for v in vals if v is not None and str(v).strip()]
    if not vals:
        return None
    if re.search(r"mes|month", c.lower()) and all(re.fullmatch(r"(0?[1-9]|1[0-2])(\.0+)?", v) for v in vals):
        return "mes_num"
    for nome, rx, _, _ in FORMATOS:
        if sum(bool(re.fullmatch(rx, v)) for v in vals) >= 0.8 * len(vals):
            return nome
    return None


def sonda(ds, tb, cands):
    """Escolhe o formato pela amostra dos valores e mede. Devolve (valor, grao, colunas) ou None."""
    tipos = {}
    for c, _ in cands:
        try:
            vals = [r["v"] for r in duck(f'SELECT DISTINCT v FROM (SELECT "{c}"::VARCHAR AS v FROM {ds}.{tb} '
                                         f'WHERE "{c}" IS NOT NULL LIMIT 5000) LIMIT 40;')]
        except Exception:
            continue
        t = classifica(c, vals)
        if t:
            tipos[c] = t
    fmt = {n: (sql, g) for n, _, sql, g in FORMATOS}
    anos = [c for c, t in tipos.items() if t == "ano"]
    meses = [c for c, t in tipos.items() if t == "mes_num"]
    escolhas = []
    if anos and meses:
        a, m = (f'try_cast(try_cast("{x}" AS DOUBLE) AS INT)' for x in (anos[0], meses[0]))
        escolhas.append((f"make_date({a}, {m}, 1)", "mes", f"{anos[0]}, {meses[0]}"))
    for c, t in tipos.items():
        if t in fmt:
            escolhas.append((_sub(fmt[t][0], c), fmt[t][1], c))
    escolhas.sort(key=lambda x: ORDEM_GRAO[x[1]])  # estável: dentro do grão, a ordem do cartão
    for e, grao, cols in escolhas:
        v = duck(f"SELECT max(d) AS v FROM (SELECT {e} AS d FROM {ds}.{tb}) "
                 f"WHERE d <= current_date AND year(d) >= 1800;")[0]["v"]
        if v:
            v = str(v)[:10]
            return (v[:7] if grao == "mes" else v[:4] if grao == "ano" else v), grao, cols
    return None


def colunas_de_tempo(cartao, perfil):
    """(coluna, tipo) candidatas, na ordem de preferência."""
    cols = {c.lower(): (c, p.get("tipo", "")) for c, p in (perfil.get("colunas") or {}).items()}
    if not cols:
        return []
    tempo = (cartao or {}).get("tempo")
    citadas = []
    if isinstance(tempo, dict) and tempo.get("coluna"):
        citadas = [w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", str(tempo["coluna"])) if w.lower() in cols]
    if not citadas:
        citadas = [n for n in ("ano", "year", "mes", "month") + NOMES if n in cols]
    if not citadas:
        citadas = [c for c, (_, t) in cols.items() if re.match(r"DATE|TIMESTAMP", t)][:1]
    return [cols[c.lower()] for c in citadas]


def expressao(cands):
    """SQL de uma linha que devolve o máximo já sem futuro, e a granularidade."""
    nomes = {c.lower(): c for c, _ in cands}
    tipos = {c.lower(): t for c, t in cands}
    ano = nomes.get("ano") or nomes.get("year")
    mes = nomes.get("mes") or nomes.get("month")
    datas = [c for c, t in cands if re.match(r"DATE|TIMESTAMP", t)]
    if datas:
        c = datas[0]
        return f'max("{c}"::DATE) FILTER ("{c}"::DATE <= current_date)', "dia"
    if ano and mes:
        e = f'try_cast("{ano}" AS INT) * 100 + try_cast("{mes}" AS INT)'
        return f"max({e}) FILTER ({e} <= {HOJE.year * 100 + HOJE.month} AND try_cast(\"{mes}\" AS INT) BETWEEN 1 AND 12)", "mes"
    if ano:
        return f'max(try_cast("{ano}" AS INT)) FILTER (try_cast("{ano}" AS INT) <= {HOJE.year})', "ano"
    c, t = cands[0]
    if re.match(r"(BIG|SMALL|U)?INT|HUGEINT", t):  # aaaamm, como o inicio/fim do histórico do CNPJ
        return f'max("{c}") FILTER ("{c}" BETWEEN 190001 AND {HOJE.year * 100 + HOJE.month})', "mes"
    e = f'coalesce(try_cast("{c}" AS DATE), try_strptime("{c}", \'%d/%m/%Y\')::DATE)'
    return f"max({e}) FILTER ({e} <= current_date)", "dia"


def formata(v, grao):
    if v is None:
        return None
    s = str(v)
    if grao == "mes" and re.fullmatch(r"\d{6}", s):
        return f"{s[:4]}-{s[4:]}"
    return s[:10] if grao == "dia" else s


def uma(tarefa):
    ds, tb, cands = tarefa
    sql, grao = expressao(cands)
    try:
        v = duck(f"SELECT {sql} AS v FROM {ds}.{tb};")[0]["v"]
        if v is None:
            achado = sonda(ds, tb, cands)
            if achado:
                return f"{ds}.{tb}", {"ultima_data": achado[0], "grao": achado[1], "coluna": achado[2], "por": "sonda"}
        return f"{ds}.{tb}", {"ultima_data": formata(v, grao), "grao": grao, "coluna": ", ".join(c for c, _ in cands)}
    except Exception as e:
        return f"{ds}.{tb}", {"erro": str(e)[:200], "coluna": ", ".join(c for c, _ in cands)}


def grava_nos_cartoes(feito):
    por_ds = {}
    for k, r in feito.items():
        ds, tb = k.split(".", 1)
        if r.get("ultima_data"):
            por_ds.setdefault(ds, {})[tb] = r["ultima_data"]
    for ds, datas in por_ds.items():
        cp = PASTA / f"{ds}.yml"
        if not cp.exists():
            continue
        linhas = [l for l in cp.read_text().splitlines() if not re.match(r"    ultima_data: ", l)]
        out = []
        for l in linhas:
            out.append(l)
            m = re.match(r"  ([A-Za-z0-9_]+):\s*$", l)
            if m and m.group(1) in datas:
                out.append(f'    ultima_data: "{datas[m.group(1)]}"  # dado mais recente, gerado por scripts/gera_ultima_data.py')
        texto = "\n".join(out) + "\n"
        yaml.safe_load(texto)  # não grava cartão quebrado
        cp.write_text(texto)


def main(args):
    feito = {} if "--refaz" in args or not SAIDA.exists() else json.loads(SAIDA.read_text())
    if "--so-faltam" in args:  # remede só o que ficou sem data
        feito = {k: r for k, r in feito.items() if r.get("ultima_data")}
    tarefas = []
    for fp in sorted(PASTA.glob("*.perfil.yml")):
        ds = fp.name[:-len(".perfil.yml")]
        perfil = yaml.safe_load(fp.read_text())
        cp = PASTA / f"{ds}.yml"
        cartoes = (yaml.safe_load(cp.read_text()) or {}).get("tabelas", {}) if cp.exists() else {}
        for tb, p in perfil["tabelas"].items():
            if f"{ds}.{tb}" in feito or "erro" in p:
                continue
            cands = colunas_de_tempo(cartoes.get(tb), p)
            if cands:
                tarefas.append((ds, tb, cands))
    print(f"{len(tarefas)} tabelas a medir", flush=True)
    with ThreadPoolExecutor(4) as ex:
        for i, (k, r) in enumerate(ex.map(uma, tarefas), 1):
            feito[k] = r
            print(f"{i}/{len(tarefas)} {k}: {r.get('ultima_data') or r.get('erro')}", flush=True)
            if i % 25 == 0:
                SAIDA.write_text(json.dumps(feito, ensure_ascii=False, indent=0, sort_keys=True))
    SAIDA.write_text(json.dumps(feito, ensure_ascii=False, indent=0, sort_keys=True))
    grava_nos_cartoes(feito)


if __name__ == "__main__":
    main(sys.argv[1:])
