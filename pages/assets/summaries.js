// Cartões das tabelas em mcp.html / mcp-en.html: ao abrir "N tabelas" de um dataset, busca
// assets/summaries/<dataset>.json (uma vez) e desenha uma linha por tabela; clicar expande o cartão.
// Os textos dos cartões vêm em português nas duas páginas; só os rótulos mudam com o idioma.
(function () {
  var EN = document.documentElement.lang.slice(0, 2) === 'en';
  var T = EN ? {
    ate: 'data through', erro: 'unreadable', erroTit: 'The profiler could not read this table', mais: 'details',
    falha: 'Could not load the table cards.', carregando: 'loading…', chave: 'key', semChave: 'no unique key',
    medidas: 'Measures', filtros: 'Typical filters', use: 'Use for', naoUse: 'Do not use for',
    verificado: 'Checked', notas: 'Drafts (inferred, not measured)', rasc: 'draft', rascTit: 'Inferred, not measured',
    naoSoma: 'do not sum', semTerr: 'no territory', lbl: 'unit'
  } : {
    ate: 'dados até', erro: 'sem leitura', erroTit: 'O perfil não conseguiu ler esta tabela', mais: 'detalhes',
    falha: 'Não foi possível carregar os cartões das tabelas.', carregando: 'carregando…', chave: 'chave',
    semChave: 'sem chave única', medidas: 'Medidas', filtros: 'Filtros típicos', use: 'Use para',
    naoUse: 'Não use para', verificado: 'Verificado', notas: 'Rascunho (deduzido, sem medição)', rasc: 'rascunho',
    rascTit: 'Deduzido, sem medição', naoSoma: 'não some', semTerr: 'sem território', lbl: 'unidade'
  };
  var NATUREZA = EN ? {
    retrato_atual: 'current snapshot', serie_anual: 'yearly series', serie_mensal: 'monthly series',
    serie_diaria: 'daily series', serie_de_periodos: 'series of periods', sem_tempo: 'no time', soma_de_retratos: 'sum of snapshots'
  } : {
    retrato_atual: 'retrato atual', serie_anual: 'série anual', serie_mensal: 'série mensal',
    serie_diaria: 'série diária', serie_de_periodos: 'série de períodos', sem_tempo: 'sem tempo', soma_de_retratos: 'soma de retratos'
  };
  var NIVEL = EN ? {
    nenhum: '', municipio: 'municipality', uf: 'state', regiao: 'region', brasil: 'Brazil', ponto: 'point', outro: 'other area'
  } : {
    nenhum: '', municipio: 'município', uf: 'estado', regiao: 'região', brasil: 'Brasil', ponto: 'ponto', outro: 'outra área'
  };
  var MESES = EN ? 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split(' ')
                 : 'jan fev mar abr mai jun jul ago set out nov dez'.split(' ');
  var cache = {};

  function esc(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  // mesma formatação do gera_summaries_web.py: 2026-09 -> set/2026 (pt) ou Sep 2026 (en)
  function data(s) {
    var m = /^(\d{4})(?:-(\d{2})(?:-(\d{2}))?)?$/.exec(s || '');
    if (!m) return s || '';
    if (!m[2]) return m[1];
    if (!m[3]) return MESES[+m[2] - 1] + (EN ? ' ' : '/') + m[1];
    return EN ? s : m[3] + '/' + m[2] + '/' + m[1];
  }

  // "filtro SQL (explicação); resto": a parte antes do primeiro "(" ou ";" vai em <code>
  function filtro(f) {
    var m = /^([^;(]{3,90}?)(\s*[;(].*)?$/s.exec(f);
    return m ? '<code>' + esc(m[1].trim()) + '</code>' + esc(m[2] ? ' ' + m[2].trim() : '') : esc(f);
  }

  function medida(m) {
    var nome = m[0] ? '<code>' + esc(m[0]) + '</code>' : '';
    var extra = [m[1], m[2] ? T.lbl + ': ' + m[2] : '', m[3] ? T.naoSoma : '', m[4]].filter(Boolean);
    return '<li>' + nome + (extra.length ? ' — ' + esc(extra.join('; ')) : '') + '</li>';
  }

  function secao(titulo, corpo, campo, rasc) {
    var marca = rasc.has(campo) ? ' sc-rasc" data-rasc="' + T.rasc + '" title="' + T.rascTit : '';
    return '<div class="sc-sec' + marca + '"><b>' + titulo + '</b>' + corpo + '</div>';
  }

  function cartao(t) {
    var rasc = new Set(t.r || []);
    function item(campo, texto, classe) {
      var r = rasc.has(campo) ? ' sc-rasc" title="' + T.rascTit : '';
      return '<span class="' + (classe || '') + r + '">' + texto + '</span>';
    }
    var meta = [];
    if (t.c) {
      var sem = /^nenhuma/i.test(t.c);
      meta.push(item('chave', T.chave + ': ' + esc(t.c), sem ? 'sc-aviso' : ''));
    }
    if (t.tp) {
      var cob = t.tp[2] ? ', ' + esc(t.tp[2]) : '';
      meta.push(item('tempo', esc(NATUREZA[t.tp[0]] || t.tp[0]) + cob));
    }
    if (t.te) meta.push(item('territorio', esc(NIVEL[t.te[0]] === undefined ? t.te[0] : NIVEL[t.te[0]] || T.semTerr)));
    if (t.d) meta.push('<span>' + T.ate + ' ' + data(t.d) + '</span>');

    var mais = '';
    if (t.m) mais += secao(T.medidas, '<ul>' + t.m.map(medida).join('') + '</ul>', 'medidas', rasc);
    if (t.f) mais += secao(T.filtros, '<ul>' + t.f.map(function (f) { return '<li>' + filtro(f) + '</li>'; }).join('') + '</ul>', 'filtros_tipicos', rasc);
    if (t.u) mais += secao(T.use, esc(t.u), 'use_para', rasc);
    if (t.nu) mais += secao(T.naoUse, esc(t.nu), 'nao_use_para', rasc);
    if (t.rn) mais += secao(T.notas, '<ul>' + t.rn.map(function (n) { return '<li>' + esc(n) + '</li>'; }).join('') + '</ul>', '', rasc);
    if (t.v) mais += '<div class="sc-sec sc-pequeno"><b>' + T.verificado + '</b>' + esc(t.v) + '</div>';

    return '<li><details class="sc-t' + (t.e ? ' sc-com-erro' : '') + '"><summary>' +
      '<span class="sc-n">' + esc(t.n) + '</span><span class="sc-g">' + esc(t.g) + '</span>' +
      (t.e ? '<span class="sc-d" title="' + T.erroTit + '">' + T.erro + '</span>' : '<span class="sc-d">' + (t.d ? data(t.d) : '') + '</span>') +
      '</summary><div class="sc-corpo">' +
      (t.e ? '<div class="sc-erro">' + T.erroTit + ': <code>' + esc(t.e) + '</code></div>' : '') +
      '<div class="sc-grao' + (rasc.has('grao') ? ' sc-rasc" data-rasc="' + T.rasc : '') + '">' + esc(t.g) + '</div>' +
      (meta.length ? '<div class="sc-meta">' + meta.join('') + '</div>' : '') +
      (mais ? '<details class="sc-mais"><summary>' + T.mais + '</summary>' + mais + '</details>' : '') +
      '</div></details></li>';
  }

  function carrega(ds) {
    if (!cache[ds]) {
      cache[ds] = fetch('assets/summaries/' + encodeURIComponent(ds) + '.json')
        .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
        .catch(function (e) { delete cache[ds]; throw e; });
    }
    return cache[ds];
  }

  document.addEventListener('toggle', function (ev) {
    var det = ev.target;
    if (!det.classList || !det.classList.contains('sc-ds') || !det.open || det.dataset.pronto) return;
    var corpo = det.querySelector('.sc-body');
    corpo.innerHTML = '<p class="sc-msg">' + T.carregando + '</p>';
    carrega(det.dataset.ds).then(function (d) {
      corpo.innerHTML = '<ul class="sc-list">' + d.t.map(cartao).join('') + '</ul>';
      det.dataset.pronto = '1';
    }, function () {
      corpo.innerHTML = '<p class="sc-msg">' + T.falha + '</p>';
    });
  }, true);
})();
