#!/usr/bin/env python3
"""Validação cruzada cartão × perfil e sugestões de cartão a partir do perfil. Só lê; nunca escreve em
`summaries/*.yml` nem em `*.perfil.yml`.

    python3 scripts/valida_cartao_perfil.py                  # avisos de todos os datasets, resumo por tipo
    python3 scripts/valida_cartao_perfil.py br_bcb_agencia   # só um dataset, avisos linha a linha
    python3 scripts/valida_cartao_perfil.py --detalhe        # todos, linha a linha
    python3 scripts/valida_cartao_perfil.py --sugestoes      # grava docs/context/summaries/_sugestoes.json
    python3 scripts/valida_cartao_perfil.py --json avisos.json   # avisos em JSON (para filtrar)

Avisos (nunca erro; saída 0):
  literal_ausente_do_top   literal de `filtros_tipicos` ('x', IN ('x','y'), 'x' ou 'y') que não está no `top`
                           da coluna no perfil
  literal_difere_em_caixa  o literal só existe no top com outra caixa/espaços (o filtro de igualdade erra)
  coluna_inexistente       coluna citada em chave, tempo, territorio, medidas ou filtros_tipicos que não é
                           coluna do perfil
  coluna_100_nula          coluna que o cartão manda usar e que está 100% nula no perfil
Cada aviso é `forte` quando o perfil é da tabela inteira e `brando` quando é de uma partição ou de uma
amostra (o top é da última partição/amostra, então o literal de outro ano pode faltar sem estar errado; a
coluna pode ser nula só naquele ano). Coluna `pessoal` no perfil não tem top: não gera aviso de literal.

Sugestões (`_sugestoes.json`, sempre `rascunho: true`, nunca medido, só de perfil da tabela inteira):
  cobertura   min–max de `ano`/coluna DATE do perfil, com `diverge_do_cartao` quando o cartão cita outro intervalo
  chave       colunas únicas sozinhas (distintos_aprox >= 97% das linhas, sem nulos); chave composta o
              perfil não enxerga
Rodar depois de `gera_perfil.py` e depois de revisar cartões. Pode ser chamado no fim do `gera_perfil.py`.
"""
import argparse, collections, datetime, json, re, sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
SUM = RAIZ / "docs" / "context" / "summaries"
SQL_PALAVRAS = set("""count sum avg min max distinct as and or not in is null between case when then else end like ilike
select from where group by order having over partition filter cast date year month extract coalesce nullif
round abs length substr substring lower upper concat true false limit asc desc por de do da no na em para com sem
ou e a o os as um uma ao dos das""".split())
SEM_COLUNA = {"nenhuma", "nenhum", "sem", "nao", "não", "n/a", "arquivo", "nome_coluna", "colunas"}
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def carrega(p):
    try:
        return yaml.safe_load(p.read_text()) or {}
    except Exception as e:
        print(f"aviso: {p.name} ilegível ({e})", file=sys.stderr)
        return {}


def brando(fonte):
    return "partição" in str(fonte) or "partição" in str(fonte).replace("particao", "partição") or str(fonte).startswith("amostra")


def literais(filtro):
    """[(coluna, literal)] de `col = 'x'`, `col IN ('x','y')` e `col = 'x' ou 'y'`."""
    saida = []
    for m in re.finditer(r"\b([A-Za-z_]\w*)\s*(?:=|IN\s*\()\s*((?:'[^']*'(?:\s*(?:,|ou|or|OR)\s*)?)+)", filtro):
        for lit in re.findall(r"'([^']*)'", m.group(2)):
            saida.append((m.group(1), lit))
    return saida


def cols_da_chave(chave):
    if not chave:
        return []
    cab = re.split(r"[(:;.]| — ", chave, 1)[0]
    toks = [t.strip() for t in re.split(r",| e ", cab)]
    return [t for t in toks if re.fullmatch(IDENT, t) and t.lower() not in SEM_COLUNA]


def cols_da_expressao(expr):
    expr = re.sub(r"'[^']*'", " ", expr or "")
    expr = re.sub(r"\bAS\s+\w+", " ", expr, flags=re.I)
    saida = []
    for m in IDENT.finditer(expr):
        t = m.group(0)
        resto = expr[m.end():].lstrip()
        if t.lower() in SQL_PALAVRAS or resto.startswith("(") or t.isdigit():
            continue
        if "_" in t or re.search(r"[A-Z]", t):  # só o que parece nome de coluna; prosa minúscula fica de fora
            saida.append(t)
    return saida


def citacoes(t):
    """[(campo, coluna)] que o cartão manda usar."""
    c = []
    for col in cols_da_chave(t.get("chave")):
        c.append(("chave", col))
    tempo = t.get("tempo") or {}
    for col in re.split(r",|/| e | \+ ", str(tempo.get("coluna") or "")):
        col = col.strip()
        if re.fullmatch(IDENT, col) and col.lower() not in SEM_COLUNA:
            c.append(("tempo", col))
    terr = (t.get("territorio") or {}).get("colunas") or {}
    for col in terr:
        c.append(("territorio", str(col)))
    for m in t.get("medidas") or []:
        if m.get("coluna"):
            for col in re.split(r",", str(m["coluna"])):
                col = col.strip()
                if re.fullmatch(IDENT, col) and col.lower() not in SEM_COLUNA:
                    c.append(("medidas", col))
        elif m.get("expressao"):
            for col in cols_da_expressao(m["expressao"]):
                c.append(("medidas", col))
    for f in t.get("filtros_tipicos") or []:
        for col, _ in literais(str(f)):
            if "_" in col or re.search(r"[a-z][A-Z]", col) or (col.isupper() and len(col) > 2):  # coluna em minúscula sem "_" é quase sempre palavra da prosa
                c.append(("filtros_tipicos", col))
    return c


def valida(ds, cartao, perfil):
    av = []
    for tab, t in (cartao.get("tabelas") or {}).items():
        p = (perfil.get("tabelas") or {}).get(tab)
        if not p or not p.get("colunas"):
            continue
        sev = "brando" if brando(p.get("fonte_do_perfil")) else "forte"
        cols = p["colunas"]
        low = {k.lower(): k for k in cols}

        def aviso(tipo, msg, s=sev):
            av.append({"dataset": ds, "tabela": tab, "tipo": tipo, "gravidade": s, "msg": msg})

        vistos = set()
        for campo, col in citacoes(t):
            if (campo, col) in vistos:
                continue
            vistos.add((campo, col))
            if re.search(r"xxx|N+$|\.|\*", col) or col.lower() in SEM_COLUNA or len(col) <= 2:  # molde de nome (vNNNNN, v05xxx), aninhado ou prosa
                continue
            real = low.get(col.lower())
            if real is None:
                aviso("coluna_inexistente", f"{campo}: `{col}` não está no perfil", "forte")
            else:
                if cols[real].get("nulos_pct") == 100:
                    aviso("coluna_100_nula", f"{campo}: `{real}` está 100% nula no perfil ({p.get('fonte_do_perfil')})")
        for f in t.get("filtros_tipicos") or []:
            for col, lit in literais(str(f)):
                real = low.get(col.lower())
                top = (cols.get(real) or {}).get("top") if real else None
                if not top:
                    continue
                vals = [str(v[0]) for v in top]
                if lit in vals or (lit.endswith("…") and any(v.startswith(lit[:-1]) for v in vals)):
                    continue
                # o top tem no máximo 10 valores: ausente só prova erro quando o top cobre todos os distintos
                gr = sev if (cols[real].get("distintos_aprox") or 0) <= len(vals) else "brando"
                norm = {re.sub(r"\s+", " ", v).strip().lower() for v in vals}
                if re.sub(r"\s+", " ", lit).strip().lower() in norm:
                    aviso("literal_difere_em_caixa", f"`{col} = '{lit}'` só existe no top com outra caixa/espaço: {vals[:5]}", gr)
                else:
                    aviso("literal_ausente_do_top", f"`{col} = '{lit}'` não está no top de {len(vals)} valores ({cols[real].get('distintos_aprox')} distintos): {vals[:5]}", gr)
    return av


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def sugere(ds, cartao, perfil):
    saida = {}
    for tab, p in (perfil.get("tabelas") or {}).items():
        if str(p.get("fonte_do_perfil")).strip() != "tabela inteira" or not p.get("colunas"):
            continue
        t = (cartao.get("tabelas") or {}).get(tab) or {}
        cols, linhas = p["colunas"], p.get("linhas") or 0
        s = {}
        for nome, c in cols.items():
            mn, mx = c.get("min"), c.get("max")
            if mn is None or mx is None or c.get("pessoal"):
                continue
            tipo = str(c.get("tipo", "")).upper()
            if nome.lower() == "ano" or re.fullmatch(r"(ano|year)", nome.lower()):
                a, b = num(mn), num(mx)
                if a and b and 1800 <= a <= 2100 and 1800 <= b <= 2100:
                    s["cobertura"] = {"coluna": nome, "de": str(int(a)), "ate": str(int(b))}
                    break
            elif tipo.startswith(("DATE", "TIMESTAMP")):
                s.setdefault("_datas", []).append({"coluna": nome, "de": str(mn)[:10], "ate": str(mx)[:10]})
        datas = s.pop("_datas", [])
        if "cobertura" not in s and datas:
            pref = [d for d in datas if re.search(r"^data$|^dt_|^data_|_data$|_dt$|^date", d["coluna"], re.I)] or datas
            s["cobertura"] = pref[0]
        if "cobertura" in s:
            cob = s["cobertura"]
            texto = str(((t.get("tempo") or {}).get("cobertura")) or "")
            anos = set(re.findall(r"(?<!\d)(?:19|20)\d\d(?!\d)", texto))
            cob["no_cartao"] = texto or None
            cob["diverge_do_cartao"] = bool(texto) and not (cob["de"][:4] in anos and cob["ate"][:4] in anos)
        if linhas >= 100:
            chaves = [n for n, c in cols.items()
                      if (c.get("nulos_pct") or 0) == 0 and (c.get("distintos_aprox") or 0) >= 0.97 * linhas]
            if chaves:
                s["chave_unica_sozinha"] = chaves
                texto = str(t.get("chave") or "")
                s["ja_no_cartao"] = [c for c in chaves if re.search(rf"\b{re.escape(c)}\b", texto)]
        if s:
            s["rascunho"] = True
            saida[tab] = s
    return saida


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("datasets", nargs="*")
    ap.add_argument("--detalhe", action="store_true")
    ap.add_argument("--sugestoes", action="store_true", help="grava summaries/_sugestoes.json")
    ap.add_argument("--json", help="grava os avisos neste arquivo")
    a = ap.parse_args()
    dss = a.datasets or sorted(p.name[:-4] for p in SUM.glob("*.yml") if not p.name.endswith(".perfil.yml"))
    avisos, sug = [], {}
    for ds in dss:
        c, p = SUM / f"{ds}.yml", SUM / f"{ds}.perfil.yml"
        if not (c.exists() and p.exists()):
            continue
        cartao, perfil = carrega(c), carrega(p)
        avisos += valida(ds, cartao, perfil)
        r = sugere(ds, cartao, perfil)
        if r:
            sug[ds] = r
    if a.detalhe or a.datasets:
        for x in avisos:
            print(f"[{x['gravidade']}] {x['dataset']}.{x['tabela']} {x['tipo']}: {x['msg']}")
    cont = collections.Counter((x["tipo"], x["gravidade"]) for x in avisos)
    print(f"\n{len(avisos)} avisos em {len({(x['dataset'], x['tabela']) for x in avisos})} tabelas ({len(dss)} datasets)")
    for (tipo, g), n in sorted(cont.items()):
        print(f"  {tipo:26s} {g:7s} {n}")
    if a.json:
        Path(a.json).write_text(json.dumps(avisos, ensure_ascii=False, indent=1))
    if a.sugestoes:
        out = {"aviso": "RASCUNHO: sugestões tiradas do perfil, nunca medidas; revisar antes de levar ao cartão",
               "gerado_em": datetime.date.today().isoformat(), "gerado_por": "scripts/valida_cartao_perfil.py",
               "datasets": sug}
        (SUM / "_sugestoes.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
        n = sum(len(v) for v in sug.values())
        div = sum(1 for d in sug.values() for t in d.values() if t.get("cobertura", {}).get("diverge_do_cartao"))
        print(f"sugestões: {n} tabelas, {div} com cobertura divergente do cartão -> _sugestoes.json")


if __name__ == "__main__":
    main()
