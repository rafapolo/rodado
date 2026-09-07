-- hipoteses3 · bloco 40 · ambiente. SEEG tem 165M linhas mas e particionada
-- por ano; MapBiomas municipal e de-para decenal (transicao), nao estoque --
-- por isso a metrica e "area que mudou de classe", nao "cobertura".
SET enable_progress_bar=false; SET memory_limit='6GB'; SET threads=4;

COPY (
  SELECT id_municipio,
         sum(TRY_CAST(emissao_ar6 AS DOUBLE))                                    AS seeg_emissao_total,
         -- `setor` e CODIGO NUMERICO, nao texto (br_seeg_emissoes.dicionario):
         -- 1 Agropecuaria · 2 Energia · 3 Mudanca de Uso da Terra · 4 Processos
         -- Industriais · 5 Residuos. ILIKE '%gropec%' devolvia coluna vazia.
         sum(TRY_CAST(emissao_ar6 AS DOUBLE)) FILTER (WHERE CAST(setor AS VARCHAR)='1') AS seeg_agro,
         sum(TRY_CAST(emissao_ar6 AS DOUBLE)) FILTER (WHERE CAST(setor AS VARCHAR)='2') AS seeg_energia,
         sum(TRY_CAST(emissao_ar6 AS DOUBLE)) FILTER (WHERE CAST(setor AS VARCHAR)='3') AS seeg_mut,
         sum(TRY_CAST(emissao_ar6 AS DOUBLE)) FILTER (WHERE CAST(setor AS VARCHAR)='5') AS seeg_residuos
  FROM br_seeg_emissoes.municipio
  WHERE ano = (SELECT max(ano) FROM br_seeg_emissoes.municipio)
  GROUP BY 1
) TO '__OUT__/h3_seeg.csv' (HEADER);

COPY (
  SELECT id_municipio,
         sum(TRY_CAST(area AS DOUBLE)) FILTER (WHERE id_classe_de <> id_classe_para) AS mb_area_transicao,
         sum(TRY_CAST(area AS DOUBLE))                                               AS mb_area_total,
         count(DISTINCT id_classe_para)                                              AS mb_classes
  FROM br_mapbiomas_estatisticas.transicao_municipio_de_para_decenal
  WHERE ano = (SELECT max(ano) FROM br_mapbiomas_estatisticas.transicao_municipio_de_para_decenal)
  GROUP BY 1
) TO '__OUT__/h3_mapbiomas.csv' (HEADER);

-- Telemetria da ANA: a chave e `municipiocodigo`. Emitida crua de proposito --
-- se for codigo de 6 digitos, a analise resolve pela ponte do bloco 00; se for
-- de 7, junta direto. Decidir aqui, sem ver o dado, seria chute.
COPY (
  SELECT CAST("MunicipioCodigo" AS VARCHAR) AS municipiocodigo,
         count(*)                                                AS ana_estacoes,
         count(*) FILTER (WHERE "TipoEstacaoPluviometro" IS NOT NULL AND
                                CAST("TipoEstacaoPluviometro" AS VARCHAR) NOT IN ('0','')) AS ana_pluviometricas,
         count(*) FILTER (WHERE CAST("Operando" AS VARCHAR) IN ('1','true','True')) AS ana_operando
  FROM br_ana_telemetria.estacoes GROUP BY 1
) TO '__OUT__/h3_ana_telemetria.csv' (HEADER);
