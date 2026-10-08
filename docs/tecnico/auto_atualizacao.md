# docs/tecnico/auto_atualizacao.md — como manter as 1.234 tabelas em dia

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
| Espelho do Base dos Dados | ~900 | metadado do BigQuery (`numRows`, `modified`; grátis, sem job) contra o catálogo; `updated_at` do dataset na API de busca do BD | partição nova (`ano`, `data_referencia`, `data_extracao`): `scripts/sync/sync_drifted_incremental.py`; tabela pequena: `scripts/sync/ressincroniza_bq.py`; CNPJ: `scripts/sync/atualiza_cnpj_rf.py` | scripts prontos, nada agendado |
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

- O controle de cota (`scripts/sync/bq_quota.py`, um JSON com
  read-modify-write sem trava) **não aguenta dois processos**. Para paralelizar,
  ou se põe um `flock` em volta de `reserve()`, ou se usa um processo só com um
  pool de threads interno. Até isso existir, rodar os scripts de sync um de cada
  vez.
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

1. Trava no `bq_quota.reserve()` para permitir downloads paralelos.
2. Script de checagem do espelho do BD (metadado do BigQuery contra o
   catálogo), irmão do `checa_frescor_fontes.py`.
3. Entradas no YAML de frescor para as 8 raspadas que não têm.
4. `last_date` (data dentro do dado) para mais tabelas, em
   `dataset_freshness.yaml`: é ela que diz se estamos atrás da fonte.
5. Teste de memória do beelink.
