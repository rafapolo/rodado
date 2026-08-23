/**
 * Gráficos em canvas 2D, sem biblioteca — mesmo idioma do pages/atlas.
 *
 * Série única sempre: o contrato é {tipo, x, y}, uma medida por uma dimensão.
 * Por isso não há paleta categórica nem legenda — o título nomeia a série
 * (regra da skill dataviz). A cor de acento foi validada para contraste ≥3:1
 * contra as duas superfícies do site.
 */
const css = (n) => getComputedStyle(document.body).getPropertyValue(n).trim();

const fmt = (v) => {
  if (typeof v !== "number") return String(v);
  if (Number.isInteger(v) && Math.abs(v) < 1e6) return v.toLocaleString("pt-BR");
  if (Math.abs(v) >= 1e9) return (v / 1e9).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " bi";
  if (Math.abs(v) >= 1e6) return (v / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 }) + " mi";
  if (Math.abs(v) >= 1e3) return v.toLocaleString("pt-BR", { maximumFractionDigits: 0 });
  return v.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
};

export function desenhar(canvas, spec, linhas) {
  const { tipo, x, y, titulo } = spec;
  const dados = linhas
    .map((r) => ({ rot: String(r[x] ?? ""), val: Number(r[y]) }))
    .filter((d) => Number.isFinite(d.val))
    .slice(0, 40);
  if (!dados.length) return false;

  const dpr = devicePixelRatio || 1;
  const L = 64, R = 20, T = titulo ? 34 : 14, B = 68;
  const W = canvas.clientWidth, H = 320;
  canvas.width = W * dpr; canvas.height = H * dpr;
  canvas.style.height = H + "px";
  const c = canvas.getContext("2d");
  c.setTransform(dpr, 0, 0, dpr, 0, 0);
  c.clearRect(0, 0, W, H);

  const ink = css("--ink") || "#201d18";
  const faint = css("--ink-faint") || "#77705f";
  const rule = css("--rule") || "#d9d0bd";
  const bg = css("--bg") || "#f6f2ea";
  const acc = css("--accent") || "#9c3b2e";
  const pw = W - L - R, ph = H - T - B;

  if (titulo) {
    c.fillStyle = ink; c.font = "600 14px ui-serif, Charter, Georgia, serif";
    c.textAlign = "left"; c.fillText(titulo, L, 20);
  }

  const vals = dados.map((d) => d.val);
  const max = Math.max(...vals, 0), min = Math.min(...vals, 0);
  const span = max - min || 1;
  const py = (v) => T + ph - ((v - min) / span) * ph;

  // grade recessiva, 4 passos
  c.strokeStyle = rule; c.lineWidth = 1;
  c.fillStyle = faint; c.font = "11px ui-sans-serif, system-ui, sans-serif"; c.textAlign = "right";
  for (let i = 0; i <= 4; i++) {
    const v = min + (span * i) / 4, yy = Math.round(py(v)) + 0.5;
    c.globalAlpha = 0.5; c.beginPath(); c.moveTo(L, yy); c.lineTo(L + pw, yy); c.stroke(); c.globalAlpha = 1;
    c.fillText(fmt(v), L - 8, yy + 4);
  }

  c.fillStyle = acc; c.strokeStyle = acc;

  if (tipo === "linha" || tipo === "dispersao") {
    const px = (i) => L + (dados.length === 1 ? pw / 2 : (i / (dados.length - 1)) * pw);
    if (tipo === "linha") {
      c.lineWidth = 2; c.lineJoin = "round"; c.beginPath();
      dados.forEach((d, i) => (i ? c.lineTo(px(i), py(d.val)) : c.moveTo(px(i), py(d.val))));
      c.stroke();
    }
    // anel de 2px na superfície: marcas sobrepostas seguem separáveis
    for (let i = 0; i < dados.length; i++) {
      c.beginPath(); c.arc(px(i), py(dados[i].val), tipo === "linha" ? 4 : 5, 0, 7);
      c.fillStyle = acc; c.fill();
      c.lineWidth = 2; c.strokeStyle = bg; c.stroke();
    }
    rotulosX(c, dados, px, H - B + 16, faint);
  } else {
    // barras: topo arredondado em 4px, ancorado na linha de base, 2px de folga
    const passo = pw / dados.length, larg = Math.max(2, Math.min(48, passo - 2));
    const base = py(Math.max(0, min));
    dados.forEach((d, i) => {
      const bx = L + i * passo + (passo - larg) / 2;
      const ty = py(d.val), alt = Math.abs(base - ty);
      c.beginPath();
      const r = Math.min(4, larg / 2, alt);
      if (c.roundRect) c.roundRect(bx, Math.min(ty, base), larg, alt, [r, r, 0, 0]);
      else c.rect(bx, Math.min(ty, base), larg, alt);
      c.fill();
    });
    rotulosX(c, dados, (i) => L + i * passo + passo / 2, H - B + 16, faint);
  }

  // rótulo direto seletivo: só o maior, nunca um número em cada marca
  const iMax = vals.indexOf(max);
  if (iMax >= 0 && dados.length > 1) {
    const passo = pw / dados.length;
    const bx = tipo === "barras" ? L + iMax * passo + passo / 2
      : L + (dados.length === 1 ? pw / 2 : (iMax / (dados.length - 1)) * pw);
    c.fillStyle = ink; c.font = "600 11px ui-sans-serif, system-ui, sans-serif"; c.textAlign = "center";
    c.fillText(fmt(max), Math.max(L + 16, Math.min(bx, L + pw - 16)), py(max) - 9);
  }
  return true;
}

function rotulosX(c, dados, px, y, cor) {
  c.fillStyle = cor; c.font = "11px ui-sans-serif, system-ui, sans-serif";
  const passo = Math.ceil(dados.length / 12);
  for (let i = 0; i < dados.length; i++) {
    if (i % passo) continue;
    const t = dados[i].rot.length > 12 ? dados[i].rot.slice(0, 11) + "…" : dados[i].rot;
    c.save(); c.translate(px(i), y);
    if (dados.length > 6) { c.rotate(-Math.PI / 4); c.textAlign = "right"; } else c.textAlign = "center";
    c.fillText(t, 0, 0); c.restore();
  }
}
