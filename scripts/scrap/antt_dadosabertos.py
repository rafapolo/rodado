#!/usr/bin/env python3
"""
ANTT (dados.antt.gov.br, CKAN) — RNTRC, veículos do RNTRC, CIOT e acidentes nas
rodovias concedidas -> Parquet -> beelink.

Do IP suíço o F5 da ANTT devolve "Request Rejected" (HTTP 200 com HTML, não
erro): o download sai por `_proxy_br.Pool`, que descarta essa página.

Tabelas (~/rodado/br_antt_dadosabertos/<tabela>/):
  - rntrc              transportadores do RNTRC. A ANTT republica o cadastro
                       inteiro todo mês (`transportadores_rntrc_MM_AAAA.csv`);
                       fica só o mês mais recente, os anteriores são cópia
                       quase idêntica. Coluna `referencia` = AAAA-MM do arquivo.
  - rntrc_veiculos     veículos do RNTRC, um CSV
  - ciot               Código Identificador da Operação de Transporte, fato
                       mensal (`MM_AAAA_ciots.csv`), todos os meses, ano=<a>/
  - acidentes_rodovias demonstrativo de acidentes por concessionária, um CSV
                       por concessão; coluna `concessionaria` sai do nome
                       do recurso

Tudo VARCHAR: o CSV da ANTT muda de separador e de coluna entre arquivos, e o
tipo é decidido na consulta, não no palpite do leitor.

Uso:
    python3 scripts/scrap/antt_dadosabertos.py [TEMP_DIR]
"""

import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _proxy_br import Pool  # noqa: E402

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_antt_dadosabertos"
API = "https://dados.antt.gov.br/api/3/action"
TEMP_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/antt")


def csv_para_parquet(src: Path, dst: Path, extra: dict[str, str], sem_aspas=False):
    """`sem_aspas`: lê sem tratar aspas e tira as aspas de cada campo depois.
    O RNTRC tem nome como `"''NOVA E.P. TRANSPORTES LTDA";` — aspa solta que faz
    o leitor engolir linhas: com aspas ligadas, 1.174.540 registros viravam
    534.187, e o `ignore_errors` escondia a perda."""
    import duckdb

    # transcodifica em Python: o demonstrativo da ECO050 não é UTF-8 e tem
    # bytes 0x80–0x9F (cp1252) que o leitor latin-1 do DuckDB recusa
    raw = src.read_bytes()
    try:
        txt = raw.decode("utf-8")
    except UnicodeDecodeError:
        txt = raw.decode("cp1252", errors="replace")
    utf8 = src.with_suffix(".utf8.csv")
    utf8.write_text(txt, encoding="utf-8")
    src, enc = utf8, "utf-8"
    head = txt.split("\n", 1)[0]
    sep = max([";", ",", "\t", "|"], key=head.count)
    cols = "".join(f", '{v}' AS {k}" for k, v in extra.items())
    con = duckdb.connect()
    aspas = "quote=''," if sem_aspas else ""
    con.execute(
        f"CREATE VIEW t AS SELECT * FROM read_csv('{src}', delim='{sep}', header=true, {aspas} "
        f"all_varchar=true, encoding='{enc}', strict_mode=false, null_padding=true, parallel=false, "
        f"ignore_errors=true)"
    )
    sel = "*"
    if sem_aspas:
        nomes = [r[0] for r in con.execute("DESCRIBE t").fetchall()]
        sel = ", ".join(f"""nullif(trim(\"{c}\", '"'), '') AS \"{c.strip('"')}\"""" for c in nomes)
    con.execute(f"COPY (SELECT {sel}{cols} FROM t) TO '{dst}' (FORMAT parquet, COMPRESSION zstd)")
    n = con.execute(f"SELECT count(*) FROM '{dst}'").fetchone()[0]
    # guarda: linha de CSV sem registro é perda silenciosa do ignore_errors
    linhas = txt.count("\n") - 1
    if n < 0.99 * linhas:
        raise RuntimeError(f"{src.name}: {n:,} registros para {linhas:,} linhas — o leitor perdeu dados")
    utf8.unlink()
    return n


def recursos(pool, pkg):
    rs = pool.get(f"{API}/package_show?id={pkg}").json()["result"]["resources"]
    return [r for r in rs if (r.get("format") or "").upper() == "CSV"]


def baixa(pool, url) -> Path:
    bruto = TEMP_DIR / "raw" / url.rsplit("/", 1)[-1]
    bruto.parent.mkdir(parents=True, exist_ok=True)
    if not bruto.exists():
        pool.download(url, bruto)
    return bruto


def main():
    pool = Pool(f"{API}/package_list")
    out = TEMP_DIR / "out"
    feitos = {}

    # rntrc: só o mês mais recente
    rs = recursos(pool, "rntrc")
    def ref(r):
        m = re.search(r"_(\d{2})_(\d{4})\.csv$", r["url"])
        return (int(m.group(2)), int(m.group(1))) if m else (0, 0)
    ult = max(rs, key=ref)
    a, m = ref(ult)
    d = out / "rntrc"
    d.mkdir(parents=True, exist_ok=True)
    feitos["rntrc"] = csv_para_parquet(baixa(pool, ult["url"]), d / f"rntrc_{a}_{m:02d}.parquet",
                                       {"referencia": f"{a}-{m:02d}"}, sem_aspas=True)
    print(f"  ✓ rntrc {a}-{m:02d}: {feitos['rntrc']:,}")

    # rntrc_veiculos
    d = out / "rntrc_veiculos"
    d.mkdir(parents=True, exist_ok=True)
    r = recursos(pool, "rntrc-veiculos")[0]
    feitos["rntrc_veiculos"] = csv_para_parquet(baixa(pool, r["url"]), d / "rntrc_veiculos.parquet", {})
    print(f"  ✓ rntrc_veiculos: {feitos['rntrc_veiculos']:,}")

    # ciot: todos os meses
    n = 0
    for r in recursos(pool, "ciot"):
        mm = re.search(r"(\d{2})_(\d{4})_ciots\.csv$", r["url"])
        if not mm:
            print(f"  ? ciot sem mês: {r['url']}")
            continue
        mes, ano = int(mm.group(1)), int(mm.group(2))
        d = out / "ciot" / f"ano={ano}"
        d.mkdir(parents=True, exist_ok=True)
        dst = d / f"mes_{mes:02d}.parquet"
        if dst.exists():
            continue
        k = csv_para_parquet(baixa(pool, r["url"]), dst, {"mes": str(mes)})
        n += k
        print(f"  ✓ ciot {ano}-{mes:02d}: {k:,}")
    feitos["ciot"] = n

    # acidentes_rodovias: uma concessão por arquivo
    n = 0
    d = out / "acidentes_rodovias"
    d.mkdir(parents=True, exist_ok=True)
    for r in recursos(pool, "acidentes-rodovias"):
        conc = re.split(r"Acidentes\s*[-_]\s*", r["name"], maxsplit=1)[-1].strip()
        stem = Path(r["url"].rsplit("/", 1)[-1]).stem
        k = csv_para_parquet(baixa(pool, r["url"]), d / f"{stem}.parquet", {"concessionaria": conc})
        n += k
        print(f"  ✓ acidentes {conc}: {k:,}")
    feitos["acidentes_rodovias"] = n

    for tabela, linhas in feitos.items():
        remote = f"{DATASET_PATH}/{tabela}"
        subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p {remote}"], check=True)
        subprocess.run(["rsync", "-a", f"{out}/{tabela}/", f"{BEELINK_HOST}:{remote}/"], check=True)
        print(f"  ✓ push {tabela} ({linhas:,} linhas nesta rodada)")


if __name__ == "__main__":
    main()
