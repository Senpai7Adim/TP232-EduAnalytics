/**
 * Plotly chart rendering — lazy load, theme-aware, fullscreen, resize.
 */

let chartObserver = null;
let resizeDebounce = null;

function themeColors() {
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    return {
        text: isDark ? '#CBD5E1' : '#475569',
        grid: isDark ? '#1E2D3F' : '#E8EFF5',
        bg:   'rgba(0,0,0,0)',
    };
}

function baseLayout(overrides = {}) {
    const { text, grid, bg } = themeColors();
    return {
        paper_bgcolor: bg,
        plot_bgcolor:  bg,
        font: { color: text, family: 'Inter, system-ui, sans-serif', size: 12 },
        autosize: true,
        margin: { t: 30, r: 20, b: 40, l: 50 },
        xaxis: { gridcolor: grid, linecolor: grid, zerolinecolor: grid },
        yaxis: { gridcolor: grid, linecolor: grid, zerolinecolor: grid },
        ...overrides,
    };
}

/**
 * Render a single chart container.
 */
export function renderChart(container) {
    const raw = container.getAttribute('data-chart');
    if (!raw || container.dataset.rendered === 'true') return;

    try {
        const figure = JSON.parse(raw);
        figure.layout = {
            ...baseLayout(),
            ...figure.layout,
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor:  'rgba(0,0,0,0)',
            font: { color: themeColors().text, family: 'Inter, system-ui, sans-serif', size: 12 },
            autosize: true,
        };
        // Ensure axis colors are applied
        const { grid } = themeColors();
        if (figure.layout.xaxis) figure.layout.xaxis.gridcolor = grid;
        else figure.layout.xaxis = { gridcolor: grid };
        if (figure.layout.yaxis) figure.layout.yaxis.gridcolor = grid;
        else figure.layout.yaxis = { gridcolor: grid };

        Plotly.react(container, figure.data, figure.layout, {
            responsive:      true,
            displayModeBar:  false,
            displaylogo:     false,
        });
        container.dataset.rendered = 'true';
        container.classList.add('chart-loaded');
    } catch (err) {
        console.error('[Chart] Render error:', err);
        container.innerHTML = `
            <div class="empty-state py-4">
                <i class="bi bi-bar-chart-line text-muted" style="font-size:2rem"></i>
                <p class="mt-2">Unable to render chart.</p>
            </div>`;
    }
}

/**
 * Force-re-render all charts in a root (e.g., after theme change).
 */
export function renderAllCharts(root = document) {
    root.querySelectorAll('.plotly-chart[data-chart]').forEach((el) => {
        el.dataset.rendered = 'false';
        renderChart(el);
    });
}

/**
 * Set up IntersectionObserver lazy-loading for charts.
 * Disconnects any previous observer first.
 */
export function initLazyCharts(root = document) {
    // Disconnect old observer to prevent memory leaks
    if (chartObserver) {
        chartObserver.disconnect();
        chartObserver = null;
    }

    chartObserver = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    renderChart(entry.target);
                    chartObserver?.unobserve(entry.target);
                }
            });
        },
        { rootMargin: '100px', threshold: 0.05 }
    );

    root.querySelectorAll('.plotly-chart[data-chart]').forEach((el) => {
        el.dataset.rendered = 'false';
        chartObserver.observe(el);
    });
}

/**
 * Handle fullscreen toggle and chart download actions.
 */
export function initChartActions(root = document) {
    // Fullscreen buttons
    root.querySelectorAll('[data-fullscreen]').forEach((btn) => {
        if (btn.dataset.bound) return;
        btn.dataset.bound = 'true';
        btn.addEventListener('click', () => {
            const chartId = btn.getAttribute('data-fullscreen');
            toggleFullscreen(chartId);
        });
    });

    // Download buttons
    root.querySelectorAll('[data-download]').forEach((btn) => {
        if (btn.dataset.bound) return;
        btn.dataset.bound = 'true';
        btn.addEventListener('click', () => {
            const chartId  = btn.getAttribute('data-download');
            const container = document.getElementById(chartId);
            if (!container) return;
            Plotly.downloadImage(container, {
                format:   'png',
                width:    1400,
                height:   800,
                filename: chartId,
            });
            window.EduAnalytics?.showToast('Chart downloaded as PNG.', 'success');
        });
    });
}

function toggleFullscreen(chartId) {
    const container = document.getElementById(chartId);
    if (!container) return;
    const card = container.closest('.chart-card');
    if (!card) return;

    const isFullscreen = card.classList.toggle('chart-fullscreen');

    if (isFullscreen) {
        // Add ESC hint / close button
        const closeBtn = document.createElement('button');
        closeBtn.className = 'chart-fullscreen-close';
        closeBtn.id = 'chartFullscreenClose';
        closeBtn.innerHTML = '<i class="bi bi-fullscreen-exit" aria-hidden="true"></i> Close (Esc)';
        closeBtn.setAttribute('aria-label', 'Exit fullscreen');
        card.appendChild(closeBtn);
        closeBtn.addEventListener('click', () => toggleFullscreen(chartId));
        document.body.style.overflow = 'hidden';
    } else {
        document.getElementById('chartFullscreenClose')?.remove();
        document.body.style.overflow = '';
    }

    // Re-render chart to fit new size
    container.dataset.rendered = 'false';
    requestAnimationFrame(() => {
        renderChart(container);
        if (typeof Plotly !== 'undefined') Plotly.Plots.resize(container);
    });
}

export function resetCharts() {
    if (chartObserver) {
        chartObserver.disconnect();
        chartObserver = null;
    }
}

/* ============================================================
   ESC key to exit fullscreen
   ============================================================ */
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const fullscreenCard = document.querySelector('.chart-card.chart-fullscreen');
        if (fullscreenCard) {
            const chartEl = fullscreenCard.querySelector('.plotly-chart');
            if (chartEl) toggleFullscreen(chartEl.id);
        }
    }
});

/* ============================================================
   Theme change: re-render all visible charts
   ============================================================ */
window.addEventListener('themechange', () => {
    document.querySelectorAll('.plotly-chart').forEach((el) => {
        el.dataset.rendered = 'false';
    });
    initLazyCharts();
});

/* ============================================================
   Window resize: debounce Plotly resize
   ============================================================ */
window.addEventListener('resize', () => {
    clearTimeout(resizeDebounce);
    resizeDebounce = setTimeout(() => {
        document.querySelectorAll('.plotly-chart.chart-loaded').forEach((el) => {
            if (typeof Plotly !== 'undefined') Plotly.Plots.resize(el);
        });
    }, 200);
});
