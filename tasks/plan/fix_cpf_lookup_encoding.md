# fix_cpf_lookup_encoding.md — `main.cpf_lookup` corrompe todo `information_schema.columns`

## Achado (2026-09-10, efeito colateral de investigar `br_mjsp_ckan.infopen`)

`information_schema.columns` e `duckdb_columns()` falham com `Invalid Input
Error: Invalid unicode (byte sequence mismatch)` contra **qualquer** consulta
no `basedosdados.duckdb` — sem `WHERE` que resolva, porque essas funções
materializam o catálogo inteiro antes de filtrar. Isso não é sobre
`br_mjsp_ckan.infopen` (esse já foi corrigido, ver commit e nota em
`sync_mcp_schema.py`) — depois de corrigir infopen, o erro **continuou**.

Bisecção completa (script em `/tmp/find_bad2.py` no beelink, apagável):
`DESCRIBE` em cada uma das 1030 tabelas de `schemas.json` + as 7 views do
catálogo que não estão nele → **zero** falhas. A única `BASE TABLE` fora do
schema `main`-excluído-por-infra é `main.cpf_lookup` — e isolá-la confirma:
`SELECT column_name, data_type FROM duckdb_columns() WHERE table_name='cpf_lookup'`
reproduz o erro sozinha.

## O que é `main.cpf_lookup`

Criada em `tasks/done/sync_cpf.md` (✅, arquivado) via:
```sql
CREATE TABLE cpf_lookup AS
SELECT UPPER(nome_completo) AS nome_upper, SUBSTR(CPF, 4, 6) AS cpf_mid6, CPF AS cpf_completo
FROM read_parquet('/home/polo/rodado/pessoas.parquet');
```
**223.670.206 linhas** — nome completo + CPF de pessoas físicas, usada para
completar CPF mascarado em 15 tabelas do espelho. `DESCRIBE main.cpf_lookup`
funciona (nomes de coluna limpos: `nome_upper`, `cpf_mid6`, `cpf_completo` —
vieram do alias SQL, não do parquet de origem) e `SELECT * ... LIMIT 3`
também funciona nas linhas testadas. O problema não está nos nomes de
coluna — estranhamente semelhante ao caso do `infopen`, mas numa camada
diferente.

## Hipótese de causa (não confirmada)

`pessoas.parquet` (fonte externa, `/Volumes/EXTRA/bkps/Databases/pessoas.parquet`,
5.3GB, fora deste repo) provavelmente tem o mesmo problema que `infopen.parquet`
tinha: coluna de texto sem anotação UTF8 no schema Parquet, fazendo o
`read_parquet` do DuckDB tipar `nome_completo` como `BLOB` em vez de
`VARCHAR` — e `CAST`/função de string (`UPPER()`) sobre um `BLOB` com bytes
latin-1 não valida UTF-8 no `CREATE TABLE ... AS SELECT`, deixando o valor
inválido entrar no armazenamento nativo do DuckDB. Isso é diferente do bug
do `infopen`: lá era só metadado (nome de coluna); aqui, se a hipótese
estiver certa, é **conteúdo real de 223M linhas de PII** (nome de pessoa)
armazenado em formato nativo do DuckDB, não em parquet — não dá pra
corrigir com o mesmo patch Thrift-no-footer que resolveu o infopen (formato
de storage nativo do DuckDB é bem mais complexo e versionado; não há
ferramenta validada aqui pra editá-lo com segurança).

## Por que isto parou aqui, sem tentar corrigir

- **223 milhões de linhas de CPF + nome completo** — a tabela com PII em
  maior escala que apareceu nesta investigação.
- Não está documentada em nenhum lugar do `CLAUDE.md`/`docs/` do projeto —
  `main` é schema explicitamente excluído como infra em
  `build_metadata_catalog.py`'s `JUNK_SCHEMAS`, então `cpf_lookup` nunca
  apareceu em nenhum catálogo/contagem publicada.
- `deanonimizacao_geral.md` (arquivado, tema irmão) já registra **uma
  decisão de privacidade ainda em aberto** — este achado é mais uma peça do
  mesmo assunto sensível, não um bug isolado de encoding.
- Corrigir de verdade exigiria: (a) achar/confirmar o mesmo bug em
  `pessoas.parquet` (que pode nem estar mais em `~/rodado` — `sync_cpf.md`
  só documenta o `scp` original), (b) decidir se vale reprocessar 223M
  linhas de PII pra isso, e (c) `DROP`+recriar `cpf_lookup` do zero — um
  tipo de ação bem mais pesado e mais sensível do que patchear um footer de
  parquet de tabela pública.

## Opções, sem escolher nenhuma

1. **Deixar como está.** `information_schema.columns`/`duckdb_columns()`
   continuam quebrados pro banco inteiro, mas `DESCRIBE`/`SELECT` por
   tabela nomeada seguem funcionando normalmente — é o que todo o resto do
   projeto (`mcp_server.py`, `gera_schemas.py`) já usa, então o impacto
   prático fora deste achado é baixo.
2. **Corrigir os nomes** (se `nome_upper` tiver bytes inválidos): exigiria
   `CREATE TABLE cpf_lookup_fixed AS SELECT ...` com alguma função de
   normalização de encoding, testar numa cópia, comparar contagem/amostra,
   só então trocar.
3. **Se `pessoas.parquet` ainda estiver em beelink**, rodar o mesmo
   script de diagnóstico usado no infopen (`/tmp/thrift_fix.py`, adaptar
   pra achar bytes invalidos na COLUNA `nome_completo`, não só nos nomes)
   pra confirmar a hipótese antes de decidir qualquer coisa.

Nenhuma ação tomada sobre `cpf_lookup` além de diagnosticar e isolar a
causa — decisão de como (ou se) prosseguir fica para quem já tem contexto
de privacidade sobre este dado.
