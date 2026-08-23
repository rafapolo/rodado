FROM --platform=linux/amd64 debian:12-slim

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates unzip bsdmainutils python3 python3-pip \
        less ncurses-bin && \
    curl -fsSL \
        "https://github.com/caddyserver/caddy/releases/download/v2.9.1/caddy_2.9.1_linux_amd64.tar.gz" \
        | tar -xz -C /usr/local/bin caddy && \
    chmod +x /usr/local/bin/caddy && \
    curl -fsSL \
        "https://github.com/duckdb/duckdb/releases/download/v1.5.1/duckdb_cli-linux-amd64.zip" \
        -o /tmp/duckdb.zip && \
    unzip /tmp/duckdb.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/duckdb && \
    rm /tmp/duckdb.zip && \
    curl -fsSL "https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64" \
        -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd && \
    apt-get clean && rm -rf /var/lib/apt/lists/* && \
    pip3 install --no-cache-dir --break-system-packages duckdb==1.5.1

WORKDIR /app

COPY data/basedosdados.duckdb ./data/
COPY auth.py ./
COPY start.sh ./
COPY Caddyfile ./

RUN chmod +x start.sh

EXPOSE 8080

ENTRYPOINT ["./start.sh"]
