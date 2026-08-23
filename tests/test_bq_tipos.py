"""Tests for scripts/sync/_bq_tipos.py — a conversão tipada do JSON do `bq`.

Este módulo existe por causa dos 80 `tmp*.parquet` de 2026-07-05, quando o retorno
de `bq query --format=json` foi para o espelho via `pa.Table.from_pylist()` e 154
colunas tipadas chegaram como string. A correção de 2026-08-23 tinha dois defeitos
que só apareceram quando alguém finalmente **chamou** a função:

  1. `_valor` não convertia DATE/DATETIME/TIMESTAMP/TIME — devolvia a string ISO, e
     `pa.date32()` recusa `str`, então toda tabela com coluna de data falhava.
  2. o `except` caía para string em TODAS as colunas, não só na que falhou, então
     uma única coluna de data revertia a tabela inteira ao estado pré-correção.

Os testes abaixo cobrem exatamente esses dois caminhos. `schema_bq` chama o `bq`
CLI e fica de fora; o que importa aqui é a conversão, que é pura.
"""
import datetime as dt
import sys
from pathlib import Path

import pyarrow as pa
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "sync"))
import _bq_tipos as t


# ---------------------------------------------------------------------------
# Tipos escalares — o caso que já funcionava
# ---------------------------------------------------------------------------

def test_inteiro_e_float_saem_tipados():
    tb = t.para_arrow([{"a": "12", "b": "1.5"}, {"a": "7", "b": "-0.25"}],
                      {"a": "INT64", "b": "FLOAT64"})
    assert tb.schema.field("a").type == pa.int64()
    assert tb.schema.field("b").type == pa.float64()
    assert tb.column("a").to_pylist() == [12, 7]
    assert tb.column("b").to_pylist() == [1.5, -0.25]


def test_bool_aceita_as_grafias_que_o_bq_emite():
    tb = t.para_arrow([{"c": "true"}, {"c": "false"}, {"c": "1"}, {"c": "0"}],
                      {"c": "BOOL"})
    assert tb.schema.field("c").type == pa.bool_()
    assert tb.column("c").to_pylist() == [True, False, True, False]


def test_string_vazia_vira_null_nao_zero():
    # "" é como o bq representa NULL em coluna numérica; virar 0 seria pior que nulo
    tb = t.para_arrow([{"n": ""}, {"n": "5"}], {"n": "INT64"})
    assert tb.column("n").to_pylist() == [None, 5]


def test_coluna_sem_tipo_no_schema_vira_string():
    # REPEATED/RECORD chegam como None de `schema_bq`; o resto é desconhecido
    tb = t.para_arrow([{"x": "abc"}], {"x": None})
    assert tb.schema.field("x").type == pa.string()


# ---------------------------------------------------------------------------
# Temporais — o defeito nº 1. Cada um destes falhava antes.
# ---------------------------------------------------------------------------

def test_date_vira_date32_e_nao_string():
    tb = t.para_arrow([{"d": "2020-01-01"}, {"d": None}], {"d": "DATE"})
    assert tb.schema.field("d").type == pa.date32()
    assert tb.column("d").to_pylist() == [dt.date(2020, 1, 1), None]


def test_timestamp_do_bq_vem_como_epoch_em_segundos():
    # `bq query --format=json` serializa TIMESTAMP como epoch, não como ISO
    tb = t.para_arrow([{"ts": "1577836800.0"}], {"ts": "TIMESTAMP"})
    assert tb.schema.field("ts").type == pa.timestamp("us", tz="UTC")
    assert tb.column("ts").to_pylist() == [
        dt.datetime(2020, 1, 1, tzinfo=dt.timezone.utc)
    ]


def test_datetime_iso_com_T_e_com_espaco():
    tb = t.para_arrow([{"d": "2020-01-01T13:45:00"}, {"d": "2021-06-30 08:00:00"}],
                      {"d": "DATETIME"})
    assert tb.schema.field("d").type == pa.timestamp("us")
    assert tb.column("d").to_pylist() == [
        dt.datetime(2020, 1, 1, 13, 45), dt.datetime(2021, 6, 30, 8, 0),
    ]


def test_time_vira_time64():
    tb = t.para_arrow([{"h": "13:45:00"}], {"h": "TIME"})
    assert tb.schema.field("h").type == pa.time64("us")
    assert tb.column("h").to_pylist() == [dt.time(13, 45)]


def test_nenhuma_coluna_temporal_sobra_como_string():
    """O sintoma exato do bug: tudo BYTE_ARRAY no parquet."""
    linhas = [{"d": "2020-01-01", "ts": "1577836800.0",
               "dtm": "2020-01-01T00:00:00", "h": "00:00:00"}]
    tipos = {"d": "DATE", "ts": "TIMESTAMP", "dtm": "DATETIME", "h": "TIME"}
    tb = t.para_arrow(linhas, tipos)
    assert not any(f.type == pa.string() for f in tb.schema), tb.schema


# ---------------------------------------------------------------------------
# Isolamento por coluna — o defeito nº 2
# ---------------------------------------------------------------------------

def test_coluna_que_o_arrow_recusa_nao_derruba_as_vizinhas():
    """Antes, uma coluna ruim revertia a tabela INTEIRA para string.

    Um inteiro grande demais para int64 passa por `_valor` (Python não estoura) e
    só é recusado por `pa.array`, que é o caminho onde o fallback por coluna age.
    """
    grande = "9" * 30
    tb = t.para_arrow([{"n": "1", "ruim": grande}, {"n": "2", "ruim": grande}],
                      {"n": "INT64", "ruim": "INT64"})
    assert tb.schema.field("n").type == pa.int64()      # a boa segue tipada
    assert tb.schema.field("ruim").type == pa.string()  # só a ruim caiu
    assert tb.column("ruim").to_pylist() == [grande, grande]  # e sem perder o dado


def test_valor_inconversivel_vira_null_e_avisa(capsys):
    """O outro contrato, e o mais afiado: `_valor` engole o erro e devolve None.

    A coluna continua com o tipo declarado — não cai para string — e o dado some.
    É por isso que o aviso de "converteu toda para NULL" existe; sem ele isso é
    silencioso, que é o modo de falha caro neste projeto.
    """
    tb = t.para_arrow([{"x": {"nao": "conversivel"}}], {"x": "INT64"})
    assert tb.schema.field("x").type == pa.int64()
    assert tb.column("x").to_pylist() == [None]
    assert "converteu toda" in capsys.readouterr().err


def test_mistura_grande_mantem_cada_tipo():
    linhas = [{"i": "1", "f": "2.5", "b": "true", "d": "2020-01-01",
               "s": "texto", "ts": "1577836800.0"}]
    tipos = {"i": "INT64", "f": "FLOAT64", "b": "BOOL", "d": "DATE",
             "s": "STRING", "ts": "TIMESTAMP"}
    tb = t.para_arrow(linhas, tipos)
    assert [f.type for f in tb.schema] == [
        pa.int64(), pa.float64(), pa.bool_(), pa.date32(),
        pa.string(), pa.timestamp("us", tz="UTC"),
    ]


# ---------------------------------------------------------------------------
# O aviso de coluna que some
# ---------------------------------------------------------------------------

def test_avisa_quando_coluna_com_valor_converte_toda_para_null(capsys):
    t.para_arrow([{"x": "nao-e-data"}, {"x": "tambem-nao"}], {"x": "DATE"})
    assert "converteu toda" in capsys.readouterr().err


def test_nao_avisa_quando_a_coluna_ja_era_nula_na_origem(capsys):
    t.para_arrow([{"x": None}, {"x": None}], {"x": "DATE"})
    assert capsys.readouterr().err == ""


# ---------------------------------------------------------------------------
# nome_destino — o outro lado do incidente: o basename do tempfile ia junto
# ---------------------------------------------------------------------------

def test_nome_destino_comeca_do_zero_em_diretorio_vazio():
    assert t.nome_destino([]) == "000000000000.parquet"


def test_nome_destino_pega_o_proximo_livre():
    assert t.nome_destino(["000000000000.parquet",
                           "000000000001.parquet"]) == "000000000002.parquet"


def test_nome_destino_preenche_buraco_da_sequencia():
    assert t.nome_destino(["000000000000.parquet",
                           "000000000002.parquet"]) == "000000000001.parquet"


def test_nome_destino_ignora_o_que_nao_e_parquet_numerado():
    existentes = ["000000000000.parquet", "tmp315dr7qq.parquet", "_SUCCESS"]
    assert t.nome_destino(existentes) == "000000000001.parquet"


# ---------------------------------------------------------------------------
# Bordas
# ---------------------------------------------------------------------------

def test_sem_linhas_devolve_none():
    assert t.para_arrow([], {"a": "INT64"}) is None


def test_int_que_chega_com_ponto_decimal():
    # BigQuery às vezes serializa INT64 como "12.0"
    tb = t.para_arrow([{"a": "12.0"}], {"a": "INT64"})
    assert tb.column("a").to_pylist() == [12]


def test_tipo_bq_desconhecido_cai_para_string():
    tb = t.para_arrow([{"g": "POINT(0 0)"}], {"g": "GEOGRAPHY"})
    assert tb.schema.field("g").type == pa.string()
