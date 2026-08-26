# De-anonimização — o que no espelho já tem nome

Boa parte do espelho identifica empresa e pessoa só por CNPJ ou CPF. Nove tabelas
foram reescritas para carregar o nome junto do documento, sempre **na própria tabela**
— não existe tabela `_deanonimizado` paralela, e a coluna original nunca foi removida.

Documento escrito à mão, não gerado. O log da execução, com as medições que
sustentam cada número aqui, está em `tasks/deanonimizacao_geral.md`.

## O que consultar

### Empresas — join exato por CNPJ

Nome vindo do snapshot **2025-09** de `br_me_cnpj` (`empresas` para `razao_social`,
`estabelecimentos` para `nome_fantasia` e situação cadastral). Igualdade de dígitos,
sem heurística de texto: onde a cobertura não é 100%, o que falta é documento ausente
na origem, não join incerto.

| Tabela | Colunas de nome | Cobertura |
|---|---|---|
| `br_ms_cnes.estabelecimento` | `razao_social`, `nome_fantasia`, `situacao_cadastral_codigo`, `situacao_cadastral_descricao`, `razao_social_mantenedora` | 99,996% das linhas de PJ |
| `br_ms_sih.aihs_reduzidas` | `razao_social_estabelecimento`, `nome_fantasia_estabelecimento`, `razao_social_mantenedora`, `origem_nome_estabelecimento` | 84,7% com nome próprio; 98,9% com algum nome |
| `br_bcb_sicor.operacao` | `razao_social_instituicao_financeira`, `razao_social_agente_investimento`, `razao_social_cadastrante` | 100,000% |
| `br_bcb_sicor.recurso_publico_complemento_operacao` | `razao_social_agencia`, `nome_fantasia_agencia`, `sigla_uf_agencia`, `id_municipio_agencia` | 100,000% |
| `br_bcb_sicor.recurso_publico_mutuario` | `razao_social_mutuario`, `razao_social_cnpj_basico` | 100,000% das linhas de PJ |
| `br_bcb_sicor.recurso_publico_propriedade` | `razao_social_cnpj_basico` | 100,000% das linhas de PJ |
| `br_bcb_sicor.recurso_publico_cooperado` | `razao_social_cnpj_basico` | 100,000% das linhas de PJ |
| `br_transferegov.transferencias` | `razao_social_favorecido`, `nome_fantasia_favorecido` | 100% — **leia a ressalva** |
| `br_me_rais_identificada.estabelecimentos` | `cnpj_completo`, `nome_fantasia`, `situacao_cadastral_codigo`, `situacao_cadastral_descricao`, `data_situacao_cadastral` | 99,9995% |

Com isso dá pra rankear hospital por gasto do SUS, banco por volume de crédito rural ou
agência por operação sem passar por CNPJ nenhum:

```sql
SELECT razao_social_estabelecimento, count(*) internacoes, round(sum(valor_aih)) valor
FROM br_ms_sih.aihs_reduzidas
WHERE ano = 2024 AND id_municipio_estabelecimento LIKE '35%'
  AND razao_social_estabelecimento IS NOT NULL
GROUP BY 1 ORDER BY valor DESC LIMIT 10;
```

### Pessoas físicas — só no SICOR

| Tabela | Colunas | Cobertura |
|---|---|---|
| `br_bcb_sicor.recurso_publico_mutuario` | `nome_cpf`, `variantes_nome_cpf`, `origem_nome_cpf` | 60,7% |
| `br_bcb_sicor.recurso_publico_propriedade` | idem | 54,9% |
| `br_bcb_sicor.recurso_publico_cooperado` | idem | 44,2% |

3.425.540 dos 5.607.513 CPFs distintos (61,09%), resolvidos por igualdade exata de 11
dígitos contra 16 cadastros do espelho que publicam CPF completo com nome. 99,267% têm
nome unânime entre as fontes; a divergência restante é acento e nome de casada — a
mesma pessoa, não colisão de CPF. `variantes_nome_cpf` conta quantas grafias existiam.

## O que os nomes revelam

Cinco resultados medidos em 2026-08-26, logo depois da reescrita. Servem de exemplo do
tipo de pergunta que passou a ter resposta — e o quinto é de um tipo que nenhuma tabela
respondia sozinha.

### 1. O CNES não é uma base de hospitais

Agrupando por raiz de CNPJ, os maiores "grupos de saúde" do país são redes de farmácia
e laboratório:

| Grupo | Unidades | UFs |
|---|---|---|
| RAIA DROGASIL S/A | 2.743 | 27 |
| COMERCIO DE MEDICAMENTOS BRAIR LTDA | 1.161 | 3 |
| EMPREENDIMENTOS PAGUE MENOS S/A | 1.142 | 27 |
| DIAGNOSTICOS DA AMERICA S.A. (DASA) | 640 | 12 |
| FLEURY S.A. | 317 | 9 |
| HAPVIDA ASSISTENCIA MEDICA S.A. | 217 | 15 |

O nome dá o grupo; o que a unidade **é** vem de `tipo_unidade`, decodificado por
`br_ms_cnes.dicionario`. Das 459.695 unidades de 06/2025:

| Tipo | Unidades |
|---|---|
| consultório isolado | 215.540 (116.456 registrados em CPF) |
| clínica especializada / ambulatório especializado | 84.209 |
| centro de saúde / UBS | 43.159 |
| serviço de apoio de diagnose e terapia | 31.180 |
| farmácia | 19.657 |
| policlínica | 12.264 |
| **todos os tipos hospitalares somados** | **16.218** |

Ver a armadilha 5. **Não classifique por `ILIKE` sobre a razão social** — contando por
nome eu achara 3.579 hospitais e 10.907 farmácias, contra 16.218 e 19.657 reais.
O nome serve para saber *quem opera*, `tipo_unidade` para saber *o que é*.

```sql
SELECT substr(cpf_cnpj,1,8) AS raiz, any_value(razao_social) AS grupo,
       count(DISTINCT id_estabelecimento_cnes) AS unidades, count(DISTINCT sigla_uf) AS ufs
FROM br_ms_cnes.estabelecimento
WHERE ano=2025 AND mes=6 AND tipo_pessoa='3' AND length(cpf_cnpj)=14 AND razao_social IS NOT NULL
GROUP BY 1 HAVING count(DISTINCT id_estabelecimento_cnes) >= 10 ORDER BY unidades DESC;
```

### 2. Para onde o dinheiro do SUS vai, por entidade

Maiores recebedores não-governamentais, internações de 2024:

| Entidade | Internações | Valor |
|---|---|---|
| EBSERH | 281.095 | R$ 646,1 mi |
| FUNDACAO FACULDADE REGIONAL DE MEDICINA S J RIO PRETO | 53.599 | R$ 228,0 mi |
| SANTA CASA DE MISERICORDIA DE BELO HORIZONTE | 59.497 | R$ 216,5 mi |
| MATERNIDADE E CIRURGIA N. S. DO ROCIO S/A | 53.105 | R$ 206,8 mi |
| FUNDACAO ZERBINI | 14.584 | R$ 168,6 mi |

A assimetria é a pergunta nova: Zerbini fatura R$ 168,6 mi em 14,5 mil internações;
São Camilo, R$ 198,0 mi em 158,9 mil. Valor por internação como proxy de complexidade
só existe com o nome.

**Separar poder público por nome não funciona.** Na primeira passada o filtro tinha
`%MUNICIPIO%` e deixou passar `RIO DE JANEIRO SEC MUNICIPAL DE SAUDE`. Use
`natureza_juridica` (via `br_me_cnpj.empresas`), não `ILIKE` sobre a razão social.

### 3. "Crédito rural" são dois produtos diferentes com o mesmo nome

| Banco | Operações 2024 | Volume | Ticket médio |
|---|---|---|---|
| ITAU UNIBANCO | 3.756 | R$ 16,2 bi | **R$ 4,3 mi** |
| BANCO DO BRASIL | 581.527 | R$ 154,9 bi (40,8%) | R$ 266 mil |
| BANCO DO NORDESTE | 1.095.910 | R$ 20,6 bi | **R$ 18,8 mil** |

O BNB faz quase o dobro das operações do BB movimentando 13% do valor. Itaú e BNB estão
na mesma coluna da mesma tabela com ticket **229 vezes** diferente: somar os dois num
"total de crédito rural" mistura safra corporativa com microcrédito do Pronaf.

```sql
SELECT razao_social_instituicao_financeira AS banco, count(*) operacoes,
       round(sum(valor_parcela_credito)/1e9,2) bilhoes,
       round(sum(valor_parcela_credito)/count(*)) ticket_medio
FROM br_bcb_sicor.operacao WHERE ano_emissao=2024 GROUP BY 1 ORDER BY bilhoes DESC;
```

### 4. Quem toma crédito rural, dos 3,02 milhões nomeados no `mutuario`

| Também aparece em | Pessoas |
|---|---|
| lista de benefício social | **2.575.525** |
| filiação partidária | 749.856 |
| candidatos a cargo eletivo | 110.800 |
| servidores federais | 13.518 |
| inidôneos / contas irregulares no TCU | 590 |

Sai direto de `origem_nome_cpf`, sem join novo. Os 2,58 milhões em lista de benefício
são o retrato do Pronaf — e a informação mais sensível do conjunto (armadilha 3).

### 5. A coluna vertebral: a mesma entidade atravessando domínios

Saúde, crédito rural e emprego formal não tinham chave comum. Agora têm:

- **94.688** raízes de CNPJ estão no CNES **e** na RAIS identificada — dá pra pendurar
  vínculos formais em estabelecimento de saúde.
- **71 empresas, 125 unidades** estão no CNES **e** tomando crédito rural: BRF, RAIZEN
  CENTRO-SUL, ATVOS (cinco usinas), SAO MARTINHO, LOUIS DREYFUS SUCOS, COOPERATIVA
  AURORA, BRACELL, AGROPECUARIA SCHIO, ALIBEM ALIMENTOS, STARA.

Conferido o que são essas 125 unidades, e não é hospital: **106 são consultório isolado
ou ambulatório especializado, e 120 das 125 têm `indicador_vinculo_sus = 0`**. É
**saúde ocupacional na planta** — o ambulatório da fábrica, fora do SUS, no canteiro.
A BRF aparece com unidade em seis UFs, a Atvos em cinco. A única exceção é a
`ASSOCIACAO ... HOSPITAL SAO JOSE` (MG), hospital geral com vínculo SUS que também toma
crédito rural — outra coisa, não o mesmo padrão.

Esse recorte não existia: um lado era CNPJ no CNES, o outro CNPJ no SICOR, e ninguém
juntava. É o tipo de coisa que os campos contam **em conjunto** e nenhum conta sozinho.
Vale a ressalva de que o casamento é por **raiz** de CNPJ (8 dígitos): afirma que o
mesmo grupo econômico faz as duas coisas, não que o mesmo estabelecimento faz.

```sql
WITH saude AS (
  SELECT DISTINCT substr(cpf_cnpj,1,8) raiz, razao_social FROM br_ms_cnes.estabelecimento
  WHERE ano=2025 AND mes=6 AND tipo_pessoa='3' AND length(cpf_cnpj)=14 AND razao_social IS NOT NULL),
rural AS (
  SELECT DISTINCT substr(cnpj,1,8) raiz FROM br_bcb_sicor.recurso_publico_mutuario WHERE length(cnpj)=14)
SELECT s.razao_social FROM saude s JOIN rural r USING (raiz);
```

## As cinco coisas que dão resultado errado em silêncio

**1. `razao_social` nunca cai para `razao_social_mantenedora`.** Uma UBS não é a
prefeitura. As duas colunas ficam separadas de propósito, e um `coalesce` entre elas
troca "quem é este estabelecimento" por "quem é o dono dele" sem avisar. Se você quer o
comportamento de fallback, escreva o `coalesce` explicitamente e saiba o que está
somando.

**2. `br_transferegov.transferencias.cnpj_favorecido_empenho` não é quem recebeu.** É o
agente financeiro que pagou: 4.218 das 4.248 linhas (99,3%, R$ 1,50 bi) são do BANCO DO
BRASIL SA. `razao_social_favorecido` está correta em relação à coluna que a originou —
e a coluna responde outra pergunta. Agrupar gasto por ela devolve um ranking de bancos
com cara de ranking de beneficiários. Marcada como `false_friend` em `bridges.yaml`.

**3. `origem_nome_cpf` é parte do dado, não metadado descartável.** Ela diz de qual
cadastro veio o nome. **954.718 dos produtores rurais nomeados vêm *só* do auxílio
emergencial**, e 675.356 constam das quatro listas de benefício ao mesmo tempo. Quem
agrupa por `nome_cpf` e publica está publicando "esta pessoa consta de lista de
benefício social" junto com o nome, queira ou não. Decida isso de propósito.

**4. 38,91% dos CPFs do SICOR não têm nome, e o `NULL` não é ruído aleatório.** São os
CPFs ausentes das 16 fontes — ou seja, quem não é filiado a partido, não é candidato,
não é servidor federal e não recebeu benefício. Contar só as linhas nomeadas produz uma
amostra enviesada exatamente nessas direções.

**5. Contar linha do CNES não conta hospital.** A base cobre toda unidade de saúde
registrada: das 459.695 de 06/2025, **215.540 são consultório isolado** e apenas
**16.218 são de algum tipo hospitalar**. Uma estatística de "estabelecimentos de saúde
no Brasil" tirada daqui sem recorte por `tipo_unidade` conta drogaria e consultório como
equipamento de saúde. E os 116.456 consultórios registrados em CPF são exatamente as
linhas que continuam sem nome (armadilha do `cpf_cnpj`, abaixo) — o pedaço mais anônimo
da base é também o mais numeroso.

## Onde o join mora

As receitas estão em `docs/context/bridges.yaml` (renderizadas em `join_keys.md`), e o
MCP as devolve por `resolve_join` / `explain_column`. As que mais custaram:

- **`br_ms_sih.aihs_reduzidas.cnpj_estabelecimento` perde o zero à esquerda em
  37.115.348 linhas (18,5%)** — precisa de `lpad(...,14,'0')`. E guarda **14 espaços em
  branco, não NULL**, em outras 47.490.278 (23,7%), então `count(cnpj_estabelecimento)`
  conta essas como preenchidas. Descontando os brancos, todo CNPJ real casou.
- **`br_ms_cnes.estabelecimento.cpf_cnpj` mistura CPF e CNPJ** e só `tipo_pessoa`
  separa: `'3'` é CNPJ de 14 dígitos, `'1'` é CPF de 11 alinhado à direita num campo de
  14 (`00087978997120` = CPF 87978997120). Sem filtrar `tipo_pessoa`, 22,8M linhas de
  pessoa física vão contra a base de CNPJ.
- **`br_me_cnpj.socios` não serve como fonte de nome por CPF.** A Receita mascara o CPF
  de pessoa física deixando 6 dígitos do meio, e existem 999.751 máscaras para 17,2M
  pares máscara/nome: **17,17 nomes por máscara**, 0,18% únicas. Um join por
  `substr(cpf,4,6)` acerta ~5,8% das vezes. Não é join com ruído, é join sem sinal.
- **`br_me_cnpj.empresas` e `estabelecimentos` são 43 snapshots mensais empilhados.**
  Sem `WHERE ano = 2025 AND mes = 9` o join multiplica cada empresa por 43.

## Duas armadilhas de leitura fora do join

- **`br_ms_sih.aihs_reduzidas.sigla_uf` é BIGINT e está 100% nula** nas 200M linhas —
  já era assim antes desta reescrita. Filtre por `id_municipio_estabelecimento`.
- **`br_cgu_beneficios_cidadao.bpc` tem UTF-8 inválido em 2020-11** que aborta a leitura
  de `nome_favorecido` na tabela inteira. `WHERE NOT (...)` e `WHERE ano IN (...)` **não**
  podam o row group — o erro acontece antes do filtro; só varrer ano a ano com `=`
  funciona. E `bpc_original` não é a cópia sã: é o arquivo cru da CGU, com o CPF
  mascarado, e usá-la como fallback devolve zero linhas casadas em silêncio.

## Reverter

Backups por tabela em `~/backups/<dataset>_<tabela>__20260826/` no beelink (estado
original). As três tabelas do SICOR que receberam CNPJ e depois CPF têm um segundo
backup `__20260826_balde1` com o estado intermediário. Para reverter: apagar o diretório
em `~/rodado/<ds>/<tbl>/`, copiar o backup de volta, recriar a view.

Os insumos ficaram em `~/staging/`: `lookup_cnpj14.parquet`, `lookup_cnpj8b.parquet`,
`lookup_cnes.parquet` para o lado CNPJ, e `b2_registro.parquet` — o registro CPF→nome
consolidado das 16 fontes, 3,4M linhas — para o lado CPF. Com eles dá pra refazer
qualquer join sem revarrer os 2,4 bilhões de linhas do `br_me_cnpj` nem os 2,8 bilhões
das tabelas de benefício.
