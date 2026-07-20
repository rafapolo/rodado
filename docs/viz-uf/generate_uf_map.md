# Cobertura de geolocalização — CNPJ x CNEFE, por UF

Estabelecimentos ativos (Receita Federal, snapshot mensal mais recente) geolocalizados
por casamento exato de endereço (CEP + logradouro + número) com o Cadastro Nacional de
Endereços para Fins Estatísticos (CNEFE, Censo IBGE 2022). Sem geolocalização, o
estabelecimento não aparece no mapa — não há fallback por centroide de CEP.

| UF | Estab. ativos | Geolocalizados | % | Pontos (após dedup) | Tamanho (.bin.gz) |
|---|---:|---:|---:|---:|---:|
| AC | 53,167 | 16,056 | 30.2% | 12,526 | 0.08 MB |
| AL | 230,141 | 54,804 | 23.8% | 37,492 | 0.25 MB |
| AM | 270,623 | 75,998 | 28.1% | 47,412 | 0.33 MB |
| AP | 49,910 | 19,380 | 38.8% | 13,885 | 0.10 MB |
| BA | 1,244,878 | 353,825 | 28.4% | 225,204 | 1.61 MB |
| CE | 728,165 | 225,413 | 31.0% | 150,823 | 1.07 MB |
| DF | 458,771 | 0 | 0.0% | 0 | 0.00 MB ⚠️ sem cobertura no CNEFE |
| ES | 578,732 | 223,026 | 38.5% | 124,433 | 0.84 MB |
| GO | 996,789 | 176,081 | 17.7% | 94,367 | 0.67 MB |
| MA | 366,072 | 100,501 | 27.5% | 72,306 | 0.52 MB |
| MG | 2,811,522 | 1,349,892 | 48.0% | 877,879 | 6.29 MB |
| MS | 366,019 | 177,130 | 48.4% | 130,507 | 0.89 MB |
| MT | 541,952 | 134,570 | 24.8% | 91,776 | 0.66 MB |
| PA | 506,720 | 136,537 | 26.9% | 97,995 | 0.72 MB |
| PB | 338,273 | 107,628 | 31.8% | 71,641 | 0.50 MB |
| PE | 718,039 | 248,219 | 34.6% | 156,406 | 1.09 MB |
| PI | 233,325 | 50,679 | 21.7% | 38,235 | 0.27 MB |
| PR | 1,915,683 | 913,307 | 47.7% | 544,113 | 3.85 MB |
| RJ | 2,223,553 | 924,367 | 41.6% | 435,250 | 2.97 MB |
| RN | 300,876 | 117,777 | 39.1% | 80,884 | 0.57 MB |
| RO | 166,079 | 59,865 | 36.0% | 45,480 | 0.31 MB |
| RR | 47,806 | 19,885 | 41.6% | 14,511 | 0.09 MB |
| RS | 1,700,833 | 766,081 | 45.0% | 471,821 | 3.31 MB |
| SC | 1,449,102 | 645,168 | 44.5% | 347,295 | 2.43 MB |
| SE | 167,458 | 55,492 | 33.1% | 34,613 | 0.23 MB |
| SP | 8,223,982 | 3,907,052 | 47.5% | 2,279,123 | 15.86 MB |
| TO | 175,266 | 28,986 | 16.5% | 21,854 | 0.15 MB |
| **Brasil** | **26,863,736** | **10,887,719** | **40.5%** | **6,517,831** | **45.65 MB** |

⚠️ **DF**: 0 pontos — `br_ibge_censo_2022.cadastro_enderecos` não tem nenhuma linha para essa UF no mirror atual (gap na fonte/sync, não um bug de join). DF é omitido de `meta.json` e não gera página.
