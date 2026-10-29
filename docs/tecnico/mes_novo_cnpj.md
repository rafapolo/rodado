# `br_me_cnpj` — mês novo

Desde 2026-10-13, `empresas`, `estabelecimentos` e `socios` têm um único
retrato (o último mês publicado) — não precisam de filtro de `ano`/`mes`, e
filtrar um mês antigo devolve zero linhas. A série 2021-11 em diante vive em
`empresas_historico` e `estabelecimentos_historico` (uma linha por período sem
mudança, `inicio`/`fim` em `aaaamm`; estado na data X = `inicio <= X AND fim
>= X`) e em `socios_historico` (uma linha por vínculo,
`primeiro_retrato`/`ultimo_retrato`; ex-sócio = `NOT no_ultimo_retrato`). Os
retratos mensais antigos (283 GB) foram apagados e não têm cópia: o histórico
é a única fonte do passado.

Mês novo, na ordem:

```bash
# no beelink: baixa o mês da Receita, converte, confere e publica rf_<aaaamm>_NN.parquet
python3 ~/scrap_tmp/cnpj_receita.py            # (scripts/scrap/, fora do git) ~6 h: a Receita dá ~0,5 MB/s por IP
python3 scripts/completa_cpf.py br_me_cnpj.socios  # ANTES do --anexa (ver abaixo)
python3 scripts/sync/gera_cnpj_historico.py --tabela empresas --anexa
python3 scripts/sync/gera_cnpj_historico.py --tabela estabelecimentos --anexa
python3 scripts/sync/gera_cnpj_historico.py --tabela socios --anexa
# mover os rf_<mês anterior>_* para ~/backups (apagar só depois de conferir o histórico)
python3 scripts/repara_views_beelink.py --apply
# regen do catálogo (ver docs/context/README.md, "Ordem do regen")
```

O `--anexa` precisa do retrato novo **e** do histórico publicado, e dá o
mesmo resultado de regerar tudo (conferido linha a linha em 2026-10-13).

**De onde vem o mês (desde 2026-10-28).** O `atualiza_cnpj_rf.py` trazia o mês
pelo `br_rf_cnpj` do Base dos Dados, mas lá os meses depois de 2026-04 ficaram
atrás do RLS do BD Pro, e a URL antiga da Receita dá 404. A Receita publica num
Nextcloud público (`arquivos.receitafederal.gov.br/index.php/s/gn672Ad4CF8N6TK`,
pasta `Dados/Cadastros/CNPJ/<aaaa-mm>/`). O coletor `cnpj_receita.py` (em
`scripts/scrap/`, fora do git) converte para o mesmo schema e foi calibrado
contra o 202609 da BD: `empresas` 0 diferenças em 4.494.860 linhas,
`estabelecimentos` 4 em 4.753.435 (acento dentro do texto). `--confere` gera em
staging sem publicar.

**CPF antes do `--anexa`.** O grão de `socios_historico` inclui `documento`.
Retrato novo chega mascarado; anexado assim, todo vínculo com CPF completado
fecharia e reabriria com outro `documento`. Conferir antes: a fração de
pessoa física com CPF de 11 dígitos tem de ficar perto da do mês anterior
(2026-09: 81,09%; 2026-10: 81,03%; dos vínculos dos dois meses, 14 de 27,5 M
perderam o CPF).

Armadilhas semânticas (histórico, meses ausentes, sentinela de capital
social, CPF mascarado) estão em `docs/context/gotchas/br_me_cnpj.yml` — leia
antes de consultar, não só antes de sincronizar.
