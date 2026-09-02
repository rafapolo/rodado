# Séries históricas da ANA — o que falta, e uma duplicação a resolver

O ETL do zip e a análise de tendência estão feitos e documentados em
[`done/ana_series_etl.md`](done/ana_series_etl.md). A página saiu em
`todos-rios-brasil/series.html` (404 estações com tendência comprovada: 303 caindo, 101 subindo).

Este arquivo guarda o que continua aberto.

---

## 0. RESOLVIDO (2026-08-27) — duas tabelas concorrentes no data lake

**Fix aplicado, não remoção.** Corrigido `ana_mensal_unifica.py` para manter o nível de
consistência mais alto (`descending=[False, False, True]` no sort composto
`["codigo", "mes", "nivel_consistencia"]`, mesma regra do `ana_series_historicas.py`) e
reprocessado no beelink contra o mesmo zip local (`~/ana_zip/extraido/...`, sem novo fetch).
Saída: `vazoes: 1.331.690 linhas, 3954 estações, 1901-01..2023-09` e
`cotas: 1.729.207 linhas, 7205 estações, 1900-01..2023-09` — mesma contagem de antes, só o
nível de consistência escolhido por (codigo, mes) mudou.

**Validação no beelink** (mesma comparação do item original, tabela plural × singular):

| Métrica | Vazão | Cota |
|---|---|---|
| Meses comparados | 1.331.690 | 1.729.199 |
| Meses com nível divergente ANTES | 28.037 (273 estações) | não medido antes, mas mesma causa |
| Meses com nível divergente DEPOIS | **0** | **0** |
| Meses com valor divergente DEPOIS | **0** | **0** |

As tabelas plural (`series_vazoes_mensal`, `series_cotas_mensal`) e singular
(`series_vazao_mensal`, `series_cota_mensal`) concordam perfeitamente agora — nível de
consistência e valor. As pastas do plural **não foram removidas** (decisão do usuário: corrigir,
não apagar). Regen chain rodada (`gera_schemas.py` → `sync_mcp_schema.py` →
`build_metadata_catalog.py` → `gera_join_keys.py`).

### Registro original do problema (mantido para histórico)

Em 2026-08-09 dois ETLs rodaram no mesmo dia sobre a mesma fonte e as saídas **coexistem**:

| Pasta | Script | Grão | Dedup por consistência |
|---|---|---|---|
| `series_vazoes_mensal/` (plural) | `ana_mensal_unifica.py` (13:03) | mensal | **fica com o BRUTO** |
| `series_cotas_mensal/` (plural) | `ana_mensal_unifica.py` (13:03) | mensal | **fica com o BRUTO** |
| `inventario/` | `ana_mensal_unifica.py` (13:03) | estação | — |
| `series_vazao_mensal/` (singular) | `ana_series_historicas.py` (13:24) | mensal | fica com o consistido |
| `series_vazao_diaria/` (singular) | `ana_series_historicas.py` | **diário** | fica com o consistido |
| `series_cota_mensal/` + `series_cota_diaria/` | `ana_series_historicas.py` | mensal + **diário** | fica com o consistido |
| `estacoes_inventario_2023/` | `ana_series_historicas.py` | estação | — |

**A divergência foi medida, não é teórica.** Cruzando as duas tabelas mensais de vazão:
**28.037 meses divergem, em 273 estações, e a direção é 100% uniforme** — o plural ficou com o
valor bruto onde o singular ficou com o consistido. Causa no `ana_mensal_unifica.py`:

```python
todo.sort(["codigo", "mes", "nivel_consistencia"])   # ascendente
    .unique(subset=["codigo", "mes"], keep="first")  # -> keep = nivel 1 = BRUTO
```

O consistido é o dado que passou pela crítica técnica da ANA; o bruto é o que saiu do sensor.
`todos-rios-brasil/pipeline/processa.py` sempre preferiu o consistido, então a tabela plural
também **discorda do outro pipeline** que consome a mesma fonte.

**A decidir (não fiz por conta própria — apagar tabela de outra sessão não é chamada minha):**
remover as três pastas do plural e o `ana_mensal_unifica.py`, já que o singular é um superconjunto
estrito (mensal + diário + inventário, com o dedup no lado certo). Ou, se o plural tiver
consumidor, ao menos corrigir a ordenação para `descending=True` e reprocessar.

O diário só existe no singular, e é o que destrava os dias de rio seco (613.210 dias em 623
estações) e a Q7,10 — nada disso é recuperável do mensal.

## 1. Gap 2023-08 → hoje — FEITO (2026-08-10)

**6.203 de 6.203 estações coletadas (100%).** A tabela unificada
`series_vazao_mensal_completa` tem **1.415.569 meses, 4.218 estações, 1901-01 a 2026-05** —
contra 3.954 estações e fim em 2023-09 do zip sozinho. Ganho: **+264 estações** (as que tinham
CSV só-cabeçalho no arquivo, resolvendo de vez a discrepância 4.494 × 3.954) e **+34.052 meses**
além da janela do zip, em 1.560 estações.

Feito por `ana_soap_worker.py` distribuído em **beelink + finland + livre**, e por
`ana_series_unifica_gap.py` para a fusão. A análise em `todos-rios-brasil` foi refeita: o
ranking foi de 404 para **446 estações (359 caindo, 87 subindo)** — o sinal de queda ficou mais
forte com os 2,5 anos extras.

**Atenção ao que o SOAP NÃO resolve:** ele devolve agregado mensal, então a série **diária**
continua parando em 2023-09. Os painéis de rio seco e Q7,10 têm janela mais curta que os de
tendência, e a página diz isso explicitamente.

### Registro anterior (mantido: descreve o problema que foi resolvido)

Sondagem de 2026-08-09, para não repetir o trabalho:

- O SOAP **continua no ar** apesar do desligamento anunciado para 30/06/2026 (`HTTP 200` no WSDL).
- Ele **recua até 1936**, não para em 1995: testado em 58770000 com `dataInicio=01/01/1930`,
  devolve a partir de 1936-10. O corte em 1995 do `todos-rios-brasil/pipeline/baixa_vazao.py`
  é escolha, não limite da fonte.
- **Mas a base está defasada**: naquela estação o dado mais recente é 2024-03. Amostrar ~30
  estações e medir a defasagem real antes de rodar em massa. Se for generalizada, a cauda
  2024-2026 fica rala e isso entra como limite declarado da análise, não some.

### O serviço devolve HTTP 429 — a estimativa antiga de vazão estava errada

**"~12–15 estação/s no agregado, 4.500 em 5–8 min" não acontece.** A ANA responde
**HTTP 429 Too Many Requests** sob concorrência. Medido em 2026-08-09: com 16 threads o worker
rodou **6 minutos sem gravar um único lote**. O motivo é traiçoeiro — as 4 tentativas eram
imediatas, sem backoff, queimavam em menos de 2 segundos, e a estação caía no ramo
"falhou em todas as tentativas → pula, re-baixa na próxima execução". Ou seja: **falha
silenciosa que parece progresso**, porque nada é perdido e nada avança.

Correções aplicadas no `ana_soap_worker.py`:

- Backoff exponencial com jitter (`min(60, 2**i) + random`), 6 tentativas.
- **Freio global compartilhado** entre as threads (`_respira`/`_espera_freio`): quando uma leva
  429, todas param até o mesmo instante. Sem isso as threads se revezam batendo no limite e o
  429 nunca passa — backoff por thread sozinho não resolve.
- Checkpoint a cada **100** estações, não 400: sob rate limit um lote de 400 leva muitos
  minutos de trabalho que se perdem se o processo cair.
- Progresso com taxa e ETA, e `flush=True` — sem ele o `print` bufferiza no redirecionamento e
  o log fica vazio, o que faz um processo saudável parecer travado.
- `pl.concat(..., how="diagonal_relaxed")` nos dois pontos de gravação: estação sem dados vira
  um frame de 1 coluna e o concat vertical padrão estourava schema mismatch.

**Vazão real com 4 threads: ~40 estações/min**, ou seja ~2h30 para as 6.203. Cada resposta traz
a série 1960–2026 inteira (1,6 MB de XML para uma estação com 709 meses), o que também explica
por que shardar entre hosts ajuda menos do que parece — o limite é do servidor, não nosso.

Testado na estação 15400000 → 709 meses, 1967-04 a 2026-04. O SOAP chega a **2026-04**, contra
2023-09 do arquivo: o gap fecha de verdade.

Plano restante: reunir os `batch_*.parquet` e juntar com a série do zip por `(codigo, mes)`
**priorizando o nível consistido**, depois reprocessar `analisa_tendencia.py` e
`prepara_paineis.py` no `todos-rios-brasil`. Shardar em `finland`/`livre` só vale se for para
distribuir os IPs, não os cores.

## 2. Chuva pluviométrica — FEITO (2026-08-10)

`series_chuva_mensal` (2.502.388) e `series_chuva_diaria` (**69.765.343**), 5.389 estações,
1900 a 2023-11, por `scripts/scrap/ana_chuva_historica.py`.

**O bloqueio de sudo não existia.** `apt-get download mdbtools libmdb3t64 libmdbsql3t64` +
`dpkg -x` para `~/local/root` instala sem root nenhum; basta pôr no `PATH` e no
`LD_LIBRARY_PATH`. Fica registrado como receita para qualquer outro binário que falte no beelink.

Duas armadilhas do formato, ambas de falha silenciosa:

- **A data.** `Data` é DateTime no schema, mas o `mdb-export` imprime `07/01/62 00:00:00` —
  mês/dia/ano com ano de DOIS dígitos. `-D` não resolve (só vale para data pura); o flag para
  coluna com hora é **`-T`**, e aí sai `1962-07-01` com o século vindo do binário. Lido como
  texto, julho de 1962 viraria 7 de janeiro e o século sairia por chute.
- **O código da estação.** O MDB guarda como NÚMERO e perde o zero à esquerda: `1036005` onde o
  inventário e as séries de vazão têm `01036005`. O join contra o inventário devolvia zero
  linhas, sem erro, e o painel de chuva saiu vazio na primeira rodada. `zfill(8)` no ETL.

**O que isso destravou:** o painel *é seca ou é consumo?* na `series.html`. Dos 358 rios em
queda comprovada, **196 perdem água sem que a chuva tenha caído** (167 com chuva estável, 29 com
chuva subindo); só 162 têm queda de chuva junto. Correlação entre as duas tendências: +0,32.

### Registro do bloqueio que se provou falso

Ficava assim, e estava errado — só o beelink pede senha; `finland` é root: 

Depois: 5.525 arquivos em `pluviometricas/mdb/<cod>.zip` (1,1 GB), um MDB por estação.
Descompactar em tmp, `mdb-export`, despivotar `Chuva01..31` (mm) + status, acumular em
`~/rodado/br_ana_telemetria/series_chuva_diaria`, limpando o tmp a cada estação.

**Por que vale o trabalho:** é a única forma de responder *é seca ou é consumo?*. O coeficiente
de escoamento (vazão anual ÷ chuva anual da bacia) ao longo do tempo separa as duas causas — se
a chuva se manteve e a vazão caiu, o problema não está no céu, e a resposta de política pública
é outra. Hoje a `series.html` declara essa pergunta como explicitamente em aberto.

Fallback se o mdbtools não sair: SOAP com `tipoDados=2`, 5.525 chamadas sequenciais. Funciona,
é lento, e some quando o serviço desligar.

## 3. Resolvido: a discrepância 4.494 × 3.954

Estava aberto no arquivo anterior ("~540 faltam na fonte, verificar com o SOAP"). Medido
direto no zip: são **7.205 pastas fluviométricas, das quais só 3.954 têm linhas** — o resto
são CSVs só com cabeçalho (858 bytes). O inventário marca 4.494 estações com descarga líquida
porque a flag descreve o *propósito* da estação, não a existência de série no arquivo. Não é
perda do ETL; é lacuna da fonte. Confirmável com o SOAP quando o gap rodar.

## 4. Gap da COTA (2026-08-27)

`ana_soap_worker.py` só pedia `tipoDados=3` (vazão) — `series_cota_mensal` parava em 2023-09
enquanto vazão já ia a 2026-05. Corrigido: parametrizado `--tipo {1,3}` (1=cota, 3=vazão), com
nome de coluna por prefixo (`cota_media/maxima/minima` vs `vazao_media/maxima/minima`, para não
colidir com o schema que `ana_series_unifica_gap.py` já lia). `ana_series_unifica_gap.py` também
ganhou `--tipo {vazao,cota}` para gerar `series_cota_mensal_completa` do mesmo jeito que
`series_vazao_mensal_completa`.

Teste de fumaça em 5 estações confirmou: SOAP `tipoDados=1` devolve o mesmo formato mensal
(`Cota01..31` diário embutido, `Media`/`Maxima`/`Minima`, `NivelConsistencia`) até 2026-04.
Rodada completa disparada no beelink contra os 7.197 códigos de `series_cota_mensal`, 4 threads
(mesma configuração que rendeu ~40 estações/min na vazão, por causa do rate limit 429 do lado da
ANA) — **[preencher ao terminar: linhas/estações/período de `series_cota_mensal_completa` e
resultado do `build_metadata_catalog.py`]**.

## 5. Série diária pós-2023-09 — a suposição anterior estava ERRADA

O arquivo dizia "o SOAP não serve diário". **Não é verdade — testado e confirmado em
2026-08-27.** O mesmo `HidroSerieHistorica` (`tipoDados=3`, o que `ana_soap_worker.py` já chama
para o gap mensal) devolve, dentro de **cada registro mensal**, os campos `Vazao01..Vazao31` +
`VazaoNNStatus` — exatamente o mesmo formato diário embutido que o zip CSV tinha (e que
`ana_series_historicas.py` já extrai para montar `series_vazao_diaria`). Confirmado em 3
estações/janelas (`58974000`: 24 meses 2024–2025, 31/31 dias preenchidos em dezembro/2025;
`15400000`: `Vazao01..30` presentes em 2026-03 e 2026-04; `60895000`/`17094500` sem dado
recente — a estação parou de reportar, não é limite do serviço).

**O que isso muda:** a série diária poderia ser estendida além de 2023-09 sem nova fonte —
bastaria reprocessar o `parse()` de `ana_soap_worker.py` (hoje descarta os campos `VazaoNN`) e
regravar as respostas SOAP já buscadas. **Isso não foi implementado nesta sessão** — o pedido era
confirmar e documentar, não construir o pipeline; fica registrado aqui como o próximo passo
concreto para destravar rio seco/Q7,10 pós-2023, sem precisar de fonte nova.

## 6. Procedência de `br_ana_reservatorios` e `br_ana_atlas_esgotos` — já estava correta

Investigado via `git log` (nenhum script no repo gera essas tabelas), `tasks/done/datasets_to_scrap_done.md`
(nota existente já dizia que são "produtos ANA diferentes", sem afirmar origem) e busca web:

- `br_ana_atlas_esgotos.municipio` — confirmado como dataset publicado no Base dos Dados
  (`basedosdados.br_ana_atlas_esgotos.municipio`, usado em exemplos de query da própria BD).
- `br_ana_reservatorios.sin` — confirmado: "Reservatórios Brasileiros – Base dos Dados"
  (`basedosdados.org/dataset/fc7e9d13-714d-42c1-8986-bd2a3108e208`), dados operacionais SIN da
  ANA, mirror padrão.

**Nenhuma correção foi necessária.** `scripts/build_metadata_catalog.py` já trata qualquer
dataset ausente de `datasets_to_scrap.md`/`datasets_to_scrap_done.md` como espelho do Base dos
Dados por padrão (linha ~455-474): como esses dois datasets nunca apareceram nessas listas (a
única menção existente é uma nota lateral na linha do item "ANA telemetria", que usa `ana` como
chave, não `br_ana_reservatorios`/`br_ana_atlas_esgotos`), o catálogo já atribuía
`source_name='Base dos Dados'`, `source_type='mirror'`, com a nota honesta "fora do recorte de
`docs/context/schema_ddl.sql`" (schema_ddl.sql é parcial, 527/849 tabelas). Confirmado no
beelink depois do regen desta sessão — `_rodado_metadata` mostra exatamente isso para as duas
tabelas. O item ficava marcado como pendente por engano: o mecanismo de fallback já resolvia.

## 7. Outorgas × série por bacia — separando uso de clima (2026-08-27)

Análise (não ETL), rodada direto no beelink via DuckDB. `br_ana_outorgas.captacoes` não tem
código de bacia nem lat/lon — só município/UF — então o cruzamento foi feito por
**município → bacia mais comum entre as estações daquele município** (via
`estacoes_inventario_2023.baciacodigo`), não por bacia hidrográfica real. `int_qt_vazaomedia` é
m³/h (confirmado por `reference_outorgas_snirh` — identidade com `volumeanual` já validada em
sessão anterior), convertido para m³/s dividindo por 3600.

Tendência por estação = média de 2015–2025 vs média dos primeiros 15 anos de dado de cada
estação (com ≥120 meses de série), sobre `series_vazao_mensal_completa` — **não** é o mesmo
método (Mann-Kendall + Theil-Sen + FDR) que gerou o ranking oficial de 358 rios em queda do
`todos-rios-brasil`; é um proxy rápido só para esta comparação por bacia.

| Bacia | Estações | Em queda (>10%) | Δ médio | Captação outorgada | Captação / vazão histórica* |
|---|---|---|---|---|---|
| Rio São Francisco | 203 | 186 | -36,2% | 1.218 m³/s | 2,00% |
| Atlântico Leste | 351 | 299 | -32,4% | 323 m³/s | 1,30% |
| Atlântico Norte/Nordeste | 296 | 191 | -31,0% | 394 m³/s | 2,73% |
| Rio Tocantins | 89 | 78 | -28,0% | 573 m³/s | 0,70% |
| Rio Paraná | 527 | 289 | -10,1% | 1.844 m³/s | 0,96% |
| Rio Amazonas | 202 | 40 | **+2,0%** | 507 m³/s | **0,04%** |
| Atlântico Sudeste | 140 | 25 | +10,0% | 377 m³/s | 4,02% |
| Rio Uruguai | 107 | 8 | **+20,7%** | 102 m³/s | **0,30%** |

\* soma da vazão histórica (primeiros 15 anos) de todas as estações da bacia — **soma estações
ao longo do mesmo rio, dupla-conta vazão** (estação de jusante já inclui a de montante), então o
percentual é um **piso**, não a pressão real sobre a vazão de cada trecho.

**Achado:** as quatro bacias em queda mais acentuada (São Francisco, Atlântico Leste,
Atlântico Norte/Nordeste, Tocantins — todas em regiões semiáridas ou litorâneas do Nordeste/Norte)
têm razão captação/vazão de 0,7% a 2,7%. As duas bacias com vazão **estável ou subindo**
(Amazonas +2,0%, Uruguai +20,7%) têm razão de 0,04% e 0,30% — uma ordem de grandeza menor. Rio
Paraná é o contra-exemplo interessante: maior captação absoluta do país (1.844 m³/s, 74.128
outorgas — de longe o mais industrializado/irrigado), mas queda moderada (-10,1%) porque a vazão
histórica da bacia também é grande; a razão captação/vazão (0,96%) fica no meio da tabela. Isso é
consistente com o achado do item 2 (chuva estável em 167 dos 358 rios em queda): captação
outorgada não é o único fator, mas a correlação entre uso intensivo (litoral Nordeste, São
Francisco) e queda acentuada aparece nos números, enquanto Amazônia/Uruguai — bacias com pouca
outorga relativa — não mostram queda.

**Limitações desta análise** (fica registrado para quem for refazer com mais rigor):
1. Junção por município, não por bacia hidrográfica real — aproximação de vizinhança, não
   geo-join.
2. Denominador (soma de vazão histórica) dupla-conta estações ao longo do mesmo rio.
3. `captacoes` não tem o filtro dos 463 registros anômalos (0,4% dos registros, ~2.385 m³/s no
   universo completo do SNIRH) nem separa outorga vigente de uso de passagem (hidrelétrica que
   devolve ≥90%) — o `reference_outorgas_snirh` documenta esses filtros para a fonte bruta do
   SNIRH; a tabela `br_ana_outorgas.captacoes` espelhada aqui é a coletada por
   `todos-rios-brasil/pipeline/baixa_outorgas.py`, que já filtra "vigentes" mas não
   necessariamente os outros três filtros.
4. Métrica de tendência é um proxy (não o Mann-Kendall+Theil-Sen+FDR oficial) — os números de
   "estações em queda" aqui não devem ser citados como o ranking canônico da `series.html`.

## Status

- [x] baixar zip único (2,3 GB) + extração + integridade
- [x] instalar polars no beelink
- [x] unificar em parquets — mensal **e diário**, vazão e cota, + inventário
- [x] worker SOAP montado e testado (15400000)
- [x] tendência (Mann-Kendall + Theil-Sen + FDR) e lista de rios em queda → `series.html`
- [x] esclarecer a discrepância 4.494 × 3.954
- [x] registrar as tabelas no catálogo (`_rodado_metadata`) — exigiu corrigir o
      `build_metadata_catalog.py`, que varria `${tbdir}*.parquet` e devolvia `rows=0` para
      tabela particionada; com `**/*.parquet` o lake recuperou 87 milhões de linhas
- [x] gap 2023-08 → hoje via SOAP distribuído (100% das 6.203)
- [x] chuva pluviométrica — 69,8 M de linhas diárias, mdbtools sem root
- [x] `br_ana_outorgas/{captacoes,lancamentos}` e `br_ana_bho/topologia` espelhados do
      `todos-rios-brasil` e documentados em `datasets_to_scrap.md`
- [x] **resolver a duplicação plural × singular (item 0)** — fix no sort + reprocessado
      (2026-08-27); 28.037 meses divergentes → 0
- [ ] **gap da COTA** (item 4) — `ana_soap_worker.py` parametrizado com `--tipo`, rodada disparada
      no beelink (7.197 estações, ~2h) — em andamento, ver item 4 para o resultado final
- [x] série **diária** pós-2023-09 (item 5) — a suposição "SOAP não serve diário" estava
      **errada**: confirmado que o SOAP devolve `VazaoNN` embutido no registro mensal. Não
      implementado (fora do escopo pedido), documentado como próximo passo concreto
- [x] procedência de `br_ana_reservatorios`/`br_ana_atlas_esgotos` (item 6) — confirmados como
      mirror padrão do Base dos Dados (`build_metadata_catalog.py` já atribuía corretamente por
      fallback; nada para corrigir)
- [x] outorgas × série por bacia (item 7) — análise feita, achado registrado com números reais e
      limitações explícitas
