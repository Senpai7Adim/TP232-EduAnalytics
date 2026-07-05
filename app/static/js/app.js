/**
 * EduAnalytics — Core Application JavaScript
 * Sidebar, theme, search, animations, keyboard shortcuts, toasts
 */

document.addEventListener('DOMContentLoaded', () => {
    initSidebar();
    initTheme();
    initSearch();
    initAnimatedCounters();
    initKeyboardShortcuts();
    initFlashedToasts();
    initFormLoading();
});

function initFormLoading() {
    document.querySelectorAll('form').forEach((form) => {
        form.addEventListener('submit', () => {
            if (window.APP_CONFIG?.animations === false) return;
            const btn = form.querySelector('[type="submit"]');
            if (btn && !btn.disabled) {
                btn.dataset.originalHtml = btn.innerHTML;
                btn.disabled = true;
                btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing…';
            }
            document.body.classList.add('is-loading');
        });
    });
}

function initSidebar() {
    const layout = document.getElementById('appLayout');
    const collapseBtn = document.getElementById('sidebarCollapseBtn');
    const mobileToggle = document.getElementById('mobileSidebarToggle');
    const sidebar = document.getElementById('sidebar');

    const collapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (collapsed && layout) layout.classList.add('sidebar-collapsed');

    collapseBtn?.addEventListener('click', () => {
        layout?.classList.toggle('sidebar-collapsed');
        localStorage.setItem(
            'sidebar-collapsed',
            layout?.classList.contains('sidebar-collapsed') ? 'true' : 'false'
        );
    });

    mobileToggle?.addEventListener('click', () => {
        sidebar?.classList.toggle('mobile-open');
    });

    document.addEventListener('click', (e) => {
        if (window.innerWidth < 992 && sidebar?.classList.contains('mobile-open')) {
            if (!sidebar.contains(e.target) && !mobileToggle?.contains(e.target)) {
                sidebar.classList.remove('mobile-open');
            }
        }
    });
}

function initTheme() {
    const toggle = document.getElementById('themeToggle');
    const saved = localStorage.getItem('eduanalytics-theme');
    if (saved) {
        document.documentElement.setAttribute('data-bs-theme', saved);
        updateThemeIcon(saved);
    }

    toggle?.addEventListener('click', () => {
        const current = document.documentElement.getAttribute('data-bs-theme') || 'light';
        const next = current === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-bs-theme', next);
        localStorage.setItem('eduanalytics-theme', next);
        updateThemeIcon(next);
        window.dispatchEvent(new Event('themechange'));
        showToast(`Theme: ${next}`, 'info');
    });
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('#themeToggle i');
    if (icon) icon.className = theme === 'dark' ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
}

function initSearch() {
    const input = document.getElementById('globalSearch');
    const results = document.getElementById('searchResults');
    if (!input || !results) return;

    let debounce;
    input.addEventListener('input', () => {
        clearTimeout(debounce);
        debounce = setTimeout(async () => {
            const q = input.value.trim();
            if (q.length < 2) {
                results.classList.remove('active');
                return;
            }
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
                const data = await res.json();
                results.innerHTML = data.results.length
                    ? data.results.map((r) =>
                        `<div class="search-result-item">${r.Student_ID} — Score: ${r.Exam_Score} (${r.Orientation})</div>`
                    ).join('')
                    : '<div class="search-result-item text-muted">No results</div>';
                results.classList.add('active');
            } catch {
                results.classList.remove('active');
            }
        }, 300);
    });

    document.addEventListener('click', (e) => {
        if (!input.contains(e.target) && !results.contains(e.target)) {
            results.classList.remove('active');
        }
    });
}

function initAnimatedCounters() {
    if (window.APP_CONFIG?.animations === false) return;

    document.querySelectorAll('.kpi-value[data-target]').forEach((el) => {
        const target = parseFloat(el.dataset.target);
        if (isNaN(target)) return;
        const isFloat = String(el.dataset.target).includes('.');
        const duration = 1200;
        const start = performance.now();

        function tick(now) {
            const progress = Math.min((now - start) / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            const current = target * eased;
            const small = el.querySelector('small');
            const suffix = small ? small.outerHTML : '';
            el.innerHTML = (isFloat ? current.toFixed(1) : Math.round(current)) + suffix;
            if (progress < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
    });
}

function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        if (!(e.ctrlKey || e.metaKey)) return;
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
        }
    });
}

function initFlashedToasts() {
    document.querySelectorAll('.app-alert').forEach((alert) => {
        const text = alert.textContent.trim();
        const type = alert.classList.contains('alert-success') ? 'success'
            : alert.classList.contains('alert-danger') ? 'danger'
            : alert.classList.contains('alert-warning') ? 'warning' : 'info';
        showToast(text, type);
    });
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const id = `toast-${Date.now()}`;
    const bgClass = { success: 'text-bg-success', danger: 'text-bg-danger', warning: 'text-bg-warning', info: 'text-bg-primary' }[type] || 'text-bg-primary';

    container.insertAdjacentHTML('beforeend', `
        <div id="${id}" class="toast ${bgClass}" role="alert">
            <div class="toast-body">${message}</div>
        </div>
    `);

    const toastEl = document.getElementById(id);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

window.EduAnalytics = { showToast };
