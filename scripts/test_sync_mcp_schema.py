"""Testes do mapeamento de tipo de sync_mcp_schema.py (B37).

    python3 scripts/test_sync_mcp_schema.py
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_mcp_schema import logico  # noqa: E402


def t(tipo):
    u = Counter()
    return logico(tipo, u), u


def test_struct_vira_campos_nao_colunas_soltas():
    # br_pncp.contratos: o que o DESCRIBE devolve no beelink
    r, u = t("STRUCT(ufNome VARCHAR, codigoIbge VARCHAR, ufSigla VARCHAR)")
    assert r == {"type": "STRUCT", "fields": [
        {"name": "ufNome", "type": "STRING"},
        {"name": "codigoIbge", "type": "STRING"},
        {"name": "ufSigla", "type": "STRING"},
    ]}
    assert not u


def test_struct_aninhado_e_nome_entre_aspas():
    r, _ = t('STRUCT(a STRUCT(b DECIMAL(18,2), "c d" DATE), e BIGINT)')
    assert r["fields"][0] == {"name": "a", "type": "STRUCT", "fields": [
        {"name": "b", "type": "FLOAT"}, {"name": "c d", "type": "DATE"}]}
    assert r["fields"][1] == {"name": "e", "type": "INTEGER"}


def test_tipos_logicos_que_o_parquet_schema_escondia():
    assert t("DATE")[0] == {"type": "DATE"}
    assert t("TIMESTAMP WITH TIME ZONE")[0] == {"type": "TIMESTAMP"}
    assert t("TIME WITH TIME ZONE")[0] == {"type": "TIME"}
    assert t("DECIMAL(18,2)")[0] == {"type": "FLOAT"}
    assert t("GEOMETRY")[0] == {"type": "GEOMETRY"}
    assert t('"NULL"')[0] == {"type": "NULL"}


def test_lista():
    assert t("VARCHAR[]")[0] == {"type": "LIST", "element": "STRING"}
    r, _ = t("STRUCT(x BIGINT)[]")
    assert r == {"type": "LIST", "element": "STRUCT", "fields": [{"name": "x", "type": "INTEGER"}]}


def test_schema_antigo_fisico_continua_mapeando():
    assert t("INT64")[0] == {"type": "INTEGER"}
    assert t("BYTE_ARRAY")[0] == {"type": "STRING"}


def test_desconhecido_fica_como_veio_e_e_contado():
    r, u = t("HUGEWEIRD")
    assert r == {"type": "HUGEWEIRD"} and u["HUGEWEIRD"] == 1


if __name__ == "__main__":
    n = 0
    for nome, f in list(globals().items()):
        if nome.startswith("test_") and callable(f):
            f()
            n += 1
    print(f"{n} testes ok")
