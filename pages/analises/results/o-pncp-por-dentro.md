# O PNCP por dentro

O Portal Nacional de Contratações Públicas (PNCP) junta num lugar só as compras de União,
estados e municípios. Até 24 de novembro de 2026 ele tinha **4,35 milhões de editais, 4,53
milhões de contratos e 1,26 milhão de atas de registro de preço**, publicados desde agosto de
2021. Um número de controle liga cada contrato ao edital que o originou, e o CNPJ do
fornecedor liga o contrato ao cadastro de empresas. É a base mais completa que existe sobre
o que o poder público compra no Brasil. Mas tem buracos, e alguns são grandes.

## 1. O portal só encheu em 2024

![Editais publicados por mês no PNCP, por esfera do órgão, de agosto de 2021 a outubro de 2026](/analises/img/pncp-editais-por-mes.png)

Até 2023 a nova lei de licitações (Lei 14.133) convivia com as antigas, e só quem já tinha
migrado publicava no portal. Em janeiro de 2024 as leis antigas deixaram de valer, e em três
meses o volume passou de uns 30 mil para quase 90 mil editais por mês; desde abril de 2024 fica
acima de 100 mil. **Por isso, comparar 2023 com 2024
mede a adesão ao portal, não o gasto público.**

Quem mais publica são as prefeituras e as câmaras municipais: 71% dos editais de 2025.

| ano | editais | contratos | atas |
|---|---:|---:|---:|
| 2022 | 62 mil | 41 mil | 205 |
| 2023 | 253 mil | 241 mil | 38 mil |
| 2024 | 1,23 milhão | 663 mil | 303 mil |
| 2025 | 1,46 milhão | 1,69 milhão | 487 mil |
| 2026, até 24/11 | 1,33 milhão | 1,88 milhão | 433 mil |

## 2. Quase toda prefeitura publica

![Parte dos municípios de cada UF com ao menos um edital municipal publicado em 2025](/analises/img/pncp-municipios-por-uf.png)

Em 2025, **5.227 dos 5.570 municípios** publicaram ao menos um edital, 94% deles. Em cinco
estados todos publicaram, e em outros dois faltou um. São Paulo, com 84%, e Roraima, com 80%, são os que mais
faltam.

As estatais e o Sistema S aparecem bem menos. Eles compram por regras próprias: a lei das
estatais (Lei 13.303) e os regulamentos de cada serviço do Sistema S. Por isso, não são
obrigados a usar o portal.

| quem, com cadastro ativo na Receita | quantos existem | quantos aparecem no portal |
|---|---:|---:|
| empresas públicas | 256 | 124 (48%) |
| sociedades de economia mista | 326 | 122 (37%) |
| Sistema S (Senai, Sesi, Senac, Sesc, Sebrae e outros) | 217 | 55 (25%) |

Aparecer não quer dizer publicar tudo: uma estatal pode ter um único edital no portal. Para
estudar Petrobras, Correios ou bancos públicos, o PNCP não basta.

## 3. Metade é dispensa, e quase todo o dinheiro passa por pregão

![Parte dos editais e do valor homologado de 2025 por modalidade de contratação](/analises/img/pncp-modalidades.png)

Em 2025, **49% dos editais foram dispensas de licitação**, compras pequenas ou emergenciais
feitas sem disputa. Elas somaram só 9% do valor homologado. O pregão eletrônico teve 27% dos
editais e 56% do dinheiro. A inexigibilidade, usada quando não há como competir (fornecedor
único, artista, serviço muito especializado), teve 18% dos editais e 12% do valor.

## 4. Os valores não se somam sem cuidado

![Distribuição do valor estimado dos editais de 2025, em quantidade e em soma](/analises/img/pncp-valores.png)

O portal aceita qualquer número no valor do edital. Somados, os editais de 2025 valem
**R$ 277 trilhões**, mais de 20 vezes o PIB do país. Quase tudo isso, 99,3%, está em **536
editais de R$ 1 bilhão ou mais**, 0,04% do total. Sem eles, a soma cai para R$ 2 trilhões.

O edital típico vale entre R$ 1 mil e R$ 100 mil; a mediana dos que informam valor fica em R$ 24 mil. Qualquer total
tirado do PNCP precisa de um corte, ou da mediana, antes de virar manchete. O mesmo vale para
os contratos: há contratos de trilhões, e a fonte repete o mesmo contrato em várias linhas em
2025 e 2026.

## 5. Contrato assinado antes de o edital aparecer

![Contratos assinados em 2025 antes da publicação do edital, por modalidade](/analises/img/pncp-antes-do-edital.png)

**14,5% dos contratos assinados em 2025 vieram antes de a compra deles ser publicada no
portal.** Quase todos, 82%, são contratação direta. Na dispensa e na inexigibilidade não há
disputa: o órgão escolhe o fornecedor e registra a compra depois, em geral cerca de duas
semanas depois (mediana de 13 a 14 dias). No pregão eletrônico isso quase não acontece, em
1,5% dos casos.

As exceções que chamam atenção são concorrências e credenciamentos: 30% e 26% dos contratos
assinados antes do edital, com medianas de 207 e 86 dias. É ali que vale olhar caso a caso.

## 6. Muitas portas de entrada

![Sistema de compras que publicou cada edital de 2025 no PNCP](/analises/img/pncp-sistemas.png)

O PNCP não tem formulário. Cada órgão publica pelo sistema de compras que usa, e **250
sistemas diferentes mandaram editais em 2025**. O Compras.gov.br, do governo federal, mandou
22%. Os outros 249 dividem o resto, e nenhum deles passa de 5%. Uma parte da bagunça nos
valores e nas datas nasce aí: cada sistema preenche os campos do seu jeito.

## Como foi feito e o que fica de fora

- **Coleta:** todas as páginas da API de consulta do portal, dia a dia, de agosto de 2021 até
  24 de novembro de 2026.
- **Editais** são as contratações publicadas, uma por compra. O ano é o da publicação no
  portal.
- **Contratos** contam uma vez cada um, porque a fonte repete o mesmo contrato em várias linhas.
  O que se compara com a data do edital é a data de assinatura.
- **Valor homologado** só entra quando está abaixo de R$ 1 bilhão por edital. Os poucos registros
  acima disso somam mais do que todo o resto.
- **Municípios** são contados pelo código IBGE da unidade que publicou, só em órgãos da esfera
  municipal. O Distrito Federal, sem prefeitura, fica de fora.
- **Estatais e Sistema S:** natureza jurídica e nome no cadastro da Receita Federal, só com
  matriz ativa. Uma entidade "aparece" se tem ao menos um edital, contrato ou ata como órgão.
- **Novembro de 2026** está incompleto e não entra no gráfico mensal.

---

**Fontes.** Portal Nacional de Contratações Públicas (PNCP): API de consulta de contratações,
contratos e atas de registro de preço (2021 a 2026). Receita Federal: cadastro nacional da
pessoa jurídica (novembro de 2026). IBGE: lista de municípios.
