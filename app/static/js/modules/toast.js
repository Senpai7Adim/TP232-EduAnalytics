/**
 * Toast notification system — custom animated toasts.
 */

const ICONS = {
    success: 'bi-check-circle-fill',
    danger:  'bi-x-circle-fill',
    warning: 'bi-exclamation-triangle-fill',
    info:    'bi-info-circle-fill',
};

const TITLES = {
    success: 'Success',
    danger:  'Error',
    warning: 'Warning',
    info:    'Info',
};

const DELAYS = {
    success: 4000,
    danger:  6000,
    warning: 5000,
    info:    4000,
};

/** Track recent messages to prevent duplicates */
const recentMessages = new Map();

export function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    // De-duplicate: ignore same message within 800ms
    const key = `${type}:${message}`;
    if (recentMessages.has(key)) return;
    recentMessages.set(key, true);
    setTimeout(() => recentMessages.delete(key), 800);

    const delay = DELAYS[type] || 4000;
    const icon  = ICONS[type]  || ICONS.info;
    const title = TITLES[type] || TITLES.info;
    const id    = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;

    const el = document.createElement('div');
    el.id = id;
    el.className = `app-toast toast-${type}`;
    el.setAttribute('role', 'alert');
    el.setAttribute('aria-live', type === 'danger' ? 'assertive' : 'polite');
    el.setAttribute('aria-atomic', 'true');
    el.innerHTML = `
        <i class="bi ${icon} toast-icon" aria-hidden="true"></i>
        <div class="toast-body">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${escapeHtml(message)}</div>
        </div>
        <button class="toast-close" aria-label="Dismiss notification" type="button">
            <i class="bi bi-x-lg" aria-hidden="true"></i>
        </button>
        <div class="toast-timer" style="animation-duration:${delay}ms"></div>
    `;

    container.appendChild(el);

    // Close button
    el.querySelector('.toast-close').addEventListener('click', () => dismiss(el));

    // Auto-dismiss
    const timer = setTimeout(() => dismiss(el), delay);
    el.dataset.timer = timer;
}

function dismiss(el) {
    if (!el || el.classList.contains('toast-hiding')) return;
    clearTimeout(parseInt(el.dataset.timer, 10));
    el.classList.add('toast-hiding');
    el.addEventListener('animationend', () => el.remove(), { once: true });
    // Fallback removal
    setTimeout(() => el.remove(), 500);
}

function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}
