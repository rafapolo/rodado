#!/usr/bin/env bash
# Copia para o SSD do finland (volume rodado-db-dados, /dados/local no container) os parquet
# listados em ssd_lista.txt, lidos do bucket com o mesmo caminho relativo. catalogo.py lê do SSD
# todo parquet que encontrar ali e remonta o catálogo sozinho quando a lista de cópias muda.
#
# Roda no finland, em /root/rodado-db. Idempotente: baixa de novo só o que falta ou cujo tamanho
# difere do bucket (arquivo reescrito com o mesmo nome no beelink, como as receitas de 2026).
# A lista sai do catálogo (os arquivos que as views citam), ver db/README.md.
set -uo pipefail
cd /root/rodado-db
set -a; . ./.s3; set +a
export AWS_ACCESS_KEY_ID="$S3_KEY" AWS_SECRET_ACCESS_KEY="$S3_SECRET" AWS_DEFAULT_REGION=hel1
export ENDPOINT=https://hel1.your-objectstorage.com
export DEST=/var/lib/docker/volumes/rodado-db-dados/_data/local

# tamanho de cada objeto do bucket, uma listagem por prefixo de tabela
TAMANHOS=$(mktemp)
cut -d/ -f1-2 ssd_lista.txt | sort -u | while read -r prefixo; do
  aws s3 ls --recursive --endpoint-url "$ENDPOINT" "s3://baseldosdados/$prefixo/" | awk '{print $4"\t"$3}'
done > "$TAMANHOS"
export TAMANHOS

copia() {
  local remoto local_
  remoto=$(awk -F'\t' -v f="$1" '$1 == f {print $2}' "$TAMANHOS")
  local_=$(stat -c %s "$DEST/$1" 2>/dev/null || echo -1)
  [ -n "$remoto" ] && [ "$remoto" = "$local_" ] && return 0
  mkdir -p "$(dirname "$DEST/$1")"
  # o .parcial não conta como cópia (catalogo.py só olha *.parquet); o mv é atômico
  aws s3 cp --only-show-errors --endpoint-url "$ENDPOINT" "s3://baseldosdados/$1" "$DEST/$1.parcial" \
    && mv "$DEST/$1.parcial" "$DEST/$1"
}
export -f copia
xargs -P 16 -I{} bash -c "copia {} || echo FALHOU {}" < ssd_lista.txt
rm -f "$TAMANHOS"
chown -R 1000:1000 "$DEST"
echo FIM
