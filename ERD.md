# ERD — como o espelho se conecta

🇬🇧 [English version](ERD_EN.md)

Mapa de entidades e relações das 825 tabelas (195 datasets) do espelho. Gerado por `scripts/gera_erd.py` a partir de `schemas.json` em 2026-07-27 — não edite à mão, regenere.

📊 **Pôsteres em PDF** (gerados por `scripts/gera_erd_poster.py`):
  - [`ERD-poster-domain.pdf`](ERD-poster-domain.pdf) — visão agregada: hubs + domínios (A1, ~62 KB)
  - [`ERD-poster-full.pdf`](ERD-poster-full.pdf) — catálogo completo: todos os 195 datasets listados (A0, ~47 KB)

As expressões de join, o formato de cada chave e as pegadinhas estão em [`docs/context/join_keys.md`](docs/context/join_keys.md). Este arquivo é o mapa; aquele é o manual.

## Como ler

Um único `erDiagram` com 825 tabelas seria ilegível, então o modelo sobe um nível:

- **entidade = dataset**; **atributo = uma das tabelas** dele;
- o *tipo* do atributo lista as chaves que aquela tabela carrega (`mun`, `uf`, `cnpj`, `cnes`, `escola`, `setor`, `cep`, `cpf`, `cnae`, `cbo`, `cid`, `ncm`, `pais`, `partido`, `orgao`, `ug`, `funcprog`, `ano`, `mes`), ou `sem_chave` quando não há nenhuma;
- o comentário é a contagem de linhas do `_rodado_metadata`;
- **aresta = chave de join** que chega a um hub de referência:

| aresta | significado |
|---|---|
| `HUB \|\|--o{ dataset` | (sólida) a chave está lá com o nome canônico — join direto |
| `HUB \|\|..o{ dataset` | (tracejada) a chave está lá com outro nome ou formato — normalize antes, receita em [`docs/context/join_keys.md`](docs/context/join_keys.md) |

Dataset sem nenhuma aresta aparece como caixa solta no diagrama do seu domínio: está no espelho, mas nada documentado o liga a mais nada.

## Os hubs

| hub | tabela de referência | chave | observação |
|---|---|---|---|
| `MUNICIPIO` | `br_bd_diretorios_brasil.municipio` | `id_municipio` (7) | 5.571 municípios; carrega também `id_municipio_6/_tse/_rf/_bcb` |
| `UF` | `br_bd_diretorios_brasil.uf` | `sigla_uf` / `id_uf` | 27 unidades da federação |
| `SETOR_CENSITARIO` | `br_bd_diretorios_brasil.setor_censitario_2022` | `id_setor_censitario` (15) | as malhas de 2010 e 2022 não são compatíveis |
| `CEP` | `br_bd_diretorios_brasil.cep` | `cep` (8) | 905 mil CEPs — a única tabela de diretório sem duplicação |
| `EMPRESA_CNPJ` | `br_me_cnpj.estabelecimentos` / `.empresas` | `cnpj` (14) / `cnpj_basico` (8) | 43 snapshots mensais — fixe `ano`/`mes` |
| `PESSOA_CPF` | — | `cpf` (11) | sem diretório; quase sempre mascarado |
| `ESCOLA` | `br_bd_diretorios_brasil.escola` | `id_escola` | 218 mil escolas |
| `IES` | `br_bd_diretorios_brasil.instituicao_ensino_superior` | `id_ies` |  |
| `CNES` | `br_ms_cnes.estabelecimento` | `id_estabelecimento_cnes` | snapshots mensais; chaveado por `id_municipio_6` |
| `CNAE` | `br_bd_diretorios_brasil.cnae_2` | `subclasse` (7) |  |
| `CBO` | `br_bd_diretorios_brasil.cbo_2002` | `cbo_2002` |  |
| `CID10` | `br_bd_diretorios_brasil.cid_10` | `categoria` / `subcategoria` |  |
| `NCM_SH` | `br_bd_diretorios_mundo.nomenclatura_comum_mercosul` | `id_ncm`, `id_sh4` |  |
| `PAIS` | `br_bd_diretorios_mundo.pais` | `sigla_pais_iso3`, `id_pais` |  |
| `ORGAO` | `br_cgu_licitacao_contrato.licitacao` | `id_orgao` | órgão do SIAFI; `id_orgao_superior` é o nível acima. O `id_orgao` da Câmara é outra numeração (comissões) e não entra aqui |
| `UNIDADE_GESTORA` | `br_cgu_licitacao_contrato.licitacao` | `id_unidade_gestora` | UG — o nível a que o gasto é efetivamente atribuído |
| `FUNCAO_PROGRAMA` | `br_cgu_orcamento_publico.orcamento` | `id_funcao`, `id_subfuncao`, `id_acao`, `id_programa` | classificação funcional-programática do orçamento federal |
| `PARTIDO` | `br_tse_eleicoes.partidos` | `sigla_partido` | siglas mudam entre eleições |

```mermaid
erDiagram
    UF ||--o{ MUNICIPIO : "id_municipio comeca com id_uf"
    MUNICIPIO ||--o{ SETOR_CENSITARIO : "7 primeiros digitos"
    MUNICIPIO ||--o{ CEP : "id_municipio"
    MUNICIPIO ||--o{ ESCOLA : "id_municipio"
    MUNICIPIO ||--o{ IES : "id_municipio"
    MUNICIPIO ||--o{ CNES : "id_municipio_6"
    MUNICIPIO ||--o{ EMPRESA_CNPJ : "id_municipio_rf"
    CEP ||--o{ EMPRESA_CNPJ : "cep"
    EMPRESA_CNPJ ||--o{ PESSOA_CPF : "socios"
    EMPRESA_CNPJ }o--|| CNAE : "cnae_fiscal_principal"
    PESSOA_CPF }o--o{ CBO : "vinculo RAIS/CAGED"
    PESSOA_CPF }o--o{ CID10 : "diagnostico SIH/SIM/SINAN"
    CNES ||--o{ CID10 : "diagnostico"
    PAIS ||--o{ NCM_SH : "comercio exterior"
    PARTIDO }o--o{ MUNICIPIO : "eleicoes, via id_municipio_tse"
    ORGAO ||--o{ UNIDADE_GESTORA : "id_orgao"
    UNIDADE_GESTORA }o--o{ FUNCAO_PROGRAMA : "classificacao do gasto"
```

`ano`/`mes`/`data` são a dimensão temporal de quase toda tabela — ficam como atributo, nunca como aresta, senão o diagrama vira um novelo.

---

## Cobertura

| domínio | datasets | tabelas | conectados |
|---|---|---|---|
| Diretórios e tabelas de referência | 10 | 71 | 9 |
| Saúde | 20 | 50 | 19 |
| Educação e ciência | 20 | 140 | 17 |
| Trabalho, empresas e economia | 40 | 117 | 33 |
| Governo, orçamento e compras | 31 | 107 | 26 |
| Política e eleições | 6 | 60 | 6 |
| Justiça, segurança e sanções | 21 | 52 | 12 |
| Território, ambiente e infraestrutura | 21 | 80 | 18 |
| Demografia e indicadores sociais | 17 | 123 | 15 |
| Internacional, cultura e esporte | 9 | 25 | 3 |
| **total** | **195** | **825** | **158** |

37 datasets não têm chave documentada alguma; 201 tabelas individuais não carregam chave nenhuma (ambas as listas no fim).

---

## Diretórios e tabelas de referência

10 datasets · 71 tabelas

**1/2**

```mermaid
erDiagram
    CBO ||--o{ br_bd_diretorios_brasil : "cbo_2002 +1"
    CEP ||--o{ br_bd_diretorios_brasil : "cep"
    CID10 ||--o{ br_bd_diretorios_brasil : "cid_datasus"
    CNAE ||--o{ br_bd_diretorios_brasil : "cnae_1 +2"
    EMPRESA_CNPJ ||--o{ br_bd_diretorios_brasil : "cnpj +3"
    ESCOLA ||--o{ br_bd_diretorios_brasil : "id_escola"
    IES ||--o{ br_bd_diretorios_brasil : "id_ies"
    MUNICIPIO ||--o{ br_bd_diretorios_brasil : "id_municipio +4"
    SETOR_CENSITARIO ||--o{ br_bd_diretorios_brasil : "id_setor_censitario"
    UF ||--o{ br_bd_diretorios_brasil : "sigla_uf +1"
    NCM_SH ||--o{ br_bd_diretorios_mundo : "id_ncm +3"
    PAIS ||--o{ br_bd_diretorios_mundo : "sigla_pais_iso3 +2"
    UF ||..o{ br_bd_diretorios_mundo : "sigla"
    MUNICIPIO ||..o{ br_bd_diretorios_us : "city"
    UF ||..o{ br_bd_metadados : "state"
    MUNICIPIO ||--o{ br_bd_vizinhanca : "id_municipio_1 +1"
    UF ||--o{ br_bd_vizinhanca : "sigla_uf_1 +1"
    br_bd_diretorios_brasil {
        sem_chave area_conhecimento "1.8k linhas"
        cbo cbo_1994 "4.8k linhas"
        cbo cbo_2002 "5.6k linhas"
        mun_uf_cep cep "905.2k linhas"
        cid cid_10 "25k linhas"
        cid cid_9 "1.8k linhas"
        cnae cnae_1 "1.2k linhas"
        cnae cnae_2 "2.7k linhas"
        sem_chave curso_superior "510 linhas"
        mun_uf distrito_1991 "17.7k linhas"
        mun_uf distrito_2000 "19.7k linhas"
        mun_uf distrito_2010 "20.6k linhas"
        mun_uf_cep_cnpj_cnae empresa "vazia"
        mun_uf_escola escola "436.2k linhas"
        sem_chave etnia_indigena "528 linhas"
        mun_uf_ies instituicao_ensino_superior "13.2k linhas"
        mun_uf municipio "11.1k linhas"
        sem_chave natureza_juridica "204 linhas"
        uf regiao "10 linhas"
        mun_uf_setor setor_censitario_2010 "620.2k linhas"
        mun_uf_setor setor_censitario_2022 "904.7k linhas"
        sem_chave subatividade_ibge "572 linhas"
        uf uf "54 linhas"
    }
    br_bd_diretorios_data_tempo {
        ano ano "10k linhas"
        sem_chave bimestre "6 linhas"
        ano_mes data "1.8M linhas"
        sem_chave dia "31 linhas"
        sem_chave hora "24 linhas"
        mes mes "12 linhas"
        sem_chave minuto "60 linhas"
        sem_chave segundo "60 linhas"
        sem_chave semestre "2 linhas"
        sem_chave tempo "86.4k linhas"
        sem_chave trimestre "4 linhas"
    }
    br_bd_diretorios_mundo {
        uf continente "14 linhas"
        ncm nomenclatura_comum_mercosul "27.5k linhas"
        pais pais "526 linhas"
        ncm sistema_harmonizado "13.2k linhas"
    }
    br_bd_diretorios_us {
        sem_chave cbsa_2023 "937 linhas"
        sem_chave census_tract_2020 "85.4k linhas"
        sem_chave congress_member "12.8k linhas"
        sem_chave congressional_district_119 "440 linhas"
        sem_chave county "3.2k linhas"
        mun higher_education_institution "6.1k linhas"
        sem_chave naics_2022 "2.1k linhas"
        sem_chave place "32.4k linhas"
        sem_chave puma_2020 "2.5k linhas"
        sem_chave school "102.3k linhas"
        sem_chave school_district "19.6k linhas"
    }
    br_bd_metadados {
        sem_chave bigquery_tables "3.7k linhas"
        sem_chave external_links "1.3k linhas"
        sem_chave information_requests "389 linhas"
        sem_chave organizations "554 linhas"
        uf prefect_flow_runs "233.2k linhas"
        sem_chave resources "1.7k linhas"
        sem_chave tables "470 linhas"
    }
    br_bd_vizinhanca {
        mun_ano municipio "522.8k linhas"
        uf_ano uf "1.1k linhas"
    }
```

**2/2**

```mermaid
erDiagram
    MUNICIPIO ||..o{ br_brasilapi : "city"
    UF ||..o{ br_brasilapi : "state"
    CID10 ||..o{ br_datasus_cid10 : "CAT"
    MUNICIPIO ||--o{ br_ibge_amc : "id_municipio"
    CBO ||--o{ br_ibge_cbo_2002 : "cbo_2002"
    br_brasilapi {
        sem_chave bancos "481 linhas"
        mun_uf ddd_cidades "5.6k linhas"
        sem_chave feriados "100 linhas"
        sem_chave taxas_referencia "3 linhas"
    }
    br_datasus_cid10 {
        sem_chave capitulos "22 linhas"
        cid cid_o_categorias "816 linhas"
        sem_chave cid_o_grupos "63 linhas"
        cid codigos "2k linhas"
        sem_chave grupos "275 linhas"
        sem_chave subcategorias "12.5k linhas"
    }
    br_ibge_amc {
        mun_ano municipio_de_para "434.1k linhas"
    }
    br_ibge_cbo_2002 {
        cbo perfil_ocupacional "169.8k linhas"
        cbo sinonimo "7.7k linhas"
    }
```

## Saúde

20 datasets · 50 tabelas

```mermaid
erDiagram
    EMPRESA_CNPJ ||--o{ br_ans_beneficiario : "cnpj"
    MUNICIPIO ||--o{ br_ans_beneficiario : "id_municipio"
    UF ||--o{ br_ans_beneficiario : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_anvisa_cmed : "cnpj"
    MUNICIPIO ||--o{ br_anvisa_medicamentos_industrializados : "id_municipio"
    UF ||--o{ br_anvisa_medicamentos_industrializados : "sigla_uf +1"
    MUNICIPIO ||--o{ br_ieps_saude : "id_municipio"
    UF ||--o{ br_ieps_saude : "sigla_uf"
    MUNICIPIO ||--o{ br_ms_atencao_basica : "id_municipio +1"
    UF ||--o{ br_ms_atencao_basica : "sigla_uf"
    CBO ||--o{ br_ms_cnes : "cbo_2002 +2"
    CEP ||--o{ br_ms_cnes : "cep"
    CNES ||--o{ br_ms_cnes : "id_estabelecimento_cnes"
    EMPRESA_CNPJ ||--o{ br_ms_cnes : "cnpj_mantenedora"
    IES ||..o{ br_ms_cnes : "cnpj_mantenedora"
    MUNICIPIO ||--o{ br_ms_cnes : "id_municipio +2"
    PESSOA_CPF ||..o{ br_ms_cnes : "cpf_cnpj"
    UF ||--o{ br_ms_cnes : "sigla_uf"
    MUNICIPIO ||--o{ br_ms_imunizacoes : "id_municipio"
    UF ||--o{ br_ms_imunizacoes : "sigla_uf"
    UF ||--o{ br_ms_pns : "sigla_uf"
    MUNICIPIO ||--o{ br_ms_populacao : "id_municipio"
    CID10 ||--o{ br_ms_sia : "cid_principal_categoria +5"
    CNES ||--o{ br_ms_sia : "id_estabelecimento_cnes +1"
    MUNICIPIO ||--o{ br_ms_sia : "id_municipio +1"
    UF ||--o{ br_ms_sia : "sigla_uf"
    CBO ||--o{ br_ms_sih : "cbo_2002_paciente +1"
    CID10 ||--o{ br_ms_sih : "cid_principal_categoria +27"
    CNES ||--o{ br_ms_sih : "id_estabelecimento_cnes"
    EMPRESA_CNPJ ||--o{ br_ms_sih : "cnpj_mantenedora +1"
    IES ||..o{ br_ms_sih : "cnpj_mantenedora"
    MUNICIPIO ||--o{ br_ms_sih : "id_municipio_gestor +3"
    PESSOA_CPF ||--o{ br_ms_sih : "cpf_gestor"
    UF ||--o{ br_ms_sih : "sigla_uf"
    CNES ||..o{ br_ms_sim : "codigo_estabelecimento"
    MUNICIPIO ||--o{ br_ms_sim : "id_municipio +4"
    UF ||--o{ br_ms_sim : "sigla_uf"
    CNES ||--o{ br_ms_sinan : "id_estabelecimento_cnes"
    MUNICIPIO ||--o{ br_ms_sinan : "id_municipio_infeccao +6"
    UF ||--o{ br_ms_sinan : "sigla_uf +4"
    MUNICIPIO ||..o{ br_ms_sinan_violencia : "ID_MUNICIP"
    UF ||..o{ br_ms_sinan_violencia : "SG_UF"
    CNES ||..o{ br_ms_sinasc : "codigo_estabelecimento"
    MUNICIPIO ||--o{ br_ms_sinasc : "id_municipio_mae +2"
    UF ||--o{ br_ms_sinasc : "sigla_uf"
    MUNICIPIO ||--o{ br_ms_sisvan : "id_municipio"
    UF ||--o{ br_ms_sisvan : "sigla_uf"
    CNES ||..o{ br_ms_vacinacao_covid19 : "id_estabelecimento"
    MUNICIPIO ||--o{ br_ms_vacinacao_covid19 : "id_municipio"
    UF ||--o{ br_ms_vacinacao_covid19 : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_saude_bps : "cnpj_do_fabricante +2"
    MUNICIPIO ||..o{ br_saude_bps : "nome_do_munica­pio_da_instituicao"
    EMPRESA_CNPJ ||..o{ br_saude_farmaciapopular : "numero_cnpj +1"
    MUNICIPIO ||..o{ br_saude_farmaciapopular : "codigo_municipio"
    UF ||..o{ br_saude_farmaciapopular : "codigo_uf"
    br_ans_beneficiario {
        mun_uf_cnpj_ano_mes informacao_consolidada "2.3B linhas"
    }
    br_anvisa_cmed {
        cnpj precos "51.1k linhas"
    }
    br_anvisa_consultas {
        sem_chave registros "43.3k linhas"
    }
    br_anvisa_medicamentos_industrializados {
        mun_uf_ano_mes microdados "10M linhas"
    }
    br_ieps_saude {
        ano brasil "12 linhas"
        uf_ano macrorregiao "1.4k linhas"
        mun_uf_ano municipio "66.8k linhas"
        uf_ano regiao_saude "5.4k linhas"
        uf_ano uf "324 linhas"
    }
    br_ms_atencao_basica {
        mun_uf_ano_mes municipio "901.9k linhas"
    }
    br_ms_cnes {
        mun_uf_cnes_ano_mes dados_complementares "2.7M linhas"
        sem_chave dicionario "1.6k linhas"
        mun_uf_cnes_ano_mes equipamento "153.8M linhas"
        mun_uf_cnes_ano_mes equipe "13.8M linhas"
        mun_uf_cep_cnpj_cpf_ies_cnes_ano_mes estabelecimento "68.2M linhas"
        mun_uf_cnes_ano_mes estabelecimento_ensino "26.7k linhas"
        mun_uf_cnes_ano_mes estabelecimento_filantropico "157.9k linhas"
        mun_uf_cnes_ano_mes gestao_metas "152.3k linhas"
        mun_uf_cnes_ano_mes habilitacao "4.6M linhas"
        mun_uf_cnes_ano_mes incentivos "1.2M linhas"
        mun_uf_cnes_ano_mes leito "11.7M linhas"
        mun_uf_cnes_cbo_ano_mes profissional "868.9M linhas"
        mun_uf_cnes_ano_mes regra_contratual "1.5M linhas"
        mun_uf_cnes_ano_mes servico_especializado "146M linhas"
    }
    br_ms_imunizacoes {
        mun_uf_ano municipio "149.1k linhas"
    }
    br_ms_pns {
        sem_chave dicionario "4.9k linhas"
        uf microdados_2013 "222.4k linhas"
        uf microdados_2019 "293.7k linhas"
    }
    br_ms_populacao {
        mun_ano municipio "4.9M linhas"
    }
    br_ms_sia {
        sem_chave dicionario "5.9k linhas"
        mun_uf_cnes_cid_ano_mes producao_ambulatorial "6.2B linhas"
        mun_uf_cnes_cid_ano_mes psicossocial "138.1M linhas"
    }
    br_ms_sih {
        mun_uf_cnpj_cpf_ies_cnes_cbo_cid_ano_mes aihs_reduzidas "200.1M linhas"
        sem_chave dicionario "34.4k linhas"
        mun_uf_cnes_cbo_ano_mes servicos_profissionais "2.4B linhas"
    }
    br_ms_sim {
        sem_chave dicionario "569 linhas"
        mun_uf_cnes_ano microdados "31.2M linhas"
        mun_uf_ano municipio "132.9k linhas"
    }
    br_ms_sinan {
        sem_chave dicionario "818 linhas"
        mun_uf_cnes_ano microdados_dengue "34.7M linhas"
        mun_uf_cnes_ano microdados_influenza_srag "3.7M linhas"
    }
    br_ms_sinan_violencia {
        mun_uf_ano microdados_violencia "4.9M linhas"
    }
    br_ms_sinasc {
        sem_chave dicionario "414 linhas"
        mun_uf_cnes_ano microdados "85.6M linhas"
    }
    br_ms_sisvan {
        sem_chave dicionario "55 linhas"
        mun_uf_ano_mes microdados "406.3M linhas"
    }
    br_ms_vacinacao_covid19 {
        sem_chave dicionario "114 linhas"
        mun_uf_cnes microdados_estabelecimento "805.8k linhas"
    }
    br_saude_bps {
        mun_cnpj_ano dados "342.7k linhas"
    }
    br_saude_farmaciapopular {
        mun_uf_cnpj estabelecimentos "31k linhas"
    }
```

## Educação e ciência

20 datasets · 140 tabelas

**1/3**

```mermaid
erDiagram
    PESSOA_CPF ||--o{ br_capes_bolsas : "cpf"
    MUNICIPIO ||..o{ br_cnpq_bolsas : "municipio_destino"
    UF ||--o{ br_cnpq_bolsas : "sigla_uf_origem +1"
    ESCOLA ||--o{ br_inep_ana : "id_escola"
    MUNICIPIO ||--o{ br_inep_ana : "id_municipio"
    UF ||--o{ br_inep_ana : "id_uf"
    ESCOLA ||--o{ br_inep_avaliacao_alfabetizacao : "id_escola"
    MUNICIPIO ||--o{ br_inep_avaliacao_alfabetizacao : "id_municipio"
    UF ||--o{ br_inep_avaliacao_alfabetizacao : "sigla_uf"
    CEP ||--o{ br_inep_censo_educacao_superior : "cep"
    IES ||--o{ br_inep_censo_educacao_superior : "id_ies"
    MUNICIPIO ||--o{ br_inep_censo_educacao_superior : "id_municipio"
    UF ||--o{ br_inep_censo_educacao_superior : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_inep_censo_escolar : "cnpj_mantenedora +1"
    ESCOLA ||--o{ br_inep_censo_escolar : "id_escola +1"
    IES ||..o{ br_inep_censo_escolar : "cnpj_mantenedora"
    MUNICIPIO ||--o{ br_inep_censo_escolar : "id_municipio"
    UF ||--o{ br_inep_censo_escolar : "sigla_uf"
    MUNICIPIO ||--o{ br_inep_educacao_especial : "id_municipio"
    UF ||--o{ br_inep_educacao_especial : "sigla_uf"
    br_capes_bolsas {
        cpf_ano_mes mobilidade_internacional "146k linhas"
    }
    br_cnpq_bolsas {
        sem_chave dicionario "99 linhas"
        mun_uf_ano microdados "2.8M linhas"
    }
    br_inep_ana {
        sem_chave dicionario "224 linhas"
        mun_uf_escola_ano escola "98.1k linhas"
        ano prova "480 linhas"
    }
    br_inep_avaliacao_alfabetizacao {
        mun_escola_ano alunos "3.9M linhas"
        sem_chave dicionario "27 linhas"
        ano meta_alfabetizacao_brasil "3 linhas"
        mun_ano meta_alfabetizacao_municipio "10.7k linhas"
        uf_ano meta_alfabetizacao_uf "81 linhas"
        mun_ano municipio "24k linhas"
        uf_ano uf "145 linhas"
    }
    br_inep_censo_educacao_superior {
        mun_uf_ies_ano curso "3.9M linhas"
        sem_chave dicionario "43 linhas"
        mun_uf_cep_ies_ano ies "39.4k linhas"
    }
    br_inep_censo_escolar {
        sem_chave dicionario "375 linhas"
        mun_uf_cnpj_escola_ies_ano escola "4.1M linhas"
        mun_uf_escola_ano turma "39.1M linhas"
    }
    br_inep_educacao_especial {
        ano brasil_distorcao_idade_serie "45 linhas"
        ano brasil_taxa_rendimento "45 linhas"
        uf_ano distorcao_idade_serie "1.2k linhas"
        mun_uf_ano docente_aee "16.7k linhas"
        mun_uf_ano docente_formacao "230.4k linhas"
        mun_uf_ano etapa_ensino "2.8M linhas"
        mun_uf_ano faixa_etaria "1.2M linhas"
        mun_uf_ano localizacao "1.6M linhas"
        uf_ano matricula_aee "216 linhas"
        mun_uf_ano sexo_raca_cor "2.4M linhas"
        uf_ano taxa_rendimento "1.2k linhas"
        mun_uf_ano tempo_ensino "1.6M linhas"
        mun_uf_ano tipo_deficiencia "2.4M linhas"
        uf_ano uf_distorcao_idade_serie "1.2k linhas"
        uf_ano uf_taxa_rendimento "1.2k linhas"
    }
```

**2/3**

```mermaid
erDiagram
    MUNICIPIO ||--o{ br_inep_enem : "id_municipio_prova +2"
    UF ||--o{ br_inep_enem : "sigla_uf_prova +3"
    UF ||--o{ br_inep_formacao_docente : "sigla_uf"
    ESCOLA ||--o{ br_inep_ideb : "id_escola"
    MUNICIPIO ||--o{ br_inep_ideb : "id_municipio"
    UF ||--o{ br_inep_ideb : "sigla_uf"
    ESCOLA ||--o{ br_inep_indicador_nivel_socioeconomico : "id_escola"
    MUNICIPIO ||--o{ br_inep_indicador_nivel_socioeconomico : "id_municipio"
    UF ||--o{ br_inep_indicador_nivel_socioeconomico : "sigla_uf"
    ESCOLA ||--o{ br_inep_indicadores_educacionais : "id_escola"
    MUNICIPIO ||--o{ br_inep_indicadores_educacionais : "id_municipio"
    UF ||--o{ br_inep_indicadores_educacionais : "sigla_uf"
    br_inep_enem {
        sem_chave dicionario "13.1k linhas"
        mun_uf_ano microdados "108.1M linhas"
        sem_chave questionario_socioeconomico_1998 "150.9k linhas"
        sem_chave questionario_socioeconomico_1999 "309k linhas"
        sem_chave questionario_socioeconomico_2000 "378.4k linhas"
        sem_chave questionario_socioeconomico_2001 "1.6M linhas"
        sem_chave questionario_socioeconomico_2002 "1.8M linhas"
        sem_chave questionario_socioeconomico_2003 "1.9M linhas"
        sem_chave questionario_socioeconomico_2004 "1.5M linhas"
        sem_chave questionario_socioeconomico_2005 "3M linhas"
        sem_chave questionario_socioeconomico_2006 "3.7M linhas"
        sem_chave questionario_socioeconomico_2007 "3.6M linhas"
        sem_chave questionario_socioeconomico_2008 "4M linhas"
        sem_chave questionario_socioeconomico_2009 "4.1M linhas"
        sem_chave questionario_socioeconomico_2010 "4.6M linhas"
        sem_chave questionario_socioeconomico_2011 "5.4M linhas"
        sem_chave questionario_socioeconomico_2012 "5.8M linhas"
        sem_chave questionario_socioeconomico_2013 "7.2M linhas"
        sem_chave questionario_socioeconomico_2014 "8.7M linhas"
        sem_chave questionario_socioeconomico_2015 "7.7M linhas"
        sem_chave questionario_socioeconomico_2016 "8.6M linhas"
        sem_chave questionario_socioeconomico_2017 "6.7M linhas"
        sem_chave questionario_socioeconomico_2018 "5.5M linhas"
        sem_chave questionario_socioeconomico_2019 "5.1M linhas"
        sem_chave questionario_socioeconomico_2020 "5.8M linhas"
        sem_chave questionario_socioeconomico_2021 "3.4M linhas"
        sem_chave questionario_socioeconomico_2022 "3.5M linhas"
        sem_chave questionario_socioeconomico_2023 "3.9M linhas"
    }
    br_inep_formacao_docente {
        ano brasil "5k linhas"
        sem_chave dicionario "25 linhas"
        ano regiao "25.2k linhas"
        uf_ano uf "133.8k linhas"
    }
    br_inep_ideb {
        ano brasil "140 linhas"
        mun_uf_escola_ano escola "1.2M linhas"
        mun_uf_ano municipio "324k linhas"
        ano regiao "550 linhas"
        uf_ano uf "3k linhas"
    }
    br_inep_indicador_nivel_socioeconomico {
        ano brasil "63 linhas"
        sem_chave dicionario "55 linhas"
        mun_uf_escola_ano escola "355.6k linhas"
        mun_uf_ano municipio "169.3k linhas"
        uf_ano uf "3.4k linhas"
    }
    br_inep_indicadores_educacionais {
        ano brasil "360 linhas"
        ano brasil_remuneracao_docentes "120 linhas"
        ano brasil_taxa_transicao "120 linhas"
        mun_escola_ano escola "3.3M linhas"
        mun_escola_ano escola_nivel_socioeconomico "136.8k linhas"
        mun_ano municipio "1.3M linhas"
        mun_ano municipio_taxa_transicao "357.7k linhas"
        ano regiao "1.8k linhas"
        ano regiao_taxa_transicao "600 linhas"
        uf_ano uf "9k linhas"
        uf_ano uf_remuneracao_docentes "1.9k linhas"
        uf_ano uf_taxa_transicao "2k linhas"
    }
```

**3/3**

```mermaid
erDiagram
    ESCOLA ||--o{ br_inep_saeb : "id_escola"
    MUNICIPIO ||--o{ br_inep_saeb : "id_municipio"
    UF ||--o{ br_inep_saeb : "sigla_uf"
    MUNICIPIO ||--o{ br_inep_sinopse_estatistica_educacao_basica : "id_municipio"
    UF ||--o{ br_inep_sinopse_estatistica_educacao_basica : "sigla_uf"
    IES ||--o{ br_mec_sisu : "id_ies"
    MUNICIPIO ||--o{ br_mec_sisu : "id_municipio_campus +1"
    PESSOA_CPF ||--o{ br_mec_sisu : "cpf"
    UF ||--o{ br_mec_sisu : "sigla_uf_ies +2"
    ESCOLA ||--o{ br_simet_educacao_conectada : "id_escola"
    MUNICIPIO ||--o{ br_simet_educacao_conectada : "id_municipio"
    UF ||--o{ br_simet_educacao_conectada : "sigla_uf"
    MUNICIPIO ||..o{ world_oecd_pisa : "wle_intercultural_communication_awareness"
    br_inep_saeb {
        mun_uf_escola_ano aluno_ef_2ano "305.4k linhas"
        mun_uf_escola_ano_mes aluno_ef_5ano "47.1M linhas"
        mun_uf_escola_ano_mes aluno_ef_9ano "54.6M linhas"
        mun_uf_escola_ano aluno_em_34ano "2.9M linhas"
        ano brasil "856 linhas"
        ano brasil_taxa_alfabetizacao "63 linhas"
        sem_chave dicionario "6.6k linhas"
        mun_uf_ano municipio "2M linhas"
        mun_uf_escola_ano proficiencia "94M linhas"
        uf_ano uf "20.1k linhas"
        uf_ano uf_taxa_alfabetizacao "1.5k linhas"
    }
    br_inep_sinopse_estatistica_educacao_basica {
        sem_chave dicionario "88 linhas"
        mun_uf_ano docente_deficiencia "1.3M linhas"
        mun_uf_ano docente_escolaridade "7.7M linhas"
        mun_uf_ano docente_etapa_ensino "15M linhas"
        mun_uf_ano docente_faixa_etaria_sexo "15.4M linhas"
        mun_uf_ano docente_localizacao "17.8M linhas"
        mun_uf_ano docente_regime_contrato "10M linhas"
        mun_uf_ano educacao_especial_etapa_ensino "2.6M linhas"
        mun_uf_ano educacao_especial_faixa_etaria "1.1M linhas"
        mun_uf_ano educacao_especial_localizacao "1.5M linhas"
        mun_uf_ano educacao_especial_sexo_raca_cor "2.2M linhas"
        mun_uf_ano educacao_especial_tempo_ensino "1.5M linhas"
        mun_uf_ano educacao_especial_tipo_deficiencia "2.3M linhas"
        mun_uf_ano etapa_ensino_serie "9.2M linhas"
        mun_uf_ano faixa_etaria "3.6M linhas"
        mun_uf_ano localizacao "7.2M linhas"
        mun_uf_ano sexo_raca_cor "10.6M linhas"
        mun_uf_ano tempo_ensino "5.6M linhas"
    }
    br_mec_prouni {
        sem_chave dicionario "20 linhas"
    }
    br_mec_sisu {
        mun_uf_cpf_ies_ano microdados "34.7M linhas"
    }
    br_simet_educacao_conectada {
        mun_uf_escola_ano escola "137.9k linhas"
    }
    world_iea_pirls {
        sem_chave dictionary "7.7k linhas"
        sem_chave home_context "413.4k linhas"
        sem_chave school_context "14k linhas"
        sem_chave student_achievement "413.4k linhas"
        sem_chave student_context "413.4k linhas"
        sem_chave student_teacher_link "414.7k linhas"
        sem_chave teacher_context "21.6k linhas"
        sem_chave within_country_scoring_reliability "243.7k linhas"
    }
    world_iea_timss {
        sem_chave dictionary "4.4k linhas"
        sem_chave home_context_grade_4 "396k linhas"
        sem_chave school_context_grade_4 "13k linhas"
        sem_chave school_context_grade_8 "9.4k linhas"
        sem_chave student_achievement_grade_4 "396k linhas"
        sem_chave student_achievement_grade_8 "323.9k linhas"
        sem_chave student_context_grade_4 "396k linhas"
        sem_chave student_context_grade_8 "323.9k linhas"
        sem_chave teacher_context_grade_4 "27.1k linhas"
        sem_chave teacher_mathematics_grade_8 "15.1k linhas"
        sem_chave teacher_science_grade_8 "24.9k linhas"
    }
    world_oecd_pisa {
        mun student "1.7M linhas"
    }
```

## Trabalho, empresas e economia

40 datasets · 117 tabelas

**1/2**

```mermaid
erDiagram
    CEP ||--o{ br_anp_combustiveis : "cep"
    EMPRESA_CNPJ ||--o{ br_anp_combustiveis : "cnpj"
    MUNICIPIO ||..o{ br_anp_combustiveis : "municipio"
    UF ||..o{ br_anp_combustiveis : "estado"
    EMPRESA_CNPJ ||--o{ br_anp_precos_combustiveis : "cnpj_revenda"
    MUNICIPIO ||--o{ br_anp_precos_combustiveis : "id_municipio"
    UF ||--o{ br_anp_precos_combustiveis : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_bcb_estban : "cnpj_basico +1"
    MUNICIPIO ||--o{ br_bcb_estban : "id_municipio"
    UF ||--o{ br_bcb_estban : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_bcb_sicor : "cnpj +5"
    FUNCAO_PROGRAMA ||--o{ br_bcb_sicor : "id_programa"
    MUNICIPIO ||--o{ br_bcb_sicor : "id_municipio"
    PESSOA_CPF ||--o{ br_bcb_sicor : "cpf"
    UF ||--o{ br_bcb_sicor : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_bndes_operacoes_contratadas : "cnpj_cliente +1"
    MUNICIPIO ||--o{ br_bndes_operacoes_contratadas : "id_municipio"
    UF ||--o{ br_bndes_operacoes_contratadas : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_brasilio_holdings : "cnpj +1"
    UF ||..o{ br_caixa_sinapi : "uf"
    MUNICIPIO ||--o{ br_clp_ranking_competitividade : "id_municipio"
    UF ||--o{ br_clp_ranking_competitividade : "sigla_uf"
    CEP ||--o{ br_cvm_administradores_carteira : "cep"
    EMPRESA_CNPJ ||--o{ br_cvm_administradores_carteira : "cnpj"
    MUNICIPIO ||..o{ br_cvm_administradores_carteira : "municipio"
    UF ||--o{ br_cvm_administradores_carteira : "sigla_uf"
    EMPRESA_CNPJ ||..o{ br_cvm_fundos : "CNPJ_ADMIN +5"
    PESSOA_CPF ||..o{ br_cvm_fundos : "CPF_CNPJ_GESTOR"
    EMPRESA_CNPJ ||--o{ br_cvm_oferta_publica_distribuicao : "cnpj_lider +2"
    MUNICIPIO ||..o{ br_cvm_oferta_publica_distribuicao : "data_comunicado +1"
    UF ||..o{ br_datahackers_state_data : "p1_i_1"
    MUNICIPIO ||--o{ br_firjan_ifgf : "id_municipio"
    UF ||--o{ br_firjan_ifgf : "sigla_uf"
    CID10 ||..o{ br_ibge_inpc : "categoria"
    MUNICIPIO ||--o{ br_ibge_inpc : "id_municipio"
    UF ||--o{ br_ibge_inpc : "sigla_uf"
    CID10 ||..o{ br_ibge_ipca : "categoria"
    MUNICIPIO ||--o{ br_ibge_ipca : "id_municipio"
    UF ||--o{ br_ibge_ipca : "sigla_uf"
    CID10 ||..o{ br_ibge_ipca15 : "categoria"
    MUNICIPIO ||--o{ br_ibge_ipca15 : "id_municipio"
    UF ||--o{ br_ibge_ipca15 : "sigla_uf"
    MUNICIPIO ||--o{ br_ibge_pam : "id_municipio"
    UF ||--o{ br_ibge_pam : "sigla_uf"
    MUNICIPIO ||--o{ br_ibge_pevs : "id_municipio"
    br_anp_combustiveis {
        mun_uf_cep_cnpj precos "2M linhas"
    }
    br_anp_precos_combustiveis {
        mun_uf_cnpj_ano microdados "16.4M linhas"
    }
    br_bcb_estban {
        mun_uf_cnpj_ano_mes agencia "443.8M linhas"
        sem_chave dicionario "228 linhas"
        mun_uf_cnpj_ano_mes municipio "256.2M linhas"
    }
    br_bcb_sgs {
        sem_chave series "24.9k linhas"
    }
    br_bcb_sicor {
        sem_chave dicionario "816 linhas"
        sem_chave empreendimento "6.6k linhas"
        ano_mes liberacao "21M linhas"
        uf_cnpj_funcprog_ano_mes operacao "27.2M linhas"
        ano_mes operacoes_desclassificadas "12.7k linhas"
        mun_cnpj_ano_mes recurso_publico_complemento_operacao "22M linhas"
        cnpj_cpf_funcprog_ano_mes recurso_publico_cooperado "228.3k linhas"
        ano_mes recurso_publico_gleba "7.3M linhas"
        cnpj_cpf_ano_mes recurso_publico_mutuario "17.1M linhas"
        cnpj_cpf_ano_mes recurso_publico_propriedade "26.6M linhas"
        ano_mes saldo "638.3M linhas"
    }
    br_bndes_operacoes_contratadas {
        mun_uf_cnpj operacoes_nao_automaticas "23.5k linhas"
    }
    br_brasilio_holdings {
        cnpj holdings "515.2k linhas"
    }
    br_caixa_sinapi {
        uf_mes insumos "2M linhas"
    }
    br_caixa_sorteios {
        sem_chave megasena "15.3k linhas"
    }
    br_clp_ranking_competitividade {
        mun_uf_ano nota_geral_municipio "7.1k linhas"
        uf_ano nota_geral_uf "2.4k linhas"
    }
    br_cvm_administradores_carteira {
        sem_chave pessoa_fisica "6.6k linhas"
        mun_uf_cep_cnpj pessoa_juridica "3k linhas"
        cnpj responsavel "6.5k linhas"
    }
    br_cvm_fundos {
        cnpj_cpf fundos "46.8k linhas"
    }
    br_cvm_oferta_publica_distribuicao {
        mun_cnpj dia "27.5k linhas"
    }
    br_datahackers_state_data {
        uf microdados "4.3k linhas"
    }
    br_fgv_igp {
        ano_mes igp_10_mes "359 linhas"
        ano igp_di_ano "78 linhas"
        ano_mes igp_di_mes "954 linhas"
        ano igp_m_ano "33 linhas"
        ano_mes igp_m_mes "407 linhas"
        ano igp_og_ano "53 linhas"
        ano_mes igp_og_mes "652 linhas"
    }
    br_fipe_veiculos {
        sem_chave precos "11.3k linhas"
    }
    br_firjan_ifgf {
        mun_uf_ano ranking "55.7k linhas"
    }
    br_ibge_inpc {
        ano_mes mes_brasil "558 linhas"
        cid_ano_mes mes_categoria_brasil "30.4k linhas"
        mun_uf_cid_ano_mes mes_categoria_municipio "273.6k linhas"
        uf_cid_ano_mes mes_categoria_rm "304k linhas"
    }
    br_ibge_ipca {
        ano_mes mes_brasil "549 linhas"
        cid_ano_mes mes_categoria_brasil "31.1k linhas"
        mun_uf_cid_ano_mes mes_categoria_municipio "279.7k linhas"
        uf_cid_ano_mes mes_categoria_rm "310.8k linhas"
    }
    br_ibge_ipca15 {
        ano_mes mes_brasil "302 linhas"
        cid_ano_mes mes_categoria_brasil "29.9k linhas"
        mun_uf_cid_ano_mes mes_categoria_municipio "59.9k linhas"
        uf_cid_ano_mes mes_categoria_rm "269.5k linhas"
    }
    br_ibge_ipp {
        ano_mes mes_categoria_economica "495 linhas"
        ano_mes mes_grupo_industrial "897 linhas"
        ano_mes mes_industria_atividade "3.4k linhas"
        ano_mes mes_industria_extrativa "147 linhas"
        ano_mes mes_industria_geral "99 linhas"
        ano_mes mes_industria_transformacao "99 linhas"
    }
    br_ibge_pam {
        mun_uf_ano lavoura_permanente "10.7M linhas"
        mun_uf_ano lavoura_temporaria "9.4M linhas"
    }
    br_ibge_pevs {
        mun_ano producao_extracao_vegetal "463.8k linhas"
        mun_ano producao_silvicultura "94.6k linhas"
    }
```

**2/2**

```mermaid
erDiagram
    MUNICIPIO ||--o{ br_ibge_pib : "id_municipio"
    UF ||--o{ br_ibge_pib : "sigla_uf +1"
    MUNICIPIO ||--o{ br_ibge_ppm : "id_municipio"
    UF ||--o{ br_ibge_ppm : "sigla_uf"
    MUNICIPIO ||--o{ br_mc_indicadores : "id_municipio"
    CBO ||--o{ br_me_caged : "cbo_2002"
    CID10 ||..o{ br_me_caged : "categoria"
    CNAE ||--o{ br_me_caged : "cnae_2_subclasse +1"
    MUNICIPIO ||--o{ br_me_caged : "id_municipio"
    UF ||--o{ br_me_caged : "sigla_uf"
    CNAE ||..o{ br_me_clima_organizacional : "subclasse"
    CNAE ||--o{ br_me_cno : "cnae_2"
    CEP ||--o{ br_me_cnpj : "cep"
    CNAE ||--o{ br_me_cnpj : "cnae_fiscal_principal +1"
    EMPRESA_CNPJ ||--o{ br_me_cnpj : "cnpj +3"
    MUNICIPIO ||--o{ br_me_cnpj : "id_municipio +1"
    PAIS ||--o{ br_me_cnpj : "id_pais"
    PESSOA_CPF ||--o{ br_me_cnpj : "cpf_representante_legal"
    UF ||--o{ br_me_cnpj : "sigla_uf"
    MUNICIPIO ||--o{ br_me_comex_stat : "id_municipio"
    NCM_SH ||--o{ br_me_comex_stat : "id_ncm +1"
    PAIS ||--o{ br_me_comex_stat : "sigla_pais_iso3 +1"
    UF ||--o{ br_me_comex_stat : "sigla_uf +1"
    CBO ||--o{ br_me_rais : "cbo_2002 +1"
    CEP ||--o{ br_me_rais : "cep"
    CNAE ||--o{ br_me_rais : "cnae_2_subclasse +2"
    MUNICIPIO ||--o{ br_me_rais : "id_municipio +1"
    UF ||--o{ br_me_rais : "sigla_uf"
    CNAE ||--o{ br_me_rais_identificada : "cnae_fiscal_principal"
    EMPRESA_CNPJ ||--o{ br_me_rais_identificada : "cnpj_basico"
    MUNICIPIO ||--o{ br_me_rais_identificada : "id_municipio"
    UF ||--o{ br_me_rais_identificada : "sigla_uf"
    UF ||--o{ br_mme_consumo_energia_eletrica : "sigla_uf"
    MUNICIPIO ||--o{ br_rf_arrecadacao : "id_municipio"
    UF ||--o{ br_rf_arrecadacao : "sigla_uf"
    CEP ||--o{ br_rf_cafir : "cep"
    MUNICIPIO ||--o{ br_rf_cafir : "id_municipio"
    UF ||--o{ br_rf_cafir : "sigla_uf"
    CEP ||--o{ br_rf_cno : "cep"
    CID10 ||..o{ br_rf_cno : "categoria"
    CNAE ||--o{ br_rf_cno : "cnae_2_subclasse"
    MUNICIPIO ||--o{ br_rf_cno : "id_municipio"
    PAIS ||--o{ br_rf_cno : "id_pais"
    UF ||--o{ br_rf_cno : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_trase_supply_chain : "cnpj +1"
    MUNICIPIO ||..o{ br_trase_supply_chain : "municipality_id +4"
    PESSOA_CPF ||..o{ br_trase_supply_chain : "cnpj_cpf"
    UF ||..o{ br_trase_supply_chain : "state"
    br_ibge_pib {
        ano brasil_antigo "14 linhas"
        uf_ano gini "520 linhas"
        mun_ano municipio "111.4k linhas"
        mun_ano municipio_antigo "77.9k linhas"
        ano regiao_antigo "70 linhas"
        uf_ano uf "513 linhas"
        uf_ano uf_antigo "378 linhas"
    }
    br_ibge_ppm {
        mun_uf_ano efetivo_rebanhos "1.4M linhas"
        mun_uf_ano producao_aquicultura "87.7k linhas"
        mun_uf_ano producao_origem_animal "759k linhas"
        mun_uf_ano producao_pecuaria "240.3k linhas"
    }
    br_mc_indicadores {
        mun_ano_mes transferencias_municipio "1.1M linhas"
    }
    br_me_caged {
        sem_chave dicionario "5.3k linhas"
        mun_uf_cnae_cbo_cid_ano_mes microdados_movimentacao "232.2M linhas"
        mun_uf_cnae_cbo_cid_ano_mes microdados_movimentacao_excluida "515k linhas"
        mun_uf_cnae_cbo_cid_ano_mes microdados_movimentacao_fora_prazo "8M linhas"
    }
    br_me_clima_organizacional {
        cnae microdados "16.4k linhas"
    }
    br_me_cno {
        sem_chave dicionario "19 linhas"
        cnae microdados_cnae "911.4k linhas"
        sem_chave microdados_vinculo "109.4k linhas"
    }
    br_me_cnpj {
        sem_chave dicionario "853 linhas"
        cnpj_ano_mes empresas "2.4B linhas"
        mun_uf_cep_cnpj_cnae_pais_ano_mes estabelecimentos "2.5B linhas"
        cnpj simples "47.7M linhas"
        cnpj_cpf_pais_ano_mes socios "1B linhas"
    }
    br_me_comex_stat {
        sem_chave dicionario "1.7k linhas"
        mun_uf_ncm_pais_ano_mes municipio_exportacao "21.5M linhas"
        mun_uf_ncm_pais_ano_mes municipio_importacao "33.3M linhas"
        uf_ncm_pais_ano_mes ncm_exportacao "30.3M linhas"
        uf_ncm_pais_ano_mes ncm_importacao "44.4M linhas"
    }
    br_me_exportadoras_importadoras {
        sem_chave dicionario "3 linhas"
    }
    br_me_rais {
        sem_chave dicionario "6.9k linhas"
        mun_uf_cep_cnae_ano microdados_estabelecimentos "231.8M linhas"
        mun_uf_cnae_cbo_ano_mes microdados_vinculos "2.1B linhas"
    }
    br_me_rais_identificada {
        mun_uf_cnpj_cnae_ano estabelecimentos "36.2M linhas"
    }
    br_me_sic {
        sem_chave dicionario "647 linhas"
        ano_mes transferencia "29.4k linhas"
    }
    br_mme_consumo_energia_eletrica {
        uf_ano_mes uf "38.9k linhas"
    }
    br_rf_arrecadacao {
        ano_mes cnae "2.5k linhas"
        ano_mes ir_ipi "408 linhas"
        mun_uf_ano_mes itr "516.4k linhas"
        ano_mes natureza_juridica "8.2k linhas"
        uf_ano_mes uf "7.9k linhas"
    }
    br_rf_cafir {
        sem_chave dicionario "30 linhas"
        mun_uf_cep imoveis_rurais "169.9M linhas"
    }
    br_rf_cno {
        cid areas "679.1M linhas"
        cnae cnaes "579.1M linhas"
        sem_chave dicionario "40 linhas"
        mun_uf_cep_pais microdados "534.1M linhas"
        sem_chave vinculos "63.9M linhas"
    }
    br_trase_supply_chain {
        mun beef "1.5M linhas"
        mun_uf beef_slaughterhouses "7.7k linhas"
        mun soy_beans "311.4k linhas"
        mun_uf_cnpj soy_beans_crushing_facilities "973 linhas"
        mun_uf soy_beans_refining_facilities "504 linhas"
        mun_uf_cnpj_cpf soy_beans_storage_facilities "3.2k linhas"
        mun_uf_cnpj_cpf soy_beans_storage_facilities_original "3.2k linhas"
    }
```

## Governo, orçamento e compras

31 datasets · 107 tabelas

**1/2**

```mermaid
erDiagram
    CID10 ||..o{ br_ba_feiradesantana_camara_leis : "categoria"
    MUNICIPIO ||--o{ br_cgu_beneficios_cidadao : "id_municipio"
    PESSOA_CPF ||--o{ br_cgu_beneficios_cidadao : "cpf_favorecido +3"
    UF ||--o{ br_cgu_beneficios_cidadao : "sigla_uf"
    EMPRESA_CNPJ ||--o{ br_cgu_cartao_pagamento : "cnpj_cpf_favorecido"
    ORGAO ||--o{ br_cgu_cartao_pagamento : "codigo_orgao +1"
    PESSOA_CPF ||--o{ br_cgu_cartao_pagamento : "cpf_portador"
    UNIDADE_GESTORA ||--o{ br_cgu_cartao_pagamento : "codigo_unidade_gestora"
    MUNICIPIO ||--o{ br_cgu_dados_abertos : "id_municipio"
    UF ||--o{ br_cgu_dados_abertos : "sigla_uf"
    MUNICIPIO ||--o{ br_cgu_ebt : "id_municipio"
    UF ||--o{ br_cgu_ebt : "sigla_uf"
    MUNICIPIO ||--o{ br_cgu_fef : "id_municipio"
    UF ||--o{ br_cgu_fef : "sigla_uf"
    MUNICIPIO ||..o{ br_cgu_garantia_safra : "nome_municipio +1"
    UF ||..o{ br_cgu_garantia_safra : "uf"
    EMPRESA_CNPJ ||..o{ br_cgu_licitacao_contrato : "cpf_cnpj_vencedor +2"
    MUNICIPIO ||--o{ br_cgu_licitacao_contrato : "id_municipio"
    ORGAO ||--o{ br_cgu_licitacao_contrato : "id_orgao +1"
    PESSOA_CPF ||..o{ br_cgu_licitacao_contrato : "cpf_cnpj_vencedor +2"
    UF ||--o{ br_cgu_licitacao_contrato : "sigla_uf"
    UNIDADE_GESTORA ||--o{ br_cgu_licitacao_contrato : "id_unidade_gestora +1"
    FUNCAO_PROGRAMA ||--o{ br_cgu_orcamento_publico : "id_funcao +3"
    ORGAO ||--o{ br_cgu_orcamento_publico : "id_orgao_superior +1"
    UNIDADE_GESTORA ||--o{ br_cgu_orcamento_publico : "id_unidade_orcamentaria"
    MUNICIPIO ||..o{ br_cgu_pe_de_meia : "nome_municipio +1"
    PESSOA_CPF ||--o{ br_cgu_pe_de_meia : "cpf_responsavel +1"
    UF ||..o{ br_cgu_pe_de_meia : "uf"
    ORGAO ||--o{ br_cgu_receitas_publicas : "id_orgao +1"
    UNIDADE_GESTORA ||--o{ br_cgu_receitas_publicas : "codigo_unidade_gestora"
    MUNICIPIO ||..o{ br_cgu_seguro_defeso : "nome_municipio +1"
    PESSOA_CPF ||--o{ br_cgu_seguro_defeso : "cpf_favorecido"
    UF ||..o{ br_cgu_seguro_defeso : "uf"
    PESSOA_CPF ||--o{ br_cgu_servidores_executivo_federal : "cpf +2"
    UF ||--o{ br_cgu_servidores_executivo_federal : "sigla_uf"
    ORGAO ||--o{ br_cgu_viagens : "codigo_orgao_solicitante"
    PESSOA_CPF ||--o{ br_cgu_viagens : "cpf_viajante"
    UF ||..o{ br_cgu_viagens : "origem_uf +1"
    NCM_SH ||..o{ br_comprasgov_catmatcatser : "codigo_ncm +1"
    CNAE ||..o{ br_comprasgov_sicaf : "codigoCnae"
    EMPRESA_CNPJ ||--o{ br_comprasgov_sicaf : "cnpj"
    MUNICIPIO ||..o{ br_comprasgov_sicaf : "nomeMunicipio"
    PESSOA_CPF ||--o{ br_comprasgov_sicaf : "cpf"
    UF ||..o{ br_comprasgov_sicaf : "ufSigla"
    br_ba_feiradesantana_camara_leis {
        cid microdados "6k linhas"
    }
    br_cgu_beneficios_cidadao {
        mun_uf_cpf_ano_mes auxilio_brasil "294M linhas"
        mun_uf_cpf_ano_mes auxilio_brasil_original "294M linhas"
        mun_uf_cpf_ano_mes auxilio_emergencial "491.1M linhas"
        mun_uf_cpf_ano_mes auxilio_emergencial_original "491.1M linhas"
        mun_uf_cpf_ano_mes bolsa_familia_pagamento "1.5B linhas"
        mun_uf_cpf_ano_mes bolsa_familia_pagamento_original "1.5B linhas"
        mun_uf_cpf_ano_mes bpc "419.9M linhas"
        mun_uf_cpf_ano_mes bpc_original "419.9M linhas"
        mun_uf_ano_mes garantia_safra "32.5M linhas"
        mun_uf_cpf_ano_mes novo_bolsa_familia "588.5M linhas"
        mun_uf_cpf_ano_mes novo_bolsa_familia_original "588.5M linhas"
    }
    br_cgu_cartao_pagamento {
        sem_chave dicionario "43 linhas"
        cnpj_cpf_orgao_ug_ano_mes microdados_compras_centralizadas "1.3M linhas"
        cnpj_cpf_orgao_ug_ano_mes microdados_defesa_civil "126.1k linhas"
        cnpj_cpf_orgao_ug_ano_mes microdados_governo_federal "1.7M linhas"
    }
    br_cgu_dados_abertos {
        sem_chave conjunto "12.7k linhas"
        mun_uf organizacao "254 linhas"
        sem_chave recurso "76.8k linhas"
    }
    br_cgu_ebt {
        mun_uf_ano municipio "1.3k linhas"
        uf_ano uf "54 linhas"
    }
    br_cgu_fef {
        mun_uf_ano microdados "82.7k linhas"
        mun_uf municipios_sorteados "2.2k linhas"
        sem_chave sorteio "40 linhas"
    }
    br_cgu_garantia_safra {
        mun_uf_mes garantia_safra "33.5M linhas"
    }
    br_cgu_licitacao_contrato {
        orgao_ug_ano_mes contrato_apostilamento "9.7k linhas"
        cnpj_cpf_orgao_ug_ano_mes contrato_compra "472.6k linhas"
        orgao_ano_mes contrato_item "1.5M linhas"
        orgao_ano_mes contrato_termo_aditivo "423.9k linhas"
        mun_uf_orgao_ug_ano_mes licitacao "1.7M linhas"
        ug_ano_mes licitacao_empenho "7.4M linhas"
        cnpj_cpf_orgao_ug_ano_mes licitacao_item "14.1M linhas"
        cnpj_cpf_orgao_ug_ano_mes licitacao_participante "74.4M linhas"
    }
    br_cgu_orcamento_publico {
        orgao_ug_funcprog_ano orcamento "289.4k linhas"
    }
    br_cgu_pe_de_meia {
        mun_uf_cpf_mes pe_de_meia "64M linhas"
    }
    br_cgu_receitas_publicas {
        orgao_ug_ano receitas "1.5M linhas"
    }
    br_cgu_seguro_defeso {
        mun_uf_cpf_mes seguro_defeso "42.1M linhas"
    }
    br_cgu_servidores_executivo_federal {
        cpf_ano_mes afastamentos "7.7M linhas"
        cpf_ano_mes afastamentos_original "7.7M linhas"
        cpf_ano_mes cadastro_aposentados "28.2M linhas"
        cpf_ano_mes cadastro_aposentados_original "28.2M linhas"
        cpf_ano_mes cadastro_pensionistas "32.8M linhas"
        cpf_ano_mes cadastro_pensionistas_original "32.8M linhas"
        cpf_ano_mes cadastro_reserva_reforma_militares "11M linhas"
        cpf_ano_mes cadastro_reserva_reforma_militares_original "11M linhas"
        uf_cpf_ano_mes cadastro_servidores "168.1M linhas"
        uf_cpf_ano_mes cadastro_servidores_original "168.1M linhas"
        cpf_ano_mes observacoes "23.3M linhas"
        cpf_ano_mes observacoes_original "23.3M linhas"
        cpf_ano_mes remuneracao "155.4M linhas"
        cpf_ano_mes remuneracao_original "155.4M linhas"
    }
    br_cgu_viagens {
        sem_chave pagamento "16.7M linhas"
        sem_chave passagem "5.2M linhas"
        uf trecho "20.9M linhas"
        cpf_orgao viagem "9.9M linhas"
    }
    br_comprasgov_catmatcatser {
        ncm materiais "247.9k linhas"
        sem_chave servicos "3k linhas"
    }
    br_comprasgov_sicaf {
        mun_uf_cnpj_cpf_cnae fornecedores "957.9k linhas"
    }
    br_me_estoque_divida_publica {
        ano_mes microdados "124.4k linhas"
    }
    br_me_siape {
        sem_chave servidores_executivo_federal "358.9k linhas"
    }
```

**2/2**

```mermaid
erDiagram
    MUNICIPIO ||--o{ br_me_siconfi : "id_municipio"
    UF ||--o{ br_me_siconfi : "sigla_uf +1"
    UF ||--o{ br_mp_pep : "sigla_uf"
    MUNICIPIO ||..o{ br_ok_queridodiario : "territory_id +1"
    UF ||..o{ br_ok_queridodiario : "state_code"
    MUNICIPIO ||..o{ br_siop_orcamento : "MunicÃ­pio"
    UF ||..o{ br_siop_orcamento : "UF"
    CID10 ||..o{ br_tce_es : "categoria"
    EMPRESA_CNPJ ||..o{ br_tce_es : "EmpresaCNPJ"
    MUNICIPIO ||..o{ br_tce_es : "Municipio"
    MUNICIPIO ||..o{ br_tce_pi : "codIBGE +1"
    UF ||..o{ br_tce_pi : "sigla"
    EMPRESA_CNPJ ||..o{ br_tce_rj : "CPFCNPJ +1"
    MUNICIPIO ||..o{ br_tce_rj : "Ente"
    PESSOA_CPF ||..o{ br_tce_rj : "CPFCNPJ +1"
    MUNICIPIO ||..o{ br_tce_sp : "municipio +1"
    MUNICIPIO ||..o{ br_tesouro_capag : "Nome_Município +1"
    UF ||..o{ br_tesouro_capag : "UF"
    EMPRESA_CNPJ ||--o{ br_transferegov : "cnpj_fundo_programa +7"
    FUNCAO_PROGRAMA ||--o{ br_transferegov : "id_programa"
    ORGAO ||--o{ br_transferegov : "id_orgao_superior_programa +1"
    UNIDADE_GESTORA ||--o{ br_transferegov : "id_unidade_gestora_programa"
    br_me_siconfi {
        ano brasil_despesas_funcao "9.5k linhas"
        ano brasil_despesas_orcamentarias "8.2k linhas"
        ano brasil_execucao_restos_pagar "10.2k linhas"
        ano brasil_execucao_restos_pagar_funcao "13.7k linhas"
        ano brasil_receitas_orcamentarias "6.5k linhas"
        ano brasil_variacoes_patrimoniais "5.7k linhas"
        mun_uf_ano municipio_balanco_patrimonial "14.7M linhas"
        mun_uf_ano municipio_despesas_funcao "21.2M linhas"
        mun_uf_ano municipio_despesas_orcamentarias "27M linhas"
        mun_uf_ano municipio_receitas_orcamentarias "19.4M linhas"
        uf_ano uf_despesas_funcao "175.9k linhas"
        uf_ano uf_despesas_orcamentarias "134.4k linhas"
        uf_ano uf_execucao_restos_pagar "124.9k linhas"
        uf_ano uf_execucao_restos_pagar_funcao "184.7k linhas"
        uf_ano uf_receitas_orcamentarias "88.1k linhas"
        uf_ano uf_variacoes_patrimoniais "84.8k linhas"
    }
    br_me_siorg {
        sem_chave remuneracao "258 linhas"
    }
    br_mp_pep {
        uf_ano_mes cargos_funcoes "1.8M linhas"
    }
    br_ok_queridodiario {
        mun_uf diarios "231.9k linhas"
    }
    br_siop_orcamento {
        sem_chave alteracoes_orcamentarias "9.8k linhas"
        sem_chave dados "5.6k linhas"
        mun_uf localizadores "8.1k linhas"
        sem_chave planos_orcamentarios "13.5k linhas"
    }
    br_tce_es {
        ano_mes aquisicoes_mensais "130 linhas"
        ano julgamento_contas "11.1k linhas"
        cid_ano lista_responsaveis "778 linhas"
        mun_cnpj obras_publicas "250 linhas"
        ano resultados_fiscalizacoes "156 linhas"
    }
    br_tce_pi {
        sem_chave despesas_total "17 linhas"
        sem_chave licitacoes_estado "18 linhas"
        uf orgaos "130 linhas"
        mun prefeituras "224 linhas"
        sem_chave receitas_total "17 linhas"
    }
    br_tce_rj {
        cnpj_cpf_ano contratos_estado "36.6k linhas"
        mun_cnpj_cpf_ano contratos_municipio "96.4k linhas"
        mun_ano_mes convenios_estado "2.8k linhas"
        mun gastos_com_pessoal "2.6k linhas"
        mun_ano_mes licitacoes "40.1k linhas"
        ano penalidades_ressarcimento_estado "948 linhas"
    }
    br_tce_sp {
        mun municipios "644 linhas"
    }
    br_tce_to {
        sem_chave pautas "50 linhas"
    }
    br_tcu_dadosabertos {
        ano dados "36.5k linhas"
    }
    br_tesouro_capag {
        uf estados "247 linhas"
        mun_uf municipios "5.6k linhas"
    }
    br_transferegov {
        cnpj_orgao_funcprog planos_acao "26k linhas"
        cnpj_orgao_ug_funcprog_ano programas "129 linhas"
        cnpj_ano transferencias "4.2k linhas"
    }
```

## Política e eleições

6 datasets · 60 tabelas

```mermaid
erDiagram
    EMPRESA_CNPJ ||--o{ br_camara_dados_abertos : "cnpj_cpf_fornecedor"
    MUNICIPIO ||--o{ br_camara_dados_abertos : "id_municipio_nascimento"
    PARTIDO ||--o{ br_camara_dados_abertos : "sigla_partido"
    PESSOA_CPF ||--o{ br_camara_dados_abertos : "cpf"
    UF ||--o{ br_camara_dados_abertos : "sigla_uf +3"
    FUNCAO_PROGRAMA ||--o{ br_cgu_emendas_parlamentares : "id_funcao +3"
    MUNICIPIO ||--o{ br_cgu_emendas_parlamentares : "id_municipio_gasto"
    UF ||--o{ br_cgu_emendas_parlamentares : "sigla_uf_gasto"
    MUNICIPIO ||..o{ br_poder360_pesquisas : "nome_municipio"
    PARTIDO ||--o{ br_poder360_pesquisas : "sigla_partido"
    UF ||--o{ br_poder360_pesquisas : "sigla_uf"
    UF ||..o{ br_senado_dadosabertos : "Sigla +1"
    CEP ||--o{ br_tse_eleicoes : "cep"
    CNAE ||--o{ br_tse_eleicoes : "cnae_2_doador +5"
    EMPRESA_CNPJ ||--o{ br_tse_eleicoes : "cnpj_candidato +1"
    MUNICIPIO ||--o{ br_tse_eleicoes : "id_municipio +4"
    PARTIDO ||--o{ br_tse_eleicoes : "sigla_partido"
    PESSOA_CPF ||--o{ br_tse_eleicoes : "cpf +2"
    UF ||--o{ br_tse_eleicoes : "sigla_uf +3"
    MUNICIPIO ||--o{ br_tse_filiacao_partidaria : "id_municipio +1"
    PARTIDO ||--o{ br_tse_filiacao_partidaria : "sigla_partido"
    PESSOA_CPF ||--o{ br_tse_filiacao_partidaria : "cpf"
    UF ||--o{ br_tse_filiacao_partidaria : "sigla_uf"
    br_camara_dados_abertos {
        mun_uf deputado "15.8k linhas"
        mun_uf_cpf_partido deputado_contato "7.6k linhas"
        uf_ano deputado_ocupacao "74.8k linhas"
        sem_chave deputado_profissao "25.1k linhas"
        uf_cnpj_cpf_partido_ano_mes despesa "4.8M linhas"
        sem_chave evento "121k linhas"
        sem_chave evento_orgao "124.1k linhas"
        sem_chave evento_presenca_deputado "2.7M linhas"
        sem_chave evento_requerimento "42.3k linhas"
        sem_chave frente "2.9k linhas"
        sem_chave frente_deputado "523.7k linhas"
        sem_chave funcionario "26.8k linhas"
        ano legislatura "114 linhas"
        uf_partido legislatura_mesa "310 linhas"
        ano licitacao "9.3k linhas"
        uf_cnpj_cpf_ano licitacao_contrato "2.7k linhas"
        cnpj_cpf_ano licitacao_item "127.1k linhas"
        ano licitacao_pedido "5.6k linhas"
        cnpj_cpf_ano licitacao_proposta "83.3k linhas"
        uf orgao "4.7k linhas"
        uf_partido orgao_deputado "183.7k linhas"
        uf_partido proposicao_autor "3.8M linhas"
        uf_ano proposicao_microdados "910.6k linhas"
        ano proposicao_tema "639.9k linhas"
        sem_chave sigla_partido "143 linhas"
        sem_chave votacao "367.6k linhas"
        ano votacao_objeto "751.1k linhas"
        sem_chave votacao_orientacao_bancada "100.1k linhas"
        uf_partido votacao_parlamentar "1.8M linhas"
        ano votacao_proposicao "135k linhas"
    }
    br_cgu_emendas_parlamentares {
        mun_uf_funcprog_ano microdados "89k linhas"
    }
    br_poder360_pesquisas {
        mun_uf_partido_ano microdados "162.1k linhas"
    }
    br_senado_dadosabertos {
        uf comissoes "220 linhas"
        sem_chave materias "162.1k linhas"
        sem_chave senadores "81 linhas"
        uf_ano votacoes "3.6k linhas"
    }
    br_tse_eleicoes {
        uf_ano bens_candidato "5M linhas"
        mun_uf_cpf_partido_ano candidatos "3.4M linhas"
        mun_uf_cnpj_cpf_cnae_partido_ano despesas_candidato "32.4M linhas"
        mun_uf_ano detalhes_votacao_municipio "337.1k linhas"
        mun_uf_ano detalhes_votacao_municipio_zona "375.7k linhas"
        mun_uf_ano detalhes_votacao_secao "24M linhas"
        sem_chave dicionario "92 linhas"
        mun_uf_ano partidos "1.2M linhas"
        mun_uf_cep_ano perfil_eleitorado_local_votacao "6M linhas"
        mun_uf_ano perfil_eleitorado_municipio_zona "40.9M linhas"
        mun_uf_ano perfil_eleitorado_secao "588.5M linhas"
        mun_uf_cnpj_cpf_cnae_partido_ano receitas_candidato "15.3M linhas"
        mun_uf_cnpj_cpf_cnae_partido_ano receitas_comite "341.7k linhas"
        mun_uf_cnpj_cpf_cnae_partido_ano receitas_orgao_partidario "250.1k linhas"
        mun_uf_partido_ano resultados_candidato "3.1M linhas"
        mun_uf_partido_ano resultados_candidato_municipio "31.7M linhas"
        mun_uf_partido_ano resultados_candidato_municipio_zona "40.1M linhas"
        mun_uf_partido_ano resultados_candidato_secao "505.8M linhas"
        mun_uf_partido_ano resultados_partido_municipio "3.7M linhas"
        mun_uf_partido_ano resultados_partido_municipio_zona "4.2M linhas"
        mun_uf_partido_ano resultados_partido_secao "207.7M linhas"
        mun_uf_ano vagas "102.2k linhas"
    }
    br_tse_filiacao_partidaria {
        mun_uf_cpf_partido microdados "17.2M linhas"
        mun_uf_partido microdados_antigos "24.7M linhas"
    }
```

## Justiça, segurança e sanções

21 datasets · 52 tabelas

```mermaid
erDiagram
    EMPRESA_CNPJ ||..o{ br_bcb_penalidades : "CPF_CNPJ"
    PESSOA_CPF ||..o{ br_bcb_penalidades : "CPF_CNPJ"
    UF ||--o{ br_cnj_estatisticas_poder_judiciario : "sigla_uf"
    MUNICIPIO ||..o{ br_cnj_improbidade_administrativa : "comunicado_tse"
    UF ||--o{ br_cnj_improbidade_administrativa : "sigla_uf"
    MUNICIPIO ||--o{ br_fbsp_absp : "id_municipio"
    UF ||--o{ br_fbsp_absp : "sigla_uf"
    UF ||..o{ br_mj_consumidorgovbr : "UF"
    EMPRESA_CNPJ ||..o{ br_mjsp_ckan : "NumeroCNPJ +1"
    UF ||..o{ br_mjsp_ckan : "UF"
    UF ||..o{ br_mjsp_procurados : "estado"
    MUNICIPIO ||..o{ br_mjsp_sinesp : "cód_ibge +1"
    UF ||--o{ br_mjsp_sinesp : "sigla_uf"
    CEP ||--o{ br_mjsp_sisdepen : "cep"
    MUNICIPIO ||..o{ br_mjsp_sisdepen : "municipio +5"
    UF ||..o{ br_mjsp_sisdepen : "uf"
    CID10 ||..o{ br_pgfn_dividaativa : "categoria"
    EMPRESA_CNPJ ||..o{ br_pgfn_dividaativa : "CPF_CNPJ"
    PESSOA_CPF ||..o{ br_pgfn_dividaativa : "CPF_CNPJ"
    MUNICIPIO ||--o{ br_rj_isp_estatisticas_seguranca : "id_municipio"
    EMPRESA_CNPJ ||..o{ br_tcu_inidoneos : "CPF_CNPJ"
    MUNICIPIO ||..o{ br_tcu_inidoneos : "MUNICIPIO"
    PESSOA_CPF ||..o{ br_tcu_inidoneos : "CPF +1"
    UF ||..o{ br_tcu_inidoneos : "UF"
    br_bcb_penalidades {
        cnpj_cpf penalidades "16.8k linhas"
    }
    br_cnj_estatisticas_poder_judiciario {
        uf_ano recursos_financeiros "1.2k linhas"
    }
    br_cnj_improbidade_administrativa {
        mun_uf condenacao "53.3k linhas"
    }
    br_fbsp_absp {
        mun_uf_ano municipio "162 linhas"
        uf_ano uf "405 linhas"
        uf_ano violencia_escola "1.9k linhas"
    }
    br_ggb_relatorio_lgbtqi {
        ano brasil "20 linhas"
        ano causa_obito "13 linhas"
        ano grupo_lgbtqia "60 linhas"
        ano local "16 linhas"
        ano raca_cor "36 linhas"
    }
    br_ipea_atlasviolencia {
        sem_chave series "10 linhas"
        ano valores_nacional "182 linhas"
    }
    br_mj_consumidorgovbr {
        uf_ano reclamacoes "10.2M linhas"
    }
    br_mjsp_ckan {
        sem_chave infopen "vazia"
        uf_cnpj_ano procon "13.8k linhas"
    }
    br_mjsp_procurados {
        uf procurados "195 linhas"
    }
    br_mjsp_sinesp {
        mun_uf_mes ocorrencias "823 linhas"
        uf_ano_mes ocorrencias_uf "23k linhas"
    }
    br_mjsp_sisdepen {
        mun_uf_cep_ano populacao_carceraria "38.4k linhas"
    }
    br_pgfn_dividaativa {
        cnpj_cpf_cid divida "46.6M linhas"
    }
    br_rj_isp_estatisticas_seguranca {
        ano_mes armas_apreendidas_mensal "31.4k linhas"
        mun_ano_mes armas_fogo_apreendidas_mensal "6.2k linhas"
        mun_ano_mes evolucao_mensal_cisp "37.5k linhas"
        mun_ano_mes evolucao_mensal_municipio "13.4k linhas"
        ano_mes evolucao_mensal_uf "422 linhas"
        ano_mes evolucao_mensal_upp "8k linhas"
        ano_mes evolucao_policial_morto_servico_mensal "37.5k linhas"
        mun_ano_mes feminicidio_mensal_cisp "16.4k linhas"
        mun relacao_cisp_aisp_risp "147 linhas"
        mun_ano taxa_evolucao_anual_municipio "644 linhas"
        ano taxa_evolucao_anual_uf "33 linhas"
        mun_ano_mes taxa_evolucao_mensal_municipio "12.1k linhas"
        ano_mes taxa_evolucao_mensal_uf "264 linhas"
        ano taxa_letalidade "383 linhas"
    }
    br_stf_corte_aberta {
        ano decisoes "2.7M linhas"
        sem_chave dicionario "47 linhas"
    }
    br_stj_dadosabertos {
        sem_chave documentos "549.2k linhas"
    }
    br_tcu_inidoneos {
        mun_uf_cnpj_cpf empresas "93 linhas"
        mun_uf_cpf inabilitados_funcao_publica "721 linhas"
        mun_uf_cpf resp_contas_julgadas_irreg_implicacao_eleitoral "9.7k linhas"
        mun_uf_cnpj_cpf resp_contas_julgadas_irregulares "34.9k linhas"
    }
    eu_sanctions {
        sem_chave sanctions "42.3k linhas"
    }
    global_icij_offshoreleaks {
        sem_chave addresses "402.2k linhas"
        sem_chave entities "814.3k linhas"
        sem_chave intermediaries "25.6k linhas"
        sem_chave officers "771.3k linhas"
        sem_chave other "3k linhas"
        sem_chave relationships "3.3M linhas"
    }
    global_ofac_sanctions {
        sem_chave sanctions "19.1k linhas"
    }
    global_opensanctions {
        sem_chave entities "1.3M linhas"
    }
    un_sanctions {
        sem_chave sanctions "1k linhas"
    }
```

## Território, ambiente e infraestrutura

21 datasets · 80 tabelas

**1/2**

```mermaid
erDiagram
    MUNICIPIO ||--o{ br_ana_atlas_esgotos : "id_municipio"
    UF ||--o{ br_ana_atlas_esgotos : "sigla_uf"
    MUNICIPIO ||..o{ br_ana_telemetria : "nmMunicipio +1"
    UF ||..o{ br_ana_telemetria : "nmEstado +1"
    EMPRESA_CNPJ ||--o{ br_anatel_banda_larga_fixa : "cnpj"
    MUNICIPIO ||--o{ br_anatel_banda_larga_fixa : "id_municipio"
    UF ||--o{ br_anatel_banda_larga_fixa : "sigla_uf"
    MUNICIPIO ||--o{ br_anatel_indice_brasileiro_conectividade : "id_municipio"
    UF ||--o{ br_anatel_indice_brasileiro_conectividade : "sigla_uf"
    CID10 ||..o{ br_geobr_mapas : "categoria"
    ESCOLA ||--o{ br_geobr_mapas : "id_escola"
    MUNICIPIO ||--o{ br_geobr_mapas : "id_municipio"
    SETOR_CENSITARIO ||--o{ br_geobr_mapas : "id_setor_censitario"
    UF ||--o{ br_geobr_mapas : "sigla_uf +1"
    EMPRESA_CNPJ ||..o{ br_ibama_embargos : "seq_tad;seq_decisao_judicial;dat_decisao_embargo;tipo_decisao;des_observacao;num_pessoa_interessado;interessado;cpf_cnpj_interessado;tipo_acao;dat_inclusao_acao;sit_cancelado;ultima_atualizacao_relatorio +1"
    MUNICIPIO ||..o{ br_ibama_embargos : "seq_tad;seq_hist_tad;dt_alteracao;des_status_formulario;sit_cancelado;num_tad;ser_tad;dat_embargo;dat_impressao;forma_entrega;num_processo;des_tad;cod_municipio;municipio;uf;des_localizacao;num_longitude_tad;num_latitude_tad;deter_prodes;id_poligono;embarga_poligono;qtd_area_embargada;nome_imovel;tipo_area;wkt;unid_apresentacao;unid_controle;sit_desembargo;dat_desembargo;des_desembargo;seq_auto_infracao;seq_notificacao;seq_acao_fiscalizatoria;operacao;seq_ordem_fiscalizacao;ordem_fiscalizacao;unid_ordenadora;seq_solicitacao_recurso;solicitacao_recurso;operacao_sol_recurso;dat_ult_alteracao;tipo_alteracao;justificativa_alteracao;ultima_atualizacao_relatorio +1"
    PESSOA_CPF ||..o{ br_ibama_embargos : "seq_tad;seq_decisao_judicial;dat_decisao_embargo;tipo_decisao;des_observacao;num_pessoa_interessado;interessado;cpf_cnpj_interessado;tipo_acao;dat_inclusao_acao;sit_cancelado;ultima_atualizacao_relatorio +1"
    MUNICIPIO ||--o{ br_inmet_bdmep : "id_municipio"
    MUNICIPIO ||--o{ br_inpe_prodes : "id_municipio"
    MUNICIPIO ||--o{ br_inpe_queimadas : "id_municipio"
    UF ||--o{ br_inpe_queimadas : "sigla_uf"
    MUNICIPIO ||--o{ br_inpe_sisam : "id_municipio"
    UF ||--o{ br_inpe_sisam : "sigla_uf"
    MUNICIPIO ||--o{ br_ipea_acesso_oportunidades : "id_municipio"
    MUNICIPIO ||--o{ br_mapbiomas_estatisticas : "id_municipio"
    UF ||--o{ br_mapbiomas_estatisticas : "sigla_uf"
    MUNICIPIO ||--o{ br_mdr_snis : "id_municipio"
    UF ||--o{ br_mdr_snis : "sigla_uf"
    CID10 ||..o{ br_mma_extincao : "categoria"
    br_ana_atlas_esgotos {
        mun_uf municipio "11.1k linhas"
    }
    br_ana_reservatorios {
        sem_chave sin "2.3M linhas"
    }
    br_ana_telemetria {
        mun_uf estacoes "11.4k linhas"
    }
    br_anac_dadosabertos {
        sem_chave pontualidade "12.9k linhas"
        sem_chave rab "34.6k linhas"
        sem_chave voos "82.1k linhas"
    }
    br_anatel_banda_larga_fixa {
        ano_mes densidade_brasil "384 linhas"
        mun_uf_ano_mes densidade_municipio "2.1M linhas"
        uf_ano_mes densidade_uf "10.4k linhas"
        mun_uf_cnpj_ano_mes microdados "57.8M linhas"
    }
    br_anatel_indice_brasileiro_conectividade {
        mun_uf_ano municipio "44.6k linhas"
    }
    br_geobr_mapas {
        sem_chave amazonia_legal "1 linhas"
        mun area_minima_comparavel_2010 "3.8k linhas"
        mun_uf area_risco_desastre "8.3k linhas"
        mun_uf arranjo_populacional "953 linhas"
        ano bioma "17 linhas"
        mun_uf concentracao_urbana "642 linhas"
        uf_escola escola "222.9k linhas"
        mun_uf_ano estabelecimentos_saude "360.2k linhas"
        mun_uf limite_vizinhanca "14.8k linhas"
        uf mesorregiao "137 linhas"
        uf microrregiao "558 linhas"
        mun_uf municipio "5.6k linhas"
        sem_chave pais "1 linhas"
        mun pegada_urbana "13.7k linhas"
        sem_chave regiao "5 linhas"
        uf regiao_imediata "510 linhas"
        uf regiao_intermediaria "135 linhas"
        mun_uf regiao_metropolitana_2017 "1.4k linhas"
        uf saude "438 linhas"
        mun_uf_ano sede_municipal "29.8k linhas"
        mun_uf semiarido "1.3k linhas"
        mun_uf_setor setor_censitario_2010 "316.5k linhas"
        mun_uf terra_indigena "615 linhas"
        uf uf "27 linhas"
        cid_ano unidade_conservacao "1.9k linhas"
    }
    br_ibama_embargos {
        sem_chave anexo "15.8k linhas"
        sem_chave coordenadas "64.6k linhas"
        cnpj_cpf decisao "439 linhas"
        sem_chave enquadramento "138k linhas"
        sem_chave enquadramento_complementar "13.5k linhas"
        sem_chave itens "48.8k linhas"
        mun_cnpj_cpf termo_embargo "113.9k linhas"
        mun termo_embargo_historico "497.1k linhas"
    }
    br_inmet_bdmep {
        mun estacao "633 linhas"
        ano_mes microdados "84.5M linhas"
    }
    br_inpe_prodes {
        mun_ano municipio_bioma "156.9k linhas"
    }
    br_inpe_queimadas {
        mun_uf_ano_mes microdados "17.8M linhas"
    }
    br_inpe_sisam {
        mun_uf_ano microdados "158.7M linhas"
    }
    br_ipea_acesso_oportunidades {
        mun estatisticas_2019 "336.4k linhas"
    }
    br_mapbiomas_estatisticas {
        sem_chave classe "36 linhas"
        uf_ano cobertura_uf_classe "19k linhas"
        mun_uf_ano transicao_municipio_de_para_decenal "975.1k linhas"
        uf_ano transicao_uf_de_para_anual "169.1k linhas"
        uf_ano transicao_uf_de_para_decenal "17.4k linhas"
        uf_ano transicao_uf_de_para_quinquenal "38.7k linhas"
    }
    br_mdr_snis {
        mun_uf_ano municipio_agua_esgoto "119.3k linhas"
        mun_uf_ano prestador_agua_esgoto "125.8k linhas"
    }
    br_mma_extincao {
        cid fauna_ameacada "1.3k linhas"
        cid flora_ameacada "6.4k linhas"
    }
```

**2/2**

```mermaid
erDiagram
    MUNICIPIO ||--o{ br_mobilidados_indicadores : "id_municipio"
    UF ||--o{ br_mobilidados_indicadores : "sigla_uf"
    CID10 ||..o{ br_seeg_emissoes : "categoria +1"
    MUNICIPIO ||--o{ br_seeg_emissoes : "id_municipio"
    UF ||--o{ br_seeg_emissoes : "sigla_uf"
    MUNICIPIO ||--o{ br_sfb_sicar : "id_municipio"
    UF ||--o{ br_sfb_sicar : "sigla_uf"
    PAIS ||..o{ world_wwf_hydrosheds : "country"
    br_mobilidados_indicadores {
        mun_uf_ano comprometimento_renda_tarifa_transp_publico "351 linhas"
        uf_ano divisao_modal "320 linhas"
        mun_uf_ano emissao_co2_material_particulado "324 linhas"
        mun_uf_ano proporcao_domicilios_infra_urbana "217 linhas"
        mun_uf_ano proporcao_mortes_negras_acidente_transporte "668.4k linhas"
        mun_uf_ano proporcao_pessoas_prox_infra_cicloviaria "378 linhas"
        mun_uf_ano proporcao_pessoas_proximas_pnt "630 linhas"
        mun_uf_ano taxa_motorizacao "486 linhas"
        mun_uf_ano tempo_deslocamento_casa_trabalho "229 linhas"
        mun_uf_ano transporte_media_alta_capacidade "27 linhas"
    }
    br_seeg_emissoes {
        sem_chave dicionario "1.6k linhas"
        mun_uf_cid_ano municipio "165.7M linhas"
        uf_cid_ano uf "17.9M linhas"
    }
    br_sfb_sicar {
        mun_uf area_imovel "79.3M linhas"
        sem_chave dicionario "7 linhas"
    }
    global_ibge_tabua_mares {
        sem_chave estacoes "6 linhas"
        sem_chave previsao "1.3M linhas"
    }
    world_wwf_hydrosheds {
        sem_chave basins_atlas "3.8M linhas"
        pais lakes_atlas "2.9M linhas"
        sem_chave rivers_atlas "8.5M linhas"
    }
```

## Demografia e indicadores sociais

17 datasets · 123 tabelas

**1/3**

```mermaid
erDiagram
    MUNICIPIO ||--o{ br_abrinq_oca : "id_municipio"
    MUNICIPIO ||--o{ br_ibge_censo2022_raca : "id_municipio"
    MUNICIPIO ||--o{ br_ibge_censo2022_religiao : "id_municipio"
    CEP ||--o{ br_ibge_censo_2022 : "cep"
    MUNICIPIO ||--o{ br_ibge_censo_2022 : "id_municipio"
    SETOR_CENSITARIO ||--o{ br_ibge_censo_2022 : "id_setor_censitario"
    UF ||--o{ br_ibge_censo_2022 : "sigla_uf +1"
    br_abrinq_oca {
        mun_ano municipio_primeira_infancia "111.4k linhas"
    }
    br_ce_fortaleza_sefin_iptu {
        ano face_quadra "68.9k linhas"
    }
    br_ibge_censo2022_raca {
        mun_ano fecundidade_idade "1.2M linhas"
        mun_ano instrucao "167.1k linhas"
    }
    br_ibge_censo2022_religiao {
        mun_ano alfabetizacao_idade "557.1k linhas"
        mun_ano condicao_ocupacao_domicilio_cor_raca "557.1k linhas"
        mun_ano cor_raca "334.3k linhas"
        mun_ano estado_conjugal "167.1k linhas"
        mun_ano frequencia_escola_13_17 "222.8k linhas"
        mun_ano indigenas_condicao_ocupacao "557.1k linhas"
        mun_ano indigenas_sexo "167.1k linhas"
        mun_ano instrucao "278.6k linhas"
        mun_ano internet_domicilio "167.1k linhas"
        mun_ano mulheres_fecundidade_completa "1.6M linhas"
        mun_ano mulheres_fecundidade_idade_instrucao "802.2k linhas"
        mun_ano mulheres_filhos_numero_idade "351k linhas"
        mun_ano mulheres_filhos_numero_instrucao "351k linhas"
        ano populacao_religiao "56k linhas"
        mun_ano uniao_conjugal_natureza "278.6k linhas"
    }
    br_ibge_censo_2022 {
        mun alfabetizacao_grupo_idade_sexo_raca "779.8k linhas"
        mun_uf_setor_cep cadastro_enderecos "109.8M linhas"
        mun_ano caracteristica_domicilio_grupo_idade_raca_destino_lixo "4.1M linhas"
        mun_ano caracteristica_domicilio_grupo_idade_raca_esgotamento_sanitario "5.3M linhas"
        mun_ano caracteristica_domicilio_grupo_idade_raca_ligacao_abastecimento_agua "9.9M linhas"
        mun_ano caracteristica_domicilio_grupo_idade_raca_tipo_domicilio "3.5M linhas"
        sem_chave dicionario "30 linhas"
        mun domicilio_recenseado "66.8k linhas"
        mun_ano indice_envelhecimento_raca "55.7k linhas"
        mun_uf municipio "5.6k linhas"
        mun_ano populacao_grupo_idade_sexo_raca "2.3M linhas"
        uf populacao_grupo_idade_uf "378 linhas"
        mun populacao_idade_sexo "2.5M linhas"
        mun_uf_setor setor_censitario "468.1k linhas"
        uf terra_indigena "602 linhas"
        uf territorio_quilombola "492 linhas"
    }
```

**2/3**

```mermaid
erDiagram
    MUNICIPIO ||--o{ br_ibge_censo_demografico : "id_municipio"
    PESSOA_CPF ||..o{ br_ibge_censo_demografico : "numero_familia"
    SETOR_CENSITARIO ||--o{ br_ibge_censo_demografico : "id_setor_censitario"
    UF ||--o{ br_ibge_censo_demografico : "sigla_uf"
    UF ||--o{ br_ibge_estadic : "sigla_uf"
    MUNICIPIO ||--o{ br_ibge_munic : "id_municipio"
    UF ||--o{ br_ibge_munic : "sigla_uf"
    MUNICIPIO ||--o{ br_ibge_nomes_brasil : "id_municipio"
    PESSOA_CPF ||..o{ br_ibge_pnad : "numero_familia"
    UF ||--o{ br_ibge_pnad : "sigla_uf +1"
    br_ibge_censo_demografico {
        sem_chave dicionario "3k linhas"
        mun_uf_cpf microdados_domicilio_1970 "4.7M linhas"
        mun_uf microdados_domicilio_1980 "6.5M linhas"
        mun_uf microdados_domicilio_1991 "4M linhas"
        mun_uf microdados_domicilio_2000 "5.3M linhas"
        mun_uf microdados_domicilio_2010 "6.2M linhas"
        mun_uf_cpf microdados_pessoa_1970 "24.8M linhas"
        mun_uf microdados_pessoa_1980 "29.4M linhas"
        mun_uf microdados_pessoa_1991 "17M linhas"
        mun_uf microdados_pessoa_2000 "20.3M linhas"
        mun_uf microdados_pessoa_2010 "20.6M linhas"
        uf_setor setor_censitario_alfabetizacao_homens_mulheres_2010 "310.1k linhas"
        uf_setor setor_censitario_alfabetizacao_total_2010 "310.1k linhas"
        uf_setor setor_censitario_basico_2010 "310.1k linhas"
        uf_setor setor_censitario_domicilio_caracteristicas_gerais_2010 "310.1k linhas"
        uf_setor setor_censitario_domicilio_moradores_2010 "310.1k linhas"
        uf_setor setor_censitario_domicilio_renda_2010 "310.1k linhas"
        uf_setor setor_censitario_entorno_2010 "310.1k linhas"
        uf_setor setor_censitario_idade_homens_2010 "310.1k linhas"
        uf_setor setor_censitario_idade_mulheres_2010 "310.1k linhas"
        uf_setor setor_censitario_idade_total_2010 "310.1k linhas"
        uf_setor setor_censitario_pessoa_renda_2010 "310.1k linhas"
        uf_setor setor_censitario_raca_alfabetizacao_idade_genero_2010 "310.1k linhas"
        uf_setor setor_censitario_raca_idade_0_4_genero_2010 "310.1k linhas"
        uf_setor setor_censitario_raca_idade_genero_2010 "310.1k linhas"
        uf_setor setor_censitario_registro_civil_2010 "310.1k linhas"
        uf_setor setor_censitario_relacao_parentesco_conjuges_2010 "310.1k linhas"
        uf_setor setor_censitario_relacao_parentesco_filhos_2010 "310.1k linhas"
        uf_setor setor_censitario_relacao_parentesco_filhos_enteados_2010 "310.1k linhas"
        uf_setor setor_censitario_relacao_parentesco_outros_2010 "310.1k linhas"
        uf_setor setor_censitario_responsavel_domicilios_homens_total_2010 "310.1k linhas"
        uf_setor setor_censitario_responsavel_domicilios_mulheres_2010 "310.1k linhas"
        uf_setor setor_censitario_responsavel_renda_2010 "310.1k linhas"
    }
    br_ibge_estadic {
        uf_ano comunicacao_informatica "54 linhas"
        sem_chave dicionario "182 linhas"
        uf_ano educacao "54 linhas"
        uf_ano governanca "27 linhas"
        uf_ano indicadores_perfil_gestor "405 linhas"
        uf_ano indicadores_quantidade_vinculo "2.1k linhas"
        uf_ano politica_mulher "27 linhas"
        uf_ano recursos_humanos "189 linhas"
    }
    br_ibge_munic {
        mun_uf_ano atual_prefeito "33.4k linhas"
        mun_uf_ano habitacao "66.8k linhas"
        mun_uf_ano indicadores_perfil_gestor "83.5k linhas"
        mun_uf_ano indicadores_quantidade_vinculo "490.2k linhas"
        mun_uf_ano meio_ambiente "44.5k linhas"
        mun_uf_ano recursos_gestao "39k linhas"
        mun_uf_ano recursos_humanos "94.6k linhas"
    }
    br_ibge_nomes_brasil {
        mun quantidade_municipio_nome_2010 "2M linhas"
    }
    br_ibge_pnad {
        sem_chave dicionario "142 linhas"
        uf_ano microdados_compatibilizados_domicilio "1.9M linhas"
        uf_cpf_ano_mes microdados_compatibilizados_pessoa "7.7M linhas"
    }
    br_ibge_pnad_covid {
        sem_chave dicionario "554 linhas"
    }
```

**3/3**

```mermaid
erDiagram
    MUNICIPIO ||--o{ br_ibge_pnadc : "id_municipio"
    UF ||--o{ br_ibge_pnadc : "sigla_uf +1"
    UF ||--o{ br_ibge_pof : "sigla_uf"
    MUNICIPIO ||--o{ br_ibge_populacao : "id_municipio"
    UF ||--o{ br_ibge_populacao : "sigla_uf"
    MUNICIPIO ||--o{ br_ipea_avs : "id_municipio"
    UF ||--o{ br_ipea_avs : "sigla_uf"
    CEP ||--o{ br_mg_belohorizonte_smfa_iptu : "cep"
    CEP ||--o{ br_sp_saopaulo_geosampa_iptu : "cep"
    br_ibge_pnadc {
        ano ano_brasil_grupo_idade "408 linhas"
        ano ano_brasil_raca_cor "96 linhas"
        mun_ano ano_municipio_grupo_idade "11k linhas"
        mun_ano ano_municipio_raca_cor "2.6k linhas"
        ano ano_regiao_grupo_idade "2k linhas"
        ano ano_regiao_metropolitana_grupo_idade "8.2k linhas"
        ano ano_regiao_metropolitana_raca_cor "1.9k linhas"
        ano ano_regiao_raca_cor "480 linhas"
        uf_ano ano_uf_grupo_idade "11k linhas"
        uf_ano ano_uf_raca_cor "2.6k linhas"
        sem_chave dicionario "1.8k linhas"
        uf_ano educacao "1.7M linhas"
        uf_ano microdados "28.4M linhas"
        uf_ano rendimentos_outras_fontes "1.4M linhas"
    }
    br_ibge_pof {
        uf aluguel_estimado_2017 "48.9k linhas"
        sem_chave cadastro_de_produtos_2017 "13.5k linhas"
        uf caracteristicas_dieta_2017 "46.2k linhas"
        uf condicoes_vida_2017 "58k linhas"
        uf despesa_coletiva_2017 "478.6k linhas"
        sem_chave dicionario "5.5k linhas"
        uf domicilio_2017 "57.9k linhas"
        uf inventario_2017 "870.4k linhas"
        uf_ano_mes morador_2017 "178.4k linhas"
        uf outros_rendimentos_2017 "206.1k linhas"
        uf rendimento_trabalho_2017 "97.1k linhas"
        uf restricao_saude_2017 "40.9k linhas"
        uf servico_nao_monetario_pof2_2017 "14.7k linhas"
        uf servico_nao_monetario_pof4_2017 "122.7k linhas"
    }
    br_ibge_populacao {
        ano brasil "35 linhas"
        mun_uf_ano municipio "191.1k linhas"
        uf_ano uf "946 linhas"
    }
    br_ipea_avs {
        mun_uf_ano municipio "319.7k linhas"
    }
    br_mg_belohorizonte_smfa_iptu {
        sem_chave dicionario "14 linhas"
        cep_ano_mes iptu "21.5M linhas"
    }
    br_sp_saopaulo_geosampa_iptu {
        cep_ano_mes iptu "93.4M linhas"
    }
```

## Internacional, cultura e esporte

9 datasets · 25 tabelas

```mermaid
erDiagram
    PAIS ||..o{ world_oecd_public_finance : "country"
    MUNICIPIO ||..o{ world_olympedia_olympics : "city"
    PAIS ||..o{ world_olympedia_olympics : "country"
    CEP ||--o{ world_wb_mides : "cep"
    EMPRESA_CNPJ ||..o{ world_wb_mides : "documento"
    MUNICIPIO ||--o{ world_wb_mides : "id_municipio"
    ORGAO ||..o{ world_wb_mides : "nome_orgao"
    UF ||--o{ world_wb_mides : "sigla_uf"
    UNIDADE_GESTORA ||--o{ world_wb_mides : "id_unidade_gestora"
    mundo_transfermarkt_competicoes {
        ano brasileirao_serie_a "8.5k linhas"
        ano copa_brasil "598 linhas"
    }
    mundo_transfermarkt_competicoes_internacionais {
        sem_chave champions_league "2.6k linhas"
    }
    us_harvard_ned {
        sem_chave parliamentary_elections "4.9k linhas"
        sem_chave presidential_elections "1.4k linhas"
    }
    world_ampas_oscar {
        sem_chave winner_demographics "415 linhas"
    }
    world_imdb_movies {
        sem_chave top_movies_per_year "33.6k linhas"
    }
    world_oecd_public_finance {
        pais country "2.6k linhas"
    }
    world_olympedia_olympics {
        pais athlete_bio "155.9k linhas"
        sem_chave athlete_event_result "316.8k linhas"
        sem_chave country "235 linhas"
        mun game "64 linhas"
        pais game_medal_tally "1.8k linhas"
        sem_chave result "7.4k linhas"
    }
    world_sofascore_competicoes_futebol {
        ano brasileirao_serie_a "6.8k linhas"
        ano uefa_champions_league "4.5k linhas"
    }
    world_wb_mides {
        sem_chave dicionario "961 linhas"
        mun_uf_ug_ano_mes empenho "303.3M linhas"
        mun_uf_ug_ano_mes licitacao "2.4M linhas"
        mun_uf_cnpj_ug_ano licitacao_item "50.3M linhas"
        mun_uf_cep_cnpj_ug_ano licitacao_participante "5.3M linhas"
        mun_uf_ug_ano_mes liquidacao "357.3M linhas"
        mun_uf_orgao_ug_ano orgao_unidade_gestora "341.6k linhas"
        mun_uf_ug_ano_mes pagamento "392.7M linhas"
        mun_uf_ano relacionamentos "20.6M linhas"
    }
```

---

## Sem ligação documentada

### Datasets (37)

Nenhuma coluna reconhecida como chave de nenhum hub. Alguns são séries nacionais sem recorte geográfico ou de entidade (índices de preço, cotações, agregados nacionais); o resto são fontes raspadas cujo identificador ainda não foi mapeado — esses são os candidatos às próximas pontes no `join_keys.md`.

- `br_ana_reservatorios` — `sin`
- `br_anac_dadosabertos` — `pontualidade`, `rab`, `voos`
- `br_anvisa_consultas` — `registros`
- `br_bcb_sgs` — `series`
- `br_bd_diretorios_data_tempo` — `ano`, `bimestre`, `data`, `dia`, `hora`, `mes`, `minuto`, `segundo`, `semestre`, `tempo`, `trimestre`
- `br_caixa_sorteios` — `megasena`
- `br_ce_fortaleza_sefin_iptu` — `face_quadra`
- `br_fgv_igp` — `igp_10_mes`, `igp_di_ano`, `igp_di_mes`, `igp_m_ano`, `igp_m_mes`, `igp_og_ano`, `igp_og_mes`
- `br_fipe_veiculos` — `precos`
- `br_ggb_relatorio_lgbtqi` — `brasil`, `causa_obito`, `grupo_lgbtqia`, `local`, `raca_cor`
- `br_ibge_ipp` — `mes_categoria_economica`, `mes_grupo_industrial`, `mes_industria_atividade`, `mes_industria_extrativa`, `mes_industria_geral`, `mes_industria_transformacao`
- `br_ibge_pnad_covid` — `dicionario`
- `br_ipea_atlasviolencia` — `series`, `valores_nacional`
- `br_me_estoque_divida_publica` — `microdados`
- `br_me_exportadoras_importadoras` — `dicionario`
- `br_me_siape` — `servidores_executivo_federal`
- `br_me_sic` — `dicionario`, `transferencia`
- `br_me_siorg` — `remuneracao`
- `br_mec_prouni` — `dicionario`
- `br_stf_corte_aberta` — `decisoes`, `dicionario`
- `br_stj_dadosabertos` — `documentos`
- `br_tce_to` — `pautas`
- `br_tcu_dadosabertos` — `dados`
- `eu_sanctions` — `sanctions`
- `global_ibge_tabua_mares` — `estacoes`, `previsao`
- `global_icij_offshoreleaks` — `addresses`, `entities`, `intermediaries`, `officers`, `other`, `relationships`
- `global_ofac_sanctions` — `sanctions`
- `global_opensanctions` — `entities`
- `mundo_transfermarkt_competicoes` — `brasileirao_serie_a`, `copa_brasil`
- `mundo_transfermarkt_competicoes_internacionais` — `champions_league`
- `un_sanctions` — `sanctions`
- `us_harvard_ned` — `parliamentary_elections`, `presidential_elections`
- `world_ampas_oscar` — `winner_demographics`
- `world_iea_pirls` — `dictionary`, `home_context`, `school_context`, `student_achievement`, `student_context`, `student_teacher_link`, `teacher_context`, `within_country_scoring_reliability`
- `world_iea_timss` — `dictionary`, `home_context_grade_4`, `school_context_grade_4`, `school_context_grade_8`, `student_achievement_grade_4`, `student_achievement_grade_8`, `student_context_grade_4`, `student_context_grade_8`, `teacher_context_grade_4`, `teacher_mathematics_grade_8`, `teacher_science_grade_8`
- `world_imdb_movies` — `top_movies_per_year`
- `world_sofascore_competicoes_futebol` — `brasileirao_serie_a`, `uefa_champions_league`

### Tabelas (201)

Tabelas que não carregam chave alguma, inclusive dentro de datasets que se conectam pelas outras tabelas (dicionários, agregados nacionais, metadados):

`br_ana_reservatorios.sin`, `br_anac_dadosabertos.pontualidade`, `br_anac_dadosabertos.rab`, `br_anac_dadosabertos.voos`, `br_anvisa_consultas.registros`, `br_bcb_estban.dicionario`, `br_bcb_sgs.series`, `br_bcb_sicor.dicionario`, `br_bcb_sicor.empreendimento`, `br_bd_diretorios_brasil.area_conhecimento`, `br_bd_diretorios_brasil.curso_superior`, `br_bd_diretorios_brasil.etnia_indigena`, `br_bd_diretorios_brasil.natureza_juridica`, `br_bd_diretorios_brasil.subatividade_ibge`, `br_bd_diretorios_data_tempo.bimestre`, `br_bd_diretorios_data_tempo.dia`, `br_bd_diretorios_data_tempo.hora`, `br_bd_diretorios_data_tempo.minuto`, `br_bd_diretorios_data_tempo.segundo`, `br_bd_diretorios_data_tempo.semestre`, `br_bd_diretorios_data_tempo.tempo`, `br_bd_diretorios_data_tempo.trimestre`, `br_bd_diretorios_us.cbsa_2023`, `br_bd_diretorios_us.census_tract_2020`, `br_bd_diretorios_us.congress_member`, `br_bd_diretorios_us.congressional_district_119`, `br_bd_diretorios_us.county`, `br_bd_diretorios_us.naics_2022`, `br_bd_diretorios_us.place`, `br_bd_diretorios_us.puma_2020`, `br_bd_diretorios_us.school`, `br_bd_diretorios_us.school_district`, `br_bd_metadados.bigquery_tables`, `br_bd_metadados.external_links`, `br_bd_metadados.information_requests`, `br_bd_metadados.organizations`, `br_bd_metadados.resources`, `br_bd_metadados.tables`, `br_brasilapi.bancos`, `br_brasilapi.feriados`, `br_brasilapi.taxas_referencia`, `br_caixa_sorteios.megasena`, `br_camara_dados_abertos.deputado_profissao`, `br_camara_dados_abertos.evento`, `br_camara_dados_abertos.evento_orgao`, `br_camara_dados_abertos.evento_presenca_deputado`, `br_camara_dados_abertos.evento_requerimento`, `br_camara_dados_abertos.frente`, `br_camara_dados_abertos.frente_deputado`, `br_camara_dados_abertos.funcionario`, `br_camara_dados_abertos.sigla_partido`, `br_camara_dados_abertos.votacao`, `br_camara_dados_abertos.votacao_orientacao_bancada`, `br_cgu_cartao_pagamento.dicionario`, `br_cgu_dados_abertos.conjunto`, `br_cgu_dados_abertos.recurso`, `br_cgu_fef.sorteio`, `br_cgu_viagens.pagamento`, `br_cgu_viagens.passagem`, `br_cnpq_bolsas.dicionario`, `br_comprasgov_catmatcatser.servicos`, `br_cvm_administradores_carteira.pessoa_fisica`, `br_datasus_cid10.capitulos`, `br_datasus_cid10.cid_o_grupos`, `br_datasus_cid10.grupos`, `br_datasus_cid10.subcategorias`, `br_fipe_veiculos.precos`, `br_geobr_mapas.amazonia_legal`, `br_geobr_mapas.pais`, `br_geobr_mapas.regiao`, `br_ibama_embargos.anexo`, `br_ibama_embargos.coordenadas`, `br_ibama_embargos.enquadramento`, `br_ibama_embargos.enquadramento_complementar`, `br_ibama_embargos.itens`, `br_ibge_censo_2022.dicionario`, `br_ibge_censo_demografico.dicionario`, `br_ibge_estadic.dicionario`, `br_ibge_pnad.dicionario`, `br_ibge_pnad_covid.dicionario`, `br_ibge_pnadc.dicionario`, `br_ibge_pof.cadastro_de_produtos_2017`, `br_ibge_pof.dicionario`, `br_inep_ana.dicionario`, `br_inep_avaliacao_alfabetizacao.dicionario`, `br_inep_censo_educacao_superior.dicionario`, `br_inep_censo_escolar.dicionario`, `br_inep_enem.dicionario`, `br_inep_enem.questionario_socioeconomico_1998`, `br_inep_enem.questionario_socioeconomico_1999`, `br_inep_enem.questionario_socioeconomico_2000`, `br_inep_enem.questionario_socioeconomico_2001`, `br_inep_enem.questionario_socioeconomico_2002`, `br_inep_enem.questionario_socioeconomico_2003`, `br_inep_enem.questionario_socioeconomico_2004`, `br_inep_enem.questionario_socioeconomico_2005`, `br_inep_enem.questionario_socioeconomico_2006`, `br_inep_enem.questionario_socioeconomico_2007`, `br_inep_enem.questionario_socioeconomico_2008`, `br_inep_enem.questionario_socioeconomico_2009`, `br_inep_enem.questionario_socioeconomico_2010`, `br_inep_enem.questionario_socioeconomico_2011`, `br_inep_enem.questionario_socioeconomico_2012`, `br_inep_enem.questionario_socioeconomico_2013`, `br_inep_enem.questionario_socioeconomico_2014`, `br_inep_enem.questionario_socioeconomico_2015`, `br_inep_enem.questionario_socioeconomico_2016`, `br_inep_enem.questionario_socioeconomico_2017`, `br_inep_enem.questionario_socioeconomico_2018`, `br_inep_enem.questionario_socioeconomico_2019`, `br_inep_enem.questionario_socioeconomico_2020`, `br_inep_enem.questionario_socioeconomico_2021`, `br_inep_enem.questionario_socioeconomico_2022`, `br_inep_enem.questionario_socioeconomico_2023`, `br_inep_formacao_docente.dicionario`, `br_inep_indicador_nivel_socioeconomico.dicionario`, `br_inep_saeb.dicionario`, `br_inep_sinopse_estatistica_educacao_basica.dicionario`, `br_ipea_atlasviolencia.series`, `br_mapbiomas_estatisticas.classe`, `br_me_caged.dicionario`, `br_me_cno.dicionario`, `br_me_cno.microdados_vinculo`, `br_me_cnpj.dicionario`, `br_me_comex_stat.dicionario`, `br_me_exportadoras_importadoras.dicionario`, `br_me_rais.dicionario`, `br_me_siape.servidores_executivo_federal`, `br_me_sic.dicionario`, `br_me_siorg.remuneracao`, `br_mec_prouni.dicionario`, `br_mg_belohorizonte_smfa_iptu.dicionario`, `br_mjsp_ckan.infopen`, `br_ms_cnes.dicionario`, `br_ms_pns.dicionario`, `br_ms_sia.dicionario`, `br_ms_sih.dicionario`, `br_ms_sim.dicionario`, `br_ms_sinan.dicionario`, `br_ms_sinasc.dicionario`, `br_ms_sisvan.dicionario`, `br_ms_vacinacao_covid19.dicionario`, `br_rf_cafir.dicionario`, `br_rf_cno.dicionario`, `br_rf_cno.vinculos`, `br_seeg_emissoes.dicionario`, `br_senado_dadosabertos.materias`, `br_senado_dadosabertos.senadores`, `br_sfb_sicar.dicionario`, `br_siop_orcamento.alteracoes_orcamentarias`, `br_siop_orcamento.dados`, `br_siop_orcamento.planos_orcamentarios`, `br_stf_corte_aberta.dicionario`, `br_stj_dadosabertos.documentos`, `br_tce_pi.despesas_total`, `br_tce_pi.licitacoes_estado`, `br_tce_pi.receitas_total`, `br_tce_to.pautas`, `br_tse_eleicoes.dicionario`, `eu_sanctions.sanctions`, `global_ibge_tabua_mares.estacoes`, `global_ibge_tabua_mares.previsao`, `global_icij_offshoreleaks.addresses`, `global_icij_offshoreleaks.entities`, `global_icij_offshoreleaks.intermediaries`, `global_icij_offshoreleaks.officers`, `global_icij_offshoreleaks.other`, `global_icij_offshoreleaks.relationships`, `global_ofac_sanctions.sanctions`, `global_opensanctions.entities`, `mundo_transfermarkt_competicoes_internacionais.champions_league`, `un_sanctions.sanctions`, `us_harvard_ned.parliamentary_elections`, `us_harvard_ned.presidential_elections`, `world_ampas_oscar.winner_demographics`, `world_iea_pirls.dictionary`, `world_iea_pirls.home_context`, `world_iea_pirls.school_context`, `world_iea_pirls.student_achievement`, `world_iea_pirls.student_context`, `world_iea_pirls.student_teacher_link`, `world_iea_pirls.teacher_context`, `world_iea_pirls.within_country_scoring_reliability`, `world_iea_timss.dictionary`, `world_iea_timss.home_context_grade_4`, `world_iea_timss.school_context_grade_4`, `world_iea_timss.school_context_grade_8`, `world_iea_timss.student_achievement_grade_4`, `world_iea_timss.student_achievement_grade_8`, `world_iea_timss.student_context_grade_4`, `world_iea_timss.student_context_grade_8`, `world_iea_timss.teacher_context_grade_4`, `world_iea_timss.teacher_mathematics_grade_8`, `world_iea_timss.teacher_science_grade_8`, `world_imdb_movies.top_movies_per_year`, `world_olympedia_olympics.athlete_event_result`, `world_olympedia_olympics.country`, `world_olympedia_olympics.result`, `world_wb_mides.dicionario`, `world_wwf_hydrosheds.basins_atlas`, `world_wwf_hydrosheds.rivers_atlas`
