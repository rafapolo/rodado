/* Índice de Plataformas: lê plataformas.json e monta a vitrine de teasers.
   Sem markdown, sem doc por slug — cada item é só um link (interno ou
   externo) com screenshot, legenda e etiquetas de fonte. */
(function () {
  var docEl = document.getElementById('doc');
  var eyebrow = document.getElementById('eyebrow');

  function fetchJSON(url) {
    return fetch(url).then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; });
  }

  function etiquetas(it) {
    var tags = (it.tags || []).map(function (t) {
      return '<span class="tag">' + t + '</span>';
    }).join('');
    return tags ? '<p class="tags">' + tags + '</p>' : '';
  }

  function renderGrid(items) {
    if (!items.length) {
      docEl.innerHTML = '<h1>Plataformas</h1><p class="doc-msg">Nenhuma plataforma publicada ainda.</p>';
      return;
    }
    eyebrow.textContent = items.length + ' plataformas';
    var html = '<h1>Plataformas</h1>' +
      '<p class="dek">Painel, mapa e rede navegáveis: o dado inteiro, não só o ' +
      'recorte que uma análise fechada usou. Saem do mesmo espelho local de ' +
      '1.029 tabelas públicas que alimenta as <a href="/analises/">análises</a> ' +
      '— a diferença é que aqui você explora, em vez de ler uma conclusão.</p>' +
      '<div class="teaser">';
    items.forEach(function (it) {
      var href = it.url || (encodeURIComponent(it.slug) + '/');
      html += '<a class="teaser-tile" href="' + href + '">' +
        '<img src="' + it.screenshot + '" alt="' + (it.caption || it.title) + '" loading="lazy">' +
        '<span>' + (it.caption || it.title) + '</span>' + etiquetas(it) + '</a>';
    });
    docEl.innerHTML = html + '</div>';
  }

  fetchJSON('plataformas.json').then(renderGrid);
})();
