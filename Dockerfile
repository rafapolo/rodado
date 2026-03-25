FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive

# System deps + Caddy
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv \
        curl ca-certificates unzip && \
    # Caddy
    curl -fsSL https://caddyserver.com/install.sh | bash && \
    # DuckDB CLI
    curl -fsSL \
        "https://github.com/duckdb/duckdb/releases/latest/download/duckdb_cli-linux-amd64.zip" \
        -o /tmp/duckdb.zip && \
    unzip /tmp/duckdb.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/duckdb && \
    rm /tmp/duckdb.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY prepara_db.py Caddyfile start.sh ./
RUN chmod +x start.sh

EXPOSE 8080

ENTRYPOINT ["./start.sh"]
