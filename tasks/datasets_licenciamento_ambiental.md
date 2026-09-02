# Datasets de licenciamento e poluição ambiental — o que falta raspar

> Aberto em 2026-09-01, saído do levantamento de poluentes atmosféricos de Nova
> Friburgo (`pages/analises/poluentes-do-ar-em-nova-friburgo/`, gerado por
> `scripts/gera_relatorio_nf.py`). Aquele relatório reconstrói "atividade
> potencialmente poluidora" **por CNAE**, porque não existe no espelho nenhuma
> base que diga quem é licenciado, com que número de processo, por qual órgão.
> Os campos ficaram explicitamente como "não pôde ser confirmado". Esta lista é o
> que fecharia cada buraco, em ordem de quanto fecha.
>
> Complementa `tasks/datasets_to_scrap.md` (o catálogo geral) — as entradas que
> saírem daqui para a fila de raspagem vão para lá.

## 1. INEA/RJ — licenças ambientais estaduais 🔴 o buraco central

**Fecha:** situação do licenciamento (LP/LI/LO), número do processo, número da
licença, validade, órgão, condicionantes.
**Onde:** portal do INEA (consulta pública de licenças ambientais) e publicações
de concessão no Diário Oficial do Estado do RJ (DOERJ).
**Chave de join:** CNPJ e/ou razão social + município.
**Por que importa:** hoje o relatório reporta *situação cadastral na Receita
Federal* e precisa avisar, em cada seção, que isso não é licenciamento. Com esta
base, quatro colunas do pedido original passam de "não confirmado" para dado.
**Risco:** consulta provavelmente com formulário/captcha; o caminho DOERJ (texto)
pode ser mais estável que o portal.

## 2. IBAMA — CTF/APP, Cadastro Técnico Federal de Atividades Potencialmente Poluidoras 🔴

**Fecha:** quem se declara atividade potencialmente poluidora, em que categoria e
porte — literalmente o universo que o relatório reconstrói por CNAE.
**Onde:** IBAMA dados abertos / relatórios do CTF-APP e TCFA.
**Chave:** CNPJ.
**Por que importa:** permite medir o erro do proxy por CNAE nos dois sentidos —
quem exerce a atividade sem estar cadastrado, e quem está cadastrado sob CNAE que
o recorte não pega. Também dá porte declarado, que o CNAE não dá.

## 3. IBAMA — autos de infração e sanções administrativas 🟠

**Fecha:** histórico de autuação ambiental por empresa, com tipificação (inclui
poluição atmosférica).
**Onde:** IBAMA dados abertos (autos de infração; distinto dos embargos).
**Chave:** CPF/CNPJ.
**Situação hoje:** o espelho tem só `br_ibama_embargos` — conferido, deu **zero**
para os 1.581 CNPJs do levantamento, em qualquer município do país. Embargo é
majoritariamente desmatamento; auto de infração é onde poluição industrial
apareceria.
**Nota técnica:** `br_ibama_embargos/termo_embargo/*.parquet` está gravado como
**uma coluna VARCHAR** com os campos separados por `;` — o CSV foi parseado
errado na raspagem. Reprocessar junto.

## 4. ANM / SIGMINE — títulos minerários 🟠

**Fecha:** número do processo oficial da categoria "extração de minerais não
metálicos" (20 ativos no levantamento), substância (areia, argila, brita,
granito), fase (requerimento / autorização de pesquisa / concessão de lavra /
guia de utilização), polígono e titular.
**Onde:** ANM dados abertos + SIGMINE (shapefile/CSV público, fácil de ETL).
**Chave:** CNPJ do titular + município + geometria.
**Bônus:** cruzar polígono com CNPJ revela lavra titulada sem CNPJ ativo
correspondente no município — e o contrário.

## 5. Diário Oficial de Nova Friburgo, texto completo 🟡 meio caminho andado

**Fecha:** licenciamento **municipal** de impacto local — que é competência da
prefeitura desde pelo menos 2012 (IBGE MUNIC), com LP/LI/LO concedidas.
**Situação hoje:** `br_ok_queridodiario.diarios` já tem **634 edições** de Nova
Friburgo (2023-10-17 a 2025-10-03) espelhadas — **mas só os metadados e a URL**.
Falta baixar o `txt_url` de cada edição e indexar o texto.
**Esforço:** baixo. 634 arquivos de texto, um índice full-text no DuckDB.
**Generaliza:** o mesmo passo serve para todos os municípios do Querido Diário —
vale fazer genérico, não só para Nova Friburgo.

## 7. PNCP — Portal Nacional de Contratações Públicas 🟡

**Fecha:** contrato com o poder público além do que o TCE-RJ registra.
**Situação hoje:** o cruzamento achou 6 empresas com contrato (4 via
`br_tce_rj.contratos_municipio`, 2 via `br_cgu_licitacao_contrato`). O TCE-RJ tem
96 mil contratos e o CGU só cobre o federal; o PNCP cobre contratação municipal
de todo o país pós-2021.

## 8. Emissões e qualidade do ar 🟢 contexto, não cadastro

- **SEEG / inventário municipal de emissões** — emissão estimada por município e
  setor. Liga o cadastro à grandeza física.
- **INEA — rede de monitoramento da qualidade do ar do RJ** — séries das
  estações. Nova Friburgo provavelmente não tem estação; confirmar.

**Por que importa:** hoje o relatório mede *fontes potenciais*, nunca poluente
emitido ou medido. Sem uma destas duas, não há como ligar "553 oficinas de
produtos de metal" a nenhuma concentração de poluente.

---

## Já conferido e negativo (não precisa raspar de novo)

| Base | Resultado no levantamento |
|---|---|
| `br_ibama_embargos` | 0 embargos, tanto no município quanto por CNPJ em todo o país |
| `br_tcu_inidoneos.empresas` | 0 dos 1.581 CNPJs |
| **RAIS identificada 2022+** | **Sem fonte pública — item removido da fila em 2026-09-01.** O FTP do PDET está no ar e tem até 2024 (`ftp.mtps.gov.br/pdet/microdados/RAIS/2024/`), mas publica só os arquivos `_PUB`, sem CNPJ; a versão identificada é restrita. Não é pendência de raspagem, é ausência de fonte |
| `br_pgfn_dividaativa.divida` | 237 empresas, 1.990 inscrições — **tudo tributário**, nenhuma inscrição de multa ambiental. Fora do relatório por ser off-topic |

---

## Execução — 2026-09-01

Levantamento de rota feito item a item, com teste real de rede em cada fonte.
O que estava marcado como "provavelmente com formulário/captcha" acabou sendo
outra coisa: **geo-bloqueio por IP**. Registro do que se descobriu:

### Rotas confirmadas e ETL feito

**ANM (item 4) — completo.** A URL antiga (`app.anm.gov.br/dadosabertos`) morreu;
a viva é `dadosabertos.anm.gov.br`, uma listagem IIS aberta, sem auth, regerada
diariamente. Três diretórios importam:

- `SCM/*.csv` — 13 arquivos com `Processo`, `Fase Atual`, `CPF/CNPJ do titular`,
  `Titular`, `Municipio(s)`, `Substância(s)`, `Situação`. É o item 4 inteiro.
- `CFEM/*.csv` — arrecadação e distribuição por CNPJ/substância/município/mês,
  **com `QuantidadeComercializada` e `ValorRecolhido`**. Não estava previsto: é
  grandeza física de extração, cobre parte do que o item 8 pedia.
- `SIGMINE/PROCESSOS_MINERARIOS/{UF}.zip` — shapefile por UF (polígono, fase,
  substância, titular). Sem CNPJ e sem coluna de município: o município vem do
  SCM, ou de join espacial.

Em `~/rodado/br_anm/`: 21 tabelas + 28 partições de UF do SIGMINE.

Três armadilhas de parsing, todas na origem, todas custaram tempo:
1. Os CSV são **CP1252**, não latin-1 puro — `read_csv(encoding='latin-1')` do
   DuckDB recusa o arquivo inteiro. Passar por `iconv -f CP1252 -c`.
2. `CFEM_Autuacao.csv` usa `;`; todo o resto usa `,`. Detectar por arquivo.
3. Há linhas com aspas duplicadas abrindo campo (`,""RAZAO SOCIAL`) que fundem
   dois registros em um. Com `ignore_errors=true` o DuckDB **descarta calado** e
   o resultado parece bom: `scm_licenciamento` deu 14.205 linhas assim, contra
   21.538 reais. A conversão hoje é um parser tolerante em Python
   (`_staging/anm/conv_anm4.py`) que repara a aspa e conta o que reparou.

### Bloqueio real: geo-IP, não captcha

`dadosabertos.ibama.gov.br`, `pamgia.ibama.gov.br` e `www.ibama.gov.br` devolvem
403 de WAF (Cloudflare) para **qualquer** requisição saindo de IP não brasileiro
— testado com curl e com Chrome real, do laptop e do beelink. O INEA é pior:
`inea.rj.gov.br` resolve (187.62.129.119) mas **não completa o TCP**.

O Wayback guardou só o catálogo CKAN, nunca os arquivos. O que ele deu de útil
foram os padrões de URL, que o portal bloqueado não entrega:

- CTF/APP: `https://dadosabertos.ibama.gov.br/dados/CTF/APP/{UF}/pessoasJuridicas.csv`
- CTF/AIDA: `.../dados/CTF/AIDA/pessoasJuridicas.csv`
- Autos: `.../dados/SIFISC/auto_infracao/{tabela}/{tabela}_csv.zip`
- Embargos: `.../dados/SIFISC/termo_embargo/{tabela}/{tabela}_csv.zip`

Com um proxy de saída no Brasil o download roda normalmente
(`~/Downloads/ibama/baixa_ibama.sh` respeita `ALL_PROXY`).

### Correção ao que este arquivo dizia

**`br_ibama_embargos` não é um negativo válido — é um espelho vazio.** O
problema não é só "uma coluna VARCHAR": `termo_embargo` tem 113.878 linhas com
**zero** não-vazias, `coordenadas` tem 64.562 com `max(length()) = 0`, e toda
subtabela repete o padrão. Os bytes nunca foram gravados. Logo:

- o "0 embargos para os 1.581 CNPJs" da tabela de conferidos não mediu nada;
- "reprocessar junto" não se aplica — não há o que reparsear localmente, é
  re-raspagem completa.

### SEEG (item 8): existe API, não documentada

`plataforma.seeg.eco.br` é um SPA; o dado sai de um GraphQL público em
`api.plataforma.seeg.eco.br/graphql`. A query que serve é `emissionsSummary`
com `ranking: "City"` — devolve **os 5.606 municípios de uma vez, por setor,
em ~6 s**. Detalhes que custaram descoberta:

- `emissions` (a query de aparência óbvia) responde **500** sempre, com ou sem
  filtro. Não usar.
- `emissionsRanking` devolve só o **top 30**, mesmo com `territoriesIds` de um
  estado. Serve para ranking, não para colheita.
- `areas(territoryTypes: [City])` traz `code` = código IBGE de 7 dígitos para os
  **5.608** municípios, sem exceção. É a chave de join com o espelho.

### INEA (item 1): tem dado estruturado, não só PDF

O portal `sistemas.inea.rj.gov.br` só serve tela de login, e as páginas de
licenciamento do site são menu e norma. Mas a página do **Boletim de Serviço**
carrega um índice pesquisável em HTML — e ele já traz o registro estruturado,
sem abrir PDF nenhum: número do boletim, data, os **processos SEI**, o **nome de
cada empresa/requerente** e o **tipo de ato** (`licença de operação`,
`licença ambiental unificada`, `licença prévia`, `indeferimento`…). O PDF é
anexo, não a fonte.

É formulário GET simples, sem AJAX e sem nonce:

```
GET https://www.inea.rj.gov.br/inea-licenciamento-pos-licenca-e-fiscalizacao/boletim-de-servico
    ?paged=N                    # 12 resultados por página
    &ic_b_document_type=<tipo>  # ex.: "licença de operação"
    &ic_data_inicio=DD/MM/AAAA&ic_data_fim=DD/MM/AAAA
    &ic_b_processo=<n do processo>
```

Colhido: **1.081 boletins, 28/01/2019 a 26/08/2026**, com 7.161 processos SEI e
6.877 empresas → `br_inea_boletim/{boletins,empresas,processos}`.

**Duas armadilhas que custaram um reparse.** A numeração do boletim **reinicia a
cada ano** — deduplicar por número colapsa `n158/2021` com `n158/2026` e some com
80% dos registros (226 no lugar de 1.081). A chave estável é a URL do PDF, que
carrega o ano no caminho (`/uploads/2021/11/`). E o rótulo da data vem colado ao
valor no texto limpo (`Data do boletim: 29/12/2025`), sem tag entre os dois:
regex que espera um `<tag>` no meio devolve `None` calado para todo o conjunto.

O acervo anterior a 2019 fica noutro lugar — `portalproderj.inea.rj.gov.br`,
ainda não raspado.

### SEEG: colhido

**12.106.780 linhas**, 5.601 municípios, 1990–2024, por setor e por subcategoria,
5 gases × 5 tipos de emissão → `br_seeg/emissoes_municipais`, particionado por
`agrupamento` e `gas_id`. O `code` da API (IBGE de 7 dígitos) entra como
`id_municipio` e liga direto com o resto do espelho.

---

## O que falta para fechar — situação em 2026-09-01, 20h

### Ainda baixando (só tempo, nenhuma decisão pendente)

| Item | Onde parou | Falta | Depois |
|---|---|---|---|
| Querido Diário (5) | 398/524 municípios | 126 municípios | `_staging/qd/finaliza_qd.sh` move para `br_ok_queridodiario_texto/` |
| PNCP (7) | jul/2024 | 77 janelas de 10 dias (de 206) | `_staging/pncp/converte_pncp.py` |

### Lacunas que não fecham sozinhas

1. **INEA anterior a 2019.** O índice pesquisável do Boletim de Serviço começa em
   28/01/2019. O acervo velho está em `portalproderj.inea.rj.gov.br` — outro
   sistema, que **não responde nem pelo proxy BR** (timeout, 2026-09-01). Pode
   estar desativado. Enquanto isso, o item 1 cobre 2019–2026, não a série toda.

2. **`tipos_documento` mal parseado.** O split por espaço duplo não separa a
   lista de tipos: dá 142 "indeferimento" e 34 "autorização ambiental" para 1.081
   boletins, ordem de grandeza abaixo do esperado. Os campos que importam
   (empresa, processo SEI, data, PDF) estão corretos — este é o único errado.
   Reparse é de graça: os HTML estão em `~/Downloads/inea/boletins/pg*.html`.

3. **Os 1.081 PDFs do INEA não foram baixados**, só o índice. É neles que estão
   **validade da licença e condicionantes** — dois dos campos que o relatório de
   Nova Friburgo pedia e que o índice não traz.

4. **`SIGMINE/BRASIL.zip` (125 MB) foi pulado de propósito** — consolidado
   nacional, redundante com as 28 UFs já convertidas. Registro para não parecer
   falha de coleta.

5. **Qualidade do ar (item 8, segunda metade) não foi tocada.** O SEEG fechou a
   parte de emissão estimada; a rede de monitoramento do INEA continua sem
   raspar, e segue sem confirmar se Nova Friburgo tem estação.

### Placar

| Dataset | Linhas | Período |
|---|---|---|
| `br_ibama_ctf` | 1.473.755 | ~1985–2025 |
| `br_ibama_autos` | 3.021.141 | 1977–2026 |
| `br_ibama_embargos_novo` | 892.279 | 2001–2026 |
| `br_anm` (21 tab + 28 UF) | 8.324.108 | processos desde 1935 |
| `br_seeg/emissoes_municipais` | 12.106.780 | 1990–2024, 5.601 municípios |
| `br_inea_boletim` | 1.081 boletins · 7.161 processos · 6.877 empresas | 2019–2026 |

**25.818.344 linhas em 6 datasets novos.**

`br_ibama_embargos` (o antigo, vazio) continua no disco e **deve ser removido ou
marcado como obsoleto** — quem consultar ele em vez de `br_ibama_embargos_novo`
recebe zero e acha que é resposta.
