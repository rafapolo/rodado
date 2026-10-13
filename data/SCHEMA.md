# `br_rodado_indicadores_municipais` — guia para consultas por LLM no db.rodado.xyz

Painel municipal **em formato longo**: uma linha por município × indicador × período ×
dimensão, com 987 indicadores de 17 seções (demografia, economia, saúde, educação, segurança,
política…) para os 5.571 municípios. São 12.382.056 linhas numa única tabela,
`br_rodado_indicadores_municipais.municipio`. O documento serve para escrever SQL (dialeto
**DuckDB**) contra `https://db.rodado.xyz` e para cruzar o painel com `br_tse_eleicoes`.

Medido em 2026-10-13. Os números de linhas, anos e municípios abaixo vêm de consulta, não de
documentação da fonte.

## Como consultar

```bash
# SQL no corpo; resposta em JSON (lista de objetos)
curl -u rodado:SENHA --data-binary @consulta.sql https://db.rodado.xyz/query
# CSV, até 100 mil linhas
curl -u rodado:SENHA 'https://db.rodado.xyz/query?formato=csv&limite=100000' --data-binary @consulta.sql
# sem senha, com token
curl --data-binary @consulta.sql 'https://db.rodado.xyz/query?token=TOKEN&formato=csv'
```

- **Um comando por requisição**, só leitura: `SELECT`, `WITH`, `FROM` primeiro, `DESCRIBE`,
  `SUMMARIZE`. `CREATE`, `ATTACH`, `SET`, `COPY` são recusados.
- `formato` = `json` (padrão), `csv`, `tsv` ou `parquet`; `limite` = 10.000 por padrão, até
  1.000.000. Os cabeçalhos `X-Linhas`, `X-Truncado` e `X-Segundos` dizem quantas linhas vieram,
  se o limite cortou e quanto levou.
- 300 s por consulta e 4 simultâneas. A consulta roda no servidor, lendo do object storage:
  **agregue lá e traga o resultado**, não a tabela bruta.
- Nenhum arquivo é lido direto: `read_parquet`, `glob`, `FROM '<caminho>'` e afins são
  recusados. Use só `dataset.tabela`.
- Para abrir no navegador: `https://db.rodado.xyz/?query=<SQL em base64>` abre o terminal e
  executa a consulta.
- O DuckDB aceita `max(x) FILTER (cond)`, `arg_max(valor, ano)`, `QUALIFY`, `GROUP BY ALL`,
  `ntile()`, `corr()`. Todos os exemplos abaixo usam esses recursos.

Todos os exemplos foram executados no db.rodado.xyz em 2026-10-13, em menos de 2 s, menos o 10
(32 s na primeira execução, 0,6 s na segunda, com o cache de rodapés de parquet quente). A saída mostrada é a real.

## Exemplos — só o painel

### 1. Ficha de um município: o valor mais recente de cada indicador de uma seção

```sql
-- Ficha de um município: o valor mais recente de cada indicador da seção saúde em Campinas (SP)
SELECT indicador, dimensao, ano, mes, valor, texto
FROM br_rodado_indicadores_municipais.municipio
WHERE id_municipio = '3509502' AND secao = 'saude'
  AND indicador NOT LIKE '%.erro' AND indicador NOT LIKE '%.motivo' AND indicador NOT LIKE '%.disponivel'
QUALIFY row_number() OVER (PARTITION BY indicador, dimensao ORDER BY ano DESC NULLS LAST, mes DESC NULLS LAST) = 1
ORDER BY indicador, dimensao;
```

Saída (CSV, primeiras linhas):

```
indicador,dimensao,ano,mes,valor,texto
atencao_basica.cobertura_ab,,,,68.65,
atencao_basica.cobertura_esf,,,,56.16,
atencao_basica.equipes,,,,246.0,
atencao_basica.referencia,,,,,2020-12
atencao_basica.serie.cobertura_ab,,2020,12,68.65,
atencao_basica.serie.cobertura_esf,,2020,12,56.16,
atencao_basica.serie.equipes,,2020,12,246.0,
…
```

### 2. Ranking das capitais, com a referência da UF e do Brasil na mesma linha

```sql
-- Capitais por taxa de homicídio doloso (Sinesp 2025, por 100 mil hab.), com a referência da UF e do Brasil
SELECT any_value(nome) AS capital, any_value(sigla_uf) AS uf,
  round(max(valor) FILTER (indicador = 'sinesp.taxa_homicidio_doloso_100k.municipio'), 1) AS taxa_municipio,
  round(max(valor) FILTER (indicador = 'sinesp.taxa_homicidio_doloso_100k.uf'), 1) AS taxa_uf,
  round(max(valor) FILTER (indicador = 'sinesp.taxa_homicidio_doloso_100k.brasil'), 1) AS taxa_brasil
FROM br_rodado_indicadores_municipais.municipio
WHERE indicador IN ('sinesp.taxa_homicidio_doloso_100k.municipio', 'sinesp.taxa_homicidio_doloso_100k.uf',
                    'sinesp.taxa_homicidio_doloso_100k.brasil', 'capital_uf')
GROUP BY id_municipio
HAVING max(valor) FILTER (indicador = 'capital_uf') = 1
ORDER BY taxa_municipio DESC;
```

Saída (CSV, primeiras linhas):

```
capital,uf,taxa_municipio,taxa_uf,taxa_brasil
Maceió,AL,34.7,28.0,14.8
Recife,PE,33.8,30.2,14.8
Fortaleza,CE,27.9,31.6,14.8
Porto Velho,RO,27.0,23.6,14.8
Salvador,BA,26.2,24.6,14.8
João Pessoa,PB,24.7,21.6,14.8
Teresina,PI,21.1,14.4,14.8
…
```

### 3. Série histórica: dois anos da mesma série lado a lado

```sql
-- Série histórica: cidades de mais de 500 mil habitantes que mais cresceram em população de 2010 a 2025
-- (populacao_serie tem um ano por linha; pivota os dois anos com FILTER)
SELECT any_value(nome) AS nome, any_value(sigla_uf) AS uf,
  max(valor) FILTER (ano = 2010)::INT AS pop_2010,
  max(valor) FILTER (ano = 2025)::INT AS pop_2025,
  round(100 * (max(valor) FILTER (ano = 2025) / max(valor) FILTER (ano = 2010) - 1), 1) AS crescimento_pct
FROM br_rodado_indicadores_municipais.municipio
WHERE indicador = 'populacao_serie.populacao' AND ano IN (2010, 2025)
GROUP BY id_municipio
HAVING pop_2025 >= 500000
ORDER BY crescimento_pct DESC
LIMIT 15;
```

Saída (CSV, primeiras linhas):

```
nome,uf,pop_2010,pop_2025,crescimento_pct
Serra,ES,409267,579720,41.6
Florianópolis,SC,421240,587486,39.5
Sorocaba,SP,586625,762172,29.9
Joinville,SC,515288,664541,29.0
Manaus,AM,1802014,2303732,27.8
Uberlândia,MG,604013,761835,26.1
Cuiabá,MT,551098,691875,25.5
…
```

### 4. Indicador com dimensão: categorias do Censo como colunas

```sql
-- Dimensão: % de evangélicos (Censo 2022) nas cidades de mais de 200 mil habitantes, com católicos e sem religião
-- (o valor fica na linha de cada categoria; a categoria está em dimensao = 'religiao=<nome>')
WITH r AS (
  SELECT id_municipio, any_value(nome) AS nome, any_value(sigla_uf) AS uf,
    max(valor) FILTER (dimensao = 'religiao=Evangélicas') AS evangelicos,
    max(valor) FILTER (dimensao = 'religiao=Católica Apostólica Romana') AS catolicos,
    max(valor) FILTER (dimensao = 'religiao=Sem religião') AS sem_religiao
  FROM br_rodado_indicadores_municipais.municipio
  WHERE indicador = 'censo_extra.religiao.grupos.pct'
  GROUP BY id_municipio
), p AS (
  SELECT id_municipio, valor AS pop FROM br_rodado_indicadores_municipais.municipio
  WHERE indicador = 'censo_2022.populacao'
)
SELECT nome, uf, pop::INT AS populacao, round(evangelicos, 1) AS pct_evangelicos,
  round(catolicos, 1) AS pct_catolicos, round(sem_religiao, 1) AS pct_sem_religiao
FROM r JOIN p USING (id_municipio)
WHERE pop >= 200000
ORDER BY pct_evangelicos DESC
LIMIT 20;
```

Saída (CSV, primeiras linhas):

```
nome,uf,populacao,pct_evangelicos,pct_catolicos,pct_sem_religiao
Rio Branco,AC,361869,47.1,30.5,14.8
Itaboraí,RJ,223888,44.2,26.8,19.9
Cabo de Santo Agostinho,PE,202831,43.7,28.2,22.0
Parauapebas,PA,267248,43.5,38.7,12.5
Ipatinga,MG,227309,43.3,43.4,7.9
Cabo Frio,RJ,221764,41.8,29.0,16.4
Cariacica,ES,351964,41.4,37.3,15.8
…
```

### 5. Vários indicadores pivotados + agregação por região

```sql
-- Correlação por região: IDEB dos anos iniciais (o mais recente de cada município) x % de domicílios no Bolsa Família
WITH base AS (
  SELECT id_municipio,
    any_value(texto) FILTER (indicador = 'regiao') AS regiao,
    arg_max(valor, ano) FILTER (indicador = 'ideb.iniciais.ideb') AS ideb,
    max(valor) FILTER (indicador = 'bolsa_familia.familias') AS familias_pbf,
    max(valor) FILTER (indicador = 'censo_2022.domicilios') AS domicilios
  FROM br_rodado_indicadores_municipais.municipio
  WHERE indicador IN ('regiao', 'ideb.iniciais.ideb', 'bolsa_familia.familias', 'censo_2022.domicilios')
  GROUP BY id_municipio
)
SELECT regiao, count(*) AS municipios,
  round(avg(ideb), 2) AS ideb_medio,
  round(avg(100 * familias_pbf / domicilios), 1) AS pct_dom_pbf_medio,
  round(corr(ideb, familias_pbf / domicilios), 2) AS correlacao
FROM base
WHERE ideb IS NOT NULL AND domicilios > 0
GROUP BY regiao
ORDER BY regiao;
```

Saída (CSV, primeiras linhas):

```
regiao,municipios,ideb_medio,pct_dom_pbf_medio,correlacao
Centro-Oeste,467,6.29,22.6,-0.19
Nordeste,1794,5.81,59.3,-0.15
Norte,450,5.43,53.5,-0.41
Sudeste,1668,6.51,21.4,-0.31
Sul,1180,6.69,12.7,-0.24
```

## Exemplos — painel × TSE (eleições)

A chave é `id_municipio` (IBGE, 7 dígitos, `VARCHAR`), a mesma nas duas bases. No 1º turno de
2026 (4/out) foram ao 2º turno para presidente (25/out) **Flávio Bolsonaro (PL, 22)**, com
47,03% dos válidos, e **Lula (PT, 13)**, com 45,16%. Há 2º turno de governador em AC, AM, DF,
ES, RJ, RN e TO.

### 6. Voto presidencial de 2026 por quintil de % de evangélicos

```sql
-- 1º turno de 2026 para presidente por faixa de % de evangélicos no município (Censo 2022)
-- Flávio Bolsonaro (PL, 22) x Lula (PT, 13), % dos votos válidos somados na faixa
WITH evang AS (
  SELECT id_municipio, valor AS pct_evangelicos
  FROM br_rodado_indicadores_municipais.municipio
  WHERE indicador = 'censo_extra.religiao.grupos.pct' AND dimensao = 'religiao=Evangélicas'
), voto AS (
  SELECT id_municipio,
    sum(votos) FILTER (numero_candidato = '22') AS v22,
    sum(votos) FILTER (numero_candidato = '13') AS v13,
    sum(votos) AS validos
  FROM br_tse_eleicoes.resultados_candidato_municipio
  WHERE ano = 2026 AND turno = 1 AND cargo = 'presidente' AND id_municipio IS NOT NULL
  GROUP BY id_municipio
), q AS (
  SELECT *, ntile(5) OVER (ORDER BY pct_evangelicos) AS quintil FROM evang JOIN voto USING (id_municipio)
)
SELECT quintil, count(*) AS municipios,
  round(min(pct_evangelicos), 1) AS evang_de, round(max(pct_evangelicos), 1) AS evang_ate,
  round(100 * sum(v22) / sum(validos), 1) AS pct_22,
  round(100 * sum(v13) / sum(validos), 1) AS pct_13
FROM q GROUP BY quintil ORDER BY quintil;
```

Saída (CSV, primeiras linhas):

```
quintil,municipios,evang_de,evang_ate,pct_22,pct_13
1,1114,1.3,13.5,32.3,62.1
2,1114,13.5,19.0,39.3,54.3
3,1114,19.0,24.8,44.3,47.4
4,1114,24.8,31.4,50.1,41.6
5,1114,31.4,88.7,52.8,39.2
```

### 7. Escolaridade do eleitorado (códigos do TSE no painel) × abstenção

```sql
-- Escolaridade do eleitorado x abstenção no 1º turno de 2026 (presidente)
-- instrucao.N são os códigos do TSE: 1 analfabeto, 2 lê e escreve, 3 fundamental incompleto ... 8 superior completo, 0 não informado
WITH esc AS (
  SELECT id_municipio,
    sum(valor) FILTER (indicador IN ('instrucao.1', 'instrucao.2', 'instrucao.3')) AS ate_fund_incompleto,
    sum(valor) FILTER (indicador = 'instrucao.8') AS superior,
    sum(valor) AS eleitores
  FROM br_rodado_indicadores_municipais.municipio
  WHERE secao = 'politica' AND indicador LIKE 'instrucao.%' AND ano = 2026
  GROUP BY id_municipio
), abst AS (
  SELECT id_municipio, abstencoes, aptos
  FROM br_tse_eleicoes.detalhes_votacao_municipio
  WHERE ano = 2026 AND turno = 1 AND cargo = 'presidente' AND id_municipio IS NOT NULL
), d AS (
  SELECT *, ntile(10) OVER (ORDER BY ate_fund_incompleto / eleitores) AS decil FROM esc JOIN abst USING (id_municipio)
)
SELECT decil, count(*) AS municipios,
  round(100 * sum(ate_fund_incompleto) / sum(eleitores), 1) AS pct_ate_fund_incompleto,
  round(100 * sum(superior) / sum(eleitores), 1) AS pct_superior,
  round(100 * sum(abstencoes) / sum(aptos), 1) AS pct_abstencao
FROM d GROUP BY decil ORDER BY decil;
```

Saída (CSV, primeiras linhas):

```
decil,municipios,pct_ate_fund_incompleto,pct_superior,pct_abstencao
1,557,21.1,15.5,20.9
2,557,31.2,9.0,20.6
3,557,34.8,7.8,21.0
4,557,38.1,7.3,20.7
5,557,40.9,6.7,20.6
6,557,43.5,6.0,20.4
7,557,46.1,5.5,20.6
…
```

O resultado é um achado nulo: a abstenção fica em ~21% em todos os decis.

### 8. Partido do prefeito eleito em 2024 × voto para presidente em 2026

```sql
-- Partido do prefeito eleito em 2024 x voto para presidente no 1º turno de 2026
-- (prefeito.eleito.partido guarda o partido em texto, não em valor)
WITH pref AS (
  SELECT id_municipio, texto AS partido_prefeito
  FROM br_rodado_indicadores_municipais.municipio
  WHERE indicador = 'prefeito.eleito.partido' AND ano = 2024
), voto AS (
  SELECT id_municipio,
    sum(votos) FILTER (numero_candidato = '22') AS v22,
    sum(votos) FILTER (numero_candidato = '13') AS v13,
    sum(votos) AS validos
  FROM br_tse_eleicoes.resultados_candidato_municipio
  WHERE ano = 2026 AND turno = 1 AND cargo = 'presidente' AND id_municipio IS NOT NULL
  GROUP BY id_municipio
)
SELECT partido_prefeito, count(*) AS prefeituras,
  round(100 * sum(v22) / sum(validos), 1) AS pct_22,
  round(100 * sum(v13) / sum(validos), 1) AS pct_13,
  count(*) FILTER (v22 > v13) AS municipios_22_a_frente,
  count(*) FILTER (v13 > v22) AS municipios_13_a_frente
FROM pref JOIN voto USING (id_municipio)
GROUP BY partido_prefeito
HAVING count(*) >= 100
ORDER BY pct_22 DESC;
```

Saída (CSV, primeiras linhas):

```
partido_prefeito,prefeituras,pct_22,pct_13,municipios_22_a_frente,municipios_13_a_frente
PL,514,56.3,35.6,411,103
PP,747,49.2,43.8,439,308
PSD,884,49.1,42.8,486,397
PODE,127,48.9,42.4,80,47
REPUBLICANOS,432,48.5,43.9,203,228
PSDB,274,47.8,44.8,166,108
AVANTE,136,45.5,47.2,28,108
…
```

### 9. Variação de Lula entre os 1º turnos de 2022 e 2026, por cobertura do Bolsa Família

```sql
-- Quanto Lula (13) ganhou ou perdeu do 1º turno de 2022 para o de 2026, por faixa de cobertura do Bolsa Família
-- (famílias no PBF em jul/2025 ÷ domicílios do Censo 2022; mesma régua, 1º turno x 1º turno)
WITH pbf AS (
  SELECT id_municipio,
    max(valor) FILTER (indicador = 'bolsa_familia.familias') / max(valor) FILTER (indicador = 'censo_2022.domicilios') AS cobertura
  FROM br_rodado_indicadores_municipais.municipio
  WHERE indicador IN ('bolsa_familia.familias', 'censo_2022.domicilios')
  GROUP BY id_municipio
), voto AS (
  SELECT id_municipio,
    sum(votos) FILTER (ano = 2022 AND numero_candidato = '13') AS v13_22, sum(votos) FILTER (ano = 2022) AS val_22,
    sum(votos) FILTER (ano = 2026 AND numero_candidato = '13') AS v13_26, sum(votos) FILTER (ano = 2026) AS val_26
  FROM br_tse_eleicoes.resultados_candidato_municipio
  WHERE ano IN (2022, 2026) AND turno = 1 AND cargo = 'presidente' AND id_municipio IS NOT NULL
  GROUP BY id_municipio
), q AS (
  SELECT *, ntile(5) OVER (ORDER BY cobertura) AS quintil FROM pbf JOIN voto USING (id_municipio)
)
SELECT quintil, count(*) AS municipios,
  round(100 * min(cobertura), 1) AS pbf_de, round(100 * max(cobertura), 1) AS pbf_ate,
  round(100 * sum(v13_22) / sum(val_22), 1) AS pct_13_2022,
  round(100 * sum(v13_26) / sum(val_26), 1) AS pct_13_2026,
  round(100 * (sum(v13_26) / sum(val_26) - sum(v13_22) / sum(val_22)), 1) AS variacao_pp
FROM q GROUP BY quintil ORDER BY quintil;
```

Saída (CSV, primeiras linhas):

```
quintil,municipios,pbf_de,pbf_ate,pct_13_2022,pct_13_2026,variacao_pp
1,1114,0.5,12.2,34.6,30.3,-4.3
2,1114,12.2,20.6,42.9,39.8,-3.1
3,1114,20.6,37.5,50.4,47.2,-3.2
4,1114,37.5,57.7,63.2,59.5,-3.7
5,1114,57.7,147.2,72.5,68.6,-3.9
```

### 10. 2º turno de governador: finalistas, 1º turno e onde está o eleitorado

```sql
-- 2º turno de governador em 2026: as UFs com disputa, os dois finalistas, o 1º turno e onde está o eleitorado
-- (resultado = '2º turno' marca os finalistas; eleitorado.aptos e capital_uf vêm do painel municipal)
-- fora_da_soma = comparecimento - válidos - brancos - nulos: votos que não estão em candidato nenhum do arquivo
-- (no RJ, 274 mil — padrão de votos anulados sub judice). Sem eles no denominador, o 1º colocado do RJ passa de 50%.
WITH fin AS (
  SELECT sigla_uf, numero_candidato, any_value(sigla_partido) AS partido, sum(votos) AS votos
  FROM br_tse_eleicoes.resultados_candidato_municipio
  WHERE ano = 2026 AND turno = 1 AND cargo = 'governador' AND resultado = '2º turno'
  GROUP BY ALL
), nomes AS (
  SELECT sigla_uf, numero AS numero_candidato, any_value(nome_urna) AS nome_urna
  FROM br_tse_eleicoes.candidatos
  WHERE ano = 2026 AND cargo = 'governador'
  GROUP BY ALL
), validos AS (
  SELECT sigla_uf, sum(votos_validos) AS validos, sum(aptos) AS aptos, sum(abstencoes) AS abstencoes,
    sum(comparecimento - votos_validos - votos_brancos - votos_nulos) AS fora_da_soma
  FROM br_tse_eleicoes.detalhes_votacao_municipio
  WHERE ano = 2026 AND turno = 1 AND cargo = 'governador'
  GROUP BY sigla_uf
), eleitorado AS (
  SELECT sigla_uf,
    sum(apt) FILTER (cap = 1) / sum(apt) AS pct_eleitorado_capital,
    count(*) FILTER (apt >= 200000) AS municipios_200mil_eleitores
  FROM (
    SELECT id_municipio, any_value(sigla_uf) AS sigla_uf,
      max(valor) FILTER (indicador = 'eleitorado.aptos') AS apt,
      max(valor) FILTER (indicador = 'capital_uf') AS cap
    FROM br_rodado_indicadores_municipais.municipio
    WHERE indicador IN ('eleitorado.aptos', 'capital_uf')
    GROUP BY id_municipio
  ) GROUP BY sigla_uf
)
SELECT f.sigla_uf AS uf, f.numero_candidato AS numero, n.nome_urna, f.partido,
  round(100 * f.votos / v.validos, 1) AS pct_validos_1t,
  v.fora_da_soma, round(100 * f.votos / (v.validos + v.fora_da_soma), 1) AS pct_com_fora_da_soma,
  v.aptos AS eleitores, round(100 * v.abstencoes / v.aptos, 1) AS pct_abstencao_1t,
  round(100 * e.pct_eleitorado_capital, 1) AS pct_eleitorado_na_capital,
  e.municipios_200mil_eleitores
FROM fin f
JOIN validos v USING (sigla_uf)
JOIN eleitorado e USING (sigla_uf)
LEFT JOIN nomes n USING (sigla_uf, numero_candidato)
ORDER BY uf, pct_validos_1t DESC;
```

Saída (CSV, primeiras linhas):

```
uf,numero,nome_urna,partido,pct_validos_1t,fora_da_soma,pct_com_fora_da_soma,eleitores,pct_abstencao_1t,pct_eleitorado_na_capital,municipios_200mil_eleitores
AC,11,Mailza Assis,PP,49.8,0,49.8,613316,20.4,44.0,1
AC,10,Alan Rick,REPUBLICANOS,32.3,0,32.3,613316,20.4,44.0,1
AM,55,Omar Aziz,PSD,40.6,0,40.6,2796053,20.2,52.6,1
AM,22,Professora Maria Do Carmo,PL,24.5,0,24.5,2796053,20.2,52.6,1
DF,11,Celina Leão,PP,50.0,1843,49.9,2243988,19.0,100.0,1
DF,13,Leandro Grass,PT,34.5,1843,34.5,2243988,19.0,100.0,1
ES,10,Lorenzo Pazolini,REPUBLICANOS,49.6,0,49.6,2987584,21.4,8.9,4
…
```

## Modelo de dados

| coluna | tipo | o que é |
|---|---|---|
| `id_municipio` | VARCHAR | código IBGE de 7 dígitos; chave de junção com quase todo o espelho |
| `nome`, `sigla_uf` | VARCHAR | repetidos em toda linha, para não precisar de join |
| `secao` | VARCHAR | um de 17 grupos (`demografia`, `saude`, `politica`…). Filtrar por `secao` **e** `indicador` não custa nada e evita colisão de nome (`erro` e `area_km2` existem em mais de uma seção) |
| `indicador` | VARCHAR | caminho com pontos, `fonte.grupo.medida` (ex.: `ideb.iniciais.ideb`). A árvore abaixo mostra todos |
| `ano` | INTEGER | período de referência. **NULL** = sem período (Censo 2022, cadastro, dado estático) |
| `mes` | INTEGER | mês de referência quando a fonte é mensal; senão NULL |
| `dimensao` | VARCHAR | recorte da linha, `chave=valor` com `; ` entre pares (`partido=PT`, `produto=Soja; unidade=Toneladas`). NULL = total |
| `valor` | DOUBLE | o número |
| `texto` | VARCHAR | quando o indicador é texto: nome, partido, data, código. Exatamente um de `valor`/`texto` vem preenchido, ou nenhum (linha-pai) |

### Padrões de SQL

```sql
-- pivotar indicadores em colunas: um município por linha
SELECT id_municipio, any_value(nome) AS nome,
  max(valor) FILTER (indicador = 'censo_2022.populacao') AS pop,
  arg_max(valor, ano) FILTER (indicador = 'ideb.finais.ideb') AS ideb_mais_recente
FROM br_rodado_indicadores_municipais.municipio
WHERE indicador IN ('censo_2022.populacao', 'ideb.finais.ideb')   -- sempre restrinja os indicadores
GROUP BY id_municipio;

-- ler uma chave da dimensão
SELECT regexp_extract(dimensao, 'partido=([^;]+)', 1) AS partido, sum(valor) AS filiados
FROM br_rodado_indicadores_municipais.municipio
WHERE indicador = 'filiados.por_partido.filiados'
GROUP BY 1 ORDER BY 2 DESC;

-- o período mais recente de cada indicador
QUALIFY row_number() OVER (PARTITION BY id_municipio, indicador, dimensao
                           ORDER BY ano DESC NULLS LAST, mes DESC NULLS LAST) = 1
```

Para descobrir indicadores sem ler a árvore inteira:
`SELECT DISTINCT secao, indicador FROM br_rodado_indicadores_municipais.municipio WHERE indicador ILIKE '%leito%'`.

## Armadilhas (todas medidas em 2026-10-13)

1. **Não existe chave única.** 20.458 combinações de município × indicador × ano × mês ×
   dimensão aparecem repetidas. As maiores fontes: `inse.niveis_pct.*`, `biomas.pct_area`
   (São Paulo tem duas linhas `nome=Mata Atlântica`: 100 e 98,6), `violencia_sinan.por_ciclo_vida.n`,
   `violencia_sinan.por_local.n` e `bndes.*`. Sempre agregue (`max`/`sum`) sabendo o que está
   somando.
2. **`inse.niveis_pct.nivel` e `inse.niveis_pct.pct` não são pareáveis.** Saem em linhas
   soltas, sem dimensão que diga qual percentual é de qual nível. Não use.
3. **"Último período disponível", com ano diferente por município.** `dengue.*` tem uma linha
   por município, entre 2023 e 2026 (4.372 em 2025, 858 em 2026). `caged.*` vai de 2020 a 2025
   (5.452 em 2025). `cnes.leitos.*` tem 3.606 municípios em fev/2026, e o resto parado no
   último mês em que a fonte informou leito, alguns em **2006**. Antes de comparar municípios,
   filtre `ano` (e `mes`) ou mostre-os.
4. **`ano` às vezes é o da coleta, não o do fato.** `ano_prefeito` tem `ano = 2026` e
   `valor = 2024` (ano da eleição do prefeito); `eleitorado.*` e `filiados.*` têm `ano = 2026`
   (retrato da coleta). Os indicadores `censo_2022.*` têm `ano` NULL.
5. **Unidades trocadas entre indicadores parecidos.** `censo_2022.taxa_alfabetizacao` é fração
   (mediana 0,906); `censo_extra.alfabetizacao_por_raca.taxa` é percentual (mediana 90,0). Os
   `*.pct*` costumam ir de 0 a 100. Dinheiro é R$ nominal, sem divisão por mil: `pib.serie.pib`
   tem mediana de R$ 184,8 milhões e `pib.pib_per_capita.valor` de R$ 29.895.
6. **Número guardado como texto.** `comercio_exterior.*.total_fob_usd`, `*.ano_anterior_fob_usd`,
   `conectividade ibc.fibra` e `bancario.verbetes.*` vêm em `texto`: use `TRY_CAST(texto AS DOUBLE)`.
   `id_municipio_tse`, `regiao`, `capital_uf`… estão na seção `municipio`, quase todos em `texto`
   (`capital_uf` e `amazonia_legal` em `valor`, 0/1).
7. **Linhas-pai sem valor.** `censo_extra.cor_raca`, `censo_extra.religiao.grupos`,
   `bndes.setor_5a`, `sisdepen.raca_cor`… não têm `valor` nem `texto`. O número está no filho
   (`.populacao`, `.pct`, `.desembolsado`, `.n`).
8. **`*.erro`, `*.motivo`, `*.disponivel` são metadados da coleta, não indicadores.**
   `disponivel = 0` + `motivo` diz que a fonte não cobre o município (ex.: `isp_rj` só existe no
   RJ, `fbsp` só nas 27 capitais). `erro` com `Binder Error…` é falha da coleta. Em ambos os
   casos, **ausência não é zero**.
9. **5.571 municípios.** Inclui Boa Esperança do Norte (MT, `5101837`, instalado em 2025), com
   só 251 indicadores; Fernando de Noronha (`2605459`) também tem cobertura menor. Contagens de
   referência por fonte: 5.570.
10. **Cobertura do Bolsa Família pode passar de 100%.** `bolsa_familia.familias ÷
    censo_2022.domicilios` chega a 147%: famílias do programa (jul/2025) e domicílios do Censo
    são unidades diferentes. Para ranquear serve; como "% de domicílios", é aproximação.
11. **`financas_campanha` de 2026 não é municipal.** Em 2026 existe uma única linha no país
    (o total nacional, R$ 4,49 bi em despesas). O recorte por município vale só para 2024. Para
    2026, use `br_tse_eleicoes.despesas_candidato` (parcial: o ciclo ainda está aberto).
12. **`genero.N` e `instrucao.N` (seção `politica`, eleitorado de 2026) são códigos do TSE.**
    `genero`: 0 não informado, 2 masculino, 4 feminino. `instrucao`: 0 não informado,
    1 analfabeto, 2 lê e escreve, 3 fundamental incompleto, 4 fundamental completo, 5 médio
    incompleto, 6 médio completo, 7 superior incompleto, 8 superior completo. A soma dos
    códigos é `eleitorado.aptos` (Rio de Janeiro: 4.950.429 nos dois), igual a
    `br_tse_eleicoes.perfil_eleitorado_municipio_zona` de 2026.
13. **`eleitorado.aptos` ≠ `aptos` do resultado.** O painel traz o retrato do cadastro
    (Rio: 4.950.429); `detalhes_votacao_municipio` traz o aptos do dia da eleição (4.952.612).
    Use o segundo para taxas de abstenção e comparecimento.

## Cruzando com `br_tse_eleicoes`

| tabela | grão | filtros obrigatórios | usar para |
|---|---|---|---|
| `resultados_candidato_municipio` | candidato × município × turno | `ano`, `turno`, `cargo` | votos por candidato: `numero_candidato`, `sigla_partido`, `resultado` (`'2º turno'`, `'eleito'`, `'nao eleito'`…), `votos` |
| `detalhes_votacao_municipio` | cargo × município × turno | `ano`, `turno`, `cargo` | `aptos`, `comparecimento`, `abstencoes`, `votos_validos`, `votos_brancos`, `votos_nulos` |
| `perfil_eleitorado_municipio_zona` | zona × sexo × idade × instrução… | `ano` | eleitorado detalhado (o painel já tem o agregado por município) |
| `candidatos` | candidatura | `ano`, `cargo` | `nome_urna`, `numero`, `sigla_partido`, `sigla_uf`, perfil do candidato |
| `br_rodado_eleicoes.secao_setor` | seção eleitoral × setor censitário | — | descer abaixo do município |

- `cargo` em minúsculas: `'presidente'`, `'governador'`, `'senador'`, `'deputado federal'`,
  `'prefeito'`, `'vereador'`. `turno` é inteiro (1, 2). `numero_candidato` é texto (`'13'`).
- **Filtre `id_municipio IS NOT NULL`.** O voto no exterior vem com município nulo (187 linhas
  em `detalhes_votacao_municipio` de presidente em 2026).
- **Percentuais de 2026 com voto sub judice.** No 1º turno de 2026 para governador do RJ, o
  comparecimento passa da soma de válidos + brancos + nulos em 274.411 votos, que não aparecem
  em candidato nenhum (padrão de voto anulado sub judice). Calculado sobre os válidos do
  arquivo, o 1º colocado aparece com 50,9%, embora o TSE o mande ao 2º turno; com os 274 mil no
  denominador, 49,3%. No DF a diferença é de 1.843 votos. Para presidente, a soma fecha exata.
  Confira com `comparecimento - votos_validos - votos_brancos - votos_nulos`, como no exemplo 10.
- Conferido: a soma dos votos por candidato em `resultados_candidato_municipio` é igual a
  `votos_validos` de `detalhes_votacao_municipio` nos 5.570 municípios (presidente, 1º turno
  de 2026), sem nenhuma diferença.
- O painel já traz eleição pronta na seção `politica`: prefeito eleito em 2024 (`prefeito.*`),
  câmara municipal 2020–2024 (`camara_municipal.*`), filiados por partido e sexo
  (`filiados.*`), eleitorado de 2026 (`eleitorado.*`, `genero.N`, `instrucao.N`) e
  deputados nascidos no município (`deputados_nascidos.*`).

## Árvore dos indicadores

Cada folha mostra os anos cobertos, se tem `mes`, quantos municípios têm o dado, as chaves de
`dimensao` e o tipo, quando não é `valor` numérico: `texto`, `pai (sem valor)` ou `metadado`.
O caminho da raiz até a folha, unido por pontos, é o valor de `indicador`.

```
br_rodado_indicadores_municipais.municipio
├── agropecuaria/  (39 indicadores)
│   ├── aquicultura
│   │   ├── disponivel  — sem ano · 1.304 mun. · metadado
│   │   ├── motivo  — sem ano · 1.304 mun. · metadado
│   │   ├── produtos
│   │   │   ├── quantidade  — 2013–2025 · 4.256 mun. · dim: produto
│   │   │   └── valor  — 2013–2025 · 4.267 mun. · dim: produto
│   │   └── valor_total  — 2013–2025 · 4.267 mun.
│   ├── assentamentos
│   │   ├── area_ha  — sem ano · 5.571 mun.
│   │   ├── capacidade  — sem ano · 5.571 mun.
│   │   ├── familias  — sem ano · 5.571 mun.
│   │   ├── projetos
│   │   │   ├── area_ha  — sem ano · 2.013 mun. · dim: codigo, nome, fase, criacao, obtencao
│   │   │   ├── capacidade  — sem ano · 2.013 mun. · dim: codigo, nome, fase, criacao, obtencao
│   │   │   └── familias  — sem ano · 2.013 mun. · dim: codigo, nome, fase, criacao, obtencao
│   │   └── total  — sem ano · 5.571 mun.
│   ├── credito_rural
│   │   ├── disponivel  — sem ano · 26 mun. · metadado
│   │   ├── motivo  — sem ano · 26 mun. · metadado
│   │   └── serie
│   │       ├── contratos  — 2016–2026 · 5.545 mun.
│   │       ├── contratos_pronaf  — 2016–2026 · 5.545 mun.
│   │       ├── ultimo_mes  — 2016–2026 · 5.545 mun.
│   │       ├── valor  — 2016–2026 · 5.545 mun.
│   │       └── valor_pronaf  — 2016–2026 · 5.519 mun.
│   ├── erro  — sem ano · 3 mun. · metadado
│   ├── extracao_silvicultura
│   │   ├── extracao_vegetal
│   │   │   ├── produtos
│   │   │   │   ├── quantidade  — 1989–2024 · 5.178 mun. · dim: produto, unidade
│   │   │   │   └── valor  — 1989–2024 · 5.178 mun. · dim: produto, unidade
│   │   │   └── valor_total  — 1989–2024 · 5.178 mun.
│   │   └── silvicultura
│   │       ├── produtos
│   │       │   ├── quantidade  — 1991–2024 · 3.433 mun. · dim: produto, unidade
│   │       │   └── valor  — 1991–2024 · 3.433 mun. · dim: produto, unidade
│   │       └── valor_total  — 1991–2024 · 3.433 mun.
│   ├── imoveis_rurais
│   │   ├── cafir
│   │   │   ├── area_1000ha_mais  — sem ano · 3.765 mun.
│   │   │   ├── area_ha  — sem ano · 5.546 mun.
│   │   │   ├── area_mediana_ha  — sem ano · 5.546 mun.
│   │   │   ├── data_referencia  — sem ano · 5.547 mun. · texto
│   │   │   ├── imoveis  — sem ano · 5.547 mun.
│   │   │   └── imoveis_1000ha_mais  — sem ano · 5.547 mun.
│   │   └── itr
│   │       └── valor  — 2017–2024 · 5.570 mun.
│   ├── lavouras_top
│   │   ├── area_colhida  — 1989–2024 · 5.556 mun. · dim: tipo, produto
│   │   ├── quantidade_produzida  — 1989–2024 · 5.556 mun. · dim: tipo, produto
│   │   └── valor_producao  — 1989–2024 · 5.556 mun. · dim: tipo, produto
│   ├── origem_animal
│   │   └── produtos
│   │       ├── quantidade  — 1984–2025 · 5.568 mun. · dim: produto, unidade
│   │       └── valor  — 1984–2025 · 5.568 mun. · dim: produto, unidade
│   └── rebanhos
│       └── efetivos
│           └── quantidade  — 1990–2025 · 5.568 mun. · dim: tipo_rebanho
├── beneficios/  (72 indicadores)
│   ├── bolsa_familia
│   │   ├── familias  — 2025 · com mes · 5.570 mun.
│   │   ├── repasse_mensal  — 2025 · com mes · 5.570 mun.
│   │   └── valor_medio  — 2025 · com mes · 5.570 mun.
│   ├── bpc
│   │   ├── beneficiarios  — 2025 · com mes · 5.570 mun.
│   │   └── repasse_mensal  — 2025 · com mes · 5.570 mun.
│   ├── cadastro_unico
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── familias_cadastradas  — 2020 · com mes · 5.570 mun.
│   │   ├── familias_pbf  — 2020 · com mes · 5.570 mun.
│   │   ├── pct_populacao  — 2020 · com mes · 5.570 mun.
│   │   └── pessoas_cadastradas  — 2020 · com mes · 5.570 mun.
│   ├── cadunico_mds
│   │   ├── atualizacao
│   │   │   ├── atualizadas  — 2026 · com mes · 5.571 mun.
│   │   │   └── taxa  — 2026 · com mes · 5.571 mun.
│   │   ├── esgoto
│   │   │   └── familias  — 2026 · com mes · 5.571 mun. · dim: forma
│   │   ├── familias
│   │   │   ├── acima_meio_sm  — 2026 · com mes · 5.571 mun.
│   │   │   ├── baixa_renda  — 2026 · com mes · 5.571 mun.
│   │   │   ├── pobreza  — 2026 · com mes · 5.571 mun.
│   │   │   └── total  — 2026 · com mes · 5.571 mun.
│   │   ├── grupos_especificos
│   │   │   ├── lista
│   │   │   │   └── familias  — 2026 · com mes · 5.504 mun. · dim: grupo
│   │   │   └── total  — 2026 · com mes · 5.571 mun.
│   │   ├── local
│   │   │   ├── rural  — 2026 · com mes · 5.571 mun.
│   │   │   └── urbano  — 2026 · com mes · 5.571 mun.
│   │   ├── pessoas
│   │   │   ├── acima_meio_sm  — 2026 · com mes · 5.571 mun.
│   │   │   ├── baixa_renda  — 2026 · com mes · 5.571 mun.
│   │   │   ├── pobreza  — 2026 · com mes · 5.571 mun.
│   │   │   └── total  — 2026 · com mes · 5.571 mun.
│   │   ├── raca_cor
│   │   │   └── pessoas  — 2026 · com mes · 5.571 mun. · dim: raca
│   │   ├── responsavel_sexo
│   │   │   ├── feminino  — 2026 · com mes · 5.571 mun.
│   │   │   └── masculino  — 2026 · com mes · 5.571 mun.
│   │   ├── saida_pobreza_pbf
│   │   │   ├── permanecem  — 2026 · com mes · 5.471 mun.
│   │   │   └── saem  — 2026 · com mes · 5.571 mun.
│   │   ├── serie_familias
│   │   │   └── familias  — 2012–2026 · 5.571 mun. · dim: ref
│   │   ├── situacao_rua
│   │   │   ├── familias  — 2026 · com mes · 5.571 mun.
│   │   │   ├── pct_atendimento  — 2026 · com mes · 2.843 mun.
│   │   │   └── pessoas  — 2026 · com mes · 5.571 mun.
│   │   └── trabalho_infantil
│   │       └── pessoas  — 2023–2026 · com mes · 3.322 mun.
│   ├── erro  — sem ano · 1 mun. · metadado
│   ├── garantia_safra
│   │   ├── familias  — 2013–2026 · com mes · 1.322 mun.
│   │   └── repasse  — 2013–2026 · com mes · 1.322 mun.
│   ├── inss
│   │   ├── beneficios  — 2026 · com mes · 5.569 mun.
│   │   ├── bpc_por_tipo
│   │   │   ├── idoso  — 2026 · com mes · 5.558 mun.
│   │   │   └── pcd  — 2026 · com mes · 5.569 mun.
│   │   ├── concedidos
│   │   │   ├── beneficios  — 2012–2026 · 5.569 mun.
│   │   │   ├── meses  — 2012–2026 · 5.569 mun.
│   │   │   └── valor  — 2012–2026 · 5.569 mun.
│   │   ├── disponivel  — sem ano · 2 mun. · metadado
│   │   ├── motivo  — sem ano · 2 mun. · metadado
│   │   ├── por_1000hab
│   │   │   ├── ano_populacao  — 2026 · com mes · 5.569 mun.
│   │   │   ├── brasil  — 2026 · com mes · 5.569 mun.
│   │   │   ├── municipio  — 2026 · com mes · 5.569 mun.
│   │   │   └── uf  — 2026 · com mes · 5.569 mun.
│   │   ├── por_categoria
│   │   │   ├── n  — 2026 · com mes · 5.569 mun. · dim: k
│   │   │   └── valor  — 2026 · com mes · 5.569 mun. · dim: k
│   │   ├── por_clientela
│   │   │   └── n  — 2026 · com mes · 5.569 mun. · dim: k
│   │   ├── por_faixa_etaria
│   │   │   └── n  — 2026 · com mes · 5.569 mun. · dim: k
│   │   ├── por_sexo
│   │   │   └── n  — 2026 · com mes · 5.569 mun. · dim: k
│   │   ├── serie
│   │   │   ├── beneficios  — 2021–2026 · com mes · 5.569 mun.
│   │   │   └── valor_mensal  — 2023–2026 · com mes · 5.569 mun.
│   │   ├── valor_medio  — 2026 · com mes · 5.569 mun.
│   │   └── valor_mensal  — 2026 · com mes · 5.569 mun.
│   └── programas_cgu
│       ├── erro  — sem ano · 1 mun. · metadado
│       ├── gas_do_povo
│       │   ├── pessoas  — 2026 · com mes · 4.568 mun.
│       │   ├── serie_12m
│       │   │   ├── pessoas  — 2025–2026 · com mes · 4.568 mun.
│       │   │   └── valor  — 2025–2026 · com mes · 4.568 mun.
│       │   └── valor  — 2026 · com mes · 4.568 mun.
│       ├── pe_de_meia
│       │   ├── pessoas  — 2026 · com mes · 4.567 mun.
│       │   ├── serie_12m
│       │   │   ├── pessoas  — 2025–2026 · com mes · 4.567 mun.
│       │   │   └── valor  — 2025–2026 · com mes · 4.567 mun.
│       │   └── valor  — 2026 · com mes · 4.567 mun.
│       └── seguro_defeso
│           ├── pessoas  — 2013–2026 · com mes · 3.092 mun.
│           ├── serie_12m
│           │   ├── pessoas  — 2013–2026 · com mes · 3.092 mun.
│           │   └── valor  — 2013–2026 · com mes · 3.092 mun.
│           └── valor  — 2013–2026 · com mes · 3.092 mun.
├── comercio_exterior/  (8 indicadores)
│   ├── exportacoes
│   │   ├── ano_anterior_fob_usd  — 1998–2025 · 2.549 mun. · texto
│   │   ├── top_paises  — 1997–2025 · 2.933 mun. · dim: pais_iso3, valor_fob_usd · pai (sem valor)
│   │   ├── top_sh4  — 1997–2025 · 2.933 mun. · dim: id_sh4, valor_fob_usd · pai (sem valor)
│   │   └── total_fob_usd  — 1997–2025 · 2.933 mun. · texto
│   └── importacoes
│       ├── ano_anterior_fob_usd  — 1998–2025 · 2.277 mun. · texto
│       ├── top_paises  — 1997–2025 · 2.735 mun. · dim: pais_iso3, valor_fob_usd · pai (sem valor)
│       ├── top_sh4  — 1997–2025 · 2.735 mun. · dim: id_sh4, valor_fob_usd · pai (sem valor)
│       └── total_fob_usd  — 1997–2025 · 2.735 mun. · texto
├── conectividade/  (7 indicadores)
│   ├── banda_larga
│   │   ├── densidade_100hab  — 2025 · com mes · 5.570 mun.
│   │   └── densidade_brasil  — 2025 · com mes · 5.570 mun.
│   ├── erro  — sem ano · 1 mun. · metadado
│   └── ibc
│       ├── cobertura_pop_4g5g  — 2024 · 5.570 mun.
│       ├── fibra  — 2024 · 5.570 mun. · texto
│       ├── ibc  — 2024 · 5.570 mun.
│       └── media_brasil  — 2024 · 5.570 mun.
├── demografia/  (21 indicadores)
│   ├── censo_2022
│   │   ├── area_km2  — sem ano · 5.570 mun.
│   │   ├── domicilios  — sem ano · 5.570 mun.
│   │   ├── idade_mediana  — sem ano · 5.570 mun.
│   │   ├── indice_envelhecimento  — sem ano · 5.570 mun.
│   │   ├── populacao  — sem ano · 5.570 mun.
│   │   ├── razao_sexo  — sem ano · 5.570 mun.
│   │   └── taxa_alfabetizacao  — sem ano · 5.570 mun.
│   ├── censo_extra
│   │   ├── alfabetizacao_por_raca  — sem ano · 1.119 mun. · dim: cor_raca · pai (sem valor)
│   │   │   ├── alfabetizadas  — sem ano · 5.570 mun. · dim: cor_raca
│   │   │   ├── taxa  — sem ano · 5.570 mun. · dim: cor_raca
│   │   │   └── total  — sem ano · 5.570 mun. · dim: cor_raca
│   │   ├── cor_raca  — 2010–2022 · 1.648 mun. · dim: cor_raca · pai (sem valor)
│   │   │   └── populacao  — 2010–2022 · 5.570 mun. · dim: cor_raca
│   │   └── religiao
│   │       ├── grupos  — sem ano · 5.216 mun. · dim: religiao · pai (sem valor)
│   │       │   ├── pct  — sem ano · 5.570 mun. · dim: religiao
│   │       │   └── populacao  — sem ano · 5.570 mun. · dim: religiao
│   │       └── total_10_anos_ou_mais  — sem ano · 5.570 mun.
│   ├── nomes
│   │   └── top
│   │       └── pessoas  — sem ano · 5.565 mun. · dim: nome
│   ├── piramide_etaria_2022
│   │   ├── homens  — sem ano · 5.571 mun. · dim: grupos
│   │   └── mulheres  — sem ano · 5.571 mun. · dim: grupos
│   └── populacao_serie
│       └── populacao  — 1991–2025 · 5.570 mun.
├── economia/  (66 indicadores)
│   ├── bancario
│   │   ├── agencias  — 1988–2023 · com mes · 4.168 mun.
│   │   ├── depositos_totais  — 1988–2023 · com mes · 4.078 mun.
│   │   ├── erro  — sem ano · 1.403 mun. · metadado
│   │   ├── operacoes_credito  — 1988–2023 · com mes · 4.078 mun.
│   │   └── verbetes
│   │       ├── credito  — 1988–2023 · com mes · 4.168 mun. · texto
│   │       └── depositos  — 1988–2023 · com mes · 4.168 mun. · dim: i · texto
│   ├── bndes
│   │   ├── administracao_publica
│   │   │   ├── desembolsado  — 1995–2026 · 1.653 mun. · dim: ente, programa, projeto
│   │   │   └── valor  — 1995–2026 · 1.653 mun. · dim: ente, programa, projeto, situacao
│   │   ├── nao_automaticas
│   │   │   ├── desembolsado  — sem ano · 1.141 mun. · dim: contratacao, cliente, projeto
│   │   │   └── valor  — sem ano · 1.141 mun. · dim: contratacao, cliente, projeto, produto, situacao
│   │   ├── porte_5a
│   │   │   ├── desembolsado  — sem ano · 4.563 mun. · dim: porte
│   │   │   └── operacoes  — sem ano · 4.622 mun. · dim: porte
│   │   ├── serie_indiretas
│   │   │   ├── desembolsado  — 2002–2026 · 5.454 mun.
│   │   │   └── operacoes  — 2002–2026 · 5.456 mun.
│   │   └── setor_5a  — sem ano · 274 mun. · dim: setor · pai (sem valor)
│   │       └── desembolsado  — sem ano · 4.563 mun. · dim: setor
│   ├── combustiveis
│   │   ├── erro  — sem ano · 5.155 mun. · metadado
│   │   ├── janela_dias  — sem ano · 416 mun.
│   │   └── produtos
│   │       ├── postos  — sem ano · 416 mun. · dim: produto, ultima_coleta
│   │       ├── preco_brasil  — sem ano · 416 mun. · dim: produto, ultima_coleta
│   │       ├── preco_municipio  — sem ano · 416 mun. · dim: produto, ultima_coleta
│   │       └── preco_uf  — sem ano · 416 mun. · dim: produto, ultima_coleta
│   ├── financas_publicas
│   │   ├── despesas_funcao
│   │   │   └── valor  — 2022–2025 · 5.569 mun. · dim: funcao
│   │   ├── despesas_total_empenhado  — 2022–2025 · 5.569 mun.
│   │   ├── erro  — sem ano · 2 mun. · metadado
│   │   └── receitas
│   │       ├── fpm  — 2022–2025 · 5.564 mun.
│   │       ├── fundeb  — 2022–2025 · 5.530 mun.
│   │       ├── icms  — 2022–2025 · 5.561 mun.
│   │       ├── impostos  — 2022–2025 · 5.567 mun.
│   │       ├── iptu  — 2022–2025 · 5.462 mun.
│   │       ├── iss  — 2022–2025 · 5.548 mun.
│   │       ├── receitas_capital  — 2022–2025 · 5.402 mun.
│   │       ├── receitas_correntes  — 2022–2025 · 5.569 mun.
│   │       ├── sus  — 2022–2025 · 5.563 mun.
│   │       └── total  — 2022–2025 · 5.569 mun.
│   ├── inpc_brasil
│   │   ├── variacao_anual  — 2026 · com mes · 5.571 mun.
│   │   ├── variacao_doze_meses  — 2026 · com mes · 5.571 mun.
│   │   └── variacao_mensal  — 2026 · com mes · 5.571 mun.
│   ├── mineracao_cfem
│   │   ├── disponivel  — sem ano · 1.604 mun. · metadado
│   │   ├── motivo  — sem ano · 1.604 mun. · metadado
│   │   ├── serie
│   │   │   ├── pagadores  — 2002–2026 · 3.967 mun.
│   │   │   └── valor  — 2002–2026 · 3.967 mun.
│   │   ├── substancias
│   │   │   └── valor  — 2003–2026 · 3.967 mun. · dim: substancia
│   │   └── valor_ano  — 2003–2026 · 3.967 mun.
│   ├── pib
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── pib_per_capita
│   │   │   ├── brasil  — 2023 · 5.570 mun.
│   │   │   ├── uf  — 2023 · 5.570 mun.
│   │   │   └── valor  — 2023 · 5.570 mun.
│   │   ├── ranking_uf
│   │   │   ├── posicao  — 2023 · 5.570 mun.
│   │   │   └── total  — 2023 · 5.570 mun.
│   │   └── serie
│   │       ├── impostos_liquidos  — 2012–2021 · 5.570 mun.
│   │       ├── pib  — 2012–2023 · 5.570 mun.
│   │       ├── va  — 2012–2021 · 5.570 mun.
│   │       ├── va_adespss  — 2012–2021 · 5.570 mun.
│   │       ├── va_agropecuaria  — 2012–2021 · 5.570 mun.
│   │       ├── va_industria  — 2012–2021 · 5.570 mun.
│   │       └── va_servicos  — 2012–2021 · 5.570 mun.
│   └── pix
│       ├── pagadores_pf  — 2026 · com mes · 5.571 mun.
│       ├── pagadores_pf_por_hab  — 2026 · com mes · 5.570 mun.
│       ├── pagadores_pj  — 2026 · com mes · 5.571 mun.
│       ├── serie
│       │   ├── pago  — 2023–2026 · com mes · 5.571 mun.
│       │   └── recebido  — 2023–2026 · com mes · 5.571 mun.
│       ├── transacoes_pagas  — 2026 · com mes · 5.571 mun.
│       ├── transacoes_recebidas  — 2026 · com mes · 5.571 mun.
│       ├── valor_pago  — 2026 · com mes · 5.571 mun.
│       └── valor_recebido  — 2026 · com mes · 5.571 mun.
├── educacao/  (110 indicadores)
│   ├── alfabetizacao
│   │   ├── disponivel  — sem ano · 24 mun. · metadado
│   │   ├── media_municipios_uf  — 2023–2024 · 5.547 mun.
│   │   ├── metas
│   │   │   ├── meta_alfabetizacao_2024  — 2023–2024 · 5.232 mun. · dim: id_municipio, rede
│   │   │   ├── meta_alfabetizacao_2025  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   │   ├── meta_alfabetizacao_2026  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   │   ├── meta_alfabetizacao_2027  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   │   ├── meta_alfabetizacao_2028  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   │   ├── meta_alfabetizacao_2029  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   │   ├── meta_alfabetizacao_2030  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   │   ├── nivel_alfabetizacao  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   │   ├── percentual_participacao  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   │   └── taxa_alfabetizacao  — 2023–2024 · 5.352 mun. · dim: id_municipio, rede
│   │   ├── motivo  — sem ano · 24 mun. · metadado
│   │   ├── serie
│   │   │   └── taxa_alfabetizacao  — 2023–2024 · 5.547 mun.
│   │   └── taxa  — 2023–2024 · 5.547 mun.
│   ├── censo_escolar
│   │   ├── com_biblioteca  — 2025 · 5.571 mun.
│   │   ├── com_esgoto_rede  — 2025 · 5.571 mun.
│   │   ├── com_internet  — 2025 · 5.571 mun.
│   │   ├── com_laboratorio  — 2025 · 5.571 mun.
│   │   ├── com_quadra  — 2025 · 5.571 mun.
│   │   ├── com_rampa_acessibilidade  — 2025 · 5.571 mun.
│   │   ├── docentes  — 2025 · 5.571 mun.
│   │   ├── escolas  — 2025 · 5.571 mun.
│   │   ├── escolas_rurais  — 2025 · 5.571 mun.
│   │   ├── matriculas  — 2025 · 5.571 mun.
│   │   ├── matriculas_eja  — 2025 · 5.571 mun.
│   │   ├── matriculas_especial  — 2025 · 5.571 mun.
│   │   ├── matriculas_fundamental  — 2025 · 5.571 mun.
│   │   ├── matriculas_infantil  — 2025 · 5.571 mun.
│   │   ├── matriculas_medio  — 2025 · 5.571 mun.
│   │   ├── matriculas_transporte  — 2025 · 5.571 mun.
│   │   ├── por_rede
│   │   │   ├── docentes  — 2025 · 5.571 mun. · dim: rede
│   │   │   ├── escolas  — 2025 · 5.571 mun. · dim: rede
│   │   │   └── matriculas  — 2025 · 5.571 mun. · dim: rede
│   │   ├── serie
│   │   │   ├── escolas  — 2016–2025 · 5.571 mun.
│   │   │   └── matriculas  — 2016–2025 · 5.571 mun.
│   │   └── turmas  — 2025 · 5.571 mun.
│   ├── cnpq
│   │   ├── disponivel  — sem ano · 4.954 mun. · metadado
│   │   ├── motivo  — sem ano · 4.954 mun. · metadado
│   │   ├── por_instituicao
│   │   │   └── processos  — 2004–2022 · 617 mun. · dim: instituicao
│   │   ├── por_modalidade
│   │   │   └── processos  — 2004–2022 · 617 mun. · dim: modalidade
│   │   └── serie
│   │       ├── processos  — 2002–2022 · 617 mun.
│   │       └── valor  — 2002–2022 · 617 mun.
│   ├── conectada
│   │   ├── adequadas  — 2023 · 5.570 mun.
│   │   ├── com_internet  — 2023 · 5.570 mun.
│   │   ├── disponivel  — sem ano · 1 mun. · metadado
│   │   ├── download_mediano  — 2023 · 5.469 mun.
│   │   ├── escolas  — 2023 · 5.570 mun.
│   │   ├── internet_aprendizagem  — 2023 · 5.570 mun.
│   │   ├── laboratorio  — 2023 · 5.570 mun.
│   │   ├── medidas  — 2023 · 5.570 mun.
│   │   ├── motivo  — sem ano · 1 mun. · metadado
│   │   └── por_faixa
│   │       └── escolas  — 2023 · 5.570 mun. · dim: faixa
│   ├── enem
│   │   ├── humanas  — 2023 · 1.750 mun.
│   │   ├── inscritos  — 2023 · 5.571 mun.
│   │   ├── linguagens  — 2023 · 1.750 mun.
│   │   ├── matematica  — 2023 · 1.750 mun.
│   │   ├── media_geral  — 2023 · 1.750 mun.
│   │   ├── natureza  — 2023 · 1.750 mun.
│   │   ├── presentes  — 2023 · 5.571 mun.
│   │   └── redacao  — 2023 · 1.750 mun.
│   ├── especial
│   │   ├── disponivel  — sem ano · 1 mun. · metadado
│   │   ├── motivo  — sem ano · 1 mun. · metadado
│   │   ├── por_classe
│   │   │   └── matriculas  — 2024 · 5.570 mun. · dim: classe
│   │   └── por_tipo
│   │       └── matriculas  — 2024 · 5.570 mun. · dim: tipo
│   ├── ideb
│   │   ├── finais
│   │   │   ├── ideb  — 2005–2025 · 5.568 mun.
│   │   │   ├── meta  — 2007–2019 · 5.564 mun.
│   │   │   └── taxa_aprovacao  — 2005–2025 · 5.569 mun.
│   │   ├── iniciais
│   │   │   ├── ideb  — 2005–2025 · 5.560 mun.
│   │   │   ├── meta  — 2007–2019 · 5.549 mun.
│   │   │   └── taxa_aprovacao  — 2005–2025 · 5.568 mun.
│   │   ├── referencia_brasil
│   │   │   ├── finais  — sem ano · 5.571 mun.
│   │   │   └── iniciais  — sem ano · 5.571 mun.
│   │   └── referencia_uf
│   │       ├── finais  — sem ano · 5.571 mun.
│   │       └── iniciais  — sem ano · 5.571 mun.
│   ├── indicadores
│   │   └── erro  — sem ano · 1 mun. · metadado
│   ├── inse
│   │   ├── alunos  — 2019–2021 · 5.569 mun.
│   │   ├── disponivel  — sem ano · 2 mun. · metadado
│   │   ├── inse  — 2019–2021 · 5.569 mun.
│   │   ├── media_municipios_br  — 2019–2021 · 5.569 mun.
│   │   ├── media_municipios_uf  — 2019–2021 · 5.569 mun.
│   │   ├── motivo  — sem ano · 2 mun. · metadado
│   │   └── niveis_pct
│   │       ├── nivel  — 2019–2021 · 5.569 mun.
│   │       └── pct  — 2019–2021 · 5.569 mun.
│   ├── saeb
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   └── provas
│   │       ├── distribuicao_niveis_pct  — 2021–2023 · 5.562 mun. · dim: disciplina, serie, i
│   │       └── media  — 2021–2023 · 5.562 mun. · dim: disciplina, serie
│   ├── sisu
│   │   ├── erro  — sem ano · 4 mun. · metadado
│   │   ├── serie
│   │   │   ├── aprovados  — 2017–2022 · 5.567 mun.
│   │   │   ├── candidatos  — 2017–2022 · 5.567 mun.
│   │   │   ├── matriculados  — 2017–2022 · 5.567 mun.
│   │   │   └── nota_media  — 2017–2022 · 5.567 mun.
│   │   ├── top_cursos
│   │   │   └── matriculados  — 2018–2022 · 4.846 mun. · dim: curso, ies
│   │   └── vagas_no_municipio
│   │       ├── ampla  — 2021–2022 · 550 mun.
│   │       ├── cotas  — 2021–2022 · 465 mun.
│   │       └── total  — 2021–2022 · 551 mun.
│   └── superior
│       ├── concluintes  — 2009–2024 · 3.826 mun.
│       ├── cursos  — 2009–2024 · 3.826 mun.
│       ├── cursos_presenciais  — 2009–2024 · 3.826 mun.
│       ├── disponivel  — sem ano · 1.745 mun. · metadado
│       ├── ies  — 2009–2024 · 3.826 mun.
│       ├── ingressantes  — 2009–2024 · 3.826 mun.
│       ├── matriculas  — 2009–2024 · 3.826 mun.
│       ├── matriculas_ead  — 2009–2024 · 3.770 mun.
│       ├── matriculas_presenciais  — 2009–2024 · 1.150 mun.
│       ├── motivo  — sem ano · 1.745 mun. · metadado
│       ├── por_area
│       │   └── matriculas  — 2009–2024 · 3.826 mun. · dim: area
│       ├── por_rede
│       │   └── matriculas  — 2009–2024 · 3.826 mun. · dim: rede
│       ├── serie_matriculas
│       │   └── matriculas  — 2009–2024 · 3.826 mun.
│       └── vagas  — 2009–2024 · 3.826 mun.
├── empresas/  (13 indicadores)
│   ├── ativas  — 2026 · com mes · 5.570 mun.
│   ├── baixadas  — 2026 · com mes · 5.570 mun.
│   ├── demografia_empresarial
│   │   ├── aberturas  — 2016–2026 · 5.570 mun.
│   │   ├── baixas  — 2016–2026 · 5.570 mun.
│   │   └── saldo  — 2016–2026 · 5.570 mun.
│   ├── erro  — sem ano · 1 mun. · metadado
│   ├── filiais  — 2026 · com mes · 5.570 mun.
│   ├── idade_media_anos  — 2026 · com mes · 5.570 mun.
│   ├── matrizes  — 2026 · com mes · 5.570 mun.
│   ├── mei  — 2026 · com mes · 5.570 mun.
│   ├── por_secao_cnae
│   │   └── ativas  — 2026 · com mes · 5.570 mun. · dim: secao
│   ├── registradas  — 2026 · com mes · 5.570 mun.
│   └── top_atividades
│       └── ativas  — 2026 · com mes · 5.570 mun. · dim: atividade
├── geografia/  (11 indicadores)
│   ├── arranjo_populacional
│   │   ├── nome  — sem ano · 953 mun. · texto
│   │   └── populacao_2010  — sem ano · 953 mun.
│   ├── biomas
│   │   └── pct_area  — sem ano · 5.570 mun. · dim: nome
│   ├── regiao_metropolitana
│   │   ├── nome  — sem ano · 1.384 mun. · texto
│   │   └── tipo  — sem ano · 1.384 mun. · texto
│   ├── sede_municipal
│   │   ├── lat  — 2010 · 5.565 mun.
│   │   └── lon  — 2010 · 5.565 mun.
│   ├── semiarido  — sem ano · 5.571 mun.
│   └── unidades_conservacao
│       ├── lista  — sem ano · 1.922 mun. · dim: unidade_conservacao, categoria, esfera · pai (sem valor)
│       ├── por_categoria
│       │   └── quantidade  — sem ano · 1.922 mun. · dim: categoria, esfera
│       └── total  — sem ano · 5.571 mun.
├── infraestrutura/  (85 indicadores)
│   ├── atlas_esgotos
│   │   ├── ano_referencia  — sem ano · 5.570 mun.
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── indice_atendimento_com_coleta_com_tratamento  — sem ano · 5.570 mun.
│   │   ├── indice_atendimento_com_coleta_sem_tratamento  — sem ano · 5.570 mun.
│   │   ├── indice_atendimento_solucao_individual  — sem ano · 5.570 mun.
│   │   ├── indice_sem_atendimento_sem_coleta_sem_tratamento  — sem ano · 5.570 mun.
│   │   ├── investimento_coleta  — sem ano · 5.570 mun.
│   │   ├── investimento_coleta_tratatamento  — sem ano · 5.570 mun.
│   │   ├── investimento_tratamento  — sem ano · 5.570 mun.
│   │   ├── populacao_urbana_2013  — sem ano · 5.570 mun.
│   │   ├── populacao_urbana_2035  — sem ano · 5.570 mun.
│   │   └── prestador_servico_esgotamento_sanitario  — sem ano · 5.570 mun. · texto
│   ├── censo_domicilios
│   │   ├── agua
│   │   │   ├── categorias
│   │   │   │   ├── pct  — sem ano · 5.570 mun. · dim: categoria
│   │   │   │   └── populacao  — sem ano · 5.570 mun. · dim: categoria
│   │   │   └── total  — sem ano · 5.570 mun.
│   │   ├── domicilios_recenseados  — sem ano · 2.631 mun. · dim: especie · pai (sem valor)
│   │   │   └── domicilios  — sem ano · 5.570 mun. · dim: especie
│   │   ├── esgotamento
│   │   │   ├── categorias
│   │   │   │   ├── pct  — sem ano · 5.570 mun. · dim: categoria
│   │   │   │   └── populacao  — sem ano · 5.570 mun. · dim: categoria
│   │   │   └── total  — sem ano · 5.570 mun.
│   │   ├── lixo
│   │   │   ├── categorias
│   │   │   │   ├── pct  — sem ano · 5.570 mun. · dim: categoria
│   │   │   │   └── populacao  — sem ano · 5.570 mun. · dim: categoria
│   │   │   └── total  — sem ano · 5.570 mun.
│   │   └── tipo_domicilio
│   │       ├── categorias
│   │       │   ├── pct  — sem ano · 5.570 mun. · dim: categoria
│   │       │   └── populacao  — sem ano · 5.570 mun. · dim: categoria
│   │       └── total  — sem ano · 5.570 mun.
│   ├── energia_continuidade
│   │   ├── conjuntos  — sem ano · 1.857 mun. · dim: nome, agente · pai (sem valor)
│   │   ├── erro  — sem ano · 3.714 mun. · metadado
│   │   └── serie
│   │       ├── dec_horas  — 2014–2025 · 1.838 mun.
│   │       ├── fec_vezes  — 2014–2025 · 1.838 mun.
│   │       ├── limite_dec  — 2014–2025 · 1.838 mun.
│   │       ├── limite_fec  — 2014–2025 · 1.838 mun.
│   │       └── unidades  — 2014–2025 · 1.838 mun.
│   ├── energia_gd
│   │   ├── data_base  — sem ano · 5.567 mun. · texto
│   │   ├── erro  — sem ano · 4 mun. · metadado
│   │   ├── instalacoes  — sem ano · 5.567 mun.
│   │   ├── por_ano_cadastro
│   │   │   ├── instalacoes  — 1900–2026 · 5.567 mun.
│   │   │   └── kw  — 1900–2026 · 5.567 mun.
│   │   ├── por_classe
│   │   │   ├── instalacoes  — sem ano · 5.567 mun. · dim: classe
│   │   │   └── kw  — sem ano · 5.567 mun. · dim: classe
│   │   ├── por_fonte
│   │   │   ├── instalacoes  — sem ano · 5.567 mun. · dim: fonte
│   │   │   └── kw  — sem ano · 5.567 mun. · dim: fonte
│   │   ├── potencia_mw  — sem ano · 5.567 mun.
│   │   ├── ucs_recebem_credito  — sem ano · 5.567 mun.
│   │   └── w_por_habitante  — sem ano · 5.566 mun.
│   ├── frota
│   │   ├── por_tipo
│   │   │   └── quantidade  — 2026 · com mes · 5.571 mun. · dim: tipo
│   │   ├── serie
│   │   │   └── total  — 2013–2026 · 5.571 mun.
│   │   ├── total  — 2026 · com mes · 5.571 mun.
│   │   └── veiculos_1000hab
│   │       ├── ano_populacao  — 2026 · com mes · 5.571 mun.
│   │       ├── brasil  — 2026 · com mes · 5.571 mun.
│   │       ├── municipio  — 2026 · com mes · 5.570 mun.
│   │       └── uf  — 2026 · com mes · 5.571 mun.
│   ├── obras_cno
│   │   ├── data_extracao  — sem ano · 5.568 mun. · texto
│   │   ├── disponivel  — sem ano · 3 mun. · metadado
│   │   ├── iniciadas_por_ano
│   │   │   ├── area_m2  — 2016–2025 · 5.564 mun.
│   │   │   └── obras  — 2016–2025 · 5.564 mun.
│   │   ├── motivo  — sem ano · 3 mun. · metadado
│   │   ├── obras  — sem ano · 5.568 mun.
│   │   └── por_situacao
│   │       └── obras  — sem ano · 5.568 mun. · dim: situacao
│   ├── outorgas_agua
│   │   ├── disponivel  — sem ano · 775 mun. · metadado
│   │   ├── maiores  — sem ano · 1.235 mun. · dim: responsavel · pai (sem valor)
│   │   │   └── vazao  — sem ano · 4.610 mun. · dim: responsavel
│   │   ├── motivo  — sem ano · 775 mun. · metadado
│   │   ├── outorgas  — sem ano · 4.796 mun.
│   │   ├── por_esfera
│   │   │   ├── outorgas  — sem ano · 4.796 mun. · dim: esfera
│   │   │   └── vazao  — sem ano · 4.610 mun. · dim: esfera
│   │   └── vazao_total  — sem ano · 4.796 mun.
│   └── snis
│       ├── ano_anterior
│       │   ├── a  — 2007–2021 · 5.353 mun.
│       │   ├── c  — 2007–2021 · 2.800 mun.
│       │   └── t  — 2007–2021 · 2.798 mun.
│       ├── despesa_total_servico  — 2000–2022 · 5.538 mun.
│       ├── erro  — sem ano · 22 mun. · metadado
│       ├── extensao_rede_agua  — 2000–2022 · 5.541 mun.
│       ├── extensao_rede_esgoto  — 2006–2022 · 3.101 mun.
│       ├── indice_atendimento_esgoto_esgoto  — 2008–2021 · 44 mun.
│       ├── indice_atendimento_total_agua  — 2001–2022 · 5.540 mun.
│       ├── indice_atendimento_urbano_agua  — 2000–2021 · 117 mun.
│       ├── indice_coleta_esgoto  — 2008–2022 · 2.936 mun.
│       ├── indice_perda_distribuicao_agua  — 2001–2022 · 5.516 mun.
│       ├── indice_tratamento_esgoto  — 2008–2022 · 2.939 mun.
│       ├── populacao_atendida_agua  — 2000–2022 · 5.542 mun.
│       ├── populacao_atentida_esgoto  — 2008–2022 · 2.944 mun.
│       ├── volume_agua_consumido  — 2001–2022 · 5.537 mun.
│       ├── volume_esgoto_coletado  — 2006–2022 · 3.100 mun.
│       └── volume_esgoto_tratado  — 2006–2022 · 3.101 mun.
├── meio_ambiente/  (47 indicadores)
│   ├── car
│   │   ├── area_ha  — sem ano · 5.563 mun.
│   │   ├── camadas_ha
│   │   │   ├── app  — sem ano · 5.561 mun.
│   │   │   ├── area_consolidada  — sem ano · 5.355 mun.
│   │   │   ├── reserva_legal  — sem ano · 5.560 mun.
│   │   │   ├── uso_restrito  — sem ano · 4.153 mun.
│   │   │   └── vegetacao_nativa  — sem ano · 5.558 mun.
│   │   ├── data_extracao  — sem ano · 5.564 mun. · texto
│   │   ├── disponivel  — sem ano · 7 mun. · metadado
│   │   ├── imoveis  — sem ano · 5.564 mun.
│   │   ├── motivo  — sem ano · 7 mun. · metadado
│   │   ├── pendentes  — sem ano · 5.564 mun.
│   │   ├── por_condicao
│   │   │   └── imoveis  — sem ano · 5.563 mun. · dim: condicao
│   │   ├── por_tipo
│   │   │   ├── area_ha  — sem ano · 5.563 mun. · dim: tipo
│   │   │   └── imoveis  — sem ano · 5.563 mun. · dim: tipo
│   │   └── suspensos  — sem ano · 5.564 mun.
│   ├── desastres
│   │   ├── data_extracao  — sem ano · 5.571 mun. · texto
│   │   ├── municipios_uf_com_reconhecimento  — sem ano · 5.571 mun.
│   │   └── vigentes  — sem ano · 1.091 mun. · dim: desastre, situacao, ocorrencia, vigencia · pai (sem valor)
│   ├── estacoes_inmet
│   │   └── estacoes  — sem ano · 1 mun. · dim: id_estacao, estacao, fundacao · pai (sem valor)
│   │       └── altitude  — sem ano · 607 mun. · dim: id_estacao, estacao, fundacao
│   ├── ibama
│   │   ├── autos_total  — sem ano · 5.571 mun.
│   │   ├── embargos  — sem ano · 5.571 mun.
│   │   ├── embargos_5a  — sem ano · 5.571 mun.
│   │   ├── serie
│   │   │   ├── autos  — 1981–2026 · 5.462 mun.
│   │   │   └── valor  — 1981–2026 · 5.461 mun.
│   │   ├── tipos_10a
│   │   │   └── autos  — sem ano · 4.296 mun. · dim: tipo
│   │   └── valor_total  — sem ano · 5.571 mun.
│   ├── mapbiomas
│   │   ├── anos  — sem ano · 5.571 mun. · dim: i
│   │   └── transicoes
│   │       ├── area_2010  — sem ano · 5.566 mun. · dim: de, para
│   │       └── area_2020  — sem ano · 5.566 mun. · dim: de, para
│   ├── prodes
│   │   ├── biomas
│   │   │   ├── area_total  — 2022–2023 · 5.570 mun. · dim: bioma
│   │   │   ├── desmatado  — 2022–2023 · 5.570 mun. · dim: bioma
│   │   │   └── vegetacao_natural  — 2022–2023 · 5.570 mun. · dim: bioma
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   └── serie
│   │       ├── area_total  — 2000–2023 · 5.570 mun. · dim: bioma
│   │       ├── desmatado  — 2000–2023 · 5.570 mun. · dim: bioma
│   │       └── vegetacao_natural  — 2000–2023 · 5.570 mun. · dim: bioma
│   ├── queimadas
│   │   └── serie
│   │       ├── focos  — 2003–2026 · 5.568 mun.
│   │       ├── frp_max  — 2023–2026 · 5.565 mun.
│   │       └── frp_medio  — 2023–2026 · 5.565 mun.
│   ├── seeg
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── gas  — 2024 · 5.570 mun. · texto
│   │   ├── por_setor
│   │   │   └── emissao_tco2e  — 2024 · 5.570 mun. · dim: setor
│   │   ├── tipo  — 2024 · 5.570 mun. · texto
│   │   └── total_tco2e  — 2024 · 5.570 mun.
│   └── sisam
│       └── serie
│           ├── co_ppb  — 2000–2018 · 5.570 mun.
│           └── pm25_ugm3  — 2000–2019 · 5.570 mun.
├── municipio/  (19 indicadores)
│   ├── amazonia_legal  — sem ano · 5.571 mun.
│   ├── area_km2  — sem ano · 5.570 mun.
│   ├── capital_uf  — sem ano · 5.570 mun.
│   ├── ddd  — sem ano · 5.570 mun. · texto
│   ├── id_comarca  — sem ano · 5.570 mun. · texto
│   ├── id_municipio  — sem ano · 5.571 mun. · texto
│   ├── id_municipio_bcb  — sem ano · 5.570 mun. · texto
│   ├── id_municipio_rf  — sem ano · 5.570 mun. · texto
│   ├── id_municipio_tse  — sem ano · 5.570 mun. · texto
│   ├── mesorregiao  — sem ano · 5.570 mun. · texto
│   ├── microrregiao  — sem ano · 5.570 mun. · texto
│   ├── nome  — sem ano · 5.571 mun. · texto
│   ├── nome_uf  — sem ano · 5.571 mun. · texto
│   ├── regiao  — sem ano · 5.571 mun. · texto
│   ├── regiao_imediata  — sem ano · 5.571 mun. · texto
│   ├── regiao_intermediaria  — sem ano · 5.571 mun. · texto
│   ├── regiao_metropolitana  — sem ano · 1.432 mun. · texto
│   ├── regiao_saude  — sem ano · 5.570 mun. · texto
│   └── sigla_uf  — sem ano · 5.571 mun. · texto
├── politica/  (56 indicadores)
│   ├── ano_prefeito  — 2026 · 5.570 mun.
│   ├── camara_municipal
│   │   ├── bancadas
│   │   │   ├── cadeiras  — 2020–2024 · 5.568 mun. · dim: partido
│   │   │   └── votos  — 2020–2024 · 5.568 mun. · dim: partido
│   │   ├── cadeiras_total  — 2020–2024 · 5.568 mun.
│   │   ├── erro  — 2026 · 3 mun. · metadado
│   │   ├── financiamento
│   │   │   ├── candidatos  — 2020–2024 · 5.568 mun. · dim: cargo
│   │   │   └── receita  — 2020–2024 · 5.568 mun. · dim: cargo
│   │   └── perfil_candidatos
│   │       ├── brancos  — 2020–2024 · 5.568 mun.
│   │       ├── candidatos  — 2020–2024 · 5.568 mun.
│   │       ├── feminino  — 2020–2024 · 5.568 mun.
│   │       ├── idade_media  — 2020–2024 · 5.568 mun.
│   │       ├── masculino  — 2020–2024 · 5.568 mun.
│   │       └── negros  — 2020–2024 · 5.568 mun.
│   ├── deputados_nascidos
│   │   ├── deputados  — 2026 · 1.427 mun. · dim: nome, nascimento, falecido · pai (sem valor)
│   │   └── total  — 2026 · 5.571 mun.
│   ├── eleitorado
│   │   ├── aptos  — 2026 · 5.570 mun.
│   │   ├── biometria  — 2026 · 5.570 mun.
│   │   └── zonas  — 2026 · 5.570 mun.
│   ├── erro  — sem ano · 1 mun. · metadado
│   ├── filiados
│   │   ├── data_extracao  — 2026 · 5.570 mun. · texto
│   │   ├── disponivel  — sem ano · 1 mun. · metadado
│   │   ├── filiados  — 2026 · 5.570 mun.
│   │   ├── motivo  — sem ano · 1 mun. · metadado
│   │   ├── por_partido
│   │   │   └── filiados  — 2026 · 5.570 mun. · dim: partido
│   │   └── por_sexo
│   │       └── filiados  — 2026 · 5.570 mun. · dim: sexo
│   ├── financas_campanha
│   │   ├── despesas_por_cargo
│   │   │   └── valor  — 2024–2026 · 5.569 mun. · dim: cargo
│   │   ├── despesas_por_tipo
│   │   │   └── valor  — 2024–2026 · 5.569 mun.
│   │   ├── disponivel  — 2026 · 2 mun. · metadado
│   │   ├── motivo  — 2026 · 2 mun. · metadado
│   │   ├── receitas_por_cargo
│   │   │   ├── candidatos  — 2024–2026 · 5.569 mun. · dim: cargo
│   │   │   └── valor  — 2024–2026 · 5.569 mun. · dim: cargo
│   │   └── receitas_por_origem
│   │       └── valor  — 2024–2026 · 5.569 mun. · dim: origem
│   ├── genero
│   │   ├── 0  — 2026 · 949 mun.
│   │   ├── 2  — 2026 · 5.570 mun.
│   │   └── 4  — 2026 · 5.570 mun.
│   ├── instrucao
│   │   ├── 0  — 2026 · 898 mun.
│   │   ├── 1  — 2026 · 5.570 mun.
│   │   ├── 2  — 2026 · 5.570 mun.
│   │   ├── 3  — 2026 · 5.570 mun.
│   │   ├── 4  — 2026 · 5.570 mun.
│   │   ├── 5  — 2026 · 5.570 mun.
│   │   ├── 6  — 2026 · 5.570 mun.
│   │   ├── 7  — 2026 · 5.570 mun.
│   │   └── 8  — 2026 · 5.570 mun.
│   └── prefeito
│       ├── abstencoes  — 2024 · 5.568 mun.
│       ├── aptos  — 2024 · 5.568 mun.
│       ├── comparecimento  — 2024 · 5.568 mun.
│       ├── eleito
│       │   ├── nome_urna  — 2024 · 5.515 mun. · texto
│       │   ├── partido  — 2024 · 5.518 mun. · texto
│       │   ├── turno  — 2024 · 5.518 mun.
│       │   └── votos  — 2024 · 5.518 mun.
│       ├── secoes  — 2024 · 5.568 mun.
│       ├── turno  — 2024 · 5.568 mun.
│       ├── votos_brancos  — 2024 · 5.568 mun.
│       ├── votos_nominais  — 2024 · 5.568 mun.
│       └── votos_nulos  — 2024 · 5.568 mun.
├── saude/  (157 indicadores)
│   ├── atencao_basica
│   │   ├── cobertura_ab  — sem ano · 5.570 mun.
│   │   ├── cobertura_esf  — sem ano · 5.570 mun.
│   │   ├── disponivel  — sem ano · 1 mun. · metadado
│   │   ├── equipes  — sem ano · 5.570 mun.
│   │   ├── motivo  — sem ano · 1 mun. · metadado
│   │   ├── referencia  — sem ano · 5.570 mun. · texto
│   │   └── serie
│   │       ├── cobertura_ab  — 2007–2020 · com mes · 5.570 mun.
│   │       ├── cobertura_esf  — 2007–2020 · com mes · 5.570 mun.
│   │       └── equipes  — 2007–2020 · com mes · 5.570 mun.
│   ├── cnes
│   │   ├── agentes
│   │   │   ├── ace  — 2024–2025 · com mes · 5.570 mun.
│   │   │   └── acs  — 2024–2025 · com mes · 5.570 mun.
│   │   ├── equipes
│   │   │   ├── por_tipo
│   │   │   │   └── n  — 2026 · com mes · 5.569 mun. · dim: tipo
│   │   │   └── total  — 2026 · com mes · 5.570 mun.
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── estabelecimentos  — 2025 · com mes · 5.570 mun.
│   │   ├── leitos
│   │   │   ├── sus  — 2005–2026 · com mes · 4.040 mun.
│   │   │   └── total  — 2005–2026 · com mes · 4.040 mun.
│   │   ├── profissionais
│   │   │   └── vinculos  — 2024–2025 · com mes · 5.570 mun.
│   │   └── unidades
│   │       ├── caps  — 2025 · com mes · 5.570 mun.
│   │       ├── samu  — 2025 · com mes · 5.570 mun.
│   │       ├── ubs  — 2025 · com mes · 5.570 mun.
│   │       └── upa  — 2025 · com mes · 5.570 mun.
│   ├── dengue
│   │   ├── classificacao_bruta
│   │   │   └── <evolucao>|<classificacao>  — 32 combinações de código SINAN cru · até 4.150 mun.
│   │   ├── confirmados  — 2005–2026 · 5.566 mun.
│   │   ├── erro  — sem ano · 5 mun. · metadado
│   │   ├── graves  — 2005–2026 · 5.566 mun.
│   │   ├── notificados  — 2005–2026 · 5.566 mun.
│   │   ├── notificados_ano_anterior  — 2005–2026 · 5.566 mun.
│   │   └── obitos  — 2005–2026 · 5.566 mun.
│   ├── farmacia_popular
│   │   └── estabelecimentos_credenciados  — sem ano · 5.571 mun.
│   ├── ieps
│   │   ├── ano_max  — sem ano · 5.570 mun.
│   │   ├── ano_por_indicador
│   │   │   ├── cobertura_atencao_basica  — sem ano · 5.570 mun.
│   │   │   ├── cobertura_esf  — sem ano · 5.570 mun.
│   │   │   ├── cobertura_plano_privado  — sem ano · 5.565 mun.
│   │   │   ├── despesa_saude_per_capita  — sem ano · 5.568 mun.
│   │   │   ├── enfermeiros_1000hab  — sem ano · 5.570 mun.
│   │   │   ├── leitos_sus_100k  — sem ano · 5.570 mun.
│   │   │   ├── leitos_uti_sus_100k  — sem ano · 5.570 mun.
│   │   │   ├── medicos_1000hab  — sem ano · 5.570 mun.
│   │   │   ├── pct_prenatal_adequado  — sem ano · 5.570 mun.
│   │   │   ├── pct_prenatal_zero  — sem ano · 5.570 mun.
│   │   │   ├── pct_receita_propria_saude  — sem ano · 5.568 mun.
│   │   │   ├── taxa_internacao_csap_100k  — sem ano · 5.570 mun.
│   │   │   └── taxa_mortalidade_evitavel_100k  — sem ano · 5.570 mun.
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   └── indicadores
│   │       ├── cobertura_atencao_basica  — sem ano · 5.570 mun.
│   │       ├── cobertura_esf  — sem ano · 5.570 mun.
│   │       ├── cobertura_plano_privado  — sem ano · 5.565 mun.
│   │       ├── despesa_saude_per_capita  — sem ano · 5.568 mun.
│   │       ├── enfermeiros_1000hab  — sem ano · 5.570 mun.
│   │       ├── leitos_sus_100k  — sem ano · 5.570 mun.
│   │       ├── leitos_uti_sus_100k  — sem ano · 5.570 mun.
│   │       ├── medicos_1000hab  — sem ano · 5.570 mun.
│   │       ├── pct_prenatal_adequado  — sem ano · 5.570 mun.
│   │       ├── pct_prenatal_zero  — sem ano · 5.570 mun.
│   │       ├── pct_receita_propria_saude  — sem ano · 5.568 mun.
│   │       ├── taxa_internacao_csap_100k  — sem ano · 5.570 mun.
│   │       └── taxa_mortalidade_evitavel_100k  — sem ano · 5.570 mun.
│   ├── imunizacao
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   └── serie
│   │       ├── cobertura_bcg  — 2010–2021 · 5.570 mun.
│   │       ├── cobertura_hepatite_b  — 2010–2021 · 5.570 mun.
│   │       ├── cobertura_penta  — 2012–2021 · 5.570 mun.
│   │       ├── cobertura_poliomielite  — 2010–2021 · 5.570 mun.
│   │       ├── cobertura_total  — 2010–2021 · 5.570 mun.
│   │       └── cobertura_triplice_viral_d1  — 2010–2021 · 5.570 mun.
│   ├── internacoes
│   │   ├── ano_anterior
│   │   │   ├── internacoes  — 2021–2023 · 5.570 mun.
│   │   │   └── valor_total  — 2021–2023 · 5.570 mun.
│   │   ├── diarias_uti  — 2022–2024 · 5.570 mun.
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── internacoes  — 2022–2024 · 5.570 mun.
│   │   ├── no_municipio  — 2022–2024 · 5.570 mun.
│   │   ├── obitos_hospitalares  — 2022–2024 · 5.570 mun.
│   │   ├── pct_no_municipio  — 2022–2024 · 5.570 mun.
│   │   ├── permanencia_media  — 2022–2024 · 5.570 mun.
│   │   ├── por_capitulo
│   │   │   ├── internacoes  — 2022–2024 · 5.570 mun. · dim: capitulo
│   │   │   └── valor  — 2022–2024 · 5.570 mun. · dim: capitulo
│   │   ├── serie
│   │   │   ├── internacoes  — 2013–2024 · 5.570 mun.
│   │   │   └── valor  — 2013–2024 · 5.570 mun.
│   │   ├── taxa_mortalidade_hospitalar  — 2022–2024 · 5.570 mun.
│   │   ├── urgencia  — 2022–2024 · 5.570 mun.
│   │   ├── valor_medio_aih  — 2022–2024 · 5.570 mun.
│   │   └── valor_total  — 2022–2024 · 5.570 mun.
│   ├── mortalidade
│   │   ├── agressoes  — 2025 · 5.570 mun.
│   │   ├── ano_parcial
│   │   │   ├── ate_mes  — 2026 · 5.559 mun.
│   │   │   ├── infantis  — 2026 · 5.559 mun.
│   │   │   └── obitos  — 2026 · 5.559 mun.
│   │   ├── causas_externas  — 2025 · 5.570 mun.
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── homens  — 2025 · 5.570 mun.
│   │   ├── idade_media_obito  — 2025 · 5.570 mun.
│   │   ├── infantil
│   │   │   ├── nascidos_vivos  — 2022 · 5.570 mun.
│   │   │   ├── neonatais  — 2022 · 5.570 mun.
│   │   │   ├── obitos  — 2022 · 5.570 mun.
│   │   │   └── taxa_1000nv  — 2022 · 5.570 mun.
│   │   ├── mal_definidas  — 2025 · 5.570 mun.
│   │   ├── maternas  — 2025 · 5.570 mun.
│   │   ├── mulheres  — 2025 · 5.570 mun.
│   │   ├── obitos  — 2025 · 5.570 mun.
│   │   ├── obitos_infantis  — 2025 · 5.570 mun.
│   │   ├── obitos_neonatais  — 2025 · 5.570 mun.
│   │   ├── populacao_referencia  — 2025 · 5.570 mun.
│   │   ├── por_capitulo
│   │   │   └── obitos  — 2025 · 5.570 mun. · dim: capitulo
│   │   ├── serie
│   │   │   ├── infantis  — 2014–2025 · 5.570 mun.
│   │   │   └── obitos  — 2014–2025 · 5.570 mun.
│   │   ├── suicidios  — 2025 · 5.570 mun.
│   │   ├── taxa_mortalidade_1000hab  — 2025 · 5.570 mun.
│   │   ├── top_causas
│   │   │   └── obitos  — 2025 · 5.570 mun. · dim: cid
│   │   └── transporte  — 2025 · 5.570 mun.
│   ├── nascidos_vivos
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── nascidos_vivos  — 2022 · 5.570 mun.
│   │   ├── pct_baixo_peso  — 2022 · 5.570 mun.
│   │   ├── pct_cesareo  — 2022 · 5.570 mun.
│   │   └── pre_natal_distribuicao
│   │       ├── 1  — 2022 · 3.489 mun.
│   │       ├── 2  — 2022 · 4.673 mun.
│   │       ├── 3  — 2022 · 5.484 mun.
│   │       ├── 4  — 2022 · 5.570 mun.
│   │       ├── 9  — 2022 · 1.327 mun.
│   │       └── None  — 2022 · 335 mun.
│   ├── planos_privados
│   │   ├── beneficiarios_total  — 2025 · com mes · 5.570 mun.
│   │   ├── cobertura_pct  — 2025 · com mes · 5.568 mun.
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   ├── medico_hospitalar  — 2025 · com mes · 5.568 mun.
│   │   ├── odontologico  — 2025 · com mes · 5.570 mun.
│   │   └── por_contratacao
│   │       └── beneficiarios  — 2025 · com mes · 5.570 mun. · dim: tipo
│   └── sisvan
│       ├── criancas_acompanhadas  — 2023 · 5.570 mun.
│       └── erro  — sem ano · 1 mun. · metadado
├── seguranca/  (171 indicadores)
│   ├── fbsp
│   │   ├── disponivel  — sem ano · 5.544 mun. · metadado
│   │   ├── motivo  — sem ano · 5.544 mun. · metadado
│   │   ├── proporcao_mortes_intenvencao_policial_x_mortes_violentas_intencionais  — 2021 · 27 mun.
│   │   ├── quantidade_estupro  — 2021 · 26 mun.
│   │   ├── quantidade_feminicidio  — 2021 · 27 mun.
│   │   ├── quantidade_furto_veiculos  — 2021 · 26 mun.
│   │   ├── quantidade_homicidio_doloso  — 2021 · 27 mun.
│   │   ├── quantidade_latrocinio  — 2021 · 27 mun.
│   │   ├── quantidade_lesao_corporal_dolosa_violencia_domestica  — 2021 · 25 mun.
│   │   ├── quantidade_lesao_corporal_morte  — 2021 · 26 mun.
│   │   ├── quantidade_mortes_intervencao_policial  — 2021 · 27 mun.
│   │   ├── quantidade_mortes_policiais_confronto  — 2021 · 27 mun.
│   │   ├── quantidade_mortes_violentas_intencionais  — 2021 · 27 mun.
│   │   ├── quantidade_porte_ilegal_arma_de_fogo  — 2021 · 22 mun.
│   │   ├── quantidade_posse_ilegal_arma_de_fogo  — 2021 · 20 mun.
│   │   ├── quantidade_posse_ilegal_porte_ilegal_arma_de_fogo  — 2021 · 26 mun.
│   │   ├── quantidade_posse_uso_entorpecente  — 2021 · 27 mun.
│   │   ├── quantidade_roubo_furto_veiculos  — 2021 · 27 mun.
│   │   ├── quantidade_roubo_veiculos  — 2021 · 26 mun.
│   │   └── quantidade_trafico_entorpecente  — 2021 · 27 mun.
│   ├── isp_rj
│   │   ├── disponivel  — sem ano · 5.479 mun. · metadado
│   │   ├── homicidio_doloso_ano_anterior  — 2025 · 92 mun.
│   │   ├── mensal
│   │   │   ├── homicidio_doloso  — 2025 · com mes · 92 mun.
│   │   │   └── letalidade_violenta  — 2025 · com mes · 92 mun.
│   │   ├── motivo  — sem ano · 5.479 mun. · metadado
│   │   ├── ocorrencias
│   │   │   ├── cvli  — 2025 · 92 mun.
│   │   │   ├── estupro  — 2025 · 92 mun.
│   │   │   ├── homicidio_doloso  — 2025 · 92 mun.
│   │   │   ├── intervencao_policial  — 2025 · 92 mun.
│   │   │   ├── latrocinio  — 2025 · 92 mun.
│   │   │   ├── lesao_corporal_morte  — 2025 · 92 mun.
│   │   │   ├── letalidade_violenta  — 2025 · 92 mun.
│   │   │   ├── roubo_veiculo  — 2025 · 92 mun.
│   │   │   └── tentativa_homicidio  — 2025 · 92 mun.
│   │   ├── taxas_100k
│   │   │   ├── taxa_estupro  — 2020 · 38 mun.
│   │   │   ├── taxa_homicidio_doloso  — 2020 · 38 mun.
│   │   │   ├── taxa_homicidio_intervencao_policial  — 2020 · 38 mun.
│   │   │   ├── taxa_latrocinio  — 2020 · 38 mun.
│   │   │   ├── taxa_lesao_corporal_morte  — 2020 · 38 mun.
│   │   │   ├── taxa_letalidade_violenta  — 2020 · 38 mun.
│   │   │   └── taxa_tentativa_homicidio  — 2020 · 38 mun.
│   │   └── taxas_100k_uf
│   │       ├── taxa_estupro  — 2020 · 92 mun.
│   │       ├── taxa_homicidio_doloso  — 2020 · 92 mun.
│   │       ├── taxa_homicidio_intervencao_policial  — 2020 · 92 mun.
│   │       ├── taxa_latrocinio  — 2020 · 92 mun.
│   │       ├── taxa_lesao_corporal_morte  — 2020 · 92 mun.
│   │       ├── taxa_letalidade_violenta  — 2020 · 92 mun.
│   │       ├── taxa_roubo_veiculo  — 2020 · 92 mun.
│   │       └── taxa_tentativa_homicidio  — 2020 · 92 mun.
│   ├── prf
│   │   ├── acidentes  — sem ano · 2.143 mun.
│   │   ├── ate  — sem ano · 2.143 mun.
│   │   ├── desde  — sem ano · 5.571 mun.
│   │   ├── disponivel  — sem ano · 3.428 mun. · metadado
│   │   ├── feridos_graves  — sem ano · 2.143 mun.
│   │   ├── mortos  — sem ano · 2.143 mun.
│   │   ├── motivo  — sem ano · 3.428 mun. · metadado
│   │   ├── por_ano
│   │   │   ├── acidentes  — 2021–2026 · 2.143 mun.
│   │   │   ├── feridos  — 2021–2026 · 2.143 mun.
│   │   │   ├── feridos_graves  — 2021–2026 · 2.143 mun.
│   │   │   └── mortos  — 2021–2026 · 2.143 mun.
│   │   ├── por_causa
│   │   │   └── n  — sem ano · 2.143 mun. · dim: k
│   │   ├── por_rodovia
│   │   │   └── n  — sem ano · 2.143 mun. · dim: k
│   │   └── por_tipo
│   │       └── n  — sem ano · 2.143 mun. · dim: k
│   ├── sinesp
│   │   ├── ano_parcial
│   │   │   ├── ate_mes  — 2026 · 5.570 mun.
│   │   │   └── por_tipo
│   │   │       ├── feminicidio
│   │   │       │   ├── meses  — 2026 · 5.570 mun.
│   │   │       │   ├── vitimas  — 2026 · 5.570 mun.
│   │   │       │   └── vitimas_feminino  — 2026 · 5.570 mun.
│   │   │       ├── homicidio_doloso
│   │   │       │   ├── meses  — 2026 · 5.570 mun.
│   │   │       │   ├── vitimas  — 2026 · 5.570 mun.
│   │   │       │   └── vitimas_feminino  — 2026 · 5.570 mun.
│   │   │       ├── latrocinio
│   │   │       │   ├── meses  — 2026 · 5.570 mun.
│   │   │       │   ├── vitimas  — 2026 · 5.570 mun.
│   │   │       │   └── vitimas_feminino  — 2026 · 5.570 mun.
│   │   │       ├── lesao_corporal_seguida_de_morte
│   │   │       │   ├── meses  — 2026 · 5.570 mun.
│   │   │       │   ├── vitimas  — 2026 · 5.570 mun.
│   │   │       │   └── vitimas_feminino  — 2026 · 5.570 mun.
│   │   │       ├── mandado_de_prisao_cumprido
│   │   │       │   ├── meses  — 2026 · 5.570 mun.
│   │   │       │   └── ocorrencias  — 2026 · 5.570 mun.
│   │   │       ├── morte_a_esclarecer
│   │   │       │   ├── meses  — 2026 · 4.359 mun.
│   │   │       │   ├── vitimas  — 2026 · 4.359 mun.
│   │   │       │   └── vitimas_feminino  — 2026 · 4.359 mun.
│   │   │       ├── morte_no_transito_exceto_homicidio_doloso
│   │   │       │   ├── meses  — 2026 · 5.570 mun.
│   │   │       │   ├── vitimas  — 2026 · 5.570 mun.
│   │   │       │   └── vitimas_feminino  — 2026 · 5.570 mun.
│   │   │       ├── suicidio
│   │   │       │   ├── meses  — 2026 · 5.570 mun.
│   │   │       │   ├── vitimas  — 2026 · 5.570 mun.
│   │   │       │   └── vitimas_feminino  — 2026 · 5.570 mun.
│   │   │       ├── tentativa_de_feminicidio
│   │   │       │   ├── meses  — 2026 · 5.570 mun.
│   │   │       │   ├── vitimas  — 2026 · 5.570 mun.
│   │   │       │   └── vitimas_feminino  — 2026 · 5.570 mun.
│   │   │       └── tentativa_de_homicidio
│   │   │           ├── meses  — 2026 · 5.570 mun.
│   │   │           ├── vitimas  — 2026 · 5.570 mun.
│   │   │           └── vitimas_feminino  — 2026 · 5.570 mun.
│   │   ├── disponivel  — sem ano · 1 mun. · metadado
│   │   ├── motivo  — sem ano · 1 mun. · metadado
│   │   ├── por_tipo
│   │   │   ├── feminicidio
│   │   │   │   ├── meses  — 2025 · 5.570 mun.
│   │   │   │   ├── vitimas  — 2025 · 5.570 mun.
│   │   │   │   └── vitimas_feminino  — 2025 · 5.570 mun.
│   │   │   ├── homicidio_doloso
│   │   │   │   ├── meses  — 2025 · 5.570 mun.
│   │   │   │   ├── vitimas  — 2025 · 5.570 mun.
│   │   │   │   └── vitimas_feminino  — 2025 · 5.570 mun.
│   │   │   ├── latrocinio
│   │   │   │   ├── meses  — 2025 · 5.570 mun.
│   │   │   │   ├── vitimas  — 2025 · 5.570 mun.
│   │   │   │   └── vitimas_feminino  — 2025 · 5.570 mun.
│   │   │   ├── lesao_corporal_seguida_de_morte
│   │   │   │   ├── meses  — 2025 · 5.570 mun.
│   │   │   │   ├── vitimas  — 2025 · 5.570 mun.
│   │   │   │   └── vitimas_feminino  — 2025 · 5.570 mun.
│   │   │   ├── mandado_de_prisao_cumprido
│   │   │   │   ├── meses  — 2025 · 5.570 mun.
│   │   │   │   └── ocorrencias  — 2025 · 5.393 mun.
│   │   │   ├── morte_a_esclarecer
│   │   │   │   ├── meses  — 2025 · 4.421 mun.
│   │   │   │   ├── vitimas  — 2025 · 4.421 mun.
│   │   │   │   └── vitimas_feminino  — 2025 · 4.421 mun.
│   │   │   ├── morte_no_transito_exceto_homicidio_doloso
│   │   │   │   ├── meses  — 2025 · 5.570 mun.
│   │   │   │   ├── vitimas  — 2025 · 5.570 mun.
│   │   │   │   └── vitimas_feminino  — 2025 · 5.570 mun.
│   │   │   ├── suicidio
│   │   │   │   ├── meses  — 2025 · 5.570 mun.
│   │   │   │   ├── vitimas  — 2025 · 5.570 mun.
│   │   │   │   └── vitimas_feminino  — 2025 · 5.530 mun.
│   │   │   ├── tentativa_de_feminicidio
│   │   │   │   ├── meses  — 2025 · 5.570 mun.
│   │   │   │   ├── vitimas  — 2025 · 5.570 mun.
│   │   │   │   └── vitimas_feminino  — 2025 · 5.532 mun.
│   │   │   └── tentativa_de_homicidio
│   │   │       ├── meses  — 2025 · 5.570 mun.
│   │   │       ├── vitimas  — 2025 · 5.570 mun.
│   │   │       └── vitimas_feminino  — 2025 · 5.570 mun.
│   │   ├── serie
│   │   │   ├── homicidio_doloso  — 2015–2026 · 5.570 mun.
│   │   │   └── meses  — 2015–2026 · 5.570 mun.
│   │   └── taxa_homicidio_doloso_100k
│   │       ├── ano_populacao  — 2025 · 5.570 mun.
│   │       ├── brasil  — 2025 · 5.570 mun.
│   │       ├── municipio  — 2025 · 5.570 mun.
│   │       └── uf  — 2025 · 5.570 mun.
│   ├── sisdepen
│   │   ├── capacidade  — sem ano · 1.164 mun.
│   │   ├── competencia  — sem ano · 1.164 mun. · texto
│   │   ├── disponivel  — sem ano · 4.407 mun. · metadado
│   │   ├── faixa_etaria  — sem ano · 240 mun. · dim: k · pai (sem valor)
│   │   │   └── n  — sem ano · 1.101 mun. · dim: k
│   │   ├── lista  — sem ano · 1 mun. · dim: nome · pai (sem valor)
│   │   │   └── capacidade  — sem ano · 1.164 mun. · dim: nome
│   │   ├── motivo  — sem ano · 4.407 mun. · metadado
│   │   ├── mulheres  — sem ano · 1.164 mun.
│   │   ├── populacao  — sem ano · 1.164 mun.
│   │   ├── por_regime
│   │   │   └── n  — sem ano · 1.164 mun. · dim: k
│   │   ├── provisorios  — sem ano · 1.164 mun.
│   │   ├── raca_cor  — sem ano · 229 mun. · dim: k · pai (sem valor)
│   │   │   └── n  — sem ano · 1.102 mun. · dim: k
│   │   ├── serie
│   │   │   └── populacao  — sem ano · 1.164 mun. · dim: periodo
│   │   ├── taxa_ocupacao  — sem ano · 1.163 mun.
│   │   └── unidades  — sem ano · 1.164 mun.
│   └── violencia_sinan
│       ├── arma_fogo  — 2020–2025 · 5.569 mun.
│       ├── autoprovocadas  — 2020–2025 · 5.569 mun.
│       ├── brancos  — 2020–2025 · 5.569 mun.
│       ├── erro  — sem ano · 2 mun. · metadado
│       ├── feminino  — 2020–2025 · 5.569 mun.
│       ├── financeira  — 2020–2025 · 5.569 mun.
│       ├── fisica  — 2020–2025 · 5.569 mun.
│       ├── infantil_trabalho  — 2020–2025 · 5.569 mun.
│       ├── masculino  — 2020–2025 · 5.569 mun.
│       ├── negligencia  — 2020–2025 · 5.569 mun.
│       ├── negros  — 2020–2025 · 5.569 mun.
│       ├── nota_raca  — 2020–2025 · 5.569 mun. · texto
│       ├── notificacoes  — 2020–2025 · 5.569 mun.
│       ├── pct_feminino  — 2020–2025 · 5.569 mun.
│       ├── pct_negros  — 2020–2025 · 5.569 mun.
│       ├── por_ciclo_vida
│       │   └── n  — 2020–2025 · 5.569 mun. · dim: ciclo
│       ├── por_local
│       │   └── n  — 2020–2025 · 5.569 mun. · dim: local
│       ├── psicologica  — 2020–2025 · 5.569 mun.
│       ├── raca_ignorada  — 2020–2025 · 5.569 mun.
│       ├── serie
│       │   ├── autoprovocadas  — 2011–2025 · 5.569 mun.
│       │   └── notificacoes  — 2011–2025 · 5.569 mun.
│       ├── sexual  — 2020–2025 · 5.569 mun.
│       ├── tortura  — 2020–2025 · 5.569 mun.
│       └── trafico_humano  — 2020–2025 · 5.569 mun.
├── social/  (29 indicadores)
│   ├── avs
│   │   ├── idhm  — 2010 · 5.565 mun.
│   │   ├── idhm_educacao  — 2010 · 5.565 mun.
│   │   ├── idhm_longevidade  — 2010 · 5.565 mun.
│   │   ├── idhm_renda  — 2010 · 5.565 mun.
│   │   ├── ivs  — 2010 · 5.565 mun.
│   │   ├── ivs_capital_humano  — 2010 · 5.565 mun.
│   │   ├── ivs_infraestrutura_urbana  — 2010 · 5.565 mun.
│   │   └── ivs_renda_trabalho  — 2010 · 5.565 mun.
│   ├── primeira_infancia
│   │   ├── matriculas_pre_escola  — 2019 · 5.570 mun.
│   │   ├── taxa_bruta_pre_escola  — 2019 · 5.570 mun.
│   │   └── taxa_liquida_pre_escola  — 2019 · 5.570 mun.
│   ├── rouanet
│   │   ├── disponivel  — sem ano · 1.154 mun. · metadado
│   │   ├── entidades  — sem ano · 4.417 mun.
│   │   ├── motivo  — sem ano · 1.154 mun. · metadado
│   │   ├── projetos  — sem ano · 4.417 mun.
│   │   ├── proponentes  — sem ano · 4.417 mun.
│   │   ├── top_proponentes
│   │   │   ├── projetos  — sem ano · 4.311 mun. · dim: nome
│   │   │   └── valor  — sem ano · 4.311 mun. · dim: nome
│   │   └── valor_projetos  — sem ano · 4.417 mun.
│   └── sinpatinhas
│       ├── animais  — sem ano · 5.397 mun.
│       ├── disponivel  — sem ano · 174 mun. · metadado
│       ├── motivo  — sem ano · 174 mun. · metadado
│       ├── periodo
│       │   ├── ate  — sem ano · 5.397 mun. · texto
│       │   └── de  — sem ano · 5.397 mun. · texto
│       ├── por_1000hab
│       │   ├── ano_populacao  — sem ano · 5.397 mun.
│       │   ├── brasil  — sem ano · 5.397 mun.
│       │   ├── municipio  — sem ano · 5.397 mun.
│       │   └── uf  — sem ano · 5.397 mun.
│       └── por_especie
│           └── n  — sem ano · 5.397 mun. · dim: k
├── trabalho/  (22 indicadores)
│   ├── caged
│   │   ├── admissoes  — 2020–2025 · 5.562 mun.
│   │   ├── desligamentos  — 2020–2025 · 5.562 mun.
│   │   ├── erro  — sem ano · 9 mun. · metadado
│   │   ├── salario_medio_admissao  — 2020–2025 · 5.559 mun.
│   │   └── saldo  — 2020–2025 · 5.562 mun.
│   ├── lista_suja
│   │   ├── brasil
│   │   │   ├── empregadores  — sem ano · 5.571 mun.
│   │   │   └── trabalhadores  — sem ano · 5.571 mun.
│   │   ├── data_coleta  — sem ano · 5.571 mun. · texto
│   │   ├── empregadores
│   │   │   ├── ano_acao_fiscal  — sem ano · 325 mun. · dim: empregador, documento, atividade, local
│   │   │   └── trabalhadores  — sem ano · 325 mun. · dim: empregador, documento, atividade, local
│   │   ├── total  — sem ano · 5.571 mun.
│   │   ├── trabalhadores  — sem ano · 5.571 mun.
│   │   └── uf
│   │       ├── empregadores  — sem ano · 5.571 mun.
│   │       └── trabalhadores  — sem ano · 5.555 mun.
│   ├── rais
│   │   ├── estabelecimentos  — 2025 · 5.571 mun.
│   │   ├── remuneracao_media  — 2025 · 5.571 mun.
│   │   ├── vinculos_ativos_3112  — 2025 · 5.571 mun.
│   │   └── vinculos_ativos_ano_anterior  — 2025 · 5.571 mun.
│   ├── top_empregadores
│   │   ├── erro  — sem ano · 1 mun. · metadado
│   │   └── top
│   │       └── vinculos_ativos  — 2021 · 5.564 mun. · dim: empresa, setor, natureza
│   └── top_empregadores_publicos
│       ├── erro  — sem ano · 1 mun. · metadado
│       └── top
│           └── vinculos_ativos  — 2021 · 5.556 mun. · dim: empresa, natureza
├── transparencia/  (52 indicadores)
│   ├── cauc
│   │   ├── data_pesquisa  — sem ano · 5.569 mun. · texto
│   │   ├── disponivel  — sem ano · 2 mun. · metadado
│   │   ├── itens  — sem ano · 5.569 mun.
│   │   ├── itens_pendentes  — sem ano · 4.541 mun. · dim: item, descricao, situacao · pai (sem valor)
│   │   ├── lista  — sem ano · 5.569 mun. · dim: item, descricao, situacao · pai (sem valor)
│   │   ├── motivo  — sem ano · 2 mun. · metadado
│   │   ├── pendencias  — sem ano · 5.569 mun.
│   │   └── regulares  — sem ano · 5.569 mun.
│   ├── clp
│   │   └── pilares
│   │       ├── colocacao  — 2022 · 415 mun. · dim: pilar_dimensao
│   │       └── nota_geral  — 2022 · 415 mun. · dim: pilar_dimensao
│   ├── compras_federais
│   │   ├── fornecedores_locais
│   │   │   ├── serie
│   │   │   │   ├── contratos  — 2013–2026 · 2.932 mun.
│   │   │   │   └── valor  — 2013–2026 · 2.932 mun.
│   │   │   ├── snapshot_cnpj  — sem ano · 5.570 mun. · texto
│   │   │   └── top
│   │   │       ├── contratos  — sem ano · 2.932 mun. · dim: empresa
│   │   │       └── valor  — sem ano · 2.932 mun. · dim: empresa
│   │   └── licitacoes_no_municipio
│   │       ├── por_orgao
│   │       │   ├── licitacoes  — sem ano · 609 mun. · dim: orgao
│   │       │   └── valor  — sem ano · 609 mun. · dim: orgao
│   │       └── serie
│   │           ├── licitacoes  — 2013–2023 · 609 mun.
│   │           └── valor  — 2013–2023 · 609 mun.
│   ├── consumidor
│   │   ├── erro  — sem ano · 8 mun. · metadado
│   │   ├── serie
│   │   │   ├── nota_media  — 2014–2025 · 5.539 mun.
│   │   │   ├── pct_respondida  — 2014–2025 · 5.563 mun.
│   │   │   └── reclamacoes  — 2014–2025 · 5.563 mun.
│   │   ├── top_empresas
│   │   │   └── reclamacoes  — 2016–2025 · 5.563 mun. · dim: empresa
│   │   └── top_segmentos
│   │       └── reclamacoes  — 2016–2025 · 5.563 mun. · dim: segmento
│   ├── diarios_oficiais
│   │   ├── erro  — sem ano · 5.047 mun. · metadado
│   │   ├── serie
│   │   │   ├── edicoes  — 2023–2026 · 524 mun.
│   │   │   └── extras  — 2023–2026 · 524 mun.
│   │   ├── total_edicoes  — sem ano · 524 mun.
│   │   └── ultima_edicao  — sem ano · 524 mun. · texto
│   ├── ebt
│   │   ├── nota  — 2020–2021 · 665 mun.
│   │   └── ranking  — 2020–2021 · 665 mun.
│   ├── emendas
│   │   ├── erro  — sem ano · 153 mun. · metadado
│   │   ├── janela_autores  — 2014–2025 · 5.418 mun. · texto
│   │   ├── por_funcao
│   │   │   └── pago  — 2014–2025 · 3.694 mun. · dim: funcao
│   │   ├── serie
│   │   │   ├── emendas  — 2014–2025 · 5.418 mun.
│   │   │   ├── empenhado  — 2014–2025 · 5.418 mun.
│   │   │   └── pago  — 2014–2025 · 5.418 mun.
│   │   └── top_autores
│   │       ├── emendas  — 2014–2025 · 5.418 mun. · dim: autor
│   │       └── pago  — 2014–2025 · 5.418 mun. · dim: autor
│   ├── fiscal
│   │   └── ifgf
│   │       ├── indice  — 2013–2022 · 5.566 mun.
│   │       ├── ranking_estadual  — 2013–2022 · 5.566 mun.
│   │       └── ranking_nacional  — 2013–2022 · 5.566 mun.
│   ├── fiscalizacao_cgu
│   │   └── sorteios  — sem ano · 1.949 mun. · dim: i
│   └── servidores
│       ├── adm_direta  — 2020–2023 · 5.570 mun.
│       ├── adm_indireta  — 2020–2023 · 1.431 mun.
│       ├── clt_adm_direta  — 2020–2023 · 5.570 mun.
│       ├── comissionado_adm_direta  — 2020–2023 · 5.570 mun.
│       ├── erro  — sem ano · 1 mun. · metadado
│       ├── estagio_adm_direta  — 2020–2023 · 5.570 mun.
│       ├── estatutario_adm_direta  — 2020–2023 · 5.570 mun.
│       └── sem_vinculo_permanente_adm_direta  — 2020–2023 · 5.570 mun.
└── vizinhanca/  (7 indicadores)
    ├── erro  — sem ano · 1 mun. · metadado
    ├── municipios
    │   ├── pib_per_capita  — sem ano · 5.568 mun. · dim: id_municipio, nome, sigla_uf
    │   └── populacao  — sem ano · 5.568 mun. · dim: id_municipio, nome, sigla_uf
    └── referencia
        ├── pib_ano  — sem ano · 5.570 mun.
        ├── pib_per_capita  — sem ano · 5.570 mun.
        ├── populacao  — sem ano · 5.570 mun.
        └── populacao_ano  — sem ano · 5.570 mun.
```

## Catálogo por seção

Os mesmos indicadores em tabela, com a mediana de `valor` entre todas as linhas (dá a ordem de
grandeza e a unidade). Para `texto`, um exemplo do conteúdo.

### `agropecuaria` (39 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `aquicultura.produtos.quantidade` | 2013–2025 | 4.256 | produto | valor | 3950 |
| `aquicultura.produtos.valor` | 2013–2025 | 4.267 | produto | valor | 56 |
| `aquicultura.valor_total` | 2013–2025 | 4.267 |  | valor | 194 |
| `assentamentos.area_ha` | — | 5.571 |  | valor | 0 |
| `assentamentos.capacidade` | — | 5.571 |  | valor | 0 |
| `assentamentos.familias` | — | 5.571 |  | valor | 0 |
| `assentamentos.projetos.area_ha` | — | 2.013 | codigo, nome, fase, criacao, obtencao | valor | 1444,312 |
| `assentamentos.projetos.capacidade` | — | 2.013 | codigo, nome, fase, criacao, obtencao | valor | 56 |
| `assentamentos.projetos.familias` | — | 2.013 | codigo, nome, fase, criacao, obtencao | valor | 49 |
| `assentamentos.total` | — | 5.571 |  | valor | 0 |
| `credito_rural.serie.contratos` | 2016–2026 | 5.545 |  | valor | 140 |
| `credito_rural.serie.contratos_pronaf` | 2016–2026 | 5.545 |  | valor | 97 |
| `credito_rural.serie.ultimo_mes` | 2016–2026 | 5.545 |  | valor | 12 |
| `credito_rural.serie.valor` | 2016–2026 | 5.545 |  | valor | 5.579.610,74 |
| `credito_rural.serie.valor_pronaf` | 2016–2026 | 5.519 |  | valor | 1.979.661,625 |
| `extracao_silvicultura.extracao_vegetal.produtos.quantidade` | 1989–2024 | 5.178 | produto, unidade | valor | 79 |
| `extracao_silvicultura.extracao_vegetal.produtos.valor` | 1989–2024 | 5.178 | produto, unidade | valor | 27 |
| `extracao_silvicultura.extracao_vegetal.valor_total` | 1989–2024 | 5.178 |  | valor | 63 |
| `extracao_silvicultura.silvicultura.produtos.quantidade` | 1991–2024 | 3.433 | produto, unidade | valor | 2311,5 |
| `extracao_silvicultura.silvicultura.produtos.valor` | 1991–2024 | 3.433 | produto, unidade | valor | 306 |
| `extracao_silvicultura.silvicultura.valor_total` | 1991–2024 | 3.433 |  | valor | 1064 |
| `imoveis_rurais.cafir.area_1000ha_mais` | — | 3.765 |  | valor | 12.347,8 |
| `imoveis_rurais.cafir.area_ha` | — | 5.546 |  | valor | 43.046,1 |
| `imoveis_rurais.cafir.area_mediana_ha` | — | 5.546 |  | valor | 14 |
| `imoveis_rurais.cafir.data_referencia` | — | 5.547 |  | texto | `2025-09-02` |
| `imoveis_rurais.cafir.imoveis` | — | 5.547 |  | valor | 1029 |
| `imoveis_rurais.cafir.imoveis_1000ha_mais` | — | 5.547 |  | valor | 2 |
| `imoveis_rurais.itr.valor` | 2017–2024 | 5.570 |  | valor | 27.120,09 |
| `lavouras_top.area_colhida` | 1989–2024 | 5.556 | tipo, produto | valor | 83 |
| `lavouras_top.quantidade_produzida` | 1989–2024 | 5.556 | tipo, produto | valor | 454 |
| `lavouras_top.valor_producao` | 1989–2024 | 5.556 | tipo, produto | valor | 960 |
| `origem_animal.produtos.quantidade` | 1984–2025 | 5.568 | produto, unidade | valor | 700 |
| `origem_animal.produtos.valor` | 1984–2025 | 5.568 | produto, unidade | valor | 458 |
| `rebanhos.efetivos.quantidade` | 1990–2025 | 5.568 | tipo_rebanho | valor | 1644 |

Metadados da coleta: `aquicultura.disponivel`, `aquicultura.motivo`, `credito_rural.disponivel`, `credito_rural.motivo`, `erro`.

### `beneficios` (72 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `bolsa_familia.familias` | 2025 (+mes) | 5.570 |  | valor | 1183,5 |
| `bolsa_familia.repasse_mensal` | 2025 (+mes) | 5.570 |  | valor | 792.301,5 |
| `bolsa_familia.valor_medio` | 2025 (+mes) | 5.570 |  | valor | 666,407 |
| `bpc.beneficiarios` | 2025 (+mes) | 5.570 |  | valor | 251 |
| `bpc.repasse_mensal` | 2025 (+mes) | 5.570 |  | valor | 381.027,9 |
| `cadastro_unico.familias_cadastradas` | 2020 (+mes) | 5.570 |  | valor | 2114 |
| `cadastro_unico.familias_pbf` | 2020 (+mes) | 5.570 |  | valor | 971 |
| `cadastro_unico.pct_populacao` | 2020 (+mes) | 5.570 |  | valor | 49,458 |
| `cadastro_unico.pessoas_cadastradas` | 2020 (+mes) | 5.570 |  | valor | 5668 |
| `cadunico_mds.atualizacao.atualizadas` | 2026 (+mes) | 5.571 |  | valor | 2579 |
| `cadunico_mds.atualizacao.taxa` | 2026 (+mes) | 5.571 |  | valor | 90,22 |
| `cadunico_mds.esgoto.familias` | 2026 (+mes) | 5.571 | forma | valor | 55 |
| `cadunico_mds.familias.acima_meio_sm` | 2026 (+mes) | 5.571 |  | valor | 1012 |
| `cadunico_mds.familias.baixa_renda` | 2026 (+mes) | 5.571 |  | valor | 518 |
| `cadunico_mds.familias.pobreza` | 2026 (+mes) | 5.571 |  | valor | 1165 |
| `cadunico_mds.familias.total` | 2026 (+mes) | 5.571 |  | valor | 2861 |
| `cadunico_mds.grupos_especificos.lista.familias` | 2026 (+mes) | 5.504 | grupo | valor | 6 |
| `cadunico_mds.grupos_especificos.total` | 2026 (+mes) | 5.571 |  | valor | 220 |
| `cadunico_mds.local.rural` | 2026 (+mes) | 5.571 |  | valor | 655 |
| `cadunico_mds.local.urbano` | 2026 (+mes) | 5.571 |  | valor | 1826 |
| `cadunico_mds.pessoas.acima_meio_sm` | 2026 (+mes) | 5.571 |  | valor | 1857 |
| `cadunico_mds.pessoas.baixa_renda` | 2026 (+mes) | 5.571 |  | valor | 1474 |
| `cadunico_mds.pessoas.pobreza` | 2026 (+mes) | 5.571 |  | valor | 2883 |
| `cadunico_mds.pessoas.total` | 2026 (+mes) | 5.571 |  | valor | 6616 |
| `cadunico_mds.raca_cor.pessoas` | 2026 (+mes) | 5.571 | raca | valor | 103 |
| `cadunico_mds.responsavel_sexo.feminino` | 2026 (+mes) | 5.571 |  | valor | 2175 |
| `cadunico_mds.responsavel_sexo.masculino` | 2026 (+mes) | 5.571 |  | valor | 634 |
| `cadunico_mds.saida_pobreza_pbf.permanecem` | 2026 (+mes) | 5.471 |  | valor | 65 |
| `cadunico_mds.saida_pobreza_pbf.saem` | 2026 (+mes) | 5.571 |  | valor | 979 |
| `cadunico_mds.serie_familias.familias` | 2012–2026 | 5.571 | ref | valor | 2287 |
| `cadunico_mds.situacao_rua.familias` | 2026 (+mes) | 5.571 |  | valor | 1 |
| `cadunico_mds.situacao_rua.pct_atendimento` | 2026 (+mes) | 2.843 |  | valor | 87,84 |
| `cadunico_mds.situacao_rua.pessoas` | 2026 (+mes) | 5.571 |  | valor | 1 |
| `cadunico_mds.trabalho_infantil.pessoas` | 2023–2026 (+mes) | 3.322 |  | valor | 1 |
| `garantia_safra.familias` | 2013–2026 (+mes) | 1.322 |  | valor | 1 |
| `garantia_safra.repasse` | 2013–2026 (+mes) | 1.322 |  | valor | 1925 |
| `inss.beneficios` | 2026 (+mes) | 5.569 |  | valor | 2598 |
| `inss.bpc_por_tipo.idoso` | 2026 (+mes) | 5.558 |  | valor | 88 |
| `inss.bpc_por_tipo.pcd` | 2026 (+mes) | 5.569 |  | valor | 229 |
| `inss.concedidos.beneficios` | 2012–2026 | 5.569 |  | valor | 305 |
| `inss.concedidos.meses` | 2012–2026 | 5.569 |  | valor | 12 |
| `inss.concedidos.valor` | 2012–2026 | 5.569 |  | valor | 352.774,11 |
| `inss.por_1000hab.ano_populacao` | 2026 (+mes) | 5.569 |  | valor | 2025 |
| `inss.por_1000hab.brasil` | 2026 (+mes) | 5.569 |  | valor | 188,829 |
| `inss.por_1000hab.municipio` | 2026 (+mes) | 5.569 |  | valor | 235,05 |
| `inss.por_1000hab.uf` | 2026 (+mes) | 5.569 |  | valor | 196,634 |
| `inss.por_categoria.n` | 2026 (+mes) | 5.569 | k | valor | 65 |
| `inss.por_categoria.valor` | 2026 (+mes) | 5.569 | k | valor | 117.974,79 |
| `inss.por_clientela.n` | 2026 (+mes) | 5.569 | k | valor | 1111 |
| `inss.por_faixa_etaria.n` | 2026 (+mes) | 5.569 | k | valor | 74 |
| `inss.por_sexo.n` | 2026 (+mes) | 5.569 | k | valor | 1288 |
| `inss.serie.beneficios` | 2021–2026 (+mes) | 5.569 |  | valor | 2500,5 |
| `inss.serie.valor_mensal` | 2023–2026 (+mes) | 5.569 |  | valor | 4.060.304,84 |
| `inss.valor_medio` | 2026 (+mes) | 5.569 |  | valor | 1636,956 |
| `inss.valor_mensal` | 2026 (+mes) | 5.569 |  | valor | 4.323.065,28 |
| `programas_cgu.gas_do_povo.pessoas` | 2026 (+mes) | 4.568 |  | valor | 187 |
| `programas_cgu.gas_do_povo.serie_12m.pessoas` | 2025–2026 (+mes) | 4.568 |  | valor | 173 |
| `programas_cgu.gas_do_povo.serie_12m.valor` | 2025–2026 (+mes) | 4.568 |  | valor | 17.934,965 |
| `programas_cgu.gas_do_povo.valor` | 2026 (+mes) | 4.568 |  | valor | 19.587,5 |
| `programas_cgu.pe_de_meia.pessoas` | 2026 (+mes) | 4.567 |  | valor | 25 |
| `programas_cgu.pe_de_meia.serie_12m.pessoas` | 2025–2026 (+mes) | 4.567 |  | valor | 29 |
| `programas_cgu.pe_de_meia.serie_12m.valor` | 2025–2026 (+mes) | 4.567 |  | valor | 47.075 |
| `programas_cgu.pe_de_meia.valor` | 2026 (+mes) | 4.567 |  | valor | 45.600 |
| `programas_cgu.seguro_defeso.pessoas` | 2013–2026 (+mes) | 3.092 |  | valor | 2 |
| `programas_cgu.seguro_defeso.serie_12m.pessoas` | 2013–2026 (+mes) | 3.092 |  | valor | 5 |
| `programas_cgu.seguro_defeso.serie_12m.valor` | 2013–2026 (+mes) | 3.092 |  | valor | 9726 |
| `programas_cgu.seguro_defeso.valor` | 2013–2026 (+mes) | 3.092 |  | valor | 4863 |

Metadados da coleta: `cadastro_unico.erro`, `erro`, `inss.disponivel`, `inss.motivo`, `programas_cgu.erro`.

### `comercio_exterior` (8 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `exportacoes.ano_anterior_fob_usd` | 1998–2025 | 2.549 |  | texto | `12004` |
| `exportacoes.top_paises` | 1997–2025 | 2.933 | pais_iso3, valor_fob_usd | pai (sem valor) |  |
| `exportacoes.top_sh4` | 1997–2025 | 2.933 | id_sh4, valor_fob_usd | pai (sem valor) |  |
| `exportacoes.total_fob_usd` | 1997–2025 | 2.933 |  | texto | `271383` |
| `importacoes.ano_anterior_fob_usd` | 1998–2025 | 2.277 |  | texto | `35260` |
| `importacoes.top_paises` | 1997–2025 | 2.735 | pais_iso3, valor_fob_usd | pai (sem valor) |  |
| `importacoes.top_sh4` | 1997–2025 | 2.735 | id_sh4, valor_fob_usd | pai (sem valor) |  |
| `importacoes.total_fob_usd` | 1997–2025 | 2.735 |  | texto | `39012` |

### `conectividade` (7 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `banda_larga.densidade_100hab` | 2025 (+mes) | 5.570 |  | valor | 16,374 |
| `banda_larga.densidade_brasil` | 2025 (+mes) | 5.570 |  | valor | 25,809 |
| `ibc.cobertura_pop_4g5g` | 2024 | 5.570 |  | valor | 82,677 |
| `ibc.fibra` | 2024 | 5.570 |  | texto | `100` |
| `ibc.ibc` | 2024 | 5.570 |  | valor | 52,885 |
| `ibc.media_brasil` | 2024 | 5.570 |  | valor | 52,399 |

Metadados da coleta: `erro`.

### `demografia` (21 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `censo_2022.area_km2` | — | 5.570 |  | valor | 418 |
| `censo_2022.domicilios` | — | 5.570 |  | valor | 3883,5 |
| `censo_2022.idade_mediana` | — | 5.570 |  | valor | 36 |
| `censo_2022.indice_envelhecimento` | — | 5.570 |  | valor | 61,365 |
| `censo_2022.populacao` | — | 5.570 |  | valor | 11.021 |
| `censo_2022.razao_sexo` | — | 5.570 |  | valor | 99,575 |
| `censo_2022.taxa_alfabetizacao` | — | 5.570 |  | valor | 0,906 |
| `censo_extra.alfabetizacao_por_raca` | — | 1.119 | cor_raca | pai (sem valor) |  |
| `censo_extra.alfabetizacao_por_raca.alfabetizadas` | — | 5.570 | cor_raca | valor | 623 |
| `censo_extra.alfabetizacao_por_raca.taxa` | — | 5.570 | cor_raca | valor | 90 |
| `censo_extra.alfabetizacao_por_raca.total` | — | 5.570 | cor_raca | valor | 732 |
| `censo_extra.cor_raca` | 2010–2022 | 1.648 | cor_raca | pai (sem valor) |  |
| `censo_extra.cor_raca.populacao` | 2010–2022 | 5.570 | cor_raca | valor | 817 |
| `censo_extra.religiao.grupos` | — | 5.216 | religiao | pai (sem valor) |  |
| `censo_extra.religiao.grupos.pct` | — | 5.570 | religiao | valor | 2,229 |
| `censo_extra.religiao.grupos.populacao` | — | 5.570 | religiao | valor | 272 |
| `censo_extra.religiao.total_10_anos_ou_mais` | — | 5.570 |  | valor | 9618,5 |
| `nomes.top.pessoas` | — | 5.565 | nome | valor | 108 |
| `piramide_etaria_2022.homens` | — | 5.571 | grupos | valor | 398 |
| `piramide_etaria_2022.mulheres` | — | 5.571 | grupos | valor | 400 |
| `populacao_serie.populacao` | 1991–2025 | 5.570 |  | valor | 11.068,5 |

### `economia` (66 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `bancario.agencias` | 1988–2023 (+mes) | 4.168 |  | valor | 1 |
| `bancario.depositos_totais` | 1988–2023 (+mes) | 4.078 |  | valor | 125.970.020,5 |
| `bancario.operacoes_credito` | 1988–2023 (+mes) | 4.078 |  | valor | 77.541.343,5 |
| `bancario.verbetes.credito` | 1988–2023 (+mes) | 4.168 |  | texto | `160` |
| `bancario.verbetes.depositos` | 1988–2023 (+mes) | 4.168 | i | texto | `432` |
| `bndes.administracao_publica.desembolsado` | 1995–2026 | 1.653 | ente, programa, projeto | valor | 500.000 |
| `bndes.administracao_publica.valor` | 1995–2026 | 1.653 | ente, programa, projeto, situacao | valor | 546.217,5 |
| `bndes.nao_automaticas.desembolsado` | — | 1.141 | contratacao, cliente, projeto | valor | 8.151.085,985 |
| `bndes.nao_automaticas.valor` | — | 1.141 | contratacao, cliente, projeto, produto, situacao | valor | 10.827.800 |
| `bndes.porte_5a.desembolsado` | — | 4.563 | porte | valor | 1.643.000 |
| `bndes.porte_5a.operacoes` | — | 4.622 | porte | valor | 5 |
| `bndes.serie_indiretas.desembolsado` | 2002–2026 | 5.454 |  | valor | 703.648 |
| `bndes.serie_indiretas.operacoes` | 2002–2026 | 5.456 |  | valor | 4 |
| `bndes.setor_5a` | — | 274 | setor | pai (sem valor) |  |
| `bndes.setor_5a.desembolsado` | — | 4.563 | setor | valor | 1.846.182,5 |
| `combustiveis.janela_dias` | — | 416 |  | valor | 60 |
| `combustiveis.produtos.postos` | — | 416 | produto, ultima_coleta | valor | 8 |
| `combustiveis.produtos.preco_brasil` | — | 416 | produto, ultima_coleta | valor | 6,697 |
| `combustiveis.produtos.preco_municipio` | — | 416 | produto, ultima_coleta | valor | 6,725 |
| `combustiveis.produtos.preco_uf` | — | 416 | produto, ultima_coleta | valor | 6,684 |
| `financas_publicas.despesas_funcao.valor` | 2022–2025 | 5.569 | funcao | valor | 2.613.268,71 |
| `financas_publicas.despesas_total_empenhado` | 2022–2025 | 5.569 |  | valor | 82.380.705,65 |
| `financas_publicas.receitas.fpm` | 2022–2025 | 5.564 |  | valor | 26.973.873,45 |
| `financas_publicas.receitas.fundeb` | 2022–2025 | 5.530 |  | valor | 12.070.128,46 |
| `financas_publicas.receitas.icms` | 2022–2025 | 5.561 |  | valor | 11.865.510,57 |
| `financas_publicas.receitas.impostos` | 2022–2025 | 5.567 |  | valor | 5.169.853,17 |
| `financas_publicas.receitas.iptu` | 2022–2025 | 5.462 |  | valor | 403.005,795 |
| `financas_publicas.receitas.iss` | 2022–2025 | 5.548 |  | valor | 1.786.456,365 |
| `financas_publicas.receitas.receitas_capital` | 2022–2025 | 5.402 |  | valor | 4.166.381,285 |
| `financas_publicas.receitas.receitas_correntes` | 2022–2025 | 5.569 |  | valor | 86.786.880,48 |
| `financas_publicas.receitas.sus` | 2022–2025 | 5.563 |  | valor | 6.876.515,43 |
| `financas_publicas.receitas.total` | 2022–2025 | 5.569 |  | valor | 93.100.454,3 |
| `inpc_brasil.variacao_anual` | 2026 (+mes) | 5.571 |  | valor | 0,95 |
| `inpc_brasil.variacao_doze_meses` | 2026 (+mes) | 5.571 |  | valor | 3,36 |
| `inpc_brasil.variacao_mensal` | 2026 (+mes) | 5.571 |  | valor | 0,56 |
| `mineracao_cfem.serie.pagadores` | 2002–2026 | 3.967 |  | valor | 2 |
| `mineracao_cfem.serie.valor` | 2002–2026 | 3.967 |  | valor | 14.313,81 |
| `mineracao_cfem.substancias.valor` | 2003–2026 | 3.967 | substancia | valor | 6377,635 |
| `mineracao_cfem.valor_ano` | 2003–2026 | 3.967 |  | valor | 9543,69 |
| `pib.pib_per_capita.brasil` | 2023 | 5.570 |  | valor | 53.887,223 |
| `pib.pib_per_capita.uf` | 2023 | 5.570 |  | valor | 47.321,23 |
| `pib.pib_per_capita.valor` | 2023 | 5.570 |  | valor | 29.894,604 |
| `pib.ranking_uf.posicao` | 2023 | 5.570 |  | valor | 137 |
| `pib.ranking_uf.total` | 2023 | 5.570 |  | valor | 399 |
| `pib.serie.impostos_liquidos` | 2012–2021 | 5.570 |  | valor | 9.054.000 |
| `pib.serie.pib` | 2012–2023 | 5.570 |  | valor | 184.770.000 |
| `pib.serie.va` | 2012–2021 | 5.570 |  | valor | 159.004.000 |
| `pib.serie.va_adespss` | 2012–2021 | 5.570 |  | valor | 47.219.000 |
| `pib.serie.va_agropecuaria` | 2012–2021 | 5.570 |  | valor | 25.611.000 |
| `pib.serie.va_industria` | 2012–2021 | 5.570 |  | valor | 11.961.000 |
| `pib.serie.va_servicos` | 2012–2021 | 5.570 |  | valor | 46.516.000 |
| `pix.pagadores_pf` | 2026 (+mes) | 5.571 |  | valor | 6688 |
| `pix.pagadores_pf_por_hab` | 2026 (+mes) | 5.570 |  | valor | 0,605 |
| `pix.pagadores_pj` | 2026 (+mes) | 5.571 |  | valor | 357 |
| `pix.serie.pago` | 2023–2026 (+mes) | 5.571 |  | valor | 46.365.525,36 |
| `pix.serie.recebido` | 2023–2026 (+mes) | 5.571 |  | valor | 45.175.791,115 |
| `pix.transacoes_pagas` | 2026 (+mes) | 5.571 |  | valor | 261.261 |
| `pix.transacoes_recebidas` | 2026 (+mes) | 5.571 |  | valor | 187.541 |
| `pix.valor_pago` | 2026 (+mes) | 5.571 |  | valor | 63.631.005,1 |
| `pix.valor_recebido` | 2026 (+mes) | 5.571 |  | valor | 61.409.917,14 |

Metadados da coleta: `bancario.erro`, `combustiveis.erro`, `financas_publicas.erro`, `mineracao_cfem.disponivel`, `mineracao_cfem.motivo`, `pib.erro`.

### `educacao` (110 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `alfabetizacao.media_municipios_uf` | 2023–2024 | 5.547 |  | valor | 64,781 |
| `alfabetizacao.metas.meta_alfabetizacao_2024` | 2023–2024 | 5.232 | id_municipio, rede | valor | 64,095 |
| `alfabetizacao.metas.meta_alfabetizacao_2025` | 2023–2024 | 5.352 | id_municipio, rede | valor | 66,94 |
| `alfabetizacao.metas.meta_alfabetizacao_2026` | 2023–2024 | 5.352 | id_municipio, rede | valor | 69,875 |
| `alfabetizacao.metas.meta_alfabetizacao_2027` | 2023–2024 | 5.352 | id_municipio, rede | valor | 72,665 |
| `alfabetizacao.metas.meta_alfabetizacao_2028` | 2023–2024 | 5.352 | id_municipio, rede | valor | 75,285 |
| `alfabetizacao.metas.meta_alfabetizacao_2029` | 2023–2024 | 5.352 | id_municipio, rede | valor | 77,73 |
| `alfabetizacao.metas.meta_alfabetizacao_2030` | 2023–2024 | 5.352 | id_municipio, rede | valor | 80 |
| `alfabetizacao.metas.nivel_alfabetizacao` | 2023–2024 | 5.352 | id_municipio, rede | valor | 3 |
| `alfabetizacao.metas.percentual_participacao` | 2023–2024 | 5.352 | id_municipio, rede | valor | 91,205 |
| `alfabetizacao.metas.taxa_alfabetizacao` | 2023–2024 | 5.352 | id_municipio, rede | valor | 62,445 |
| `alfabetizacao.serie.taxa_alfabetizacao` | 2023–2024 | 5.547 |  | valor | 62,74 |
| `alfabetizacao.taxa` | 2023–2024 | 5.547 |  | valor | 64,28 |
| `censo_escolar.com_biblioteca` | 2025 | 5.571 |  | valor | 4 |
| `censo_escolar.com_esgoto_rede` | 2025 | 5.571 |  | valor | 5 |
| `censo_escolar.com_internet` | 2025 | 5.571 |  | valor | 13 |
| `censo_escolar.com_laboratorio` | 2025 | 5.571 |  | valor | 3 |
| `censo_escolar.com_quadra` | 2025 | 5.571 |  | valor | 4 |
| `censo_escolar.com_rampa_acessibilidade` | 2025 | 5.571 |  | valor | 9 |
| `censo_escolar.docentes` | 2025 | 5.571 |  | valor | 184 |
| `censo_escolar.escolas` | 2025 | 5.571 |  | valor | 14 |
| `censo_escolar.escolas_rurais` | 2025 | 5.571 |  | valor | 4 |
| `censo_escolar.matriculas` | 2025 | 5.571 |  | valor | 2494 |
| `censo_escolar.matriculas_eja` | 2025 | 5.571 |  | valor | 93 |
| `censo_escolar.matriculas_especial` | 2025 | 5.571 |  | valor | 142 |
| `censo_escolar.matriculas_fundamental` | 2025 | 5.571 |  | valor | 1399 |
| `censo_escolar.matriculas_infantil` | 2025 | 5.571 |  | valor | 527 |
| `censo_escolar.matriculas_medio` | 2025 | 5.571 |  | valor | 365 |
| `censo_escolar.matriculas_transporte` | 2025 | 5.571 |  | valor | 746 |
| `censo_escolar.por_rede.docentes` | 2025 | 5.571 | rede | valor | 60 |
| `censo_escolar.por_rede.escolas` | 2025 | 5.571 | rede | valor | 4 |
| `censo_escolar.por_rede.matriculas` | 2025 | 5.571 | rede | valor | 800 |
| `censo_escolar.serie.escolas` | 2016–2025 | 5.571 |  | valor | 14 |
| `censo_escolar.serie.matriculas` | 2016–2025 | 5.571 |  | valor | 2627 |
| `censo_escolar.turmas` | 2025 | 5.571 |  | valor | 138 |
| `cnpq.por_instituicao.processos` | 2004–2022 | 617 | instituicao | valor | 5 |
| `cnpq.por_modalidade.processos` | 2004–2022 | 617 | modalidade | valor | 6 |
| `cnpq.serie.processos` | 2002–2022 | 617 |  | valor | 15 |
| `cnpq.serie.valor` | 2002–2022 | 617 |  | valor | 131.558,04 |
| `conectada.adequadas` | 2023 | 5.570 |  | valor | 1 |
| `conectada.com_internet` | 2023 | 5.570 |  | valor | 11 |
| `conectada.download_mediano` | 2023 | 5.469 |  | valor | 71,328 |
| `conectada.escolas` | 2023 | 5.570 |  | valor | 12 |
| `conectada.internet_aprendizagem` | 2023 | 5.570 |  | valor | 7 |
| `conectada.laboratorio` | 2023 | 5.570 |  | valor | 3 |
| `conectada.medidas` | 2023 | 5.570 |  | valor | 7 |
| `conectada.por_faixa.escolas` | 2023 | 5.570 | faixa | valor | 3 |
| `enem.humanas` | 2023 | 1.750 |  | valor | 506,895 |
| `enem.inscritos` | 2023 | 5.571 |  | valor | 0 |
| `enem.linguagens` | 2023 | 1.750 |  | valor | 504,185 |
| `enem.matematica` | 2023 | 1.750 |  | valor | 510,103 |
| `enem.media_geral` | 2023 | 1.750 |  | valor | 522,594 |
| `enem.natureza` | 2023 | 1.750 |  | valor | 480,927 |
| `enem.presentes` | 2023 | 5.571 |  | valor | 0 |
| `enem.redacao` | 2023 | 1.750 |  | valor | 594,749 |
| `especial.por_classe.matriculas` | 2024 | 5.570 | classe | valor | 44 |
| `especial.por_tipo.matriculas` | 2024 | 5.570 | tipo | valor | 3 |
| `ideb.finais.ideb` | 2005–2025 | 5.568 |  | valor | 4,3 |
| `ideb.finais.meta` | 2007–2019 | 5.564 |  | valor | 4,1 |
| `ideb.finais.taxa_aprovacao` | 2005–2025 | 5.569 |  | valor | 88,4 |
| `ideb.iniciais.ideb` | 2005–2025 | 5.560 |  | valor | 5,2 |
| `ideb.iniciais.meta` | 2007–2019 | 5.549 |  | valor | 4,7 |
| `ideb.iniciais.taxa_aprovacao` | 2005–2025 | 5.568 |  | valor | 94,8 |
| `ideb.referencia_brasil.finais` | — | 5.571 |  | valor | 5 |
| `ideb.referencia_brasil.iniciais` | — | 5.571 |  | valor | 6,1 |
| `ideb.referencia_uf.finais` | — | 5.571 |  | valor | 5,2 |
| `ideb.referencia_uf.iniciais` | — | 5.571 |  | valor | 6,3 |
| `inse.alunos` | 2019–2021 | 5.569 |  | valor | 313 |
| `inse.inse` | 2019–2021 | 5.569 |  | valor | 4,91 |
| `inse.media_municipios_br` | 2019–2021 | 5.569 |  | valor | 4,859 |
| `inse.media_municipios_uf` | 2019–2021 | 5.569 |  | valor | 4,936 |
| `inse.niveis_pct.nivel` | 2019–2021 | 5.569 |  | valor | 4,5 |
| `inse.niveis_pct.pct` | 2019–2021 | 5.569 |  | valor | 10,96 |
| `saeb.provas.distribuicao_niveis_pct` | 2021–2023 | 5.562 | disciplina, serie, i | valor | 11,4 |
| `saeb.provas.media` | 2021–2023 | 5.562 | disciplina, serie | valor | 234,87 |
| `sisu.serie.aprovados` | 2017–2022 | 5.567 |  | valor | 45 |
| `sisu.serie.candidatos` | 2017–2022 | 5.567 |  | valor | 80 |
| `sisu.serie.matriculados` | 2017–2022 | 5.567 |  | valor | 3 |
| `sisu.serie.nota_media` | 2017–2022 | 5.567 |  | valor | 545,545 |
| `sisu.top_cursos.matriculados` | 2018–2022 | 4.846 | curso, ies | valor | 1 |
| `sisu.vagas_no_municipio.ampla` | 2021–2022 | 550 |  | valor | 102,5 |
| `sisu.vagas_no_municipio.cotas` | 2021–2022 | 465 |  | valor | 70 |
| `sisu.vagas_no_municipio.total` | 2021–2022 | 551 |  | valor | 163 |
| `superior.concluintes` | 2009–2024 | 3.826 |  | valor | 15 |
| `superior.cursos` | 2009–2024 | 3.826 |  | valor | 49 |
| `superior.cursos_presenciais` | 2009–2024 | 3.826 |  | valor | 0 |
| `superior.ies` | 2009–2024 | 3.826 |  | valor | 3 |
| `superior.ingressantes` | 2009–2024 | 3.826 |  | valor | 82 |
| `superior.matriculas` | 2009–2024 | 3.826 |  | valor | 152 |
| `superior.matriculas_ead` | 2009–2024 | 3.770 |  | valor | 143 |
| `superior.matriculas_presenciais` | 2009–2024 | 1.150 |  | valor | 687 |
| `superior.por_area.matriculas` | 2009–2024 | 3.826 | area | valor | 15 |
| `superior.por_rede.matriculas` | 2009–2024 | 3.826 | rede | valor | 148,5 |
| `superior.serie_matriculas.matriculas` | 2009–2024 | 3.826 |  | valor | 283 |
| `superior.vagas` | 2009–2024 | 3.826 |  | valor | 0 |

Metadados da coleta: `alfabetizacao.disponivel`, `alfabetizacao.motivo`, `cnpq.disponivel`, `cnpq.motivo`, `conectada.disponivel`, `conectada.motivo`, `especial.disponivel`, `especial.motivo`, `indicadores.erro`, `inse.disponivel`, `inse.motivo`, `saeb.erro`, `sisu.erro`, `superior.disponivel`, `superior.motivo`.

### `empresas` (13 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `ativas` | 2026 (+mes) | 5.570 |  | valor | 879 |
| `baixadas` | 2026 (+mes) | 5.570 |  | valor | 1281 |
| `demografia_empresarial.aberturas` | 2016–2026 | 5.570 |  | valor | 116 |
| `demografia_empresarial.baixas` | 2016–2026 | 5.570 |  | valor | 67 |
| `demografia_empresarial.saldo` | 2016–2026 | 5.570 |  | valor | 46 |
| `filiais` | 2026 (+mes) | 5.570 |  | valor | 46 |
| `idade_media_anos` | 2026 (+mes) | 5.570 |  | valor | 8,61 |
| `matrizes` | 2026 (+mes) | 5.570 |  | valor | 823 |
| `mei` | 2026 (+mes) | 5.570 |  | valor | 379 |
| `por_secao_cnae.ativas` | 2026 (+mes) | 5.570 | secao | valor | 73 |
| `registradas` | 2026 (+mes) | 5.570 |  | valor | 2468 |
| `top_atividades.ativas` | 2026 (+mes) | 5.570 | atividade | valor | 30 |

Metadados da coleta: `erro`.

### `geografia` (11 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `arranjo_populacional.nome` | — | 953 |  | texto | `Internacional de Assis Brasil/` |
| `arranjo_populacional.populacao_2010` | — | 953 |  | valor | 23.001 |
| `biomas.pct_area` | — | 5.570 | nome | valor | 97,656 |
| `regiao_metropolitana.nome` | — | 1.384 |  | texto | `RM do Sertão` |
| `regiao_metropolitana.tipo` | — | 1.384 |  | texto | `RM` |
| `sede_municipal.lat` | 2010 | 5.565 |  | valor | -18,09 |
| `sede_municipal.lon` | 2010 | 5.565 |  | valor | -46,516 |
| `semiarido` | — | 5.571 |  | valor | 0 |
| `unidades_conservacao.lista` | — | 1.922 | unidade_conservacao, categoria, esfera | pai (sem valor) |  |
| `unidades_conservacao.por_categoria.quantidade` | — | 1.922 | categoria, esfera | valor | 1 |
| `unidades_conservacao.total` | — | 5.571 |  | valor | 0 |

### `infraestrutura` (85 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `atlas_esgotos.ano_referencia` | — | 5.570 |  | valor | 2013 |
| `atlas_esgotos.indice_atendimento_com_coleta_com_tratamento` | — | 5.570 |  | valor | 0 |
| `atlas_esgotos.indice_atendimento_com_coleta_sem_tratamento` | — | 5.570 |  | valor | 0,02 |
| `atlas_esgotos.indice_atendimento_solucao_individual` | — | 5.570 |  | valor | 0,042 |
| `atlas_esgotos.indice_sem_atendimento_sem_coleta_sem_tratamento` | — | 5.570 |  | valor | 0,428 |
| `atlas_esgotos.investimento_coleta` | — | 5.570 |  | valor | 6.040.904,88 |
| `atlas_esgotos.investimento_coleta_tratatamento` | — | 5.570 |  | valor | 8.184.485,233 |
| `atlas_esgotos.investimento_tratamento` | — | 5.570 |  | valor | 1.879.307,909 |
| `atlas_esgotos.populacao_urbana_2013` | — | 5.570 |  | valor | 6577 |
| `atlas_esgotos.populacao_urbana_2035` | — | 5.570 |  | valor | 8286,5 |
| `atlas_esgotos.prestador_servico_esgotamento_sanitario` | — | 5.570 |  | texto | `Prefeitura Municipal de Acrelâ` |
| `censo_domicilios.agua.categorias.pct` | — | 5.570 | categoria | valor | 19,362 |
| `censo_domicilios.agua.categorias.populacao` | — | 5.570 | categoria | valor | 2106 |
| `censo_domicilios.agua.total` | — | 5.570 |  | valor | 11.021 |
| `censo_domicilios.domicilios_recenseados` | — | 2.631 | especie | pai (sem valor) |  |
| `censo_domicilios.domicilios_recenseados.domicilios` | — | 5.570 | especie | valor | 706 |
| `censo_domicilios.esgotamento.categorias.pct` | — | 5.570 | categoria | valor | 2,574 |
| `censo_domicilios.esgotamento.categorias.populacao` | — | 5.570 | categoria | valor | 365 |
| `censo_domicilios.esgotamento.total` | — | 5.570 |  | valor | 11.021 |
| `censo_domicilios.lixo.categorias.pct` | — | 5.570 | categoria | valor | 1,208 |
| `censo_domicilios.lixo.categorias.populacao` | — | 5.570 | categoria | valor | 185 |
| `censo_domicilios.lixo.total` | — | 5.570 |  | valor | 11.021 |
| `censo_domicilios.tipo_domicilio.categorias.pct` | — | 5.570 | categoria | valor | 0,473 |
| `censo_domicilios.tipo_domicilio.categorias.populacao` | — | 5.570 | categoria | valor | 81 |
| `censo_domicilios.tipo_domicilio.total` | — | 5.570 |  | valor | 11.021 |
| `energia_continuidade.conjuntos` | — | 1.857 | nome, agente | pai (sem valor) |  |
| `energia_continuidade.serie.dec_horas` | 2014–2025 | 1.838 |  | valor | 12,37 |
| `energia_continuidade.serie.fec_vezes` | 2014–2025 | 1.838 |  | valor | 5,95 |
| `energia_continuidade.serie.limite_dec` | 2014–2025 | 1.838 |  | valor | 13 |
| `energia_continuidade.serie.limite_fec` | 2014–2025 | 1.838 |  | valor | 8,771 |
| `energia_continuidade.serie.unidades` | 2014–2025 | 1.838 |  | valor | 22.412,5 |
| `energia_gd.data_base` | — | 5.567 |  | texto | `2026-09-04` |
| `energia_gd.instalacoes` | — | 5.567 |  | valor | 260 |
| `energia_gd.por_ano_cadastro.instalacoes` | 1900–2026 | 5.567 |  | valor | 22 |
| `energia_gd.por_ano_cadastro.kw` | 1900–2026 | 5.567 |  | valor | 245,08 |
| `energia_gd.por_classe.instalacoes` | — | 5.567 | classe | valor | 19 |
| `energia_gd.por_classe.kw` | — | 5.567 | classe | valor | 355,38 |
| `energia_gd.por_fonte.instalacoes` | — | 5.567 | fonte | valor | 207 |
| `energia_gd.por_fonte.kw` | — | 5.567 | fonte | valor | 2502,14 |
| `energia_gd.potencia_mw` | — | 5.567 |  | valor | 3,175 |
| `energia_gd.ucs_recebem_credito` | — | 5.567 |  | valor | 422 |
| `energia_gd.w_por_habitante` | — | 5.566 |  | valor | 269,607 |
| `frota.por_tipo.quantidade` | 2026 (+mes) | 5.571 | tipo | valor | 74 |
| `frota.serie.total` | 2013–2026 | 5.571 |  | valor | 3891 |
| `frota.total` | 2026 (+mes) | 5.571 |  | valor | 5220 |
| `frota.veiculos_1000hab.ano_populacao` | 2026 (+mes) | 5.571 |  | valor | 2025 |
| `frota.veiculos_1000hab.brasil` | 2026 (+mes) | 5.571 |  | valor | 622,388 |
| `frota.veiculos_1000hab.municipio` | 2026 (+mes) | 5.570 |  | valor | 567,212 |
| `frota.veiculos_1000hab.uf` | 2026 (+mes) | 5.571 |  | valor | 696,069 |
| `obras_cno.data_extracao` | — | 5.568 |  | texto | `2025-07-28` |
| `obras_cno.iniciadas_por_ano.area_m2` | 2016–2025 | 5.564 |  | valor | 7463,5 |
| `obras_cno.iniciadas_por_ano.obras` | 2016–2025 | 5.564 |  | valor | 9 |
| `obras_cno.obras` | — | 5.568 |  | valor | 94 |
| `obras_cno.por_situacao.obras` | — | 5.568 | situacao | valor | 12 |
| `outorgas_agua.maiores` | — | 1.235 | responsavel | pai (sem valor) |  |
| `outorgas_agua.maiores.vazao` | — | 4.610 | responsavel | valor | 37,64 |
| `outorgas_agua.outorgas` | — | 4.796 |  | valor | 13 |
| `outorgas_agua.por_esfera.outorgas` | — | 4.796 | esfera | valor | 9 |
| `outorgas_agua.por_esfera.vazao` | — | 4.610 | esfera | valor | 290,701 |
| `outorgas_agua.vazao_total` | — | 4.796 |  | valor | 286,673 |
| `snis.ano_anterior.a` | 2007–2021 | 5.353 |  | valor | 75,66 |
| `snis.ano_anterior.c` | 2007–2021 | 2.800 |  | valor | 72,03 |
| `snis.ano_anterior.t` | 2007–2021 | 2.798 |  | valor | 100 |
| `snis.despesa_total_servico` | 2000–2022 | 5.538 |  | valor | 2.193.409,62 |
| `snis.extensao_rede_agua` | 2000–2022 | 5.541 |  | valor | 47,91 |
| `snis.extensao_rede_esgoto` | 2006–2022 | 3.101 |  | valor | 32 |
| `snis.indice_atendimento_esgoto_esgoto` | 2008–2021 | 44 |  | valor | 81,45 |
| `snis.indice_atendimento_total_agua` | 2001–2022 | 5.540 |  | valor | 76,45 |
| `snis.indice_atendimento_urbano_agua` | 2000–2021 | 117 |  | valor | 99,8 |
| `snis.indice_coleta_esgoto` | 2008–2022 | 2.936 |  | valor | 71,485 |
| `snis.indice_perda_distribuicao_agua` | 2001–2022 | 5.516 |  | valor | 29,88 |
| `snis.indice_tratamento_esgoto` | 2008–2022 | 2.939 |  | valor | 100 |
| `snis.populacao_atendida_agua` | 2000–2022 | 5.542 |  | valor | 7045 |
| `snis.populacao_atentida_esgoto` | 2008–2022 | 2.944 |  | valor | 6641,5 |
| `snis.volume_agua_consumido` | 2001–2022 | 5.537 |  | valor | 365 |
| `snis.volume_esgoto_coletado` | 2006–2022 | 3.100 |  | valor | 329,25 |
| `snis.volume_esgoto_tratado` | 2006–2022 | 3.101 |  | valor | 142,36 |

Metadados da coleta: `atlas_esgotos.erro`, `energia_continuidade.erro`, `energia_gd.erro`, `obras_cno.disponivel`, `obras_cno.motivo`, `outorgas_agua.disponivel`, `outorgas_agua.motivo`, `snis.erro`.

### `meio_ambiente` (47 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `car.area_ha` | — | 5.563 |  | valor | 35.486,032 |
| `car.camadas_ha.app` | — | 5.561 |  | valor | 5468,847 |
| `car.camadas_ha.area_consolidada` | — | 5.355 |  | valor | 17.586,571 |
| `car.camadas_ha.reserva_legal` | — | 5.560 |  | valor | 5711,305 |
| `car.camadas_ha.uso_restrito` | — | 4.153 |  | valor | 58,841 |
| `car.camadas_ha.vegetacao_nativa` | — | 5.558 |  | valor | 7002,839 |
| `car.data_extracao` | — | 5.564 |  | texto | `2025-10-15` |
| `car.imoveis` | — | 5.564 |  | valor | 985 |
| `car.pendentes` | — | 5.564 |  | valor | 10 |
| `car.por_condicao.imoveis` | — | 5.563 | condicao | valor | 53 |
| `car.por_tipo.area_ha` | — | 5.563 | tipo | valor | 21.277,774 |
| `car.por_tipo.imoveis` | — | 5.563 | tipo | valor | 526 |
| `car.suspensos` | — | 5.564 |  | valor | 0 |
| `desastres.data_extracao` | — | 5.571 |  | texto | `2026-10-09` |
| `desastres.municipios_uf_com_reconhecimento` | — | 5.571 |  | valor | 59 |
| `desastres.vigentes` | — | 1.091 | desastre, situacao, ocorrencia, vigencia | pai (sem valor) |  |
| `estacoes_inmet.estacoes` | — | 1 | id_estacao, estacao, fundacao | pai (sem valor) |  |
| `estacoes_inmet.estacoes.altitude` | — | 607 | id_estacao, estacao, fundacao | valor | 335,68 |
| `ibama.autos_total` | — | 5.571 |  | valor | 32 |
| `ibama.embargos` | — | 5.571 |  | valor | 3 |
| `ibama.embargos_5a` | — | 5.571 |  | valor | 0 |
| `ibama.serie.autos` | 1981–2026 | 5.462 |  | valor | 2 |
| `ibama.serie.valor` | 1981–2026 | 5.461 |  | valor | 11.500 |
| `ibama.tipos_10a.autos` | — | 4.296 | tipo | valor | 2 |
| `ibama.valor_total` | — | 5.571 |  | valor | 403.813 |
| `mapbiomas.anos` | — | 5.571 | i | valor | 2015 |
| `mapbiomas.transicoes.area_2010` | — | 5.566 | de, para | valor | 6,843 |
| `mapbiomas.transicoes.area_2020` | — | 5.566 | de, para | valor | 4,827 |
| `prodes.biomas.area_total` | 2022–2023 | 5.570 | bioma | valor | 336,272 |
| `prodes.biomas.desmatado` | 2022–2023 | 5.570 | bioma | valor | 210,1 |
| `prodes.biomas.vegetacao_natural` | 2022–2023 | 5.570 | bioma | valor | 76,2 |
| `prodes.serie.area_total` | 2000–2023 | 5.570 | bioma | valor | 401,291 |
| `prodes.serie.desmatado` | 2000–2023 | 5.570 | bioma | valor | 225,6 |
| `prodes.serie.vegetacao_natural` | 2000–2023 | 5.570 | bioma | valor | 105,6 |
| `queimadas.serie.focos` | 2003–2026 | 5.568 |  | valor | 12 |
| `queimadas.serie.frp_max` | 2023–2026 | 5.565 |  | valor | 98,4 |
| `queimadas.serie.frp_medio` | 2023–2026 | 5.565 |  | valor | 11,522 |
| `seeg.gas` | 2024 | 5.570 |  | texto | `CO2e (t) GWP` |
| `seeg.por_setor.emissao_tco2e` | 2024 | 5.570 | setor | valor | 7614,415 |
| `seeg.tipo` | 2024 | 5.570 |  | texto | `Emissão` |
| `seeg.total_tco2e` | 2024 | 5.570 |  | valor | 113.347,521 |
| `sisam.serie.co_ppb` | 2000–2018 | 5.570 |  | valor | 123,912 |
| `sisam.serie.pm25_ugm3` | 2000–2019 | 5.570 |  | valor | 9,87 |

Metadados da coleta: `car.disponivel`, `car.motivo`, `prodes.erro`, `seeg.erro`.

### `municipio` (19 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `amazonia_legal` | — | 5.571 |  | valor | 0 |
| `area_km2` | — | 5.570 |  | valor | 418 |
| `capital_uf` | — | 5.570 |  | valor | 0 |
| `ddd` | — | 5.570 |  | texto | `68` |
| `id_comarca` | — | 5.570 |  | texto | `1200013` |
| `id_municipio` | — | 5.571 |  | texto | `1200013` |
| `id_municipio_bcb` | — | 5.570 |  | texto | `41849` |
| `id_municipio_rf` | — | 5.570 |  | texto | `643` |
| `id_municipio_tse` | — | 5.570 |  | texto | `1120` |
| `mesorregiao` | — | 5.570 |  | texto | `Vale do Acre` |
| `microrregiao` | — | 5.570 |  | texto | `Rio Branco` |
| `nome` | — | 5.571 |  | texto | `Acrelândia` |
| `nome_uf` | — | 5.571 |  | texto | `Acre` |
| `regiao` | — | 5.571 |  | texto | `Norte` |
| `regiao_imediata` | — | 5.571 |  | texto | `Rio Branco` |
| `regiao_intermediaria` | — | 5.571 |  | texto | `Rio Branco` |
| `regiao_metropolitana` | — | 1.432 |  | texto | `Região Metropolitana do Agrest` |
| `regiao_saude` | — | 5.570 |  | texto | `Baixo Acre e Purus` |
| `sigla_uf` | — | 5.571 |  | texto | `AC` |

### `politica` (56 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `ano_prefeito` | 2026 | 5.570 |  | valor | 2024 |
| `camara_municipal.bancadas.cadeiras` | 2020–2024 | 5.568 | partido | valor | 2 |
| `camara_municipal.bancadas.votos` | 2020–2024 | 5.568 | partido | valor | 755 |
| `camara_municipal.cadeiras_total` | 2020–2024 | 5.568 |  | valor | 9 |
| `camara_municipal.financiamento.candidatos` | 2020–2024 | 5.568 | cargo | valor | 10 |
| `camara_municipal.financiamento.receita` | 2020–2024 | 5.568 | cargo | valor | 213.002,435 |
| `camara_municipal.perfil_candidatos.brancos` | 2020–2024 | 5.568 |  | valor | 27 |
| `camara_municipal.perfil_candidatos.candidatos` | 2020–2024 | 5.568 |  | valor | 60 |
| `camara_municipal.perfil_candidatos.feminino` | 2020–2024 | 5.568 |  | valor | 20 |
| `camara_municipal.perfil_candidatos.idade_media` | 2020–2024 | 5.568 |  | valor | 47,114 |
| `camara_municipal.perfil_candidatos.masculino` | 2020–2024 | 5.568 |  | valor | 39 |
| `camara_municipal.perfil_candidatos.negros` | 2020–2024 | 5.568 |  | valor | 30 |
| `deputados_nascidos.deputados` | 2026 | 1.427 | nome, nascimento, falecido | pai (sem valor) |  |
| `deputados_nascidos.total` | 2026 | 5.571 |  | valor | 0 |
| `eleitorado.aptos` | 2026 | 5.570 |  | valor | 9311 |
| `eleitorado.biometria` | 2026 | 5.570 |  | valor | 8498 |
| `eleitorado.zonas` | 2026 | 5.570 |  | valor | 1 |
| `filiados.data_extracao` | 2026 | 5.570 |  | texto | `2026-08-04` |
| `filiados.filiados` | 2026 | 5.570 |  | valor | 1330 |
| `filiados.por_partido.filiados` | 2026 | 5.570 | partido | valor | 46 |
| `filiados.por_sexo.filiados` | 2026 | 5.570 | sexo | valor | 643 |
| `financas_campanha.despesas_por_cargo.valor` | 2024–2026 | 5.569 | cargo | valor | 184.611,5 |
| `financas_campanha.despesas_por_tipo.valor` | 2024–2026 | 5.569 |  | valor | 370.457,87 |
| `financas_campanha.receitas_por_cargo.candidatos` | 2024–2026 | 5.569 | cargo | valor | 10 |
| `financas_campanha.receitas_por_cargo.valor` | 2024–2026 | 5.569 | cargo | valor | 214.493,15 |
| `financas_campanha.receitas_por_origem.valor` | 2024–2026 | 5.569 | origem | valor | 39.830,605 |
| `genero.0` | 2026 | 949 |  | valor | 3 |
| `genero.2` | 2026 | 5.570 |  | valor | 4589 |
| `genero.4` | 2026 | 5.570 |  | valor | 4716 |
| `instrucao.0` | 2026 | 898 |  | valor | 3 |
| `instrucao.1` | 2026 | 5.570 |  | valor | 480 |
| `instrucao.2` | 2026 | 5.570 |  | valor | 830 |
| `instrucao.3` | 2026 | 5.570 |  | valor | 2524 |
| `instrucao.4` | 2026 | 5.570 |  | valor | 500,5 |
| `instrucao.5` | 2026 | 5.570 |  | valor | 1689,5 |
| `instrucao.6` | 2026 | 5.570 |  | valor | 2011,5 |
| `instrucao.7` | 2026 | 5.570 |  | valor | 275 |
| `instrucao.8` | 2026 | 5.570 |  | valor | 558 |
| `prefeito.abstencoes` | 2024 | 5.568 |  | valor | 1507 |
| `prefeito.aptos` | 2024 | 5.568 |  | valor | 9414 |
| `prefeito.comparecimento` | 2024 | 5.568 |  | valor | 7817,5 |
| `prefeito.eleito.nome_urna` | 2024 | 5.515 |  | texto | `Olavinho Boiadeiro` |
| `prefeito.eleito.partido` | 2024 | 5.518 |  | texto | `REPUBLICANOS` |
| `prefeito.eleito.turno` | 2024 | 5.518 |  | valor | 1 |
| `prefeito.eleito.votos` | 2024 | 5.518 |  | valor | 4386 |
| `prefeito.secoes` | 2024 | 5.568 |  | valor | 31 |
| `prefeito.turno` | 2024 | 5.568 |  | valor | 1 |
| `prefeito.votos_brancos` | 2024 | 5.568 |  | valor | 104 |
| `prefeito.votos_nominais` | 2024 | 5.568 |  | valor | 7342,5 |
| `prefeito.votos_nulos` | 2024 | 5.568 |  | valor | 223 |

Metadados da coleta: `camara_municipal.erro`, `erro`, `filiados.disponivel`, `filiados.motivo`, `financas_campanha.disponivel`, `financas_campanha.motivo`.

### `saude` (157 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `atencao_basica.cobertura_ab` | — | 5.570 |  | valor | 100 |
| `atencao_basica.cobertura_esf` | — | 5.570 |  | valor | 100 |
| `atencao_basica.equipes` | — | 5.570 |  | valor | 4 |
| `atencao_basica.referencia` | — | 5.570 |  | texto | `2020-12` |
| `atencao_basica.serie.cobertura_ab` | 2007–2020 (+mes) | 5.570 |  | valor | 100 |
| `atencao_basica.serie.cobertura_esf` | 2007–2020 (+mes) | 5.570 |  | valor | 100 |
| `atencao_basica.serie.equipes` | 2007–2020 (+mes) | 5.570 |  | valor | 4 |
| `cnes.agentes.ace` | 2024–2025 (+mes) | 5.570 |  | valor | 7 |
| `cnes.agentes.acs` | 2024–2025 (+mes) | 5.570 |  | valor | 24 |
| `cnes.equipes.por_tipo.n` | 2026 (+mes) | 5.569 | tipo | valor | 2 |
| `cnes.equipes.total` | 2026 (+mes) | 5.570 |  | valor | 11 |
| `cnes.estabelecimentos` | 2025 (+mes) | 5.570 |  | valor | 18 |
| `cnes.leitos.sus` | 2005–2026 (+mes) | 4.040 |  | valor | 29 |
| `cnes.leitos.total` | 2005–2026 (+mes) | 4.040 |  | valor | 32 |
| `cnes.profissionais.vinculos` | 2024–2025 (+mes) | 5.570 |  | valor | 205 |
| `cnes.unidades.caps` | 2025 (+mes) | 5.570 |  | valor | 0 |
| `cnes.unidades.samu` | 2025 (+mes) | 5.570 |  | valor | 0 |
| `cnes.unidades.ubs` | 2025 (+mes) | 5.570 |  | valor | 6 |
| `cnes.unidades.upa` | 2025 (+mes) | 5.570 |  | valor | 0 |
| `dengue.classificacao_bruta.10\|1` | 2021–2026 | 4.150 |  | valor | 15 |
| `dengue.classificacao_bruta.10\|2` | 2024–2025 | 144 |  | valor | 2 |
| `dengue.classificacao_bruta.10\|3` | 2024–2025 | 119 |  | valor | 2 |
| `dengue.classificacao_bruta.10\|4` | 2024–2026 | 77 |  | valor | 1 |
| `dengue.classificacao_bruta.10\|9` | 2023–2026 | 848 |  | valor | 2 |
| `dengue.classificacao_bruta.10\|None` | 2022–2026 | 1.995 |  | valor | 4 |
| `dengue.classificacao_bruta.11\|1` | 2022–2026 | 1.076 |  | valor | 3 |
| `dengue.classificacao_bruta.11\|2` | 2024–2025 | 87 |  | valor | 2 |
| `dengue.classificacao_bruta.11\|3` | 2025 | 32 |  | valor | 2 |
| `dengue.classificacao_bruta.11\|4` | 2025 | 44 |  | valor | 1 |
| `dengue.classificacao_bruta.11\|9` | 2024–2026 | 167 |  | valor | 2 |
| `dengue.classificacao_bruta.11\|None` | 2024–2026 | 482 |  | valor | 2 |
| `dengue.classificacao_bruta.12\|1` | 2024–2026 | 237 |  | valor | 2 |
| `dengue.classificacao_bruta.12\|2` | 2023–2025 | 235 |  | valor | 2 |
| `dengue.classificacao_bruta.12\|3` | 2024–2025 | 25 |  | valor | 2 |
| `dengue.classificacao_bruta.12\|4` | 2022–2025 | 51 |  | valor | 1 |
| `dengue.classificacao_bruta.12\|9` | 2025 | 27 |  | valor | 2 |
| `dengue.classificacao_bruta.12\|None` | 2022–2025 | 90 |  | valor | 2 |
| `dengue.classificacao_bruta.5 \|1` | 2015–2019 | 3 |  | valor | 1 |
| `dengue.classificacao_bruta.5 \|None` | 2019 | 1 |  | valor | 1 |
| `dengue.classificacao_bruta.5\|1` | 2005–2011 | 2 |  | valor | 1 |
| `dengue.classificacao_bruta.8 \|1` | 2023–2025 | 458 |  | valor | 2 |
| `dengue.classificacao_bruta.8 \|2` | 2025 | 2 |  | valor | 1,5 |
| `dengue.classificacao_bruta.8 \|3` | 2025 | 7 |  | valor | 1 |
| `dengue.classificacao_bruta.8 \|4` | 2025 | 38 |  | valor | 1 |
| `dengue.classificacao_bruta.8 \|9` | 2024–2025 | 148 |  | valor | 2 |
| `dengue.classificacao_bruta.8 \|None` | 2017–2025 | 3.619 |  | valor | 7 |
| `dengue.classificacao_bruta.None\|1` | 2025–2026 | 92 |  | valor | 1 |
| `dengue.classificacao_bruta.None\|3` | 2025–2026 | 4 |  | valor | 1 |
| `dengue.classificacao_bruta.None\|4` | 2025 | 42 |  | valor | 1 |
| `dengue.classificacao_bruta.None\|9` | 2025–2026 | 59 |  | valor | 1 |
| `dengue.classificacao_bruta.None\|None` | 2017–2026 | 3.593 |  | valor | 3 |
| `dengue.confirmados` | 2005–2026 | 5.566 |  | valor | 15 |
| `dengue.graves` | 2005–2026 | 5.566 |  | valor | 0 |
| `dengue.notificados` | 2005–2026 | 5.566 |  | valor | 18 |
| `dengue.notificados_ano_anterior` | 2005–2026 | 5.566 |  | valor | 89 |
| `dengue.obitos` | 2005–2026 | 5.566 |  | valor | 0 |
| `farmacia_popular.estabelecimentos_credenciados` | — | 5.571 |  | valor | 1 |
| `ieps.ano_max` | — | 5.570 |  | valor | 2021 |
| `ieps.ano_por_indicador.cobertura_atencao_basica` | — | 5.570 |  | valor | 2021 |
| `ieps.ano_por_indicador.cobertura_esf` | — | 5.570 |  | valor | 2021 |
| `ieps.ano_por_indicador.cobertura_plano_privado` | — | 5.565 |  | valor | 2021 |
| `ieps.ano_por_indicador.despesa_saude_per_capita` | — | 5.568 |  | valor | 2021 |
| `ieps.ano_por_indicador.enfermeiros_1000hab` | — | 5.570 |  | valor | 2021 |
| `ieps.ano_por_indicador.leitos_sus_100k` | — | 5.570 |  | valor | 2021 |
| `ieps.ano_por_indicador.leitos_uti_sus_100k` | — | 5.570 |  | valor | 2021 |
| `ieps.ano_por_indicador.medicos_1000hab` | — | 5.570 |  | valor | 2021 |
| `ieps.ano_por_indicador.pct_prenatal_adequado` | — | 5.570 |  | valor | 2020 |
| `ieps.ano_por_indicador.pct_prenatal_zero` | — | 5.570 |  | valor | 2020 |
| `ieps.ano_por_indicador.pct_receita_propria_saude` | — | 5.568 |  | valor | 2021 |
| `ieps.ano_por_indicador.taxa_internacao_csap_100k` | — | 5.570 |  | valor | 2021 |
| `ieps.ano_por_indicador.taxa_mortalidade_evitavel_100k` | — | 5.570 |  | valor | 2020 |
| `ieps.indicadores.cobertura_atencao_basica` | — | 5.570 |  | valor | 100 |
| `ieps.indicadores.cobertura_esf` | — | 5.570 |  | valor | 100 |
| `ieps.indicadores.cobertura_plano_privado` | — | 5.565 |  | valor | 4,323 |
| `ieps.indicadores.despesa_saude_per_capita` | — | 5.568 |  | valor | 1037,745 |
| `ieps.indicadores.enfermeiros_1000hab` | — | 5.570 |  | valor | 1,022 |
| `ieps.indicadores.leitos_sus_100k` | — | 5.570 |  | valor | 106,046 |
| `ieps.indicadores.leitos_uti_sus_100k` | — | 5.570 |  | valor | 0 |
| `ieps.indicadores.medicos_1000hab` | — | 5.570 |  | valor | 0,692 |
| `ieps.indicadores.pct_prenatal_adequado` | — | 5.570 |  | valor | 75,556 |
| `ieps.indicadores.pct_prenatal_zero` | — | 5.570 |  | valor | 0,671 |
| `ieps.indicadores.pct_receita_propria_saude` | — | 5.568 |  | valor | 21,24 |
| `ieps.indicadores.taxa_internacao_csap_100k` | — | 5.570 |  | valor | 789,853 |
| `ieps.indicadores.taxa_mortalidade_evitavel_100k` | — | 5.570 |  | valor | 121,874 |
| `imunizacao.serie.cobertura_bcg` | 2010–2021 | 5.570 |  | valor | 87,86 |
| `imunizacao.serie.cobertura_hepatite_b` | 2010–2021 | 5.570 |  | valor | 96,67 |
| `imunizacao.serie.cobertura_penta` | 2012–2021 | 5.570 |  | valor | 90,29 |
| `imunizacao.serie.cobertura_poliomielite` | 2010–2021 | 5.570 |  | valor | 96,39 |
| `imunizacao.serie.cobertura_total` | 2010–2021 | 5.570 |  | valor | 79,9 |
| `imunizacao.serie.cobertura_triplice_viral_d1` | 2010–2021 | 5.570 |  | valor | 99,13 |
| `internacoes.ano_anterior.internacoes` | 2021–2023 | 5.570 |  | valor | 787 |
| `internacoes.ano_anterior.valor_total` | 2021–2023 | 5.570 |  | valor | 1.071.010,935 |
| `internacoes.diarias_uti` | 2022–2024 | 5.570 |  | valor | 414,5 |
| `internacoes.internacoes` | 2022–2024 | 5.570 |  | valor | 809 |
| `internacoes.no_municipio` | 2022–2024 | 5.570 |  | valor | 66 |
| `internacoes.obitos_hospitalares` | 2022–2024 | 5.570 |  | valor | 32 |
| `internacoes.pct_no_municipio` | 2022–2024 | 5.570 |  | valor | 9,883 |
| `internacoes.permanencia_media` | 2022–2024 | 5.570 |  | valor | 4,451 |
| `internacoes.por_capitulo.internacoes` | 2022–2024 | 5.570 | capitulo | valor | 77 |
| `internacoes.por_capitulo.valor` | 2022–2024 | 5.570 | capitulo | valor | 108.863,02 |
| `internacoes.serie.internacoes` | 2013–2024 | 5.570 |  | valor | 692 |
| `internacoes.serie.valor` | 2013–2024 | 5.570 |  | valor | 871.903,87 |
| `internacoes.taxa_mortalidade_hospitalar` | 2022–2024 | 5.570 |  | valor | 4,138 |
| `internacoes.urgencia` | 2022–2024 | 5.570 |  | valor | 568 |
| `internacoes.valor_medio_aih` | 2022–2024 | 5.570 |  | valor | 1613,181 |
| `internacoes.valor_total` | 2022–2024 | 5.570 |  | valor | 1.283.664,935 |
| `mortalidade.agressoes` | 2025 | 5.570 |  | valor | 1 |
| `mortalidade.ano_parcial.ate_mes` | 2026 | 5.559 |  | valor | 5 |
| `mortalidade.ano_parcial.infantis` | 2026 | 5.559 |  | valor | 0 |
| `mortalidade.ano_parcial.obitos` | 2026 | 5.559 |  | valor | 27 |
| `mortalidade.causas_externas` | 2025 | 5.570 |  | valor | 9 |
| `mortalidade.homens` | 2025 | 5.570 |  | valor | 49 |
| `mortalidade.idade_media_obito` | 2025 | 5.570 |  | valor | 67,956 |
| `mortalidade.infantil.nascidos_vivos` | 2022 | 5.570 |  | valor | 133,5 |
| `mortalidade.infantil.neonatais` | 2022 | 5.570 |  | valor | 1 |
| `mortalidade.infantil.obitos` | 2022 | 5.570 |  | valor | 2 |
| `mortalidade.infantil.taxa_1000nv` | 2022 | 5.570 |  | valor | 9,917 |
| `mortalidade.mal_definidas` | 2025 | 5.570 |  | valor | 4 |
| `mortalidade.maternas` | 2025 | 5.570 |  | valor | 0 |
| `mortalidade.mulheres` | 2025 | 5.570 |  | valor | 36 |
| `mortalidade.obitos` | 2025 | 5.570 |  | valor | 84 |
| `mortalidade.obitos_infantis` | 2025 | 5.570 |  | valor | 1 |
| `mortalidade.obitos_neonatais` | 2025 | 5.570 |  | valor | 1 |
| `mortalidade.populacao_referencia` | 2025 | 5.570 |  | valor | 11.358,5 |
| `mortalidade.por_capitulo.obitos` | 2025 | 5.570 | capitulo | valor | 8 |
| `mortalidade.serie.infantis` | 2014–2025 | 5.570 |  | valor | 2 |
| `mortalidade.serie.obitos` | 2014–2025 | 5.570 |  | valor | 77 |
| `mortalidade.suicidios` | 2025 | 5.570 |  | valor | 1 |
| `mortalidade.taxa_mortalidade_1000hab` | 2025 | 5.570 |  | valor | 7,621 |
| `mortalidade.top_causas.obitos` | 2025 | 5.570 | cid | valor | 3 |
| `mortalidade.transporte` | 2025 | 5.570 |  | valor | 3 |
| `nascidos_vivos.nascidos_vivos` | 2022 | 5.570 |  | valor | 133,5 |
| `nascidos_vivos.pct_baixo_peso` | 2022 | 5.570 |  | valor | 8,824 |
| `nascidos_vivos.pct_cesareo` | 2022 | 5.570 |  | valor | 62,193 |
| `nascidos_vivos.pre_natal_distribuicao.1` | 2022 | 3.489 |  | valor | 3 |
| `nascidos_vivos.pre_natal_distribuicao.2` | 2022 | 4.673 |  | valor | 5 |
| `nascidos_vivos.pre_natal_distribuicao.3` | 2022 | 5.484 |  | valor | 21 |
| `nascidos_vivos.pre_natal_distribuicao.4` | 2022 | 5.570 |  | valor | 103 |
| `nascidos_vivos.pre_natal_distribuicao.9` | 2022 | 1.327 |  | valor | 2 |
| `nascidos_vivos.pre_natal_distribuicao.None` | 2022 | 335 |  | valor | 3 |
| `planos_privados.beneficiarios_total` | 2025 (+mes) | 5.570 |  | valor | 731,5 |
| `planos_privados.cobertura_pct` | 2025 (+mes) | 5.568 |  | valor | 5,458 |
| `planos_privados.medico_hospitalar` | 2025 (+mes) | 5.568 |  | valor | 491,5 |
| `planos_privados.odontologico` | 2025 (+mes) | 5.570 |  | valor | 210 |
| `planos_privados.por_contratacao.beneficiarios` | 2025 (+mes) | 5.570 | tipo | valor | 136 |
| `sisvan.criancas_acompanhadas` | 2023 | 5.570 |  | valor | 0 |

Metadados da coleta: `atencao_basica.disponivel`, `atencao_basica.motivo`, `cnes.erro`, `dengue.erro`, `ieps.erro`, `imunizacao.erro`, `internacoes.erro`, `mortalidade.erro`, `nascidos_vivos.erro`, `planos_privados.erro`, `sisvan.erro`.

### `seguranca` (171 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `fbsp.proporcao_mortes_intenvencao_policial_x_mortes_violentas_intencionais` | 2021 | 27 |  | valor | 11 |
| `fbsp.quantidade_estupro` | 2021 | 26 |  | valor | 366 |
| `fbsp.quantidade_feminicidio` | 2021 | 27 |  | valor | 5 |
| `fbsp.quantidade_furto_veiculos` | 2021 | 26 |  | valor | 870 |
| `fbsp.quantidade_homicidio_doloso` | 2021 | 27 |  | valor | 218 |
| `fbsp.quantidade_latrocinio` | 2021 | 27 |  | valor | 9 |
| `fbsp.quantidade_lesao_corporal_dolosa_violencia_domestica` | 2021 | 25 |  | valor | 995 |
| `fbsp.quantidade_lesao_corporal_morte` | 2021 | 26 |  | valor | 3,5 |
| `fbsp.quantidade_mortes_intervencao_policial` | 2021 | 27 |  | valor | 15 |
| `fbsp.quantidade_mortes_policiais_confronto` | 2021 | 27 |  | valor | 1 |
| `fbsp.quantidade_mortes_violentas_intencionais` | 2021 | 27 |  | valor | 273 |
| `fbsp.quantidade_porte_ilegal_arma_de_fogo` | 2021 | 22 |  | valor | 241,5 |
| `fbsp.quantidade_posse_ilegal_arma_de_fogo` | 2021 | 20 |  | valor | 74 |
| `fbsp.quantidade_posse_ilegal_porte_ilegal_arma_de_fogo` | 2021 | 26 |  | valor | 307 |
| `fbsp.quantidade_posse_uso_entorpecente` | 2021 | 27 |  | valor | 452 |
| `fbsp.quantidade_roubo_furto_veiculos` | 2021 | 27 |  | valor | 2146 |
| `fbsp.quantidade_roubo_veiculos` | 2021 | 26 |  | valor | 1106 |
| `fbsp.quantidade_trafico_entorpecente` | 2021 | 27 |  | valor | 1083 |
| `isp_rj.homicidio_doloso_ano_anterior` | 2025 | 92 |  | valor | 7 |
| `isp_rj.mensal.homicidio_doloso` | 2025 (+mes) | 92 |  | valor | 1 |
| `isp_rj.mensal.letalidade_violenta` | 2025 (+mes) | 92 |  | valor | 1 |
| `isp_rj.ocorrencias.cvli` | 2025 | 92 |  | valor | 8,5 |
| `isp_rj.ocorrencias.estupro` | 2025 | 92 |  | valor | 17,5 |
| `isp_rj.ocorrencias.homicidio_doloso` | 2025 | 92 |  | valor | 8 |
| `isp_rj.ocorrencias.intervencao_policial` | 2025 | 92 |  | valor | 0 |
| `isp_rj.ocorrencias.latrocinio` | 2025 | 92 |  | valor | 0 |
| `isp_rj.ocorrencias.lesao_corporal_morte` | 2025 | 92 |  | valor | 0 |
| `isp_rj.ocorrencias.letalidade_violenta` | 2025 | 92 |  | valor | 9 |
| `isp_rj.ocorrencias.roubo_veiculo` | 2025 | 92 |  | valor | 2 |
| `isp_rj.ocorrencias.tentativa_homicidio` | 2025 | 92 |  | valor | 9 |
| `isp_rj.taxas_100k.taxa_estupro` | 2020 | 38 |  | valor | 29,515 |
| `isp_rj.taxas_100k.taxa_homicidio_doloso` | 2020 | 38 |  | valor | 24,565 |
| `isp_rj.taxas_100k.taxa_homicidio_intervencao_policial` | 2020 | 38 |  | valor | 4,79 |
| `isp_rj.taxas_100k.taxa_latrocinio` | 2020 | 38 |  | valor | 0 |
| `isp_rj.taxas_100k.taxa_lesao_corporal_morte` | 2020 | 38 |  | valor | 0 |
| `isp_rj.taxas_100k.taxa_letalidade_violenta` | 2020 | 38 |  | valor | 33,795 |
| `isp_rj.taxas_100k.taxa_tentativa_homicidio` | 2020 | 38 |  | valor | 28,07 |
| `isp_rj.taxas_100k_uf.taxa_estupro` | 2020 | 92 |  | valor | 27,33 |
| `isp_rj.taxas_100k_uf.taxa_homicidio_doloso` | 2020 | 92 |  | valor | 20,41 |
| `isp_rj.taxas_100k_uf.taxa_homicidio_intervencao_policial` | 2020 | 92 |  | valor | 7,17 |
| `isp_rj.taxas_100k_uf.taxa_latrocinio` | 2020 | 92 |  | valor | 0,5 |
| `isp_rj.taxas_100k_uf.taxa_lesao_corporal_morte` | 2020 | 92 |  | valor | 0,18 |
| `isp_rj.taxas_100k_uf.taxa_letalidade_violenta` | 2020 | 92 |  | valor | 28,26 |
| `isp_rj.taxas_100k_uf.taxa_roubo_veiculo` | 2020 | 92 |  | valor | 340,57 |
| `isp_rj.taxas_100k_uf.taxa_tentativa_homicidio` | 2020 | 92 |  | valor | 25,06 |
| `prf.acidentes` | — | 2.143 |  | valor | 63 |
| `prf.ate` | — | 2.143 |  | valor | 2026 |
| `prf.desde` | — | 5.571 |  | valor | 2021 |
| `prf.feridos_graves` | — | 2.143 |  | valor | 23 |
| `prf.mortos` | — | 2.143 |  | valor | 9 |
| `prf.por_ano.acidentes` | 2021–2026 | 2.143 |  | valor | 14 |
| `prf.por_ano.feridos` | 2021–2026 | 2.143 |  | valor | 16 |
| `prf.por_ano.feridos_graves` | 2021–2026 | 2.143 |  | valor | 5 |
| `prf.por_ano.mortos` | 2021–2026 | 2.143 |  | valor | 2 |
| `prf.por_causa.n` | — | 2.143 | k | valor | 8 |
| `prf.por_rodovia.n` | — | 2.143 | k | valor | 30 |
| `prf.por_tipo.n` | — | 2.143 | k | valor | 9 |
| `sinesp.ano_parcial.ate_mes` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.feminicidio.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.feminicidio.vitimas` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.feminicidio.vitimas_feminino` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.homicidio_doloso.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.homicidio_doloso.vitimas` | 2026 | 5.570 |  | valor | 1 |
| `sinesp.ano_parcial.por_tipo.homicidio_doloso.vitimas_feminino` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.latrocinio.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.latrocinio.vitimas` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.latrocinio.vitimas_feminino` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.lesao_corporal_seguida_de_morte.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.lesao_corporal_seguida_de_morte.vitimas` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.lesao_corporal_seguida_de_morte.vitimas_feminino` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.mandado_de_prisao_cumprido.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.mandado_de_prisao_cumprido.ocorrencias` | 2026 | 5.570 |  | valor | 5 |
| `sinesp.ano_parcial.por_tipo.morte_a_esclarecer.meses` | 2026 | 4.359 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.morte_a_esclarecer.vitimas` | 2026 | 4.359 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.morte_a_esclarecer.vitimas_feminino` | 2026 | 4.359 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.morte_no_transito_exceto_homicidio_doloso.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.morte_no_transito_exceto_homicidio_doloso.vitimas` | 2026 | 5.570 |  | valor | 1 |
| `sinesp.ano_parcial.por_tipo.morte_no_transito_exceto_homicidio_doloso.vitimas_feminino` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.suicidio.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.suicidio.vitimas` | 2026 | 5.570 |  | valor | 1 |
| `sinesp.ano_parcial.por_tipo.suicidio.vitimas_feminino` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.tentativa_de_feminicidio.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.tentativa_de_feminicidio.vitimas` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.tentativa_de_feminicidio.vitimas_feminino` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.ano_parcial.por_tipo.tentativa_de_homicidio.meses` | 2026 | 5.570 |  | valor | 8 |
| `sinesp.ano_parcial.por_tipo.tentativa_de_homicidio.vitimas` | 2026 | 5.570 |  | valor | 1 |
| `sinesp.ano_parcial.por_tipo.tentativa_de_homicidio.vitimas_feminino` | 2026 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.feminicidio.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.feminicidio.vitimas` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.feminicidio.vitimas_feminino` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.homicidio_doloso.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.homicidio_doloso.vitimas` | 2025 | 5.570 |  | valor | 1 |
| `sinesp.por_tipo.homicidio_doloso.vitimas_feminino` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.latrocinio.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.latrocinio.vitimas` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.latrocinio.vitimas_feminino` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.lesao_corporal_seguida_de_morte.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.lesao_corporal_seguida_de_morte.vitimas` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.lesao_corporal_seguida_de_morte.vitimas_feminino` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.mandado_de_prisao_cumprido.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.mandado_de_prisao_cumprido.ocorrencias` | 2025 | 5.393 |  | valor | 7 |
| `sinesp.por_tipo.morte_a_esclarecer.meses` | 2025 | 4.421 |  | valor | 12 |
| `sinesp.por_tipo.morte_a_esclarecer.vitimas` | 2025 | 4.421 |  | valor | 0 |
| `sinesp.por_tipo.morte_a_esclarecer.vitimas_feminino` | 2025 | 4.421 |  | valor | 0 |
| `sinesp.por_tipo.morte_no_transito_exceto_homicidio_doloso.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.morte_no_transito_exceto_homicidio_doloso.vitimas` | 2025 | 5.570 |  | valor | 1 |
| `sinesp.por_tipo.morte_no_transito_exceto_homicidio_doloso.vitimas_feminino` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.suicidio.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.suicidio.vitimas` | 2025 | 5.570 |  | valor | 1 |
| `sinesp.por_tipo.suicidio.vitimas_feminino` | 2025 | 5.530 |  | valor | 0 |
| `sinesp.por_tipo.tentativa_de_feminicidio.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.tentativa_de_feminicidio.vitimas` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.por_tipo.tentativa_de_feminicidio.vitimas_feminino` | 2025 | 5.532 |  | valor | 0 |
| `sinesp.por_tipo.tentativa_de_homicidio.meses` | 2025 | 5.570 |  | valor | 12 |
| `sinesp.por_tipo.tentativa_de_homicidio.vitimas` | 2025 | 5.570 |  | valor | 1 |
| `sinesp.por_tipo.tentativa_de_homicidio.vitimas_feminino` | 2025 | 5.570 |  | valor | 0 |
| `sinesp.serie.homicidio_doloso` | 2015–2026 | 5.570 |  | valor | 1 |
| `sinesp.serie.meses` | 2015–2026 | 5.570 |  | valor | 12 |
| `sinesp.taxa_homicidio_doloso_100k.ano_populacao` | 2025 | 5.570 |  | valor | 2025 |
| `sinesp.taxa_homicidio_doloso_100k.brasil` | 2025 | 5.570 |  | valor | 14,754 |
| `sinesp.taxa_homicidio_doloso_100k.municipio` | 2025 | 5.570 |  | valor | 8,112 |
| `sinesp.taxa_homicidio_doloso_100k.uf` | 2025 | 5.570 |  | valor | 10,83 |
| `sisdepen.capacidade` | — | 1.164 |  | valor | 80 |
| `sisdepen.competencia` | — | 1.164 |  | texto | `2025/2` |
| `sisdepen.faixa_etaria` | — | 240 | k | pai (sem valor) |  |
| `sisdepen.faixa_etaria.n` | — | 1.101 | k | valor | 15 |
| `sisdepen.lista` | — | 1 | nome | pai (sem valor) |  |
| `sisdepen.lista.capacidade` | — | 1.164 | nome | valor | 98 |
| `sisdepen.mulheres` | — | 1.164 |  | valor | 0 |
| `sisdepen.populacao` | — | 1.164 |  | valor | 156 |
| `sisdepen.por_regime.n` | — | 1.164 | k | valor | 6 |
| `sisdepen.provisorios` | — | 1.164 |  | valor | 52 |
| `sisdepen.raca_cor` | — | 229 | k | pai (sem valor) |  |
| `sisdepen.raca_cor.n` | — | 1.102 | k | valor | 9 |
| `sisdepen.serie.populacao` | — | 1.164 | periodo | valor | 186 |
| `sisdepen.taxa_ocupacao` | — | 1.163 |  | valor | 1,769 |
| `sisdepen.unidades` | — | 1.164 |  | valor | 1 |
| `violencia_sinan.arma_fogo` | 2020–2025 | 5.569 |  | valor | 0 |
| `violencia_sinan.autoprovocadas` | 2020–2025 | 5.569 |  | valor | 6 |
| `violencia_sinan.brancos` | 2020–2025 | 5.569 |  | valor | 5 |
| `violencia_sinan.feminino` | 2020–2025 | 5.569 |  | valor | 15 |
| `violencia_sinan.financeira` | 2020–2025 | 5.569 |  | valor | 0 |
| `violencia_sinan.fisica` | 2020–2025 | 5.569 |  | valor | 12 |
| `violencia_sinan.infantil_trabalho` | 2020–2025 | 5.569 |  | valor | 0 |
| `violencia_sinan.masculino` | 2020–2025 | 5.569 |  | valor | 7 |
| `violencia_sinan.negligencia` | 2020–2025 | 5.569 |  | valor | 0 |
| `violencia_sinan.negros` | 2020–2025 | 5.569 |  | valor | 12 |
| `violencia_sinan.nota_raca` | 2020–2025 | 5.569 |  | texto | `negro = preto + pardo (CS_RACA` |
| `violencia_sinan.notificacoes` | 2020–2025 | 5.569 |  | valor | 23 |
| `violencia_sinan.pct_feminino` | 2020–2025 | 5.569 |  | valor | 68,421 |
| `violencia_sinan.pct_negros` | 2020–2025 | 5.569 |  | valor | 65 |
| `violencia_sinan.por_ciclo_vida.n` | 2020–2025 | 5.569 | ciclo | valor | 4 |
| `violencia_sinan.por_local.n` | 2020–2025 | 5.569 | local | valor | 3 |
| `violencia_sinan.psicologica` | 2020–2025 | 5.569 |  | valor | 4 |
| `violencia_sinan.raca_ignorada` | 2020–2025 | 5.569 |  | valor | 0 |
| `violencia_sinan.serie.autoprovocadas` | 2011–2025 | 5.569 |  | valor | 3 |
| `violencia_sinan.serie.notificacoes` | 2011–2025 | 5.569 |  | valor | 12 |
| `violencia_sinan.sexual` | 2020–2025 | 5.569 |  | valor | 2 |
| `violencia_sinan.tortura` | 2020–2025 | 5.569 |  | valor | 0 |
| `violencia_sinan.trafico_humano` | 2020–2025 | 5.569 |  | valor | 0 |

Metadados da coleta: `fbsp.disponivel`, `fbsp.motivo`, `isp_rj.disponivel`, `isp_rj.motivo`, `prf.disponivel`, `prf.motivo`, `sinesp.disponivel`, `sinesp.motivo`, `sisdepen.disponivel`, `sisdepen.motivo`, `violencia_sinan.erro`.

### `social` (29 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `avs.idhm` | 2010 | 5.565 |  | valor | 0,664 |
| `avs.idhm_educacao` | 2010 | 5.565 |  | valor | 0,559 |
| `avs.idhm_longevidade` | 2010 | 5.565 |  | valor | 0,806 |
| `avs.idhm_renda` | 2010 | 5.565 |  | valor | 0,652 |
| `avs.ivs` | 2010 | 5.565 |  | valor | 0,336 |
| `avs.ivs_capital_humano` | 2010 | 5.565 |  | valor | 0,412 |
| `avs.ivs_infraestrutura_urbana` | 2010 | 5.565 |  | valor | 0,195 |
| `avs.ivs_renda_trabalho` | 2010 | 5.565 |  | valor | 0,39 |
| `primeira_infancia.matriculas_pre_escola` | 2019 | 5.570 |  | valor | 294,5 |
| `primeira_infancia.taxa_bruta_pre_escola` | 2019 | 5.570 |  | valor | 84,4 |
| `primeira_infancia.taxa_liquida_pre_escola` | 2019 | 5.570 |  | valor | 77,4 |
| `rouanet.entidades` | — | 4.417 |  | valor | 2 |
| `rouanet.projetos` | — | 4.417 |  | valor | 3 |
| `rouanet.proponentes` | — | 4.417 |  | valor | 1 |
| `rouanet.top_proponentes.projetos` | — | 4.311 | nome | valor | 1 |
| `rouanet.top_proponentes.valor` | — | 4.311 | nome | valor | 0 |
| `rouanet.valor_projetos` | — | 4.417 |  | valor | 0 |
| `sinpatinhas.animais` | — | 5.397 |  | valor | 22 |
| `sinpatinhas.periodo.ate` | — | 5.397 |  | texto | `2025-12-02` |
| `sinpatinhas.periodo.de` | — | 5.397 |  | texto | `2025-04-15` |
| `sinpatinhas.por_1000hab.ano_populacao` | — | 5.397 |  | valor | 2025 |
| `sinpatinhas.por_1000hab.brasil` | — | 5.397 |  | valor | 4,351 |
| `sinpatinhas.por_1000hab.municipio` | — | 5.397 |  | valor | 2,011 |
| `sinpatinhas.por_1000hab.uf` | — | 5.397 |  | valor | 3,861 |
| `sinpatinhas.por_especie.n` | — | 5.397 | k | valor | 12 |

Metadados da coleta: `rouanet.disponivel`, `rouanet.motivo`, `sinpatinhas.disponivel`, `sinpatinhas.motivo`.

### `trabalho` (22 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `caged.admissoes` | 2020–2025 | 5.562 |  | valor | 445,5 |
| `caged.desligamentos` | 2020–2025 | 5.562 |  | valor | 413 |
| `caged.salario_medio_admissao` | 2020–2025 | 5.559 |  | valor | 1931,543 |
| `caged.saldo` | 2020–2025 | 5.562 |  | valor | 22 |
| `lista_suja.brasil.empregadores` | — | 5.571 |  | valor | 508 |
| `lista_suja.brasil.trabalhadores` | — | 5.571 |  | valor | 3989 |
| `lista_suja.data_coleta` | — | 5.571 |  | texto | `2026-10-09` |
| `lista_suja.empregadores.ano_acao_fiscal` | — | 325 | empregador, documento, atividade, local | valor | 2024 |
| `lista_suja.empregadores.trabalhadores` | — | 325 | empregador, documento, atividade, local | valor | 4 |
| `lista_suja.total` | — | 5.571 |  | valor | 0 |
| `lista_suja.trabalhadores` | — | 5.571 |  | valor | 0 |
| `lista_suja.uf.empregadores` | — | 5.571 |  | valor | 25 |
| `lista_suja.uf.trabalhadores` | — | 5.555 |  | valor | 183 |
| `rais.estabelecimentos` | 2025 | 5.571 |  | valor | 497 |
| `rais.remuneracao_media` | 2025 | 5.571 |  | valor | 3080,452 |
| `rais.vinculos_ativos_3112` | 2025 | 5.571 |  | valor | 1641 |
| `rais.vinculos_ativos_ano_anterior` | 2025 | 5.571 |  | valor | 1449 |
| `top_empregadores.top.vinculos_ativos` | 2021 | 5.564 | empresa, setor, natureza | valor | 18 |
| `top_empregadores_publicos.top.vinculos_ativos` | 2021 | 5.556 | empresa, natureza | valor | 60 |

Metadados da coleta: `caged.erro`, `top_empregadores.erro`, `top_empregadores_publicos.erro`.

### `transparencia` (52 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `cauc.data_pesquisa` | — | 5.569 |  | texto | `02/10/2026` |
| `cauc.itens` | — | 5.569 |  | valor | 28 |
| `cauc.itens_pendentes` | — | 4.541 | item, descricao, situacao | pai (sem valor) |  |
| `cauc.lista` | — | 5.569 | item, descricao, situacao | pai (sem valor) |  |
| `cauc.pendencias` | — | 5.569 |  | valor | 2 |
| `cauc.regulares` | — | 5.569 |  | valor | 24 |
| `clp.pilares.colocacao` | 2022 | 415 | pilar_dimensao | valor | 208 |
| `clp.pilares.nota_geral` | 2022 | 415 | pilar_dimensao | valor | 53,94 |
| `compras_federais.fornecedores_locais.serie.contratos` | 2013–2026 | 2.932 |  | valor | 2 |
| `compras_federais.fornecedores_locais.serie.valor` | 2013–2026 | 2.932 |  | valor | 333.268,625 |
| `compras_federais.fornecedores_locais.snapshot_cnpj` | — | 5.570 |  | texto | `2026-09` |
| `compras_federais.fornecedores_locais.top.contratos` | — | 2.932 | empresa | valor | 2 |
| `compras_federais.fornecedores_locais.top.valor` | — | 2.932 | empresa | valor | 562.670,4 |
| `compras_federais.licitacoes_no_municipio.por_orgao.licitacoes` | — | 609 | orgao | valor | 280 |
| `compras_federais.licitacoes_no_municipio.por_orgao.valor` | — | 609 | orgao | valor | 11.494.046,2 |
| `compras_federais.licitacoes_no_municipio.serie.licitacoes` | 2013–2023 | 609 |  | valor | 38 |
| `compras_federais.licitacoes_no_municipio.serie.valor` | 2013–2023 | 609 |  | valor | 1.061.791,865 |
| `consumidor.serie.nota_media` | 2014–2025 | 5.539 |  | valor | 3 |
| `consumidor.serie.pct_respondida` | 2014–2025 | 5.563 |  | valor | 92,199 |
| `consumidor.serie.reclamacoes` | 2014–2025 | 5.563 |  | valor | 11 |
| `consumidor.top_empresas.reclamacoes` | 2016–2025 | 5.563 | empresa | valor | 2 |
| `consumidor.top_segmentos.reclamacoes` | 2016–2025 | 5.563 | segmento | valor | 3 |
| `diarios_oficiais.serie.edicoes` | 2023–2026 | 524 |  | valor | 144 |
| `diarios_oficiais.serie.extras` | 2023–2026 | 524 |  | valor | 0 |
| `diarios_oficiais.total_edicoes` | — | 524 |  | valor | 581 |
| `diarios_oficiais.ultima_edicao` | — | 524 |  | texto | `2026-10-01` |
| `ebt.nota` | 2020–2021 | 665 |  | valor | 6,56 |
| `ebt.ranking` | 2020–2021 | 665 |  | valor | 332,5 |
| `emendas.janela_autores` | 2014–2025 | 5.418 |  | texto | `2020–2025` |
| `emendas.por_funcao.pago` | 2014–2025 | 3.694 | funcao | valor | 400.000 |
| `emendas.serie.emendas` | 2014–2025 | 5.418 |  | valor | 1 |
| `emendas.serie.empenhado` | 2014–2025 | 5.418 |  | valor | 500.000 |
| `emendas.serie.pago` | 2014–2025 | 5.418 |  | valor | 0 |
| `emendas.top_autores.emendas` | 2014–2025 | 5.418 | autor | valor | 1 |
| `emendas.top_autores.pago` | 2014–2025 | 5.418 | autor | valor | 47.767,85 |
| `fiscal.ifgf.indice` | 2013–2022 | 5.566 |  | valor | 0,494 |
| `fiscal.ifgf.ranking_estadual` | 2013–2022 | 5.566 |  | valor | 134 |
| `fiscal.ifgf.ranking_nacional` | 2013–2022 | 5.566 |  | valor | 2662 |
| `fiscalizacao_cgu.sorteios` | — | 1.949 | i | valor | 22 |
| `servidores.adm_direta` | 2020–2023 | 5.570 |  | valor | 597 |
| `servidores.adm_indireta` | 2020–2023 | 1.431 |  | valor | 16 |
| `servidores.clt_adm_direta` | 2020–2023 | 5.570 |  | valor | 0 |
| `servidores.comissionado_adm_direta` | 2020–2023 | 5.570 |  | valor | 56 |
| `servidores.estagio_adm_direta` | 2020–2023 | 5.570 |  | valor | 1 |
| `servidores.estatutario_adm_direta` | 2020–2023 | 5.570 |  | valor | 308 |
| `servidores.sem_vinculo_permanente_adm_direta` | 2020–2023 | 5.570 |  | valor | 94 |

Metadados da coleta: `cauc.disponivel`, `cauc.motivo`, `consumidor.erro`, `diarios_oficiais.erro`, `emendas.erro`, `servidores.erro`.

### `vizinhanca` (7 indicadores)

| indicador | anos | mun. | dimensão (chaves) | tipo | mediana |
|---|---|---:|---|---|---:|
| `municipios.pib_per_capita` | — | 5.568 | id_municipio, nome, sigla_uf | valor | 29.862,15 |
| `municipios.populacao` | — | 5.568 | id_municipio, nome, sigla_uf | valor | 13.723 |
| `referencia.pib_ano` | — | 5.570 |  | valor | 2023 |
| `referencia.pib_per_capita` | — | 5.570 |  | valor | 29.107,211 |
| `referencia.populacao` | — | 5.570 |  | valor | 11.358,5 |
| `referencia.populacao_ano` | — | 5.570 |  | valor | 2025 |

Metadados da coleta: `erro`.
