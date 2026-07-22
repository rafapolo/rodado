# Fecundidade, fronteira, terra indígena e religião — top 10 municípios (2022)

Municípios com mais nascimentos proporcionalmente à população (SINASC 2022,
residência da mãe, ÷ população Censo 2022). Achado: não é um fator só —
idade mediana baixa, % população indígena e localização na Amazônia Legal
(proxy de fronteira) puxam a taxa de forma independente e aditiva.

## Tabela

| Município | UF | Nasc./1.000 hab | Idade mediana | % indígena | Fronteira intl. | % Católica | % Evangélica | % sem religião |
|---|---|---|---|---|---|---|---|---|
| Uiramutã | RR | 37,24 | 15 | 96,9% | Sim (Guyana) | 66,6% | 21,0% | 0,3% |
| Alto Alegre | RR | 32,15 | 20 | 60,5% | Não | 29,3% | 20,7% | 23,5% |
| Normandia | RR | 31,89 | 17 | 89,2% | Sim (Guyana) | 53,2% | 35,0% | 3,9% |
| Amajari | RR | 31,28 | 19 | 70,4% | Não | 31,5% | 26,3% | 14,0% |
| Pacaraima | RR | 31,15 | 21 | 62,8% | Sim (Venezuela) | 35,5% | **40,5%** | 10,6% |
| Bonfim | RR | 30,96 | 21 | 46,6% | Sim (Guyana) | 51,5% | 32,8% | 4,0% |
| Santa Rosa do Purus | AC | 29,18 | 17 | 64,0% | Sim (Peru) | 31,1% | **47,7%** | 4,3% |
| Assis Brasil | AC | 29,05 | 25 | 14,9% | Sim (Peru/Bolívia) | 41,1% | **41,8%** | 13,9% |
| Campinápolis | MT | 28,20 | 22 | 55,2% | Não | 42,0% | 38,2% | 9,1% |
| São Gabriel da Cachoeira | AM | 28,19 | 22 | 93,3% | Sim (Colômbia/Venezuela) | 64,1% | 29,0% | 2,1% |
| **Brasil (média)** | — | ~12,6 | 35,4 | — | — | 56,7% | 26,9% | 9,3% |

Nota: `Amajari`/`Alto Alegre`/`Campinápolis` não ficam na linha de fronteira mas têm
o mesmo padrão de idade jovem — o fator comum real é composição etária jovem,
não fronteira em si (ver seção seguinte).

## Achados (ver conversa completa para os números de correlação)

- Correlação nasc./1.000 hab × % indígena: **0,393**. Correlação nasc./1.000 hab ×
  Amazônia Legal (proxy fronteira): **0,435**. Força parecida, efeitos independentes.
- Cruzando os dois fatores (município com pop ≥ 2.000, Brasil inteiro): baseline
  11,73 nasc./mil fora da Amazônia Legal com baixa % indígena → 23,35 quando os
  dois fatores se combinam (quase o dobro).
- Religião: 4 dos 10 municípios já têm Evangélica > Católica ou empatado
  (Pacaraima, Santa Rosa do Purus, Assis Brasil, Campinápolis) — bem acima do
  gap nacional de 30pp (56,7% Católica vs 26,9% Evangélica). Nos de maioria
  indígena mais isolada (Uiramutã, São Gabriel da Cachoeira) a Católica ainda
  domina com folga.

## Perguntas em aberto para pesquisar depois

1. **Avanço evangélico ao longo do tempo**: esses municípios estão ficando
   mais evangélicos? Precisa comparar com Censo 2010 (`br_ibge_censo_demografico`
   microdados, variável `v6121` = religião — dataset já mirrorado, cobre até 2010).
   `br_ibge_censo2022_religiao.populacao_religiao` só tem o corte de 2022.
2. **Colonização/invasão de terra segue ativa?** Nenhuma fonte no rodado ainda
   cobre isso diretamente. Candidatos a scraping: desmatamento dentro de TIs
   (MapBiomas/INPE PRODES, já parcialmente no rodado via `br_mapbiomas_estatisticas`
   e `br_inpe_prodes` — falta cruzar com polígono de `br_ibge_censo_2022.terra_indigena`),
   garimpo ilegal (FUNAI/IBAMA autos de infração — gap conhecido, ver
   `docs/notes/gaps_vs_mcp_brasil.md`), presença de missões evangélicas em TI.

## Fontes / reprodução

- `br_ms_sinasc.microdados` (nascimentos, ano=2022, `id_municipio_residencia`)
- `br_ibge_censo_2022.municipio` (população, idade_mediana, populacao_indigena)
- `br_bd_diretorios_brasil.municipio` (nomes, `amazonia_legal` — usado como proxy
  de fronteira; não existe flag exata de "faixa de fronteira" no rodado ainda)
- `br_ibge_censo2022_religiao.populacao_religiao` (scraper novo, `scripts/scrap/ibge_censo2022_religiao.py`,
  fonte SIDRA tabela 9537, não é view do BigQuery — só `read_parquet` direto)
