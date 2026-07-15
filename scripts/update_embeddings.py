#!/usr/bin/env python3
"""
Regenerate docs/context/table_embeddings.json to match the current
docs/context/basedosdados-schema.json (unified catalog: original Base dos
Dados mirror + independently-scraped sources, both now reflecting beelink's
actual directory tree per scripts/gera_schemas.py).

Keeps embeddings for tables that already have one (avoids re-embedding all
759 tables every run), computes new embeddings only for tables newly present
in the schema, and drops embeddings for tables no longer in the schema (so
search_tables() never surfaces a phantom table).

Usage:
    python3 scripts/update_embeddings.py                     # incremental
    python3 scripts/update_embeddings.py --rebuild           # re-embed everything
    python3 scripts/update_embeddings.py --rebuild --model paraphrase-multilingual-MiniLM-L12-v2
"""
import argparse
import json
from pathlib import Path

SCHEMA_PATH = Path("docs/context/basedosdados-schema.json")
EMBEDDINGS_PATH = Path("docs/context/table_embeddings.json")

# Scraped datasets carry no per-column descriptions (raw column names, often
# in English), which makes them invisible to Portuguese natural-language
# queries. These dataset-level hints get prefixed to the embedded text so
# semantic search finds them from PT queries too.
DATASET_HINTS = {
    "eu_sanctions": "Lista de sanções internacionais da União Europeia: pessoas e entidades sancionadas",
    "un_sanctions": "Lista de sanções internacionais da ONU (Nações Unidas): pessoas e entidades sancionadas",
    "global_ofac_sanctions": "Lista de sanções internacionais OFAC (Tesouro dos EUA): pessoas, empresas e navios sancionados",
    "global_opensanctions": "OpenSanctions: base consolidada de sanções internacionais, pessoas politicamente expostas (PEP) e entidades de risco",
    "global_icij_offshoreleaks": "ICIJ Offshore Leaks (Panama Papers, Paradise Papers, Pandora Papers): empresas offshore, paraísos fiscais e beneficiários",
    "br_comprasgov_sicaf": "SICAF: fornecedores cadastrados para licitações e compras do governo federal",
    "br_mj_consumidorgovbr": "Consumidor.gov.br: reclamações de consumidores contra empresas",
    "br_ms_sinan_violencia": "SINAN: notificações de violência doméstica, sexual e interpessoal",
    "br_pgfn_dividaativa": "PGFN: dívida ativa da União, devedores inscritos",
    "br_tce_es": "Tribunal de Contas do Espírito Santo: obras públicas, contas municipais e fiscalizações",
    "br_tce_pi": "Tribunal de Contas do Piauí: despesas, receitas e licitações estaduais e municipais",
    "br_tce_rj": "Tribunal de Contas do Rio de Janeiro: contratos, convênios, licitações e penalidades",
    "br_tce_sp": "Tribunal de Contas de São Paulo: municípios fiscalizados",
    "br_tce_to": "Tribunal de Contas do Tocantins: pautas de julgamento",
    "br_anp_combustiveis": "ANP: preços de combustíveis (gasolina, etanol, diesel) por posto e município",
    "br_anvisa_consultas": "ANVISA: registros de medicamentos e produtos de saúde",
    "br_ipea_atlasviolencia": "IPEA Atlas da Violência: séries de homicídios e criminalidade por município e UF",
    "br_mjsp_procurados": "Ministério da Justiça: pessoas procuradas pela polícia",
    "br_mjsp_ckan": "Ministério da Justiça dados abertos: sistema penitenciário (Infopen) e segurança pública",
    "br_tcu_inidoneos": "TCU: empresas declaradas inidôneas e inabilitadas para contratar com o poder público",
    "br_cnj_improbidade_administrativa": "CNJ: condenados por improbidade administrativa",
    "br_mp_pep": "Pessoas politicamente expostas (PEP) no Brasil",
    "br_me_siape": "SIAPE: servidores públicos federais e remunerações",
    "br_brasilio_holdings": "Brasil.io: sócios e holdings de empresas brasileiras",
    "us_harvard_ned": "Harvard NED: resultados de eleições presidenciais e parlamentares nos Estados Unidos (EUA) e outros países",
    "br_fipe_veiculos": "Tabela FIPE: preços médios de veículos",
    "br_caixa_sorteios": "Caixa: resultados de loterias e sorteios",
    "br_bcb_penalidades": "Banco Central: penalidades e processos sancionadores contra instituições financeiras",
    "br_tse_eleicoes": "TSE eleições no Brasil: candidatos, resultados, votação, bens, receitas e gastos/despesas de campanha eleitoral",
}


def build_text(dataset: str, table: str, columns: list) -> str:
    parts = []
    for col in columns:
        name = col.get("name", "")
        type_ = col.get("type", "")
        desc = col.get("description")
        if desc:
            parts.append(f"{name} ({type_}) - {desc}")
        else:
            parts.append(f"{name} ({type_})")
    hint = DATASET_HINTS.get(dataset)
    prefix = f"{hint}. " if hint else ""
    return f"{prefix}{dataset}.{table}: " + ", ".join(parts)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild", action="store_true",
                        help="re-embed every table (required when changing --model)")
    parser.add_argument("--model", default=None,
                        help="sentence-transformers model (default: keep the one in the embeddings file)")
    args = parser.parse_args()

    with open(SCHEMA_PATH, encoding="utf-8") as f:
        schema = json.load(f)
    with open(EMBEDDINGS_PATH, encoding="utf-8") as f:
        emb_data = json.load(f)

    model_name = args.model or emb_data["model"]
    if args.model and args.model != emb_data["model"] and not args.rebuild:
        parser.error("--model changes the vector space; pass --rebuild along with it")
    existing_by_id = {} if args.rebuild else {t["id"]: t for t in emb_data["tables"]}

    schema_ids = {f"{ds}.{tbl}" for ds, tables in schema.items() for tbl in tables}
    to_embed = []
    for ds, tables in schema.items():
        for tbl, columns in tables.items():
            table_id = f"{ds}.{tbl}"
            if table_id not in existing_by_id:
                to_embed.append((table_id, build_text(ds, tbl, columns)))

    dropped = [tid for tid in existing_by_id if tid not in schema_ids]

    print(f"Schema has {len(schema_ids)} tables")
    print(f"Already embedded (kept): {len(schema_ids) - len(to_embed)}")
    print(f"New tables to embed: {len(to_embed)}")
    print(f"Stale embeddings to drop: {len(dropped)}")

    if to_embed:
        from sentence_transformers import SentenceTransformer

        print(f"Loading model {model_name} ...")
        model = SentenceTransformer(model_name)
        texts = [t[1] for t in to_embed]
        print(f"Embedding {len(texts)} new table descriptions ...")
        vectors = model.encode(texts, show_progress_bar=True)

        for (table_id, text), vector in zip(to_embed, vectors):
            existing_by_id[table_id] = {
                "id": table_id,
                "text": text,
                "embedding": vector.tolist(),
            }

    for tid in dropped:
        del existing_by_id[tid]

    result = {
        "tables": [existing_by_id[tid] for tid in sorted(schema_ids)],
        "model": model_name,
    }
    with open(EMBEDDINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)

    print(f"\nWrote {EMBEDDINGS_PATH} ({len(result['tables'])} tables)")


if __name__ == "__main__":
    main()
