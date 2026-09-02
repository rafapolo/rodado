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

#### 2. Benefícios CGU novos: Pé-de-Meia, Gás do Povo, Novo Bolsa Família ✅ feito e com view — ver Execução 2026-09-02
- **Fonte**: https://portaldatransparencia.gov.br/download-de-dados (CSV zipados mensais)
- **Volume**: BF ~20M famílias/mês; Pé-de-Meia ~3M/mês; Gás do Povo ~15M famílias (nov/2025+)
- **Chaves**: NIS, CPF mascarado, município/UF; Gás do Povo traz CNPJ da revenda
- **Por quê**: Pé-de-Meia cruza com Censo Escolar (aluno/escola) que já se tem. Nota: `pe_de_meia` bulk já foi baixada (~64M rows no beelink via Portal da Transparência) — validar cobertura vs. esta fonte; **Gás do Povo e Novo Bolsa Família não existem**.
- **Status BD**: Auxílio Emergencial/Auxílio Brasil parciais na BD; Pé-de-Meia/Gás do Povo não existem
- **2026-09-02**: Gás do Povo **feito** (`br_cgu_gas_do_povo`, 20.817.231 linhas, 8/8 meses — a contagem
  de 34.846.839 registrada mais cedo hoje estava inflada por um `.parquet` duplicado que uma sessão
  paralela gravou por engano na mesma pasta com outro padrão de nome; removido e recontado, ver
  Execução abaixo). Novo Bolsa Família **feito** (`br_cgu_novo_bolsa_familia`, 821.346.847 linhas,
  41/41 meses). **View criada em ambos e conferida por `count(*)`** (terceira rodada, 2026-09-02) — ver
  Execução abaixo.

#### 3. Transferegov.br (ex-SICONV) — transferências completas ✅ feito e com view — ver Execução 2026-09-02
- **Fonte**: http://repositorio.dados.gov.br/seges/detru/
- **Freq**: diária (extração às 9h) · **Formato**: CSV.zip · **Volume**: ~20 tabelas, dezenas de GB histórico (na verdade **54** arquivos CSV.zip no diretório, ver Execução)
- **Chaves**: `cnpj` proponente/convenente, `codigo_ibge`
- **Por quê**: fluxo integral União→municípios/OSC (convênios, propostas, empenhos, desembolsos, pagamentos a favorecidos). Casa com Siconfi/SIOP/TransfereGov parcial já existente (`br_transferegov` tem só 3 tabelas).
- **Status BD**: não
- **2026-09-02**: **feito** (`br_transferegov_siconv`, 62 tabelas, 69.060.758 linhas — incluindo os 5
  zips multi-membro recuperados na terceira rodada). View criada e conferida por `count(*)` em cada
  tabela — ver Execução abaixo.

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

#### 6. CNEFE Censo 2022 (Cadastro Nacional de Endereços) ✅ feito 2026-09-02
- **Fonte real**: `ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/Censo_Demografico_2022/Arquivos_CNEFE/CSV/UF/` (não fica debaixo de `Censos/Censo_Demografico_2022/` como a entrada original supunha — divulgado jun/2024)
- **Volume**: 111.102.875 endereços com coordenadas, setor censitário, CEP, face de quadra — 2,8 GB em parquet+zstd, CSV por UF
- **Chaves**: **CEP ↔ setor censitário ↔ id_municipio** — a grande ponte faltante para geolocalizar qualquer base
- **Status BD**: `br_ibge_cnefe.enderecos`, ver Execução 2026-09-02 (terceira rodada)

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

#### 10. CNJ — Painel Justiça em Números (agregados) ❌ serviço fora do ar
- **Fonte**: https://paineis.cnj.jus.br (downloads agregados); microdado DataJud fica no bucket deferred-api_key por Res. 331/2020
- **Chaves**: tribunal, município (unidade judiciária), CNPJ de partes PJ nos agregados de litigiosidade
- **Status BD**: não — **2026-09-02**: `paineis.cnj.jus.br` devolve 502 Bad Gateway de forma consistente (3 tentativas), balanceador do próprio CNJ rejeitando. Rota alternativa `cnj.jus.br/paineis-de-dados` dá 404. Reteste depois — pode ser transitório

#### 11. BCB SCR.data + Desenrola Brasil ✅ feito 2026-09-02
- **Fonte**: catálogo CKAN `dadosabertos.bcb.gov.br` (`scr_data`, `desenrola-brasil`) — URLs reais de download em `bcb.gov.br/pda/desig/scrdata_{ANO}.zip` (V2, 2012–2026 completo) e `.../desenrola/dados_desenrola.csv`
- **Freq**: mensal · **Formato**: CSV.zip
- **Chaves**: UF × CNAE/ocupação × porte × modalidade (SCR.data não tem `id_municipio`, grão é UF)
- **Por quê**: crédito por dupla chave que o rodado domina.
- **Status BD**: `br_bcb_scrdata.dados` (169 meses, 2012-07 a 2026-07, 43.061.984 linhas) e `br_bcb_desenrola.dados` (12.751 linhas), ver Execução 2026-09-02 (terceira rodada)

### Tier 3 — valioso, escopo mais estreito

| # | Dataset | Fonte | Chave | Status BD |
|---|---|---|---|---|
| 12 | Emendas parlamentares (bulk CGU) | portaldatransparencia.gov.br/download-de-dados/emendas | autor, id_municipio, código SIAFI | não (só via mirror CGU parcial) |
| 13 | ANP cadastro de revendas (postos/GLP, bandeira) | gov.br/anp dados abertos | CNPJ | não — enriquece `br_anp_combustiveis.precos`. **2026-09-02**: achei o dataset em `dados.gov.br/dados/conjuntos-dados/relacao-de-revendedores-varejistas-de-combustiveis-automotivos` (página HTML 200), mas a API do `dados.gov.br` novo (`/api/3/action/package_show`) devolve **401** mesmo pra leitura pública — a plataforma passou a exigir chave de API que não temos. Vira item gated por credencial, sai da lista de "sem chave" |
| 14 | CadÚnico agregados municipais | MDS VIS DATA / portal analítico | id_municipio | não (só painéis) — **2026-09-02**: bloqueado, `aplicacoes.mds.gov.br` trava no TLS handshake (laptop e beelink), não é credencial |
| 15 | CAUC / Tesouro Transparente — regularidade fiscal | tesourotransparente.gov.br | codigo_siafi/id_municipio | **2026-09-02: feito** — `br_tesouro_cauc.{situacao_estados,situacao_municipios,legenda_itens}` |
| 16 | PNS 2023 microdados | IBGE FTP | UF/região (chave fraca) | BD não tem 2023 — **2026-09-02**: confirmado que a PNS 2023 ainda não foi publicada no FTP público (só 2013/2019 existem), não é bloqueio de acesso |
| 17 | PRODES/DETER BiomasBR all-biomas | terrabrasilis.dpi.inpe.br/downloads/ + API v1 | id_municipio | BD/espelho têm versões antigas só Amazônia/Cerrado; desde 2024–26 cobre todos os biomas com Sentinel-2 — **2026-09-02**: DETER (avisos quase em tempo real, 4 biomas) feito em `br_inpe_deter.avisos`; PRODES acumulado (polígonos, >800MB/bioma) segue como "janela própria" |
| 18 | DIRPF destinações FDCA/FDI | gov.br/receitafederal/dados | CNPJ do fundo/município | **2026-09-02: feito** (lista de fundos habilitados) — `br_rf_dirpf.fundos_habilitados`; valores destinados por declaração seguem sem achar |
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

**Checagem 2026-09-02, mais tarde:** o job do PNCP não está mais rodando —
`persistente.log` no beelink registra `sem progresso entre rodadas — fonte
esgotada, parando` às 18:49, depois de 3 rodadas travadas em ~3.545 páginas
faltando. `br_pncp.contratos` está em **1.979.024 linhas** agora (confirmado
via `count(*)` no beelink, readonly), contra os 1.412.466 registrados antes
desta sessão — progresso real, mas o job parou sozinho, não terminou. Para
retomar: `nohup bash ~/rodado/_staging/pncp/duplo.sh &` no beelink (mesmo
comando de sempre, resumível por `stat`) — mas vale esperar a janela de rate
limit por IP abrir de novo antes, já que "fonte esgotada" é sinal de cota
batida, não de bug.
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

### Novo Bolsa Família — feito

`br_cgu_novo_bolsa_familia/novo_bolsa_familia/` — mesmo padrão do Gás do Povo.
**Terminou sozinho no beelink** (job ficou rodando sem supervisão depois que
esta sessão parou de acompanhar; log mostra `=== DONE ===` às 16:42:48 de
2026-09-02). Verificado ao vivo:

```sql
SELECT count(*), min(ano_mes), max(ano_mes), count(distinct ano_mes)
FROM read_parquet('~/rodado/br_cgu_novo_bolsa_familia/novo_bolsa_familia/*.parquet');
-- 821.346.847 linhas · 202303 → 202607 · 41 de 41 meses (completo)
```

Colunas: `ano_mes, mes_competencia, mes_referencia, uf, codigo_municipio_siafi,
nome_municipio, cpf_favorecido (mascarado), nis_favorecido, nome_favorecido,
valor_parcela`.

**Falta**: registrar a view no `.duckdb` (parquet no disco, mas
`information_schema` não enxerga o dataset ainda — mesma armadilha
documentada em `datasets_to_scrap.md`; `scripts/sync/cria_views_novas.py`
resolve isso, não rodado ainda para este dataset) e o regen de metadado
(`gera_schemas.py` → `sync_mcp_schema.py` → `build_metadata_catalog.py`).

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

**Terminou sozinho no beelink** (log: `=== DONE transferegov ===` às 16:15:13
de 2026-09-02, sem supervisão depois que a sessão que o iniciou parou de
acompanhar). **48 tabelas landed, 66.107.314 linhas somadas**, confirmado por
`count(*)` tabela a tabela em 2026-09-02. Maiores: `siconv_itens_dl`
(9.805.615), `siconv_historico_situacao` (8.957.864), `siconv_dl`
(7.487.823), `siconv_pagamento` (7.359.136), `siconv_plano_aplicacao`
(4.855.746).

**5 zips ficaram de fora, motivo logado por arquivo — todos recuperados na
terceira rodada (2026-09-02), ver seção "Os 5 zips multi-membro" mais
abaixo**:

| Zip | Motivo original | Resolução |
|---|---|---|
| `siconv_acomp_obras_mod_empresas.csv.zip` | 2 membros CSV (esperado 1) | 2 tabelas landed |
| `siconv_inst_cont_aio_mod_empresas.csv.zip` | 3 membros CSV | 3 tabelas landed |
| `siconv_projeto_basico_mod_empresas.csv.zip` | 5 membros CSV | 5 tabelas landed |
| `siconv_proposta.csv.zip` | 0 membros CSV (zip vazio ou corrompido — checar na fonte) | download truncado numa tentativa anterior, não corrupção na fonte — 1 tabela landed |
| `siconv_vrpl_mod_empresas.csv.zip` | 3 membros CSV | 3 tabelas landed |

**View criada e conferida na terceira rodada (2026-09-02)** — ver seção de
Execução mais abaixo; as 62 tabelas (48 originais + 14 dos zips
multi-membro) têm view em `br_transferegov_siconv` e `count(*)` confere com
o disco.

**Script**: `~/rodado/_staging/fetch_transferegov.sh` no beelink — corrigido
na terceira rodada (extrai o membro `.csv` do zip por nome em vez de um
`unzip -p` cego, que corrompia o CSV quando o zip trazia um segundo membro
não-CSV). Resumível (pula tabela cujo `dados.parquet` já existe):

```bash
ssh beelink 'nohup bash ~/rodado/_staging/fetch_transferegov.sh > ~/rodado/_staging/transferegov/run.log 2>&1 < /dev/null & disown'
ssh beelink 'tail -f ~/rodado/_staging/transferegov/run.log'
```

### Views registradas e metadados regenerados — feito 2026-09-02 (terceira rodada)

Os três datasets — `br_cgu_gas_do_povo`, `br_cgu_novo_bolsa_familia`,
`br_transferegov_siconv` — ganharam view no `.duckdb` via
`scripts/sync/cria_views_novas.py`, e cada view foi conferida com
`SELECT count(*)` (readonly, via SSH, nunca só `read_parquet`):

| View | Linhas |
|---|---|
| `br_cgu_gas_do_povo.gas_do_povo` | 20.817.231 |
| `br_cgu_novo_bolsa_familia.novo_bolsa_familia` | 821.346.847 |
| `br_transferegov_siconv.*` (62 tabelas) | 69.060.758 |

Regen completo na ordem do `CLAUDE.md` (`gera_schemas.py` →
`sync_mcp_schema.py` → `build_metadata_catalog.py` → `gera_join_keys.py`),
rodado duas vezes (antes e depois de recuperar os 5 zips abaixo). Catálogo
final: **1.022 tabelas, 39,14 bi linhas**. Os três datasets aparecem em
`docs/context/all_tables.txt` e na view `_rodado_metadata` do beelink.
`gera_schema_graph.py`/`build_atlas.py` não foram rodados — ficam para quem
quiser os três novos datasets também no Atlas.

**Achado no caminho — 2 tabelas do Transferegov estavam sem parquet, fora
dos 5 zips já catalogados como pendentes:** `siconv_prop_inst_indicadores_estados`
e `siconv_prop_inst_indicadores_municipios` tinham diretório vazio no disco,
log com `FAIL parquet`. Causa: os dois zips-fonte trazem um **segundo membro
não-CSV** (um PDF de "campos de extração de dados"), e
`unzip -o -p "$zip" > "$csv"` sem apontar o nome do membro concatena
**todos** os arquivos do zip — o PDF binário se mistura ao CSV e o DuckDB
falha ao converter (silenciosamente, sem erro claro, só "FAIL parquet" no
log). O checador `nmembers -ne 1` só contava membros `.csv`, então passou
batido: 1 membro CSV, mas 2 membros no total. Reextraído apontando o nome do
membro `.csv` explicitamente, convertido, `dados.parquet` gravado
(12.349 + 236.467 linhas). `~/rodado/_staging/fetch_transferegov.sh` no
beelink foi corrigido para a próxima vez que rodar (extrai o membro `.csv`
por nome, resolvido via `unzip -l | grep -oE '.*\.csv$'`, em vez de um
`unzip -p` cego).

### Os 5 zips multi-membro — resolvidos 2026-09-02 (terceira rodada)

Todos os 5 continham dado genuíno, não lixo. Baixados de novo (o cache local
tinha expirado/sido limpo), inspecionados membro a membro, e cada membro
`.csv` distinto virou uma tabela própria — nome do membro sem o sufixo
redundante `_modulo_empresas` (os 5 zips-fonte já são "`_mod_empresas`", o
sufixo no nome do membro não carrega informação nova), mesmo padrão das 48
tabelas já landed:

| Zip | Membros → tabelas | Linhas |
|---|---|---|
| `siconv_acomp_obras_mod_empresas.csv.zip` | `siconv_acomp_obras_contratos_medicoes`, `siconv_acomp_obras_valores_itens_medicao` | 27.713 + 25.909 |
| `siconv_inst_cont_aio_mod_empresas.csv.zip` | `siconv_inst_cont_contratos_lotes_empresas`, `siconv_inst_cont_metas_submetas_po`, `siconv_inst_cont_proposta_aio` | 36.613 + 45.729 + 31.739 |
| `siconv_projeto_basico_mod_empresas.csv.zip` | `siconv_projeto_basico_acffo`, `_lae`, `_metas`, `_proposta`, `_submetas` | 63.644 + 219.059 + 273.336 + 101.260 + 417.785 |
| `siconv_proposta.csv.zip` | `siconv_proposta` (1 membro só) | 1.153.701 |
| `siconv_vrpl_mod_empresas.csv.zip` | `siconv_vrpl_lotes_fornecedores_licitacao`, `_metas_submetas`, `_proposta_licitacao` | 105.324 + 161.624 + 41.192 |

**`siconv_proposta.csv.zip` não estava corrompido nem vazio** — o "0 membros"
registrado antes era sintoma de um download truncado numa tentativa anterior
(a fonte, `repositorio.dados.gov.br`, entrega o arquivo completo: 199 MB
zipado, 1 único membro CSV de 750 MB, 1.153.701 linhas). Baixado de novo do
zero, `unzip -l` mostrou exatamente 1 membro `.csv`, conversão limpa.

Total: **2.704.628 linhas em 14 tabelas novas**, todas com view criada e
`count(*)` conferido. `br_transferegov_siconv` fecha em **62 tabelas,
69.060.758 linhas**.

### PNCP — restart confirmado, mas já estava rodando quando a sessão chegou

A instrução era reiniciar via `duplo.sh` (2 faixas: direto + proxy). Ao
checar antes de rodar, **já havia um job ativo** — `multi.sh` (variante mais
nova, 8 faixas A–H alternando rota direta/proxy, sem `sleep` entre páginas),
iniciado às 21:31:58 de 2026-09-02, PID raiz 2506225, reparented para `init`
(`nohup ... & disown`, não via cron — `crontab -l` não tem entrada de PNCP).
Confirmado com progresso real, não só processo pendurado: contagem de
arquivos JSON em `~/rodado/_staging/pncp/json/` subiu de 4.103 para 4.174 em
~6 minutos de observação, e os contadores "faltando" por faixa (`multi2.log`)
caem a cada passada.

**Decisão: não iniciar `duplo.sh` em paralelo.** O próprio `duplo.sh`
documenta que paralelizar do mesmo IP piora a cota (é rate-limit por IP, não
instabilidade da API — ver nota de 2026-09-02 no topo deste arquivo);
rodar as duas faixas de `duplo.sh` ao lado das 8 de `multi.sh` competiria
pela mesma cota e provavelmente derrubaria as duas. `multi.sh` já cobre o
mesmo objetivo (coleta ativa, resumível, roda sem supervisão) com mais
paralelismo que `duplo.sh` ofereceria.

**Como checar o progresso mais tarde:**

```bash
ssh beelink 'pgrep -fl multi.sh'                                   # confere se ainda está de pé
ssh beelink 'tail -20 ~/rodado/_staging/pncp/multi2.log'           # última passada por faixa
ssh beelink 'find ~/rodado/_staging/pncp/json -name "*.json" | wc -l'  # páginas já baixadas
ssh beelink '~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb' <<'SQL'
SELECT count(*) FROM br_pncp.contratos;
SQL
```

O `count(*)` só sobe depois de rodar `converte_pncp.py` sobre o JSON
acumulado (conversão json→parquet é passo separado, não automático dentro de
`multi.sh`) — para ver progresso em tempo real, o contador de arquivos JSON
é o sinal mais direto. Se o job parar sozinho de novo ("sem progresso entre
rodadas"), é cota de IP batida — esperar a janela abrir antes de tentar de
novo, não é bug para investigar.

### Itens não tocados nesta rodada — status revisado na rodada seguinte

A lista original (CNEFE #6, CadÚnico #14, CAUC #15, PNS 2023 #16, PRODES/DETER
#17, DIRPF #18, TCEs estaduais #20, SPU SIAPA #21, CNJ Painel #10, BCB
SCR.data/Desenrola #11) foi trabalhada item a item na rodada seguinte — ver
"Execução 2026-09-02 (terceira rodada)" logo abaixo.

---

## Execução 2026-09-02 (terceira rodada) — os itens não tocados

Trabalhando os 9 itens marcados como "não investigados" na rodada anterior
(CNEFE #6, CadÚnico #14, CAUC #15, PNS 2023 #16, PRODES/DETER #17, DIRPF #18,
TCEs estaduais #20, SPU SIAPA #21, CNJ Painel #10, BCB SCR.data/Desenrola
#11). Não tocado: as seções de Gás do Povo/Novo Bolsa Família/Transferegov/
PNCP acima (outra sessão trabalhando em paralelo no mesmo arquivo) nem
`datasets_to_scrap.md`/`espelho_subutilizado.md`/`respostas_pendentes.md`.

### CNEFE Censo 2022 (#6) — feito, microdado completo, não só o agregado

A fonte real é `ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/`
— **não** fica debaixo de `Censos/Censo_Demografico_2022/` (por isso o item
tinha ficado sem investigar: quem procura pelo caminho óbvio erra o diretório
e cai num 404). Duas rotas existem ali: `Agregados_por_CEP` (zip único de 9
MB, contagens por CEP) e `Arquivos_CNEFE/CSV/UF/` — **27 CSV, um por UF, ASCII
`;`-delimitado, 34 colunas, 3,9 GB zipados no total**. Fui pela segunda: é o
microdado completo, não o agregado, e é o que a entrada do arquivo já descrevia
como "a grande ponte faltante" — endereço a endereço, com `CEP`, `COD_SETOR`
(setor censitário — atenção: tem sufixo de letra às vezes, ex.
`140010005000549P`, por isso ficou `VARCHAR` e não numérico), `COD_MUNICIPIO`
(código IBGE 7 dígitos, compatível com `id_municipio` do resto do espelho) e
`LATITUDE`/`LONGITUDE`.

Script: baixa UF por UF, converte com `read_csv(..., all_varchar=true)` do
próprio DuckDB no beelink (rodou em segundos por UF, sem armadilha de
encoding — o CSV é puro ASCII, sem acento), resumível por `stat` do parquet
de saída.

**Verificado no beelink (readonly), view `br_ibge_cnefe.enderecos`:**

```sql
SELECT count(*) FROM br_ibge_cnefe.enderecos;
-- 111.102.875 linhas, 27 UFs, 2,8 GB em parquet+zstd
```

Bate com a estimativa original do item ("~110M endereços"). Colunas completas
em `docs/context/basedosdados-schema.json` (`br_ibge_cnefe.enderecos`).

### CAUC / Tesouro Transparente (#15) — feito

CKAN público (`tesourotransparente.gov.br/ckan/api/3/action/package_search`),
sem chave. O dataset `cauc` tem 2 CSV vivos (situação atual, não série
histórica — é um retrato do dia da consulta): um para os 26 estados+DF, outro
para os 5.570 municípios. Formato incomum: 3 linhas de metadado, depois a
tabela de dados (colunas `1.1`, `1.2` ... `5.8` — códigos de exigência sem
nome), depois — sem separador — uma **segunda tabela** de legenda (`código do
item` → texto da exigência) colada no mesmo arquivo. Parser em Python
(`polars`, não pandas — convenção do projeto) que separa as duas seções pelo
marcador de linha `"Código do Itens";"Exigência"`.

**Verificado no beelink (readonly):**

```sql
SELECT count(*) FROM br_tesouro_cauc.situacao_estados;    -- 27
SELECT count(*) FROM br_tesouro_cauc.situacao_municipios; -- 5.569
SELECT count(*) FROM br_tesouro_cauc.legenda_itens;       -- 78 (item x nível estados/municípios)
```

Chave de join: `Código IBGE` (7 dígitos, = `id_municipio`) em ambas as
tabelas. Os valores por item são datas (`DD/MM/AA`) ou `"Desabilitado"`/`"!"`
(irregular) — a legenda diz o que cada código de item significa; junte por
`codigo_item` + `nivel`.

### BCB Desenrola Brasil (#11a) — feito

CSV público e direto, achado via CKAN do BCB
(`dadosabertos.bcb.gov.br/api/3/action/package_show?id=desenrola-brasil`) —
`https://www.bcb.gov.br/pda/desig/desenrola/dados_desenrola.csv`, sem chave.
UTF-8, `;`-delimitado.

**Verificado no beelink (readonly):**

```sql
SELECT count(*), min(DATA_BASE), max(DATA_BASE) FROM br_bcb_desenrola.dados;
-- 12.751 linhas, 202309 -> mais recente
```

Chave: `UNIDADE_FEDERACAO` (UF), `COD_CONGLOMERADO_FINANCEIRO`. Não tem
`id_municipio` — grão é UF x instituição x mês.

### BCB SCR.data (#11b) — feito, Versão 2 completa 2012–2026

Achado pelo mesmo CKAN (`package_show?id=scr_data`) — os dois recursos ZIP
tinham `url` vazia na API, mas a `description` de cada um documenta o padrão
de URL real: Versão 1 (legada, descontinuada em jun/2025) em
`bcb.gov.br/pda/desig/planilha_{ANO}.zip`, Versão 2 (atual, cobre **todo** o
histórico 2012–2026, não só o período pós-jun/2025) em
`bcb.gov.br/pda/desig/scrdata_{ANO}.zip`. Fui só pela V2 — mesma metodologia
do início ao fim, sem precisar reconciliar duas séries diferentes.

Cada zip anual contém um CSV por mês (~310 mil linhas/mês, UTF-8 com BOM,
`;`-delimitado). Script baixa por ano, converte cada CSV mensal para parquet
individual (`{AAAAMM}.parquet`), resumível por mês — útil porque são 168
meses ao todo (14 anos x 12).

**Verificado no beelink (readonly), 169/169 meses (2012 só tem jul-dez, por
isso não são 168 = 14 anos x 12):**

```sql
SELECT count(*), count(distinct data_base), min(data_base), max(data_base) FROM br_bcb_scrdata.dados;
-- 43.061.984 linhas, 169 meses, 2012-07-31 -> 2026-07-31
```

Grão: UF x segmento x tipo de cliente (PF/PJ) x CNAE/ocupação x porte x
modalidade x mês — carteira ativa, inadimplência, ativo problemático. Chave:
`uf`, `cnae_ocupacao` (CNAE só para PJ).

### INPE DETER — avisos de desmatamento quase em tempo real (parte do #17)

**Não é o PRODES acumulado** (polígono completo desde 2000/2007, centenas de
MB a ~900MB só de um bioma em `.gpkg.zip`) — é o **DETER**, os avisos de
alteração de cobertura detectados por sensor, atualizados quase diariamente,
que o espelho não tinha em nenhuma forma. Achado via o endpoint AJAX que a
página de downloads do TerraBrasilis usa por trás (`/business/api/v1/download/all`,
231 datasets catalogados, nenhum documentado numa página estática — por isso
o item tinha ficado como "provavelmente dashboard sem endpoint óbvio"; o
endpoint existe, só não está em HTML nenhum).

4 biomas têm endpoint de shapefile DETER público: Amazônia, Cerrado,
Pantanal, e um recorte "não-floresta" da Amazônia. Os dois primeiros trazem
`GEOCODIBGE` (= `id_municipio`) e `MUNICIPALI` direto no shapefile — join
pronto, sem precisar de join espacial. Os outros dois (Pantanal,
não-floresta) usam um schema mais simples sem essas colunas — ficaram só com
coordenadas.

**Decisão de shape**: geometria do polígono virou **centroide (lat/lon)**, não
WKT completo — testei os dois: WKT do bioma Amazônia sozinho pesava 298 MB
(455K alertas, polígonos com muitos vértices), centroide reduziu para 14 MB
(21x menor) sem perder a localização pontual, que é o que a maioria das
consultas de join precisa.

**Verificado no beelink (readonly), view `br_inpe_deter.avisos`:**

```sql
SELECT bioma_arquivo, count(*), min(VIEW_DATE), max(VIEW_DATE)
FROM br_inpe_deter.avisos GROUP BY 1;
-- amazonia            455.392   2016-08-02 -> 2026-08-21
-- cerrado             132.607   2018-05-01 -> 2026-08-21
-- nao_floresta_amz     74.492   2023-08-01 -> 2026-08-21
-- pantanal             23.645   2023-08-03 -> 2026-08-21
-- total               686.136
```

**O PRODES acumulado (polígono completo por bioma) não foi baixado** — cada
bioma sozinho passa de 800 MB zipado, os 231 datasets do TerraBrasilis cobrem
todos os biomas em raster e vetor, e isso é claramente a "janela própria"
que o item já pedia desde a análise original. `br_inpe_prodes.municipio_bioma`
(já espelhado da BD, 156.864 linhas, até 2023, já com `id_municipio`) segue
sendo a fonte pra série longa agregada por município — o gap real que sobra é
só 2024-2026, e fechar isso com fidelidade exigiria replicar o método de
agregação da BD sobre os polígonos brutos, não é ETL de 20 minutos.

### PNS 2023 microdados (#16) — confirmado bloqueado, mas não por credencial

`ftp.ibge.gov.br/PNS/` está no ar, sem autenticação — mas só lista `2013/` e
`2019/`. **A PNS 2023 simplesmente não foi publicada no FTP público ainda** —
não é geo-bloqueio nem WAF nem chave, é o dado não ter saído do IBGE. (A
página HTML do IBGE que anunciaria a data de publicação devolve 403 pro
`curl` puro, mesmo padrão de anti-bot já visto no MUNIC/ESTADIC — não
persegui um browser real pra confirmar a data prevista.) Continua bloqueado,
motivo diferente do suposto antes.

### SPU SIAPA (#21) — investigado, sem endpoint público de bulk achado

A página oficial (`gov.br/spu`) linka dois sistemas vivos:
`geoportal.spunet.economia.gov.br` (não resolveu) e
`sistema.patrimoniodetodos.gov.br` (SPA Angular, responde 200). O SPA aponta
pra uma API (`API_PUBLIC_URL = 'https://me.evolux.cx'`, domínio de terceiro —
parece a consultoria que construiu o sistema) que devolve 403/404 em todo
endpoint tentado às cegas. `dados.gov.br` (a rota que serviria um catálogo
CKAN) devolve **401 mesmo pra leitura pública** — mesmo bloqueio já documentado
no item ANP #13 desta vez confirmado de novo num domínio diferente, então é a
plataforma `dados.gov.br` inteira que passou a exigir chave, não coincidência
pontual. Sem engenharia reversa da SPA (inspecionar tráfego de rede real, não
só o HTML/JS estático), não achei o endpoint que serve os 813K imóveis —
mesma categoria de esforço do `consultar_oab` já documentado como pesquisa,
não implementação direta.

### DIRPF FDCA/FDI (#18) — feito, mas é a lista de fundos habilitados, não os microdados de imposto

A página `gov.br/receitafederal/dados/` (o índice de dados abertos da
Receita) devolve 200 pro `curl` puro — diferente da página institucional
principal, que dá 403. Achei os dois arquivos que o item pedia: "Anexo I —
FDCAs habilitados para a DIRPF 2025" e "Anexo II — FDIs habilitados" (fundos
da criança/adolescente e do idoso habilitados a receber destinação via
declaração de IR), formato `.ods`. O link direto de download (`/@@download/file`,
mesmo padrão Plone visto no SINESP) devolveu 403 com `curl` puro mas
**200 com um `User-Agent` de navegador** — diferente do bloqueio do SINESP
(que persistiu com WAF mesmo via proxy BR), aqui é filtro de UA simples, não
WAF de verdade.

Cada `.ods` tem 26 colunas, mas só as 12 primeiras são dado (o resto é rastro
de auditoria interna da planilha da Receita — colunas como
`final.num.diferentes.CNPJ do Fundo`, claramente debug, descartadas). `pandas`
com engine `odf` pra ler o `.ods` (`polars`/`fastexcel` não leem ODS, só
XLSX) — única exceção à preferência por Polars nesta rodada, e só pro parse;
a escrita final é parquet via `polars.from_pandas`.

**Verificado no beelink (readonly), view `br_rf_dirpf.fundos_habilitados`:**

```sql
SELECT anexo, count(*), count(distinct id_municipio) FROM br_rf_dirpf.fundos_habilitados GROUP BY 1;
-- FDCA  4.286 linhas, 4.286 municípios
-- FDI   2.185 linhas, 2.185 municípios/estados
```

Colunas: `numero, uf, nome_municipio, id_municipio, tipo_fundo (M/E),
cnpj_fundo, codigo_banco, codigo_agencia, numero_conta, vai_pgd, e_classe,
nome_empresarial, anexo (FDCA/FDI), ano_dirpf`. Chave de join: `cnpj_fundo`,
`id_municipio`. **Nota**: isto é a lista de fundos **habilitados a receber**
destinação — não os valores efetivamente destinados por declaração. A fonte
dos valores (se publicada) segue sem achar.

### TCEs estaduais (#20) — não tocado, confirmado alto esforço

Não investigado a fundo nesta rodada além do que a análise original (mcp-brasil)
já tinha mapeado. Um teste de conectividade rápido em 2 domínios (TCE-SP,
TCE-RS) não achou um padrão de API comum — cada corte parece ter portal e
formato próprios, confirmando a avaliação já registrada ("11 fontes
distintas, esforço alto"). Sem mudança de status.

### CNJ Painel (#10) — confirmado bloqueado, não é dashboard sem endpoint, é o serviço fora do ar

`paineis.cnj.jus.br` devolveu **502 Bad Gateway** de forma consistente (3
tentativas espaçadas, `NSX LB` no header — balanceador do próprio CNJ
rejeitando, não CDN de terceiro). Diferente do que a nota anterior sugeria
("responde 200/302, provavelmente dashboard sem endpoint óbvio") — não chegou
a resolver pra examinar dashboard nenhum, o serviço está fora do ar agora.
`www.cnj.jus.br/paineis-de-dados` (tentativa de rota alternativa) deu 404.
Reteste mais tarde — mesmo padrão do item BCB Pix (#4), pode ser transitório
do lado do órgão.

### Regen de metadados e views — feito

`scripts/sync/cria_views_novas.py` para os datasets desta rodada
(`br_ibge_cnefe.enderecos`, `br_inpe_deter.avisos`, `br_bcb_desenrola.dados`,
`br_tesouro_cauc.{situacao_estados,situacao_municipios,legenda_itens}`,
`br_rf_dirpf.fundos_habilitados`) — view criada e cada uma conferida com
`count(*)` direto no beelink, readonly. `br_bcb_scrdata.dados` (169 parquets,
um por mês) recebeu a mesma view depois que o job de coleta terminou —
**43.061.984 linhas, 2012-07 a 2026-07, conferido**.

Regen completo `gera_schemas.py` → `sync_mcp_schema.py` →
`build_metadata_catalog.py` → `gera_join_keys.py` rodado depois que os 4
primeiros landed (antes do DIRPF e do SCR.data — regen final fica pra fechar
a rodada); catálogo foi de 1.017 para 1.023 tabelas / 39,2 bi linhas (inclui
também os datasets da sessão paralela — Gás do Povo, Novo Bolsa Família,
Transferegov). `gera_schema_graph.py`/`build_atlas.py` não rodados — ficam
pra quem quiser os datasets desta rodada também no Atlas.

**Provenance corrigida 2026-09-02.** Os 9 datasets desta e da rodada paralela
(`br_ibge_cnefe`, `br_inpe_deter`, `br_bcb_desenrola`, `br_tesouro_cauc`,
`br_rf_dirpf`, `br_bcb_scrdata`, `br_cgu_gas_do_povo`, `br_cgu_novo_bolsa_familia`,
`br_transferegov_siconv`) ganharam linha em `done/datasets_to_scrap_done.md`
com a fonte real documentada acima — `build_metadata_catalog.py` só lê esse
arquivo (+ `datasets_to_scrap.md`) para decidir procedência, então qualquer
dataset ausente dele vira `source_name="Base dos Dados"`/mirror por padrão
(comentário no próprio script, linha ~52), o que estava acontecendo com os 9.
`gera_schemas.py` → `sync_mcp_schema.py` → `build_metadata_catalog.py` →
`gera_join_keys.py` rerodados; `_rodado_metadata` no beelink confirma
`source_name` correto para os 9 (`Gás do Povo (CGU)`, `BCB SCR.data` etc.).

### Itens que continuam abertos depois desta rodada

| # | Item | Situação |
|---|---|---|
| 14 | CadÚnico agregados (VIS DATA / SAGI-MDS) | **investigado, bloqueado — não é credencial.** `aplicacoes.mds.gov.br` (o host do VIS DATA) resolve e aceita a conexão TCP, mas trava no TLS handshake — testado do laptop e do beelink (IP brasileiro), mesmo padrão do ANEEL (#7). `gov.br/mds` (dados abertos) está no ar mas não lista CadÚnico bulk, só contratos de adesão. `dados.gov.br` de novo 401 (mesmo bloqueio sistêmico de API key já visto em ANP #13 e SPU #21) |
| 17 | PRODES acumulado (só o DETER foi feito) | cada bioma sozinho >800 MB zipado; "janela própria" confirmada necessária |
| 18 | DIRPF microdados de destinação (valores, não só habilitados) | não achado |
| 20 | TCEs estaduais | alto esforço confirmado, não iniciado |
| 21 | SPU SIAPA | sem endpoint de bulk público achado; exigiria engenharia reversa de SPA |
| 10 | CNJ Painel | serviço fora do ar (502), reteste depois |
| 4 | BCB Pix por município | segue quebrado do lado do BCB (já documentado antes) |
