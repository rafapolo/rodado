# Nossos dados e os do Colmeia batem?

Batem em quase tudo. A comparação é entre `br_rodado_eleicoes` (a ponte entre seção eleitoral
e setor censitário, descrita em [`docs/pesquisa/eleicoes_setor/schema.md`](../pesquisa/eleicoes_setor/schema.md))
e o que o [Colmeia](https://colmeiabrasil.github.io/colmeia/) publica para o 1º turno de 2026.
Os dois seguem o mesmo método, adaptado de
[deltafolha/eleicoes-por-setores-censitarios](https://github.com/deltafolha/eleicoes-por-setores-censitarios),
e foram implementados de forma independente.

Medido em 2026-10-09, contra o commit `7edbda2` do repositório `colmeiabrasil/colmeia` e os
arquivos de setor publicados no site nessa data.

## O que foi comparado

- **Por setor:** 29.930 setores de 726 subdistritos — o Acre inteiro mais 700 subdistritos
  sorteados no país (semente fixa). Para cada setor: quais locais de votação estão ligados a
  ele, a distância ao local mais próximo, os "votos para Lula vencer" e o "potencial de votos".
- **Por município:** os 5.555 municípios com resultado nos dois lados — percentual de Lula e
  de Flávio sobre os votos válidos, abstenção, brancos e nulos.

Os dois indicadores por setor foram recalculados do nosso lado com a fórmula da
especificação do Colmeia, só nos setores em que os locais ligados são os mesmos:

- votos para Lula vencer = metade da diferença entre Flávio e Lula, mais um, com a diferença
  percentual ponderada (peso 1 ÷ distância ao centroide) aplicada aos votos válidos sem peso;
  zero quando Lula lidera;
- potencial de votos = fração ponderada de abstenções + brancos + nulos, aplicada aos aptos sem peso.

## Resultado

| O que | Bate | Não bate |
|---|---|---|
| Locais de votação ligados a cada setor | 29.079 de 29.930 (97,2%) idênticos | 686 parcialmente iguais, 165 diferentes |
| Distância do setor ao local mais próximo | 25.135 (84%) iguais: 19.676 em ±1 m, 5.459 com menos de 1% | 4.795 (16%) |
| Votos para Lula vencer | 12.816 de 13.008 (98,5%) em ±1 voto | 192 |
| Potencial de votos | 12.839 de 13.051 (98,4%) em ±1 | 212, dos quais 198 abaixo de 2% |
| Resultado por município (Lula e Flávio, ±0,05 p.p.) | 5.544 de 5.555 | 11 |
| Abstenção por município (±0,05 p.p.) | 5.544 de 5.555 | 11 |

Coordenadas foram comparadas com tolerância de 0,00003 grau (cerca de 3 m), porque o Colmeia
publica com cinco casas decimais.

## De onde vêm as diferenças

**Locais parcialmente iguais (686 setores).** Em 487 temos um local a mais, em 196 o Colmeia
tem, e em 3 cada lado tem um local que o outro não tem. Parte do nosso excesso é por
construção: o Colmeia descarta o local sem coordenada no arquivo do TSE, e aqui ele herda a
coordenada da mesma seção ou do mesmo local em outro ano. O resto é local na fronteira de
uma faixa de 100 m.

**Distância (16% dos setores).** Entre o 5º e o 95º percentil, a nossa distância vai de
36 m menor a 0,7 m maior que a deles; a mediana da diferença é zero. Medimos numa projeção
local por município; o código do cálculo do Colmeia não está no repositório público, então
não dá para dizer qual das duas está mais certa. É essa diferença que empurra um local para
a faixa vizinha.

**Locais totalmente diferentes (165 setores).** Não foram investigados caso a caso. Nos
exemplos vistos, cada lado ligou o setor a um local distinto e as distâncias divergem muito
(1.096 m lá e 22 m aqui, 276 m lá e 0 m aqui).

**Municípios (11).** Araguari, Caratinga, Carneirinho, Divino, Dores do Turvo, Extrema,
Perdizes e Tapira (MG), Nova Ubiratã (MT), Alexandria (RN) e São Miguel da Boa Vista (SC).
Nos seis abertos, o Colmeia soma mais de um código de município do TSE sob o mesmo município
do IBGE:

| Município (IBGE) | Códigos do TSE somados pelo Colmeia | A quem pertencem |
|---|---|---|
| Perdizes | 49956 + 46450 | Perdizes + Itaipé |
| Tapira | 53619 + 53635 | Tapira + Tapiraí |
| Araguari | 40690 + 46132 + 50016 | Araguari + Indianópolis + Piau |
| Divino | 44393 + 52655 | Divino + outro, não identificado |
| São Miguel da Boa Vista | 80780 + 81680 | São Miguel da Boa Vista + Tigrinhos |
| Nova Ubiratã | 90883 + 73709 | Nova Ubiratã + Boa Esperança do Norte |

Em Perdizes isso leva Lula de 31,7% (aqui) para 41,3% (lá). Em Perdizes, Tapira e Araguari o
nosso número foi conferido contra a tabela de resultados por município do TSE e fecha. A
causa do lado deles não foi confirmada; a hipótese é que o município venha da posição do
local de votação, e um local com coordenada errada caia em outro município.

## O que a comparação corrigiu do nosso lado

O código do TSE `73709` (MT) estava sem município do IBGE: são 13 seções e 4.323 eleitores.
É **Boa Esperança do Norte** (IBGE `5101837`), município instalado em 1º de janeiro de 2025,
desmembrado de Nova Ubiratã e Sorriso; a tabela de locais de votação do espelho traz o código
sem correspondência. Como a malha de setores é de 2022, nenhum setor tem o código do
município novo. A correção, em `scripts/eleicoes_setor/constroi_ponte.sql`:

- o código `73709` passa a apontar para `5101837`;
- a tabela `secao_setor` ganhou a coluna `id_municipio_malha`: o município da seção como ele
  existe na malha de 2022. Para município criado depois do Censo, é o município da malha que
  contém o ponto. As 13 seções caem em Vera (8) e Nova Ubiratã (5), em 3 setores.

Os números da tabela de resultado são de antes dessa correção, que mexe em 13 seções.

## Como refazer

```bash
./scripts/eleicoes_setor/constroi_ponte.sh       # reconstrói br_rodado_eleicoes no beelink
# agregados nossos por setor e por município (grava dois CSV em ~/duckdb_tmp no beelink):
ssh beelink '~/bin/duckdb -readonly ~/rodado/basedosdados.duckdb' < scripts/eleicoes_setor/compara_colmeia_nosso.sql
# clonar colmeiabrasil/colmeia (dados/locais e dados/municipios) e baixar a amostra de setores do site:
python3 scripts/eleicoes_setor/compara_colmeia_baixa.py cmp_nosso_setor.csv.gz <pasta_setores>
python3 scripts/eleicoes_setor/compara_colmeia.py cmp_nosso_setor.csv.gz <pasta_setores> <clone_do_colmeia> cmp_nosso_mun.csv.gz
```

Os arquivos de setor do Colmeia estão em Git LFS; sem `git-lfs` o clone vem sem eles, e por
isso a amostra é baixada do site publicado.
