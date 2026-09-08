# Achados de CNPJ — o espaço inteiro de trincas/quadras/quintuplas de papel

Extensão de [`achados.md`](achados.md) e do eixo de identificador que `h3_20_matriz_cnpj.py`
abriu só até pares (ver `cnpj_pares.csv`). Aqui o espaço inteiro de combinações
de papel de cadastro (não só pares) foi minerado via **Apriori** (mineração de
itemsets frequentes) sobre **42 papéis de CNPJ** — sancionado, terceirizado
federal, fornecedor da Câmara/Senado, doador de campanha, autuado pelo IBAMA,
devedor da PGFN, titular de mineração, e outros 34.

## Pipeline (`scripts/hipoteses-cnpj/`)

```bash
python3 scripts/hipoteses-cnpj/10_cache_universo.py     # carrega papeis+cadastro uma vez -> universo.npz
python3 scripts/hipoteses-cnpj/20_apriori_itemsets.py --k-max 5 --n-min 30 --lift-min 2.0
```

Rodado no beelink (offline, sem rede) sobre os CSVs já extraídos em
`~/rodado_hipoteses/h3_20260907/` pela rodada h3. `10_cache_universo.py` paga
uma vez o custo de ler `h3_cnpj_cadastro.csv` (3,4 GB, 64.491.794 raízes) e
grava um cache compacto; `20_apriori_itemsets.py` faz a mineração de verdade.

**Por que Apriori, não força bruta**: com 42 papéis, testar todas as
combinações de tamanho 5 seria C(42,5) = 850.668 candidatos. Apriori poda pela
propriedade antimonotônica — se um par não bate o piso de 30 empresas em
comum, nenhuma trinca que o contenha pode bater — e usa junção por prefixo
(agrupa por k-2 elementos em comum) em vez de comparar todo par de itemsets,
o que evita o colapso O(F²) que a primeira tentativa deste pipeline teve (13
minutos de CPU parado, sem geração nenhuma — corrigido antes do resultado
final abaixo).

**Espaço testado, de fato**:

| Nível | Candidatos (pós-poda) | Frequentes (≥ 30 empresas) |
|---|---|---|
| pares | 861 | 499 |
| trincas | 3.741 | 2.842 |
| quadras | 10.880 | 9.250 |
| quintuplas | 20.473 | 18.456 |
| **total** | **35.955** | **31.047** (16.775 não-definicionais, lift ≥ 2,0) |

## O artefato que quase virou manchete falsa — e como foi corrigido

O ranking bruto por `lift` (P(itemset) ÷ produto das probabilidades
marginais) despenca para números absurdos ao empilhar papéis raros: o topo
chegava a lift = **1,77 bilhão** para uma quíntupla de ~40-50 empresas. Isso
não é bug de dado — é a mecânica do próprio lift: cada papel raro adicional
multiplica o denominador (a probabilidade "esperada sob independência") por
uma fração cada vez menor, então mesmo uma associação real infla o número
por ordens de grandeza a cada papel a mais. Comparar o lift de uma quíntupla
com o lift de um par (como o h3 "MH = 291,3" que já é manchete) é comparar
escalas diferentes.

**Correção**: a tabela abaixo ordena por **contagem real de empresas**
(`n`), não pelo lift composto, e reporta os **lifts dos pares internos** —
já validados pelo `h3_20_matriz_cnpj.py` original, cada um isoladamente
"achado" (não definicional) — como evidência de apoio. O lift composto de 5
vias aparece só como sinal de ranking interno, nunca como "empresa é X vezes
mais provável" — essa afirmação só vale para os pares.

## Achados (contagem real + pares internos validados)

Todos os pares abaixo foram conferidos individualmente contra `cnpj_pares.csv`
(k=2 da mesma corrida) — dois candidatos iniciais (fornecedor do
Congresso × devedor da PGFN; estabelecimento de saúde × licitante+PNCP)
caíram nessa conferência: os pares que os sustentariam tinham lift **abaixo
de 1** (fornecedor do Congresso é *menos* provável de dever à PGFN que a
base, não mais) ou muito perto de 1 (sem sinal real). Ficam de fora — o
propósito desta tabela é reportar só o que a evidência interna sustenta.

| # | Papéis | n (empresas) | Pares internos (lift, tipo achado) | O que significa | Por que importa |
|---|---|---|---|---|---|
| N1 | fornecedor da Câmara + registro ambiental (CTF/IBAMA) + revenda de combustível + fornecedor do Senado (CEAPS) | 5.397 | câmara×IBAMA 4,7 · câmara×combustível 20,2 · câmara×Senado 56,7 · IBAMA×combustível 5,9 · IBAMA×Senado 5,6 · combustível×Senado 26,9 | Um grupo de ~5.400 empresas que ao mesmo tempo vende combustível (fiscalizada pelo IBAMA por isso), fornece para a Câmara **e** para o Senado — provavelmente o mercado de abastecimento de frota do Congresso | Primeira vez que se mede o tamanho desse cluster; nenhum dos 6 pares que o compõem é definicional — a sobreposição é real, não decorre de definição de cadastro |
| N2 | participante de licitação federal (CGU) + fornecedor do PNCP + contratado do TCE-RJ | 5.154 | licitante×PNCP 6,1 · licitante×TCE-RJ 11,5 · PNCP×TCE-RJ 14,5 | ~5.150 empresas participam de licitação federal, vendem via PNCP **e** têm contrato com prefeitura fluminense auditada pelo TCE-RJ | Estende o achado "maior lift da corrida" do h3 (fornecedor do Banco de Preços em Saúde × TCE-RJ, MH=291,3) para um terceiro cadastro de compra pública |
| N3 | doador de campanha + autuado pelo IBAMA | 8.623 | doador×autuado 26,2 (a terceira perna, registro CTF, foi descartada: doador×CTF = 1,1, sem sinal) | 8.623 empresas doaram para campanha eleitoral e já foram autuadas pelo IBAMA por infração ambiental | Cruza financiamento eleitoral com histórico de infração ambiental — o par isolado, sem inflar com uma terceira perna que não acrescenta nada |
| N4 | participante de licitação federal + geração distribuída solar + fornecedor do PNCP | 8.554 | licitante×solar 2,6 · licitante×PNCP 6,1 · solar×PNCP 2,2 | 8.554 empresas que disputam licitação federal e vendem ao governo via PNCP também têm sistema de geração solar próprio no CNPJ (sinal moderado, não forte) | Ponte com os achados de energia solar como marcador de classe (B4/h2 em `relevantes-bio.md`) — agora do lado da **empresa** fornecedora, não do domicílio |
| N5 | cartão corporativo do governo + participante de licitação + fornecedor do PNCP | 5.617 | cartão×licitante 7,1 · cartão×PNCP 2,7 · licitante×PNCP 6,1 | 5.617 empresas usam cartão corporativo governamental, disputam licitação federal e vendem via PNCP | Perfil de "empresa que vive de contrato público" com três pontas de evidência administrativa independentes, todas positivas |

## Camada extrema — pequena, mas estruturalmente incomum

Estes têm poucas empresas (30-90) e lift composto astronômico — não porque
sejam "achados mais fortes" que os de cima, mas porque combinam vários papéis
individualmente raros. O número de lift **não** deve ser citado; a contagem e
a lista de papéis, sim.

| Papéis | n | Leitura |
|---|---|---|
| penalidade do BC + BNDES não-automático + autuado IBAMA + outorga de lançamento de água + patrocinador Rouanet | 50 | Um grupo de 50 empresas que acumula multa do Banco Central, crédito BNDES não-automático, autuação ambiental, outorga de lançamento de efluente **e** patrocínio cultural — cinco chapéus regulatórios muito diferentes na mesma raiz de CNPJ |
| penalidade do BC + BNDES não-automático + sócio-holding + outorga de lançamento de água + patrocinador Rouanet | 44 | Variante do grupo acima trocando autuação IBAMA por estrutura societária em holding |

## O que ainda falta

`cnpj_itemsets.csv` (31.047 linhas, `tasks/hipoteses_resultado/hipoteses-cnpj/`)
guarda o espaço inteiro — a tabela acima é uma curadoria de 7 combinações
(5 + 2 na camada extrema), conferidas par a par, não uma leitura exaustiva.
Os 16.775 marcados "achado" (não-definicional, lift ≥ 2,0) são material bruto
para quem quiser minerar mais ângulos — mas qualquer extração nova precisa
passar pela mesma conferência par-a-par antes de virar afirmação, como os
dois candidatos descartados acima mostram.
