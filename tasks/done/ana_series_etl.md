# done/ana_series_etl.md — ETL das séries da ANA + análise de tendência

Continuação de [`done/ana_series_historicas.md`](ana_series_historicas.md), que trouxe e
extraiu o zip. Aqui o zip virou tabela e a tabela virou a análise dos "rios morrendo".

Concluído em 2026-08-09.

## O que ficou pronto

### 1. ETL — `scripts/scrap/ana_series_historicas.py`

Roda no beelink (os CSVs já estão lá; puxar 1,4 GB pela rede para devolver seria desperdício).
Escreve em `~/rodado/br_ana_telemetria/`, particionado por bacia (2 primeiros dígitos do
código), zstd:

| Tabela | Linhas | Estações |
|---|---|---|
| `series_vazao_mensal` | 1.331.690 | 3.954 |
| `series_vazao_diaria` | 36.137.783 | 3.954 |
| `series_cota_mensal` | 1.729.199 | 7.197 |
| `series_cota_diaria` | 47.788.422 | 7.197 |
| `estacoes_inventario_2023` | 37.782 | — |

Cobertura medida: **1901-01 a 2023-09**. Span médio por estação 30,5 anos, mediana 24;
2.250 estações passam de 20 anos, 1.714 de 30, 900 de 50, 361 de 70.

Conferido contra a linha crua do CSV: estação 58770000 em 02/1934 sai com `media=112.196`,
`maxima=181.448`, `minima=95.634003` e `nivel_consistencia=2`. Vazão específica com mediana
de 15,4 L/s/km² e 99% dentro da banda 0,05–70 que o `processa.py` do todos-rios-brasil aceita.

**O parsing é mais simples do que a doc da ANA sugere.** Medido nos arquivos: ASCII puro,
LF (não CRLF), exatamente 77 campos, e `Data` sempre `MM/YYYY` — o `Descricao_Arquivos_Dados.csv`
afirma `MMM/YY`, e está errado. Só o inventário é diferente: UTF-8 com BOM e CRLF.

Duas armadilhas que valem registrar:

- `pl.read_csv` não aceita lista de caminhos nesta versão do polars; só `pl.scan_csv` aceita.
- Os status diários 4/5/6 (régua seca, rio cortado, rio seco) vêm sem valor. O ETL grava
  `valor = 0` nesses casos: é dado, não lacuna, e é o único registro de rio que parou de correr.
  São **613.210 dias** assim, em **623 estações**.

### 2. Sobreposição com `ana_mensal_unifica.py`

Aquele script já fazia o recorte mensal e ficou **superado** — o novo cobre mensal + diário +
inventário. Vale saber por que não dá para só manter o antigo: ele ordena
`["codigo","mes","nivel_consistencia"]` ascendente e fica com o primeiro, o que preserva o
**bruto (1)** e descarta o **consistido (2)** — o inverso do pretendido. O novo ordena
descendente. Os dois não colidiram em disco porque escrevem em caminhos diferentes
(`series_vazoes_mensal` no plural contra `series_vazao_mensal`); decidir se remove o antigo.

### 3. Análise — no `todos-rios-brasil`

- `pipeline/analisa_tendencia.py` — Mann-Kendall (com correção de empates e de continuidade) e
  inclinação de Theil-Sen sobre médias anuais, em numpy puro, porque o beelink não tem scipy.
  Correção de Benjamini-Hochberg para testes múltiplos. Validado contra
  `scipy.stats.kendalltau` (bate na 2ª casa significativa, inclusive na série com empates) e
  contra séries sintéticas de inclinação conhecida.
- `pipeline/prepara_paineis.py` — dias de rio seco, deslocamento do mês de cheia por média
  circular, Q7,10 em duas janelas, e tamanho da rede por ano.
- `pipeline/template_series.html` + `monta_series.py` — a página, 770 KB autocontidos.

**Resultado:** 1.375 estações elegíveis (≥20 anos, último ano ≥2015); no ranking padrão
(≥30 anos, fora de estrutura hidráulica, significativo pós-FDR) sobram **404 — 303 caindo e
101 subindo**.

Três contaminações que precisaram de filtro e que voltam a morder quem refizer isto:

1. **Estação em barragem/açude/canal** (122 das 1.375). A "tendência" ali é a data da obra. A
   maior alta do país sem o filtro era o Uruguai no barramento da UHE Itá, +70%/década.
2. **Série curta infla o extremo**: correlação −0,33 entre |%/década| e número de anos; os 50
   extremos tinham mediana de 26 anos contra 47 do conjunto.
3. **Ordenar por magnitude ignora significância**: só 30 dos 50 extremos sobreviviam ao FDR.

### 4. Achado colateral sobre a fonte

A consistência da ANA desabou: **1.931 estações consistidas em 2014, 707 em 2015, e uma em
2022**. Dado bruto continua entrando; quase ninguém mais o confere. A rede reportando também
caiu (2.067 em 2014 → 1.275 em 2022), mas essa parte é confundida com defasagem de publicação,
já que o arquivo é retrato de ago/2023 — a queda da consistência não tem essa desculpa.

## O que ficou de fora

- [ ] **Gap 2023-08 → hoje.** Adiado a pedido; a análise será refeita quando existir.
      Sondado nesta rodada: o SOAP **continua no ar** apesar do desligamento anunciado para
      30/06/2026, e **recua até 1936** (testado em 58770000 com `dataInicio=01/01/1930`) — o
      corte em 1995 do `baixa_vazao.py` é escolha, não limite da fonte. Mas a base está
      defasada: naquela estação o dado mais recente é 2024-03. Reaproveitar
      `scripts/scrap/ana_soap_worker.py`, que já tem checkpoint resumível.
- [ ] **Chuva pluviométrica.** Bloqueado em `sudo apt install mdbtools` no beelink, que pede
      senha interativa. São 5.525 zips de MDB, 1,1 GB. Sem isso não sai a pergunta que mais
      importa: se a vazão caiu mas a chuva não, a causa é consumo e uso do solo, não clima.
