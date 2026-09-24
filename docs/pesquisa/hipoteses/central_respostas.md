# Respostas — referência cruzada com central_perguntas.md

Mesma convenção de [`respostas.md`](respostas.md): cada entrada usa o código
`E<esquema>-<nº>` que identifica a pergunta em [`central_perguntas.md`](central_perguntas.md),
e carrega dois eixos — status (a query rodou?) e força do achado.

**Status:** ✅ respondida · ◐ parcial (rodou, mas com ressalva de cobertura/método) ·
⏳ pendente (não executada ainda) · ❌ sem resposta (bloqueio de dado verificado).
**Força:** 🟢 forte (contraste ≥2× ou padrão marcante) · 🟡 moderada (1,3×–2×) ·
🟠 fraca · ⚪ nula/achado negativo · ⬜ descritivo (contagem, série, fato, não é
correlação). Modificadores: **↯** contraria a hipótese · **⚠** número frágil.

Todas as queries rodaram em beelink via DuckDB, `run_sql` (read-only).

## Resumo

| # | Esquema | Achado | Força |
|---|---|---|---|
| E7-1 | concentração do valor das emendas | top 10% das emendas = 72,2% do valor pago; metade das emendas de menor valor = 2,7% | 🟢 |
| E2-1 | baixa concorrência em licitação | 44,9% das licitações do mirror têm exatamente 1 participante | ⬜ (base nacional, não segmentada por emenda) |
| E8-1 | crescimento do controle do Legislativo sobre o orçamento | valor pago em emenda salta de ~R$16,2bi (2016) para R$31,5bi pago / R$47,1bi empenhado (2025) | ⬜ |
| E6-1/E6-2 | vantagem de incumbência via emenda | reeleição 2022 não difere por ter recebido emenda (66,2% vs 64,5%) nem pelo valor médio recebido (R$34,9M vs R$32,8M) | ⚪↯ |
| E3-1 | emenda como barganha eleitoral (autovoto) | r = −0,06 entre emenda por município e votos do próprio senador ali (n=101 pares, 22 de 81 senadores) | ⚪⚠ |
| E1-1 | conflito de interesse automático | pareamento ingênuo nome+CPF parcial "acha" 71% dos deputados como sócio de empresa — volume alto demais pra confiar sem checagem manual | ⬜ (confirma a ressalva da reportagem) |
| E4-1/E4-2 | eventos desproporcionais ao orçamento | nenhum município-ano passa de 1,7% do próprio orçamento pago em emenda de cultura/desporto/turismo | ◐⚠ |

## E1 · Conflito de interesse por vínculo societário

- **E1-1 ✅ ⬜** Cruzando os 546 deputados federais eleitos em 2022 (`br_tse_eleicoes.candidatos`,
  CPF não nulo) com `br_me_cnpj.socios` (pessoa física, nome normalizado sem acento +
  os 6 dígitos centrais do CPF — únicos não mascarados no dado da Receita), **366
  deputados (71%) casam com pelo menos uma empresa**, somando 1.454 CNPJs distintos e
  mais de 50 mil pares nome-empresa. Essa taxa é alta demais pra ser um sinal confiável
  de vínculo real: nome comum + 6 dígitos de CPF colide com frequência em uma base de
  dezenas de milhões de sócios pessoa física. O achado, na prática, **confirma** o que a
  segunda reportagem do UOL diz — "os mecanismos públicos disponíveis também não
  conseguem identificar esses vínculos de forma automática" — em vez de refutá-lo:
  tentar automatizar aqui produz uma lista grande demais pra ser útil sem checagem
  caso a caso (nome completo, data de entrada na sociedade, CPF completo — que este
  mirror não tem, porque a Receita mascara e o TSE zera `cpf` em parte dos anos).
- **E1-2 ⏳** Não executado. Precisaria cruzar os 1.454 CNPJs candidatos de E1-1 com
  `br_cgu_licitacao_contrato.licitacao_participante` (vencedor=true) e casar o
  órgão/unidade gestora da licitação com o município beneficiado por emenda do mesmo
  deputado — `licitacao_participante` não carrega código de município direto, então o
  join real passa por `licitacao` (a checar `id_unidade_gestora`→município) antes de
  poder rodar. Próximo passo natural, não follow-up trivial.
- **E1-3 ❌** Bloqueio de dado: `central_emendas.md` nomeia os parlamentares dos seis
  casos (Marcelo Castro, Marcos Aurélio Sampaio, Duda Ramos, Yury do Paredão, Dal
  Barreto) mas não nomeia as empresas envolvidas — só a reportagem original do UOL
  tem isso. Sem o nome/CNPJ da empresa não há o que cruzar no mirror.

## E2 · Padrões atípicos de contratação

- **E2-1 ◐ ⬜** Nacionalmente, de 99.154 licitações em `br_cgu_licitacao_contrato.licitacao_participante`,
  **44.522 (44,9%) tiveram exatamente 1 participante** — quase metade das licitações do
  mirror não teve concorrência nenhuma. É consistente com o padrão que a reportagem
  aponta ("número reduzido de concorrentes"), mas isto é a taxa **nacional geral**, não
  segmentada por município beneficiado por emenda vs não — falta esse corte pra virar
  achado sobre emendas especificamente, não sobre licitação pública em geral.
- **E2-2 ⏳** Não executado — precisa de `licitacao_item` com valores de 1º/2º colocado
  por item, lógica de "diferença <1%" ainda não escrita.

## E3 · Emenda como moeda de barganha eleitoral

- **E3-1 ◐ ⚪⚠** Generalizando o caso do Amazonas para todos os senadores: casando
  `nome_urna` de senadores eleitos em 2022 com `nome_autor_emenda` (mesma UF), somando
  emenda paga por município (2023–2025) e correlacionando com os próprios votos do
  senador nesse município em 2022, **r = −0,06 (n=101 pares, 22 dos 81 senadores)** —
  nulo. Duas ressalvas importantes: (1) isto mede **autovoto**, não o "apoio de
  prefeito a outro candidato" que a reportagem original testou no Amazonas — é um teste
  adjacente, não uma réplica direta; (2) a cobertura é baixa — só 22 senadores casaram,
  porque `candidatos ano=2022` só cobre o 1/3 do Senado que disputou eleição naquele
  ano (Omar Aziz, eleito em 2014/2018, por exemplo só casou em 2 dos 17 municípios do
  AM em que destinou emenda). Estender pra 2018 e 2014 cobriria o resto do Senado —
  não feito aqui.
- **E3-2 ◐ 🟡⚠** Valor médio por emenda em anos eleitorais (2018, 2022) é **R$1,69M**
  contra **R$2,26M** em anos não-eleitorais — 25% *menor*, não maior, em ano eleitoral.
  Isto contraria a leitura ingênua da hipótese, mas o teste está confundido pelo
  crescimento forte da série ao longo do tempo (ver E8-1): 2018 e 2022 caem cedo na
  janela 2015–2025, quando os valores eram sistematicamente menores por causa da
  tendência, não do calendário eleitoral. Não dá pra separar os dois efeitos sem
  controlar por ano civil (ex.: comparar cada ano eleitoral só com o ano
  imediatamente anterior e posterior) — não feito aqui.

## E4 · Pulverização em eventos desproporcionais ao orçamento local

- **E4-1 ◐ ⚪⚠** Cruzando emenda paga em subfunção Desporto comunitário/Difusão
  cultural/Turismo/Desporto de rendimento com a despesa total paga do município no
  mesmo ano (`br_me_siconfi.municipio_despesas_funcao`), **nenhum município-ano passa
  de 1,7%** do próprio orçamento pago (o teto observado: município 1720309, 2016,
  R$200 mil de emenda de evento sobre R$11,9 milhões de despesa total). Ressalva
  séria: a mediana de "despesa total" calculada aqui somando todas as linhas de
  `estagio_bd='Despesas Pagas'` deu R$109 milhões — implausivelmente alto para o
  município mediano brasileiro, sinal de que a soma por função+subfunção do SICONFI
  conta o mesmo gasto mais de uma vez (hierarquia função→subfunção sobreposta). O
  denominador está inflado, então a razão real por município é maior que a calculada
  aqui — o teto de 1,7% é um **piso**, não um valor confiável. Precisa de uma consulta
  que pegue só o nível certo da hierarquia SICONFI antes de reportar como achado firme.
- **E4-2 ◐ ⚪⚠** Restringindo a município-ano de despesa total (calculada, com a mesma
  ressalva acima) abaixo de R$20 milhões, só **3 município-anos** aparecem no cruzamento
  — cobertura baixa demais pra caracterizar a distribuição em municípios pequenos. O
  caso citado pela reportagem (Santa Bárbara do Tugúrio, orçamento de R$930 mil) não
  aparece em `br_cgu_emendas_parlamentares` — indício de que aquele evento específico é
  financiado por outra via (convênio estadual direto, não emenda parlamentar federal
  rastreada pela CGU), fora do escopo deste dataset.

## E5 · Emenda não transforma a estrutura do orçamento municipal

- **E5-1 ⏳** Não executado. Pede painel: identificar municípios com salto de emenda
  recebida ano a ano, comparar a participação de saúde/educação na despesa total nos 2
  anos seguintes contra municípios sem salto — regressão/controle fora do escopo desta
  passada.

## E6 · Vantagem de incumbência via emenda

- **E6-1 ✅ ⚪↯** Dos 513 deputados federais eleitos em 2018, 434 casaram (por nome) com
  pelo menos uma emenda destinada entre 2019–2022; desses, 346 concorreram de novo em
  2022 e **229 (66,2%) se reelegeram**. O valor médio total de emenda recebida no
  mandato foi **R$34,9 milhões para os reeleitos** contra **R$32,8 milhões para os que
  perderam** — contraste de apenas 1,06×, praticamente nulo. O valor de emenda
  destinado **não** distingue quem se reelege de quem não se reelege.
- **E6-2 ✅ ⚪↯** Comparando quem teve emenda rastreada (n=434) contra quem não teve
  nenhuma (n=79): taxa de reeleição entre os que candidataram de novo foi **66,2% (229/346)
  com emenda** vs **64,5% (20/31) sem emenda** — 1,03×, sem diferença. Contraria a leitura
  ingênua de "quem manda mais dinheiro pro reduto se reelege mais" — pelo menos como
  efeito principal isolado, sem controlar por outros fatores de força eleitoral (parece
  mais causa comum — quem já é forte politicamente consegue tanto emenda quanto
  reeleição — do que a emenda "comprando" o segundo mandato).

## E7 · Concentração vs. pulverização do valor das emendas

- **E7-1 ✅ 🟢** Dividindo todas as emendas pagas (2014–2025, valor > 0) em decis por
  valor individual: o **decil de maior valor concentra R$121,8 bilhões — 72,2% do total
  pago (R$168,6bi)** — enquanto os **5 decis de menor valor (metade de todas as
  emendas, ~20.925 delas) somam só R$4,5 bilhões — 2,7% do total**. Contraste de ~27×
  entre a metade de baixo e o decil de cima. As duas coisas que a reportagem descreve
  são verdadeiras ao mesmo tempo e não se contradizem: há de fato uma quantidade enorme
  de emendas pequenas (pulverização, dificultando o acompanhamento item a item) *e* o
  grosso do dinheiro está concentrado num punhado de emendas grandes.

## E8 · Avanço do Legislativo sobre o orçamento

- **E8-1 ✅ ⬜** Série anual de `br_cgu_emendas_parlamentares.microdados`: valor pago
  salta de **R$16,2 bilhões em 2016** (primeiro ano com cobertura de autores
  confiável — 2014 tem `n_autores=1`, indício de problema de qualidade nesse ano
  inicial, tratar com ressalva) para **R$31,5 bilhões pagos / R$47,1 bilhões
  empenhados em 2025**. Confirma a direção do que a reportagem descreve (crescimento
  acentuado da fatia do orçamento controlada por emenda), embora os valores absolutos
  não batam exatamente com os citados (R$50,4bi ou R$60bi em 2025) — a diferença é
  provavelmente de métrica: "pago" é mais conservador que "empenhado", e a Central das
  Emendas provavelmente soma também emendas ainda não classificadas neste corte do CGU
  ou usa outra base (orçamentária/LOA em vez de execução).

## Bloqueios mapeados

- **CPF de candidatos** existe na maioria dos anos de `br_tse_eleicoes.candidatos`, mas
  **nulo por inteiro em 1996** e parcial em 2024 (230.724 de 462.821) — checar
  `count(cpf)` por ano antes de qualquer cruzamento por CPF.
- **`br_me_cnpj.socios.documento`** mascara CPF de pessoa física no padrão
  `***XXXXXX**` (só 6 dos 11 dígitos visíveis) — suficiente pra reduzir falsos
  positivos combinado com nome exato, mas não pra eliminá-los (ver E1-1). Não existe,
  neste mirror, nenhuma fonte com CPF completo de sócio pessoa física.
- **Vínculo família/ex-assessor/doador** (os outros três tipos de vínculo que a
  reportagem descreve, além de sócio direto) não tem fonte estruturada neste mirror —
  nem sobrenome de cônjuge, nem histórico de cargos em gabinete, nem doações de
  campanha ligadas a CNPJ vencedor de licitação (isso último seria possível via
  `br_tse_eleicoes.receitas_candidato` × `licitacao_participante`, não tentado aqui).
- **Nome da empresa contratada por convênio/emenda** não está em
  `br_transferegov.planos_acao` (ele carrega CNPJ do ente recebedor — geralmente a
  prefeitura — não da empresa executora da obra); a empresa executora só aparece via
  `br_cgu_licitacao_contrato`, que não referencia `id_emenda` diretamente — o elo entre
  as duas bases é indireto (por município + ano + função), nunca uma chave exata.
- **Auditoria do TCU** (citada em `central_emendas.md`: "82% das emendas analisadas por
  amostragem" com problema, tema da 19ª edição) não tem tabela correspondente neste
  mirror — sem fonte pra verificar ou generalizar esse número.
