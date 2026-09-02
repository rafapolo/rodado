# LFM2.5 + DSpark substituiria o Gemma 4 no harness?

> Aberto em 2026-09-02, a pedido do rafael, a partir de
> https://www.liquid.ai/blog/lfm2.5-dspark
>
> **Resposta curta: não como está — mas há um experimento que vale, e não é o
> que o nome sugere.** Nada abaixo foi rodado no beelink; os números do Gemma
> são medidos (ver `gemma_stats.md`), os do LFM2.5 são do anúncio da Liquid.

## O que o DSpark é, e o que não é

DSpark **não é um modelo**. São checkpoints de rascunho (~300M) para
**decodificação especulativa**: um modelo leve propõe tokens e o modelo alvo
verifica vários de uma vez, cortando latência na fase limitada por memória.

Consequência que decide a pergunta: **o rascunho só serve ao alvo para o qual
foi treinado.** Os DSpark da Liquid são para LFM2.5-1.2B, 2.6B e 8B-A1B. Não
existe DSpark para o Gemma 4, então "usar DSpark" aqui significa **trocar o
modelo inteiro**, não acelerar o que já temos.

Arquitetura do rascunho: pilha de 5 camadas, projeção de estado oculto, cabeça
de cadeia de Markov e cabeça de confiança.

## Os candidatos

| Modelo | GGUF | Arquitetura | Contexto |
|---|---|---|---|
| **Gemma 4 26B-A4B** (atual) | 13,43 GB q4_0 QAT | MoE 128 experts, ~4B ativos | 262k |
| LFM2.5-8B-A1B | 9,01 GB Q8_0 | MoE 32 experts, 4 ativos (~1B) | 128k |
| LFM2.5-2.6B | 2,87 GB Q8_0 | densa | — |
| LFM2.5-2.6B-DSpark | 0,20–0,66 GB | rascunho, não roda sozinho | — |

Ganhos anunciados pela Liquid: 2,27–2,87x no M4 Max, 3,18x no H100, e **57% de
redução de latência em function calling** — este último é o número relevante,
porque o harness é function calling do começo ao fim.

## Por que não trocar

**O gargalo aqui não é velocidade, é acerto de SQL.** Medido hoje:

- Escolha de dataset entre 212: **97,8%** com few-shot no prefixo.
- O modelo escreve SQL multi-CTE ligando 3 datasets, com as chaves certas.
- E ainda assim erra silencioso: `causa_basica BETWEEN 'X60' AND 'X84'` deu 726
  em vez de 789 — 8% a menos, número plausível. O portão pegou; o modelo, não.

Esse é o tipo de erro que **piora** com modelo menor. LFM2.5-8B-A1B ativa ~1B de
parâmetros por token contra ~4B do Gemma; 2,6B denso é menor ainda. Trocar
26B-A4B por 8B-A1B para ganhar 2x de velocidade, num harness onde o custo de um
número errado é uma análise publicada errada, é trocar na direção errada.

**E a velocidade já tinha 4,4x parado na mesa, de graça.** O laço do dsh gastava
883 s por pergunta porque o raciocínio do Gemma estava ligado sem eu perceber —
o `reasoningEfforts: false` do dsh declara o modelo como não-raciocinante para o
harness, mas não manda nada que desligue o thinking no llama.cpp. A correção é
uma flag no servidor:

```
llama-server ... --chat-template-kwargs '{"enable_thinking":false}'
```

Medido: **20,9 s → 4,7 s** por turno de tool calling, com o tool call intacto.
Isto é maior que os 2,27–2,87x do DSpark e não custa nenhuma perda de qualidade.

## O experimento que vale

O DSpark do Gemma não existe, mas **a especulação não exige um rascunho
treinado sob medida** — o llama.cpp aceita qualquer modelo compatível como
`--model-draft`. Duas ideias, em ordem de esforço:

1. **Rascunho pequeno para o Gemma 4.** Testar `gemma-4-E2B-it` (o tier mobile da
   mesma família, mesmo tokenizador) como `--model-draft` do 26B-A4B. Se o
   tokenizador casar, é uma flag. O ganho de especulação vem da taxa de aceitação,
   que é alta quando os dois modelos são da mesma família.
2. **Medir LFM2.5-8B-A1B como apurador**, não como redator. Se ele escolher
   dataset e escrever SQL a 90%+ do Gemma pela metade do tempo, vira o motor da
   etapa cara (muitas consultas, muita iteração) com o Gemma só na redação. Mas
   isso depende de medir, e o conjunto de avaliação já existe:
   `bun harness/avalia_datasets.ts --fewshot`.

## O que fazer com isto

Nada agora. O caminho crítico é medir o harness atual ponta a ponta contra os 53
casos com `n` conferido. Trocar de modelo antes de ter esse número é otimizar sem
linha de base.

Reabrir se: (a) a taxa de acerto do Gemma travar num teto que velocidade
resolveria, ou (b) o item 1 acima (rascunho E2B) mostrar ganho — é barato e não
troca o modelo que responde.

## Fontes

- [LFM2.5-DSpark](https://www.liquid.ai/blog/lfm2.5-dspark) — anúncio
- [LFM2.5-8B-A1B-GGUF](https://huggingface.co/LiquidAI/LFM2.5-8B-A1B-GGUF)
- [LFM2.5-2.6B-DSpark-GGUF](https://huggingface.co/LiquidAI/LFM2.5-2.6B-DSpark-GGUF)
- `gemma_stats.md`, `harness/README.md` — as medições do que está rodando
