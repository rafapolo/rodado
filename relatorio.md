# Malária e esquistossomose em Nova Friburgo

Levantamento a partir dos microdados do SINAN espelhados em `~/rodado`
(`br_ms_sinan_malaria` e `br_ms_sinan_esquistossomose`), consultados por
município de **residência** do notificado (código 330340).

Fonte: Sistema de Informação de Agravos de Notificação, Ministério da Saúde.
Série da malária: 2004–2024. Série da esquistossomose: 2007–2026.
Levantamento em 2026-09-01.

---

## O achado principal: a malária de Nova Friburgo é local

Das notificações de malária em residentes do município, **20 foram confirmadas**
em laboratório. Dessas, **18 têm a infecção registrada no próprio estado do Rio
de Janeiro** — e **16 apontam Nova Friburgo como o município de infecção**.

Isso contraria a leitura usual. Malária fora da Amazônia costuma ser caso
importado, trazido por quem viajou para área endêmica. Aqui não é: a maioria
absoluta dos casos confirmados foi contraída dentro do município.

No país inteiro, 155 notificações de malária registram infecção ocorrida no Rio
de Janeiro. **27 delas são de moradores de Nova Friburgo** — o segundo município
do Brasil nesse recorte, atrás apenas da capital fluminense (58).

### Casos confirmados por ano

| Ano | Confirmados | Infectados em Nova Friburgo |
|---|---|---|
| 2013 | 3 | 2 |
| 2015 | 7 | 7 |
| 2016 | 4 | 4 |
| 2018 | 2 | 1 |
| 2020 | 1 | 1 |
| 2022 | 3 | 1 |

**Total: 20 confirmados, 16 com infecção no município.**

O pico de 2015–2016 concentra 11 dos 20 casos. Não há caso confirmado depois de
2022 na série disponível.

### A ressalva que mais importa

Foram **99 notificações** de residentes, mas **62 foram descartadas** na
investigação e 17 ficaram sem classificação final. Só 20 se confirmaram.
Reportar "99 casos de malária" seria errado por um fator de cinco — a notificação
compulsória registra o caso suspeito, não o caso confirmado.

Nenhuma das 62 notificações descartadas tinha infecção atribuída ao RJ, o que dá
alguma consistência ao recorte: o que se confirma é justamente o que é local.

---

## Esquistossomose: volume baixo, mas com transmissão local

**19 notificações** de residentes entre 2007 e 2026 — número pequeno, e Nova
Friburgo não aparece entre os cinco maiores do estado (lideram Barra do Piraí com
378, capital com 330, São João da Barra com 123).

| Ano | Casos | Autóctones |
|---|---|---|
| 2008 | 1 | 0 |
| 2014 | 1 | 0 |
| 2015 | 8 | 1 |
| 2016 | 1 | 0 |
| 2017 | 5 | 1 |
| 2019 | 1 | 0 |
| 2020 | 1 | 1 |
| 2022 | 1 | 0 |

**Três casos autóctones** — contraídos no município, não importados. Para
esquistossomose isso é o dado que pesa: significa presença do caramujo
transmissor (*Biomphalaria*) em coleção de água local, e liga o caso diretamente
a saneamento e curso d'água, não a histórico de viagem.

Dos 19, **10 foram tratados e 10 evoluíram para cura** registrada; 4 tiveram exame
qualitativo positivo. As formas clínicas se dividem entre 8 de um tipo e 8 de
outro, com 3 sem registro.

O ano de 2015 aparece como pico nas duas doenças — 8 casos de esquistossomose e
7 de malária confirmada. A coincidência é notável mas não foi investigada aqui;
pode ser vigilância mais ativa naquele ano, não necessariamente mais doença.

---

## O que estes números não dizem

**Subnotificação não é medida.** Toda a série é de notificação passiva: conta
quem procurou serviço de saúde e teve o caso registrado. Malária e
esquistossomose têm formas leves ou assintomáticas que nunca chegam ao sistema.

**Não há denominador populacional aqui.** Os números são contagem absoluta, não
incidência por 100 mil habitantes — o que impede comparar Nova Friburgo com
municípios de porte diferente sem antes normalizar.

**O código do município no SINAN tem 6 dígitos** (330340), sem o dígito
verificador do IBGE (3303401). Cruzar com outras bases do espelho exige ajustar
isso, ou o join falha em silêncio e devolve zero.

**Oropouche não entra neste relatório porque não existe microdado público.** O
SINAN não publica grupo próprio para a doença no FTP do DataSUS; o painel do
Ministério da Saúde é um embed de PowerBI sem arquivo para download.

---

## Como reproduzir

```sql
-- malária confirmada, residentes de Nova Friburgo
SELECT ano_sinan, count(*) AS confirmados,
       count(*) FILTER (WHERE COMUNINF = '330340') AS infectados_no_municipio
FROM br_ms_sinan_malaria.microdados_malaria
WHERE ID_MN_RESI = '330340' AND CLASSI_FIN = '1'
GROUP BY 1 ORDER BY 1;

-- esquistossomose, com marcação de autoctonia
SELECT ano_sinan, count(*) AS casos,
       count(*) FILTER (WHERE TPAUTOCTO = '1') AS autoctones
FROM br_ms_sinan_esquistossomose.microdados_esquistossomose
WHERE ID_MN_RESI = '330340'
GROUP BY 1 ORDER BY 1;
```
