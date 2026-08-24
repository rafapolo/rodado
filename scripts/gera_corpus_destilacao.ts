#!/usr/bin/env bun
/**
 * Corpus de destilação: converte os sobreviventes do oráculo + exemplares
 * verificados em JSONL de chat para `mlx_lm.lora`.
 *
 *   bun run scripts/gera_corpus_destilacao.ts
 *   # -> tasks/corpus_destilacao/{train,jsonl,valid.jsonl}
 *
 * Formato de cada linha (chat):
 *   {"messages":[{"role":"system","content":SISTEMA},
 *                {"role":"user","content":"TABELAS...\nPERGUNTA: q"},
 *                {"role":"assistant","content":"<sql>"}]}
 *
 * Só entra par com SQL que RODOU e passou na sanção — corpus aspiracional
 * ensina o modelo a escrever SQL bonito que não roda.
 */
import { readFileSync, writeFileSync, mkdirSync, existsSync, readdirSync } from "node:fs";

const META = JSON.parse(readFileSync("web/static/index/meta.json", "utf-8"));
const COLUNAS = JSON.parse(readFileSync("web/static/index/colunas.json", "utf-8"));
const EXEMPLOS = JSON.parse(readFileSync("web/static/index/exemplos.json", "utf-8")).exemplos;

// lê todos os pedaços do oráculo (workers paralelos escrevem arquivos separados)
const ORACULO: Record<string, any> = {};
for (const f of readdirSync("tasks").filter((f) => /^oraculo_resultados.*\.json$/.test(f))) {
  Object.assign(ORACULO, JSON.parse(readFileSync(`tasks/${f}`, "utf-8")));
}

const SISTEMA = `Você escreve SQL DuckDB sobre o acervo rodado (dados públicos brasileiros).

REGRAS
- Responda APENAS com o SQL. Sem explicação, sem markdown, sem \`\`\`.
- Sempre qualifique a tabela: dataset.tabela. "dataset." nunca é prefixo de coluna.
- Agregue: SUM/COUNT com GROUP BY, corr() para correlação entre dois fenômenos.
  Correlação de pesquisa: CTEs que agregam cada fonte por id_municipio+ano,
  join, corr(a.x, b.y) e count(*) como n.
- Filtre ano/mes/sigla_uf/id_municipio sempre que existirem (partições).
- Valores de texto em minúscula; datasets codificados resolvem pelo .dicionario.
- Use SOMENTE colunas do DDL dado. Não invente.
- Mostre NOME juntando com br_bd_diretorios_brasil.municipio (id_municipio, nome)
  ou .uf — ATENÇÃO: .uf usa coluna SIGLA, não sigla_uf. Ex.: u.sigla = o.sigla_uf.
- Impossível com estas tabelas? Responda exatamente {"error": "motivo"}.`;

function ddlDe(ids: string[]) {
  return ids.map((id) => {
    const cols = (COLUNAS[id] ?? []).slice(0, 20).map((c: any) => `${c.n}:${c.t}`).join(" ");
    return `${id}: ${cols}`;
  }).join("\n");
}

const pares: any[] = [];

// ---- sobreviventes do oráculo ----------------------------------------------
for (const [codigo, reg: any] of Object.entries<any>(ORACULO)) {
  if (reg.status !== "ok" || !reg.sql || !reg.q) continue;
  pares.push({
    origem: `oraculo:${codigo}`,
    messages: [
      { role: "system", content: SISTEMA },
      { role: "user", content: `TABELAS DISPONÍVEIS\n${ddlDe(reg.tabelas)}\nPERGUNTA: ${reg.q}` },
      { role: "assistant", content: reg.sql },
    ],
  });
}

// ---- exemplares verificados (docs/context/exemplos_sql.yaml) ----------------
for (const e of EXEMPLOS) {
  // pergunta canônica sintética: o gatilho é o que chega do usuário
  const q = `Exemplo de pergunta de pesquisa sobre ${e.datasets.join(" × ")} (${(e.gatilhos ?? []).slice(0, 2).join("/")}) — produza a mesma estrutura.`;
  pares.push({
    origem: `exemplar:${e.id}`,
    messages: [
      { role: "system", content: SISTEMA },
      { role: "user", content: `TABELAS DISPONÍVEIS\n${ddlDe(e.datasets.map((d: string) => `${d}.*`))}\nPERGUNTA: ${q}` },
      { role: "assistant", content: e.sql },
    ],
  });
}

if (pares.length < 20) {
  console.error(`corpus pequeno demais (${pares.length}) — rode mais do oráculo antes de treinar.`);
}

mkdirSync("tasks/corpus_destilacao", { recursive: true });
const embaralhado = [...pares].sort(() => Math.random() - 0.5);
const corte = Math.max(1, Math.floor(embaralhado.length * 0.9));
const j = (arr: any[]) => arr.map((p) => JSON.stringify(p)).join("\n") + "\n";
writeFileSync("tasks/corpus_destilacao/train.jsonl", j(embaralhado.slice(corte)));
writeFileSync("tasks/corpus_destilacao/valid.jsonl", j(embaralhado.slice(0, corte)));

console.log(`${embaralhado.length} pares (${embaralhado.length - corte} validação)`);
for (const p of embaralhado.slice(0, 3)) console.log(`  ${p.origem}`);
