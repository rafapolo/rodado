-- Tema 82 de docs/perguntas.md — trincas de familia genuinamente novas,
-- reavaliadas apos corrigir dois blocos "falsos" do Bloco R (ver nota em
-- tasks/hipoteses.md): mobilidade e fiscal_municipal tinham UMA tabela ruim
-- catalogada como bloqueio da familia inteira; ha outra tabela boa em cada.

-- H82-1 fiscal_municipal (ITR) x fundiario (SICAR) x agropecuaria (PPM)
COPY (SELECT id_municipio, sum(valor_arrecadado) AS itr_valor
      FROM br_rf_arrecadacao.itr WHERE ano>=2022 GROUP BY 1)
  TO '__OUT__/v_itr.csv' (HEADER);

COPY (SELECT id_municipio, sum(area) AS sicar_area, count(*) AS sicar_n
      FROM br_sfb_sicar.area_imovel GROUP BY 1)
  TO '__OUT__/v_sicar2.csv' (HEADER);

COPY (SELECT id_municipio, sum(quantidade) AS bovino_n
      FROM br_ibge_ppm.efetivo_rebanhos
      WHERE tipo_rebanho ILIKE '%bovino%' AND ano=(SELECT max(ano) FROM br_ibge_ppm.efetivo_rebanhos)
      GROUP BY 1)
  TO '__OUT__/v_ppm2.csv' (HEADER);

-- H82-2 vigilancia_sinan (violencia domestica/sexual, NUNCA testada -- so
-- arboviroses foram usadas no tema 71) x conectividade, molde registro_vs_fenomeno.
-- checar comprimento do id antes de assumir 6 ou 7 digitos (gotcha SINAN dengue
-- de hoje: id_municipio_residencia era IBGE 7, diferente do SIH/SIA).
COPY (SELECT ID_MUNICIP AS id_municipio, count(*) AS viol_n
      FROM br_ms_sinan_violencia.microdados_violencia
      WHERE NU_ANO IN ('2022','2023') AND ID_MUNICIP IS NOT NULL
      GROUP BY 1)
  TO '__OUT__/v_sinan_violencia.csv' (HEADER);

-- H82-3 mobilidade (mortes negras em acidente de transporte) x raca (Censo 2022)
COPY (SELECT id_municipio, arg_max(prop_mortes_negras_acidente_transporte, ano) AS prop_mortes_negras
      FROM br_mobilidados_indicadores.proporcao_mortes_negras_acidente_transporte
      GROUP BY 1)
  TO '__OUT__/v_mobilidade_racial.csv' (HEADER);

-- share_negra: mesmo pivot usado em H13/92_lacunas.py (instrucao tem uma
-- categoria_principal='Total', que serve de populacao total por raca).
COPY (SELECT id_municipio, cor_raca, categoria_principal, valor
      FROM br_ibge_censo2022_raca.instrucao
      WHERE categoria_principal='Total')
  TO '__OUT__/v_censo_raca_total.csv' (HEADER);
