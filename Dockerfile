FROM debian:12-slim

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates unzip bsdmainutils python3 \
        less ncurses-bin build-essential pkg-config libssl-dev && \
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
    duckdb :memory: "INSTALL httpfs;" && \
    curl -fsSL "https://github.com/tsl0922/ttyd/releases/latest/download/ttyd.x86_64" \
        -o /usr/local/bin/ttyd && \
    chmod +x /usr/local/bin/ttyd

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.cargo/bin:${PATH}" \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

WORKDIR /app

COPY basedosdados.duckdb Caddyfile start.sh auth.py ./
COPY ask/ ./ask/
RUN cd ask && /root/.cargo/bin/cargo build --release && \
    mv target/release/ask /app/ask && \
    rm -rf target && \
    file /app/ask && \
    ldd /app/ask || true
RUN chmod +x start.sh /app/ask

EXPOSE 8080

ENTRYPOINT ["./start.sh"]
