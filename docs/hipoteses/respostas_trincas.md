# Hipóteses 2/3 — as trincas de família, o painel estendido e o grafo de identificadores

Companheiro de [`respostas.md`](respostas.md), com uma diferença de método: lá
as perguntas foram escritas uma a uma e respondidas uma a uma; aqui **o espaço
inteiro foi enumerado e rodado de uma vez**, em duas rodadas sucessivas.

O que tornou isso possível não foi capacidade de máquina, foi enxergar que
**uma trinca de famílias é um trio de colunas do painel municipal** — e o
painel já estava extraído do beelink pelas rodadas anteriores. A primeira
rodada (h2) fundiu três painéis (`20260906`, `inedito`, `familias`) em 5.571
municípios × 270 colunas e rodou as **1.330 trincas** que isso permitia, em
8 segundos, sem tocar no beelink. A segunda (h3) estendeu o painel para
**358 colunas** (37 datasets novos — ENEM, Censo Escolar, SEEG, MapBiomas,
ESTBAN, BNDES, SIA, ANS, SISVAN, Imunizações, filiação partidária) e abriu um
**segundo eixo**, o do grafo de identificadores CNPJ/CPF, que a cascata F0–F7
de [`tasks/hipoteses.md`](../../tasks/hipoteses.md) nunca contava por exigir
chave territorial.

## Método

- **Spearman**, nunca Pearson cru — distribuição municipal tem cauda pesada.
- **Parcial** residualizando `log(população)`, `log(PIB per capita)`,
  **`log(área)`** e efeito fixo de UF. A log-área entra *sempre*, não só quando
  as duas pernas são extensivas: metade do painel é normalizada por hectare ou
  por área, e o `1/área` compartilhado produz correlação sozinho.
- Só colunas **intensivas** (taxa, share, per capita, índice): 107 colunas em
  21 famílias na rodada h2; **149 colunas em 22 famílias** na h3 (entra
  `politica`, com a filiação partidária do TSE — filiado vivo por município,
  número efetivo de partidos, HHI partidário —, que sozinha abre **210 trincas**
  novas). Contagem crua correlaciona com o tamanho do município.
- **Benjamini-Hochberg** sobre os pares testados. Rodar milhares de pares e
  reportar o maior |r| sem correção é garimpo de ruído, não achado.
- Piso de `|r_parcial| ≥ 0,10` (o mesmo do glifo 🟠 do documento irmão),
  `q < 0,01` e `n ≥ 500`.

**Eixo de força idêntico ao de [`respostas.md`](respostas.md)**:
🟢 forte (≥ 0,50) · 🟡 moderada (0,30–0,50) · 🟠 fraca (0,10–0,30) · ⚪ nula.
A força da trinca é a da **perna mais fraca** — uma hipótese de três pernas vale
o que vale seu elo mais frouxo. Aqui ⚪ tem um sentido preciso: **ao menos uma
das três pernas não sobrevive ao controle**, então a trinca não se sustenta como
hipótese de três vias — mesmo quando uma das outras pernas é forte, e a linha
mostra qual.

## Validação — o pipeline reproduz o que já estava publicado

Rodando às cegas (rodada h2) contra os achados da rodada 2026-09-05
(tabela `B` de `respostas.md`):

| Achado | Publicado | Aqui |
|---|---|---|
| B2 densidade agropecuária × cobertura 4G/5G | −0,55 | **−0,55** |
| B7 penetração do Pix × densidade agropecuária | −0,45 | **−0,45** |
| B6 ticket do Pix × cobertura do Bolsa Família | −0,37 | **−0,37** |
| B4 geração distribuída × cobertura do Bolsa Família | −0,34 | **−0,34** |
| B11 templos por domicílio × cobertura do Bolsa Família | +0,22 | **+0,22** |
| B5 alerta DETER × autos do IBAMA | +0,36 | +0,32 |

Cinco de seis batem na segunda casa. O B5 é o que difere, e a diferença é
informativa: é o único par em que as duas pernas dependem de área, e é
exatamente o efeito que a log-área desconta.

## O que a corrida achou

| | h2 (270 colunas) | h3 (358 colunas) |
|---|---|---|
| pares testados | 5.325 | **10.279** |
| pares que sobrevivem às guardas | 995 | **1.950** → 1.491 após a 3ª guarda |
| trincas de família | 1.330 | **1.540** |
| pares acima de \|r\| = 0,50 | 3 | **1** |
| trincas 🟢 forte (elo mais fraco ≥ 0,50) | 0 (0%) | — |
| trincas 🟡 moderada | 44 (3%) | — |
| trincas 🟠 fraca | 808 (61%) | — |
| trincas ⚪ nula | 478 (36%) | — |

A h3 não recontou a força por **trinca** (só por par — ver tabela abaixo);
a distribuição de força dos pares, porém, é "a mesma da rodada anterior": o
espelho continua sendo um objeto de correlações fracas sob controle.

**O resultado principal é negativo, e é o mais informativo que estas corridas
podiam produzir**: depois de descontar porte, renda, área e UF, praticamente
nada passa de |r| = 0,50 em nenhuma das duas rodadas. Isso **não** desqualifica
os achados de `achados_fortes.md` — ele já reportava parciais, e são os mesmos
números. O que a enumeração completa acrescenta é o denominador: agora dá para
dizer que os achados fortes publicados são fortes *em relação a um espaço de
milhares de hipóteses testadas*, não apenas fortes entre as que alguém pensou
em perguntar.

## Guardas — o que foi excluído, e por quê

Sem estas guardas a corrida devolveria artefato como descoberta. São três,
e a terceira só nasceu na h3, quando o painel estendido trouxe INSE e IDHM
para perto do IVS:

- **duplicata conceitual** (8 pares na h2) — a mesma grandeza por duas fontes.
  `sic_pessoal_pc` × `mides_valor_pc` (+0,69) é gasto municipal per capita
  medido por SICONFI *e* MIDES; `pdm_share` × `nbf_share_dom` (+0,60) é o
  Pé-de-Meia, que **exige CadÚnico** — correlacioná-lo com o Bolsa Família é
  desenho de programa, não achado. A h3 ampliou a lista: cobertura de atenção
  básica e de vacina também aparecem em duplicata (IEPS × Ministério da
  Saúde). Lista completa em
  [`scripts/hipoteses/h2_familias_colunas.yaml`](../../scripts/hipoteses/h2_familias_colunas.yaml).
- **métrica de registro** (14 colunas na h2, 438 sobreviventes marcados `⚠`
  na h3) — a coluna mede a capacidade de registrar antes do fenômeno.
  `snis_gap_agua` é a razão entre a água *declarada* ao SNIS e a medida pelo
  IBGE; notificação de arbovirose mede vigilância instalada. **A nota do ENEM
  entrou aqui na h3** por um motivo específico do espelho:
  `id_municipio_residencia` existe e está **100% nula em todos os anos**, então
  a agregação é por município de **prova**, não de residência — a média é a
  dos alunos da região inteira que foram prestar prova no polo.
- **mesmo construto** (21 sobreviventes marcados, só na h3) — guarda nova,
  nascida quando o topo da corrida virou IVS × INSE × IDHM × cobertura do
  Bolsa Família. Não são a mesma fonte, mas são o mesmo construto latente:
  "quão pobre é este município". Publicar isso como descoberta seria
  constrangedor. É esta guarda que derrubou o que era o achado mais forte da
  h2 (IVS 2010 × Bolsa Família, +0,51) — reclassificado como a mesma coisa
  medida duas vezes, não uma correlação de fato. Um par que **sai** desse
  grupo para um desfecho de verdade (IVS × nota do ENEM) segue valendo.

## A fronteira — famílias sem coluna no painel

Com a estreia de `politica` na h3, seis famílias seguem sem nenhuma coluna:

- **ciencia_tecnologia** — CNPq/CAPES bolsas -- municipal, extraivel
- **comercio_exterior** — COMEX municipio -- municipal, extraivel
- **mobilidade** — frota/ANTT -- municipal, extraivel
- **seguranca** — SINESP/FBSP -- so UF, cortado pelo filtro F1 da cascata
- **justica** — CNJ/improbidade -- so UF, cortado por F1
- **precos_indices** — series nacionais -- sem grao municipal, cortado por F1

As 3 primeiras são municipais e extraíveis: entram numa próxima rodada. As 3
últimas são só UF, e a cascata F1 de [`tasks/hipoteses.md`](../../tasks/hipoteses.md)
já as cortava — n=27 não sustenta parcial com efeito fixo.

## Os achados no topo (h3, painel de 358 colunas)

Substitui a listagem da h2 — mesmo método, painel maior, praticamente os
mesmos pares no topo (é a validação cega de novo). `(já conhecido)` marca o
que já estava em `achados_fortes.md`.

| r parcial | bruto | n | par | leitura |
|---|---|---|---|---|
| **−0,51** | −0,37 | 5.390 | `sicor_hhi_tomador` × `agro_1000dom` | Onde há mais agropecuária, o crédito rural é **menos** concentrado num único tomador — fenômeno de município pouco agrícola, não da região produtora |
| **+0,49** | +0,53 | 5.538 | `desmat_share` × `bov_por_ha` | *(já conhecido — A2/T10-3)* Sobrevive ao controle de área |
| **+0,48** | +0,21 | 5.370 | `sicor_hhi_tomador` × `cafir_ha_por_imovel` | **Supressão**: bruto +0,21, parcial +0,48 — onde o imóvel médio é maior, o crédito rural concentra |
| **+0,48** | +0,61 | 5.564 | `cno_1000dom` × `gd_por_domicilio` | Obra registrada no CNO e geração solar medem a mesma coisa por caminhos independentes: quem investe no próprio imóvel |
| **+0,47** | +0,81 | 5.565 | `idhm_2010` × `cob_priv` | Plano de saúde é marcador de desenvolvimento, não de oferta médica |
| **+0,47** | +0,30 | 5.363 | `cred_ha` × `agro_1000dom` | **Supressão** (+0,30 → +0,47) |
| **+0,47** | +0,62 | 5.564 | `formal_obra` × `gd_por_domicilio` | Mesmo padrão do CNO×solar, por outra medida de formalidade |
| **−0,47** | −0,38 | 5.390 | `sicor_share_top` × `agro_1000dom` | Mesmo padrão do primeiro da lista |
| **+0,46** | +0,24 | 5.370 | `sicor_share_top` × `cafir_ha_por_imovel` | Mesmo padrão do terceiro da lista |
| **−0,45** | −0,63 | 5.570 | `agro_1000dom` × `cobertura_pop_4g5g` | *(já conhecido — B2)* O campo segue sendo o bolsão não conectado |
| **+0,45** | +0,54 | 5.456 | `credito_ha` × `desmat_share` | *(já conhecido — C1/T17-3)* Sobrevive à log-área |
| **−0,45** | −0,58 | 5.570 | `cobertura_pop_4g5g` × `share_docente_rural` | Novo na h3: conectividade prediz composição do corpo docente rural |

O par mais forte da h2 (IVS × geração solar, −0,43) e a nota sobre
**concentração onomástica × pagamento municipal** (+0,07 bruto → +0,32
parcial, n=3.336 — proxy de sociedade local fechada, tratar como pista, não
achado) continuam valendo; não foram retestados explicitamente na h3.

## O segundo eixo — político → sociedade → papel da empresa

Este é o caminho que motivou a rodada h3, e ele funciona. O casamento é
`TSE candidatos` (CPF completo + nome) contra `br_me_cnpj.socios` (CPF
**mascarado** `***123456**` + nome), pela mesma técnica do T37-3: nome
normalizado mais os 6 dígitos visíveis.

**A ressalva vem antes do número, porque ela manda no resultado.** O par
(nome, 6 dígitos) não é identificador único: **58,8% dos casamentos brutos são
ambíguos** — homônimo com os mesmos 6 dígitos — e saem do agregado. O que sobra
é uma lista para conferência, não um cadastro de fato. E "político" aqui é
*candidato desde 2014*, não eleito: são 1.384.616 pessoas.

A comparação é **dentro** do conjunto de empresas com algum papel, não contra a
população geral — candidato é mais velho, mais rico e mais urbano que a média, e
essas três coisas já predizem ser sócio de empresa.

Taxa-base: **0,33%** das 9.255.368 empresas com algum papel têm sócio-político.

| papel | empresas | com sócio-político | taxa | lift |
|---|---|---|---|---|
| `cepim` | 1.935 | 82 | 4,24% | **12,78** |
| `siconv_fornecedor_obra` | 10.076 | 131 | 1,30% | **3,92** |
| `sicor_mutuario_rural` | 6.456 | 75 | 1,16% | **3,50** |
| `ibama_embargado` | 12.705 | 142 | 1,12% | **3,37** |
| `ceis` | 7.200 | 63 | 0,88% | **2,64** |
| `tce_rj_contratado_municipio` | 18.088 | 155 | 0,86% | **2,58** |
| `salic_cultura` | 51.585 | 441 | 0,85% | **2,58** |
| `outorga_agua_captacao` | 13.538 | 110 | 0,81% | **2,45** |
| `cnep` | 866 | 7 | 0,81% | **2,44** |
| `cfem_arrecadador` | 10.384 | 82 | 0,79% | **2,38** |
| `ibama_autuado` | 89.544 | 704 | 0,79% | **2,37** |
| `pncp_fornecedor` | 388.733 | 2.996 | 0,77% | **2,32** |
| `camara_fornecedor` | 110.230 | 760 | 0,69% | **2,08** |
| `geracao_distribuida` | 261.888 | 1.742 | 0,67% | **2,01** |

## Todos os pares de papel sobre o mesmo CNPJ

499 pares acima do piso de 30 empresas em comum, dos quais **24 são
definicionais** e saem da lista: vencedor de licitação é subconjunto de
participante, embargo do IBAMA nasce de um auto de infração, SICAF é
pré-requisito para vender à União, CEIS e CNEP são cadastros de sanção que se
sobrepõem. Sem essa quarta guarda, os 18 maiores lifts da corrida são todos
variações de "A implica B por desenho do processo". Sobram **475**.

A medida **não é correlação** — é *lift*, `P(B|A) ÷ P(B)`: quantas vezes mais
provável é a empresa que faz A também fazer B, comparada a uma empresa
qualquer. Dois denominadores são reportados sempre (cadastro inteiro e
empresas-com-papel), porque escolher um e omitir o outro é como se fabrica
manchete falsa com dado verdadeiro. E o `or_mh_cnae_idade` é o Mantel-Haenszel
estratificado por divisão CNAE e tercil de idade da empresa — o análogo do
parcial: quando ele desaba, o achado era porte e setor.

| lift | MH (CNAE×idade) | empresas em comum | P(B\|A) | par |
|---|---|---|---|---|
| **109,6** | 291,3 | 706 | 21,4% | `bps_fornecedor_saude` × `tce_rj_contratado_municipio` |
| **56,7** | 264,9 | 17.891 | 16,2% | `camara_fornecedor` × `senado_ceaps_fornecedor` |
| **153,8** | 220,4 | 306 | 4,2% | `ceis` × `terceirizacao_federal` |
| **75,7** | 188,4 | 230 | 5,3% | `bndes_nao_automatica` × `sicor_mutuario_rural` |
| **80,3** | 166,1 | 206 | 6,2% | `bps_fornecedor_saude` × `ceis` |
| **26,9** | 161,2 | 5.913 | 7,7% | `revenda_combustivel` × `senado_ceaps_fornecedor` |
| **125,3** | 158,3 | 30 | 3,5% | `cnep` × `terceirizacao_federal` |
| **17,5** | 155,3 | 7.409 | 1,9% | `pncp_fornecedor` × `siconv_fornecedor_obra` |
| **20,2** | 147,7 | 18.520 | 16,8% | `camara_fornecedor` × `revenda_combustivel` |
| **42,3** | 117,9 | 595 | 8,3% | `ceis` × `tce_rj_contratado_municipio` |
| **152,3** | 117,0 | 170 | 6,8% | `bcb_penalidade` × `outorga_agua_lancamento` |
| **14,5** | 108,2 | 11.045 | 2,8% | `pncp_fornecedor` × `tce_rj_contratado_municipio` |
| **12,7** | 104,7 | 1.363 | 0,4% | `pncp_fornecedor` × `terceirizacao_federal` |
| **8,2** | 98,9 | 11.963 | 1,6% | `sicaf_habilitado` × `tce_rj_contratado_municipio` |
| **102,1** | 98,8 | 964 | 7,1% | `outorga_agua_captacao` × `sicor_mutuario_rural` |

`ceis`/`cnep` × `terceirizacao_federal` (lift 154×/125×, MH 220/158) é o
achado mais forte das duas rodadas: sancionado não só não é filtrado da
terceirização federal, ele está **concentrado** ali muito além do acaso.

## Como refazer

```bash
# rodada h2 — trincas territoriais sobre o painel de 270 colunas
python3 scripts/hipoteses/h2_00_painel_mestre.py     # 3 painéis -> painel_mestre.csv (5.571 × 270)
python3 scripts/hipoteses/h2_10_roda_trincas.py      # -> pares.csv + trincas.csv (8s)
python3 scripts/hipoteses/h2_20_escreve_respostas.py # gera a seção de trincas deste arquivo

# rodada h3 — extração no beelink (offline, retomável por sentinela)
mkdir -p /tmp/h3 && cp scripts/hipoteses/h3_*.sql scripts/hipoteses/h3_roda.sh /tmp/h3/
scp -r /tmp/h3 beelink:~/hipoteses3 && ssh beelink 'cd ~/hipoteses3 && bash h3_roda.sh'
scp -r beelink:~/rodado_hipoteses/h3_<data> tasks/hipoteses_resultado/

# rodada h3 — análise local
python3 scripts/hipoteses/h3_10_estende_painel.py    # painel 270 -> 358 colunas
python3 scripts/hipoteses/h3_40_roda_trincas.py      # eixo território
python3 scripts/hipoteses/h3_20_matriz_cnpj.py       # eixo identificador
python3 scripts/hipoteses/h3_30_politico_empresa.py  # a ponte
python3 scripts/hipoteses/h3_50_escreve.py           # gera as duas últimas seções acima
```

O mapa coluna→família vive em
[`scripts/hipoteses/h2_familias_colunas.yaml`](../../scripts/hipoteses/h2_familias_colunas.yaml)
(h2) e [`scripts/hipoteses/h3_familias_colunas.yaml`](../../scripts/hipoteses/h3_familias_colunas.yaml)
(h3, complementa o primeiro) — o elo que faltava: `docs/context/familias.yaml`
mapeia dataset→família, o painel tem coluna, e ninguém mapeava coluna→família.
Editar o YAML, nunca a saída.

## As 1.330 trincas (rodada h2, painel de 270 colunas)

Código `U####`, força pela perna mais fraca, e as pernas que sobreviveram com a
coluna exata que as mediu. Ordenadas por família. **Esta listagem não foi
regerada no painel estendido da h3** (que abre 1.540 trincas, não 1.330) —
a h3 só reporta pares e trincas agregados, não a lista completa trinca a
trinca; refazer a listagem completa exigiria adaptar `h2_20_escreve_respostas.py`
para ler o painel de 358 colunas, o que não foi feito.

- **U0001 ✅ 🟠** administracao × agropecuaria × compras_publicas — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563)
- **U0002 ✅ ⚪** administracao × agropecuaria × conectividade — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) — 2/3 pernas sobrevivem ao controle
- **U0003 ✅ 🟠** administracao × agropecuaria × credito_financeiro — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570)
- **U0004 ✅ 🟠⚠** administracao × agropecuaria × cultura_consumo — `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0005 ✅ 🟠** administracao × agropecuaria × demografia_censo — `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0006 ✅ ⚪** administracao × agropecuaria × desmatamento_clima — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) — 2/3 pernas sobrevivem ao controle
- **U0007 ✅ 🟠** administracao × agropecuaria × educacao — `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `ies_pc`×`agro_1000dom` **+0,19** (n=719) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563)
- **U0008 ✅ 🟠** administracao × agropecuaria × fiscal_municipal — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536)
- **U0009 ✅ 🟠⚠** administracao × agropecuaria × fiscalizacao_ambiental — `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) · `emb_100k`×`pevs_share` **-0,11** (n=1.317)
- **U0010 ✅ 🟠** administracao × agropecuaria × fundiario — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563)
- **U0011 ✅ 🟠** administracao × agropecuaria × mineracao_energia — `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0012 ✅ ⚪** administracao × agropecuaria × mortalidade — `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0013 ✅ 🟠⚠** administracao × agropecuaria × natalidade — `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0014 ✅ 🟠⚠** administracao × agropecuaria × sancao_integridade — `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0015 ✅ 🟠⚠** administracao × agropecuaria × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0016 ✅ 🟠⚠** administracao × agropecuaria × saude_producao — `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `cob_priv`×`ebt_nota` **+0,15** (n=665)
- **U0017 ✅ 🟠** administracao × agropecuaria × trabalho_empresa — `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563)
- **U0018 ✅ 🟠⚠** administracao × agropecuaria × transferencia_renda — `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0019 ✅ ⚪** administracao × agropecuaria × vigilancia_sinan — `va_agro_ha`×`munic_vinc_pc` **-0,18** (n=5.563) — 1/3 pernas sobrevivem ao controle
- **U0020 ✅ ⚪** administracao × compras_publicas × conectividade — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339) — 2/3 pernas sobrevivem ao controle
- **U0021 ✅ 🟠** administracao × compras_publicas × credito_financeiro — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570)
- **U0022 ✅ 🟠⚠** administracao × compras_publicas × cultura_consumo — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0023 ✅ 🟠** administracao × compras_publicas × demografia_censo — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339)
- **U0024 ✅ ⚪** administracao × compras_publicas × desmatamento_clima — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063) — 2/3 pernas sobrevivem ao controle
- **U0025 ✅ 🟠** administracao × compras_publicas × educacao — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547)
- **U0026 ✅ 🟠** administracao × compras_publicas × fiscal_municipal — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330)
- **U0027 ✅ 🟠⚠** administracao × compras_publicas × fiscalizacao_ambiental — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340)
- **U0028 ✅ 🟠** administracao × compras_publicas × fundiario — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0029 ✅ 🟠** administracao × compras_publicas × mineracao_energia — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0030 ✅ ⚪** administracao × compras_publicas × mortalidade — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) — 1/3 pernas sobrevivem ao controle
- **U0031 ✅ 🟠⚠** administracao × compras_publicas × natalidade — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `cesarea`×`share_credor_local` **+0,17** (n=780) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0032 ✅ 🟠⚠** administracao × compras_publicas × sancao_integridade — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0033 ✅ 🟠⚠** administracao × compras_publicas × saneamento_agua — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0034 ✅ 🟠⚠** administracao × compras_publicas × saude_producao — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `cob_priv`×`ebt_nota` **+0,15** (n=665)
- **U0035 ✅ 🟠** administracao × compras_publicas × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542)
- **U0036 ✅ 🟠⚠** administracao × compras_publicas × transferencia_renda — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0037 ✅ ⚪⚠** administracao × compras_publicas × vigilancia_sinan — `mides_credores_pc`×`munic_vinc_pc` **+0,25** (n=3.339) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) — 2/3 pernas sobrevivem ao controle
- **U0038 ✅ ⚪** administracao × conectividade × credito_financeiro — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0039 ✅ ⚪⚠** administracao × conectividade × cultura_consumo — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `reclam_100k`×`ebt_nota` **+0,13** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0040 ✅ ⚪** administracao × conectividade × demografia_censo — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U0041 ✅ ⚪** administracao × conectividade × desmatamento_clima — `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0042 ✅ ⚪** administracao × conectividade × educacao — `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `sisu_pc`×`ibc` **+0,14** (n=551) — 2/3 pernas sobrevivem ao controle
- **U0043 ✅ ⚪** administracao × conectividade × fiscal_municipal — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) — 1/3 pernas sobrevivem ao controle
- **U0044 ✅ ⚪⚠** administracao × conectividade × fiscalizacao_ambiental — `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 1/3 pernas sobrevivem ao controle
- **U0045 ✅ ⚪** administracao × conectividade × fundiario — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U0046 ✅ ⚪** administracao × conectividade × mineracao_energia — `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U0047 ✅ ⚪** administracao × conectividade × mortalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0048 ✅ ⚪⚠** administracao × conectividade × natalidade — `cesarea`×`ibc` **+0,15** (n=1.733) · `mae_adol`×`ebt_nota` **-0,12** (n=630) — 2/3 pernas sobrevivem ao controle
- **U0049 ✅ ⚪⚠** administracao × conectividade × sancao_integridade — `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0050 ✅ ⚪⚠** administracao × conectividade × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `atlas_individual`×`ebt_nota` **-0,12** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0051 ✅ ⚪⚠** administracao × conectividade × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `cob_priv`×`ebt_nota` **+0,15** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0052 ✅ ⚪** administracao × conectividade × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0053 ✅ ⚪⚠** administracao × conectividade × transferencia_renda — `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) — 2/3 pernas sobrevivem ao controle
- **U0054 ✅ ⚪⚠** administracao × conectividade × vigilancia_sinan — `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) — 1/3 pernas sobrevivem ao controle
- **U0055 ✅ 🟠⚠** administracao × credito_financeiro × cultura_consumo — `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0056 ✅ 🟠** administracao × credito_financeiro × demografia_censo — `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570)
- **U0057 ✅ ⚪** administracao × credito_financeiro × desmatamento_clima — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0058 ✅ 🟠** administracao × credito_financeiro × educacao — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570)
- **U0059 ✅ 🟠** administracao × credito_financeiro × fiscal_municipal — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570)
- **U0060 ✅ 🟠⚠** administracao × credito_financeiro × fiscalizacao_ambiental — `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) · `cred_ha`×`autos_100k` **-0,12** (n=4.150)
- **U0061 ✅ 🟠** administracao × credito_financeiro × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570)
- **U0062 ✅ 🟠** administracao × credito_financeiro × mineracao_energia — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0063 ✅ ⚪** administracao × credito_financeiro × mortalidade — `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0064 ✅ 🟠⚠** administracao × credito_financeiro × natalidade — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0065 ✅ 🟠⚠** administracao × credito_financeiro × sancao_integridade — `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0066 ✅ 🟠⚠** administracao × credito_financeiro × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0067 ✅ 🟠⚠** administracao × credito_financeiro × saude_producao — `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `cob_priv`×`ebt_nota` **+0,15** (n=665)
- **U0068 ✅ 🟠** administracao × credito_financeiro × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570)
- **U0069 ✅ 🟠⚠** administracao × credito_financeiro × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0070 ✅ ⚪⚠** administracao × credito_financeiro × vigilancia_sinan — `pix_penetracao`×`munic_vinc_pc` **+0,17** (n=5.570) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0071 ✅ 🟠⚠** administracao × cultura_consumo × demografia_censo — `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0072 ✅ ⚪⚠** administracao × cultura_consumo × desmatamento_clima — `reclam_100k`×`ebt_nota` **+0,13** (n=665) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0073 ✅ 🟠⚠** administracao × cultura_consumo × educacao — `ies_pc`×`relig_100k` **+0,28** (n=719) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0074 ✅ ⚪⚠** administracao × cultura_consumo × fiscal_municipal — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `reclam_100k`×`ebt_nota` **+0,13** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0075 ✅ ⚪⚠** administracao × cultura_consumo × fiscalizacao_ambiental — `reclam_100k`×`ebt_nota` **+0,13** (n=665) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 2/3 pernas sobrevivem ao controle
- **U0076 ✅ 🟠⚠** administracao × cultura_consumo × fundiario — `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0077 ✅ 🟠⚠** administracao × cultura_consumo × mineracao_energia — `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0078 ✅ ⚪⚠** administracao × cultura_consumo × mortalidade — `reclam_100k`×`ebt_nota` **+0,13** (n=665) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563) — 2/3 pernas sobrevivem ao controle
- **U0079 ✅ 🟠⚠** administracao × cultura_consumo × natalidade — `cesarea`×`relig_100k` **+0,23** (n=1.733) · `reclam_100k`×`ebt_nota` **+0,13** (n=665) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0080 ✅ 🟠⚠** administracao × cultura_consumo × sancao_integridade — `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `reclam_100k`×`ebt_nota` **+0,13** (n=665) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0081 ✅ 🟠⚠** administracao × cultura_consumo × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `reclam_100k`×`ebt_nota` **+0,13** (n=665) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0082 ✅ 🟠⚠** administracao × cultura_consumo × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `cob_priv`×`ebt_nota` **+0,15** (n=665) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0083 ✅ 🟠⚠** administracao × cultura_consumo × trabalho_empresa — `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0084 ✅ 🟠⚠** administracao × cultura_consumo × transferencia_renda — `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) · `reclam_100k`×`ebt_nota` **+0,13** (n=665)
- **U0085 ✅ ⚪⚠** administracao × cultura_consumo × vigilancia_sinan — `reclam_100k`×`ebt_nota` **+0,13** (n=665) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0086 ✅ ⚪** administracao × demografia_censo × desmatamento_clima — `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U0087 ✅ 🟠** administracao × demografia_censo × educacao — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547)
- **U0088 ✅ 🟠** administracao × demografia_censo × fiscal_municipal — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537)
- **U0089 ✅ ⚪⚠** administracao × demografia_censo × fiscalizacao_ambiental — `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 2/3 pernas sobrevivem ao controle
- **U0090 ✅ 🟠** administracao × demografia_censo × fundiario — `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0091 ✅ 🟠** administracao × demografia_censo × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0092 ✅ ⚪** administracao × demografia_censo × mortalidade — `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U0093 ✅ 🟠⚠** administracao × demografia_censo × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0094 ✅ 🟠⚠** administracao × demografia_censo × sancao_integridade — `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0095 ✅ 🟠⚠** administracao × demografia_censo × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0096 ✅ 🟠⚠** administracao × demografia_censo × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `cob_priv`×`ebt_nota` **+0,15** (n=665)
- **U0097 ✅ 🟠** administracao × demografia_censo × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542)
- **U0098 ✅ 🟠⚠** administracao × demografia_censo × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0099 ✅ ⚪⚠** administracao × demografia_censo × vigilancia_sinan — `share_nome_top`×`munic_vinc_pc` **+0,29** (n=5.565) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) — 2/3 pernas sobrevivem ao controle
- **U0100 ✅ ⚪** administracao × desmatamento_clima × educacao — `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `ies_pc`×`desmat_share` **+0,16** (n=719) — 2/3 pernas sobrevivem ao controle
- **U0101 ✅ ⚪** administracao × desmatamento_clima × fiscal_municipal — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) — 1/3 pernas sobrevivem ao controle
- **U0102 ✅ ⚪⚠** administracao × desmatamento_clima × fiscalizacao_ambiental — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 2/3 pernas sobrevivem ao controle
- **U0103 ✅ ⚪** administracao × desmatamento_clima × fundiario — `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U0104 ✅ ⚪** administracao × desmatamento_clima × mineracao_energia — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U0105 ✅ ⚪** administracao × desmatamento_clima × mortalidade — `infec_100k`×`desmat_share` **+0,11** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0106 ✅ ⚪⚠** administracao × desmatamento_clima × natalidade — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `mae_adol`×`ebt_nota` **-0,12** (n=630) — 2/3 pernas sobrevivem ao controle
- **U0107 ✅ ⚪⚠** administracao × desmatamento_clima × sancao_integridade — `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) — 1/3 pernas sobrevivem ao controle
- **U0108 ✅ ⚪⚠** administracao × desmatamento_clima × saneamento_agua — `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `atlas_individual`×`ebt_nota` **-0,12** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0109 ✅ ⚪⚠** administracao × desmatamento_clima × saude_producao — `cob_priv`×`ebt_nota` **+0,15** (n=665) · `cob_priv`×`desmat_share` **+0,10** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U0110 ✅ ⚪** administracao × desmatamento_clima × trabalho_empresa — `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0111 ✅ ⚪⚠** administracao × desmatamento_clima × transferencia_renda — `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) — 2/3 pernas sobrevivem ao controle
- **U0112 ✅ ⚪** administracao × desmatamento_clima × vigilancia_sinan — nenhuma perna sobrevive
- **U0113 ✅ 🟠** administracao × educacao × fiscal_municipal — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `ies_pc`×`capag_ind2` **+0,14** (n=700)
- **U0114 ✅ 🟠⚠** administracao × educacao × fiscalizacao_ambiental — `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) · `ies_pc`×`emb_100k` **+0,12** (n=648)
- **U0115 ✅ 🟠** administracao × educacao × fundiario — `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547)
- **U0116 ✅ 🟠** administracao × educacao × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0117 ✅ ⚪** administracao × educacao × mortalidade — `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U0118 ✅ 🟠⚠** administracao × educacao × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0119 ✅ 🟠⚠** administracao × educacao × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0120 ✅ 🟠⚠** administracao × educacao × saneamento_agua — `ies_pc`×`atlas_individual` **-0,21** (n=719) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0121 ✅ 🟠⚠** administracao × educacao × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `cob_priv`×`ebt_nota` **+0,15** (n=665)
- **U0122 ✅ 🟠** administracao × educacao × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547)
- **U0123 ✅ 🟠⚠** administracao × educacao × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0124 ✅ ⚪⚠** administracao × educacao × vigilancia_sinan — `pdm_share`×`munic_vinc_pc` **+0,20** (n=5.547) · `ies_pc`×`notif_100k` **+0,14** (n=713) — 2/3 pernas sobrevivem ao controle
- **U0125 ✅ 🟠⚠** administracao × fiscal_municipal × fiscalizacao_ambiental — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318)
- **U0126 ✅ 🟠** administracao × fiscal_municipal × fundiario — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520)
- **U0127 ✅ ⚪** administracao × fiscal_municipal × mineracao_energia — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U0128 ✅ ⚪** administracao × fiscal_municipal × mortalidade — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) — 1/3 pernas sobrevivem ao controle
- **U0129 ✅ 🟠⚠** administracao × fiscal_municipal × natalidade — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0130 ✅ 🟠⚠** administracao × fiscal_municipal × sancao_integridade — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0131 ✅ ⚪⚠** administracao × fiscal_municipal × saneamento_agua — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `atlas_individual`×`ebt_nota` **-0,12** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0132 ✅ ⚪⚠** administracao × fiscal_municipal × saude_producao — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `cob_priv`×`ebt_nota` **+0,15** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0133 ✅ 🟠** administracao × fiscal_municipal × trabalho_empresa — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542)
- **U0134 ✅ 🟠⚠** administracao × fiscal_municipal × transferencia_renda — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0135 ✅ ⚪** administracao × fiscal_municipal × vigilancia_sinan — `sic_pessoal_pc`×`custo_por_vinculo` **+0,38** (n=5.542) — 1/3 pernas sobrevivem ao controle
- **U0136 ✅ 🟠⚠** administracao × fiscalizacao_ambiental × fundiario — `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322)
- **U0137 ✅ ⚪⚠** administracao × fiscalizacao_ambiental × mineracao_energia — `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 2/3 pernas sobrevivem ao controle
- **U0138 ✅ ⚪⚠** administracao × fiscalizacao_ambiental × mortalidade — `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 1/3 pernas sobrevivem ao controle
- **U0139 ✅ ⚪⚠** administracao × fiscalizacao_ambiental × natalidade — `mae_adol`×`ebt_nota` **-0,12** (n=630) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 2/3 pernas sobrevivem ao controle
- **U0140 ✅ ⚪⚠** administracao × fiscalizacao_ambiental × sancao_integridade — `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U0141 ✅ ⚪⚠** administracao × fiscalizacao_ambiental × saneamento_agua — `atlas_individual`×`ebt_nota` **-0,12** (n=665) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 2/3 pernas sobrevivem ao controle
- **U0142 ✅ ⚪⚠** administracao × fiscalizacao_ambiental × saude_producao — `cob_priv`×`ebt_nota` **+0,15** (n=665) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 2/3 pernas sobrevivem ao controle
- **U0143 ✅ ⚪⚠** administracao × fiscalizacao_ambiental × trabalho_empresa — `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 2/3 pernas sobrevivem ao controle
- **U0144 ✅ 🟠⚠** administracao × fiscalizacao_ambiental × transferencia_renda — `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) · `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340)
- **U0145 ✅ ⚪⚠** administracao × fiscalizacao_ambiental × vigilancia_sinan — `autos_100k`×`munic_vinc_pc` **+0,12** (n=4.340) — 1/3 pernas sobrevivem ao controle
- **U0146 ✅ 🟠** administracao × fundiario × mineracao_energia — `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0147 ✅ ⚪** administracao × fundiario × mortalidade — `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U0148 ✅ 🟠⚠** administracao × fundiario × natalidade — `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0149 ✅ ⚪⚠** administracao × fundiario × sancao_integridade — `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U0150 ✅ 🟠⚠** administracao × fundiario × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0151 ✅ 🟠⚠** administracao × fundiario × saude_producao — `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `cob_priv`×`ebt_nota` **+0,15** (n=665) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U0152 ✅ 🟠** administracao × fundiario × trabalho_empresa — `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U0153 ✅ 🟠⚠** administracao × fundiario × transferencia_renda — `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0154 ✅ ⚪** administracao × fundiario × vigilancia_sinan — `cafir_ha_por_imovel`×`munic_vinc_pc` **+0,19** (n=5.547) — 1/3 pernas sobrevivem ao controle
- **U0155 ✅ ⚪** administracao × mineracao_energia × mortalidade — `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U0156 ✅ 🟠⚠** administracao × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0157 ✅ ⚪⚠** administracao × mineracao_energia × sancao_integridade — `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U0158 ✅ 🟠⚠** administracao × mineracao_energia × saneamento_agua — `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0159 ✅ 🟠⚠** administracao × mineracao_energia × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `cob_priv`×`ebt_nota` **+0,15** (n=665) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0160 ✅ 🟠** administracao × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0161 ✅ 🟠⚠** administracao × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566)
- **U0162 ✅ ⚪⚠** administracao × mineracao_energia × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `gd_por_domicilio`×`munic_vinc_pc` **-0,14** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U0163 ✅ ⚪⚠** administracao × mortalidade × natalidade — `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `mae_adol`×`ebt_nota` **-0,12** (n=630) — 2/3 pernas sobrevivem ao controle
- **U0164 ✅ ⚪⚠** administracao × mortalidade × sancao_integridade — `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U0165 ✅ ⚪⚠** administracao × mortalidade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `atlas_individual`×`ebt_nota` **-0,12** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0166 ✅ ⚪⚠** administracao × mortalidade × saude_producao — `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `cob_priv`×`ebt_nota` **+0,15** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0167 ✅ ⚪** administracao × mortalidade × trabalho_empresa — `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `formal_obra`×`infec_100k` **+0,12** (n=5.568) — 2/3 pernas sobrevivem ao controle
- **U0168 ✅ ⚪⚠** administracao × mortalidade × transferencia_renda — `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) — 2/3 pernas sobrevivem ao controle
- **U0169 ✅ ⚪** administracao × mortalidade × vigilancia_sinan — nenhuma perna sobrevive
- **U0170 ✅ 🟠⚠** administracao × natalidade × sancao_integridade — `cesarea`×`sanc_100k` **+0,15** (n=878) · `mae_adol`×`ebt_nota` **-0,12** (n=630) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0171 ✅ 🟠⚠** administracao × natalidade × saneamento_agua — `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `mae_adol`×`ebt_nota` **-0,12** (n=630) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0172 ✅ 🟠⚠** administracao × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `cob_priv`×`ebt_nota` **+0,15** (n=665) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0173 ✅ 🟠⚠** administracao × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0174 ✅ 🟠⚠** administracao × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) · `mae_adol`×`ebt_nota` **-0,12** (n=630)
- **U0175 ✅ ⚪⚠** administracao × natalidade × vigilancia_sinan — `notif_100k`×`cesarea` **+0,15** (n=1.672) · `mae_adol`×`ebt_nota` **-0,12** (n=630) — 2/3 pernas sobrevivem ao controle
- **U0176 ✅ 🟠⚠** administracao × sancao_integridade × saneamento_agua — `atlas_individual`×`ebt_nota` **-0,12** (n=665) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U0177 ✅ 🟠⚠** administracao × sancao_integridade × saude_producao — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `cob_priv`×`ebt_nota` **+0,15** (n=665) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0178 ✅ 🟠⚠** administracao × sancao_integridade × trabalho_empresa — `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0179 ✅ 🟠⚠** administracao × sancao_integridade × transferencia_renda — `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) · `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483)
- **U0180 ✅ ⚪⚠** administracao × sancao_integridade × vigilancia_sinan — `sanc_100k`×`munic_vinc_pc` **+0,12** (n=1.483) — 1/3 pernas sobrevivem ao controle
- **U0181 ✅ 🟠⚠** administracao × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `cob_priv`×`ebt_nota` **+0,15** (n=665) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0182 ✅ 🟠⚠** administracao × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0183 ✅ 🟠⚠** administracao × saneamento_agua × transferencia_renda — `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) · `atlas_individual`×`ebt_nota` **-0,12** (n=665)
- **U0184 ✅ ⚪⚠** administracao × saneamento_agua × vigilancia_sinan — `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `atlas_individual`×`ebt_nota` **-0,12** (n=665) — 2/3 pernas sobrevivem ao controle
- **U0185 ✅ 🟠⚠** administracao × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `cob_priv`×`ebt_nota` **+0,15** (n=665)
- **U0186 ✅ 🟠⚠** administracao × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `cob_priv`×`ebt_nota` **+0,15** (n=665) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0187 ✅ ⚪⚠** administracao × saude_producao × vigilancia_sinan — `cob_priv`×`ebt_nota` **+0,15** (n=665) · `cob_priv`×`notif_100k` **+0,13** (n=4.945) — 2/3 pernas sobrevivem ao controle
- **U0188 ✅ 🟠⚠** administracao × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `nbf_share_dom`×`ebt_nota` **-0,14** (n=664)
- **U0189 ✅ ⚪⚠** administracao × trabalho_empresa × vigilancia_sinan — `rem_media`×`custo_por_vinculo` **+0,24** (n=5.542) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) — 2/3 pernas sobrevivem ao controle
- **U0190 ✅ ⚪⚠** administracao × transferencia_renda × vigilancia_sinan — `nbf_share_dom`×`ebt_nota` **-0,14** (n=664) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) — 2/3 pernas sobrevivem ao controle
- **U0191 ✅ 🟠** agropecuaria × compras_publicas × conectividade — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0192 ✅ 🟠** agropecuaria × compras_publicas × credito_financeiro — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335)
- **U0193 ✅ 🟠⚠** agropecuaria × compras_publicas × cultura_consumo — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335)
- **U0194 ✅ 🟠** agropecuaria × compras_publicas × demografia_censo — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0195 ✅ 🟠** agropecuaria × compras_publicas × desmatamento_clima — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335)
- **U0196 ✅ 🟠** agropecuaria × compras_publicas × educacao — `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0197 ✅ 🟠** agropecuaria × compras_publicas × fiscal_municipal — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536)
- **U0198 ✅ 🟠⚠** agropecuaria × compras_publicas × fiscalizacao_ambiental — `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `emb_100k`×`pevs_share` **-0,11** (n=1.317)
- **U0199 ✅ 🟠** agropecuaria × compras_publicas × fundiario — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0200 ✅ 🟠** agropecuaria × compras_publicas × mineracao_energia — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335)
- **U0201 ✅ ⚪** agropecuaria × compras_publicas × mortalidade — `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0202 ✅ 🟠** agropecuaria × compras_publicas × natalidade — `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0203 ✅ 🟠⚠** agropecuaria × compras_publicas × sancao_integridade — `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335)
- **U0204 ✅ 🟠⚠** agropecuaria × compras_publicas × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0205 ✅ 🟠** agropecuaria × compras_publicas × saude_producao — `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918)
- **U0206 ✅ 🟠** agropecuaria × compras_publicas × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335)
- **U0207 ✅ 🟠** agropecuaria × compras_publicas × transferencia_renda — `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0208 ✅ ⚪⚠** agropecuaria × compras_publicas × vigilancia_sinan — `mides_valor_pc`×`va_agro_ha` **-0,19** (n=3.335) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) — 2/3 pernas sobrevivem ao controle
- **U0209 ✅ 🟡** agropecuaria × conectividade × credito_financeiro — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570)
- **U0210 ✅ 🟠⚠** agropecuaria × conectividade × cultura_consumo — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563)
- **U0211 ✅ 🟠** agropecuaria × conectividade × demografia_censo — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0212 ✅ 🟠** agropecuaria × conectividade × desmatamento_clima — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570)
- **U0213 ✅ 🟠** agropecuaria × conectividade × educacao — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `ies_pc`×`agro_1000dom` **+0,19** (n=719) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0214 ✅ ⚪** agropecuaria × conectividade × fiscal_municipal — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) — 2/3 pernas sobrevivem ao controle
- **U0215 ✅ ⚪⚠** agropecuaria × conectividade × fiscalizacao_ambiental — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0216 ✅ 🟠** agropecuaria × conectividade × fundiario — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547)
- **U0217 ✅ 🟠** agropecuaria × conectividade × mineracao_energia — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0218 ✅ 🟠** agropecuaria × conectividade × mortalidade — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0219 ✅ 🟠** agropecuaria × conectividade × natalidade — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0220 ✅ 🟠** agropecuaria × conectividade × sancao_integridade — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0221 ✅ 🟡⚠** agropecuaria × conectividade × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302)
- **U0222 ✅ 🟠** agropecuaria × conectividade × saude_producao — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565)
- **U0223 ✅ 🟠** agropecuaria × conectividade × trabalho_empresa — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570)
- **U0224 ✅ 🟠** agropecuaria × conectividade × transferencia_renda — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532)
- **U0225 ✅ ⚪⚠** agropecuaria × conectividade × vigilancia_sinan — `agro_1000dom`×`cobertura_pop_4g5g` **-0,45** (n=5.570) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0226 ✅ 🟠⚠** agropecuaria × credito_financeiro × cultura_consumo — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563)
- **U0227 ✅ 🟠** agropecuaria × credito_financeiro × demografia_censo — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0228 ✅ 🟡** agropecuaria × credito_financeiro × desmatamento_clima — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `credito_ha`×`desmat_share` **+0,45** (n=5.456)
- **U0229 ✅ 🟠** agropecuaria × credito_financeiro × educacao — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0230 ✅ 🟠** agropecuaria × credito_financeiro × fiscal_municipal — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536)
- **U0231 ✅ 🟠⚠** agropecuaria × credito_financeiro × fiscalizacao_ambiental — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) · `emb_100k`×`pevs_share` **-0,11** (n=1.317)
- **U0232 ✅ 🟡** agropecuaria × credito_financeiro × fundiario — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547)
- **U0233 ✅ 🟠** agropecuaria × credito_financeiro × mineracao_energia — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534)
- **U0234 ✅ 🟠** agropecuaria × credito_financeiro × mortalidade — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0235 ✅ 🟠** agropecuaria × credito_financeiro × natalidade — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709)
- **U0236 ✅ 🟠** agropecuaria × credito_financeiro × sancao_integridade — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0237 ✅ 🟡⚠** agropecuaria × credito_financeiro × saneamento_agua — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302)
- **U0238 ✅ 🟠** agropecuaria × credito_financeiro × saude_producao — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565)
- **U0239 ✅ 🟠** agropecuaria × credito_financeiro × trabalho_empresa — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570)
- **U0240 ✅ 🟠** agropecuaria × credito_financeiro × transferencia_renda — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532)
- **U0241 ✅ ⚪⚠** agropecuaria × credito_financeiro × vigilancia_sinan — `sicor_hhi_tomador`×`agro_1000dom` **-0,51** (n=5.390) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0242 ✅ 🟠⚠** agropecuaria × cultura_consumo × demografia_censo — `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0243 ✅ 🟠⚠** agropecuaria × cultura_consumo × desmatamento_clima — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0244 ✅ 🟠⚠** agropecuaria × cultura_consumo × educacao — `ies_pc`×`relig_100k` **+0,28** (n=719) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0245 ✅ ⚪⚠** agropecuaria × cultura_consumo × fiscal_municipal — `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) — 2/3 pernas sobrevivem ao controle
- **U0246 ✅ ⚪⚠** agropecuaria × cultura_consumo × fiscalizacao_ambiental — `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0247 ✅ 🟠⚠** agropecuaria × cultura_consumo × fundiario — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0248 ✅ 🟠⚠** agropecuaria × cultura_consumo × mineracao_energia — `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563)
- **U0249 ✅ 🟠⚠** agropecuaria × cultura_consumo × mortalidade — `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0250 ✅ 🟠⚠** agropecuaria × cultura_consumo × natalidade — `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `cesarea`×`relig_100k` **+0,23** (n=1.733) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563)
- **U0251 ✅ 🟠⚠** agropecuaria × cultura_consumo × sancao_integridade — `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483)
- **U0252 ✅ 🟠⚠** agropecuaria × cultura_consumo × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563)
- **U0253 ✅ 🟠⚠** agropecuaria × cultura_consumo × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563)
- **U0254 ✅ 🟠⚠** agropecuaria × cultura_consumo × trabalho_empresa — `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563)
- **U0255 ✅ 🟠⚠** agropecuaria × cultura_consumo × transferencia_renda — `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563)
- **U0256 ✅ ⚪⚠** agropecuaria × cultura_consumo × vigilancia_sinan — `agro_1000dom`×`reclam_100k` **-0,20** (n=5.563) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0257 ✅ ⚪** agropecuaria × demografia_censo × desmatamento_clima — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533) — 2/3 pernas sobrevivem ao controle
- **U0258 ✅ 🟠** agropecuaria × demografia_censo × educacao — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ies_pc`×`agro_1000dom` **+0,19** (n=719) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0259 ✅ 🟠** agropecuaria × demografia_censo × fiscal_municipal — `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536)
- **U0260 ✅ ⚪⚠** agropecuaria × demografia_censo × fiscalizacao_ambiental — `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0261 ✅ 🟠** agropecuaria × demografia_censo × fundiario — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0262 ✅ 🟠** agropecuaria × demografia_censo × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0263 ✅ 🟠** agropecuaria × demografia_censo × mortalidade — `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0264 ✅ 🟠** agropecuaria × demografia_censo × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0265 ✅ 🟠** agropecuaria × demografia_censo × sancao_integridade — `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061)
- **U0266 ✅ 🟠⚠** agropecuaria × demografia_censo × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0267 ✅ 🟠** agropecuaria × demografia_censo × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0268 ✅ 🟠** agropecuaria × demografia_censo × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0269 ✅ 🟠** agropecuaria × demografia_censo × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533)
- **U0270 ✅ ⚪⚠** agropecuaria × demografia_censo × vigilancia_sinan — `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `ivs_2010`×`bov_por_ha` **-0,17** (n=5.533) — 2/3 pernas sobrevivem ao controle
- **U0271 ✅ 🟠** agropecuaria × desmatamento_clima × educacao — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `ies_pc`×`agro_1000dom` **+0,19** (n=719) · `ies_pc`×`desmat_share` **+0,16** (n=719)
- **U0272 ✅ ⚪** agropecuaria × desmatamento_clima × fiscal_municipal — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) — 2/3 pernas sobrevivem ao controle
- **U0273 ✅ 🟠⚠** agropecuaria × desmatamento_clima × fiscalizacao_ambiental — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `emb_100k`×`pevs_share` **-0,11** (n=1.317)
- **U0274 ✅ 🟠** agropecuaria × desmatamento_clima × fundiario — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547)
- **U0275 ✅ 🟠** agropecuaria × desmatamento_clima × mineracao_energia — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566)
- **U0276 ✅ 🟠** agropecuaria × desmatamento_clima × mortalidade — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U0277 ✅ 🟠** agropecuaria × desmatamento_clima × natalidade — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `cesarea`×`desmat_share` **+0,27** (n=1.733) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709)
- **U0278 ✅ ⚪** agropecuaria × desmatamento_clima × sancao_integridade — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0279 ✅ 🟠⚠** agropecuaria × desmatamento_clima × saneamento_agua — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570)
- **U0280 ✅ 🟠** agropecuaria × desmatamento_clima × saude_producao — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U0281 ✅ 🟠** agropecuaria × desmatamento_clima × trabalho_empresa — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570)
- **U0282 ✅ 🟠** agropecuaria × desmatamento_clima × transferencia_renda — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803)
- **U0283 ✅ ⚪** agropecuaria × desmatamento_clima × vigilancia_sinan — `desmat_share`×`bov_por_ha` **+0,49** (n=5.538) — 1/3 pernas sobrevivem ao controle
- **U0284 ✅ 🟠** agropecuaria × educacao × fiscal_municipal — `ies_pc`×`agro_1000dom` **+0,19** (n=719) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) · `ies_pc`×`capag_ind2` **+0,14** (n=700)
- **U0285 ✅ 🟠⚠** agropecuaria × educacao × fiscalizacao_ambiental — `ies_pc`×`agro_1000dom` **+0,19** (n=719) · `ies_pc`×`emb_100k` **+0,12** (n=648) · `emb_100k`×`pevs_share` **-0,11** (n=1.317)
- **U0286 ✅ 🟠** agropecuaria × educacao × fundiario — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0287 ✅ 🟠** agropecuaria × educacao × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0288 ✅ 🟠** agropecuaria × educacao × mortalidade — `ies_pc`×`agro_1000dom` **+0,19** (n=719) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0289 ✅ 🟠** agropecuaria × educacao × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0290 ✅ 🟠⚠** agropecuaria × educacao × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0291 ✅ 🟠⚠** agropecuaria × educacao × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `ies_pc`×`atlas_individual` **-0,21** (n=719) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0292 ✅ 🟠** agropecuaria × educacao × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0293 ✅ 🟠** agropecuaria × educacao × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0294 ✅ 🟠** agropecuaria × educacao × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `ies_pc`×`agro_1000dom` **+0,19** (n=719)
- **U0295 ✅ ⚪⚠** agropecuaria × educacao × vigilancia_sinan — `ies_pc`×`agro_1000dom` **+0,19** (n=719) · `ies_pc`×`notif_100k` **+0,14** (n=713) — 2/3 pernas sobrevivem ao controle
- **U0296 ✅ 🟠⚠** agropecuaria × fiscal_municipal × fiscalizacao_ambiental — `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) · `emb_100k`×`pevs_share` **-0,11** (n=1.317)
- **U0297 ✅ 🟠** agropecuaria × fiscal_municipal × fundiario — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536)
- **U0298 ✅ ⚪** agropecuaria × fiscal_municipal × mineracao_energia — `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) — 2/3 pernas sobrevivem ao controle
- **U0299 ✅ ⚪** agropecuaria × fiscal_municipal × mortalidade — `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0300 ✅ 🟠** agropecuaria × fiscal_municipal × natalidade — `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U0301 ✅ 🟠⚠** agropecuaria × fiscal_municipal × sancao_integridade — `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479)
- **U0302 ✅ ⚪⚠** agropecuaria × fiscal_municipal × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) — 2/3 pernas sobrevivem ao controle
- **U0303 ✅ ⚪** agropecuaria × fiscal_municipal × saude_producao — `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) — 2/3 pernas sobrevivem ao controle
- **U0304 ✅ 🟠** agropecuaria × fiscal_municipal × trabalho_empresa — `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536)
- **U0305 ✅ 🟠** agropecuaria × fiscal_municipal × transferencia_renda — `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014)
- **U0306 ✅ ⚪** agropecuaria × fiscal_municipal × vigilancia_sinan — `sic_pessoal_pc`×`va_agro_ha` **-0,16** (n=5.536) — 1/3 pernas sobrevivem ao controle
- **U0307 ✅ 🟠⚠** agropecuaria × fiscalizacao_ambiental × fundiario — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322)
- **U0308 ✅ ⚪⚠** agropecuaria × fiscalizacao_ambiental × mineracao_energia — `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0309 ✅ ⚪⚠** agropecuaria × fiscalizacao_ambiental × mortalidade — `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0310 ✅ ⚪⚠** agropecuaria × fiscalizacao_ambiental × natalidade — `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0311 ✅ ⚪⚠** agropecuaria × fiscalizacao_ambiental × sancao_integridade — `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0312 ✅ ⚪⚠** agropecuaria × fiscalizacao_ambiental × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0313 ✅ ⚪⚠** agropecuaria × fiscalizacao_ambiental × saude_producao — `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0314 ✅ ⚪⚠** agropecuaria × fiscalizacao_ambiental × trabalho_empresa — `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 2/3 pernas sobrevivem ao controle
- **U0315 ✅ 🟠⚠** agropecuaria × fiscalizacao_ambiental × transferencia_renda — `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `emb_100k`×`pevs_share` **-0,11** (n=1.317)
- **U0316 ✅ ⚪⚠** agropecuaria × fiscalizacao_ambiental × vigilancia_sinan — `emb_100k`×`pevs_share` **-0,11** (n=1.317) — 1/3 pernas sobrevivem ao controle
- **U0317 ✅ 🟠** agropecuaria × fundiario × mineracao_energia — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543)
- **U0318 ✅ 🟠** agropecuaria × fundiario × mortalidade — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0319 ✅ 🟠** agropecuaria × fundiario × natalidade — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729)
- **U0320 ✅ ⚪** agropecuaria × fundiario × sancao_integridade — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0321 ✅ 🟠⚠** agropecuaria × fundiario × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279)
- **U0322 ✅ 🟠** agropecuaria × fundiario × saude_producao — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U0323 ✅ 🟠** agropecuaria × fundiario × trabalho_empresa — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U0324 ✅ 🟠** agropecuaria × fundiario × transferencia_renda — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541)
- **U0325 ✅ ⚪** agropecuaria × fundiario × vigilancia_sinan — `agro_1000dom`×`cafir_ha_por_imovel` **-0,39** (n=5.547) — 1/3 pernas sobrevivem ao controle
- **U0326 ✅ 🟠** agropecuaria × mineracao_energia × mortalidade — `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0327 ✅ 🟠** agropecuaria × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709)
- **U0328 ✅ ⚪** agropecuaria × mineracao_energia × sancao_integridade — `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0329 ✅ 🟠⚠** agropecuaria × mineracao_energia × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U0330 ✅ 🟠** agropecuaria × mineracao_energia × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565)
- **U0331 ✅ 🟠** agropecuaria × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570)
- **U0332 ✅ 🟠** agropecuaria × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532)
- **U0333 ✅ ⚪⚠** agropecuaria × mineracao_energia × vigilancia_sinan — `bov_por_ha`×`gd_por_domicilio` **+0,26** (n=5.534) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) — 2/3 pernas sobrevivem ao controle
- **U0334 ✅ 🟠** agropecuaria × mortalidade × natalidade — `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0335 ✅ 🟠⚠** agropecuaria × mortalidade × sancao_integridade — `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483)
- **U0336 ✅ 🟠⚠** agropecuaria × mortalidade × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0337 ✅ 🟠** agropecuaria × mortalidade × saude_producao — `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0338 ✅ 🟠** agropecuaria × mortalidade × trabalho_empresa — `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U0339 ✅ 🟠** agropecuaria × mortalidade × transferencia_renda — `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) · `infec_100k`×`agro_1000dom` **-0,13** (n=5.570)
- **U0340 ✅ ⚪** agropecuaria × mortalidade × vigilancia_sinan — `infec_100k`×`agro_1000dom` **-0,13** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0341 ✅ 🟠⚠** agropecuaria × natalidade × sancao_integridade — `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `cesarea`×`sanc_100k` **+0,15** (n=878)
- **U0342 ✅ 🟠⚠** agropecuaria × natalidade × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U0343 ✅ 🟠** agropecuaria × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565)
- **U0344 ✅ 🟠** agropecuaria × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570)
- **U0345 ✅ 🟠** agropecuaria × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532)
- **U0346 ✅ ⚪⚠** agropecuaria × natalidade × vigilancia_sinan — `cesarea`×`bov_por_ha` **+0,26** (n=1.709) · `notif_100k`×`cesarea` **+0,15** (n=1.672) — 2/3 pernas sobrevivem ao controle
- **U0347 ✅ 🟠⚠** agropecuaria × sancao_integridade × saneamento_agua — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U0348 ✅ 🟠⚠** agropecuaria × sancao_integridade × saude_producao — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061)
- **U0349 ✅ 🟠⚠** agropecuaria × sancao_integridade × trabalho_empresa — `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `formalidade`×`sanc_100k` **+0,16** (n=1.483)
- **U0350 ✅ 🟠⚠** agropecuaria × sancao_integridade × transferencia_renda — `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U0351 ✅ ⚪** agropecuaria × sancao_integridade × vigilancia_sinan — `pago_a_devedor`×`agro_1000dom` **-0,20** (n=3.061) — 1/3 pernas sobrevivem ao controle
- **U0352 ✅ 🟠⚠** agropecuaria × saneamento_agua × saude_producao — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565)
- **U0353 ✅ 🟠⚠** agropecuaria × saneamento_agua × trabalho_empresa — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570)
- **U0354 ✅ 🟠⚠** agropecuaria × saneamento_agua × transferencia_renda — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U0355 ✅ ⚪⚠** agropecuaria × saneamento_agua × vigilancia_sinan — `agro_1000dom`×`snis_gap_agua` **-0,44** (n=5.302) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) — 2/3 pernas sobrevivem ao controle
- **U0356 ✅ 🟠** agropecuaria × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565)
- **U0357 ✅ 🟠** agropecuaria × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532)
- **U0358 ✅ ⚪⚠** agropecuaria × saude_producao × vigilancia_sinan — `cob_priv`×`agro_1000dom` **-0,23** (n=5.565) · `cob_priv`×`notif_100k` **+0,13** (n=4.945) — 2/3 pernas sobrevivem ao controle
- **U0359 ✅ 🟠** agropecuaria × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532)
- **U0360 ✅ ⚪⚠** agropecuaria × trabalho_empresa × vigilancia_sinan — `formalidade`×`agro_1000dom` **-0,26** (n=5.570) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) — 2/3 pernas sobrevivem ao controle
- **U0361 ✅ ⚪⚠** agropecuaria × transferencia_renda × vigilancia_sinan — `pbf_2019_2006`×`bov_por_ha` **-0,23** (n=5.532) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) — 2/3 pernas sobrevivem ao controle
- **U0362 ✅ 🟠** compras_publicas × conectividade × credito_financeiro — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0363 ✅ 🟠** compras_publicas × conectividade × cultura_consumo — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0364 ✅ 🟠** compras_publicas × conectividade × demografia_censo — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0365 ✅ 🟠** compras_publicas × conectividade × desmatamento_clima — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0366 ✅ 🟠** compras_publicas × conectividade × educacao — `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `sisu_pc`×`ibc` **+0,14** (n=551) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0367 ✅ ⚪** compras_publicas × conectividade × fiscal_municipal — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339) — 2/3 pernas sobrevivem ao controle
- **U0368 ✅ ⚪⚠** compras_publicas × conectividade × fiscalizacao_ambiental — `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339) — 2/3 pernas sobrevivem ao controle
- **U0369 ✅ 🟠** compras_publicas × conectividade × fundiario — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0370 ✅ 🟠** compras_publicas × conectividade × mineracao_energia — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0371 ✅ ⚪** compras_publicas × conectividade × mortalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339) — 2/3 pernas sobrevivem ao controle
- **U0372 ✅ 🟠** compras_publicas × conectividade × natalidade — `cesarea`×`share_credor_local` **+0,17** (n=780) · `cesarea`×`ibc` **+0,15** (n=1.733) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0373 ✅ 🟠⚠** compras_publicas × conectividade × sancao_integridade — `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0374 ✅ 🟠⚠** compras_publicas × conectividade × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0375 ✅ 🟠** compras_publicas × conectividade × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0376 ✅ 🟠** compras_publicas × conectividade × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0377 ✅ 🟠** compras_publicas × conectividade × transferencia_renda — `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0378 ✅ 🟠⚠** compras_publicas × conectividade × vigilancia_sinan — `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) · `mides_valor_pc`×`densidade_smp` **+0,12** (n=3.339)
- **U0379 ✅ 🟠⚠** compras_publicas × credito_financeiro × cultura_consumo — `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968)
- **U0380 ✅ 🟠** compras_publicas × credito_financeiro × demografia_censo — `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968)
- **U0381 ✅ 🟠** compras_publicas × credito_financeiro × desmatamento_clima — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063)
- **U0382 ✅ 🟠** compras_publicas × credito_financeiro × educacao — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547)
- **U0383 ✅ 🟠** compras_publicas × credito_financeiro × fiscal_municipal — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542)
- **U0384 ✅ 🟠⚠** compras_publicas × credito_financeiro × fiscalizacao_ambiental — `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `cred_ha`×`autos_100k` **-0,12** (n=4.150)
- **U0385 ✅ 🟠** compras_publicas × credito_financeiro × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0386 ✅ 🟠** compras_publicas × credito_financeiro × mineracao_energia — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968)
- **U0387 ✅ ⚪** compras_publicas × credito_financeiro × mortalidade — `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) — 2/3 pernas sobrevivem ao controle
- **U0388 ✅ 🟠** compras_publicas × credito_financeiro × natalidade — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0389 ✅ 🟠⚠** compras_publicas × credito_financeiro × sancao_integridade — `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0390 ✅ 🟠⚠** compras_publicas × credito_financeiro × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0391 ✅ 🟠** compras_publicas × credito_financeiro × saude_producao — `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918)
- **U0392 ✅ 🟠** compras_publicas × credito_financeiro × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968)
- **U0393 ✅ 🟠** compras_publicas × credito_financeiro × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0394 ✅ 🟠⚠** compras_publicas × credito_financeiro × vigilancia_sinan — `cred_ha`×`share_credor_local` **+0,23** (n=2.968) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0395 ✅ 🟠** compras_publicas × cultura_consumo × demografia_censo — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063)
- **U0396 ✅ 🟠** compras_publicas × cultura_consumo × desmatamento_clima — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0397 ✅ 🟠** compras_publicas × cultura_consumo × educacao — `ies_pc`×`relig_100k` **+0,28** (n=719) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547)
- **U0398 ✅ ⚪** compras_publicas × cultura_consumo × fiscal_municipal — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) — 2/3 pernas sobrevivem ao controle
- **U0399 ✅ ⚪⚠** compras_publicas × cultura_consumo × fiscalizacao_ambiental — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) — 2/3 pernas sobrevivem ao controle
- **U0400 ✅ 🟠⚠** compras_publicas × cultura_consumo × fundiario — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0401 ✅ 🟠** compras_publicas × cultura_consumo × mineracao_energia — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566)
- **U0402 ✅ ⚪⚠** compras_publicas × cultura_consumo × mortalidade — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563) — 2/3 pernas sobrevivem ao controle
- **U0403 ✅ 🟠** compras_publicas × cultura_consumo × natalidade — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `cesarea`×`relig_100k` **+0,23** (n=1.733) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0404 ✅ 🟠⚠** compras_publicas × cultura_consumo × sancao_integridade — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483)
- **U0405 ✅ 🟠⚠** compras_publicas × cultura_consumo × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0406 ✅ 🟠** compras_publicas × cultura_consumo × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918)
- **U0407 ✅ 🟠** compras_publicas × cultura_consumo × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0408 ✅ 🟠** compras_publicas × cultura_consumo × transferencia_renda — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0409 ✅ 🟠⚠** compras_publicas × cultura_consumo × vigilancia_sinan — `share_credor_local`×`comercio_por_dom` **+0,23** (n=3.063) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0410 ✅ ⚪** compras_publicas × demografia_censo × desmatamento_clima — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063) — 2/3 pernas sobrevivem ao controle
- **U0411 ✅ 🟠** compras_publicas × demografia_censo × educacao — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547)
- **U0412 ✅ 🟠** compras_publicas × demografia_censo × fiscal_municipal — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537)
- **U0413 ✅ ⚪⚠** compras_publicas × demografia_censo × fiscalizacao_ambiental — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) — 2/3 pernas sobrevivem ao controle
- **U0414 ✅ 🟠** compras_publicas × demografia_censo × fundiario — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0415 ✅ 🟠** compras_publicas × demografia_censo × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063)
- **U0416 ✅ ⚪** compras_publicas × demografia_censo × mortalidade — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U0417 ✅ 🟠** compras_publicas × demografia_censo × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0418 ✅ 🟠⚠** compras_publicas × demografia_censo × sancao_integridade — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061)
- **U0419 ✅ 🟠⚠** compras_publicas × demografia_censo × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0420 ✅ 🟠** compras_publicas × demografia_censo × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918)
- **U0421 ✅ 🟠** compras_publicas × demografia_censo × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063)
- **U0422 ✅ 🟠** compras_publicas × demografia_censo × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0423 ✅ 🟠⚠** compras_publicas × demografia_censo × vigilancia_sinan — `share_nome_top`×`mides_valor_pc` **+0,32** (n=3.336) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723)
- **U0424 ✅ 🟠** compras_publicas × desmatamento_clima × educacao — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `ies_pc`×`desmat_share` **+0,16** (n=719)
- **U0425 ✅ ⚪** compras_publicas × desmatamento_clima × fiscal_municipal — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063) — 2/3 pernas sobrevivem ao controle
- **U0426 ✅ 🟠⚠** compras_publicas × desmatamento_clima × fiscalizacao_ambiental — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429)
- **U0427 ✅ 🟠** compras_publicas × desmatamento_clima × fundiario — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0428 ✅ 🟠** compras_publicas × desmatamento_clima × mineracao_energia — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063)
- **U0429 ✅ ⚪** compras_publicas × desmatamento_clima × mortalidade — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `infec_100k`×`desmat_share` **+0,11** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0430 ✅ 🟠** compras_publicas × desmatamento_clima × natalidade — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0431 ✅ ⚪⚠** compras_publicas × desmatamento_clima × sancao_integridade — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) — 2/3 pernas sobrevivem ao controle
- **U0432 ✅ 🟠** compras_publicas × desmatamento_clima × saneamento_agua — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0433 ✅ 🟠** compras_publicas × desmatamento_clima × saude_producao — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U0434 ✅ 🟠** compras_publicas × desmatamento_clima × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `share_credor_local`×`desmat_share` **+0,22** (n=3.063)
- **U0435 ✅ 🟠** compras_publicas × desmatamento_clima × transferencia_renda — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0436 ✅ ⚪⚠** compras_publicas × desmatamento_clima × vigilancia_sinan — `share_credor_local`×`desmat_share` **+0,22** (n=3.063) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) — 2/3 pernas sobrevivem ao controle
- **U0437 ✅ 🟠** compras_publicas × educacao × fiscal_municipal — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `ies_pc`×`capag_ind2` **+0,14** (n=700)
- **U0438 ✅ 🟠⚠** compras_publicas × educacao × fiscalizacao_ambiental — `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `ies_pc`×`emb_100k` **+0,12** (n=648)
- **U0439 ✅ 🟠** compras_publicas × educacao × fundiario — `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0440 ✅ 🟠** compras_publicas × educacao × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547)
- **U0441 ✅ ⚪** compras_publicas × educacao × mortalidade — `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U0442 ✅ 🟠** compras_publicas × educacao × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0443 ✅ 🟠⚠** compras_publicas × educacao × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024)
- **U0444 ✅ 🟠** compras_publicas × educacao × saneamento_agua — `ies_pc`×`atlas_individual` **-0,21** (n=719) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0445 ✅ 🟠** compras_publicas × educacao × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918)
- **U0446 ✅ 🟠** compras_publicas × educacao × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547)
- **U0447 ✅ 🟠** compras_publicas × educacao × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0448 ✅ 🟠⚠** compras_publicas × educacao × vigilancia_sinan — `sisu_pc`×`pncp_valor_mediano` **-0,20** (n=547) · `ies_pc`×`notif_100k` **+0,14** (n=713) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723)
- **U0449 ✅ 🟠⚠** compras_publicas × fiscal_municipal × fiscalizacao_ambiental — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318)
- **U0450 ✅ 🟠** compras_publicas × fiscal_municipal × fundiario — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0451 ✅ ⚪** compras_publicas × fiscal_municipal × mineracao_energia — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) — 2/3 pernas sobrevivem ao controle
- **U0452 ✅ ⚪** compras_publicas × fiscal_municipal × mortalidade — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) — 1/3 pernas sobrevivem ao controle
- **U0453 ✅ 🟠** compras_publicas × fiscal_municipal × natalidade — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `cesarea`×`share_credor_local` **+0,17** (n=780) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U0454 ✅ 🟠⚠** compras_publicas × fiscal_municipal × sancao_integridade — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479)
- **U0455 ✅ ⚪** compras_publicas × fiscal_municipal × saneamento_agua — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063) — 2/3 pernas sobrevivem ao controle
- **U0456 ✅ ⚪** compras_publicas × fiscal_municipal × saude_producao — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) — 2/3 pernas sobrevivem ao controle
- **U0457 ✅ 🟠** compras_publicas × fiscal_municipal × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542)
- **U0458 ✅ 🟠** compras_publicas × fiscal_municipal × transferencia_renda — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014)
- **U0459 ✅ ⚪⚠** compras_publicas × fiscal_municipal × vigilancia_sinan — `sic_pessoal_pc`×`mides_credores_pc` **+0,24** (n=3.330) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) — 2/3 pernas sobrevivem ao controle
- **U0460 ✅ 🟠⚠** compras_publicas × fiscalizacao_ambiental × fundiario — `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322)
- **U0461 ✅ ⚪⚠** compras_publicas × fiscalizacao_ambiental × mineracao_energia — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) — 2/3 pernas sobrevivem ao controle
- **U0462 ✅ ⚪⚠** compras_publicas × fiscalizacao_ambiental × mortalidade — `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) — 1/3 pernas sobrevivem ao controle
- **U0463 ✅ ⚪⚠** compras_publicas × fiscalizacao_ambiental × natalidade — `cesarea`×`share_credor_local` **+0,17** (n=780) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) — 2/3 pernas sobrevivem ao controle
- **U0464 ✅ ⚪⚠** compras_publicas × fiscalizacao_ambiental × sancao_integridade — `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) — 2/3 pernas sobrevivem ao controle
- **U0465 ✅ ⚪⚠** compras_publicas × fiscalizacao_ambiental × saneamento_agua — `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063) — 2/3 pernas sobrevivem ao controle
- **U0466 ✅ ⚪⚠** compras_publicas × fiscalizacao_ambiental × saude_producao — `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) — 2/3 pernas sobrevivem ao controle
- **U0467 ✅ ⚪⚠** compras_publicas × fiscalizacao_ambiental × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) — 2/3 pernas sobrevivem ao controle
- **U0468 ✅ 🟠⚠** compras_publicas × fiscalizacao_ambiental × transferencia_renda — `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0469 ✅ ⚪⚠** compras_publicas × fiscalizacao_ambiental × vigilancia_sinan — `mides_valor_pc`×`autos_100k` **+0,15** (n=2.429) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) — 2/3 pernas sobrevivem ao controle
- **U0470 ✅ 🟠** compras_publicas × fundiario × mineracao_energia — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0471 ✅ ⚪** compras_publicas × fundiario × mortalidade — `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324) — 2/3 pernas sobrevivem ao controle
- **U0472 ✅ 🟠** compras_publicas × fundiario × natalidade — `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `cesarea`×`share_credor_local` **+0,17** (n=780) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0473 ✅ ⚪⚠** compras_publicas × fundiario × sancao_integridade — `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324) — 2/3 pernas sobrevivem ao controle
- **U0474 ✅ 🟠⚠** compras_publicas × fundiario × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0475 ✅ 🟠** compras_publicas × fundiario × saude_producao — `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U0476 ✅ 🟠** compras_publicas × fundiario × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U0477 ✅ 🟠** compras_publicas × fundiario × transferencia_renda — `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060) · `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324)
- **U0478 ✅ ⚪⚠** compras_publicas × fundiario × vigilancia_sinan — `mides_valor_pc`×`cafir_ha_por_imovel` **+0,13** (n=3.324) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) — 2/3 pernas sobrevivem ao controle
- **U0479 ✅ ⚪** compras_publicas × mineracao_energia × mortalidade — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U0480 ✅ 🟠** compras_publicas × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0481 ✅ ⚪⚠** compras_publicas × mineracao_energia × sancao_integridade — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) — 2/3 pernas sobrevivem ao controle
- **U0482 ✅ 🟠⚠** compras_publicas × mineracao_energia × saneamento_agua — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0483 ✅ 🟠** compras_publicas × mineracao_energia × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918)
- **U0484 ✅ 🟠** compras_publicas × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063)
- **U0485 ✅ 🟠** compras_publicas × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0486 ✅ 🟠⚠** compras_publicas × mineracao_energia × vigilancia_sinan — `share_credor_local`×`gd_por_domicilio` **+0,26** (n=3.063) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723)
- **U0487 ✅ ⚪** compras_publicas × mortalidade × natalidade — `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `cesarea`×`share_credor_local` **+0,17** (n=780) — 2/3 pernas sobrevivem ao controle
- **U0488 ✅ ⚪⚠** compras_publicas × mortalidade × sancao_integridade — `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U0489 ✅ ⚪⚠** compras_publicas × mortalidade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063) — 2/3 pernas sobrevivem ao controle
- **U0490 ✅ ⚪** compras_publicas × mortalidade × saude_producao — `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) — 2/3 pernas sobrevivem ao controle
- **U0491 ✅ ⚪** compras_publicas × mortalidade × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `formal_obra`×`infec_100k` **+0,12** (n=5.568) — 2/3 pernas sobrevivem ao controle
- **U0492 ✅ ⚪** compras_publicas × mortalidade × transferencia_renda — `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) — 2/3 pernas sobrevivem ao controle
- **U0493 ✅ ⚪⚠** compras_publicas × mortalidade × vigilancia_sinan — `notif_100k`×`share_credor_local` **+0,13** (n=2.723) — 1/3 pernas sobrevivem ao controle
- **U0494 ✅ 🟠⚠** compras_publicas × natalidade × sancao_integridade — `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `cesarea`×`share_credor_local` **+0,17** (n=780) · `cesarea`×`sanc_100k` **+0,15** (n=878)
- **U0495 ✅ 🟠⚠** compras_publicas × natalidade × saneamento_agua — `cesarea`×`share_credor_local` **+0,17** (n=780) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0496 ✅ 🟠** compras_publicas × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0497 ✅ 🟠** compras_publicas × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `cesarea`×`share_credor_local` **+0,17** (n=780)
- **U0498 ✅ 🟠** compras_publicas × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `cesarea`×`share_credor_local` **+0,17** (n=780) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0499 ✅ 🟠⚠** compras_publicas × natalidade × vigilancia_sinan — `cesarea`×`share_credor_local` **+0,17** (n=780) · `notif_100k`×`cesarea` **+0,15** (n=1.672) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723)
- **U0500 ✅ 🟠⚠** compras_publicas × sancao_integridade × saneamento_agua — `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U0501 ✅ 🟠⚠** compras_publicas × sancao_integridade × saude_producao — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918)
- **U0502 ✅ 🟠⚠** compras_publicas × sancao_integridade × trabalho_empresa — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `formalidade`×`sanc_100k` **+0,16** (n=1.483)
- **U0503 ✅ 🟠⚠** compras_publicas × sancao_integridade × transferencia_renda — `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U0504 ✅ ⚪⚠** compras_publicas × sancao_integridade × vigilancia_sinan — `mides_credores_pc`×`sanc_100k` **+0,19** (n=1.024) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) — 2/3 pernas sobrevivem ao controle
- **U0505 ✅ 🟠⚠** compras_publicas × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0506 ✅ 🟠⚠** compras_publicas × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0507 ✅ 🟠** compras_publicas × saneamento_agua × transferencia_renda — `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063)
- **U0508 ✅ 🟠⚠** compras_publicas × saneamento_agua × vigilancia_sinan — `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `share_credor_local`×`atlas_individual` **-0,13** (n=3.063) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723)
- **U0509 ✅ 🟠** compras_publicas × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918)
- **U0510 ✅ 🟠** compras_publicas × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0511 ✅ 🟠⚠** compras_publicas × saude_producao × vigilancia_sinan — `prod_por_leito`×`mides_valor_pc` **-0,18** (n=1.918) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) · `cob_priv`×`notif_100k` **+0,13** (n=4.945)
- **U0512 ✅ 🟠** compras_publicas × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060)
- **U0513 ✅ 🟠⚠** compras_publicas × trabalho_empresa × vigilancia_sinan — `formal_obra`×`share_credor_local` **+0,27** (n=3.063) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723)
- **U0514 ✅ 🟠⚠** compras_publicas × transferencia_renda × vigilancia_sinan — `pbf_2019_2006`×`share_credor_local` **-0,15** (n=3.060) · `notif_100k`×`share_credor_local` **+0,13** (n=2.723) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U0515 ✅ 🟠⚠** conectividade × credito_financeiro × cultura_consumo — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563)
- **U0516 ✅ 🟡** conectividade × credito_financeiro × demografia_censo — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565)
- **U0517 ✅ 🟠** conectividade × credito_financeiro × desmatamento_clima — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570)
- **U0518 ✅ 🟠** conectividade × credito_financeiro × educacao — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0519 ✅ ⚪** conectividade × credito_financeiro × fiscal_municipal — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0520 ✅ ⚪⚠** conectividade × credito_financeiro × fiscalizacao_ambiental — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0521 ✅ 🟠** conectividade × credito_financeiro × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547)
- **U0522 ✅ 🟠** conectividade × credito_financeiro × mineracao_energia — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0523 ✅ 🟠** conectividade × credito_financeiro × mortalidade — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570)
- **U0524 ✅ 🟠** conectividade × credito_financeiro × natalidade — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0525 ✅ 🟠** conectividade × credito_financeiro × sancao_integridade — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0526 ✅ 🟡⚠** conectividade × credito_financeiro × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570)
- **U0527 ✅ 🟠** conectividade × credito_financeiro × saude_producao — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565)
- **U0528 ✅ 🟠** conectividade × credito_financeiro × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568)
- **U0529 ✅ 🟠** conectividade × credito_financeiro × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555)
- **U0530 ✅ 🟠⚠** conectividade × credito_financeiro × vigilancia_sinan — `pix_penetracao`×`densidade_smp` **+0,37** (n=5.570) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0531 ✅ 🟠** conectividade × cultura_consumo × demografia_censo — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565)
- **U0532 ✅ 🟠** conectividade × cultura_consumo × desmatamento_clima — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0533 ✅ 🟠** conectividade × cultura_consumo × educacao — `ies_pc`×`relig_100k` **+0,28** (n=719) · `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0534 ✅ ⚪** conectividade × cultura_consumo × fiscal_municipal — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0535 ✅ ⚪** conectividade × cultura_consumo × fiscalizacao_ambiental — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0536 ✅ 🟠⚠** conectividade × cultura_consumo × fundiario — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0537 ✅ 🟠** conectividade × cultura_consumo × mineracao_energia — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0538 ✅ 🟠⚠** conectividade × cultura_consumo × mortalidade — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0539 ✅ 🟠** conectividade × cultura_consumo × natalidade — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `cesarea`×`relig_100k` **+0,23** (n=1.733) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0540 ✅ 🟠⚠** conectividade × cultura_consumo × sancao_integridade — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0541 ✅ 🟠⚠** conectividade × cultura_consumo × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570)
- **U0542 ✅ 🟠** conectividade × cultura_consumo × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599)
- **U0543 ✅ 🟠** conectividade × cultura_consumo × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0544 ✅ 🟠** conectividade × cultura_consumo × transferencia_renda — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555)
- **U0545 ✅ 🟠⚠** conectividade × cultura_consumo × vigilancia_sinan — `cobertura_pop_4g5g`×`templos_1000dom` **-0,28** (n=5.570) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0546 ✅ ⚪** conectividade × demografia_censo × desmatamento_clima — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0547 ✅ 🟠** conectividade × demografia_censo × educacao — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0548 ✅ ⚪** conectividade × demografia_censo × fiscal_municipal — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) — 2/3 pernas sobrevivem ao controle
- **U0549 ✅ ⚪** conectividade × demografia_censo × fiscalizacao_ambiental — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U0550 ✅ 🟠** conectividade × demografia_censo × fundiario — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0551 ✅ 🟠** conectividade × demografia_censo × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0552 ✅ 🟠** conectividade × demografia_censo × mortalidade — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565)
- **U0553 ✅ 🟠** conectividade × demografia_censo × natalidade — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0554 ✅ 🟠** conectividade × demografia_censo × sancao_integridade — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0555 ✅ 🟡⚠** conectividade × demografia_censo × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565)
- **U0556 ✅ 🟡** conectividade × demografia_censo × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565)
- **U0557 ✅ 🟠** conectividade × demografia_censo × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568)
- **U0558 ✅ 🟠** conectividade × demografia_censo × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555)
- **U0559 ✅ 🟠⚠** conectividade × demografia_censo × vigilancia_sinan — `idhm_2010`×`cobertura_pop_4g5g` **+0,39** (n=5.565) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950)
- **U0560 ✅ 🟠** conectividade × desmatamento_clima × educacao — `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `ies_pc`×`desmat_share` **+0,16** (n=719) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0561 ✅ ⚪** conectividade × desmatamento_clima × fiscal_municipal — `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0562 ✅ ⚪⚠** conectividade × desmatamento_clima × fiscalizacao_ambiental — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0563 ✅ 🟠** conectividade × desmatamento_clima × fundiario — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547)
- **U0564 ✅ 🟠** conectividade × desmatamento_clima × mineracao_energia — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0565 ✅ 🟠** conectividade × desmatamento_clima × mortalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U0566 ✅ 🟠** conectividade × desmatamento_clima × natalidade — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0567 ✅ ⚪** conectividade × desmatamento_clima × sancao_integridade — `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0568 ✅ 🟠⚠** conectividade × desmatamento_clima × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570)
- **U0569 ✅ 🟠** conectividade × desmatamento_clima × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U0570 ✅ 🟠** conectividade × desmatamento_clima × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570)
- **U0571 ✅ 🟠** conectividade × desmatamento_clima × transferencia_renda — `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570)
- **U0572 ✅ ⚪⚠** conectividade × desmatamento_clima × vigilancia_sinan — `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `desmat_share`×`cobertura_pop_4g5g` **+0,18** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0573 ✅ ⚪** conectividade × educacao × fiscal_municipal — `ies_pc`×`capag_ind2` **+0,14** (n=700) · `sisu_pc`×`ibc` **+0,14** (n=551) — 2/3 pernas sobrevivem ao controle
- **U0574 ✅ ⚪⚠** conectividade × educacao × fiscalizacao_ambiental — `sisu_pc`×`ibc` **+0,14** (n=551) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U0575 ✅ 🟠** conectividade × educacao × fundiario — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0576 ✅ 🟠** conectividade × educacao × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0577 ✅ 🟠** conectividade × educacao × mortalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0578 ✅ 🟠** conectividade × educacao × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `cesarea`×`ibc` **+0,15** (n=1.733) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0579 ✅ 🟠⚠** conectividade × educacao × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `sisu_pc`×`ibc` **+0,14** (n=551) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0580 ✅ 🟠⚠** conectividade × educacao × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `ies_pc`×`atlas_individual` **-0,21** (n=719) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0581 ✅ 🟠** conectividade × educacao × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0582 ✅ 🟠** conectividade × educacao × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0583 ✅ 🟠** conectividade × educacao × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `sisu_pc`×`ibc` **+0,14** (n=551)
- **U0584 ✅ 🟠⚠** conectividade × educacao × vigilancia_sinan — `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `sisu_pc`×`ibc` **+0,14** (n=551) · `ies_pc`×`notif_100k` **+0,14** (n=713)
- **U0585 ✅ ⚪⚠** conectividade × fiscal_municipal × fiscalizacao_ambiental — `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 1/3 pernas sobrevivem ao controle
- **U0586 ✅ ⚪** conectividade × fiscal_municipal × fundiario — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) — 2/3 pernas sobrevivem ao controle
- **U0587 ✅ ⚪** conectividade × fiscal_municipal × mineracao_energia — `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) — 1/3 pernas sobrevivem ao controle
- **U0588 ✅ ⚪** conectividade × fiscal_municipal × mortalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0589 ✅ ⚪** conectividade × fiscal_municipal × natalidade — `cesarea`×`ibc` **+0,15** (n=1.733) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) — 2/3 pernas sobrevivem ao controle
- **U0590 ✅ ⚪⚠** conectividade × fiscal_municipal × sancao_integridade — `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0591 ✅ ⚪⚠** conectividade × fiscal_municipal × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) — 1/3 pernas sobrevivem ao controle
- **U0592 ✅ ⚪** conectividade × fiscal_municipal × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U0593 ✅ ⚪** conectividade × fiscal_municipal × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0594 ✅ ⚪** conectividade × fiscal_municipal × transferencia_renda — `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) — 2/3 pernas sobrevivem ao controle
- **U0595 ✅ ⚪⚠** conectividade × fiscal_municipal × vigilancia_sinan — `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) — 1/3 pernas sobrevivem ao controle
- **U0596 ✅ ⚪⚠** conectividade × fiscalizacao_ambiental × fundiario — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U0597 ✅ ⚪** conectividade × fiscalizacao_ambiental × mineracao_energia — `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) — 1/3 pernas sobrevivem ao controle
- **U0598 ✅ ⚪** conectividade × fiscalizacao_ambiental × mortalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0599 ✅ ⚪** conectividade × fiscalizacao_ambiental × natalidade — `cesarea`×`ibc` **+0,15** (n=1.733) — 1/3 pernas sobrevivem ao controle
- **U0600 ✅ ⚪** conectividade × fiscalizacao_ambiental × sancao_integridade — `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061) — 1/3 pernas sobrevivem ao controle
- **U0601 ✅ ⚪⚠** conectividade × fiscalizacao_ambiental × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) — 1/3 pernas sobrevivem ao controle
- **U0602 ✅ ⚪** conectividade × fiscalizacao_ambiental × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U0603 ✅ ⚪** conectividade × fiscalizacao_ambiental × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) — 1/3 pernas sobrevivem ao controle
- **U0604 ✅ ⚪⚠** conectividade × fiscalizacao_ambiental × transferencia_renda — `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) — 2/3 pernas sobrevivem ao controle
- **U0605 ✅ ⚪⚠** conectividade × fiscalizacao_ambiental × vigilancia_sinan — `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) — 1/3 pernas sobrevivem ao controle
- **U0606 ✅ 🟠** conectividade × fundiario × mineracao_energia — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543)
- **U0607 ✅ 🟠** conectividade × fundiario × mortalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547)
- **U0608 ✅ 🟠** conectividade × fundiario × natalidade — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0609 ✅ ⚪** conectividade × fundiario × sancao_integridade — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0610 ✅ 🟠⚠** conectividade × fundiario × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547)
- **U0611 ✅ 🟠** conectividade × fundiario × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U0612 ✅ 🟠** conectividade × fundiario × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U0613 ✅ 🟠** conectividade × fundiario × transferencia_renda — `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541)
- **U0614 ✅ ⚪⚠** conectividade × fundiario × vigilancia_sinan — `cafir_ha_por_imovel`×`cobertura_pop_4g5g` **+0,23** (n=5.547) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0615 ✅ 🟠** conectividade × mineracao_energia × mortalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566)
- **U0616 ✅ 🟠** conectividade × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0617 ✅ ⚪** conectividade × mineracao_energia × sancao_integridade — `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0618 ✅ 🟠⚠** conectividade × mineracao_energia × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U0619 ✅ 🟠** conectividade × mineracao_energia × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0620 ✅ 🟠** conectividade × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0621 ✅ 🟠** conectividade × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0622 ✅ 🟠⚠** conectividade × mineracao_energia × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `ibc`×`gd_por_domicilio` **+0,17** (n=5.566)
- **U0623 ✅ 🟠** conectividade × mortalidade × natalidade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0624 ✅ 🟠⚠** conectividade × mortalidade × sancao_integridade — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0625 ✅ 🟠⚠** conectividade × mortalidade × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570)
- **U0626 ✅ 🟠** conectividade × mortalidade × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `cob_priv`×`infec_100k` **+0,19** (n=5.565)
- **U0627 ✅ 🟠** conectividade × mortalidade × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U0628 ✅ 🟠** conectividade × mortalidade × transferencia_renda — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U0629 ✅ ⚪⚠** conectividade × mortalidade × vigilancia_sinan — `infec_100k`×`cobertura_pop_4g5g` **+0,25** (n=5.570) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0630 ✅ 🟠⚠** conectividade × natalidade × sancao_integridade — `cesarea`×`sanc_100k` **+0,15** (n=878) · `cesarea`×`ibc` **+0,15** (n=1.733) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0631 ✅ 🟠⚠** conectividade × natalidade × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0632 ✅ 🟠** conectividade × natalidade × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0633 ✅ 🟠** conectividade × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0634 ✅ 🟠** conectividade × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0635 ✅ 🟠⚠** conectividade × natalidade × vigilancia_sinan — `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `notif_100k`×`cesarea` **+0,15** (n=1.672) · `cesarea`×`ibc` **+0,15** (n=1.733)
- **U0636 ✅ 🟠⚠** conectividade × sancao_integridade × saneamento_agua — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U0637 ✅ 🟠⚠** conectividade × sancao_integridade × saude_producao — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0638 ✅ 🟠⚠** conectividade × sancao_integridade × trabalho_empresa — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0639 ✅ 🟠⚠** conectividade × sancao_integridade × transferencia_renda — `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061)
- **U0640 ✅ ⚪⚠** conectividade × sancao_integridade × vigilancia_sinan — `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `pago_a_devedor`×`cobertura_pop_4g5g` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0641 ✅ 🟡⚠** conectividade × saneamento_agua × saude_producao — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565)
- **U0642 ✅ 🟠⚠** conectividade × saneamento_agua × trabalho_empresa — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568)
- **U0643 ✅ 🟠⚠** conectividade × saneamento_agua × transferencia_renda — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U0644 ✅ 🟠⚠** conectividade × saneamento_agua × vigilancia_sinan — `snis_gap_agua`×`cobertura_pop_4g5g` **+0,63** (n=5.302) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950)
- **U0645 ✅ 🟠** conectividade × saude_producao × trabalho_empresa — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568)
- **U0646 ✅ 🟠** conectividade × saude_producao × transferencia_renda — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555)
- **U0647 ✅ 🟠⚠** conectividade × saude_producao × vigilancia_sinan — `cob_priv`×`cobertura_pop_4g5g` **+0,36** (n=5.565) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `cob_priv`×`notif_100k` **+0,13** (n=4.945)
- **U0648 ✅ 🟠** conectividade × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `nbf_share_dom`×`ibc` **-0,24** (n=5.555)
- **U0649 ✅ 🟠⚠** conectividade × trabalho_empresa × vigilancia_sinan — `cno_1000dom`×`cobertura_pop_4g5g` **+0,29** (n=5.568) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `formal_obra`×`notif_100k` **+0,17** (n=4.948)
- **U0650 ✅ 🟠⚠** conectividade × transferencia_renda × vigilancia_sinan — `nbf_share_dom`×`ibc` **-0,24** (n=5.555) · `notif_100k`×`cobertura_pop_4g5g` **+0,18** (n=4.950) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U0651 ✅ 🟠⚠** credito_financeiro × cultura_consumo × demografia_censo — `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565)
- **U0652 ✅ 🟠⚠** credito_financeiro × cultura_consumo × desmatamento_clima — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0653 ✅ 🟠⚠** credito_financeiro × cultura_consumo × educacao — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ies_pc`×`relig_100k` **+0,28** (n=719) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563)
- **U0654 ✅ ⚪⚠** credito_financeiro × cultura_consumo × fiscal_municipal — `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0655 ✅ ⚪⚠** credito_financeiro × cultura_consumo × fiscalizacao_ambiental — `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0656 ✅ 🟠⚠** credito_financeiro × cultura_consumo × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0657 ✅ 🟠⚠** credito_financeiro × cultura_consumo × mineracao_energia — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566)
- **U0658 ✅ 🟠⚠** credito_financeiro × cultura_consumo × mortalidade — `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0659 ✅ 🟠⚠** credito_financeiro × cultura_consumo × natalidade — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `cesarea`×`relig_100k` **+0,23** (n=1.733)
- **U0660 ✅ 🟠⚠** credito_financeiro × cultura_consumo × sancao_integridade — `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0661 ✅ 🟠⚠** credito_financeiro × cultura_consumo × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563)
- **U0662 ✅ 🟠⚠** credito_financeiro × cultura_consumo × saude_producao — `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599)
- **U0663 ✅ 🟠⚠** credito_financeiro × cultura_consumo × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0664 ✅ 🟠⚠** credito_financeiro × cultura_consumo × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555)
- **U0665 ✅ 🟠⚠** credito_financeiro × cultura_consumo × vigilancia_sinan — `pix_penetracao`×`reclam_100k` **+0,27** (n=5.563) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0666 ✅ ⚪** credito_financeiro × demografia_censo × desmatamento_clima — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U0667 ✅ 🟡** credito_financeiro × demografia_censo × educacao — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565)
- **U0668 ✅ 🟠** credito_financeiro × demografia_censo × fiscal_municipal — `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542)
- **U0669 ✅ ⚪⚠** credito_financeiro × demografia_censo × fiscalizacao_ambiental — `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0670 ✅ 🟠** credito_financeiro × demografia_censo × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0671 ✅ 🟡** credito_financeiro × demografia_censo × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565)
- **U0672 ✅ 🟠** credito_financeiro × demografia_censo × mortalidade — `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565)
- **U0673 ✅ 🟡** credito_financeiro × demografia_censo × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733)
- **U0674 ✅ 🟠** credito_financeiro × demografia_censo × sancao_integridade — `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0675 ✅ 🟡⚠** credito_financeiro × demografia_censo × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565)
- **U0676 ✅ 🟠** credito_financeiro × demografia_censo × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565)
- **U0677 ✅ 🟡** credito_financeiro × demografia_censo × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565)
- **U0678 ✅ 🟡** credito_financeiro × demografia_censo × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565)
- **U0679 ✅ 🟠⚠** credito_financeiro × demografia_censo × vigilancia_sinan — `ivs_2010`×`pix_ticket_pf` **-0,34** (n=5.565) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0680 ✅ 🟠** credito_financeiro × desmatamento_clima × educacao — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ies_pc`×`desmat_share` **+0,16** (n=719)
- **U0681 ✅ ⚪** credito_financeiro × desmatamento_clima × fiscal_municipal — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0682 ✅ 🟠⚠** credito_financeiro × desmatamento_clima × fiscalizacao_ambiental — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `cred_ha`×`autos_100k` **-0,12** (n=4.150)
- **U0683 ✅ 🟠** credito_financeiro × desmatamento_clima × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547)
- **U0684 ✅ 🟠** credito_financeiro × desmatamento_clima × mineracao_energia — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566)
- **U0685 ✅ 🟠** credito_financeiro × desmatamento_clima × mortalidade — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U0686 ✅ 🟠** credito_financeiro × desmatamento_clima × natalidade — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `cesarea`×`desmat_share` **+0,27** (n=1.733)
- **U0687 ✅ ⚪** credito_financeiro × desmatamento_clima × sancao_integridade — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0688 ✅ 🟠⚠** credito_financeiro × desmatamento_clima × saneamento_agua — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570)
- **U0689 ✅ 🟠** credito_financeiro × desmatamento_clima × saude_producao — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U0690 ✅ 🟠** credito_financeiro × desmatamento_clima × trabalho_empresa — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `formal_obra`×`desmat_share` **+0,27** (n=5.568)
- **U0691 ✅ 🟠** credito_financeiro × desmatamento_clima × transferencia_renda — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803)
- **U0692 ✅ ⚪⚠** credito_financeiro × desmatamento_clima × vigilancia_sinan — `credito_ha`×`desmat_share` **+0,45** (n=5.456) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0693 ✅ 🟠** credito_financeiro × educacao × fiscal_municipal — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `ies_pc`×`capag_ind2` **+0,14** (n=700)
- **U0694 ✅ 🟠⚠** credito_financeiro × educacao × fiscalizacao_ambiental — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) · `ies_pc`×`emb_100k` **+0,12** (n=648)
- **U0695 ✅ 🟠** credito_financeiro × educacao × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408)
- **U0696 ✅ 🟡** credito_financeiro × educacao × mineracao_energia — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543)
- **U0697 ✅ 🟠** credito_financeiro × educacao × mortalidade — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `pdm_share`×`homic_100k` **+0,15** (n=5.547)
- **U0698 ✅ 🟡** credito_financeiro × educacao × natalidade — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `pdm_share`×`cesarea` **-0,30** (n=1.731)
- **U0699 ✅ 🟠⚠** credito_financeiro × educacao × sancao_integridade — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ies_pc`×`sanc_100k` **+0,26** (n=555) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0700 ✅ 🟠⚠** credito_financeiro × educacao × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ies_pc`×`atlas_individual` **-0,21** (n=719)
- **U0701 ✅ 🟠** credito_financeiro × educacao × saude_producao — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ies_pc`×`leitos_1000` **+0,37** (n=706) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565)
- **U0702 ✅ 🟠** credito_financeiro × educacao × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `formal_obra`×`pdm_share` **-0,30** (n=5.545)
- **U0703 ✅ 🟠** credito_financeiro × educacao × transferencia_renda — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `ideb`×`nbf_share_dom` **-0,29** (n=5.415)
- **U0704 ✅ 🟠⚠** credito_financeiro × educacao × vigilancia_sinan — `pdm_share`×`pix_ticket_pf` **-0,40** (n=5.547) · `ies_pc`×`notif_100k` **+0,14** (n=713) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0705 ✅ 🟠⚠** credito_financeiro × fiscal_municipal × fiscalizacao_ambiental — `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318)
- **U0706 ✅ 🟠** credito_financeiro × fiscal_municipal × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520)
- **U0707 ✅ ⚪** credito_financeiro × fiscal_municipal × mineracao_energia — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0708 ✅ ⚪** credito_financeiro × fiscal_municipal × mortalidade — `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0709 ✅ 🟠** credito_financeiro × fiscal_municipal × natalidade — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U0710 ✅ 🟠⚠** credito_financeiro × fiscal_municipal × sancao_integridade — `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0711 ✅ ⚪⚠** credito_financeiro × fiscal_municipal × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0712 ✅ ⚪** credito_financeiro × fiscal_municipal × saude_producao — `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0713 ✅ 🟠** credito_financeiro × fiscal_municipal × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542)
- **U0714 ✅ 🟠** credito_financeiro × fiscal_municipal × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014)
- **U0715 ✅ ⚪⚠** credito_financeiro × fiscal_municipal × vigilancia_sinan — `pix_penetracao`×`sic_pessoal_pc` **+0,18** (n=5.542) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0716 ✅ 🟠⚠** credito_financeiro × fiscalizacao_ambiental × fundiario — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322)
- **U0717 ✅ ⚪⚠** credito_financeiro × fiscalizacao_ambiental × mineracao_energia — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0718 ✅ ⚪⚠** credito_financeiro × fiscalizacao_ambiental × mortalidade — `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0719 ✅ ⚪⚠** credito_financeiro × fiscalizacao_ambiental × natalidade — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0720 ✅ ⚪⚠** credito_financeiro × fiscalizacao_ambiental × sancao_integridade — `cred_ha`×`autos_100k` **-0,12** (n=4.150) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0721 ✅ ⚪⚠** credito_financeiro × fiscalizacao_ambiental × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0722 ✅ ⚪⚠** credito_financeiro × fiscalizacao_ambiental × saude_producao — `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0723 ✅ ⚪⚠** credito_financeiro × fiscalizacao_ambiental × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `cred_ha`×`autos_100k` **-0,12** (n=4.150) — 2/3 pernas sobrevivem ao controle
- **U0724 ✅ 🟠⚠** credito_financeiro × fiscalizacao_ambiental × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `cred_ha`×`autos_100k` **-0,12** (n=4.150)
- **U0725 ✅ ⚪⚠** credito_financeiro × fiscalizacao_ambiental × vigilancia_sinan — `cred_ha`×`autos_100k` **-0,12** (n=4.150) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0726 ✅ 🟠** credito_financeiro × fundiario × mineracao_energia — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543)
- **U0727 ✅ 🟠** credito_financeiro × fundiario × mortalidade — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547)
- **U0728 ✅ 🟠** credito_financeiro × fundiario × natalidade — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729)
- **U0729 ✅ ⚪** credito_financeiro × fundiario × sancao_integridade — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0730 ✅ 🟠⚠** credito_financeiro × fundiario × saneamento_agua — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279)
- **U0731 ✅ 🟠** credito_financeiro × fundiario × saude_producao — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U0732 ✅ 🟠** credito_financeiro × fundiario × trabalho_empresa — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U0733 ✅ 🟠** credito_financeiro × fundiario × transferencia_renda — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541)
- **U0734 ✅ ⚪⚠** credito_financeiro × fundiario × vigilancia_sinan — `sicor_hhi_tomador`×`cafir_ha_por_imovel` **+0,48** (n=5.370) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0735 ✅ 🟠** credito_financeiro × mineracao_energia × mortalidade — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566)
- **U0736 ✅ 🟡** credito_financeiro × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733)
- **U0737 ✅ ⚪** credito_financeiro × mineracao_energia × sancao_integridade — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0738 ✅ 🟠⚠** credito_financeiro × mineracao_energia × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U0739 ✅ 🟠** credito_financeiro × mineracao_energia × saude_producao — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565)
- **U0740 ✅ 🟡** credito_financeiro × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566)
- **U0741 ✅ 🟡** credito_financeiro × mineracao_energia × transferencia_renda — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551)
- **U0742 ✅ 🟠⚠** credito_financeiro × mineracao_energia × vigilancia_sinan — `pix_ticket_pf`×`gd_por_domicilio` **+0,40** (n=5.566) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0743 ✅ 🟠** credito_financeiro × mortalidade × natalidade — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `homic_100k`×`mae_adol` **+0,20** (n=1.733)
- **U0744 ✅ 🟠⚠** credito_financeiro × mortalidade × sancao_integridade — `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0745 ✅ 🟠⚠** credito_financeiro × mortalidade × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570)
- **U0746 ✅ 🟠** credito_financeiro × mortalidade × saude_producao — `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `cob_priv`×`infec_100k` **+0,19** (n=5.565)
- **U0747 ✅ 🟠** credito_financeiro × mortalidade × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U0748 ✅ 🟠** credito_financeiro × mortalidade × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U0749 ✅ ⚪⚠** credito_financeiro × mortalidade × vigilancia_sinan — `infec_100k`×`pix_penetracao` **+0,24** (n=5.570) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0750 ✅ 🟠⚠** credito_financeiro × natalidade × sancao_integridade — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `cesarea`×`sanc_100k` **+0,15** (n=878) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0751 ✅ 🟠⚠** credito_financeiro × natalidade × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U0752 ✅ 🟠** credito_financeiro × natalidade × saude_producao — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565)
- **U0753 ✅ 🟠** credito_financeiro × natalidade × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `formal_obra`×`cesarea` **+0,30** (n=1.733)
- **U0754 ✅ 🟡** credito_financeiro × natalidade × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733)
- **U0755 ✅ 🟠⚠** credito_financeiro × natalidade × vigilancia_sinan — `cesarea`×`pix_ticket_pf` **+0,34** (n=1.733) · `notif_100k`×`cesarea` **+0,15** (n=1.672) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0756 ✅ 🟠⚠** credito_financeiro × sancao_integridade × saneamento_agua — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U0757 ✅ 🟠⚠** credito_financeiro × sancao_integridade × saude_producao — `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0758 ✅ 🟠⚠** credito_financeiro × sancao_integridade × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0759 ✅ 🟠⚠** credito_financeiro × sancao_integridade × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) · `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061)
- **U0760 ✅ ⚪⚠** credito_financeiro × sancao_integridade × vigilancia_sinan — `pix_penetracao`×`pago_a_devedor` **+0,11** (n=3.061) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0761 ✅ 🟠⚠** credito_financeiro × saneamento_agua × saude_producao — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565)
- **U0762 ✅ 🟡⚠** credito_financeiro × saneamento_agua × trabalho_empresa — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `formalidade`×`snis_gap_agua` **+0,31** (n=5.302)
- **U0763 ✅ 🟠⚠** credito_financeiro × saneamento_agua × transferencia_renda — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U0764 ✅ 🟠⚠** credito_financeiro × saneamento_agua × vigilancia_sinan — `pix_penetracao`×`snis_gap_agua` **+0,43** (n=5.302) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0765 ✅ 🟠** credito_financeiro × saude_producao × trabalho_empresa — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565)
- **U0766 ✅ 🟠** credito_financeiro × saude_producao × transferencia_renda — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565)
- **U0767 ✅ 🟠⚠** credito_financeiro × saude_producao × vigilancia_sinan — `cob_priv`×`pix_pag_pc` **+0,28** (n=5.565) · `cob_priv`×`notif_100k` **+0,13** (n=4.945) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0768 ✅ 🟡** credito_financeiro × trabalho_empresa × transferencia_renda — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553)
- **U0769 ✅ 🟠⚠** credito_financeiro × trabalho_empresa × vigilancia_sinan — `formalidade`×`pix_pag_pc` **+0,40** (n=5.570) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0770 ✅ 🟠⚠** credito_financeiro × transferencia_renda × vigilancia_sinan — `nbf_share_dom`×`pix_ticket_pf` **-0,38** (n=5.555) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) · `notif_100k`×`pix_pag_pc` **+0,10** (n=4.950)
- **U0771 ✅ ⚪** cultura_consumo × demografia_censo × desmatamento_clima — `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0772 ✅ 🟠** cultura_consumo × demografia_censo × educacao — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ies_pc`×`relig_100k` **+0,28** (n=719) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565)
- **U0773 ✅ ⚪** cultura_consumo × demografia_censo × fiscal_municipal — `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) — 2/3 pernas sobrevivem ao controle
- **U0774 ✅ ⚪** cultura_consumo × demografia_censo × fiscalizacao_ambiental — `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U0775 ✅ 🟠⚠** cultura_consumo × demografia_censo × fundiario — `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0776 ✅ 🟠** cultura_consumo × demografia_censo × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566)
- **U0777 ✅ 🟠⚠** cultura_consumo × demografia_censo × mortalidade — `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0778 ✅ 🟠** cultura_consumo × demografia_censo × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `cesarea`×`relig_100k` **+0,23** (n=1.733)
- **U0779 ✅ 🟠⚠** cultura_consumo × demografia_censo × sancao_integridade — `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061)
- **U0780 ✅ 🟠⚠** cultura_consumo × demografia_censo × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565)
- **U0781 ✅ 🟠** cultura_consumo × demografia_censo × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599)
- **U0782 ✅ 🟠** cultura_consumo × demografia_censo × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0783 ✅ 🟠** cultura_consumo × demografia_censo × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555)
- **U0784 ✅ 🟠⚠** cultura_consumo × demografia_censo × vigilancia_sinan — `ivs_2010`×`templos_1000dom` **+0,26** (n=5.565) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0785 ✅ 🟠** cultura_consumo × desmatamento_clima × educacao — `ies_pc`×`relig_100k` **+0,28** (n=719) · `ies_pc`×`desmat_share` **+0,16** (n=719) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0786 ✅ ⚪** cultura_consumo × desmatamento_clima × fiscal_municipal — `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0787 ✅ ⚪⚠** cultura_consumo × desmatamento_clima × fiscalizacao_ambiental — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0788 ✅ 🟠⚠** cultura_consumo × desmatamento_clima × fundiario — `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0789 ✅ 🟠** cultura_consumo × desmatamento_clima × mineracao_energia — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0790 ✅ 🟠⚠** cultura_consumo × desmatamento_clima × mortalidade — `infec_100k`×`reclam_100k` **+0,12** (n=5.563) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U0791 ✅ 🟠** cultura_consumo × desmatamento_clima × natalidade — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `cesarea`×`relig_100k` **+0,23** (n=1.733) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0792 ✅ ⚪⚠** cultura_consumo × desmatamento_clima × sancao_integridade — `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0793 ✅ 🟠⚠** cultura_consumo × desmatamento_clima × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0794 ✅ 🟠** cultura_consumo × desmatamento_clima × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U0795 ✅ 🟠** cultura_consumo × desmatamento_clima × trabalho_empresa — `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0796 ✅ 🟠** cultura_consumo × desmatamento_clima × transferencia_renda — `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570)
- **U0797 ✅ ⚪⚠** cultura_consumo × desmatamento_clima × vigilancia_sinan — `desmat_share`×`comercio_por_dom` **+0,12** (n=5.570) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0798 ✅ ⚪** cultura_consumo × educacao × fiscal_municipal — `ies_pc`×`relig_100k` **+0,28** (n=719) · `ies_pc`×`capag_ind2` **+0,14** (n=700) — 2/3 pernas sobrevivem ao controle
- **U0799 ✅ ⚪⚠** cultura_consumo × educacao × fiscalizacao_ambiental — `ies_pc`×`relig_100k` **+0,28** (n=719) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U0800 ✅ 🟠⚠** cultura_consumo × educacao × fundiario — `ies_pc`×`relig_100k` **+0,28** (n=719) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0801 ✅ 🟠** cultura_consumo × educacao × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `ies_pc`×`relig_100k` **+0,28** (n=719) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566)
- **U0802 ✅ 🟠⚠** cultura_consumo × educacao × mortalidade — `ies_pc`×`relig_100k` **+0,28** (n=719) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0803 ✅ 🟠** cultura_consumo × educacao × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `ies_pc`×`relig_100k` **+0,28** (n=719) · `cesarea`×`relig_100k` **+0,23** (n=1.733)
- **U0804 ✅ 🟠⚠** cultura_consumo × educacao × sancao_integridade — `ies_pc`×`relig_100k` **+0,28** (n=719) · `ies_pc`×`sanc_100k` **+0,26** (n=555) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483)
- **U0805 ✅ 🟠⚠** cultura_consumo × educacao × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `ies_pc`×`relig_100k` **+0,28** (n=719) · `ies_pc`×`atlas_individual` **-0,21** (n=719)
- **U0806 ✅ 🟠** cultura_consumo × educacao × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `ies_pc`×`relig_100k` **+0,28** (n=719) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599)
- **U0807 ✅ 🟠** cultura_consumo × educacao × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `ies_pc`×`relig_100k` **+0,28** (n=719) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0808 ✅ 🟠** cultura_consumo × educacao × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `ies_pc`×`relig_100k` **+0,28** (n=719) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555)
- **U0809 ✅ 🟠⚠** cultura_consumo × educacao × vigilancia_sinan — `ies_pc`×`relig_100k` **+0,28** (n=719) · `ies_pc`×`notif_100k` **+0,14** (n=713) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0810 ✅ ⚪⚠** cultura_consumo × fiscal_municipal × fiscalizacao_ambiental — `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 1/3 pernas sobrevivem ao controle
- **U0811 ✅ ⚪⚠** cultura_consumo × fiscal_municipal × fundiario — `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) — 2/3 pernas sobrevivem ao controle
- **U0812 ✅ ⚪** cultura_consumo × fiscal_municipal × mineracao_energia — `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) — 1/3 pernas sobrevivem ao controle
- **U0813 ✅ ⚪⚠** cultura_consumo × fiscal_municipal × mortalidade — `infec_100k`×`reclam_100k` **+0,12** (n=5.563) — 1/3 pernas sobrevivem ao controle
- **U0814 ✅ ⚪** cultura_consumo × fiscal_municipal × natalidade — `cesarea`×`relig_100k` **+0,23** (n=1.733) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) — 2/3 pernas sobrevivem ao controle
- **U0815 ✅ ⚪⚠** cultura_consumo × fiscal_municipal × sancao_integridade — `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) — 2/3 pernas sobrevivem ao controle
- **U0816 ✅ ⚪⚠** cultura_consumo × fiscal_municipal × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) — 1/3 pernas sobrevivem ao controle
- **U0817 ✅ ⚪** cultura_consumo × fiscal_municipal × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) — 1/3 pernas sobrevivem ao controle
- **U0818 ✅ ⚪** cultura_consumo × fiscal_municipal × trabalho_empresa — `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0819 ✅ ⚪** cultura_consumo × fiscal_municipal × transferencia_renda — `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) — 2/3 pernas sobrevivem ao controle
- **U0820 ✅ ⚪⚠** cultura_consumo × fiscal_municipal × vigilancia_sinan — `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) — 1/3 pernas sobrevivem ao controle
- **U0821 ✅ ⚪⚠** cultura_consumo × fiscalizacao_ambiental × fundiario — `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U0822 ✅ ⚪** cultura_consumo × fiscalizacao_ambiental × mineracao_energia — `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) — 1/3 pernas sobrevivem ao controle
- **U0823 ✅ ⚪⚠** cultura_consumo × fiscalizacao_ambiental × mortalidade — `infec_100k`×`reclam_100k` **+0,12** (n=5.563) — 1/3 pernas sobrevivem ao controle
- **U0824 ✅ ⚪** cultura_consumo × fiscalizacao_ambiental × natalidade — `cesarea`×`relig_100k` **+0,23** (n=1.733) — 1/3 pernas sobrevivem ao controle
- **U0825 ✅ ⚪⚠** cultura_consumo × fiscalizacao_ambiental × sancao_integridade — `sanc_100k`×`relig_100k` **+0,17** (n=1.483) — 1/3 pernas sobrevivem ao controle
- **U0826 ✅ ⚪⚠** cultura_consumo × fiscalizacao_ambiental × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) — 1/3 pernas sobrevivem ao controle
- **U0827 ✅ ⚪** cultura_consumo × fiscalizacao_ambiental × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) — 1/3 pernas sobrevivem ao controle
- **U0828 ✅ ⚪** cultura_consumo × fiscalizacao_ambiental × trabalho_empresa — `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) — 1/3 pernas sobrevivem ao controle
- **U0829 ✅ ⚪⚠** cultura_consumo × fiscalizacao_ambiental × transferencia_renda — `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) — 2/3 pernas sobrevivem ao controle
- **U0830 ✅ ⚪⚠** cultura_consumo × fiscalizacao_ambiental × vigilancia_sinan — `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) — 1/3 pernas sobrevivem ao controle
- **U0831 ✅ 🟠⚠** cultura_consumo × fundiario × mineracao_energia — `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0832 ✅ 🟠⚠** cultura_consumo × fundiario × mortalidade — `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0833 ✅ 🟠⚠** cultura_consumo × fundiario × natalidade — `cesarea`×`relig_100k` **+0,23** (n=1.733) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0834 ✅ ⚪⚠** cultura_consumo × fundiario × sancao_integridade — `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) — 2/3 pernas sobrevivem ao controle
- **U0835 ✅ 🟠⚠** cultura_consumo × fundiario × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0836 ✅ 🟠⚠** cultura_consumo × fundiario × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U0837 ✅ 🟠⚠** cultura_consumo × fundiario × trabalho_empresa — `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U0838 ✅ 🟠⚠** cultura_consumo × fundiario × transferencia_renda — `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545)
- **U0839 ✅ ⚪⚠** cultura_consumo × fundiario × vigilancia_sinan — `cafir_ha_por_imovel`×`reclam_100k` **+0,14** (n=5.545) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0840 ✅ 🟠⚠** cultura_consumo × mineracao_energia × mortalidade — `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0841 ✅ 🟠** cultura_consumo × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `cesarea`×`relig_100k` **+0,23** (n=1.733) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566)
- **U0842 ✅ ⚪⚠** cultura_consumo × mineracao_energia × sancao_integridade — `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U0843 ✅ 🟠⚠** cultura_consumo × mineracao_energia × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U0844 ✅ 🟠** cultura_consumo × mineracao_energia × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566)
- **U0845 ✅ 🟠** cultura_consumo × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566)
- **U0846 ✅ 🟠** cultura_consumo × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566)
- **U0847 ✅ 🟠⚠** cultura_consumo × mineracao_energia × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `gd_por_domicilio`×`relig_100k` **+0,20** (n=5.566) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0848 ✅ 🟠⚠** cultura_consumo × mortalidade × natalidade — `cesarea`×`relig_100k` **+0,23** (n=1.733) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0849 ✅ 🟠⚠** cultura_consumo × mortalidade × sancao_integridade — `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483)
- **U0850 ✅ 🟠⚠** cultura_consumo × mortalidade × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0851 ✅ 🟠⚠** cultura_consumo × mortalidade × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0852 ✅ 🟠⚠** cultura_consumo × mortalidade × trabalho_empresa — `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `formal_obra`×`infec_100k` **+0,12** (n=5.568) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0853 ✅ 🟠⚠** cultura_consumo × mortalidade × transferencia_renda — `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) · `infec_100k`×`reclam_100k` **+0,12** (n=5.563)
- **U0854 ✅ ⚪⚠** cultura_consumo × mortalidade × vigilancia_sinan — `infec_100k`×`reclam_100k` **+0,12** (n=5.563) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0855 ✅ 🟠⚠** cultura_consumo × natalidade × sancao_integridade — `cesarea`×`relig_100k` **+0,23** (n=1.733) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `cesarea`×`sanc_100k` **+0,15** (n=878)
- **U0856 ✅ 🟠⚠** cultura_consumo × natalidade × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `cesarea`×`relig_100k` **+0,23** (n=1.733) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U0857 ✅ 🟠** cultura_consumo × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `cesarea`×`relig_100k` **+0,23** (n=1.733)
- **U0858 ✅ 🟠** cultura_consumo × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `cesarea`×`relig_100k` **+0,23** (n=1.733) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0859 ✅ 🟠** cultura_consumo × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `cesarea`×`relig_100k` **+0,23** (n=1.733) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555)
- **U0860 ✅ 🟠⚠** cultura_consumo × natalidade × vigilancia_sinan — `cesarea`×`relig_100k` **+0,23** (n=1.733) · `notif_100k`×`cesarea` **+0,15** (n=1.672) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0861 ✅ 🟠⚠** cultura_consumo × sancao_integridade × saneamento_agua — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U0862 ✅ 🟠⚠** cultura_consumo × sancao_integridade × saude_producao — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483)
- **U0863 ✅ 🟠⚠** cultura_consumo × sancao_integridade × trabalho_empresa — `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `formalidade`×`sanc_100k` **+0,16** (n=1.483)
- **U0864 ✅ 🟠⚠** cultura_consumo × sancao_integridade × transferencia_renda — `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U0865 ✅ ⚪⚠** cultura_consumo × sancao_integridade × vigilancia_sinan — `sanc_100k`×`relig_100k` **+0,17** (n=1.483) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) — 2/3 pernas sobrevivem ao controle
- **U0866 ✅ 🟠⚠** cultura_consumo × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599)
- **U0867 ✅ 🟠⚠** cultura_consumo × saneamento_agua × trabalho_empresa — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0868 ✅ 🟠⚠** cultura_consumo × saneamento_agua × transferencia_renda — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U0869 ✅ 🟠⚠** cultura_consumo × saneamento_agua × vigilancia_sinan — `snis_gap_agua`×`templos_1000dom` **-0,33** (n=5.302) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0870 ✅ 🟠** cultura_consumo × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0871 ✅ 🟠** cultura_consumo × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555)
- **U0872 ✅ 🟠⚠** cultura_consumo × saude_producao × vigilancia_sinan — `leitos_1000`×`relig_100k` **+0,26** (n=3.599) · `cob_priv`×`notif_100k` **+0,13** (n=4.945) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0873 ✅ 🟠** cultura_consumo × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568)
- **U0874 ✅ 🟠⚠** cultura_consumo × trabalho_empresa × vigilancia_sinan — `cno_1000dom`×`comercio_por_dom` **+0,20** (n=5.568) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950)
- **U0875 ✅ 🟠⚠** cultura_consumo × transferencia_renda × vigilancia_sinan — `nbf_share_dom`×`templos_1000dom` **+0,21** (n=5.555) · `notif_100k`×`templos_1000dom` **-0,11** (n=4.950) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U0876 ✅ ⚪** demografia_censo × desmatamento_clima × educacao — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ies_pc`×`desmat_share` **+0,16** (n=719) — 2/3 pernas sobrevivem ao controle
- **U0877 ✅ ⚪** demografia_censo × desmatamento_clima × fiscal_municipal — `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) — 1/3 pernas sobrevivem ao controle
- **U0878 ✅ ⚪⚠** demografia_censo × desmatamento_clima × fiscalizacao_ambiental — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) — 1/3 pernas sobrevivem ao controle
- **U0879 ✅ ⚪** demografia_censo × desmatamento_clima × fundiario — `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0880 ✅ ⚪** demografia_censo × desmatamento_clima × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U0881 ✅ ⚪** demografia_censo × desmatamento_clima × mortalidade — `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `infec_100k`×`desmat_share` **+0,11** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0882 ✅ ⚪** demografia_censo × desmatamento_clima × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `cesarea`×`desmat_share` **+0,27** (n=1.733) — 2/3 pernas sobrevivem ao controle
- **U0883 ✅ ⚪** demografia_censo × desmatamento_clima × sancao_integridade — `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) — 1/3 pernas sobrevivem ao controle
- **U0884 ✅ ⚪⚠** demografia_censo × desmatamento_clima × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0885 ✅ ⚪** demografia_censo × desmatamento_clima × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `cob_priv`×`desmat_share` **+0,10** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U0886 ✅ ⚪** demografia_censo × desmatamento_clima × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) — 2/3 pernas sobrevivem ao controle
- **U0887 ✅ ⚪** demografia_censo × desmatamento_clima × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) — 2/3 pernas sobrevivem ao controle
- **U0888 ✅ ⚪⚠** demografia_censo × desmatamento_clima × vigilancia_sinan — `idhm_2010`×`notif_100k` **+0,19** (n=4.945) — 1/3 pernas sobrevivem ao controle
- **U0889 ✅ 🟠** demografia_censo × educacao × fiscal_municipal — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `ies_pc`×`capag_ind2` **+0,14** (n=700)
- **U0890 ✅ ⚪⚠** demografia_censo × educacao × fiscalizacao_ambiental — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U0891 ✅ 🟠** demografia_censo × educacao × fundiario — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0892 ✅ 🟡** demografia_censo × educacao × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543)
- **U0893 ✅ 🟠** demografia_censo × educacao × mortalidade — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `pdm_share`×`homic_100k` **+0,15** (n=5.547)
- **U0894 ✅ 🟡** demografia_censo × educacao × natalidade — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `pdm_share`×`cesarea` **-0,30** (n=1.731)
- **U0895 ✅ 🟠⚠** demografia_censo × educacao × sancao_integridade — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ies_pc`×`sanc_100k` **+0,26** (n=555) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061)
- **U0896 ✅ 🟠⚠** demografia_censo × educacao × saneamento_agua — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `ies_pc`×`atlas_individual` **-0,21** (n=719)
- **U0897 ✅ 🟡** demografia_censo × educacao × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ies_pc`×`leitos_1000` **+0,37** (n=706)
- **U0898 ✅ 🟠** demografia_censo × educacao × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `formal_obra`×`pdm_share` **-0,30** (n=5.545)
- **U0899 ✅ 🟠** demografia_censo × educacao × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `ideb`×`nbf_share_dom` **-0,29** (n=5.415)
- **U0900 ✅ 🟠⚠** demografia_censo × educacao × vigilancia_sinan — `ivs_2010`×`pdm_share` **+0,41** (n=5.542) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `ies_pc`×`notif_100k` **+0,14** (n=713)
- **U0901 ✅ ⚪⚠** demografia_censo × fiscal_municipal × fiscalizacao_ambiental — `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 2/3 pernas sobrevivem ao controle
- **U0902 ✅ 🟠** demografia_censo × fiscal_municipal × fundiario — `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0903 ✅ ⚪** demografia_censo × fiscal_municipal × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) — 2/3 pernas sobrevivem ao controle
- **U0904 ✅ ⚪** demografia_censo × fiscal_municipal × mortalidade — `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U0905 ✅ 🟠** demografia_censo × fiscal_municipal × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U0906 ✅ 🟠⚠** demografia_censo × fiscal_municipal × sancao_integridade — `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479)
- **U0907 ✅ ⚪⚠** demografia_censo × fiscal_municipal × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) — 2/3 pernas sobrevivem ao controle
- **U0908 ✅ ⚪** demografia_censo × fiscal_municipal × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) — 2/3 pernas sobrevivem ao controle
- **U0909 ✅ 🟠** demografia_censo × fiscal_municipal × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542)
- **U0910 ✅ 🟠** demografia_censo × fiscal_municipal × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014)
- **U0911 ✅ ⚪⚠** demografia_censo × fiscal_municipal × vigilancia_sinan — `share_nome_top`×`sic_pessoal_pc` **+0,23** (n=5.537) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) — 2/3 pernas sobrevivem ao controle
- **U0912 ✅ ⚪⚠** demografia_censo × fiscalizacao_ambiental × fundiario — `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U0913 ✅ ⚪** demografia_censo × fiscalizacao_ambiental × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) — 1/3 pernas sobrevivem ao controle
- **U0914 ✅ ⚪** demografia_censo × fiscalizacao_ambiental × mortalidade — `idhm_2010`×`infec_100k` **+0,19** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U0915 ✅ ⚪** demografia_censo × fiscalizacao_ambiental × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) — 1/3 pernas sobrevivem ao controle
- **U0916 ✅ ⚪** demografia_censo × fiscalizacao_ambiental × sancao_integridade — `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) — 1/3 pernas sobrevivem ao controle
- **U0917 ✅ ⚪⚠** demografia_censo × fiscalizacao_ambiental × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) — 1/3 pernas sobrevivem ao controle
- **U0918 ✅ ⚪** demografia_censo × fiscalizacao_ambiental × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U0919 ✅ ⚪** demografia_censo × fiscalizacao_ambiental × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) — 1/3 pernas sobrevivem ao controle
- **U0920 ✅ ⚪⚠** demografia_censo × fiscalizacao_ambiental × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) — 2/3 pernas sobrevivem ao controle
- **U0921 ✅ ⚪⚠** demografia_censo × fiscalizacao_ambiental × vigilancia_sinan — `idhm_2010`×`notif_100k` **+0,19** (n=4.945) — 1/3 pernas sobrevivem ao controle
- **U0922 ✅ 🟠** demografia_censo × fundiario × mineracao_energia — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0923 ✅ 🟠** demografia_censo × fundiario × mortalidade — `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0924 ✅ 🟠** demografia_censo × fundiario × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0925 ✅ ⚪** demografia_censo × fundiario × sancao_integridade — `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0926 ✅ 🟠⚠** demografia_censo × fundiario × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0927 ✅ 🟠** demografia_censo × fundiario × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U0928 ✅ 🟠** demografia_censo × fundiario × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U0929 ✅ 🟠** demografia_censo × fundiario × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542)
- **U0930 ✅ ⚪⚠** demografia_censo × fundiario × vigilancia_sinan — `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `ivs_2010`×`cafir_ha_por_imovel` **+0,14** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0931 ✅ 🟠** demografia_censo × mineracao_energia × mortalidade — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566)
- **U0932 ✅ 🟡** demografia_censo × mineracao_energia × natalidade — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `ivs_2010`×`cesarea` **-0,36** (n=1.733)
- **U0933 ✅ ⚪** demografia_censo × mineracao_energia × sancao_integridade — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0934 ✅ 🟠⚠** demografia_censo × mineracao_energia × saneamento_agua — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U0935 ✅ 🟠** demografia_censo × mineracao_energia × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561)
- **U0936 ✅ 🟡** demografia_censo × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563)
- **U0937 ✅ 🟡** demografia_censo × mineracao_energia × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551)
- **U0938 ✅ 🟠⚠** demografia_censo × mineracao_energia × vigilancia_sinan — `ivs_2010`×`gd_por_domicilio` **-0,43** (n=5.561) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945)
- **U0939 ✅ 🟠** demografia_censo × mortalidade × natalidade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565)
- **U0940 ✅ 🟠⚠** demografia_censo × mortalidade × sancao_integridade — `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483)
- **U0941 ✅ 🟠⚠** demografia_censo × mortalidade × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565)
- **U0942 ✅ 🟠** demografia_censo × mortalidade × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565)
- **U0943 ✅ 🟠** demografia_censo × mortalidade × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U0944 ✅ 🟠** demografia_censo × mortalidade × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U0945 ✅ ⚪⚠** demografia_censo × mortalidade × vigilancia_sinan — `idhm_2010`×`infec_100k` **+0,19** (n=5.565) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) — 2/3 pernas sobrevivem ao controle
- **U0946 ✅ 🟠⚠** demografia_censo × natalidade × sancao_integridade — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `cesarea`×`sanc_100k` **+0,15** (n=878)
- **U0947 ✅ 🟠⚠** demografia_censo × natalidade × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U0948 ✅ 🟡** demografia_censo × natalidade × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `leitos_1000`×`cesarea` **+0,31** (n=1.728)
- **U0949 ✅ 🟠** demografia_censo × natalidade × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `formal_obra`×`cesarea` **+0,30** (n=1.733)
- **U0950 ✅ 🟡** demografia_censo × natalidade × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `cesarea`×`nbf_share_dom` **-0,34** (n=1.731)
- **U0951 ✅ 🟠⚠** demografia_censo × natalidade × vigilancia_sinan — `ivs_2010`×`cesarea` **-0,36** (n=1.733) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `notif_100k`×`cesarea` **+0,15** (n=1.672)
- **U0952 ✅ 🟠⚠** demografia_censo × sancao_integridade × saneamento_agua — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U0953 ✅ 🟠⚠** demografia_censo × sancao_integridade × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061)
- **U0954 ✅ 🟠⚠** demografia_censo × sancao_integridade × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `formalidade`×`sanc_100k` **+0,16** (n=1.483)
- **U0955 ✅ 🟠⚠** demografia_censo × sancao_integridade × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U0956 ✅ ⚪⚠** demografia_censo × sancao_integridade × vigilancia_sinan — `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `dom_por_cep`×`pago_a_devedor` **+0,17** (n=3.061) — 2/3 pernas sobrevivem ao controle
- **U0957 ✅ 🟡⚠** demografia_censo × saneamento_agua × saude_producao — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298)
- **U0958 ✅ 🟡⚠** demografia_censo × saneamento_agua × trabalho_empresa — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `formalidade`×`snis_gap_agua` **+0,31** (n=5.302)
- **U0959 ✅ 🟠⚠** demografia_censo × saneamento_agua × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U0960 ✅ 🟠⚠** demografia_censo × saneamento_agua × vigilancia_sinan — `idhm_2010`×`snis_gap_agua` **+0,41** (n=5.298) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945)
- **U0961 ✅ 🟡** demografia_censo × saude_producao × trabalho_empresa — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `cno_1000dom`×`cob_priv` **+0,35** (n=5.563)
- **U0962 ✅ 🟡** demografia_censo × saude_producao × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550)
- **U0963 ✅ 🟠⚠** demografia_censo × saude_producao × vigilancia_sinan — `idhm_2010`×`cob_priv` **+0,47** (n=5.565) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `cob_priv`×`notif_100k` **+0,13** (n=4.945)
- **U0964 ✅ 🟡** demografia_censo × trabalho_empresa × transferencia_renda — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553)
- **U0965 ✅ 🟠⚠** demografia_censo × trabalho_empresa × vigilancia_sinan — `idhm_2010`×`cno_1000dom` **+0,43** (n=5.563) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `formal_obra`×`notif_100k` **+0,17** (n=4.948)
- **U0966 ✅ 🟠⚠** demografia_censo × transferencia_renda × vigilancia_sinan — `ivs_2010`×`nbf_share_dom` **+0,51** (n=5.550) · `idhm_2010`×`notif_100k` **+0,19** (n=4.945) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U0967 ✅ ⚪** desmatamento_clima × educacao × fiscal_municipal — `ies_pc`×`desmat_share` **+0,16** (n=719) · `ies_pc`×`capag_ind2` **+0,14** (n=700) — 2/3 pernas sobrevivem ao controle
- **U0968 ✅ 🟠⚠** desmatamento_clima × educacao × fiscalizacao_ambiental — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `ies_pc`×`desmat_share` **+0,16** (n=719) · `ies_pc`×`emb_100k` **+0,12** (n=648)
- **U0969 ✅ 🟠** desmatamento_clima × educacao × fundiario — `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `ies_pc`×`desmat_share` **+0,16** (n=719) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547)
- **U0970 ✅ 🟠** desmatamento_clima × educacao × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `ies_pc`×`desmat_share` **+0,16** (n=719)
- **U0971 ✅ 🟠** desmatamento_clima × educacao × mortalidade — `ies_pc`×`desmat_share` **+0,16** (n=719) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U0972 ✅ 🟠** desmatamento_clima × educacao × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `cesarea`×`desmat_share` **+0,27** (n=1.733) · `ies_pc`×`desmat_share` **+0,16** (n=719)
- **U0973 ✅ ⚪⚠** desmatamento_clima × educacao × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `ies_pc`×`desmat_share` **+0,16** (n=719) — 2/3 pernas sobrevivem ao controle
- **U0974 ✅ 🟠** desmatamento_clima × educacao × saneamento_agua — `ies_pc`×`atlas_individual` **-0,21** (n=719) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `ies_pc`×`desmat_share` **+0,16** (n=719)
- **U0975 ✅ 🟠** desmatamento_clima × educacao × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `ies_pc`×`desmat_share` **+0,16** (n=719) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U0976 ✅ 🟠** desmatamento_clima × educacao × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `ies_pc`×`desmat_share` **+0,16** (n=719)
- **U0977 ✅ 🟠** desmatamento_clima × educacao × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `ies_pc`×`desmat_share` **+0,16** (n=719)
- **U0978 ✅ ⚪⚠** desmatamento_clima × educacao × vigilancia_sinan — `ies_pc`×`desmat_share` **+0,16** (n=719) · `ies_pc`×`notif_100k` **+0,14** (n=713) — 2/3 pernas sobrevivem ao controle
- **U0979 ✅ ⚪⚠** desmatamento_clima × fiscal_municipal × fiscalizacao_ambiental — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 2/3 pernas sobrevivem ao controle
- **U0980 ✅ ⚪** desmatamento_clima × fiscal_municipal × fundiario — `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U0981 ✅ ⚪** desmatamento_clima × fiscal_municipal × mineracao_energia — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) — 1/3 pernas sobrevivem ao controle
- **U0982 ✅ ⚪** desmatamento_clima × fiscal_municipal × mortalidade — `infec_100k`×`desmat_share` **+0,11** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0983 ✅ ⚪** desmatamento_clima × fiscal_municipal × natalidade — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) — 2/3 pernas sobrevivem ao controle
- **U0984 ✅ ⚪⚠** desmatamento_clima × fiscal_municipal × sancao_integridade — `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) — 1/3 pernas sobrevivem ao controle
- **U0985 ✅ ⚪** desmatamento_clima × fiscal_municipal × saneamento_agua — `desmat_share`×`atlas_individual` **-0,17** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U0986 ✅ ⚪** desmatamento_clima × fiscal_municipal × saude_producao — `cob_priv`×`desmat_share` **+0,10** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U0987 ✅ ⚪** desmatamento_clima × fiscal_municipal × trabalho_empresa — `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U0988 ✅ ⚪** desmatamento_clima × fiscal_municipal × transferencia_renda — `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) — 2/3 pernas sobrevivem ao controle
- **U0989 ✅ ⚪** desmatamento_clima × fiscal_municipal × vigilancia_sinan — nenhuma perna sobrevive
- **U0990 ✅ 🟠⚠** desmatamento_clima × fiscalizacao_ambiental × fundiario — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322)
- **U0991 ✅ ⚪⚠** desmatamento_clima × fiscalizacao_ambiental × mineracao_energia — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U0992 ✅ ⚪⚠** desmatamento_clima × fiscalizacao_ambiental × mortalidade — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `infec_100k`×`desmat_share` **+0,11** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0993 ✅ ⚪⚠** desmatamento_clima × fiscalizacao_ambiental × natalidade — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `cesarea`×`desmat_share` **+0,27** (n=1.733) — 2/3 pernas sobrevivem ao controle
- **U0994 ✅ ⚪⚠** desmatamento_clima × fiscalizacao_ambiental × sancao_integridade — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) — 1/3 pernas sobrevivem ao controle
- **U0995 ✅ ⚪⚠** desmatamento_clima × fiscalizacao_ambiental × saneamento_agua — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U0996 ✅ ⚪⚠** desmatamento_clima × fiscalizacao_ambiental × saude_producao — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `cob_priv`×`desmat_share` **+0,10** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U0997 ✅ ⚪⚠** desmatamento_clima × fiscalizacao_ambiental × trabalho_empresa — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) — 2/3 pernas sobrevivem ao controle
- **U0998 ✅ 🟠⚠** desmatamento_clima × fiscalizacao_ambiental × transferencia_renda — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `defeso_share`×`autos_100k` **+0,15** (n=3.213)
- **U0999 ✅ ⚪⚠** desmatamento_clima × fiscalizacao_ambiental × vigilancia_sinan — `emb_100k`×`deter_share_area` **+0,32** (n=1.270) — 1/3 pernas sobrevivem ao controle
- **U1000 ✅ 🟠** desmatamento_clima × fundiario × mineracao_energia — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547)
- **U1001 ✅ 🟠** desmatamento_clima × fundiario × mortalidade — `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U1002 ✅ 🟠** desmatamento_clima × fundiario × natalidade — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547)
- **U1003 ✅ ⚪** desmatamento_clima × fundiario × sancao_integridade — `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) — 1/3 pernas sobrevivem ao controle
- **U1004 ✅ 🟠⚠** desmatamento_clima × fundiario × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547)
- **U1005 ✅ 🟠** desmatamento_clima × fundiario × saude_producao — `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U1006 ✅ 🟠** desmatamento_clima × fundiario × trabalho_empresa — `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1007 ✅ 🟠** desmatamento_clima × fundiario × transferencia_renda — `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547)
- **U1008 ✅ ⚪** desmatamento_clima × fundiario × vigilancia_sinan — `desmat_share`×`cafir_ha_por_imovel` **-0,15** (n=5.547) — 1/3 pernas sobrevivem ao controle
- **U1009 ✅ 🟠** desmatamento_clima × mineracao_energia × mortalidade — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U1010 ✅ 🟠** desmatamento_clima × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `cesarea`×`desmat_share` **+0,27** (n=1.733) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566)
- **U1011 ✅ ⚪** desmatamento_clima × mineracao_energia × sancao_integridade — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) — 1/3 pernas sobrevivem ao controle
- **U1012 ✅ 🟠⚠** desmatamento_clima × mineracao_energia × saneamento_agua — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1013 ✅ 🟠** desmatamento_clima × mineracao_energia × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U1014 ✅ 🟠** desmatamento_clima × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566)
- **U1015 ✅ 🟠** desmatamento_clima × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803)
- **U1016 ✅ ⚪⚠** desmatamento_clima × mineracao_energia × vigilancia_sinan — `desmat_share`×`gd_por_domicilio` **+0,26** (n=5.566) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) — 2/3 pernas sobrevivem ao controle
- **U1017 ✅ 🟠** desmatamento_clima × mortalidade × natalidade — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U1018 ✅ ⚪⚠** desmatamento_clima × mortalidade × sancao_integridade — `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) · `infec_100k`×`desmat_share` **+0,11** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U1019 ✅ 🟠⚠** desmatamento_clima × mortalidade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U1020 ✅ 🟠** desmatamento_clima × mortalidade × saude_producao — `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `infec_100k`×`desmat_share` **+0,11** (n=5.570) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U1021 ✅ 🟠** desmatamento_clima × mortalidade × trabalho_empresa — `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `formal_obra`×`infec_100k` **+0,12** (n=5.568) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U1022 ✅ 🟠** desmatamento_clima × mortalidade × transferencia_renda — `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) · `infec_100k`×`desmat_share` **+0,11** (n=5.570)
- **U1023 ✅ ⚪** desmatamento_clima × mortalidade × vigilancia_sinan — `infec_100k`×`desmat_share` **+0,11** (n=5.570) — 1/3 pernas sobrevivem ao controle
- **U1024 ✅ ⚪⚠** desmatamento_clima × natalidade × sancao_integridade — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `cesarea`×`sanc_100k` **+0,15** (n=878) — 2/3 pernas sobrevivem ao controle
- **U1025 ✅ 🟠⚠** desmatamento_clima × natalidade × saneamento_agua — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570)
- **U1026 ✅ 🟠** desmatamento_clima × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `cesarea`×`desmat_share` **+0,27** (n=1.733) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U1027 ✅ 🟠** desmatamento_clima × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `cesarea`×`desmat_share` **+0,27** (n=1.733) · `formal_obra`×`desmat_share` **+0,27** (n=5.568)
- **U1028 ✅ 🟠** desmatamento_clima × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `cesarea`×`desmat_share` **+0,27** (n=1.733) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803)
- **U1029 ✅ ⚪⚠** desmatamento_clima × natalidade × vigilancia_sinan — `cesarea`×`desmat_share` **+0,27** (n=1.733) · `notif_100k`×`cesarea` **+0,15** (n=1.672) — 2/3 pernas sobrevivem ao controle
- **U1030 ✅ ⚪⚠** desmatamento_clima × sancao_integridade × saneamento_agua — `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1031 ✅ ⚪⚠** desmatamento_clima × sancao_integridade × saude_producao — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `cob_priv`×`desmat_share` **+0,10** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U1032 ✅ ⚪⚠** desmatamento_clima × sancao_integridade × trabalho_empresa — `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1033 ✅ ⚪⚠** desmatamento_clima × sancao_integridade × transferencia_renda — `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) — 2/3 pernas sobrevivem ao controle
- **U1034 ✅ ⚪** desmatamento_clima × sancao_integridade × vigilancia_sinan — nenhuma perna sobrevive
- **U1035 ✅ 🟠⚠** desmatamento_clima × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U1036 ✅ 🟠⚠** desmatamento_clima × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570)
- **U1037 ✅ 🟠** desmatamento_clima × saneamento_agua × transferencia_renda — `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U1038 ✅ ⚪⚠** desmatamento_clima × saneamento_agua × vigilancia_sinan — `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `desmat_share`×`atlas_individual` **-0,17** (n=5.570) — 2/3 pernas sobrevivem ao controle
- **U1039 ✅ 🟠** desmatamento_clima × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U1040 ✅ 🟠** desmatamento_clima × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `cob_priv`×`desmat_share` **+0,10** (n=5.565)
- **U1041 ✅ ⚪⚠** desmatamento_clima × saude_producao × vigilancia_sinan — `cob_priv`×`notif_100k` **+0,13** (n=4.945) · `cob_priv`×`desmat_share` **+0,10** (n=5.565) — 2/3 pernas sobrevivem ao controle
- **U1042 ✅ 🟠** desmatamento_clima × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803)
- **U1043 ✅ ⚪⚠** desmatamento_clima × trabalho_empresa × vigilancia_sinan — `formal_obra`×`desmat_share` **+0,27** (n=5.568) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) — 2/3 pernas sobrevivem ao controle
- **U1044 ✅ ⚪⚠** desmatamento_clima × transferencia_renda × vigilancia_sinan — `defeso_share`×`fogo_dias_sem_chuva_med` **-0,21** (n=3.803) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) — 2/3 pernas sobrevivem ao controle
- **U1045 ✅ 🟠⚠** educacao × fiscal_municipal × fiscalizacao_ambiental — `ies_pc`×`capag_ind2` **+0,14** (n=700) · `ies_pc`×`emb_100k` **+0,12** (n=648) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318)
- **U1046 ✅ 🟠** educacao × fiscal_municipal × fundiario — `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `ies_pc`×`capag_ind2` **+0,14** (n=700)
- **U1047 ✅ ⚪** educacao × fiscal_municipal × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `ies_pc`×`capag_ind2` **+0,14** (n=700) — 2/3 pernas sobrevivem ao controle
- **U1048 ✅ ⚪** educacao × fiscal_municipal × mortalidade — `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `ies_pc`×`capag_ind2` **+0,14** (n=700) — 2/3 pernas sobrevivem ao controle
- **U1049 ✅ 🟠** educacao × fiscal_municipal × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `ies_pc`×`capag_ind2` **+0,14** (n=700) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U1050 ✅ 🟠⚠** educacao × fiscal_municipal × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `ies_pc`×`capag_ind2` **+0,14** (n=700) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479)
- **U1051 ✅ ⚪** educacao × fiscal_municipal × saneamento_agua — `ies_pc`×`atlas_individual` **-0,21** (n=719) · `ies_pc`×`capag_ind2` **+0,14** (n=700) — 2/3 pernas sobrevivem ao controle
- **U1052 ✅ ⚪** educacao × fiscal_municipal × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `ies_pc`×`capag_ind2` **+0,14** (n=700) — 2/3 pernas sobrevivem ao controle
- **U1053 ✅ 🟠** educacao × fiscal_municipal × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `ies_pc`×`capag_ind2` **+0,14** (n=700)
- **U1054 ✅ 🟠** educacao × fiscal_municipal × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) · `ies_pc`×`capag_ind2` **+0,14** (n=700)
- **U1055 ✅ ⚪⚠** educacao × fiscal_municipal × vigilancia_sinan — `ies_pc`×`capag_ind2` **+0,14** (n=700) · `ies_pc`×`notif_100k` **+0,14** (n=713) — 2/3 pernas sobrevivem ao controle
- **U1056 ✅ 🟠⚠** educacao × fiscalizacao_ambiental × fundiario — `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `ies_pc`×`emb_100k` **+0,12** (n=648) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322)
- **U1057 ✅ ⚪⚠** educacao × fiscalizacao_ambiental × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U1058 ✅ ⚪⚠** educacao × fiscalizacao_ambiental × mortalidade — `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U1059 ✅ ⚪⚠** educacao × fiscalizacao_ambiental × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U1060 ✅ ⚪⚠** educacao × fiscalizacao_ambiental × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U1061 ✅ ⚪⚠** educacao × fiscalizacao_ambiental × saneamento_agua — `ies_pc`×`atlas_individual` **-0,21** (n=719) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U1062 ✅ ⚪⚠** educacao × fiscalizacao_ambiental × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U1063 ✅ ⚪⚠** educacao × fiscalizacao_ambiental × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U1064 ✅ 🟠⚠** educacao × fiscalizacao_ambiental × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `ies_pc`×`emb_100k` **+0,12** (n=648)
- **U1065 ✅ ⚪⚠** educacao × fiscalizacao_ambiental × vigilancia_sinan — `ies_pc`×`notif_100k` **+0,14** (n=713) · `ies_pc`×`emb_100k` **+0,12** (n=648) — 2/3 pernas sobrevivem ao controle
- **U1066 ✅ 🟠** educacao × fundiario × mineracao_energia — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543)
- **U1067 ✅ 🟠** educacao × fundiario × mortalidade — `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `pdm_share`×`homic_100k` **+0,15** (n=5.547)
- **U1068 ✅ 🟠** educacao × fundiario × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729)
- **U1069 ✅ ⚪⚠** educacao × fundiario × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) — 2/3 pernas sobrevivem ao controle
- **U1070 ✅ 🟠⚠** educacao × fundiario × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `ies_pc`×`atlas_individual` **-0,21** (n=719)
- **U1071 ✅ 🟠** educacao × fundiario × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U1072 ✅ 🟠** educacao × fundiario × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1073 ✅ 🟠** educacao × fundiario × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541)
- **U1074 ✅ ⚪⚠** educacao × fundiario × vigilancia_sinan — `ideb`×`cafir_ha_por_imovel` **-0,22** (n=5.408) · `ies_pc`×`notif_100k` **+0,14** (n=713) — 2/3 pernas sobrevivem ao controle
- **U1075 ✅ 🟠** educacao × mineracao_energia × mortalidade — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `pdm_share`×`homic_100k` **+0,15** (n=5.547)
- **U1076 ✅ 🟡** educacao × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `pdm_share`×`cesarea` **-0,30** (n=1.731)
- **U1077 ✅ ⚪⚠** educacao × mineracao_energia × sancao_integridade — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `ies_pc`×`sanc_100k` **+0,26** (n=555) — 2/3 pernas sobrevivem ao controle
- **U1078 ✅ 🟠⚠** educacao × mineracao_energia × saneamento_agua — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `ies_pc`×`atlas_individual` **-0,21** (n=719) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1079 ✅ 🟠** educacao × mineracao_energia × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561)
- **U1080 ✅ 🟠** educacao × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `formal_obra`×`pdm_share` **-0,30** (n=5.545)
- **U1081 ✅ 🟠** educacao × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `ideb`×`nbf_share_dom` **-0,29** (n=5.415)
- **U1082 ✅ 🟠⚠** educacao × mineracao_energia × vigilancia_sinan — `pdm_share`×`gd_por_domicilio` **-0,33** (n=5.543) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `ies_pc`×`notif_100k` **+0,14** (n=713)
- **U1083 ✅ 🟠** educacao × mortalidade × natalidade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `pdm_share`×`homic_100k` **+0,15** (n=5.547)
- **U1084 ✅ 🟠⚠** educacao × mortalidade × sancao_integridade — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483)
- **U1085 ✅ 🟠⚠** educacao × mortalidade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `ies_pc`×`atlas_individual` **-0,21** (n=719) · `pdm_share`×`homic_100k` **+0,15** (n=5.547)
- **U1086 ✅ 🟠** educacao × mortalidade × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `pdm_share`×`homic_100k` **+0,15** (n=5.547)
- **U1087 ✅ 🟠** educacao × mortalidade × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U1088 ✅ 🟠** educacao × mortalidade × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U1089 ✅ ⚪⚠** educacao × mortalidade × vigilancia_sinan — `pdm_share`×`homic_100k` **+0,15** (n=5.547) · `ies_pc`×`notif_100k` **+0,14** (n=713) — 2/3 pernas sobrevivem ao controle
- **U1090 ✅ 🟠⚠** educacao × natalidade × sancao_integridade — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `ies_pc`×`sanc_100k` **+0,26** (n=555) · `cesarea`×`sanc_100k` **+0,15** (n=878)
- **U1091 ✅ 🟠⚠** educacao × natalidade × saneamento_agua — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `ies_pc`×`atlas_individual` **-0,21** (n=719) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U1092 ✅ 🟡** educacao × natalidade × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `pdm_share`×`cesarea` **-0,30** (n=1.731)
- **U1093 ✅ 🟠** educacao × natalidade × trabalho_empresa — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `formal_obra`×`cesarea` **+0,30** (n=1.733)
- **U1094 ✅ 🟠** educacao × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `pdm_share`×`cesarea` **-0,30** (n=1.731) · `ideb`×`nbf_share_dom` **-0,29** (n=5.415)
- **U1095 ✅ 🟠⚠** educacao × natalidade × vigilancia_sinan — `pdm_share`×`cesarea` **-0,30** (n=1.731) · `notif_100k`×`cesarea` **+0,15** (n=1.672) · `ies_pc`×`notif_100k` **+0,14** (n=713)
- **U1096 ✅ 🟠⚠** educacao × sancao_integridade × saneamento_agua — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `ies_pc`×`atlas_individual` **-0,21** (n=719) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U1097 ✅ 🟠⚠** educacao × sancao_integridade × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `ies_pc`×`sanc_100k` **+0,26** (n=555) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239)
- **U1098 ✅ 🟠⚠** educacao × sancao_integridade × trabalho_empresa — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `ies_pc`×`sanc_100k` **+0,26** (n=555) · `formalidade`×`sanc_100k` **+0,16** (n=1.483)
- **U1099 ✅ 🟠⚠** educacao × sancao_integridade × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `ies_pc`×`sanc_100k` **+0,26** (n=555) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U1100 ✅ ⚪⚠** educacao × sancao_integridade × vigilancia_sinan — `ies_pc`×`sanc_100k` **+0,26** (n=555) · `ies_pc`×`notif_100k` **+0,14** (n=713) — 2/3 pernas sobrevivem ao controle
- **U1101 ✅ 🟠⚠** educacao × saneamento_agua × saude_producao — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `ies_pc`×`atlas_individual` **-0,21** (n=719)
- **U1102 ✅ 🟠⚠** educacao × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `ies_pc`×`atlas_individual` **-0,21** (n=719)
- **U1103 ✅ 🟠** educacao × saneamento_agua × transferencia_renda — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `ies_pc`×`atlas_individual` **-0,21** (n=719) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U1104 ✅ 🟠⚠** educacao × saneamento_agua × vigilancia_sinan — `ies_pc`×`atlas_individual` **-0,21** (n=719) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `ies_pc`×`notif_100k` **+0,14** (n=713)
- **U1105 ✅ 🟠** educacao × saude_producao × trabalho_empresa — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `formal_obra`×`pdm_share` **-0,30** (n=5.545)
- **U1106 ✅ 🟠** educacao × saude_producao × transferencia_renda — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `ideb`×`nbf_share_dom` **-0,29** (n=5.415)
- **U1107 ✅ 🟠⚠** educacao × saude_producao × vigilancia_sinan — `ies_pc`×`leitos_1000` **+0,37** (n=706) · `ies_pc`×`notif_100k` **+0,14** (n=713) · `cob_priv`×`notif_100k` **+0,13** (n=4.945)
- **U1108 ✅ 🟠** educacao × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `ideb`×`nbf_share_dom` **-0,29** (n=5.415)
- **U1109 ✅ 🟠⚠** educacao × trabalho_empresa × vigilancia_sinan — `formal_obra`×`pdm_share` **-0,30** (n=5.545) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `ies_pc`×`notif_100k` **+0,14** (n=713)
- **U1110 ✅ 🟠⚠** educacao × transferencia_renda × vigilancia_sinan — `ideb`×`nbf_share_dom` **-0,29** (n=5.415) · `ies_pc`×`notif_100k` **+0,14** (n=713) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U1111 ✅ 🟠⚠** fiscal_municipal × fiscalizacao_ambiental × fundiario — `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322)
- **U1112 ✅ ⚪⚠** fiscal_municipal × fiscalizacao_ambiental × mineracao_energia — `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 1/3 pernas sobrevivem ao controle
- **U1113 ✅ ⚪⚠** fiscal_municipal × fiscalizacao_ambiental × mortalidade — `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 1/3 pernas sobrevivem ao controle
- **U1114 ✅ ⚪⚠** fiscal_municipal × fiscalizacao_ambiental × natalidade — `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 2/3 pernas sobrevivem ao controle
- **U1115 ✅ ⚪⚠** fiscal_municipal × fiscalizacao_ambiental × sancao_integridade — `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 2/3 pernas sobrevivem ao controle
- **U1116 ✅ ⚪⚠** fiscal_municipal × fiscalizacao_ambiental × saneamento_agua — `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 1/3 pernas sobrevivem ao controle
- **U1117 ✅ ⚪⚠** fiscal_municipal × fiscalizacao_ambiental × saude_producao — `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 1/3 pernas sobrevivem ao controle
- **U1118 ✅ ⚪⚠** fiscal_municipal × fiscalizacao_ambiental × trabalho_empresa — `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 2/3 pernas sobrevivem ao controle
- **U1119 ✅ 🟠⚠** fiscal_municipal × fiscalizacao_ambiental × transferencia_renda — `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) · `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318)
- **U1120 ✅ ⚪⚠** fiscal_municipal × fiscalizacao_ambiental × vigilancia_sinan — `sic_pessoal_pc`×`autos_100k` **+0,12** (n=4.318) — 1/3 pernas sobrevivem ao controle
- **U1121 ✅ ⚪** fiscal_municipal × fundiario × mineracao_energia — `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) — 2/3 pernas sobrevivem ao controle
- **U1122 ✅ ⚪** fiscal_municipal × fundiario × mortalidade — `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U1123 ✅ 🟠** fiscal_municipal × fundiario × natalidade — `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U1124 ✅ ⚪⚠** fiscal_municipal × fundiario × sancao_integridade — `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) — 2/3 pernas sobrevivem ao controle
- **U1125 ✅ ⚪⚠** fiscal_municipal × fundiario × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) — 2/3 pernas sobrevivem ao controle
- **U1126 ✅ ⚪** fiscal_municipal × fundiario × saude_producao — `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U1127 ✅ 🟠** fiscal_municipal × fundiario × trabalho_empresa — `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1128 ✅ 🟠** fiscal_municipal × fundiario × transferencia_renda — `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014)
- **U1129 ✅ ⚪** fiscal_municipal × fundiario × vigilancia_sinan — `sic_pessoal_pc`×`cafir_ha_por_imovel` **+0,16** (n=5.520) — 1/3 pernas sobrevivem ao controle
- **U1130 ✅ ⚪** fiscal_municipal × mineracao_energia × mortalidade — `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) — 1/3 pernas sobrevivem ao controle
- **U1131 ✅ ⚪** fiscal_municipal × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) — 2/3 pernas sobrevivem ao controle
- **U1132 ✅ ⚪⚠** fiscal_municipal × mineracao_energia × sancao_integridade — `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) — 1/3 pernas sobrevivem ao controle
- **U1133 ✅ ⚪⚠** fiscal_municipal × mineracao_energia × saneamento_agua — `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300) — 1/3 pernas sobrevivem ao controle
- **U1134 ✅ ⚪** fiscal_municipal × mineracao_energia × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) — 1/3 pernas sobrevivem ao controle
- **U1135 ✅ ⚪** fiscal_municipal × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U1136 ✅ ⚪** fiscal_municipal × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) — 2/3 pernas sobrevivem ao controle
- **U1137 ✅ ⚪⚠** fiscal_municipal × mineracao_energia × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) — 1/3 pernas sobrevivem ao controle
- **U1138 ✅ ⚪** fiscal_municipal × mortalidade × natalidade — `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) — 2/3 pernas sobrevivem ao controle
- **U1139 ✅ ⚪⚠** fiscal_municipal × mortalidade × sancao_integridade — `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1140 ✅ ⚪⚠** fiscal_municipal × mortalidade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) — 1/3 pernas sobrevivem ao controle
- **U1141 ✅ ⚪** fiscal_municipal × mortalidade × saude_producao — `cob_priv`×`infec_100k` **+0,19** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U1142 ✅ ⚪** fiscal_municipal × mortalidade × trabalho_empresa — `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `formal_obra`×`infec_100k` **+0,12** (n=5.568) — 2/3 pernas sobrevivem ao controle
- **U1143 ✅ ⚪** fiscal_municipal × mortalidade × transferencia_renda — `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) — 2/3 pernas sobrevivem ao controle
- **U1144 ✅ ⚪** fiscal_municipal × mortalidade × vigilancia_sinan — nenhuma perna sobrevive
- **U1145 ✅ 🟠⚠** fiscal_municipal × natalidade × sancao_integridade — `cesarea`×`sanc_100k` **+0,15** (n=878) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U1146 ✅ ⚪⚠** fiscal_municipal × natalidade × saneamento_agua — `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) — 2/3 pernas sobrevivem ao controle
- **U1147 ✅ ⚪** fiscal_municipal × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) — 2/3 pernas sobrevivem ao controle
- **U1148 ✅ 🟠** fiscal_municipal × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U1149 ✅ 🟠** fiscal_municipal × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721)
- **U1150 ✅ ⚪⚠** fiscal_municipal × natalidade × vigilancia_sinan — `notif_100k`×`cesarea` **+0,15** (n=1.672) · `cesarea`×`sic_pessoal_pc` **-0,13** (n=1.721) — 2/3 pernas sobrevivem ao controle
- **U1151 ✅ ⚪⚠** fiscal_municipal × sancao_integridade × saneamento_agua — `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1152 ✅ ⚪⚠** fiscal_municipal × sancao_integridade × saude_producao — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) — 2/3 pernas sobrevivem ao controle
- **U1153 ✅ 🟠⚠** fiscal_municipal × sancao_integridade × trabalho_empresa — `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479)
- **U1154 ✅ 🟠⚠** fiscal_municipal × sancao_integridade × transferencia_renda — `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) · `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U1155 ✅ ⚪⚠** fiscal_municipal × sancao_integridade × vigilancia_sinan — `sic_pessoal_pc`×`sanc_100k` **+0,13** (n=1.479) — 1/3 pernas sobrevivem ao controle
- **U1156 ✅ ⚪⚠** fiscal_municipal × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) — 1/3 pernas sobrevivem ao controle
- **U1157 ✅ ⚪⚠** fiscal_municipal × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U1158 ✅ ⚪** fiscal_municipal × saneamento_agua × transferencia_renda — `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) — 2/3 pernas sobrevivem ao controle
- **U1159 ✅ ⚪⚠** fiscal_municipal × saneamento_agua × vigilancia_sinan — `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) — 1/3 pernas sobrevivem ao controle
- **U1160 ✅ ⚪** fiscal_municipal × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) — 2/3 pernas sobrevivem ao controle
- **U1161 ✅ ⚪** fiscal_municipal × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) — 2/3 pernas sobrevivem ao controle
- **U1162 ✅ ⚪⚠** fiscal_municipal × saude_producao × vigilancia_sinan — `cob_priv`×`notif_100k` **+0,13** (n=4.945) — 1/3 pernas sobrevivem ao controle
- **U1163 ✅ 🟠** fiscal_municipal × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014)
- **U1164 ✅ ⚪⚠** fiscal_municipal × trabalho_empresa × vigilancia_sinan — `rem_media`×`sic_pessoal_pc` **+0,18** (n=5.542) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) — 2/3 pernas sobrevivem ao controle
- **U1165 ✅ ⚪⚠** fiscal_municipal × transferencia_renda × vigilancia_sinan — `nbf_share_dom`×`capag_ind3` **-0,15** (n=5.014) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) — 2/3 pernas sobrevivem ao controle
- **U1166 ✅ ⚪⚠** fiscalizacao_ambiental × fundiario × mineracao_energia — `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U1167 ✅ ⚪⚠** fiscalizacao_ambiental × fundiario × mortalidade — `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U1168 ✅ ⚪⚠** fiscalizacao_ambiental × fundiario × natalidade — `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U1169 ✅ ⚪⚠** fiscalizacao_ambiental × fundiario × sancao_integridade — `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 1/3 pernas sobrevivem ao controle
- **U1170 ✅ ⚪⚠** fiscalizacao_ambiental × fundiario × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U1171 ✅ ⚪⚠** fiscalizacao_ambiental × fundiario × saude_producao — `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U1172 ✅ ⚪⚠** fiscalizacao_ambiental × fundiario × trabalho_empresa — `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 2/3 pernas sobrevivem ao controle
- **U1173 ✅ 🟠⚠** fiscalizacao_ambiental × fundiario × transferencia_renda — `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322)
- **U1174 ✅ ⚪⚠** fiscalizacao_ambiental × fundiario × vigilancia_sinan — `autos_100k`×`cafir_ha_por_imovel` **+0,10** (n=4.322) — 1/3 pernas sobrevivem ao controle
- **U1175 ✅ ⚪** fiscalizacao_ambiental × mineracao_energia × mortalidade — `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) — 1/3 pernas sobrevivem ao controle
- **U1176 ✅ ⚪** fiscalizacao_ambiental × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) — 1/3 pernas sobrevivem ao controle
- **U1177 ✅ ⚪** fiscalizacao_ambiental × mineracao_energia × sancao_integridade — nenhuma perna sobrevive
- **U1178 ✅ ⚪⚠** fiscalizacao_ambiental × mineracao_energia × saneamento_agua — `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300) — 1/3 pernas sobrevivem ao controle
- **U1179 ✅ ⚪** fiscalizacao_ambiental × mineracao_energia × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) — 1/3 pernas sobrevivem ao controle
- **U1180 ✅ ⚪** fiscalizacao_ambiental × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) — 1/3 pernas sobrevivem ao controle
- **U1181 ✅ ⚪⚠** fiscalizacao_ambiental × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) — 2/3 pernas sobrevivem ao controle
- **U1182 ✅ ⚪⚠** fiscalizacao_ambiental × mineracao_energia × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) — 1/3 pernas sobrevivem ao controle
- **U1183 ✅ ⚪** fiscalizacao_ambiental × mortalidade × natalidade — `homic_100k`×`mae_adol` **+0,20** (n=1.733) — 1/3 pernas sobrevivem ao controle
- **U1184 ✅ ⚪⚠** fiscalizacao_ambiental × mortalidade × sancao_integridade — `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) — 1/3 pernas sobrevivem ao controle
- **U1185 ✅ ⚪⚠** fiscalizacao_ambiental × mortalidade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) — 1/3 pernas sobrevivem ao controle
- **U1186 ✅ ⚪** fiscalizacao_ambiental × mortalidade × saude_producao — `cob_priv`×`infec_100k` **+0,19** (n=5.565) — 1/3 pernas sobrevivem ao controle
- **U1187 ✅ ⚪** fiscalizacao_ambiental × mortalidade × trabalho_empresa — `formal_obra`×`infec_100k` **+0,12** (n=5.568) — 1/3 pernas sobrevivem ao controle
- **U1188 ✅ ⚪⚠** fiscalizacao_ambiental × mortalidade × transferencia_renda — `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) — 2/3 pernas sobrevivem ao controle
- **U1189 ✅ ⚪** fiscalizacao_ambiental × mortalidade × vigilancia_sinan — nenhuma perna sobrevive
- **U1190 ✅ ⚪⚠** fiscalizacao_ambiental × natalidade × sancao_integridade — `cesarea`×`sanc_100k` **+0,15** (n=878) — 1/3 pernas sobrevivem ao controle
- **U1191 ✅ ⚪⚠** fiscalizacao_ambiental × natalidade × saneamento_agua — `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) — 1/3 pernas sobrevivem ao controle
- **U1192 ✅ ⚪** fiscalizacao_ambiental × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) — 1/3 pernas sobrevivem ao controle
- **U1193 ✅ ⚪** fiscalizacao_ambiental × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) — 1/3 pernas sobrevivem ao controle
- **U1194 ✅ ⚪⚠** fiscalizacao_ambiental × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) — 2/3 pernas sobrevivem ao controle
- **U1195 ✅ ⚪⚠** fiscalizacao_ambiental × natalidade × vigilancia_sinan — `notif_100k`×`cesarea` **+0,15** (n=1.672) — 1/3 pernas sobrevivem ao controle
- **U1196 ✅ ⚪⚠** fiscalizacao_ambiental × sancao_integridade × saneamento_agua — `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483) — 1/3 pernas sobrevivem ao controle
- **U1197 ✅ ⚪⚠** fiscalizacao_ambiental × sancao_integridade × saude_producao — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) — 1/3 pernas sobrevivem ao controle
- **U1198 ✅ ⚪⚠** fiscalizacao_ambiental × sancao_integridade × trabalho_empresa — `formalidade`×`sanc_100k` **+0,16** (n=1.483) — 1/3 pernas sobrevivem ao controle
- **U1199 ✅ ⚪⚠** fiscalizacao_ambiental × sancao_integridade × transferencia_renda — `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) — 2/3 pernas sobrevivem ao controle
- **U1200 ✅ ⚪** fiscalizacao_ambiental × sancao_integridade × vigilancia_sinan — nenhuma perna sobrevive
- **U1201 ✅ ⚪⚠** fiscalizacao_ambiental × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) — 1/3 pernas sobrevivem ao controle
- **U1202 ✅ ⚪⚠** fiscalizacao_ambiental × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) — 1/3 pernas sobrevivem ao controle
- **U1203 ✅ ⚪⚠** fiscalizacao_ambiental × saneamento_agua × transferencia_renda — `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) — 2/3 pernas sobrevivem ao controle
- **U1204 ✅ ⚪⚠** fiscalizacao_ambiental × saneamento_agua × vigilancia_sinan — `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) — 1/3 pernas sobrevivem ao controle
- **U1205 ✅ ⚪** fiscalizacao_ambiental × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) — 1/3 pernas sobrevivem ao controle
- **U1206 ✅ ⚪⚠** fiscalizacao_ambiental × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) — 2/3 pernas sobrevivem ao controle
- **U1207 ✅ ⚪⚠** fiscalizacao_ambiental × saude_producao × vigilancia_sinan — `cob_priv`×`notif_100k` **+0,13** (n=4.945) — 1/3 pernas sobrevivem ao controle
- **U1208 ✅ ⚪⚠** fiscalizacao_ambiental × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `defeso_share`×`autos_100k` **+0,15** (n=3.213) — 2/3 pernas sobrevivem ao controle
- **U1209 ✅ ⚪⚠** fiscalizacao_ambiental × trabalho_empresa × vigilancia_sinan — `formal_obra`×`notif_100k` **+0,17** (n=4.948) — 1/3 pernas sobrevivem ao controle
- **U1210 ✅ ⚪⚠** fiscalizacao_ambiental × transferencia_renda × vigilancia_sinan — `defeso_share`×`autos_100k` **+0,15** (n=3.213) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) — 2/3 pernas sobrevivem ao controle
- **U1211 ✅ 🟠** fundiario × mineracao_energia × mortalidade — `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547)
- **U1212 ✅ 🟠** fundiario × mineracao_energia × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543)
- **U1213 ✅ ⚪** fundiario × mineracao_energia × sancao_integridade — `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) — 1/3 pernas sobrevivem ao controle
- **U1214 ✅ 🟠⚠** fundiario × mineracao_energia × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1215 ✅ 🟠** fundiario × mineracao_energia × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U1216 ✅ 🟠** fundiario × mineracao_energia × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1217 ✅ 🟠** fundiario × mineracao_energia × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543)
- **U1218 ✅ ⚪⚠** fundiario × mineracao_energia × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `cafir_ha_por_imovel`×`gd_por_domicilio` **-0,17** (n=5.543) — 2/3 pernas sobrevivem ao controle
- **U1219 ✅ 🟠** fundiario × mortalidade × natalidade — `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547)
- **U1220 ✅ ⚪⚠** fundiario × mortalidade × sancao_integridade — `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1221 ✅ 🟠⚠** fundiario × mortalidade × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547)
- **U1222 ✅ 🟠** fundiario × mortalidade × saude_producao — `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U1223 ✅ 🟠** fundiario × mortalidade × trabalho_empresa — `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `formal_obra`×`infec_100k` **+0,12** (n=5.568) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1224 ✅ 🟠** fundiario × mortalidade × transferencia_renda — `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U1225 ✅ ⚪** fundiario × mortalidade × vigilancia_sinan — `homic_100k`×`cafir_ha_por_imovel` **+0,15** (n=5.547) — 1/3 pernas sobrevivem ao controle
- **U1226 ✅ ⚪⚠** fundiario × natalidade × sancao_integridade — `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `cesarea`×`sanc_100k` **+0,15** (n=878) — 2/3 pernas sobrevivem ao controle
- **U1227 ✅ 🟠⚠** fundiario × natalidade × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U1228 ✅ 🟠** fundiario × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U1229 ✅ 🟠** fundiario × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1230 ✅ 🟠** fundiario × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729)
- **U1231 ✅ ⚪⚠** fundiario × natalidade × vigilancia_sinan — `mae_adol`×`cafir_ha_por_imovel` **+0,20** (n=1.729) · `notif_100k`×`cesarea` **+0,15** (n=1.672) — 2/3 pernas sobrevivem ao controle
- **U1232 ✅ ⚪⚠** fundiario × sancao_integridade × saneamento_agua — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1233 ✅ ⚪⚠** fundiario × sancao_integridade × saude_producao — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U1234 ✅ ⚪⚠** fundiario × sancao_integridade × trabalho_empresa — `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U1235 ✅ ⚪⚠** fundiario × sancao_integridade × transferencia_renda — `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) — 2/3 pernas sobrevivem ao controle
- **U1236 ✅ ⚪** fundiario × sancao_integridade × vigilancia_sinan — nenhuma perna sobrevive
- **U1237 ✅ 🟠⚠** fundiario × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U1238 ✅ 🟠⚠** fundiario × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1239 ✅ 🟠⚠** fundiario × saneamento_agua × transferencia_renda — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U1240 ✅ ⚪⚠** fundiario × saneamento_agua × vigilancia_sinan — `cafir_ha_por_imovel`×`snis_gap_agua` **+0,30** (n=5.279) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) — 2/3 pernas sobrevivem ao controle
- **U1241 ✅ 🟠** fundiario × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1242 ✅ 🟠** fundiario × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547)
- **U1243 ✅ ⚪⚠** fundiario × saude_producao × vigilancia_sinan — `cob_priv`×`notif_100k` **+0,13** (n=4.945) · `saude_1000dom`×`cafir_ha_por_imovel` **-0,13** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U1244 ✅ 🟠** fundiario × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547)
- **U1245 ✅ ⚪⚠** fundiario × trabalho_empresa × vigilancia_sinan — `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `formalidade`×`cafir_ha_por_imovel` **+0,12** (n=5.547) — 2/3 pernas sobrevivem ao controle
- **U1246 ✅ ⚪⚠** fundiario × transferencia_renda × vigilancia_sinan — `pbf_2019_2006`×`cafir_ha_por_imovel` **+0,21** (n=5.541) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) — 2/3 pernas sobrevivem ao controle
- **U1247 ✅ 🟠** mineracao_energia × mortalidade × natalidade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566)
- **U1248 ✅ ⚪⚠** mineracao_energia × mortalidade × sancao_integridade — `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1249 ✅ 🟠⚠** mineracao_energia × mortalidade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1250 ✅ 🟠** mineracao_energia × mortalidade × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566)
- **U1251 ✅ 🟠** mineracao_energia × mortalidade × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U1252 ✅ 🟠** mineracao_energia × mortalidade × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U1253 ✅ ⚪⚠** mineracao_energia × mortalidade × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `transito_100k`×`gd_por_domicilio` **+0,16** (n=5.566) — 2/3 pernas sobrevivem ao controle
- **U1254 ✅ ⚪⚠** mineracao_energia × natalidade × sancao_integridade — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `cesarea`×`sanc_100k` **+0,15** (n=878) — 2/3 pernas sobrevivem ao controle
- **U1255 ✅ 🟠⚠** mineracao_energia × natalidade × saneamento_agua — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1256 ✅ 🟠** mineracao_energia × natalidade × saude_producao — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561)
- **U1257 ✅ 🟠** mineracao_energia × natalidade × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `formal_obra`×`cesarea` **+0,30** (n=1.733)
- **U1258 ✅ 🟡** mineracao_energia × natalidade × transferencia_renda — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551)
- **U1259 ✅ 🟠⚠** mineracao_energia × natalidade × vigilancia_sinan — `cesarea`×`gd_por_domicilio` **+0,42** (n=1.729) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `notif_100k`×`cesarea` **+0,15** (n=1.672)
- **U1260 ✅ ⚪⚠** mineracao_energia × sancao_integridade × saneamento_agua — `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1261 ✅ ⚪⚠** mineracao_energia × sancao_integridade × saude_producao — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) — 2/3 pernas sobrevivem ao controle
- **U1262 ✅ ⚪⚠** mineracao_energia × sancao_integridade × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1263 ✅ ⚪⚠** mineracao_energia × sancao_integridade × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) — 2/3 pernas sobrevivem ao controle
- **U1264 ✅ ⚪⚠** mineracao_energia × sancao_integridade × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) — 1/3 pernas sobrevivem ao controle
- **U1265 ✅ 🟠⚠** mineracao_energia × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1266 ✅ 🟠⚠** mineracao_energia × saneamento_agua × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1267 ✅ 🟠⚠** mineracao_energia × saneamento_agua × transferencia_renda — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1268 ✅ 🟠⚠** mineracao_energia × saneamento_agua × vigilancia_sinan — `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `snis_gap_agua`×`gd_por_domicilio` **+0,15** (n=5.300)
- **U1269 ✅ 🟠** mineracao_energia × saude_producao × trabalho_empresa — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561)
- **U1270 ✅ 🟠** mineracao_energia × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561)
- **U1271 ✅ 🟠⚠** mineracao_energia × saude_producao × vigilancia_sinan — `cob_priv`×`gd_por_domicilio` **+0,30** (n=5.561) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `cob_priv`×`notif_100k` **+0,13** (n=4.945)
- **U1272 ✅ 🟡** mineracao_energia × trabalho_empresa × transferencia_renda — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551)
- **U1273 ✅ 🟠⚠** mineracao_energia × trabalho_empresa × vigilancia_sinan — `cno_1000dom`×`gd_por_domicilio` **+0,48** (n=5.564) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `formal_obra`×`notif_100k` **+0,17** (n=4.948)
- **U1274 ✅ 🟠⚠** mineracao_energia × transferencia_renda × vigilancia_sinan — `nbf_share_dom`×`gd_por_domicilio` **-0,34** (n=5.551) · `notif_100k`×`gd_por_domicilio` **+0,25** (n=4.946) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U1275 ✅ 🟠⚠** mortalidade × natalidade × sancao_integridade — `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `cesarea`×`sanc_100k` **+0,15** (n=878) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483)
- **U1276 ✅ 🟠⚠** mortalidade × natalidade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U1277 ✅ 🟠** mortalidade × natalidade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `cob_priv`×`infec_100k` **+0,19** (n=5.565)
- **U1278 ✅ 🟠** mortalidade × natalidade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U1279 ✅ 🟠** mortalidade × natalidade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U1280 ✅ ⚪⚠** mortalidade × natalidade × vigilancia_sinan — `homic_100k`×`mae_adol` **+0,20** (n=1.733) · `notif_100k`×`cesarea` **+0,15** (n=1.672) — 2/3 pernas sobrevivem ao controle
- **U1281 ✅ 🟠⚠** mortalidade × sancao_integridade × saneamento_agua — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U1282 ✅ 🟠⚠** mortalidade × sancao_integridade × saude_producao — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483)
- **U1283 ✅ 🟠⚠** mortalidade × sancao_integridade × trabalho_empresa — `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `formal_obra`×`infec_100k` **+0,12** (n=5.568) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483)
- **U1284 ✅ 🟠⚠** mortalidade × sancao_integridade × transferencia_renda — `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) · `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483)
- **U1285 ✅ ⚪⚠** mortalidade × sancao_integridade × vigilancia_sinan — `homic_juv_100k`×`sanc_100k` **-0,11** (n=1.483) — 1/3 pernas sobrevivem ao controle
- **U1286 ✅ 🟠⚠** mortalidade × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `cob_priv`×`infec_100k` **+0,19** (n=5.565)
- **U1287 ✅ 🟠⚠** mortalidade × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U1288 ✅ 🟠⚠** mortalidade × saneamento_agua × transferencia_renda — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U1289 ✅ ⚪⚠** mortalidade × saneamento_agua × vigilancia_sinan — `infec_100k`×`snis_gap_agua` **+0,29** (n=5.302) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) — 2/3 pernas sobrevivem ao controle
- **U1290 ✅ 🟠** mortalidade × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U1291 ✅ 🟠** mortalidade × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555)
- **U1292 ✅ ⚪⚠** mortalidade × saude_producao × vigilancia_sinan — `cob_priv`×`infec_100k` **+0,19** (n=5.565) · `cob_priv`×`notif_100k` **+0,13** (n=4.945) — 2/3 pernas sobrevivem ao controle
- **U1293 ✅ 🟠** mortalidade × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) · `formal_obra`×`infec_100k` **+0,12** (n=5.568)
- **U1294 ✅ ⚪⚠** mortalidade × trabalho_empresa × vigilancia_sinan — `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `formal_obra`×`infec_100k` **+0,12** (n=5.568) — 2/3 pernas sobrevivem ao controle
- **U1295 ✅ ⚪⚠** mortalidade × transferencia_renda × vigilancia_sinan — `homic_100k`×`nbf_share_dom` **+0,14** (n=5.555) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) — 2/3 pernas sobrevivem ao controle
- **U1296 ✅ 🟠⚠** natalidade × sancao_integridade × saneamento_agua — `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `cesarea`×`sanc_100k` **+0,15** (n=878) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U1297 ✅ 🟠⚠** natalidade × sancao_integridade × saude_producao — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `cesarea`×`sanc_100k` **+0,15** (n=878)
- **U1298 ✅ 🟠⚠** natalidade × sancao_integridade × trabalho_empresa — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `cesarea`×`sanc_100k` **+0,15** (n=878)
- **U1299 ✅ 🟠⚠** natalidade × sancao_integridade × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `cesarea`×`sanc_100k` **+0,15** (n=878) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U1300 ✅ ⚪⚠** natalidade × sancao_integridade × vigilancia_sinan — `notif_100k`×`cesarea` **+0,15** (n=1.672) · `cesarea`×`sanc_100k` **+0,15** (n=878) — 2/3 pernas sobrevivem ao controle
- **U1301 ✅ 🟠⚠** natalidade × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U1302 ✅ 🟠⚠** natalidade × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `formal_obra`×`cesarea` **+0,30** (n=1.733) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662)
- **U1303 ✅ 🟠⚠** natalidade × saneamento_agua × transferencia_renda — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U1304 ✅ 🟠⚠** natalidade × saneamento_agua × vigilancia_sinan — `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `cesarea`×`snis_gap_agua` **+0,17** (n=1.662) · `notif_100k`×`cesarea` **+0,15** (n=1.672)
- **U1305 ✅ 🟠** natalidade × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `formal_obra`×`cesarea` **+0,30** (n=1.733)
- **U1306 ✅ 🟡** natalidade × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `leitos_1000`×`cesarea` **+0,31** (n=1.728)
- **U1307 ✅ 🟠⚠** natalidade × saude_producao × vigilancia_sinan — `leitos_1000`×`cesarea` **+0,31** (n=1.728) · `notif_100k`×`cesarea` **+0,15** (n=1.672) · `cob_priv`×`notif_100k` **+0,13** (n=4.945)
- **U1308 ✅ 🟠** natalidade × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `formal_obra`×`cesarea` **+0,30** (n=1.733)
- **U1309 ✅ 🟠⚠** natalidade × trabalho_empresa × vigilancia_sinan — `formal_obra`×`cesarea` **+0,30** (n=1.733) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `notif_100k`×`cesarea` **+0,15** (n=1.672)
- **U1310 ✅ 🟠⚠** natalidade × transferencia_renda × vigilancia_sinan — `cesarea`×`nbf_share_dom` **-0,34** (n=1.731) · `notif_100k`×`cesarea` **+0,15** (n=1.672) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U1311 ✅ 🟠⚠** sancao_integridade × saneamento_agua × saude_producao — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U1312 ✅ 🟠⚠** sancao_integridade × saneamento_agua × trabalho_empresa — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U1313 ✅ 🟠⚠** sancao_integridade × saneamento_agua × transferencia_renda — `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483)
- **U1314 ✅ ⚪⚠** sancao_integridade × saneamento_agua × vigilancia_sinan — `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `sanc_100k`×`esgoto_ok` **+0,11** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1315 ✅ 🟠⚠** sancao_integridade × saude_producao × trabalho_empresa — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `formalidade`×`sanc_100k` **+0,16** (n=1.483)
- **U1316 ✅ 🟠⚠** sancao_integridade × saude_producao × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U1317 ✅ ⚪⚠** sancao_integridade × saude_producao × vigilancia_sinan — `leitos_1000`×`sanc_100k` **+0,23** (n=1.239) · `cob_priv`×`notif_100k` **+0,13** (n=4.945) — 2/3 pernas sobrevivem ao controle
- **U1318 ✅ 🟠⚠** sancao_integridade × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) · `defeso_share`×`sanc_100k` **+0,12** (n=1.169)
- **U1319 ✅ ⚪⚠** sancao_integridade × trabalho_empresa × vigilancia_sinan — `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `formalidade`×`sanc_100k` **+0,16** (n=1.483) — 2/3 pernas sobrevivem ao controle
- **U1320 ✅ ⚪⚠** sancao_integridade × transferencia_renda × vigilancia_sinan — `defeso_share`×`sanc_100k` **+0,12** (n=1.169) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936) — 2/3 pernas sobrevivem ao controle
- **U1321 ✅ 🟡⚠** saneamento_agua × saude_producao × trabalho_empresa — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `formalidade`×`snis_gap_agua` **+0,31** (n=5.302)
- **U1322 ✅ 🟠⚠** saneamento_agua × saude_producao × transferencia_renda — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U1323 ✅ 🟠⚠** saneamento_agua × saude_producao × vigilancia_sinan — `cob_priv`×`snis_gap_agua` **+0,36** (n=5.298) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `cob_priv`×`notif_100k` **+0,13** (n=4.945)
- **U1324 ✅ 🟠⚠** saneamento_agua × trabalho_empresa × transferencia_renda — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555)
- **U1325 ✅ 🟠⚠** saneamento_agua × trabalho_empresa × vigilancia_sinan — `formalidade`×`snis_gap_agua` **+0,31** (n=5.302) · `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `formal_obra`×`notif_100k` **+0,17** (n=4.948)
- **U1326 ✅ 🟠⚠** saneamento_agua × transferencia_renda × vigilancia_sinan — `notif_100k`×`snis_gap_agua` **+0,19** (n=4.729) · `nbf_share_dom`×`atlas_sem_nada` **+0,16** (n=5.555) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U1327 ✅ 🟡** saude_producao × trabalho_empresa × transferencia_renda — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553)
- **U1328 ✅ 🟠⚠** saude_producao × trabalho_empresa × vigilancia_sinan — `cno_1000dom`×`cob_priv` **+0,35** (n=5.563) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `cob_priv`×`notif_100k` **+0,13** (n=4.945)
- **U1329 ✅ 🟠⚠** saude_producao × transferencia_renda × vigilancia_sinan — `cob_priv`×`nbf_share_dom` **-0,36** (n=5.550) · `cob_priv`×`notif_100k` **+0,13** (n=4.945) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
- **U1330 ✅ 🟠⚠** trabalho_empresa × transferencia_renda × vigilancia_sinan — `cno_1000dom`×`nbf_share_dom` **-0,34** (n=5.553) · `formal_obra`×`notif_100k` **+0,17** (n=4.948) · `notif_100k`×`nbf_share_dom` **-0,11** (n=4.936)
