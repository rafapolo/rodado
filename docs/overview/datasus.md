# DATASUS — Fonte Primária de Dados de Saúde

O [DATASUS](https://datasus.saude.gov.br/) é o departamento de informática do SUS que
disponibiliza os dados brutos dos sistemas nacionais de saúde via FTP público em
`ftp://ftp.datasus.gov.br/dissemin/publicos/`.

Este documento mapeia o que existe no FTP, compara com o que já está no mirror da
Base dos Dados, e quantifica o esforço de um possível ETL direto.

## Visão Geral do FTP

Formato predominante: **DBC** (DBF comprimido proprietário do DATASUS) — arquivos
compactados anuais/mensais por UF. Também há dados abertos em CSV/JSON/XML/PARQUET
em `Dados_Abertos/`.

**Tamanho total estimado: ~1.230 GB** (1,2 TB)

## Sistemas no FTP

### JÁ cobertos pelo mirror da Base dos Dados

Estes datasets já existem (parcial ou totalmente) no BD. O FTP tem o histórico
completo e dados mais brutos; o BD entrega em Parquet com schema padronizado.

| Sistema | Tamanho FTP | Tamanho BD | Descrição |
|---------|-------------|------------|-----------|
| **SIHSUS** | 414 GB | 32 GB | Internações hospitalares (AIH). FTP tem série histórica completa desde 1992; BD tem subconjunto (~7,6 GB AIH + 24 GB serviços prof.) |
| **SIASUS** | 400 GB | 46 GB | Produção ambulatorial (PA). FTP desde 1994; BD tem ~45 GB de produção ambulatorial |
| **CNES** | 49 GB | 24 GB | Cadastro Nacional de Estabelecimentos de Saúde. Dados detalhados por competência: PF (profissional) 42 GB, ST 3 GB, RC 1,5 GB, etc. |
| **PNI** | 20 GB | ? | Programa Nacional de Imunizações. BD tem `br_ms_imunizacoes` (escopo menor?) |
| **SINASC** | 6,4 GB | 1,4 GB | Nascidos vivos. FTP desde 1994; BD tem 1,4 GB |
| **SIM** | 5,7 GB | 872 MB | Mortalidade. FTP desde 1996 (CID9 + CID10); BD tem 872 MB |
| **SINAN (DBC)** | 3,2 GB | 616 MB | Doenças de notificação compulsória. FTP em DBC bruto por agravo |
| **ANS** | ~0 | 8,3 GB | Diretório vazio no FTP — dados da ANS migraram para portal próprio. BD já tem `br_ans_beneficiario` |

### NÃO cobertos pelo mirror da Base dos Dados

Candidatos prioritários para ETL direto do FTP:

| Sistema | Tamanho | Descrição | Observação |
|---------|---------|-----------|------------|
| **SISCAN** | 52 GB | Rastreamento de câncer: SISCAN (49,7 GB), SISCOLO (2,4 GB), SISMAMA (0,3 GB) | **Maior lacuna**. Dados de preventivo de colo de útero e mamografia |
| **CIHA** | 5,3 GB | Comunicação de Internação Hospitalar (complementar à AIH) | Dados mais detalhados que o SIH |
| **Dados_Abertos/SINAN** | vários GB | SINAN em CSV/JSON/XML/PARQUET por agravo (~37 agravos: dengue, chikungunya, sífilis, hepatite, zika, tuberculose, etc.) | Já em formato aberto — ETL mais simples |
| **CIH** | 0,17 GB | CIH antigo (2008-2010) | Histórico |
| **SISPRENATAL** | 0,22 GB | Pré-natal | Pequeno, fácil |
| **painel_oncologia** | 0,18 GB | Painel oncológico | Pequeno, fácil |
| **PCE** | 0,01 GB | Programa de Controle de Epidemias | Descontinuado? |
| **CMD** | 0,04 GB | Doenças crônicas | |
| **RESP** | < 0,01 GB | Doenças respiratórias | |
| **ESUSNOTIFICA** | < 0,01 GB | Notificações e-SUS | |

### Dados_Abertos (272 GB)

Pasta com dados já convertidos para formatos abertos:

| Subpasta | Tamanho | Conteúdo |
|----------|---------|----------|
| `BackUp_Ducks_SIASUS_PA` | 230 GB | Dump DuckDB de produção ambulatorial (APACs 26 GB incluso) |
| `APAC_SIA` | 7,7 GB | APACs em formato aberto |
| `SINAN/` | — | 37 agravos em CSV/JSON/XML + alguns em Parquet |

### Utilitários / Outros

| Item | Descrição |
|------|-----------|
| **TABWIN / TABNET / TABDOS** | Aplicativos TabWin, TabNet, TabDOS para tabulação (programas legados Windows, ~20 MB total) |
| **IBGE** | População (150 MB), projeções populacionais (86 MB), censo (11 MB) — dados auxiliares |
| **EXTR ESP** | Arquivo tiny de extrato especial |

## Comparação BD vs FTP Direto

### Vantagens do BD (status quo)
- Dados em **Parquet** (colunar, comprimido, consultável via DuckDB)
- Schema padronizado e documentado
- Junções entre datasets já mapeadas (`docs/context/join_keys.md`)
- Particionado por ano/mês/UF

### Vantagens do FTP direto
- **Dados mais frescos** (BD tem defasagem de meses)
- **Série histórica completa** (BD às vezes só tem alguns anos)
- **Sistemas inteiros faltando** (SISCAN, CIHA, SISPRENATAL)
- Sem dependência do pipeline BigQuery → GCS → S3

### Desvantagens do FTP
- Formato **DBC** (precisa de conversão: `dbc2parquet` ou similar)
- Arquivos separados por UF/ano/mês — precisa de lógica de merge
- Sem schema documentado (precisa extrair do DBF header)
- Dados_Abertos/SINAN já está em CSV/JSON/XML mas sem schema padronizado

## ETL Futuro — Rascunho

```bash
# 1. Baixar DBCs de um sistema
lftp -c "open ftp://ftp.datasus.gov.br; mirror /dissemin/publicos/SISCAN ./raw/SISCAN"

# 2. Converter DBC → Parquet (ferramentas existentes)
#    - https://github.com/1papaya/dbc2parquet
#    - https://github.com/JoaoCarats/pydbc (Python)
#    - https://github.com/ppoisot/dbf2parquet

# 3. Organizar por dataset/tabela no formato BD
#    raw/SISCAN/SISCAN/ -> data/SISCAN/  (particionado por ano)

# 4. Criar views no DuckDB (similar a prepara_db.py)
```

### Prioridade sugerida

1. **SISCAN** (52 GB) — maior impacto, sem cobertura na BD
2. **CIHA** (5,3 GB) — complementar ao SIH
3. **Dados_Abertos/SINAN** (vários GB, já em CSV) — baixo esforço
4. **SISPRENATAL** + **painel_oncologia** (< 0,5 GB) — triviais

O resto (~1.100 GB) tem sobreposição significativa com o BD e só valeria a pena se
houver necessidade de dados mais frescos ou séries históricas completas que o BD não
cobre.
