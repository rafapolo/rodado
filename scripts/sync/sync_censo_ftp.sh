#!/bin/bash
# Mirrors the IBGE FTP folders NOT already covered by basedosdados.duckdb into
# ~/ibge_ftp_raw/<Folder>/, in priority order. Resumable: safe to kill and re-run
# anytime — completed folders are skipped, partial ones resume via lftp --continue.
# See tasks/sync_censo.md for the full plan and status board.

set -u

DEST_ROOT="$HOME/ibge_ftp_raw"
STATUS_FILE="$DEST_ROOT/.sync_status"
LOG_FILE="$DEST_ROOT/sync.log"
FTP_HOST="ftp.ibge.gov.br"

mkdir -p "$DEST_ROOT"
touch "$STATUS_FILE"

# Priority order: tier 1 (thematic value) -> tier 2 -> tier 3, smallest-first within
# each tier, with Programa/Estatcart forced last regardless (large, low-confidence value).
FOLDERS=(
  "pense_avaliacao_nutricional_2009"
  "Caracteristicas_etnico_raciais_populacao"
  "Mobilidade_Socio_Ocupacional_2014"
  "seguranca_alimentar_2004_2009"
  "Tabuas_Abreviadas_de_Mortalidade"
  "vitimizacao_acesso_justica_2009"
  "Aspectos_das_relacoes_de_trabalho_e_sindicalicacao"
  "Estatisticas_de_Genero"
  "Tabuas_Completas_de_Mortalidade"
  "seguranca_alimentar_2013"
  "PNS"
  "seculoxx"
  "Contas_Regionais"
  "Registro_Civil"
  "Contas_Nacionais"
  "pense"
  "Censo_Agropecuario"
  "Matriz_insumo-produto"
  "Aspectos_e_cuidados_das_criancas"
  "Retroprojecao_da_populacao"
  "Educacao_e_qualificacao_profissional"
  "Economia_Turismo"
  "Meio_Ambiente"
  "Pratica_de_esporte_e_atividade_fisica"
  "acesso_ao_cadastro_unico_2014"
  "Indices_de_Precos_Consumidor_Harmonizado"
  "Assistencia_Social_Privada_Sem_Fins_Lucrativos"
  "Demografia_das_Empresas_e_Estatisticas_de_Empreendedorismo"
  "Tecnologias_de_Informacao_e_Comunicacao_nas_Empresas"
  "Setor_Publico"
  "Economia_da_Saude"
  "Estatisticas_de_Empreendedorismo"
  "Demografia_das_Empresas"
  "panorama_saude_brasil_20032008"
  "Estatisticas_Sociais"
  "Acesso_a_internet_e_posse_celular"
  "Estatisticas_Vitais"
  "Indicadores_Desenvolvimento_Sustentavel"
  "Fundacoes_Privadas_e_Associacoes"
  "Industria_da_Construcao"
  "Projecao_da_Populacao"
  "Contagem_da_Populacao"
  "Economia_Cadastro_de_Empresas"
  "Indicadores_Sociais"
  "Comercio_e_Servicos"
  "Industrias_Extrativas_e_de_Transformacao"
  "Pesquisa_de_Servicos_de_Tecnologia_da_Informacao"
  "Salario_Minimo"
  "Artigos_e_Apresentacoes"
  "Pesquisa_de_Esporte"
  "Audiencia_Publica"
  "Inovacao"
  "Micro_Empresa"
  "Dimensionamento_em_areas_indigenas_e_quilombolas_para_acoes_de_enfrentamento_COVID-19"
  "Pulso_Empresa"
  "Programa_de_Comparacao_Internacional_PCI"
  "Estatisticas_dos_Cadastros_de_Microempreendedores_Individuais"
  "Atualizacao_Aplicativos"
  "Documentos"
  "englishpub"
  "Metodos_Alternativos_Censo"
  "Informacoes_Gerais_e_Referencia"
  "Precos_Custos_e_Indices_da_Construcao_Civil"
  "Estoque"
  "Dados_Genericos"
  "edital"
  "Programa"
  "Estatcart"
)

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

is_done() {
  grep -qxF "$1	done" "$STATUS_FILE"
}

mark_done() {
  echo -e "$1\tdone" >> "$STATUS_FILE"
}

log "=== sync_censo_ftp.sh starting, ${#FOLDERS[@]} folders total ==="

for folder in "${FOLDERS[@]}"; do
  if is_done "$folder"; then
    log "skip (already done): $folder"
    continue
  fi

  log "start: $folder"
  mkdir -p "$DEST_ROOT/$folder"

  attempt=0
  while true; do
    attempt=$((attempt + 1))
    lftp -c "
      set net:timeout 20;
      set net:max-retries 0;
      set net:reconnect-interval-base 30;
      set net:reconnect-interval-max 600;
      set mirror:parallel-transfer-count 3;
      open ftp://$FTP_HOST;
      mirror --continue --verbose=1 \"/$folder\" \"$DEST_ROOT/$folder\";
    " >> "$LOG_FILE" 2>&1

    status=$?
    if [ $status -eq 0 ]; then
      log "done ($folder), attempt $attempt"
      mark_done "$folder"
      break
    else
      log "lftp exited $status on $folder (attempt $attempt) — retrying in 30s"
      sleep 30
    fi
  done
done

log "=== sync_censo_ftp.sh: ALL FOLDERS DONE ==="
