# Servidor MCP por HTTP, com DuckDB embutido (MCP_BACKEND=inprocess).
# Contexto do build é a raiz do repo: docker build -f mcp/Dockerfile .
# docs/context/rodado-schema.json fica fora do git — gere antes do build
# (gera_schemas.py + sync_mcp_schema.py), senão o servidor não sobe.
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
# duckdb fixo: é a versão em que a trava de arquivo e o httpfs foram testados
RUN pip install --no-cache-dir "mcp==1.28.1" "pyyaml>=6.0" "duckdb==1.5.5" "uvicorn>=0.30"

RUN useradd --create-home rodado
USER rodado
WORKDIR /app
# a extensão entra na imagem: em produção o acesso externo fica desligado
RUN python -c "import duckdb; duckdb.sql('INSTALL httpfs')"

COPY --chown=rodado mcp/mcp_server.py mcp/mcp_server.py
# Arquivo por arquivo, nunca a pasta: docs/context/privado/ não pode entrar na imagem.
COPY --chown=rodado docs/context/rodado-schema.json docs/context/join_keys.md \
     docs/context/bridges.yaml docs/context/metrics.yaml docs/context/hierarchies.yaml \
     docs/context/dicionario_coverage.json docs/context/schema_dict_status.json \
     docs/context/column_codes.yaml docs/context/
COPY --chown=rodado docs/context/gotchas docs/context/gotchas

ENV MCP_BACKEND=inprocess \
    MCP_TRANSPORT=http \
    MCP_HTTP_HOST=0.0.0.0 \
    MCP_HTTP_PORT=8000 \
    MCP_TEMP_DIR=/tmp/rodado_duckdb_tmp \
    MCP_CALL_LOG=/tmp/mcp_calls.jsonl
# Em tempo de execução: MCP_DATA_ROOT, MCP_HTTP_TOKENS, MCP_HTTP_ALLOWED_HOSTS
# e, se a raiz for s3://, MCP_S3_KEY_ID / MCP_S3_SECRET / MCP_S3_ENDPOINT / MCP_S3_REGION.
EXPOSE 8000
HEALTHCHECK CMD curl -fsS http://127.0.0.1:8000/healthz || exit 1
CMD ["python", "mcp/mcp_server.py"]
