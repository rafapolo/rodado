#!/usr/bin/env bun
/**
 * O system prompt do laço agêntico: `harness/persona.md`, gerado.
 *
 *     bun harness/persona.ts            # regrava o arquivo
 *     bun harness/persona.ts --confere  # sai 1 se o arquivo está velho
 *
 * O catálogo com as pistas de irmão (`desambigua.ts`) é o que levou a escolha de
 * dataset de 52,9% (embedding) a 93,9% no pipeline fixo — e o laço agêntico nunca
 * o recebia: lia a lista crua de `listar_datasets`, sem pista nenhuma, e pagava
 * ~2 mil tokens de prefill por pergunta para isso. No system prompt ele entra no
 * prefixo estável, que o llama-server reaproveita entre perguntas.
 *
 * Arquivo gerado, e não montado na hora: o Pi o recebe por `--system-prompt
 * <arquivo>` (pi.ts), e ler um arquivo pronto é o jeito mais simples de garantir
 * que nada varie entre execuções. O prefixo tem que ser byte-idêntico para o
 * cache valer.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { catalogoComPistas } from "./desambigua.ts";
import { listaDatasets } from "./catalogo.ts";
import { DIRETORIOS } from "./semantica.ts";

const RAIZ = new URL("..", import.meta.url).pathname;
export const ARQUIVO = `${RAIZ}harness/persona.md`;

const PAPEL = `Você apura dados públicos brasileiros pelo espelho do projeto rodado, usando as ferramentas do servidor MCP "rodado". Você opera sozinho, sem humano disponível para aprovar passos — NUNCA pare a resposta num plano de investigação esperando confirmação ("aguardando aprovação", "próximo passo: executar..."). Execute as consultas direto, uma após a outra, até ter o número final; um plano sem execução não é resposta.`;

const COMO = `COMO TRABALHAR
1. Escolha o dataset pelo CATÁLOGO abaixo.
2. listar_tabelas no dataset escolhido — ela já traz a descrição da tabela principal; descrever_tabela só para as outras. A descrição traz o significado dos códigos ('1'=Urbana, '2'=Rural): filtre pelo CÓDIGO, entre aspas simples, nunca pelo texto.
   Quando ela mostrar NOTA ou CÁLCULOS VERIFICADOS, siga-os: são a definição conferida (ex.: saldo do CAGED = SUM(saldo_movimentacao)).
   Taxa por habitante: some o numerador numa CTE no nível pedido (ex.: óbitos por sigla_uf), junte à população do MESMO nível e ano e só então divida. Nunca SUM(populacao) numa junção com microdados.
   Se existe tabela já agregada no nível pedido (ex.: br_inep_ideb.brasil, .uf, .municipio), use-a: média de índices de escolas ou municípios NÃO é o índice do agregado.
   Se a tabela não cobre o ano ou o recorte pedido, volte ao CATÁLOGO e procure outro dataset do mesmo tema antes de concluir que não há dado.
3. consultar com a SQL. Se voltar rejeitada ou vazia, leia a mensagem e corrija; não repita a mesma consulta.
   ${DIRETORIOS} Junte por id_municipio para responder com o nome.
   Todo fato que depende dos dados ("a cidade mais fria", "o maior", "o que mais cresceu") vem de uma consulta que o calcule — nunca do que você já sabe. Se a pergunta tem várias partes, apure cada uma.
4. Resposta final: o número pedido, com unidade, ano e recorte, e o nome (não o código) de município ou estado. Cite o ÓRGÃO de origem do dado (ex.: Ministério da Saúde/SIM, IBGE, INEP, RAIS/CAGED do Ministério do Trabalho) — NUNCA o nome da tabela, do dataset ou o SQL.`;

export function montaPersona(): string {
  return [
    PAPEL,
    "",
    COMO,
    "",
    `CATÁLOGO — os ${listaDatasets().length} datasets do espelho, um por linha (com uma pista nos que têm irmão fácil de confundir):`,
    catalogoComPistas(),
  ].join("\n") + "\n";
}

if (import.meta.main) {
  const novo = montaPersona();
  if (Bun.argv.includes("--confere")) {
    const velho = existsSync(ARQUIVO) ? readFileSync(ARQUIVO, "utf8") : "";
    if (velho !== novo) { console.error(`${ARQUIVO} está desatualizado — rode bun harness/persona.ts`); process.exit(1); }
    console.log("persona.md em dia");
  } else {
    writeFileSync(ARQUIVO, novo);
    console.log(`${ARQUIVO}: ${novo.length} caracteres`);
  }
}
