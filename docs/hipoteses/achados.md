# Achados fortes × cobertura online

Companheiro de [`achados_fortes.md`](achados_fortes.md): mesma lista de 85
achados, com uma pergunta a mais em cada linha — **esse fenômeno já é
conhecido fora deste espelho?** Curadoria editorial antes de decidir o que
vira `pages/analises/`, não checagem de prioridade científica. ~35 buscas
(`WebSearch`, 2026-09-07) por *fenômeno geral*, não pela correlação exata —
nenhuma medição deste espelho tem paralelo publicado por construção; o que se
busca é se o padrão já circula.

## Legenda

| Selo | Significa |
|---|---|
| 🟢 | **Pouco coberto** — busca não achou equivalente; candidato a ângulo inédito (busca vazia ≠ ineditismo confirmado) |
| 🟡 | **Parcial** — mecanismo conhecido, medição/ângulo específico não |
| 🔴 | **Bem documentado** — publicar como "descoberta" seria enganoso |
| ⚫ | **Não verificável por busca** — validação interna, achado intraurbano de cidade única, correção, ou nulo que essa escala não se aplica |

Nas tabelas por seção, 🟢 vem primeiro. **Essa escala só serve para achado
positivo** — para negativo/nulo a pergunta certa é se existe crença
pública/oficial de que a relação é positiva. Ver a seção seguinte.

---

## Achados negativos — quando o nulo é a notícia

A própria `achados_fortes.md` já nomeia um padrão e o rastreia por sete
achados independentes, espalhados pela lista e cada um lido isoladamente como
caso pontual: **"a regra não morde"** — um mecanismo de controle formal
(fiscal, licitatório, creditício, cultural) que existe *explicitamente* para
filtrar risco, e na prática não filtra nada. Juntos, não são sete achados
médios — são um único achado forte: a mesma falha estrutural aparece em sete
domínios que não têm nenhuma razão administrativa para compartilhar causa.

| # | Achado | O que a crença afirma | O que os dados mostram | Crença é documentada? |
|---|---|---|---|---|
| **T68-3** | CAUC (pendência fiscal) × sucesso de convênio | STN, FNP e associações municipalistas afirmam categoricamente: pendência **bloqueia** transferência voluntária | r_parcial ≈ −0,001 — quem decide é a emenda parlamentar (B1), não o filtro fiscal | 🔴 sim — é a própria justificativa oficial do CAUC |
| **G7** | CAPAG (nota de capacidade de pagamento) × contratação real de dívida | Tesouro Nacional: a nota existe para "apresentar se um novo endividamento representa risco de crédito" — propósito declarado da ferramenta | r_parcial = −0,004 controlando renda — o gradiente aparente (A+ 40,4% × D 5,3%) é quase todo PIB per capita disfarçado | 🔴 sim — propósito declarado pelo próprio Tesouro |
| **D7 / F1** | Devedor da PGFN × acesso a licitação/pagamento municipal | Regularidade fiscal é pré-requisito formal de licitação; devedor "deveria" estar fora | R$ 241,7 bi em contratos e 22,7% do valor pago municipal vão a devedor da PGFN mesmo assim | 🔴 sim — é regra escrita na Lei de Licitações |
| **D9 / K2 / F5** | CEIS/CNEP (sanção) × capacidade de contratar com o governo | "Empresas sancionadas estão impedidas de contratar com a administração pública" — texto normativo do próprio cadastro | R$ 18,4 bi pagos a sancionado (F5); sancionado é 17-24× a taxa-base entre patrocinadores da Rouanet (K2) | 🔴 sim — impedimento é a razão de existir do cadastro |
| **F6** | Constatação grave da CGU × pobreza do município | Suposição implícita de fiscalização de risco: município mais pobre deveria concentrar mais achado grave | Bruto +0,37 → parcial +0,08 — depois do controle a irregularidade grave é quase uniforme; o que varia é a chance de ser sorteado para auditoria, não a conduta | 🟡 crença implícita, não declarada por nenhum órgão |
| **C3 / D19 / J5** | Notificação compulsória (violência, dengue) × incidência real | Série de notificação é tratada como medida do fenômeno em si | Notificação prevê muito mais **acesso a serviço** (celular, internet, renda) que o desfecho real — J5 mede isso direto: 4,4× mais preditor de notificação que de internação | 🟡 crença de uso corrente em pesquisa, raramente questionada explicitamente |
| **I2** | Choque de CFEM (mineração) × emprego/saúde fiscal municipal | Senso comum de "boom" de mineração: mais royalty, mais emprego formal, mais folga fiscal | r_parcial +0,04 (CAGED) e −0,002 (CAUC) — mineração emprega pouco e não é choque fiscal detectável, mesmo excluindo outlier de denominador | 🟡 crença difusa, não institucional |

**O metapadrão é a notícia.** Sete mecanismos de controle formal que existem
para filtrar risco, e nenhum filtra — isso, sozinho, é mais forte como
reportagem do que qualquer um dos sete isolado. "Nenhuma das travas de
integridade do setor público brasileiro trava" é a manchete que a lista
aponta e que nenhum item individual contava sozinho — e é, plausivelmente, o
achado mais publicável de todo `achados_fortes.md`.

**Um oitavo caso chegou com a rodada h3, e é o mais forte de
todos**: sancionado (CEIS) é **220× mais provável** (Mantel-Haenszel
estratificado por CNAE×idade) de também ser terceirizado federal; sancionado
(CNEP), **158×**. Diferente dos outros sete — nulo ou quase nulo —, aqui o
cadastro de sanção não só falha em filtrar, ele **concentra** exatamente onde
deveria bloquear.

---

## Leitura agregada

| Selo | Achados | % |
|---|---|---|
| 🟢 Pouco coberto | 28 | 33% |
| 🟡 Parcial | 26 | 31% |
| 🔴 Bem documentado | 22 | 26% |
| ⚫ Não verificável por busca | 9 | 11% |

Os 🟢 (listados primeiro em cada tabela abaixo) são os candidatos a ângulo
inédito, mas busca vazia não é confirmação — vale checagem mais funda (Google
Scholar, acervo de jornal, TCU/CGU direto) antes de publicar como furo. Os
quatro com número mais forte e explicação mais contraintuitiva: **D7**
(devedor vence licitação), **B1** (emenda como mecanismo de aprovação de
convênio), **G3** (SNIS subdeclara e quem prevê é celular, não renda) e **B9**
(Desenrola 9,4× mais rico). Os 🔴 servem como contexto que valida uma análise
maior, não como manchete própria; fontes pagas e teses fora do índice do
Google não aparecem em nenhuma busca, então um 🟢 pode já estar coberto em
lugar que a varredura não alcança.

---

## Novidades das rodadas de trincas (h2/h3)

As duas rodadas majoritariamente confirmam achados já publicados (é o que a
validação cega de cada uma reporta). O que sobra de genuinamente novo, fora o
caso já coberto acima:

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **h2** | CNO (obra registrada) × geração distribuída por domicílio, +0,48 | 🟢 | Nada cruza registro formal de obra com geração solar — só valorização de imóvel por instalar placa |
| **h3** | Fornecedor do Banco de Preços em Saúde × contratado do TCE-RJ: MH = 291,3 (maior de toda a corrida) | 🟢 | Nenhum cruzamento entre esses dois cadastros de fornecedor aparece feito em outro lugar |
| **h3** | Candidato (desde 2014) como sócio × empresa ligada ao CEPIM: 12,78× a taxa-base | 🟢 | Eixo político×empresa via renegociação de dívida não aparece testado; casamento nome+CPF mascarado tem 58,8% de ambiguidade |
| **h2** | IDHM 2010 × cobertura de plano de saúde privado, +0,47 | 🟡 | IDHM já correlaciona com outros desfechos de saúde, mas não com plano privado especificamente |
| **h3** | Cobertura 4G/5G × share de docente rural, −0,45 | 🟡 | Falta de internet do professor rural é fenômeno conhecido; a correlação com cobertura de rede não |
| **h3** | Mesmo fornecedor serve Câmara e Senado (CEAPS): MH = 264,9 | 🟡 | Casos avulsos de fornecedor duplo já circularam; a magnitude sistemática da sobreposição não |

A rodada h3 também derrubou o que era o achado mais forte da rodada h2 (IVS 2010 × Bolsa Família, então +0,51): uma guarda nova
("mesmo construto") reclassificou o par como a mesma coisa medida duas vezes
— pobreza por dois nomes —, não uma correlação de fato.

---

## As relações fortes (2026-09-05)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **B1** | Emenda parlamentar leva convênio a 86,5% de aprovação × 15,6% sem ela | 🟢 | O mecanismo emenda→SICONV é descrito em manuais oficiais do TransfereGov, mas nenhum estudo publicado quantifica o gap de aprovação |
| **B9** | Desenrola: DF 945 × MA 100 por mil famílias do Bolsa Família (9,4×) | 🟢 | Debate público sobre Desenrola existe, mas é sobre dívida *estadual*; a desigualdade regional na renegociação de dívida de pessoa física não aparece medida |
| **B13** | 16% das terceirizadas federais estão no CEIS/CNEP | 🟢 | Gasto com terceirização (R$84 bi, IPEA) e existência do CEIS são documentados separadamente; o cruzamento não |
| **B4** | Geração solar por domicílio × cobertura do Bolsa Família, r_parcial −0,34 | 🟢 | Cobertura de imprensa sobre solar é sobre GW instalado e empregos, não sobre geografia de classe |
| **B10** | Inadimplência PF × conectividade, r −0,62 (vs −0,31 com PIB pc) | 🟢 | Dados abertos do BC têm as duas séries separadas; ninguém parece ter cruzado |
| **T68-3** | CAUC × sucesso em convênio, r_parcial −0,001 (nulo) | 🟢 | Achado negativo específico — não haveria cobertura de imprensa para um "não efeito" |
| **B2** | Densidade agropecuária × cobertura 4G/5G, r_parcial −0,55 | 🟡 | O apagão rural é fato conhecido (cobertura móvel 58,6% rural × 99,75% urbana, Anatel) — a correlação *com densidade agropecuária especificamente*, não |
| **B3** | Multa IBAMA por tipificação: Amazônia × Cerrado, 45× em infração documental | 🟡 | Valores de multa por bioma aparecem soltos na imprensa (Poder360, Terra), mas não essa comparação direta por tipificação |
| **T73-2** | Margem do intermediário na terceirização federal, regressiva (53%→30%) | 🟡 | O piso salarial 27,4% menor do terceirizado é documentado (IPEA); a regressividade *por faixa salarial* não |
| **B11** | Templos por domicílio × Bolsa Família, r_parcial +0,22 | 🟡 | Pesquisa do Cebrap (Censo 2022) já mostra mais templo em favela que fora dela — mecanismo relacionado, não a mesma correlação |
| **T66-2** | "Adiantamento a depositante": 59,2% de inadimplência | 🟡 | A modalidade e sua natureza de crédito emergencial são documentadas no SCR.data; a taxa específica não aparece publicada |
| **T58-1** | Substância minerada prediz perfil social (basalto rico × quartzito pobre) | 🟡 | Existe linha de pesquisa "Mineração & Condições de Vida" sobre os 79 municípios mineradores, mas não segmentada por substância |
| **B18** | BNDES: cobertura indireta 12,6× a direta | 🟡 | O modelo de crédito indireto via banco credenciado é descrito pelo próprio BNDES; a razão exata não |
| **B7 / B16** | Pix: 70% dos municípios devedores líquidos; penetração r_parcial +0,38 com 4G/5G | 🟡 | Pix como infraestrutura pública digital é discurso oficial do BC; a métrica "devedor líquido" por município é original |
| **T70-3** | Canteiro brasileiro é autoconstrução pobre, não incorporação | 🔴 | IBGE confirma 77% das moradias autoconstruídas; informalidade na construção 68% (maior no Norte/Nordeste) é dado oficial corrente |
| **B5 / T59-1** | Alerta DETER sem autuação: 27 municípios, zero autos desde 2015 | 🔴 | ((o))eco e Brasil de Fato já documentaram: só 1,3% dos alertas de desmate geram auto de infração — "impunidade" é tema recorrente de imprensa ambiental |
| **B15** | Desmatamento acumulado: Cerrado 326.731 km² × Amazônia 139.868 km² | 🔴 | MapBiomas e PRODES confirmam publicamente: Cerrado supera a Amazônia em área desmatada há dois anos seguidos |
| **T69-2** | Pendências do CAUC: Matriz de Saldos Contábeis 1.509 × transparência eletrônica 8 | 🔴 | FNP e Tesouro Nacional já divulgam: 59,3% dos estados e 61,2% dos municípios têm pendência no CAUC |

## Rodada de fechamento (C1–C17, 2026-09-05)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **C12** | "Frente ativa" (DETER÷passivo): Roraima e Amapá lideram | 🟢 | A narrativa "nova fronteira é Roraima/Amapá" circula qualitativamente; esta métrica específica não |
| **C15** | HHI de titulares da CFEM: mediana 0,822, 44% acima de 0,9 | 🟢 | CFEM é bem documentada em geral; concentração de titular por município não aparece medida |
| **C2** | Valor agropecuário/ha × crédito/ha, r +0,73 | 🟡 | Decorre do mesmo corpo de literatura de C1, mas a forma intensiva específica (por hectare) não aparece isolada |
| **C3** | Notificação de violência adolescente × homicídio juvenil, r≈0 (mas +0,22 com PIB) | 🟡 | Viés de "notificação mede capacidade de notificar" é tema conhecido em saúde pública (ver subnotificação de HIV/Aids, 42,7%); esta combinação específica não |
| **C5** | Obesidade adulta × PIB pc +0,54; déficit infantil × BF +0,46 | 🟡 | Transição nutricional migrando para baixa renda é tema ativo (SciELO); a coexistência "geografias opostas" no mesmo painel não |
| **C6** | Servidor federal ganha 7,74× a mediana no PB, 2,73× no AP | 🟡 | Debate "privilégio do funcionalismo federal" é recorrente (InfoMoney, CUT); a métrica exata (razão salário/mediana RAIS por UF) não |
| **C9** | Gasolina mais cara no município pobre; concorrência não explica | 🟡 | Caso isolado documentado (Porto Velho, mesma distribuição, preço final maior); a generalização sistemática nacional não |
| **C10** | Vazão recente ÷ histórica: mediana 0,901, 38% perderam >20% | 🟡 | Seca histórica é manchete recorrente (CNN, Rio São Francisco −60% em 30 anos); a métrica de razão por estação e o viés de cobertura na fronteira agrícola são originais |
| **C13** | 22 de 27 UFs são "renda média-alta" pelo critério do Banco Mundial | 🟡 | Brasil como país é classificado assim pelo Bird; o exercício "UF como país" não aparece feito |
| **C14** | Deslocamento intermunicipal RAIS: 58,6% na mesma região imediata | 🟡 | Literatura de mobilidade pendular é robusta (SciELO, IBGE Censo); esta cifra específica com RAIS não |
| **C1** | Crédito rural × desmatamento acumulado, r_parcial +0,64→+0,39 | 🔴 | Literatura acadêmica extensa (IPEA, Imazon, Assunção/Gandour/Rocha 2013) já mede esse vínculo com metodologia própria |
| **C4** | INSE (INEP) × pobreza, r = −0,90 | 🔴 | Confirmado de forma independente: literatura já reporta correlação INSE×pobreza de 0,86–0,93 — colinearidade é fato estabelecido |
| **C8** | Medalhas olímpicas por edição: degraus de política, não de PIB | 🔴 | Bem documentado: salto de ~12 para ~19 medalhas/edição após Bolsa Atleta é citado amplamente na imprensa esportiva |
| **C11** | Desmatamento acumulado por UF: PA lidera, 5 dos 6 seguintes são Cerrado/Caatinga | 🔴 | Dado PRODES é público e citado rotineiramente |
| **C17** | *(duplicata de T69-2)* | 🔴 | ver T69-2 |
| **C16** | 6 municípios fora da Área Mínima Comparável 2000→2010 | ⚫ | Fato técnico de malha do IBGE — não é o tipo de coisa que geraria cobertura, é achado de nota de rodapé metodológica |

## Rodada de fechamento das pendentes (D1–D22, 2026-09-06)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **D6** | CEPIM: execução financeira 85,1% × prestação de contas 39,3% | 🟢 | Não encontrado — nicho de controle interno pouco coberto por imprensa |
| **D7** | Devedor da PGFN vence licitação federal: R$ 241,7 bi em jogo | 🟢 | Buscado duas vezes — a regra formal (impedimento) é bem descrita, mas nenhuma reportagem documenta que na prática não trava |
| **D9** | 55% das licitações federais com participante único | 🟢 | TCU só publica jurisprudência sobre licitar com 1 participante ser permitido — nenhuma estatística agregada encontrada |
| **D13** | 2.755 CNPJ sancionados citados em diário oficial de 482 municípios | 🟢 | Não encontrado — extração de texto de Querido Diário é método original |
| **D17** | Hora extra do Senado: pico em julho (3,6× a mediana) | 🟢 | Cobertura de recesso parlamentar existe, mas não cruzada com hora extra de servidores |
| **D22** | Assistência social é 3,51% da despesa municipal, não responde a BF | 🟢 | Não encontrado — nicho de execução orçamentária municipal |
| **D8** | 59% dos sócios de empresa sancionada estão em outras empresas | 🟡 | O expediente ("empresa nova, mesmo sócio") é descrito qualitativamente por Jusbrasil e jurisprudência do STJ; o percentual exato não |
| **D11** | Instituições financeiras sediadas: 690→464 municípios | 🟡 | Concentração em SP (60% das sedes bancárias) é documentada; a série temporal de queda de município sede não |
| **D12** | Crédito rural cresce 2,75× × PIB agro 1,66×, descolamento maior no pobre | 🟡 | Descolamento crédito/produção é tema ativo (Insper, "dívida cresce mais que produção"); o recorte por pobreza municipal não |
| **D14** | Emergência declarada localmente × reconhecimento federal: só 83 de 401 | 🟡 | O processo de reconhecimento via S2ID é documentado oficialmente; a taxa de descasamento (20%) não |
| **D19** | Notificação de dengue × PIB pc, +0,22 (artefato de registro) | 🟡 | Padrão geral (subnotificação mesmo com acesso, estudo de Aids 42,7%) é conhecido; esta combinação específica não |
| **D20** | 10,7% dos doadores de 2014 hoje são fornecedores do PNCP | 🟡 | Vínculo doação→contrato é estudado academicamente (Redalyc); o recorte "quintil de doação × % fornecedor" não |
| **D2** | Encarceramento × queda de homicídios, r = −0,02 (nulo) | 🔴 | O próprio diretor-geral do Depen já declarou publicamente "encarceramento não reduz criminalidade" (CNJ) |
| **D3** | Letalidade policial: AP 13,0% e RJ 12,7% × SE 0,6% | 🔴 | Fórum Brasileiro de Segurança Pública publica isso anualmente; Amapá como líder é manchete recorrente |
| **D5** | Plano de saúde privado × pobreza, r = −0,73 (sistema dual) | 🔴 | Literatura de saúde coletiva (SciELO) documenta extensamente o sistema dual renda/plano × ESF/pobreza |
| **D10** | Metade dos municípios perdeu agência bancária 2014→2022 | 🔴 | Amplamente coberto: Dieese/sindicatos bancários reportam 37% de fechamento de agências em 10 anos, ~48% dos municípios sem agência |
| **D15** | Escola rural sem internet: 30,5% × 2,0% urbana | 🔴 | NIC.br e Anatel publicam números quase idênticos (17,1% × 0,9% em outra medição) — tema recorrente |
| **D16** | Senado ~15 pontos mais disciplinado que Câmara (índice de Rice) | 🔴 | Literatura acadêmica (SciELO, Limongi/Figueiredo) mede disciplina partidária por índice de Rice extensamente |
| **D18** | Cooperativas de crédito: 433 × 20 bancos grandes, município médio | 🔴 | Bem documentado: Sicredi/Sicoob única presença em ~460 municípios, avançando onde bancos fecham |
| **D21** | Despesa do Judiciário estadual: TJDFT R$ 985 × TJCE R$ 145 per capita | 🔴 | CNJ confirma publicamente desigualdade similar (TJDFT R$ 554,95 × média nacional R$ 123,57 — números diferentes, mesmo padrão) |
| **D1** ⚠️ | *(rebaixado pela própria bateria H16 — não é mais achado)* | ⚫ | Correção interna, não afirmação a checar externamente |
| **D4** ⚠️ | *(rebaixado — lacuna de gênero é fenômeno de renda no bruto, não sobrevive ao parcial)* | ⚫ | Correção interna |

## Hipóteses inéditas fora de `perguntas.md` (E1–E3, 2026-09-06)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **E2** | Pé-de-Meia: r = +0,89 com cobertura do Bolsa Família (melhor focalização medida) | 🟡 | A prioridade a famílias do BF é regra oficial documentada (CadÚnico); a magnitude da focalização (r=0,89) não aparece medida |
| **E3** | Nota de transparência (EBT/CGU) não prevê integridade — sinal é o contrário | 🔴 | A própria CGU já reconhece publicamente que o IPC "não mede corrupção real"; a crítica ao indicador é debate estabelecido |
| **E1** | *(encerrado — concentração onomástica não sobrevive ao parcial)* | ⚫ | Achado negativo/retratação interna |

## Bateria H01–H19 (F1–F7, 2026-09-06)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **F1** | Devedor da PGFN é 12,2% dos credores municipais, leva 22,7% do valor | 🟢 | Mesmo padrão de D7 — regra documentada, prática não |
| **F2** | Reclamação no Consumidor.gov como proxy de acesso digital, r_parcial +0,29 com Pix | 🟢 | Não encontrado — reformulação original de uma base de reclamação de consumidor |
| **F4** | Concentração de pagamento municipal: HHI mediano 0,167, >50% em 234 municípios | 🟢 | Não encontrado — primeira medida de concentração de fornecedor municipal, segundo o próprio achado |
| **F5** | R$ 18,4 bi pagos a empresa sancionada (CEIS/CNEP) | 🟢 | Não encontrado agregado nesse nível |
| **F6** | Constatação grave da CGU não acompanha pobreza (+0,37→+0,08) | 🟢 | Não encontrado |
| **F7** | 49,4% dos pagamentos vão a fornecedor sediado no próprio município | 🟢 | Não encontrado |
| **F3** | Crédito rural/ha × desmatamento intensivo, r_parcial +0,45 | 🔴 | Mesmo corpo de literatura de C1 |

## Achados da varredura de inéditos (G1–G7, 2026-09-06)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **G3** | SNIS subdeclara saneamento; conectividade prevê mais que renda (+0,63) | 🟢 | A imprecisão do SNIS é reconhecida em geral (indicadores "de consistência limitada"); o mecanismo específico (celular > renda) não aparece |
| **G2** | Tamanho médio da propriedade × uso da terra (7× e 6× entre quintis) | 🟡 | Decorre do corpo de literatura de C1/C2 sobre concentração fundiária e produtividade |
| **G7** | CAPAG não prevê contratação de dívida real (r_parcial −0,004) | 🟡 | O próprio Tesouro já ressalva que CAPAG "é estimativa, não constatação da situação real" — a crítica institucional existe, o teste numérico não |
| **G1** | Preço de medicamento varia 2,4× a 5,8× entre compradores públicos, mesmo ano | 🔴 | SciELO já mediu variação de 32% a 482% do preço SIGTAP no Paraná — mesma ordem de grandeza, achado estabelecido na literatura de saúde pública |
| **G4** | Obra registrada (CNO) ÷ construção real (CNEFE): mediana 0,46 | 🔴 | Decorre do mesmo corpo de dados de informalidade na construção (IBGE 68%) |
| **G5** | Coleta de lixo em BH × padrão do imóvel, 5 degraus monotônicos | ⚫ | Achado intraurbano de uma única cidade — natureza da pergunta não geraria cobertura prévia |
| **G6** | Infraestrutura urbana precificada em Fortaleza, por rua não por face | ⚫ | Idem — intraurbano, grão de quarteirão, inerentemente original por construção |

## Fechamento do Bloco I (I1–I3, 2026-09-06)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **I1** | Bolsa Família prevê maternidade adolescente melhor que mercado de trabalho ou IDEB | 🟡 | Literatura de política social já liga BF a menor gravidez adolescente; a comparação de poder preditivo contra HHI ocupacional/IDEB é original |
| **I2** | Choque de CFEM não move CAGED nem CAUC (duplo nulo) | ⚫ | Validação metodológica interna contra artefato de denominador |
| **I3** | Construção por domicílio acompanha crescimento populacional, não só PIB | ⚫ | Achado de divisão de trabalho entre sessões, nota metodológica de nomenclatura incluída |

## Lei Rouanet (K1–K2, 2026-09-06)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **K1** | Funil Rouanet invertido: Sudeste converte pior que Norte (p=0,0002) | 🟢 | Concentração regional da Rouanet no Sudeste é conhecida qualitativamente; a inversão do funil de captação não |
| **K2** | Sancionado é 17-24× a taxa-base entre proponentes/patrocinadores da Rouanet | 🟢 | Não encontrado — primeiro cruzamento de `br_minc_salic` com CEIS/PGFN neste espelho |

## Trincas do Bloco R (L1, 2026-09-06)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **L1** | ITR per capita × tamanho da propriedade, r_parcial +0,53 (49× entre quintis) | 🟢 | Progressividade do ITR por tamanho é regra na lei; o teste empírico cruzando fiscal×fundiário não aparece feito |

## Achados das famílias vazias (J1–J5, 2026-09-06)

| # | Achado | Cobertura | Por quê |
|---|---|---|---|
| **J2** | Crédito rural é muito pulverizado (HHI mediano 0,007) | 🟢 | Não encontrado — contraste com concentração de fornecedor municipal (F4) parece original |
| **J4** | Escola sem internet × IDEB, r_parcial −0,144 (sobrevive a renda) | 🟡 | O gap de conectividade escolar é bem documentado (D15); o efeito sobre a *nota*, isolado de renda, não |
| **J5** | Conectividade prevê notificação 4,4× mais que internação | 🟡 | O padrão geral (notificação mede acesso, não incidência) é reconhecido em vigilância epidemiológica; esta medição comparativa específica não |
| **J1** | Bovino/ha × desmatamento, r_parcial +0,486 (supera o F3) | 🔴 | Pecuária como motor do desmatamento é o achado mais clássico e mais estudado da literatura ambiental brasileira |
| **J3** | Cesárea concentrada em horário comercial, excedente +8,7 pontos | 🔴 | Taxa de cesárea alta no Brasil e o padrão de agendamento em horário comercial são tema recorrente em obstetrícia e imprensa de saúde |
