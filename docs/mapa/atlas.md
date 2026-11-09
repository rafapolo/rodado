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
- Três vistas: Ontologia (padrão, ver abaixo), `temas` (um território por
  tema, chaves flutuando entre os que ligam; layout pré-calculado em Python e
  embarcado no JSON) e 3D. A Grade de cartões de dataset saiu em 2026-11-08,
  a pedido.
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

## Modo Ontologia (`?mode=ontologia`)

A vista padrão do atlas (a Grade de cartões saiu a pedido), um nível acima de Temas e 3D: as entidades que as
chaves identificam (Município, Estabelecimento, Pessoa, Licitação…) e as
relações entre elas, num grafo de forças em SVG. Além das entidades (disco
cheio), os **fatos** (anel): óbito, internação, ocorrência, nota, vínculo,
benefício, sanção, voto… — entram por tabela (`tabelas:` no YAML), não por
coluna. As colunas vêm de todo o `schemas.json`, não só das chaves do atlas, e
o gerador confere as colunas de CNPJ/CPF do `../datative` quando o repo está ao
lado. `docs/context/ontologia.yaml`
é curado à mão (classes, regex das variantes de coluna, relações com o `via`);
`bun scripts/gera_ontologia.ts` lê esse YAML, `bridges.yaml` e
`schema_graph.json` e grava `pages/atlas/ontologia.json` (buscado só quando o
modo abre; embutido na cópia de Artifact) + `docs/mapa/ONTOLOGIA.md` (mermaid,
ELK). Chaves e datasets vão como índices do `schema_graph.json`, então clicar
numa coluna ou dataset no inspetor desce para Temas.

- Em Distribuição é o primeiro dos três botões (Ontologia · Temas · 3D).
- `?mode=ontologia&classe=<id>` abre já com a classe no inspetor.
- O build recusa conceito de `bridges.yaml` sem classe ou em duas, e relação
  para classe inexistente — conceito novo em `bridges.yaml` exige classe aqui.
- Ordem: `gera_schema_graph.py` → `gera_ontologia.ts` → `build_atlas.py`.
