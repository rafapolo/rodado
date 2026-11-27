# Integridade: hash lógico de cada tabela

> Visão geral de fonte, hash por publicação e histórico de mudanças: [`governanca.md`](governanca.md).

`hashes.csv` (gerado pela primeira passada, em andamento desde 25/11/2026) traz, para cada tabela do espelho, o número de linhas e um **hash do conteúdo**.
`particoes.csv` traz o mesmo por ano, nas tabelas que têm a coluna `ano`. O histórico do git
destes dois arquivos registra quando cada hash mudou, ou seja, quando o conteúdo mudou:
uma linha acrescentada, tirada ou alterada, na fonte ou aqui.

O hash é **lógico**: depende só das linhas, não dos arquivos. Não muda com a ordem das linhas,
a divisão em arquivos, o tamanho dos grupos do Parquet ou a compressão. Assim, outro espelho
que tenha o mesmo conteúdo chega ao mesmo valor, e um espelho que recebeu uma versão diferente
descobre isso sem baixar nada além da sua própria cópia.

## Versão `adh120-v1`

1. **Linha canônica:** `to_json()` do DuckDB aplicado a um struct com todas as colunas da tabela,
   em ordem alfabética do nome da coluna. Calculado com o **DuckDB 2.0.0**: a forma como o `to_json()`
   escreve números decimais e datas pode mudar entre versões, então confira com a mesma versão.
2. **Hash da linha:** `sha256` da linha canônica, em hexadecimal.
3. **Soma:** `a` = soma de `int(h[0:15], 16)` e `b` = soma de `int(h[15:30], 16)` sobre todas as
   linhas, cada uma módulo 2⁶⁰.
4. **Hash da tabela:** `adh120-v1:` seguido de `a` e `b` em 15 dígitos hexadecimais cada.

É um hash aditivo de multiconjunto (Bellare e Micciancio, 1997): a soma das partições é a soma
da tabela, e uma tabela com uma linha repetida tem hash diferente da mesma tabela sem a repetição.
Serve para conferir uma cópia, não como prova contra quem quer forjar uma: para isso, a versão 2
usará um hash de reticulado da família LtHash.

## Conferir a sua cópia

Com o DuckDB, numa tabela `t` com as colunas `c1`, `c2`, … já em ordem alfabética:

```sql
WITH h AS (SELECT sha256(to_json(struct_pack(c1 := t.c1, c2 := t.c2 /* … */))) s FROM t)
SELECT count(*) linhas,
       'adh120-v1:' || lpad(format('{:x}', (sum(('0x' || substr(s, 1, 15))::BIGINT)::HUGEINT % 1152921504606846976)::BIGINT), 15, '0')
                    || lpad(format('{:x}', (sum(('0x' || substr(s, 16, 15))::BIGINT)::HUGEINT % 1152921504606846976)::BIGINT), 15, '0') hash
FROM h;
```

O resultado tem que ser igual ao da linha da tabela em `hashes.csv`. Se só o número de linhas
bater, o conteúdo difere. `particoes.csv` diz em que ano está a diferença.

## O que não está aqui

- **Os arquivos brutos baixados das fontes** e os endereços de onde vieram: os endereços não são
  publicados.
- **As versões antigas das linhas** que a fonte apagou ou alterou: ficam no registro de mudanças
  do espelho, que não é público.
