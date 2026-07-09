# br_ibge_censo_demografico.microdados_pessoa_2000

**Fonte**: `basedosdados-schema.json` + Documentação oficial do IBGE (Censo 2000)

Este arquivo contém os **microdados de pessoas** do Censo Demográfico 2000.

---

## Colunas Disponíveis

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `sigla_uf` | VARCHAR | Sigla da Unidade da Federação |
| `id_mesorregiao` | VARCHAR | Código da mesorregião |
| `id_microrregiao` | VARCHAR | Código da microrregião |
| `id_municipio` | VARCHAR | Código do município (IBGE 7 dígitos) |
| `id_distrito` | VARCHAR | Código do distrito |
| `id_subdistrito` | VARCHAR | Código do subdistrito |
| `id_regiao_metropolitana` | VARCHAR | Código da região metropolitana |
| `controle` | INTEGER | Código de controle do registro |
| `serie` | INTEGER | Série/Ano de escolaridade |
| `area_ponderacao` | INTEGER | Código da área de ponderação |
| `v1001` | VARCHAR | Variável V1001 (ver dicionário) |
| `v1005` | VARCHAR | Variável V1005 (ver dicionário) |
| `...` | ... | Mais 98 variáveis (v1001 a vXXXX) |

**Nota**: Este é um microdado, cada linha representa uma pessoa individual.

---

## Principais Variáveis (V-códigos)

Consulte o dicionário de variáveis para a descrição completa:
- `/Volumes/EXTRA/bkps/Censos/Censo_Demografico_2000/Microdados/1_Documentacao_20170908.zip`

---

## Fonte

Documentação completa disponível em:
- `/Volumes/EXTRA/bkps/Censos/Censo_Demografico_2000/Microdados/`
