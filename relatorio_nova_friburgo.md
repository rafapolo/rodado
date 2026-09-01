# Poluentes atmosféricos em Nova Friburgo/RJ — levantamento semestral

**Referência:** setembro/2025 (2º semestre de 2025) · **Gerado em:** 01/09/2026
**Página:** https://rodado.xyz/analises/poluentes-do-ar-em-nova-friburgo/
**Gerador:** `scripts/gera_relatorio_nf.py` · **Uma folha A4:** `relatorio.pdf`

Levantamento cadastral das oito atividades potencialmente geradoras de emissões
atmosféricas pedidas, no município de Nova Friburgo (IBGE 3303401), a partir do
CNPJ da Receita Federal cruzado com RAIS, contratos públicos e cadastros de
sanção. **732 estabelecimentos ativos**, sem dupla contagem — 0,94% dos 78.211
estabelecimentos do município.

## Quadro-resumo

| Atividade | Ativos | CNAE princ. | CNAE sec. | Inaptos | Baixados | Vínculos (RAIS 2025) | Δ último semestre |
|---|--:|--:|--:|--:|--:|--:|--:|
| Marmorarias | 30 | 13 | 17 | 9 | 29 | 32 | +30,0% |
| Metalurgia (CNAE 24) | 7 | 3 | 4 | 6 | 10 | 32 | 0,0% |
| Produtos de metal (CNAE 25) | 553 | 302 | 251 | 138 | 437 | 3.623 | +2,4% |
| Torrefação e moagem de café | 3 | 1 | 2 | 5 | 4 | 0 | −50,0% |
| Fabricação de produtos químicos | 13 | 5 | 8 | 15 | 60 | 36 | −16,7% |
| Olaria e artefatos de cerâmica | 87 | 38 | 49 | 11 | 57 | 6 | +8,6% |
| Gesso e produtos à base de gesso | 56 | 12 | 44 | 12 | 43 | 0 | +9,1% |
| Gorduras vegetais e animais | 5 | 2 | 3 | 4 | 6 | 7 | 0,0% |
| Extração de minerais não metálicos | 20 | 17 | 3 | 11 | 35 | 14 | 0,0% |

A soma das linhas passa de 732 porque um mesmo CNPJ pode ter atividade em duas
categorias. A variação semestral é medida sobre CNAE principal — critério
reproduzível em qualquer mês da série.

## O que o levantamento mostrou

- **A cidade é metal-mecânica, não metalúrgica.** 553 estabelecimentos ativos de
  fabricação de produtos de metal (serralheria, esquadria, usinagem, solda), com
  3.623 empregos formais. Metalurgia no sentido estrito — quem funde metal — são
  **3**. As empresas com "metalúrgica" no nome estão quase todas cadastradas em
  CNAE 2542-0/00, serralheria.
- **Dois em cada três são MEI** (459 dos 732); 92% são microempresa. Esse porte
  não aparece em cadastro estadual de licenciamento.
- **Uma torrefação de café ativa** (Conselheiro Paulino). As outras ~35 empresas
  com "café" no nome são cafeterias e lanchonetes.
- **Nenhum fabricante de gesso.** A CNAE 2392-3/00 tem zero registros no
  município; as quatro empresas com "gesso" no nome instalam drywall ou vendem
  material. Os 12 ativos contados na categoria estão na CNAE agregada 2330-3/99
  (concreto/cimento/fibrocimento/gesso), que não permite isolar.
- **Extração mineral parada em 17 ativos** há sete semestres, mas o emprego caiu
  de 53 (2018) para 14 (2025).
- **Conselheiro Paulino concentra 102 dos 732** (14%) — o distrito industrial.

## Cruzamentos por CNPJ

| Cruzamento | Resultado |
|---|---|
| RAIS identificada (empregados por CNPJ) | 206 empresas, 4.425 vínculos somados — a série vai só até 2021 |
| Contrato público (TCE-RJ municipal + CGU federal) | 6 empresas · 1 com a prefeitura de Nova Friburgo, 2 com Bom Jardim, 1 com Quissamã, 2 federais |
| SICAF (fornecedor do governo federal) | 20 empresas |
| Embargo ambiental do IBAMA | **0** — conferido por CNPJ em todo o país |
| Inidôneos / suspensos no TCU | **0** |

A dívida ativa da PGFN casou em 237 empresas (1.990 inscrições), mas é toda
tributária — nenhuma multa ambiental. Ficou fora do relatório por ser off-topic.

## O que não pôde ser confirmado

- **Situação de licenciamento (LP/LI/LO), número do processo e da licença.** Não
  existem em nenhuma base pública espelhada. O que o relatório traz é a *situação
  cadastral na Receita Federal* — se o CNPJ existe e está ativo, não se a
  atividade está licenciada. Preencher exige consulta ao INEA e à Secretaria de
  Meio Ambiente de Nova Friburgo. Nenhum número foi estimado.
- **Órgão responsável.** Por competência: INEA/RJ para o que não é de impacto
  local; município para o impacto local — o IBGE MUNIC registra que Nova Friburgo
  assumiu o licenciamento de impacto local (2012 e 2015, com LP/LI/LO concedidas)
  e tem legislação sobre poluição do ar desde 2009.
- **Empreendimentos sem CNPJ** (extração informal, olaria de fundo de quintal)
  estão fora do alcance de todas as bases usadas.

O que fecharia cada uma dessas lacunas está catalogado em
`tasks/datasets_licenciamento_ambiental.md`.

## Comparação entre semestres

Série de sete semestres (2022-S2 a 2025-S2), montada das fotos mensais do
cadastro em março e setembro. Para o próximo levantamento:

```bash
python3 scripts/gera_relatorio_nf.py --ref 2026-03 \
  --a4 /tmp/a4.html --artifact /tmp/relatorio-nf.html
python3 scripts/gera_analises.py          # SEO + cartão
```

O script refaz a série, o quadro-resumo, os cruzamentos e a lista completa; a
comparação entre períodos sai pronta na seção 03 da página.

## Fontes

Receita Federal (CNPJ, Simples/MEI) · MTE (RAIS estabelecimentos e RAIS
identificada) · IBGE/Concla (CNAE 2.3) · IBGE (MUNIC Meio Ambiente) · IBAMA
(áreas embargadas) · TCE-RJ (contratos municipais) · CGU (contratos federais) ·
Compras.gov (SICAF) · TCU (inidôneos). A página traz a data de espelhamento de
cada uma no rodapé.
