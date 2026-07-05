/**
 * Page initialisers — bind page-specific behaviour after each SPA navigation.
 */

import { initLazyCharts, initChartActions } from './charts.js';
import { initForms } from './forms.js';
import { bindDatasetTable } from './table.js';

/* ============================================================
   COUNTER ANIMATION
   ============================================================ */
function animateCounters(root) {
    if (window.APP_CONFIG?.animations === false) return;
    root.querySelectorAll('.kpi-value[data-target]').forEach((el) => {
        const target = parseFloat(el.dataset.target);
        if (isNaN(target)) return;
        const isFloat    = String(el.dataset.target).includes('.');
        const suffix     = el.querySelector('small')?.outerHTML || '';
        const duration   = 900;
        const startTime  = performance.now();

        function tick(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const eased    = 1 - Math.pow(1 - progress, 3); // Cubic ease-out
            const current  = target * eased;
            el.innerHTML   = (isFloat ? current.toFixed(1) : Math.round(current)) + suffix;
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });
}

/* ============================================================
   METRIC COUNTER (for non-KPI numbers like regression metrics)
   ============================================================ */
function animateMetricPills(root) {
    if (window.APP_CONFIG?.animations === false) return;
    root.querySelectorAll('.metric-pill[data-value]').forEach((el) => {
        const raw    = el.dataset.value;
        const target = parseFloat(raw);
        if (isNaN(target)) return;
        const decimals = (raw.split('.')[1] || '').length;
        const prefix   = el.dataset.prefix || '';
        const suffix   = el.dataset.suffix || '';
        const duration = 700;
        const startTime = performance.now();
        function tick(now) {
            const progress = Math.min((now - startTime) / duration, 1);
            const eased    = 1 - Math.pow(1 - progress, 2);
            el.textContent = prefix + (target * eased).toFixed(decimals) + suffix;
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });
}

/* ============================================================
   STAGGER ANIMATION for card grids
   ============================================================ */
function staggerCards(root) {
    if (window.APP_CONFIG?.animations === false) return;
    const items = root.querySelectorAll('.kpi-card, .cluster-card, .report-stat');
    items.forEach((el, i) => {
        el.style.opacity  = '0';
        el.style.transform = 'translateY(12px)';
        el.style.transition = `opacity 0.35s ease ${i * 50}ms, transform 0.35s ease ${i * 50}ms`;
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                el.style.opacity   = '1';
                el.style.transform = 'translateY(0)';
            });
        });
    });
}

/* ============================================================
   PAGE-SPECIFIC INITS
   ============================================================ */
const PAGE_INIT = {
    dashboard: (root) => {
        animateCounters(root);
        staggerCards(root);
    },
    dataset: (root) => {
        bindDatasetTable(root);
    },
    'question-1': (root) => {
        animateMetricPills(root);
    },
    'question-2': (root) => {
        animateMetricPills(root);
        // Init prob-fill bars that may already be in the page
        root.querySelectorAll('.prob-fill[data-target]').forEach((bar) => {
            requestAnimationFrame(() => { bar.style.width = bar.dataset.target; });
        });
    },
    'question-3': (root) => {
        animateMetricPills(root);
        staggerCards(root);
    },
    'question-4': (root) => {
        animateMetricPills(root);
        staggerCards(root);
    },
    reports:  (root) => { staggerCards(root); },
    settings: () => {},
    about:    () => {},
};

/* ============================================================
   MAIN ENTRY POINT
   ============================================================ */
export function initPage(page, root) {
    if (!root) return;
    initForms(root);
    initLazyCharts(root);
    initChartActions(root);
    PAGE_INIT[page]?.(root);
}
