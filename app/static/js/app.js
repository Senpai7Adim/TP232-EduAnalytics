/**
 * EduAnalytics — SPA application entry point.
 */

import { api } from './modules/api.js';
import { showToast } from './modules/toast.js';
import { initRouter, navigate } from './modules/router.js';
import { refreshSession } from './modules/session.js';

/* ============================================================
   SIDEBAR
   ============================================================ */
function initSidebar() {
    const layout      = document.getElementById('appLayout');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    const mobileToggle = document.getElementById('mobileSidebarToggle');
    const sidebar     = document.getElementById('sidebar');
    const backdrop    = document.getElementById('sidebarBackdrop');

    // Restore collapsed state
    if (localStorage.getItem('sidebar-collapsed') === 'true') {
        layout?.classList.add('sidebar-collapsed');
        collapseBtn?.setAttribute('aria-expanded', 'false');
    }

    collapseBtn?.addEventListener('click', () => {
        const collapsed = layout?.classList.toggle('sidebar-collapsed');
        localStorage.setItem('sidebar-collapsed', collapsed ? 'true' : 'false');
        collapseBtn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    });

    const openMobile = () => {
        sidebar?.classList.add('mobile-open');
        backdrop?.classList.add('active');
        mobileToggle?.setAttribute('aria-expanded', 'true');
        // Trap focus within sidebar
        sidebar?.querySelector('.nav-item')?.focus();
    };

    const closeMobile = () => {
        sidebar?.classList.remove('mobile-open');
        backdrop?.classList.remove('active');
        mobileToggle?.setAttribute('aria-expanded', 'false');
        mobileToggle?.focus();
    };

    mobileToggle?.addEventListener('click', () => {
        if (sidebar?.classList.contains('mobile-open')) closeMobile();
        else openMobile();
    });

    backdrop?.addEventListener('click', closeMobile);

    // Close mobile sidebar on outside click
    document.addEventListener('click', (e) => {
        if (
            window.innerWidth < 992 &&
            sidebar?.classList.contains('mobile-open') &&
            !sidebar.contains(e.target) &&
            !mobileToggle?.contains(e.target)
        ) {
            closeMobile();
        }
    });

    // ESC closes mobile sidebar
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar?.classList.contains('mobile-open')) {
            closeMobile();
        }
    });
}

/* ============================================================
   THEME
   ============================================================ */
function initTheme() {
    const toggle = document.getElementById('themeToggle');
    const saved  = localStorage.getItem('eduanalytics-theme');
    if (saved) {
        document.documentElement.setAttribute('data-bs-theme', saved);
        _updateThemeIcon(saved);
    }

    toggle?.addEventListener('click', async () => {
        const current = document.documentElement.getAttribute('data-bs-theme') || 'light';
        const next    = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-bs-theme', next);
        localStorage.setItem('eduanalytics-theme', next);
        _updateThemeIcon(next);
        window.dispatchEvent(new Event('themechange'));
        try {
            await api.post('/api/settings', {
                theme:      next,
                language:   window.APP_CONFIG.language,
                animations: window.APP_CONFIG.animations,
            });
        } catch { /* non-critical */ }
        showToast(`Theme switched to ${next} mode.`, 'info');
    });
}

function _updateThemeIcon(theme) {
    const icon = document.querySelector('#themeToggle i');
    if (icon) icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
}

/* ============================================================
   GLOBAL SEARCH
   ============================================================ */
function initSearch() {
    const input   = document.getElementById('globalSearch');
    const results = document.getElementById('searchResults');
    if (!input || !results) return;

    let debounce;

    input.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(async () => {
            const q = input.value.trim();
            if (q.length < 2) {
                closeResults();
                return;
            }
            try {
                const data = await api.get(`/api/search?q=${encodeURIComponent(q)}`);
                if (!data.results.length) {
                    results.innerHTML = '<div class="search-result-item text-muted" role="option">No results found</div>';
                } else {
                    results.innerHTML = data.results.map((r) =>
                        `<div class="search-result-item" role="option" tabindex="0">
                            <strong>${r.Student_ID}</strong> &mdash;
                            Score: <strong>${r.Exam_Score}</strong>
                            <span class="badge-orientation ${r.Orientation.toLowerCase()} ms-2">${r.Orientation}</span>
                        </div>`
                    ).join('');
                }
                results.classList.add('active');
                input.setAttribute('aria-expanded', 'true');
            } catch {
                closeResults();
            }
        }, 300);
    });

    function closeResults() {
        results.classList.remove('active');
        input.setAttribute('aria-expanded', 'false');
    }

    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !results.contains(e.target)) {
            closeResults();
        }
    });

    input.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') { closeResults(); input.blur(); }
        if (e.key === 'ArrowDown') {
            const first = results.querySelector('[role="option"]');
            first?.focus();
        }
    });

    // Keyboard navigation within results
    results.addEventListener('keydown', (e) => {
        const items = [...results.querySelectorAll('[role="option"]')];
        const idx   = items.indexOf(document.activeElement);
        if (e.key === 'ArrowDown' && idx < items.length - 1) items[idx + 1]?.focus();
        if (e.key === 'ArrowUp') {
            if (idx <= 0) input.focus();
            else items[idx - 1]?.focus();
        }
        if (e.key === 'Escape') { closeResults(); input.focus(); }
    });
}

/* ============================================================
   KEYBOARD SHORTCUTS
   ============================================================ */
function initKeyboardShortcuts() {
    const NAV_SHORTCUTS = {
        '1': 'dashboard',
        '2': 'dataset',
        '3': 'question-1',
        '4': 'question-2',
        '5': 'question-3',
        '6': 'question-4',
        '7': 'reports',
        '8': 'settings',
    };

    document.addEventListener('keydown', (e) => {
        // Don't trigger in inputs
        if (['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement?.tagName)) return;

        if (e.ctrlKey || e.metaKey) {
            switch (e.key.toLowerCase()) {
                case 'k':
                    e.preventDefault();
                    document.getElementById('globalSearch')?.focus();
                    break;
                case 'b':
                    e.preventDefault();
                    document.getElementById('sidebarCollapseBtn')?.click();
                    break;
                case 'd':
                    e.preventDefault();
                    document.getElementById('themeToggle')?.click();
                    break;
                default:
                    break;
            }
        }

        // Number keys for navigation (no modifier)
        if (!e.ctrlKey && !e.metaKey && !e.altKey && !e.shiftKey) {
            const page = NAV_SHORTCUTS[e.key];
            if (page) navigate(`/${page === 'dashboard' ? '' : page + '/'}`);
        }
    });
}

/* ============================================================
   BOOT
   ============================================================ */
document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initTheme();
    initSearch();
    initKeyboardShortcuts();
    initRouter();
    refreshSession();
});

/* ============================================================
   GLOBAL API
   ============================================================ */
window.EduAnalytics = { showToast, api, navigate };
