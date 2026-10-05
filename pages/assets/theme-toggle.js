(function () {
  var root = document.documentElement;
  var btn = document.getElementById('themeToggle');

  // ?mode=dark or ?mode=light forces the theme for this pageview, overriding
  // whatever's in localStorage — useful for shared links and screenshots.
  // It does not overwrite the stored preference; the next toggle click (or a
  // reload without the param) falls back to it as usual.
  var fromUrl = null;
  try {
    var m = new URLSearchParams(location.search).get('mode');
    if (m === 'dark' || m === 'light') fromUrl = m;
  } catch (e) { /* no-op */ }

  // localStorage lança em alguns modos privados (Safari antigo) e com cookies
  // bloqueados: sem o try, o botão de tema morria junto
  var saved = null;
  try { saved = localStorage.getItem('rodado-theme'); } catch (e) { /* no-op */ }
  var stored = fromUrl || saved;

  function effectiveTheme() {
    return stored || 'light';
  }

  // a barra do navegador no celular acompanha o fundo do tema escolhido
  function applyThemeColor(theme) {
    var meta = document.querySelector('meta[name="theme-color"]');
    if (!meta) {
      meta = document.createElement('meta');
      meta.name = 'theme-color';
      document.head.appendChild(meta);
    }
    meta.content = theme === 'dark' ? '#13161b' : '#f9f8f5';
  }

  function applyIcon(theme) {
    applyThemeColor(theme);
    if (!btn) return;
    btn.innerHTML = theme === 'dark'
      ? '<i class="fa-solid fa-lightbulb"></i>'
      : '<i class="fa-solid fa-moon"></i>';
  }

  if (stored) root.setAttribute('data-theme', stored);
  applyIcon(effectiveTheme());

  if (btn) {
    btn.addEventListener('click', function () {
      var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
      stored = next;
      try { localStorage.setItem('rodado-theme', next); } catch (e) { /* no-op */ }
      root.setAttribute('data-theme', next);
      applyIcon(next);
    });
  }
})();
