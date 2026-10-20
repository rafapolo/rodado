# db.rodado.xyz num container só, no finland: Caddy (senha, token, prévia de link) na
# frente, e atrás dele o terminal (ttyd + terminal.py) e o endpoint (consulta.py), que leem
# os parquet do bucket s3://baseldosdados pelo catálogo que catalogo.py mantém em /dados.
FROM caddy:2.10.2-alpine AS caddy

FROM python:3.12-slim
ADD --chmod=755 https://github.com/tsl0922/ttyd/releases/download/1.7.7/ttyd.x86_64 /usr/local/bin/ttyd
COPY --from=caddy /usr/bin/caddy /usr/local/bin/caddy
RUN pip install --no-cache-dir duckdb==1.5.5 prompt_toolkit==3.0.51 pygments==2.19.2 wcwidth==0.2.13 \
    "mcp==1.28.1" "pyyaml>=6.0" "uvicorn>=0.30" \
 && useradd -m rodado && mkdir -p /dados && chown rodado /dados
USER rodado
# o autoinstall fica desligado em tempo de consulta: a extensão já vem na imagem
RUN python -c "import duckdb; duckdb.connect().execute('INSTALL httpfs')"
WORKDIR /app
COPY proxy/Caddyfile /etc/caddy/Caddyfile
COPY proxy/og.html /srv/og.html
COPY rodado_sql.py consulta.py terminal.py catalogo.py index.html llm.md contexto.json inicia.sh ./
# o servidor MCP (/mcp) e a camada semântica que ele lê; o deploy põe em mcp/ a cópia de
# mcp/mcp_server.py e dos arquivos de docs/context — nunca docs/context/privado/
COPY mcp/ ./mcp/
ENV RODADO_DB=/dados/catalogo.duckdb PROMPT_TOOLKIT_NO_CPR=1 \
    MCP_CONTEXT_DIR=/app/mcp/context MCP_CALL_LOG=/tmp/mcp_calls.jsonl
EXPOSE 8080
CMD ["./inicia.sh"]
