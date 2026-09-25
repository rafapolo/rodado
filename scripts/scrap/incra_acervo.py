#!/usr/bin/env python3
"""
INCRA — imóveis certificados (SIGEF e SNCI) e assentamentos -> Parquet -> beelink.

A página `certificacao.incra.gov.br/csv_shp/export_shp.py` passou a exigir login
gov.br, mas os zips estáticos que ela linka continuam públicos:
    https://certificacao.incra.gov.br/csv_shp/zip/<Nome>.zip
Só abrem por IP brasileiro (`_proxy_br.Pool`).

Tabelas (~/rodado/br_incra_acervo/<tabela>/):
  - sigef_parcelas   parcelas certificadas no SIGEF, um shapefile por UF
  - snci_parcelas    imóveis certificados no SNCI (sistema anterior, até 2013),
                     por UF, quando o zip existe
  - assentamentos    projetos de assentamento, um shapefile nacional

Geometria: mesma decisão de DETER e PRODES — o polígono não entra (um estado
passa de centenas de MB em WKT). Ficam `lat`/`lon` do centroide e `area_ha`
calculada em projeção de área igual (EPSG:5880, Policônica Brasil).

Uso:
    python3 scripts/scrap/incra_acervo.py [TEMP_DIR]
"""

import subprocess
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).parent))
from _proxy_br import Pool  # noqa: E402

BEELINK_HOST = "beelink"
DATASET_PATH = "~/rodado/br_incra_acervo"
BASE = "https://certificacao.incra.gov.br/csv_shp/zip/"
TEMP_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/incra")
UFS = ("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC SE SP TO").split()

FONTES = {
    "assentamentos": [(None, "Assentamento Brasil.zip")],
    "sigef_parcelas": [(uf, f"Sigef Brasil_{uf}.zip") for uf in UFS],
    "snci_parcelas": [(uf, f"Imóvel certificado SNCI Brasil_{uf}.zip") for uf in UFS],
}


def shp_para_parquet(zipf: Path, dst: Path, uf: str | None) -> int:
    import duckdb

    pasta = zipf.with_suffix("")
    if not pasta.exists():
        # ditto, não unzip: o unzip do macOS sai com 50 nos nomes "Imóvel ..." do SNCI
        subprocess.run(["ditto", "-x", "-k", str(zipf), str(pasta)], check=True)
    shp = next(pasta.rglob("*.shp"))
    con = duckdb.connect()
    con.execute("LOAD spatial")
    uf_col = f", '{uf}' AS sigla_uf_arquivo" if uf else ""
    # a geometria vem em SIRGAS 2000 geográfico (EPSG:4674); área em EPSG:5880
    con.execute(f"""
        COPY (
          SELECT * EXCLUDE (geom),
                 ST_Y(ST_Centroid(geom)) AS lat,
                 ST_X(ST_Centroid(geom)) AS lon,
                 ST_Area(ST_Transform(geom, 'EPSG:4674', 'EPSG:5880', always_xy := true)) / 1e4 AS area_ha
                 {uf_col}
          FROM ST_Read('{shp}')
        ) TO '{dst}' (FORMAT parquet, COMPRESSION zstd)
    """)
    return con.execute(f"SELECT count(*) FROM '{dst}'").fetchone()[0]


def main():
    pool = Pool(BASE + quote("Assentamento Brasil.zip"))
    feitos = {}
    for tabela, itens in FONTES.items():
        outdir = TEMP_DIR / "out" / tabela
        outdir.mkdir(parents=True, exist_ok=True)
        total = 0
        for uf, nome in itens:
            dst = outdir / f"{uf or 'brasil'}.parquet"
            if dst.exists():
                continue
            url = BASE + quote(nome)
            zipf = TEMP_DIR / "raw" / tabela / nome.replace(" ", "_")
            zipf.parent.mkdir(parents=True, exist_ok=True)
            if not zipf.exists():
                # só 404 quer dizer "não existe"; erro de proxy não pode virar ausência
                # (a 1ª rodada marcou MG..TO como "sem zip" quando o pool caiu)
                try:
                    r = pool.get(url, stream=True, timeout=40)
                    tam = int(r.headers.get("content-length") or 0)
                    r.close()
                except Exception as e:
                    print(f"  ✗ {tabela} {uf}: proxy falhou ({e}); rode de novo")
                    continue
                if r.status_code == 404:
                    print(f"  - {tabela} {uf}: sem zip na fonte (404)")
                    continue
                if tam > 16 << 20:
                    pool.download_paralelo(url, zipf, tam)
                else:
                    pool.download(url, zipf)
            n = shp_para_parquet(zipf, dst, uf)
            total += n
            print(f"  ✓ {tabela} {uf or 'BR'}: {n:,}")
        feitos[tabela] = total

    for tabela in feitos:
        if not any((TEMP_DIR / "out" / tabela).glob("*.parquet")):
            continue
        remote = f"{DATASET_PATH}/{tabela}"
        subprocess.run(["ssh", BEELINK_HOST, f"mkdir -p {remote}"], check=True)
        subprocess.run(["rsync", "-a", f"{TEMP_DIR}/out/{tabela}/", f"{BEELINK_HOST}:{remote}/"], check=True)
        print(f"  ✓ push {tabela}")


if __name__ == "__main__":
    main()
