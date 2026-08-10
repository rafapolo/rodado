# Gaps vs mcp-brasil

Comparação entre o rodado (mirror de dados públicos + scrapers) e o [mcp-brasil](https://github.com/Mcp-Brasil/mcp-brasil) (533 tools, 70 fontes).

## Paradigma

| | rodado | mcp-brasil |
|---|--------|-----------|
| Modelo | Pre-computed Parquet mirror de BigQuery | Live API passthrough |
| Atualização | Batch (síncrono do beelink) | Fresh a cada call |
| Performance | Rápido (S3 collocated) | Limitado pela API upstream |
| Query | SQL (DuckDB) | Tools + SQL (DuckDB embedded) |

## Cobertura compartilhada

Ambos cobrem (via rodado ou mcp-brasil):
BCB, BNDES, Câmara, CGU/Transparência, Educação (INEP), Eleições (TSE), IBGE, INPE, IPEA, Meio Ambiente (MapBiomas), MS/Saúde (CNES, SIM, SINASC etc.), Portal da Transparência, RAIS/CAGED, Receita Federal, SICONFI, STF, ANP, PNCP/ComprasNet.

## Gaps

| Área | mcp-brasil tem | rodado não tem |
|------|---------------|----------------|
| **Judicial** | DataJud (processos vivos), jurisprudência STF/STJ/TST | CNJ stats agregados só |
| **TCEs estaduais** | 11 cortes (SP, RJ, RS, PE, CE, ES, RN, PI, SC, TO, PA) | Zero |
| **Infraestrutura** | ANEEL, ANTT, ANAC (aeronaves + voos regulares) | Nada |
| **Segurança pública** | SINESP, FBSP Anuário, Atlas da Violência | Só RJ ISP |
| **MJSP** | INFOPEN, PROCON/Sindec, armas | Nada |
| **Diários oficiais** | Querido Diário (5K+ municípios) + DOU | DOU scraper quebrado (inlabs requer registro) |
| **Utilidades** | BrasilAPI (CEP, CNPJ, DDD live), Tábua de Marés | CNPJ dump estático |
| **SPU** | SIAPA (813K imóveis da União) | Nada |
| **Saúde** | DENASUS, Farmácia Popular, BPS, RENAME | CNES/SIM/SINASC só |
| **Meio Ambiente** | IBAMA (autos infração, CTF, TCFA) | Server 500 |
| **Eleitoral** | Meta Ad Library (anúncios eleitorais) | Nada |
| **Energia** | ANEEL (SIGA, geração distribuída, tarifas) | Nada |
| **Transportes** | ANTT (rodovias concedidas, cargas, passageiros) | Nada |

## Maiores gaps estruturais

1. **TCEs estaduais** — 11 estados com APIs de licitações, contratos, despesas municipais. Nada disso está no espelho.
2. **DataJud** — processos judiciais vivos. CNJ stats são agregados; DataJud é粒ado (grão de processo).
3. **BrasilAPI** — utilidades (CEP, CNPJ, DDD, FIPE). Dado transacional que faz sentido live, não mirror.
4. **Diários municipais (Querido Diário)** — 5K+ cidades. Escala inviável pra mirror.

## Observações

- mcp-brasil é um **MCP server** (live API). rodado é um **ETL + SQL endpoint**. Não são concorrentes diretos.
- Nosso diferencial: SQL direto em 533 tabelas normalizadas com schema unificado.
- Dá pra preencher alguns gaps com scrapers adicionais (ex: ANEEL, ANTT têm CKAN).
- TCEs e DataJud seriam os de maior valor, mas exigem sync contínuo (não batch).
