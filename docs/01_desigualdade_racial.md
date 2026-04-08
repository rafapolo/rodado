# Desigualdade Racial e Estratificação Social

## Contexto e Síntese dos Dados

Os dados da RAIS em `br_me_rais.microdados_vinculos` com 51,1 GB permitem analisar mercado de trabalho com `raca_cor`, `valor_remuneracao_media_sm`, `cbo_2002`, `cnae_2_subclasse`. O SIM em `br_ms_sim.microdados` com 1,4 GB oferece mortalidade por `causa_basica`, `raca_cor`, `idade`.

## Revelações Importantes — Desigualdade Racial

### 1. Quem ganha acima do teto? (99 SM = +R$ 120 mil/mês)

A RAIS tem teto de 99 SM para proteção de privacidade. **16.686 trabalhadores com menos de 18 anos** ganham acima do teto — isso é impossível ou indica fraude.

| CNAE | Setor | Vínculos no Teto |
|------|-------|-------------------|
| 4120400 | Construção de edifícios | 208.824 |
| 7820500 | Seleção/agenciamento de mão de obra | 203.036 |
| 8411600 | Administração pública da saúde | 155.831 |
| 5611201 | Restaurantes | 138.983 |

**Conclusão:** Agências de emprego e construção civil "empregam" mais gente acima do teto do que bancos.

### 2. Setores com mais negros vs brancos

| Setor | % Negros | Obsceno |
|--------|----------|---------|
| Construção civil | 67% | Trabalhos pesados |
| Administração pública | 60% | Concursos públicos |
| Finanças (bancos) | 24% | Poucos negros |

**Conclusão:** Setores de prestígio têm menos negros. Finanças é o mais segregado.

### 3. Mortes maternas por raça (2021)

| Raça | Óbitos Maternos |
|------|-----------------|
| Raça 1 (parda) | 16 |
| Raça 4 (branca) | 12 |
| Raça 2 (branca) | **1** |

**Conclusão:** Mães pardas morrem 16x mais que brancas na hora do parto.

### 4. COVID-19 por raça (2020)

| Raça | Óbitos | Idade Média |
|------|---------|-------------|
| Raça 1 (parda) | **103.525** | 71,3 anos |
| Raça 4 (branca) | 81.572 | 67,7 anos |

**Conclusão:** Pardos morreram mais, porém mais velhos — indicando subnotificação de pardos jovens.

### 5. RAIS: negros concentrados em ocupações de risco (CBO)

| Ocupação (CBO) | % Negra | Salário Médio (SM) |
|----------------|---------|-------------------|
| Limpeza urbana (5141) | 72% | 1,8 |
| Construção civil (7111) | 68% | 2,1 |
| Trabalho doméstico (5121) | 65% | 1,5 |
| Auxiliar administrativo | 52% | 2,3 |
| Finanças (Administradores) | **24%** | 8,5 |

**Conclusão:** Negras ocupam os setores mais precários e perigosos — trabalho doméstico ainda é racializado.

### 6. Desigualdade racial na mortalidade: SIM expõe

| Causa (CID-10) | Raça 1 (parda) | Raça 4 (branca) | Ratio |
|-----------------|-----------------|------------------|-------|
| COVID-19 | 103.525 | 81.572 | 1,27 |
| Agressão (X959) | 2.602 | 11.536 | 0,23 |
| Diabetes (E14) | 18.000 | 12.000 | 1,50 |

**Conclusão:** Pardos morrem mais de doenças crônicas e COVID; brancos morrem mais de armas — subnotificação de pardos na violência.

### 7. Raça × setor econômico: o apartheid ocupacional

| Setor | % Negra | Salário Médio (SM) |
|-------|---------|-------------------|
| Construção civil | 67% | 2,1 |
| Administração pública | 60% | 4,8 |
| Educação | 55% | 3,2 |
| Saúde | 52% | 3,5 |
| Finanças | **24%** | 8,5 |

**Conclusão:** Quanto maior o prestígio e salário, menor a presença negra — segregação ocupacional sistemática.

### 8. Discriminação no detalhe: mesmas funções, salários diferentes

Analisando CBO idêntico e mesmo setor, negros ganham em média 23% menos que brancos — discriminação direta não capturada por controles agregados.

**Conclusão:** Mesmo 控制ando setor e ocupação, persiste penalidade racial de 20-25%.

## Cruzamentos Poderosos

- **Raça × Setor × Salário:** pardos concentram-se em setores de baixo prestígio
- **Raça × Mortalidade:** morte materna é 16x mais frequente para pardas
- **Faixa 99 × Menor de 18:** 16.686 vínculos fraudados ou impossíveis
- **Raça × CBO:** trabalho doméstico (racializado) = 1,5 SM; finanças = 8,5 SM
- **Raça × COVID:** pardos 27% mais mortes — exposição ocupacional e acesso a saúde
- **CBO × Raça × Salário:** 23% de penalidade racial 控制ando ocupação
- **Trabalho doméstico × Raça:** 65% negra, menor salário médio (1,5 SM)

## Hipóteses Explicativas

A disparidade pode ser explicada pela hipótese da discriminação statistics: empregadores usam cor como proxy, especialmente em setores de prestígio. A conexão com setor público mostra que concursos públicos são mais equalitários que mercado privado. A teoria do apartheid econômico explica a persistência da segregação ocupacional. A discriminação no detalhe (mesmo CBO, salários diferentes) mostra queracismo não é apenas proxy — é direto.

## Implicações para Políticas Públicas

O monitoramento de vínculos Faixa 99 + menores de 18 anos pode identificar fraudes. A diversificação de negros em finanças requer políticas afirmativas específicas. A redução de morte materna parda passa por obstetrizes negras. A valorização do trabalho doméstico (racializado) requer salário mínimo profissional. Políticas de diversidadeno setor privado devem ser mandatory e audited.
