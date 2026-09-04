# Automatizar a atualização das fontes raspadas — plano

> Aberto em 2026-09-04, a pedido, depois de uma checagem manual de
> "upgradability" numa amostra de 6 datasets (`br_bcb_sgs`,
> `br_anac_dadosabertos`, `br_mjsp_sinesp`, `br_cvm_fundos`,
> `br_tesouro_capag`, `br_anvisa_cmed` — ver `docs/context/dataset_freshness.yaml`
> e a entrada correspondente em `tasks/README.md`).

## O que já existe (não é preciso criar)

- **`source_url` no `catalog.parquet`** — já existe desde a criação do
  catálogo (`scripts/build_metadata_catalog.py`), preenchido pra maioria dos
  datasets raspados independentemente (87 tabelas ainda sem, ver
  `docs/housekeeping.md` item 6.2 — pré-existente, não é o foco deste plano).
- **`docs/context/dataset_freshness.yaml`** — curado, mapeia
  `dataset.tabela → expressão SQL` pra achar a data mais recente **dentro do
  nosso mirror**. Só 6 entradas por enquanto.
- **Um `scripts/scrap/<nome>.py` por fonte independente** — a lógica de
  busca já existe pra praticamente todo dataset raspado (confirmado hoje:
  `bcb_sgs.py`, `fipe_veiculos.py`, `anac_dadosabertos.py`, `mjsp_sinesp.py`,
  `cvm_fundos.py`, `anvisa_cmed.py`, `tesouro_capag.py` — todos rodáveis de
  novo, não precisam ser reescritos).

## O que falta — a peça que falta é a automação, não o dado

`source_url` sozinho não automatiza nada: é só um link pra fonte, não diz
**o que está lá agora** nem **qual script rodar** se estiver desatualizado.
Faltam três coisas distintas:

1. **Checar o frescor da fonte viva**, não só do nosso mirror.
   `dataset_freshness.yaml` hoje só olha pra dentro (`max()` na nossa
   tabela) — precisa de um segundo mecanismo que pergunte à fonte "qual é o
   dado mais recente que você tem?" (ex.: `api.bcb.gov.br/.../ultimos/1`,
   listagem de diretório do ANAC, `Last-Modified` do `cad_fi.csv` da CVM).
   Isso é específico por fonte, do mesmo jeito que o scraper é.
2. **Um mapa dataset → script scraper**, pra saber o que rodar quando um
   gap for confirmado.
3. **Um orquestrador** que junta os dois pontos acima: pra cada entrada
   curada, compara frescor da fonte vs. frescor do mirror e decide o que
   fazer.

## Por que isto não deve virar automação sem supervisão de cara

A sessão de 2026-09-04 que motivou este plano encontrou, na prática, em
menos de um dia:

- Um proxy que funcionava pro PNCP (`_staging/pncp/duplo.sh`) morreu sem
  aviso entre sessões.
- Um pool de 5 proxies BR novos, achado no mesmo dia, teve 2 de 5 caindo e
  voltando em minutos — instabilidade real de proxy gratuito, não exceção.
- Um bug de terminador de linha (`\r\n` do CSV gerado em Python) corrompeu
  **toda** URL de download silenciosamente — nenhum erro claro, só "toda
  tentativa falha", em qualquer proxy, até alguém rodar `bash -x` e olhar
  byte a byte.
- Uma checagem manual de frescor do BCB SGS deu um resultado **errado**
  (`max()` de string em vez de data) que só foi pego porque a rotina
  `_probe_freshness_dates` comparou com o resultado certo depois.

Nenhum desses seria pego por um cron job silencioso. Um scraper que roda
sozinho e escreve parquet errado — sem quebrar, sem logar nada estranho — é
pior que não rodar: o dado errado parece bom até alguém medir contra um
número conhecido (a mesma lição de `feedback_check_metrics_before_hand_rolling`
na memória do projeto). **Automação aqui significa automatizar a checagem,
não a correção.**

## Proposta em duas fases

### Fase 1 — checar, nunca corrigir sozinho (baixo risco, vale fazer)

Um novo arquivo curado, `docs/context/source_freshness_checks.yaml`, irmão
de `dataset_freshness.yaml`, mapeando cada entrada já curada pra uma forma
de perguntar à fonte "qual é seu dado mais recente":

```yaml
br_bcb_sgs.series:
  check: http_json          # tipo de checagem — cada tipo tem uma função em scripts/checa_frescor_fontes.py
  url: "https://api.bcb.gov.br/dados/serie/bcdata.sgs.1/dados/ultimos/1?formato=json"
  json_path: "[0].data"     # DD/MM/YYYY
br_anac_dadosabertos.voos:
  check: dir_listing        # lista o diretório mensal mais recente com arquivo de verdade dentro
  url: "https://sistemas.anac.gov.br/dadosabertos/Voos%20e%20opera%C3%A7%C3%B5es%20a%C3%A9reas/Voo%20Regular%20Ativo%20%28VRA%29/{ano}/"
br_cvm_fundos.fundos:
  check: http_last_modified
  url: "https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv"
br_mjsp_sinesp.ocorrencias:
  check: dead               # fonte confirmada morta (dados.mj.gov.br, NXDOMAIN) — não checar, só documentar
```

`scripts/checa_frescor_fontes.py` (novo): pra cada entrada com `check` != `dead`,
resolve o frescor da fonte, compara com `last_date` do `catalog.parquet`
(já existe), e **só imprime um relatório** — nada de rodar scraper, nada de
gravar parquet. Saída pensada pra virar uma tabela em `tasks/`, do mesmo
jeito que `tasks/README.md § "Proxy BR encontrado"` documentou o achado de
hoje.

Roda sob demanda (`python3 scripts/checa_frescor_fontes.py`), não em cron,
pelo menos no início — decisão de quando automatizar o disparo é da Fase 2.

### Fase 2 — automação de verdade (mais adiante, precisa de mais confiança)

Só depois que a Fase 1 rodar tempo suficiente pra confiar no sinal (sem
falso-positivo tipo o do BCB SGS desta sessão):

- Um `scripts/scrap/<nome>.py → dataset.tabela` explícito por entrada
  curada (hoje é 1:1 óbvio pela maioria dos nomes, mas nem sempre — ex.
  `br_transferegov_siconv` tem 62 tabelas de um scraper só).
  Extensão natural do YAML: `scraper: scripts/scrap/bcb_sgs.py`.
- Um gate de segurança antes de qualquer re-scrape automático: rodar o
  scraper, mas nunca sobrescrever a tabela existente direto — gravar num
  `_staging/` e só promover depois de uma contagem sanidade (o mesmo padrão
  manual que a sessão de 2026-09-04 já seguiu à mão pra todo dataset novo:
  contagem bate com o esperado, verificado via `read_parquet()` readonly
  antes de criar view).
- Alerta, não auto-aplicação: mesmo com o gate, a recomendação é o
  orquestrador **abrir um item em `tasks/`** com o que mudaria, não aplicar
  sozinho — pelo menos até o histórico de Fase 1 mostrar que os falsos
  positivos pararam de acontecer.

## Ordem recomendada

1. `docs/context/source_freshness_checks.yaml` com as 5 entradas já
   investigadas hoje (a 6ª, SINESP, marca `check: dead`).
2. `scripts/checa_frescor_fontes.py` — só lê e reporta.
3. Rodar contra o resto dos 77 datasets raspados independentemente, um lote
   por vez (a mesma amostragem que motivou este plano — ver
   `tasks/README.md`), curando `source_freshness_checks.yaml` conforme
   cada fonte é investigada manualmente uma vez.
4. Só considerar Fase 2 depois disso ter rodado sem falso-positivo por um
   tempo — sem prazo fixo, é uma decisão de confiança, não de calendário.
