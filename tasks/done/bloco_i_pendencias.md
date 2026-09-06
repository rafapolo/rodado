# Bloco I (H41–H45) — o que falta para fechar

> **✅ Fechado em 2026-09-06.** Os quatro itens abaixo rodaram via
> [`scripts/hipoteses/96_blocof_fechamento.py`](../../scripts/hipoteses/96_blocof_fechamento.py)
> (novo, no padrão de `92_lacunas.py`) e um fix de uma linha em `90_analise.py`.
> Resultado: **5 de 5 ✅** — H41 e H42 fecham como nulo duplo (efeito principal +
> a perna que faltava), H43 como confirmação parcial (Jaccard sobrevive ao
> teste de permutação, perfil do entrante não), H44c e H45 passaram a checagem
> de magnitude e entraram em `docs/achados_fortes.md` como H1/H2. Detalhe
> completo em `tasks/hipoteses.md` §Bloco I e `docs/respostas.md` tema 77.
> Arquivado aqui por provenance — ver `tasks/README.md`.

Plano de continuação de [`tasks/hipoteses.md`](../hipoteses.md) §Bloco I e
[`docs/respostas.md`](../../docs/respostas.md) tema 77 (T77-1…5). A corrida
completa de 2026-09-06 já rodou (`.hipoteses/20260906_blocof/`, gitignorado)
e resolveu 2 de 5 hipóteses (H44 ✅, H45 ✅); os quatro itens abaixo são o que
falta para fechar as outras três (H41 ◐, H42 ◐, H43 ⏳) — nenhum precisa de
extração nova, todos trabalham sobre os CSV já extraídos por
[`scripts/hipoteses/50_novas.sql`](../../scripts/hipoteses/50_novas.sql).

## 1 · H41b — testar a interação por quintil de HHI (não a correlação linear)

A hipótese (`tasks/hipoteses.md` H41) não é "choque de exportação prevê queda
de PBF" — é "o efeito é **maior** onde a pauta exportadora é concentrada". A
correlação linear simples entre `comex_hhi_sh4_2019` e `pbf_choque_pct` mede a
coisa errada; o teste certo é cortar por quintil de HHI e comparar a
correlação choque×PBF **dentro** de cada quintil (ou, mais direto, um termo de
interação `comex_choque_pct × comex_hhi_sh4_2019` na regressão residualizada).

- Padrão a seguir: [`scripts/hipoteses/92_lacunas.py`](../../scripts/hipoteses/92_lacunas.py)
  já faz exatamente este tipo de corte condicional para H08 (controla o IVS
  inicial em vez de só população/PIB/UF) — mesma lógica, controle diferente.
- Rodar sobre `painel.csv` de `.hipoteses/20260906_blocof/` (ou nova corrida) —
  colunas já existem: `comex_choque_pct`, `comex_hhi_sh4_2019`, `pbf_choque_pct`.
- Se o efeito emergir só nos quintis altos de HHI, H41 vira ✅ com ressalva de
  interação (padrão de escrita: "H44b domina o efeito principal" já usado para
  H44 em `docs/respostas.md`).

## 2 · H42b — corrigir por que o parcial não saiu

`sih_valor_aih_mediano` (custo mediano da AIH) não está na lista `INTENSIVAS`
de [`scripts/hipoteses/90_analise.py`](../../scripts/hipoteses/90_analise.py)
— por isso nunca entrou no scan de `correlacoes.tsv`, e o par
`saude_share_terceirizado × sih_valor_aih_mediano` (H42b) caiu no fallback do
`NOMEADAS`, que só calcula `r_bruto` (ver o bloco `idx.get((a,b))` em
`90_analise.py`, linha ~265). É o par mais forte do Bloco I em bruto (+0,25) e
é o único sem parcial calculado.

- Fix de uma linha: adicionar `"sih_valor_aih_mediano"` a `INTENSIVAS`.
- Checar que não vira falso-tautológico contra `sih_aih_n`/`sih_retencao_n`
  (adicionar a `FONTES`/`ESPELHO` só se de fato derivar de uma das duas — não
  deriva, é `median(valor_aih)`, então não precisa).
- Rerodar `90_analise.py` sobre o painel já extraído (não precisa nova
  extração SQL) e atualizar T77-2 em `docs/respostas.md` com o parcial real.

## 3 · H43 — construir o teste de grupo que falta

H43 continua `⏳` porque a variável (`troca_partido_2016_2020`) é binária e o
filtro `nunique < 5` de `90_analise.py` a exclui do scan de correlação por
desenho — não é bug, é o filtro certo para variável degenerada, mas significa
que H43 nunca vai sair de Spearman. A pergunta pede comparação de **grupos**
(troca vs. reeleição), não correlação.

- Script novo, no padrão de `92_lacunas.py` (uma seção de `print` por
  hipótese, não precisa de infraestrutura nova): comparar mediana/distribuição
  de `mides_jaccard_credor`, `entrantes_share_nao_local`,
  `entrantes_share_sancionado` entre o grupo `troca_partido_2016_2020==1` e
  `==0`.
- Cuidado de leitura: `prefeito_partido_2016 == prefeito_partido_2020` não
  distingue reeleição (mesma pessoa) de sucessão pelo mesmo partido — só dá
  para separar os dois casos com o nome/CPF do candidato, que
  `resultados_candidato_municipio` também tem (`sequencial_candidato`). Se o
  objetivo é mesmo "troca vs. reeleição" e não "troca vs. continuidade
  partidária", vale extrair `sequencial_candidato` também — decisão a tomar
  antes de escrever o script, não depois.
- Teste de diferença: Mann-Whitney (scipy não está disponível no beelink por
  convenção do runner — ver `hipoteses_overnight.sh`, "sem rede: só numpy e
  pandas") — usar diferença de mediana com bootstrap simples ou permutação em
  numpy puro, não `scipy.stats`.

## 4 · H44c e H45 — checagem de magnitude antes de promover

`docs/respostas.md` já marca os dois como ✅, mas nenhum está em
`docs/achados_fortes.md` ainda. Antes de promover, aplicar a regra do
`CLAUDE.md` ("Antes de apresentar resultados: (1) ordem de grandeza esperada,
(2) flag de anomalia, (3) verificar de duas formas independentes"):

- **H44c** (`nbf_share_dom × sinasc_share_mae_adolescente`, r_parcial +0,30):
  conferir a taxa de maternidade adolescente contra um número externo
  conhecido (ex.: taxa nacional do SINASC/MS já publicada) para garantir que
  `sinasc_share_mae_adolescente` está na faixa plausível (não um erro de
  denominador) antes de escrever o achado.
- **H45** (duplo nulo CFEM×CAGED, CFEM×CAUC): confirmar que o denominador de
  `cfem_razao_2225_1721` não está dominado por poucos municípios com CFEM
  quase zero em 2017-2021 (razão explode) — checar a distribuição da razão,
  não só a correlação.
- Formato de entrada em `achados_fortes.md`: seguir o padrão G1/G2 que a outra
  sessão (`dataset-coverage-discovery`) já usou — próxima letra livre é **H**
  (G1, G2 ocupados; F* são os achados antigos F1–F7).

## Coordenação

Este arquivo e os itens acima tocam só `.hipoteses/` (gitignorado),
`scripts/hipoteses/90_analise.py`/`92_lacunas.py`-like scripts, e as três
entradas de `docs/respostas.md`/`tasks/hipoteses.md` já criadas para o Bloco I
— não tocam `docs/context/familias.yaml`, `moldes.yaml`,
`cobertura_municipal.json` nem `tasks/inedito_*.tsv`, que são do
`dataset-coverage-discovery`. Antes de rodar `hipoteses_overnight.sh` de novo
no beelink, checar sessões concorrentes e usar um `OUT=` isolado (padrão usado
em `~/hipoteses_run_blocof` / `~/rodado_hipoteses/20260906_blocof`) — o
`.duckdb` é sempre `-readonly`, mas dois runners escrevendo no mesmo `OUT`
correm por cima um do outro.
