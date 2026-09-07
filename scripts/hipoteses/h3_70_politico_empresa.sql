-- hipoteses3 · bloco 70 · A PONTE POLITICO -> SOCIEDADE.
--
-- O caminho que a cascata territorial nunca enxergou:
--   TSE candidatos (CPF cheio + nome) -> CNPJ socios (CPF MASCARADO + nome)
--   -> cnpj_basico -> matriz de papeis dos blocos 60-62 (licitacao, sancao,
--      divida ativa, convenio, cartao corporativo...)
--
-- O casamento e por (nome normalizado, 6 digitos visiveis do CPF). E a mesma
-- tecnica do T37-3, e herda a mesma ressalva, que precisa ser lida antes de
-- qualquer numero daqui: o CPF do socio vem mascarado no cadastro publico
-- (`***123456**`), entao o par nome+6-digitos NAO e identificador unico.
-- Homonimo com os mesmos 6 digitos existe. O resultado e uma LISTA DE
-- CANDIDATOS A VINCULO para conferencia, nao um cadastro de fato.
--
-- Por isso o bloco emite `n_homonimos`: casamento com n_homonimos > 1 e
-- suspeito por construcao e nao deve entrar em contagem agregada.
--
-- E `socios` tem 43 snapshots mensais: sem filtrar ano+mes, cada casamento sai
-- repetido 43 vezes (15,6 milhoes de linhas medidos, contra ~360 mil reais).
SET enable_progress_bar=false;
SET memory_limit='6GB';
SET threads=4;

CREATE OR REPLACE TEMP MACRO nm(x) AS
  trim(regexp_replace(upper(strip_accents(CAST(x AS VARCHAR))), '[^A-Z ]', ' ', 'g'));
CREATE OR REPLACE TEMP MACRO so_digito(x) AS
  regexp_replace(CAST(x AS VARCHAR), '[^0-9]', '', 'g');

-- 1. candidatos com CPF utilizavel (11 digitos), um por CPF por ano/cargo
COPY (
  SELECT so_digito(cpf)                         AS cpf,
         substr(so_digito(cpf), 4, 6)           AS cpf_meio,
         nm(nome)                               AS nome_norm,
         ano, cargo, sigla_partido, sigla_uf, id_municipio, situacao, ocupacao
  FROM br_tse_eleicoes.candidatos
  WHERE length(so_digito(cpf)) = 11 AND ano >= 2014
) TO '__OUT__/h3_tse_candidatos.csv' (HEADER);

-- 2. socios PF com documento mascarado, ja com a chave de casamento pronta
COPY (
  SELECT cnpj_basico                            AS raiz,
         nm(nome)                               AS nome_norm,
         so_digito(documento)                   AS doc_digitos,
         qualificacao,
         data_entrada_sociedade
  FROM br_me_cnpj.socios
  WHERE tipo = '2' AND length(so_digito(documento)) = 6
    AND ano = (SELECT max(ano) FROM br_me_cnpj.socios)
    AND mes = (SELECT max(mes) FROM br_me_cnpj.socios
               WHERE ano = (SELECT max(ano) FROM br_me_cnpj.socios))
) TO '__OUT__/h3_cnpj_socios_pf.csv' (HEADER);

-- 3. o casamento ja resolvido, com o contador de homonimo do lado
COPY (
  WITH cand AS (
    SELECT DISTINCT so_digito(cpf) AS cpf, substr(so_digito(cpf), 4, 6) AS cpf_meio,
           nm(nome) AS nome_norm
    FROM br_tse_eleicoes.candidatos
    WHERE length(so_digito(cpf)) = 11 AND ano >= 2014
  ),
  soc AS (
    SELECT cnpj_basico AS raiz, nm(nome) AS nome_norm, so_digito(documento) AS doc
    FROM br_me_cnpj.socios
    WHERE tipo = '2' AND length(so_digito(documento)) = 6
      AND ano = (SELECT max(ano) FROM br_me_cnpj.socios)
      AND mes = (SELECT max(mes) FROM br_me_cnpj.socios
                 WHERE ano = (SELECT max(ano) FROM br_me_cnpj.socios))
  ),
  par AS (
    SELECT c.cpf, c.nome_norm, s.raiz
    FROM cand c JOIN soc s
      ON s.doc = c.cpf_meio AND s.nome_norm = c.nome_norm
  )
  SELECT p.cpf, p.nome_norm, p.raiz,
         count(*) OVER (PARTITION BY p.nome_norm, substr(p.cpf, 4, 6)) AS n_homonimos
  FROM par p
) TO '__OUT__/h3_politico_socio.csv' (HEADER);
