/* Viewer universal de análises: renderiza qualquer .md em analises/results/
   Uso: analises/<slug>/      → página própria, com metadados de compartilhamento
                                (o shell traz data-slug; gerado por gera_analises.py)
        analises/?doc=<slug>  → mesma coisa, sem metadados próprios; mantido
                                porque links assim já circulam por aí
        analises/             → índice (lê results/manifest.json); se houver só
                                uma análise, abre direto.
        analises/en           → índice em inglês (en.html, data-lang="en"): só
                                as análises com "lang": "en" no manifest.
   Adicionar uma análise = soltar o .md em results/, uma linha no manifest.json
   e rodar scripts/gera_analises.py (que também chama o gera_seo). A capa
   precisa de uma linha em TEMAS de scripts/gera_capas.ts: docs/tecnico/covers.md. */
(function () {
  var docEl = document.getElementById('doc');
  var eyebrow = document.getElementById('eyebrow');
  // nas páginas próprias o conteúdo fica um nível abaixo de analises/
  var base = docEl.dataset.base || '';
  // índice em inglês (analises/en.html): só as análises com "lang": "en"
  var EN = docEl.dataset.lang === 'en';
  var T = EN ? {
    todas: 'All', analises: 'analyses', de: 'of', mais: '+{n} sources',
    menos: 'fewer sources', filtrar: 'Filter by source',
    vazio: 'No analysis published yet.'
  } : {
    todas: 'Todas', analises: 'análises', de: 'de', mais: '+{n} fontes',
    menos: 'menos fontes', filtrar: 'Filtrar por fonte',
    vazio: 'Nenhuma análise publicada ainda.'
  };
  // conta como análise a mais? No índice PT, a tradução ("par" + "lang": "en")
  // não conta (regra gêmea: bloco_analises em scripts/gera_home.py); no EN só
  // aparecem as em inglês, e todas contam
  function conta(it) { return EN || !(it.par && it.lang === 'en'); }
  var slug = docEl.dataset.slug ||
             new URLSearchParams(location.search).get('doc') ||
             (location.hash ? location.hash.slice(1) : '');

  // página de análise gerada já vem com o corpo pronto e não carrega o marked
  if (window.marked) marked.setOptions({ gfm: true, breaks: false });

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
    // a página gerada já traz o corpo pronto (gera_analises.py renderiza o .md com o
    // mesmo marked): sem buscar nada, só os enfeites. O .md via fetch fica para o
    // ?doc=<slug> antigo e para página gerada antes do corpo estático
    var corpo = docEl.hasAttribute('data-pronto')
      ? Promise.resolve(null)
      : fetchText(base + 'results/' + name + '.md');
    return corpo.then(function (md) {
      if (md !== null) {
        docEl.innerHTML = marked.parse(md);
        // gráficos abaixo do primeiro só baixam perto da tela; o markdown não
        // carrega width/height, então isso é o que segura o peso inicial
        docEl.querySelectorAll('img').forEach(function (img, i) {
          img.decoding = 'async';
          if (i > 0) img.loading = 'lazy';
        });
      }
      enhance();
      var h1 = docEl.querySelector('h1');
      if (h1) {
        document.title = h1.textContent + ' — rodado';
        eyebrow.innerHTML = '<a href="' + (base || './') + '" ' +
          'style="color:inherit;text-decoration:none">Análises</a> ／ ' + name;
      }
      // hash de capítulo manda; sem ele, começa do topo (só quando o corpo acabou
      // de entrar: com ele já na página, o navegador pode ter restaurado a rolagem)
      if (!vaiProHash() && md !== null) window.scrollTo(0, 0);
      return leiaTambem(name);
    }).catch(function () {
      docEl.innerHTML = '<h1>Análise não encontrada</h1>' +
        '<p class="doc-msg">Nenhuma análise com esse nome em <code>results/</code>. ' +
        '<a href="' + (base || './') + '">Ver todas &rarr;</a></p>';
    });
  }

  // --- "Leia também" ---------------------------------------------------------
  // 3 análises relacionadas ao fim do corpo: pontua por órgão de fonte em comum
  // (texto antes do " · " em tags), desempata pela data mais recente. Nunca a
  // própria, nem o par de tradução; mesma língua. Sem órgão em comum, as mais
  // recentes completam.
  // o manifest escreve o mesmo órgão de jeitos diferentes (PT/EN, sigla ou
  // nome); filtro e "leia também" comparam pelo nome canônico daqui
  var SINONIMOS = {
    'Federal Revenue': 'Receita Federal', 'ANA': 'Agência Nacional de Águas',
    'Tribunal Superior Eleitoral': 'TSE', 'Central Bank': 'Banco Central',
    'Concla/IBGE': 'IBGE', 'Ministry of Health / DATASUS': 'DataSUS',
    'National Supplementary Health Agency (ANS)': 'ANS',
    'Transparency Portal and CGU': 'CGU', 'Portal da Transparência e CGU': 'CGU',
    'Portal da Transparência/TransfereGov': 'CGU'
  };
  function orgao(tag) {
    var o = tag.split(' · ')[0].trim();
    return SINONIMOS[o] || o;
  }
  function orgaos(it) {
    return (it.tags || []).map(orgao);
  }
  function chaveData(it) {
    var d = it.rodado_em;
    if (d && /^\d{2}-\d{2}-\d{4}$/.test(d)) return d.slice(6) + d.slice(3, 5) + d.slice(0, 2);
    return (it.date || '').replace(/-/g, '') + '00';
  }
  function relacionadas(items, atual, n) {
    var lang = atual.lang || 'pt-br', meus = orgaos(atual);
    return items.filter(function (it) {
      return it.slug !== atual.slug && it.slug !== atual.par && it.par !== atual.slug &&
        (it.lang || 'pt-br') === lang;
    }).map(function (it) {
      var o = orgaos(it);
      var comuns = meus.filter(function (x, i) { return o.indexOf(x) >= 0 && meus.indexOf(x) === i; }).length;
      return { it: it, pontos: comuns, data: chaveData(it) };
    }).sort(function (a, b) {
      return b.pontos - a.pontos || (a.data < b.data ? 1 : a.data > b.data ? -1 : 0);
    }).slice(0, n).map(function (x) { return x.it; });
  }
  function leiaTambem(slugAtual) {
    return fetchJSON(base + 'results/manifest.json').then(function (items) {
      var atual = items.filter(function (it) { return it.slug === slugAtual; })[0];
      if (!atual) return;
      var rel = relacionadas(items, atual, 3);
      if (!rel.length) return;
      var en = (atual.lang || 'pt-br') !== 'pt-br';
      var html = '<aside class="leia-tambem"><h2>' + (en ? 'Read also' : 'Leia também') +
        '</h2><div class="noticias idx-cartoes">';
      rel.forEach(function (it) {
        var href = it.url || (base + encodeURIComponent(it.slug) + '/');
        html += '<a class="noticia" href="' + href + '">' +
          '<img class="noticia-capa" src="' + base + 'img/capa-' + encodeURIComponent(it.slug) +
          '.webp" alt="" width="1680" height="240" loading="lazy" decoding="async" ' +
          'onerror="this.remove()">' +
          '<span class="noticia-data">' + dataBr(it) + '</span>' +
          '<span class="noticia-titulo">' + it.title + '</span></a>';
      });
      docEl.insertAdjacentHTML('beforeend', html + '</div></aside>');
    });
  }

  // rodado_em é DD-MM-AAAA; sem ele, cai no ano-mês de "date" (igual a gera_home.py)
  function dataBr(it) {
    var d = it.rodado_em;
    if (d && /^\d{2}-\d{2}-\d{4}$/.test(d)) {
      // EN no formato ISO, como os cartões da home em inglês (gera_home.data_br)
      if (EN) return d.slice(6) + '-' + d.slice(3, 5) + '-' + d.slice(0, 2);
      return d.replace(/-/g, '/');
    }
    return it.date || '';
  }

  function renderIndex(items) {
    if (EN) items = items.filter(function (i) { return i.lang === 'en'; });
    if (!items.length) {
      docEl.innerHTML = '<h1>' + (EN ? 'Analyses' : 'Análises') + '</h1><p class="doc-msg">' + T.vazio + '</p>';
      return;
    }
    var total = items.filter(conta).length;
    eyebrow.textContent = total + ' ' + T.analises;
    // o 1,758 do lede EN segue os números do lede PT logo abaixo (atualizar juntos)
    var html = EN ? '<h1>Analyses</h1>' +
      '<p class="dek">Public health data, federal spending, congressional ' +
      'earmarks — Brazilian public records cross-referenced until they show ' +
      'what none of them shows alone.</p>' +
      '<p class="lede">These are the analyses written in English. Most of ' +
      'rodado\'s work is in Portuguese: the <a href="./">full list</a> has ' +
      'every one, all from the same local mirror of 1,758 public tables, ' +
      'queried on demand. For the whole data to explore, not just a ' +
      'conclusion, see <a href="/plataformas/en">Platforms</a>.</p>' +
      '<div class="fonte-filtro" id="fonte-filtro"></div>' +
      '<div class="noticias idx-cartoes">'
      : '<h1>Análises</h1>' +
      '<p class="dek">Emendas parlamentares, dívida ativa, outorgas de água, ' +
      'contas de campanha, óbitos do SUS — registros públicos cruzados uns com ' +
      'os outros até aparecer o que nenhum deles mostra sozinho.</p>' +
      // ponte pro módulo irmão: mesmo espelho de dados, uso diferente
      // números do espelho: os mesmos da home (index.html, eyebrow "1.758 tabelas ·
      // 294 datasets · 140 fontes"), que é texto fixo — atualizar os dois juntos
      '<p class="lede">Cada uma sai do mesmo espelho local de 1.758 tabelas ' +
      'públicas, em 294 datasets e 140 fontes — RAIS, SIM, TSE, CGU, IBGE, ' +
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
    document.title = EN ? 'Brazilian public data analyses — rodado' : 'Análises de dados públicos — rodado';
    filtroFonte(items);
  }

  // --- filtro por fonte (órgão = texto antes de " · " em cada tag) ----------
  function esc(t) { return String(t).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;'); }
  function fontesDe(it) {
    var out = [];
    (it.tags || []).forEach(function (t) {
      var o = orgao(t);
      if (o && out.indexOf(o) < 0) out.push(o);
    });
    return out;
  }
  function filtroFonte(items) {
    var box = document.getElementById('fonte-filtro');
    var cards = docEl.querySelectorAll('.noticia[data-fontes]');
    if (!box) return;
    var cont = {};
    items.forEach(function (it) {
      if (!conta(it)) return; // tradução não soma no chip
      fontesDe(it).forEach(function (o) { cont[o] = (cont[o] || 0) + 1; });
    });
    var lista = Object.keys(cont).sort(function (a, b) { return cont[b] - cont[a] || a.localeCompare(b, 'pt'); });
    // tradução não conta como análise a mais (mesma regra do eyebrow e da home)
    var traducao = items.map(function (i) { return !conta(i); });
    var total = traducao.filter(function (t) { return !t; }).length;
    var chip = function (o, extra) {
      return '<button type="button" class="fonte-chip' + (extra ? ' fonte-extra' : '') + '" data-fonte="' + esc(o) + '">' +
        esc(o) + ' <span>' + cont[o] + '</span></button>';
    };
    // órgão de uma análise só fica atrás do "+N": sem isso eram 4 linhas de chips
    var h = '<button type="button" class="fonte-chip" data-fonte="">' + T.todas + ' <span>' + total + '</span></button>';
    var raros = lista.filter(function (o) { return cont[o] < 2; });
    lista.forEach(function (o) { if (cont[o] >= 2) h += chip(o); });
    raros.forEach(function (o) { h += chip(o, true); });
    var rotMais = T.mais.replace('{n}', raros.length);
    if (raros.length) h += '<button type="button" class="fonte-mais" aria-expanded="false">' + rotMais + '</button>';
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', T.filtrar);
    box.innerHTML = h;
    var chips = box.querySelectorAll('.fonte-chip');

    function marcaMais(b) {
      var aberto = box.classList.contains('aberto');
      b.setAttribute('aria-expanded', aberto ? 'true' : 'false');
      b.textContent = aberto ? T.menos : rotMais;
    }
    function aplica() {
      var f = new URLSearchParams(location.search).get('fonte') || '';
      if (f && !cont[f]) f = '';
      chips.forEach(function (c) { c.setAttribute('aria-pressed', c.dataset.fonte === f ? 'true' : 'false'); });
      // fonte rara escolhida (ou vinda pela URL) abre o "+N" para o chip aparecer
      if (f && cont[f] < 2) box.classList.add('aberto');
      var n = 0;
      cards.forEach(function (a, i) {
        var ok = !f || a.dataset.fontes.split('|').indexOf(f) >= 0;
        a.hidden = !ok;
        if (ok && !traducao[i]) n++;
      });
      eyebrow.textContent = (f ? n + ' ' + T.de + ' ' : '') + total + ' ' + T.analises;
      var mais = box.querySelector('.fonte-mais');
      if (mais) marcaMais(mais);
    }
    box.addEventListener('click', function (e) {
      if (e.target.closest('.fonte-mais')) {
        box.classList.toggle('aberto');
        marcaMais(e.target.closest('.fonte-mais'));
        return;
      }
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
