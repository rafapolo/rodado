# beelink: `~/.duckdbrc` e a trava de arquivo

Desde 2026-10-04, o llama-server (Gemma, `127.0.0.1:8099`) não fica mais
sempre no ar: sobe com `~/bin/llama-on` e desce com `~/bin/llama-off`
(argumentos em `~/llm/llama-server.args`, log em `~/llm/llama-server.log`). Os
dois chamam `~/bin/duckdb-modo`, que ajusta o `~/.duckdbrc`: com o modelo no
ar, `memory_limit = '8GB'` e `threads = 8` (o limite é **por processo**, e o
llama-server ocupa ~20 dos 27 GB); sem ele, `'16GB'` e `14` threads (de 16). O
harness (branch `harness-gemma`) precisa de `llama-on` antes.

O `~/.duckdbrc` tem ainda `enable_progress_bar = false`,
`autoinstall_known_extensions = false` e o despejo em `~/duckdb_tmp` no NVMe,
com teto de 100 GB. O `SECRET healthbr` vem entre `.output /dev/null` e
`.output`: sem isso o `CREATE SECRET` imprime uma tabela no stdout de toda
sessão e quebra o `-json` do `run_sql` e do harness. **Nunca** apontar
`temp_directory` para `/dev/shm` nem `/tmp`: os dois são tmpfs, e despejar lá
é despejar na RAM. Em 2026-09-24 havia 10 GB de despejo órfão em `/dev/shm`
com o swap 100% cheio, e o OOM killer matou o llama-server. Nenhuma chave vai
no `.duckdbrc`.

`mcp_server.py` com `MCP_BACKEND=ssh` (`_run_sql_ssh`) — e `harness/beelink.ts`,
no branch `harness-gemma` — abrem cada sessão com `allowed_directories` em
`~/rodado` e `~/duckdb_tmp`, o prefixo `s3://healthbr-data/`,
`enable_external_access=false` e `lock_configuration=true`: a SQL vem de um
modelo, e um `SELECT * FROM read_text('~/.ssh/...')` passa pela checagem de
somente-leitura. Ferramenta nova que leia fora de `~/rodado` precisa entrar na
lista, não desligar a trava.

**View com nomes de coluna velhos** (parquet corrigido depois de criar a
view) — procedimento completo e exemplos em `docs/tecnico/housekeeping.md`,
item 10.
