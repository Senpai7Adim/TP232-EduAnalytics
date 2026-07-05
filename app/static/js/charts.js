/**
 * EduAnalytics — Plotly chart rendering, download, and fullscreen
 */

document.addEventListener('DOMContentLoaded', () => {
    renderAllCharts();
    initChartActions();
});

window.addEventListener('themechange', renderAllCharts);

function renderAllCharts() {
    const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    const textColor = isDark ? '#CBD5E1' : '#475569';
    const gridColor = isDark ? '#334155' : '#E2E8F0';

    document.querySelectorAll('.plotly-chart[data-chart]').forEach((container) => {
        const raw = container.getAttribute('data-chart');
        if (!raw) return;

        try {
            const figure = JSON.parse(raw);
            figure.layout = {
                ...figure.layout,
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: { color: textColor, family: 'Inter, system-ui, sans-serif' },
            };
            if (figure.layout.xaxis) {
                figure.layout.xaxis.gridcolor = gridColor;
            } else {
                figure.layout.xaxis = { gridcolor: gridColor };
            }
            if (figure.layout.yaxis) {
                figure.layout.yaxis.gridcolor = gridColor;
            } else {
                figure.layout.yaxis = { gridcolor: gridColor };
            }

            const config = {
                responsive: true,
                displayModeBar: false,
                displaylogo: false,
            };

            Plotly.react(container, figure.data, figure.layout, config);
        } catch (err) {
            console.error('Chart render error:', err);
            container.innerHTML = '<p class="text-muted text-center py-4">Unable to render chart.</p>';
        }
    });
}

function initChartActions() {
    document.querySelectorAll('[data-fullscreen]').forEach((btn) => {
        btn.addEventListener('click', () => {
            const chartId = btn.getAttribute('data-fullscreen');
            const card = document.getElementById(chartId)?.closest('.chart-card');
            if (card) {
                card.classList.toggle('chart-fullscreen');
                renderAllCharts();
            }
        });
    });

    document.querySelectorAll('[data-download]').forEach((btn) => {
        btn.addEventListener('click', () => {
            const chartId = btn.getAttribute('data-download');
            const container = document.getElementById(chartId);
            if (container) {
                Plotly.downloadImage(container, {
                    format: 'png',
                    width: 1200,
                    height: 700,
                    filename: chartId,
                });
                window.EduAnalytics?.showToast('Chart downloaded as PNG', 'success');
            }
        });
    });
}

window.renderAllCharts = renderAllCharts;
