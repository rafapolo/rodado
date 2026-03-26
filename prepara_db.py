import os
import duckdb
import boto3
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

BUCKET       = os.environ['HETZNER_S3_BUCKET']
ENDPOINT_URL = os.environ['HETZNER_S3_ENDPOINT']
ACCESS_KEY   = os.environ['AWS_ACCESS_KEY_ID']
SECRET_KEY   = os.environ['AWS_SECRET_ACCESS_KEY']

# DuckDB expects the endpoint without scheme
s3_endpoint = ENDPOINT_URL.removeprefix('https://').removeprefix('http://')

# Lista todos os objetos do bucket de uma vez, agrupando por dataset/tabela
s3 = boto3.client('s3',
                  endpoint_url=ENDPOINT_URL,
                  aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY)
paginator = s3.get_paginator('list_objects_v2')

table_files = defaultdict(lambda: defaultdict(list))
for page in paginator.paginate(Bucket=BUCKET):
    for obj in page.get('Contents', []):
        key = obj['Key']
        if not key.endswith('.parquet'):
            continue
        parts = key.split('/')
        if len(parts) >= 3:
            dataset, table = parts[0], parts[1]
            table_files[dataset][table].append(f"s3://{BUCKET}/{key}")

# Cria conexão DuckDB e configura S3
con = duckdb.connect('basedosdados.duckdb')
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute(f"""
    SET s3_endpoint='{s3_endpoint}';
    SET s3_access_key_id='{ACCESS_KEY}';
    SET s3_secret_access_key='{SECRET_KEY}';
    SET s3_url_style='path';
    SET enable_object_cache=true;
    SET threads=4;
    SET memory_limit='6GB';
    SET preserve_insertion_order=false;
    SET http_keep_alive=true;
    SET http_retries=3;
""")

# Cria schemas e views com lista explícita de arquivos
for dataset, tables in table_files.items():
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {dataset}")
    for table, files in tables.items():
        file_list = ", ".join(f"'{f}'" for f in sorted(files))
        try:
            con.execute(f"""
                CREATE OR REPLACE VIEW {dataset}.{table} AS
                SELECT * FROM read_parquet([{file_list}], hive_partitioning=true, union_by_name=true)
            """)
            print(f"✓ {dataset}.{table} ({len(files)} files)")
        except Exception as e:
            if 'Geoparquet' in str(e) or 'geometria' in str(e) or 'geometry' in str(e).lower():
                print(f"  skip (geoparquet) {dataset}.{table}")
            else:
                raise

con.close()
print("Done! Open with: duckdb --ui basedosdados.duckdb")
