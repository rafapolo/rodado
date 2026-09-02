# Harness local: Gemma 4 + dsh respondendo perguntas abertas sobre o espelho

Diário de experimentos, 2026-09-01/02. Tudo aqui foi **medido no beelink**, não
estimado; onde há estimativa está dito. O código está em `harness/`, o branch é
`harness-gemma`.

**Pergunta que o experimento responde:** dá para responder pergunta aberta em
pt-BR sobre as 904 tabelas do espelho, com número correto, sem pagar API?

**Resposta até agora:** dá, com laço agêntico, a ~8 min por pergunta. O que quase
deu errado não foi o modelo — foram sete decisões minhas de arquitetura e
configuração, seis delas invisíveis sem medição.

---

## 1. O resultado que decide o desenho

Mesmas 5 perguntas, mesmo modelo, mesmo portão, mesmo beelink. Muda só quem
decide a sequência de passos.

| | dsh + MCP (agêntico) | pipeline fixo (`laco.ts`) |
|---|---|---|
| **Correto** | **3/3 = 100%** | **0/3 = 0%** |
| Tempo | 879 s → **~400 s** | 61 s |

O pipeline fixo é 14x mais rápido e não serve. As três falhas dele nomeiam o que
o laço agêntico faz de essencial, e nenhuma é erro de SQL:

- respondeu **573** em vez de 789 — agrupou por sexo e reportou um grupo só;
- devolveu **`3550308`** em vez de "São Paulo", por não ir ao diretório;
- bateu 4x no portão e desistiu, sem recuperar.

**São erros de não iterar.** É por isso que o agêntico ganha mesmo custando 7x
mais tempo, e é por isso que otimizar tempo aqui só vale enquanto a correção não
cai junto.

---

## 2. O portão, e por que ele não é opcional

`_check_read_only` do `mcp_server.py` valida tipo de statement e palavra
proibida. Basta enquanto quem dirige é uma pessoa: a disciplina de partição e de
codificação está em prosa no docstring do `run_sql`. **Prosa em docstring não é
enforcement para um modelo autônomo.**

Duas camadas existem por erro que o Gemma cometeu de verdade:

| Erro do modelo | Custo |
|---|---|
| `SELECT COUNT(*) FROM br_ms_sim.microdados` — sua primeira tool call | Varredura completa segura o lock do DuckDB por horas |
| `causa_basica BETWEEN 'X60' AND 'X84'` | CID é guardado **sem ponto** (`X840`), e `'X840' > 'X84'` — o grupo X84 some. **726 contra 789 reais: 8% a menos, com número plausível** |

O segundo é o modo de falha que importa: não dá erro, dá um número que passa.

Uma terceira camada veio de um achado de outra sessão: `br_ibama_embargos` tem
497 mil linhas e `status='done'`, e mesmo assim não serve — os valores são
strings vazias porque o CSV foi parseado errado e os bytes nunca chegaram. Ela
responde zero, e o zero passa por resposta: "não há embargos" no lugar de "não há
dado". O único sinal no espelho é a nota do dataset que a substituiu, o que deu
um mecanismo geral: varrer as notas de todos por ``Substitui `X` `` e aposentar X.

---

## 3. Recuperação: catálogo no prefixo vence embedding

| Estratégia de escolha de dataset | Recall | Casos perfeitos |
|---|---|---|
| `search_tables` (embedding doc2query) | 52,9% | — |
| catálogo de 212 nomes no prefixo | 91,3% | 85,7% |
| **+ 43 exemplos resolvidos no prefixo** | **97,8%** | **96,4%** |

Funciona porque os nomes já são semânticos — `br_ms_sim` é Ministério da Saúde /
Sistema de Informação sobre Mortalidade. O embedding comprime isso num vetor e
perde; ler a lista literal não perde.

E é **grátis por pergunta**: o `llama-server` reaproveita o KV do prefixo comum.
Medido — prefixo de 1.165 tokens: 1ª chamada 19,5 s, 2ª **0,44 s** (5 tokens
novos). Com 43 exemplos o prefixo vai a ~11k e o prefill medido continua em ~45.

**Consequência de projeto:** estabilidade do prefixo é restrição de arquitetura,
não otimização. Qualquer coisa variável (timestamp, ordem não determinística)
evapora o 44x sem ninguém perceber. O campo `timings.prompt_n` é o detector.

Divisão treino/teste **por tema**, não por caso: dentro de um tema as 5 perguntas
são variações do mesmo cruzamento, e dividir por caso deixaria o vizinho
quase-idêntico no prefixo, medindo memória.

---

## 4. Sete erros meus, e como cada um apareceu

Nenhum deles daria erro. Todos precisaram de medição.

| # | O erro | Como apareceu | Custo |
|---|---|---|---|
| 1 | 16 threads (`nproc`) | varredura de threads | prefill −32%, geração −31%, desvio 10x maior |
| 2 | Raciocínio do Gemma ligado | `reasoning-chunks` no log de sessão | 20,9 s → **4,7 s** por turno ao desligar |
| 3 | `-ctk q8_0 -ctv q8_0` | prefill 15,8 t/s onde o bench dava 70 | desquantizar a cada atenção domina em CPU: **15,8 → 50,5 t/s** |
| 4 | `-c 65536` com 4 slots | `n_slots = 4` no log | o `-c` é **por slot** — 4x o KV sem perceber |
| 5 | Modelo escapando pelo `bash` | trace da sessão | contornava o portão inteiro; e gastava os passos explorando |
| 6 | Sem `get_metric` | PIB per capita deu 23.704 | a métrica verificada dá **32.066** — 35% de diferença, nenhuma das duas dá erro |
| 7 | Benchmark premiando resposta errada | "não foram encontrados óbitos" contado como acerto | media a coisa errada; o certo é 789 |

O 7 é o pior: **por um tempo eu estava otimizando contra uma medição quebrada.**

### Como desligar o raciocínio (não é óbvio)

`reasoningEfforts: false` no dsh declara o modelo como não-raciocinante *para o
harness*, e não manda nada ao llama.cpp. `--reasoning off` no servidor também não
resolve. O que resolve:

```
llama-server ... --chat-template-kwargs '{"enable_thinking":false}'
```

E `reasoningEfforts: off:` (sem valor) **não carrega** — o plugin recusa com
"offers no level beyond off". `--dump-config` não pega isso: valida a composição
do patch, não o carregamento do plugin. Só o boot pega.

---

## 5. O contexto é o gargalo, não a velocidade bruta

| | 2k de contexto | ~18k (dentro do laço) | ~25k |
|---|---|---|---|
| Prefill | 50,5 t/s | 15 t/s | pior |
| Geração | 13,3 t/s | 9 t/s | pior |

Cai ~3x. E o system prompt do próprio dsh eram **14.213 tokens** — desligar as
ferramentas que o harness não usa (`bash`, `fs`, `web`, `subagent`, `skill`,
`workflow`, `todo`, `goal`, `ralph`, `jobs`) levou a **6.849**, corte de 52%.

Efeito medido, com a correção intacta:

| | antes | depois |
|---|---|---|
| Suicídios RJ | 645 s | **490 s** |
| PIB per capita MG | 504 s | **293 s** |

Cortar superfície de ferramenta tem um segundo ganho: um 26B em q4 escolhe melhor
entre 5 ferramentas do que entre vinte.

---

## 6. Onde o modelo ainda erra sozinho

- **Não chama a ferramenta que resolveria.** Gastou 991 s em 31 consultas caçando
  o nome da coluna (`causa_materia`, `causa_materna`, `cid_causa_morte`) sem
  achar `causa_basica`, que `descrever_tabela` devolve na quinta linha em 619
  tokens. Conserto: a rejeição do portão passou a **listar as colunas parecidas**
  em vez de só acusar.
- **Codificação do domínio.** CID sem ponto, `coded_differently` (`sexo`,
  `raca_cor`, `estado_civil`). É onde erra plausível.
- **Prosa cita a ferramenta.** As respostas mencionam `br_ibge_pib.municipio`, e
  a convenção de `pages/analises/results/` é citar o órgão de origem, nunca a
  tabela. Ainda não corrigido.

---

## 7. O que fica

**Arquitetura:** laço agêntico (dsh) + portão exposto como ferramenta MCP. A
rejeição volta ao modelo como resultado de tool, então o reparo é do harness e
não código meu — foi assim que 726 virou 789.

**MCP é o transporte, não o custo nem o benefício.** O primeiro teste de tool
calling não usou MCP nenhum e funcionou; o protocolo custa milissegundos contra
turnos de 20 s. O que o MCP entrega é o portão como ferramenta e o log auditável.

**O que ainda não sei:** a taxa de acerto nos 58 casos com `n` conferido de
`respostas.md` — o conjunto multi-tabela, que é o objetivo real. É o próximo
número.

## Ver também

- `harness/README.md` — como rodar
- `gemma_stats.md` — o benchmark do modelo isolado
- `tasks/check-dspark-replacement.md` — por que LFM2.5+DSpark não substitui
- `tasks/harness_gemma_dsh.md` — o plano original, para comparar com o que saiu
