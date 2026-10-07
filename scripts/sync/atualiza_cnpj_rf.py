#!/usr/bin/env python3
"""Completa `br_me_cnpj` no beelink com os retratos mensais que só o `br_rf_cnpj` tem.

    python3 scripts/sync/atualiza_cnpj_rf.py                       # o que falta, sem baixar
    python3 scripts/sync/atualiza_cnpj_rf.py --apply --mes 202609  # um mês, as 3 tabelas
    python3 scripts/sync/atualiza_cnpj_rf.py --apply --tabela socios
    python3 scripts/sync/atualiza_cnpj_rf.py --apply               # tudo o que falta

Por que existe: em 2026-08-13 o Base dos Dados rebatizou o cadastro do CNPJ de
`br_me_cnpj` para `br_rf_cnpj`. O antigo parou em 2026-07-15 e saiu do catálogo. É o
mesmo dado, com `ano`/`mes`/`data` trocados por `data_referencia` (e uma
`data_modificacao` a mais). O espelho segue com o nome `br_me_cnpj`, que é o que
`bridges.yaml`, as métricas e o MCP conhecem; este script traz os meses novos já no
schema antigo, em vez de baixar 1,1 TB de novo sob outro nome.

Cada mês entra como arquivos `rf_<aaaamm>_<NNNN>.parquet` ao lado dos numerados
(`000000000000.parquet`), nome fora da faixa que os outros scripts de sync usam. Nada
existente é tocado. O que falta é decidido pelo disco: mês com `rf_<aaaamm>_*` ou com
linhas daquele `ano`/`mes` nos arquivos antigos é pulado.

As linhas vêm em streaming (`to_arrow_iterable`, pela Storage Read API), um mês de `estabelecimentos` tem
~72 M linhas e não cabe em memória de uma vez.

Depois de rodar: `python3 scripts/repara_views_beelink.py --apply` (as views listam os
arquivos um a um e não enxergam os novos sozinhas).
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import bq_quota  # noqa: E402
import ressincroniza_bq as rs  # noqa: E402

ORIGEM = "br_rf_cnpj"
DESTINO = "br_me_cnpj"
TABELAS = ["socios", "empresas", "estabelecimentos"]
LINHAS_POR_ARQUIVO = 1_000_000


def colunas_locais(tb):
    """Nome e ordem das colunas do parquet do espelho, que é o schema a reproduzir."""
    r = rs.duck(f"SELECT column_name c FROM (DESCRIBE SELECT * FROM "
                f"read_parquet('{rs.ROOT}/{DESTINO}/{tb}/000000000000.parquet'));")
    if not r:
        sys.exit(f"não li o schema local de {DESTINO}.{tb}")
    return [x["c"] for x in r]


def meses_locais(tb):
    r = rs.duck(f"SELECT DISTINCT ano*100+mes m FROM "
                f"read_parquet('{rs.ROOT}/{DESTINO}/{tb}/*.parquet');", timeout=3600)
    if r is None:
        sys.exit(f"não li os meses locais de {DESTINO}.{tb}")
    return {str(x["m"]) for x in r}


def meses_origem(client, tb):
    """{aaaamm: linhas} pelas partições, sem job: metadado, custo zero."""
    t = client.get_table(f"{rs.BQ_PROJECT}.{ORIGEM}.{tb}")
    out = {}
    for p in client.list_partitions(t):
        if p.isdigit():
            n = client.get_table(f"{rs.BQ_PROJECT}.{ORIGEM}.{tb}${p}").num_rows
            if n:
                out[p] = n
    return out


def consulta(tb, cols, mes):
    expr = {"ano": "EXTRACT(YEAR FROM data_referencia) AS ano",
            "mes": "EXTRACT(MONTH FROM data_referencia) AS mes",
            "data": "data_referencia AS data"}
    sel = ", ".join(expr.get(c, f"`{c}`") for c in cols)
    ini = f"{mes[:4]}-{mes[4:]}-01"
    return (f"SELECT {sel} FROM `{rs.BQ_PROJECT}.{ORIGEM}.{tb}` "
            f"WHERE data_referencia >= DATE '{ini}' "
            f"AND data_referencia < DATE_ADD(DATE '{ini}', INTERVAL 1 MONTH)")


def baixa_mes(client, leitor, bq, pq, tb, cols, mes, esperado, reserva_gb):
    alvo = f"{DESTINO}.{tb} {mes}"
    sql = consulta(tb, cols, mes)
    est = client.query(sql, job_config=bq.QueryJobConfig(
        dry_run=True, use_query_cache=False)).total_bytes_processed
    falta = rs.exige_espaco(est, reserva_gb)
    if falta:
        return f"{alvo}: {falta}"
    if not bq_quota.reserve(est):
        return f"{alvo}: cota do mês: {bq_quota.status()}"

    remoto = f"{rs.ROOT}/{DESTINO}/{tb}"
    staging = f"{remoto}.rf_{mes}"
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp)
        # com a Storage Read API; pela REST vêm ~4 mil linhas/s (medido 2026-10-07).
        # Os lotes são agrupados em row groups grandes por rs.escreve_shards: um row
        # group por lote deixou 1.200 row groups por arquivo e a view estourou memória.
        lotes = client.query(sql).result().to_arrow_iterable(bqstorage_client=leitor)
        rs.LINHAS_POR_SHARD = LINHAS_POR_ARQUIVO
        n, _ = rs.escreve_shards(lotes, local, pq)
        for f in sorted(local.glob("*.parquet")):
            f.rename(local / f"rf_{mes}_{int(f.stem):04d}.parquet")
        if n != esperado:
            return f"{alvo}: vieram {n:,} linhas, a partição tem {esperado:,}"
        rs.sh(f"rm -rf {staging} && mkdir -p {staging}", check=True)
        r = subprocess.run(["rsync", "-a", f"{local}/", f"{rs.BEELINK}:{staging}/"],
                           capture_output=True, text=True, timeout=7200)
        if r.returncode != 0:
            rs.sh(f"rm -rf {staging}")
            return f"{alvo}: rsync: {r.stderr[:200]}"

    # confere no staging antes de misturar com os arquivos do espelho
    c = rs.duck(f"SELECT count(*) n, min(ano*100+mes) a, max(ano*100+mes) b "
                f"FROM read_parquet('{staging}/*.parquet');")
    if not c or c[0]["n"] != esperado or str(c[0]["a"]) != mes or str(c[0]["b"]) != mes:
        return f"{alvo}: conferência no beelink falhou ({c}); arquivos em {staging}"
    rs.sh(f"chmod 664 {staging}/*.parquet && mv {staging}/*.parquet {remoto}/ && "
          f"rmdir {staging}", check=True)
    print(f"  {alvo:38} {n:>12,} linhas  {est/1e9:6.1f} GB de cota", flush=True)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--mes", action="append", help="aaaamm; repetível. Padrão: todos os que faltam")
    ap.add_argument("--tabela", action="append", choices=TABELAS)
    ap.add_argument("--reserva-gb", type=float, default=100.0)
    a = ap.parse_args()

    import warnings
    warnings.filterwarnings("ignore")
    from google.cloud import bigquery as bq
    from google.cloud import bigquery_storage
    import pyarrow.parquet as pq

    rs.exige_sandbox()
    client = bq.Client(project=rs.BILLING_PROJECT)
    leitor = bigquery_storage.BigQueryReadClient()

    erros = []
    for tb in a.tabela or TABELAS:
        origem = meses_origem(client, tb)
        faltam = sorted(set(origem) - meses_locais(tb), reverse=True)  # o mais recente primeiro
        if a.mes:
            faltam = [m for m in faltam if m in a.mes]
        print(f"\n{DESTINO}.{tb}: faltam {len(faltam)} meses, "
              f"{sum(origem[m] for m in faltam):,} linhas: {' '.join(faltam)}", flush=True)
        if not a.apply:
            continue
        cols = colunas_locais(tb)
        for m in faltam:
            # o stream da Storage API cai às vezes no meio de um mês ("503 Stream
            # removed", 2026-10-07); o mês só entra no espelho depois de conferido,
            # então repetir é seguro. Custa a cota do mês de novo.
            for tentativa in range(3):
                try:
                    e = baixa_mes(client, leitor, bq, pq, tb, cols, m, origem[m],
                                  a.reserva_gb)
                    break
                except Exception as exc:                          # noqa: BLE001
                    e = f"{DESTINO}.{tb} {m}: {str(exc)[:200]}"
                    print(f"  falhou (tentativa {tentativa + 1}/3): {e}", flush=True)
            if e:
                print(f"  ERRO {e}", flush=True)
                erros.append(e)
                if "cota" in e or "sem espaço" in e:
                    return 1
    print(f"\n{bq_quota.status()}")
    if a.apply:
        print("agora rode: python3 scripts/repara_views_beelink.py --apply")
    return 1 if erros else 0


if __name__ == "__main__":
    sys.exit(main())
