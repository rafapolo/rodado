// setas ‹ › nos carrosséis da home (.teaser.carrossel, .noticias.carrossel). Sem JS a faixa
// continua rolando por toque/trackpad/scroll-snap; isto só acrescenta o
// clique para quem está de mouse.
(function () {
  var en = document.documentElement.lang === 'en';
  document.querySelectorAll('.carrossel').forEach(function (faixa) {
    var wrap = document.createElement('div');
    wrap.className = 'carrossel-wrap';
    faixa.parentNode.insertBefore(wrap, faixa);
    wrap.appendChild(faixa);

    function seta(classe, texto, rotulo, sentido) {
      var b = document.createElement('button');
      b.type = 'button';
      b.className = 'carrossel-seta ' + classe;
      b.textContent = texto;
      b.setAttribute('aria-label', rotulo);
      b.addEventListener('click', function () {
        faixa.scrollBy({ left: sentido * faixa.clientWidth * 0.8 });
      });
      wrap.appendChild(b);
      return b;
    }
    var ant = seta('ant', '‹', en ? 'Previous' : 'Anterior', -1);
    var prox = seta('prox', '›', en ? 'Next' : 'Próximo', 1);

    function atualiza() {
      var max = faixa.scrollWidth - faixa.clientWidth;
      ant.hidden = faixa.scrollLeft <= 2;
      prox.hidden = faixa.scrollLeft >= max - 2;
    }
    // arrastar com o mouse, como o dedo no celular; um arrasto de verdade
    // (> 5 px) cancela o clique no link e a abertura da imagem em nova aba
    var x0 = 0, s0 = 0, arrastando = false, moveu = false;
    faixa.addEventListener('dragstart', function (ev) { ev.preventDefault(); });
    faixa.addEventListener('pointerdown', function (ev) {
      if (ev.pointerType !== 'mouse' || ev.button !== 0) return;
      arrastando = true; moveu = false; x0 = ev.clientX; s0 = faixa.scrollLeft;
    });
    window.addEventListener('pointermove', function (ev) {
      if (!arrastando) return;
      var dx = ev.clientX - x0;
      if (!moveu && Math.abs(dx) > 5) {
        moveu = true;
        faixa.classList.add('arrastando');
      }
      if (moveu) faixa.scrollLeft = s0 - dx;
    });
    window.addEventListener('pointerup', function () {
      if (!arrastando) return;
      arrastando = false;
      faixa.classList.remove('arrastando');
    });
    faixa.addEventListener('click', function (ev) {
      if (moveu) { ev.preventDefault(); ev.stopPropagation(); moveu = false; }
    }, true);

    faixa.addEventListener('scroll', atualiza, { passive: true });
    window.addEventListener('resize', atualiza);
    atualiza();
  });
})();
