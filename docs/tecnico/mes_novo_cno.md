# `br_rf_cno` — retrato novo

Desde 2026-11-03, `microdados`, `areas`, `cnaes` e `vinculos` têm um único retrato
(`<tabela>/000000000000.parquet`, o último `data_extracao`); o passado vive em
`<tabela>_historico` (uma linha por período em que a linha inteira se repetiu,
`inicio`/`fim` em datas de `data_extracao`; leitura em
`docs/context/gotchas/br_rf_cno.yml`, `historico_como_ler`). As quatro tabelas não
andam juntas: cada uma tem o seu último retrato (`max(fim)` do seu histórico) e é
anexada sozinha.

Retrato novo **nunca** vira mais um parquet solto em `<tabela>/`: ele cai em
`~/scrap_tmp/retrato_novo/br_rf_cno/<tabela>/<data>/` e passa por
`gera_retrato_historico.py --anexa`, que não relê o passado (minutos, contra ~1 h para
regerar, e sem os 2.202 retratos brutos do COLD).

## Caminho do sync

Quem leva o retrato novo ao beelink é o `atualiza_particoes_bq.py` (ou, vindo do finland,
`coleta_pouso_bq.py` + `aplica_pouso_bq.py`). A lista de tabelas nesse regime é
`docs/context/retratos_historico.yaml`; o desvio está em `scripts/sync/retrato_novo.py`.

- `atualiza_particoes_bq.py`: para essas tabelas só considera partição `data_extracao` **mais
  nova que `max(fim)`** do histórico (as antigas "faltam" no disco por desenho), baixa para o
  diretório de trabalho e chama o `--anexa` por ssh, sob `flock ~/scrap_tmp/pesado.lock`.
- `aplica_pouso_bq.py` (cron do beelink): idem, a partir do `_pouso`; se o `pesado.lock` estiver
  ocupado ou o `--anexa` recusar, devolve falso e o retrato fica no diretório de trabalho para a
  próxima passada (o pouso só é limpo depois do anexo).
- `ressincroniza_bq.py` e `sync_drifted_incremental.py` **recusam** essas tabelas (trariam todos
  os retratos de volta, ou um parquet solto). Liberar só uma: `IGNORA_FONTE_PROPRIA=br_rf_cno.areas`.

## Anexar à mão

```bash
# no beelink; o retrato novo (parquet, no mesmo schema da tabela) já está em
# ~/scrap_tmp/retrato_novo/br_rf_cno/areas/ (qualquer subpasta; "_anexados/" é ignorada)
flock ~/scrap_tmp/pesado.lock python3 ~/scrap_tmp/repo/scripts/sync/gera_retrato_historico.py \
    br_rf_cno areas --anexa
# conferir sem trocar nada: acrescente --sem-publica (fica em ~/scrap_tmp/retrato_hist_anexa/)
```

O que ele faz, com `D` = `data_extracao` do retrato novo e a identidade da linha = hash de
todas as colunas menos a data, mais um ordinal para cópias repetidas:

| Situação | Resultado |
|---|---|
| linha vigente (`fim` = último retrato) que está no retrato novo | `fim` passa a `D` |
| linha nova ou mudada | período novo, `inicio = fim = D` |
| linha vigente que sumiu | fica fechada como está |

Para linha repetida: a cópia `j` só existe enquanto a contagem for ≥ `j`; nos vigentes o
ordinal sai de `inicio` crescente, no retrato novo é arbitrário (cópias idênticas).
Id fora de toda faixa vai para a primeira (abaixo do menor) ou a última (acima do maior); o
limite de baixo de cada faixa é o menor `id_cno` do arquivo, o que reproduz os cortes da geração.

**Recusas** (nada é escrito em `~/rodado`): `D <= max(fim)`; retrato vazio; mais de uma data é
aceito, em ordem, um de cada vez; `id_cno` ou `data_extracao` NULL; colunas ou tipos diferentes
(schema mudou na fonte: regerar o histórico); parquet solto em `<tabela>/`; histórico que não
fecha com a tabela atual; retrato com menos de 90% das linhas do anterior
(`--limite-encolher`, `--aceitar-encolher` depois de olhar a fonte: no histórico já houve
`areas` a 50% e `vinculos` a 12% de um retrato para o outro).

**Conferência antes de publicar** (qualquer falha para e deixa tudo no trabalho):

1. `D` reconstruído pelo histórico novo = fonte (contagem e soma do hash da linha);
2. todas as pontas de período do histórico de antes reconstruídas no novo = as de antes (contagem
   e soma do hash em cada data, o retrato anterior incluído);
3. histórico novo sem o que abriu em `D` e com o `fim` revertido = histórico antigo (contagem e
   soma do hash da linha inteira);
4. cada faixa gravada duas vezes (`copia_dupla`); tudo no `valida_parquet.py`;
5. depois da troca: tabela atual e histórico em `D` = fonte de novo.

Publica trocando o diretório do histórico (mesmos nomes `faixa_NNN.parquet`: as views por glob
seguem valendo, **não precisa** de `repara_views_beelink.py`) e o `000000000000.parquet`. Os
antigos ficam em `~/scrap_tmp/retrato_hist_anexa/br_rf_cno/<tabela>/<D>/substituido/` (apagar à
mão, depois de conferir); o retrato novo vai para `_anexados/` ao lado de onde estava.

## Depois do anexo

- Datas no texto: gotchas `snapshot_por_extracao` e `historico_como_ler` (último retrato de
  cada tabela), cartões e `docs/context/dataset_freshness.yaml`.
- Catálogo: `build_metadata_catalog.py` e o regen (`docs/context/README.md`, "Ordem do regen").
- S3, COLD e finland: os dois arquivos que mudam por tabela têm o mesmo nome de antes, então o
  rsync/`mc` por nome e tamanho os vê; conferir que o `valida_parquet` do sync aprovou.
- Deploy do código: o cron e o `ssh` usam `~/scrap_tmp/repo` no beelink, que não é um clone:
  copiar `scripts/sync/{gera_retrato_historico,retrato_novo,fonte_propria,atualiza_particoes_bq,
  aplica_pouso_bq}.py` e `docs/context/retratos_historico.yaml` para lá.
