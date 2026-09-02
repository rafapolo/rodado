# datasets_coverage_gaps.md — datasets do espelho que nenhuma pergunta nunca tocou

Nasceu de uma observação simples em 2026-08-25: `docs/perguntas.md` tinha 215
perguntas (43 temas × 5) mas só citava 86 dos 197 datasets do espelho. Os
outros 111 nunca foram cruzados com nada — nunca geraram uma query real, nunca
tiveram uma chance de expor um bug de join ou uma armadilha de unidade, porque
a disciplina de `respostas_pendentes.md` (responder com query real, documentar
bloqueio real) só roda sobre pergunta que existe.

Diferente de `datasets_gap_analysis.md` (que procura **fontes novas fora do
espelho**) e de `respostas_pendentes.md` (que fecha o backlog de perguntas
**já escritas**), este arquivo rastreia **datasets já espelhados que nenhuma
pergunta usa** — o inventário pra decidir o próximo tema a escrever, não pra
executar.

## Metodologia (temas 44/45 como precedente)

```python
import json, re
d = json.load(open('docs/context/basedosdados-schema.json'))
text = open('docs/perguntas.md').read()
untouched = [ds for ds in sorted(d) if ds not in text and re.sub(r'^(br_|world_|global_)', '', ds) not in text]
```

Temas 44 (Saneamento/Produção Rural/Desmatamento) e 45 (Integridade Financeira)
nasceram exatamente assim em 2026-08-25: filtrar os untouched, escolher os com
chave de join plausível (`id_municipio`, `cnpj`/`cpf`, `sigla_uf`), escrever 5
perguntas por tema, responder com a mesma disciplina de `respostas_pendentes.md`.
Resultado dessa primeira rodada: 7/10 respondidas com número real, 3 bloqueadas
por corrupção de dado **genuína e nova** (não catalogada antes) —
`br_rf_cafir.imoveis_rurais` com 61-64% de linhas sem id em todo snapshot,
`br_ibama_embargos` com 100% das colunas vazias em todas as 8 tabelas — e 1
achado de escala (`br_ibge_pam.valor_producao` em mil reais, virou métrica).
A taxa de achado (3 bugs reais em 10 perguntas de dataset nunca tocado) é bem
mais alta que nas rodadas sobre temas 1-43 (que já tinham sido escritos e
parcialmente tentados) — sugere que "nunca tocado" é um preditor melhor de bug
que "tema difícil".

## Estado em 2026-08-25

Depois dos temas 44/45: **99 de 197 datasets** (era 111) ainda nunca aparecem
em `docs/perguntas.md`. Triados abaixo em três baldes.

**Atualização pós-tema 46**: grupo "Educação superior e acesso" do Balde C
virou tema 46 (`docs/perguntas.md`), respondido em `docs/respostas.md`
(T46-1…T46-5, todas ✅). Tocou `br_capes_bolsas`, `br_mec_sisu`,
`br_inep_censo_educacao_superior`, `br_inep_ana`,
`br_inep_indicadores_educacionais` — untouched caiu de 99 para **94**.
`br_mec_prouni` foi investigado também (achado: dataset praticamente vazio,
só tem a tabela `dicionario` no beelink — ver bloqueio T46-1 em
`respostas.md`) mas não sai da contagem automática porque a heurística de
substring não bate com "PROUNI" maiúsculo/sem o dataset citado literalmente
no texto — é tocado de fato, só não pela heurística. Dois bridges/bugs novos
saíram desta rodada: `id_municipio_campus` (br_mec_sisu.microdados, não
documentado antes) e `nivel_socio_economico` (br_inep_ana.escola) com código
diferente entre os dois anos da própria tabela (2014 vs 2016) — ambos em
`bridges.yaml`.

**Atualização pós-tema 47**: grupo "Servidor público e integridade" virou
tema 47, respondido em `docs/respostas.md` (T47-1…T47-5, todas ✅). Tocou
`br_mp_pep`, `br_me_siape`, `br_rf_cno` — untouched caiu de 94 para **91**.
`br_me_siorg` e `br_me_cno` foram investigados também (achados: SIORG usa
um esquema de cargo — CA/CAS/CCD/CCE — incompatível por nome com o do PEP —
DAS/CCX/FEX/FPE —, sem tabela-ponte no espelho; `br_me_cno` é uma versão
bem menor e provavelmente defasada de `br_rf_cno`, não usada) mas não saem
da contagem automática pela mesma razão da heurística de substring. Achado
mais importante da rodada: `br_mp_pep` **não é "Pessoas Expostas
Politicamente"** como a triagem original supôs — é o Painel Estatístico de
Pessoal (cargos comissionados agregados, sem CPF/nome), então o ângulo AML
que a entrada original do Balde C previa não existe nesse dataset; o
ângulo de integridade que funcionou foi outro (CNO × TCU inidôneos, T47-4)
— achou C R Almeida S/A de novo, a mesma empresa do T45-4, confirmando por
uma segunda via independente. Novo bridge em `bridges.yaml`:
`br_rf_cno.microdados.id_responsavel → cnpj` (mais o achado de que essa
coluna é a string literal `"nan"` — não NULL — pra 65,5% das linhas, as de
responsável pessoa física).

**Atualização pós-temas 48-55 (2026-08-25, rodada paralela — 8 agentes, um
por grupo do Balde C restante)**: todos os grupos restantes do Balde C
viraram tema (`docs/perguntas.md`, `docs/respostas.md`) na mesma rodada.
Untouched caiu de 91 para **62**. Resumo por tema (detalhe completo em
`docs/respostas.md`, seções 48-55, e no catálogo "Bloqueios mapeados"):

- **T48 · Sanções Internacionais**: `eu_sanctions`/`un_sanctions`/`global_ofac_sanctions`
  não têm nenhum vínculo brasileiro com identificador estruturado (bloqueio
  honesto, T48-1). `global_icij_offshoreleaks` foi o achado real: 292 CNPJs
  brasileiros casados por nome com entidades do Panama/Pandora/Paradise
  Papers, 99% sob a natureza jurídica "Empresa Domiciliada no Exterior" —
  novo bridge em `bridges.yaml`. Join por nome funciona bem pra empresa
  offshore (nome distintivo) mas falha pra pessoa física (nome comum colide
  — T48-3, documentado como bloqueio, não forçado).
- **T49 · Saúde Suplementar**: achou bug real de duplicação silenciosa em
  `br_ans_beneficiario` (múltiplas `data_carga` no mesmo ano/mês, soma
  direta infla ~1,5x) — virou métrica verificada `beneficiarios_ans_ativos`.
  `br_ms_vacinacao_covid19` só tem o diretório de estabelecimentos — as
  tabelas de microdado de dose que o próprio dicionário promete não existem
  no mirror (mesmo padrão do PROUNI).
- **T50 · Justiça Complementar**: corrigiu um bridge ERRADO já existente
  (`br_mjsp_sinesp.ocorrencias_uf.uf` não é sigla de 2 letras como o
  bridges.yaml dizia — é nome do estado por extenso). Achou bug de escala
  grave em `br_cnj_estatisticas_poder_judiciario` (despesas absolutas
  duplicadas 28x no ramo Eleitoral, e inconsistentes no Estadual).
- **T51 · Energia e Infraestrutura**: corrigiu a premissa de que
  `br_mme_consumo_energia_eletrica` tem grão municipal — só tem UF.
  `br_me_exportadoras_importadoras` é outro dataset vazio (só dicionário,
  mesmo padrão do PROUNI/vacinação Covid). Achado forte: consumo elétrico
  "Comercial" por UF é proxy quase perfeito do setor de comércio formal
  (RAIS) mesmo per capita (r=0,89).
- **T52 · Financeiro/Macro**: três bugs de escala/schema novos —
  `br_me_estoque_divida_publica` soma ~12x se não filtrar mês;
  `br_bcb_sgs` SELIC é mensal apesar do nome sugerir anual; as 4 tabelas
  `br_fgv_igp.*_mes` têm as colunas `ano`/`mes` TROCADAS (tabelas `*_ano`
  estão certas). Todos viraram métricas verificadas em `metrics.yaml`.
- **T53 · Índices e Comparativos Internacionais**: `world_wb_mides` **não
  é** o dataset internacional que o nome sugere — é procurement/orçamento
  municipal brasileiro de 10 estados (mesma classe de erro do PEP em tema
  47); permanece "untouched" pela heurística porque nenhuma pergunta boa
  usa esse dado. `world_oecd_public_finance` tem as colunas de despesa
  pública corrompidas (sentinel `INT32_MIN` em 82-98% das linhas) — não
  desbloqueia o gasto saúde/educação comparado que os itens T33-2…T33-5
  pediam, só desbloqueia parcialmente PIB/desemprego/Gini/governança.
- **T54 · Censo Histórico**: achado grave — 30% dos municípios atuais não
  existiam como código em 1970/1980 (emancipação pós-1988); join direto
  por `id_municipio` entre censos históricos perde isso silenciosamente.
  `br_ibge_populacao` e `br_ms_populacao` batem byte-a-byte na maioria dos
  anos mas divergem ~4% em 2022-2023 porque o MS não aplicou o reset do
  Censo 2022 — virou caveat na métrica `populacao`.
- **T55 · Vulnerabilidade Social/Medicamentos/Veículos**: `br_fipe_veiculos`
  não tem preço/ano/geografia nenhuma, apesar do nome — é só um catálogo
  de marca/modelo. `br_anvisa_medicamentos_industrializados` está truncada
  em exatamente 10.000.000 de linhas, cobrindo só municípios do começo do
  alfabeto (nenhuma capital grande) — corte de scraping, não amostra.
  `br_anvisa_cmed` desbloqueou parcialmente o tema 41 (preço regulado real
  existe) mas não tem série histórica, então T41-4 continua bloqueado.

Nove bridges novos e três correções de bridge existente foram pra
`bridges.yaml` nesta rodada; seis novas métricas foram pra `metrics.yaml`
(todas com `verified` e `caveat`). Regenerado `join_keys.md`,
`metrics.json`, `valida_metrics.py` rodou limpo (0 erros).

Todos os grupos do Balde C original (2026-08-25, primeira triagem) viraram
tema em temas 46-55 — ver as duas atualizações acima. Re-triagem completa
dos **62 datasets** que sobraram untouched depois dessa rodada, em quatro
baldes.

### Confirmados quebrados/vazios/mal-rotulados nesta rodada — não retentar sem re-scraping

Ficam fora de qualquer Balde C futuro até o dado ser corrigido na fonte:
`br_mec_prouni` (só dicionário, T46-1), `br_me_exportadoras_importadoras`
(só dicionário, T51), `br_me_siorg` (esquema de cargo incompatível com PEP,
sem tabela-ponte, T47), `br_me_cno` (versão pequena/defasada de
`br_rf_cno`, T47), `world_wb_mides` (é procurement municipal brasileiro,
não dado internacional, T53).

### Balde A — puro lookup/dimensão, não vale pergunta própria

`br_bd_diretorios_brasil`, `br_bd_diretorios_data_tempo`, `br_bd_diretorios_mundo`,
`br_bd_diretorios_us`, `br_bd_metadados`, `br_bd_vizinhanca`, `br_brasilapi`,
`br_datasus_cid10`, `br_ibge_cbo_2002`, `br_ibge_amc`,
`global_ibge_tabua_mares`, `br_comprasgov_catmatcatser` (catálogo
CATMAT/CATSER, código de material/serviço).

### Balde B — escopo muito estreito ou difícil de cruzar

`br_ba_feiradesantana_camara_leis`, `br_ce_fortaleza_sefin_iptu`,
`br_mg_belohorizonte_smfa_iptu`, `br_sp_saopaulo_geosampa_iptu` (IPTU de
uma cidade só), `br_caixa_sorteios`, `world_ampas_oscar`, `world_imdb_movies`,
`mundo_transfermarkt_competicoes*`, `world_sofascore_competicoes_futebol`,
`br_datahackers_state_data`, `br_tce_to` (TCE de um único estado),
`us_harvard_ned`, `br_ok_queridodiario` (diário oficial em texto livre —
tem bridge municipal documentada mas cruzar exigiria NLP, não SQL simples),
`br_ibge_inpc`/`br_ibge_ipca15`/`br_ibge_ipp` (índices de preço paralelos
ao IPCA já usado — baixa prioridade, redundantes sem um ângulo novo),
`br_me_rais_identificada` (RAIS com mais PII, mas provavelmente redundante
com `br_me_rais` já usado em dezenas de temas).

### Balde C — candidatos reais pro próximo lote de temas

- **Programas sociais e transparência CGU** (grupo grande, nunca tocado):
  `br_cgu_pe_de_meia` (programa Pé-de-Meia, permanência escolar — cruza
  com INEP/Censo Escolar), `br_cgu_garantia_safra` (já tem bridge
  documentada em `bridges.yaml` como exemplo de gotcha, mas nunca virou
  pergunta), `br_cgu_receitas_publicas`, `br_cgu_orcamento_publico`,
  `br_cgu_viagens` (viagens a serviço de servidor público — cruza com
  SIAPE/PEP do tema 47), `br_cgu_ebt`, `br_cgu_fef`, `br_cgu_seguro_defeso`,
  `br_cgu_dados_abertos`.
- **Justiça/tribunais ainda não tocados**: `br_stj_dadosabertos`,
  `br_tcu_dadosabertos` (mais amplo que só `tcu_inidoneos`, já usado),
  `br_mjsp_procurados` (confirmado pequeno demais em T50 — só 195 linhas,
  mas ainda não descartado formalmente).
- **Água e hidrologia, extensão do tema 44**: `br_ana_bho`, `br_ana_reservatorios`
  — cruzam naturalmente com `br_ana_outorgas`/`br_ana_atlas_esgotos` já
  usados.
- **Violência e vulnerabilidade, extensão do tema 06**: `br_ipea_atlasviolencia`
  (Atlas da Violência IPEA — surpreendente ainda estar untouched, é
  referência clássica), `br_ms_sinan_violencia`, `br_abrinq_oca`
  (observatório da criança e do adolescente).
- **Servidor público, extensão do tema 47**: `br_me_clima_organizacional`
  (pesquisa de clima organizacional do funcionalismo — cruza com
  SIAPE/PEP).
- **Consumidor, extensão do tema 50**: `br_mj_consumidorgovbr`
  (reclamações consumidor.gov.br — mesmo ângulo do PROCON em T50-5, mas
  cobertura nacional diferente, vale checar se cobre os estados que o
  PROCON não cobriu).
- **Comparativos internacionais de educação, extensão do tema 33/38**:
  `world_iea_pirls`, `world_iea_timss` (leitura e matemática/ciências
  internacional — mesmo padrão do PISA já usado).
- **Mercado financeiro, extensão do tema 19/45**: `br_cvm_oferta_publica_distribuicao`
  (cruza com `cvm_fundos` já usado em T45-2).
- **Infraestrutura urbana**: `br_mc_indicadores` (Ministério das Cidades),
  `br_ipea_acesso_oportunidades` (acesso a oportunidades urbanas).
- **Pandemia**: `br_ibge_pnad_covid` (PNAD-COVID, pesquisa especial —
  cruza com vacinação/SIM do período).
- **Demografia cultural**: `br_ibge_nomes_brasil` (frequência de nomes por
  ano/UF — ângulo cultural/geracional, baixa prioridade mas incomum).
- **Vulnerabilidade social/medicamentos, resíduo do tema 55**:
  `br_anvisa_consultas` já foi usado (T55-3), mas vale conferir cobertura
  completa; `br_anvisa_medicamentos_industrializados` está truncado em
  10M linhas (ver bloqueio T55) — não retentar sem re-scraping, mas
  **não** entra na lista de "confirmados quebrados" porque ainda produziu
  resposta real dentro da limitação conhecida.

**Atualização pós-tema 56 (2026-08-27, rodada em paralelo com outro agente
trabalhando em `respostas.md`/`bridges.yaml` dos temas 1-45 — esta sessão
rodou read-only, texto entregue pra fusão pela orquestradora)**: grupo
"Violência e vulnerabilidade, extensão do tema 06" do Balde C virou tema 56
(`docs/perguntas.md`, texto pronto entregue no relatório final desta
sessão — ainda não mesclado no momento desta nota). Tocou
`br_ipea_atlasviolencia`, `br_ms_sinan_violencia`, `br_abrinq_oca`. A
recontagem heurística no topo deste arquivo hoje dá **64** untouched (não
62 como a nota anterior registrava — o schema cresceu de 197 pra 199
datasets desde 2026-08-25, com `br_ibge_censo2022_raca`, `br_minc_salic`,
`br_senado_ceaps` entrando na lista); depois que o tema 56 for mesclado em
`docs/perguntas.md` a contagem cai pra **61**.

Achados da rodada (detalhe completo no relatório da sessão, a mesclar em
`respostas.md`): (1) `br_ipea_atlasviolencia` só tem a tabela
`valores_nacional` — série 100% agregada nacional, sem UF nem município,
apesar do Atlas da Violência ser referência clássica de dado *municipal*
noutras publicações do IPEA; o que está espelhado aqui é só o painel
nacional. (2) bug de partição: `br_ms_sinan_violencia.microdados_violencia.NU_ANO`
vem vazio para 100% do lote com `ano_sinan=2020` (326.503 de 326.563 linhas
em branco) — qualquer `GROUP BY NU_ANO` pula 2020 inteiro em silêncio;
`ano_sinan` é a partição confiável pra série 2009-2025 completa. (3) gotcha
conceitual de raça: `br_ipea_atlasviolencia`'s "Homicídios Negros" já
agrega preto+pardo (padrão IBGE), enquanto o `CS_RACA` cru do SINAN mantém
os dois separados (2=preta, 4=parda) — filtrar só `CS_RACA='2'` pensando
"negro" captura ~9% quando o correto (preto+pardo) é 46-58% ao longo dos
anos. Sem bloqueio novo: os cinco itens do tema foram todos respondidos com
número real.

## Pra continuar

1. Escolher 1-2 grupos do Balde C, escrever o próximo tema (56 em diante)
   em `docs/perguntas.md` (5 perguntas cada, formato
   `*(n=N: dataset_a, dataset_b\*)*`).
2. Responder com a mesma disciplina de sempre — `resolve_join`/`explain_column`
   antes de join à mão, `get_metric` antes de calcular per-capita/proporção,
   verificar contra ordem de grandeza conhecida antes de reportar.
3. Documentar em `docs/respostas.md` (✅/◐ com número real, ⏳ com motivo
   verificado — nunca "pendente" sem razão).
4. Todo bridge novo ou verificado pela primeira vez vai pra `docs/context/bridges.yaml`
   (+ `scripts/gera_join_keys.py`); toda armadilha de unidade/escala vira
   `docs/context/metrics.yaml` (+ `scripts/gera_metrics_json.py` +
   `scripts/valida_metrics.py`).
5. Regenerar o golden set:
   ```bash
   python3 scripts/build_douradas_perguntas.py
   python3 scripts/avalia_douradas_perguntas.py
   ```
6. Reexecutar o levantamento do topo deste arquivo pra atualizar a lista de
   untouched e mover os datasets recém-tocados pro histórico, não deletar —
   o valor deste arquivo é rastrear o que falta, então cada rodada deveria
   encolher o Balde C e engordar o "tocado", não sumir com o registro.
7. Ao paralelizar com múltiplos agentes (como nas rodadas 48-55), cada
   agente deve rodar em modo **read-only puro** (só investigar e reportar
   texto pronto pra colar) — a fusão nos arquivos compartilhados
   (`perguntas.md`, `respostas.md`, `bridges.yaml`, `metrics.yaml`) fica
   sempre pra sessão orquestradora, sequencial, pra evitar conflito de
   edição concorrente no mesmo arquivo.
