# Sanções, Offshore e Arquitetura da Impunidade Empresarial
```mermaid
erDiagram
    global_icij_offshoreleaks_entities {
        string node_id
        string name
        string jurisdiction_description
        string countries
        date incorporation_date
    }
    br_comprasgov_sicaf_fornecedores { string cnpj string cpf bool habilitadoLicitar bool ativo string ufSigla }
    br_cgu_sancoes_ceis { date data_extracao string tipo_pessoa string cpf_cnpj_sancionado string categoria_sancao string abrangencia_sancao string esfera_orgao date data_inicio_sancao date data_final_sancao }
    br_cgu_sancoes_cnep { date data_extracao string cpf_cnpj_sancionado string categoria_sancao string abrangencia_sancao date data_final_sancao }
    br_cgu_sancoes_acordos_leniencia { date data_extracao string id_acordo string cnpj_sancionado string situacao_acordo }
    br_tcu_inidoneos_empresas { string NOME string CPF_CNPJ string PROCESSO date DATA_FINAL }
    br_pgfn_dividaativa_divida { string CPF_CNPJ string NOME_DEVEDOR string VALOR_CONSOLIDADO string INDICADOR_AJUIZADO string categoria }
    global_opensanctions_entities { string id string name string countries string sanctions }
    global_icij_offshoreleaks_entities ||--o{ global_opensanctions_entities : "name"
    br_comprasgov_sicaf_fornecedores ||--o{ br_tcu_inidoneos_empresas : "cnpj"
    br_comprasgov_sicaf_fornecedores ||--o{ br_cgu_sancoes_ceis : "cnpj = cpf_cnpj_sancionado"
    br_comprasgov_sicaf_fornecedores ||--o{ br_cgu_sancoes_cnep : "cnpj = cpf_cnpj_sancionado"
```

## Contexto e Síntese dos Dados

Quatro registros de má conduta empresarial que raramente sao lidos juntos: `global_icij_offshoreleaks` (814.344 entidades vazadas, 1.532 com vinculo brasileiro), `global_opensanctions`/`eu_sanctions`/`un_sanctions`/`global_ofac_sanctions` (listas internacionais de sancao), `br_tcu_inidoneos` (banidos de contratar com o poder publico pelo TCU), `br_cgu_sancoes` (CEIS, CNEP, CEPIM e acordos de leniencia da CGU — sancoes de orgaos federais, estaduais e municipais; **cada tabela empilha retratos por `data_extracao`, filtrar o mais recente** senao conta em dobro) e `br_pgfn_dividaativa` (46,6 milhoes de inscricoes de divida ativa da Uniao, 3 categorias: FGTS, previdenciario e nao-previdenciario).

## Revelacoes Importantes

### 1. Offshore brasileira por jurisdicao

| Jurisdicao | Entidades |
|---|---|
| Panama | 589 |
| Ilhas Virgens Britanicas | 492 |
| Nevada (EUA) | 132 |
| Niue | 91 |
| Seicheles | 79 |

**Conclusao:** 70% das estruturas brasileiras em Panama e BVI; Nevada supera Seicheles e Bahamas.

### 2. Funil de responsabilizacao

| Registro | Quantidade |
|---|---|
| Cadastros no SICAF (jul/2026) | 962.016 |
| CNPJs distintos habilitados a licitar | 640.060 |
| Empresas com sancao vigente no CEIS/CNEP (24/10/2026) | 7.559 |
| — inidoneas por algum orgao | 1.727 |
| — proibidas em todas as esferas e Poderes | 988 |
| Empresas inidoneas (TCU, 123 linhas) | 117 |
| Acordos de leniencia CGU (empresas) | 52 (139) |

Das 7.559 sancionadas, 3.711 constam `habilitadoLicitar` no SICAF; das 988 com `abrangencia_sancao = 'Todas as Esferas em todos os Poderes'`, 213 (21,6%). Todas com `data_inicio_sancao` anterior ao retrato do SICAF (2026-07-13) e `data_final_sancao` >= 2026-10-24 ou nula. Conferido com `IN` e com `LEFT JOIN` (mesmo resultado); casando pela raiz de 8 digitos sobe para 3.731.

**Conclusao:** uma em cada cinco empresas proibidas em todo o pais segue habilitada no cadastro federal.

### 3. Divida Ativa da Uniao (46,6 milhoes de inscricoes)

| Categoria | Inscricoes | Exemplo de devedor |
|---|---|---|
| FGTS | 532.707 | Empresas com FGTS nao recolhido |
| Previdenciario | 3.742.859 | Contribuicoes devidas ao INSS |
| Nao-previdenciario | 42.331.519 | Tributos federais (IRPJ, COFINS, CPMF, etc) |

Maiores devedores pessoa juridica: Vale S.A. (R$ 44 bi), Banco Santander Brasil (R$ 11,7 bi), Petrobras (R$ 29 bi em multiplas inscricoes), Carital Brasil/Zirconia Participacoes (R$ 10 bi cada, falidas).

**Conclusao:** a divida nao-previdenciario domina (91% das inscricoes). Tres empresas concentram dezenas de bilhoes. A PGFN cobre so a esfera federal — divida ativa estadual e municipal nao esta incluida.

## Cruzamentos Poderosos

- **Offshore x Jurisdicao:** 70% em Panama e Ilhas Virgens Britanicas.
- **SICAF x CEIS/CNEP:** 213 das 988 empresas proibidas em todas as esferas seguem habilitadas.
- **TCU x CGU:** 117 inidoneas no TCU contra 7.559 empresas com sancao vigente na CGU.
- **FGTS x Concentracao:** 1% dos devedores responde por 45,8% do valor.
- **Divida x Judicializacao:** 35,9% do FGTS nunca virou acao judicial.
- **PGFN x SICAF:** cruzar 46,6M inscricoes de divida ativa com fornecedores habilitados revela empresas que devem a Uniao enquanto contratam com ela.
- **Nevada x Caribe:** um estado dos EUA recebe mais offshore brasileira que Seicheles.

## Hipoteses Explicativas

Detectar irregularidade e barato e automatizavel; puni-la exige devido processo, com custo humano e prazo proprios. O resultado e um funil onde a deteccao cresce com a tecnologia e a punicao permanece limitada pelo numero de servidores.

## Implicacoes para Politicas Publicas

Priorizar cobranca pelos maiores devedores recuperaria metade do valor com fracao do esforco. Integrar o cadastro de inidoneos ao SICAF na habilitacao fecharia a janela em que empresa punida segue cadastrada.
