# Gotchas por dataset — um `.yml` por dataset, entregue pelo `describe_table`

> Aberto 2026-09-05, a pedido. Nasce de uma medição feita nesta sessão: duas
> rodadas do `pi_prompt.md` contra o Gemma 4 26B q4 (`llama-server` no beelink,
> as 18 ferramentas de `mcp_server.py` faladas por `pi-ai` sobre stdio). Os
> números abaixo foram medidos; o que é plano está marcado como plano. Nada
> deste arquivo foi implementado ainda.

## A medição que motiva isto

Cinco perguntas, gabarito conferido no beelink **antes** de rodar o modelo.
Duas versões do mesmo prompt de sistema: `v1` em inglês, genérico; `v2` em
pt-BR, com as armadilhas escritas literalmente.

| # | Pergunta | v1 | v2 | Verdade |
|---|---|---|---|---|
| 1 | Suicídios RJ 2020 | 749 ✗ | **789** ✓ | 789 |
| 2 | PIB per capita médio, municípios MG 2020 | 23.704,50 ✗ | **32.066,73** ✓ | 32.066,73 |
| 3 | Idem 1, por sexo | 132 ✗ | **789** ✓ | 573 M / 215 F / 1 |
| 4 | População de MG 2022 | ✓ | ✓ | 20.539.989 |
| 5 | Município do RJ com mais suicídios 2020 | 1.076 ✗ | **335** ✓ | 335 (Rio) |

|  | v1 | v2 |
|---|---|---|
| Corretas | 1/5 | 5/5 |
| Chamadas de ferramenta | 39 | 26 |
| Relógio de parede | 25,3 min | 19,2 min |

Dois achados que decidem o desenho:

1. **A sequência de descoberta nunca foi o problema.** `search_tables →
   describe_table → run_sql` rodou 5/5 nas **duas** versões, sem ser cobrada.
   Todas as 4 falhas da v1 foram de armadilha, nenhuma de descoberta.
2. **Escrever a armadilha no prompt conserta — e é mais barato, não mais caro.**
   A v2 tem ~70 palavras a mais e gastou 13 chamadas a menos. Precisão no
   prefixo saiu mais barata que iteração no laço.

E o problema que isto cria: 3 das 5 perguntas são mortalidade/CID, e o parágrafo
sobre `causa_basica` serve **um dataset entre 233**. A v2 acerta em parte porque
a resposta foi escrita nela. Só as perguntas 2 e 4 são evidência independente.

## Por que não cabe num prompt global

233 datasets × ~50 palavras de armadilha ≈ **15,5k tokens**. O `llama-server`
sobe com `-c 32768`, e `harness/README.md` mede o prefill caindo de 50,5 para
15 t/s entre 2k e ~18k de contexto. Um catálogo global de armadilhas gastaria o
contexto inteiro, e metade da velocidade, com 232 datasets que não têm nada a
ver com a pergunta. **Por dataset e sob demanda não é elegância — é a única
forma que cabe.**

## Por que os quatro avisos que já existem não pegaram este caso

`describe_table` já devolve `warning` (linha duplicada), `dicionario_coverage`,
`coded_value_warning` e `nao_verificado_warning`. O modelo leu todos, e ainda
assim usou `circunstancia_obito`.

O motivo é preciso e vale registrar: `circunstancia_obito` é a coluna que
**motivou** o `nao_verificado_warning` (item 9 de `harness/tasks/backlog.md`,
`plan/generate-full-schema-dict.md`), mas na resposta real ela **não aparece**
nesse aviso — aparece em `dicionario_coverage.decodable_columns`, que é um sinal
**positivo**. Ela saiu do balde de alerta ao ganhar dicionário. Ter decode não
diz nada sobre ser a coluna certa para a pergunta.

As quatro classes existentes são **estruturais** (código diverge, não há decode,
linha duplica, nome colide). A armadilha que disparou é **semântica**: a coluna
existe, está documentada, decodifica limpo, e continua sendo a errada. Agregar
as classes estruturais até o nível de dataset dá uma lista maior com o mesmo
ponto cego — é classe que falta, não escopo. Mas a classe que falta **é**
de escopo de dataset ("no SIM, causa de morte é sempre `causa_basica`" vale para
todas as tabelas do dataset), e é isso que fecha o desenho.

## Forma proposta

`docs/context/gotchas/<dataset>.yml` — um arquivo por dataset, 233 possíveis,
**escritos só onde há evidência**. A expectativa é que a grande maioria nunca
exista: ausência de arquivo significa "nada medido", nunca "sem armadilha".

```yaml
dataset: br_ms_sim
gotchas:
  - id: causa_vs_circunstancia
    resumo: "Para causa de morte use causa_basica (CID-10)."
    detalhe: >
      circunstancia_obito é campo auxiliar de circunstância declarada,
      preenchido em parte dos registros. Contar por ele subconta sem erro.
    colunas: [causa_basica, circunstancia_obito]
    severidade: silencioso        # silencioso | erro | custo
    verificado: "749 contra 789 reais, RJ 2020, medido 2026-09-05"
```

`verificado` é obrigatório, mesma disciplina de `bridges.yaml` e `metrics.yaml`:
sem o que casou e quando, a linha é aspiracional e não deve entrar.

## Entrega — sem ferramenta nova

Um quinto bloco `gotchas` na resposta de `describe_table`, com as entradas do
dataset da tabela descrita. Custo de superfície: **zero** — nenhuma descrição
de ferramenta nova (uma `explain_dataset` custaria ~150-250 tokens de prefixo em
todo turno), e cai exatamente onde o modelo já vai sozinho, 5/5 nas duas rodadas.

## Como popular sem inventar

A matéria-prima já existe, espalhada, e em pelo menos dois casos **já foi
achada e não tem onde morar**:

| Fonte | O que tem |
|---|---|
| `tasks/respostas_pendentes.md` | sentinela `capital_social=999999999999.0` em 124 empresas; coluna `modalidade` não documentada em `br_inep_formacao_docente.uf` que infla `GROUP BY` em >600% — **duas gotchas medidas, hoje sem destino** |
| `harness/tasks/backlog.md` item 9 | `circunstancia_obito` (749 × 789) |
| `tasks/done/mcp_search_refino.md` | `sexo` RAIS × CAGED; ENEM com duas convenções na mesma tabela em anos diferentes |
| `docs/respostas.md`, "Bloqueios mapeados" | bloqueios estruturais por dataset |
| `docs/context/schema_dict_status.json` | 8.690 colunas `nao_verificado` — **candidatas**, não gotchas: entram só depois de medidas |

## Fases

**Fase 0 — mecanismo, com um arquivo só.** Schema, loader, o bloco em
`describe_table`, e `docs/context/gotchas/br_ms_sim.yml`. O teste que decide:
rodar a pergunta 1 com o `pi_prompt.md` **sem** o parágrafo do `causa_basica`.
Se ainda devolver 789, o mecanismo substituiu o hardcode. Se voltar a 749, a v2
estava acertando por memorização e o desenho não se sustenta.

**Fase 1 — colher o que já foi medido** nos arquivos da tabela acima. Estimativa
~10 datasets. Nada escrito por LLM sem `verificado`.

**Fase 2 — medição estratificada, ~75 min.** 20 perguntas de
`tasks/douradas_perguntas.json`: 10 em datasets **com** gotcha e 10 em datasets
**sem**. O segundo grupo é o controle, e é a única coisa que separa "o mecanismo
funciona" de "a resposta foi escrita no prompt" — que é justamente o que o 5/5
atual não consegue dizer.

**Fase 3 — rodada completa do golden set.** 193 perguntas × 3,8 min ≈ **12,2 h**,
estritamente sequencial (`-np 1`; rodar em paralelo disputa o mesmo
`llama-server` e corrompe o tempo, ver `harness/README.md`). Trabalho de uma
noite, não checagem.

**Fase 4 — só então** considerar promover a `explain_dataset` como ferramenta
própria, se a lista por dataset ficar grande a ponto de repeti-la por tabela
custar mais que uma chamada separada.

## Riscos

- **A sobre-especialização muda de lugar, não some** — sai do prompt e entra no
  YAML. O grupo de controle da Fase 2 é a única defesa.
- **Gotcha escrita por LLM é asserção sem medição.** `verificado` é o portão;
  sem ele o arquivo vira folclore com aparência de dado.
- **A resposta de `describe_table` cresce.** Ela já tem teto de 150 colunas; o
  bloco novo precisa de teto próprio.

## O que este plano decide NÃO fazer

**Não renomear colunas para rótulos mais explícitos.** Considerado e descartado
na mesma sessão, por quatro motivos: (1) a falha medida não foi de legibilidade —
`causa_basica` e `circunstancia_obito` são dois nomes claros, e o modelo errou
porque os dois são plausíveis, de modo que um rótulo mais explícito
(`tipo_de_morte_violenta`) teria **aumentado** a confiança na coluna errada;
(2) o nome da coluna é a volta para a documentação do órgão, e "conferir na
fonte" só funciona enquanto o nome bate; (3) o espelho é re-sincronizado da
origem, e uma camada de renome precisa de remapeamento a cada sync; (4) são
28.263 colunas, mais tudo que é chaveado pelo nome real — `bridges.yaml`,
`metrics.yaml`, `join_keys.md`, o corpus doc2query de 6.464 perguntas, as SQL
conferidas de `docs/respostas.md`. O que falta de verdade não é nome melhor: é
**descrição nenhuma** — `describe_table` diz isso na própria docstring ("Column
descriptions are not available: the mirrored schema carries only name and type"),
e uma varredura em `basedosdados-schema.json` acha `description`/`descricao` em
quantidade desprezível. Importar as descrições que a origem já publica é aditivo,
chaveado pelo nome original, e não quebra nada — mas é outro plano.

## Pendência de arrumação

`pi_prompt.md` está na raiz do repo, **fora do controle de versão**, hoje na
versão pt-BR/Gemma. A versão em inglês (genérica, para modelo capaz) só existe
no scratchpad da sessão, que não é durável. Decidir se uma das duas — ou as
duas — entram no repo antes de a sessão fechar.
