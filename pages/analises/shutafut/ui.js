// Legend type filters
document.querySelectorAll('.legend-item[data-type]').forEach(item => {
    item.addEventListener('click', () => {
        if (!window.networkViz) return;
        window.networkViz.toggleTypeFilter(item.dataset.type);
        const at = window.networkViz.activeTypes;
        document.querySelectorAll('.legend-item[data-type]').forEach(el => {
            el.classList.toggle('legend-disabled', at != null && !at.has(el.dataset.type));
        });
    });
});

document.getElementById('copyNodeLink').addEventListener('click', () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
        const btn = document.getElementById('copyNodeLink');
        btn.classList.add('copied');
        btn.textContent = '✓';
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.textContent = '🔗';
        }, 1500);
    });
});

// ── Panel resize & collapse ────────────────────────
(function () {
    const leftPanel  = document.getElementById('leftPanel');
    const rightPanel = document.getElementById('nodeInfo');
    const leftHandle  = document.getElementById('leftResizeHandle');
    const rightHandle = document.getElementById('rightResizeHandle');
    const leftTab  = document.getElementById('leftPanelTab');
    const rightTab = document.getElementById('rightPanelTab');
    const MARGIN = 20;
    let leftCollapsed  = false;
    let rightCollapsed = false;
    let rightVisible   = false;

    function updatePositions() {
        if (window.innerWidth <= 768) return;

        const lw = leftPanel.offsetWidth;
        const lh = leftPanel.offsetHeight;
        const lt = leftPanel.offsetTop;

        // Left tab — centered vertically to left panel
        leftTab.style.top = (lt + lh / 2) + 'px';
        leftTab.style.transform = 'translateY(-50%)';
        if (leftCollapsed) {
            leftTab.style.left = '0px';
            leftTab.textContent = '›';
            leftHandle.style.display = 'none';
        } else {
            leftTab.style.left = MARGIN + lw + 'px';
            leftTab.textContent = '‹';
            leftHandle.style.left = MARGIN + lw - 3 + 'px';
            leftHandle.style.display = 'block';
        }

        // Right tab & handle
        if (!rightVisible) {
            rightTab.style.display = 'none';
            rightHandle.style.display = 'none';
            return;
        }
        const rw = rightPanel.offsetWidth;
        const rh = rightPanel.offsetHeight;
        const rt = rightPanel.offsetTop;
        rightTab.style.display = 'flex';
        if (rightCollapsed) {
            rightTab.style.right = '0px';
            rightTab.style.top = rt + rh / 2 + 'px';
            rightTab.style.transform = 'translateY(-50%)';
            rightTab.textContent = '‹';
            rightHandle.style.display = 'none';
        } else {
            rightTab.style.right = MARGIN + rw + 'px';
            rightTab.style.top = rt + rh / 2 + 'px';
            rightTab.style.transform = 'translateY(-50%)';
            rightTab.textContent = '›';
            rightHandle.style.right = MARGIN + rw - 3 + 'px';
            rightHandle.style.top = rt + 'px';
            rightHandle.style.height = rh + 'px';
            rightHandle.style.bottom = 'auto';
            rightHandle.style.display = 'block';
        }
    }

    // ── Collapse toggles ──────────────────────────
    leftTab.addEventListener('click', () => {
        leftCollapsed = !leftCollapsed;
        if (leftCollapsed) {
            leftPanel.style.transform = `translateX(calc(-100% - ${MARGIN}px))`;
            leftPanel.style.pointerEvents = 'none';
        } else {
            leftPanel.style.transform = 'translateX(0)';
            leftPanel.style.pointerEvents = '';
        }
        updatePositions();
    });

    rightTab.addEventListener('click', () => {
        rightCollapsed = !rightCollapsed;
        if (rightCollapsed) {
            rightPanel.style.transform = `translateX(calc(100% + ${MARGIN}px))`;
            rightPanel.style.pointerEvents = 'none';
        } else {
            rightPanel.style.transform = 'translateX(0)';
            rightPanel.style.pointerEvents = '';
        }
        updatePositions();
    });

    // ── Resize drag ───────────────────────────────
    let isResizing = false, whichPanel = null, startX = 0, startW = 0;

    function startResize(e, which) {
        isResizing = true;
        whichPanel = which;
        startX = e.clientX;
        startW = which === 'left' ? leftPanel.offsetWidth : rightPanel.offsetWidth;
        document.getElementById(which === 'left' ? 'leftResizeHandle' : 'rightResizeHandle')
            .classList.add('dragging');
        document.body.style.cursor = 'ew-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    }

    leftHandle.addEventListener('mousedown', e => startResize(e, 'left'));
    rightHandle.addEventListener('mousedown', e => startResize(e, 'right'));

    document.addEventListener('mousemove', e => {
        if (!isResizing) return;
        if (whichPanel === 'left') {
            leftPanel.style.width = Math.max(355, Math.min(640, startW + e.clientX - startX)) + 'px';
        } else {
            rightPanel.style.width = Math.max(220, Math.min(640, startW - (e.clientX - startX))) + 'px';
        }
        updatePositions();
    });

    document.addEventListener('mouseup', () => {
        if (!isResizing) return;
        isResizing = false;
        leftHandle.classList.remove('dragging');
        rightHandle.classList.remove('dragging');
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        whichPanel = null;
    });

    // ── Mobile panel toggle ───────────────────────
    const mobileToggle = document.getElementById('mobileToggle');
    mobileToggle.addEventListener('click', e => {
        e.stopPropagation();
        leftPanel.classList.toggle('mobile-open');
    });
    document.addEventListener('click', e => {
        if (window.innerWidth <= 768 && !leftPanel.contains(e.target) && e.target !== mobileToggle) {
            leftPanel.classList.remove('mobile-open');
        }
    });

    // ── Hook from viz ─────────────────────────────
    window.onNodeInfoToggle = function (visible) {
        rightVisible = visible;
        if (visible) {
            rightCollapsed = false;
            rightPanel.style.transform = 'translateX(0)';
            rightPanel.style.pointerEvents = '';
        }
        requestAnimationFrame(updatePositions);
    };

    window.addEventListener('resize', updatePositions);
    updatePositions();
})();
