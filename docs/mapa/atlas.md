# `pages/atlas/` — Rodado Atlas (rodado.xyz/atlas)

Mapa navegável das tabelas e das colunas de join que as conectam. O espelho
não tem foreign key — o que o liga são colunas que significam a mesma coisa
em mais de uma tabela, a mesma seleção que `gera_join_keys.py` faz.

```bash
python3 scripts/gera_schema_graph.py   # schemas.json + catalog.parquet -> pages/atlas/schema_graph.json
python3 scripts/build_atlas.py         # + pages/atlas/_page.html       -> pages/atlas/index.html
python3 scripts/build_atlas.py /tmp/atlas.html   # também emite a cópia autocontida pra Artifact
```

- `_page.html` é a **única fonte**; `index.html` é gerado — não edite o gerado.
- O grafo é **bipartido**: tabela→chave, nunca tabela→tabela. Par a par seriam
  89.598 arestas (novelo); pela chave são 2.151.
- Duas distribuições, ambas pré-calculadas em Python e embarcadas no JSON:
  `grade` (cartões de dataset empacotados) e `temas` (um território por tema,
  chaves flutuando entre os que ligam).
- O painel repete o que `describe_table` do MCP diz de cada tabela: armadilhas
  (`gotchas/`), colunas com código (`dicionario_coverage.json`,
  `coded_differently`, `column_codes.yaml`; o `nao_verificado` fica de fora, a
  pedido), métricas (`metrics.yaml`), busca rápida (`ORDENADA_POR` de
  `db/consulta.py`), data da coleta e, dos perfis, nulos e valores mais
  frequentes, além do cartão e do "dados até" de `pages/assets/summaries/`.
  `gera_schema_graph.py` grava um JSON por dataset em `pages/atlas/detalhes/`,
  buscado quando o painel abre. A fonte aparece só pelo nome: a URL das
  fontes raspadas é o mapa de coleta, que fica fora do repo.
- `?db=<dataset>` abre o atlas já centrado naquele dataset com o painel aberto
  (`rodado.xyz/atlas?db=br_me_rais`); o parâmetro acompanha a seleção via
  `replaceState`, então a barra de endereço é sempre um link pro que está na
  tela.
- **Cor = tema**, nunca chave. Só 4 matizes passam o gate all-pairs de CVD,
  então os 10 temas dependem de território rotulado + isolamento por clique; a
  cor reforça, não carrega sozinha.
- Depois de qualquer sync que mude tabelas: `gera_schemas.py` →
  `build_metadata_catalog.py` → `gera_schema_graph.py` → `build_atlas.py`.

Ligar um **dataset novo** no atlas (tema certo, chave de join reconhecida) é
um passo separado, com os dois jeitos de falhar em silêncio — ver
`docs/tecnico/housekeeping.md`, item 9.
