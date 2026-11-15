#!/usr/bin/env bun
/**
 * Capa abstrata de cada análise: pages/analises/img/capa-<slug>.webp
 *
 * Linguagem visual: mandala radial pintada, anéis finos soltos e uma faixa
 * pontilhada horizontal atravessando tudo — no centro, um motivo que puxa o
 * tema da análise (fluxo de sankey, rede, gota d'água...).
 *
 * A mesma imagem aparece em duas proporções, sempre com 120px de altura: no
 * cartão (~2,8:1, só o miolo) e no topo da página da análise (~6:1). Por isso
 * a tela é 7:1 e o motivo fica no terço central; as laterais só completam.
 *
 * O SVG tem filtro de turbulência (textura de tinta) — pesado para o navegador
 * repintar num carrossel arrastável — então sai rasterizado em WebP
 * (rsvg-convert + cwebp, ambos do Homebrew). 1680×240 = 2x da altura exibida.
 *
 * Uso: bun scripts/gera_capas.ts [slug...]   (sem argumento: todo o manifest)
 * Análise nova sem entrada em TEMAS ganha paleta e motivo sorteados pelo slug.
 *
 * Lógica da estética, paletas, motivos e o passo a passo de análise nova:
 * docs/tecnico/covers.md — atualizar lá ao mudar algo aqui.
 */
import { readFileSync, writeFileSync, mkdtempSync, rmSync } from "node:fs";
import { join, resolve } from "node:path";
import { tmpdir } from "node:os";

const RAIZ = resolve(import.meta.dir, "..");
const ANALISES = join(RAIZ, "pages", "analises");
const MANIFEST = join(ANALISES, "results", "manifest.json");

const W = 1680, H = 240, CX = W / 2, CY = H / 2;

// ── paletas: [fundo, fundo2, anel, raio A, raio B, miolo, traço] ──
const PALETAS: Record<string, string[]> = {
  turquesa: ["#2aa3c4", "#1d6f9e", "#e8392b", "#f39c1f", "#f7cf2a", "#fbe7c4", "#163a7a"],
  solar: ["#f2b31c", "#e8721f", "#d62f2a", "#3a8fd0", "#f6dd6a", "#fff4d6", "#7a1f1a"],
  violeta: ["#4b2a8c", "#7e2fa3", "#f0a21d", "#e8452c", "#f8d244", "#fff0c9", "#1f164f"],
  floresta: ["#1f8a5a", "#0f5c4a", "#e8452c", "#9bd14a", "#f2c53b", "#eaf6d6", "#0b3328"],
  rubro: ["#d8322a", "#9e1f2b", "#2aa3c4", "#f39c1f", "#f7cf2a", "#fde9d6", "#3a0f14"],
  aurora: ["#e85a8a", "#7d3fb0", "#2fb3c9", "#f6a23a", "#fbe36a", "#fff0f3", "#2a174d"],
  oceano: ["#1e4fa8", "#0f2f72", "#2fc1d6", "#f2b31c", "#e85a3a", "#e3f6fb", "#081a44"],
  terra: ["#c8662a", "#7c3a1d", "#2a9a8a", "#f2b31c", "#e8d27a", "#fbecd6", "#3a1a0c"],
};

type Motivo = (rng: () => number, p: string[]) => string;

// ── utilidades ──
function semente(txt: string): () => number {
  let h = 2166136261;
  for (const c of txt) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
  return () => {
    h = Math.imul(h ^ (h >>> 15), 2246822507);
    h = Math.imul(h ^ (h >>> 13), 3266489909);
    return ((h ^= h >>> 16) >>> 0) / 4294967296;
  };
}
const f = (n: number) => n.toFixed(1);
const pol = (cx: number, cy: number, r: number, a: number) => [cx + r * Math.cos(a), cy + r * Math.sin(a)];
const circ = (cx: number, cy: number, r: number, attrs: string) =>
  `<circle cx="${f(cx)}" cy="${f(cy)}" r="${f(r)}" ${attrs}/>`;

// mandala: anel cheio, cacos radiais alternados, discos internos
function mandala(cx: number, cy: number, R: number, p: string[], rng: () => number, n = 18): string {
  let s = circ(cx, cy, R, `fill="${p[2]}"`);
  s += circ(cx, cy, R * 0.86, `fill="${p[3]}"`);
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + rng() * 0.05;
    const d = (Math.PI / n) * (0.7 + rng() * 0.4);
    const r1 = R * (0.3 + rng() * 0.12), r2 = R * (0.84 - rng() * 0.12);
    const [x1, y1] = pol(cx, cy, r1, a);
    const [x2, y2] = pol(cx, cy, r2, a - d);
    const [x3, y3] = pol(cx, cy, r2, a + d);
    s += `<path d="M${f(x1)},${f(y1)}L${f(x2)},${f(y2)}L${f(x3)},${f(y3)}Z" fill="${i % 2 ? p[4] : p[2]}" opacity="${(0.75 + rng() * 0.25).toFixed(2)}"/>`;
  }
  s += circ(cx, cy, R * 0.44, `fill="${p[1]}"`);
  for (let i = 0; i < 28; i++) {
    const [x, y] = pol(cx, cy, R * 0.47, (i / 28) * Math.PI * 2);
    s += circ(x, y, R * 0.018 + 1, `fill="${p[5]}" opacity="0.9"`);
  }
  s += circ(cx, cy, R * 0.38, `fill="none" stroke="${p[5]}" stroke-width="2" opacity="0.8"`);
  return s;
}

// anéis finos espalhados, como os da referência
function aneis(rng: () => number, p: string[], n: number): string {
  let s = "";
  const cores = [p[6], p[2], p[5], p[3], "#2f7fd0"];
  for (let i = 0; i < n; i++) {
    const x = rng() * W, y = rng() * H, r = 24 + rng() * 110;
    s += circ(x, y, r, `fill="none" stroke="${cores[i % cores.length]}" stroke-width="${f(2 + rng() * 3)}" opacity="${(0.55 + rng() * 0.4).toFixed(2)}"`);
  }
  return s;
}

// faixa pontilhada horizontal — a espinha comum a todas as capas
function faixa(rng: () => number, p: string[]): string {
  let s = `<g filter="url(#brilho)">`;
  for (let x = 0; x < W; x += 6 + rng() * 10) {
    const r = 1.5 + Math.pow(rng(), 2.2) * 6.5;
    const y = CY + (rng() - 0.5) * (r > 4 ? 10 : 18);
    s += circ(x, y, r, `fill="${rng() < 0.85 ? "#fffaf0" : p[4]}" opacity="${(0.65 + rng() * 0.35).toFixed(2)}"`);
  }
  return s + "</g>";
}

// ── motivos centrais, um por tema ──
const LINHA = (p: string[], w = 4) => `fill="none" stroke="${p[5]}" stroke-width="${w}" stroke-linecap="round"`;

const MOTIVOS: Record<string, Motivo> = {
  // fitas de sankey se abrindo da esquerda para a direita
  sankey: (rng, p) => {
    let s = "";
    const larg = [30, 18, 12, 8, 6, 4];
    let yA = CY - 42;
    larg.forEach((w, i) => {
      const y1 = yA + w / 2;
      const y2 = CY - 85 + i * 34 + rng() * 8;
      s += `<path d="M${CX - 200},${f(y1)} C${CX - 50},${f(y1)} ${CX + 50},${f(y2)} ${CX + 200},${f(y2)}" fill="none" stroke="${[p[5], p[4], p[3], p[2], p[5], p[4]][i]}" stroke-width="${w}" opacity="0.85"/>`;
      yA += w + 3;
    });
    return s;
  },
  // rede: nós em anéis com ligações
  rede: (rng, p) => {
    const nos: number[][] = [[CX, CY]];
    for (let i = 0; i < 14; i++) nos.push(pol(CX, CY, 40 + rng() * 80, rng() * Math.PI * 2) as number[]);
    let s = "";
    nos.forEach((a, i) => nos.forEach((b, j) => {
      if (j > i && (i === 0 || rng() < 0.12)) s += `<line x1="${f(a[0])}" y1="${f(a[1])}" x2="${f(b[0])}" y2="${f(b[1])}" stroke="${p[5]}" stroke-width="2" opacity="0.8"/>`;
    }));
    nos.forEach((a, i) => (s += circ(a[0], a[1], i ? 5 + rng() * 6 : 14, `fill="${i ? p[4] : p[5]}" stroke="${p[6]}" stroke-width="2"`)));
    return s;
  },
  // virada: disco partido em duas cores e seta girando
  virada: (rng, p) => {
    const r = 70;
    return `<path d="M${CX},${CY - r} A${r},${r} 0 0 0 ${CX},${CY + r} Z" fill="#d8322a"/>` +
      `<path d="M${CX},${CY - r} A${r},${r} 0 0 1 ${CX},${CY + r} Z" fill="#2f5fc0"/>` +
      `<path d="M${CX - 95},${CY - 30} A100,100 0 0 1 ${CX + 90},${CY - 40}" ${LINHA(p, 5)}/>` +
      `<path d="M${CX + 70},${CY - 58} L${CX + 92},${CY - 38} L${CX + 66},${CY - 22}" ${LINHA(p, 5)}/>`;
  },
  // saúde: pulso + células
  saude: (rng, p) => {
    let s = "";
    for (let i = 0; i < 9; i++) {
      const [x, y] = pol(CX, CY, 30 + rng() * 60, rng() * Math.PI * 2);
      s += circ(x, y, 10 + rng() * 14, `fill="${p[5]}" opacity="0.35" stroke="${p[6]}" stroke-width="1.5"`);
    }
    s += `<path d="M${CX - 200},${CY} H${CX - 50} L${CX - 30},${CY - 60} L${CX - 5},${CY + 55} L${CX + 20},${CY - 30} L${CX + 35},${CY} H${CX + 200}" ${LINHA(p, 5)}/>`;
    return s;
  },
  // laço: seta que volta para si mesma, com moeda no meio
  laco: (rng, p) =>
    `<path d="M${CX + 62},${CY + 30} A68,68 0 1 1 ${CX + 66},${CY - 18}" ${LINHA(p, 7)}/>` +
    `<path d="M${CX + 44},${CY - 30} L${CX + 66},${CY - 16} L${CX + 84},${CY - 38}" ${LINHA(p, 7)}/>` +
    circ(CX, CY, 30, `fill="${p[4]}" stroke="${p[6]}" stroke-width="3"`) +
    `<text x="${CX}" y="${CY + 11}" text-anchor="middle" font-family="Georgia,serif" font-weight="700" font-size="32" fill="${p[6]}">$</text>`,
  // dívida → contrato: moedas empilhadas de um lado, papel do outro
  divida: (rng, p) => {
    let s = "";
    for (let i = 0; i < 5; i++) s += `<ellipse cx="${CX - 80}" cy="${CY + 40 - i * 16}" rx="34" ry="10" fill="${p[4]}" stroke="${p[6]}" stroke-width="2"/>`;
    s += `<rect x="${CX + 50}" y="${CY - 50}" width="64" height="86" rx="4" fill="${p[5]}" stroke="${p[6]}" stroke-width="2"/>`;
    for (let i = 0; i < 4; i++) s += `<line x1="${CX + 60}" x2="${CX + 104}" y1="${CY - 34 + i * 16}" y2="${CY - 34 + i * 16}" stroke="${p[6]}" stroke-width="2"/>`;
    s += `<path d="M${CX - 30},${CY - 10} H${CX + 36}" ${LINHA(p, 5)}/><path d="M${CX + 22},${CY - 22} L${CX + 38},${CY - 10} L${CX + 22},${CY + 2}" ${LINHA(p, 5)}/>`;
    return s;
  },
  // cinco cadastros: cinco círculos sobrepostos
  venn: (rng, p) => {
    let s = "";
    for (let i = 0; i < 5; i++) {
      const [x, y] = pol(CX, CY, 34, (i / 5) * Math.PI * 2 - Math.PI / 2);
      s += circ(x, y, 52, `fill="${[p[2], p[3], p[4], p[5], p[0]][i]}" fill-opacity="0.32" stroke="${p[5]}" stroke-width="3"`);
    }
    return s + circ(CX, CY, 9, `fill="${p[6]}"`);
  },
  // 63 retratos: grade de pontos dentro do círculo
  grade: (rng, p) => {
    let s = "";
    for (let i = 0; i < 9; i++) for (let j = 0; j < 7; j++) {
      const x = CX - 96 + i * 24, y = CY - 72 + j * 24;
      s += circ(x, y, 4 + rng() * 6, `fill="${rng() < 0.2 ? p[2] : p[5]}" stroke="${p[6]}" stroke-width="1.2"`);
    }
    return s;
  },
  // poluentes: chaminés e plumas em espiral
  fumaca: (rng, p) => {
    let s = "";
    [-60, -10, 40].forEach((dx, i) => {
      const h = 50 + i * 15;
      s += `<rect x="${CX + dx}" y="${CY + 80 - h}" width="22" height="${h}" fill="${p[6]}"/>`;
      for (let k = 0; k < 4; k++) s += circ(CX + dx + 11 + k * 18 + rng() * 6, CY + 70 - h - k * 22, 9 + k * 6, `fill="${p[5]}" opacity="${(0.75 - k * 0.15).toFixed(2)}"`);
    });
    return s;
  },
  // três cidades: três emissores de ondas
  ondas: (rng, p) => {
    let s = "";
    [-110, 0, 110].forEach((dx, i) => {
      s += circ(CX + dx, CY, 8, `fill="${p[5]}"`);
      for (let k = 1; k <= 3; k++) s += `<path d="M${CX + dx - k * 14},${CY - k * 16} A${k * 22},${k * 22} 0 0 1 ${CX + dx + k * 14},${CY - k * 16}" ${LINHA(p, 4)} opacity="${(1 - k * 0.2).toFixed(2)}"/>`;
    });
    return s;
  },
  // água: gota e ondas
  agua: (rng, p) => {
    let s = `<path d="M${CX},${CY - 80} C${CX + 20},${CY - 40} ${CX + 52},${CY - 5} ${CX + 52},${CY + 22} A52,52 0 0 1 ${CX - 52},${CY + 22} C${CX - 52},${CY - 5} ${CX - 20},${CY - 40} ${CX},${CY - 80} Z" fill="${p[2]}" stroke="${p[5]}" stroke-width="4"/>`;
    for (let k = 0; k < 3; k++) {
      const y = CY + 10 + k * 18;
      s += `<path d="M${CX - 150},${y} q25,-14 50,0 t50,0 t50,0 t50,0 t50,0 t50,0" ${LINHA(p, 3)} opacity="0.8"/>`;
    }
    return s;
  },
  // patrimônio que cresce mais que o salário: barras subindo acima da linha
  barras: (rng, p) => {
    let s = "";
    for (let i = 0; i < 9; i++) {
      const h = 18 + Math.pow(i / 8, 2.2) * 130;
      s += `<rect x="${CX - 120 + i * 27}" y="${CY + 70 - h}" width="18" height="${h}" fill="${i > 5 ? p[2] : p[5]}" stroke="${p[6]}" stroke-width="2"/>`;
    }
    return s + `<line x1="${CX - 140}" x2="${CX + 140}" y1="${CY + 10}" y2="${CY + 10}" stroke="${p[6]}" stroke-width="3" stroke-dasharray="8 6"/>`;
  },
  // um doador → muitas campanhas
  leque: (rng, p) => {
    let s = "";
    const n = 50;
    for (let i = 0; i < n; i++) {
      const [x, y] = pol(CX, CY, 70 + rng() * 50, (i / n) * Math.PI * 2);
      s += `<line x1="${CX}" y1="${CY}" x2="${f(x)}" y2="${f(y)}" stroke="${p[5]}" stroke-width="1.5" opacity="0.7"/>` + circ(x, y, 3.5, `fill="${p[4]}"`);
    }
    return s + circ(CX, CY, 16, `fill="${p[5]}" stroke="${p[6]}" stroke-width="3"`);
  },
  // escritório: 12 sócios em bloco, cada um abrindo seu leque
  escritorio: (rng, p) => {
    let s = "";
    const socios: number[][] = [];
    for (let i = 0; i < 12; i++) socios.push([CX - 33 + (i % 4) * 22, CY - 22 + Math.floor(i / 4) * 22]);
    socios.forEach(([sx, sy]) => {
      for (let k = 0; k < 8; k++) {
        const [x, y] = pol(CX, CY, 85 + rng() * 45, rng() * Math.PI * 2);
        s += `<line x1="${sx}" y1="${sy}" x2="${f(x)}" y2="${f(y)}" stroke="${p[5]}" stroke-width="1" opacity="0.5"/>` + circ(x, y, 3, `fill="${p[4]}"`);
      }
    });
    s += `<rect x="${CX - 46}" y="${CY - 35}" width="92" height="70" rx="6" fill="${p[6]}" opacity="0.85"/>`;
    socios.forEach(([x, y]) => (s += circ(x, y, 6, `fill="${p[5]}"`)));
    return s;
  },
  // censo: treliça hexagonal
  hexagonos: (rng, p) => {
    let s = "";
    const r = 20;
    for (let i = -4; i <= 4; i++) for (let j = -2; j <= 2; j++) {
      const x = CX + i * r * 1.75 + (j % 2 ? r * 0.875 : 0), y = CY + j * r * 1.5;
      if (Math.hypot(x - CX, y - CY) > 105) continue;
      const pts = Array.from({ length: 6 }, (_, k) => pol(x, y, r * 0.92, (k / 6) * Math.PI * 2 + Math.PI / 6).map(f).join(",")).join(" ");
      s += `<polygon points="${pts}" fill="${rng() < 0.3 ? p[4] : "none"}" fill-opacity="0.7" stroke="${p[5]}" stroke-width="2.5"/>`;
    }
    return s;
  },
  // religião × polarização: campo partido, pontos espalhados dos dois lados
  dividido: (rng, p) => {
    let s = `<line x1="${CX}" x2="${CX}" y1="${CY - 100}" y2="${CY + 100}" stroke="${p[5]}" stroke-width="4"/>`;
    for (let i = 0; i < 70; i++) {
      const [x, y] = pol(CX, CY, rng() * 100, rng() * Math.PI * 2);
      const lado = x < CX ? "#d8322a" : "#2f5fc0";
      s += circ(x, y, 3 + rng() * 5, `fill="${rng() < 0.75 ? lado : p[5]}" stroke="${p[5]}" stroke-width="1"`);
    }
    return s;
  },
  // moradia: casinhas em linha do tempo
  casas: (rng, p) => {
    let s = "";
    for (let i = 0; i < 6; i++) {
      const x = CX - 150 + i * 60, h = 30 + rng() * 25, y = CY + 40;
      s += `<path d="M${x - 20},${y} V${y - h} L${x},${y - h - 22} L${x + 20},${y - h} V${y} Z" fill="${i % 2 ? p[5] : p[4]}" stroke="${p[6]}" stroke-width="2.5"/>`;
    }
    return s;
  },
  // dados de saúde em massa: matriz de quadradinhos + pulso
  matriz: (rng, p) => {
    let s = "";
    for (let i = 0; i < 18; i++) for (let j = 0; j < 9; j++) {
      const x = CX - 108 + i * 12.5, y = CY - 56 + j * 12.5;
      if (Math.hypot(x - CX, y - CY) > 110) continue;
      s += `<rect x="${f(x)}" y="${f(y)}" width="8" height="8" fill="${p[5]}" opacity="${(0.25 + rng() * 0.75).toFixed(2)}"/>`;
    }
    return s + `<path d="M${CX - 180},${CY} H${CX - 40} L${CX - 20},${CY - 50} L${CX + 5},${CY + 45} L${CX + 25},${CY} H${CX + 180}" fill="none" stroke="${p[6]}" stroke-width="5" stroke-linecap="round"/>`;
  },
};

// tema de cada análise: paleta + motivo (o par PT/EN compartilha a mesma capa)
const TEMAS: Record<string, [string, string]> = {
  "para-onde-vai-o-dinheiro-da-uniao": ["turquesa", "sankey"],
  corresponsaveis: ["violeta", "rede"],
  "os-vira-casacas-de-lula-para-bozo": ["solar", "virada"],
  "brazil-public-real-world-data": ["oceano", "matriz"],
  "emenda-que-pagou-a-propria-empresa": ["rubro", "laco"],
  "devedora-antes-fornecedora-depois": ["terra", "divida"],
  "cinco-cadastros-as-mesmas-empresas": ["aurora", "venn"],
  "o-brasil-que-os-dados-revelam": ["floresta", "grade"],
  "what-the-data-reveals-about-brazil": ["floresta", "grade"],
  "poluentes-do-ar-em-nova-friburgo": ["terra", "fumaca"],
  "tres-cidades-tres-comunicacoes": ["violeta", "ondas"],
  "duas-outorgas-mais-agua-que-a-copasa": ["oceano", "agua"],
  "o-salario-nao-explica": ["solar", "barras"],
  "nao-era-um-doador-era-um-escritorio": ["rubro", "escritorio"],
  "o-unico-doador-do-negao": ["turquesa", "leque"],
  "cancer-mata-interna": ["aurora", "saude"],
  "censo-judeus-brasil": ["oceano", "hexagonos"],
  "religiao-x-polarizacao": ["solar", "dividido"],
  ibge13: ["terra", "casas"],
};

function capa(slug: string): string {
  const rng = semente(slug);
  const nomes = Object.keys(PALETAS), motivos = Object.keys(MOTIVOS);
  const [pn, mn] = TEMAS[slug] ?? [nomes[Math.floor(rng() * nomes.length)], motivos[Math.floor(rng() * motivos.length)]];
  const p = PALETAS[pn], motivo = MOTIVOS[mn];
  const sx = (rng() - 0.5) * 60; // desloca um pouco o centro: capas não ficam idênticas no enquadramento

  const manchas = Array.from({ length: 7 }, () =>
    circ(rng() * W, rng() * H, 80 + rng() * 200, `fill="${[p[1], p[0], p[3], p[2]][Math.floor(rng() * 4)]}" opacity="${(0.25 + rng() * 0.3).toFixed(2)}"`)).join("");

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">
<defs>
  <linearGradient id="g" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stop-color="${p[0]}"/><stop offset="1" stop-color="${p[1]}"/></linearGradient>
  <filter id="mancha" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="38"/></filter>
  <filter id="pincel" x="-5%" y="-5%" width="110%" height="110%">
    <feTurbulence type="fractalNoise" baseFrequency="0.035" numOctaves="3" seed="${Math.floor(rng() * 999)}"/>
    <feDisplacementMap in="SourceGraphic" scale="9"/>
  </filter>
  <filter id="papel"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="7"/><feColorMatrix values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.22 0"/></filter>
  <filter id="brilho" x="-10%" y="-200%" width="120%" height="500%"><feGaussianBlur stdDeviation="1.6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
</defs>
<rect width="${W}" height="${H}" fill="url(#g)"/>
<g filter="url(#mancha)">${manchas}</g>
<g filter="url(#pincel)">
  ${mandala(150 + rng() * 140, CY + (rng() - 0.5) * 120, 110 + rng() * 70, p, rng, 10 + Math.floor(rng() * 8))}
  ${mandala(W - 150 - rng() * 140, CY + (rng() - 0.5) * 120, 110 + rng() * 80, p, rng, 10 + Math.floor(rng() * 8))}
  ${mandala(CX + sx, CY, 330, p, rng, 22)}
  ${aneis(rng, p, 14)}
</g>
${faixa(rng, p)}
<g filter="url(#pincel)" transform="translate(${f(sx)},0)">${motivo(rng, p)}</g>
<rect width="${W}" height="${H}" filter="url(#papel)"/>
</svg>`;
}

const itens: { slug: string }[] = JSON.parse(readFileSync(MANIFEST, "utf8"));
const pedidos = process.argv.slice(2);
const slugs = pedidos.length ? pedidos : itens.map((i) => i.slug);
const tmp = mkdtempSync(join(tmpdir(), "capas-"));
try {
  for (const slug of slugs) {
    const svg = join(tmp, `${slug}.svg`), png = join(tmp, `${slug}.png`);
    const destino = join(ANALISES, "img", `capa-${slug}.webp`);
    writeFileSync(svg, capa(slug));
    for (const cmd of [["rsvg-convert", "-o", png, svg], ["cwebp", "-quiet", "-q", "78", png, "-o", destino]]) {
      const r = Bun.spawnSync(cmd);
      if (r.exitCode !== 0) throw new Error(`${cmd[0]} falhou em ${slug}: ${r.stderr}`);
    }
    if (!TEMAS[slug]) console.log(`  ! ${slug}: sem tema em TEMAS, paleta/motivo sorteados`);
    console.log(`  pages/analises/img/capa-${slug}.webp`);
  }
} finally {
  rmSync(tmp, { recursive: true, force: true });
}
