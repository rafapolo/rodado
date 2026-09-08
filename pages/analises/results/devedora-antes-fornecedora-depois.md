# Devedora antes, fornecedora depois

67.017 empresas venceram licitação federal e têm dívida ativa inscrita na
PGFN. Isso já era conhecido. O que faltava era a data: em **11,2% dos casos
(7.533 empresas), a dívida já existia antes da primeira licitação vencida** —
não é coincidência de cadastro, é uma empresa que continuou contratando com a
União sabendo, ou podendo saber, que já estava inadimplente. A mediana do
intervalo entre a inscrição da dívida e o próximo vencimento de licitação é
**34 meses** — quase três anos de contratos seguidos depois de virar devedora.

No cartão corporativo o padrão se repete, em proporção maior: **21,9% (5.453
empresas)** já deviam antes de receber o primeiro pagamento, com mediana de
**25 meses** entre a dívida e o recebimento.

Olhando não só a primeira vez, mas cada vencimento e cada pagamento
individualmente: **R$ 135,6 bilhões em itens de licitação** foram para 14.133
empresas privadas **depois** de a própria empresa já constar como devedora da
União, e **R$ 15,9 milhões em cartão corporativo** foram para outras 8.275,
no mesmo recorte.

---

## Quem são — licitação vencida depois de virar devedora

As dez maiores por valor, excluídas estatais (Caixa, Banco do Brasil, Correios,
Serpro e Dataprev também aparecem na dívida ativa da PGFN, mas por razão
administrativa diferente da de uma empresa privada inadimplente — ver
Ressalvas):

| Empresa | Devedora desde | Itens vencidos depois | Valor | Meses até o último vencido |
|---|---|---:|---:|---:|
| Vibra Energia | set/2008 | 3.609 | R$ 8,50 bi | 181 |
| Light Serviços de Eletricidade | ago/1996 | 1.704 | R$ 6,16 bi | 326 |
| CNH Industrial Brasil | abr/2012 | 17 | R$ 6,03 bi | 98 |
| Volkswagen Truck & Bus | out/2016 | 67 | R$ 3,80 bi | 84 |
| LCM Construção e Comércio | mar/2022 | 59 | R$ 2,83 bi | 19 |
| Mercedes-Benz do Brasil | ago/1995 | 24 | R$ 2,43 bi | 313 |
| Blau Farmacêutica | abr/2013 | 637 | R$ 2,22 bi | 126 |
| Editora FTD | ago/2016 | 36 | R$ 2,08 bi | 86 |
| Editora Ática | fev/2016 | 33 | R$ 1,70 bi | 92 |
| General Motors do Brasil | nov/2010 | 65 | R$ 1,49 bi | 155 |

LCM Construção é o caso mais rápido da lista: virou devedora em março de 2022
e, 19 meses depois, ainda vencia licitação — R$ 2,83 bilhões acumulados no
período. No outro extremo, Light e Mercedes-Benz seguiram vencendo licitação
por mais de 25 anos depois de inscritas na dívida ativa.

## E no cartão corporativo

Valores bem menores — é o canal de despesa miúda, não de contrato grande —
mas o mesmo padrão temporal:

| Empresa | Devedora desde | Transações depois | Valor |
|---|---|---:|---:|
| Mercado Pago Instituição de Pagamento | dez/2021 | 2.164 | R$ 1,34 milhão |
| Superdelli Atacado e Supermercado | out/2012 | 316 | R$ 295,4 mil |
| Marajó Locação e Serviços | abr/2020 | 4 | R$ 252,1 mil |
| Frigelar Comércio e Indústria | set/2020 | 199 | R$ 123,7 mil |
| Palácio da Ferramenta Máquinas | set/2019 | 494 | R$ 120,6 mil |

## Que tipo de empresa

Por CNAE, o mesmo setor lidera nos dois canais: **Comércio Varejista** é a
atividade principal de 2.588 das 14.133 empresas que venceram licitação depois
de já devedoras, e de 4.377 das 8.275 que receberam no cartão. Depois vêm
comércio atacadista, comércio/reparação de veículos e construção — setores de
margem apertada e giro de caixa curto, coerentes com por que a dívida se
acumula (fluxo de caixa tenso é mais comum que fraude elaborada). Um destaque
fora desse padrão: **atividades de atenção à saúde humana** é o terceiro setor
mais numeroso (852 empresas) entre quem venceu licitação depois de já dever —
prestador de saúde contratado pelo poder público, endividado com o próprio
poder público.

Por porte, a distribuição muda entre os dois canais. No cartão corporativo,
microempresa domina (4.550 de 8.275, 55%). Na licitação, não: empresa de
**porte médio/grande é a fatia relativamente maior** (5.290 de 14.133, 37% —
mais que micro e mais que pequena isoladamente) — indício de que quem segue
contratando com a União mesmo depois de constar como devedora tende a ser,
proporcionalmente, empresa maior, não menor.

## A direção do tempo importa

A maioria dos casos de sobreposição vai no sentido oposto ao que a manchete
sugere: a empresa já era fornecedora ou usuária do cartão **antes** de cair na
dívida ativa — o que é o padrão esperado (negócio primeiro, dificuldade
financeira depois). É a minoria que interessa:

| Canal | Total no cruzamento | Dívida ANTES do evento | Evento antes da dívida | Mediana (dívida antes) |
|---|---:|---:|---:|---:|
| Venceu licitação | 67.017 | 7.533 (11,2%) | 59.429 (88,7%) | 34 meses |
| Recebeu no cartão | 24.926 | 5.453 (21,9%) | 19.463 (78,1%) | 25 meses |

O corte usa a **primeira** inscrição de dívida de cada CNPJ contra o
**primeiro** evento (venceu/recebeu) — o recorte mais favorável à empresa,
porque uma dívida inscrita mais recentemente teria empurrado ainda mais casos
para a coluna "dívida antes". Os R$ 135,6 bi e R$ 15,9 milhões acima já são a
versão completa, item por item: contam todo vencimento e todo pagamento
posteriores à primeira dívida, não só o primeiro.

## Ressalvas

- **Data de inscrição não é data do fato gerador.** `DATA_INSCRICAO` marca
  quando a PGFN formalizou o débito em dívida ativa, que pode vir bem depois
  do vencimento original do tributo — o intervalo real entre "a empresa deixou
  de pagar" e "a empresa venceu de novo" pode ser maior do que o medido aqui.
- **Uma dívida inscrita não é, por si, prova de irregularidade contratual.**
  A lei permite seguir contratando com a União enquanto há certidão positiva
  com efeito de negativa — parcelamento, garantia oferecida ou discussão
  judicial em curso. O achado mede escala e janela de tempo, não julga cada
  caso.
- **Estatais foram excluídas do ranking, não dos totais.** Caixa Econômica
  Federal, Banco do Brasil, Correios, Serpro e Dataprev também têm CNPJ
  inscrito na dívida ativa da PGFN (natureza jurídica de empresa pública ou
  sociedade de economia mista) — nomeá-las ao lado de fornecedor privado
  inadimplente distorceria o quadro, então saíram do "Quem são" mas
  permanecem nos totais agregados de contagem.
- **Uma data corrompida foi descartada.** Uma linha trazia `DATA_INSCRICAO`
  como ano 1000 — claramente um valor inválido na fonte. O corte
  `DATA_INSCRICAO >= 1970` remove esse e qualquer outro caso do mesmo tipo.
- **Cobertura temporal desigual entre as bases.** Licitações federais (CGU)
  vão de 2013 a 2023; cartão corporativo, de 2013 a 2025; dívida ativa da
  PGFN cobre inscrições desde décadas antes disso. Uma dívida muito antiga
  comparada a um evento em 2013 (início da série de licitação/cartão) tende a
  cair em "dívida antes" mesmo quando a ordem real dos fatos foi outra — a
  série de licitação/cartão simplesmente não alcança para trás o suficiente
  para provar o contrário.
- **O recorte é por CNPJ completo (matriz+filial)**, não por raiz de CNPJ —
  diferente da análise "Cinco cadastros, as mesmas empresas", que agrega por
  raiz.

---

*Fontes: Procuradoria-Geral da Fazenda Nacional — dívida ativa da União;
Controladoria-Geral da União/Portal da Transparência — licitações e contratos
federais, cartão de pagamento do governo federal; Receita Federal — Cadastro
Nacional da Pessoa Jurídica (natureza jurídica, porte, CNAE). Dados
consultados em setembro de 2026.*
