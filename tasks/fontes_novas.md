# Fontes novas — o que existe de dado público que o espelho ainda não tem

> Agrupado em 2026-09-02 de dois arquivos que respondiam a mesma pergunta em
> escalas diferentes: `datasets_gap_analysis.md` (varredura ampla do dado
> público brasileiro fora do espelho, rankeada por valor/esforço) e
> `datasets_licenciamento_ambiental.md` (o mergulho temático em licenciamento
> e poluição, saído do relatório de Nova Friburgo). O segundo é um caso
> particular do primeiro — mantê-los separados espalhava "fonte candidata a
> ETL" por dois lugares que ninguém cruzava.

**Como isto se relaciona com os vizinhos:**

| Arquivo | Escopo |
|---|---|
| **este** | fontes **fora** do espelho, ainda não raspadas — candidatas a ETL |
| [`datasets_to_scrap.md`](datasets_to_scrap.md) | as que já entraram na fila de raspagem e têm status (`blocked`, `deferred-api_key`…) |
| [`espelho_subutilizado.md`](espelho_subutilizado.md) | o contrário daqui: dado que **já está** no espelho e nada consome |

Quando um item daqui vira trabalho de verdade, ele ganha linha em
`datasets_to_scrap.md` — este arquivo é o inventário, aquele é o board.

---

# Parte I — Varredura geral (2026-08-23)

Análise de lacunas entre o que o rodado já cobre (849 tabelas / 203 datasets / 38,1 bi linhas: 689 espelhadas do Base dos Dados + 160 raspadas) e o que existe de dado público brasileiro fora desse universo. Complementa `datasets_to_scrap.md` (que rastreia fontes em andamento); aqui ficam as **fontes novas** candidatas, rankeadas por valor/esforço.

### Onde o projeto é denho hoje

Cobertura densa em: trabalho/empresas (RAIS, CAGED, CNPJ, CNO), educação INEP (Censo Escolar/Superior, ENEM, SAEB, IDEB), saúde DataSUS (SIH, SINAN, SINASC, CNES, SIM), eleições TSE, orçamento/execução (Siconfi, SIOP, CGU), sanções (TCU, IBAMA, OpenSanctions/OFAC/EU/UN), SICAF/CATMAT.

### Dívida interna conhecida (antes de olhar pra fora)

| Gap | Detalhe |
|---|---|
| Row drift ~5 bi linhas em 115 tabelas | `br_ans_beneficiario` (~940M atrás), `br_me_cnpj.empresas/estabelecimentos`, `br_rf_cno.*` — fecham devagar por design (teto 5M rows/3GB por execução) |
| Querido Diário | buraco ~9 meses (2025-10-05 → 2026-07-10) a re-fetchar |
| Atlas da Violência | 146/157 séries faltando quando a IPEA voltar |
| Consumidor.gov.br | 16 arquivos pendentes (fonte em outage) |
| Quick-win BCB | `br_bcb_taxa_cambio.taxa_cambio` e `br_bcb_taxa_selic.taxa_selic` ausentes |
| MUNIC/ESTADIC | stale (~2019–21); edições 2023–2024 disponíveis |
| `consultar_oab` (mcp-live, bloqueado) | `consultar_painelprecos` **já construído** em 2026-08-24 (API real confirmada, testada ao vivo). `consultar_oab(numero)` continua pendente por motivo diferente: a nota original em `datasets_to_scrap.md` (linha OAB advogado) diz explicitamente que **nenhuma API real foi encontrada** — `cna.oab.org.br`/`consulta.oab.org.br` são SPAs Angular e todo caminho de API tentado devolveu o `index.html` da própria SPA, não dado real. Construir esse tool exige engenharia reversa nova (inspecionar o bundle JS/tráfego de rede da SPA), não é só escrever o wrapper — tratar como pesquisa, não como implementação direta |

### Comparação com o mcp-brasil — a lente externa (2026-08-26)

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

#### O que ele tem e nós não

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

#### Os quatro gaps estruturais

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

### Tier 1 — maior valor por esforço

#### 1. PNCP — Portal Nacional de Contratações Públicas
- **Fonte**: https://pncp.gov.br/api/pncp/v3 (Swagger) + bulk CSV em gov.br/pncp/acesso-a-informacao/dados-abertos; complementar https://dadosabertos.compras.gov.br
- **Órgão**: MGI / Rede Nacional de Contratações Públicas (Lei 14.133)
- **Freq**: diária · **Formato**: REST JSON sem chave + CSV · **Volume**: milhões de editais/atas/contratos desde 2021, União+estados+municípios
- **Chaves**: `cnpj` (órgão = raiz, fornecedor = completo), `id_municipio`
- **Por quê**: única fonte com licitações **municipais** padronizadas; substitui e ultrapassa o ComprasNet. Não existe na BD.
- **Status BD**: não existe
- **2026-09-02**: já em coleta por outro processo em paralelo (`_staging/pncp/multi.sh` +
  `persistente.sh`, rodando no beelink desde antes desta sessão — ver `tasks/README.md` § "Em
  aberto"). Não tocado aqui para não duplicar/competir por rate limit com esse workstream.

#### 2. Benefícios CGU novos: Pé-de-Meia, Gás do Povo, Novo Bolsa Família ✅ / 🔵 ver Execução 2026-09-02
- **Fonte**: https://portaldatransparencia.gov.br/download-de-dados (CSV zipados mensais)
- **Volume**: BF ~20M famílias/mês; Pé-de-Meia ~3M/mês; Gás do Povo ~15M famílias (nov/2025+)
- **Chaves**: NIS, CPF mascarado, município/UF; Gás do Povo traz CNPJ da revenda
- **Por quê**: Pé-de-Meia cruza com Censo Escolar (aluno/escola) que já se tem. Nota: `pe_de_meia` bulk já foi baixada (~64M rows no beelink via Portal da Transparência) — validar cobertura vs. esta fonte; **Gás do Povo e Novo Bolsa Família não existem**.
- **Status BD**: Auxílio Emergencial/Auxílio Brasil parciais na BD; Pé-de-Meia/Gás do Povo não existem
- **2026-09-02**: Gás do Povo **feito** (`br_cgu_gas_do_povo`, 20.817.231 linhas, 8/8 meses — a contagem
  de 34.846.839 registrada mais cedo hoje estava inflada por um `.parquet` duplicado que uma sessão
  paralela gravou por engano na mesma pasta com outro padrão de nome; removido e recontado, ver
  Execução abaixo). Novo Bolsa Família **em andamento** (`br_cgu_novo_bolsa_familia`, resumível) — ver
  Execução abaixo.

#### 3. Transferegov.br (ex-SICONV) — transferências completas 🔵 ver Execução 2026-09-02
- **Fonte**: http://repositorio.dados.gov.br/seges/detru/
- **Freq**: diária (extração às 9h) · **Formato**: CSV.zip · **Volume**: ~20 tabelas, dezenas de GB histórico (na verdade **54** arquivos CSV.zip no diretório, ver Execução)
- **Chaves**: `cnpj` proponente/convenente, `codigo_ibge`
- **Por quê**: fluxo integral União→municípios/OSC (convênios, propostas, empenhos, desembolsos, pagamentos a favorecidos). Casa com Siconfi/SIOP/TransfereGov parcial já existente (`br_transferegov` tem só 3 tabelas).
- **Status BD**: não
- **2026-09-02**: **em andamento** (`br_transferegov_siconv`, resumível) — ver Execução abaixo.

#### 4. BCB — Estatísticas do Pix por município + meios de pagamento ❌ endpoint quebrado do lado do BCB
- **Fonte**: https://olinda.bcb.gov.br/olinda/servico/Pix_DadosAbertos/versao/v1/odata (`TransacoesPixPorMunicipio`); https://dadosabertos.bcb.gov.br/dataset/pix
- **Freq**: mensal desde nov/2020 · **Formato**: OData JSON/CSV · **Volume**: ~5.570 municípios × PF/PJ × mês
- **Chaves**: `id_municipio`
- **Por quê**: proxy econômico mensal municipal de altíssimo valor analítico; ETL trivial. BD só tem séries SGS agregadas.
- **Status BD**: não (Pix por município)
- **2026-09-02 — testado ao vivo, não é credencial**: o entity set real é `_TransacoesPixPorMunicipio` (com underscore — sem ele o serviço devolve 400 "malformed", o nome do item na doc original estava sem underscore). Com underscore, **toda** variação testada (`$top`, `$filter=AnoMes eq …`, com/sem `$format=json`, chave composta `(202401)`) devolve `HTTP 500 {"codigo":500,"mensagem":"Erro desconhecido"}` — no mesmo host, no mesmo serviço, outros entity sets (`PixUsuariosCadastradosDICT`, sem underscore) respondem normalmente. `$metadata` também responde 200 e descreve o schema certinho. Ou seja: o schema existe, o endpoint de dado está quebrado no lado do BCB, não é geo-bloqueio nem parâmetro errado nosso. Sem CSV alternativo no CKAN (`dadosabertos.bcb.gov.br/dataset/pix` só linka de volta pro mesmo OData). Reteste periodicamente — pode ser transitório.

#### 5. SINESP VDE — criminalidade municipal consolidada ❌ WAF bloqueia o download, não é geo/credencial
- **Fonte**: https://dados.mj.gov.br/dataset/sistema-nacional-de-estatisticas-de-seguranca-publica ; gov.br/mj dados nacionais
- **Freq**: mensal (2015–2026) · **Formato**: XLSX/CSV · **Volume**: ~16 indicadores × município × mês
- **Chaves**: `id_municipio`; cross-check com SIM (CID-10)
- **Por quê**: única série nacional de criminalidade municipal (homicídio doloso, feminicídio, estupro, roubo/furto de veículo e carga…). O `br_mjsp_sinesp` existente tem só 2 tabelas — validar se cobre VDE municipal consolidado ou apenas agregado UF.
- **Status BD**: não
- **2026-09-02**: `dados.mj.gov.br` não resolve mais (DNS falha — domínio parece desativado). A base migrou para
  `gov.br/mj/.../base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023`
  — página HTML acessível (200) e lista **12 XLSX diretos**, um por ano, 2015–2026
  (`.../download/dnsp-base-de-dados/bancovde-{2015..2026}.xlsx/@@download/file`). Mas os links de
  download em si devolvem **403** — testado direto do laptop, direto do beelink e via o proxy BR
  (`129.121.55.206:8080`) já usado pelo PNCP: os três dão 403 idêntico, com e sem `Referer`/cookie de
  sessão da página. Não é o mesmo padrão de bloqueio geo-IP do IBAMA/INEA (que cede a qualquer IP
  brasileiro) — aqui até o proxy BR apanha, então é uma regra de WAF específica para o path
  `/@@download/file` (Plone), não geografia. Não achei contorno em esforço razoável; próxima tentativa:
  testar com um browser real (cookies/JS challenge) em vez de curl.

### Tier 2 — alto valor, esforço médio

#### 6. CNEFE Censo 2022 (Cadastro Nacional de Endereços)
- **Fonte**: https://ftp.ibge.gov.br/Censos/Censo_Demografico_2022/ (divulgado jun/2024)
- **Volume**: ~110M endereços com coordenadas, setor censitário, CEP, face de quadra — dezenas de GB, CSV por UF
- **Chaves**: **CEP ↔ setor censitário ↔ id_municipio** — a grande ponte faltante para geolocalizar qualquer base
- **Status BD**: não

#### 7. ANEEL — geração distribuída, usinas SIGA, tarifas
- **Fonte**: https://dadosabertos.aneel.gov.br (CKAN, vários datasets em **Parquet nativo**)
- **Freq**: mensal/diária · **Volume**: GD >3M unidades consumidoras
- **Chaves**: município, CNAE da distribuidora
- **Nota**: o bloqueio antigo era NXDOMAIN do portal velho — o portal mudou de endereço; re-testar.
- **Status BD**: não
- **2026-09-02**: re-testado, ainda fora do ar — mas o modo de falha mudou. O domínio novo
  (`dadosabertos.aneel.gov.br`) **resolve** (`200.198.220.169`), só não completa a conexão TCP na
  porta 443 (timeout, direto e via beelink). Não é mais NXDOMAIN — é o host que não responde. Sem
  contorno testado.

#### 8. IBGE MUNIC 2024 / ESTADIC 2024
- **Fonte**: SIDRA / https://www.ibge.gov.br/estatisticas/sociais/saude/10586-pesquisa-de-informacoes-basicas-municipais.html
- **Volume**: ~5.570 municípios × ~300 variáveis · edição 2024 trouxe igualdade racial + eventos climáticos RS
- **Chaves**: `id_municipio`
- **Por quê**: refresh pequeno do `br_ibge_munic`/`br_ibge_estadic` que estão stale.
- **Status BD**: até ~2019–21

#### 9. ANTT RNTRC (+ veículos, CIOT)
- **Fonte**: https://dados.antt.gov.br/dataset/rntrc , rntrc-veiculos, ciot
- **Freq**: mensal (snapshot) · **Formato**: CSV ~70MB/mês · **Volume**: ~2M transportadores (TAC/ETC/CTC) + frota
- **Chaves**: cnpj/cpf, id_municipio
- **Nota**: ANTT está no bucket blocked→mcp-todo por WAF; o portal CKAN `dados.antt.gov.br` pode ser caminho alternativo.
- **Status BD**: não
- **2026-09-02**: re-testado — o caminho CKAN alternativo também apanha. `dados.antt.gov.br/dataset/rntrc`
  (HTML) responde 200, mas a API (`/api/3/action/package_show`) devolve um HTML de rejeição de WAF
  ("Request Rejected... consult your administrator", assinatura de F5 BigIP ASM) — mesmo bloqueio,
  camada diferente. Confirma que continua bloqueado, não é achado novo.

#### 10. CNJ — Painel Justiça em Números (agregados)
- **Fonte**: https://paineis.cnj.jus.br (downloads agregados); microdado DataJud fica no bucket deferred-api_key por Res. 331/2020
- **Chaves**: tribunal, município (unidade judiciária), CNPJ de partes PJ nos agregados de litigiosidade
- **Status BD**: não

#### 11. BCB SCR.data + Desenrola Brasil
- **Fonte**: https://www.bcb.gov.br/estabilidadefinanceira/scrdata ; dataset Desenrola no portal de dados abertos do BCB
- **Freq**: mensal · **Formato**: CSV.zip
- **Chaves**: município × CNAE × porte × modalidade
- **Por quê**: crédito por dupla chave que o rodado domina.
- **Status BD**: não

### Tier 3 — valioso, escopo mais estreito

| # | Dataset | Fonte | Chave | Status BD |
|---|---|---|---|---|
| 12 | Emendas parlamentares (bulk CGU) | portaldatransparencia.gov.br/download-de-dados/emendas | autor, id_municipio, código SIAFI | não (só via mirror CGU parcial) |
| 13 | ANP cadastro de revendas (postos/GLP, bandeira) | gov.br/anp dados abertos | CNPJ | não — enriquece `br_anp_combustiveis.precos`. **2026-09-02**: achei o dataset em `dados.gov.br/dados/conjuntos-dados/relacao-de-revendedores-varejistas-de-combustiveis-automotivos` (página HTML 200), mas a API do `dados.gov.br` novo (`/api/3/action/package_show`) devolve **401** mesmo pra leitura pública — a plataforma passou a exigir chave de API que não temos. Vira item gated por credencial, sai da lista de "sem chave" |
| 14 | CadÚnico agregados municipais | MDS VIS DATA / portal analítico | id_municipio | não (só painéis) |
| 15 | CAUC / Tesouro Transparente — regularidade fiscal | tesourotransparente.gov.br | codigo_siafi/id_municipio | não — pré-requisito de convênios, casa com Transferegov |
| 16 | PNS 2023 microdados | IBGE FTP | UF/região (chave fraca) | BD não tem 2023 |
| 17 | PRODES/DETER BiomasBR all-biomas | terrabrasilis.dpi.inpe.br/downloads/ + API v1 | id_municipio | BD/espelho têm versões antigas só Amazônia/Cerrado; desde 2024–26 cobre todos os biomas com Sentinel-2 |
| 18 | DIRPF destinações FDCA/FDI | gov.br/receitafederal/dados | CNPJ do fundo/município | não |
| 19 | Corpus PT-BR (Jabuticaba etc., HF Parquet) | huggingface.co | — | relevante só p/ treinar PT-BR do `ask`, não é join-analítico |
| 20 | TCEs estaduais (11 cortes: SP, RJ, RS, PE, CE, ES, RN, PI, SC, TO, PA) | portais/API de cada corte | cnpj, id_municipio | não — 11 fontes distintas, esforço alto; achado na comparação com o mcp-brasil |
| 21 | SPU SIAPA — imóveis da União | gov.br/spu | id_municipio, CEP | não — ~813K imóveis; idem |

### Ordem recomendada

1. **Quick-wins internos primeiro**: `br_bcb_taxa_cambio`/`taxa_selic`; MUNIC/ESTADIC 2023-24 via SIDRA; retomar Consumidor.gov (16 arquivos) e buraco do Querido Diário quando fontes voltarem.
2. **Tier 1 externo**, todos bulk/API sem chave, chaves de join já dominadas, padrão fetch→Parquet→rsync→regenerar catálogo:
   - PNCP → benefícios CGU (Gás do Povo + Novo Bolsa Família; validar Pé-de-Meia) → Transferegov completo → Pix por município → SINESP VDE.
3. **Tier 2** conforme cota BigQuery Sandbox sobrar e drift interno fechar (CNEFE é o mais pesado — planejar janela própria).
4. **Tier 3** por oportunidade. Dos achados na comparação com o mcp-brasil, TCEs (#20) é o de maior valor e o de maior esforço — 11 APIs sem padrão comum; INFOPEN/PROCON e SIAPA fazem mais sentido como tool live (padrão `consultar_*`) do que como ETL.

### Chaves de join exploradas pelos candidatos

| Chave | Candidatos |
|---|---|
| CNPJ | PNCP, Transferegov, RNTRC, SCR, ComprasNet, ANP cadastros, Emendas |
| id_municipio | Pix/BCB, SINESP, PRODES/DETER, MUNIC, CadÚnico, Querido Diário, benefícios CGU, CAUC |
| NIS/CPF mascarado | Benefícios CGU (BF, Pé-de-Meia, Gás do Povo, BPC), CadÚnico (agregado) |
| CEP/setor censitário | CNEFE (ponte faltante) |
| CID-10 | SINESP↔SIM cross-check, PNS |

### Execução 2026-08-27 — os quick-wins internos

#### `br_bcb_taxa_cambio`/`taxa_selic` — continuam bloqueados, mas por um motivo diferente do que se pensava

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

#### MUNIC/ESTADIC 2023-2024 — não é row drift, é a própria BD estar parada

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

#### Consumidor.gov.br — pulado, conforme instrução (outro agente já investigando; ver `tasks/done/threads_pos_scraping_2026-07.md`)

#### Buraco do Querido Diário — investigado, nada executado

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

---

# Parte II — Licenciamento e poluição ambiental (2026-09-01)

> Aberto em 2026-09-01, saído do levantamento de poluentes atmosféricos de Nova
> Friburgo (`pages/analises/poluentes-do-ar-em-nova-friburgo/`, gerado por
> `scripts/gera_relatorio_nf.py`). Aquele relatório reconstrói "atividade
> potencialmente poluidora" **por CNAE**, porque não existe no espelho nenhuma
> base que diga quem é licenciado, com que número de processo, por qual órgão.
> Os campos ficaram explicitamente como "não pôde ser confirmado". Esta lista é o
> que fecharia cada buraco, em ordem de quanto fecha.
>
> Complementa `tasks/datasets_to_scrap.md` (o catálogo geral) — as entradas que
> saírem daqui para a fila de raspagem vão para lá.

### 1. INEA/RJ — licenças ambientais estaduais 🔴 o buraco central

**Fecha:** situação do licenciamento (LP/LI/LO), número do processo, número da
licença, validade, órgão, condicionantes.
**Onde:** portal do INEA (consulta pública de licenças ambientais) e publicações
de concessão no Diário Oficial do Estado do RJ (DOERJ).
**Chave de join:** CNPJ e/ou razão social + município.
**Por que importa:** hoje o relatório reporta *situação cadastral na Receita
Federal* e precisa avisar, em cada seção, que isso não é licenciamento. Com esta
base, quatro colunas do pedido original passam de "não confirmado" para dado.
**Risco:** consulta provavelmente com formulário/captcha; o caminho DOERJ (texto)
pode ser mais estável que o portal.

### 2. IBAMA — CTF/APP, Cadastro Técnico Federal de Atividades Potencialmente Poluidoras 🔴

**Fecha:** quem se declara atividade potencialmente poluidora, em que categoria e
porte — literalmente o universo que o relatório reconstrói por CNAE.
**Onde:** IBAMA dados abertos / relatórios do CTF-APP e TCFA.
**Chave:** CNPJ.
**Por que importa:** permite medir o erro do proxy por CNAE nos dois sentidos —
quem exerce a atividade sem estar cadastrado, e quem está cadastrado sob CNAE que
o recorte não pega. Também dá porte declarado, que o CNAE não dá.

### 3. IBAMA — autos de infração e sanções administrativas 🟠

**Fecha:** histórico de autuação ambiental por empresa, com tipificação (inclui
poluição atmosférica).
**Onde:** IBAMA dados abertos (autos de infração; distinto dos embargos).
**Chave:** CPF/CNPJ.
**Situação hoje:** o espelho tem só `br_ibama_embargos` — conferido, deu **zero**
para os 1.581 CNPJs do levantamento, em qualquer município do país. Embargo é
majoritariamente desmatamento; auto de infração é onde poluição industrial
apareceria.
**Nota técnica:** `br_ibama_embargos/termo_embargo/*.parquet` está gravado como
**uma coluna VARCHAR** com os campos separados por `;` — o CSV foi parseado
errado na raspagem. Reprocessar junto.

### 4. ANM / SIGMINE — títulos minerários 🟠

**Fecha:** número do processo oficial da categoria "extração de minerais não
metálicos" (20 ativos no levantamento), substância (areia, argila, brita,
granito), fase (requerimento / autorização de pesquisa / concessão de lavra /
guia de utilização), polígono e titular.
**Onde:** ANM dados abertos + SIGMINE (shapefile/CSV público, fácil de ETL).
**Chave:** CNPJ do titular + município + geometria.
**Bônus:** cruzar polígono com CNPJ revela lavra titulada sem CNPJ ativo
correspondente no município — e o contrário.

### 5. Diário Oficial de Nova Friburgo, texto completo 🟡 meio caminho andado

**Fecha:** licenciamento **municipal** de impacto local — que é competência da
prefeitura desde pelo menos 2012 (IBGE MUNIC), com LP/LI/LO concedidas.
**Situação hoje:** `br_ok_queridodiario.diarios` já tem **634 edições** de Nova
Friburgo (2023-10-17 a 2025-10-03) espelhadas — **mas só os metadados e a URL**.
Falta baixar o `txt_url` de cada edição e indexar o texto.
**Esforço:** baixo. 634 arquivos de texto, um índice full-text no DuckDB.
**Generaliza:** o mesmo passo serve para todos os municípios do Querido Diário —
vale fazer genérico, não só para Nova Friburgo.

### 7. PNCP — Portal Nacional de Contratações Públicas 🟡

**Fecha:** contrato com o poder público além do que o TCE-RJ registra.
**Situação hoje:** o cruzamento achou 6 empresas com contrato (4 via
`br_tce_rj.contratos_municipio`, 2 via `br_cgu_licitacao_contrato`). O TCE-RJ tem
96 mil contratos e o CGU só cobre o federal; o PNCP cobre contratação municipal
de todo o país pós-2021.

### 8. Emissões e qualidade do ar 🟢 contexto, não cadastro

- **SEEG / inventário municipal de emissões** — emissão estimada por município e
  setor. Liga o cadastro à grandeza física.
- **INEA — rede de monitoramento da qualidade do ar do RJ** — séries das
  estações. Nova Friburgo provavelmente não tem estação; confirmar.

**Por que importa:** hoje o relatório mede *fontes potenciais*, nunca poluente
emitido ou medido. Sem uma destas duas, não há como ligar "553 oficinas de
produtos de metal" a nenhuma concentração de poluente.

---

### Já conferido e negativo (não precisa raspar de novo)

| Base | Resultado no levantamento |
|---|---|
| `br_ibama_embargos` | 0 embargos, tanto no município quanto por CNPJ em todo o país |
| `br_tcu_inidoneos.empresas` | 0 dos 1.581 CNPJs |
| **RAIS identificada 2022+** | **Sem fonte pública — item removido da fila em 2026-09-01.** O FTP do PDET está no ar e tem até 2024 (`ftp.mtps.gov.br/pdet/microdados/RAIS/2024/`), mas publica só os arquivos `_PUB`, sem CNPJ; a versão identificada é restrita. Não é pendência de raspagem, é ausência de fonte |
| `br_pgfn_dividaativa.divida` | 237 empresas, 1.990 inscrições — **tudo tributário**, nenhuma inscrição de multa ambiental. Fora do relatório por ser off-topic |

---

### Execução — 2026-09-01

Levantamento de rota feito item a item, com teste real de rede em cada fonte.
O que estava marcado como "provavelmente com formulário/captcha" acabou sendo
outra coisa: **geo-bloqueio por IP**. Registro do que se descobriu:

#### Rotas confirmadas e ETL feito

**ANM (item 4) — completo.** A URL antiga (`app.anm.gov.br/dadosabertos`) morreu;
a viva é `dadosabertos.anm.gov.br`, uma listagem IIS aberta, sem auth, regerada
diariamente. Três diretórios importam:

- `SCM/*.csv` — 13 arquivos com `Processo`, `Fase Atual`, `CPF/CNPJ do titular`,
  `Titular`, `Municipio(s)`, `Substância(s)`, `Situação`. É o item 4 inteiro.
- `CFEM/*.csv` — arrecadação e distribuição por CNPJ/substância/município/mês,
  **com `QuantidadeComercializada` e `ValorRecolhido`**. Não estava previsto: é
  grandeza física de extração, cobre parte do que o item 8 pedia.
- `SIGMINE/PROCESSOS_MINERARIOS/{UF}.zip` — shapefile por UF (polígono, fase,
  substância, titular). Sem CNPJ e sem coluna de município: o município vem do
  SCM, ou de join espacial.

Em `~/rodado/br_anm/`: 21 tabelas + 28 partições de UF do SIGMINE.

Três armadilhas de parsing, todas na origem, todas custaram tempo:
1. Os CSV são **CP1252**, não latin-1 puro — `read_csv(encoding='latin-1')` do
   DuckDB recusa o arquivo inteiro. Passar por `iconv -f CP1252 -c`.
2. `CFEM_Autuacao.csv` usa `;`; todo o resto usa `,`. Detectar por arquivo.
3. Há linhas com aspas duplicadas abrindo campo (`,""RAZAO SOCIAL`) que fundem
   dois registros em um. Com `ignore_errors=true` o DuckDB **descarta calado** e
   o resultado parece bom: `scm_licenciamento` deu 14.205 linhas assim, contra
   21.538 reais. A conversão hoje é um parser tolerante em Python
   (`_staging/anm/conv_anm4.py`) que repara a aspa e conta o que reparou.

#### Bloqueio real: geo-IP, não captcha

`dadosabertos.ibama.gov.br`, `pamgia.ibama.gov.br` e `www.ibama.gov.br` devolvem
403 de WAF (Cloudflare) para **qualquer** requisição saindo de IP não brasileiro
— testado com curl e com Chrome real, do laptop e do beelink. O INEA é pior:
`inea.rj.gov.br` resolve (187.62.129.119) mas **não completa o TCP**.

O Wayback guardou só o catálogo CKAN, nunca os arquivos. O que ele deu de útil
foram os padrões de URL, que o portal bloqueado não entrega:

- CTF/APP: `https://dadosabertos.ibama.gov.br/dados/CTF/APP/{UF}/pessoasJuridicas.csv`
- CTF/AIDA: `.../dados/CTF/AIDA/pessoasJuridicas.csv`
- Autos: `.../dados/SIFISC/auto_infracao/{tabela}/{tabela}_csv.zip`
- Embargos: `.../dados/SIFISC/termo_embargo/{tabela}/{tabela}_csv.zip`

Com um proxy de saída no Brasil o download roda normalmente
(`~/Downloads/ibama/baixa_ibama.sh` respeita `ALL_PROXY`).

#### Correção ao que este arquivo dizia

**`br_ibama_embargos` não é um negativo válido — é um espelho vazio.** O
problema não é só "uma coluna VARCHAR": `termo_embargo` tem 113.878 linhas com
**zero** não-vazias, `coordenadas` tem 64.562 com `max(length()) = 0`, e toda
subtabela repete o padrão. Os bytes nunca foram gravados. Logo:

- o "0 embargos para os 1.581 CNPJs" da tabela de conferidos não mediu nada;
- "reprocessar junto" não se aplica — não há o que reparsear localmente, é
  re-raspagem completa.

#### SEEG (item 8): existe API, não documentada

`plataforma.seeg.eco.br` é um SPA; o dado sai de um GraphQL público em
`api.plataforma.seeg.eco.br/graphql`. A query que serve é `emissionsSummary`
com `ranking: "City"` — devolve **os 5.606 municípios de uma vez, por setor,
em ~6 s**. Detalhes que custaram descoberta:

- `emissions` (a query de aparência óbvia) responde **500** sempre, com ou sem
  filtro. Não usar.
- `emissionsRanking` devolve só o **top 30**, mesmo com `territoriesIds` de um
  estado. Serve para ranking, não para colheita.
- `areas(territoryTypes: [City])` traz `code` = código IBGE de 7 dígitos para os
  **5.608** municípios, sem exceção. É a chave de join com o espelho.

#### INEA (item 1): tem dado estruturado, não só PDF

O portal `sistemas.inea.rj.gov.br` só serve tela de login, e as páginas de
licenciamento do site são menu e norma. Mas a página do **Boletim de Serviço**
carrega um índice pesquisável em HTML — e ele já traz o registro estruturado,
sem abrir PDF nenhum: número do boletim, data, os **processos SEI**, o **nome de
cada empresa/requerente** e o **tipo de ato** (`licença de operação`,
`licença ambiental unificada`, `licença prévia`, `indeferimento`…). O PDF é
anexo, não a fonte.

É formulário GET simples, sem AJAX e sem nonce:

```
GET https://www.inea.rj.gov.br/inea-licenciamento-pos-licenca-e-fiscalizacao/boletim-de-servico
    ?paged=N                    # 12 resultados por página
    &ic_b_document_type=<tipo>  # ex.: "licença de operação"
    &ic_data_inicio=DD/MM/AAAA&ic_data_fim=DD/MM/AAAA
    &ic_b_processo=<n do processo>
```

Colhido: **1.081 boletins, 28/01/2019 a 26/08/2026**, com 7.161 processos SEI e
6.877 empresas → `br_inea_boletim/{boletins,empresas,processos}`.

**Duas armadilhas que custaram um reparse.** A numeração do boletim **reinicia a
cada ano** — deduplicar por número colapsa `n158/2021` com `n158/2026` e some com
80% dos registros (226 no lugar de 1.081). A chave estável é a URL do PDF, que
carrega o ano no caminho (`/uploads/2021/11/`). E o rótulo da data vem colado ao
valor no texto limpo (`Data do boletim: 29/12/2025`), sem tag entre os dois:
regex que espera um `<tag>` no meio devolve `None` calado para todo o conjunto.

O acervo anterior a 2019 fica noutro lugar — `portalproderj.inea.rj.gov.br`,
ainda não raspado.

#### SEEG: colhido

**12.106.780 linhas**, 5.601 municípios, 1990–2024, por setor e por subcategoria,
5 gases × 5 tipos de emissão → `br_seeg/emissoes_municipais`, particionado por
`agrupamento` e `gas_id`. O `code` da API (IBGE de 7 dígitos) entra como
`id_municipio` e liga direto com o resto do espelho.

---

### O que falta para fechar — situação em 2026-09-01, 20h

#### Ainda baixando (só tempo, nenhuma decisão pendente)

| Item | Onde parou | Falta | Depois |
|---|---|---|---|
| Querido Diário (5) | 398/524 municípios | 126 municípios | `_staging/qd/finaliza_qd.sh` move para `br_ok_queridodiario_texto/` |
| PNCP (7) | jul/2024 | 77 janelas de 10 dias (de 206) | `_staging/pncp/converte_pncp.py` |

#### Lacunas que não fecham sozinhas

1. **INEA anterior a 2019.** O índice pesquisável do Boletim de Serviço começa em
   28/01/2019. O acervo velho está em `portalproderj.inea.rj.gov.br` — outro
   sistema, que **não responde nem pelo proxy BR** (timeout, 2026-09-01). Pode
   estar desativado. Enquanto isso, o item 1 cobre 2019–2026, não a série toda.

2. **`tipos_documento` mal parseado.** O split por espaço duplo não separa a
   lista de tipos: dá 142 "indeferimento" e 34 "autorização ambiental" para 1.081
   boletins, ordem de grandeza abaixo do esperado. Os campos que importam
   (empresa, processo SEI, data, PDF) estão corretos — este é o único errado.
   Reparse é de graça: os HTML estão em `~/Downloads/inea/boletins/pg*.html`.

3. **Os 1.081 PDFs do INEA não foram baixados**, só o índice. É neles que estão
   **validade da licença e condicionantes** — dois dos campos que o relatório de
   Nova Friburgo pedia e que o índice não traz.

4. **`SIGMINE/BRASIL.zip` (125 MB) foi pulado de propósito** — consolidado
   nacional, redundante com as 28 UFs já convertidas. Registro para não parecer
   falha de coleta.

5. **Qualidade do ar (item 8, segunda metade) não foi tocada.** O SEEG fechou a
   parte de emissão estimada; a rede de monitoramento do INEA continua sem
   raspar, e segue sem confirmar se Nova Friburgo tem estação.

#### Placar

| Dataset | Linhas | Período |
|---|---|---|
| `br_ibama_ctf` | 1.473.755 | ~1985–2025 |
| `br_ibama_autos` | 3.021.141 | 1977–2026 |
| `br_ibama_embargos_novo` | 892.279 | 2001–2026 |
| `br_anm` (21 tab + 28 UF) | 8.324.108 | processos desde 1935 |
| `br_seeg/emissoes_municipais` | 12.106.780 | 1990–2024, 5.601 municípios |
| `br_inea_boletim` | 1.081 boletins · 7.161 processos · 6.877 empresas | 2019–2026 |

**25.818.344 linhas em 6 datasets novos.**

`br_ibama_embargos` (o antigo, vazio) continua no disco e **deve ser removido ou
marcado como obsoleto** — quem consultar ele em vez de `br_ibama_embargos_novo`
recebe zero e acha que é resposta.

---

## Execução 2026-09-02 (segunda rodada) — Tier 1 externo

Trabalhando a "Ordem recomendada" de cima para baixo. PNCP (#1) já estava em
coleta por outro processo em paralelo (`_staging/pncp/`) — não foi tocado aqui.
Os itens #4 (Pix) e #5 (SINESP) foram investigados a fundo e **não são
credencial** — são fonte quebrada (Pix) e WAF (SINESP); ver as notas inline
nos itens acima. #7 (ANEEL) e #9 (ANTT) foram re-testados e continuam
bloqueados, motivo confirmado, sem contorno novo.

### Gás do Povo — feito

`br_cgu_gas_do_povo/gas_do_povo/` — CSV mensal de
`portaldatransparencia.gov.br/download-de-dados/gas-do-povo`, baixado via CDN
direto (`dadosabertos-download.cgu.gov.br`, sem chave), CP1252 → UTF-8 via
`iconv`, convertido a parquet+zstd com DuckDB no próprio beelink (o host tem
acesso direto ao CDN — não precisou passar pelo laptop).

**Verificado no beelink (readonly):**

```sql
SELECT count(*), min(mes_referencia), max(mes_referencia)
FROM read_parquet('~/rodado/br_cgu_gas_do_povo/gas_do_povo/*.parquet');
-- 20.817.231 linhas · 202511 → 202607 (8/8 meses, completo)
```

**Correção 2026-09-02, mais tarde:** a contagem de 34.846.839 registrada antes nesta mesma
seção estava errada — duplicada por uma sessão paralela que, sem saber deste job já em
andamento no beelink, rodou `scripts/scrap/portal_transparencia.py` a partir do laptop para
o mesmo dataset e gravou 6 arquivos extras na mesma pasta com outro padrão de nome
(`2025_11_gas_do_povo.parquet` etc., em vez de `202511.parquet`) — mesmo conteúdo, nome
diferente, então `read_parquet('*.parquet')` contava as duas cópias. Os 6 arquivos
duplicados foram identificados (contagem por arquivo batendo par a par) e removidos; a
contagem real e final é 20.817.231. `scripts/scrap/portal_transparencia.py` ganhou uma
entrada `gas-do-povo` no `DATA_DICT` como efeito colateral dessa colisão — fica como
scraper reutilizável de git para reprocessamentos incrementais futuros, mas **não rodar de
novo sem checar primeiro se o job no beelink já não fez o mês** (ele não faz essa checagem
de existência antes de baixar).

Colunas: `mes_referencia, uf, codigo_municipio_siafi, nome_municipio,
cpf_beneficiario (mascarado na origem), nome_favorecido, cnpj_estabelecimento,
estabelecimento, quantidade_pessoas_familia, periodo_validade_vale_meses,
data_inicio_vigencia_vale, data_fim_vigencia_vale, data_retirada_vale,
valor_beneficio`. Chave de join: `cnpj_estabelecimento` (revenda de gás),
`codigo_municipio_siafi`.

### Novo Bolsa Família — em andamento, resumível

`br_cgu_novo_bolsa_familia/novo_bolsa_familia/` — mesmo padrão, mas 41 meses
(2023-03 a 2026-07) de ~2,2 GB de CSV cru cada, então é um job muito mais
longo. No momento em que este arquivo foi escrito:

```sql
SELECT count(*), min(ano_mes), max(ano_mes), count(distinct ano_mes)
FROM read_parquet('~/rodado/br_cgu_novo_bolsa_familia/novo_bolsa_familia/*.parquet');
-- 184.099.724 linhas · 202303 → 202311 · 9 de 41 meses feitos
```

Colunas: `ano_mes, mes_competencia, mes_referencia, uf, codigo_municipio_siafi,
nome_municipio, cpf_favorecido (mascarado), nis_favorecido, nome_favorecido,
valor_parcela`.

**Script**: `~/rodado/_staging/fetch_cgu.sh` no beelink (cópia do que gerou
este job). **Resumível por design** — pula qualquer `{ano_mes}.parquet` que já
exista, então rodar de novo não reprocessa o que já foi feito:

```bash
ssh beelink 'nohup bash ~/rodado/_staging/fetch_cgu.sh > ~/rodado/_staging/cgu_beneficios/run.log 2>&1 < /dev/null & disown'
# acompanhar:
ssh beelink 'tail -f ~/rodado/_staging/cgu_beneficios/run.log'
# checar se ainda roda:
ssh beelink 'ps aux | grep fetch_cgu.sh | grep -v grep'
```

Estava rodando (processo vivo no beelink) no momento em que esta sessão
encerrou — não foi morto, só não foi esperado até o fim porque 41 arquivos de
~2,2 GB cada não cabe no orçamento de uma sessão. Terminando, o total esperado
é da ordem de 700-800M linhas (9 meses já deram 184M, ritmo consistente de
~20M linhas/mês).

### Transferegov/SICONV completo — em andamento, resumível

`br_transferegov_siconv/<tabela>/dados.parquet` — dataset novo, separado do
`br_transferegov` existente (que usa nomes de tabela normalizados da própria
BD — `planos_acao`, `programas`, `transferencias` — diferentes da estrutura
crua do SICONV). O diretório `repositorio.dados.gov.br/seges/detru/` tem
**54 arquivos** `.zip`; pulado de propósito `siconv.zip` (3 GB, consolidado,
redundante com os CSVs individuais — mesmo raciocínio do `SIGMINE/BRASIL.zip`
pulado no ANM), `data_carga_siconv.csv.zip` (metadado de timestamp, não dado)
e `modelo_dados_siconv.zip` (dicionário de dados, não dado). CSV é UTF-8 com
BOM, `;`-delimitado, direto — sem a armadilha de encoding do CGU.

No momento em que este arquivo foi escrito, **23 das ~50 tabelas candidatas**
já landed, soma parcial:

| Tabela | Linhas |
|---|---|
| `siconv_itens_dl` | 9.805.615 |
| `siconv_dl` | 7.487.823 |
| `siconv_historico_situacao` | 8.957.864 |
| `siconv_cronograma_desembolso` | 2.732.825 |
| `siconv_etapa_crono_fisico` | 3.272.439 |
| `siconv_contrato` | 726.602 |
| `siconv_convenio` | 285.743 |
| `siconv_apoiadores_emendas_programas` | 291.954 |
| `siconv_emenda` | 297.828 |
| `siconv_historico_projeto_basico` | 1.061.746 |
| (+ 13 tabelas menores) | — |

**~37,4M linhas somadas até aqui**, com as tabelas maiores restantes
(`siconv_itens_licitacao` 210MB zip, `siconv_justificativas_proposta` 682MB
zip, `siconv_pagamento` 328MB zip, `siconv_plano_aplicacao` 267MB zip,
`siconv_proposta` 190MB zip) ainda por vir — o total final deve passar de
60-80M linhas.

Três arquivos zip têm **mais de um CSV membro** (`siconv_inst_cont_aio_mod_empresas.csv.zip`
trouxe 3: `..._contratos_lotes_empresas_modulo_empresas`,
`..._metas_submetas_po_modulo_empresas`, `..._proposta_aio_modulo_empresas`) — o
script detecta isso e **pula com log**, em vez de adivinhar qual pegar; ficam
para uma segunda passada que trate zips multi-membro explicitamente.

**Script**: `~/rodado/_staging/fetch_transferegov.sh` no beelink. Também
resumível (pula tabela cujo `dados.parquet` já existe):

```bash
ssh beelink 'nohup bash ~/rodado/_staging/fetch_transferegov.sh > ~/rodado/_staging/transferegov/run.log 2>&1 < /dev/null & disown'
ssh beelink 'tail -f ~/rodado/_staging/transferegov/run.log'
ssh beelink 'ps aux | grep fetch_transferegov.sh | grep -v grep'
```

Também deixado rodando (processo vivo) ao encerrar a sessão.

### Depois que os dois jobs terminarem

Nenhum dos dois datasets novos (`br_cgu_gas_do_povo`, `br_cgu_novo_bolsa_familia`,
`br_transferegov_siconv`) passou ainda pelo regen de metadados — falta, nessa
ordem, depois que `fetch_cgu.sh`/`fetch_transferegov.sh` terminarem:

```bash
python3 scripts/gera_schemas.py
python3 scripts/sync_mcp_schema.py
python3 scripts/build_metadata_catalog.py
python3 scripts/gera_join_keys.py
```

(`gera_schema_graph.py`/`build_atlas.py` se quiser os três novos datasets no
Atlas também.)

### Itens não tocados nesta rodada

Tier 2/3 além de #7/#9 (CNEFE #6, CadÚnico #14, CAUC #15, PNS 2023 #16,
PRODES/DETER #17, DIRPF #18, TCEs estaduais #20, SPU SIAPA #21) não foram
investigados nesta sessão — nem confirmados como bloqueados nem como viáveis,
simplesmente não houve tempo depois de #1-#5, #7, #9, #13. CNJ Painel (#10) e
BCB SCR.data/Desenrola (#11) tiveram um teste de conectividade rápido (ambos
respondem HTTP 200/302) mas não foram explorados a fundo — provavelmente
dashboards embarcados (Power BI) sem endpoint de bulk download óbvio, precisa
de investigação própria antes de virar ETL.
