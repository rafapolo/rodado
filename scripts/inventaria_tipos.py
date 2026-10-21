#!/usr/bin/env python3
"""Inventário de colunas STRING que poderiam ter outro tipo — só leitura, nada é alterado.

Para cada coluna VARCHAR de cada parquet do beelink, mede pelos valores (não pelo nome)
se ela inteira cabe num número (inteiro, decimal com vírgula ou com ponto, milhar
pt-BR ou en), numa data/timestamp (ISO, dd/mm/aaaa, aaaammdd, ddmmaaaa) ou num
booleano. Duas passadas:

  A. amostra (tabela inteira até LIMITE_CHEIO linhas; acima, ~25 mil linhas de até 12
     arquivos espalhados) -> estatísticas por padrão -> proposta de tipo + expressão
  B. só nas colunas com proposta, varredura completa: quantos valores não vazios a
     expressão de conversão devolveria NULL (`falhas`) e quais são os mais comuns

`seguro` exige falhas == 0 na tabela inteira, precisão cabendo no tipo (≤15 dígitos
significativos em DOUBLE, ≤18 em BIGINT) e data plausível. Marcadores como '-', 'X',
'...', 'NA' NÃO são tratados como nulo: viram falha, porque convertê-los em NULL apaga
a diferença entre "sem dado" e "sigilo"/"não se aplica" — quem decide é a revisão.
Inteiro com zero à esquerda, largura fixa ou nome de código (cnpj, cep, id_, cod...)
fica como `codigo`: virar número perde o zero e quebra join com a outra ponta STRING.

    python3 scripts/inventaria_tipos.py --roda      # sobe e dispara no beelink (nohup, retomável)
    python3 scripts/inventaria_tipos.py --status    # quantas tabelas já foram
    python3 scripts/inventaria_tipos.py --analisa   # baixa o JSONL e escreve o relatório
"""
import json, os, glob, subprocess, sys, collections

HOST = os.environ.get("BEELINK_HOST", "beelink")
REMOTO_PY = "~/inventaria_tipos_remoto.py"
REMOTO_OUT = "~/inventaria_tipos.jsonl"
LOCAL_OUT = "/tmp/inventaria_tipos.jsonl"
RELATORIO = "docs/context/tipos_propostos.json"

REMOTO = r'''
import duckdb, os, glob, json, re, sys, threading, time
R = os.path.expanduser("~/rodado")
OUT = os.environ.get("OUT") or os.path.expanduser("~/inventaria_tipos.jsonl")
SO = set(filter(None, os.environ.get("SO", "").split(",")))  # teste: SO=ds.tb,ds.tb
LIMITE_CHEIO = 5_000_000
LOTE = 40
TIMEOUT = 1800

con = duckdb.connect()
con.execute("SET threads=4; SET memory_limit='6GB'; SET preserve_insertion_order=false")
con.execute(f"SET temp_directory='{os.path.expanduser('~/duckdb_tmp')}'")

def q(sql):
    t = threading.Timer(TIMEOUT, con.interrupt); t.start()
    try: return con.execute(sql).fetchall()
    finally: t.cancel()

def ident(c): return '"' + c.replace('"', '""') + '"'
def lit(s): return "'" + s.replace("'", "''") + "'"

# padrões (sobre trim(valor), vazio excluído)
NUM_BR = r"[+-]?(\d+|\d{1,3}(\.\d{3})+)(,\d+)?|[+-]?,\d+"
NUM_US = r"[+-]?(\d+|\d{1,3}(,\d{3})+)(\.\d+)?|[+-]?\.\d+|[+-]?\d+(\.\d+)?[eE][+-]?\d+"
AMB = r"[+-]?[1-9]\d{0,2}[.,]\d{3}"
P = {
  "int": r"[+-]?\d+", "lz": r"[+-]?0\d+",
  "br": NUM_BR, "us": NUM_US, "amb": AMB,
  "iso_d": r"\d{4}-\d{2}-\d{2}",
  "iso_dt": r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?",
  "br_d": r"\d{1,2}/\d{1,2}/\d{4}",
  "br_dt": r"\d{1,2}/\d{1,2}/\d{4}[ T]\d{1,2}:\d{2}(:\d{2})?",
  "br_d2": r"\d{1,2}/\d{1,2}/\d{2}", "d6": r"\d{6}",
}
BOOL = "('S','N','SIM','NAO','NÃO','TRUE','FALSE','T','F','Y','YES','NO','VERDADEIRO','FALSO')"
ANO_OK = "BETWEEN 1850 AND 2100"

def aggs(x):
    a = [f"count({x})", f"count_if({x} = '')"]
    a += [f"count_if(regexp_full_match({x}, {lit(p)}))" for p in P.values()]
    a += [f"count_if(regexp_full_match({x}, '\\d{{8}}') AND year(try_strptime({x}, '%Y%m%d')) {ANO_OK})",
          f"count_if(regexp_full_match({x}, '\\d{{8}}') AND year(try_strptime({x}, '%d%m%Y')) {ANO_OK})",
          f"count_if(upper({x}) IN {BOOL})",
          f"max(length(ltrim(regexp_replace({x}, '[^0-9]', '', 'g'), '0'))) FILTER (regexp_full_match({x}, '[+-]?[0-9.,]+'))",
          f"min(length({x})) FILTER ({x} <> '')", f"max(length({x}))",
          f"approx_count_distinct({x})",
          f"min({x}) FILTER ({x} <> '')", f"max({x})"]
    return a
CHAVES = ["nn", "vazio", *P.keys(), "d8_ymd", "d8_dmy", "bool", "sig", "minlen", "maxlen", "ndist", "exmin", "exmax"]

def stats(src, cols):
    out = {}
    for i in range(0, len(cols), LOTE):
        lote = cols[i:i+LOTE]
        proj = ", ".join(f"trim(CAST({ident(c)} AS VARCHAR)) AS c{j}" for j, c in enumerate(lote))
        sel = ", ".join(", ".join(aggs(f"c{j}")) for j in range(len(lote)))
        row = q(f"SELECT count(*), {sel} FROM (SELECT {proj} FROM {src})")[0]
        n, vals = row[0], row[1:]
        k = len(CHAVES)
        for j, c in enumerate(lote):
            s = dict(zip(CHAVES, vals[j*k:(j+1)*k])); s["n"] = n
            out[c] = s
    return out

NOME_DATA = re.compile(r"(^|_)(data|dt|dta|dat|date|dia|nascimento|nasc|inicio|fim|validade|abertura|emissao|vencimento|inclusao|alteracao|criacao|atualizacao|publicacao|registro|obito|entrada|saida)|^(dt|data|dat)[a-z]", re.I)
NOME_COD = re.compile(r"^(id|cod|codigo|cd|co|nu|num|numero|nr|no|cnpj|cpf|cep|cnae|cbo|cid|ncm|sh\d|sigla|matricula|registro|inscricao|processo|protocolo|chave|ibge|setor|tse|titulo|pis|nis|renavam|placa|telefone|fone|ddd|crm|cns|cnes|siafi|uasg|ug|orgao|natureza|tipo|situacao|classe|grupo|categoria|subclasse|secao|divisao)|(_id|^id_|cnpj|cpf|cep|cnae|ibge|processo|codigo|_cod|cod_|_cd$|_nu$|siafi|cnes|_cns)", re.I)
NOME_TEMPO = re.compile(r"^(ano|mes|dia|trimestre|semestre|semana|bimestre)(_[a-z_]*)?$|(_ano|_mes)$", re.I)

def propoe(c, s):
    """-> (veredito, tipo, expressao com {x}) a partir das estatísticas."""
    k = (s["nn"] or 0) - (s["vazio"] or 0)
    if k == 0: return ("vazia", None, None)
    def tem(n): return (s[n] or 0) == k
    datas = []
    # datas: formatos sem ambiguidade de cara; aaaammdd/ddmmaaaa exigem nome de data
    if tem("iso_d"): datas.append(("DATE", "try_strptime({x}, '%Y-%m-%d')::DATE"))
    elif (s["iso_d"] or 0) + (s["iso_dt"] or 0) >= k and s["iso_dt"]: datas.append(("TIMESTAMP", "TRY_CAST({x} AS TIMESTAMP)"))
    if tem("br_d"): datas.append(("DATE", "try_strptime({x}, '%d/%m/%Y')::DATE"))
    elif (s["br_d"] or 0) + (s["br_dt"] or 0) >= k and s["br_dt"]:
        datas.append(("TIMESTAMP", "try_strptime({x}, ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d/%m/%Y'])"))
    nome_data = bool(NOME_DATA.search(c))
    if nome_data and tem("d8_ymd") and not tem("d8_dmy"): datas.append(("DATE", "try_strptime({x}, '%Y%m%d')::DATE"))
    if nome_data and tem("d8_dmy") and not tem("d8_ymd"): datas.append(("DATE", "try_strptime({x}, '%d%m%Y')::DATE"))
    if datas: return ("candidato", *datas[0])
    if nome_data and (tem("br_d2") or tem("d6") or tem("d8_ymd") or
                      (s["d6"] or 0) + (s["d8_ymd"] or 0) + (s["d8_dmy"] or 0) >= k and s["d6"]):
        return ("ambiguo", "DATE?", None)  # ano de 2 dígitos, ddmmaa x aaaamm, ou formatos misturados

    if tem("int"):
        if s["lz"] or NOME_COD.search(c) and not NOME_TEMPO.search(c) or \
           (s["minlen"] == s["maxlen"] and (s["maxlen"] or 0) >= 4 and not NOME_TEMPO.search(c)):
            return ("codigo", "BIGINT?", None)
        if (s["sig"] or 0) > 18: return ("revisar", "HUGEINT?", None)
        return ("candidato", "INTEGER" if (s["sig"] or 0) <= 9 else "BIGINT", "TRY_CAST({x} AS BIGINT)")
    br, us = tem("br"), tem("us")
    if br or us:
        if s["lz"]: return ("codigo", "DOUBLE?", None)
        if br and us: return ("ambiguo", "DOUBLE?", None)  # só '1.234'/'1,234': milhar ou decimal?
        tipo = "DOUBLE" if (s["sig"] or 0) <= 15 else "DECIMAL?"
        if br: return ("candidato", tipo, "TRY_CAST(replace(replace({x}, '.', ''), ',', '.') AS DOUBLE)")
        return ("candidato", tipo, "TRY_CAST(replace({x}, ',', '') AS DOUBLE)")
    if tem("bool") and (s["ndist"] or 0) <= 3: return ("booleano", "BOOLEAN", None)
    # quase: um padrão cobre >=90% — os outros 10% são exatamente o que se perderia
    melhor = max(("br", "us", "iso_d", "iso_dt", "br_d", "br_dt"), key=lambda n: s[n] or 0)
    if (s[melhor] or 0) >= 0.9 * k and not s["lz"]:
        expr = {"br": "TRY_CAST(replace(replace({x}, '.', ''), ',', '.') AS DOUBLE)",
                "us": "TRY_CAST(replace({x}, ',', '') AS DOUBLE)",
                "iso_d": "try_strptime({x}, '%Y-%m-%d')::DATE", "iso_dt": "TRY_CAST({x} AS TIMESTAMP)",
                "br_d": "try_strptime({x}, '%d/%m/%Y')::DATE",
                "br_dt": "try_strptime({x}, ['%d/%m/%Y %H:%M:%S', '%d/%m/%Y %H:%M', '%d/%m/%Y'])"}[melhor]
        tipo = "DOUBLE" if melhor in ("br", "us") else "DATE" if melhor.endswith("_d") else "TIMESTAMP"
        return ("quase", tipo, expr)
    # nome de data e mais da metade com cara de data, mas com marcador/formato misturado
    parece = sum(s[n] or 0 for n in ("iso_d", "iso_dt", "br_d", "br_dt", "br_d2", "d6", "d8_ymd", "d8_dmy"))
    if nome_data and parece >= 0.5 * k: return ("revisar", "DATE?", None)
    return ("texto", None, None)

def confere(src, c, tipo, expr):
    """passada B: tabela inteira, falhas e valores que falham"""
    x = f"trim(CAST({ident(c)} AS VARCHAR))"
    e = expr.format(x=x)
    extra = ""
    if tipo in ("DATE", "TIMESTAMP"):
        extra = f", min({e})::VARCHAR, max({e})::VARCHAR, count_if(year({e}) NOT {ANO_OK})"
        if tipo == "TIMESTAMP": extra += f", count_if({e}::TIME <> TIME '00:00:00')"
    else:
        extra = f", min({e}), max({e}), count_if({e} <> round({e}))"
    r = q(f"SELECT count_if({x} <> ''), count_if({x} <> '' AND ({e}) IS NULL){extra} FROM {src}")[0]
    d = {"reais": r[0], "falhas": r[1], "min": r[2], "max": r[3]}
    if tipo in ("DATE", "TIMESTAMP"):
        d["ano_implausivel"] = r[4]
        if tipo == "TIMESTAMP": d["com_hora"] = r[5]
    else:
        d["nao_inteiros"] = r[4]
    if d["falhas"]:
        d["top_falhas"] = [[v, n] for v, n in q(
            f"SELECT {x} v, count(*) n FROM {src} WHERE {x} <> '' AND ({e}) IS NULL GROUP BY v ORDER BY n DESC LIMIT 15")]
    return d

feitos = set()
if os.path.exists(OUT):
    for l in open(OUT):
        try:
            j = json.loads(l)
            if j.get("fim"): feitos.add(j["tabela"])
        except Exception: pass

f = open(OUT, "a")
def w(o): f.write(json.dumps(o, ensure_ascii=False, default=str) + "\n"); f.flush()

for ds in sorted(os.listdir(R)):
    if ds.startswith(('_', '.')) or not os.path.isdir(f"{R}/{ds}"): continue
    for tb in sorted(os.listdir(f"{R}/{ds}")):
        nome = f"{ds}.{tb}"
        if nome in feitos or SO and nome not in SO: continue
        p = f"{R}/{ds}/{tb}"
        arqs = sorted(glob.glob(f"{p}/**/*.parquet", recursive=True))
        if not arqs: continue
        t0 = time.time()
        try:
            full = f"read_parquet({lit(p + '/**/*.parquet')}, union_by_name=true, hive_partitioning=false)"
            linhas = q(f"SELECT sum(num_rows) FROM parquet_file_metadata({lit(p + '/**/*.parquet')})")[0][0] or 0
            cols = [r[0] for r in q(f"DESCRIBE SELECT * FROM {full}") if r[1] == "VARCHAR"]
            if not cols:
                w({"tabela": nome, "fim": True, "linhas": linhas, "varchar": 0}); continue
            cheio = linhas <= LIMITE_CHEIO
            if cheio:
                amostra = full
            else:
                pegos = [arqs[round(i * (len(arqs) - 1) / 11)] for i in range(12)] if len(arqs) > 12 else arqs
                pegos = list(dict.fromkeys(pegos))
                lim = 300_000 // len(pegos)
                amostra = "(" + " UNION ALL BY NAME ".join(
                    f"(SELECT * FROM read_parquet({lit(a)}, hive_partitioning=false) LIMIT {lim})" for a in pegos) + ")"
            st = stats(amostra, cols)
            for c in cols:
                s = st[c]
                ver, tipo, expr = propoe(c, s)
                o = {"tabela": nome, "coluna": c, "linhas": linhas, "amostra": not cheio,
                     "veredito": ver, "tipo": tipo, "expr": expr}
                if ver != "texto" or s["nn"]:
                    o["stats"] = {k: s[k] for k in CHAVES if s[k]}
                if expr:
                    try: o["conferencia"] = confere(full, c, tipo, expr)
                    except Exception as e: o["erro_conferencia"] = str(e)[:200]
                w(o)
            w({"tabela": nome, "fim": True, "linhas": linhas, "varchar": len(cols), "seg": round(time.time() - t0, 1)})
        except Exception as e:
            w({"tabela": nome, "erro": str(e)[:300]})
print("FIM", file=sys.stderr)
'''


def roda():
    subprocess.run(["ssh", HOST, f"cat > {REMOTO_PY}"], input=REMOTO, text=True, check=True)
    subprocess.run(["ssh", HOST, f"nohup nice python3 {REMOTO_PY} > ~/inventaria_tipos.log 2>&1 &"], check=True)
    print("disparado; acompanhe com --status")


def status():
    subprocess.run(["ssh", HOST, f"grep -c '\"fim\": true' {REMOTO_OUT}; grep -c '\"erro\"' {REMOTO_OUT}; "
                    f"tail -c 300 ~/inventaria_tipos.log; pgrep -f inventaria_tipos_remoto >/dev/null && echo rodando || echo parado"])


def seguro(o):
    c = o.get("conferencia")
    if o["veredito"] != "candidato" or not c or c["falhas"]: return False
    if o["tipo"] in ("DATE", "TIMESTAMP") and c.get("ano_implausivel"): return False
    return o["tipo"] in ("DATE", "TIMESTAMP", "INTEGER", "BIGINT", "DOUBLE")


def analisa():
    with open(LOCAL_OUT, "w") as f:
        subprocess.run(["ssh", HOST, f"cat {REMOTO_OUT}"], stdout=f, check=True)
    cols, erros, tabelas = [], [], 0
    for l in open(LOCAL_OUT):
        o = json.loads(l)
        if o.get("fim"): tabelas += 1
        elif "erro" in o: erros.append(o)
        else: cols.append(o)
    for o in cols:
        if seguro(o): o["veredito"] = "seguro"
        elif o["veredito"] == "candidato": o["veredito"] = "candidato_com_falhas"
        # TIMESTAMP sem hora nenhuma vira DATE
        c = o.get("conferencia") or {}
        if o["veredito"] == "seguro" and o["tipo"] == "TIMESTAMP" and c.get("com_hora") == 0:
            o["tipo"] = "DATE"; o["expr"] = "(" + o["expr"] + ")::DATE"
        # DOUBLE que só tem inteiro
        if o["veredito"] == "seguro" and o["tipo"] == "DOUBLE" and c.get("nao_inteiros") == 0:
            o["obs"] = "só valores inteiros; BIGINT também serve"
    # quem grava cada tabela: o scraper (local, fora do git) ou o sync do espelho
    origem = dict(json.loads(l) for l in subprocess.run(
        ["ssh", HOST, "~/bin/duckdb -readonly -noheader -list ~/rodado/basedosdados.duckdb"],
        input="SET enable_progress_bar=false; SELECT json_array(dataset || '.' || \"table\", source_type) FROM _rodado_metadata;",
        text=True, capture_output=True, check=True).stdout.splitlines() if l.startswith("["))
    fontes = {f: open(f, errors="ignore").read() for d in ("scripts/scrap", "scripts/sync")
              if os.path.isdir(d) for f in sorted(glob.glob(f"{d}/**/*.*", recursive=True))
              if f.endswith((".py", ".ts", ".sh"))}
    for o in cols:
        ds, tb = o["tabela"].split(".", 1)
        o["origem"] = origem.get(o["tabela"])
        o["scraper"] = [f for f, txt in fontes.items() if ds in txt and tb in txt] or \
                       [f for f, txt in fontes.items() if ds in txt]
    por = collections.Counter(o["veredito"] for o in cols)
    print(f"tabelas: {tabelas}  colunas VARCHAR: {len(cols)}  erros: {len(erros)}")
    for k, v in por.most_common(): print(f"  {k:22} {v}")
    tipos = collections.Counter(o["tipo"] for o in cols if o["veredito"] == "seguro")
    print("seguro por tipo:", dict(tipos))
    rel = {"colunas": [o for o in cols if o["veredito"] not in ("texto", "vazia")],
           "resumo": dict(por), "seguro_por_tipo": dict(tipos), "erros": erros}
    json.dump(rel, open(RELATORIO, "w"), ensure_ascii=False, indent=1, default=str)
    print("->", RELATORIO)


APLICAR = "docs/context/tipos_aplicar.json"
QUANT = r"(quantidade|qtd|qtde|qt_|total|numero_de|num_de|^n_|populacao|valor|^vl|vlr|preco|custo|saldo|receita|despesa|montante|^ano$|^ano_|_ano$|^mes$|^mes_|_mes$|(^|_)idade|area|peso|altura|volume|potencia|capacidade|extensao|distancia|duracao|dias|horas|minutos|percent|taxa|indice|media|soma|contagem|vagas|leitos|matriculas|alunos|votos|eleitores|habitantes|pessoas|domicilios|obitos|nascidos|casos|empregos|vinculos)"


def seleciona():
    """Do inventário, só o que entra nesta passada: tabelas raspadas, `seguro`, fora de
    toda chave/código curado. Grava APLICAR com o motivo de cada exclusão."""
    import re, yaml
    rel = json.load(open(RELATORIO))
    cod = set(); cod_tab = set()
    b = yaml.safe_load(open("docs/context/bridges.yaml"))
    cod |= {k.lower() for k in (b.get("concepts") or {})} | {k.lower() for k in (b.get("coded_differently") or {})}
    cod |= {k.lower() for k in (b.get("false_friends") or {})}
    for al in (b.get("concept_aliases") or {}).values(): cod |= {k.lower() for k in al}
    jk = open("docs/context/join_keys.md").read()
    cod |= {m.lower() for m in re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", jk)}
    for e in yaml.safe_load(open("docs/context/column_codes.yaml"))["entradas"]:
        cod_tab |= {f"{e['tabela']}.{c}".lower() for c in e.get("colunas", [])}
    for t, cs in json.load(open("docs/context/dicionario_coverage.json"))["tables"].items():
        cod_tab |= {f"{t}.{c}".lower() for c in cs}
    sds = json.load(open("docs/context/schema_dict_status.json"))["columns"]
    sds = {k.lower(): v["label"] for k, v in sds.items()}
    nome_cod = re.compile(r"^(id|cod|codigo|cd|co|nu|num|numero|nr|cnpj|cpf|cep|cnae|cbo|cid|ncm|sigla|sg|matricula|registro|inscricao|processo|protocolo|chave|ibge|setor|pis|nis|renavam|placa|telefone|fone|ddd|crm|cns|cnes|siafi|uasg|ug|tipo|tp|situacao|classe|grupo|categoria|cs|in|st|fl|flag)(_|$)|(_id|cnpj|cpf|cep|cnae|ibge|processo|codigo|_cod|cod_|_cd$|_nu$|siafi|cnes|_cns|_tp$|_tipo$)", re.I)
    quant = re.compile(QUANT, re.I)
    sim, nao = [], collections.Counter()
    for o in rel["colunas"]:
        if o["veredito"] != "seguro": continue
        c, chave = o["coluna"], f"{o['tabela']}.{o['coluna']}".lower()
        motivo = None
        if o.get("origem") == "mirror": motivo = "espelho BdD (fica para o sync do espelho)"
        elif chave in cod_tab: motivo = "codigo curado (column_codes/dicionario)"
        elif o["tipo"] in ("DATE", "TIMESTAMP"): pass
        elif c.lower() in cod: motivo = "chave/conceito em bridges ou join_keys"
        elif nome_cod.search(c): motivo = "nome de codigo"
        elif sds.get(chave) in ("padrao_externo", "documentado_em_outro_lugar", "nao_verificado") and not quant.search(c):
            motivo = f"schema_dict_status={sds.get(chave)}"
        elif o["tipo"] in ("INTEGER", "BIGINT") and not quant.search(c): motivo = "inteiro sem nome de quantidade (provavel codigo)"
        elif o["tipo"] == "DOUBLE" and (o.get("conferencia") or {}).get("nao_inteiros") == 0 and not quant.search(c):
            motivo = "DOUBLE so com inteiros e sem nome de quantidade"
        if motivo: nao[motivo] += 1; o["excluido"] = motivo
        else: sim.append(o)
    print("aplicar:", len(sim), "colunas em", len({o["tabela"] for o in sim}), "tabelas;",
          dict(collections.Counter(o["tipo"] for o in sim)))
    for k, v in nao.most_common(): print(f"  fora: {v:6}  {k}")
    json.dump(sim, open(APLICAR, "w"), ensure_ascii=False, indent=1, default=str)
    print("->", APLICAR)


if __name__ == "__main__":
    {"--roda": roda, "--status": status, "--analisa": analisa, "--seleciona": seleciona}.get(sys.argv[1] if len(sys.argv) > 1 else "", lambda: print(__doc__))()
