-- hipoteses3 · bloco 30 · renda e transferencia (fora o pagamento do Bolsa
-- Familia, que tem 1,5 bilhao de linhas e arquivo proprio).
SET enable_progress_bar=false; SET memory_limit='6GB'; SET threads=4;

-- Gas do Povo: a chave e SIAFI, nao IBGE. Junta com a ponte do bloco 00.
COPY (
  SELECT p.id_municipio,
         count(DISTINCT g.cpf_beneficiario)                        AS gas_beneficiarios,
         -- valor vem TEXTO com virgula decimal ("108,00"): TRY_CAST direto da NULL
         sum(TRY_CAST(replace(CAST(g.valor_beneficio AS VARCHAR), ',', '.') AS DOUBLE)) AS gas_valor,
         avg(TRY_CAST(g.quantidade_pessoas_familia AS DOUBLE))     AS gas_pessoas_familia,
         count(DISTINCT g.cnpj_estabelecimento)                    AS gas_estabelecimentos
  FROM br_cgu_gas_do_povo.gas_do_povo g
  JOIN read_csv_auto('__OUT__/h3_ponte_siafi.csv') p
    ON CAST(g.codigo_municipio_siafi AS VARCHAR) = CAST(p.codigo_municipio_siafi AS VARCHAR)
  WHERE g.ano_mes = (SELECT max(ano_mes) FROM br_cgu_gas_do_povo.gas_do_povo)
  GROUP BY 1
) TO '__OUT__/h3_gas_do_povo.csv' (HEADER);

COPY (
  SELECT id_municipio, count(*) AS dirpf_fundos,
         count(DISTINCT tipo_fundo) AS dirpf_tipos
  FROM br_rf_dirpf.fundos_habilitados GROUP BY 1
) TO '__OUT__/h3_dirpf_fundos.csv' (HEADER);

COPY (
  SELECT id_municipio_gasto AS id_municipio,
         count(*)                                        AS emendas_n,
         count(DISTINCT id_autor_emenda)                 AS emendas_autores,
         sum(TRY_CAST(valor_pago AS DOUBLE))             AS emendas_valor_pago,
         sum(TRY_CAST(valor_empenhado AS DOUBLE))        AS emendas_valor_empenhado
  FROM br_cgu_emendas_parlamentares.microdados GROUP BY 1
) TO '__OUT__/h3_emendas.csv' (HEADER);
