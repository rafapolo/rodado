#!/usr/bin/env python3
"""Perfil gerado das tabelas de um dataset -> docs/context/summaries/<dataset>.perfil.yml.

    python3 scripts/gera_perfil.py br_me_rais br_me_cnpj
    python3 scripts/gera_perfil.py --todos      # pula o dataset que já tem perfil; --refaz gera de novo
    python3 scripts/gera_perfil.py --limpa      # reaplica a regra de privacidade aos perfis já gerados

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
PESSOAL = re.compile(r"nome|razao|cpf|cnpj(?!_basico$)|documento|telefone|fax|ddd|email|logradouro|numero|complemento|bairro|cep|representante|endereco|favorecid|beneficiari|titular|_nis|^nis$|pis_pasep|matricula|placa|respons|^resp$|escriturador|candidato$|proponente|contratad|fornecedor|favorecid|company|importer|exporter|identifica|^nm_|_nm_|_nome|doador|socio|servidor$|individual|^name$|(^|_)(diretor|chefe|arbitro|gestor|relator|autor|juiz|advogado|procurador|treinador|tecnico|jogador|player|atleta|athlete|actor|ator|director|interessado|requerente|paciente|pessoa)(_|$)", re.I)
# pessoa pública: nos datasets de político, o nome de candidato e parlamentar pode aparecer; o de
# doador, fornecedor, servidor e assessor, e qualquer documento ou endereço, continua escondido
POLITICOS = {"br_tse_eleicoes", "br_tse_filiacao_partidaria", "politicos", "br_camara_dados_abertos",
             "br_senado_dados_abertos", "br_senado_dadosabertos", "br_senado_ceaps", "br_mp_pep"}
NOME_PUBLICO = re.compile(r"nome|candidato|parlamentar|deputado|senador|vereador|urna|autor|relator|presidente|^nm_|_nm_", re.I)
NUNCA_PUBLICO = re.compile(r"cpf|documento|titulo|telefone|fax|ddd|email|logradouro|endereco|numero|complemento|bairro|cep|_nis|^nis$|"
                           r"doador|fornecedor|favorecid|servidor|assessor|chefe|socio|beneficiari|contratad|filiado|eleitor", re.I)
TEXTO_LIVRE = 1000   # coluna de texto com mais distintos que isso: min e max são extremos alfabéticos, sem informação e com risco de ser nome
TOP_ATE = 50
CORTE = 120   # caracteres de min/max de texto; texto longo inteiro só incha o arquivo


def pessoal(ds, nome):
    if ds in POLITICOS and NOME_PUBLICO.search(nome) and not NUNCA_PUBLICO.search(nome):
        return False
    return bool(PESSOAL.search(nome))


def duck(sql, timeout=1800):
    # o timeout vale também no beelink: matar só o ssh local deixava o duckdb órfão lá, rodando por horas
    # (2026-10-27: dois SUMMARIZE de PNS e PIRLS a 100% de CPU, 11 h e 6 h depois de o script desistir deles)
    remoto = f"timeout -k 30 {timeout - 60} ~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"
    r = subprocess.run(["ssh", "beelink", remoto],
                       input="SET enable_progress_bar=false;\nSET threads=8;\n" + sql, capture_output=True, text=True,
                       errors="replace", timeout=timeout)
    if r.returncode == 124:
        raise subprocess.TimeoutExpired(remoto, timeout - 60)
    if r.returncode or "Error" in r.stderr:
        erro = [l for l in r.stderr.splitlines() if "Error" in l]
        raise RuntimeError(erro[0].split("\x1b[00m")[-1] if erro else f"duckdb saiu com {r.returncode} sem mensagem (memória?)")
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


def resumo_manual(ds, tb, q):
    """O que o SUMMARIZE devolve, sem o desvio-padrão, uma consulta por coluna."""
    out = []
    for c in duck(f"DESCRIBE {ds}.{tb};"):
        n, t = c["column_name"], c["column_type"]
        numerica = re.match(r"(BIG|SMALL|TINY|U)?INT|DOUBLE|FLOAT|DECIMAL|HUGEINT", t)
        extra = (f", avg(\"{n}\") avg, quantile_cont(\"{n}\", 0.25) q25, quantile_cont(\"{n}\", 0.5) q50, "
                 f"quantile_cont(\"{n}\", 0.75) q75") if numerica else ", NULL avg, NULL q25, NULL q50, NULL q75"
        r = duck(f"SELECT min(\"{n}\")::VARCHAR min, max(\"{n}\")::VARCHAR max, approx_count_distinct(\"{n}\") approx_unique, "
                 f"100.0 * count(*) FILTER (\"{n}\" IS NULL) / greatest(count(*), 1) null_percentage{extra} FROM {q};")[0]
        out.append({"column_name": n, "column_type": t, **r})
    return out


def perfil_tabela(ds, tb, linhas):
    if not linhas:  # view: o catálogo guarda 0 linhas
        linhas = duck(f"SELECT count(*) n FROM {ds}.{tb};", timeout=3600)[0]["n"]
    q, como = fonte(ds, tb, linhas)
    try:
        resumo = duck(f"SUMMARIZE SELECT * FROM {q};", timeout=3600)
    except RuntimeError as e:
        # o SUMMARIZE estoura no desvio-padrão de double enorme, e sem memória em tabela larga:
        # refaz coluna a coluna, sem desvio, numa amostra menor
        if "STDDEV" not in str(e) and "sem mensagem" not in str(e):
            raise
        if "sem mensagem" in str(e):
            q, como = f"(SELECT * FROM {q} USING SAMPLE 200000 ROWS (reservoir, 42))", como + ", reduzida a 200 mil linhas (faltou memória)"
        resumo = resumo_manual(ds, tb, q)
    colunas, poucas, geo = {}, [], []
    for c in resumo:
        nome, tipo = c["column_name"], c["column_type"]
        p = {"tipo": tipo, "nulos_pct": num(c["null_percentage"]), "distintos_aprox": num(c["approx_unique"])}
        if pessoal(ds, nome):
            p["pessoal"] = "só contagens: valores seriam dado pessoal"
        elif tipo.startswith(("GEOMETRY", "BLOB")):
            # min/max de geometria é um polígono inteiro em WKT: o perfil do geobr chegou a 54 MB
            if tipo.startswith("GEOMETRY"):
                geo.append(nome)
        else:
            corta = lambda v: v[:CORTE] + "…" if isinstance(v, str) and len(v) > CORTE else v
            p["min"], p["max"] = corta(c["min"]), corta(c["max"])
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
    if geo:
        # no lugar do min/max: tipos de geometria, caixa envolvente e pontos por linha
        sel = ", ".join(f"list(DISTINCT ST_GeometryType(\"{g}\")::VARCHAR) \"{g}_tipos\", "
                        f"[min(ST_XMin(\"{g}\")), min(ST_YMin(\"{g}\")), max(ST_XMax(\"{g}\")), max(ST_YMax(\"{g}\"))] \"{g}_caixa\", "
                        f"avg(ST_NPoints(\"{g}\")) \"{g}_pontos\"" for g in geo)
        r = duck(f"LOAD spatial;\nSELECT {sel} FROM {q};", timeout=3600)[0]
        for g in geo:
            colunas[g]["geometrias"] = sorted(t for t in r[f"{g}_tipos"] or [] if t)
            colunas[g]["caixa_xmin_ymin_xmax_ymax"] = [round(v, 4) if v is not None else None for v in r[f"{g}_caixa"] or []]
            colunas[g]["pontos_media"] = num(r[f"{g}_pontos"])
    return {"linhas": linhas, "fonte_do_perfil": como, "colunas": colunas}


def limpa(arquivo):
    """Aplica a regra de privacidade a um perfil já gerado, sem consultar o banco."""
    doc = yaml.safe_load(arquivo.read_text())
    for t in doc["tabelas"].values():
        for nome, p in (t.get("colunas") or {}).items():
            texto = re.match(r"VARCHAR|GEOMETRY|BLOB", p.get("tipo", ""))
            if pessoal(doc["dataset"], nome):
                for k in ("min", "max", "top", "media", "quartis"):
                    p.pop(k, None)
                p["pessoal"] = "só contagens: valores seriam dado pessoal"
            elif texto and (p.get("distintos_aprox") or 0) > TEXTO_LIVRE:
                p.pop("min", None); p.pop("max", None)
    arquivo.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False, width=140, default_flow_style=None))


def datasets():
    return [x["dataset"] for x in duck("SELECT DISTINCT dataset FROM _rodado_metadata WHERE source <> 'view_only' AND dataset NOT LIKE '\\_local%' ESCAPE '\\' ORDER BY 1;")]  # _local_*: infra local, fora do repo público


def main(args):
    SAIDA.mkdir(parents=True, exist_ok=True)
    if "--limpa" in args:
        for f in sorted(SAIDA.glob("*.perfil.yml")):
            limpa(f)
        return
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
