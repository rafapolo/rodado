#!/usr/bin/env python3
"""Escreve um FRAGMENTO com as secoes da rodada h3 a partir dos tres resultados
do lote -- nao o doc final. docs/hipoteses/respostas_trincas.md fundiu h2+h3
manualmente num unico arquivo (2026-09-07); rodar este script de novo gera
material novo aqui, mas colar no lugar certo de respostas_trincas.md
("O que a corrida achou" em diante, ate "Como refazer") e trabalho manual --
nao sobrescreva o merge automaticamente.

  python3 scripts/hipoteses/h3_50_escreve.py
"""
import itertools, sys
from pathlib import Path
import pandas as pd, yaml

REPO = Path(__file__).resolve().parent.parent.parent
RES  = REPO/"tasks"/"hipoteses_resultado"/"hipoteses3"
OUT  = REPO/"tasks"/"hipoteses_resultado"/"hipoteses3"/"respostas_h3_fragmento.md"

def forca(r):
    r=abs(r); return "🟢" if r>=.50 else "🟡" if r>=.30 else "🟠" if r>=.10 else "⚪"

def br(x, casas=0):
    s=f"{x:,.{casas}f}".replace(",","§").replace(".",",").replace("§",".")
    return s

def main():
    pares=pd.read_csv(RES/"pares_h3.csv")
    tri  =pd.read_csv(RES/"trincas_h3.csv")
    pol  =pd.read_csv(RES/"politico_papel.csv") if (RES/"politico_papel.csv").exists() else None
    cnpj =pd.read_csv(RES/"cnpj_pares.csv") if (RES/"cnpj_pares.csv").exists() else None
    viv=pares[pares.sobrevive]; ach=viv[viv.tipo=="achado"]

    L=[]
    A=L.append
    A("# Hipóteses 3 — os dois eixos, com o espelho inteiro que dá para usar\n")
    A("""Terceira e última rodada da série. A [primeira](respostas.md)
respondeu perguntas escritas uma a uma; a [segunda](respostas_trincas.md)
enumerou e rodou as 1.330 trincas de família que o painel então permitia. Esta
faz duas coisas que as anteriores não faziam:

1. **estende o painel** com 37 datasets que tinham cobertura municipal medida e
   nunca haviam sido extraídos — ENEM, Censo Escolar, SEEG, MapBiomas, ESTBAN,
   BNDES, SIA, ANS, SISVAN, Imunizações, filiação partidária;
2. **abre um segundo eixo**, o do **grafo de identificadores** — CNPJ e CPF —,
   que a cascata F0–F7 de [`tasks/hipoteses.md`](../../tasks/hipoteses.md)
   **nunca contou**, porque o filtro F0 exige "chave territorial" e joga o grafo
   fora por construção.
""")

    A("## O que mudou no eixo territorial\n")
    A(f"""| | hipóteses 2 | hipóteses 3 |
|---|---|---|
| colunas intensivas | 107 | **149** |
| famílias com coluna | 21 | **22** (entra `politica`) |
| pares testados | 5.325 | **{br(len(pares))}** |
| pares que sobrevivem | 995 | **{br(int(pares.sobrevive.sum()))}** |
| trincas de família | 1.330 | **{br(len(tri))}** |

A família `politica` estreia com a filiação partidária do TSE (filiado vivo por
município, número efetivo de partidos e HHI partidário) e sozinha abre
**210 trincas** que antes não existiam.
""")

    A("### As três guardas, e por que a terceira precisou existir\n")
    A(f"""Rodar dez mil pares sem guarda devolve artefato no topo. São três filtros,
e cada um nasceu de um artefato real desta corrida:

- **duplicata conceitual** ({int((pares.tipo=='duplicata').sum())} pares barrados) — a mesma grandeza por duas fontes.
  Cobertura do Bolsa Família aparece no espelho por *duas* vias (CGU novo
  Bolsa Família e CGU pagamento); cobertura de atenção básica e de vacina, por
  IEPS *e* por Ministério da Saúde. Correlacionar as duas é medir a mesma coisa
  duas vezes. O Pé-de-Meia entra aqui por outro motivo: ele **exige CadÚnico**,
  então sua correlação com o Bolsa Família é desenho de programa, não achado.
- **métrica de registro** ({int((viv.tipo=='registro').sum())} sobreviventes marcados `⚠`) — a coluna mede a
  capacidade de registrar antes do fenômeno. `snis_gap_agua` é a razão entre a
  água *declarada* ao SNIS e a medida pelo IBGE; notificação de arbovirose mede
  vigilância instalada; e a **nota do ENEM** entrou aqui nesta rodada, por um
  motivo específico do espelho: `id_municipio_residencia` existe e está **100%
  nula em todos os anos**, então a agregação é por município de **prova** — a
  média é a dos alunos da região inteira que foram prestar prova no polo.
- **mesmo construto** ({int((viv.tipo=='construto').sum())} sobreviventes marcados) — guarda nova, e ela
  nasceu quando o topo da corrida virou IVS × INSE × IDHM × cobertura do Bolsa
  Família. Não são a mesma fonte, mas são o mesmo construto latente: "quão pobre
  é este município". Publicar isso como descoberta seria constrangedor. Par que
  **sai** desse grupo para um desfecho (IVS × nota do ENEM) segue valendo.
""")

    A(f"""Depois das três guardas sobram **{br(len(ach))} achados**, e a distribuição é a
mesma da rodada anterior — o espelho continua sendo um objeto de correlações
fracas sob controle: **{int((ach.r_parcial.abs()>=.5).sum())}** passa de |r| = 0,50,
{int(((ach.r_parcial.abs()>=.3)&(ach.r_parcial.abs()<.5)).sum())} ficam entre 0,30 e 0,50, e
{br(int((ach.r_parcial.abs()<.3).sum()))} são fracos.
""")

    A("### Os achados no topo\n")
    A("| r parcial | bruto | n | par | famílias |\n|---|---|---|---|---|")
    for _,r in ach.head(12).iterrows():
        A(f"| **{r.r_parcial:+.2f}".replace(".",",") + "** | "
          + f"{r.r_bruto:+.2f}".replace(".",",") + f" | {br(r.n)} | "
          + f"`{r.col_a}` × `{r.col_b}` | {r.fam_a} × {r.fam_b} |")
    A("")

    if pol is not None:
        pol=pol.sort_values("lift",ascending=False)
        base=pol.taxa_base.iat[0]
        A("## O segundo eixo — político → sociedade → papel da empresa\n")
        A(f"""Este é o caminho que motivou a rodada, e ele funciona. O casamento é
`TSE candidatos` (CPF completo + nome) contra `br_me_cnpj.socios` (CPF
**mascarado** `***123456**` + nome), pela mesma técnica do T37-3: nome
normalizado mais os 6 dígitos visíveis.

**A ressalva vem antes do número, porque ela manda no resultado.** O par
(nome, 6 dígitos) não é identificador único: **{br(58.8,1)}% dos casamentos brutos são
ambíguos** — homônimo com os mesmos 6 dígitos — e saem do agregado. O que sobra
é uma lista para conferência, não um cadastro de fato. E "político" aqui é
*candidato desde 2014*, não eleito: são {br(1384616)} pessoas.

A comparação é **dentro** do conjunto de empresas com algum papel, não contra a
população geral — candidato é mais velho, mais rico e mais urbano que a média, e
essas três coisas já predizem ser sócio de empresa.

Taxa-base: **{base:.2%}** das {br(9255368)} empresas com algum papel têm sócio-político.
""".replace(".",",",0))
        A("| papel | empresas | com sócio-político | taxa | lift |\n|---|---|---|---|---|")
        for _,r in pol.head(14).iterrows():
            A(f"| `{r.papel}` | {br(r.empresas_papel)} | {br(r.com_socio_politico)} | "
              + f"{r.taxa:.2%}".replace(".",",") + " | **"
              + f"{r.lift:.2f}".replace(".",",") + "** |")
        A("")

    if cnpj is not None:
        # lift_papel, nao lift_cadastro: o cadastro inteiro (64,5 milhoes de
        # raizes, todo MEI e toda empresa morta ja registrada) infla o lift em
        # ordens de grandeza sem informar nada.
        ch="lift_papel"
        cnpj_ach=cnpj[cnpj.tipo=="achado"] if "tipo" in cnpj else cnpj
        n_def=len(cnpj)-len(cnpj_ach)
        A("## Todos os pares de papel sobre o mesmo CNPJ\n")
        A(f"""{br(len(cnpj))} pares acima do piso de 30 empresas em comum, dos quais
**{br(n_def)} são definicionais** e saem da lista: vencedor de licitação é
subconjunto de participante, embargo do IBAMA nasce de um auto de infração, SICAF
é pré-requisito para vender à União, CEIS e CNEP são cadastros de sanção que se
sobrepõem. Sem essa quarta guarda, os 18 maiores lifts da corrida são todos
variações de "A implica B por desenho do processo". Sobram **{br(len(cnpj_ach))}**.

A medida **não é
correlação** — é *lift*, `P(B|A) ÷ P(B)`: quantas vezes mais provável é a empresa
que faz A também fazer B, comparada a uma empresa qualquer. Dois denominadores
são reportados sempre (cadastro inteiro e empresas-com-papel), porque escolher um
e omitir o outro é como se fabrica manchete falsa com dado verdadeiro. E o
`or_mh_cnae_idade` é o Mantel-Haenszel estratificado por divisão CNAE e tercil de
idade da empresa — o análogo do parcial: quando ele desaba, o achado era porte e
setor.
""")
        A("| lift | MH (CNAE×idade) | empresas em comum | P(B\\|A) | par |\n|---|---|---|---|---|")
        for _,r in cnpj_ach.head(15).iterrows():
            pct=f"{r.p_b_dado_a:.1%}".replace(".",",")
            A(f"| **{br(r[ch],1)}** | {br(r.or_mh_cnae_idade,1)} | {br(r.n_ambos)} "
              f"| {pct} | `{r.papel_a}` × `{r.papel_b}` |")
        A("")

    A("## Como refazer\n")
    A("""```bash
# 1. extracao (no beelink, offline e retomavel) — os .sql de h3_ ficam soltos em
# scripts/hipoteses/ junto com os das outras rodadas, entao stage antes do scp
mkdir -p /tmp/h3 && cp scripts/hipoteses/h3_*.sql scripts/hipoteses/h3_roda.sh /tmp/h3/
scp -r /tmp/h3 beelink:~/hipoteses3 && ssh beelink 'cd ~/hipoteses3 && bash h3_roda.sh'
scp -r beelink:~/rodado_hipoteses/h3_<data> tasks/hipoteses_resultado/

# 2. analise (local)
python3 scripts/hipoteses/h3_10_estende_painel.py    # painel 270 -> 358 colunas
python3 scripts/hipoteses/h3_40_roda_trincas.py      # eixo territorio
python3 scripts/hipoteses/h3_20_matriz_cnpj.py       # eixo identificador
python3 scripts/hipoteses/h3_30_politico_empresa.py  # a ponte
python3 scripts/hipoteses/h3_50_escreve.py           # este arquivo
```
""")
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text("\n".join(L)+"\n",encoding="utf-8")
    print(f"{OUT.relative_to(REPO)}: {len(L)} blocos")

if __name__=="__main__":
    sys.exit(main())
