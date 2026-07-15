/* ============================================================
   Atlas Brasil — JS Utilities (swissviz-dark)
   ============================================================ */

const ATLAS = (() => {
  // --- Palettes ---
  const SEQUENTIAL_BLUE  = [[247,251,255],[198,219,239],[158,202,225],[107,174,214],[49,130,189],[8,81,156]];
  const SEQUENTIAL_GREEN = [[237,248,251],[186,228,179],[116,196,118],[49,163,84],[0,109,44]];
  const SEQUENTIAL_RED   = [[255,255,204],[254,204,92],[253,141,60],[240,59,32],[189,0,38]];
  const DIVERGING_RDBU   = [[165,0,38],[215,48,39],[244,109,67],[253,174,97],[255,255,191],[171,217,233],[116,173,209],[69,117,180],[49,54,149]];
  const CATEGORICAL_BRIGHT = [[166,206,227],[31,120,180],[178,223,138],[51,160,44],[251,154,153],[227,26,28],[253,192,134],[255,127,0],[202,178,214],[106,61,154]];

  // --- Display ---
  const isTouch = window.matchMedia('(hover: none)').matches;

  function fmtNum(v, decimals) {
    if (v == null) return '—';
    return Number(v).toLocaleString('pt-BR', {
      minimumFractionDigits: decimals ?? 2,
      maximumFractionDigits: decimals ?? 2,
    });
  }

  function fmtPct(v, decimals) {
    if (v == null) return '—';
    return (v * 100).toLocaleString('pt-BR', {
      minimumFractionDigits: decimals ?? 1,
      maximumFractionDigits: decimals ?? 1,
    }) + '%';
  }

  function fmtMoney(v) {
    if (v == null) return '—';
    return 'R$ ' + Number(v).toLocaleString('pt-BR', {
      minimumFractionDigits: 2, maximumFractionDigits: 2,
    });
  }

  // --- Tooltip ---
  let tooltipEl = null;

  function showTooltip(x, y, html) {
    if (!tooltipEl) {
      tooltipEl = document.getElementById('tooltip');
      if (!tooltipEl) return;
    }
    tooltipEl.innerHTML = html;
    tooltipEl.style.display = 'block';
    // constrain to viewport
    const w = tooltipEl.offsetWidth;
    const h = tooltipEl.offsetHeight;
    let l = x + 14, t = y + 14;
    if (l + w > window.innerWidth - 10)  l = x - w - 14;
    if (t + h > window.innerHeight - 10) t = y - h - 14;
    if (l < 10) l = 10;
    if (t < 10) t = 10;
    tooltipEl.style.left = l + 'px';
    tooltipEl.style.top  = t + 'px';
  }

  function hideTooltip() {
    if (tooltipEl) tooltipEl.style.display = 'none';
  }

  // --- Legend ---
  function buildLegend(opts) {
    let el = document.getElementById('legend');
    if (!el) {
      el = document.createElement('div');
      el.id = 'legend';
      document.getElementById('app').appendChild(el);
    }
    if (opts.type === 'gradient' && opts.gradient) {
      const g = opts.gradient;
      el.innerHTML = `
        <div class="legend-title">${opts.title}</div>
        ${opts.unit ? `<div class="legend-subtitle">${opts.unit}</div>` : ''}
        <div class="gradient-bar" style="background: linear-gradient(to right, ${g.from}, ${g.to});"></div>
        <div class="gradient-labels">
          <span>${fmtMoney(g.min)}</span>
          <span>${fmtMoney(g.max)}</span>
        </div>
      `;
    } else if (opts.type === 'categorical' && opts.items) {
      el.innerHTML = `
        <div class="legend-title">${opts.title}</div>
        ${opts.items.map(i => `
          <div style="display:flex;align-items:center;gap:6px;margin-top:4px;font-size:12px;color:var(--text-secondary);">
            <span style="width:10px;height:10px;border-radius:2px;background:${i.color};flex-shrink:0;"></span>
            ${i.label}
          </div>
        `).join('')}
      `;
    }
  }

  // --- Color scale from palette ---
  function colorScaleFromPalette(palette, min, max) {
    return (val) => {
      if (val == null) return [180, 180, 180, 100];
      const t = max === min ? 0.5 : (val - min) / (max - min);
      const idx = Math.min(palette.length - 1, Math.max(0, Math.round(t * (palette.length - 1))));
      const c = palette[idx];
      return [...c, 200];
    };
  }

  // --- Quantile-based color scale ---
  function quantileScale(values, palette) {
    const sorted = values.filter(v => v != null).sort((a, b) => a - b);
    const n = sorted.length;
    if (n === 0) return () => [180, 180, 180, 100];
    const breaks = palette.map((_, i) => {
      const p = i / (palette.length - 1);
      const idx = Math.round(p * (n - 1));
      return sorted[Math.min(idx, n - 1)];
    });
    return (val) => {
      if (val == null) return [180, 180, 180, 100];
      let idx = 0;
      for (let i = 0; i < breaks.length - 1; i++) {
        if (val >= breaks[i]) idx = i;
      }
      // assign to closest break
      let best = 0, bestDist = Infinity;
      for (let i = 0; i < breaks.length; i++) {
        const d = Math.abs(val - breaks[i]);
        if (d < bestDist) { bestDist = d; best = i; }
      }
      const c = palette[Math.min(best, palette.length - 1)];
      return [...c, 200];
    };
  }

  // --- Load JSON helpers ---
  async function loadJSON(url) {
    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`Failed to load ${url}: ${resp.status}`);
    return resp.json();
  }

  async function loadData(basePath) {
    const [geojson, salarios] = await Promise.all([
      loadJSON(basePath + 'dados/municipios.geojson'),
      loadJSON(basePath + 'dados/salarios.json'),
    ]);
    return { geojson, salarios };
  }

  // --- initMap ---
  const INITIAL_VIEW_STATE = {
    longitude: -53.1,
    latitude:  -14.2,
    zoom:       4,
    pitch:     45,
    bearing:    0,
    minZoom:    2,
    maxZoom:   16,
  };

  function initMap(containerId) {
    const map = new maplibregl.Map({
      container: containerId,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
      zoom: INITIAL_VIEW_STATE.zoom,
      pitch: INITIAL_VIEW_STATE.pitch,
      bearing: INITIAL_VIEW_STATE.bearing,
      minZoom: INITIAL_VIEW_STATE.minZoom,
      maxZoom: INITIAL_VIEW_STATE.maxZoom,
      attributionControl: false,
    });

    // Apply swissviz tint
    map.on('load', () => {
      try {
        map.getStyle().layers.forEach(l => {
          if (l.type === 'raster') {
            map.setPaintProperty(l.id, 'raster-brightness-min', 0.07);
            map.setPaintProperty(l.id, 'raster-hue-rotate', 210);
            map.setPaintProperty(l.id, 'raster-saturation', 0.4);
            map.setPaintProperty(l.id, 'raster-contrast', -0.1);
          }
        });
      } catch (_) {}
    });

    const deckOverlay = new deck.MapboxOverlay({
      interleaved: true,
    });
    map.addControl(deckOverlay);

    return { map, deck: deckOverlay };
  }

  // --- setupActions ---
  function setupActions(map, vizNum, getShareState, getSql) {
    const resetBtn = document.getElementById('btn-reset');
    const shareBtn = document.getElementById('btn-share');
    const sqlBtn   = document.getElementById('btn-sql');

    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        map.flyTo({
          center: [INITIAL_VIEW_STATE.longitude, INITIAL_VIEW_STATE.latitude],
          zoom: INITIAL_VIEW_STATE.zoom,
          pitch: INITIAL_VIEW_STATE.pitch,
          bearing: INITIAL_VIEW_STATE.bearing,
          duration: 600,
        });
      });
    }

    if (shareBtn) {
      shareBtn.addEventListener('click', async () => {
        const state = getShareState ? getShareState() : {};
        const params = new URLSearchParams();
        if (vizNum) params.set('v', vizNum);
        Object.entries(state).forEach(([k, v]) => {
          if (v != null && v !== '') params.set(k, v);
        });
        const url = `${window.location.origin}${window.location.pathname}?${params}`;
        try {
          await navigator.clipboard.writeText(url);
          shareBtn.textContent = '✓';
          setTimeout(() => { shareBtn.textContent = '⎘'; }, 1500);
        } catch (_) {
          // fallback
          const ta = document.createElement('textarea');
          ta.value = url; document.body.appendChild(ta);
          ta.select(); document.execCommand('copy');
          document.body.removeChild(ta);
          shareBtn.textContent = '✓';
          setTimeout(() => { shareBtn.textContent = '⎘'; }, 1500);
        }
      });
    }

    if (sqlBtn) {
      sqlBtn.addEventListener('click', () => {
        const modal = document.getElementById('sql-modal');
        if (modal) {
          const code = modal.querySelector('pre code');
          if (code) code.textContent = getSql ? getSql() : '';
          modal.classList.toggle('open');
        }
      });
    }

    // close modal on overlay click
    document.addEventListener('click', (e) => {
      const modal = document.getElementById('sql-modal');
      if (modal && modal.classList.contains('open') && e.target === modal) {
        modal.classList.remove('open');
      }
    });
  }

  // --- setupMobilePanels ---
  function setupMobilePanels() {
    const toggleLeft = document.getElementById('toggle-left');
    const toggleRight = document.getElementById('toggle-right');
    const leftPanel = document.getElementById('control-panel');
    const rightPanel = document.getElementById('stats-panel');

    function togglePanel(panel, btn) {
      if (!panel) return;
      const isOpen = panel.classList.contains('open');
      // close all
      [leftPanel, rightPanel].forEach(p => { if (p) p.classList.remove('open'); });
      if (!isOpen) panel.classList.add('open');
    }

    if (toggleLeft && leftPanel) {
      toggleLeft.addEventListener('click', () => togglePanel(leftPanel, toggleLeft));
    }
    if (toggleRight && rightPanel) {
      toggleRight.addEventListener('click', () => togglePanel(rightPanel, toggleRight));
    }
  }

  // --- hideLoading ---
  function hideLoading() {
    const el = document.getElementById('loading');
    if (el) el.classList.add('hidden');
  }

  return {
    // palettes
    SEQUENTIAL_BLUE, SEQUENTIAL_GREEN, SEQUENTIAL_RED,
    DIVERGING_RDBU, CATEGORICAL_BRIGHT,
    INITIAL_VIEW_STATE,

    // utils
    isTouch,
    fmtNum, fmtPct, fmtMoney,
    colorScaleFromPalette, quantileScale,

    // UI
    showTooltip, hideTooltip, buildLegend,
    initMap, setupActions, setupMobilePanels, hideLoading,

    // data
    loadJSON, loadData,
  };
})();
