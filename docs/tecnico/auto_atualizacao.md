# docs/tecnico/auto_atualizacao.md — como manter as 1.389 tabelas em dia

Irmão de [`housekeeping.md`](housekeeping.md): aquele é a checklist **depois**
de um dado novo entrar; este é como fazer o dado entrar de novo quando a fonte
anda, para todas as tabelas, com o máximo de paralelismo que o beelink e a cota
aguentam. Escrito em 2026-10-08, depois da rodada de 2026-10-07 que trouxe 205
tabelas novas e 2,1 bi de linhas do CNPJ e atualizou ~70 fontes raspadas. Tudo
que está como "medido" aqui foi medido nessa rodada.

## O que "atualizado" quer dizer no nosso catálogo

`_rodado_metadata.updated_at` é **quando nós regravamos a tabela pela última
vez**: data e hora do parquet mais novo dela em `~/rodado`. Muda no sync do
Base dos Dados, na raspagem e no gate de troca das fontes raspadas. (Até
2026-10-08 a coluna era a data da regeneração do catálogo, igual em todas as
linhas; nada a lia.) Não confundir com:

- `scrape_date`: nas raspadas, a data da primeira coleta, escrita à mão na
  linha de procedência; não anda com as atualizações;
- `last_date`: a data mais recente **dentro** do dado (último dia de cotação,
  último mês de competência), de `docs/context/dataset_freshness.yaml`. É a que
  diz se estamos atrás da fonte, mas hoje só 4 tabelas a têm.

## As duas famílias e o que já existe

| Família | Tabelas | Como saber se a fonte andou | Como trazer | Estado |
|---|---|---|---|---|
| Espelho do Base dos Dados | ~900 | `scripts/sync/checa_espelho_bd.py`: metadado do BigQuery (`numRows`, `modified`; grátis, sem job) contra o catálogo; `updated_at` do dataset na API de busca do BD | tabela grande em que só algumas partições mudaram: `scripts/sync/atualiza_particoes_bq.py` (linhas por partição saem do metadado com `scripts/sync/particoes_bq_metadado.py`); tabela pequena: `scripts/sync/ressincroniza_bq.py`; CNPJ: `scripts/sync/atualiza_cnpj_rf.py` | scripts prontos, nada agendado |
| Raspadas | ~330 | `scripts/checa_frescor_fontes.py`: pergunta à fonte (JSON, Last-Modified, regex ou nota manual), uma entrada por tabela no YAML de frescor | `scripts/scrap/atualiza_fonte.py <scraper>`: roda o scraper em staging, compara nome de arquivo, schema, linhas e data máxima, e só troca com `--promover` | checagem pronta, troca manual de propósito |

O YAML de frescor (fonte, checagem e flags do gate de cada tabela) e os
scrapers ficam fora do git. Tabela raspada sem entrada no YAML não é checada:
das 33 que entraram nos últimos 30 dias, 8 ainda não têm (ANEEL, ANTT, emendas
da CGU, INCRA, CadÚnico, SICAR, PRODES, MapBiomas).

## Ordem de uma rodada completa

```
1. checar (barato, tudo em paralelo)
     espelho BD: metadado de cada tabela no BigQuery x catálogo
     raspadas:   checa_frescor_fontes.py
   -> lista do que está atrás, com o tamanho estimado
2. preflight (uma vez)
     billing desligado no projeto de job, cota do mês, espaço no beelink,
     ninguém mais escrevendo no beelink (ver "Concorrência")
3. trazer (paralelo com limites, ver abaixo)
     espelho BD: partições novas / tabela inteira, cada uma conferida pela contagem
     raspadas:   atualiza_fonte.py em staging, --promover só no que der verde
4. publicar (serial, uma vez no fim)
     views novas (cria_views_novas.py) e views fora de sincronia (repara_views_beelink.py)
5. regenerar (serial, uma vez)
     a cadeia de housekeeping.md item 2, e a checklist inteira
```

Os passos 1 e 3 paralelizam; 4 e 5 não: escrever view exige o lock exclusivo
do `basedosdados.duckdb`, e a regeneração lê o beelink inteiro.

## Paralelizar: o que pode e o que não pode

**Checagem (passo 1): tudo junto.** O metadado do BigQuery é leitura grátis
(`get_table`, `list_partitions`), e 8 threads checaram as 309 tabelas que
faltavam em segundos. As checagens das fontes raspadas batem em hosts
diferentes e podem ir num pool de threads; a exceção são fontes atrás de proxy
BR gratuito, que saturam com concorrência (um worker por proxy).

**Download do Base dos Dados (passo 3): poucos processos, cada um rápido.**

- O controle de cota (`scripts/sync/bq_quota.py`) tem `flock` em volta de
  `reserve()` desde 2026-10-08; antes disso dois processos perdiam a reserva um
  do outro. A cota aguenta paralelo; a banda e o beelink é que limitam.
- A velocidade vem da Storage Read API, não do número de processos: com ela
  foram ~3,6 M linhas/min por tabela (contra ~4 mil linhas/s pela REST). Dois ou
  três downloads simultâneos já enchem uma conexão doméstica; mais que isso só
  divide a banda.
- O gargalo da rodada de 2026-10-07 foi a rede do laptop (hotspot, de 10 MB/s a
  40 KB/s no mesmo dia), não o BigQuery nem o beelink.

**Raspagem (passo 3): por fonte, em paralelo.** Fontes diferentes não
competem entre si. O limite é o beelink: o gate grava em `~/scrap_tmp/staging`
e confere com DuckDB lá, então muitas fontes grandes ao mesmo tempo voltam ao
problema de concorrência abaixo.

**Publicação e regeneração (passos 4 e 5): nunca em paralelo**, nem entre
sessões. Combine com quem mais estiver no beelink antes de rodar.

## Concorrência no beelink: uma carga pesada de cada vez

Em 2026-10-07, com dois processos DuckDB grandes ao mesmo tempo (cada um com
até 16 GB, numa máquina de 27 GB) e downloads gravando no mesmo NVMe, o beelink
devolveu `Invalid Error: Out of buffer` e `ZSTD Decompression failure`
intermitentes em arquivos íntegros (md5 lido direto do disco igual ao do COLD),
nas versões 1.5.4 e 1.5.6, e **uma vez um resultado errado sem erro nenhum**
(duas linhas a mais numa junção que, refeita quatro vezes, deu sempre o número
certo). Sozinho, o mesmo trabalho é determinístico. Causa não achada (memória
ou I/O sob carga); até achar:

- uma carga pesada de DuckDB por vez no beelink;
- toda etapa que grava derivado confere o resultado por um caminho
  independente antes de publicar (contagem contra a fonte, estado final contra
  o original); nada vai para `~/rodado` antes de conferido;
- teste de memória (memtest86+) pendente.

## Armadilhas da rodada de 2026-10-07

- **Stream que trava sem erro.** A Storage Read API às vezes fica em
  `CLOSE_WAIT` e o processo espera para sempre. Um vigia que encerra o download
  quando nenhum arquivo novo aparece em 15 min, e que não encerra durante o
  `rsync` para o beelink (um envio grande passa 15 min sem gravar nada), resolve;
  os scripts pulam o que já entrou e retomam.
- **Row group minúsculo.** A Storage API entrega lotes de ~800 linhas; um row
  group por lote fez a view com `union_by_name` passar de 26 GB e o OOM matar o
  processo. `escreve_shards` em `ressincroniza_bq.py` junta em row groups de
  122.880 linhas.
- **Catálogo vazio publicado.** A varredura do disco tinha teto de 600 s;
  estourou, e o catálogo saiu com as 1.234 tabelas `view_only` e 0 linhas no
  beelink. Agora o teto é 3.600 s e, sem varredura, o script aborta sem gravar.
- **Tabela renomeada na fonte.** O BD rebatizou `br_me_cnpj` para `br_rf_cnpj`.
  Antes de baixar algo "novo", comparar as colunas com o que já temos e olhar
  quais datasets nossos sumiram do catálogo da fonte.
- **COLD cheio.** O backup a cada 6 h só acrescenta (sem `--delete`); em
  2026-10-07 o disco de 916 GB encheu no meio da cópia dos retratos novos do
  CNPJ e passou a falhar. Conferir `df -h /mnt/COLD` antes de uma rodada grande.

## Armadilhas da rodada de 2026-10-09 e 10

- **Laptop que dorme.** Os downloads rodam no laptop; quando ele dormiu, três
  ficaram 4 h vivos e parados (`CLOSE_WAIT`) e dez fontes do gate falharam por
  DNS. Todo processo longo sai com `caffeinate -i`.
- **Contar por partição gasta cota.** `count(*) GROUP BY ano` custa 8 bytes por
  linha da tabela: o plano de 38 tabelas grandes gastou ~65 GB (RAIS, CNO e
  MiDES têm centenas de milhões de linhas). `particoes_bq_metadado.py` lê
  `INFORMATION_SCHEMA.PARTITIONS` e devolve as linhas por partição por 10 MB.
  Só o trecho fora da faixa de partição (`__UNPARTITIONED__`, os anos mais
  novos) precisa de contagem, e ali ela é barata (17 MB na dengue).
- **Row-level security no Base dos Dados.** 22 tabelas (CAGED, CAFIR, ESTBAN,
  SICOR, PNADC, servidores da CGU, BPC, Novo Bolsa Família, CNES, SIH, SIA,
  INMET, ANS) devolvem `None` no dry-run e o `numRows` do metadado conta linha
  que não conseguimos ler. Para essas vale raspar da fonte original.
- **A checagem lê o catálogo.** `checa_espelho_bd.py` só vê uma tabela como em
  dia depois de `build_metadata_catalog.py`; no meio de uma rodada, o que falta
  sai de lista menos log.
- **Arquivo que mistura partições.** No MiDES os parquet de 2022 a 2024 juntam
  anos; `atualiza_particoes_bq.py` recusa trocar partição assim. Tabela inteira
  ou reescrever os arquivos.
- **Tabela "meio trocada" pode ser carga de outra sessão.** Arquivos com data
  nova ao lado dos antigos, numerados em sequência, eram a partição `ano = 2026`
  de `resultados_candidato_municipio_zona` acrescentada por outra sessão: 14
  arquivos novos só com 2026, 125 antigos sem 2026. Contar por partição e por
  arquivo antes de concluir que houve troca pela metade.
- **Pausar um trabalho no tmux.** `kill -STOP` não segura: o servidor tmux manda
  `SIGCONT` ao grupo do painel. O que pausa é o cgroup do painel
  (`echo 1 > <escopo tmux-spawn-*.scope>/cgroup.freeze`, gravável sem sudo;
  `echo 0` retoma). E `pgrep -f "<texto>"` casa com o próprio shell que contém o
  texto e com o servidor tmux, cujo cmdline traz o comando da sessão: usar
  `pgrep -x <nome>` e conferir o cmdline, ou o PID.
- **Coluna que a fonte deixou de publicar.** O gate com `--conformar` regrava a
  coluna sumida como NULL e passa verde; foi assim que `CARGO/FUNCAO` do TCU
  quase perdeu 6.732 valores. Ler `viraram_null` no relatório antes de promover;
  quando a tabela tem chave única, dá para promover e repor o valor antigo por
  junção com o backup (feito em 2026-10-10, 6.731 valores mantidos).

## O que "encolheu" quer dizer

`checa_espelho_bd.py` marca `encolheu` quando o BigQuery tem menos linhas que o
disco. Conferidas as 13 de 2026-10-09 por partição (metadado do BigQuery contra
o disco), nenhuma era perda de dado na fonte; são cinco casos diferentes:

| Caso | Tabelas | O que fazer |
|---|---|---|
| O disco é que está à frente: o projeto raspa a fonte original | `br_inpe_queimadas.microdados` (2003 a 2024 idênticos; 2026 tem 2.157.888 linhas no disco e 269.810 no BigQuery), `br_tse_eleicoes.candidatos` (2 linhas a mais, em 2000 e 2006) | nada |
| O BigQuery perdeu um pedaço que temos | `br_ibge_censo_2022.cadastro_enderecos`: a diferença, 1.318.887, é exatamente o DF | nada; não ressincronizar |
| A fonte passou a guardar só o retrato mais novo | `br_sfb_sicar.area_imovel`: o disco tem 10 extrações (2024-10 a 2025-10, 7,7 a 8,2 milhões cada); o BigQuery tem uma, de 2026-06 a 2026-08, 8.484.586 linhas | acrescentar a extração nova como partição (6,4 GB de cota), sem apagar as antigas |
| A fonte reprocessou os anos recentes | `br_ms_sinan.microdados_dengue`: 2000 a 2023 idênticos; 2025 caiu de 3.435.753 para 1.728.234 e 2026 subiu de 5.174 para 398.786. `br_ms_sia.psicossocial`: 2012 a 2023 idênticos; 2024 em diante soma 25.034.859 no disco e 18.194.192 no BigQuery (tabela com row-level security, não dá para abrir por ano) | dengue: trocar as partições 2024 a 2026; psicossocial: raspar do DataSUS |
| O disco tem linha repetida de sync antigo, ou retrato velho de tabela pequena | `br_me_siconfi.uf_receitas_orcamentarias`: 2021 tem 7.435 linhas e 7.159 distintas, e o BigQuery tem 7.159. `br_cgu_sancoes.cepim`, `br_camara_dados_abertos.licitacao_contrato`, `br_senado_dados_abertos.{comissao,lideranca,relatoria}`: retrato mais novo na fonte | `ressincroniza_bq.py` (menos de 0,1 GB no total) |

`br_ms_sim.dicionario` (569 linhas no disco, 15 no BigQuery) não é nenhum dos
casos: o dicionário do disco é maior de propósito e fica.

## "Atrás" logo depois de ressincronizar

O `numRows` do metadado conta também as linhas que só o BD Pro lê (os meses mais
recentes, por row-level security). Tabela assim continua `atras` depois de uma
ressincronização que trouxe tudo o que é público: em 2026-10-10, das 179 tabelas
do lote pequeno trocadas na véspera, 85 ficaram em dia e 87 seguiram `atras`; em
61 dessas o BigQuery não tinha mudado desde a checagem anterior (7 do SICOR, 7 do
CNES, 7 da Câmara, 6 do Senado, 4 da Anatel banda larga, 4 do IPCA-15, 4 do Comex,
3 dos servidores da CGU e outras 19), somando 18,8 milhões de linhas que a consulta
não devolve. `br_anatel_banda_larga_fixa.densidade_brasil` mostra o padrão: 193
linhas no disco antes e depois da troca, 199 no metadado, uma por mês que falta.
Nas demais a causa não foi conferida uma a uma. As outras 26 foram regravadas na
fonte de um dia para o outro (o BD atualiza todo dia). Antes de
gastar cota numa tabela `atras`, conferir se a contagem do disco mudou na última
ressincronização: se não mudou, não há o que trazer.

## Fonte nova que roda no beelink

Os três scrapers de 2026-10-10 (`cvm_cia_aberta.py`, `ans_operadoras.py`,
`ibge_censo2022_agregados.py`) baixam e convertem no próprio beelink, sem
passar pelo laptop: `scp` do script para `~/scrap_tmp/`, `ssh beelink python3`,
resultado em `~/scrap_tmp/novos/<dataset>/`, e só `--publicar` move para
`~/rodado`. Cada um confere as linhas contra o arquivo de origem antes. O que
custou tempo:

- o leitor de CSV do DuckDB recusa como `latin-1` os bytes 0x80 a 0x9F (aspas
  curvas e travessão do Windows-1252): passar o arquivo para UTF-8 antes;
- a ANS mistura UTF-8 e ISO-8859-1 na mesma pasta e duas escritas de data na
  mesma coluna; detectar por arquivo;
- o IBGE publica o mesmo tema duas vezes na pasta (com e sem data no nome);
  vale a versão de data mais recente;
- chave "única" da fonte que repete: um bairro de Vila Velha vem uma vez por
  subdistrito. Conferir unicidade antes de juntar arquivos pela chave.

## Agendar

Os downloads do BigQuery rodam no laptop (é lá que estão as credenciais, e os
parquet são montados localmente e só copiados para o beelink); a checagem das
raspadas e o gate rodam a partir do laptop também, via SSH. Um agendamento
razoável, quando os itens em aberto abaixo estiverem resolvidos:

- **diário:** checagem das duas famílias, só relatório;
- **semanal:** download do que está atrás no espelho do BD, dentro da cota, e
  gate das raspadas sem `--promover`;
- **depois de cada troca:** publicação, regeneração e a checklist de
  `housekeeping.md`, com uma pessoa olhando o relatório antes de promover.

## Em aberto

1. Entradas no YAML de frescor para as 8 raspadas que não têm.
2. `last_date` (data dentro do dado) para mais tabelas, em
   `dataset_freshness.yaml`: é ela que diz se estamos atrás da fonte.
3. Teste de memória do beelink.
4. `checa_espelho_bd.py` não enxerga as tabelas que no BigQuery são VIEW (127 em
   2026-10-08): o metadado de view não traz contagem.
5. `atualiza_particoes_bq.py` ainda conta as partições com `count(*)`; trocar pelo
   metadado de `particoes_bq_metadado.py` e contar só o trecho `__UNPARTITIONED__`.
6. Do diagnóstico de "encolheu": a extração nova do SICAR, as partições 2024 a 2026
   da dengue e as 7 tabelas pequenas a ressincronizar. E as 16 que sumiram do
   BigQuery (quase todas `*_original`) seguem no disco sem fonte para conferir.
7. Sem começar, por cota: `br_ms_sinasc.microdados` (18,5 GB), MiDES (`licitacao_item`,
   `liquidacao`, `empenho`, `pagamento`, 239 GB), CNO (`cnaes`, `areas`, `microdados`,
   140 GB), `br_bd_diretorios_brasil.empresa` (15,2 GB) e
   `br_cgu_licitacao_contrato.licitacao_participante` (19,6 GB), as duas últimas sem partição.

Fechados em 2026-10-08: a trava no `bq_quota.reserve()` (`flock` + gravação
atômica; 400 reservas de 8 processos somaram 400) e o script de checagem do
espelho do BD. Na primeira rodada ele achou 216 tabelas atrás (4,72 bi de linhas,
~1.060 GB de cota), 14 em que o BigQuery tem menos linhas que o disco e 16 que
sumiram da fonte.
