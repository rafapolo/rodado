-- Conserta br_mj_consumidorgovbr.reclamacoes: o arquivo 'Base Completa Consumidor.gov.br - Abril_2022'
-- (154.493 reclamações finalizadas em abr/2022, abertas fev-abr) foi lido numa coluna só,
-- com os 30 campos separados por tab e o cabeçalho como nome da coluna. Nenhum outro arquivo tem
-- finalização em abr/2022, então recuperar não duplica. Data Finalização vira ISO, como nos vizinhos.
-- Rodado no beelink em 2026-09-25 (duckdb sem arquivo de banco); original em ~/bkp_parquet/.
-- Depois: mv para ~/rodado/.../reclamacoes.parquet e CREATE OR REPLACE VIEW com o SQL de duckdb_views().
SET enable_progress_bar=false;
SET preserve_insertion_order=false;
COPY (
  WITH src AS (SELECT * FROM read_parquet('/home/polo/rodado/br_mj_consumidorgovbr/reclamacoes/reclamacoes.parquet')),
  ok AS (SELECT COLUMNS(c -> NOT contains(c, chr(9))) FROM src WHERE arquivo_origem NOT LIKE '%Abril_2022'),
  br AS (SELECT string_split(COLUMNS('^Gestor\t'), chr(9)) f, arquivo_origem FROM src WHERE arquivo_origem LIKE '%Abril_2022'),
  fx AS (SELECT
    nullif(f[1],'') "Gestor", nullif(f[2],'') "Canal de Origem", nullif(f[3],'') "Região", nullif(f[4],'') "UF",
    nullif(f[5],'') "Cidade", nullif(f[6],'') "Sexo", nullif(f[7],'') "Faixa Etária", nullif(f[8],'') "Ano Abertura",
    nullif(f[9],'') "Mês Abertura", nullif(f[10],'') "Data Abertura", nullif(f[11],'') "Data Resposta",
    nullif(f[12],'') "Data Análise", nullif(f[13],'') "Data Recusa",
    strftime(try_strptime(nullif(f[14],''),'%d/%m/%Y'),'%Y-%m-%d') "Data Finalização",
    nullif(f[15],'') "Prazo Resposta", nullif(f[16],'') "Prazo Analise Gestor", nullif(f[17],'') "Tempo Resposta",
    nullif(f[18],'') "Nome Fantasia", nullif(f[19],'') "Segmento de Mercado", nullif(f[20],'') "Área",
    nullif(f[21],'') "Assunto", nullif(f[22],'') "Grupo Problema", nullif(f[23],'') "Problema",
    nullif(f[24],'') "Como Comprou Contratou", nullif(f[25],'') "Procurou Empresa", nullif(f[26],'') "Respondida",
    nullif(f[27],'') "Situação", nullif(f[28],'') "Avaliação Reclamação", nullif(f[29],'') "Nota do Consumidor",
    nullif(f[30],'') "Análise da Recusa", arquivo_origem
   FROM br)
  SELECT * FROM ok UNION ALL BY NAME SELECT * FROM fx
) TO '/home/polo/duckdb_tmp/reclamacoes_fix.parquet' (FORMAT parquet, COMPRESSION zstd);
