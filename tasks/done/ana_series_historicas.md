# done/ana_series_historicas.md — Série histórica ANA: zip único baixado e extraído

## Objetivo
Trazer para o beelink a série histórica completa das estações da ANA (vazão e cota), como
insumo para a análise de tendência de vazão no `todos-rios-brasil` — os "rios morrendo".

## O que foi resolvido (concluído em 2026-08-09)

### 1. Localizada a fonte de download único
A ANA publicou as séries históricas agregadas em um único repo do GitHub
(`anagovbr/hidro-dados-estacoes-convencionais`), criado originalmente como contingência ao
ataque cibernético de set/2023.

- **Atenção a um gotcha:** o HEAD do repo foi **esvaziado** pela própria ANA em dez/2025
  (commits "Delete fluviometricas directory" etc.). O zip de `refs/heads/main` sai com 0
  bytes. O **commit `b8b65b0`** ainda carrega tudo.

### 2. Download do zip (in alcance no beelink)
- Arquivo: `beelink:~/ana_zip/hidro_estacoes_convencionais_20230804.zip`
- Tamanho: **2,3 GB**, 31.134 arquivos (4,3 GB descomprimidos)
- `unzip -tqq` → **íntegro** (exit 0)
- Data do retrato dos dados: **04/08/2023** (de 2023-08→hoje ainda falta, ver task)

### 3. Extração (feita no beelink)
```bash
cd ~/ana_zip && unzip -q hidro_stacoes_convencionais_20230804.zip -d extraido
```
Em `~/ana_zip/extraido/hidro-dados-estacoes-convencionais-b8b65b0/`:

| Caminho | Conteúdo | Tamanho |
|---|---|---|
| `fluviometricas/csv/<código>/{est}_vazoes.csv` | séri de vazão | — |
| `fluviometricas/csv/<código>/{est}_cotas.csv` | séri de cota | — |
| `pluviometricas/mdb/<código>.zip` | precipitação (needs Access/MDB) | 1,1 GB |
| `Inventario_Estacoes_Hidrologicas_04-08-2023.csv` | inventário completo | 10 MB |

### 4. Formato dos CSVs (para o schema do ETL)
Uma linha por mês, `;` separado. Colunas de interesse por linha:
- `EstacaoCodigo; NivelConsistencia; Data (MM/YYYY); MediaDiaria; MetodoObtencaoVazoes; Maxima; Minima; Media; DiaMaxima; DiaMinima`
- Colunas `Vazao01..Vazao31` (cm³/s/dia) + status — quando se quiser série **diária**
- Média mensal = `Media`; o mesmo esqueleto para cotas (`Cota01..31`, `TipoMedicaoCotas`)

Contagem de conjuntos de séries disponíveis:
- **7.205 estações fluviométricas** com `vazoes.csv` + `cotas.csv`
- pluviométricas em zip-MDB por estação (ouside do 1º ETL)

### 5. Infra do beelink preparada
- Instalado `polars` 1.43.2 em `python3` do beelink:
  `python3 -m pip install --user --break-system-packages polars` (PEP 668, precisou do flag)

## Diagrama do pipeline (próx. passo — ver `tasks/ana_series_historicas.md`)
```
ana_zip/hidro...zip ──(extraíd)──> CSVs
        │
        ├── inventário ──> br_ana_telemetria/estacoes (completo)
        ├── vazoes/cotas mensais ──> series_vazao_mensal / series_cota_mensal
        │                            (join do 2023-08?→hoje via SOAP depois)
        └── (depois ETL diário + MDB pluvio)
```

## Fontes
- repo: https://github.com/anagovbr/hidro-dados-estacoes-convencionais (commit `b8b60b0`)
- notícia ANA de 2023-10-25 descrevendo o conteúdo da release