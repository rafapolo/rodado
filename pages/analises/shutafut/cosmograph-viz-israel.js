class FastNetworkVisualization {
  constructor() {
    this.canvas = document.getElementById('network-canvas');
    this.context = this.canvas.getContext('2d');
    this.data = null;
    this.transform = d3.zoomIdentity;
    this.simulation = null;
    this.selectedNode = null;
    this.labelPositions = [];
    this.showLabels = true;
    this.edgesBright = false;
    this.activeCnaes      = null;
    this.activeTypes      = null;
    this.yearFilter       = null;
    this.yearExact        = false;
    this.activeSituacoes  = null;

    this.paisMap = {
      76: 'Brasil', 105: 'EUA', 158: 'Reino Unido', 161: 'Rússia',
      163: 'El Salvador', 171: 'Suíça', 175: 'Turquia', 181: 'Uruguai',
      191: 'Venezuela', 245: 'França', 249: 'Alemanha', 251: 'Itália',
      252: 'Espanha', 253: 'Portugal', 254: 'Holanda', 308: 'China',
      351: 'Japão', 383: 'Israel', 386: 'Líbano', 388: 'Síria',
      399: 'Argentina', 403: 'Bolívia', 431: 'Canadá', 432: 'Chile',
      453: 'Colômbia', 492: 'Equador', 531: 'México', 589: 'Paraguai',
      599: 'Peru', 628: 'Áustria', 684: 'Bélgica', 764: 'Hungria',
      795: 'Polônia',
    };

    this.exteriorQuals = new Set([37, 38, 55, 56, 57, 58, 66, 70, 71, 72, 73, 74, 75, 79]);

    this.qualificacaoSocioMap = {
      0: "Não informada", 5: "Administrador", 8: "Conselheiro de Administração",
      9: "Curador", 10: "Diretor", 11: "Interventor", 12: "Inventariante",
      13: "Liquidante", 14: "Mãe", 15: "Pai", 16: "Presidente", 17: "Procurador",
      18: "Secretário", 19: "Síndico (Condomínio)", 20: "Sociedade Consorciada",
      21: "Sociedade Filiada", 22: "Sócio", 23: "Sócio Capitalista",
      24: "Sócio Comanditado", 25: "Sócio Comanditário", 26: "Sócio de Indústria",
      28: "Sócio-Gerente", 29: "Sócio Incapaz ou Relat.Incapaz (exceto menor)",
      30: "Sócio Menor (Assistido/Representado)", 31: "Sócio Ostensivo",
      32: "Tabelião", 33: "Tesoureiro", 34: "Titular de Empresa Individual Imobiliária",
      35: "Tutor", 37: "Sócio Pessoa Jurídica Domiciliado no Exterior",
      38: "Sócio Pessoa Física Residente no Exterior", 39: "Diplomata", 40: "Cônsul",
      41: "Representante de Organização Internacional", 42: "Oficial de Registro",
      43: "Responsável", 46: "Ministro de Estado das Relações Exteriores",
      47: "Sócio Pessoa Física Residente no Brasil",
      48: "Sócio Pessoa Jurídica Domiciliado no Brasil",
      49: "Sócio-Administrador", 50: "Empresário",
      51: "Candidato a cargo Político Eletivo", 52: "Sócio com Capital",
      53: "Sócio sem Capital", 54: "Fundador",
      55: "Sócio Comanditado Residente no Exterior",
      56: "Sócio Comanditário Pessoa Física Residente no Exterior",
      57: "Sócio Comanditário Pessoa Jurídica Domiciliado no Exterior",
      58: "Sócio Comanditário Incapaz", 59: "Produtor Rural",
      60: "Cônsul Honorário", 61: "Responsável indígena",
      62: "Representante da Instituição Extraterritorial",
      63: "Cotas em Tesouraria", 64: "Administrador Judicial",
      65: "Titular Pessoa Física Residente ou Domiciliado no Brasil",
      66: "Titular Pessoa Física Residente ou Domiciliado no Exterior",
      67: "Titular Pessoa Física Incapaz ou Relativamente Incapaz (exceto menor)",
      68: "Titular Pessoa Física Menor (Assistido/Representado)",
      69: "Beneficiário Final", 70: "Administrador Residente ou Domiciliado no Exterior",
      71: "Conselheiro de Administração Residente ou Domiciliado no Exterior",
      72: "Diretor Residente ou Domiciliado no Exterior",
      73: "Presidente Residente ou Domiciliado no Exterior",
      74: "Sócio-Administrador Residente ou Domiciliado no Exterior",
      75: "Fundador Residente ou Domiciliado no Exterior",
      78: "Titular Pessoa Jurídica Domiciliada no Brasil",
      79: "Titular Pessoa Jurídica Domiciliada no Exterior"
    };

    this.situacaoClass = { Ativa: 'conn-sit-ativa', Baixada: 'conn-sit-baixada', Inapta: 'conn-sit-inapta', Suspensa: 'conn-sit-suspensa' };
    this.situacaoColor = { Ativa: '#00c853', Baixada: '#ff5050', Inapta: '#ff9800', Suspensa: '#ffc107' };
    this.nodeTypeColor = { company: '#00c853', israeli_company: '#0038b8', israeli_socio: '#7eb8f7', socio: '#ffd600' };

    this.loadingEl = null;
    this.zoom = null;

    this.simulationParams = {
      linkDistance: 145, chargeStrength: -500, linkStrength: 0.1, alphaDecay: 0.02
    };

    this.visualParams = { nodeSizeMultiplier: 3.5, linkOpacity: 0.6, linkWidth: 2.0 };

    this.setupCanvas();
    this.setupEventListeners();
    this.loadNetwork();
  }

  setupCanvas() {
    const width = window.innerWidth;
    const height = window.innerHeight;
    const ratio = Math.min(window.devicePixelRatio, 2);
    this.canvas.width = width * ratio;
    this.canvas.height = height * ratio;
    this.canvas.style.width = width + 'px';
    this.canvas.style.height = height + 'px';
    this.context.scale(ratio, ratio);
    this.width = width;
    this.height = height;
  }

  setupEventListeners() {
    const searchInput = document.getElementById('searchInput');
    const searchClear = document.getElementById('searchClear');

    searchInput.addEventListener('input', (e) => {
      const val = e.target.value.toLowerCase();
      searchClear.style.display = val ? 'flex' : 'none';
      this.searchNodes(val);
    });

    searchClear.addEventListener('click', () => {
      searchInput.value = '';
      searchClear.style.display = 'none';
      this.searchNodes('');
    });

    this.zoom = d3.zoom()
      .scaleExtent([0.03, 10])
      .on('zoom', (event) => { this.transform = event.transform; this.redraw(); });

    d3.select(this.canvas).call(this.zoom);

    this.canvas.addEventListener('click', (event) => {
      if (!this.data) return;
      const rect = this.canvas.getBoundingClientRect();
      const canvasX = (event.clientX - rect.left - this.transform.x) / this.transform.k;
      const canvasY = (event.clientY - rect.top  - this.transform.y) / this.transform.k;

      let clickedNode = null, minDist = Infinity;
      for (const node of this.data.nodes) {
        const d = Math.hypot(canvasX - node.x, canvasY - node.y);
        if (d <= 30 && d < minDist) { clickedNode = node; minDist = d; }
      }

      if (clickedNode) { this.selectNode(clickedNode); this.showNodeInfo(clickedNode); }
      else { this.clearSelection(); this.hideNodeInfo(); }
    });

    d3.select(this.canvas).call(
      this.zoom.transform,
      d3.zoomIdentity.translate(this.width / 2, this.height / 2).scale(0.5)
    );

    window.addEventListener('resize', () => { this.setupCanvas(); if (this.data) this.redraw(); });

    document.getElementById('closeNodeInfo').addEventListener('click', () => {
      this.hideNodeInfo(); this.clearSelection();
    });

    document.getElementById('edgesBrightBtn').addEventListener('click', () => {
      this.edgesBright = !this.edgesBright;
      document.getElementById('edgesBrightBtn').classList.toggle('active', this.edgesBright);
      this.redraw();
    });

  }

  getQualificacaoDescription(codigo) {
    return this.qualificacaoSocioMap[codigo] || 'Não informada';
  }

  // ── Data loading ──────────────────────────────────────────────────────────

  async loadNetwork() {
    this.showLoading(true, 'Carregando rede israelense…');
    try {
      const response = await fetch('output/network_israel.json');
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const total = parseInt(response.headers.get('content-length') || '0');
      if (total && response.body) {
        const reader = response.body.getReader();
        const chunks = [];
        let received = 0;
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
          received += value.length;
          this.showLoading(true, `Carregando… ${Math.round(received / total * 100)}%`);
        }
        const buf = new Uint8Array(received);
        let offset = 0;
        for (const chunk of chunks) { buf.set(chunk, offset); offset += chunk.length; }
        this.data = JSON.parse(new TextDecoder().decode(buf));
      } else {
        this.data = await response.json();
      }
      this.paisMap = this.data.paisMap ?? this.paisMap;
      this.qualificacaoSocioMap = this.data.qualificacaoSocioMap ?? this.qualificacaoSocioMap;
      console.log('Loaded:', this.data.nodes.length, 'nodes,', this.data.links.length, 'links');
      this.processData();
      this.initializeSimulation();
      this.updateStats();
      this.populateCnaeFilter();
      this.initSituacaoFilter();
      this.initYearSlider();
      this.restoreFromURL();
    } catch (err) {
      console.error(err);
      alert('Não foi possível carregar os dados. Execute "bun generate.js" primeiro.');
    }
    this.showLoading(false);
  }

  processData() {
    this.data.nodes.forEach(node => {
      node.originalColor  = node.color;
      node.originalRadius = node.originalRadius ?? node.radius;
    });
  }

  initializeSimulation() {
    if (this.simulation) this.simulation.stop();
    this.simulation = d3.forceSimulation(this.data.nodes)
      .force('link', d3.forceLink(this.data.links).id(d => d.id)
        .distance(this.simulationParams.linkDistance)
        .strength(this.simulationParams.linkStrength))
      .force('charge', d3.forceManyBody().strength(this.simulationParams.chargeStrength))
      .force('center', d3.forceCenter(0, 0))
      .force('collision', d3.forceCollide().radius(d => d.radius + 2))
      .alphaDecay(this.simulationParams.alphaDecay)
      .on('tick', () => this.redraw());
  }

  // ── Situação filter ──────────────────────────────────────────────────────

  initSituacaoFilter() {
    const counts = new Map();
    this.data.nodes
      .filter(n => n.type === 'company' || n.type === 'israeli_company')
      .forEach(n => {
        const s = n.situacao || '—';
        counts.set(s, (counts.get(s) || 0) + 1);
      });

    const order = ['Ativa', 'Baixada', 'Inapta', 'Suspensa', '—'];
    const container = document.getElementById('situacaoChips');
    container.innerHTML = '';

    order.forEach(sit => {
      if (!counts.has(sit)) return;
      const chip = document.createElement('button');
      chip.className = 'sit-chip sit-chip-' + sit.toLowerCase().replace('—', 'desconhecida');
      chip.dataset.sit = sit;
      chip.textContent = `${sit} ${counts.get(sit).toLocaleString()}`;
      chip.addEventListener('click', () => this.toggleSituacaoFilter(sit));
      container.appendChild(chip);
    });
  }

  toggleSituacaoFilter(sit) {
    const all = new Set(
      [...document.querySelectorAll('#situacaoChips .sit-chip')].map(c => c.dataset.sit)
    );
    if (!this.activeSituacoes) {
      this.activeSituacoes = new Set([...all].filter(s => s !== sit));
    } else {
      const s = new Set(this.activeSituacoes);
      if (s.has(sit)) s.delete(sit); else s.add(sit);
      this.activeSituacoes = s.size === all.size ? null : s;
    }
    document.querySelectorAll('#situacaoChips .sit-chip').forEach(chip => {
      chip.classList.toggle('sit-chip-off', this.activeSituacoes != null && !this.activeSituacoes.has(chip.dataset.sit));
    });
    this.redraw();
  }

  // ── Year slider ──────────────────────────────────────────────────────────

  initYearSlider() {
    const years = this.data.nodes
      .filter(n => (n.type === 'company' || n.type === 'israeli_company') && n.data_abertura)
      .map(n => parseInt(n.data_abertura.slice(0, 4)))
      .filter(y => y > 1950 && y <= 2026);
    if (!years.length) return;
    const minYear = Math.min(...years);
    const maxYear = new Date().getFullYear();
    const slider = document.getElementById('yearSlider');
    slider.min = minYear;
    slider.max = maxYear;
    slider.value = maxYear;
    document.getElementById('yearMin').textContent = minYear;
    document.getElementById('yearMax').textContent = maxYear;
    document.getElementById('yearValue').textContent = 'todos';
    const updateLabel = (year) => {
      const atMax = year >= maxYear;
      if (atMax && !this.yearExact) {
        document.getElementById('yearValue').textContent = 'todos';
        this.yearFilter = null;
      } else {
        document.getElementById('yearValue').textContent = this.yearExact ? `em ${year}` : `até ${year}`;
        this.yearFilter = year;
      }
    };

    slider.addEventListener('input', () => {
      updateLabel(parseInt(slider.value));
      this.redraw();
    });

    const exactBtn = document.getElementById('yearExactBtn');
    exactBtn.addEventListener('click', () => {
      this.yearExact = !this.yearExact;
      exactBtn.classList.toggle('active', this.yearExact);
      updateLabel(parseInt(slider.value));
      this.redraw();
    });
  }

  // ── CNAE filter ──────────────────────────────────────────────────────────

  populateCnaeFilter() {
    const totalCompanies = this.data.nodes.filter(n => n.type === 'company' || n.type === 'israeli_company').length;
    const cnaeCount = new Map();

    this.data.nodes
      .filter(n => (n.type === 'company' || n.type === 'israeli_company') && n.cnae_code)
      .forEach(n => {
        if (!cnaeCount.has(n.cnae_code)) cnaeCount.set(n.cnae_code, { count: 0, desc: n.cnae_desc || n.cnae_code });
        cnaeCount.get(n.cnae_code).count++;
      });

    const cnaes = [...cnaeCount.entries()]
      .map(([code, { count, desc }]) => ({ code, desc, count }))
      .sort((a, b) => b.count - a.count);

    const listEl = document.getElementById('cnaeList');
    listEl.innerHTML = cnaes.map(c =>
      `<div class="cnae-item" data-code="${c.code}" title="${c.desc}"><span class="cnae-pct">(${c.count})</span> ${c.desc}</div>`
    ).join('');

    document.getElementById('cnaeFilter').style.display = 'flex';

    listEl.querySelectorAll('.cnae-item').forEach(item => {
      item.addEventListener('click', () => {
        if (this.activeCnaes === null) {
          listEl.querySelectorAll('.cnae-item').forEach(i => i.classList.add('cnae-disabled'));
          item.classList.remove('cnae-disabled');
        } else {
          item.classList.toggle('cnae-disabled');
        }
        this.applyFilter();
      });
    });

    document.getElementById('cnaeSearch').addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase();
      listEl.querySelectorAll('.cnae-item').forEach(item => {
        item.style.display = item.textContent.toLowerCase().includes(term) ? '' : 'none';
      });
    });

    document.getElementById('cnaeClearAll').addEventListener('click', () => {
      listEl.querySelectorAll('.cnae-item').forEach(item => item.classList.add('cnae-disabled'));
      this.applyFilter();
    });

    document.getElementById('cnaeSelectAll').addEventListener('click', () => {
      listEl.querySelectorAll('.cnae-item').forEach(item => item.classList.remove('cnae-disabled'));
      this.applyFilter();
    });
  }

  applyFilter() {
    const disabled = new Set([...document.querySelectorAll('.cnae-item.cnae-disabled')].map(el => el.dataset.code));
    if (disabled.size === 0) { this.activeCnaes = null; }
    else {
      this.activeCnaes = new Set([...document.querySelectorAll('.cnae-item:not(.cnae-disabled)')].map(el => el.dataset.code));
    }
    this.redraw();
  }

  isCompanyVisible(node) {
    if (node.type !== 'company' && node.type !== 'israeli_company') return false;
    if (this.activeTypes && !this.activeTypes.has(node.type)) return false;
    if (this.yearFilter) {
      const year = node.data_abertura ? parseInt(node.data_abertura.slice(0, 4)) : null;
      if (this.yearExact) {
        if (year !== this.yearFilter) return false;
      } else {
        if (year && year > this.yearFilter) return false;
      }
    }
    if (this.activeCnaes && !this.activeCnaes.has(String(node.cnae_code))) return false;
    if (this.activeSituacoes && !this.activeSituacoes.has(node.situacao || '—')) return false;
    return true;
  }

  toggleTypeFilter(type) {
    const allTypes = new Set(['company', 'israeli_company', 'israeli_socio', 'socio']);
    if (!this.activeTypes) {
      this.activeTypes = new Set([...allTypes].filter(t => t !== type));
    } else {
      const s = new Set(this.activeTypes);
      if (s.has(type)) s.delete(type); else s.add(type);
      this.activeTypes = s.size === allTypes.size ? null : s;
    }
    this.redraw();
  }

  isNodeDimmed(node) {
    if (this.activeTypes && !this.activeTypes.has(node.type)) return true;
    if (node.type === 'company' || node.type === 'israeli_company') {
      return !this.isCompanyVisible(node);
    }
    // Socio: dim if ALL connected companies are not visible
    const hasVisibleCompany = this.data.links.some(l => {
      const sid = typeof l.source === 'object' ? l.source.id : l.source;
      const tid = typeof l.target === 'object' ? l.target.id : l.target;
      const otherId = sid === node.id ? tid : tid === node.id ? sid : null;
      if (otherId == null) return false;
      const other = this.data.nodes.find(n => n.id === otherId);
      return other && this.isCompanyVisible(other);
    });
    return !hasVisibleCompany;
  }

  // ── Render ────────────────────────────────────────────────────────────────

  redraw() {
    if (!this.data) return;
    this.context.save();
    this.context.clearRect(0, 0, this.width, this.height);
    this.context.translate(this.transform.x, this.transform.y);
    this.context.scale(this.transform.k, this.transform.k);
    this.drawLinks();
    this.drawNodes();
    if (this.showLabels || this.selectedNode) this.drawLabels();
    if (this.transform.k > 1.0) this.drawEdgeLabels();
    this.context.restore();
  }

  drawLinks() {
    const baseWidth = this.visualParams.linkWidth;
    const baseAlpha = this.edgesBright ? 1.0 : this.visualParams.linkOpacity;
    const baseColor = this.edgesBright ? '#aaaaaa' : '#555';

    this.data.links.forEach(link => {
      const srcId = typeof link.source === 'object' ? link.source.id : link.source;
      const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
      const srcNode = this.data.nodes.find(n => n.id === srcId);
      const tgtNode = this.data.nodes.find(n => n.id === tgtId);

      if (this.activeCnaes && (this.isNodeDimmed(srcNode) || this.isNodeDimmed(tgtNode))) {
        this.context.globalAlpha = 0.04;
        this.context.strokeStyle = '#444';
        this.context.lineWidth = baseWidth;
        this.context.shadowBlur = 0;
        this.context.beginPath();
        this.context.moveTo(link.source.x, link.source.y);
        this.context.lineTo(link.target.x, link.target.y);
        this.context.stroke();
        return;
      }

      let strokeStyle = baseColor, lineWidth = baseWidth, alpha = baseAlpha;

      if (this.selectedNode) {
        const isConnected = link.source.id === this.selectedNode.id || link.target.id === this.selectedNode.id;
        if (isConnected) {
          strokeStyle = '#00ff88'; lineWidth = Math.max(2.0, 3 / this.transform.k); alpha = 1.0;
          this.context.shadowColor = '#00ff88'; this.context.shadowBlur = 10;
        } else { this.context.shadowBlur = 0; }
      } else { this.context.shadowBlur = 0; }

      this.context.globalAlpha = alpha;
      this.context.strokeStyle = strokeStyle;
      this.context.lineWidth = lineWidth;
      this.context.beginPath();
      this.context.moveTo(link.source.x, link.source.y);
      this.context.lineTo(link.target.x, link.target.y);
      this.context.stroke();
    });

    this.context.shadowBlur = 0;
  }

  drawNodes() {
    this.context.globalAlpha = 1;

    this.data.nodes.forEach(node => {
      const dimmed = this.isNodeDimmed(node);
      let fillStyle = node.color, radius = node.radius, strokeStyle = null, strokeWidth = 0;

      if (dimmed) {
        this.context.globalAlpha = 0.08;
        this.context.shadowBlur = 0;
        this.context.fillStyle = node.color;
        this.context.beginPath();
        this.context.arc(node.x, node.y, radius, 0, 2 * Math.PI);
        this.context.fill();
        return;
      }

      if (this.selectedNode) {
        if (node.id === this.selectedNode.id) {
          radius = node.radius * 1.8;
          strokeStyle = '#ffffff'; strokeWidth = Math.max(1, 3 / this.transform.k);
          this.context.shadowColor = '#ffffff'; this.context.shadowBlur = 15;
        } else if (this.isConnectedToSelected(node)) {
          fillStyle = '#00ff88'; radius = node.radius * 1.4;
          strokeStyle = '#ffffff'; strokeWidth = Math.max(1, 2 / this.transform.k);
          this.context.shadowColor = '#00ff88'; this.context.shadowBlur = 10;
        } else { this.context.shadowBlur = 0; }
      } else { this.context.shadowBlur = 0; }

      this.context.globalAlpha = 1.0;
      this.context.fillStyle = fillStyle;
      this.context.beginPath();
      this.context.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      this.context.fill();

      if (strokeStyle && strokeWidth > 0) {
        this.context.strokeStyle = strokeStyle; this.context.lineWidth = strokeWidth; this.context.stroke();
      }

      if (node.type === 'israeli_socio' && node.id !== this.selectedNode?.id) {
        this.context.strokeStyle = 'rgba(255,255,255,0.35)';
        this.context.lineWidth = 0.5; this.context.stroke();
      }
    });

    this.context.shadowBlur = 0;
  }

  drawLabels() {
    this.labelPositions = [];
    const zoom = this.transform.k;

    const labelsToShow = this.data.nodes.filter(node => {
      if (this.isNodeDimmed(node)) return false;
      if (this.showLabels) return true;
      if (this.selectedNode) return node.id === this.selectedNode.id || this.isConnectedToSelected(node);
      if (zoom > 2.0) return node.radius >= 3;
      if (zoom > 1.0) return node.type === 'company' || node.radius >= 5;
      return node.type === 'company' || node.radius > 8;
    });

    labelsToShow.sort((a, b) => {
      const aIsComp = a.type === 'company'; const bIsComp = b.type === 'company';
      if (aIsComp !== bIsComp) return bIsComp - aIsComp;
      if (this.selectedNode) {
        if (a.id === this.selectedNode.id) return -1;
        if (b.id === this.selectedNode.id) return 1;
      }
      return b.radius - a.radius;
    });

    let maxLabels;
    if (this.showLabels)   maxLabels = Math.max(500, Math.min(2000, zoom * 800));
    else if (zoom > 2.0)   maxLabels = Math.max(200, Math.min(800, zoom * 300));
    else if (zoom > 1.0)   maxLabels = Math.max(100, Math.min(400, zoom * 200));
    else                   maxLabels = Math.max(50, Math.min(150, zoom * 100));

    const finalLabels = labelsToShow.slice(0, maxLabels);
    this.context.font = '14px Barlow';
    this.context.textAlign = 'center';

    finalLabels.forEach(node => {
      let fontSize  = Math.max(12, Math.min(20, 12 + zoom * 3));
      let maxLength = Math.max(15, Math.min(60, 15 + zoom * 15));

      if (this.selectedNode) {
        if (node.id === this.selectedNode.id) { fontSize = Math.min(20, fontSize * 1.5); maxLength = Math.min(80, maxLength * 1.5); }
        else if (this.isConnectedToSelected(node)) { fontSize = Math.min(18, fontSize * 1.2); maxLength = Math.min(70, maxLength * 1.2); }
      }

      const text = node.label.length > maxLength ? node.label.substring(0, maxLength) + '…' : node.label;
      this.context.font = `${fontSize}px Barlow`;
      const textWidth = this.context.measureText(text).width;
      const textHeight = fontSize + 2;
      const offset = node.radius + Math.max(8, 12 / zoom);
      const labelY = this.findBestLabelPosition(node.x, node.y - offset, textWidth, textHeight);

      let fillStyle = '#ffffff', strokeStyle = '#000000';
      let lineWidth = Math.max(2, 4 / zoom);

      if (this.selectedNode) {
        if (node.id === this.selectedNode.id)     { lineWidth = Math.max(3, 5 / zoom); }
        else if (this.isConnectedToSelected(node)) { fillStyle = '#00ff88'; }
      }

      this.context.lineWidth = lineWidth;
      this.context.strokeStyle = strokeStyle;
      this.context.fillStyle = fillStyle;
      this.context.strokeText(text, node.x, labelY);
      this.context.fillText(text, node.x, labelY);

      this.labelPositions.push({ x: node.x - textWidth / 2 - 2, y: labelY - textHeight - 2, width: textWidth + 4, height: textHeight + 4 });
    });
  }

  findBestLabelPosition(x, preferredY, width, height) {
    const sp = Math.max(15, 25 / this.transform.k);
    const positions = [preferredY, preferredY - sp, preferredY + sp, preferredY - sp*2, preferredY + sp*2, preferredY - sp*3, preferredY + sp*3];
    for (const y of positions) {
      const r = { x: x - width/2 - 2, y: y - height - 2, width: width + 4, height: height + 4 };
      if (!this.hasLabelCollision(r)) return y;
    }
    return preferredY;
  }

  hasLabelCollision(rect) {
    return this.labelPositions.some(p =>
      rect.x < p.x + p.width && rect.x + rect.width > p.x &&
      rect.y < p.y + p.height && rect.y + rect.height > p.y
    );
  }

  drawEdgeLabels() {
    if (!this.data?.links) return;
    this.context.lineWidth = 2; this.context.textAlign = 'center'; this.context.textBaseline = 'middle';
    const fs = Math.max(8, Math.min(12, 8 + this.transform.k * 1.5));
    this.context.font = `${fs}px Arial`;
    const showAll = this.transform.k > 2.0;

    this.data.links.forEach(link => {
      if (!link.qualificacao_socio && link.qualificacao_socio !== 0) return;
      const s = typeof link.source === 'object' ? link.source.id : link.source;
      const t = typeof link.target === 'object' ? link.target.id : link.target;
      let show = showAll;
      if (this.selectedNode && !showAll) {
        show = s === this.selectedNode.id || t === this.selectedNode.id;
      }
      if (!show) return;

      const desc = this.getQualificacaoDescription(link.qualificacao_socio);
      if (!desc || desc === 'Não informada') return;

      const midX = (link.source.x + link.target.x) / 2;
      const midY = (link.source.y + link.target.y) / 2;
      const angle = Math.atan2(link.target.y - link.source.y, link.target.x - link.source.x);
      const off = 15 / this.transform.k;
      const maxLen = Math.max(10, 20 - (2 - this.transform.k) * 5);
      const text = desc.length > maxLen ? desc.substring(0, maxLen) + '…' : desc;

      this.context.fillStyle = this.selectedNode && (s === this.selectedNode.id || t === this.selectedNode.id) ? '#00ff88' : '#cccccc';
      this.context.strokeStyle = '#000000';
      this.context.strokeText(text, midX + Math.sin(angle) * off, midY - Math.cos(angle) * off);
      this.context.fillText(text, midX + Math.sin(angle) * off, midY - Math.cos(angle) * off);
    });
  }

  // ── URL sharing ───────────────────────────────────────────────────────────

  getNodeStableId(node) {
    if (node.cnpj_basico)    return `cnpj:${node.cnpj_basico}`;
    if (node.cpf_cnpj_socio) return `cpf:${node.cpf_cnpj_socio}`;
    return `name:${encodeURIComponent(node.label)}`;
  }

  findNodeByStableId(stableId) {
    if (stableId.startsWith('cnpj:')) return this.data.nodes.find(n => n.cnpj_basico === stableId.slice(5));
    if (stableId.startsWith('cpf:'))  return this.data.nodes.find(n => n.cpf_cnpj_socio === stableId.slice(4));
    if (stableId.startsWith('name:')) {
      const name = decodeURIComponent(stableId.slice(5));
      return this.data.nodes.find(n => n.label === name);
    }
    return null;
  }

  updateURL(node) {
    const url = new URL(window.location);
    url.searchParams.set('node', this.getNodeStableId(node));
    history.replaceState(null, '', url);
    const copyBtn = document.getElementById('copyNodeLink');
    if (copyBtn) copyBtn.style.display = 'flex';
  }

  clearURL() {
    const url = new URL(window.location);
    url.searchParams.delete('node');
    history.replaceState(null, '', url);
    const copyBtn = document.getElementById('copyNodeLink');
    if (copyBtn) copyBtn.style.display = 'none';
  }

  restoreFromURL() {
    const stableId = new URLSearchParams(window.location.search).get('node');
    if (!stableId) return;
    const node = this.findNodeByStableId(stableId);
    if (node) { this.selectNode(node); this.showNodeInfo(node); }
  }

  selectNode(node) { this.selectedNode = node; this.updateURL(node); this.redraw(); }
  clearSelection() { this.selectedNode = null; this.clearURL(); this.redraw(); }

  showNodeInfo(node) {
    const connectedNodes = [];
    this.data.links.forEach(link => {
      const sid = typeof link.source === 'object' ? link.source.id : link.source;
      const tid = typeof link.target === 'object' ? link.target.id : link.target;
      if (sid === node.id) {
        const t = typeof link.target === 'object' ? link.target : this.data.nodes.find(n => n.id === link.target);
        if (t) connectedNodes.push(t);
      } else if (tid === node.id) {
        const s = typeof link.source === 'object' ? link.source : this.data.nodes.find(n => n.id === link.source);
        if (s) connectedNodes.push(s);
      }
    });

    const unique = connectedNodes
      .filter((n, i, a) => a.findIndex(x => x.id === n.id) === i)
      .sort((a, b) => a.label.localeCompare(b.label));

    const typeLabel = { company: 'Empresa Brasileira', israeli_company: 'Empresa Israelense', israeli_socio: 'Sócio Israelense', socio: 'Sócio' }[node.type] || 'Nó';
    const typeClass = { company: 'reag', israeli_company: 'expanded', israeli_socio: 'connected', socio: 'normal' }[node.type] || 'normal';

    // Company details block
    let detailsHtml = '';
    if ((node.type === 'company' || node.type === 'israeli_company') && (node.uf || node.cnae_code || node.situacao)) {
      const fmt = (val) => val || '—';
      const fmtCapital = (v) => v != null && v > 0 ? 'R$ ' + Number(v).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '—';
      const sitClass = { 'Ativa': 'sit-ativa', 'Baixada': 'sit-baixada', 'Inapta': 'sit-baixada', 'Suspensa': 'sit-suspensa' }[node.situacao] || '';
      const cnaeText = node.cnae_code ? `${node.cnae_code} — ${fmt(node.cnae_desc)}` : '—';
      let locText;
      if (node.uf === 'EX' || node.est_pais) {
        const countryName = node.est_pais ? (this.paisMap[node.est_pais] || `País ${node.est_pais}`) : 'Exterior';
        locText = countryName;
      } else {
        locText = [node.uf, node.municipio].filter(Boolean).join(' — ') || '—';
      }

      detailsHtml = `
        <div class="company-details">
          ${node.cnae_code   ? `<div class="detail-row"><span class="dl">CNAE</span><span class="dv">${cnaeText}</span></div>` : ''}
          ${node.uf          ? `<div class="detail-row"><span class="dl">Localização</span><span class="dv">${locText}</span></div>` : ''}
          ${node.data_abertura ? `<div class="detail-row"><span class="dl">Abertura</span><span class="dv">${node.data_abertura}</span></div>` : ''}
          ${node.situacao    ? `<div class="detail-row"><span class="dl">Situação</span><span class="dv ${sitClass}">${node.situacao}</span></div>` : ''}
          ${node.porte       ? `<div class="detail-row"><span class="dl">Porte</span><span class="dv">${node.porte}</span></div>` : ''}
          ${node.capital_social != null ? `<div class="detail-row"><span class="dl">Capital</span><span class="dv">${fmtCapital(node.capital_social)}</span></div>` : ''}
          ${node.natureza_juridica ? `<div class="detail-row"><span class="dl">Natureza</span><span class="dv">${node.natureza_juridica}</span></div>` : ''}
          ${node.nome_fantasia ? `<div class="detail-row"><span class="dl">Fantasia</span><span class="dv">${node.nome_fantasia}</span></div>` : ''}
        </div>`;
    }

    let connectionsHtml = '';
    if (unique.length > 0) {
      const items = unique.map(cn => {
        const itemClass = 'connection-item ' + ({ company: 'reag', israeli_company: 'israeli-co', israeli_socio: 'connected', socio: 'estendida' }[cn.type] || 'estendida');
        const count = this.data.links.filter(l => {
          const s = typeof l.source === 'object' ? l.source.id : l.source;
          const t = typeof l.target === 'object' ? l.target.id : l.target;
          return s === cn.id || t === cn.id;
        }).length;
        const lb = this.data.links.find(l => {
          const s = typeof l.source === 'object' ? l.source.id : l.source;
          const t = typeof l.target === 'object' ? l.target.id : l.target;
          return (s === node.id && t === cn.id) || (s === cn.id && t === node.id);
        });
        let qualLabel = '';
        if (lb?.qualificacao_socio != null) {
          const qCode = lb.qualificacao_socio;
          if (this.exteriorQuals.has(qCode) && cn.pais != null) {
            qualLabel = this.paisMap[cn.pais] || `Exterior (${cn.pais})`;
          } else {
            qualLabel = this.getQualificacaoDescription(qCode);
          }
        }
        const dotColor = this.nodeTypeColor[cn.type] || '#888';
        let subHtml = '';
        let labelStyle = '';
        if (cn.type === 'company' || cn.type === 'israeli_company') {
          const sit = cn.situacao;
          const sitClass = this.situacaoClass[sit] || (sit && sit !== '—' ? 'conn-sit-desconhecida' : '');
          const ufSpan = (cn.uf && cn.uf !== 'EX') ? `<span>${cn.uf}</span>` : '';
          const sitBadge = (sit && sit !== '—') ? `<span class="conn-sit ${sitClass}">${sit}</span>` : '';
          if (ufSpan || sitBadge) subHtml = `<span class="conn-sub">${ufSpan}${sitBadge}</span>`;
          if (this.situacaoColor[sit]) labelStyle = ` style="color:${this.situacaoColor[sit]}"`;
        }
        return `<li class="${itemClass}" data-node-id="${cn.id}"><span class="conn-dot" style="background:${dotColor}"></span><span class="conn-body"><span class="conn-label"${labelStyle}>${cn.label}</span>${subHtml}${qualLabel ? `<span class="conn-qual">${qualLabel}</span>` : ''}</span><span class="conn-count">${count}</span></li>`;
      }).join('');

      connectionsHtml = `
        <div class="connections-section">
          <div class="connections-header">Conexões <span class="connection-count">${unique.length}</span></div>
          <ul class="connections-list">${items}</ul>
        </div>`;
    }

    document.getElementById('nodeInfo').style.display = 'flex';
    if (window.onNodeInfoToggle) window.onNodeInfoToggle(true);
    document.getElementById('nodeInfoContent').innerHTML = `
      <div class="node-details">
        <div class="node-name">${node.label}</div>
        <div class="node-badges"><span class="node-type ${typeClass}">${typeLabel}</span></div>
      </div>
      ${detailsHtml}
      ${connectionsHtml}`;

    document.querySelectorAll('.connection-item[data-node-id]').forEach(item => {
      item.addEventListener('click', (e) => {
        e.stopPropagation();
        const target = this.data.nodes.find(n => n.id === Number(item.getAttribute('data-node-id')));
        if (target) this.selectNodeById(target.id);
      });
    });
  }

  hideNodeInfo() {
    document.getElementById('nodeInfo').style.display = 'none';
    if (window.onNodeInfoToggle) window.onNodeInfoToggle(false);
  }

  selectNodeById(nodeId) {
    const node = this.data.nodes.find(n => n.id === nodeId);
    if (!node) return;
    this.selectNode(node); this.showNodeInfo(node);
    if (node.x != null) {
      const scale = Math.max(1, this.transform.k);
      d3.select(this.canvas).transition().duration(500).call(
        this.zoom.transform,
        d3.zoomIdentity.translate(this.width / 2 - node.x * scale, this.height / 2 - node.y * scale).scale(scale)
      );
    }
  }

  isConnectedToSelected(node) {
    if (!this.selectedNode) return false;
    return this.data.links.some(link => {
      const s = typeof link.source === 'object' ? link.source.id : link.source;
      const t = typeof link.target === 'object' ? link.target.id : link.target;
      return (s === this.selectedNode.id && t === node.id) || (t === this.selectedNode.id && s === node.id);
    });
  }

  searchNodes(searchTerm) {
    const countEl = document.getElementById('searchCount');
    if (!this.data || !searchTerm.trim()) {
      this.data.nodes.forEach(n => { n.color = n.originalColor; n.radius = n.originalRadius; });
      if (countEl) countEl.textContent = '';
      this.redraw(); return;
    }

    const matches = this.data.nodes.filter(n => n.label.toLowerCase().includes(searchTerm));
    if (countEl) countEl.textContent = matches.length ? `${matches.length} resultado${matches.length !== 1 ? 's' : ''}` : 'nenhum resultado';
    if (!matches.length) {
      this.data.nodes.forEach(n => { n.color = n.originalColor; n.radius = n.originalRadius; });
      this.redraw(); return;
    }

    const matchIds = new Set(matches.map(n => n.id));
    const connectedIds = new Set();
    this.data.links.forEach(l => {
      if (matchIds.has(l.source.id)) connectedIds.add(l.target.id);
      if (matchIds.has(l.target.id)) connectedIds.add(l.source.id);
    });

    this.data.nodes.forEach(n => {
      if (matchIds.has(n.id))         { n.color = '#ffff00'; n.radius = 10; }
      else if (connectedIds.has(n.id)) { n.color = '#00ffff'; n.radius = 6; }
      else                             { n.color = '#333333'; n.radius = 3; }
    });
    this.redraw();

    const first = matches[0];
    if (first) {
      const scale = 1.5;
      d3.select(this.canvas).transition().duration(750).call(
        this.zoom.transform,
        d3.zoomIdentity.translate(this.width/2 - first.x*scale, this.height/2 - first.y*scale).scale(scale)
      );
    }
  }

  // ── Stats ─────────────────────────────────────────────────────────────────

  updateStats() {
    const companies        = this.data.nodes.filter(n => n.type === 'company').length;
    const israeliCompanies = this.data.nodes.filter(n => n.type === 'israeli_company').length;
    const israeli          = this.data.nodes.filter(n => n.type === 'israeli_socio').length;
    const other            = this.data.nodes.filter(n => n.type === 'socio').length;

    // Update legend counts
    const legendCounts = { company: companies, israeli_company: israeliCompanies, israeli_socio: israeli, socio: other };
    document.querySelectorAll('.legend-item[data-type]').forEach(el => {
      const type = el.dataset.type;
      const cnt  = legendCounts[type];
      let countEl = el.querySelector('.legend-count');
      if (!countEl) { countEl = document.createElement('span'); countEl.className = 'legend-count'; el.appendChild(countEl); }
      countEl.textContent = cnt != null ? cnt.toLocaleString() : '';
    });

  }

  showLoading(show, msg) {
    const el = this.loadingEl ??= document.getElementById('loading');
    el.style.display = show ? 'block' : 'none';
    if (show && msg) el.textContent = msg;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.networkViz = new FastNetworkVisualization();
});
