#!/usr/bin/env python3
"""docs/context/schema_dict_status.json -> mesmo arquivo, com uma passada de
julgamento humano/LLM sobre as colunas `nao_verificado`.

    python3 scripts/llm_triage_schema_dict_status.py

`gera_schema_dict_status.py` decide por REGEX — pega padrão genérico
(`ano`, `mes`, `indicador_*`...) mas não sabe ler. Boa parte do que sobrou
como `nao_verificado` é, lendo de verdade, autoexplicativo: SISDEPEN inteiro
(3.233 colunas) é a PERGUNTA LITERAL do formulário oficial, convertida em
slug numerado por seção — "2_18_ha_acessibilidade_para_pessoas_com_
deficiencia" não precisa de dicionário nenhum, o nome já é a explicação.
Regex não pega isso porque não é um padrão fixo, é linguagem natural — exige
alguém (ou algo) ler.

Feito por leitura de amostra real (não é achismo): pra cada dataset abaixo,
puxei uma amostra aleatória das colunas `nao_verificado` reais (não as
adiadas por tamanho) e li. `DATASET_VERDICTS` é o resultado — datasets onde a
amostra confirma que os nomes são frase legível (formulário/questionário
convertido em slug) viram `nao_e_codigo` em bloco; o resto fica
`nao_verificado`, porque a amostra mostrou código opaco de verdade (ex.:
PIRLS/TIMSS usam a nomenclatura oficial do IEA — `atbr03b`, `btbs22db` —,
SINAN usa abreviação DATASUS maiúscula — `CS_RACA`, `SEX_EXPLO`) ou uma
mistura que não dá pra resolver em bloco sem risco de marcar errado.

Achados pontuais registrados aqui, não achismo de regex:
  - `br_ibge_censo_demografico.setor_censitario_*` (2.228 colunas, 88% do
    dataset): são códigos V-prefixados do produto "Agregados por Setores
    Censitários" do Censo 2010, que TEM dicionário oficial publicado pelo
    IBGE (achado via busca, não confirmado célula a célula — ver reason).
  - `cor_raca`/`sexo_paciente`/`raca_cor_paciente` (16 colunas, 3 datasets):
    mesmo conceito de `bridges.yaml coded_differently`, só com a ordem das
    palavras trocada ou um sufixo — o match exato do gerador original não
    pega variação de ordem. Reclassificadas para `documentado_em_outro_lugar`
    com o mesmo motivo do conceito canônico.
  - `br_siop_orcamento`: achado um bug de import, não falta de dicionário —
    colunas como `FunÃ§Ã£o`/`RegiÃ£o`/`ï»¿ano` são mojibake (nome de coluna
    veio com encoding corrompido do CSV original) coexistindo com as versões
    corretas (`funcao`). Marcado à parte, não é candidato a pesquisa.

Rerun se `gera_schema_dict_status.py` rodar de novo e sobrescrever o
arquivo — esta passada não é idempotente automaticamente, precisa rodar
depois, sempre.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DST = REPO / "docs" / "context" / "schema_dict_status.json"

# dataset -> motivo (aplicado a TODA coluna nao_verificado real do dataset,
# exceto as citadas em SPECIAL_CASES abaixo). Confirmado por amostra lida à
# mão, não é heurística.
DATASET_VERDICTS: dict[str, str] = {
    "br_mjsp_sisdepen": (
        "nome da coluna é a pergunta literal do formulário oficial SISDEPEN "
        "(levantamento penitenciário do MJSP/Senappen), convertida em slug "
        "numerado por seção — o texto já é a explicação. Confirmado por "
        "amostra de ~80 das 3.233 colunas, lidas à mão."
    ),
    "br_ibge_munic": "nome é a pergunta/tema do questionário MUNIC (IBGE), legível diretamente — confirmado por amostra",
    "br_ibge_estadic": "nome é a pergunta/tema do questionário ESTADIC (IBGE), legível diretamente — confirmado por amostra",
    "br_inep_censo_escolar": "nome descreve o item do Censo Escolar (INEP) diretamente — confirmado por amostra",
    "world_sofascore_competicoes_futebol": "estatística de partida de futebol (posse de bola, faltas...), nome autoexplicativo — confirmado por amostra",
    "mundo_transfermarkt_competicoes": "estatística de partida de futebol, nome autoexplicativo — confirmado por amostra",
    "br_camara_dados_abertos": "campo da API de dados abertos da Câmara, nome autoexplicativo — confirmado por amostra",
    "br_cgu_beneficios_cidadao": "campo de folha de pagamento de benefício social (Bolsa Família etc.), nome autoexplicativo — confirmado por amostra",
    "br_transferegov": "campo de transferência de recursos federais, nome burocrático mas legível — confirmado por amostra",
    "br_bd_diretorios_brasil": "campo de diretório (escola/estabelecimento), nome autoexplicativo — confirmado por amostra",
    "br_ieps_saude": "indicador de saúde agregado (contagem/despesa), o nome já diz o que é contado — confirmado por amostra",
    "br_ms_cnes": "campo cadastral de estabelecimento de saúde (CNES), nome autoexplicativo — confirmado por amostra",
    "br_ana_telemetria": "campo de estação telemétrica (ANA), nome autoexplicativo apesar do CamelCase legado — confirmado por amostra",
    "br_tse_eleicoes": "categoria de prestação de contas eleitoral (TSE), nome descreve o conceito — confirmado por amostra; código exato de cada categoria pode ainda valer a pena checar no manual do TSE se for usado em agregação fina",
    "eu_sanctions": "campo do schema da lista de sanções da UE (inglês, CamelCase), nome autoexplicativo — confirmado por amostra",
    "br_senado_dadosabertos": "campo da API de dados abertos do Senado, nome autoexplicativo apesar do camelCase — confirmado por amostra",
    "world_oecd_pisa": "campo do estudo PISA (OCDE), nome em inglês autoexplicativo — confirmado por amostra",
    "br_ibama_embargos_novo": "campo de auto de embargo do IBAMA, nome autoexplicativo — confirmado por amostra",
    "br_ibama_autos": "campo de auto de infração do IBAMA, nome autoexplicativo — confirmado por amostra",
    "br_anm": "campo de processo minerário da ANM, nome autoexplicativo — confirmado por amostra",
    "br_bcb_sicor": "campo de operação de crédito rural (SICOR/BCB), nome autoexplicativo — confirmado por amostra; `finalidade` específica pode valer conferência se usada pra agregação fina",
}

# dataset.column (ou dataset.table.coluna) -> (label, motivo) — exceções que
# não seguem o veredito em bloco do dataset, ou casos fora de qualquer
# dataset da lista acima.
SPECIAL_CASE_COLUMNS: dict[str, tuple[str, str]] = {
    "cor_raca": ("documentado_em_outro_lugar",
                 "mesmo conceito de bridges.yaml coded_differently.raca_cor, só com a ordem das palavras trocada — "
                 "ver a entrada raca_cor: código numérico difere por fonte, decodificar via {dataset}.dicionario"),
    "sexo_paciente": ("documentado_em_outro_lugar",
                       "mesmo conceito de bridges.yaml coded_differently.sexo, com sufixo _paciente — "
                       "código numérico difere por fonte, decodificar via {dataset}.dicionario"),
    "raca_cor_paciente": ("documentado_em_outro_lugar",
                           "mesmo conceito de bridges.yaml coded_differently.raca_cor, com sufixo _paciente — "
                           "código numérico difere por fonte, decodificar via {dataset}.dicionario"),
}

SISDEPEN_MOJIBAKE_REASON = (
    "bug de import, não falta de dicionário: nome de coluna veio com encoding corrompido "
    "(mojibake) do CSV original do SIOP — existe uma versão correta coexistindo "
    "(ex.: 'funcao' ao lado de 'FunÃ§Ã£o'). Não é candidato a pesquisa externa, é limpeza de dado."
)

SETOR_CENSITARIO_REASON = (
    "código V-prefixado do produto \"Agregados por Setores Censitários\" do Censo 2010 (IBGE). "
    "O IBGE publica dicionário oficial de variáveis pra este produto — achado via busca "
    "(FTP oficial: ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Resultados_do_Universo/"
    "Agregados_por_Setores_Censitarios/, documentação em PDF/XLS por UF), mas NÃO conferido "
    "célula a célula contra os códigos reais desta tabela — tratar como pista forte, não como "
    "decode verificado. Cobre 2.228 das 2.522 colunas nao_verificado do dataset; o resto "
    "(m-prefixadas e algumas v- nas tabelas microdados_*) não está nem no dicionario nativo "
    "nem nesta documentação — genuinamente sem fonte, seguem nao_verificado."
)


def main():
    with open(DST, encoding="utf-8") as f:
        out = json.load(f)
    columns = out["columns"]

    changed = {"nao_e_codigo": 0, "documentado_em_outro_lugar": 0}
    for key, info in columns.items():
        if info["label"] != "nao_verificado":
            continue
        dataset, table, col = key.split(".", 2)

        if dataset == "br_siop_orcamento" and any(ord(ch) > 127 for ch in col):
            info.update(label="nao_e_codigo", reason=SISDEPEN_MOJIBAKE_REASON, judged_by="llm")
            changed["nao_e_codigo"] += 1
            continue

        if dataset == "br_ibge_censo_demografico" and table.startswith("setor_censitario") and col.lower().startswith("v"):
            info.update(label="documentado_em_outro_lugar", reason=SETOR_CENSITARIO_REASON, judged_by="llm")
            changed["documentado_em_outro_lugar"] += 1
            continue

        if col.lower() in SPECIAL_CASE_COLUMNS:
            label, reason = SPECIAL_CASE_COLUMNS[col.lower()]
            info.update(label=label, reason=reason.format(dataset=dataset), judged_by="llm")
            changed[label] += 1
            continue

        if dataset in DATASET_VERDICTS:
            info.update(label="nao_e_codigo", reason=f"LLM: {DATASET_VERDICTS[dataset]}", judged_by="llm")
            changed["nao_e_codigo"] += 1

    by_label = {}
    for info in columns.values():
        by_label[info["label"]] = by_label.get(info["label"], 0) + 1

    out["_meta"]["counts_by_label"] = by_label
    out["_meta"]["llm_triage"] = {
        "script": "scripts/llm_triage_schema_dict_status.py",
        "datasets_bulk_reclassified": sorted(DATASET_VERDICTS),
        "note": (
            "Passada de leitura humana/LLM sobre uma amostra real de cada dataset listado — "
            "não é regex. Datasets NÃO listados aqui (PIRLS, TIMSS, PNS, censo_2022, "
            "SINAN, ENEM, POF, PNADC, SIH, SAEB e o resto) foram amostrados e achados "
            "genuinamente opacos ou mistos demais pra reclassificar em bloco sem risco — "
            "seguem nao_verificado, candidatos reais ao estágio 4 (pesquisa manual)."
        ),
    }

    DST.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"reclassificadas: {changed}")
    print(f"novos totais: {by_label}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
