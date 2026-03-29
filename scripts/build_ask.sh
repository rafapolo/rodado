#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "=== Building ask binary for Linux x86_64 ==="
echo "Using Debian x86_64 container for native build..."

# Build in an x86_64 Debian container - this gives us a real x86_64 environment
# so we can build natively without cross-compilation complexity
# Use ask/ as context to avoid .dockerignore excluding src/
docker build \
    --platform linux/amd64 \
    -t ask-builder \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    -f - ask/ <<'EOF'
FROM rust:1.85-slim

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        build-essential pkg-config libssl-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY . ./
RUN cargo build --release --locked

FROM scratch
COPY --from=0 /build/target/release/ask /ask
EOF

echo "=== Extracting binary ==="
# Extract the binary from the container
docker run --rm --platform linux/amd64 ask-builder cat /ask > ./ask/target/release/ask

# Make it executable
chmod +x ./ask/target/release/ask

echo "=== Binary built successfully ==="
file ./ask/target/release/ask
ls -lh ./ask/target/release/ask
