# Cobertura de geolocalização — CNPJ x CNEFE, por UF

Estabelecimentos ativos (Receita Federal, snapshot mensal mais recente) geolocalizados
por casamento exato de endereço (CEP + logradouro + número) com o Cadastro Nacional de
Endereços para Fins Estatísticos (CNEFE, Censo IBGE 2022). Sem geolocalização, o
estabelecimento não aparece no mapa — não há fallback por centroide de CEP.

| UF | Estab. ativos | Geolocalizados | % | Pontos (após dedup) | Tamanho (.bin.gz) |
|---|---:|---:|---:|---:|---:|
| AC | 53,167 | 33,535 | 63.1% | 24,477 | 0.16 MB |
| AL | 230,141 | 137,641 | 59.8% | 87,891 | 0.60 MB |
| AM | 270,623 | 150,142 | 55.5% | 89,126 | 0.63 MB |
| AP | 49,910 | 34,354 | 68.8% | 23,937 | 0.18 MB |
| BA | 1,244,878 | 758,160 | 60.9% | 473,310 | 3.49 MB |
| CE | 728,165 | 447,002 | 61.4% | 288,026 | 2.10 MB |
| DF | 458,771 | 0 | 0.0% | 0 | 0.00 MB ⚠️ sem cobertura no CNEFE |
| ES | 578,732 | 387,582 | 67.0% | 209,227 | 1.45 MB |
| GO | 996,789 | 385,134 | 38.6% | 187,432 | 1.35 MB |
| MA | 366,072 | 223,023 | 60.9% | 143,831 | 1.06 MB |
| MG | 2,811,522 | 2,091,490 | 74.4% | 1,321,729 | 9.71 MB |
| MS | 366,019 | 271,236 | 74.1% | 194,130 | 1.35 MB |
| MT | 541,952 | 279,342 | 51.5% | 178,186 | 1.30 MB |
| PA | 506,720 | 278,508 | 55.0% | 188,537 | 1.42 MB |
| PB | 338,273 | 222,103 | 65.7% | 140,243 | 0.99 MB |
| PE | 718,039 | 500,426 | 69.7% | 302,583 | 2.16 MB |
| PI | 233,325 | 120,814 | 51.8% | 84,812 | 0.62 MB |
| PR | 1,915,683 | 1,463,448 | 76.4% | 842,578 | 6.08 MB |
| RJ | 2,223,553 | 1,560,329 | 70.2% | 717,555 | 5.00 MB |
| RN | 300,876 | 223,645 | 74.3% | 148,333 | 1.06 MB |
| RO | 166,079 | 99,917 | 60.2% | 71,497 | 0.50 MB |
| RR | 47,806 | 33,616 | 70.3% | 23,254 | 0.15 MB |
| RS | 1,700,833 | 1,242,398 | 73.0% | 754,982 | 5.44 MB |
| SC | 1,449,102 | 1,057,164 | 73.0% | 554,330 | 3.97 MB |
| SE | 167,458 | 116,567 | 69.6% | 71,474 | 0.48 MB |
| SP | 8,223,982 | 5,952,125 | 72.4% | 3,327,945 | 23.91 MB |
| TO | 175,266 | 62,897 | 35.9% | 44,303 | 0.32 MB |
| **Brasil** | **26,863,736** | **18,132,598** | **67.5%** | **10,493,728** | **75.47 MB** |

⚠️ **DF**: 0 pontos — `br_ibge_censo_2022.cadastro_enderecos` não tem nenhuma linha para essa(s) UF(s) no mirror atual (gap na fonte/sync, não um bug de join). Essas UFs são omitidas de `meta.json` e não geram página.
