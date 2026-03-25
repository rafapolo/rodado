FROM debian:12-slim

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates unzip && \
    curl -fsSL https://caddyserver.com/install.sh | bash && \
    curl -fsSL \
        "https://github.com/duckdb/duckdb/releases/latest/download/duckdb_cli-linux-amd64.zip" \
        -o /tmp/duckdb.zip && \
    unzip /tmp/duckdb.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/duckdb && \
    rm /tmp/duckdb.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY basedosdados.duckdb Caddyfile start.sh ./
RUN chmod +x start.sh

EXPOSE 8080

ENTRYPOINT ["./start.sh"]
