(function () {
  var root = document.documentElement;
  var btn = document.getElementById('themeToggle');
  var stored = localStorage.getItem('rodado-theme');

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
