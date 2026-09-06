# Banco de hipóteses — o que ainda dá para perguntar ao espelho

Complementa [`docs/hipoteses/perguntas.md`](../docs/hipoteses/perguntas.md) (o banco de perguntas
formuladas) e [`docs/hipoteses/achados_fortes.md`](../docs/hipoteses/achados_fortes.md) (o que já foi
medido). Aqui fica: **quanto do espaço de hipóteses é de fato válido**, **quais
hipóteses concretas estão na fila** e **como rodar a bateria offline**.

- Bateria: [`scripts/hipoteses_overnight.sh`](../scripts/hipoteses_overnight.sh)
- Blocos SQL: [`scripts/hipoteses/`](../scripts/hipoteses/)
- Estado das perguntas: **80 temas, 398 perguntas** — todos os 80 fechados em 2026-09-06 (77 via T77-1..5, 78-80 via T78-1..5/T79-1..5/T80-1..4, ver `docs/respostas.md`); 339 no conjunto-dourado
- Estado das hipóteses: **5 ✅ · 9 ❌ · 5 ◐ · 0 ⏳** (de H01–H19, fechado em 2026-09-06 — §3)
- **H20–H36** rodaram em 2026-09-06 (12): **6 ✅ · 4 ❌ · 1 ◐ · 1 ⏳** (achados G1–G7) — §5.2
- **H46–H62** rodaram em 2026-09-06, todas as 17: **5 ✅ · 9 ❌ · 3 ◐** (achados J1–J5) — §5.5
- H41–H45 são da sessão paralela (§2 Bloco I); H38–H40 fechados por ela em §5.2 Bloco H
- Espaço medido: **1.383 de 1.771** combinações de 2–3 famílias (78%) ainda inéditas;
  **5 ✅ · 0 ◐ · 0 ⏳** (de H41–H45, Bloco I, fechado em 2026-09-06 — mesma seção)

---

## 1 · Quanto do espaço é válido

Medido em cascata sobre `docs/context/basedosdados-schema.json` (228 datasets),
com a cobertura municipal **aferida no beelink** (`approx_count_distinct` sobre a
maior tabela municipal de cada dataset, amostrando as acima de 20M linhas).

| Filtro | Datasets | Trincas |
|---|---|---|
| **F0** tem chave territorial | 150 | 551.300 |
| **F1** tem chave **municipal** (só UF ⇒ n=27) | 128 | 341.376 |
| **F2** exclui referência, dicionário e diretório | 124 | 310.124 |
| **F3** cobre ≥500 municípios | 114 | 240.464 |
| **F4** cobre ≥2.000 municípios | 103 | 176.851 |
| **F5** três **famílias temáticas** distintas (24 famílias) | — | 146.316 |
| **F6** no máximo uma perna de covariável-controle | — | 145.236 |
| **F7** **trincas de família** — a hipótese, não a instância | — | **2.002** |

**2.002, não 573.800.** As 145 mil de F6 são *instâncias* da mesma hipótese:
`RAIS×SIM×PIB` e `CAGED×SIM×Censo` testam a mesma proposição com tabelas
diferentes. Hipótese distinta é trinca de **famílias**. Dessas, `perguntas.md`
cobre **93 (4,6%)** — restam **1.909**.

### A armadilha do F3

Datasets que *parecem* municipais e não são. Cruzá-los "por município" produz
n de duas casas:

| Dataset | Municípios de fato |
|---|---|
| `br_ibge_ipca`, `br_mobilidados_indicadores` | **9** |
| `br_ipea_acesso_oportunidades` | **18** |
| `br_fbsp_absp`, `br_ibge_pnadc`, `br_cgu_dados_abertos` | **29** |
| `br_rj_isp_estatisticas_seguranca` | **86** (é só o Rio) |
| `br_ms_cnes.estabelecimento_ensino` | 115 (tabela nicho; o dataset cobre 5.570) |

### As 24 famílias

`educacao` 14 · `demografia_censo` 12 · `vigilancia_sinan` 10 ·
`fiscalizacao_ambiental` 7 · `transferencia_renda` 7 · `saude_producao` 6 ·
`credito_financeiro` 5 · `compras_publicas` 5 · `desmatamento_clima` 5 ·
`trabalho_empresa` 5 · `fiscal_municipal` 4 · `conectividade` 3 ·
`agropecuaria` 3 · `politica` 3 · `justica` 3 · `mineracao_energia` 2 ·
`fundiario` 2 — e **sete famílias de uma perna só**: `precos_indices`,
`comercio_exterior`, `seguranca`, `mobilidade`, `mortalidade`, `natalidade`,
`sancao_integridade`.

**As famílias de uma perna são o gargalo real.** Segurança pública municipal
depende inteiramente do SISDEPEN; preços, do IPCA de 9 municípios; integridade
empresarial, do CEIS. Achados como D3 (letalidade policial) e B13/D7/D8
(sanção) **não têm confirmação cruzada possível dentro do espelho** — é
limitação de fonte, não de análise.

---

## 2 · A fila de hipóteses

Prioridade por: (a) família nunca cruzada, (b) construir sobre achado forte já
existente, (c) usar dataset sem nenhuma pergunta. Cada linha diz **o que
falsearia** a hipótese — sem isso não é hipótese, é expectativa.

> **Estado em 2026-09-06:** H01–H19 rodaram, e as 19 estão respondidas (§3).
> Quatro (H05 pré×pós do sorteio FEF, H08 desfecho pós-2020 para a dose do
> PBF, H14 inadimplência do SCR por UF, H15 variação de vínculos 2019→2020)
> precisaram de recorte temporal que os blocos SQL 00-50 não fazem — fechadas
> no mesmo dia por `scripts/hipoteses/70_temporais.sql` + `98_temporais.py`
> (três falseadas, uma sobrevive fraca), ver a tabela de veredito abaixo.

### Bloco A · MIDES: 392 milhões de pagamentos municipais com CNPJ do credor

Destravado em 2026-09-06. `world_wb_mides.pagamento` tem `id_municipio` **e**
`documento_credor` — é a primeira fonte do espelho que permite seguir dinheiro
público **municipal** até a empresa. Cruza `compras_publicas` ×
`sancao_integridade` × `fiscal_municipal`, uma trinca inédita.

| # | Hipótese | Falsearia se |
|---|---|---|
| **H01** | A concentração de credores por município (HHI de pagamento) é maior onde há menos fornecedores locais, não onde há mais pobreza | HHI acompanhar pobreza e não densidade empresarial |
| **H02** | Municípios que pagam mais a fornecedor **sediado fora** são os pequenos e mal servidos — a compra pública vaza para o polo regional | share de credor local não cair com o porte |
| **H03** | A fatia do pagamento municipal que vai a empresa sancionada (CEIS/CNEP) é maior onde o CAUC tem mais pendência | share sancionado ser ortogonal ao CAUC (como foi ortogonal ao EBT em E3) |
| **H04** | Devedores da PGFN recebem pagamento municipal na mesma proporção que recebem federal (T37-2: 25.643 vencedores, R$ 241,7 bi) | a proporção municipal ser muito menor — indicaria filtro local que o federal não tem |

### Bloco B · CGU FEF: fiscalização por sorteio

`br_cgu_fef.microdados` tem `sorteio_ciclo_fef`, `montante_fiscalizado` e
`tipo_constatacao` por município. **É o desenho mais próximo de experimento no
espelho**: o município é sorteado, não escolhido. Permite comparar auditado ×
não-auditado sem viés de seleção — algo que nenhum achado atual tem.

| # | Hipótese | Falsearia se |
|---|---|---|
| **H05** | Municípios sorteados e auditados mudam de comportamento depois: menos pendência no CAUC, menos pagamento a sancionado nos anos seguintes | não haver diferença entre auditados e não-auditados no pós |
| **H06** | A taxa de constatação grave **não** acompanha pobreza — irregularidade é uniforme, o que varia é a chance de ser pego | share grave subir com pobreza mesmo entre sorteados |
| **H07** | O montante fiscalizado por habitante identifica onde a União concentra risco, e isso não coincide com onde ela concentra repasse | montante fiscalizado acompanhar linearmente o convênio recebido |

### Bloco C · Longo prazo da transferência de renda

`br_mc_indicadores` tem Bolsa Família **2004–2020** por município. Hoje todo
achado de transferência é corte transversal (B11, D22, E2). Cruza
`transferencia_renda` × `demografia_censo` × qualquer desfecho — com **15 anos
de exposição**.

| # | Hipótese | Falsearia se |
|---|---|---|
| **H08** | Municípios com maior exposição acumulada ao PBF (2004–2020) reduziram mais o IVS entre 2000 e 2010 e têm hoje menor mortalidade infantil — o efeito de dose | exposição acumulada não prever Δ IVS depois de controlar o IVS inicial (T31-4 mostrou convergência pura: r = −0,48 com o ponto de partida) |
| **H09** | A razão PBF 2019/2006 separa município que **saiu** da pobreza de município que só cresceu — e o primeiro grupo tem hoje mais formalização | a razão ser explicada só por crescimento populacional |

### Bloco D · Famílias nunca cruzadas

| # | Hipótese | Famílias | Falsearia se |
|---|---|---|---|
| **H10** | Reclamação no Consumidor.gov por 100 mil hab mede **acesso digital**, não lesão ao consumidor: acompanha Pix e conectividade, não pobreza | cultura_consumo × conectividade × credito_financeiro | correlacionar com pobreza acima de conectividade |
| **H11** | A nota do consumidor (satisfação com a resposta da empresa) é pior onde há menos concorrência empresarial local | cultura_consumo × trabalho_empresa | nota ser ortogonal à densidade de CNPJ |
| **H12** | Municípios de pesca artesanal (Seguro-Defeso) têm perfil social distinto do agrícola de mesma renda: mais informalidade, menos crédito rural | transferencia_renda × credito_financeiro × trabalho_empresa | o perfil ser indistinguível do agrícola |
| **H13** | A composição racial por nível de instrução (Censo 2022) prevê a lacuna salarial de gênero (D4) melhor que a renda | demografia_censo × trabalho_empresa | a lacuna seguir só renda, como em D4 |
| **H14** | Onde o Garantia-Safra pagou mais (série 2013+), a inadimplência rural do SCR subiu no ano seguinte — quebra de safra vira crédito podre | transferencia_renda × credito_financeiro × agropecuaria | não haver defasagem detectável (o SCR é por UF, então o teste é estadual) |
| **H15** | O capital social mediano do estabelecimento (RAIS identificada) prevê resiliência: municípios de capital baixo perderam mais vínculos em 2020 | trabalho_empresa × demografia_censo | capital social ser puro proxy de porte |

### Bloco I · Trincas nunca cruzadas em H01-H19 (2026-09-06, via revisão Opus)

> **Nota de numeração (2026-09-06):** esta seção nasceu como "Bloco F,
> H20–H24". Renumerada para **Bloco I, H41–H45** para não colidir com o Bloco F
> de §5.2 (`br_sp_saopaulo_geosampa_iptu` etc.), escrito em paralelo por outra
> sessão no mesmo arquivo e que também começava em H20. Letras A–H e números até
> H40 já estavam ocupados quando a colisão foi notada; ver `git log -p` deste
> arquivo se precisar da numeração original em algum log externo já publicado.

Cinco hipóteses adicionais, cada uma cruzando 3 famílias que nenhuma das
H01-H19 combina — extração pronta em [`50_novas.sql`](../scripts/hipoteses/50_novas.sql),
já rodada em teste de fumaça (ver §3).

| # | Hipótese | Famílias | Falsearia se |
|---|---|---|---|
| **H41** | Queda na exportação municipal (choque 2019→2020) é absorvida pelo PBF, não pelo emprego — e mais onde a pauta é concentrada num único SH4 | comercio_exterior × transferencia_renda × trabalho_empresa | Δ PBF acompanhar só a tendência nacional do programa, com coeficiente do choque de exportação nulo; ou o HHI de SH4 não interagir |
| **H42** | Terceirizar saúde municipal (empenho função 10 em serviços de terceiros-PJ) retém mais paciente e custa mais por AIH, sem reduzir mortalidade evitável — compra capacidade, não desfecho | compras_publicas × saude_producao × mortalidade | a retenção não subir com a terceirização; ou subir **e** a mortalidade evitável cair junto |
| **H43** | Troca de partido na prefeitura reduz a sobreposição de credores MIDES em torno da posse mais que reeleição — e os entrantes são mais de fora e mais sancionados | politica × compras_publicas × sancao_integridade | o Jaccard pós-troca ser indistinguível do pós-reeleição; ou o perfil dos entrantes ser igual ao dos que saem |
| **H44** | Maternidade adolescente (SINASC) segue a estreiteza da oferta ocupacional feminina (HHI de CBO na RAIS), não o IDEB nem a pobreza | educacao × natalidade × trabalho_empresa | o HHI ocupacional perder para o IDEB ou para a cobertura do PBF na regressão conjunta |
| **H45** | Choque de CFEM (2017-2021→2022-2025) não derruba o CAGED — mineração emprega pouco — mas eleva pendência no CAUC: é choque de caixa, não de emprego | mineracao_energia × fiscal_municipal × trabalho_empresa | o saldo do CAGED cair proporcionalmente à CFEM; ou o CAUC não se mover |

Corrida completa (2026-09-06, beelink, `bash hipoteses_overnight.sh` isolado em
`~/hipoteses_run_blocof` + `OUT=~/rodado_hipoteses/20260906_blocof`, para não
disputar arquivo com outra sessão rodando em paralelo no mesmo host). Números
idênticos ao teste de fumaça anterior — confirma que não era artefato de corte
parcial de dados. Resumo (gitignorado, local) em [`.hipoteses/20260906_blocof/`](../.hipoteses/20260906_blocof/).

| # | n | r_bruto | r_parcial | Leitura |
|---|---|---|---|---|
| H41 | 2.056 | −0,084 | −0,062 | fraco: o choque de exportação não move o PBF de forma detectável nesse recorte |
| H41b | 2.214 | −0,146 | −0,034 | HHI da pauta não amplifica o efeito em correlação linear |
| H41c | 2.056 | −0,000 | +0,016 | nulo: o choque de exportação também não move o CAGED — reforça que o canal é outro (ou nenhum) |
| H42 | 1.616 | −0,172 | −0,028 | terceirização não prevê retenção controlando porte — H42 como escrita não se sustenta |
| H42b | 1.616 | +0,251 | **+0,087** | terceirização × custo mediano da AIH era o par mais forte do bloco em bruto — cai a +0,087 no parcial, mesmo padrão de artefato de escala do resto do bloco |
| H42c | 3.071 | +0,198 | +0,039 | fraco: terceirização não acompanha infecciosos após controle |
| H43 | 3.045 | −0,035 | ver abaixo | binário (troca de partido) — Spearman não é o teste certo, ver comparação de grupo |
| H43b | 2.381 | +0,032 | ver abaixo | idem |
| H43c | 2.381 | −0,014 | ver abaixo | idem |
| H44 | 5.570 | +0,420 | **+0,088** | cai como E1/H18 caíram — a maior parte era artefato de escala |
| H44b | 5.241 | −0,489 | **−0,235** | IDEB sobrevive ao parcial melhor que o HHI ocupacional — contra a expectativa de H44 |
| H44c | 5.555 | +0,611 | **+0,303** | cobertura do Bolsa Família (proxy de pobreza) domina os outros dois — é o resultado mais forte do bloco inteiro |
| H45 | 2.865 | +0,041 | +0,042 | nulo — CFEM não move CAGED, consistente com "mineração emprega pouco" |
| H45b | 2.864 | −0,005 | −0,002 | nulo — CFEM também não move CAUC; H45 como está não separa "choque de caixa" de "sem efeito nenhum" |

**H41b — corte por quintil de HHI e termo de interação** (`scripts/hipoteses/96_blocof_fechamento.py`,
n=2.056–2.214): a correlação choque×PBF dentro de cada quintil de HHI da pauta
fica em −0,13 / −0,03 / −0,16 / −0,04 do quintil 1 ao 4 (o 5º funde com o 4º por
`qcut` com empates) — **sem crescer** com a concentração, ao contrário do que a
hipótese previa. O termo de interação `comex_choque_pct × comex_hhi_sh4_2019`
residualizado (controla os dois efeitos principais + log-pop, log-PIB, UF) dá
**+0,006** — indistinguível de zero. A interação proposta por H41 não existe
neste recorte, nem em forma linear nem em forma de corte. **H41 fecha como nulo
duplo** (efeito principal nulo + interação nula).

**H43 — comparação de grupo (troca de partido × reeleição/sucessão mesmo
partido)**, via diferença de mediana + teste de permutação em numpy puro
(5.000 permutações, `96_blocof_fechamento.py`; sem scipy, convenção do runner
offline):

| Variável | Troca (mediana) | Não-troca (mediana) | diff | p (permutação) |
|---|---|---|---|---|
| `mides_jaccard_credor` (n=3.045) | 0,2292 | 0,2457 | **−0,0165** | **0,0004** |
| `entrantes_share_nao_local` (n=2.381) | 0,5517 | 0,5436 | +0,0081 | 0,3325 |
| `entrantes_share_sancionado` (n=2.381) | 0,0171 | 0,0179 | −0,0008 | 0,2430 |

A sobreposição de credores (Jaccard) é significativamente **menor** depois de
troca de partido do que depois de reeleição/sucessão pelo mesmo partido — efeito
pequeno em magnitude (~7% relativo) mas robusto ao teste de permutação. As duas
pernas de perfil do entrante (não-local, sancionado) **não** se sustentam — nem
o sinal de "entrante sancionado" bate com a direção prevista. **Nota de leitura**:
`prefeito_partido_2016 != prefeito_partido_2020` mede troca de **partido**, não
de **pessoa** — sucessão pelo mesmo partido conta como "não-troca" aqui.
Distinguir reeleição de sucessão exigiria `sequencial_candidato`
(`br_tse_eleicoes.resultados_candidato_municipio`), não extraído nesta rodada
por não precisar de SQL nova para fechar o bloco; decisão registrada, não
pendência — se a leitura "partido" bastar, H43 está fechada.

**Resolução por hipótese**: **as cinco fecham nesta rodada — 5 ✅ de 5** (nenhuma
◐ ou ⏳ restante no Bloco I). **H41 nulo duplo** (efeito principal + interação,
ambos nulos). **H42 nulo duplo** (retenção nula; custo da AIH, que era a perna
promissora em bruto, cai a +0,087 no parcial). **H43 confirma parcialmente**: a
perna do Jaccard sobrevive (pequena, mas significativa), as duas pernas de
perfil do entrante não. **H44 e H45 ✅** (já resolvidas na rodada anterior — a
segunda como nulo duplo confirmado robusto a outlier, ver checagem de magnitude
em `achados_fortes.md`).

**H44c é o achado que salta**: pobreza prevê maternidade adolescente muito melhor
que educação ou estrutura ocupacional — o oposto da hipótese original (que
apostava no mercado de trabalho feminino como mecanismo dominante). Passou a
checagem de magnitude (mediana 13,7%, agregado 12,3%, mesma vizinhança da taxa
nacional do SINASC/MS ~15–18%) e está registrado em `achados_fortes.md`.

### Bloco E · Reteste de achados que merecem confirmação

| # | O quê | Por quê |
|---|---|---|
| **H16** | D1 (CAFIR × desmatamento, r = +0,82) controlando área do município | a correlação pode ser "município grande tem mais de tudo" — o parcial ainda não foi rodado |
| **H17** | C1 (crédito rural × desmatamento) com o crédito restrito a 2019+ | o `id_car` só existe de 2019; a série anterior usada em C1 mistura cobertura |
| **H18** | E1 (concentração onomástica) com nascimentos como offset explícito | o parcial caiu de +0,48 para +0,11; confirmar se sobra algo |
| **H19** | D13 (sancionados em diário) contra H03 (sancionados **pagos**) | citação ≠ pagamento; a diferença entre os dois é a medida de quanto o diário é ruído |

---

## 3 · Como rodar (offline, overnight)

```bash
# na máquina que tem o .duckdb (beelink), sem rede:
bash scripts/hipoteses_overnight.sh

# variáveis opcionais
DB=~/rodado/basedosdados.duckdb \
OUT=~/rodado_hipoteses/$(date +%Y%m%d) \
ONLY=40 \                      # roda só os blocos cujo nome casa com o padrão
bash scripts/hipoteses_overnight.sh
```

- **Retomável**: cada bloco deixa um sentinela `.done_<bloco>`; rodar de novo
  pula o que terminou. Se a máquina cair às 3h, é só rodar de novo.
- **Não aborta no erro**: um bloco que falha é registrado no log e o script
  segue — uma tabela quebrada não perde a noite inteira.
- **`-readonly` sempre**: o `.duckdb` é lido por outras sessões, e uma conexão
  de escrita trava todas (ver `feedback_duckdb_readonly_no_kill`).
- **Sem rede**: só DuckDB, `python3`, `numpy` e `pandas` (todos já no beelink;
  não usa scipy nem polars).

### Blocos

| Bloco | O que extrai | Custo medido |
|---|---|---|
| `00_bridges.sql` | SIAFI→IBGE e código SUS 6→7 dígitos | 2 s |
| `10_base.sql` | população, PIB, RAIS, SIM, Anatel, PRODES, CNEFE | 3 s |
| `20_conhecidos.sql` | Pix, CFEM, GD, DETER, IBAMA, SICAR, CAFIR, SICOR, NBF, PNCP, IEPS, AVS | 3 s |
| `30_novos.sql` | MIDES, FEF, PBF série, Censo raça, Consumidor.gov, Defeso, Pé-de-Meia, Garantia-Safra, EBT, nomes, RAIS identificada | 8 s |
| `40_cadeias.sql` | pagamento×sanção, pagamento×PGFN, credor local, sancionado empregando | 45 s |
| `50_novas.sql` | Comex×PBF×CAGED, MIDES saúde×SIH, TSE prefeito×credor (Jaccard), SINASC×RAIS CBO×IDEB, CFEM×CAUC (H41–H45) | 24 s |
| `90_analise.py` | painel + Spearman bruto e parcial dos pares intensivos + quintis + H01–H19, H41–H45 | 12 s |

Dois passos **fora** do runner, rodados no repo depois de trazer o resultado —
eles existem porque a varredura de `90_analise.py` deixa buracos por desenho:

| Script | Por que não está no runner |
|---|---|
| `91_parciais.py` | A varredura só cobre par **intensivo**, então todo par com uma ponta extensiva (H01, H02, H04, H05, H08, H16, H17) sai de `hipoteses.tsv` com `r_parcial` em branco. Aqui o parcial é calculado para todos os pares nomeados, com **`log(area_total)` no controle** — o número que vale para par extensivo |
| `92_lacunas.py` | Pivota `v_censo_raca` (perna racial de H13) e `v_garantia_safra` (H14), que saem em formato longo e não entram no merge; roda H08 contra o **falseador que a própria hipótese escreveu** (o IVS inicial); e troca a correlação de H04 pela **fatia**, que é o que a hipótese pede |
| `96_blocof_fechamento.py` | Fecha o Bloco I: interação por quintil de HHI + termo de interação residualizado (H41b, a correlação linear simples testa a coisa errada); comparação de grupo troca-de-partido × jaccard/entrantes via permutação em numpy puro (H43, variável binária cai fora do scan por `nunique<5`); checagem de magnitude (H44c, H45) antes de promover a `achados_fortes.md` |
| `97_h38_h40.py` | Roda sobre `tasks/hipoteses_resultado/20260906/painel.csv` (OUT dir de outra sessão): testa os três falseadores de §5.2 Bloco H — `log(nascimentos)` explícito no controle (H38), crescimento do PIB além do nível (H39), corte por metade de cobertura do MIDES (H40) |
| `70_temporais.sql` + `98_temporais.py` | Extração e análise de H05/H08/H14/H15 — as quatro que exigiam recorte temporal (pré×pós, defasagem, Δ ano-a-ano), não acumulado por município. OUT dir próprio (`~/rodado_hipoteses/temporais/` no beelink, `.hipoteses/temporais/` local) |
| `71_rouanet.sql` + `99_rouanet.py` | H30/H31 — Lei Rouanet (`br_minc_salic`, sem view no `.duckdb`, lido via `read_parquet` direto do disco): funil regional (H30) e integridade de proponente/patrocinador contra taxa-base de CNPJ ativo (H31). OUT dir próprio (`~/rodado_hipoteses/rouanet/` no beelink, `.hipoteses/rouanet/` local) |
| `100_pares_existentes.py` | Tema 81 de `docs/perguntas.md` — pares de variáveis **já extraídas** no painel principal que nunca tinham sido cruzadas entre si (vacinação×IVS, telecom×pobreza, ESF×IDEB, PNCP×EBT, CAUC×capital social). Sem SQL nova. Achado de método: `hhi_smp` provavelmente não é HHI de concentração — correlaciona positivo com população/renda/densidade, o oposto do esperado de um índice de concentração |
| `72_novidades.sql` + `101_novidades.py` | Tema 82 — corrige o Bloco R: `mobilidade` e a tabela geral de `br_rf_arrecadacao` estavam travadas, mas `itr` (fiscal_municipal) e `proporcao_mortes_negras_acidente_transporte` (mobilidade) não. ITR×tamanho de propriedade rural vira **L1** (r_parcial +0,53). OUT dir próprio (`~/rodado_hipoteses/inedito2/`) |

### O que sai

| Arquivo | Conteúdo |
|---|---|
| `painel.csv` | 1 linha por município, ~130 colunas (brutas + derivadas) |
| `painel_uf.csv` | agregado estadual |
| `correlacoes.tsv` | **1.941 pares intensivos** com n, `r_bruto`, `r_parcial`, ranqueado por \|r_parcial\| |
| `hipoteses.tsv` | só os pares nomeados H01–H19 e H41–H45, para leitura direta |
| `hipoteses_parciais.tsv` | idem, com o parcial que inclui **log-área** — o único válido para par extensivo (`91_parciais.py`) |
| `tautologias.tsv` | pares descartados (derivada × fonte, ou o mesmo objeto duas vezes) |
| `quintis.txt` | tabela de quintil dos 60 pares mais fortes |
| `run.log` | tempo por bloco e erro de cada falha |

`r_parcial` residualiza **log-população, log-PIB per capita e efeito fixo de
UF** — e, quando as duas pontas são extensivas, **também log-área do município**
(ver `91_parciais.py`). É o que separa achado real de "município grande tem mais
de tudo". Todo
número que for para `achados_fortes.md` precisa do parcial, não só do bruto
(ver E1, onde o bruto de +0,48 virou +0,11, e H18 abaixo, onde virou +0,03).

**Duas decisões de método embutidas na varredura, aprendidas no teste:**

1. **Só variáveis intensivas entram.** A varredura roda sobre 64 taxas, razões e
   índices — nunca sobre contagem bruta. Contagem é extensiva: escala com
   população, e o resíduo em rank de log-pop **não** absorve isso. Na primeira
   versão o topo do ranking era `óbitos × nascimentos` (+0,83) e
   `população × nomes distintos` (+0,87) — ruído de tamanho com cara de achado.
   As 100 colunas extensivas ficam em `painel.csv` para uso dirigido.
2. **Tautologias vão para arquivo separado.** Derivada × sua fonte
   (`homicidios` × `homic_100k`), e grupos que medem o mesmo objeto sob outro
   nome (`mides_valor` × `pag_total_valor`), saem para `tautologias.tsv` em vez
   de poluir o ranking.
3. **Área entra no controle quando as duas pontas são extensivas.** Não estava
   na primeira versão, e sem ela o D1 passou por achado confirmado. Ver §3.

**O que a varredura ainda não pega, e é para saber ao ler `correlacoes.tsv`:**
razões que **compartilham numerador ou denominador** não são marcadas como
tautológicas e sobem no ranking por construção — `credito_pc` × `credito_ha`
(+0,65) dividem `credito_rural`; `cob_ab` × `cob_esf` (+0,78) são cobertura
básica e cobertura de ESF, uma contida na outra. Conferir os componentes antes
de tratar um par do topo como achado.

### Depois

```bash
scp -r beelink:~/rodado_hipoteses/<data> ./tasks/hipoteses_resultado/
```

E então: analisar `correlacoes.tsv`, escrever as respostas em
`docs/respostas.md` e promover o que sobreviver ao parcial para
`docs/achados_fortes.md`.

### Resultado da corrida completa (2026-09-06, beelink)

A bateria inteira roda em **88 segundos**, não numa noite — o espelho é local e o
DuckDB só lê as colunas usadas. Rodar overnight continua sendo a forma segura
(nada compete pelo lock, e há folga se um bloco novo for pesado), mas o custo
real é baixo. Painel: **5.571 municípios × 164 colunas**, 1.941 pares intensivos.

**As respostas completas estão em [`docs/hipoteses/respostas.md`](../docs/hipoteses/respostas.md),
seção "Bateria de hipóteses H01–H19"; o que sobreviveu ao parcial está em
[`docs/hipoteses/achados_fortes.md`](../docs/hipoteses/achados_fortes.md) como F1–F7.**

Placar: **5 confirmadas · 9 falseadas · 5 fracas · 0 não testáveis** — H05, H08,
H14 e H15 fecharam em 2026-09-06 com o recorte temporal que faltava
(`scripts/hipoteses/70_temporais.sql` + `98_temporais.py`), ver as quatro
linhas abaixo e `docs/respostas.md` bateria H01–H19.

| # | Veredito | Resumo |
|---|---|---|
| **H01** | ❌ falseada | HHI de pagamento acompanha pobreza (+0,14) tanto quanto densidade empresarial (−0,13); nenhuma domina |
| **H02** | ◐ fraca | Credor local sobe com o porte (35,2% → 50,5% por quintil), mas parcial +0,11 |
| **H03** | ❌ nula | R$ 18,4 bi pagos a sancionado; × EBT +0,05. Confirma E3 |
| **H04** | ✅ respondida | 12,2% dos credores devem à PGFN e levam **22,7% do valor** (R$ 467,6 bi) |
| **H05** | ❌ falseada (2026-09-06, pré×pós real) | Δ médio sorteado −0,05 p.p. × não-sorteado −0,11 p.p., diff-in-diff **+0,06 p.p., p=0,51**, IC95% ±0,17 p.p. (n=351/1.254) — descarta efeito de fiscalização >~24% da fatia média (0,71%); sinal contrário. CAUC ficou de fora: tabela sem coluna de ano |
| **H06** | ✅ confirmada | Constatação grave × pobreza: +0,37 → **+0,08**. Irregularidade é uniforme |
| **H07** | ◐ fraca | Montante fiscalizado pc × pobreza: +0,56 → +0,14 |
| **H08** | ❌ falseada (2026-09-06, desfecho pós-2020 real) | Mortalidade infantil 2021-24 (n=4.746, mediana 10,1‰) × `pbf_valor_acumulado`: bruto +0,22 → parcial +0,11 → **+IVS 2000 +0,07**. Cinco especificações testadas (pobreza histórica/contemporânea, per capita, extensivo×intensivo à la D1) — nenhuma zera: per capita +0,06, +BF atual +0,08, **per capita + BF atual juntos +0,057** (a decisiva). Residual robusto, não é artefato de escala nem de confound de pobreza — mas também não é causal sem instrumento |
| **H09** | ◐ fraca | Formalização −0,11 × crescimento populacional +0,14 — mesma ordem, não separa |
| **H10** | ✅ confirmada | Reclamação × Pix **+0,29**, × conectividade +0,28, × pobreza −0,16. Mede acesso digital |
| **H11** | ❌ falseada | Nota do consumidor × densidade empresarial +0,05 |
| **H12** | ◐ parcial | Menos agro (−0,17) e menos crédito (−0,08); a perna de informalidade dissolve (−0,03) |
| **H13** | ❌ falseada | Composição racial prevê **pior** (+0,06) que renda (+0,11) — e as duas colapsam |
| **H14** | ❌ falseada (2026-09-06, SCR real) | GS(t) × Δinadimplência(t→t+1), n=122 UF-anos: bruto **−0,05**, +efeito fixo de UF **−0,05** — nulo/contrário, não a alta esperada |
| **H15** | ◐ fraca, sobrevive (2026-09-06, Δ2019→2020 real) | Δvínculos × capital social: bruto +0,08 → parcial +0,06 → **+log(vínculos 2019) +0,06**. Sobrevive ao controle de porte quase sem mudar, sinal certo, mas fraco |
| **H16** | ❌ **derruba o D1** | +0,82 → +0,31 com área → **+0,04 em intensidade**; e **zero fora da Amazônia** |
| **H17** | ✅ **confirma o C1** | Crédito por hectare × share desmatada **+0,45 parcial**, quintis 0,37→0,83, igual dentro e fora da Amazônia |
| **H18** | ❌ **mata o E1** | Concentração onomástica × pobreza: +0,48 → **+0,03** |
| **H19** | ✅ confirmada | Sancionado pago × sancionado sediado: **−0,004**. Citação ≠ pagamento |

**O achado de método da rodada** — e a razão de H16 e H17 discordarem apesar de
serem a mesma pergunta com fonte diferente: **par extensivo × extensivo precisa
de `log(area_total)` no controle**, não só `log(populacao)`. Área CAFIR e área
desmatada são dois tamanhos; os municípios de maior área da Amazônia são os de
**menor** população, então controlar população não controla área. A primeira
leitura desta mesma corrida reportou H16b como "+0,76, sobrevive ao controle" —
era o controle errado. O crédito rural (H17) sobrevive porque é **fluxo**; o
cadastro fundiário (H16) não, porque é **estoque de área** correlacionado com
outro estoque de área.

Segunda lição, menor: `v_censo_raca` e `v_garantia_safra` saem em **formato
longo** e por isso não entraram no merge de `90_analise.py` — a perna racial de
H13 e todo o H14 ficaram silenciosamente de fora da primeira passada. Um CSV
extraído não é um CSV analisado; conferir a lista de colunas do painel contra a
lista de blocos.

---

## 4 · Gotchas já embutidos nos blocos

Estes já estão tratados no SQL — não redescobrir:

- Portal da Transparência usa `codigo_municipio_siafi`, não `id_municipio`
  (ponte em `00_bridges.sql`, recupera 5.556 de 5.571).
- SIH e SINAN usam código do SUS de **6 dígitos**.
- `br_bcb_sicor`: o município está embutido no `id_car`
  (`UF(2)+IBGE(7)+hash(32)`), e **só existe de 2019 em diante**.
- `world_wb_mides.pagamento`: a coluna de valor é `valor_final`, não
  `valor_pago`.
- `br_ibama_embargos_novo.qtd_area_embargada` é 100% nula — só contar termos.
- `br_pncp.contratos.valorGlobal` tem outliers de trilhões — usar mediana.
- `br_mjsp_sisdepen`: a UF vem como `"Minas Gerais (MG)"`.
- `br_bcb_scrdata`: números em VARCHAR com vírgula decimal.
- SIM 2022 está incompleto para RJ, DF, AP e RR — séries que terminem em 2022
  precisam conferir a razão 2022/2021 por UF.

A lista completa está em `docs/achados_fortes.md`, seção "Avisos de dado".
---

## 5 · O que ainda não foi perguntado

§1 conta **quantas** hipóteses existem (2.002 trincas de família). Esta seção
responde a outra pergunta: **quais** ainda não foram feitas. O método é
subtração explícita, não intuição, e roda em
[`scripts/hipoteses/93_inedito.py`](../scripts/hipoteses/93_inedito.py) sobre
três arquivos novos:

| Arquivo | O que é |
|---|---|
| [`docs/context/familias.yaml`](../docs/context/familias.yaml) | dataset → família + papel (`desfecho`/`controle`/`referencia`), 228 datasets em 29 famílias. Antes só existia como prosa nesta página, e sem ele não dá para subtrair nada |
| [`docs/context/moldes.yaml`](../docs/context/moldes.yaml) | os **8 moldes** de achado que se repetem em `achados_fortes.md`, com o teste, o falseador e os datasets em que o molde ainda não foi aplicado |
| [`docs/context/cobertura_municipal.json`](../docs/context/cobertura_municipal.json) | quantos municípios cada dataset realmente cobre — o filtro F3/F4 tinha sido medido uma vez e nunca gravado |

A subtração precisa de um léxico: `achados_fortes.md` cita fonte em prosa
("CNEFE", "PRODES", "Pix"), não como token `br_*`. Sem os `apelidos` de
`familias.yaml` o gerador enxerga **zero** achado como cobertura e "descobre" o
que já foi medido — foi o primeiro resultado errado desta passada.

### 5.1 · O achado estrutural: a espinha municipal é o limite

**30 datasets nunca aparecem em `perguntas.md`, `respostas.md`, `hipoteses.md`
nem `achados_fortes.md`.** Nenhum deles tem `id_municipio`. Não é descuido: é
que toda a análise do projeto roda na espinha municipal, e o que não está nela
é invisível por construção.

Eles se separam em dois grupos, e só um é aproveitável:

| | Datasets | Chave de entrada |
|---|---|---|
| **Ilhas** — sem nenhuma chave de join | 26 | nenhuma. `br_ana_bho`, `br_ana_reservatorios`, `br_inea_boletim`, `br_cgu_receitas_publicas`, `br_cgu_orcamento_publico`, `br_ibge_ipp`, `br_me_sic`, `br_stj_dadosabertos`, `br_tce_to`, os 6 de esporte/cinema… Não são hipóteses por fazer; são fontes **sem ponte**. Construir a ponte é tarefa de extração |
| **Fora da espinha, mas juntáveis** | 4 | `br_sp_saopaulo_geosampa_iptu` (CEP, bairro, lote) · `br_mg_belohorizonte_smfa_iptu` (CEP, lote) · `br_ce_fortaleza_sefin_iptu` (face de quadra, centroide) · `br_comprasgov_catmatcatser` (item CATMAT) |

Os três IPTUs são **a única fonte intramunicipal em escala do espelho** —
`br_ipea_acesso_oportunidades` é a outra, e cobre 18 municípios. São Paulo tem
**93,4 milhões de linhas lote×ano em 48.177 CEPs**; Belo Horizonte, 21,5 milhões
em 12.485; Fortaleza, 68.932 faces de quadra com água, esgoto, pavimentação,
iluminação, arborização **e centróide**. `br_bd_diretorios_brasil.cep` (905.210
CEPs) é a ponte pronta, e o CNEFE não tem nulo em CEP nos seus 111 milhões de
endereços.

### 5.2 · A fila H20–H40 — **rodada em 2026-09-06**

Prioridade: (a) molde que funciona aplicado a fonte que nunca o recebeu,
(b) fonte fora da espinha que ninguém abriu, (c) o que a varredura empírica já
sinalizou. Cada linha traz o **falseador**, como as anteriores.

> **Estado:** H20–H29, H32 e H36 rodaram (12 no total) — **6 ✅ · 4 ❌ · 1 ◐ · 1 ⏳**.
> Respostas em [`docs/hipoteses/respostas.md`](../docs/hipoteses/respostas.md) ("Bateria de inéditos
> H20–H36"); o que sobreviveu está em
> [`docs/hipoteses/achados_fortes.md`](../docs/hipoteses/achados_fortes.md) como **G1–G7**.
> Extração: `scripts/hipoteses/50_inedito.sql` · análise:
> `scripts/hipoteses/95_inedito.py`.
>
> | # | Veredito | Resumo |
> |---|---|---|
> | **H20** | ❌ | **90,5% da variância de R$/m² em SP é ENTRE bairros**, 9,5% dentro. A desigualdade é de bairro, não de quadra |
> | **H21** | ❌ no grão fino | Face com esgoto vale **2,01×** a sem (r +0,42 global) — mas **+0,03 dentro do mesmo logradouro**. É precificada por rua |
> | **H22** | ✅ | Coleta diária: **P1 1,5% → P5 81,4%**, positiva em 9/9 zonas → **G5** |
> | **H23** | ✅ | Preço de medicamento: razão p90/p10 **2,40×** → **G1** |
> | **H24** | ✅ **forte** | SNIS declarado/IBGE mediana **0,616**; × 4G/5G **r_parcial +0,634** → **G3** |
> | **H25** | ✅ | MUNIC declarado × SICONFI executado **+0,515**; custo por vínculo varia 2,2× |
> | **H26** | ◐ nula | Zero municípios com leito declarado e nenhuma internação. Não há leito fantasma por esta via |
> | **H27** | ✅ | CNO ÷ CNEFE mediana **0,46**; × pobreza **−0,346** → **G4** |
> | **H28** | ❌ | CAPAG: A+ 40,4% × D 5,3% contratam crédito, mas parcial **−0,004** → **G7** |
> | **H29** | ⏳ | Lista do TCU tem **84 CNPJ** contra 7.893 do CEIS — pequena demais |
> | **H30** | ❌ **invertida** | Sudeste **capta MENOS** do que aprova (mediana 0,47) que Norte (mediana 1,00), p=0,0002 — oposto do previsto, não "sem diferença" → **K1** |
> | **H31** | ✅ **confirmada** | Proponente/patrocinador Rouanet: sancionado 17-24× a taxa-base, devedor PGFN 1,7-3,2× — sem controle de porte → **K2** |
> | **H32** | ❌ | SISU em só **551 municípios**; × pobreza −0,07, × IES +0,11 |
> | **H33, H34** | 🔒 travadas | Farmácia Popular sem volume dispensado; CMED×BPS sem chave comum (substância em texto livre, fuzzy match ou nada) |
> | **H35** | 🔒 travada | `br_caixa_sinapi.insumos` só tem UF, sem município — a pergunta pede porte municipal, não roda com esse grão |
> | **H36** | ✅ | Acre: **28.600 condenações, 3.446/100 mil × 33 em RO (104×)** |
> | **H37** | ✅ | Tamanho da propriedade → **G2** |
> | **H38–H40** | ❌ ✅ ◐ | Fechados pela sessão paralela (`97_h38_h40.py`): H38 é definicional (piora a −0,51 com `log(nascimentos)`), H39 sobrevive (+0,31) → achado **I3**, H40 metade artefato de recorte. Ver §5.2 Bloco H |

**H30/H31 fechadas em 2026-09-06** (`scripts/hipoteses/71_rouanet.sql` +
`99_rouanet.py`, sem dono até então — ver §2 "em aberto, sem dono"). H33 e H34
ficam travadas por fonte (Farmácia Popular sem volume dispensado; CMED×BPS
sem chave comum — substância em texto livre, fuzzy match ou nada, diagnóstico
da sessão paralela) e H35 trava por grão (`br_caixa_sinapi.insumos` só tem UF,
a pergunta pede município) — as três vão para o Bloco R (§5.5), junto com
mobilidade/comércio exterior/segurança/justiça.

**H30 — funil regional, resultado invertido do previsto.** A taxa de
*aprovação* (aprovado/solicitado) segue a intuição — Sul 0,99, Sudeste 0,97 >
Nordeste 0,94, Norte 0,93, Centro-Oeste 0,92 — mas a taxa de *captação*
condicional (apoiado/aprovado, dado que já foi aprovado) inverte: Norte
mediana **1,00**, Nordeste 0,93 > Sul 0,58, Centro-Oeste 0,50, **Sudeste
0,47** (mediana; teste em rank, robusto aos outliers extremos que a razão
bruta produz — projeto com `aprovado` de poucos reais e `apoiado` de milhões
dá razão de milhares, visto no describe() sem cap). Sudeste × Norte:
diff=−0,53, **p=0,0002** (permutação). A leitura não é "sem diferença" — é
**inversão de sinal**: Sudeste aprova **196.539** projetos (81.447 com
aprovado>0) contra **3.073** do Norte, e a maior parte do volume aprovado no
Sudeste **nunca capta nada** (25% dos casos com captação=0, contra piso de
24% no Norte também, mas a mediana Norte já está em 1,00 — a cauda de fracasso
é proporcionalmente maior no Sudeste). Leitura plausível: aprovação no
Sudeste é pouco seletiva (fila grande, projeto marginal entra), captação no
Norte reflete poucos projetos já com patrocínio quase garantido antes de
entrar no funil — mas isso é hipótese nova, não testada aqui. **H30 como
escrita (Sudeste converte melhor) está falseada — e na direção oposta à
prevista.** → achado **K1**.

**H31 — confirmada, sem controle de porte.** Taxa-base corrigida (a sessão
paralela flagrou que 7.893/6,68 mi do D7/H29 usava o denominador errado — 6,68
mi já É o universo de devedores da PGFN, não o total de empresas do país;
confirmado aqui: 6.673.698 de 67.640.763 CNPJ ativos em
`br_me_cnpj.estabelecimentos` são devedores PGFN, bate com o 6,68 mi do D7).
Taxa-base certa: sancionado (CEIS/CNEP) **0,0117%**, devedor PGFN **9,87%**
dos CNPJ ativos do país. Contra isso, CNPJ **proponente** da Rouanet (27.274
únicos): sancionado **0,19%** (**16,7×** a taxa-base, 53 observados × 3,2
esperados), devedor PGFN **16,6%** (**1,68×**). CNPJ **patrocinador**
(22.399 únicos, quem tem o benefício fiscal — papel diferente do proponente,
reportado separado a pedido da sessão paralela): sancionado **0,28%**
(**23,7×**), devedor PGFN **31,3%** (**3,18×**) — patrocinador é
sistematicamente mais devedor que proponente. **Sem controle de porte/setor**
(a opção cara que ficou de fora): parte do excesso pode ser que empresa que
patrocina cultura/tem CNPJ ativo grande o bastante para aparecer nesses dois
cadastros não é a empresa média do universo de 67,6 milhões, que inclui muito
CNPJ inativo/microempresa. Mesmo assim, a interseção é **muito maior**, não
menor, que o esperado pelo acaso — falseador não se confirma, H31 sustenta.
Mesmo padrão de "a regra não morde" que já apareceu 6× no espelho (T68-3, D7,
D9, F1, F5, G7) → achado **K2**.

#### Bloco F · Fora da espinha municipal

| # | Hipótese | Molde | Falsearia se |
|---|---|---|---|
| **H20** | O valor de terreno por m² do IPTU paulistano, agregado por CEP, prevê a composição do endereço no CNEFE (domicílio × comércio × religioso) melhor do que o bairro prevê — a desigualdade é de quadra, não de distrito | — | a variância entre CEPs do mesmo bairro ser pequena diante da variância entre bairros |
| **H21** | Em Fortaleza, a face de quadra sem esgoto/pavimentação/arborização não é aleatória dentro do bairro: acompanha o valor da própria face. A infraestrutura urbana é precificada no metro, não no distrito | declarado_vs_observado | os indicadores de infraestrutura serem constantes dentro do bairro |
| **H22** | Em Belo Horizonte, a **frequência de coleta de lixo** acompanha o padrão de acabamento do imóvel, controlando zoneamento — o serviço mais básico é distribuído por renda dentro da mesma cidade | programa_vs_necessidade | a frequência ser explicada só por zoneamento/densidade |
| **H23** | O mesmo medicamento custa preços muito diferentes a compradores públicos diferentes no mesmo ano — e quem paga mais não é o comprador pequeno | margem_por_elo | a dispersão sumir ao controlar ano, unidade de fornecimento e porte do comprador |

#### Bloco G · Moldes que funcionam, fontes que nunca os receberam

| # | Hipótese | Molde | Falsearia se |
|---|---|---|---|
| **H24** | O SNIS é **auto-declarado pelo prestador**: o atendimento de água que ele reporta acompanha a capacidade administrativa do município (conectividade, porte da prefeitura) antes de acompanhar a rede de fato. Cruzar com a outorga da ANA, que é medida por terceiro | registro_vs_fenomeno + declarado_vs_observado | a razão declarado/outorgado ser constante entre municípios |
| **H25** | A `br_ibge_munic` é o município **descrevendo a si mesmo** (tem plano diretor? conselho? lei X?). Testar contra o que ele **executa** no SICONFI: quem declara mais estrutura gasta mais na função correspondente? | declarado_vs_observado | declaração e execução andarem juntas |
| **H26** | O CNES é o estabelecimento **declarando** leito e profissional; o SIA/SIH é a produção **faturada**. Municípios com muito leito declarado e pouca produção são o mapa do leito que não existe | declarado_vs_observado | a razão produção/leito ser uniforme |
| **H27** | A obra registrada no CNO (`br_rf_cno`, com `id_municipio`, `tipo_obra` e metragem) cobre uma fração do domicílio em construção do CNEFE — e a fração cai com a pobreza, confirmando o T70-3 pelo lado da formalidade | declarado_vs_observado | a razão CNO/CNEFE não variar com renda |
| **H28** | A nota CAPAG do Tesouro deveria limitar endividamento. Testar se município com nota pior contrata **menos** operação de crédito de fato | regra_nao_morde | o endividamento cair com a nota, como a regra prevê |
| **H29** | Empresa declarada inidônea pelo TCU (`br_tcu_inidoneos`) continua recebendo pagamento municipal no MIDES e vencendo no PNCP, como já se mostrou para CEIS (F5) e PGFN (F1) | regra_nao_morde + mesmo_cnpj_dois_cadastros | a inidoneidade do TCU morder onde o CEIS não morde |
| **H30** | A Lei Rouanet (`br_minc_salic`: projetos, entidades com CNPJ, incentivos, recibos) tem um **funil** — solicitado → aprovado → captado. A perda no funil não é uniforme no território: o proponente do Sudeste converte aprovação em dinheiro numa taxa que o do Norte não alcança | programa_vs_necessidade | a taxa de conversão aprovado→captado ser igual entre regiões |
| **H31** | Os proponentes da Rouanet cruzados com CEIS/CNEP e PGFN: o incentivo fiscal cultural tem o mesmo filtro de integridade que a compra pública tem (ou seja, nenhum) | mesmo_cnpj_dois_cadastros | a interseção ser menor que a esperada pelo acaso |
| **H32** | ProUni e SISU distribuem vaga onde há aluno pobre ou onde há faculdade privada? Testar contra a cobertura do Bolsa Família e contra a densidade de IES do Censo da Educação Superior | programa_vs_necessidade | a distribuição acompanhar pobreza acima da oferta instalada |
| **H33** | A Farmácia Popular cobre o município onde há doença crônica ou onde há farmácia credenciada? É o B18 (BNDES precisa de banco credenciado) aplicado à saúde | programa_vs_necessidade | a cobertura não depender da rede credenciada |
| **H34** | O preço-teto da CMED (`br_anvisa_cmed`) é respeitado na compra pública de medicamento? Comparar com o preço unitário do BPS item a item | margem_por_elo | o preço pago ficar sistematicamente abaixo do teto, como a regra pretende |
| **H35** | O custo unitário do SINAPI é a referência de obra pública. Comparar com o valor por item das licitações de obra — a margem sobre a referência varia com o porte do município? | margem_por_elo | a razão pago/referência ser constante |
| **H36** | `br_cnj_improbidade_administrativa` tem o Acre com 28.600 condenações (5,5× São Paulo). Testar formalmente que a série mede **alimentação do cadastro**, não improbidade — é o quarto caso do mesmo molde, depois de C3, D19 e F2 | registro_vs_fenomeno | a série acompanhar sanção da CGU ou pendência do CAUC em vez de acompanhar capacidade de registro |

#### Bloco H · O que a varredura empírica sinalizou

Saíram de `correlacoes.tsv` — pares medidos, fortes no parcial, que nenhum
achado explica.

| # | Hipótese | Sinal medido | Falsearia se |
|---|---|---|---|
| **H37** | O **tamanho médio da propriedade rural** (CAFIR, ha/imóvel) é a variável fundiária que sobrevive onde a área total morreu (D1): prevê produtividade e crédito por hectare | ver 5.3 — já medido | o efeito sumir sob controle de log-área |
| **H38** | ❌ **não é confound, é definicional** — `div_nomes × share_nome_top`: bruto −0,07, parcial −0,40 → **−0,51** ao acrescentar `log(nascimentos)` explícito no controle (piorou, não sumiu) | −0,510 (n 5.565) | ver nota abaixo |
| **H39** | ✅ **sobrevive** — `obras_1000dom × cresc_pop`: parcial +0,33 → **+0,31** com crescimento do PIB (`pib/pib_2010-1`) também no controle, quase sem mudar | +0,308 (n 5.565) | ver nota abaixo |
| **H40** | ◐ **metade** — `div_nomes × mides_valor_pc` (a da inversão de sinal) some na metade de cobertura MIDES alta (−0,02) e fica em −0,25 na baixa: artefato de recorte confirmado. Mas `mides_valor_pc × share_nome_top` fica positiva **nas duas** metades | −0,02 alta / −0,25 baixa · +0,20 e +0,28 | ver nota abaixo — a segunda perna não é recorte e segue sem explicação mecânica; em aberto |

**H38-H40 fechados em 2026-09-06** (`scripts/hipoteses/97_h38_h40.py`, sobre
`tasks/hipoteses_resultado/20260906/painel.csv` — OUT dir da sessão que sinalizou
os três pares originalmente; combinado entre as duas sessões que eu (a outra
sessão que fechou o Bloco I, H41-H45) pegasse esses três, ver nota de sessão
paralela em §5.5):

**H38 — não é confounding, é definicional.** O falseador escrito era "sumir ao
controlar por `nascimentos`" — o oposto aconteceu: acrescentar `log(nascimentos)`
explícito no controle (além do log-população padrão) **piora** o parcial de
−0,40 para −0,51. Isso descarta a hipótese de confound removível por covariável,
mas não torna a relação um achado onomástico real: `div_nomes` e `share_nome_top`
vêm da **mesma tabela** (`br_ibge_nomes_brasil`) e são dois resumos estatísticos
da mesma distribuição categórica — número de categorias por item (diversidade)
e concentração no item mais frequente (dominância) são inversamente ligados por
construção combinatória (o mesmo padrão que faz riqueza de espécie e índice de
Simpson andarem em direções opostas em ecologia), não por confusão estatística.
**Não é para promover a `achados_fortes.md`**: é a mesma tabela medida duas vezes
sob nomes diferentes, deveria ter caído em `tautologias.tsv` — registrar em
`ESPELHO` de `90_analise.py` (`{"nomes_distintos","share_nome_top","nascimentos"}`)
na próxima passada.

**H39 — sobrevive, achado modesto mas robusto.** Acrescentar crescimento do PIB
(`pib/pib_2010-1`) ao controle, além do nível de PIB per capita que já estava lá,
quase não move o parcial (+0,33 → +0,31, n=5.565). A intensidade de construção
por domicílio (CNEFE) acompanha crescimento populacional 2000→2010
independentemente do nível **e** do crescimento da economia — complementa o
T70-3 (obras × PIB per capita, inverso: autoconstrução pobre) com uma dimensão
demográfica que T70-3 não testou. Candidato a `achados_fortes.md` (ver H3 na
seção de fechamento do Bloco I).

**H40 — resultado misto, não os três juntos.** Cortando os 3.336 municípios do
MIDES em metade de cobertura ALTA/BAIXA (proxy: `mides_pagamentos`, mediana
32.171 registros):
- `div_nomes × mides_valor_pc` (a perna com **inversão de sinal**, bruto +0,47 →
  parcial −0,23): na metade de cobertura ALTA o parcial cai a **−0,02**
  (essencialmente zero); na metade BAIXA fica em −0,25, quase igual ao painel
  inteiro. **Falseador confirmado**: a inversão é artefato de recorte
  incompleto, concentrado nos municípios com menos registro de pagamento.
- `mides_valor_pc × share_nome_top` (bruto +0,07, parcial +0,32): fica positivo
  nas duas metades (ALTA +0,20, BAIXA +0,28) — **não** confirma o falseador,
  a relação não está confinada à cobertura ruim. Fraca (r~0,2-0,3) e sem
  explicação mecânica óbvia — fica em aberto, não é para promover sem mais
  investigação.

### 5.3 · Duas já medidas nesta passada

Não ficaram como promessa — foram ao beelink. As duas estão em
`docs/achados_fortes.md` como **G1** e **G2**.

**Dispersão de preço de medicamento (H23).** `br_saude_bps`: 342.716 compras,
12.993 itens CATMAT, com `preco_unitario`, CNPJ do comprador **e** do
fornecedor. Fixando item × unidade de fornecimento × **ano** (para não medir
inflação), em 1.199 células com ≥60 compras e ≥15 compradores, cobrindo
**R$ 7,1 bilhões**: a razão p90/p10 mediana é **2,40×**, e no decil mais
disperso **3,75×**. Midazolam 5 mg/ml injetável em 2021 varia **5,8×** entre
compradores; risperidona 1 mg/ml, 4,4×; enoxaparina 100 mg/ml, 3,3× sobre
R$ 109 milhões.

**Tamanho da propriedade rural (H37).** O D1 caiu porque media *quanta* terra
está cadastrada. O que sobrevive é o *tamanho* dela. CAFIR ha/imóvel, parcial
com log-área:

| Desfecho | bruto | parcial (pop, PIB, UF) | **+ log-área** |
|---|---|---|---|
| valor agropecuário por hectare | −0,483 | −0,392 | **−0,204** |
| crédito rural por hectare | −0,463 | −0,347 | **−0,301** |
| frente ativa DETER (share) | +0,393 | +0,252 | +0,094 ❌ |

Do primeiro ao quinto quintil de tamanho médio (130 ha → 3.630 ha), o valor
agropecuário por hectare cai de R$ 294 para R$ 40 e o crédito por hectare de
R$ 365 para R$ 59 — **7× e 6×**. A perna de desmatamento **não** sobrevive
(+0,09, e −0,015 dentro da Amazônia): tamanho de propriedade é intensidade de
uso, não fronteira.

### 5.4 · O que este método não pega

- **Molde é lista curada, não descoberta.** Os 8 moldes vieram de ler os 60
  achados existentes. Um molde que nunca ocorreu neste espelho não está lá.
- **A subtração é por família, não por pergunta.** Se `perguntas.md` cobre
  `credito × trabalho` uma vez, a combinação inteira conta como ocupada — o que
  subestima o que resta. É deliberado: erra para o lado de não repetir.
- **Cobertura municipal exige contagem exata.** `approx_count_distinct` devolveu
  **6.859 idêntico para 50 datasets diferentes** — o HLL é determinístico dado o
  mesmo conjunto de valores, e erra +23% no conjunto dos 5.570 códigos IBGE.
  Qualquer filtro de poder construído sobre ele está inflado; usar
  `count(DISTINCT)`.


### 5.5 · A fila seguinte — H46–H62

> **Nota de numeração e de sessão paralela (2026-09-06):** este arquivo foi
> escrito por **duas sessões ao mesmo tempo**. H41–H45 e o `Bloco I` de §2 são
> da outra sessão (trincas nunca cruzadas, tema 77 de `perguntas.md`, extração
> em `50_novas.sql`, resultados em `respostas.md` §77 e no plano
> [`tasks/done/bloco_i_pendencias.md`](done/bloco_i_pendencias.md)). Os blocos
> **N–R abaixo, H46–H62**, são desta sessão, e as letras I–M já estavam
> ocupadas. Antes de abrir a próxima fila, **conferir as duas numerações**.

Gerada pelo mesmo método, agora com a cobertura municipal **medida com
`count(DISTINCT)`** (117 datasets em `cobertura_municipal.json`). O gerador
enumera **1.771 combinações de 2–3 famílias com poder ≥2.000 municípios; 1.383
delas (78%) continuam inéditas**. As famílias mais vazias, por combinações
ocupadas:

| Família | Combos ocupados | Combos inéditos | Cobertura da melhor fonte |
|---|---|---|---|
| `mobilidade` | 4 | 224 | — só UF |
| `comercio_exterior` | 6 | 220 | — só UF |
| `fundiario` | 9 | 195 | 5.559 |
| `agropecuaria` | 10 | 215 | 5.567 |
| `saneamento_agua` | 10 | 213 | 5.570 |
| `fiscalizacao_ambiental` | 12 | 193 | 5.559 |
| `natalidade` | 12 | 185 | 5.723 |
| `conectividade` | 14 | 203 | 5.570 |

Contra `demografia_censo` (64) e `trabalho_empresa` (75), que estão saturadas.
**A fila abaixo ataca as sete primeiras** — todas com fonte municipal de
cobertura quase total e quase nenhuma pergunta feita.

> **Estado (2026-09-06):** H46–H62 rodaram, todas as 17 — **5 ✅ · 9 ❌ · 3 ◐**. Extração `scripts/hipoteses/60_familias_vazias.sql`, análise
> `scripts/hipoteses/97_familias.py`, OUT dir `~/rodado_hipoteses/familias/`.
> Respostas em [`docs/hipoteses/respostas.md`](../docs/hipoteses/respostas.md) ("Bateria das
> famílias vazias"); sobreviventes como **J1–J4** em
> [`docs/hipoteses/achados_fortes.md`](../docs/hipoteses/achados_fortes.md).
>
> | # | Veredito | Resumo |
> |---|---|---|
> | **H46** | ❌ | A PAM **não registra quebra de safra**: colhida ≈ plantada (perda mediana 0,0000). A medida não existe |
> | **H47** | ❌ | HHI da pauta agrícola × mortalidade infecciosa: **+0,001** |
> | **H48** | ❌ | **A defasagem não existe**: mesmo ano −0,442, 1 ano −0,468, 2 anos −0,446 — iguais. A perna de tamanho confirma (quartil dos maiores −0,220 contra −0,47/−0,55) |
> | **H49** | ◐ | Silvicultura × frente DETER **−0,204** (evita a fronteira), mas × desmatamento acumulado +0,008 (nula) |
> | **H50** | ✅ **forte** | Bovinos/ha × share desmatada **+0,486** com log-área, quintis 0,332→0,831 — **supera o F3** → **J1** |
> | **H51** | ◐ | Atlas × conectividade **−0,101**: um décimo do G3. Por ser modelado, o Atlas não carrega o viés de quem preenche |
> | **H52** | ❌ | Natureza jurídica do prestador: esgoto tratado mediano é **0,0 em todas** as categorias, não separa |
> | **H53** | ❌ | Esgoto sem tratamento × internação infecciosa **−0,015**, e × óbito infeccioso **−0,084** — sinal invertido, é `registro_vs_fenomeno` |
> | **H54** | ❌ | Ponte nome→IBGE casou 1.573/1.577 (99,7%); vazão pc × esgoto sem tratamento bruto −0,359 → **parcial −0,043**. Os brutos eram porte |
> | **H55** | ✅ | HHI de tomador do SICOR mediano **0,007** (crédito rural é pulverizado); × tamanho da propriedade +0,174, × crédito/ha **−0,352** → **J2** |
> | **H56** | ❌ | Embargo × tamanho da propriedade **+0,091** (bruto +0,327 era escala); × desmatamento **−0,169** |
> | **H57** | ◐ | Razão SICAR/CAFIR mediana **0,75**; 11,8% declaram mais ao ambiente que ao fisco. × desmatamento +0,143, × tamanho da propriedade **−0,226** — é fenômeno de propriedade pequena |
> | **H58** | ❌ | Fogo com chuva recente (22,9% dos focos) ortogonal a tudo: +0,011 · +0,001 · +0,010 |
> | **H59** | ✅ | Cesárea 59,7%; **72,5% em 8-17h contra 59,4%** de todos os nascimentos. Mas o excedente cai onde a cesárea é comum (**−0,622**) → **J3** |
> | **H60** | ❌ | Baixo peso × esgoto, atenção básica e pobreza: as quatro colapsam |
> | **H61** | ✅ | Notificação × 4G/5G **+0,159** contra internação **+0,036** — **4,4×**. Quintis de IBC: notificação 117→293, internação 183→239 → **J5** |
> | **H62** | ✅ | Escola sem internet × IDEB **−0,144 parcial** — custa nota, não é só proxy de renda → **J4** |

#### Bloco N · Agropecuária — 10 combinações ocupadas, 5.567 municípios

`br_ibge_pam` (lavoura, com `area_plantada`, `area_colhida`,
`rendimento_medio_producao`, `valor_producao` por produto), `br_ibge_ppm`
(rebanho e produção animal), `br_ibge_pevs` (extrativismo e silvicultura). Três
tabelas municipais completas, praticamente sem pergunta.

| # | Hipótese | Molde | Falsearia se |
|---|---|---|---|
| **H46** | A razão **área colhida ÷ área plantada** da PAM é uma medida direta de quebra de safra por município e ano. Cruzada com o Garantia-Safra (H14, que ficou sem a perna do SCR), diz se o seguro paga onde a safra quebrou ou onde o cadastro existe | programa_vs_necessidade | a perda de safra prever o pagamento tão bem quanto o cadastro prévio prevê |
| **H47** | Municípios de **monocultura** (HHI alto sobre `valor_producao` por produto na PAM) têm mortalidade por agrotóxico/neoplasia maior que os de policultura de mesma renda | — (cruzamento inédito: agropecuaria × mortalidade) | o HHI de produto ser ortogonal à causa de óbito |
| **H48** | O rendimento médio da lavoura (kg/ha, já pronto na PAM) responde a crédito rural com **defasagem de um ano**, e a resposta é menor onde a propriedade é grande (G2) | fluxo_vs_estoque | não haver defasagem, ou a resposta não variar com o tamanho da propriedade |
| **H49** | A silvicultura (PEVS) ocupa o município que **já** desmatou, não o que está desmatando: correlaciona com PRODES acumulado e não com DETER recente — a imagem espelhada do C1 | fluxo_vs_estoque | silvicultura acompanhar a frente ativa |
| **H50** | Rebanho bovino por hectare (PPM ÷ área) prevê desmatamento melhor que crédito rural, e a diferença entre os dois separa pecuária extensiva de agricultura intensiva | fluxo_vs_estoque | rebanho e crédito preverem igual |

#### Bloco O · Saneamento — 10 ocupadas, cobertura total, e um par declarado/observado já provado

O H24 mostrou que o SNIS mede quem preenche. O **Atlas Esgotos da ANA**
(`br_ana_atlas_esgotos`) é a mesma pergunta medida por **modelagem de terceiro**,
com `indice_atendimento_com_coleta_com_tratamento` e vazão por município.

| # | Hipótese | Molde | Falsearia se |
|---|---|---|---|
| **H51** | O índice do Atlas Esgotos (modelado pela ANA) e o declarado do SNIS divergem sistematicamente — e a divergência é o **mesmo eixo de capacidade administrativa** do H24, não erro aleatório | declarado_vs_observado | a divergência ser ruído sem preditor |
| **H52** | Município cujo prestador de água é **empresa estadual** declara cobertura maior que o de autarquia municipal, controlando renda e porte — a natureza jurídica do prestador (`natureza_juridica` no SNIS) prediz a declaração | registro_vs_fenomeno | a natureza jurídica ser ortogonal à razão declarado/IBGE |
| **H53** | Esgoto sem tratamento (Atlas) prevê internação por doença infecciosa (SIH/SINAN) acima do que a renda prevê — o teste clássico que este espelho nunca fez | — (saneamento × saúde: 0 combinações) | a associação sumir sob controle de renda |
| **H54** | A vazão de lançamento outorgada pela ANA por município, cruzada com o esgoto não tratado do Atlas, identifica onde o lançamento é **legal e sem tratamento** — poluição autorizada | declarado_vs_observado | as duas medidas não se sobreporem territorialmente |

#### Bloco P · Fundiário e ambiental — o que sobra depois de G2

| # | Hipótese | Molde | Falsearia se |
|---|---|---|---|
| **H55** | O tamanho médio da propriedade (G2) prevê **concentração de crédito**: onde a propriedade é grande, poucos CPF/CNPJ tomam a maior parte do SICOR — o HHI de crédito rural por município | margem_por_elo | o HHI de tomador não variar com o tamanho da propriedade |
| **H56** | O embargo do IBAMA recai sobre o imóvel grande ou o pequeno? Cruzar `br_ibama_embargos_novo` (só contagem de termos serve — a área é 100% nula) com o tamanho médio CAFIR | regra_nao_morde | o embargo ser proporcional à área, como a regra pretende |
| **H57** | Municípios com muito CAR e pouco CAFIR (cadastro ambiental sem cadastro fiscal) são a medida da terra que se declara ao ambiente e não ao fisco | declarado_vs_observado | a razão CAR/CAFIR ser constante |
| **H58** | Foco de calor do INPE (`br_inpe_queimadas`, com `dias_sem_chuva` e `precipitacao` na própria linha) permite separar **fogo climático de fogo de manejo**: o foco em dia com chuva recente é intencional | — | a distribuição de `dias_sem_chuva` no foco ser igual à do município no mesmo mês |

#### Bloco Q · Natalidade e conectividade — 12 e 14 ocupadas

| # | Hipótese | Molde | Falsearia se |
|---|---|---|---|
| **H59** | `br_ms_sinasc` tem `peso`, `raca_cor`, `hora_nascimento` e `local_nascimento` por nascimento. A **fração de cesárea por hora do dia** distingue cesárea eletiva de emergência — e a eletiva concentra em horário comercial onde há plano de saúde privado (IEPS) | registro_vs_fenomeno | a distribuição horária ser uniforme, ou não variar com cobertura de plano |
| **H60** | Baixo peso ao nascer (SINASC) × esgoto sem tratamento (Atlas) × cobertura de atenção básica: qual das três pernas prevê, depois de renda? | — (natalidade × saneamento: inédita) | as três colapsarem sob controle de renda, como D4 |
| **H61** | A conectividade (IBC) prediz a **notificação** de agravo (SINAN) melhor que prediz a incidência medida por internação (SIH). A diferença entre os dois é a medida direta do viés de registro do C3/D19 | registro_vs_fenomeno | notificação e internação responderem igual à conectividade |
| **H62** | Escola sem internet (SIMET, D15) × desempenho (IDEB/SAEB) dentro da mesma UF: a defasagem digital custa nota, ou é proxy de renda? | — | o efeito sumir sob controle do INSE (que é pobreza com outro nome, C4) |

#### Bloco R · Onde o espelho não deixa perguntar

Estas **não** entram na fila: são registro de limite, para não serem
redescobertas.

| Família | Por que está travada |
|---|---|
| `mobilidade` | ⚠️ **corrigido em 2026-09-06** — a nota original testou só `br_mobilidados_indicadores.transporte_alta_capacidade` (9 municípios) e `br_anac_dadosabertos` (por aeroporto). A tabela `proporcao_mortes_negras_acidente_transporte` do mesmo dataset cobre **5.544 municípios** e nunca tinha sido testada — ver tema 82 de `docs/perguntas.md` e achado L1 de `achados_fortes.md`. A família **não está travada**, só estava sub-explorada |
| `comercio_exterior` | 220 inéditas; COMEX STAT é por município de **domicílio fiscal do exportador**, não de produção — o cruzamento territorial é enganoso |
| `precos_indices` | IPCA/INPC/IPCA-15 cobrem 9, 9 e 2 municípios. Preço municipal só existe via ANP (422 municípios) |
| `seguranca` | Depende inteiramente do SISDEPEN, com preenchimento desigual por UF |
| `justica` | Os 5 espelhos de TCE não têm penalidade por município; CNJ improbidade está contaminado (H36) |

#### O que falta para fechar o ciclo

`93_inedito.py` hoje **enumera e ranqueia**, mas quem escreve a hipótese
concreta a partir da tupla de famílias ainda é leitura humana. O passo que
falta é usar `moldes.yaml` para emitir a frase — cada molde já tem `teste`,
`falseia` e `candidatos`, que é exatamente o que uma hipótese precisa ter.
Com isso a fila deixa de ser escrita à mão e passa a ser gerada, revisada e
podada.
