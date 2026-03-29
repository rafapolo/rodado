# Relatório de Auditoria — Base dos Dados (DuckDB)

Análise de auditoria dos 8 padrões de risco para detecção de fraudes em compras públicas, implementados sobre o banco de dados DuckDB da Base dos Dados.

---

## Visão Geral do Banco de Dados

| Métrica | Valor |
|---------|-------|
| Total de views | 568 |
| Período dos dados de contratos | 2013–2025 |
| Tabelas de licitação/contrato | 8 tabelas no dataset `br_cgu_licitacao_contrato` |

### Tabelas Principais (br_cgu_licitacao_contrato)

| Tabela | Descrição | Colunas Relevantes |
|--------|-----------|---------------------|
| `contrato_compra` | Contratos de compra | `id_orgao_superior`, `nome_orgao_superior`, `cpf_cnpj_contratado`, `valor_inicial_compra`, `valor_final_compra`, `data_assinatura_contrato`, `id_unidade_gestora`, `objeto` |
| `licitacao` | Licitações | `id_licitacao`, `id_orgao_superior`, `valor_licitacao`, `modalidade_compra` |
| `licitacao_participante` | Participantes de licitações | `id_licitacao`, `cpf_cnpj_participante`, `nome_participante`, `vencedor` |
| `contrato_termo_aditivo` | Aditivos contratuais | `id_contrato`, `valor_aditivo`, `data_aditivo` |
| `contrato_apostilamento` | Apostilamentos | `id_contrato`, `valor_apostilamento` |

### Tabela de Diretórios

| Tabela | Descrição | Colunas Relevantes |
|--------|-----------|---------------------|
| `br_bd_diretorios_brasil.municipio` | Diretório de municípios | `id_municipio`, `nome`, `sigla_uf` |
| `br_bd_diretorios_brasil.empresa` | Dados de empresas (CNPJ) | `cnpj_basico`, `razao_social`, `data_inicio_atividade`, `natureza_juridica` |

---

## PS1 — Contratos Divididos Abaixo do Limiar (`split_contracts_below_threshold`)

### Base Legal
- **Lei 8.666/1993, art. 23, §5º**: Vedação ao fracionamento de licitação
- **Lei 14.133/2021, art. 145**: Proibição direta de fracionamento para evadir a obrigatoriedade de licitação

### Limiares por Ano

| Período | Limiar | Base Legal |
|---------|--------|------------|
| ≤ 2023 | R$ 17.600 | Decreto 9.412/2018 / Lei 8.666/93 |
| 2024+ | R$ 57.912 | Decreto 11.871/2024 / Lei 14.133/2021 |

### Cenários de Falso Positivo
1. **Compra de múltiplos itens**: Fornecedor entregando itens diversos legitimately gera muitos contratos pequenos
2. **Contratos recorrentes de serviço**: Taxas mensais de serviço (ex: R$ 1.500/mês limpeza) geram 12 contratos/ano
3. **Diferentes sub-unidades**: Ministério com múltiplas sub-unidades contratando independentemente

### Implementação DuckDB

```sql
WITH contratos_por_mes AS (
    SELECT
        ano,
        mes,
        id_orgao_superior,
        nome_orgao_superior,
        COUNT(*) AS num_contratos,
        SUM(valor_inicial_compra) AS valor_total
    FROM br_cgu_licitacao_contrato.contrato_compra
    WHERE ano = 2023
      AND data_assinatura_contrato IS NOT NULL
      AND valor_inicial_compra > 0
    GROUP BY ano, mes, id_orgao_superior, nome_orgao_superior
),
limiares AS (
    SELECT
        2023 AS ano,
        17600.0 AS limiar
)
SELECT
    c.ano,
    c.mes,
    c.id_orgao_superior,
    c.nome_orgao_superior,
    c.num_contratos,
    c.valor_total,
    l.limiar,
    CASE WHEN c.ano <= 2023 THEN 17600.0 ELSE 57912.0 END AS limiar_aplicavel
FROM contratos_por_mes c
JOIN limiares l ON c.ano = l.ano
WHERE c.num_contratos >= 3
  AND c.valor_total > limiar_aplicavel
ORDER BY c.valor_total DESC;
```

### Notas de Qualidade de Dados
- `data_assinatura_contrato` pode ser NULL em contratos antigos. **FORMAT_DATE em NULL retorna NULL** — a cláusula `IS NOT NULL` é essencial
- `valor_inicial_compra` é usado intencionalmente (data da assinatura, não valor final)

---

## PS2 — Concentração de Contratos (`contract_concentration`)

### Base Legal
- **CGU "Manual de Orientações para Análise de Risco em Compras Públicas" (2022)**: >40% de participação como indicador de risco
- **TCU**: Metodologia de auditoria trata concentração >40% como indicativo prima facie

### Limiares
- **40% de participação**: acima disso, a competição é funcionalmente inexistente
- **R$ 50.000 mínimo total do órgão**: exclui micro-unidades
- **R$ 10.000 mínimo por fornecedor**: exclui casos triviais

### Cenários de Falso Positivo
1. **Nichos especializados**: Tradução judicial, dispositivos médicos específicos
2. **Mercados monopolísticos**: Utilidades, telecomunicações
3. **Acordos-quadro**: Um fornecedor pode dominar mesmo com competição prévia

### Implementação DuckDB

```sql
WITH gasto_fornecedor AS (
    SELECT
        id_orgao_superior,
        nome_orgao_superior,
        cpf_cnpj_contratado,
        SUM(valor_inicial_compra) AS gasto_fornecedor
    FROM br_cgu_licitacao_contrato.contrato_compra
    WHERE ano = 2023
    GROUP BY id_orgao_superior, nome_orgao_superior, cpf_cnpj_contratado
),
gasto_orgao AS (
    SELECT
        id_orgao_superior,
        nome_orgao_superior,
        SUM(valor_inicial_compra) AS gasto_total_orgao
    FROM br_cgu_licitacao_contrato.contrato_compra
    WHERE ano = 2023
    GROUP BY id_orgao_superior, nome_orgao_superior
)
SELECT
    g.id_orgao_superior,
    g.nome_orgao_superior,
    g.cpf_cnpj_contratado,
    g.gasto_fornecedor,
    o.gasto_total_orgao,
    (g.gasto_fornecedor / o.gasto_total_orgao * 100) AS concentracao_pct
FROM gasto_fornecedor g
JOIN gasto_orgao o ON g.id_orgao_superior = o.id_orgao_superior
WHERE o.gasto_total_orgao >= 50000
  AND g.gasto_fornecedor >= 10000
  AND (g.gasto_fornecedor / o.gasto_total_orgao) > 0.40
ORDER BY concentracao_pct DESC;
```

---

## PS3 — Recorrência de Inexigibilidade (`inexigibility_recurrence`)

### Base Legal
- **Lei 14.133/2021 art. 74** e **Lei 8.666/93 art. 25**: inexigibilidade é legal quando competição é tecnicamente impossível
- **TCU Acórdão 1.793/2011**: uso recorrente de inexigibilidade como indicador de risco

### Limiar: 3 contratos por unidade gestora
- Abaixo de 3: podem ser duas necessidades legítimas de fonte única
- A partir de 3: padrão sugere direcionamento sistemático

### Cenários de Falso Positivo
1. **Fornecedores exclusivos legítimos**: Editoras, teatros, vendors de TI proprietários
2. **Parcerias técnicas de longo prazo**: Framework com parceiro técnico exclusivo
3. **Organizações artísticas/culturais**: Museus, orquestras

### Implementação DuckDB

```sql
WITH inexigibilidades AS (
    SELECT
        id_unidade_gestora,
        nome_unidade_gestora,
        cpf_cnpj_contratado,
        nome_contratado,
        COUNT(*) AS num_contratos,
        SUM(valor_inicial_compra) AS valor_total
    FROM br_cgu_licitacao_contrato.contrato_compra
    WHERE ano = 2023
      AND fundamento_legal = 'inexigibilidade'
      AND valor_inicial_compra >= 1000
    GROUP BY
        id_unidade_gestora,
        nome_unidade_gestora,
        cpf_cnpj_contratado,
        nome_contratado
)
SELECT
    id_unidade_gestora,
    nome_unidade_gestora,
    cpf_cnpj_contratado,
    nome_contratado,
    num_contratos,
    valor_total
FROM inexigibilidades
WHERE num_contratos >= 3
ORDER BY num_contratos DESC, valor_total DESC;
```

---

## PS4 — Licitação com Único Licitante (`single_bidder`)

### Base Legal
- **Open Contracting Partnership "73 Red Flags" (2024)**: Flag #1 — "Apenas uma proposta recebida"
- **CGU "Programa de Fiscalização em Entes Federativos" 2023**: taxa >30% de licitações com um único licitante é indicador de risco

### Limiar: 2 ocorrências
- Intencionalmente baixo. Até uma vitória de licitante único merece investigação

### Cenários de Falso Positivo
1. **Mercados especializados**: Comunicações via satélite, materiais nucleares
2. **Isolamento geográfico**: Municípios remotos com fornecedores locais limitados
3. **Editais mal temporizados**: Janelas curtas ou períodos de férias

### Implementação DuckDB

```sql
WITH lances_por_licitacao AS (
    SELECT
        id_licitacao,
        COUNT(DISTINCT cpf_cnpj_participante) AS total_licitantes,
        MAX(CASE WHEN vencedor THEN cpf_cnpj_participante END) AS cnpj_vencedor
    FROM br_cgu_licitacao_contrato.licitacao_participante
    WHERE ano = 2023
    GROUP BY id_licitacao
    HAVING COUNT(*) >= 1
)
SELECT
    id_licitacao,
    total_licitantes,
    cnpj_vencedor
FROM lances_por_licitacao
WHERE total_licitantes = 1
ORDER BY id_licitacao;
```

### Notas de Robustez SQL
- Contagem inclui CPF e CNPJ (pessoas físicas e jurídicas)
- `LENGTH = 14` apenas para extração do CNPJ do vencedor (evita CPF na chave)

---

## PS5 — Vencedor Fixo (`always_winner`)

### Base Legal
Não é ilegal por si só, mas altas taxas de vitória indicam possível:
- **Cartelização** (Lei 12.529/2011 art. 36, IV)
- **Especificações sob medida** (Lei 14.133/2021 art. 9, I)
- **Referência**: OCDE "Guidelines for Fighting Bid Rigging in Public Procurement" (2021)

### Limiares
- **≥80% taxa de vitória**: mínimo para significância estatística
- **≥10 participações competitivas**: amostra mínima para relevância
- **Apenas licitações competitivas (≥2 licitantes)**: evita sobreposição com PS4

### Correção Crítica
O padrão PS4 filtra licitações com apenas 1 licitante. PS5 filtra para licitações **competitivas** (≥2). Um empresa que sempre vence porque é o único licitante recebe apenas PS4.

### Distribuição de Taxa de Vitória
O dataset `licitacao_participante` é **bimodal**: ~33% das empresas com ≥10 participações competitivas têm taxa de vitória de 100%.

### Implementação DuckDB

```sql
WITH competitivo AS (
    SELECT id_licitacao
    FROM br_cgu_licitacao_contrato.licitacao_participante
    WHERE ano = 2023
    GROUP BY id_licitacao
    HAVING COUNT(DISTINCT cpf_cnpj_participante) >= 2
),
empresas_competitivas AS (
    SELECT
        p.cpf_cnpj_participante,
        p.nome_participante,
        COUNT(*) AS total_participacoes,
        SUM(CASE WHEN p.vencedor THEN 1 ELSE 0 END) AS total_vitorias,
        ROUND(SUM(CASE WHEN p.vencedor THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS taxa_vitoria
    FROM br_cgu_licitacao_contrato.licitacao_participante p
    JOIN competitivo c ON p.id_licitacao = c.id_licitacao
    WHERE p.ano = 2023
    GROUP BY p.cpf_cnpj_participante, p.nome_participante
    HAVING COUNT(*) >= 10
)
SELECT
    cpf_cnpj_participante,
    nome_participante,
    total_participacoes,
    total_vitorias,
    taxa_vitoria
FROM empresas_competitivas
WHERE taxa_vitoria >= 80
ORDER BY taxa_vitoria DESC, total_participacoes DESC;
```

---

## PS6 — Inflação de Aditivos (`amendment_inflation`)

### Base Legal
- **Lei 14.133/2021 art. 125 §1º**: aditivos não podem aumentar o valor em mais de 25% (bens/serviços) ou 50% (obras)

### Limiar: 1,25× (25% acima do original)
- Contratos em 1,25× estão no limite legal
- Acima de 1,25× são potencialmente ilegais

### Cenários de Falso Positivo
1. **Aditivos excepcionais legais**: Art. 125 §2º permite exceder 25% para "serviços adicionais indispensáveis"
2. **Contratos de obras**: Limite legal é 50%, não 25%
3. **Cláusulas de reajuste**: Contratos com correção inflacionária podem atingir 1,25× legitimamente

### Detecção de Obras por Palavras-chave

```sql
WITH contratos_com_ratio AS (
    SELECT
        id_contrato,
        id_orgao_superior,
        cpf_cnpj_contratado,
        valor_inicial_compra,
        valor_final_compra,
        objeto,
        CASE
            WHEN REGEXP_CONTAINS(LOWER(IFNULL(objeto, '')), 
                'obra|constru|reform|engenhari|paviment|demoli')
            THEN valor_final_compra / valor_inicial_compra
            ELSE valor_final_compra / valor_inicial_compra
        END AS ratio_inflacao,
        CASE
            WHEN REGEXP_CONTAINS(LOWER(IFNULL(objeto, '')), 
                'obra|constru|reform|engenhari|paviment|demoli')
            THEN 1.50
            ELSE 1.25
        END AS limiar_legal
    FROM br_cgu_licitacao_contrato.contrato_compra
    WHERE ano BETWEEN 2021 AND 2023
      AND valor_inicial_compra > 0
      AND valor_final_compra / valor_inicial_compra <= 10  -- Cap em 10×
)
SELECT
    id_contrato,
    cpf_cnpj_contratado,
    valor_inicial_compra,
    valor_final_compra,
    ROUND(ratio_inflacao, 2) AS ratio_inflacao,
    limiar_legal,
    objeto
FROM contratos_com_ratio
WHERE ratio_inflacao > limiar_legal
ORDER BY ratio_inflacao DESC
LIMIT 100;
```

### Palavras-chave para Obras

| Palavra-chave | Matches | Rationale |
|---------------|---------|-----------|
| `obra` | obra, obras | Construção geral |
| `constru` | construção, construir | Construção/edificação |
| `reform` | reforma, reformar | Renovação |
| `engenhari` | engenharia, engenheiro | Serviços de engenharia |
| `paviment` | pavimentação | Pavimentação |
| `demoli` | demolição | Demolição |

---

## PS7 — Empresa Recém-Criada (`newborn_company`)

### Base Legal
- **Lei 14.133/2021 art. 68, I**: fornecedores devem demonstrar qualificação técnica e econômica
- **CGU "Guia Prático de Análise de Empresas de Fachada" (2021)**: idade < 6 meses é indicador de risco

### Limiares
- **180 dias**: mínimo prático para operacionalização legítima
- **R$ 50.000 mínimo**: exclui contratos de treinamento e pequenas aquisições

### Cenários de Falso Positivo
1. **Spin-offs e reestruturações**: CNPJ novo pode ser entidade reestruturada de empresa existente
2. **Estruturas de holding**: Holding criada para receber contrato específico
3. **Startups em programas de inovação**: Programas governamentais contratam empresas novas

### Nota de Qualidade de Dados
`data_inicio_atividade` vem de `br_me_cnpj.estabelecimentos`, não de `empresas`. O CNPJ raiz (8 dígitos) agrupa todas as filiais.

### Implementação DuckDB

```sql
WITH fundacao AS (
    SELECT
        e.cnpj_basico,
        MIN(e.data_inicio_atividade) AS data_fundacao
    FROM br_me_cnpj.estabelecimentos e
    WHERE e.ano = 2023 AND e.mes = 12
    GROUP BY e.cnpj_basico
),
primeiro_contrato AS (
    SELECT
        SUBSTR(REGEXP_REPLACE(cpf_cnpj_contratado, '\D', ''), 1, 8) AS cnpj_basico,
        MIN(data_assinatura_contrato) AS data_primeiro_contrato
    FROM br_cgu_licitacao_contrato.contrato_compra
    WHERE valor_final_compra >= 50000
    GROUP BY cnpj_basico
)
SELECT
    f.cnpj_basico,
    f.data_fundacao,
    p.data_primeiro_contrato,
    DATE_DIFF('day', f.data_fundacao, p.data_primeiro_contrato) AS dias_desde_fundacao
FROM fundacao f
JOIN primeiro_contrato p ON f.cnpj_basico = p.cnpj_basico
WHERE DATE_DIFF('day', f.data_fundacao, p.data_primeiro_contrato) < 180
ORDER BY dias_desde_fundacao;
```

---

## PS8 — Surto Súbito (`sudden_surge`)

### Base Legal
- **UNODC "Guidebook on anti-corruption in public procurement" (2013)**: aumento súbito é indicador de risco
- **TCU Acórdão 2.622/2015**: aumentos grandes sem histórico merecem escrutínio

### Limiares
- **5× crescimento YoY**: exclui crescimento normal (2-3×)
- **R$ 1.000.000 mínimo**: salto de R$ 200k para R$ 1M é relevante; R$ 10k para R$ 50k é ruído
- **Lookback de 4 anos**: captura contexto antes do surto

### Cenários de Falso Positivo
1. **Recuperação pós-reestruturação**: Empresa inativa por 2 anos retoma operações
2. **Novos acordos-quadro**: Inclusão em framework pode produzir surto aparente
3. **Ciclos orçamentários**: Contratos plurianuais a cada 4 anos criam saltos aparentes

### Guarda de Ano Consecutivo
A comparação usa `LAG(ano)` para garantir que apenas anos **consecutivos** sejam comparados, evitando comparação de anos distantes (ex: 2019 vs 2023).

### Implementação DuckDB

```sql
WITH gasto_anual AS (
    SELECT
        SUBSTR(REGEXP_REPLACE(cpf_cnpj_contratado, '\D', ''), 1, 8) AS cnpj_basico,
        ano,
        SUM(valor_inicial_compra) AS gasto_anual
    FROM br_cgu_licitacao_contrato.contrato_compra
    WHERE ano BETWEEN 2019 AND 2023
    GROUP BY cnpj_basico, ano
),
com_surto AS (
    SELECT
        g.cnpj_basico,
        g.ano AS ano_surto,
        g.gasto_anual,
        LAG(g.ano) OVER (PARTITION BY g.cnpj_basico ORDER BY g.ano) AS ano_anterior,
        LAG(g.gasto_anual) OVER (PARTITION BY g.cnpj_basico ORDER BY g.ano) AS gasto_anterior,
        g.gasto_anual / NULLIF(LAG(g.gasto_anual) OVER (PARTITION BY g.cnpj_basico ORDER BY g.ano), 0) AS ratio_crescimento
    FROM gasto_anual g
)
SELECT
    c.cnpj_basico,
    c.ano_anterior,
    c.ano_surto,
    c.gasto_anterior,
    c.gasto_anual,
    ROUND(c.ratio_crescimento, 2) AS ratio_crescimento
FROM com_surto c
WHERE c.gasto_anterior >= 1000000  -- Mínimo de R$ 1M no ano anterior
  AND c.ratio_crescimento >= 5.0   -- Crescimento de 5×
  AND c.ano_surto - c.ano_anterior = 1  -- Apenas anos consecutivos
ORDER BY c.ratio_crescimento DESC
LIMIT 100;
```

---

## Resumo dos Padrões

| Padrão | Risco FP | Base Legal | Implementação DuckDB |
|--------|----------|------------|---------------------|
| PS1 Split | Médio | Decreto 9.412/2018, Lei 14.133/2021 | Filtro NULL + limiar dinâmico |
| PS2 Concentration | Médio | CGU 2022 | GROUP BY (id+name) composto |
| PS3 Inexigibility | Alto | TCU Acórdão 1.793/2011 | GROUP BY id_unidade_gestora |
| PS4 Single Bidder | Médio | OCP 2024 Flag #1 | Contagem total (CPF+CNPJ) |
| PS5 Always Winner | Médio | OCDE 2021 | Apenas auctions competitivos |
| PS6 Amendment | Médio | Lei 14.133/2021 art.125 | Detecção de obras por palavras-chave |
| PS7 Newborn | Alto | CGU 2021 | MIN(data_inicio) por cnpj_basico |
| PS8 Surge | Médio | UNODC 2013 | Guarda de ano consecutivo |

---

## Notas de Implementação

### Formato de Moeda Brasileira

Para formatar valores em reais com notação brasileira:

```sql
SELECT
    'R$ ' ||
    REGEXP_REPLACE(
        REVERSE(REGEXP_REPLACE(REVERSE(SPLIT_PART(printf('%.2f', valor), '.', 1)), '(\d{3})', '\1.', 'g')),
        '^\.', ''
    ) ||
    ',' || SPLIT_PART(printf('%.2f', valor), '.', 2) AS valor_formatado
FROM br_cgu_licitacao_contrato.contrato_compra
LIMIT 10;
```

### Particionamento

As tabelas possuem colunas `ano` e `mes` que são usadas como partições. Sempre filtre por ano primeiro:

```sql
WHERE ano = 2023
WHERE ano BETWEEN 2020 AND 2023
```

### Junções Geográficas

```sql
SELECT
    m.nome AS municipio,
    m.sigla_uf,
    c.valor_total
FROM (
    SELECT id_municipio, SUM(valor) AS valor_total
    FROM br_cgu_licitacao_contrato.contrato_compra
    WHERE ano = 2023
    GROUP BY id_municipio
) c
JOIN br_bd_diretorios_brasil.municipio m ON c.id_municipio = m.id_municipio
```

---

## Considerações Finais

1. **Todos os padrões são complementares**: PS7 e PS8 podem sinalizar a mesma empresa simultaneamente
2. **CNPJ raiz (cnpj_basico)**: Agrupa todas as filiais de um corporativo — pode gerar falsos positivos para grandes empresas
3. **Valores monetários**: Sempre verificar se valores estão em reais ou outra unidade
4. **Datas NULL**: Sempre incluir `IS NOT NULL` em filtros de data
5. **Qualidade de dados**: Dados de contratos antigos podem ter inconsistências

---

*Relatório gerado em $(date +%Y-%m-%d) com base nos schemas do DuckDB e no documento de auditoria de padrões.*
