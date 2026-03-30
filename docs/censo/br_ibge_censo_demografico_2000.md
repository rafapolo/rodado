# br_ibge_censo_demografico — Census 2000 Variáveis Agregadas

**Fonte**: `basedosdados-schema.json` + Documentação oficial do IBGE (Microdados da Amostra + Resultados do Universo)

Este dataset contém os microdados e variáveis agregadas do **Censo Demográfico 2000** para os setores censitários brasileiros.

---

## Tabelas Disponíveis

### Microdados (Nível Individual)

| Tabela | Descrição |
|--------|-----------|
| `microdados_domicilio_2000` | Domicílios e suas características |
| `microdados_pessoa_2000` | Pessoas e suas características |

### Variáveis Agregadas por Setor Censitário

| Tabela | Descrição |
|--------|-----------|
| `setor_censitario_basico_2000` | Variáveis básicas (identificação geográfica) |
| `setor_censitario_*_2000` | Diversas variáveis demográficas |

---

## Principais Variáveis Geográficas

| Variável | Descrição |
|---|---|
| `V0102` | Unidade da Federação |
| `V1002` | Código da Mesorregião |
| `V1003` | Código da Microrregião |
| `V0103` | Código do Município |
| `V0104` | Código do Distrito |
| `V0105` | Código do Subdistrito |
| `V1001` | Região Geográfica |
| `V1004` | Região Metropolitana |
| `V1005` | Situação do Setor (Urbano/Rural) |
| `V1006` | Situação do Domicílio |
| `V1007` | Tipo do Setor |

---

## Situação do Setor (V1005)

| Código | Descrição |
|--------|-----------|
| 1 | Área urbanizada de vila ou cidade |
| 2 | Área não urbanizada de vila ou cidade |
| 3 | Área urbanizada isolada |
| 4 | Rural - extensão urbana |
| 5 | Rural - povoado |
| 6 | Rural - núcleo |
| 7 | Rural - outros aglomerados |
| 8 | Rural, exclusive aglomerados |

---

## Tipo de Setor (V1007)

| Código | Descrição |
|--------|-----------|
| 0 | Setor comum ou não especial |
| 1 | Setor especial de aglomerado subnormal |
| 2 | Setor especial de quartéis, bases militares, etc. |
| 3 | Setor especial de alojamento, acampamentos, etc. |

---

## Fonte

Documentação completa disponível em:
- `/Volumes/EXTRA/bkps/Censos/Censo_Demografico_2000/Microdados/1_Documentacao_20170908.zip`
