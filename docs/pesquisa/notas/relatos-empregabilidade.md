# 10 perguntas sobre desemprego e empregabilidade no Brasil

Dados extraídos de `br_me_caged.microdados_movimentacao` (admissões/desligamentos CLT, 2020–2025), `br_ibge_pnadc.microdados` (PNAD Contínua, 2025-T3), `br_me_rais.microdados_vinculos` (estoque de vínculos formais, 2024) e `br_ibge_populacao.municipio`, via DuckDB (beelink). Todas as taxas da PNAD são ponderadas pelo peso amostral `V1028`.

---

### 1. Existe um mês do ano em que o Brasil formal perde mais empregos do que ganha?

**Sim — só um: dezembro.** Analisando 2022–2025, todo mês tem saldo positivo (mais admissões que desligamentos), exceto dezembro, que fecha com **saldo negativo de ~1,4 milhão de vínculos** (4,4M admissões vs 5,8M desligamentos). É o efeito do 13º salário: empresas concentram rescisões no fim do ano para evitar o pagamento proporcional integral, e a contratação praticamente para durante as festas.

### 2. E qual é o mês "oposto" — o de maior saldo positivo?

**Fevereiro**, com saldo de **+1,3 milhão** de vínculos (8,8M admissões vs 7,5M desligamentos) — quase o dobro de qualquer outro mês. É o rebote pós-dezembro: retomada da contratação normal somada à sazonalidade de comércio, agronegócio e educação no início do ano.

### 3. Qual região do Brasil tem a maior taxa de desocupação, e qual a menor?

PNAD Contínua, 2025-T3: **Nordeste lidera com 7,84%**, contra **3,40% no Sul** — mais que o dobro. Norte (6,19%), Sudeste (5,27%) e Centro-Oeste (4,38%) ficam no meio. A disparidade regional histórica do mercado de trabalho brasileiro segue intacta.

### 4. Homens e mulheres têm a mesma taxa de desemprego?

Não. Na mesma PNAD Contínua (2025-T3), a taxa de desocupação entre **mulheres é 6,88%**, contra **4,54% entre homens** — quase 52% maior. A diferença é estrutural e persiste mesmo em trimestres de mercado aquecido.

### 5. Existe algum município brasileiro com mais empregos formais do que moradores?

Sim, dois — em 2024 (RAIS, vínculos ativos em 31/12): **Borá (SP)**, com 1.176 vínculos para 932 habitantes (**126%**), e **Barueri (SP)**, com 397.250 vínculos para 333.737 habitantes (**119%**). Barueri é o caso mais relevante em escala: é sede de dezenas de empresas (região de Alphaville), então a maioria de quem trabalha lá mora em outras cidades da Grande São Paulo — a "população empregada" ultrapassa a população residente.

### 6. Qual profissão tem o maior "efeito porta giratória" (contrata e demite quase na mesma proporção)?

**Pedreiro.** Em 2024, foram 329.648 admissões e 330.329 desligamentos — um saldo líquido praticamente zero apesar de mais de 650 mil movimentações. É reflexo direto da natureza da construção civil: contratos atrelados à duração da obra, não a um vínculo permanente. Soldador, açougueiro e cozinheiro geral aparecem logo atrás, todas ocupações "por projeto/turno".

### 7. O contrato intermitente (criado pela reforma trabalhista de 2017) está crescendo?

Sim, quase dobrou em volume absoluto: **174.648 admissões em 2020 → 347.892 em 2024** (pico de participação em 2023, 1,44% de todas as admissões formais do ano). Ainda é uma fatia pequena do total de contratações, mas seu crescimento consistente ano a ano mostra a modalidade se firmando como alternativa formal de baixa previsibilidade de renda.

### 8. Qual a diferença de informalidade entre as regiões do Brasil?

Entre trabalhadores ocupados (PNAD Contínua, 2025-T3), **metade dos empregados no Norte (50,6%) e no Nordeste (50,3%) não tem carteira assinada**, contra **22,6% no Sul** — mais que o dobro. Centro-Oeste (32,0%) e Sudeste (26,4%) ficam no meio do caminho.

### 9. A partir de que idade o mercado formal brasileiro começa a "expulsar" mais gente do que admite?

A crença popular aponta os 40 anos, mas os dados (CAGED 2024) mostram outra coisa: o saldo por idade só vira **negativo a partir dos 54 anos** — antes disso, toda faixa etária tem mais admissões que desligamentos, mesmo que a margem encolha progressivamente desde os 30. Depois dos 60, o saldo negativo dispara (ex: -22 mil aos 62 anos), combinando aposentadoria com dificuldade real de recolocação.

### 10. O CAGED registra admissões formais de menores de 15 anos fora da condição de aprendiz?

Sim, e chama atenção: em 2024, além dos ~93 mil admitidos corretamente como "Aprendiz" (categoria legal a partir dos 14 anos), o CAGED registrou **539 admissões de jovens de 14 anos e 2.572 de 15 anos sob a categoria "Empregado - Geral"** — fora do regime de aprendizagem exigido por lei para essa faixa etária. Pode refletir tanto erro de cadastro (data de nascimento) quanto contratações fora da conformidade; qualquer uma das duas leituras já seria digna de auditoria.

---

## Outras irregularidades encontradas no CAGED (2023–2025)

Na mesma linha da pergunta 10, uma varredura por padrões fora do esperado nos registros de admissão encontrou mais quatro sinais:

**Aprendiz acima do limite legal de idade (24 anos), sem deficiência declarada**
2.541 admissões marcadas como "Aprendiz" (`indicador_aprendiz='1'`) com idade acima de 24 anos e `tipo_deficiencia='0'` (não deficiente) — a lei do aprendiz (14 a 24 anos) só permite exceção de idade para PCD, e esses casos não têm essa marcação.

**Salário mensal zero ou negativo em vínculos CLT "gerais"**
798.317 admissões com `salario_mensal <= 0`, sendo **280.531 delas na categoria 101 (Empregado Geral/CLT comum)** — não intermitente, não aprendiz, não temporário. Um vínculo CLT padrão com salário declarado zero é, no mínimo, um erro de preenchimento; na pior hipótese, mascara remuneração não registrada.

**Jornada contratual acima do limite legal de 44h semanais**
1.837.805 admissões com `horas_contratuais > 44`. A distribuição mostra picos reais em 48h (198k) e 45h (161k) — plausivelmente turnos não compensados corretamente — mas também um pico artificial em **99,0h** (55.527 casos), quase certamente um código de "não informado" usado como se fosse valor de horas, não uma jornada real. Vale filtrar esse valor-sentinela antes de qualquer análise séria com essa coluna.

**Admissões de pessoas com mais de 90 anos**
74 casos entre 2023 e 2025, com idade entre 91 e 98 anos. As profissões mais comuns entre eles:

| Profissão | Admissões | Faixa etária |
|---|---|---|
| Auxiliar de Escritório | 12 | 91–95 |
| Assistente Administrativo | 8 | 91–98 |
| Recepcionista, em geral | 5 | 91–94 |
| Ator | 4 | 91–94 |
| Vendedor de comércio varejista | 3 | 91 |
| Diretor geral de empresa e organizações | 2 | 93–95 |
| Faxineiro | 2 | 91–93 |

Mais 33 profissões aparecem com 1 admissão cada, entre elas: Farmacêutico, Relações Públicas (96 anos), Operador de guindaste móvel, Pedreiro, Motofretista, Consultor jurídico, Gerente financeiro, Agente indígena de saúde (94 anos) e Tecnólogo em gastronomia (97 anos, o registro mais velho da lista). Não é ilegal — não há teto de idade para admissão formal no Brasil — mas a diversidade de ocupações físicas nessa faixa etária (servente de obras, magarefe, carregador, trabalhador volante da agricultura) chama atenção e merece checagem manual: pode ser trabalho real tardio ou erro de digitação na data de nascimento.

Nenhum desses itens está confirmado como violação legal — podem ser erros de cadastro no eSocial/CAGED em vez de fraude — mas os itens de aprendiz fora da idade e salário zero em CLT geral são os que mais destoam de qualquer explicação operacional razoável.

---

*Metodologia: CAGED mede o mercado de trabalho formal (CLT); não captura informalidade nem desalento. PNAD Contínua é amostral e ponderada; a diferença entre regiões e sexos usa o trimestre mais recente disponível (2025-T3). RAIS reflete o estoque de vínculos ativos em 31/12/2024, a base mais recente disponível localmente.*
