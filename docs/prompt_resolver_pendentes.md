# Prompt — resolver as pendências de docs/respostas.md

> Não executar automaticamente. Este arquivo é o prompt a ser colado numa sessão
> (ou usado com `/loop`) quando alguém decidir de fato rodar as 180 perguntas
> pendentes. Gerado em 2026-08-24 a partir do estado de `docs/perguntas.md` e
> `docs/respostas.md` naquele momento.

---

## Prompt

Você vai resolver as pendências (`⏳`) de `docs/respostas.md`, cruzando com as
perguntas originais em `docs/perguntas.md`. Hoje há **180 itens pendentes**
(alguns `◐` parciais também merecem ser completados) espalhados pelos 43 temas
mais a seção multi-referência (M1–M5).

### Regras não-negociáveis (vêm do CLAUDE.md do projeto)

1. **Nunca BigQuery, GCP, `bq`, S3 ou o endpoint `db.xn--2dk.xyz`.** Toda query
   roda via `ssh beelink '~/bin/duckdb -json ~/rodado/basedosdados.duckdb'`,
   com `SET enable_progress_bar=false;` antes.
2. **Filtre por partição** (`ano`, `mes`, `sigla_uf`) em qualquer tabela
   grande — SIH, SIA, SINAN, CAGED, CGU servidores/cartão, PGFN, etc. têm
   centenas de milhões a bilhões de linhas.
3. **Nunca junte por `false_friends`.** Antes de escrever um `ON` à mão,
   consulte `docs/context/bridges.yaml` (ou as ferramentas MCP
   `resolve_join`/`explain_column`/`get_join_keys` se disponíveis) —
   `cnpj`, `valor`, `id_municipio` têm armadilhas documentadas ali.
4. **Valide cada resultado três vezes** antes de reportar: (1) diga a ordem de
   grandeza esperada, (2) sinalize qualquer linha fora dela, (3) confira a
   contagem por dois caminhos independentes. Só entra em `respostas.md` o que
   passa nas três.
5. Correlações são Pearson sobre agregados municipais (5.570 municípios) ou
   estaduais (27 UFs) — mantenha esse padrão para comparabilidade com A1–A16.
6. Preserve o formato exato já usado em `respostas.md`: código `T<tema>-<nº>`,
   selo `✅`/`◐`/`⏳`, métrica em negrito, `n`, referência cruzada `*(A됨N)*`
   quando a correlação também entra na tabela "Resultados transversais".

### Ordem sugerida de ataque

Vá tema por tema, na ordem de `perguntas.md`, mas dentro de cada tema resolva
primeiro os itens que dependem só de tabelas **já usadas** em A1–A16
(RAIS, SIM, SINASC, CAGED, TSE, PIB, Censo, PRODES, SEEG, PPM, Anatel IBC,
CNPJ) — são join barato, painel pronto. Deixe para o fim os que dependem de
tabelas nunca tocadas no painel atual (SICOR, SICAR, SNIS, SIOP, Transferegov,
CGU cartão/servidores, SINAN, SIH, SIA, CNJ, TCEs, ANP, IPCA, POF, CNPq,
COMEX, TRASE, geobr, ipea_avs, QUEIMADAS, INMET, ANA, MMA, Olympedia,
Poder360, PNS, PNADC, world_oecd_pisa) — cada uma dessas exige achar a tabela
certa com `search_tables`/`describe_table` antes de escrever a query.

Para cada pergunta pendente:

1. Releia o enunciado exato em `perguntas.md` (código `T<tema>-<nº>`) e a nota
   `(n=...)` que lista os datasets exigidos.
2. Confirme que as tabelas existem no beelink (`describe_table` ou
   `SELECT * FROM information_schema.tables WHERE table_name ILIKE '%...%'`).
3. Resolva os joins com `bridges.yaml`/`resolve_join` em vez de chutar
   coluna por nome igual.
4. Escreva a query com filtro de partição, rode via `ssh beelink`.
5. Se a pergunta pede correlação, calcule Pearson (`corr(x, y)`) sobre o nível
   certo (município ou UF) e registre `n`.
6. Se a tabela não existir no espelho hoje ou exigir pipeline dedicado
   (>1 bi linhas sem partição viável, ou requer normalização que não existe),
   mantenha `⏳` mas adicione uma frase objetiva do motivo — não invente dado.
7. Atualize a linha correspondente em `docs/respostas.md`: troque `⏳` por
   `✅` (ou `◐` se só parte do cruzamento saiu), com métrica, `n` e uma leitura
   de uma frase. Se o achado for forte (|r| ≥ 0,4) e transversal, adicione uma
   linha nova na tabela "Resultados transversais" com o próximo código livre
   (`A17`, `A18`, ...) e referencie com `*(AN)*` no final da entrada de tema.
8. Não toque em itens já `✅`. Não invente número — se a query não confirmar
   com folga o esperado, marque `◐` e explique a limitação em vez de forçar
   um `✅`.

### Casos que exigem cuidado extra (não são query simples)

- **T13 (Migração), T21 (Corrupção), T26 (Servidores)**: exigem agregação
  dedicada em tabelas de centenas de milhões de linhas (CAGED 232M,
  CGU servidores 852M). Não tente `SELECT *`; agregue direto no DuckDB com
  `GROUP BY` e filtro de ano antes de trazer qualquer linha para o cliente.
- **T23–T24 (Epidemiologia/SUS)**: SIH/SIA são bilhões de linhas — comece
  pela tabela de partição mais estreita possível (um `ano` + uma `sigla_uf`)
  para validar a query antes de rodar full-panel.
- **T34 (Atlas/geobr)**: exige funções espaciais (`ST_*`) — confirme que a
  extensão `spatial` do DuckDB está carregada no ambiente do beelink antes de
  tentar.
- **T05/T15/T29 (Câmara/Senado dados abertos)**: essas fontes normalmente não
  têm `id_municipio` direto — o join com TSE/Censo passa por normalização de
  nome do candidato/partido; documente a taxa de match.
- **Multi-referência M1–M5**: são cadeias de 3+ joins em cascata. Resolva
  primeiro os componentes isolados (já parcialmente em A1/A2/T37-1/T37-5) e só
  monte a cadeia completa depois que cada elo individual estiver validado.

### Time-boxing — encerrar bem antes de estourar o orçamento da sessão

Esta tarefa é grande demais para uma sessão só (180 itens, vários exigindo
tabelas nunca tocadas). Não tente terminar tudo de uma vez — monitore o
orçamento e pare de forma limpa bem antes de ficar sem tokens:

1. **Cheque o orçamento periodicamente**, não só no fim: a cada tema
   concluído (ou a cada ~15–20 min de trabalho), olhe o contador
   `<total_tokens>N tokens left</total_tokens>` que aparece nos
   `system-reminder` da própria conversa, e rode `/usage` como referência
   complementar (ele mostra o consumo agregado da conta/sessão, não só desta
   janela — útil para saber se está perto de um limite de plano além do
   limite de contexto).
2. **Defina uma reserva de segurança**: pare de puxar *itens novos* quando
   restar menos de ~20% do orçamento inicial da sessão (ou um valor absoluto
   folgado o bastante para escrever o resumo final + editar `respostas.md`
   sem cortar no meio). Não espere chegar a zero para reagir.
3. **Feche o item em andamento antes de parar** — nunca deixe uma query
   rodada sem registrar o resultado, nem uma edição de `respostas.md` pela
   metade. É melhor entregar um tema a menos do que uma entrada quebrada.
4. **Ao bater a reserva**, pare de abrir novas perguntas e escreva o estado:
   - `grep -o '⏳' docs/respostas.md | wc -l` para o número de pendências
     restantes.
   - Quantos itens viraram `✅`, quantos `◐`, e por quê os que continuam `⏳`
     (dado fora do painel vs. pipeline não construído vs. não chegou a vez).
   - Qual foi o **último tema totalmente processado** e qual seria o
     **próximo item a retomar** — para a próxima sessão não perder tempo
     recontextualizando nem repetir trabalho.
5. Se a tarefa for rodada via `/loop` (self-paced), use esse mesmo checkpoint
   como critério de `noop`/parada: ao invés de tentar espremer mais um tema
   quando o orçamento já está apertado, prefira fechar a sessão limpa e
   deixar o próximo `/loop` continuar de onde parou.
6. Não faça commit automático — pare para revisão do usuário antes de
   `git add`/`git commit`, mesmo ao encerrar por orçamento.
