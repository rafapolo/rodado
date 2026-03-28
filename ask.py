#!/usr/bin/env python3
"""
ask.py — Send a Portuguese question to Gemini and get back SQL.

Usage:
    python ask.py "Quantos pedidos foram feitos por cliente no último mês?"
    python ask.py "Qual a taxa de mortalidade infantil por município em 2020?"

Env vars:
    GEMINI_API_KEY  — required
    SCHEMA_FILE     — path to DDL file (default: context/schema_compact_inline.txt)
    GEMINI_MODEL    — model slug (default: gemini-2.0-flash-latest)
"""

import os
import sys
import json
import requests
import duckdb
from dotenv import load_dotenv

load_dotenv()

SCHEMA_FILE = os.getenv("SCHEMA_FILE", "context/schema_compact_inline.txt")
MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
DB_FILE = os.getenv("DB_FILE", "basedosdados.duckdb")


def load_schema(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def ask(question: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        sys.exit("Error: GEMINI_API_KEY not set")

    schema_ddl = load_schema(SCHEMA_FILE)

    system_prompt = (
        "You are a SQL expert for Base dos Dados (basedosdados.org), "
        "a Brazilian open data warehouse with tables accessed via DuckDB.\n\n"
        "Rules:\n"
        "- Use DuckDB syntax. Tables are referenced as dataset.table.\n"
        "- Only use columns from the provided DDL — never invent column names.\n"
        "- Add WHERE filters on ano, sigla_uf, or id_municipio whenever possible.\n"
        "- Return ONLY the SQL query, no explanation, no markdown fences.\n\n"
        f"Schema DDL:\n\n{schema_ddl}"
    )

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models"
        f"/{MODEL}:generateContent"
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "parts": [{"text": question}]
            }
        ]
    }

    response = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "X-goog-api-key": api_key,
        },
        data=json.dumps(payload),
        timeout=300,
    )

    response.raise_for_status()
    result = response.json()

    return result["candidates"][0]["content"]["parts"][0]["text"].strip()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {sys.argv[0]} \"<pergunta em português>\"", file=sys.stderr)
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    print(f"Question: {question}\n", file=sys.stderr)
    print(f"Model:    {MODEL}\n", file=sys.stderr)

    sql = ask(question)

    print(f"\n── SQL ──────────────────────────────────────────\n{sql}\n", file=sys.stderr)

    con = duckdb.connect(DB_FILE, read_only=True)
    rel = con.sql(sql)

    # box mode: build borders from column names + data
    cols = rel.columns
    rows = rel.fetchall()

    if not rows:
        print("(no rows returned)")
        return

    col_widths = [len(c) for c in cols]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val) if val is not None else "NULL"))

    def bar(left, mid, right, fill="─"):
        return left + mid.join(fill * (w + 2) for w in col_widths) + right

    header = "│" + "│".join(f" {c:{w}} " for c, w in zip(cols, col_widths)) + "│"

    print(bar("┌", "┬", "┐"))
    print(header)
    print(bar("├", "┼", "┤"))
    for row in rows:
        vals = [str(v) if v is not None else "NULL" for v in row]
        print("│" + "│".join(f" {v:{w}} " for v, w in zip(vals, col_widths)) + "│")
    print(bar("└", "┴", "┘"))
    print(f"\n{len(rows)} row(s)")


if __name__ == "__main__":
    main()
