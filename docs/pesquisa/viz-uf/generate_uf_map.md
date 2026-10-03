# Cobertura de geolocalização — CNPJ x CNEFE, por UF

Estabelecimentos ativos (Receita Federal, snapshot mensal mais recente) geolocalizados
por casamento exato de endereço (CEP + logradouro + número) com o Cadastro Nacional de
Endereços para Fins Estatísticos (CNEFE, Censo IBGE 2022). Sem geolocalização, o
estabelecimento não aparece no mapa — não há fallback por centroide de CEP.

| UF | Estab. ativos | Geolocalizados | % | Pontos (após dedup) | Tamanho (.bin.gz) |
|---|---:|---:|---:|---:|---:|
| AC | 53,167 | 33,527 | 63.1% | 24,471 | 0.16 MB |
| AL | 230,141 | 137,626 | 59.8% | 87,867 | 0.61 MB |
| AM | 270,623 | 150,133 | 55.5% | 89,118 | 0.63 MB |
| AP | 49,910 | 34,356 | 68.8% | 23,940 | 0.18 MB |
| BA | 1,244,878 | 758,146 | 60.9% | 473,289 | 3.45 MB |
| CE | 728,165 | 447,001 | 61.4% | 288,053 | 2.06 MB |
| DF | 458,771 | 0 | 0.0% | 0 | 0.00 MB ⚠️ sem cobertura no CNEFE |
| ES | 578,732 | 387,564 | 67.0% | 209,215 | 1.45 MB |
| GO | 996,789 | 385,145 | 38.6% | 187,444 | 1.36 MB |
| MA | 366,072 | 223,020 | 60.9% | 143,805 | 1.05 MB |
| MG | 2,811,522 | 2,091,476 | 74.4% | 1,321,696 | 9.67 MB |
| MS | 366,019 | 271,229 | 74.1% | 194,133 | 1.35 MB |
| MT | 541,952 | 279,345 | 51.5% | 178,201 | 1.29 MB |
| PA | 506,720 | 278,496 | 55.0% | 188,545 | 1.40 MB |
| PB | 338,273 | 222,137 | 65.7% | 140,260 | 0.99 MB |
| PE | 718,039 | 500,328 | 69.7% | 302,541 | 2.16 MB |
| PI | 233,325 | 120,820 | 51.8% | 84,869 | 0.61 MB |
| PR | 1,915,683 | 1,463,513 | 76.4% | 842,531 | 6.08 MB |
| RJ | 2,223,553 | 1,560,170 | 70.2% | 717,457 | 5.00 MB |
| RN | 300,876 | 223,643 | 74.3% | 148,338 | 1.05 MB |
| RO | 166,079 | 99,929 | 60.2% | 71,504 | 0.50 MB |
| RR | 47,806 | 33,618 | 70.3% | 23,257 | 0.16 MB |
| RS | 1,700,833 | 1,242,440 | 73.0% | 754,924 | 5.46 MB |
| SC | 1,449,102 | 1,057,091 | 72.9% | 554,311 | 3.97 MB |
| SE | 167,458 | 116,585 | 69.6% | 71,492 | 0.48 MB |
| SP | 8,223,982 | 5,952,172 | 72.4% | 3,327,873 | 23.88 MB |
| TO | 175,266 | 62,892 | 35.9% | 44,377 | 0.32 MB |
| **Brasil** | **26,863,736** | **18,132,402** | **67.5%** | **10,493,511** | **75.32 MB** |

⚠️ **DF**: 0 pontos — `br_ibge_censo_2022.cadastro_enderecos` não tem nenhuma linha para essa(s) UF(s) no mirror atual (gap na fonte/sync, não um bug de join). Essas UFs são omitidas de `meta.json` e não geram página.
