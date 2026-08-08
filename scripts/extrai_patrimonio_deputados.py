#!/usr/bin/env python3
"""Painel de evolução patrimonial dos deputados federais — extração dos dados.

Monta o dataset que alimenta o app de exploração: todas as pessoas já eleitas
deputado federal desde 2006, com a série completa de declarações de bens que
fizeram à Justiça Eleitoral, a composição de cada declaração, as empresas em
que constam como sócias e a régua do subsídio que o mandato pagou.

  universo   2.347 pessoas eleitas deputado federal em alguma eleição de 2006
             a 2022, e todas as candidaturas que registraram de 2010 em
             diante —
             inclusive a prefeito e vereador, que entram na série porque
             carregam declaração de bens.
  série      2010, 2012, 2014, 2016, 2018, 2020, 2022 e 2026.

Por que a série começa em 2010
------------------------------
Em 2006 e 2008 o sequencial_candidato **não é único** na tabela de candidatos:
19.204 linhas para 3.162 sequenciais distintos em 2006, 381.250 para 68.551 em
2008. Como é essa a chave que liga candidato a bem declarado, juntar por ela
nesses dois anos espalha os bens de uma pessoa por dezenas de outras — o
sintoma foi um patrimônio de R$ 132.386.000 aparecendo idêntico em duas pessoas
diferentes, e uma mediana de crescimento de −2,6 vezes o subsídio, que não
existe no mundo. De 2010 em diante a chave é única e o cruzamento fecha.
  régua      subsídio bruto acumulado entre duas declarações consecutivas,
             contado só nos meses em que a pessoa exercia mandato federal
             (deputado federal ou senador) — ver "A régua" abaixo.

A régua
-------
O subsídio só entra na conta quando é conhecido. A tabela de valores em
scripts/referencia/subsidio_parlamentar.json cobre deputado federal e senador, que
recebem o mesmo valor por força dos mesmos decretos legislativos. Prefeito,
vereador e deputado estadual não têm valor conhecido aqui, então os meses de
mandato municipal ou estadual **não somam nada** à régua — e o ponto sai
marcado com `regua_parcial`, para o app poder dizer que ali a comparação está
incompleta em vez de fingir que o período foi de graça.

Correção de uma constante errada
--------------------------------
Os scripts plot_patrimonio_deputados_2018_2022.py e plot_patrimonio_abaixo_-
subsidio.py usam SUBSIDIO = 1_764_767, derivado de R$ 39.293,32/mês "desde
fevereiro de 2019". A data está errada: esse valor só passou a vigorar em 1º de
janeiro de 2023 (Decreto Legislativo 172/2022). No mandato 2019-2022 o subsídio
foi R$ 33.763,00, congelado desde 2015 — o acumulado correto é R$ 1.516.521, e
a régua publicada estava 16,4% alta. Este script calcula a partir da tabela de
vigências e não repete o erro.

Ressalva de dado
----------------
bens_candidato traz ~1% de linhas byte-idênticas repetidas (mesmo candidato,
mesmo item, mesmo valor, sem coluna que as distinga). A consulta aplica
DISTINCT, o que também colapsa o caso raro de dois bens genuinamente idênticos
pelo mesmo valor. Mesmo tratamento dos scripts de patrimônio já publicados.

2026 está incompleto
--------------------
O prazo de registro se encerra em 15/08/2026 e o arquivo do TSE ainda cresce a
cada dia. Os pontos de 2026 saem com `parcial: true` e o app tem de tratá-los
como provisórios: ausência ali não é ausência de bem, é candidatura ainda não
registrada. Quanto do ciclo já estava protocolado no momento da geração é
medido na hora, contra o total de 2022, e vai para a ressalva do JSON.

O ano de 2026 não vem mais de CSV baixado aqui: quem cuida dele é
scripts/scrap/tse_eleicoes_2026.py, que conforma o arquivo do TSE ao schema da
Base dos Dados e o deixa no espelho junto dos outros anos. Rode aquele script
antes deste para gerar o painel com o retrato mais recente.

Consulta (beelink, via SSH — BEELINK_HOST, default 'beelink'):
  br_tse_eleicoes/resultados_candidato_municipio   eleitos, para o universo e a régua
  br_tse_eleicoes/candidatos                       CPF, nome, UF, partido, cargo (2010-2026)
  br_tse_eleicoes/bens_candidato                   declarações de bens (2010-2026)
  br_me_cnpj/socios                                quadro societário
  br_me_cnpj/empresas                              capital social

Uso:
  python3 scripts/extrai_patrimonio_deputados.py
  python3 scripts/extrai_patrimonio_deputados.py --saida pages/analises/patrimonio/dados.json
  python3 scripts/extrai_patrimonio_deputados.py --sem-2026
"""
import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "scripts" / "referencia"

# ── as 55 rubricas do TSE colapsadas em 7 macro-categorias ───────────────────
# De-para explícito de propósito: regex sobre esses rótulos erraria em
# "Ações (inclusive as provenientes de linha telefônica)" contra "Linha
# telefônica", que são coisas diferentes e caem em categorias diferentes.
CATEGORIAS = ["imovel", "veiculo", "dinheiro", "aplicacao",
              "societaria", "credito", "outros"]

MAPA = {
    "imovel": [
        "Casa", "Terreno", "Apartamento", "Outros bens imóveis", "Terra nua",
        "Prédio comercial", "Prédio residencial", "Loja", "Sala ou conjunto",
        "Construção", "Benfeitorias", "Galpão",
    ],
    "veiculo": [
        "Veículo automotor terrestre: caminhão, automóvel, moto, etc.",
        "Embarcação", "Aeronave",
    ],
    "dinheiro": [
        "Depósito bancário em conta corrente no País",
        "Dinheiro em espécie - moeda nacional", "Caderneta de poupança",
        "Dinheiro em espécie - moeda estrangeira",
        "Depósito bancário em conta corrente no exterior",
        "Outros depósitos à vista e numerário",
    ],
    "aplicacao": [
        "Aplicação de renda fixa (CDB, RDB e outros)",
        "Outras aplicações e Investimentos", "Outros fundos",
        "VGBL - Vida Gerador de Benefício Livre", "Fundo de capitalização",
        "Fundos: Ações, Mútuos de Privatização, Invest. Empresas Emergentes, "
        "Invest.Participação e Invest. Índice Mercado",
        "Fundo de investimento financeiro - FIF",
        "Fundo de Longo Prazo e Fundo de Investimentos em Direitos Creditórios (FIDC)",
        "Fundo de Investimento Imobiliário", "Fundo de Curto Prazo",
        "Ouro, ativo financeiro",
        "Fundo de ações, inclusive Carteira Livre e Fundo de Investimento no exterior",
        "Mercado futuros, de opções e a termo",
        "Plano PAIT e caderneta de pecúlio",
        "Fundo de aplicação em quotas de fundos de investimento",
        "Poupança para construção ou aquisição de bem imóvel",
        # rubrica de nome ambíguo: é poupança vinculada, não crédito a receber
        "Outros créditos e poupança vinculados",
    ],
    "societaria": [
        "Quotas ou quinhões de capital", "Outras participações societárias",
        "Ações (inclusive as provenientes de linha telefônica)",
    ],
    "credito": [
        "Crédito decorrente de empréstimo", "Crédito decorrente de alienação",
    ],
    "outros": [
        "OUTROS BENS E DIREITOS", "Outros bens e direitos", "Outros bens móveis",
        "Bem relacionado com o exercício da atividade autônoma",
        "Consórcio não contemplado", "Linha telefônica",
        "Título de clube e assemelhado",
        "Jóia, quadro, objeto de arte, de coleção, antiguidade, etc.",
        "Direito de lavra e assemelhado", "Licença e concessões especiais",
        "Direito de autor, de inventor e patente", "Leasing",
    ],
}

# qualificações de propriedade no quadro societário da Receita. Administrador,
# conselheiro, diretor e presidente contratados ficam de fora: não implicam
# quota alguma. Mesmo recorte dos scripts de patrimônio já publicados.
QUALIF_SOCIO = ("22", "49", "52", "53", "65")

CARGOS_FEDERAIS = ("deputado federal", "senador")


def sql_categoria() -> str:
    """CASE que traduz tipo_item em macro-categoria, gerado do MAPA."""
    linhas = []
    for cat, tipos in MAPA.items():
        for t in tipos:
            linhas.append(f"    WHEN tipo_item = '{t.replace(chr(39), chr(39)*2)}'"
                          f" THEN '{cat}'")
    return "CASE\n" + "\n".join(linhas) + "\n    ELSE 'outros' END"


def consulta(sql: str):
    """Roda SQL no DuckDB do beelink e devolve list[dict].

    SET enable_progress_bar=false é obrigatório: a barra de progresso vai para
    o stdout e corrompe o JSON.
    """
    host = os.environ.get("BEELINK_HOST", "beelink")
    res = subprocess.run(["ssh", host, "~/bin/duckdb -json"],
                         input=sql.encode(), capture_output=True, check=True)
    saida = res.stdout.decode().strip()
    return json.loads(saida) if saida else []


# ── a régua: subsídio acumulado ──────────────────────────────────────────────
def carrega_vigencias():
    d = json.loads((DADOS / "subsidio_parlamentar.json").read_text("utf-8"))
    vig = [(date.fromisoformat(v["desde"]), v["valor"]) for v in d["vigencias"]]
    return sorted(vig)


VIGENCIAS = carrega_vigencias()


def valor_no_mes(ano: int, mes: int) -> float:
    """Subsídio mensal vigente naquele mês. Zero antes da primeira vigência."""
    ref = date(ano, mes, 1)
    valor = 0.0
    for desde, v in VIGENCIAS:
        if desde <= ref:
            valor = v
        else:
            break
    return valor


def acumulado(meses) -> float:
    """Soma o subsídio dos meses dados, mais um 13º por ano civil, na
    proporção dos meses efetivamente exercidos naquele ano."""
    total = sum(valor_no_mes(a, m) for a, m in meses)
    por_ano = {}
    for a, m in meses:
        por_ano.setdefault(a, []).append(m)
    for a, ms in por_ano.items():
        # 13º proporcional aos meses exercidos, pelo valor de dezembro
        total += valor_no_mes(a, 12) * len(ms) / 12
    return total


def meses_de_mandato(ano_eleicao: int):
    """Meses de exercício de um mandato federal ganho naquela eleição.

    Legislatura federal: posse em 1º de fevereiro do ano seguinte, quatro anos.
    Senador eleito cumpre oito, mas a régua entre duas declarações consecutivas
    nunca passa de quatro anos, então o excedente é aparado pelo intervalo.
    """
    ini = date(ano_eleicao + 1, 2, 1)
    fim = date(ano_eleicao + 5, 1, 31)
    return ini, fim


def meses_no_intervalo(ini: date, fim: date):
    a, m = ini.year, ini.month
    while (a, m) <= (fim.year, fim.month):
        yield a, m
        m += 1
        if m > 12:
            a, m = a + 1, 1


# ── consultas ────────────────────────────────────────────────────────────────
SQL_PAINEL = """SET enable_progress_bar=false;
WITH el AS (
  SELECT DISTINCT ano, sequencial_candidato AS seq
  FROM read_parquet('~/rodado/br_tse_eleicoes/resultados_candidato_municipio/*.parquet')
  WHERE cargo='deputado federal'
    AND resultado IN ('eleito por media','eleito por qp') AND ano>=2010
),
ca AS (
  SELECT ano, sequencial, cpf, nome, sigla_uf, sigla_partido, cargo
  FROM read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet')
  WHERE ano>=2010 AND cpf IS NOT NULL AND cpf<>''
),
pes AS (SELECT DISTINCT ca.cpf FROM el JOIN ca ON ca.ano=el.ano AND ca.sequencial=el.seq),
bens AS (
  SELECT DISTINCT ano, sequencial_candidato, tipo_item, descricao_item, valor_item
  FROM read_parquet('~/rodado/br_tse_eleicoes/bens_candidato/*.parquet')
  WHERE ano>=2010
),
bcat AS (
  SELECT ano, sequencial_candidato AS seq, {caso} AS cat, SUM(valor_item) AS v
  FROM bens GROUP BY 1,2,3
)
SELECT ca.cpf, ca.ano,
       any_value(ca.nome) AS nome, any_value(ca.sigla_uf) AS uf,
       any_value(ca.sigla_partido) AS partido, any_value(ca.cargo) AS cargo,
       {somas},
       COALESCE(SUM(bcat.v), 0) AS total
FROM ca
JOIN pes ON pes.cpf = ca.cpf
LEFT JOIN bcat ON bcat.seq = ca.sequencial AND bcat.ano = ca.ano
GROUP BY ca.cpf, ca.ano
ORDER BY ca.cpf, ca.ano;
"""

SQL_MANDATOS = """SET enable_progress_bar=false;
WITH el AS (
  SELECT DISTINCT ano, cargo, sequencial_candidato AS seq
  FROM read_parquet('~/rodado/br_tse_eleicoes/resultados_candidato_municipio/*.parquet')
  WHERE resultado IN ('eleito por media','eleito por qp') AND ano>=2002
),
ca AS (
  SELECT ano, sequencial, cpf FROM read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet')
  WHERE ano>=2002 AND cpf IS NOT NULL AND cpf<>''
)
SELECT DISTINCT ca.cpf, el.ano, el.cargo
FROM el JOIN ca ON ca.ano=el.ano AND ca.sequencial=el.seq
ORDER BY 1,2;
"""

SQL_EMPRESAS = """SET enable_progress_bar=false;
WITH el AS (
  SELECT DISTINCT ano, sequencial_candidato AS seq
  FROM read_parquet('~/rodado/br_tse_eleicoes/resultados_candidato_municipio/*.parquet')
  WHERE cargo='deputado federal'
    AND resultado IN ('eleito por media','eleito por qp') AND ano>=2010
),
ca AS (
  SELECT ano, sequencial, cpf, nome FROM read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet')
  WHERE ano>=2010 AND cpf IS NOT NULL AND cpf<>''
),
pes AS (
  SELECT ca.cpf, any_value(ca.nome) AS nome
  FROM el JOIN ca ON ca.ano=el.ano AND ca.sequencial=el.seq GROUP BY ca.cpf
),
soc AS (
  SELECT DISTINCT p.cpf, s.cnpj_basico
  FROM pes p
  JOIN read_parquet('~/rodado/br_me_cnpj/socios/*.parquet') s
    ON UPPER(strip_accents(TRIM(s.nome))) = UPPER(strip_accents(TRIM(p.nome)))
   AND SUBSTR(s.documento,4,6) = SUBSTR(p.cpf,4,6)
   AND s.qualificacao IN {qualif}
),
ult AS (
  SELECT cnpj_basico, MAX(ano*100+mes) AS snap
  FROM read_parquet('~/rodado/br_me_cnpj/empresas/*.parquet')
  WHERE cnpj_basico IN (SELECT cnpj_basico FROM soc) GROUP BY 1
),
cap AS (
  SELECT e.cnpj_basico, ANY_VALUE(e.razao_social) AS razao,
         ANY_VALUE(e.capital_social) AS capital
  FROM read_parquet('~/rodado/br_me_cnpj/empresas/*.parquet') e
  JOIN ult ON ult.cnpj_basico=e.cnpj_basico AND ult.snap=e.ano*100+e.mes
  GROUP BY 1
)
-- uma linha por empresa, não por pessoa: a contagem e a soma de capital saem
-- daqui mesmo, no Python, e a razão social vai junto para o painel poder
-- dizer de que empresas se trata. O CNPJ fica de fora de propósito: o
-- casamento é por nome + seis dígitos do CPF e admite homônimo, então
-- publicar o número do cadastro daria à ligação uma precisão que ela não tem.
SELECT soc.cpf, cap.razao, COALESCE(cap.capital, 0) AS capital
FROM soc LEFT JOIN cap ON cap.cnpj_basico = soc.cnpj_basico
ORDER BY soc.cpf, capital DESC, cap.razao;
"""

# Quanto do ciclo de 2026 já estava protocolado quando o painel foi gerado. A
# régua é o total de candidaturas de 2022, o ciclo geral anterior — não é o
# número exato que o prazo vai fechar, mas é a única referência honesta que
# existe antes de 15/08.
SQL_COBERTURA = """SET enable_progress_bar=false;
SELECT
  CAST(count(*) FILTER (WHERE ano = 2026) AS BIGINT) AS agora,
  CAST(count(*) FILTER (WHERE ano = 2022) AS BIGINT) AS base
FROM read_parquet('~/rodado/br_tse_eleicoes/candidatos/*.parquet')
WHERE ano IN (2022, 2026);
"""


def monta_sql(modelo: str) -> str:
    somas = ", ".join(
        f"COALESCE(SUM(bcat.v) FILTER (WHERE bcat.cat='{c}'), 0) AS {c}"
        for c in CATEGORIAS)
    return modelo.format(caso=sql_categoria(), somas=somas,
                         qualif=str(QUALIF_SOCIO))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", default=None,
                    help="caminho do JSON de saída (default: scratchpad)")
    ap.add_argument("--sem-2026", action="store_true",
                    help="descarta o ano de 2026, que está incompleto")
    args = ap.parse_args()

    saida = Path(args.saida) if args.saida else (
        Path(os.environ.get("SCRATCHPAD", "/tmp")) / "patrimonio_dados.json")

    print("consultando o painel…", file=sys.stderr)
    linhas = consulta(monta_sql(SQL_PAINEL))
    print(f"  {len(linhas)} linhas pessoa-ano", file=sys.stderr)

    # 2026 sai da mesma consulta que os outros anos — só precisa ser marcado
    # como provisório, ou descartado quando se quer só o que já fechou.
    if args.sem_2026:
        linhas = [l for l in linhas if int(l["ano"]) != 2026]
        cobertura = None
    else:
        n26 = 0
        for l in linhas:
            if int(l["ano"]) == 2026:
                l["parcial"] = True
                n26 += 1
        c = consulta(SQL_COBERTURA)[0]
        cobertura = 100 * c["agora"] / c["base"] if c["base"] else 0
        print(f"  {n26} declarações de 2026 · o TSE já registrou "
              f"{cobertura:.1f}% do que 2022 teve", file=sys.stderr)

    print("consultando mandatos…", file=sys.stderr)
    mandatos = {}
    for m in consulta(SQL_MANDATOS):
        mandatos.setdefault(m["cpf"], []).append((int(m["ano"]), m["cargo"]))

    print("consultando empresas…", file=sys.stderr)
    empresas = {}
    n_soc = 0
    for e in consulta(monta_sql(SQL_EMPRESAS)):
        reg = empresas.setdefault(e["cpf"], {"n_empresas": 0, "capital": 0.0,
                                             "lista": []})
        reg["n_empresas"] += 1
        reg["capital"] += float(e["capital"] or 0)
        reg["lista"].append([e["razao"] or "—", round(float(e["capital"] or 0))])
        n_soc += 1
    print(f"  {len(empresas)} pessoas com empresa · {n_soc} vínculos",
          file=sys.stderr)

    # ── montagem ────────────────────────────────────────────────────────────
    por_cpf = {}
    for l in linhas:
        por_cpf.setdefault(l["cpf"], []).append(l)

    espectro = json.loads((DADOS / "espectro_partidario.json").read_text("utf-8"))
    mapa_esp = {k: v["espectro"] for k, v in espectro["partidos"].items()}

    # tabelas de intern: partido, cargo e UF viram índice. O payload é
    # dominado por strings repetidas 8.400 vezes — só isso corta mais da
    # metade do arquivo.
    def intern(valores):
        tab = sorted({v for v in valores if v})
        return tab, {v: i for i, v in enumerate(tab)}

    tab_part, ix_part = intern(l["partido"] for l in linhas)
    tab_cargo, ix_cargo = intern(l["cargo"] for l in linhas)
    tab_uf, ix_uf = intern(l["uf"] for l in linhas)
    tab_esp = ["esquerda", "centro", "direita"]
    ix_esp = {v: i for i, v in enumerate(tab_esp)}

    # bits do campo de flags de cada ponto
    F_ELEITO, F_REGUA_PARCIAL, F_ANO_PARCIAL = 1, 2, 4

    pessoas = []
    for cpf, pts in sorted(por_cpf.items()):
        pts.sort(key=lambda p: int(p["ano"]))
        emp = empresas.get(cpf, {})

        # meses de mandato federal desta pessoa, ao longo de toda a vida, e os
        # anos em que ganhou alguma eleição — sem isso não dá para separar
        # quem exerceu mandato de quem apenas concorreu, que é a diferença
        # entre os 472 do artigo e os 774 que a coorte devolve sem o filtro.
        federais, anos_eleito = set(), set()
        for ano_el, cargo in mandatos.get(cpf, []):
            anos_eleito.add(ano_el)
            if cargo in CARGOS_FEDERAIS:
                ini, fim = meses_de_mandato(ano_el)
                federais.update(meses_no_intervalo(ini, fim))

        pontos = []
        for i, p in enumerate(pts):
            ano = int(p["ano"])
            regua = None
            flags = 0
            if ano in anos_eleito:
                flags |= F_ELEITO
            if p.get("parcial"):
                flags |= F_ANO_PARCIAL
            if i > 0:
                # entre a declaração anterior e esta: agosto a agosto, que é
                # quando o registro de candidatura é protocolado
                ini = date(int(pts[i - 1]["ano"]), 8, 1)
                fim = date(ano, 7, 31)
                janela = list(meses_no_intervalo(ini, fim))
                pagos = [m for m in janela if m in federais]
                regua = round(acumulado(pagos))
                if 0 < len(pagos) < len(janela):
                    flags |= F_REGUA_PARCIAL
            comp = [round(float(p[c])) for c in CATEGORIAS]
            pontos.append([
                ano,
                ix_part.get(p["partido"], -1),
                ix_cargo.get(p["cargo"], -1),
                round(float(p["total"])),
                regua,
                flags,
                comp if any(comp) else 0,
            ])

        pessoas.append([
            pts[-1]["nome"],
            ix_uf.get(pts[-1]["uf"], -1),
            ix_esp.get(mapa_esp.get(pts[-1]["partido"]), -1),
            int(emp.get("n_empresas", 0) or 0),
            round(float(emp.get("capital", 0) or 0)),
            pontos,
            emp.get("lista", []),
        ])

    doc = {
        "meta": {
            "gerado": date.today().isoformat(),
            "categorias": CATEGORIAS,
            "partidos": tab_part,
            "cargos": tab_cargo,
            "ufs": tab_uf,
            "espectros": tab_esp,
            "espectro_por_partido": mapa_esp,
            "campos_pessoa": ["nome", "uf", "espectro", "empresas", "capital",
                              "pontos", "empresas_lista"],
            "campos_ponto": ["ano", "partido", "cargo", "total", "regua",
                             "flags", "comp"],
            "flags": {"1": "eleito nessa eleição",
                      "2": "régua parcial — houve período em mandato não federal",
                      "4": "ano ainda incompleto no dado do TSE"},
            "universo": ("pessoas eleitas deputado federal em alguma eleição "
                         "de 2006 a 2022, e todas as candidaturas que "
                         "registraram no período"),
            "pessoas": len(pessoas),
            "declaracoes": sum(len(p[5]) for p in pessoas),
            "anos_parciais": [] if args.sem_2026 else [2026],
            "ressalvas": {
                "valores": "Nominais, a custo de aquisição, como manda a regra do imposto de renda. Não são corrigidos por inflação — e corrigir seria errado: imóvel comprado em 1990 está declarado a preço de 1990.",
                "regua": "Subsídio bruto, antes de imposto e previdência. Só conta meses de mandato federal; período em mandato municipal ou estadual não soma, e o ponto sai marcado como régua parcial.",
                "empresas": "Receita Federal, retrato de setembro de 2024. Casamento por nome e seis dígitos do CPF: há risco de homônimo. É indício, não fato.",
                "2026": (
                    f"Prazo de registro até 15/08/2026. Quando isto foi gerado, "
                    f"o arquivo do TSE trazia "
                    f"{('%.1f' % cobertura).replace('.', ',')}% das candidaturas "
                    f"que 2022 teve. Ausência em 2026 não é ausência de bem — é "
                    f"candidatura ainda não registrada."
                ) if cobertura is not None else "",
                "ausencia": "Pessoa sem declaração num ano pode simplesmente não ter concorrido àquela eleição.",
            },
        },
        "pessoas": pessoas,
    }

    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")),
                     encoding="utf-8")
    kb = saida.stat().st_size / 1024
    print(f"ok: {saida} · {len(pessoas)} pessoas · "
          f"{doc['meta']['declaracoes']} declarações · {kb:.0f} KB",
          file=sys.stderr)


if __name__ == "__main__":
    main()
