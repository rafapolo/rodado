(function(){
"use strict";
fetch("dados.json").then(r=>r.json()).then(function(D){
const M = D.meta, PESSOAS = D.pessoas;
const [NOME,UF,ESP,EMP,CAP,PTS] = [0,1,2,3,4,5];
const [ANO,PART,CARGO,TOTAL,REGUA,FLAGS,COMP] = [0,1,2,3,4,5,6];
const F_ELEITO=1, F_REGUA_PARCIAL=2, F_ANO_PARCIAL=4;
const CAT_ROTULO = {imovel:"imóveis",veiculo:"veículos",dinheiro:"dinheiro",
  aplicacao:"aplicações",societaria:"participações societárias",
  credito:"créditos",outros:"outros"};
const CAT_COR = ["#7d6b58","#8a8f7e","#5d7f88","#6f8fa8","#c2683c","#9a7f9c","#a9b2ac"];

/* ── derivados por pessoa, calculados uma vez ───────────────────────────── */
PESSOAS.forEach((p,i)=>{
  const pts = p[PTS];
  p.i = i;
  p.chave = p[NOME].normalize("NFD").replace(/[\u0300-\u036f]/g,"").toUpperCase();
  p.ultimo = pts[pts.length-1];
  p.primeiro = pts[0];
  p.patrimonio = p.ultimo[TOTAL];
  p.partidoAtual = p.ultimo[PART] >= 0 ? M.partidos[p.ultimo[PART]] : null;
  p.crescimento = p.ultimo[TOTAL] - p.primeiro[TOTAL];
  p.regua = pts.reduce((s,x)=> s + (x[REGUA]||0), 0);
  // Piso da régua: cerca de doze meses de subsídio. Sem ele, quem passou só
  // uns poucos meses em mandato federal dentro da janela entre duas
  // declarações ganha uma régua de valor ínfimo, e a divisão devolve
  // múltiplos absurdos — 92.495× no caso que apareceu no teste. Régua curta
  // não mede: essas pessoas entram como "sem régua comparável", que é o que
  // de fato são.
  p.multiplo = p.regua >= 200000 ? p.crescimento / p.regua : null;
  p.mandatos = pts.filter(x=> x[FLAGS] & F_ELEITO).length;
  p.parcial = pts.some(x=> x[FLAGS] & F_ANO_PARCIAL);
});

/* ── formatação ─────────────────────────────────────────────────────────── */
const nf = new Intl.NumberFormat("pt-BR");
function brl(v){
  const a = Math.abs(v), s = v<0 ? "−" : "";
  if(a >= 1e6) return s+"R$ "+(a/1e6).toFixed(a>=1e7?0:1).replace(".",",")+" mi";
  if(a >= 1e3) return s+"R$ "+Math.round(a/1e3)+" mil";
  return s+"R$ "+nf.format(Math.round(a));
}
function mult(v){
  if(v === null) return "—";
  return (v<0?"−":"")+Math.abs(v).toFixed(Math.abs(v)<10?1:0).replace(".",",")+"×";
}
function corMult(v){
  if(v === null) return "var(--ink3)";
  return v > 1 ? "var(--acima)" : "var(--abaixo)";
}

/* ── estado ─────────────────────────────────────────────────────────────── */
const est = {q:"", espectro:new Set(), partido:"", uf:"",
             empresa:false, regua:false, acima:false,
             aba:"panorama", sel:null, fixados:[],
             ordem:"multiplo", limite:120};

function leHash(){
  const h = new URLSearchParams(location.hash.slice(1));
  est.q = h.get("q") || "";
  est.espectro = new Set((h.get("e")||"").split(",").filter(Boolean));
  est.partido = h.get("p") || "";
  est.uf = h.get("uf") || "";
  est.empresa = h.get("emp") === "1";
  est.regua = h.get("reg") === "1";
  est.acima = h.get("ac") === "1";
  est.aba = ["panorama","dossie"].includes(h.get("aba")) ? h.get("aba") : "panorama";
  est.ordem = ORDENS[h.get("ord")] ? h.get("ord") : "multiplo";
  est.limite = 120;
  est.sel = h.has("i") ? +h.get("i") : null;
  est.fixados = (h.get("fx")||"").split(",").filter(Boolean).map(Number);
}
function gravaHash(){
  const h = new URLSearchParams();
  if(est.q) h.set("q", est.q);
  if(est.espectro.size) h.set("e", [...est.espectro].join(","));
  if(est.partido) h.set("p", est.partido);
  if(est.uf) h.set("uf", est.uf);
  if(est.empresa) h.set("emp","1");
  if(est.regua) h.set("reg","1");
  if(est.acima) h.set("ac","1");
  if(est.aba !== "panorama") h.set("aba", est.aba);
  if(est.ordem !== "multiplo") h.set("ord", est.ordem);
  if(est.sel !== null) h.set("i", est.sel);
  if(est.fixados.length) h.set("fx", est.fixados.join(","));
  history.replaceState(null, "", "#" + h.toString());
}

/* ── filtro ─────────────────────────────────────────────────────────────── */
function filtra(){
  const q = est.q.normalize("NFD").replace(/[\u0300-\u036f]/g,"").toUpperCase().trim();
  return PESSOAS.filter(p=>{
    if(q && !p.chave.includes(q)) return false;
    if(est.espectro.size){
      const e = p[ESP] >= 0 ? M.espectros[p[ESP]] : "sem";
      if(!est.espectro.has(e)) return false;
    }
    if(est.partido && p.partidoAtual !== est.partido) return false;
    if(est.uf && (p[UF] < 0 || M.ufs[p[UF]] !== est.uf)) return false;
    if(est.empresa && !p[EMP]) return false;
    if(est.regua && p.multiplo === null) return false;
    if(est.acima && !(p.multiplo > 1)) return false;
    return true;
  });
}

/* ── controles ──────────────────────────────────────────────────────────── */
const el = id => document.getElementById(id);
const ESPECTROS = [["esquerda","esq"],["centro","cen"],["direita","dir"],["sem","sem"]];

function montaControles(){
  el("fEspectro").innerHTML = ESPECTROS.map(([e,c])=>
    `<button class="chip ${c}" type="button" data-e="${e}" aria-pressed="false">${
      e === "sem" ? "sem classificação" : e}</button>`).join("");
  el("fEspectro").onclick = ev=>{
    const b = ev.target.closest("[data-e]"); if(!b) return;
    const e = b.dataset.e;
    est.espectro.has(e) ? est.espectro.delete(e) : est.espectro.add(e);
    vista = null; est.limite = 120; desenha();
  };
  const partidos = [...new Set(PESSOAS.map(p=>p.partidoAtual).filter(Boolean))].sort();
  el("fPartido").innerHTML = '<option value="">todos</option>' +
    partidos.map(p=>`<option>${p}</option>`).join("");
  const ufs = [...new Set(PESSOAS.map(p=> p[UF]>=0 ? M.ufs[p[UF]] : null)
    .filter(Boolean))].sort();
  el("fUf").innerHTML = '<option value="">todas</option>' +
    ufs.map(u=>`<option>${u}</option>`).join("");

  // busca: addEventListener em vez de oninput (não se perde se algo
  // reatribuir a propriedade), e um respiro de 90ms para que digitar rápido
  // não dispare 2.347 pontos a cada tecla
  let tBusca = 0;
  const campo = el("q");
  const aoBuscar = e=>{
    est.q = e.target.value;
    est.vistaSuja = true;
    clearTimeout(tBusca);
    tBusca = setTimeout(()=>{ vista = null; est.limite = 120; desenha(); }, 90);
  };
  campo.addEventListener("input", aoBuscar);
  campo.addEventListener("search", aoBuscar);   // o "x" nativo do type=search

  el("fPartido").onchange = e=>{ est.partido = e.target.value; vista=null; est.limite=120; desenha(); };
  el("fUf").onchange = e=>{ est.uf = e.target.value; vista=null; est.limite=120; desenha(); };
  el("fEmpresa").onchange = e=>{ est.empresa = e.target.checked; vista=null; est.limite=120; desenha(); };
  el("fRegua").onchange = e=>{ est.regua = e.target.checked; vista=null; est.limite=120; desenha(); };
  el("fAcima").onchange = e=>{ est.acima = e.target.checked; vista=null; est.limite=120; desenha(); };
  el("limpar").onclick = ()=>{
    Object.assign(est,{q:"",espectro:new Set(),partido:"",uf:"",
      empresa:false,regua:false,acima:false});
    vista = null; est.limite = 120; est.ordem = 'multiplo'; sincronizaControles(); desenha();
  };
  el("gaveta").onclick = ()=>{
    const r = el("rail"), aberto = r.dataset.aberto === "true";
    r.dataset.aberto = String(!aberto);
    el("gaveta").setAttribute("aria-expanded", String(!aberto));
  };
  document.querySelectorAll(".aba").forEach(b=> b.onclick = ()=>{
    est.aba = b.dataset.aba; desenha();
  });
  el("btnTema").onclick = ()=>{
    const atual = document.documentElement.getAttribute("data-theme");
    const escuro = atual ? atual === "dark"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    document.documentElement.setAttribute("data-theme", escuro ? "light" : "dark");
    desenha();
  };
}
function sincronizaControles(){
  // só escreve no campo quando difere: reatribuir o mesmo valor joga o cursor
  // para o fim e atrapalha quem está corrigindo o meio da palavra
  const campo = el("q");
  if(campo.value !== est.q) campo.value = est.q;
  const nFiltros = est.espectro.size + (est.partido?1:0) + (est.uf?1:0)
    + (est.empresa?1:0) + (est.regua?1:0) + (est.acima?1:0);
  const selo = el("gavetaSelo");
  if(selo) selo.textContent = nFiltros ? `${nFiltros} ativo${nFiltros>1?"s":""}` : "nenhum";
  el("fPartido").value = est.partido;
  el("fUf").value = est.uf;
  el("fEmpresa").checked = est.empresa;
  el("fRegua").checked = est.regua;
  el("fAcima").checked = est.acima;
  document.querySelectorAll("[data-e]").forEach(b=>
    b.setAttribute("aria-pressed", est.espectro.has(b.dataset.e)));
  document.querySelectorAll(".aba").forEach(b=>
    b.setAttribute("aria-selected", b.dataset.aba === est.aba));
}

/* ── dica flutuante ─────────────────────────────────────────────────────── */
const dica = el("dica");
function mostraDica(html, x, y){
  dica.innerHTML = html; dica.style.opacity = "1";
  const r = dica.getBoundingClientRect();
  dica.style.left = Math.min(x + 14, innerWidth - r.width - 8) + "px";
  dica.style.top = Math.max(8, y - r.height - 12) + "px";
}
const escondeDica = ()=> dica.style.opacity = "0";

/* ── lista lateral ──────────────────────────────────────────────────────── */
const PAGINA = 120;

/* Miniatura da trajetória. Normalizada por pessoa: interessa a forma —
   subiu, caiu, deu salto —, porque a magnitude já está no múltiplo ao lado.
   Ponto final destacado; declaração de ano ainda incompleto sai vazada. */
function faisca(p){
  const v = p[PTS].map(x=>x[TOTAL]);
  const L = 52, A = 17, m = 2.5;
  if(v.length < 2){
    return `<svg class="spark" width="${L}" height="${A}" aria-hidden="true">
      <circle cx="${L-m}" cy="${A/2}" r="2.2" fill="var(--ink3)"/></svg>`;
  }
  const lo = Math.min(...v), hi = Math.max(...v), amp = hi-lo;
  const px = i => m + i/(v.length-1)*(L-2*m);
  const py = x => amp ? (A-m) - (x-lo)/amp*(A-2*m) : A/2;
  const d = v.map((x,i)=>`${px(i).toFixed(1)},${py(x).toFixed(1)}`).join("L");
  const cor = p.multiplo === null ? "var(--ink3)"
            : p.multiplo > 1 ? "var(--acima)" : "var(--abaixo)";
  const ult = p[PTS][p[PTS].length-1];
  return `<svg class="spark" width="${L}" height="${A}" aria-hidden="true">
    <path d="M${d}" fill="none" stroke="${cor}" stroke-width="1.4"
          stroke-linejoin="round" stroke-linecap="round" opacity=".85"/>
    <circle cx="${px(v.length-1).toFixed(1)}" cy="${py(v[v.length-1]).toFixed(1)}"
            r="2.4" fill="${ult[FLAGS]&F_ANO_PARCIAL?"var(--surface)":cor}"
            stroke="${cor}" stroke-width="1.2"/></svg>`;
}

const ORDENS = {
  // quem não tem régua comparável vai para o fim: "—" no topo é a linha que
  // menos informa. O sinal aqui estava invertido e enchia a abertura da lista
  // de gente com uma declaração só.
  multiplo:   ["múltiplo do subsídio", (a,b)=> (a.multiplo===null)-(b.multiplo===null)
                                              || b.multiplo-a.multiplo],
  patrimonio: ["patrimônio declarado",  (a,b)=> b.patrimonio - a.patrimonio],
  crescimento:["variação em reais",     (a,b)=> b.crescimento - a.crescimento],
  empresas:   ["número de empresas",    (a,b)=> b[EMP]-a[EMP] || b.patrimonio-a.patrimonio],
  declaracoes:["declarações na série",  (a,b)=> b[PTS].length-a[PTS].length],
  nome:       ["nome",                  (a,b)=> a.chave.localeCompare(b.chave)],
};

function desenhaLista(res){
  el("contagem").innerHTML =
    `<b>${nf.format(res.length)}</b> de ${nf.format(PESSOAS.length)} pessoas`
    + `<br>${nf.format(res.reduce((s,p)=>s+p[PTS].length,0))} declarações`;

  const sel = el("fOrdem");
  if(sel && sel.dataset.pronto !== "1"){
    sel.innerHTML = Object.entries(ORDENS)
      .map(([k,[r]])=>`<option value="${k}">${r}</option>`).join("");
    sel.dataset.pronto = "1";
    sel.onchange = e=>{ est.ordem = e.target.value; est.limite = PAGINA; desenha(); };
  }
  if(sel) sel.value = est.ordem;

  const lista = el("lista");
  if(!res.length){
    lista.innerHTML = `<p class="nada">Nenhuma pessoa com esses filtros.
      Tente afrouxar o recorte ou <b>limpar os filtros</b>.</p>`;
    return;
  }

  const ord = res.slice().sort(ORDENS[est.ordem][1]);
  const visiveis = ord.slice(0, est.limite);
  lista.innerHTML = visiveis.map(p=>{
    const meta = [p[UF]>=0?M.ufs[p[UF]]:"—", p.partidoAtual||"—",
                  `${p[PTS].length} decl.`];
    if(p[EMP]) meta.push(`${p[EMP]} empr.`);
    return `<button class="item" type="button" data-i="${p.i}" data-e="${p[ESP]}"
      ${est.sel===p.i?'aria-current="true"':""}>
      <span class="nm">${p[NOME]}</span>
      <span class="mult" style="color:${corMult(p.multiplo)}">${mult(p.multiplo)}</span>
      <span class="sub">${meta.join(" · ")}</span>
      ${faisca(p)}
    </button>`;}).join("")
    + (ord.length > est.limite
      ? `<button class="mais" type="button" id="verMais">mostrar mais ${
          nf.format(Math.min(PAGINA, ord.length-est.limite))} de ${
          nf.format(ord.length-est.limite)} restantes</button>` : "");

  const btMais = el("verMais");
  if(btMais) btMais.onclick = ()=>{ est.limite += PAGINA; desenhaLista(filtra()); };

  lista.onclick = ev=>{
    const b = ev.target.closest("[data-i]"); if(!b) return;
    est.sel = +b.dataset.i; est.aba = "dossie"; desenha();
  };
  // navegação por teclado: setas percorrem, Enter/Espaço abrem
  lista.onkeydown = ev=>{
    if(ev.key !== "ArrowDown" && ev.key !== "ArrowUp") return;
    const itens = [...lista.querySelectorAll(".item")];
    const i = itens.indexOf(ev.target.closest(".item"));
    if(i < 0) return;
    ev.preventDefault();
    const alvo = itens[i + (ev.key === "ArrowDown" ? 1 : -1)];
    if(alvo) alvo.focus();
  };
}

/* ── panorama: dispersão em canvas, com zoom e arraste ──────────────────── */
// A vista é guardada em coordenadas de dado — x em log10 de reais, y em
// múltiplos do subsídio — e não em pixels. Isso é o que permite ampliar sem
// aparar valor nenhum: ponto fora da janela some da vista em vez de virar
// fileira falsa colada na borda, que era o defeito da primeira versão.
let vista = null;

/* Moldura padrão, fixa. Ela não muda quando os filtros mudam, e é isso que
   permite comparar dois recortes de cabeça: a linha de 1× fica sempre na
   mesma altura da tela, e as marcas do eixo caem sempre em R$ 1 mil, 10 mil,
   100 mil, 1 mi, 10 mi. Ajustar automaticamente aos dados de cada filtro
   parecia mais esperto e era pior — o gráfico se remexia a cada clique. Quem
   quiser o ajuste tem o botão "ajustar aos dados". */
const VISTA_PADRAO = {x0:3, x1:7.9, y0:-1.5, y1:8};
function vistaInicial(){ return {...VISTA_PADRAO}; }

function vistaAjustada(com){
  if(!com.length) return vistaInicial();
  const xs = com.map(p=> Math.log10(Math.max(p.patrimonio,1e3))).sort((a,b)=>a-b);
  const ys = com.map(p=> p.multiplo).sort((a,b)=>a-b);
  const q = (a,f)=> a[Math.min(a.length-1, Math.max(0, Math.floor(a.length*f)))];
  const y0 = Math.min(-0.5, q(ys,0.01)), y1 = Math.max(2, q(ys,0.985));
  const mx = (q(xs,0.995)-q(xs,0.005))*0.04 || .2;
  return {x0:q(xs,0.005)-mx, x1:q(xs,0.995)+mx,
          y0:y0-(y1-y0)*0.06, y1:y1+(y1-y0)*0.10};
}

/* Passo de grade da escada 1-2-5: em qualquer nível de zoom as marcas caem em
   número redondo, nunca em 0,37×. */
function passoBonito(amp, alvo){
  const bruto = amp/alvo;
  const p = Math.pow(10, Math.floor(Math.log10(bruto)));
  const n = bruto/p;
  return (n<1.5 ? 1 : n<3 ? 2 : n<7 ? 5 : 10) * p;
}

function panorama(res){
  const alvo = el("palcoConteudo");
  alvo.innerHTML = `
    <div class="quadro">
      <div class="ferramentas">
        <button class="bt" id="zMais" type="button" aria-label="aproximar">+</button>
        <button class="bt" id="zMenos" type="button" aria-label="afastar">−</button>
        <button class="bt" id="zReset" type="button">moldura padrão</button>
        <button class="bt" id="zAjusta" type="button">ajustar aos dados</button>
        <span class="dizer" id="zDizer"></span>
      </div>
      <canvas id="cv"></canvas>
      <div class="legenda">
        <span><i class="swatch" style="background:#b2544f"></i>esquerda</span>
        <span><i class="swatch" style="background:#8a8f7e"></i>centro</span>
        <span><i class="swatch" style="background:var(--abaixo)"></i>direita</span>
        <span><i class="swatch" style="background:var(--neutro)"></i>sem classificação</span>
        <span>tamanho do ponto = número de empresas</span>
        <span>role para ampliar · arraste para mover</span>
      </div>
    </div>`;
  const cv = el("cv"), ctx = cv.getContext("2d");
  const css = getComputedStyle(document.documentElement);
  const cor = n => css.getPropertyValue(n).trim();

  const com = res.filter(p=> p.multiplo !== null);
  const sem = res.length - com.length;
  const estreito = innerWidth < 880;
  const ALT = estreito ? 380 : 520;
  if(!vista) vista = vistaInicial();

  let geo = null;   // preenchido a cada pintura, usado pelo apontamento

  function pinta(){
    const dpr = devicePixelRatio || 1;
    const L = cv.clientWidth || 600, A = ALT;
    cv.width = L*dpr; cv.height = A*dpr; cv.style.height = A+"px";
    ctx.setTransform(dpr,0,0,dpr,0,0);
    ctx.clearRect(0,0,L,A);

    const mE = estreito ? 46 : 64, mD = 14, mT = 16, mB = estreito ? 44 : 52;
    const x0=mE, x1=L-mD, y0=mT, y1=A-mB;
    const px = v => x0 + (Math.log10(Math.max(v,1))-vista.x0)/(vista.x1-vista.x0)*(x1-x0);
    const py = v => y1 - (v-vista.y0)/(vista.y1-vista.y0)*(y1-y0);
    const ix = p => Math.pow(10, vista.x0 + (p-x0)/(x1-x0)*(vista.x1-vista.x0));
    const iy = p => vista.y0 + (y1-p)/(y1-y0)*(vista.y1-vista.y0);
    geo = {x0,x1,y0,y1,px,py,ix,iy};

    ctx.save();
    ctx.beginPath(); ctx.rect(x0,y0,x1-x0,y1-y0); ctx.clip();

    ctx.font = '11px ui-monospace,Menlo,monospace';
    ctx.lineWidth = 1;
    // grade horizontal: passo escolhido pela amplitude visível
    const passo = passoBonito(vista.y1-vista.y0, estreito ? 5 : 7);
    ctx.strokeStyle = cor("--rule");
    for(let v=Math.ceil(vista.y0/passo)*passo; v<=vista.y1; v+=passo){
      const y = Math.round(py(v))+.5;
      ctx.beginPath(); ctx.moveTo(x0,y); ctx.lineTo(x1,y); ctx.stroke();
    }
    // grade vertical: uma linha por década de reais
    for(let e=Math.ceil(vista.x0); e<=vista.x1; e++){
      const x = Math.round(px(Math.pow(10,e)))+.5;
      ctx.beginPath(); ctx.moveTo(x,y0); ctx.lineTo(x,y1); ctx.stroke();
    }
    // a régua: a linha de 1×
    if(1>=vista.y0 && 1<=vista.y1){
      const yr = Math.round(py(1))+.5;
      ctx.strokeStyle = cor("--ink2"); ctx.setLineDash([5,4]);
      ctx.beginPath(); ctx.moveTo(x0,yr); ctx.lineTo(x1,yr); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = cor("--ink2"); ctx.textAlign="left"; ctx.textBaseline="bottom";
      ctx.fillText(estreito ? "1× — o que o cargo pagou"
        : "1× — cresceu exatamente o que o cargo pagou", x0+6, yr-5);
    }

    const CORES = [cor("--acima"),"#8a8f7e",cor("--abaixo")];
    let fora = 0;
    com.forEach(p=>{
      const cx = px(p.patrimonio), cy = py(p.multiplo);
      p._x = cx; p._y = cy;
      if(cx<x0-8 || cx>x1+8 || cy<y0-8 || cy>y1+8){ fora++; p._vis=false; return; }
      p._vis = true;
      const r = (estreito?1.9:2.2) + Math.min(p[EMP],9)*.42;
      p._r = r;
      ctx.beginPath(); ctx.arc(cx,cy,r,0,6.284);
      ctx.fillStyle = p[ESP] >= 0 ? CORES[p[ESP]] : cor("--neutro");
      ctx.globalAlpha = est.sel === p.i ? 1 : .62;
      ctx.fill();
      if(est.sel === p.i){
        ctx.globalAlpha=1; ctx.strokeStyle=cor("--ink"); ctx.lineWidth=2;
        ctx.beginPath(); ctx.arc(cx,cy,r+3.5,0,6.284); ctx.stroke();
      }
    });
    ctx.globalAlpha = 1;
    ctx.restore();

    // rótulos dos eixos, fora da área recortada
    ctx.font = '11px ui-monospace,Menlo,monospace';
    ctx.fillStyle = cor("--ink3");
    ctx.textAlign="right"; ctx.textBaseline="middle";
    for(let v=Math.ceil(vista.y0/passo)*passo; v<=vista.y1; v+=passo){
      const casas = passo>=1 ? 0 : passo>=.1 ? 1 : 2;
      const t = (Math.abs(v)<1e-9?0:v).toFixed(casas).replace(".",",");
      ctx.fillText(t+"×", x0-7, py(v));
    }
    ctx.textAlign="center"; ctx.textBaseline="top";
    const ESCALA = {3:"1 mil",4:"10 mil",5:"100 mil",6:"1 mi",7:"10 mi",8:"100 mi"};
    for(let e=Math.ceil(vista.x0); e<=vista.x1; e++){
      if(ESCALA[e]) ctx.fillText(ESCALA[e], px(Math.pow(10,e)), y1+7);
    }
    ctx.textAlign="left";
    ctx.fillText(estreito ? "patrimônio declarado →"
      : "patrimônio declarado no registro mais recente →", x0, y1+24);

    const partes = [];
    if(fora) partes.push(fora+" fora da vista");
    if(sem) partes.push(sem+" sem régua");
    const dz = el("zDizer");
    if(dz) dz.textContent = `${com.length} no gráfico`
      + (partes.length ? " · "+partes.join(" · ") : "");
  }
  pinta();
  if(panorama._resize) removeEventListener("resize", panorama._resize);
  panorama._resize = ()=> pinta();
  addEventListener("resize", panorama._resize, {passive:true});

  /* zoom: mantém fixo o ponto sob o cursor */
  function amplia(fator, ancX, ancY){
    if(!geo) return;
    const ax = geo.ix(ancX), ay = geo.iy(ancY);
    const lx = Math.log10(Math.max(ax,1));
    const nx = (vista.x1-vista.x0)*fator, ny = (vista.y1-vista.y0)*fator;
    if(nx < .05 || nx > 12) return;
    const fx = (lx-vista.x0)/(vista.x1-vista.x0), fy = (ay-vista.y0)/(vista.y1-vista.y0);
    vista = {x0:lx-fx*nx, x1:lx+(1-fx)*nx, y0:ay-fy*ny, y1:ay+(1-fy)*ny};
    pinta();
  }
  cv.addEventListener("wheel", ev=>{
    ev.preventDefault();
    const r = cv.getBoundingClientRect();
    amplia(Math.exp(ev.deltaY*0.0016), ev.clientX-r.left, ev.clientY-r.top);
  }, {passive:false});
  const meio = ()=> geo ? [(geo.x0+geo.x1)/2, (geo.y0+geo.y1)/2] : [0,0];
  el("zMais").onclick = ()=> amplia(0.7, ...meio());
  el("zMenos").onclick = ()=> amplia(1/0.7, ...meio());
  el("zReset").onclick = ()=>{ vista = vistaInicial(); pinta(); };
  el("zAjusta").onclick = ()=>{ vista = vistaAjustada(com); pinta(); };

  /* arraste para mover, e pinça de dois dedos no toque */
  const pts = new Map();
  let base = null;
  cv.addEventListener("pointerdown", ev=>{
    cv.setPointerCapture(ev.pointerId);
    pts.set(ev.pointerId, {x:ev.clientX, y:ev.clientY, moveu:0});
    base = null;
  });
  cv.addEventListener("pointermove", ev=>{
    const a = pts.get(ev.pointerId); if(!a){ aponta(ev); return; }
    const dx = ev.clientX-a.x, dy = ev.clientY-a.y;
    a.moveu += Math.abs(dx)+Math.abs(dy);
    a.x = ev.clientX; a.y = ev.clientY;
    if(pts.size === 2){
      const [p1,p2] = [...pts.values()];
      const d = Math.hypot(p1.x-p2.x, p1.y-p2.y);
      if(base){
        const r = cv.getBoundingClientRect();
        amplia(base/d, (p1.x+p2.x)/2-r.left, (p1.y+p2.y)/2-r.top);
      }
      base = d;
      return;
    }
    if(!geo) return;
    const ex = (vista.x1-vista.x0)/(geo.x1-geo.x0), ey = (vista.y1-vista.y0)/(geo.y1-geo.y0);
    vista = {x0:vista.x0-dx*ex, x1:vista.x1-dx*ex,
             y0:vista.y0+dy*ey, y1:vista.y1+dy*ey};
    pinta();
  });
  function solta(ev){
    const a = pts.get(ev.pointerId);
    pts.delete(ev.pointerId); base = null;
    // arraste curto conta como clique: abre o dossiê do ponto mais próximo
    if(a && a.moveu < 6 && cv._alvo){ est.sel = cv._alvo.i; est.aba="dossie"; desenha(); }
  }
  cv.addEventListener("pointerup", solta);
  cv.addEventListener("pointercancel", ev=>{ pts.delete(ev.pointerId); base=null; });

  function aponta(ev){
    const r = cv.getBoundingClientRect();
    const mx = ev.clientX-r.left, my = ev.clientY-r.top;
    let achou = null, melhor = 144;
    for(const p of com){
      if(!p._vis) continue;
      const d = (p._x-mx)**2 + (p._y-my)**2;
      if(d < melhor){ melhor = d; achou = p; }
    }
    cv._alvo = achou;
    if(achou && ev.pointerType !== "touch"){
      cv.style.cursor = "pointer";
      mostraDica(`<b>${achou[NOME]}</b><br>${achou.partidoAtual||"—"} · ${
        achou[UF]>=0?M.ufs[achou[UF]]:"—"}<br>declara ${brl(achou.patrimonio)}<br>cresceu ${
        mult(achou.multiplo)} o subsídio${achou[EMP]?`<br>${achou[EMP]} empresa${
        achou[EMP]>1?"s":""}`:""}`, ev.clientX, ev.clientY);
    } else if(!achou){ escondeDica(); cv.style.cursor="grab"; }
  }
  cv.addEventListener("pointerleave", escondeDica);
  cv.addEventListener("dblclick", ()=>{ vista = vistaInicial(); pinta(); });
}

/* ── dossiê ─────────────────────────────────────────────────────────────── */
function dossie(){
  const alvo = el("palcoConteudo");
  const p = est.sel !== null ? PESSOAS[est.sel] : null;
  if(!p){
    alvo.innerHTML = `<p class="vazio">Escolha uma pessoa na lista ao lado, ou
      clique num ponto do panorama, para ver a trajetória declarada dela.</p>`;
    return;
  }
  const pts = p[PTS];
  alvo.innerHTML = `
    <div class="ficha">
      <h2>${p[NOME]}</h2>
      <span class="dado">${p[UF]>=0?M.ufs[p[UF]]:"—"} · <b>${p.partidoAtual||"—"}</b>${
        p[ESP]>=0?" · "+M.espectros[p[ESP]]:" · sem classificação"}</span>
      <span class="dado">declara <b>${brl(p.patrimonio)}</b></span>
      <span class="dado">variação <b style="color:${corMult(p.multiplo)}">${
        brl(p.crescimento)}</b>${p.multiplo!==null?` · ${mult(p.multiplo)} o subsídio`:""}</span>
      <span class="dado">${p.mandatos} mandato${p.mandatos===1?"":"s"}</span>
      ${p[EMP]?`<span class="dado">sócio de <b>${p[EMP]}</b> empresa${
        p[EMP]>1?"s":""} · capital ${brl(p[CAP])}</span>`:""}
    </div>
    <div class="quadro"><div id="trajetoria"></div>
      <div class="legenda">
        <span><i class="swatch" style="background:var(--ink)"></i>patrimônio declarado</span>
        <span><i class="swatch" style="background:var(--abaixo)"></i>subsídio acumulado do mandato</span>
      </div>
    </div>
    <div class="quadro"><div id="composicao"></div>
      <div class="legenda">${M.categorias.map((c,i)=>
        `<span><i class="swatch" style="background:${CAT_COR[i]}"></i>${CAT_ROTULO[c]}</span>`
      ).join("")}</div>
    </div>
    <div class="quadro rolagem">
      <table><thead><tr>
        <th>eleição</th><th>cargo</th><th>partido</th><th>declarado</th>
        <th>variação</th><th>subsídio no período</th><th>múltiplo</th>
      </tr></thead><tbody>${pts.map((x,i)=>{
        const dv = i ? x[TOTAL]-pts[i-1][TOTAL] : null;
        const m = i && x[REGUA] ? dv/x[REGUA] : null;
        return `<tr>
          <td>${x[ANO]} ${x[FLAGS]&F_ELEITO?'<span class="tag t-eleito">eleito</span>':""}${
            x[FLAGS]&F_ANO_PARCIAL?' <span class="tag t-parcial">parcial</span>':""}</td>
          <td>${x[CARGO]>=0?M.cargos[x[CARGO]]:"—"}</td>
          <td>${x[PART]>=0?M.partidos[x[PART]]:"—"}</td>
          <td>${brl(x[TOTAL])}</td>
          <td>${dv===null?"—":brl(dv)}</td>
          <td>${x[REGUA]?brl(x[REGUA]):"—"}${
            x[FLAGS]&F_REGUA_PARCIAL?' <span class="tag t-parcial">parcial</span>':""}</td>
          <td style="color:${corMult(m)}">${m===null?"—":mult(m)}</td>
        </tr>`;}).join("")}</tbody></table>
    </div>`;
  trajetoria(el("trajetoria"), pts);
  composicao(el("composicao"), pts);
}

const SVG = "http://www.w3.org/2000/svg";
function svgEl(n, at){
  const e = document.createElementNS(SVG, n);
  for(const k in at) e.setAttribute(k, at[k]);
  return e;
}
function eixoAnos(g, pts, px, y1){
  pts.forEach(x=>{
    const t = svgEl("text",{x:px(x[ANO]), y:y1+18, "text-anchor":"middle",
      fill:"var(--ink3)", "font-size":11, "font-family":"var(--mono)"});
    t.textContent = x[ANO]; g.appendChild(t);
  });
}

function trajetoria(alvo, pts){
  const L = alvo.clientWidth || 720, A = 300;
  const mE=76, mD=22, mT=16, mB=34;
  const x0=mE, x1=L-mD, y0=mT, y1=A-mB;
  const anos = pts.map(x=>x[ANO]);
  const aMin = Math.min(...anos), aMax = Math.max(...anos);
  const px = a => aMax===aMin ? (x0+x1)/2
    : x0 + (a-aMin)/(aMax-aMin)*(x1-x0);
  // acumula a régua ao longo da série, para virar uma curva comparável
  let acc = 0; const regua = pts.map(x=> acc += (x[REGUA]||0));
  const vMax = Math.max(...pts.map(x=>x[TOTAL]), ...regua, 1);
  const py = v => y1 - (v/vMax)*(y1-y0);

  const s = svgEl("svg",{viewBox:`0 0 ${L} ${A}`, height:A,
                         role:"img","aria-label":"trajetória patrimonial"});
  // grade
  for(let k=0;k<=4;k++){
    const v = vMax*k/4, y = py(v);
    s.appendChild(svgEl("line",{x1:x0,x2:x1,y1:y,y2:y,stroke:"var(--rule)"}));
    const t = svgEl("text",{x:x0-9,y:y+4,"text-anchor":"end",fill:"var(--ink3)",
      "font-size":11,"font-family":"var(--mono)"});
    t.textContent = k ? brl(v) : "0"; s.appendChild(t);
  }
  // régua acumulada
  s.appendChild(svgEl("path",{d:"M"+pts.map((x,i)=>`${px(x[ANO])},${py(regua[i])}`)
    .join("L"), fill:"none", stroke:"var(--abaixo)", "stroke-width":2,
    "stroke-dasharray":"5 4"}));
  // patrimônio
  s.appendChild(svgEl("path",{d:"M"+pts.map(x=>`${px(x[ANO])},${py(x[TOTAL])}`)
    .join("L"), fill:"none", stroke:"var(--ink)", "stroke-width":2.4}));
  pts.forEach(x=>{
    const parcial = x[FLAGS] & F_ANO_PARCIAL;
    s.appendChild(svgEl("circle",{cx:px(x[ANO]), cy:py(x[TOTAL]), r:4.5,
      fill: parcial ? "var(--surface)" : "var(--ink)",
      stroke:"var(--ink)", "stroke-width":2}));
  });
  eixoAnos(s, pts, px, y1);
  alvo.innerHTML = ""; alvo.appendChild(s);
}

/* Composição em barras horizontais, uma por declaração, cada uma normalizada
   a 100%. Vertical e em escala absoluta, como estava antes, a pergunta "de
   que é feito este patrimônio" ficava ilegível: nas declarações pequenas as
   fatias viravam fios de um pixel. Aqui a proporção é sempre legível, e o
   valor absoluto vai ao lado, em texto. */
function composicao(alvo, pts){
  const L = alvo.clientWidth || 720;
  const estreito = L < 520;
  const mE = estreito ? 42 : 52;            // ano
  const mD = estreito ? 78 : 104;           // total em reais
  const linha = 30, gap = 9, mT = 6;
  const x0 = mE, x1 = L - mD, larg = Math.max(x1-x0, 40);
  const A = mT + pts.length*(linha+gap);

  const s = svgEl("svg",{viewBox:`0 0 ${L} ${A}`, height:A, role:"img",
    "aria-label":"composição do patrimônio declarado, por tipo de bem"});

  pts.forEach((x,i)=>{
    const y = mT + i*(linha+gap);
    const comp = x[COMP] || [];
    const soma = comp.reduce((a,b)=>a+b, 0);

    const ano = svgEl("text",{x:x0-10, y:y+linha/2+4, "text-anchor":"end",
      fill:"var(--ink2)","font-size":12,"font-family":"var(--mono)"});
    ano.textContent = x[ANO]; s.appendChild(ano);

    if(!soma){
      s.appendChild(svgEl("rect",{x:x0, y:y+linha/2-1, width:larg, height:2,
        fill:"var(--rule2)"}));
      const nada = svgEl("text",{x:x0+larg+10, y:y+linha/2+4,
        fill:"var(--ink3)","font-size":11.5,"font-family":"var(--mono)"});
      nada.textContent = "nada declarado"; s.appendChild(nada);
      return;
    }

    let acc = 0;
    M.categorias.forEach((c,k)=>{
      const v = comp[k] || 0; if(v <= 0) return;
      const frac = v/soma, w = frac*larg, cx = x0 + (acc/soma)*larg;
      acc += v;
      const r = svgEl("rect",{x:cx, y:y, width:Math.max(w,.7), height:linha,
        fill:CAT_COR[k]});
      const t = svgEl("title");
      t.textContent = `${x[ANO]} · ${CAT_ROTULO[c]}: ${brl(v)} (${
        (frac*100).toFixed(1).replace(".",",")}%)`;
      r.appendChild(t); s.appendChild(r);
      // o rótulo só entra quando cabe sem encavalar
      if(w > 34){
        const pct = svgEl("text",{x:cx+w/2, y:y+linha/2+4, "text-anchor":"middle",
          fill:"#fff","font-size":11,"font-family":"var(--mono)",
          "font-weight":"600"});
        pct.textContent = Math.round(frac*100)+"%";
        s.appendChild(pct);
      }
    });

    const tot = svgEl("text",{x:x0+larg+10, y:y+linha/2+4, fill:"var(--ink2)",
      "font-size":11.5,"font-family":"var(--mono)"});
    tot.textContent = brl(soma)
      + (x[FLAGS]&F_ANO_PARCIAL ? " ·parcial" : "");
    s.appendChild(tot);
  });
  alvo.innerHTML = ""; alvo.appendChild(s);
}

/* ── comparar ───────────────────────────────────────────────────────────── */
function comparar(){
  const alvo = el("palcoConteudo");
  const fx = est.fixados.map(i=>PESSOAS[i]).filter(Boolean);
  if(fx.length < 2){
    alvo.innerHTML = `<p class="vazio">Abra o dossiê de uma pessoa e use
      <b>fixar para comparar</b>. Com duas ou mais fixadas, as trajetórias
      aparecem sobrepostas aqui — em múltiplos do subsídio, para que gerações
      diferentes fiquem comparáveis.
      ${fx.length===1?`<br><br>Fixada até agora: ${fx[0][NOME]}.`:""}</p>`;
    return;
  }
  alvo.innerHTML = `<div class="quadro"><div id="cmp"></div>
    <div class="legenda" id="cmpLeg"></div></div>
    <div class="quadro rolagem"><table><thead><tr>
      <th>pessoa</th><th>declarações</th><th>primeiro</th><th>último</th>
      <th>variação</th><th>subsídio somado</th><th>múltiplo</th><th></th>
    </tr></thead><tbody>${fx.map(p=>`<tr>
      <td>${p[NOME]}</td><td>${p[PTS].length}</td>
      <td>${brl(p.primeiro[TOTAL])}</td><td>${brl(p.patrimonio)}</td>
      <td>${brl(p.crescimento)}</td>
      <td>${p.regua?brl(p.regua):"—"}</td>
      <td style="color:${corMult(p.multiplo)}">${mult(p.multiplo)}</td>
      <td><button class="chip" type="button" data-solta="${p.i}">soltar</button></td>
    </tr>`).join("")}</tbody></table></div>`;
  alvo.onclick = ev=>{
    const b = ev.target.closest("[data-solta]"); if(!b) return;
    est.fixados = est.fixados.filter(i=> i !== +b.dataset.solta); desenha();
  };
  const PALETA = ["#d1453b","#5d7f88","#c2683c","#6f8fa8","#8a8f7e","#9a7f9c"];
  el("cmpLeg").innerHTML = fx.map((p,i)=>
    `<span><i class="swatch" style="background:${PALETA[i]}"></i>${p[NOME]}</span>`).join("");

  const alvoG = el("cmp");
  const L = alvoG.clientWidth || 720, A = 340;
  const mE=68, mD=22, mT=16, mB=34;
  const x0=mE, x1=L-mD, y0=mT, y1=A-mB;
  const anos = [...new Set(fx.flatMap(p=>p[PTS].map(x=>x[ANO])))].sort();
  const aMin = anos[0], aMax = anos[anos.length-1];
  const px = a => aMax===aMin ? (x0+x1)/2 : x0+(a-aMin)/(aMax-aMin)*(x1-x0);

  // cada pessoa vira a curva do patrimônio dividido pela régua acumulada
  const series = fx.map(p=>{
    let acc = 0, base = p.primeiro[TOTAL];
    return p[PTS].map(x=>{
      acc += (x[REGUA]||0);
      return {ano:x[ANO], v: acc > 0 ? (x[TOTAL]-base)/acc : null};
    }).filter(d=> d.v !== null);
  });
  const vals = series.flat().map(d=>d.v);
  const vMax = Math.max(1.2, ...vals), vMin = Math.min(0, ...vals);
  const py = v => y1 - (v-vMin)/(vMax-vMin)*(y1-y0);

  const s = svgEl("svg",{viewBox:`0 0 ${L} ${A}`, height:A, role:"img",
    "aria-label":"comparação de trajetórias"});
  for(let k=0;k<=4;k++){
    const v = vMin + (vMax-vMin)*k/4, y = py(v);
    s.appendChild(svgEl("line",{x1:x0,x2:x1,y1:y,y2:y,stroke:"var(--rule)"}));
    const t = svgEl("text",{x:x0-9,y:y+4,"text-anchor":"end",fill:"var(--ink3)",
      "font-size":11,"font-family":"var(--mono)"});
    t.textContent = mult(v); s.appendChild(t);
  }
  const yr = py(1);
  s.appendChild(svgEl("line",{x1:x0,x2:x1,y1:yr,y2:yr,stroke:"var(--ink2)",
    "stroke-dasharray":"5 4"}));
  const rot = svgEl("text",{x:x0+6,y:yr-6,fill:"var(--ink2)","font-size":11,
    "font-family":"var(--mono)"});
  rot.textContent = "1× — o subsídio explica exatamente"; s.appendChild(rot);
  series.forEach((sr,i)=>{
    if(!sr.length) return;
    s.appendChild(svgEl("path",{d:"M"+sr.map(d=>`${px(d.ano)},${py(d.v)}`).join("L"),
      fill:"none", stroke:PALETA[i], "stroke-width":2.4}));
    sr.forEach(d=> s.appendChild(svgEl("circle",{cx:px(d.ano),cy:py(d.v),r:3.6,
      fill:PALETA[i]})));
  });
  anos.forEach(a=>{
    const t = svgEl("text",{x:px(a),y:y1+18,"text-anchor":"middle",
      fill:"var(--ink3)","font-size":11,"font-family":"var(--mono)"});
    t.textContent = a; s.appendChild(t);
  });
  alvoG.innerHTML = ""; alvoG.appendChild(s);
}

/* ── notas de leitura ───────────────────────────────────────────────────── */
el("notas").innerHTML = `
  <p><b>O que a régua mede.</b> O subsídio é bruto — antes de imposto de renda,
  previdência e de qualquer despesa de viver. Declarar menos do que o cargo pagou
  é o comportamento da maioria da Câmara, não anomalia. O múltiplo mede quanto da
  variação o salário <em>deixa</em> de explicar; é onde a checagem começa, não
  onde ela termina.</p>
  <p><b>Crescer acima da régua não é ilícito.</b> Parlamentar pode ter empresa,
  aluguel, herança, venda de bem, ganho de capital ou renda do cônjuge.</p>
  <p><b>Os valores são nominais.</b> A declaração do TSE segue a regra do imposto
  de renda e registra bens pelo custo de aquisição: imóvel comprado em 1990 segue
  declarado a preço de 1990. Por isso nada aqui é corrigido pela inflação —
  corrigir seria introduzir um valor que a declaração não afirma.</p>
  <p><b>A régua só conta mandato federal.</b> ${M.ressalvas.regua}</p>
  <p><b>Empresas são indício, não fato.</b> ${M.ressalvas.empresas}</p>
  <p><b>2026 está incompleto.</b> ${M.ressalvas["2026"]}</p>
  <p><b>Ausência não é omissão.</b> ${M.ressalvas.ausencia}</p>
  <p style="color:var(--ink3)">Universo: ${M.universo}. ${nf.format(M.pessoas)}
  pessoas, ${nf.format(M.declaracoes)} declarações. Fontes: Tribunal Superior
  Eleitoral (declarações de bens dos registros de candidatura), Câmara dos
  Deputados (decretos legislativos que fixaram o subsídio) e Receita Federal
  (quadro societário). Dados extraídos em ${M.gerado}.</p>`;

/* ── ciclo ──────────────────────────────────────────────────────────────── */
function desenha(){
  sincronizaControles();
  const res = filtra();
  desenhaLista(res);
  if(est.aba === "panorama") panorama(res);
  else if(est.aba === "dossie") dossie();
  else dossie();
  gravaHash();
}

leHash();
montaControles();
desenha();
addEventListener("hashchange", ()=>{ leHash(); desenha(); });
});
})();