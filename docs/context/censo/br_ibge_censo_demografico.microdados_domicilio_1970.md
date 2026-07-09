# br_ibge_censo_demografico.microdados_domicilio_1970

**Fonte**: `basedosdados-schema.json` + Documentação oficial do IBGE (Censo 1970)

Este arquivo contém os **microdados de domicílios** do Censo Demográfico 1970.

---

## Colunas Disponíveis

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `sigla_uf` | VARCHAR | Sigla da Unidade da Federação |
| `id_municipio` | VARCHAR | Código do município (IBGE 7 dígitos) |
| `id_domicilio` | VARCHAR | Identificador do domicílio |
| `numero_familia` | INTEGER | Número da família |
| `v001` | VARCHAR | Variável V001 |
| `v002` | VARCHAR | Variável V002 |
| `v003` | VARCHAR | Variável V003 |
| `v004` | VARCHAR | Variável V004 |
| `...` | ... | Mais 18 variáveis |

---

## Características do Censo 1970

- Um dos censos mais antigos disponíveis em microdados
- Dados em formato legível (input format)
- Cobertura nacional completa

---

## Fonte

Documentação disponível em:
- `/Volumes/EXTRA/bkps/Censos/Censo_Demografico_1970/Microdados/`
