# Espelho subutilizado — dado que já temos e nada consome

> Agrupado em 2026-09-02 de três levantamentos que mediam a mesma lacuna por
> três consumidores diferentes. Todos partem de dado **já espelhado** e
> perguntam "quem usa isto?" — a resposta em todos os casos é "ninguém ainda".
>
> - **Parte I** — os 111 datasets que nenhuma pergunta de `docs/perguntas.md` tocou
> - **Parte II** — os 53 datasets com coluna de município que o dashboard `dataviz/municipio` não usa
> - **Parte III** — o mapa de saúde mental: um tema onde o dado existia e o relatório não
>
> Parte III é a forma concreta que as Partes I e II tomam quando alguém
> escolhe um recorte: sai do inventário e vira "o que dá pra responder".
>
> **Rodada de 2026-09-02 (fechamento parcial):** Parte III publicada como
> relatório (`pages/analises/results/mapa-da-saude-mental.md`) — fechada.
> Parte I ganhou o tema 57 (fecha `br_cvm_oferta_publica_distribuicao`).
> Parte II não teve seção de dashboard criada — o código do dashboard
> (`dataviz/municipio/`) vive no repo `xn--2dk.xyz`/`xyz`, fora do escopo
> desta sessão (repo declarado: `rodado`) — em vez disso, uma rodada de
> verificação real no beelink resolveu 6 dos "checar antes de assumir"
> espalhados pelos três baldes, promovendo/rebaixando item por achado
> real em vez de hipótese. Detalhe de cada achado nas seções abaixo.

**Como isto se relaciona com os vizinhos:** o oposto de
[`fontes_novas.md`](fontes_novas.md), que cataloga o que o espelho **não**
tem. Aqui é excesso não aproveitado, lá é falta. Nenhum dos dois executa —
quem executa é [`respostas_pendentes.md`](respostas_pendentes.md) (perguntas)
e [`datasets_to_scrap.md`](datasets_to_scrap.md) (coleta).

---

# Parte I — Datasets que nenhuma pergunta nunca tocou

Nasceu de uma observação simples em 2026-08-25: `docs/perguntas.md` tinha 215
perguntas (43 temas × 5) mas só citava 86 dos 197 datasets do espelho. Os
outros 111 nunca foram cruzados com nada — nunca geraram uma query real, nunca
tiveram uma chance de expor um bug de join ou uma armadilha de unidade, porque
a disciplina de `respostas_pendentes.md` (responder com query real, documentar
bloqueio real) só roda sobre pergunta que existe.

Diferente de `fontes_novas.md` (que procura **fontes novas fora do
espelho**) e de `respostas_pendentes.md` (que fecha o backlog de perguntas
**já escritas**), este arquivo rastreia **datasets já espelhados que nenhuma
pergunta usa** — o inventário pra decidir o próximo tema a escrever, não pra
executar.

### Metodologia (temas 44/45 como precedente)

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

### Estado em 2026-08-25

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

**Atualização pós-tema 57 (2026-09-02)**: grupo "Mercado financeiro,
extensão do tema 19/45" (`br_cvm_oferta_publica_distribuicao`) virou tema 57
(`docs/perguntas.md`, `docs/respostas.md`, commit `bf562fc`). Achado: a
série para em 2022 sem aviso e é 100% ICVM 476 (colocação privada, não IPO
registrado) — quem espera oferta pública registrada no sentido comum não
encontra nenhuma aqui. Concentração real por tipo de ativo (cotas fechadas +
debêntures = 78,1%) e por líder coordenador (top 3 = 41,6%); cruzamento com
`cvm_fundos` (8,9% dos fundos já ofertaram) e `tcu_inidoneos` (zero
coincidência, achado limpo). Novo bridge
`cnpj_emissor`/`cnpj_lider`/`cnpj_ofertante` em `bridges.yaml`. Untouched
cai de 61 para **60**.

Todos os grupos do Balde C original (2026-08-25, primeira triagem) viraram
tema em temas 46-55 — ver as duas atualizações acima. Re-triagem completa
dos **62 datasets** que sobraram untouched depois dessa rodada, em quatro
baldes.

#### Confirmados quebrados/vazios/mal-rotulados nesta rodada — não retentar sem re-scraping

Ficam fora de qualquer Balde C futuro até o dado ser corrigido na fonte:
`br_mec_prouni` (só dicionário, T46-1), `br_me_exportadoras_importadoras`
(só dicionário, T51), `br_me_siorg` (esquema de cargo incompatível com PEP,
sem tabela-ponte, T47), `br_me_cno` (versão pequena/defasada de
`br_rf_cno`, T47), `world_wb_mides` (é procurement municipal brasileiro,
não dado internacional, T53), `br_ana_bho` (o schema **não existe** no
DuckDB do beelink — `SHOW TABLES FROM br_ana_bho` falha com "no catalog
found"; está listado em `all_tables.txt`/`schemas.json` mas não é
consultável hoje, achado verificando o Balde C em 2026-09-02).

#### Balde A — puro lookup/dimensão, não vale pergunta própria

`br_bd_diretorios_brasil`, `br_bd_diretorios_data_tempo`, `br_bd_diretorios_mundo`,
`br_bd_diretorios_us`, `br_bd_metadados`, `br_bd_vizinhanca`, `br_brasilapi`,
`br_datasus_cid10`, `br_ibge_cbo_2002`, `br_ibge_amc`,
`global_ibge_tabua_mares`, `br_comprasgov_catmatcatser` (catálogo
CATMAT/CATSER, código de material/serviço).

#### Balde B — escopo muito estreito ou difícil de cruzar

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

#### Balde C — candidatos reais pro próximo lote de temas

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

### Pra continuar

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

---

# Parte II — Datasets de município fora do dashboard

Levantamento de 2026-08-28: dos 111 datasets do espelho que têm pelo menos uma
tabela com coluna de município (`docs/context/basedosdados-schema.json`, busca
por `municip` no nome da coluna), `dataviz/municipio/extract_municipio.py`
(repo `xn--2dk.xyz` / `xyz`, não este) usa 62. Os 53 abaixo não entraram —
triados em três baldes pra decidir depois quais valem uma seção nova. A
maioria segue como hipótese de escopo a partir do nome das tabelas e
colunas — pra guiar a próxima rodada de decisão, não pra implementar
direto —, mas 6 já foram checados com query real no beelink em 2026-09-02
(marcados "verificado" abaixo): 1 promovido de Balde C pra A
(`br_anp_precos_combustiveis`, achado: não duplica, é estritamente melhor
que o que já está no dashboard), 1 confirmado já resolvido em outra sessão
(`br_ms_populacao`), 2 com grão real mas escopo estreito confirmado
(`br_ibge_pnadc`, `br_rf_arrecadacao`), 1 parcialmente checado sem acesso
ao código do dashboard (`br_ibge_censo2022_raca`). **Criar a seção em si —
a parte que muda `dataviz/municipio/` — segue fora do escopo desta sessão**:
esse código vive no repo `xyz`, e decidir qual item vira seção nova (e como
ela se encaixa no layout existente) é uma escolha de produto/editorial que
cabe a quem trabalha nesse repo, não uma inferência a fazer daqui.

### Balde A — gap real, provável de valer a pena

- `br_ms_sia` (`producao_ambulatorial`, `psicossocial`) — produção ambulatorial do SUS; complemento natural do SIH (internação) que já está no dashboard.
- `br_ms_atencao_basica` (`municipio`) — cobertura de atenção básica/ESF; hoje o dashboard só tem CNES (estrutura) e agravos pontuais, nada sobre cobertura de saúde da família.
- `br_transferegov` (`transferencias`, `programas`, `planos_acao`) — repasses federais a convênios/planos de ação, além das emendas parlamentares já cobertas.
- `br_tcu_inidoneos` (`empresas`, `inabilitados_funcao_publica`, ...) — empresas e pessoas inabilitadas para contratar com o poder público; complementa a seção de transparência com um ângulo de integridade.
- `br_tse_filiacao_partidaria` (`microdados`) — filiação partidária por município; complementa a seção de política, que hoje só tem eleitorado e resultado.
- `br_comprasgov_sicaf` (`fornecedores`) — fornecedores cadastrados no SICAF sediados no município; complementa CNPJ/licitação.
- `br_bndes_operacoes_contratadas` (`operacoes_nao_automaticas`) — financiamentos do BNDES contratados no município.
- `br_cgu_pe_de_meia` (`pe_de_meia`) — programa de transferência a estudantes do ensino médio (2024+); mesma família de `bolsa_familia`/`bpc` já cobertos em `beneficios`.
- `br_cgu_seguro_defeso` (`seguro_defeso`) — seguro-defeso a pescadores artesanais; mesma família de benefícios sociais.
- `br_ibge_ipca` / `br_ibge_ipca15` (`mes_categoria_municipio`) — inflação por categoria **no município**, não só o INPC nacional que já está em `economia`. Cobertura limitada às ~16 cidades onde o IBGE coleta preços (capitais + poucas outras) — checar se Nova Friburgo tem dado antes de prometer a seção.
- `br_anp_precos_combustiveis` (`microdados`) — **verificado 2026-09-02, promovido do Balde C**: NÃO duplica `br_anp_combustiveis.precos`. São sistemas diferentes — 16.409.523 linhas (2004-2026) contra 2.006.614 (formato distinto, inclui GLP, `municipio` como texto livre em vez de `id_municipio`). Esta tabela já vem com `id_municipio` (formato padrão IBGE) e `sigla_uf`, além de `preco_compra`/`preco_venda` (a que já está no dashboard só tem `preco_revenda`) — é estritamente melhor para join municipal que a que já está no dashboard, não uma redundância.

### Balde B — relevante, mas com escopo geográfico estreito (não aparece pra toda cidade)

- `br_tce_es`, `br_tce_pi`, `br_tce_sp` — dados de tribunais de contas estaduais; só existem para município do ES/PI/SP respectivamente, então uma seção "genérica" mostraria vazio pra ~89% dos municípios do país.
- `br_trase_supply_chain` (`soy_beans*`, `beef*`) — rastreabilidade de cadeia de soja/boi; só tem dado real pra município de fronteira agrícola.
- `br_ibama_embargos` — embargos ambientais; concentrado em município de desmatamento/Amazônia Legal. Nota: a Parte I deste arquivo já registrou que as 8 tabelas deste dataset têm 100% das colunas vazias em pelo menos um teste (2026-08-25) — checar se ainda está quebrado antes de investir tempo aqui.
- `br_ana_outorgas` (`captacoes`, `lancamentos`) — outorgas de uso de água; só relevante pra município com corpo d'água outorgado. O projeto já tem conhecimento verificado sobre este dataset (ver memória `reference_outorgas_snirh` / `bridges.yaml`), então o custo de adicionar é baixo mesmo sendo de cobertura parcial.
- `br_ana_telemetria` (`estacoes`, `series_chuva_*`, `series_cota_*`) — séries de chuva/nível de rio por estação telemétrica; só município com estação ANA por perto.
- `br_cnpq_bolsas` (`microdados`) — bolsas CNPq por município de destino; concentrado em município com instituição de pesquisa.
- `br_sfb_sicar` (`area_imovel`) — Cadastro Ambiental Rural; mais relevante pra município rural/agropecuário.
- `br_ibge_pevs` (`producao_extracao_vegetal`, `producao_silvicultura`) — produção de extrativismo vegetal e silvicultura; só município com essa atividade.
- `world_wb_mides` (`licitacao`, `empenho`, `liquidacao`) — execução orçamentária por município apesar do prefixo `world_`; parece ligado a um programa financiado pelo Banco Mundial, cobertura provavelmente restrita aos municípios participantes desse programa — checar antes de assumir.

### Balde C — baixa prioridade, niche ou registro administrativo sem grão cívico

- `br_anvisa_medicamentos_industrializados` — fabricantes de medicamento registrados por município; só relevante pra município com planta farmacêutica.
- `br_bcb_sicor` (`operacao`, `empreendimento`, ...) — operações de crédito rural por instituição financeira; nicho, mais dado de mercado financeiro que perfil municipal.
- `br_cvm_administradores_carteira` — administradores de carteira registrados na CVM; registro profissional, não indicador do município.
- `br_rf_cafir` (`imoveis_rurais`) — Cadastro de Imóveis Rurais da Receita; a Parte I deste arquivo já registrou 61-64% das linhas sem id em todo snapshot (achado de 2026-08-25) — dado corrompido conhecido, não vale investir sem re-checar a fonte.
- `br_rf_cno` (`microdados`, `vinculos`, `areas`, `cnaes`) — Cadastro Nacional de Obras; nicho, mais dado de fiscalização trabalhista em obra que perfil municipal.
- `br_rf_arrecadacao` (`ir_ipi`, `itr`, ...) — **verificado 2026-09-02**: grão é misto dentro do próprio dataset. `itr` (Imposto Territorial Rural) TEM `id_municipio`+`sigla_uf`+`ano`+`mes` — daria uma seção real, estreita (só ITR); `ir_ipi` NÃO tem nem UF nem município, só `ano`/`mes`/`tributo`/`decendio` nacional — não serve pro dashboard municipal de jeito nenhum. Não tratar o dataset como uma unidade só.
- `br_ibge_amc` (`municipio_de_para`) — crosswalk de códigos de município ao longo do tempo (municípios que se desmembraram); é metadado de correspondência, não dado sobre o município em si.
- `br_ibge_nomes_brasil` (`quantidade_municipio_nome_2010`) — nomes de bebês por município, censo 2010; curiosidade demográfica, não indicador.
- `br_ibge_censo2022_raca` (`fecundidade_idade`, `instrucao`) — **verificado parcialmente 2026-09-02**: o grão é raça/cor **cruzada** com categoria (`cor_raca` × `categoria_principal`, ex. nível de instrução), não uma contagem simples de população por raça — se `censo_extra`/`demografia` no dashboard só tem contagem simples, não é sobreposição, é um corte novo. Não foi possível confirmar contra o código do dashboard em si (fora deste repo, ver nota no topo do arquivo) — verificação de sobreposição real ainda pendente de quem tiver acesso ao `xyz`.
- `br_ibge_censo_demografico` (`microdados_domicilio_1970` … `2010`) — censos históricos pré-2022; dado rico mas trabalho pesado (33 tabelas, microdados de domicílio) pra uma seção "perfil atual" — mais adequado a uma seção de série histórica futura, se um dia o dashboard ganhar visão temporal longa.
- `br_ibge_pnadc` (`ano_municipio_raca_cor`, `ano_municipio_grupo_idade`) — **verificado 2026-09-02**: `ano_municipio_raca_cor` de fato tem `id_municipio`+`populacao`+`raca_cor`+`sexo`, confirmando a agregação municipal — mas cobre só **27 municípios por ano** (as capitais, onde a amostra do PNAD-C é densa o bastante pra publicar no grão município) e para em **2019** (zero linhas em 2022 ou depois). Fica no Balde C mesmo: promoveria uma seção que existe pra 27 das 5.570 cidades e já está parada há 7 anos.
- `br_inep_ana`, `br_inep_avaliacao_alfabetizacao`, `br_inep_censo_educacao_superior`, `br_inep_educacao_especial`, `br_inep_indicador_nivel_socioeconomico`, `br_inep_sinopse_estatistica_educacao_basica` — tabelas INEP adicionais (alfabetização, educação especial, nível socioeconômico, ensino superior); o núcleo forte (IDEB/SAEB/ENEM/censo_escolar/SISU) já está coberto, estas são complementares, não um buraco óbvio.
- `br_inmet_bdmep` (`estacao`, `microdados`) — dados meteorológicos por estação INMET; só município com estação por perto, e é clima, não indicador socioeconômico.
- `br_ipea_acesso_oportunidades` (`estatisticas_2019`) — índice de acesso a oportunidades urbanas (empregos, serviços por transporte); dado único de 2019, sem série.
- `br_mobilidados_indicadores` — indicadores de mobilidade urbana; provavelmente só grandes cidades têm cobertura real.
- `br_ms_populacao` (`municipio`) — **já verificado, não é hipótese**: tema 54 (`docs/respostas.md` T54-1, 2026-08-25) já confirmou que bate byte-a-byte com `br_ibge_populacao` na maioria dos anos mas diverge até 4% em 2022-2023 porque o MS não aplicou o reset do Censo 2022 — caveat verificado na métrica `populacao` (`metrics.yaml`). Não somar as duas séries nesses dois anos; nos demais são intercambiáveis.
- `br_ms_vacinacao_covid19` (`microdados_estabelecimento`) — vacinação covid por estabelecimento; dado histórico de um evento específico, não indicador contínuo.
- `br_mjsp_sisdepen` (`populacao_carceraria`) — população carcerária; o projeto já tem conhecimento verificado deste dataset (`bridges.yaml`, correção de formato feita nesta mesma sessão), custo de adicionar é baixo.
- `br_poder360_pesquisas` (`microdados`) — pesquisas eleitorais; dado de opinião, não indicador do município.
- `br_simet_educacao_conectada` (`escola`) — conectividade de escola; sobrepõe parcialmente `conectividade`/`educacao` já existentes.
- `br_cgu_dados_abertos` (`conjunto`, `organizacao`, `recurso`) — metadado do portal de dados abertos, não dado sobre o município.
- `br_cgu_fef` (`microdados`, `municipios_sorteados`, `sorteio`) — Fundo de Fiscalização de sorteio da CGU; nicho, cobertura por sorteio, não sistemática.
- `br_cgu_garantia_safra` — já tem bridge documentado e é da mesma família de benefícios, mas não é usado ainda; baixa prioridade só porque `bolsa_familia`/`bpc` já cobrem o essencial de `beneficios`.
- `world_oecd_public_finance` (`country`) — grão é país, não município; entrou na varredura por falso positivo (não tem coluna de município real) — descartar da lista de pendências.

### Como decidir depois

Pra promover um item do Balde A/B pra uma seção real: `mcp__rodado__describe_table`
+ uma query real no beelink pra confirmar que Nova Friburgo (`id_municipio`
`3303401`) tem dado não-nulo, antes de prometer a seção no dashboard — vários
destes datasets têm bugs conhecidos e catalogados (`br_rf_cafir`,
`br_ibama_embargos`) que só apareceram ao tentar de fato.

---

# Parte III — Saúde mental: mapa do que o espelho responde

> **Fechada em 2026-09-02** — virou relatório publicado:
> `pages/analises/mapa-da-saude-mental/` ("O mapa da saúde mental no SUS",
> commit `815d658`, rodada em paralelo com esta sessão). Achados: PNS 2019
> tem o escore PHQ-9 completo (colunas `n010`-`n018`, 9 itens — não em
> `Q09201`/`Q094` como esta sessão tinha mapeado abaixo, que são
> acompanhamento/abandono de tratamento, não o instrumento de rastreio) —
> 10,5% dos adultos com sintoma depressivo moderado/grave em 2019, de 7,4%
> (AM) a 14,9% (SE); CAPS fez 16,4 milhões de atendimentos em 2023 (2,2x
> 2013), com buraco de 16x em 2020; taxa de suicídio quase dobrou
> 2000-2021 (3,78→7,14/100mil, 78% homens); notificação de autolesão
> (SINAN) cresceu 10x mais rápido que óbito real no mesmo período —
> mais cobertura de notificação que epidemia, não confundir as duas séries.
> O mapa abaixo (tabelas, chaves, três pontes fechadas nesta sessão)
> fica como registro do levantamento que alimentou o relatório — não
> precisa de mais trabalho.

### Tabelas já mapeadas

| Tabela | O que dá | Chave/filtro |
|---|---|---|
| `br_ms_sia.psicossocial` | Atendimentos em CAPS/serviços psicossociais do SUS, mensal, por município. `cid_principal_categoria/subcategoria` (diagnóstico), `tipo_droga`, `indicador_situacao_rua`, idade/sexo/raça | `ano`, `id_municipio` |
| `br_ms_cnes.leito` | Leitos de psiquiatria por estabelecimento/município — capacidade instalada, não atendimento | `id_municipio`, especialidade |
| `br_ms_cnes.estabelecimento` | Localiza CAPS especificamente (não só leito psiquiátrico): `tipo_unidade = '70'` = "centro de atencao psicossocial". Verificado: 1.822 CAPS distintos (`id_estabelecimento_cnes`) em 2010 subindo pra 3.411 em 2023 — condiz com a expansão conhecida da rede CAPS; a tabela é de grão mensal (`ano`+`mes`), então `count(*)` sem `DISTINCT id_estabelecimento_cnes` infla ~12x | `id_municipio`, `tipo_unidade='70'` |
| `br_ms_sih.aihs_reduzidas` | Internações SUS (AIH); não é específica de psiquiatria, mas `especialidade_leito` + `cid_principal_categoria/subcategoria` (e 9 diagnósticos secundários) permitem filtrar por CID F00-F99. Tem custo (`valor_aih`), permanência, óbito (`indicador_obito`) | `cid_principal_categoria` LIKE 'F%' |
| `br_ms_sim.microdados` | Óbitos (SIM). `causa_basica` em CID-10 isola suicídio (X60-X84) e transtorno mental como causa (F00-F99); cruza com `circunstancia_obito`, idade, sexo, escolaridade, município | `causa_basica`, `id_municipio_residencia` |
| `br_ms_sinan_violencia.microdados_violencia` | Notificação de violência interpessoal/autoprovocada (SINAN). Colunas específicas: `LES_AUTOP` (lesão autoprovocada), `CONS_SUIC` (ideação/tentativa de suicídio), `CONS_MENT` (transtorno mental como consequência), `TRAN_MENT`/`TRAN_COMP` (transtorno preexistente), `DEF_MENTAL`, `AUTOR_ALCO` | `ID_MUNICIP`, `NU_ANO` |
| `br_datasus_cid10.codigos` | Referência CID-10 — monta a lista de códigos F00-F99 (transtornos mentais) e X60-X84 (suicídio) usada nos filtros acima | lookup |

**Cuidado ao decodificar:** `sexo`, `raca_cor`, `estado_civil` em `br_ms_sim.microdados` têm código que **diverge por tabela** — sempre decodificar via `br_ms_sim.dicionario`, nunca reusar código de outra fonte (ver `coded_value_warning` do `describe_table`).

**Atualização 2026-09-02** — as três investigações abaixo foram fechadas (`describe_table`/`resolve_join`/query real no beelink):

- **`br_ms_pns.microdados_2013`/`microdados_2019`**: tem sim saúde mental autorreferida — 2019 usa o módulo Q (`Q09201`/`Q09202` diagnóstico de depressão, `Q094`/`Q098` acompanhamento, `Q09502` motivo de abandono do tratamento, `Q106` encaminhamento a especialista); 2013 usa `J004=18` ("Depressão") e `J004=19` ("Outro problema de saúde mental") na lista de causa da última consulta, mais `Q113` (percepção de estigma). **Mas a tabela não tem `id_municipio` nem `sigla_uf` além de `sigla_uf` — grão é só UF/nacional** (é PNAD-like, amostral, geografia detalhada é sigilosa) — mesma limitação do `br_ipea_atlasviolencia` (Parte I). Serve pra fechar parcialmente a lacuna de prevalência, mas só em recorte estadual/nacional, nunca municipal, e é diagnóstico autorreferido de depressão especificamente — não "transtorno mental" em geral.
- **`br_ms_cnes.estabelecimento`**: fechado — ver linha nova na tabela acima (`tipo_unidade='70'`).
- **`resolve_join` entre `psicossocial`/`aihs_reduzidas`/`sim`/`cnes.estabelecimento`**: psicossocial↔sih, psicossocial↔cnes.estabelecimento e sih↔sim juntam limpo por `ano`/`mes`/`sigla_uf`/`id_estabelecimento_cnes` — nenhuma ponte nova precisou pra esses pares. **Um gap real apareceu**: `sih.aihs_reduzidas` guarda município em `id_municipio_paciente` (6 dígitos, hub `id_municipio_6` já em `bridges.yaml`) enquanto `sim.microdados` guarda em `id_municipio_residencia` (7 dígitos, formato padrão, mas nunca tinha sido registrado como bridge) — `resolve_join(sih, sim)` não achava o par de município por isso, só `ano`/`sigla_uf`. Registrado agora em `bridges.yaml` (`br_ms_sim.microdados.id_municipio_residencia`/`id_municipio_ocorrencia`, concept `id_municipio`, verificado 99,85%/100% em 2022) — cruzar SIH×SIM por município exige então o crosswalk `id_municipio_6`→`id_municipio` (via `br_bd_diretorios_brasil.municipio`), não um cast direto. **Nota**: `join_keys.md` **não** foi regenerado junto — `scripts/gera_join_keys.py` lê `schemas.json`, que nesta sessão tinha alterações não commitadas de outra sessão em paralelo (218 datasets/940 tabelas vs. os 211/895 do HEAD); regenerar contra esse estado teria misturado tabelas novas de raspagem alheia no diff deste bridge. Regenerar `join_keys.md` depois que o `schemas.json` desse ciclo de sync for commitado.

### Lacunas conhecidas

- **Prevalência de transtorno mental na população geral**: parcialmente fechada por `br_ms_pns` (diagnóstico autorreferido de depressão, só grão UF/nacional) — mas nenhuma tabela dá prevalência **municipal**, nem cobre transtorno mental além de depressão. Todo o resto é atendimento (demanda que chegou ao SUS) ou óbito, sub-representando quem não busca/consegue atendimento.
- Sem cobertura de rede privada/planos de saúde — todas as fontes são SUS (SIA, SIH, CNES) ou vigilância (SIM, SINAN); `br_ms_pns` cobre a população geral mas sem grão municipal.

### Próximos passos

Nenhum — ver a nota de fechamento no topo desta Parte III. O relatório está
publicado em `pages/analises/mapa-da-saude-mental/`; qualquer extensão
futura (outro recorte, série temporal mais longa, cruzamento com rede
privada) é um relatório novo, não uma pendência desta parte.
