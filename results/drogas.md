# Relatório: Dados sobre Drogas no Base dos Dados

Este relatório reúne informações sobre uso de drogas extraídas de todas as tabelas disponíveis no mirror do Base dos Dados (beelink). As fontes cobrem **atendimento psicossocial (SIA/SUS)**, **ocorrências criminais (RJ)** e **violência escolar (Pesquisa ABSP)**.

---

## 1. Atendimentos Psicossociais — `br_ms_sia.psicossocial` (2013–2025)

Registros ambulatoriais de alto custo (APAC) com campo `tipo_droga` que informa a(s) substância(s) envolvida(s):

| Droga(s) | Atendimentos | % com info |
|---|---|---|
| **Álcool** (sozinho) | 12.022.817 | 36,7% |
| **Outras drogas** (sozinho) | 8.239.209 | 25,1% |
| **Álcool + Outras** | 5.078.804 | 15,5% |
| **Álcool + Crack + Outras** | 4.357.840 | 13,3% |
| **Crack** (sozinho) | 1.041.813 | 3,2% |
| **Álcool + Crack** | 1.000.992 | 3,1% |
| **Crack + Outras** | 975.566 | 3,0% |
| Ignorado | 65.801 | 0,2% |
| **Total c/ informação** | **32.796.285** | **100%** |

- **Total de atendimentos (2013–2025):** 138.059.411
- **23,8%** têm informação sobre tipo de droga
- **Álcool** aparece em **68,6%** dos registros com droga informada
- **Crack** aparece em **22,5%**
- **Outras drogas** aparece em **56,9%**
- Atendimentos cresceram de ~6,7M (2013) para ~16,4M (2023), com o campo `tipo_droga` preenchido passando de 125 mil para 3,7M registros/ano

### Evolução por ano

| Ano | Total | c/ droga | Álcool | Crack | Outras |
|-----|-------|----------|--------|-------|--------|
| 2013 | 6.690.932 | 125.600 | 93.455 | 34.964 | 57.835 |
| 2014 | 7.974.315 | 1.688.555 | 1.197.014 | 386.363 | 797.249 |
| 2015 | 9.091.689 | 2.545.661 | 1.861.461 | 616.946 | 1.230.899 |
| 2016 | 9.661.111 | 2.643.085 | 1.916.313 | 598.640 | 1.337.718 |
| 2017 | 10.730.298 | 3.008.322 | 2.111.400 | 628.282 | 1.569.907 |
| 2018 | 12.259.259 | 3.389.093 | 2.378.568 | 775.301 | 1.814.768 |
| 2019 | 14.261.000 | 3.754.767 | 2.663.949 | 848.376 | 2.037.949 |
| 2020 | 873.113 | 226.800 | 158.528 | 49.854 | 133.917 |
| 2021 | 11.761.278 | 3.048.187 | 2.089.668 | 702.390 | 1.815.747 |
| 2022 | 13.354.137 | 3.076.896 | 2.057.937 | 667.176 | 1.883.660 |
| 2023 | 16.358.186 | 3.682.727 | 2.440.723 | 816.461 | 2.296.118 |
| 2024 | 15.513.334 | 3.610.098 | 2.265.983 | 819.626 | 2.379.850 |
| 2025 | 9.521.525 | 1.996.194 | 1.238.890 | 431.832 | 1.309.238 |

> Nota: 2020 com dados parciais (possível quebra na série). 2025 parcial (até meados do ano).

---

## 2. Ocorrências Criminais — RJ (`br_rj_isp_estatisticas_seguranca.evolucao_mensal_uf`)

Registros policiais do estado do RJ (série histórica 1991–2026):

| Tipo | Total (série histórica) |
|------|------------------------|
| **Posse de drogas** | 163.405 |
| **Tráfico de drogas** | 193.272 |
| **Apreensão de drogas** | 515.497 |
| Apreensão de drogas sem autor | 47.324 |
| **Total ocorrências drogas** | **919.498** |

### Últimos anos (RJ):

| Ano | Posse | Tráfico | Apreensão |
|-----|-------|---------|-----------|
| 2021 | 9.559 | 10.478 | 21.682 |
| 2022 | 9.308 | 9.738 | 20.641 |
| 2023 | 11.161 | 9.582 | 22.522 |
| 2024 | 10.557 | 10.752 | 23.930 |
| 2025 | 9.276 | 12.031 | 25.830 |
| 2026 | 1.588 | 2.050 | 4.181 |

> Nota: dados de 2026 são parciais (até ~julho).

---

## 3. Violência Escolar — `br_fbsp_absp.violencia_escola` (2021)

Pesquisa nacional com escolas sobre violência, respondida por UF:

| Tema | Nunca | Poucas vezes | Várias vezes | Sem resposta |
|------|-------|-------------|-------------|-------------|
| Permanência de pessoas sob efeito de **drogas** | 59.560 | 4.013 | 183 | 10.783 |
| Permanência de pessoas sob efeito de **álcool** | 60.587 | 3.106 | 79 | 10.767 |
| **Tráfico de drogas** | 60.570 | 2.930 | 293 | 10.746 |

- **183 escolas** relataram várias ocorrências de pessoas sob efeito de drogas
- **293 escolas** relataram tráfico de drogas várias vezes
- RJ, SP e PE lideram em frequência de tráfico e presença de drogas nas escolas

---

## 4. Classificação CID-10 (`br_bd_diretorios_brasil.cid_10`)

- **860** subcategorias CID-10 são classificadas como causa de overdose
- Capítulo F1* — Transtornos mentais e comportamentais devidos ao uso de substâncias:
  - **F10**: Álcool
  - **F11**: Opiáceos
  - **F12**: Cannabinoides
  - **F13**: Sedativos/hipnóticos
  - **F14**: Cocaína
  - **F15**: Outros estimulantes (cafeína)
  - **F16**: Alucinógenos
  - **F17**: Fumo
  - **F18**: Solventes voláteis
  - **F19**: Múltiplas drogas/outras substâncias psicoativas

---

## 5. Notas e Observações

- A tabela `br_ms_sinan.microdados_violencia` **não está disponível** no beelink. A coluna `tipo_droga` pertence a `br_ms_sia.psicossocial`.
- O campo `tipo_droga` usa códigos de letras (A=álcool, C=crack, O=outras); registros com códigos inconsistentes foram normalizados.
- Dados criminais existem **apenas para o estado do RJ** (Instituto de Segurança Pública — ISP).
- Views obsoletas no DuckDB que apontam para `s3://baseldosdados` (bucket extinto) — todas as queries usam `read_parquet()` diretamente sobre os arquivos locais do beelink.
- 2020 apresentou queda atípica nos registros de psicossocial, possivelmente relacionada à pandemia de COVID-19.
