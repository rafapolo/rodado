/**
 * O prefixo estável — um só system prompt para TODAS as etapas do laço.
 *
 * Por que um só: o llama-server reaproveita o KV do prefixo comum, e o ganho
 * medido é 44x (1.165 tokens caem de 19,5 s para 0,44 s). Um system prompt por
 * etapa daria um prefixo por etapa, e cada pergunta pagaria o prefill inteiro
 * quatro vezes. Com um prefixo só, a etapa vai no *user message* e o prefixo
 * fica intacto do começo ao fim da avaliação.
 *
 * Consequência prática: **nada aqui pode variar entre chamadas.** Sem timestamp,
 * sem ordem de Set/Map, sem embaralhar exemplo. `Resposta.prefilados` é o
 * detector — se parar de ficar em ~dezenas, alguma coisa passou a variar.
 */
import { readFileSync } from "node:fs";
import { parse } from "yaml";
import { listaDatasets } from "./catalogo.ts";
import type { Caso } from "./casos.ts";

const RAIZ = new URL("..", import.meta.url).pathname;

interface Bridges {
  false_friends?: Record<string, unknown>;
  coded_differently?: Record<string, unknown>;
}

interface Desambiguacao {
  descricoes: Record<string, string>;
}

/**
 * Item 1 do backlog: 24 das 36 falhas da rodada de 274 foram o modelo
 * escolhendo o dataset irmão errado (`ibge_ppm` por `ibge_pam`, `me_caged` por
 * `me_rais`...). `harness/dados/desambiguacao.json` guarda a frase curta e
 * contrastiva que separa cada par — só onde há ambiguidade, nunca um glossário
 * do catálogo inteiro (isso estouraria o orçamento de contexto do item 4).
 */
function descricoesDeDesambiguacao(): Record<string, string> {
  const d = JSON.parse(
    readFileSync(new URL("./dados/desambiguacao.json", import.meta.url), "utf8"),
  ) as Desambiguacao;
  return d.descricoes;
}

/** Só as duas seções de perigo. `concepts` + `bridges` são 15.758 tokens e vão
 *  sob demanda via resolve_join; false_friends + coded_differently são 2.538 e
 *  precisam estar SEMPRE visíveis: `valor` aparece em 91 tabelas de 56 datasets
 *  significando coisas diferentes, e juntar por ele dá resultado grande,
 *  plausível e errado. */
function perigos(): string {
  const b = parse(readFileSync(`${RAIZ}docs/context/bridges.yaml`, "utf8")) as Bridges;
  const ff = Object.keys(b.false_friends ?? {}).sort();
  const cd = Object.keys(b.coded_differently ?? {}).sort();
  return (
    `COLUNAS QUE PARECEM A MESMA E NÃO SÃO (nunca junte por elas):\n  ${ff.join(", ")}\n` +
    `CÓDIGO QUE DIVERGE ENTRE DATASETS (não compare com literal; decodifique pelo dicionario do dataset):\n  ${cd.join(", ")}`
  );
}

const REGRAS = `REGRAS DO ESPELHO — quebrar qualquer uma faz a consulta ser rejeitada:
1. Tabela grande exige filtro de partição: WHERE ano = ... (e sigla_uf quando o recorte for estadual).
2. Escreva sempre dataset.tabela. Nunca só o dataset.
3. Consulta sem agregação precisa de LIMIT.
4. CID-10 é guardado SEM ponto ('X840'). Faixa se faz com substr(coluna,1,3) BETWEEN 'X60' AND 'X84'.
   Comparar a coluna crua com BETWEEN perde a última categoria inteira, calado.
5. Dialeto é DuckDB. Nada de BigQuery.`;

const ETAPAS = `ETAPAS. Cada mensagem começa com "ETAPA <nome>". Responda no formato pedido, sem explicação:
- ETAPA datasets  -> só os nomes dos datasets, separados por vírgula.
- ETAPA tabelas   -> só os nomes dataset.tabela, separados por vírgula.
- ETAPA sql       -> só a consulta SQL DuckDB, sem markdown, sem comentário.
- ETAPA prosa     -> um parágrafo em português citando os números recebidos.`;

/** Nome do catálogo, com a descrição contrastiva grudada só onde há dataset
 *  irmão — a maioria das linhas fica como estava. */
function linhaCatalogo(dataset: string, desc: Record<string, string>): string {
  const d = desc[dataset];
  return d ? `${dataset} — ${d}` : dataset;
}

export function montaPrefixo(exemplos: Caso[]): string {
  const desc = descricoesDeDesambiguacao();
  const partes = [
    "Você consulta o espelho de dados públicos brasileiros do projeto rodado.",
    "",
    `CATÁLOGO — os ${listaDatasets().length} datasets, um por linha ` +
      "(com uma pista curta nos que têm irmão fácil de confundir):",
    listaDatasets().map((d) => linhaCatalogo(d, desc)).join("\n"),
    "",
    REGRAS,
    "",
    perigos(),
    "",
    ETAPAS,
  ];
  if (exemplos.length) {
    // Os exemplos carregam a MARCA DA ETAPA a que pertencem. Sem isso eles
    // dominam: medido, o modelo respondia datasets também quando a mensagem
    // pedia "ETAPA tabelas" — chegou a ecoar "ETAPA datasets" na resposta,
    // porque todo exemplo do prefixo tinha essa forma. A marca faz o padrão
    // disparar só na etapa certa.
    partes.push(
      "",
      "EXEMPLOS DA ETAPA datasets, já conferidos no beelink:",
      ...exemplos.map(
        (e) => `ETAPA datasets\nPergunta: ${e.pergunta}\n-> ${e.obrigatorios.map((d) => `br_${d}`).join(", ")}`,
      ),
      "",
      "Os exemplos acima valem SÓ para a ETAPA datasets. Nas outras etapas, siga o formato da etapa pedida.",
    );
  }
  return partes.join("\n");
}
