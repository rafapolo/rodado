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

  var stored = fromUrl || localStorage.getItem('rodado-theme');

  function effectiveTheme() {
    return stored || 'light';
  }

  function applyIcon(theme) {
    if (!btn) return;
    btn.innerHTML = theme === 'dark'
      ? '<i class="fa-solid fa-sun"></i>'
      : '<i class="fa-solid fa-moon"></i>';
  }

  if (stored) root.setAttribute('data-theme', stored);
  applyIcon(effectiveTheme());

  if (btn) {
    btn.addEventListener('click', function () {
      var next = effectiveTheme() === 'dark' ? 'light' : 'dark';
      stored = next;
      localStorage.setItem('rodado-theme', next);
      root.setAttribute('data-theme', next);
      applyIcon(next);
    });
  }
})();
