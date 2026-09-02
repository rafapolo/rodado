# Gap analysis & candidatos a ETL — pesquisa 2026-08-23

Análise de lacunas entre o que o rodado já cobre (849 tabelas / 203 datasets / 38,1 bi linhas: 689 espelhadas do Base dos Dados + 160 raspadas) e o que existe de dado público brasileiro fora desse universo. Complementa `datasets_to_scrap.md` (que rastreia fontes em andamento); aqui ficam as **fontes novas** candidatas, rankeadas por valor/esforço.

## Onde o projeto é denho hoje

Cobertura densa em: trabalho/empresas (RAIS, CAGED, CNPJ, CNO), educação INEP (Censo Escolar/Superior, ENEM, SAEB, IDEB), saúde DataSUS (SIH, SINAN, SINASC, CNES, SIM), eleições TSE, orçamento/execução (Siconfi, SIOP, CGU), sanções (TCU, IBAMA, OpenSanctions/OFAC/EU/UN), SICAF/CATMAT.

## Dívida interna conhecida (antes de olhar pra fora)

| Gap | Detalhe |
|---|---|
| Row drift ~5 bi linhas em 115 tabelas | `br_ans_beneficiario` (~940M atrás), `br_me_cnpj.empresas/estabelecimentos`, `br_rf_cno.*` — fecham devagar por design (teto 5M rows/3GB por execução) |
| Querido Diário | buraco ~9 meses (2025-10-05 → 2026-07-10) a re-fetchar |
| Atlas da Violência | 146/157 séries faltando quando a IPEA voltar |
| Consumidor.gov.br | 16 arquivos pendentes (fonte em outage) |
| Quick-win BCB | `br_bcb_taxa_cambio.taxa_cambio` e `br_bcb_taxa_selic.taxa_selic` ausentes |
| MUNIC/ESTADIC | stale (~2019–21); edições 2023–2024 disponíveis |
| `consultar_oab` (mcp-live, bloqueado) | `consultar_painelprecos` **já construído** em 2026-08-24 (API real confirmada, testada ao vivo). `consultar_oab(numero)` continua pendente por motivo diferente: a nota original em `datasets_to_scrap.md` (linha OAB advogado) diz explicitamente que **nenhuma API real foi encontrada** — `cna.oab.org.br`/`consulta.oab.org.br` são SPAs Angular e todo caminho de API tentado devolveu o `index.html` da própria SPA, não dado real. Construir esse tool exige engenharia reversa nova (inspecionar o bundle JS/tráfego de rede da SPA), não é só escrever o wrapper — tratar como pesquisa, não como implementação direta |

## Comparação com o mcp-brasil — a lente externa (2026-08-26)

O [mcp-brasil](https://github.com/Mcp-Brasil/mcp-brasil) (533 tools, 70 fontes) é o
inventário mais próximo do nosso e serve de espelho: o que ele cobre e nós não é a
lista de candidatos que ninguém aqui teria pensado sozinho. **Não são concorrentes**
— ele é um MCP server de *live API passthrough*, o rodado é um mirror pré-computado
com SQL direto sobre schema unificado.

| | rodado | mcp-brasil |
|---|--------|-----------|
| Modelo | mirror Parquet pré-computado | live API passthrough |
| Atualização | batch (sync do beelink) | fresh a cada call |
| Performance | rápido (parquet local) | limitado pela API upstream |
| Query | SQL (DuckDB) | tools + SQL (DuckDB embedded) |

Cobertura compartilhada (ambos têm): BCB, BNDES, Câmara, CGU/Transparência, INEP,
TSE, IBGE, INPE, IPEA, MapBiomas, DataSUS (CNES, SIM, SINASC…), Portal da
Transparência, RAIS/CAGED, Receita Federal, SICONFI, STF, ANP, PNCP/ComprasNet.

### O que ele tem e nós não

| Área | mcp-brasil tem | situação no rodado |
|------|---------------|--------------------|
| **TCEs estaduais** | 11 cortes (SP, RJ, RS, PE, CE, ES, RN, PI, SC, TO, PA) | zero |
| **Judicial** | DataJud (processos vivos), jurisprudência STF/STJ/TST | só CNJ agregado — ver #10 |
| **MJSP** | INFOPEN, PROCON/Sindec, armas | nada |
| **SPU** | SIAPA (813K imóveis da União) | nada |
| **Saúde** | DENASUS, Farmácia Popular, BPS, RENAME | só CNES/SIM/SINASC etc. |
| **Meio ambiente** | IBAMA (autos de infração, CTF, TCFA) | server 500 |
| **Eleitoral** | Meta Ad Library (anúncios eleitorais) | nada |
| **Segurança pública** | SINESP, FBSP Anuário, Atlas da Violência | só ISP-RJ — SINESP é #5, Atlas está na dívida interna |
| **Energia / transportes** | ANEEL (SIGA, GD, tarifas), ANTT, ANAC | ANEEL é #7, ANTT é #9; ANAC não |
| **Diários oficiais** | Querido Diário (5K+ municípios) + DOU | QD com buraco de 9 meses; DOU quebrado (inlabs exige registro) |
| **Utilidades** | BrasilAPI (CEP, CNPJ, DDD live) | dump CNPJ estático + `consultar_cep`/`consultar_cnpj` |

### Os quatro gaps estruturais

1. **TCEs estaduais** — 11 estados com API de licitações, contratos e despesas
   municipais. É o maior buraco absoluto e não tem nada equivalente no espelho.
2. **DataJud** — processo judicial vivo, no grão do processo. O CNJ que temos como
   candidato (#10) é agregado; o microdado fica atrás da Res. 331/2020 (bucket
   `deferred-api_key`).
3. **BrasilAPI** — dado transacional que faz sentido *live*, não mirror. Caminho
   certo aqui é tool MCP, não ETL (é o que `consultar_cep`/`consultar_cnpj` já fazem).
4. **Querido Diário municipal** — 5K+ cidades; a escala inviabiliza mirror completo,
   e o que já temos está com buraco a re-fetchar.

**Leitura**: ANEEL, ANTT e SINESP já estavam nos tiers acima por conta própria — a
comparação confirma a prioridade. O que ela acrescenta de genuinamente novo à fila
é **TCEs estaduais** (bulk/API, chave `cnpj` + `id_municipio`, encaixa no padrão
fetch→Parquet→rsync) e, como tool live e não como ETL, INFOPEN/PROCON e SIAPA.
DataJud continua bloqueado por credencial, não por esforço.

## Tier 1 — maior valor por esforço

### 1. PNCP — Portal Nacional de Contratações Públicas
- **Fonte**: https://pncp.gov.br/api/pncp/v3 (Swagger) + bulk CSV em gov.br/pncp/acesso-a-informacao/dados-abertos; complementar https://dadosabertos.compras.gov.br
- **Órgão**: MGI / Rede Nacional de Contratações Públicas (Lei 14.133)
- **Freq**: diária · **Formato**: REST JSON sem chave + CSV · **Volume**: milhões de editais/atas/contratos desde 2021, União+estados+municípios
- **Chaves**: `cnpj` (órgão = raiz, fornecedor = completo), `id_municipio`
- **Por quê**: única fonte com licitações **municipais** padronizadas; substitui e ultrapassa o ComprasNet. Não existe na BD.
- **Status BD**: não existe

### 2. Benefícios CGU novos: Pé-de-Meia, Gás do Povo, Novo Bolsa Família
- **Fonte**: https://portaldatransparencia.gov.br/download-de-dados (CSV zipados mensais)
- **Volume**: BF ~20M famílias/mês; Pé-de-Meia ~3M/mês; Gás do Povo ~15M famílias (nov/2025+)
- **Chaves**: NIS, CPF mascarado, município/UF; Gás do Povo traz CNPJ da revenda
- **Por quê**: Pé-de-Meia cruza com Censo Escolar (aluno/escola) que já se tem. Nota: `pe_de_meia` bulk já foi baixada (~64M rows no beelink via Portal da Transparência) — validar cobertura vs. esta fonte; **Gás do Povo e Novo Bolsa Família não existem**.
- **Status BD**: Auxílio Emergencial/Auxílio Brasil parciais na BD; Pé-de-Meia/Gás do Povo não existem

### 3. Transferegov.br (ex-SICONV) — transferências completas
- **Fonte**: http://repositorio.dados.gov.br/seges/detru/
- **Freq**: diária (extração às 9h) · **Formato**: CSV.zip · **Volume**: ~20 tabelas, dezenas de GB histórico
- **Chaves**: `cnpj` proponente/convenente, `codigo_ibge`
- **Por quê**: fluxo integral União→municípios/OSC (convênios, propostas, empenhos, desembolsos, pagamentos a favorecidos). Casa com Siconfi/SIOP/TransfereGov parcial já existente (`br_transferegov` tem só 3 tabelas).
- **Status BD**: não

### 4. BCB — Estatísticas do Pix por município + meios de pagamento
- **Fonte**: https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata (`TransacoesPixPorMunicipio`); https://dadosabertos.bcb.gov.br/dataset/pix
- **Freq**: mensal desde nov/2020 · **Formato**: OData JSON/CSV · **Volume**: ~5.570 municípios × PF/PJ × mês
- **Chaves**: `id_municipio`
- **Por quê**: proxy econômico mensal municipal de altíssimo valor analítico; ETL trivial. BD só tem séries SGS agregadas.
- **Status BD**: não (Pix por município)

### 5. SINESP VDE — criminalidade municipal consolidada
- **Fonte**: https://dados.mj.gov.br/dataset/sistema-nacional-de-estatisticas-de-seguranca-publica ; gov.br/mj dados nacionais
- **Freq**: mensal (2015–2026) · **Formato**: XLSX/CSV · **Volume**: ~16 indicadores × município × mês
- **Chaves**: `id_municipio`; cross-check com SIM (CID-10)
- **Por quê**: única série nacional de criminalidade municipal (homicídio doloso, feminicídio, estupro, roubo/furto de veículo e carga…). O `br_mjsp_sinesp` existente tem só 2 tabelas — validar se cobre VDE municipal consolidado ou apenas agregado UF.
- **Status BD**: não

## Tier 2 — alto valor, esforço médio

### 6. CNEFE Censo 2022 (Cadastro Nacional de Endereços)
- **Fonte**: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/ (divulgado jun/2024)
- **Volume**: ~110M endereços com coordenadas, setor censitário, CEP, face de quadra — dezenas de GB, CSV por UF
- **Chaves**: **CEP ↔ setor censitário ↔ id_municipio** — a grande ponte faltante para geolocalizar qualquer base
- **Status BD**: não

### 7. ANEEL — geração distribuída, usinas SIGA, tarifas
- **Fonte**: https://dadosabertos.aneel.gov.br (CKAN, vários datasets em **Parquet nativo**)
- **Freq**: mensal/diária · **Volume**: GD >3M unidades consumidoras
- **Chaves**: município, CNAE da distribuidora
- **Nota**: o bloqueio antigo era NXDOMAIN do portal velho — o portal mudou de endereço; re-testar.
- **Status BD**: não

### 8. IBGE MUNIC 2024 / ESTADIC 2024
- **Fonte**: SIDRA / https://www.ibge.gov.br/estatisticas/sociais/saude/10586-pesquisa-de-informacoes-basicas-municipais.html
- **Volume**: ~5.570 municípios × ~300 variáveis · edição 2024 trouxe igualdade racial + eventos climáticos RS
- **Chaves**: `id_municipio`
- **Por quê**: refresh pequeno do `br_ibge_munic`/`br_ibge_estadic` que estão stale.
- **Status BD**: até ~2019–21

### 9. ANTT RNTRC (+ veículos, CIOT)
- **Fonte**: https://dados.antt.gov.br/dataset/rntrc , rntrc-veiculos, ciot
- **Freq**: mensal (snapshot) · **Formato**: CSV ~70MB/mês · **Volume**: ~2M transportadores (TAC/ETC/CTC) + frota
- **Chaves**: cnpj/cpf, id_municipio
- **Nota**: ANTT está no bucket blocked→mcp-todo por WAF; o portal CKAN `dados.antt.gov.br` pode ser caminho alternativo.
- **Status BD**: não

### 10. CNJ — Painel Justiça em Números (agregados)
- **Fonte**: https://paineis.cnj.jus.br (downloads agregados); microdado DataJud fica no bucket deferred-api_key por Res. 331/2020
- **Chaves**: tribunal, município (unidade judiciária), CNPJ de partes PJ nos agregados de litigiosidade
- **Status BD**: não

### 11. BCB SCR.data + Desenrola Brasil
- **Fonte**: https://www.bcb.gov.br/estabilidadefinanceira/scrdata ; dataset Desenrola no portal de dados abertos do BCB
- **Freq**: mensal · **Formato**: CSV.zip
- **Chaves**: município × CNAE × porte × modalidade
- **Por quê**: crédito por dupla chave que o rodado domina.
- **Status BD**: não

## Tier 3 — valioso, escopo mais estreito

| # | Dataset | Fonte | Chave | Status BD |
|---|---|---|---|---|
| 12 | Emendas parlamentares (bulk CGU) | portaldatransparencia.gov.br/download-de-dados/emendas | autor, id_municipio, código SIAFI | não (só via mirror CGU parcial) |
| 13 | ANP cadastro de revendas (postos/GLP, bandeira) | gov.br/anp dados abertos | CNPJ | não — enriquece `br_anp_combustiveis.precos` |
| 14 | CadÚnico agregados municipais | MDS VIS DATA / portal analítico | id_municipio | não (só painéis) |
| 15 | CAUC / Tesouro Transparente — regularidade fiscal | tesourotransparente.gov.br | codigo_siafi/id_municipio | não — pré-requisito de convênios, casa com Transferegov |
| 16 | PNS 2023 microdados | IBGE FTP | UF/região (chave fraca) | BD não tem 2023 |
| 17 | PRODES/DETER BiomasBR all-biomas | terrabrasilis.dpi.inpe.br/downloads/ + API v1 | id_municipio | BD/espelho têm versões antigas só Amazônia/Cerrado; desde 2024–26 cobre todos os biomas com Sentinel-2 |
| 18 | DIRPF destinações FDCA/FDI | gov.br/receitafederal/dados | CNPJ do fundo/município | não |
| 19 | Corpus PT-BR (Jabuticaba etc., HF Parquet) | huggingface.co | — | relevante só p/ treinar PT-BR do `ask`, não é join-analítico |
| 20 | TCEs estaduais (11 cortes: SP, RJ, RS, PE, CE, ES, RN, PI, SC, TO, PA) | portais/API de cada corte | cnpj, id_municipio | não — 11 fontes distintas, esforço alto; achado na comparação com o mcp-brasil |
| 21 | SPU SIAPA — imóveis da União | gov.br/spu | id_municipio, CEP | não — ~813K imóveis; idem |

## Ordem recomendada

1. **Quick-wins internos primeiro**: `br_bcb_taxa_cambio`/`taxa_selic`; MUNIC/ESTADIC 2023-24 via SIDRA; retomar Consumidor.gov (16 arquivos) e buraco do Querido Diário quando fontes voltarem.
2. **Tier 1 externo**, todos bulk/API sem chave, chaves de join já dominadas, padrão fetch→Parquet→rsync→regenerar catálogo:
   - PNCP → benefícios CGU (Gás do Povo + Novo Bolsa Família; validar Pé-de-Meia) → Transferegov completo → Pix por município → SINESP VDE.
3. **Tier 2** conforme cota BigQuery Sandbox sobrar e drift interno fechar (CNEFE é o mais pesado — planejar janela própria).
4. **Tier 3** por oportunidade. Dos achados na comparação com o mcp-brasil, TCEs (#20) é o de maior valor e o de maior esforço — 11 APIs sem padrão comum; INFOPEN/PROCON e SIAPA fazem mais sentido como tool live (padrão `consultar_*`) do que como ETL.

## Chaves de join exploradas pelos candidatos

| Chave | Candidatos |
|---|---|
| CNPJ | PNCP, Transferegov, RNTRC, SCR, ComprasNet, ANP cadastros, Emendas |
| id_municipio | Pix/BCB, SINESP, PRODES/DETER, MUNIC, CadÚnico, Querido Diário, benefícios CGU, CAUC |
| NIS/CPF mascarado | Benefícios CGU (BF, Pé-de-Meia, Gás do Povo, BPC), CadÚnico (agregado) |
| CEP/setor censitário | CNEFE (ponte faltante) |
| CID-10 | SINESP↔SIM cross-check, PNS |

## Execução 2026-08-27 — os quick-wins internos

### `br_bcb_taxa_cambio`/`taxa_selic` — continuam bloqueados, mas por um motivo diferente do que se pensava

Não é "ainda não fizemos" — é **ACL negada no projeto BigQuery da própria Base dos Dados**,
confirmado ao vivo:

```
$ bq query --project_id=raspa-491716 --use_legacy_sql=false \
  'SELECT * FROM `basedosdados.br_bcb_taxa_cambio.taxa_cambio` LIMIT 5'
Access Denied: Table basedosdados:br_bcb_taxa_cambio.taxa_cambio: User does not
have permission to query table ..., or perhaps it does not exist.
```

`bq show` (metadata) funciona e devolve `numRows: 801451` — é por isso que a tabela
aparece no catálogo como "existe, só falta puxar". Mas o `SELECT` real falha porque o
dataset não tem `Readers: allUsers` na ACL — só `projectReaders`. Comparação direta:

| Dataset | ACL `Readers` | Query funciona? |
|---|---|---|
| `br_ibge_munic` (funciona) | `allUsers, projectReaders` | sim |
| `br_bcb_ifdata` (funciona) | `allUsers, projectReaders` | sim |
| `br_bcb_taxa_cambio` | só `projectReaders` | **não — access denied** |
| `br_bcb_taxa_selic` | só `projectReaders` | **não — access denied** |

Isso não é algo que dá pra contornar do nosso lado — é uma decisão de permissão no projeto
`basedosdados` da BD. `scripts/sync/gcp_to_beelink_sync.py` tentou as duas e ambas caíram
em `fetch failed (likely access-denied view)`, confirmando o diagnóstico. Nada foi escrito
no beelink por essas duas tabelas.

**Ação tomada em vez disso**: `br_bcb_sgs.series` (scraper existente, direto na API pública
do BCB, sem passar por BigQuery) já cobre o equivalente funcional — série 1
(`dolar_comercial_venda`, câmbio USD/BRL diário) e série 11 (`taxa_selic_diaria`) — mas
estava parada em 31/12/2025. Rodei `python3 scripts/scrap/bcb_sgs.py` (todas as 18 séries
curadas, full-history pull, idempotente — sobrescreve o mesmo `series.parquet`) e confirmei
no beelink:

```
series_code=1  (dolar_comercial_venda) : 6.660 → 6.694 linhas, max date 2026-08-26
series_code=11 (taxa_selic_diaria)      : 6.660 → 6.694 linhas, max date 2026-08-26
```

Nota: `date` na tabela é `VARCHAR` em formato `DD/MM/YYYY` — `max(date)` como string dá
resultado errado (`"31/12/2025"` ordena depois de `"27/08/2026"` lexicograficamente); usar
`max(strptime(date, '%d/%m/%Y'))`.

Isto **não é o mesmo schema** que as tabelas `br_bcb_taxa_cambio`/`taxa_selic` da BD (que
trazem paridade compra/venda por boletim intradiário, múltiplas moedas) — é uma série
diária única por indicador. Cobre o caso de uso mais comum (cotação e Selic do dia), não
substitui a tabela original se alguém precisar do boletim PTAX completo.

### MUNIC/ESTADIC 2023-2024 — não é row drift, é a própria BD estar parada

Comparei `bq show`/dry-run ao vivo contra os números locais do beelink: **beelink já
espelha exatamente o que a Base dos Dados tem hoje no BigQuery** — nenhuma linha de drift
a fechar.

| Tabela | beelink (linhas / ano_max) | BD BigQuery (linhas / ano_max, checado ao vivo) |
|---|---|---|
| `br_ibge_munic.atual_prefeito` | 33.399 / 2021 | 33.399 / 2021 |
| `br_ibge_munic.habitacao` | 66.808 / 2024 | 66.808 |
| `br_ibge_munic.meio_ambiente` | 44.534 / 2020 | 44.534 |
| `br_ibge_munic.recursos_gestao` | 38.958 / 2019 | 38.958 / 2019 |
| `br_ibge_munic.recursos_humanos` | 94.647 / 2024 | 94.647 |
| `br_ibge_estadic.governanca` | 27 / 2019 | 27 / 2019 |

Ou seja: `habitacao` e `recursos_humanos` **já têm 2024** (a própria BD atualizou essas
duas), mas `atual_prefeito`/`meio_ambiente`/`recursos_gestao` e a maior parte do ESTADIC
seguem travadas em 2018-2021 **na própria BD** — não é algo que um `bq query` daqui
resolve, porque não existe linha mais nova pra puxar do lado de lá.

**Fonte direta confirmada por `curl` (sem necessidade de cadastro/API key)**:

```
https://ftp.ibge.gov.br/Perfil_Municipios/2024/Base_de_Dados/Base_MUNIC_2024_20251107.xlsx  (25,5 MB, HTTP 200)
https://ftp.ibge.gov.br/Perfil_Municipios/2023/Base_de_Dados/Base_MUNIC_2023.xlsx            (HTTP 200)
https://ftp.ibge.gov.br/Perfil_Estados/2024/Base_Estadic_2024.xlsx                            (211 KB, HTTP 200)
https://ftp.ibge.gov.br/Perfil_Estados/2023/Base_Estadic_2023.xlsx                            (HTTP 200)
```

(A página HTML do IBGE devolve 403 pra `curl` simples — SPA/anti-bot — mas o FTP estático
`ftp.ibge.gov.br` não tem essa barreira.)

**Por que não escrevi o scraper agora**: cada ano vem como **um único XLSX consolidado**
com centenas de variáveis (não um CSV por tema), enquanto a BD modela MUNIC em 7 tabelas
normalizadas (`atual_prefeito`, `habitacao`, `indicadores_perfil_gestor`,
`indicadores_quantidade_vinculo`, `meio_ambiente`, `recursos_gestao`,
`recursos_humanos`) e ESTADIC em mais 7. Mapear ~300 colunas do XLSX pras 7 tabelas exige
o dicionário/codebook do IBGE pra não inventar a correspondência — isso é uma tarefa de
ETL própria, não um refresh de 20 minutos. Confirmar a fonte era o que a instrução pedia;
construir o parser fica para quem decidir o escopo (schema idêntico à BD com o join
completo, ou tabela nova mais simples "uma linha por município/ano" com as colunas cruas).

### Consumidor.gov.br — pulado, conforme instrução (outro agente já investigando via `tasks/todo.md`)

### Buraco do Querido Diário — investigado, nada executado

Confirmado ao vivo, sem escrever nada:

- `br_ok_queridodiario.diarios` no beelink tem **231.899 linhas**, `2023-07-10` a
  `2025-10-04`. Só existe **um** arquivo no diretório
  (`diarios_partial_2023-07-10_2025-06-15.parquet`, 14 MB) — o nome do arquivo (até
  2025-06-15) não bate com o dado real dentro dele (vai até 2025-10-04); não investiguei
  a causa da inconsistência do nome, só registro que existe.
- O buraco é maior do que o "~9 meses" registrado antes: outubro/2025 já aparece truncado
  (só 1.225 registros, contra ~8-9 mil/mês nos meses anteriores) e não há nada depois. Hoje
  (2026-08-27) o buraco real é **2025-10-05 → hoje, ~10,7 meses**.
- **A API está no ar e respondendo normalmente** — testei ao vivo (`GET /gazettes` com
  `published_since=2026-08-01&published_until=2026-08-07` devolveu HTTP 200,
  `total_gazettes: 1473`, dados de agosto/2026 reais). Não é outage — o script simplesmente
  não foi rodado de novo desde 2026-07-10.
- **Por que não rodei o refresh direto**: `scripts/scrap/querido_diario.py` só aceita
  `--years N` (default 3) — sempre um pull completo dos últimos N anos, sem `--since`/
  `--until`. Rodá-lo hoje sem modificação re-buscaria ~2 anos de dado que o beelink já tem
  (2023-2025) só pra alcançar o buraco de 10 meses, e escreveria um **segundo** arquivo de
  parte com sobreposição total ao já existente (o dataset lê `*.parquet` glob — dois
  arquivos cobrindo o mesmo período duplicaria toda linha em contagens). Antes de rodar,
  precisa de um dos dois: (a) adicionar `--since`/`--until` ao script pra buscar só o
  buraco, ou (b) rodar com `--years` maior e apagar o arquivo antigo antes do rsync. Decisão
  de escopo, não escrevi nenhum dos dois sem confirmação.
