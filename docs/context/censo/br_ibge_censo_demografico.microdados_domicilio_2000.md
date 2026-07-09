# br_ibge_censo_demografico.microdados_domicilio_2000

**Fonte**: `basedosdados-schema.json` + Documentação oficial do IBGE (Censo 2000)

Este arquivo contém os **microdados de domicílios** do Censo Demográfico 2000.

---

## Colunas Disponíveis

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_regiao` | VARCHAR | Código da região geográfica |
| `sigla_uf` | VARCHAR | Sigla da Unidade da Federação |
| `id_mesorregiao` | VARCHAR | Código da mesorregião |
| `id_microrregiao` | VARCHAR | Código da microrregião |
| `id_municipio` | VARCHAR | Código do município (IBGE 7 dígitos) |
| `id_distrito` | VARCHAR | Código do distrito |
| `id_subdistrito` | VARCHAR | Código do subdistrito |
| `id_regiao_metropolitana` | VARCHAR | Código da região metropolitana |
| `controle` | INTEGER | Código de controle do registro |
| `situacao_setor` | INTEGER | Código da situação do setor |
| `situacao_domicilio` | INTEGER | Código da situação do domicílio |
| `tipo_setor` | VARCHAR | Tipo do setor censitário |
| `peso_amostral` | DOUBLE | Peso amostral para expansão |

**Nota**: Este é um microdado, cada linha representa um domicílio individual.

---

## Fonte

Documentação completa disponível em:
- `/Volumes/EXTRA/bkps/Censos/Censo_Demografico_2000/Microdados/`
- `1_Documentacao_20170908.zip`
