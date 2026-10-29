#!/usr/bin/env python3
"""Trava de integridade antes de copiar parquet de ~/rodado para o S3 e para o COLD.

Roda NO beelink, em ~/scripts/valida_parquet.py (cópia deste arquivo; a fonte é o repo,
scripts/sync/valida_parquet.py). Chamado por ~/scripts/s3_sync_check.py e por
~/scripts/backup_rodado_to_cold.sh: arquivo reprovado não sobe nem vai para o COLD, e a
cópia antiga (boa) fica onde está.

Por que existe (2026-10-28): o S3 e o COLD guardavam fielmente os parquet que os scrapers
tinham gravado errado, porque o sync só comparava nome e tamanho. Cada regra abaixo é um
erro que de fato chegou lá:

  cabecalho_colado   nome de coluna com o cabeçalho inteiro (`a;b;c`) ou `column01..NN` de
                     enchimento: o sniffer do read_csv escolheu o delimitador errado
                     (42 arquivos de br_mgi_compras_publicas).
  json_nulo          coluna de tipo JSON inteira nula: o read_json grava JSON quando o campo
                     nunca veio, e a view com union_by_name herda JSON do primeiro arquivo e
                     quebra no primeiro texto (81 arquivos de br_mgi_pncp).
  leitura            o DuckDB não lê todas as colunas até o fim: texto latin-1 ou UTF-8
                     cortado no meio do caractere (ICMBio, SEMAS-PA, ~1.200 arquivos da SIA),
                     página corrompida, segfault (o leitor roda em subprocesso; morrer
                     reprova o arquivo).
  linhas             o rodapé diz N linhas e a leitura devolve outro número.
  encolheu           menos da metade das linhas da cópia anterior (a do COLD).
  colunas_trocadas   menos da metade dos nomes de coluna da cópia anterior sobrou.

As duas últimas comparam com a versão anterior e podem ser liberadas, arquivo a arquivo, em
~/scripts/valida_parquet_libera.txt (um glob relativo a ~/rodado por linha, `#` comenta),
quando a mudança é de propósito. As outras nunca são liberadas: corrija o arquivo.

Resultado em cache por (caminho, tamanho, mtime) em ~/.cache/valida_parquet.jsonl: a
segunda rodada do sync e o backup do COLD não releem o que já foi conferido. Reprovados
vão para ~/logs/valida_parquet_rejeitados.log.

    python3 valida_parquet.py arquivo.parquet ...       # imprime um JSON por arquivo
    python3 valida_parquet.py --stdin < lista            # caminhos relativos a ~/rodado ou absolutos
    python3 valida_parquet.py --sem-anterior ...         # não compara com o COLD
"""
import fnmatch, json, os, re, subprocess, sys, tempfile, time

H = os.path.expanduser("~")
RAIZ = f"{H}/rodado"
COLD = "/mnt/COLD/rodado"
CACHE = os.environ.get("VALIDA_CACHE", f"{H}/.cache/valida_parquet.jsonl")
LIBERA = f"{H}/scripts/valida_parquet_libera.txt"
LOG = os.environ.get("VALIDA_LOG", f"{H}/logs/valida_parquet_rejeitados.log")
VERSAO = 1   # sobe quando uma regra muda: o cache antigo deixa de valer
COLADO = re.compile(r"^column\d+$", re.I)


def _abs(p):
    return p if p.startswith("/") else os.path.join(RAIZ, p)


def _rel(p):
    return os.path.relpath(p, RAIZ)


def _id(p):
    st = os.stat(p)
    return f"{p}|{st.st_size}|{st.st_mtime_ns}|v{VERSAO}"


# ---------------------------------------------------------------- o que roda no subprocesso
def _confere(p, anterior):
    import duckdb, pyarrow.parquet as pq
    motivos = []
    md = pq.ParquetFile(p).metadata
    n = md.num_rows
    nomes = md.schema.to_arrow_schema().names
    if any(x.count(";") >= 2 or COLADO.match(x) for x in nomes):
        motivos.append("cabecalho_colado")
    nulos = {}
    for i in range(md.num_columns):
        col = md.schema.column(i)
        if "JSON" in (str(col.logical_type), str(col.converted_type)):
            nc = 0
            for rg in range(md.num_row_groups):
                s = md.row_group(rg).column(i).statistics
                if s is None or not s.has_null_count:
                    nc = None
                    break
                nc += s.null_count
            if nc is not None and nc == n:
                nulos[col.path] = True
    if nulos:
        motivos.append("json_nulo: " + ", ".join(sorted(nulos))[:200])
    con = duckdb.connect(config={"memory_limit": "2GB", "threads": 4})
    try:
        lidas = con.execute("SELECT count(*), sum(hash(t))::HUGEINT FROM read_parquet(?) t", [p]).fetchone()[0]
        if lidas != n:
            motivos.append(f"linhas: rodapé {n}, leitura {lidas}")
    except duckdb.Error as e:
        motivos.append("leitura: " + str(e).splitlines()[0][:200])
    if anterior and os.path.exists(anterior):
        try:
            ma = pq.ParquetFile(anterior).metadata
            na, nomes_a = ma.num_rows, set(ma.schema.to_arrow_schema().names)
            if any(x.count(";") >= 2 or COLADO.match(x) for x in nomes_a):
                nomes_a = set()   # a cópia anterior é a quebrada: não serve de régua para os nomes
            if na >= 1000 and n < na / 2:
                motivos.append(f"encolheu: {na} -> {n} linhas")
            if nomes_a and len(nomes_a & set(nomes)) < len(nomes_a) / 2:
                motivos.append(f"colunas_trocadas: {len(nomes_a & set(nomes))} de {len(nomes_a)} nomes sobraram")
        except Exception as e:  # noqa: BLE001 — cópia anterior ilegível não reprova a nova
            pass
    return {"ok": not motivos, "linhas": n, "motivos": motivos}


def _trabalhador(lista):
    """Lê `caminho\tanterior` do arquivo `lista`; antes de cada arquivo avisa qual é, para o pai
    saber quem matou o processo se ele morrer. A lista vem por arquivo, não pelo stdin: com mais
    de 64 KB o pai travava escrevendo no stdin enquanto o filho travava escrevendo no stdout
    (2026-10-28, 1.400 arquivos da SIA)."""
    for linha in open(lista):
        p, anterior = linha.rstrip("\n").split("\t")
        print(json.dumps({"inicio": p}), flush=True)
        try:
            r = _confere(p, anterior or None)
        except Exception as e:  # noqa: BLE001
            r = {"ok": False, "motivos": ["rodape: " + str(e).splitlines()[0][:200] if str(e) else type(e).__name__]}
        print(json.dumps({"f": p, **r}), flush=True)


# ---------------------------------------------------------------- o que o sync chama
def _libera():
    try:
        return [l.split("#")[0].strip() for l in open(LIBERA) if l.split("#")[0].strip()]
    except FileNotFoundError:
        return []


def _cache():
    c = {}
    try:
        for l in open(CACHE):
            try:
                r = json.loads(l)
                c[r["id"]] = r
            except (ValueError, KeyError):
                pass
    except FileNotFoundError:
        pass
    return c


def valida(caminhos, anterior=True):
    """{caminho absoluto: {"ok", "motivos", ...}} para os .parquet da lista; o resto da lista
    (não parquet, arquivo que sumiu) não entra no resultado e passa."""
    alvos = []
    for c in caminhos:
        p = _abs(c)
        if p.endswith(".parquet") and os.path.isfile(p):
            alvos.append(p)
    cache, out, falta = _cache(), {}, []
    libera = _libera()
    for p in alvos:
        try:
            k = _id(p)
        except FileNotFoundError:
            continue
        if k in cache:
            # liberação acrescentada depois da reprovação vale também para o resultado em cache
            # (2026-10-29: os 10 do INMET liberados seguiam reprovados no COLD pelo cache)
            out[p] = _aplica_libera(p, cache[k], libera)
        else:
            falta.append((p, k))
    os.makedirs(os.path.dirname(CACHE), exist_ok=True)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(CACHE, "a") as fc, open(LOG, "a") as fl:
        while falta:
            ids = dict(falta)
            entrada = "".join(f"{p}\t{(os.path.join(COLD, _rel(p)) if anterior and os.path.isdir(COLD) else '')}\n"
                              for p, _ in falta)
            with tempfile.NamedTemporaryFile("w", prefix="valida_parquet.", suffix=".lista", delete=False) as tf:
                tf.write(entrada)
            proc = subprocess.Popen(["nice", "-n", "15", sys.executable, os.path.abspath(__file__), "--trabalhador", tf.name],
                                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True)
            atual = None
            for linha in proc.stdout:
                r = json.loads(linha)
                if "inicio" in r:
                    atual = r["inicio"]
                    continue
                atual = None
                p = r.pop("f")
                _grava(fc, fl, out, p, ids[p], r, libera)
            proc.wait()
            os.unlink(tf.name)
            feitos = set(out)
            if atual:   # morreu lendo este arquivo
                _grava(fc, fl, out, atual, ids[atual],
                       {"ok": False, "motivos": [f"leitura: o leitor morreu (exit {proc.returncode})"]}, libera)
                feitos.add(atual)
            resto = [(p, k) for p, k in falta if p not in feitos]
            if len(resto) == len(falta):   # não andou: não fica em laço
                for p, k in resto:
                    _grava(fc, fl, out, p, k, {"ok": False, "motivos": [f"leitura: o leitor saiu sem conferir (exit {proc.returncode})"]}, libera)
                resto = []
            falta = resto
    return out


def _aplica_libera(p, r, libera):
    """Só `encolheu`/`colunas_trocadas` se liberam; leitura, rodapé e afins nunca."""
    if not r["ok"] and any(fnmatch.fnmatch(_rel(p), g) for g in libera):
        duros = [m for m in r["motivos"] if not m.startswith(("encolheu", "colunas_trocadas"))]
        if not duros:
            r = {**r, "ok": True, "liberado": r["motivos"], "motivos": []}
    return r


def _grava(fc, fl, out, p, k, r, libera):
    rel = _rel(p)
    r = _aplica_libera(p, r, libera)
    r = {"id": k, **r}
    out[p] = r
    fc.write(json.dumps(r) + "\n")
    fc.flush()
    if not r["ok"]:
        fl.write(f"{time.strftime('%F %T')} {rel}: {'; '.join(r['motivos'])}\n")
        fl.flush()


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--trabalhador"]:
        _trabalhador(a[1])
        sys.exit()
    ant = "--sem-anterior" not in a
    a = [x for x in a if x != "--sem-anterior"]
    lista = [l.strip() for l in sys.stdin if l.strip()] if a[:1] == ["--stdin"] else a
    res = valida(lista, anterior=ant)
    for p, r in res.items():
        print(json.dumps({"f": _rel(p), **{k: v for k, v in r.items() if k != "id"}}, ensure_ascii=False))
    sys.exit(0 if all(r["ok"] for r in res.values()) else 2)
