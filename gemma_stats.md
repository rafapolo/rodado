# Gemma 4 26B-A4B no beelink — benchmark medido

Medição real de `gemma-4-26B-A4B-it-qat` (q4_0) rodando em CPU no beelink.
Data: 2026-09-01. Todos os números abaixo são **medidos**, salvo onde marcado como estimativa.

## Máquina

| Item | Valor |
|---|---|
| CPU | AMD Ryzen 7 5800H (Zen 3), 8 núcleos físicos / 16 threads |
| ISA | AVX2, FMA, BMI2 — **sem AVX-512** |
| Cache | L2 4 MiB (8×512 KiB), L3 16 MiB |
| RAM | 27 GiB, DDR4-3200 dual-channel |
| **Banda de memória medida** | **38,1 GB/s leitura** / 21,5 GB/s copy (74% do teórico de 51,2) |
| GPU | Radeon Vega (Cezanne iGPU) — sem CUDA; RADV/Vulkan instalado, não testado |
| SO | Ubuntu 26.04 LTS, kernel 7.0.0-27-generic |
| Disco | NVMe, 336 GB livres |

Banda medida com benchmark OpenMP próprio (leitura sequencial de 1 GiB, 16 threads, melhor de 5).

## Modelo

| Item | Valor |
|---|---|
| Arquivo | `google/gemma-4-26B-A4B-it-qat-q4_0-gguf` → `gemma-4-26B_q4_0-it.gguf` |
| Tamanho | 14.439.363.584 bytes (13,43 GiB) |
| Arquitetura | `gemma4` MoE — 128 experts, ~4B ativos por token |
| Params | 25,23 B |
| Camadas | 30 · hidden 2816 · janela deslizante 1024 · contexto 262K |
| Quantização | q4_0 **QAT** (treinado com a quantização no laço) |

Escolhido o QAT oficial do Google em vez do `UD-Q4_K_XL` da unsloth por dois motivos que
apontam pro mesmo lado: q4_0 é o formato-alvo do treino QAT (qualidade), e tem o
desempacotamento mais simples com caminho de repack AVX2 no llama.cpp (velocidade).

## Build

```
llama.cpp build 8887a48 (2026-09-01)
cmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON -DLLAMA_CURL=OFF -DGGML_BACKEND_DL=OFF
GCC 15.2.0, -march=native (→ znver3)
```

Instalado em: `~/llama.cpp`, modelo em `~/llm`, cmake 3.31.6 standalone em `~/opt` (symlink `~/bin/cmake`).

## Condições

- Governor `performance` + EPP `performance` nos **16/16** cores (verificado core a core).
  Antes estava `powersave`/`balance_performance`.
- Sem carga concorrente: nenhum DuckDB rodando, sem throttle térmico.
- `--mlock` **não usado** — `ulimit -l` é 8 MB e travar 13,4 GiB exige root.

---

## Resultado 1 — varredura de threads

`llama-bench -p 512 -n 128 -r 5`

| Threads | pp512 (t/s) | tg128 (t/s) |
|---|---|---|
| 4 | 40,99 ± 0,28 | 15,69 ± 0,49 |
| 6 | 57,31 ± 1,09 | 15,35 ± 0,22 |
| **8** | **70,42 ± 2,95** | **14,86 ± 0,23** |
| 12 | 56,52 ± 0,31 | 14,74 ± 0,71 |
| 16 | 47,68 ± 10,34 | 10,26 ± 6,27 |

### Achado principal: usar todos os 16 threads é a pior configuração

Contra 8 threads, os 16 dão **-32% no prefill e -31% na geração**, com desvio-padrão
~10x maior (±0,23 → ±6,27). Consistente em duas baterias independentes.

Causa: os 8 núcleos físicos já saturam a banda de memória sozinhos. Os 8 threads
lógicos do SMT não acrescentam banda — só disputa por porta de load/store e por L2.
Numa carga limitada por memória, SMT é puro custo.

**Ótimo: `-t 8`.** Threads 4–6 dão geração marginalmente melhor (15,7 vs 14,9) mas
custam muito prefill (41 vs 70).

## Resultado 2 — números finais em `-t 8`

| Teste | t/s |
|---|---|
| pp512 | 70,42 ± 2,95 |
| pp4096 (prompt agêntico) | 54,05 ± 0,71 |
| tg128 | 14,83 ± 0,02 |
| tg128 @ profundidade 4096 | 11,03 ± 0,42 |

A geração cai 26% com 4K de contexto no KV. A janela deslizante de 1024 do Gemma 4
segura bem — degrada menos que uma arquitetura de atenção plena.

## Resultado 3 — KV quantizado (inconclusivo)

| Config | pp512 | tg128 |
|---|---|---|
| KV f16, t=16 | 47,68 ± 10,34 | 10,26 ± 6,27 |
| KV q8_0, t=16 | 48,47 ± 2,86 | 12,30 ± 1,30 |

Só medido em 16 threads, onde o ruído é de ±6 — a diferença está dentro da barra de erro.
**Não conclusivo.** Em contexto curto o KV é pequeno demais pra importar; só vale
reavaliar acima de ~32K.

---

## Tempo real de resposta (derivado dos números de t=8)

| Cenário | Prompt | Resposta | Prefill | Geração | Total |
|---|---|---|---|---|---|
| Pergunta solta | 50 tok | 150 tok | 0,7 s | 10 s | **~11 s** |
| Colar uma página | 1.000 tok | 400 tok | 15 s | 29 s | **~44 s** |
| Resposta longa | 500 tok | 2.000 tok | 7 s | 2min14 | **~2 min 40** |
| Agêntico | 8.000 tok | 600 tok | 2min28 | 55 s | **~3 min 35** |

O prefill é custo por prompt e cresce com a entrada; a geração cresce com a saída.
Num loop de ferramenta o prefill é pago **a cada rodada** — é ele que decide viabilidade agêntica.

## Como rodar

```bash
~/llama.cpp/build/bin/llama-server -m ~/llm/gemma-4-26B_q4_0-it.gguf \
  -t 8 -c 8192 --host 0.0.0.0 --port 8080
```

```bash
# rebench
~/llama.cpp/build/bin/llama-bench -m ~/llm/gemma-4-26B_q4_0-it.gguf -p 512 -n 128 -t 8 -r 5
```

---

## Ressalvas

**Disputa de page cache com o DuckDB.** Durante o bench o `buff/cache` caiu de 23 GiB
para 12 GiB — os 13,4 GiB do modelo despejaram os parquet do mirror. As primeiras
queries depois de usar o LLM ficam lentas até o cache reaquecer. Se virar `llama-server`
permanente, é uma troca consciente: velocidade do DuckDB por velocidade do LLM.

**Governor ficou em `performance`.** Voltar exige sudo:
`sudo cpupower frequency-set -g powersave`

**iGPU não testada.** RADV/Vulkan está instalado (`libvulkan_radeon.so`, `radeon_icd.json`).
A Vega compartilha a mesma DDR4, então a geração (limitada por banda) não deve melhorar —
mas o prefill é limitado por FLOPs e é o gargalo do caso agêntico. É o único ganho
plausível que resta.

## Comparação com Bonsai 27B (1-bit)

Estimativas para o Bonsai neste mesmo hardware — **não medidas**, escaladas da banda de 38,1 GB/s:

| | Gemma 4 26B-A4B (medido) | Bonsai 27B Q1_0 (estimado) |
|---|---|---|
| Disco | 13,43 GiB | 3,79 GB |
| Lido por token | ~2,2 GB (só experts ativos) | ~3,6 GB (denso) |
| Geração | **14,83 t/s** | ~4–5 t/s |
| Prefill 512 | **70,42 t/s** | ~10 t/s |
| Qualidade | QAT, perda mínima | ~89,5% do FP16 |

MoE ataca banda **e** FLOPs (expert desligado não gasta nenhum dos dois); quantização
de 1 bit ataca só bytes, e o prefill continua sendo 27B de contas. Por isso o Gemma
ganha em ambos os eixos aqui, apesar de ocupar 3,5x mais disco.
