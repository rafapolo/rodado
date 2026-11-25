#!/usr/bin/env bash
# Refaz no SSD do finland as tabelas dadas, depois de uma atualização no beelink + S3:
# troca em ssd_lista.txt as linhas desses prefixos pela listagem atual do bucket, apaga do SSD
# os parquet desses prefixos que não existem mais no bucket (o 202611_parcial que virou
# 202611, por exemplo) e roda o ssd_copia.sh. O catálogo remonta sozinho na volta seguinte
# (ou na hora: catalogo.py --uma-vez).
#
#   ./ssd_prefixos.sh br_pncp/contratos br_mgi_pncp/contratacao br_mgi_pncp/ata_registro_preco
#
# Roda no finland, em /root/rodado-db. Sem isso, o catálogo segue lendo a versão velha do SSD
# (ele prefere o SSD ao bucket): foi o que aconteceu com 44 arquivos em 2026-11-02.
set -euo pipefail
cd /root/rodado-db
[ $# -gt 0 ] || { echo "uso: $0 <dataset/tabela> ..."; exit 1; }
set -a; . ./.s3; set +a
export AWS_ACCESS_KEY_ID="$S3_KEY" AWS_SECRET_ACCESS_KEY="$S3_SECRET" AWS_DEFAULT_REGION=hel1
ENDPOINT=https://hel1.your-objectstorage.com
DEST=/var/lib/docker/volumes/rodado-db-dados/_data/local
novo=$(mktemp); manter=$(mktemp)
for p in "$@"; do
  aws s3 ls --recursive --endpoint-url "$ENDPOINT" "s3://baseldosdados/$p/" | awk '{print $4}' | grep '\.parquet$' >> "$novo" || true
done
[ -s "$novo" ] || { echo "nada no bucket para $*: lista não mexida"; exit 1; }
cp -p ssd_lista.txt "ssd_lista.txt.antes_$(date +%Y%m%d-%H%M%S)"
padrao=$(printf '%s\n' "$@" | sed 's#[.]#\\.#g; s#^#^#; s#$#/#' | paste -sd'|')
grep -Ev "$padrao" ssd_lista.txt > "$manter" || true
cat "$manter" "$novo" > ssd_lista.txt
# o que saiu do bucket sai do SSD
for p in "$@"; do
  [ -d "$DEST/$p" ] || continue
  (cd "$DEST" && find "$p" -name '*.parquet') | grep -vxF -f "$novo" | while read -r f; do
    rm -f "$DEST/$f" && echo "saiu do SSD: $f"
  done || true   # grep sem linha devolve 1, e com pipefail o set -e matava o script aqui
done
echo "$(wc -l < "$novo") arquivos de $# tabela(s) na lista"
./ssd_copia.sh
# marcador por tabela: a lista do bucket. O catalogo.py só lê do SSD uma view com curinga
# (br_pncp.contratos/*/*.parquet) quando os arquivos locais batem com ela; sem cópia completa, fica no S3
for p in "$@"; do
  grep "^$p/" "$novo" > "$DEST/$p/.ssd_completo.tmp" && mv "$DEST/$p/.ssd_completo.tmp" "$DEST/$p/.ssd_completo"
  faltam=$(while read -r f; do [ -f "$DEST/$f" ] || echo "$f"; done < "$DEST/$p/.ssd_completo" | wc -l)
  echo "$p: $(wc -l < "$DEST/$p/.ssd_completo") no bucket, $faltam faltando no SSD"
done
rm -f "$novo" "$manter"
