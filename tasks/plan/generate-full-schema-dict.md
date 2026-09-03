# Mapear o que falta documentar no schema — plano

> Aberto em 2026-09-03, a pedido, depois de uma pergunta sobre treinar um
> modelo pra "saber o schema de antemão" esbarrar num problema anterior: boa
> parte do schema **não tem significado documentado em lugar nenhum**, nem
> pra um modelo nem pra uma pessoa lendo `describe_table`. Não é problema de
> tamanho de contexto — é problema de conhecimento que nunca foi escrito.

## O achado que motivou isto

`harness/tasks/backlog.md` item 9: `br_ms_sim.circunstancia_obito` subconta
suicídio contra `causa_basica` (CID-10) — 749 contra 789 reais no RJ 2020, 40
óbitos que o CID classifica como suicídio e o campo não captou. Achado ao
vivo, por acidente, testando outra coisa. **Nenhum mecanismo hoje avisava**:
não está em `bridges.yaml` (`coded_differently`/`false_friends`), não tem
`coded_value_warning` porque não é um caso de "mesmo conceito, código
diverge" — é um campo plausível, fácil de achar via `descrever_tabela`, que
simplesmente está sub-preenchido, e nada no espelho diz isso.

Esse é o padrão geral, não um caso isolado: **um modelo (ou uma pessoa) acha
uma coluna com nome plausível, usa ela, e o número sai errado e crível, sem
nenhum aviso.** A pergunta que abriu este plano foi "treinar um LoRA pra
saber o schema de antemão resolveria isso?" — a resposta é não, porque
treino não cria conhecimento que não existe em lugar nenhum pra começar. Isso
tem que ser escrito antes de qualquer treino fazer sentido, e tem valor
sozinho — pra busca, pro portão do harness, pra quem lê a documentação.

## O que já existe (e não é pouco, mas é parcial)

| Mecanismo | Cobre | Não cobre |
|---|---|---|
| `{dataset}.dicionario` (tabela nativa do espelho, vem do Base dos Dados) | **45 de ~230 datasets, 168 tabelas, 6.256 colunas** (`docs/context/dicionario_coverage.json`, gerado por `scripts/gera_dicionario_coverage.py`) — decodifica chave→valor **ao vivo**, sem precisar de arquivo | Os outros **~185 datasets**: nenhum decode disponível, nem na tabela nem em arquivo |
| `bridges.yaml` → `coded_differently` | Colunas onde o **mesmo conceito** tem código que diverge entre datasets — `sexo`, `raca_cor`, `estado_civil` (achado num teste cego do MCP) | Só o que já foi pego ao vivo por acidente — não é varredura sistemática |
| `bridges.yaml` → `false_friends` | Nomes que parecem a mesma coisa e não são (`valor` em 91 tabelas de 56 datasets) | Mesma limitação — curado, não varrido |
| `hierarchies.yaml` | CNAE e CID-10 são **posicionais** (substr() dá o pai, sem precisar de dicionário) — cobre a estrutura desses dois padrões-padrão inteiros | Só esses dois sistemas de código; qualquer outro (ex.: `circunstancia_obito`, tipos de logradouro, situação cadastral) fica de fora |
| `docs/overview/` | 43 arquivos temáticos, contexto narrativo por tema de pergunta | Não é por coluna — não ajuda a saber o que `circunstancia_obito=2` significa |

Juntando tudo: existe decodificação **ao vivo** pra ~20% dos datasets, um
punhado de armadilhas **curadas à mão** (achadas por acidente, uma de cada
vez), e dois sistemas de código bem documentados (CNAE, CID). O resto —
provavelmente a maioria das colunas tipo-código do espelho — não tem
nenhuma fonte de significado, documentada ou viva.

## O que "pronto" significa

Não é "documentar toda coluna do espelho" — a maioria das ~6.700 colunas
totais (contando as 1.024 tabelas) é numérica contínua, texto livre, ou
identificador, sem "significado" a decodificar. O alvo é bem mais estreito:
**toda coluna que parece código (baixa cardinalidade, valores curtos,
inteiro ou string curta) tem que sair desta varredura com uma etiqueta**:

- `dicionario_disponivel` — já coberto por `dicionario_coverage.json`, nada a
  fazer.
- `padrao_externo` — CNAE, CID-10, código de município IBGE, CBO... um
  padrão público e estável, só precisa apontar pra `hierarchies.yaml` ou pra
  documentação de fora, não pesquisar do zero.
- `documentado_em_outro_lugar` — achado em `provenance_notes`, no site do
  Base dos Dados, ou na documentação da fonte original (ex.: manual do
  SICONV) — vira entrada nova em `bridges.yaml`/comentário no schema.
  `docs/context/schema_ddl.sql` e `provenance_notes` do catálogo já são
  fontes conferíveis sem sair do projeto.
- `nao_e_codigo` — a varredura heurística errou (ex.: CEP, que tem muitos
  valores distintos mas não é "código" no sentido de precisar de glossário).
- `nao_verificado` — sobrou sem fonte. **Esta é a etiqueta que importa**: diz
  pro portão (e pra qualquer pessoa) "trate como `circunstancia_obito` até
  prova em contrário — não confie no nome, confira antes de usar".

`nao_verificado` não precisa virar `documentado_em_outro_lugar` pra este
plano fechar. Precisa **existir e estar marcado**, porque hoje a alternativa
não é "menos documentado" — é **silêncio total**, que é o que deixou
`circunstancia_obito` passar despercebido.

## Abordagem, em estágios (o barato primeiro)

### Estágio 1 — varredura heurística, sem pesquisa nenhuma

Script novo (`scripts/gera_candidatos_dicionario.py` ou similar), rodando no
beelink como `gera_dicionario_coverage.py` já faz: pra cada coluna de cada
tabela **fora** da cobertura de `dicionario_coverage.json`, medir
cardinalidade (`COUNT(DISTINCT col)`) e forma do valor (inteiro pequeno,
string curta tipo `"1"`/`"2"`/sigla). Um limiar simples (ex.: <100 valores
distintos, e não é `id_*`/`sigla_uf`/coluna de partição já conhecida) separa
"candidato a código" de "não é código". Isso já dá a lista completa de
colunas que PRECISAM de uma etiqueta — sem isso, não dá nem pra saber o
tamanho real do problema.

**Custo:** um `COUNT(DISTINCT)` por coluna candidata é uma varredura de
metadado, não uma consulta pesada — mesma categoria de custo de
`build_metadata_catalog.py`. Rodar em minutos, não horas.

### Estágio 2 — triagem contra fontes que já existem, sem pesquisa nova

Pra cada candidato do estágio 1: já está em `coded_differently` (então já é
conhecido)? O nome bate com CNAE/CID (já coberto por `hierarchies.yaml`)?
`provenance_notes` do dataset já menciona o significado? Isso separa
`dicionario_disponivel`/`padrao_externo`/`documentado_em_outro_lugar` do que
sobra — sem abrir uma página externa ainda.

### Estágio 3 — priorizar o que sobrou por uso real, não por ordem alfabética

O que sobrar do estágio 2 (candidato sem fonte) não vira pesquisa em massa
de uma vez. Prioriza pelo que **já é usado**: os datasets que aparecem nos
58 casos de `harness/tasks/backlog.md` item 2, no golden set
(`douradas_perguntas.json`, `douradas_multi.json`), ou nos 43 temas de
`docs/perguntas.md`. Documentar uma coluna de um dataset que ninguém nunca
perguntou nada tem retorno menor que fechar o buraco de um dataset que já
está no caminho de uma pergunta real — mesma disciplina de "toda camada
nasce de um erro observado" que rege o portão do harness.

### Estágio 4 — pesquisa de verdade, só pro que sobrar priorizado

Aqui sim entra trabalho manual: ler a documentação da fonte original
(muitas vezes o próprio site do Base dos Dados tem um dicionário publicado
mesmo quando a tabela `.dicionario` não foi espelhada — conferir antes de
assumir que não existe) ou o manual do órgão de origem. Escopo aberto de
propósito — não dá pra estimar até o estágio 1/2 dizerem quantas colunas
realmente sobram sem fonte alguma.

## Formato de saída

Estender `docs/context/dicionario_coverage.json` (ou um arquivo irmão,
`docs/context/schema_dict_status.json`) com uma etiqueta por coluna
candidata, no formato das cinco categorias acima. `describe_table` (MCP) já
lê `dicionario_coverage.json` pra avisar quais colunas são decodificáveis —
a extensão natural é o mesmo mecanismo também avisar `nao_verificado`,
generalizando o alerta ad-hoc que o item 9 do `harness/tasks/backlog.md`
teve que escrever à mão pra um caso só.

## O que isto destrava

- **A pergunta que abriu este plano**: só faz sentido perguntar "treinar
  algo pra saber o schema" depois de saber quais colunas TÊM significado
  documentável. Hoje a resposta seria "treinar em cima de quê, pra ~80% das
  colunas-código?".
- **Generaliza o item 9** — de um alerta manual (`circunstancia_obito`) pra
  um mecanismo que soa antes de alguém achar o próximo caso por acidente.
- **Ajuda `search_tables`/doc2query** — colunas com significado documentado
  entram como contexto melhor pras perguntas sintéticas do
  `scripts/doc2query_lotes.py`.
- **Vale por si**, mesmo sem nenhum modelo — é documentação que humano lendo
  `describe_table` também precisa.

## Ver também

- [`harness/tasks/backlog.md`](../../harness/tasks/backlog.md) item 9 — o
  achado que motivou este plano
- [`docs/context/dicionario_coverage.json`](../../docs/context/dicionario_coverage.json) — a cobertura que já existe
- [`docs/context/bridges.yaml`](../../docs/context/bridges.yaml) — `coded_differently`/`false_friends`, a curadoria manual de hoje
- [`docs/context/hierarchies.yaml`](../../docs/context/hierarchies.yaml) — CNAE/CID, os dois padrões externos já cobertos
- [`scripts/gera_dicionario_coverage.py`](../../scripts/gera_dicionario_coverage.py) — o gerador que este plano estende
