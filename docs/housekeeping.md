# docs/housekeeping.md — checklist pós-scraping

Toda vez que um scraper novo (ou um job resumido/retomado sem supervisão) larga
parquet em `~/rodado/<dataset>/<tabela>/` no beelink, sobra um conjunto fixo de
passos que **nada faz sozinho** — nenhum hook cria a view, regenera o catálogo
ou avisa que um job parou. Esta checklist existe porque isso já causou dado
real "invisível" e contagem errada mais de uma vez (2026-09-02). Rodar depois
de qualquer scrape novo, antes de declarar um dataset pronto.

## 1. Existe view no `.duckdb`?

`read_parquet()` funciona sem view. `information_schema.tables` — e por
extensão `describe_table`/`list_tables`/todo o `mcp_server.py` — não. Um
dataset pode ter o parquet inteiro, correto e verificado no disco, e ainda
assim ser invisível para toda ferramenta que não seja `read_parquet` direto.
Achado ao vivo em três datasets no mesmo dia: `br_cgu_gas_do_povo`,
`br_cgu_novo_bolsa_familia`, `br_transferegov_siconv` — todos com parquet
completo, todos com `information_schema.tables` devolvendo 0.

Confira sempre os dois antes de declarar "pronto":

```bash
ssh beelink "~/bin/duckdb -readonly -json ~/rodado/basedosdados.duckdb -c \
  \"SELECT count(*) FROM information_schema.tables WHERE table_schema='<dataset>'\""
```

Se der 0 com parquet real no disco, crie a(s) view(s) — roda local, não no
beelink, ele mesmo abre SSH:

```bash
# lista.txt: um "dataset/tabela" por linha
python3 scripts/sync/cria_views_novas.py lista.txt
```

Idempotente — pula o que já tem view, então rodar de novo é sempre seguro.
(`repara_views_beelink.py` é o script irmão: conserta view que já existe e
saiu de sincronia com o disco; não cria view nova do zero — são scripts
diferentes para dois problemas diferentes.)

## 2. Regen de metadados, sempre nesta ordem

Depois que a view existir, roda a cadeia inteira documentada na seção
"Camada semântica" deste `CLAUDE.md` — `gera_schemas.py` →
`sync_mcp_schema.py` → `build_metadata_catalog.py` → `gera_join_keys.py` (e
o resto, se o schema mudou o bastante). `sync_mcp_schema.py` é o passo mais
esquecido: sem ele, `describe_table` continua mentindo sobre colunas novas.

## 3. Um job que devia continuar rodando — ainda está rodando?

Um `nohup ... & disown` no beelink sobrevive ao fim da sessão SSH que o
lançou, mas nada avisa quando ele termina, trava ou desiste. Antes de
assumir "ainda baixando", confirme o processo:

```bash
ssh beelink "ps aux | grep -iE '<padrão do script>' | grep -v grep"
```

Vazio **não** significa "terminou com sucesso" — pode ter parado por
esgotamento de cota sem erro fatal nenhum. Sempre olhar o log também:

```bash
ssh beelink "tail -30 ~/rodado/_staging/<job>/<algo>.log"
```

Padrão real visto em `_staging/pncp/persistente.log` (2026-09-02): `sem
progresso entre rodadas — fonte esgotada, parando` — o job se auto-encerrou
de propósito depois de 3 rodadas sem avançar. É rate limit por IP, não bug;
retomar exige esperar a janela abrir, não só re-lançar o script na hora.

## 4. Contagem duplicada entre sessões concorrentes

Duas sessões que não sabem uma da outra, rodando o mesmo scraper para o
mesmo dataset com padrões de nome de arquivo diferentes (`202511.parquet`
vs `2025_11_gas_do_povo.parquet`, mesmo conteúdo), fazem
`read_parquet('*.parquet')` contar as duas cópias como linhas distintas —
aconteceu com Gás do Povo em 2026-09-02 (34,8M contado vs. 20,8M real, achado
só porque a contagem batia estranho com o esperado). Antes de reportar uma
contagem "grande demais pro que a fonte deveria ter", listar os arquivos do
diretório e checar se há duplicata de conteúdo sob nome diferente — não
assumir que nome diferente é dado diferente.

## 5. Zip com mais de um CSV membro

Scrapers que baixam `.zip` esperando 1 CSV por arquivo (padrão CGU/
Transferegov) devem **pular e logar**, nunca adivinhar, quando um zip trouxer
N membros — o nome do zip não diz qual membro vira qual tabela. Ficam para
uma segunda passada manual: abrir o zip, inspecionar os nomes dos membros,
decidir a tabela de cada um seguindo a convenção já usada pelos outros
arquivos do mesmo dataset. Zip com **0** membros CSV é sinal de baixar de
novo antes de descartar como corrompido — pode ter sido um download
truncado, não necessariamente um problema na fonte.

## 6. `source_url` preenchida na proveniência, não só `source_name`

`build_metadata_catalog.py` extrai `source_url` da linha do `done.md`/
`datasets_to_scrap.md` por regex (`URL_RE` exige esquema `https://` explícito;
sem isso cai num fallback mais fraco por hostname entre crase, que só pega
hostname puro, sem caminho). Um `` `dominio.gov.br/caminho` `` sem `https://`
na frente não vira URL — a coluna fica vazia. Escreva a URL completa com
esquema na nota de proveniência, sempre.

**Duas armadilhas achadas ao vivo em 2026-09-04:**

1. **Linha velha e stale em `datasets_to_scrap.md` vence a linha nova em
   `done.md`.** ANEEL tinha uma linha antiga `blocked` apontando pro domínio
   morto `dados.aneel.gov.br` (Tier 1a) que continuou lá depois do dataset
   ter sido raspado com sucesso e ganhar linha própria em `done.md` — o
   `source_url` do catálogo saiu errado (domínio morto) até a linha velha ser
   removida. Sempre que um item sai de `blocked`/`deferred-api_key` para
   `done`, a linha velha em `datasets_to_scrap.md` precisa **sair do
   arquivo**, não só ganhar uma linha nova em `done.md` ao lado dela.
2. **87 tabelas raspadas independentemente (fora do espelho Base dos Dados)
   seguem sem `source_url`** no catálogo — pré-existente, não introduzido
   nesta rodada, não corrigido (precisaria pesquisar a URL original de cada
   uma). Checar com:
   ```sql
   SELECT dataset, "table" FROM _rodado_metadata
   WHERE (source_url IS NULL OR source_url = '') AND source <> 'view_only'
     AND source_name NOT LIKE 'Base dos Dados%';
   ```

## 7. `catalog.parquet` mudou → `docs/catalog.md` tem que ser regenerado junto

`docs/catalog.md` é um export legível do `_rodado_metadata`/`catalog.parquet`
(um dataset por linha: descrição, nº de tabelas, linhas, fonte). É gerado, não
editado à mão. Toda vez que `build_metadata_catalog.py` roda — e portanto
toda vez que um dataset novo entra, uma tabela some, uma proveniência muda —
`docs/catalog.md` fica desatualizado até rodar de novo:

```bash
python3 scripts/build_metadata_catalog.py   # regrava catalog.parquet
python3 scripts/gera_catalog_md.py          # regrava docs/catalog.md a partir dele
```

Novo dataset sem descrição em `docs/context/dataset_descriptions.yaml`? O
próprio `build_metadata_catalog.py` avisa no stderr (`N dataset(s) missing a
description`) — a linha existe no catalog e no `catalog.md` com a coluna
`description` vazia, não quebra o regen, mas fica feio até alguém preencher.

## Ordem completa, resumida

```
scrape novo/retomado
  -> 1. view existe? (information_schema.tables, cria_views_novas.py se não)
  -> 2. regen de metadados (gera_schemas.py -> sync_mcp_schema.py -> build_metadata_catalog.py -> gera_join_keys.py)
  -> 2b. catalog.parquet mudou -> gera_catalog_md.py (nunca esquecer, ver item 7)
  -> 3. algum job que devia continuar rodando parou sozinho? (ps aux + tail do log)
  -> 4. contagem bate com o esperado da fonte? (checar duplicata de arquivo antes de aceitar um número grande demais)
  -> 5. algum zip multi-membro ficou pra trás? (inspecionar antes de descartar)
```
