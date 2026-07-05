/**
 * Client-side router — SPA navigation without full page reloads.
 */

import { api } from './api.js';
import { showProgressBar, completeProgressBar, showContentSkeleton } from './loading.js';
import { initPage } from './pages.js';

const PATH_MAP = {
    '/':             'dashboard',
    '/dashboard':    'dashboard',
    '/dataset':      'dataset',
    '/dataset/':     'dataset',
    '/question-1':   'question-1',
    '/question-1/':  'question-1',
    '/question-2':   'question-2',
    '/question-2/':  'question-2',
    '/question-3':   'question-3',
    '/question-3/':  'question-3',
    '/question-4':   'question-4',
    '/question-4/':  'question-4',
    '/reports':      'reports',
    '/reports/':     'reports',
    '/settings':     'settings',
    '/settings/':    'settings',
    '/about':        'about',
    '/about/':       'about',
};

let currentPage  = null;
let navigating   = false;

export function pathToPage(path) {
    if (!path) return null;
    const normalised = path.split('?')[0].replace(/\/+$/, '') || '/';
    return PATH_MAP[path] || PATH_MAP[normalised] || PATH_MAP[`${normalised}/`] || null;
}

export function pageToPath(page) {
    const paths = {
        dashboard:   '/',
        dataset:     '/dataset/',
        'question-1': '/question-1/',
        'question-2': '/question-2/',
        'question-3': '/question-3/',
        'question-4': '/question-4/',
        reports:     '/reports/',
        settings:    '/settings/',
        about:       '/about/',
    };
    return paths[page] || '/';
}

function saveScroll() {
    const area = document.getElementById('contentArea');
    if (area && currentPage) {
        sessionStorage.setItem(`scroll:${currentPage}`, String(area.scrollTop));
    }
}

function restoreScroll(page) {
    const area = document.getElementById('contentArea');
    const saved = sessionStorage.getItem(`scroll:${page}`);
    if (area && saved) {
        requestAnimationFrame(() => {
            requestAnimationFrame(() => { area.scrollTop = parseInt(saved, 10) || 0; });
        });
    } else if (area) {
        area.scrollTop = 0;
    }
}

function updateActiveNav(page) {
    document.querySelectorAll('.nav-item[data-spa-nav]').forEach((btn) => {
        const isActive = btn.dataset.spaNav === page;
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-current', isActive ? 'page' : 'false');
    });
}

function announcePageChange(title) {
    const announcer = document.getElementById('pageAnnouncer');
    if (announcer) {
        announcer.textContent = '';
        requestAnimationFrame(() => { announcer.textContent = `Navigated to ${title}`; });
    }
}

function renderError(area, message, page) {
    area.innerHTML = `
        <div class="card-rounded" style="max-width:520px;margin:2rem auto;text-align:center">
            <div class="empty-state">
                <i class="bi bi-exclamation-triangle-fill text-warning"></i>
                <h4>Unable to Load Page</h4>
                <p class="mb-4">${escapeHtml(message)}</p>
                <button type="button" class="btn btn-primary" id="retryBtn">
                    <i class="bi bi-arrow-clockwise me-2"></i>Retry
                </button>
            </div>
        </div>`;
    area.querySelector('#retryBtn')?.addEventListener('click', () => {
        navigate(pageToPath(page || currentPage), { force: true });
    });
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = String(str);
    return d.innerHTML;
}

export async function navigate(path, { replace = false, params = {}, force = false } = {}) {
    const page = pathToPage(path);
    if (!page) return;
    if (navigating && !force) return;
    if (page === currentPage && !force && !Object.keys(params).length) return;

    navigating = true;
    saveScroll();

    const area = document.getElementById('contentArea');
    showProgressBar();
    showContentSkeleton(area, page);

    try {
        const data = await api.getPartial(page, params);

        // Clear previous animate-in to allow re-trigger
        area.classList.remove('animate-in');
        area.innerHTML = data.html;
        void area.offsetHeight; // Force reflow
        area.classList.add('animate-in');

        const title = `${data.title} | ${window.APP_CONFIG?.courseCode || 'INF232'}`;
        document.title = title;
        announcePageChange(data.title);

        const url = pageToPath(page) + (params.k ? `?k=${params.k}` : '');
        if (replace) {
            history.replaceState({ page, params }, '', url);
        } else {
            history.pushState({ page, params }, '', url);
        }

        currentPage = page;
        updateActiveNav(page);
        completeProgressBar();
        initPage(page, area);
        restoreScroll(page);

    } catch (err) {
        completeProgressBar();
        if (err.status === 404 && err.data?.redirect) {
            navigating = false;
            await navigate(err.data.redirect, { replace: true });
            return;
        }
        renderError(area, err.message || 'Failed to load page.', page);
    } finally {
        navigating = false;
    }
}

export function initRouter() {
    currentPage = pathToPage(location.pathname) || 'dashboard';

    // Bind SPA nav buttons
    document.querySelectorAll('[data-spa-nav]').forEach((btn) => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const page = btn.dataset.spaNav;
            navigate(pageToPath(page));
            // Close mobile sidebar
            document.getElementById('sidebar')?.classList.remove('mobile-open');
            document.getElementById('sidebarBackdrop')?.classList.remove('active');
        });
    });

    // Browser back/forward
    window.addEventListener('popstate', (e) => {
        const state = e.state || {};
        const page  = state.page || pathToPage(location.pathname) || 'dashboard';
        navigate(pageToPath(page), { replace: true, params: state.params || {}, force: true });
    });

    // Initialize the current page (content already rendered server-side)
    updateActiveNav(currentPage);
    initPage(currentPage, document.getElementById('contentArea'));
}

export function getCurrentPage() { return currentPage; }

export async function refreshCurrentPage(params = {}) {
    if (!currentPage) return;
    await navigate(pageToPath(currentPage), { replace: true, params, force: true });
}
