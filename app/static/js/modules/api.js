/**
 * API client — fetch wrapper with deduplication, timeout, and error handling.
 */

const inflight = new Map();
const REQUEST_TIMEOUT = 30_000; // 30 seconds

function requestKey(url, options = {}) {
    // Only deduplicate GET requests (POST keys include body)
    const method = options.method || 'GET';
    if (method !== 'GET') return null; // Don't deduplicate mutations
    return `GET:${url}`;
}

/**
 * Wraps a fetch promise with a timeout.
 */
function withTimeout(promise, ms) {
    return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
            reject(new Error('Request timed out. Please try again.'));
        }, ms);
        promise.then(
            (val) => { clearTimeout(timer); resolve(val); },
            (err) => { clearTimeout(timer); reject(err); }
        );
    });
}

/**
 * Extract the best error message from an API response.
 */
function extractError(data, status, statusText) {
    if (data && typeof data === 'object') {
        return data.error || data.message || data.detail || statusText || 'An error occurred.';
    }
    if (status === 404) return 'Resource not found.';
    if (status === 400) return 'Invalid request.';
    if (status === 500) return 'Server error. Please try again.';
    return statusText || 'An unexpected error occurred.';
}

export async function apiFetch(url, options = {}) {
    const key = requestKey(url, options);

    // Deduplicate in-flight GET requests
    if (key && inflight.has(key)) {
        return inflight.get(key);
    }

    const headers = {
        'X-Requested-With': 'XMLHttpRequest',
        Accept: 'application/json',
        ...(options.headers || {}),
    };

    if (options.json && !(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
        options.body = JSON.stringify(options.json);
    }

    const fetchOptions = { ...options, headers };
    delete fetchOptions.json; // Not a native fetch option

    const promise = withTimeout(
        fetch(url, fetchOptions).then(async (res) => {
            const contentType = res.headers.get('content-type') || '';
            let data = null;

            if (contentType.includes('application/json')) {
                try { data = await res.json(); } catch { data = null; }
            }

            if (!res.ok) {
                const err = new Error(extractError(data, res.status, res.statusText));
                err.status = res.status;
                err.data = data;
                throw err;
            }

            // JSON response
            if (data !== null) return data;

            // Binary/file response — return raw Response for blob handling
            return res;
        }).catch((err) => {
            // Network error (no connection, CORS, etc.)
            if (!err.status) {
                err.message = err.message.includes('timed out')
                    ? err.message
                    : 'Network error. Check your connection.';
            }
            throw err;
        }),
        REQUEST_TIMEOUT
    ).finally(() => {
        if (key) inflight.delete(key);
    });

    if (key) inflight.set(key, promise);
    return promise;
}

export function getPartial(page, params = {}) {
    const qs = new URLSearchParams(params).toString();
    const url = `/api/views/${page}${qs ? `?${qs}` : ''}`;
    return apiFetch(url);
}

export function downloadFile(url, filename) {
    return fetch(url, {
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
    }).then(async (res) => {
        const contentType = res.headers.get('content-type') || '';
        if (!res.ok || contentType.includes('application/json')) {
            let errMsg = 'Download failed.';
            if (contentType.includes('application/json')) {
                try {
                    const data = await res.json();
                    errMsg = data.error || data.message || errMsg;
                } catch { /* ignore */ }
            }
            throw new Error(errMsg);
        }
        const disposition = res.headers.get('content-disposition') || '';
        const match = disposition.match(/filename[^;=\n]*=\s*['"]?([^'"\n;]+)/);
        const name = match ? match[1] : filename || 'export';
        const blob = await res.blob();
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = name;
        document.body.appendChild(link);
        link.click();
        link.remove();
        URL.revokeObjectURL(link.href);
    });
}

export const api = {
    get:        (url)             => apiFetch(url),
    post:       (url, json)       => apiFetch(url, { method: 'POST', json }),
    upload:     (url, formData)   => apiFetch(url, { method: 'POST', body: formData }),
    getPartial,
    downloadFile,
};
