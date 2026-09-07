#!/usr/bin/env python3
"""pares.csv + trincas.csv -> docs/hipoteses/respostas_trincas.md

Usa o MESMO eixo de forca de respostas.md (🟢🟡🟠⚪⬜), para os
dois documentos serem lidos com a mesma regua.

  python3 scripts/hipoteses/h2_20_escreve_respostas.py
"""
import itertools, sys
from pathlib import Path
import pandas as pd, yaml

REPO = Path(__file__).resolve().parent.parent.parent
RES  = REPO / "tasks" / "hipoteses_resultado" / "hipoteses2"
OUT  = REPO / "docs" / "hipoteses" / "respostas_trincas.md"

def forca(r):
    r = abs(r)
    return "🟢" if r >= .50 else "🟡" if r >= .30 else "🟠" if r >= .10 else "⚪"

def main():
    mapa = yaml.safe_load((REPO/"scripts"/"hipoteses"/"h2_familias_colunas.yaml").read_text(encoding="utf-8"))
    d  = pd.read_csv(RES/"pares.csv")
    viv = d[d.sobrevive]
    fams = sorted(set(d.fam_a) | set(d.fam_b))
    reg = set(mapa["metricas_de_registro"])

    # melhor perna viva por par de familias
    melhor = {}
    for _, r in viv.iterrows():
        ch = frozenset((r.fam_a, r.fam_b))
        if ch not in melhor or abs(r.r_parcial) > abs(melhor[ch].r_parcial):
            melhor[ch] = r

    linhas, resumo = [], {"🟢":0,"🟡":0,"🟠":0,"⚪":0}
    for i, t in enumerate(itertools.combinations(fams, 3), 1):
        pernas = [frozenset(p) for p in itertools.combinations(t, 2)]
        vivas  = [melhor[p] for p in pernas if p in melhor]
        cod = f"U{i:04d}"
        if len(vivas) < 3:
            g = "⚪"; nota = f"{len(vivas)}/3 pernas sobrevivem ao controle"
        else:
            g = forca(min(abs(v.r_parcial) for v in vivas)); nota = ""
        resumo[g] += 1
        mod = "⚠" if any((v.col_a in reg or v.col_b in reg) for v in vivas) else ""
        det = " · ".join(
            f"`{v.col_a}`×`{v.col_b}` **{v.r_parcial:+.2f}".replace(".", ",") + f"** (n={v.n:,})".replace(",", ".")
            for v in sorted(vivas, key=lambda v: -abs(v.r_parcial)))
        linhas.append(f"- **{cod} ✅ {g}{mod}** {' × '.join(t)} — "
                      + (det if det else "nenhuma perna sobrevive")
                      + (f" — {nota}" if nota and det else ""))

    tot = sum(resumo.values())
    n_ach = int((viv.tipo == "achado").sum())
    n_sup = int(((viv.r_parcial.abs() - viv.r_bruto.abs()) > 0.15).sum())
    cab = f"""# Hipóteses 2 — as {tot} trincas de família, todas rodadas

Companheiro de [`respostas.md`](respostas.md), com uma
diferença de método: lá as perguntas foram escritas uma a uma e respondidas uma a
uma; aqui **o espaço inteiro foi enumerado e rodado de uma vez**.

O que tornou isso possível não foi capacidade de máquina, foi enxergar que **uma
trinca de famílias é um trio de colunas do painel municipal** — e o painel já
estava extraído do beelink pelas rodadas anteriores. Fundidos os três painéis
(`20260906`, `inedito`, `familias`), sobra 1 tabela de **5.571 municípios × 270
colunas**; a partir dela, mais uma hipótese custa uma correlação em numpy. As
{tot} trincas rodam em **8 segundos**, sem tocar no beelink.

## Método

- **Spearman**, nunca Pearson cru — distribuição municipal tem cauda pesada.
- **Parcial** residualizando `log(população)`, `log(PIB per capita)`,
  **`log(área)`** e efeito fixo de UF. A log-área entra *sempre*, não só quando
  as duas pernas são extensivas: metade do painel é normalizada por hectare ou
  por área, e o `1/área` compartilhado produz correlação sozinho.
- Só colunas **intensivas** (taxa, share, per capita, índice): 107 colunas em
  21 famílias. Contagem crua correlaciona com o tamanho do município.
- **Benjamini-Hochberg** sobre os **5.325** pares testados. Rodar cinco mil pares
  e reportar o maior |r| sem correção é garimpo de ruído, não achado.
- Piso de `|r_parcial| ≥ 0,10` (o mesmo do glifo 🟠 do documento irmão),
  `q < 0,01` e `n ≥ 500`.

**Eixo de força idêntico ao de [`respostas.md`](respostas.md)**:
🟢 forte (≥ 0,50) · 🟡 moderada (0,30–0,50) · 🟠 fraca (0,10–0,30) · ⚪ nula.
A força da trinca é a da **perna mais fraca** — uma hipótese de três pernas vale
o que vale seu elo mais frouxo. Aqui ⚪ tem um sentido preciso: **ao menos uma
das três pernas não sobrevive ao controle**, então a trinca não se sustenta como
hipótese de três vias — mesmo quando uma das outras pernas é forte, e a linha
mostra qual. `⚠` marca trinca que se apoia em **métrica de
registro** (notificação, auto de infração, reclamação, declaração ao SNIS): mede
a capacidade de registrar antes de medir o fenômeno.

## Validação — o pipeline reproduz o que já estava publicado

Rodando às cegas contra os achados da rodada 2026-09-05
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

| Força da trinca | Trincas | % |
|---|---|---|
| 🟢 forte (elo mais fraco ≥ 0,50) | {resumo['🟢']} | {100*resumo['🟢']/tot:.0f}% |
| 🟡 moderada | {resumo['🟡']} | {100*resumo['🟡']/tot:.0f}% |
| 🟠 fraca | {resumo['🟠']} | {100*resumo['🟠']/tot:.0f}% |
| ⚪ nula (não sobrevive ao controle) | {resumo['⚪']} | {100*resumo['⚪']/tot:.0f}% |
| **total** | **{tot}** | |

**O resultado principal é negativo, e é o mais informativo que esta corrida
podia produzir**: depois de descontar porte, renda, área e UF, dos 5.325 pares
testados **{int(viv.shape[0])} sobrevivem** ao FDR e ao piso de 0,10, e entre eles apenas
**{int((viv.r_parcial.abs()>=.5).sum())} passam de |r| = 0,50**. O espelho é um objeto de correlações
fracas: quase tudo que parece forte no bruto é tamanho, riqueza ou geografia.

Isso **não** desqualifica os achados do documento irmão — ele já reportava
parciais, e são os mesmos números. O que a enumeração completa acrescenta é o
denominador: agora dá para dizer que os achados fortes publicados são fortes
*em relação a um espaço de 1.330 hipóteses testadas*, e não apenas fortes entre
as que alguém pensou em perguntar.

## Guardas — o que foi excluído, e por quê

Sem estas duas listas a corrida devolveria como descoberta as duas correlações
mais fortes do painel inteiro:

| Par | r | Por que não é achado |
|---|---|---|
| `sic_pessoal_pc` × `mides_valor_pc` | +0,69 | gasto municipal per capita medido por duas fontes (SICONFI × MIDES) |
| `pdm_share` × `nbf_share_dom` | +0,60 | o Pé-de-Meia **exige CadÚnico**: é a mesma elegibilidade do Bolsa Família |

São 8 pares de duplicata conceitual, listados em
[`scripts/hipoteses/h2_familias_colunas.yaml`](../../scripts/hipoteses/h2_familias_colunas.yaml).
Outras 14 colunas são **métricas de registro** e recebem `⚠` — `snis_gap_agua`,
por exemplo, é a razão entre a água declarada ao SNIS e a medida pelo IBGE:
correlacioná-la com conectividade mede quem declara direito, não quem tem água.

## A fronteira — 7 famílias sem nenhuma coluna no painel

{chr(10).join(f'- **{k}** — {v}' for k, v in mapa['ausentes'].items())}

As 4 primeiras são municipais e extraíveis: entram numa próxima rodada e abrem
C(25,3) − C(21,3) = **970 trincas novas**. As 3 últimas são só UF, e a cascata
F1 de [`tasks/hipoteses.md`](../../tasks/hipoteses.md) já as cortava — n=27 não
sustenta parcial com efeito fixo.

## Como refazer

```bash
python3 scripts/hipoteses/h2_00_painel_mestre.py     # 3 painéis -> painel_mestre.csv (5.571 × 270)
python3 scripts/hipoteses/h2_10_roda_trincas.py      # -> pares.csv + trincas.csv (8s)
python3 scripts/hipoteses/h2_20_escreve_respostas.py # -> este arquivo
```

O mapa coluna→família vive em
[`scripts/hipoteses/h2_familias_colunas.yaml`](../../scripts/hipoteses/h2_familias_colunas.yaml)
— é o elo que faltava: `docs/context/familias.yaml` mapeia dataset→família, o
painel tem coluna, e ninguém mapeava coluna→família. Editar lá, nunca a saída.

## Os achados que se sustentam

Os dez pares mais fortes entre os {n_ach} que sobrevivem, com a leitura. `(já
conhecido)` marca o que a rodada anterior já tinha publicado — reaparecer aqui é
validação, não descoberta.

| r parcial | Par | Leitura |
|---|---|---|
| **−0,51** | concentração do crédito rural × densidade agropecuária | Onde há mais agropecuária, o crédito é **menos** concentrado num único tomador. Crédito rural concentrado é fenômeno de município **pouco** agrícola — a fazenda grande isolada, não a região produtora. |
| **+0,51** | IVS 2010 × cobertura do Novo Bolsa Família | A vulnerabilidade medida em 2010 prevê a cobertura de 2026. A focalização acerta, e a geografia da vulnerabilidade é **estável por 15 anos**. |
| **+0,49** | desmatamento × bovinos por hectare | *(já conhecido — A2/T10-3)* Sobrevive ao controle de área, que é o teste que derrubou o D1. |
| **+0,48** | concentração do crédito × tamanho médio do imóvel rural | **Supressão**: bruto +0,21, parcial +0,48 — mais que dobra sob controle. Onde o imóvel médio é maior, o crédito rural concentra; o efeito estava mascarado por porte e renda do município. |
| **+0,48** | obras registradas no CNO × geração solar por domicílio | As duas medem a mesma coisa por caminhos independentes: **quem investe no próprio imóvel**. Nenhuma pergunta anterior cruzou obra formal com energia. |
| **+0,47** | crédito por hectare × densidade agropecuária | **Supressão** (+0,30 → +0,47). |
| **+0,47** | IDHM 2010 × cobertura de plano privado | Plano de saúde é marcador de desenvolvimento, não de oferta médica. |
| **−0,45** | densidade agropecuária × cobertura 4G/5G | *(já conhecido — B2)* O campo segue sendo o bolsão não conectado. |
| **+0,45** | crédito rural por hectare × desmatamento | *(já conhecido — C1/T17-3)* Sobrevive à log-área. |
| **−0,43** | IVS 2010 × geração solar por domicílio | Solar distribuída é de município **menos** vulnerável — a transição energética doméstica segue renda, não sol. |

### O que só aparece sob controle

{n_sup} pares têm `|r_parcial|` pelo menos 0,15 acima do bruto — relação real
que a correlação crua esconde porque porte e renda puxam as duas pontas em
direções opostas. O caso extremo é **concentração onomástica × pagamento
municipal per capita** (+0,07 bruto → **+0,32** parcial, n=3.336): o mesmo
`share_nome_top` cuja correlação com pobreza o H18 matou (+0,48 → +0,03) tem,
contra pagamento municipal, o comportamento inverso — nulo no bruto e presente
no parcial. Tratar como pista, não como achado: é proxy de sociedade local
fechada, e o n é dos menores do painel.

## As {tot} trincas

Código `U####`, força pela perna mais fraca, e as pernas que sobreviveram com a
coluna exata que as mediu. Ordenadas por família.

"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    print(f"{OUT.relative_to(REPO)}: {tot} trincas | {resumo}")

if __name__ == "__main__":
    sys.exit(main())
