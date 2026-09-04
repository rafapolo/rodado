# Folha de cola das tabelas-hub — evitar a caçada por tabela de referência

> Aberto em 2026-09-04, a pedido, durante o head-to-head ao vivo de
> `ferramentas_claude_code.md` (T04-2, CAGED×RAIS). Não é hipótese: achado e
> consertado na mesma sessão, com uma rodada v2→v3 provando o antes/depois.

## O gap, medido

Rodando a mesma pergunta três vezes seguidas (v1, v2, v3 — logs em
`tasks/ferramentas_claude_code.md`), a v2 gastou os passos 6-12 **caçando a
tabela que traduz `id_municipio` pra nome do município**, chutando dataset
atrás de dataset:

```
descrever_tabela("br_ibge_munic")             -> não existe (faltou .tabela)
listar_tabelas("br_ibge_munic")                -> existe, mas não tem nome de município
listar_tabelas("br_ibge_nomes_brasil")          -> dataset ERRADO (nomes de PESSOA, não de município)
descrever_tabela("br_ibge_munic.habitacao")     -> ainda não é a certa
```

A tabela certa — `br_bd_diretorios_brasil.municipio` (`id_municipio`, `nome`)
— nunca foi tentada. Não é falta de raciocínio: é falta de um jeito barato de
descobrir uma tabela de referência que a pergunta não cita, porque o harness
não tem `search_tables` (busca semântica) nem qualquer índice do que existe
além do nome exato do dataset.

**Conserto imediato aplicado:** uma linha na descrição de `listar_datasets`
(`mcp.ts`) apontando direto pra `br_bd_diretorios_brasil.municipio`. v3
(mesma pergunta, harness com o fix) não repetiu a caçada nos primeiros 5
passos — resultado completo no corpo de `ferramentas_claude_code.md`.

## Por que generalizar, e por que NÃO treinar pra isso

Discutido ao vivo com quem pediu: treinar (LoRA) o schema nos pesos do Gemma
foi descartado — o schema é alvo móvel (o mirror já mudou de 1024 pra 1027
tabelas durante esta mesma sessão), e o projeto já tem um plano de LoRA
parado (`backlog.md` item 11, pra outro bug, passo 0 nunca rodado) — empilhar
"ensinar schema" em cima de um pipeline de treino não validado é compor risco
sobre risco.

O que funciona é a mesma disciplina do resto do projeto: informação que não
muda entre perguntas vai no **prefixo estável** (a mesma regra que dá o cache
de 44x), como dado GERADO, não curadoria manual que dessincroniza.

## O plano

`docs/context/bridges.yaml` já lista `canonical_table` para praticamente todo
conceito de junção (município, UF, CNAE, CBO, CID, CNPJ...). Isso já É a
lista das tabelas-hub — só nunca foi extraída e servida pro modelo.

1. **`scripts/gera_tabelas_hub.py`** (novo): lê `bridges.yaml`, agrupa os
   `canonical_table` únicos por `concepts`, gera uma lista curta (~15-20
   linhas) `tabela — o que ela traduz — colunas-chave`.
2. Embutir essa lista no prompt estático do `dsh/rodado.patch.yml` (ou, mais
   barato ainda, na descrição de `listar_datasets` em `mcp.ts`, expandindo o
   hint pontual que já foi aplicado pra município) — decisão de onde entra é
   de quem mantém, mas tem que ser **gerado**, nunca editado à mão, mesma
   regra de `join_keys.md`.
3. Regenerar sempre que `bridges.yaml` mudar — entra na lista de comandos do
   `CLAUDE.md` junto dos outros geradores da camada semântica.
4. Medir: rodar de novo perguntas que citam conceito só por ID (município,
   CNAE, CBO — qualquer pergunta que peça "nome de X" a partir de código) e
   contar se a caçada por tabela de referência desaparece.

## Estado

🔵 aberto 2026-09-04 — plano registrado, só o caso `id_municipio` → `nome`
está consertado (hint pontual em `listar_datasets`, commit a seguir). O
generalizador (`gera_tabelas_hub.py`) ainda não existe.

## Ver também

- [`ferramentas_claude_code.md`](ferramentas_claude_code.md) — o head-to-head
  completo, incluindo o antes/depois v2→v3 desta mesma caçada
- `docs/context/bridges.yaml` — fonte dos `canonical_table`, nada aqui deveria
  duplicar dado, só reformatar pro prompt
