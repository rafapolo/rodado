/* Índice de Plataformas: lê plataformas.json e monta a vitrine de teasers.
   Sem markdown, sem doc por slug — cada item é só um link (interno ou
   externo) com screenshot, legenda e etiquetas de fonte.

   Serve index.html (pt-BR) e en.html: o idioma vem do <html lang>. Em inglês
   cada campo de texto sai de `<campo>_en` e cai para o português quando a
   tradução falta; o link é o mesmo nos dois, as plataformas em si são pt-BR. */
(function () {
  var docEl = document.getElementById('doc');
  var eyebrow = document.getElementById('eyebrow');
  var en = /^en/i.test(document.documentElement.lang || '');

  var T = en ? {
    h1: 'Platforms',
    vazio: 'No platforms published yet.',
    contagem: ' platforms',
    dek: 'Navigable dashboards, maps and networks: the whole data, not just the ' +
      'slice a finished analysis used. They come from the same local mirror of ' +
      '1,069 public tables that feeds the <a href="/analises/">analyses</a> ' +
      '— the difference is that here you explore, instead of reading a ' +
      'conclusion. The platforms themselves are in Portuguese.'
  } : {
    h1: 'Plataformas',
    vazio: 'Nenhuma plataforma publicada ainda.',
    contagem: ' plataformas',
    dek: 'Painel, mapa e rede navegáveis: o dado inteiro, não só o ' +
      'recorte que uma análise fechada usou. Saem do mesmo espelho local de ' +
      '1.069 tabelas públicas que alimenta as <a href="/analises/">análises</a> ' +
      '— a diferença é que aqui você explora, em vez de ler uma conclusão.'
  };

  function campo(it, k) {
    return (en && it[k + '_en']) || it[k];
  }

  function fetchJSON(url) {
    return fetch(url).then(function (r) { return r.ok ? r.json() : []; }).catch(function () { return []; });
  }

  function etiquetas(it) {
    var tags = (campo(it, 'tags') || []).map(function (t) {
      return '<span class="tag">' + t + '</span>';
    }).join('');
    return tags ? '<p class="tags">' + tags + '</p>' : '';
  }

  function renderGrid(items) {
    if (!items.length) {
      docEl.innerHTML = '<h1>' + T.h1 + '</h1><p class="doc-msg">' + T.vazio + '</p>';
      return;
    }
    eyebrow.textContent = items.length + T.contagem;
    var html = '<h1>' + T.h1 + '</h1>' +
      '<p class="dek">' + T.dek + '</p>' +
      '<div class="teaser">';
    items.forEach(function (it) {
      var href = it.url || (encodeURIComponent(it.slug) + '/');
      var titulo = campo(it, 'title');
      var dek = campo(it, 'dek');
      html += '<a class="teaser-tile" href="' + href + '">' +
        '<img src="' + it.screenshot + '" alt="' + (campo(it, 'caption') || titulo) + '" loading="lazy">' +
        '<span class="teaser-title">' + titulo + '</span>' +
        (dek ? '<p class="teaser-dek">' + dek + '</p>' : '') +
        etiquetas(it) + '</a>';
    });
    docEl.innerHTML = html + '</div>';
  }

  fetchJSON('plataformas.json').then(renderGrid);
})();
