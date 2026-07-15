#!/usr/bin/env python3
"""
Fetch ANA (Agencia Nacional de Aguas e Saneamento Basico) telemetric station
inventory -> Parquet -> beelink.

Source: legacy SOAP service telemetriaws1.ana.gov.br/ServiceANA.asmx. ANA's
newer REST API (hidrowebservice, has a Swagger UI at
ana.gov.br/hidrowebservice/swagger-ui) requires an OAuth token that is only
issued after emailing hidro@ana.gov.br with a justification -- confirmed
still true as of the manual dated 2026-02-20 (no self-service signup exists),
so that path is out per this project's "don't request credentials" policy.

The legacy ASMX service, however, is genuinely open: GET on the .asmx path
returns HTTP 200 with the auto-generated ASP.NET help page (not a 405), and
POSTing a SOAP 1.1 envelope works with no auth at all. Two gotchas that took
some trial and error to work around:
  1. It's SOAP-only -- a GET (or POST without a body) returns a generic
     help page, not data. Needs a real POST with a `SOAPAction` header and
     an XML envelope.
  2. The WSDL's declared targetNamespace is "http://MRCS/" (WITH a trailing
     slash). Every element in the request body must be qualified with that
     exact namespace (xmlns="http://MRCS/") -- get that wrong (e.g. drop
     the trailing slash) and the service silently returns a canned
     input-validation error instead of an HTTP error, no matter what values
     you send, which looks confusingly like the input itself is invalid.

This script calls the `HidroInventario` operation (station catalog) once
for tpEst=1 (fluviometrica/river-level stations) and once for tpEst=2
(pluviometrica/rain-gauge stations), both filtered to telemetrica=1
(telemetric stations only, matching the "estacoes" target table -- these
are the real-time-reporting stations, not ANA's much larger historical
non-telemetric station network). That's the full station inventory in 2
calls, ~4,300+ fluviometric stations alone.

Scope note: recent readings (the `DadosHidrometeorologicosGerais`
operation) take a single station code + date range per call -- there's no
bulk "all stations' latest reading" operation in this legacy service, so
pulling readings for the full station list would mean several thousand
sequential SOAP calls (one per station), which is a much bigger, slower
pipeline than this station-catalog pass. Left out of scope here; the
station inventory (with lat/lon, river, basin, operator, and the exact set
of measurement types each station reports) is itself the useful join target
for `br_ana_telemetria/estacoes`.

Usage:
    python3 scripts/scrap/ana_telemetria.py
"""

import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

BEELINK_HOST = "beelink"
BEELINK_PATH = "~/rodado/br_ana_telemetria/estacoes"

SOAP_URL = "http://telemetriaws1.ana.gov.br/ServiceANA.asmx"
NS = "http://MRCS/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
TEMP_DIR = Path(
    "/private/tmp/claude-501/-Users-polux-Projetos-rodado/c780c9c0-b6b3-44b0-964e-08a3b2f2024c/scratchpad/ana_telemetria"
)

TIPO_ESTACAO = {"1": "fluviometrica", "2": "pluviometrica"}

ENVELOPE_TMPL = """<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <HidroInventario xmlns="{ns}">
      <codEstDE></codEstDE>
      <codEstATE></codEstATE>
      <tpEst>{tp_est}</tpEst>
      <nmEst></nmEst>
      <nmRio></nmRio>
      <codSubBacia></codSubBacia>
      <codBacia></codBacia>
      <nmMunicipio></nmMunicipio>
      <nmEstado></nmEstado>
      <sgResp></sgResp>
      <sgOper></sgOper>
      <telemetrica>{telemetrica}</telemetrica>
    </HidroInventario>
  </soap:Body>
</soap:Envelope>"""


def fetch_inventario(session: requests.Session, tp_est: str) -> list[dict]:
    body = ENVELOPE_TMPL.format(ns=NS, tp_est=tp_est, telemetrica="1")
    resp = session.post(
        SOAP_URL,
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "text/xml; charset=utf-8",
            "SOAPAction": "http://MRCS/HidroInventario",
        },
        timeout=120,
    )
    resp.raise_for_status()

    root = ET.fromstring(resp.content)
    rows = []
    # Result payload is a MS ADO.NET diffgram; namespace-agnostic search for
    # <Table> rows since the inner "Estacoes"/"Table" elements use the
    # empty/default namespace, not a fixed prefix.
    for table_el in root.iter():
        if table_el.tag.rsplit("}", 1)[-1] != "Table":
            continue
        record = {"tipo_estacao_consulta": TIPO_ESTACAO.get(tp_est, tp_est)}
        for child in table_el:
            tag = child.tag.rsplit("}", 1)[-1]
            record[tag] = child.text
        rows.append(record)
    return rows


def main():
    import pyarrow as pa
    import pyarrow.parquet as pq

    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": UA})

    all_rows = []
    for tp_est in ["1", "2"]:
        label = TIPO_ESTACAO[tp_est]
        print(f"Fetching HidroInventario tpEst={tp_est} ({label}, telemetrica=1)...")
        rows = fetch_inventario(session, tp_est)
        print(f"  {len(rows)} stations")
        all_rows.extend(rows)

    print(f"\nTotal rows: {len(all_rows)}")
    if not all_rows:
        print("No rows fetched -- aborting, not pushing an empty file.")
        return 1

    # Columns vary slightly between fluviometrica/pluviometrica payloads
    # (extra Periodo* fields) -- pyarrow's from_pylist handles the union of
    # keys with nulls for missing ones.
    table = pa.Table.from_pylist(all_rows)
    parquet_path = TEMP_DIR / "estacoes.parquet"
    pq.write_table(table, str(parquet_path), compression="zstd")
    print(f"Wrote {parquet_path} ({parquet_path.stat().st_size / 1e6:.1f} MB, {table.num_rows} rows)")

    subprocess.run(f"ssh {BEELINK_HOST} 'mkdir -p {BEELINK_PATH}'", shell=True, check=True)
    result = subprocess.run(
        f"rsync -av {parquet_path} {BEELINK_HOST}:{BEELINK_PATH}/",
        shell=True,
    )
    if result.returncode != 0:
        print("rsync failed", file=sys.stderr)
        return 1

    print(f"Pushed to {BEELINK_HOST}:{BEELINK_PATH}/{parquet_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
