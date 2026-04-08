# br_ibge_censo_demografico.microdados_domicilio_1991

**Fonte**: `basedosdados-schema.json` + Documentação oficial do IBGE (Censo 1991)

Este arquivo contém os **microdados de domicílios** do Censo Demográfico 1991.

---

## Colunas Disponíveis

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `sigla_uf` | VARCHAR | Sigla da Unidade da Federação |
| `id_municipio` | VARCHAR | Código do município (IBGE 7 dígitos) |
| `id_questionario` | VARCHAR | Identificador do questionário |
| `peso_amostral` | DOUBLE | Peso amostral para expansão |
| `v0109` | VARCHAR | Variável V0109 |
| `v1061` | VARCHAR | Variável V1061 |
| `v7003` | VARCHAR | Variável V7003 |
| `v0111` | INTEGER | Variável V0111 |
| `...` | ... | Mais 35 variáveis |

---

## Características do Censo 1991

- Primeiro censo brasileiro a utilizar amostragem sistemática
- Microdados disponíveis para domicílios e pessoas
- Dados com peso amostral para expansão

---

## Fonte

Documentação disponível em:
- `/Volumes/EXTRA/bkps/Censos/Censo_Demografico_1991/Microdados/`
