import os
import duckdb
import boto3
from dotenv import load_dotenv

load_dotenv()

S3_ENDPOINT = os.environ["HETZNER_S3_ENDPOINT"]          # https://hel1.your-objectstorage.com
S3_BUCKET   = os.environ["HETZNER_S3_BUCKET"]            # baseldosdados
ACCESS_KEY  = os.environ["AWS_ACCESS_KEY_ID"]
SECRET_KEY  = os.environ["AWS_SECRET_ACCESS_KEY"]

# Strip protocol for DuckDB httpfs (expects bare hostname)
s3_host = S3_ENDPOINT.removeprefix("https://").removeprefix("http://")

con = duckdb.connect('basedosdados.duckdb')

con.execute("INSTALL httpfs; LOAD httpfs;")
con.execute(f"""
    CREATE OR REPLACE PERSISTENT SECRET hetzner (
        TYPE S3,
        KEY_ID '{ACCESS_KEY}',
        SECRET '{SECRET_KEY}',
        ENDPOINT '{s3_host}',
        URL_STYLE 'path'
    );
""")

# List all dataset/table prefixes in the bucket
s3 = boto3.client(
    's3',
    endpoint_url=S3_ENDPOINT,
    aws_access_key_id=ACCESS_KEY,
    aws_secret_access_key=SECRET_KEY,
)
paginator = s3.get_paginator('list_objects_v2')

datasets = {}
for page in paginator.paginate(Bucket=S3_BUCKET, Delimiter='/'):
    for prefix in page.get('CommonPrefixes', []):
        dataset = prefix['Prefix'].rstrip('/')
        datasets[dataset] = []
        for page2 in paginator.paginate(Bucket=S3_BUCKET,
                                        Prefix=dataset + '/',
                                        Delimiter='/'):
            for p in page2.get('CommonPrefixes', []):
                table = p['Prefix'].rstrip('/').split('/')[-1]
                datasets[dataset].append(table)

# Create schemas and views
for dataset, tables in datasets.items():
    con.execute(f"CREATE SCHEMA IF NOT EXISTS {dataset}")
    for table in tables:
        path = f"s3://{S3_BUCKET}/{dataset}/{table}/*.parquet"
        con.execute(f"""
            CREATE OR REPLACE VIEW {dataset}.{table} AS
            SELECT * FROM '{path}'
        """)
        print(f"✓ {dataset}.{table}")

con.close()
print("Done! Open with: duckdb --ui basedosdados.duckdb")
