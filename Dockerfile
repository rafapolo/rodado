FROM --platform=linux/amd64 rust:latest AS builder

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        build-essential pkg-config libssl-dev curl unzip musl-tools && \
    curl -fsSL https://github.com/duckdb/duckdb/releases/download/v1.5.1/libduckdb-linux-amd64.zip \
        -o /tmp/libduckdb.zip && \
    unzip -o /tmp/libduckdb.zip -d /usr/local && \
    cp /usr/local/libduckdb.so /usr/local/lib/ && \
    cp /usr/local/duckdb.hpp /usr/local/include/ && \
    cp /usr/local/duckdb.h /usr/local/include/ && \
    ldconfig && \
    rm /tmp/libduckdb.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /build/ask
COPY ask/Cargo.toml ask/Cargo.lock ./
COPY ask/src ./src

RUN rustup target add x86_64-unknown-linux-musl && \
    mkdir -p /build/ask/.cargo && \
    printf '[target.x86_64-unknown-linux-musl]\nlinker = "gcc"\n' > /build/ask/.cargo/config.toml && \
    printf 'rustflags = ["-L", "/usr/local/lib", "-C", "target-feature=+crt-static"]\n' >> /build/ask/.cargo/config.toml && \
    sed -i 's/features = \["bundled"\]/default-features = false/' Cargo.toml && \
    rm -f Cargo.lock && \
    cargo build --release --target x86_64-unknown-linux-musl

WORKDIR /build/dbquery
COPY dbquery/Cargo.toml dbquery/Cargo.lock* ./
COPY dbquery/src ./src

RUN mkdir -p /build/dbquery/.cargo && \
    printf '[target.x86_64-unknown-linux-musl]\nlinker = "gcc"\n' > /build/dbquery/.cargo/config.toml && \
    printf 'rustflags = ["-C", "target-feature=+crt-static"]\n' >> /build/dbquery/.cargo/config.toml && \
    cargo build --release --target x86_64-unknown-linux-musl

FROM --platform=linux/amd64 debian:12-slim

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        curl ca-certificates unzip bsdmainutils python3 \
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
    curl -fsSL https://github.com/duckdb/duckdb/releases/download/v1.5.1/libduckdb-linux-amd64.zip \
        -o /tmp/libduckdb.zip && \
    unzip -o /tmp/libduckdb.zip -d /usr/local && \
    cp /usr/local/libduckdb.so /usr/local/lib/ && \
    ldconfig && \
    rm /tmp/libduckdb.zip && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /build/ask/target/x86_64-unknown-linux-musl/release/ask ./ask
COPY --from=builder /build/dbquery/target/x86_64-unknown-linux-musl/release/dbquery ./dbquery
COPY ask/system_prompt.md ./system_prompt.md
COPY data/basedosdados.duckdb ./data/
COPY context ./context/
COPY auth.py ./
COPY start.sh ./
COPY Caddyfile ./

RUN chmod +x start.sh ask dbquery

EXPOSE 8080

ENTRYPOINT ["./start.sh"]
