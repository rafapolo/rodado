/* Viewer universal de análises: renderiza qualquer .md em analises/results/
   Uso: analises/<slug>/      → página própria, com metadados de compartilhamento
                                (o shell traz data-slug; gerado por gera_analises.py)
        analises/?doc=<slug>  → mesma coisa, sem metadados próprios; mantido
                                porque links assim já circulam por aí
        analises/             → índice (lê results/manifest.json); se houver só
                                uma análise, abre direto.
   Adicionar uma análise = soltar o .md em results/, uma linha no manifest.json
   e rodar scripts/gera_analises.py (que também chama o gera_seo). */
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

  function renderIndex(items) {
    if (!items.length) {
      docEl.innerHTML = '<h1>Análises</h1><p class="doc-msg">Nenhuma análise publicada ainda.</p>';
      return;
    }
    var html = '<h1>Análises</h1><p class="dek">Cruzamentos e achados a partir de dados públicos.</p><ul class="idx-list">';
    items.forEach(function (it) {
      // as tags dizem de que fonte pública a reportagem foi tirada — vêm do
      // manifest, abaixo do resumo, para dar o cheiro do dado antes do clique
      var tags = (it.tags || []).map(function (t) {
        return '<span class="tag">' + t + '</span>';
      }).join('');
      // "url" é para análises hospedadas fora do results/*.md (ex.: repos
      // externos como rios-do-brasil, checados out em pages/analises/ no deploy)
      var href = it.url || (encodeURIComponent(it.slug) + '/');
      html += '<li><a href="' + href + '">' + it.title + '</a>' +
        (it.rodado_em ? ' <span class="meta">· rodado em ' + it.rodado_em + '</span>' : '') +
        (it.dek ? '<p class="dek">' + it.dek + '</p>' : '') +
        (tags ? '<p class="tags">' + tags + '</p>' : '') + '</li>';
    });
    docEl.innerHTML = html + '</ul>';
    document.title = 'Análises — rodado';
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
