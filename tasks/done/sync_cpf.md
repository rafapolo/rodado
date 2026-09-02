# sync_cpf.md — Completar CPFs mascarados com pessoas.parquet

## Objetivo
Completar CPFs mascarados em 15 tabelas no beelink usando `pessoas.parquet`. Atualizar **apenas** os campos de CPF — nada mais é alterado.

## Dados de origem
- `/Volumes/EXTRA/bkps/Databases/pessoas.parquet` — 223M linhas, 5.3GB
  - Schema: CPF (varchar), nome_completo (varchar), genero (varchar), data_nascimento (date)

## Tabelas alvo (15 tabelas, 3 formatos de máscara)

### Formato A — `***.XXX.XXX-**` (com pontuação)

| # | Schema | Tabela | Coluna CPF | Coluna Nome |
|---|--------|--------|------------|-------------|
| 1 | br_cgu_servidores_executivo_federal | observacoes | cpf | nome |
| 2 | br_cgu_servidores_executivo_federal | afastamentos | cpf | nome |
| 3 | br_cgu_servidores_executivo_federal | cadastro_reserva_reforma_militares | cpf | nome |
| 4 | br_cgu_servidores_executivo_federal | cadastro_pensionistas | cpf | nome |
| 5 | br_cgu_servidores_executivo_federal | cadastro_aposentados | cpf | nome |
| 6 | br_cgu_servidores_executivo_federal | remuneracao | cpf | nome |
| 7 | br_cgu_servidores_executivo_federal | cadastro_servidores | cpf | nome |
| 8 | br_cgu_beneficios_cidadao | novo_bolsa_familia | cpf_favorecido | nome_favorecido |
| 9 | br_cgu_beneficios_cidadao | bpc | cpf_favorecido, cpf_representante | nome_favorecido, nome_representante |
| 10 | br_cgu_beneficios_cidadao | auxilio_emergencial | cpf_beneficiario, cpf_responsavel | nome_beneficiario, nome_responsavel |
| 11 | br_cgu_beneficios_cidadao | auxilio_brasil | cpf_favorecido | nome_favorecido |
| 12 | br_cgu_beneficios_cidadao | bolsa_familia_pagamento | cpf_favorecido | nome_favorecido |

### Formato B — `***XXXXXX**` (sem pontuação)

| # | Schema | Tabela | Coluna CPF | Coluna Nome |
|---|--------|--------|------------|-------------|
| 13 | br_me_cnpj | socios | cpf_representante_legal | nome_representante_legal |
| 14 | br_me_cnpj | socios | documento (tipo=2) | nome |

## Estratégia de match
1. Busca por `UPPER(nome)` → se único, match direto
2. Se duplicata, usa `SUBSTR(CPF, 4, 6)` (6 dígitos visíveis) para desambiguar
3. Pessoas sem correspondência mantêm o CPF mascarado (não é erro)

## Passos

### Passo 0 — Transferir dados
```bash
scp /Volumes/EXTRA/bkps/Databases/pessoas.parquet beelink:~/rodado/
scp docs/context/basedosdados-schema.json beelink:~/rodado/docs/context/
scp docs/context/schema_compact.txt beelink:~/rodado/docs/context/
```

### Passo 1 — Criar lookup indexado
```sql
CREATE TABLE cpf_lookup AS
SELECT UPPER(nome_completo) AS nome_upper, SUBSTR(CPF, 4, 6) AS cpf_mid6, CPF AS cpf_completo
FROM read_parquet('/home/polo/rodado/pessoas.parquet');
CREATE INDEX idx_lookup_nome ON cpf_lookup(nome_upper);
CREATE INDEX idx_lookup_mid6 ON cpf_lookup(cpf_mid6);
```

### Passo 2 — Enriquecer cada tabela
Para cada tabela: ler parquet local → JOIN com lookup → substituir CPF mascarado → escrever enriched → mover para substituir original.

### Passo 3 — Atualizar views para parquet local

### Passo 4 — Validação e benchmark
