# BPE no harness — de query→resposta para query→relatório

> Aberto em 2026-09-02, a partir da leitura de EvoHarness-RL
> ([arxiv 2608.05446](https://arxiv.org/html/2608.05446v1)). Não é plano de
> treino — este projeto não tem infra de SFT+GRPO para o Gemma 4, nem faria
> sentido montá-la para um harness que já mede certo por outros meios (ver
> `regras.md`). É um mapeamento: o que o paper chama de Belief,
> Progress e Experience já existe aqui, em partes, de forma implícita ou
> hardcoded — e a Fase 5 (relatório) de `harness_gemma_agente.md` é exatamente o
> ponto onde a ausência começa a doer.

## O conceito, em uma frase

Agentes de longo horizonte perdem-se de três formas: esquecem o estado atual,
esquecem o que já fizeram, redescobrem o mesmo conserto toda vez. O paper dá
nome a cada uma (Belief, Progress, Experience) e a um conjunto de
ações (`track`, `commit`, `recall`, `note`) para o agente ler/escrever cada
uma, treinadas com GRPO cost-aware porque essas chamadas consomem o mesmo
orçamento de turnos que as ações reais. Achado central que interessa mesmo sem
treinar nada: BPE ajuda **como scaffold estático em tempo de inferência**, não
só como alvo de treino — e ajuda mais em modelos fracos (GPT-4.1 +22,1%,
GPT-5 +25,7%) do que em modelos já perto do teto (Opus 4.5 +2,1%). Gemma 4
26B-A4B em q4, sem `tools` no template embutido, está claramente no primeiro
grupo.

## Onde cada peça já existe aqui, incompleta

| Peça do BPE | Já existe como | O que falta |
|---|---|---|
| **Belief** | `anos.ts` (faixa de ano por tabela), `resolve_join`/`get_metric` (fatos já resolvidos) | Nada disso persiste **na sessão**. Cada chamada MCP é sem estado — o portão redescobre a faixa de ano, o join, a métrica a cada vez em vez de reusar o que já foi verificado nesta mesma pergunta |
| **Progress** | Nada. Não há lista de subgoal com status — só o texto que o laço vai produzindo | É exatamente o buraco que trava a Fase 5: um relatório é várias sub-alegações; sem registro de "isto já foi verificado" o risco da Rodada 6 (573 reportado como total, um `GROUP BY` mal lido) se repete por seção |
| **Experience** | As regras por subsistema de `regras.md` — cada uma é um par erro observado→refino, com o custo medido | Hoje cada linha vira código em `portao.ts` por um humano. Não é recuperável em tempo de execução pelo modelo; é enforcement, não conhecimento consultável |

O princípio já declarado em `regras.md` — *"toda camada do portão
nasce de um erro observado"* — é consolidação de experiência feita à mão, uma
rodada de cada vez. O que o paper propõe é rodar essa mesma disciplina dentro
do episódio, sem esperar um humano promover o achado a código.

## Proposta — scaffold estático, sem treino

Três acréscimos, na mesma linha do que já funcionou (`avalia_datasets.ts`
chegou a 97,8% via few-shot no prefixo estável, não via fine-tuning):

### 1. Belief — objeto de sessão, não mais uma chamada por fato

Um registro que o portão escreve e lê durante a mesma pergunta: tabelas
tocadas + faixa de ano já verificada, joins já resolvidos via `resolve_join`,
métricas já obtidas via `get_metric`, avisos de `coded_value_warning` já
emitidos. `portao.ts` consulta esse registro antes de rederivar qualquer coisa
— mesma disciplina do cache de prefixo (medição 1: 44x), agora para fatos
estruturados em vez de tokens.

### 2. Progress — outline do relatório como lista de subgoal

Só relevante a partir da Fase 5. Antes de escrever prosa, a lista de seções
do relatório entra como subgoals com status (`pendente` / `consultado` /
`verificado` / `redigido`). O portão já sabe rejeitar e devolver o motivo ao
modelo (é o mecanismo que corrigiu 726→789 na medição 6 de
`harness_gemma_agente.md`) — aplicar o mesmo mecanismo a "seção X citada sem
subgoal `verificado`" fecha exatamente o buraco que a Rodada 6 expôs no
pipeline fixo.

### 3. Experience — as regras de `regras.md` como store consultável

Semear com as linhas já catalogadas: CID pede `substr()` não `BETWEEN`,
`n=0` em join costuma ser bridge faltando, valores codificados divergem por
dataset para `sexo`/`raca_cor`/`estado_civil`, nome de coluna rejeitado deve
listar os parecidos. Recuperação por overlap de palavra-chave (barato, sem
treino) em vez de embedding — a mesma lição da Rodada 3 (catálogo no prefixo
bateu embedding, 91,3% vs 52,9%) sugere que recuperação simples e determinística
tende a vencer aqui. Achados novos entram via `note` durante a sessão; viram
candidatos a regra nova em `regras.md` numa revisão humana
periódica — a mesma consolidação por época do paper, só que já é o hábito
deste projeto.

### Mecanismo: 4 ferramentas MCP a mais, ensinadas por few-shot

`track_belief`, `commit_progress`, `recall_experience`, `note_finding` ao lado
das ferramentas já existentes (`mcp.ts` já expõe o portão como ferramenta
MCP — o padrão de "rejeição volta como resultado de tool call, o laço
agêntico repara sozinho" já está provado rodando). Nenhuma delas precisa de
GRPO: o precedente de `avalia_datasets.ts` mostra que exemplos no prefixo
estável já levam a escolha correta sem treinar pesos.

## O que NÃO fazer

- **Não montar pipeline de SFT+GRPO.** Sem infra, sem dataset de demonstração,
  e o próprio paper diz que o scaffold estático já captura parte do ganho.
- **Não usar embedding para Experience.** Rodada 3 já mostrou, neste mesmo
  harness, que recuperação determinística/lexical venceu embedding para
  seleção de dataset; não há motivo para esperar diferente aqui.
- **Não deixar Belief/Progress/Experience soltos sem orçamento.** Rodada 5
  (cortar o prompt de 14.213→6.849 tokens cortou tempo quase 2x) é o aviso:
  sem um teto de chamadas por seção, as 4 ferramentas novas competem pelo
  mesmo orçamento de turnos que a Rodada 5 já mostrou ser escasso a 12–15 t/s
  de geração. Análogo manual do "annealing" do paper: começar com um teto
  apertado (ex.: 1 `recall` + 1 `commit` por seção) em vez de deixar livre e
  podar depois.

## Ordem sugerida

Depende da Fase 4 de `harness_gemma_agente.md` estar fechada (medir os 32 casos
com `n` conferido) — não faz sentido adicionar BPE antes de saber se o portão
atual já resolve sozinho. Depois:

1. Belief primeiro — é o que tem uso mesmo em query→resposta (evita
   rederivar faixa de ano/join/métrica dentro do laço de reparo de uma
   pergunta só).
2. Experience segundo — baixo risco, alto reuso (a tabela já existe, só
   precisa virar dado consultável em vez de comentário em markdown).
3. Progress por último, só junto com a Fase 5 — é a única peça sem uso fora
   de relatório multi-seção.

## Riscos

- Belief/Progress mal desenhados viram só mais log — o valor está em serem
  **consultados pelo portão**, não em existirem.
- Experience por keyword-overlap pode confundir classes de erro parecidas
  (ex. `n=0` por bridge faltando vs. `n=0` por filtro de ano fora de faixa)
  — precisa de teste dirigido antes de confiar, mesmo padrão de
  "toda camada nasce de um erro observado".
- Sem o teto de chamadas, o custo por seção de relatório pode superar o
  orçamento de ~2–6 min já medido para uma resposta simples, multiplicado
  pelo número de seções.

## Fontes

- [EvoHarness-RL, arxiv 2608.05446v1](https://arxiv.org/html/2608.05446v1)
- `tasks/harness_gemma_agente.md` — arquitetura e medições que motivam este documento
- `tasks/regras.md` — as regras por subsistema, semente do Experience store
