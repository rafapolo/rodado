# ETLs importados do br-acc

Abaixo as 8 fontes priorizadas (Tier 1) que não existiam no nosso mirror e foram
adaptadas do repositório [gliunextage/br-acc](https://github.com/gliunextage/br-acc).

Cada scraper baixa dados brutos da fonte original e gera Parquet no beelink em
`~/baseldosdados-data/<dataset>/<tabela>/`.

## Status

| # | Dataset | Fonte original | Script | Status (testado) | Tam. aprox. |
|---|---------|---------------|--------|-----------------|-------------|
| 1 | `br_imprensa_nacional_dou.atos` | Imprensa Nacional (XML) | `scrapers/fetch_dou.py` | 🔴 inlabs.in.gov.br agora requer registro — URL returns 403 | ~50 GB |
| 2 | `br_bndes_desembolsos.operacoes_nao_automaticas` | BNDES Dados Abertos (CSV) | `scrapers/fetch_bndes.py` | ✅ 23.591 linhas, ~13s | ~20 MB |
| 3 | `br_ibama_areas_embargadas.termos_embargo` | IBAMA Dados Abertos (CSV/ZIP) | `scrapers/fetch_ibama.py` | 🔴 servidor dadosabertos.ibama.gov.br retornando 500 | ~50 MB |
| 4 | `br_socios_brasil.holdings` | Brasil.IO (CSV) | `scrapers/fetch_holdings.py` | ✅ 507.550 linhas | ~200 MB |
| 5 | `br_pncp_contratacoes.contratos` | PNCP API (JSON) | `scrapers/fetch_pncp.py` | ⚠️ funciona, mas API rate-limitada (frequentes 429) | ~10 GB |
| 6 | `br_senado_ceaps.despesas` | Senado Federal (CSV) | `scrapers/fetch_senado.py` | ✅ 365.851 linhas (2008–2025) | ~500 MB |
| 7 | `br_tcu_sancoes.sancionados` | OpenSanctions (CSV) | `scrapers/fetch_tcu.py` | ✅ 652 linhas (inabilitados + inidoneos) | ~10 MB |
| 8 | `br_transferegov_emendas.emendas_parlamentares` | Portal da Transparência (CSV) | `scrapers/fetch_transferegov.py` | ✅ 94.168+813.799+84.603 linhas | ~5 GB |

## URLs descobertas / alteradas durante implementação

| Dataset | URL | Observação |
|---------|-----|------------|
| Senado (≤2021) | `https://www.senado.leg.br/transparencia/LAI/verba/{year}.csv` | CSV com header extra ("ULTIMA ATUALIZACAO") |
| Senado (≥2022) | `https://adm.senado.gov.br/adm-dadosabertos/api/v1/senadores/despesas_ceaps/{year}/csv` | Swagger API sem auth, retorna CSV |
| TCU inabilitados | `https://data.opensanctions.org/artifacts/br_tcu_disqualified/{version}/targets.simple.csv` | Versão resolvida dinamicamente via `datasets/latest/index.json` |
| TCU inidoneos | `https://data.opensanctions.org/artifacts/br_tcu_debarred/{version}/targets.simple.csv` | Mesmo esquema |
| IBAMA (ZIP) | `https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/termo_embargo/termo_embargo_csv.zip` | CKAN dataset, servidor atualmente 500 |
| IBAMA (CSV alt) | `https://dadosabertos.ibama.gov.br/dados/SIFISC/termo_embargo/termo_embargo/termo_embargo.csv` | Também 500 |

## Como usar

```bash
# Rodar todos os 8 scrapers
./scripts/scrapers/run_all.py

# Rodar um específico
./scripts/scrapers/fetch_bndes.py

# Rodar com saída local (sem rsync)
./scripts/scrapers/fetch_bndes.py --local-dir ./data/scraped

# Configurar destino (variáveis de ambiente)
export BEELINK_HOST=beelink
export BEELINK_PATH=~/baseldosdados-data
```

## Arquitetura

Cada scraper:
1. **Download** do dado bruto da fonte oficial (CSV, JSON, XML)
2. **Transform** em DataFrame limpo
3. **Write** Parquet com pyarrow
4. **Rsync** para o beelink via SSH

O `_utils.py` compartilha: `download_file()`, `write_parquet()`, `rsync_to_beelink()`.
