# `docs/pesquisa/hipoteses/` — perguntas e respostas

`perguntas.md` é a fonte fixa (43 temas × 5 perguntas, `n=X: dataset_a,
dataset_b*`, nunca editado por script); `respostas.md` é o log de trabalho
vivo — cada pergunta respondida no beelink muda o status ali (`✅`/`◐`/`⏳` por
`T<tema>-<item>`), e o harness (branch `harness-gemma`) lê os dois para montar
seus casos. Um item `⏳` costuma vir com o motivo exato no próprio texto (dado
corrompido, tabela ausente, sem chave compartilhada) — a seção "Bloqueios
mapeados" ao fim de `respostas.md` cataloga o que está estruturalmente
bloqueado (precisa de re-scraping ou campo novo), separado do que só ainda não
foi tentado.

`respostas.md` marca **dois eixos** desde 2026-09-07: o status (`✅ ◐ ⏳ ❌`, "a
query rodou?") e a **força do achado** (`🟢` forte, `🟡` moderada, `🟠` fraca,
`⚪` nula, `⬜` descritivo, mais os modificadores `↯` contraria a hipótese e `⚠`
número frágil), logo depois do status. O segundo eixo é documental: um achado
`⚪` (relação nula) segue valendo como pergunta respondida.

## `respostas_trincas.md` — o espaço inteiro, enumerado

`respostas.md` responde perguntas escritas uma a uma. `respostas_trincas.md`
**enumera e roda o espaço inteiro de trincas de família de uma vez**, em duas
rodadas (h2+h3) fundidas num único documento — método, validação contra
achados publicados e resultado por rodada estão lá, não aqui.

Os scripts de ambas as rodadas vivem em `scripts/hipoteses/` com prefixo
`h2_`/`h3_` (evita colidir com a numeração dos blocos SQL originais):

```bash
python3 scripts/hipoteses/h2_00_painel_mestre.py     # 3 paineis -> painel_mestre.csv
python3 scripts/hipoteses/h2_10_roda_trincas.py      # -> pares.csv + trincas.csv
python3 scripts/hipoteses/h2_20_escreve_respostas.py # -> a secao de trincas de respostas_trincas.md

python3 scripts/hipoteses/h3_10_estende_painel.py    # painel 270 -> 358 colunas
python3 scripts/hipoteses/h3_40_roda_trincas.py      # eixo territorio (extensao do h2)
python3 scripts/hipoteses/h3_20_matriz_cnpj.py       # eixo identificador (lift, nao correlacao)
python3 scripts/hipoteses/h3_30_politico_empresa.py  # a ponte entre os dois eixos
python3 scripts/hipoteses/h3_50_escreve.py           # -> fragmento em tasks/hipoteses_resultado/, colar a mao
```

**Os dois `_escreve` geram documentos separados, não o arquivo final** — a
fusão em `respostas_trincas.md` foi manual; rodar `h3_50_escreve.py` de novo
produz um fragmento em
`tasks/hipoteses_resultado/hipoteses3/respostas_h3_fragmento.md` que precisa
ser colado à mão nas seções correspondentes ("O que a corrida achou" até
"Como refazer"), não um doc pronto para publicar.

A extração SQL do h3 (`scripts/hipoteses/h3_*.sql` + `h3_roda.sh`, retomável por
sentinela `.done_<nome>`) roda no beelink offline — como os arquivos ficam soltos
junto com o resto de `scripts/hipoteses/`, faça stage antes do `scp` (`mkdir -p
/tmp/h3 && cp scripts/hipoteses/h3_*.sql scripts/hipoteses/h3_roda.sh /tmp/h3/`).

`scripts/hipoteses/h2_familias_colunas.yaml` é o elo que faltava — `familias.yaml`
mapeia dataset→família, o painel tem coluna, e ninguém mapeava coluna→família.
Ele também carrega as duas guardas sem as quais a corrida devolve artefato como
descoberta: `duplicatas_conceituais` (mesma quantidade por duas fontes, ou
elegibilidade compartilhada — o Pé-de-Meia exige CadÚnico, então correlacioná-lo
com o Bolsa Família é tautologia) e `metricas_de_registro` (coluna que mede a
capacidade de notificar/declarar/fiscalizar antes do fenômeno). `h3_familias_colunas.yaml`
complementa com as famílias novas do painel estendido. **Editar o YAML, nunca o
`respostas_trincas*.md` gerado.**
