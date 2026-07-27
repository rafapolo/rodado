/* Viewer universal de análises: renderiza qualquer .md em analises/results/
   Uso: analises/?doc=<slug>  → mostra results/<slug>.md
        analises/            → índice (lê results/manifest.json); se houver só
                               uma análise, abre direto.
   Adicionar uma análise = soltar o .md em results/ e uma linha no manifest.json. */
(function () {
  var docEl = document.getElementById('doc');
  var eyebrow = document.getElementById('eyebrow');
  var slug = new URLSearchParams(location.search).get('doc') ||
             (location.hash ? location.hash.slice(1) : '');

  marked.setOptions({ gfm: true, breaks: false });

  function fetchText(url) {
    return fetch(url).then(function (r) { if (!r.ok) throw new Error(r.status); return r.text(); });
  }
  function fetchJSON(url) {
    return fetch(url).then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; });
  }

  function enhance() {
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
    return fetchText('results/' + name + '.md').then(function (md) {
      docEl.innerHTML = marked.parse(md);
      enhance();
      var h1 = docEl.querySelector('h1');
      if (h1) {
        document.title = h1.textContent + ' — rodado';
        eyebrow.innerHTML = '<a href="./" style="color:inherit;text-decoration:none">Análises</a> ／ ' +
          (new URLSearchParams(location.search).get('doc') || name);
      }
      window.scrollTo(0, 0);
    }).catch(function () {
      docEl.innerHTML = '<h1>Análise não encontrada</h1>' +
        '<p class="doc-msg">Nenhuma análise com esse nome em <code>results/</code>. ' +
        '<a href="./">Ver todas &rarr;</a></p>';
    });
  }

  function renderIndex(items) {
    if (!items.length) {
      docEl.innerHTML = '<h1>Análises</h1><p class="doc-msg">Nenhuma análise publicada ainda.</p>';
      return;
    }
    var html = '<h1>Análises</h1><p class="dek">Cruzamentos e achados a partir de dados públicos.</p><ul class="idx-list">';
    items.forEach(function (it) {
      html += '<li><a href="?doc=' + encodeURIComponent(it.slug) + '">' + it.title + '</a>' +
        (it.date ? ' <span class="meta">· ' + it.date + '</span>' : '') +
        (it.dek ? '<p class="dek">' + it.dek + '</p>' : '') + '</li>';
    });
    docEl.innerHTML = html + '</ul>';
    document.title = 'Análises — rodado';
  }

  if (slug) {
    renderDoc(slug);
  } else {
    fetchJSON('results/manifest.json').then(function (items) {
      if (items.length === 1) renderDoc(items[0].slug);
      else renderIndex(items);
    });
  }
})();
