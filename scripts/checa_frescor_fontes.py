#!/usr/bin/env python3
"""
Compara o dado mais recente da FONTE com o que o espelho tem. Só reporta.

    python3 scripts/checa_frescor_fontes.py            # todas as entradas
    python3 scripts/checa_frescor_fontes.py br_cgu_    # só as que começam assim
    python3 scripts/checa_frescor_fontes.py --md       # tabela em markdown
    python3 scripts/checa_frescor_fontes.py --sem-proxy  # pula as fontes que só abrem por IP brasileiro

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
  - `updated_at` anda quando o espelho é regravado sem coleta nova (tipos, zstd, ordenação).
    Quem não pode ser enganado por isso declara `ref: scrape_date`: vale a mais nova entre a
    coleta do catálogo e a última promoção do gate (~/scrap_tmp/backup/<dataset>/<tabela>/).
    O scrape_date sozinho não anda numa nova coleta, e uma recoleta fora do gate fica invisível.
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


POOLS = {}


def por_proxy(url, stream=False):
    if "--sem-proxy" in sys.argv:
        raise RuntimeError("pulada (--sem-proxy): a fonte só abre por IP brasileiro")
    """Fonte que filtra por país (`proxy_br: true`). O pool vive em scripts/scrap/, fora do git:
    sem ele a checagem dá ERRO e as outras seguem. Um pool por host, como no raspador."""
    sys.path.insert(0, str(RAIZ / "scripts/scrap"))
    from _proxy_br import Pool
    host = url.split("/")[2]
    if host not in POOLS:
        POOLS[host] = Pool(url)
    return POOLS[host].get(url, timeout=60, stream=stream, tentativas=8)


def tri100(hoje):
    """AAAAMM do último trimestre encerrado há mais de 100 dias: o IF.data publica ~90 d depois."""
    d = hoje - dt.timedelta(days=100)
    m = (d.month - 1) // 3 * 3
    return f"{d.year}{m:02d}" if m else f"{d.year - 1}12"


def endereco(c):
    hoje = dt.date.today()
    ant = (hoje.replace(day=1) - dt.timedelta(days=1))
    return (c["url"].replace("{ano}", str(hoje.year)).replace("{hoje}", hoje.strftime("%Y%m%d"))
            .replace("{ha3}", (hoje - dt.timedelta(days=3)).strftime("%Y%m%d"))
            .replace("{ha30}", (hoje - dt.timedelta(days=30)).isoformat())
            .replace("{mes}", hoje.strftime("%Y%m")).replace("{mes_ant}", ant.strftime("%Y%m"))
            .replace("{tri100}", tri100(hoje)))


CACHE = {}


def baixa(c, de_novo=False):
    """`bytes: N` pede só os N primeiros (data no cabeçalho de arquivo grande), `cauda: N` os N últimos (o
    diretório central de um zip lista os nomes); `cabecalhos` vão como `-H`;
    `ua` troca o User-Agent; `timeout` (s) sobe o teto do curl. Respostas iguais (mesma URL e
    cabeçalhos) ficam em cache na rodada: as 6 entradas do SINAN leem uma só listagem do FTP."""
    if c.get("proxy_br"):
        return por_proxy(endereco(c)).content
    extra = ["-r", f"0-{c['bytes']}"] if c.get("bytes") else ["-r", f"-{c['cauda']}"] if c.get("cauda") else []
    if c.get("ua"):   # gov.br serve outra página (sem os links) para UA que não é de navegador
        extra += ["-A", c["ua"]]
    for h in c.get("cabecalhos", []):
        extra += ["-H", h]
    chave = (endereco(c), tuple(extra))
    if de_novo or chave not in CACHE:
        CACHE[chave] = curl([*extra, endereco(c)], timeout=c.get("timeout", 90))
    return CACHE[chave]


def curl(args, timeout=90):
    r = subprocess.run(["curl", "-sS", "-L", "-m", str(timeout), "-A", UA, *args], capture_output=True, timeout=timeout + 10)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.decode(errors="replace").strip()[:120])
    return r.stdout


MESES_PT = {"janeiro": "January", "fevereiro": "February", "marco": "March", "março": "March", "maro": "March",
            "abril": "April", "maio": "May", "junho": "June", "julho": "July", "agosto": "August",
            "setembro": "September", "outubro": "October", "novembro": "November", "dezembro": "December"}


def le_data(texto, formato):
    if formato == "epoch_ms":
        return dt.datetime.fromtimestamp(int(texto) / 1000, dt.timezone.utc).date()
    if "%B" in formato:   # mês por extenso em português ("Maro" é o "Março" sem o ç, como o Plone grava)
        texto = re.sub(r"[A-Za-zçÇ]+", lambda m: MESES_PT.get(m.group(0).lower(), m.group(0)), texto)
    d = dt.datetime.strptime(texto, formato)
    # formato sem ano (o mês de um diretório do ano corrente): assume o ano corrente
    return (d.replace(year=dt.date.today().year) if "%Y" not in formato and "%y" not in formato else d).date()


def http_json(c):
    v = json.loads(baixa(c))
    for passo in c["json_path"]:
        v = v[passo]
    return le_data(str(v), c["formato"])


def http_last_modified(c):
    if c.get("proxy_br"):
        with por_proxy(endereco(c), stream=True) as r:
            cab = "".join(f"{k}: {v}\n" for k, v in r.headers.items())
    else:
        cab = curl(["-I", endereco(c)], timeout=240).decode(errors="replace")   # o FTP do DATASUS leva minutos no HEAD
    achados = re.findall(r"(?im)^last-modified:\s*(.+?)\s*$", cab)
    if not achados:
        raise RuntimeError("sem Last-Modified")
    return email.utils.parsedate_to_datetime(achados[-1]).date()   # o último, depois dos redirects


def regex(c):
    """`tentativas: N` repete quando o padrão não casa ou o curl falha (o WAF do consumidor.gov.br
    devolve uma página de erro 504 com status 200 de vez em quando)."""
    import time
    for i in range(c.get("tentativas", 1)):
        try:
            txt = baixa(c, de_novo=i > 0).decode(errors="replace")
        except RuntimeError:
            if i + 1 == c.get("tentativas", 1):
                raise
            time.sleep(20)
            continue
        achados = {"".join(m) if isinstance(m, tuple) else m for m in re.findall(c["padrao"], txt)}
        if achados or i + 1 == c.get("tentativas", 1):
            break
        time.sleep(20)
    if c.get("confirma_arquivo"):   # diretório de mês vazio (só tmp.txt) não conta: abre cada um e exige o arquivo
        base = endereco(c)
        achados = {a for a in achados
                   if (d := re.search(r'href="(%s%%20-%%20[^"]*)"' % re.escape(a), txt))
                   and c["confirma_arquivo"] in curl([base + d.group(1)]).decode(errors="replace")}
    if not achados:
        raise RuntimeError("padrão não casou — a página mudou?")
    return max(le_data(a, c["formato"]) for a in achados)


def retrato(c):
    """Fonte viva sem data nenhuma: ela vale por hoje, e `ciclo_dias` diz quanto o espelho pode
    ficar sem coleta. Não prova que a fonte mudou, só que passou o prazo."""
    if c.get("url"):  # a fonte ao menos responde; ERRO aqui é fonte fora do ar ou caminho que mudou
        baixa(c)
    return dt.date.today()


TIPOS = {"http_json": http_json, "http_last_modified": http_last_modified, "regex": regex, "retrato": retrato}
SEM_FONTE = {"dead": "morta", "manual": "manual", "estatico": "estática", "bd": "só pela BD", "derivado": "derivada"}


def catalogo():
    sql = ("SET enable_progress_bar=false; "
           "SELECT dataset || '.' || \"table\" AS t, CAST(last_date AS VARCHAR) AS last_date, "
           "CAST(scrape_date AS VARCHAR) AS scrape_date, "
           "CAST(updated_at AS VARCHAR) AS updated_at FROM _rodado_metadata;")
    out = subprocess.run(["ssh", BEELINK, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                         input=sql, capture_output=True, text=True, timeout=180).stdout
    return {r["t"]: r for r in json.loads(out[out.index("["):])}


def promocoes():
    """Última promoção do gate por tabela, do carimbo em ~/scrap_tmp/backup."""
    out = subprocess.run(["ssh", BEELINK, "cd ~/scrap_tmp/backup && ls -d */*/*"], capture_output=True, text=True, timeout=60).stdout
    ult = {}
    for linha in out.split():
        partes = linha.split("/")
        if len(partes) == 3 and re.match(r"\d{8}-", partes[2]):
            d = f"{partes[2][:4]}-{partes[2][4:6]}-{partes[2][6:8]}"
            ult[f"{partes[0]}.{partes[1]}"] = max(ult.get(f"{partes[0]}.{partes[1]}", ""), d)
    return ult


def data_no_espelho(tabela, expr):
    """`espelho: <expr>`: max da expressão na tabela, para o que dataset_freshness.yaml não cobre.
    Entrada curinga (`dataset.*`) diz qual tabela medir com `espelho_tabela`."""
    sql = f"SET enable_progress_bar=false; SELECT CAST(max({expr}) AS DATE) AS d FROM {tabela};"
    r = subprocess.run(["ssh", BEELINK, "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb"],
                       input=sql, capture_output=True, text=True, timeout=120)
    if "[" not in r.stdout:
        raise RuntimeError("espelho: " + r.stderr.strip().splitlines()[-1][:100])
    return json.loads(r.stdout[r.stdout.index("["):])[0]["d"] or ""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    md = "--md" in sys.argv
    if not CHECKS.exists():
        print(f"{CHECKS} não existe — a pasta privado/ fica fora do git e não vem num clone novo", file=sys.stderr)
        return 1
    checks = yaml.safe_load(CHECKS.read_text())
    cat, promovidas = catalogo(), promocoes()
    linhas = []
    for tabela, c in checks.items():
        if args and not any(tabela.startswith(a) for a in args):
            continue
        meta = cat.get(tabela, {})
        if tabela.endswith(".*"):
            # curinga: vale a data mais NOVA entre as tabelas do dataset (a rodada costuma regravá-las juntas)
            irmas = [t for t in cat if t.startswith(tabela[:-1])]
            meta = {k: max((cat[t].get(k) or "" for t in irmas), default="") for k in ("last_date", "scrape_date", "updated_at")}
            promovidas[tabela] = max((promovidas.get(t, "") for t in irmas), default="")
        espelho = (meta.get("last_date") or "")[:10]
        coleta = max((meta.get("scrape_date") or "")[:10], promovidas.get(tabela, ""))
        # updated_at = parquet mais novo da tabela (quando regravamos); scrape_date é a 1ª coleta e não anda
        raspado = (meta.get("updated_at") or meta.get("scrape_date") or "")[:10]
        tipo = c["check"]
        fonte, estado = "", ""
        if tipo in SEM_FONTE:
            estado = SEM_FONTE[tipo]
        else:
            try:
                d = TIPOS[tipo](c)
                fonte = d.isoformat()
                if c.get("espelho"):
                    espelho = data_no_espelho(c.get("espelho_tabela", tabela), c["espelho"])
                # last_modified fala do arquivo: compara com quando raspamos. Os outros falam do dado.
                arquivo = tipo == "http_last_modified" or c.get("compara") == "arquivo" or (tipo == "retrato" and not c.get("espelho"))
                base = coleta if c.get("ref") == "scrape_date" else raspado
                ref = base if arquivo else (espelho or raspado)
                if not ref:
                    estado = "sem referência no catálogo"
                else:
                    atraso = (d - dt.date.fromisoformat(ref)).days
                    estado = "em dia" if atraso <= c.get("ciclo_dias", 0) else f"fonte +{atraso} d"
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
        if nota and (s.startswith(("fonte +", "ERRO")) or tipo in SEM_FONTE):
            print(f"{'':26} nota: {nota}")
    atras = sum(1 for l in linhas if l[5].startswith("fonte +"))
    erros = sum(1 for l in linhas if l[5].startswith("ERRO"))
    print(f"\n{len(linhas)} entradas: {atras} com a fonte à frente, {erros} com erro de checagem")
    return 0


if __name__ == "__main__":
    sys.exit(main())
