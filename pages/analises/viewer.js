/* Viewer universal de análises: renderiza qualquer .md em analises/results/
   Uso: analises/<slug>/      → página própria, com metadados de compartilhamento
                                (o shell traz data-slug; gerado por gera_analises.py)
        analises/?doc=<slug>  → mesma coisa, sem metadados próprios; mantido
                                porque links assim já circulam por aí
        analises/             → índice (lê results/manifest.json); se houver só
                                uma análise, abre direto.
   Adicionar uma análise = soltar o .md em results/, uma linha no manifest.json
   e rodar scripts/gera_analises.py (que também chama o gera_seo). A capa
   precisa de uma linha em TEMAS de scripts/gera_capas.ts: docs/tecnico/covers.md. */
(function () {
  var docEl = document.getElementById('doc');
  var eyebrow = document.getElementById('eyebrow');
  // nas páginas próprias o conteúdo fica um nível abaixo de analises/
  var base = docEl.dataset.base || '';
  var slug = docEl.dataset.slug ||
             new URLSearchParams(location.search).get('doc') ||
             (location.hash ? location.hash.slice(1) : '');

  marked.setOptions({ gfm: true, breaks: false });

  function fetchText(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); });
  }
  function fetchJSON(url) {
    return fetch(url).then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; });
  }

  // --- lightbox ------------------------------------------------------------
  // Clicar numa figura abre em tela cheia (ajustada à janela); o clique
  // seguinte vai pro tamanho real, com pan pelo scroll do palco. Imagens que
  // já são link (ex.: o teaser do shutafut) seguem sendo link.
  var box, boxImg, boxCap, boxStage, ultimaFig;

  function montaBox() {
    box = document.createElement('div');
    box.className = 'lightbox';
    box.hidden = true;
    box.setAttribute('role', 'dialog');
    box.setAttribute('aria-modal', 'true');
    box.innerHTML =
      '<button class="lb-close" type="button" aria-label="Fechar (Esc)">&times;</button>' +
      '<div class="lb-stage"><img alt=""></div>' +
      '<p class="lb-cap"></p>';
    boxStage = box.querySelector('.lb-stage');
    boxImg = box.querySelector('img');
    boxCap = box.querySelector('.lb-cap');
    document.body.appendChild(box);

    box.querySelector('.lb-close').addEventListener('click', fecha);
    // clique fora da imagem fecha; na imagem, alterna o zoom
    box.addEventListener('click', function (e) {
      if (e.target === boxImg) alternaZoom(e.clientX, e.clientY);
      else if (e.target === boxStage || e.target === box || e.target === boxCap) fecha();
    });
    document.addEventListener('keydown', function (e) {
      if (!box.hidden && (e.key === 'Escape' || e.key === 'Esc')) fecha();
    });
  }

  function abre(img) {
    if (!box) montaBox();
    ultimaFig = img;
    box.classList.remove('is-zoomed');
    boxImg.src = img.currentSrc || img.src;
    boxImg.alt = img.alt || '';
    boxCap.textContent = img.alt || '';
    box.hidden = false;
    boxStage.scrollTop = boxStage.scrollLeft = 0;
    document.documentElement.style.overflow = 'hidden';
    box.querySelector('.lb-close').focus();
  }

  function fecha() {
    if (!box || box.hidden) return;
    box.hidden = true;
    box.classList.remove('is-zoomed');
    boxImg.removeAttribute('src');
    document.documentElement.style.overflow = '';
    if (ultimaFig) ultimaFig.focus();
  }

  // ao ampliar, o ponto clicado vira o centro da viewport
  function alternaZoom(x, y) {
    if (box.classList.contains('is-zoomed')) {
      box.classList.remove('is-zoomed');
      boxStage.scrollTop = boxStage.scrollLeft = 0;
      return;
    }
    var r = boxImg.getBoundingClientRect();
    var fx = (x - r.left) / r.width, fy = (y - r.top) / r.height;
    box.classList.add('is-zoomed');
    boxStage.scrollLeft = fx * boxImg.offsetWidth - boxStage.clientWidth / 2;
    boxStage.scrollTop = fy * boxImg.offsetHeight - boxStage.clientHeight / 2;
  }

  function ampliavel(img) {
    return img && docEl.contains(img) && !img.closest('a');
  }

  docEl.addEventListener('click', function (e) {
    var img = e.target.closest ? e.target.closest('img') : null;
    if (!ampliavel(img)) return;
    e.preventDefault();
    abre(img);
  });
  docEl.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var img = e.target.closest ? e.target.closest('img') : null;
    if (!ampliavel(img)) return;
    e.preventDefault();
    abre(img);
  });

  // --- âncoras de capítulo ---------------------------------------------------
  // Cada título vira alvo de link (#slug-do-titulo), com um "#" clicável ao
  // lado para copiar o endereço do capítulo. Como o corpo é montado por JS, o
  // salto nativo do navegador para o hash já passou quando os ids existem —
  // por isso o rolar à mão em renderDoc().
  function slugifica(txt) {
    return txt.normalize('NFD').replace(/[\u0300-\u036f]/g, '')
      .toLowerCase().replace(/[^a-z0-9]+/g, '-')
      .slice(0, 60).replace(/^-+|-+$/g, '') || 'secao';
  }

  function ancoraTitulos() {
    var usados = {};
    docEl.querySelectorAll('h2, h3, h4').forEach(function (h) {
      var id = h.id || slugifica(h.textContent);
      if (usados[id]) id += '-' + (++usados[id]);
      else usados[id] = 1;
      h.id = id;
      var a = document.createElement('a');
      a.className = 'anchor';
      a.href = '#' + id;
      a.setAttribute('aria-label', 'Link para esta seção');
      a.textContent = '#';
      h.appendChild(a);
    });
  }

  function vaiProHash() {
    var alvo = location.hash && location.hash.length > 1
      ? docEl.querySelector('[id="' + CSS.escape(location.hash.slice(1)) + '"]')
      : null;
    if (!alvo) return false;
    alvo.scrollIntoView();
    // as figuras entram sem altura declarada: cada uma que termina de carregar
    // empurra o texto abaixo dela e tira o capítulo de baixo do olho. Reancora
    // a cada chegada — e larga o leitor assim que ele rolar por conta própria.
    var solto = false;
    ['wheel', 'touchstart', 'keydown', 'mousedown'].forEach(function (ev) {
      window.addEventListener(ev, function () { solto = true; },
                              { once: true, passive: true });
    });
    docEl.querySelectorAll('img').forEach(function (img) {
      if (img.complete) return;
      img.addEventListener('load', function () {
        if (!solto) alvo.scrollIntoView();
      });
    });
    return true;
  }

  function enhance() {
    ancoraTitulos();
    // figuras ampliáveis viram alvo de teclado também
    docEl.querySelectorAll('img').forEach(function (img) {
      if (!ampliavel(img)) return;
      img.tabIndex = 0;
      img.setAttribute('role', 'button');
      if (img.alt) img.title = img.alt + ' — clique para ampliar';
    });
    // tabelas responsivas (mesma classe do site)
    docEl.querySelectorAll('table').forEach(function (t) {
      if (t.closest('.data-table-wrap')) return;
      var w = document.createElement('div'); w.className = 'data-table-wrap';
      t.parentNode.insertBefore(w, t); w.appendChild(t);
    });
    // links externos abrem em nova aba
    docEl.querySelectorAll('a[href^="http"]').forEach(function (a) {
      a.target = '_blank'; a.rel = 'noopener';
    });
    // parágrafo "Mapas interativos" ganha classe pra estilo
    docEl.querySelectorAll('p').forEach(function (p) {
      if (/Mapas interativos/i.test(p.textContent)) p.classList.add('maps');
    });
  }

  function renderDoc(name) {
    return fetchText(base + 'results/' + name + '.md').then(function (md) {
      docEl.innerHTML = marked.parse(md);
      // gráficos abaixo do primeiro só baixam perto da tela; o markdown não
      // carrega width/height, então isso é o que segura o peso inicial
      docEl.querySelectorAll('img').forEach(function (img, i) {
        img.decoding = 'async';
        if (i > 0) img.loading = 'lazy';
      });
      enhance();
      var h1 = docEl.querySelector('h1');
      if (h1) {
        document.title = h1.textContent + ' — rodado';
        eyebrow.innerHTML = '<a href="' + (base || './') + '" ' +
          'style="color:inherit;text-decoration:none">Análises</a> ／ ' + name;
      }
      // hash de capítulo manda; sem ele, começa do topo
      if (!vaiProHash()) window.scrollTo(0, 0);
    }).catch(function () {
      docEl.innerHTML = '<h1>Análise não encontrada</h1>' +
        '<p class="doc-msg">Nenhuma análise com esse nome em <code>results/</code>. ' +
        '<a href="' + (base || './') + '">Ver todas &rarr;</a></p>';
    });
  }

  // rodado_em é DD-MM-AAAA; sem ele, cai no ano-mês de "date" (igual a gera_home.py)
  function dataBr(it) {
    var d = it.rodado_em;
    if (d && /^\d{2}-\d{2}-\d{4}$/.test(d)) return d.replace(/-/g, '/');
    return it.date || '';
  }

  function renderIndex(items) {
    if (!items.length) {
      docEl.innerHTML = '<h1>Análises</h1><p class="doc-msg">Nenhuma análise publicada ainda.</p>';
      return;
    }
    // tradução ("par" + "lang": "en") não conta como análise a mais (regra gêmea: bloco_analises em scripts/gera_home.py)
    var total = items.filter(function (i) { return !(i.par && i.lang === 'en'); }).length;
    eyebrow.textContent = total + ' análises';
    var html = '<h1>Análises</h1>' +
      '<p class="dek">Emendas parlamentares, dívida ativa, outorgas de água, ' +
      'contas de campanha, óbitos do SUS — registros públicos cruzados uns com ' +
      'os outros até aparecer o que nenhum deles mostra sozinho.</p>' +
      // ponte pro módulo irmão: mesmo espelho de dados, uso diferente
      // números do espelho: AGENTS.md (1.759 tabelas · 295 datasets · 140 fontes,
      // 2026-11-11). A home e plataformas.js também os têm em texto fixo.
      '<p class="lede">Cada uma sai do mesmo espelho local de 1.759 tabelas ' +
      'públicas, em 295 datasets e 140 fontes — RAIS, SIM, TSE, CGU, IBGE, ' +
      'Receita Federal e outras, além de fontes raspadas de forma ' +
      'independente — consultado sob demanda por ' +
      'DuckDB, e fecha uma pergunta com um número. Quem quiser o dado ' +
      'inteiro pra navegar, não só a conclusão, encontra em ' +
      '<a href="/plataformas/">Plataformas</a>.</p>' +
      '<h2>Rodados</h2>' +
      '<p class="mod-sub">Cada uma abre com o achado e leva a tabela de ' +
      'evidência junto — número, fonte oficial e a data em que foi rodada, ' +
      'para conferir, não só ler.</p>' +
      '<div class="fonte-filtro" id="fonte-filtro"></div>' +
      '<div class="noticias idx-cartoes">';
    // os mesmos cartões .noticia da home (site.css), em grade com todas
    items.forEach(function (it) {
      // "url" é para análises hospedadas fora do results/*.md (ex.: repos
      // externos, checados out em pages/analises/ no deploy)
      var href = it.url || (encodeURIComponent(it.slug) + '/');
      var fonte = (it.tags || [])[0];
      // capa abstrata (scripts/gera_capas.ts); se faltar, a imagem some sozinha
      html += '<a class="noticia" href="' + href + '" data-fontes="' + esc(fontesDe(it).join('|')) + '">' +
        '<img class="noticia-capa" src="' + base + 'img/capa-' + encodeURIComponent(it.slug) +
        '.webp" alt="" width="1680" height="240" loading="lazy" decoding="async" ' +
        'onerror="this.remove()">' +
        '<span class="noticia-data">' + dataBr(it) + '</span>' +
        '<span class="noticia-titulo">' + it.title + '</span>' +
        (it.dek ? '<span class="noticia-dek">' + it.dek + '</span>' : '') +
        (fonte ? '<span class="noticia-fonte">' + fonte + '</span>' : '') +
        '</a>';
    });
    docEl.innerHTML = html + '</div>';
    document.title = 'Análises de dados públicos — rodado';
    filtroFonte(items);
  }

  // --- filtro por fonte (órgão = texto antes de " · " em cada tag) ----------
  function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
  function fontesDe(it) {
    var out = [];
    (it.tags || []).forEach(function (t) {
      var o = t.split(' · ')[0].trim();
      if (o && out.indexOf(o) < 0) out.push(o);
    });
    return out;
  }
  function filtroFonte(items) {
    var box = document.getElementById('fonte-filtro');
    var cards = docEl.querySelectorAll('.noticia[data-fontes]');
    if (!box) return;
    var cont = {};
    items.forEach(function (it) { fontesDe(it).forEach(function (o) { cont[o] = (cont[o] || 0) + 1; }); });
    var orgaos = Object.keys(cont).sort(function (a, b) { return cont[b] - cont[a] || a.localeCompare(b, 'pt'); });
    var h = '<button type="button" class="fonte-chip" data-fonte="">Todas <span>' + items.length + '</span></button>';
    orgaos.forEach(function (o) {
      h += '<button type="button" class="fonte-chip" data-fonte="' + esc(o) + '">' + esc(o) + ' <span>' + cont[o] + '</span></button>';
    });
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', 'Filtrar por fonte');
    box.innerHTML = h;
    var chips = box.querySelectorAll('.fonte-chip');

    function aplica() {
      var f = new URLSearchParams(location.search).get('fonte') || '';
      if (f && !cont[f]) f = '';
      chips.forEach(function (c) { c.setAttribute('aria-pressed', c.dataset.fonte === f ? 'true' : 'false'); });
      var n = 0;
      cards.forEach(function (a) {
        var ok = !f || a.dataset.fontes.split('|').indexOf(f) >= 0;
        a.hidden = !ok;
        if (ok) n++;
      });
      eyebrow.textContent = f ? n + ' de ' + items.length + ' análises' : items.length + ' análises';
    }
    box.addEventListener('click', function (e) {
      var c = e.target.closest('.fonte-chip');
      if (!c) return;
      var u = new URL(location.href);
      if (c.dataset.fonte) u.searchParams.set('fonte', c.dataset.fonte); else u.searchParams.delete('fonte');
      history.pushState(null, '', u.pathname + u.search + u.hash);
      aplica();
    });
    window.addEventListener('popstate', aplica);
    aplica();
  }

  // ?doc=<slug> é a forma antiga: não tem metadados próprios, então mandamos
  // para a página da análise. Só depois de confirmar no manifest — assim um
  // slug inexistente cai na mensagem daqui, e não num 404 do Pages.
  var legado = !docEl.dataset.slug && slug;

  if (legado) {
    fetchJSON(base + 'results/manifest.json').then(function (items) {
      var existe = items.some(function (it) { return it.slug === slug; });
      if (existe) location.replace(encodeURIComponent(slug) + '/');
      else renderDoc(slug);
    });
  } else if (slug) {
    renderDoc(slug);
  } else {
    fetchJSON(base + 'results/manifest.json').then(function (items) {
      if (items.length === 1) location.replace(encodeURIComponent(items[0].slug) + '/');
      else renderIndex(items);
    });
  }
})();
