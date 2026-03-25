import os
import duckdb
import boto3
from dotenv import load_dotenv

load_dotenv()

BUCKET       = os.environ['HETZNER_S3_BUCKET']
ENDPOINT_URL = os.environ['HETZNER_S3_ENDPOINT']
ACCESS_KEY   = os.environ['AWS_ACCESS_KEY_ID']
SECRET_KEY   = os.environ['AWS_SECRET_ACCESS_KEY']

# DuckDB expects the endpoint without scheme
s3_endpoint = ENDPOINT_URL.removeprefix('https://').removeprefix('http://')

# Lista todos os prefixos no bucket (dataset/tabela)
s3 = boto3.client('s3',
                  endpoint_url=ENDPOINT_URL,
                  aws_access_key_id=ACCESS_KEY,
                  aws_secret_access_key=SECRET_KEY)
paginator = s3.get_paginator('list_objects_v2')

datasets = {}
for page in paginator.paginate(Bucket=BUCKET, Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        dataset = prefix['Prefix'].rstrip('/')
        datasets[dataset] = []
        for page2 in paginator.paginate(Bucket=BUCKET,
                                         Prefix=dataset+'/',
                                         Delimiter='/'):
            for p in page2.get('CommonPrefixes', []):
                table = p['Prefix'].rstrip('/').split('/')[-1]
                datasets[dataset].append(table)

# Cria conexão DuckDB e configura S3
con = duckdb.connect('basedosdados3.duckdb')
con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute(f"""
    SET s3_endpoint='{s3_endpoint}';
    SET s3_access_key_id='{ACCESS_KEY}';
    SET s3_secret_access_key='{SECRET_KEY}';
    SET s3_url_style='path';
""")

# Cria schemas e views
for dataset, tables in datasets.items():
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {dataset}")
    for table in tables:
        path = f"s3://{BUCKET}/{dataset}/{table}/*.parquet"
        try:
            con.execute(f"""
                CREATE OR REPLACE VIEW {dataset}.{table} AS
                SELECT * FROM read_parquet('{path}', hive_partitioning=true)
            """)
            print(f"✓ {dataset}.{table}")
        except Exception as e:
            if 'Geoparquet' in str(e) or 'geometria' in str(e) or 'geometry' in str(e).lower():
                print(f"  skip (geoparquet) {dataset}.{table}")
            else:
                raise

con.close()
print("Done! Open with: duckdb --ui basedosdados3.duckdb")
