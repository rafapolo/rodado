import duckdb
import os
from dotenv import load_dotenv

load_dotenv()

BUCKET       = os.environ['HETZNER_S3_BUCKET']
ENDPOINT_URL = os.environ['HETZNER_S3_ENDPOINT']
ACCESS_KEY   = os.environ['AWS_ACCESS_KEY_ID']
SECRET_KEY   = os.environ['AWS_SECRET_ACCESS_KEY']

s3_endpoint = ENDPOINT_URL.removeprefix('https://').removeprefix('http://')

con = duckdb.connect('basedosdados.duckdb')
con.execute("LOAD httpfs;")
con.execute(f"""
    SET s3_endpoint='{s3_endpoint}';
    SET s3_access_key_id='{ACCESS_KEY}';
    SET s3_secret_access_key='{SECRET_KEY}';
    SET s3_url_style='path';
    SET enable_object_cache=true;
    SET threads=4;
    SET memory_limit='6GB';
""")

schemas = [row[0] for row in con.execute(
    "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('main', 'information_schema', 'pg_catalog')"
).fetchall()]

try:
    with open("dataset_sample.txt", "a") as f:
        f.write("# Dataset samples\n\n")

        for schema in sorted(schemas):
            tables = [row[0] for row in con.execute(
                f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{schema}'"
            ).fetchall()]

            for table in sorted(tables):
                full = f"{schema}.{table}"
                try:
                    rows = con.execute(
                        f"SELECT * FROM {full} USING SAMPLE 2 ROWS"
                    ).fetchall()
                    cols = [f"{d[0]}:{d[1]}" for d in con.description]

                    f.write(f"## {schema}/{table}/\n")
                    f.write(",".join(cols) + "\n")
                    for row in rows:
                        f.write(",".join("" if v is None else str(v) for v in row) + "\n")
                    f.write("\n")
                    f.flush()
                    print(f"done: {full}")
                except Exception as e:
                    f.write(f"## {schema}/{table}/\n[error: {e}]\n\n")
                    f.flush()
                    print(f"error: {full}: {e}")

except KeyboardInterrupt:
    print("\nCancelled.")

con.close()
