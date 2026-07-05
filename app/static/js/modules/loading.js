/**
 * Loading states — progress bar, skeletons, button states.
 */

/* ============================================================
   TOP PROGRESS BAR
   ============================================================ */
let progressTimer = null;
let progressValue = 0;

export function showProgressBar() {
    const bar = document.getElementById('pageProgressBar');
    if (!bar) return;
    clearTimeout(progressTimer);
    progressValue = 0;
    bar.style.width = '0%';
    bar.classList.add('progress-active');
    bar.classList.remove('progress-complete');

    // Simulate progress: fast to 70%, slow to 90%
    const step = () => {
        if (progressValue < 70) {
            progressValue += Math.random() * 15 + 10;
        } else if (progressValue < 90) {
            progressValue += Math.random() * 3 + 1;
        } else {
            return;
        }
        progressValue = Math.min(progressValue, 92);
        bar.style.width = `${progressValue}%`;
        progressTimer = setTimeout(step, 200 + Math.random() * 200);
    };
    progressTimer = setTimeout(step, 80);
}

export function completeProgressBar() {
    const bar = document.getElementById('pageProgressBar');
    if (!bar) return;
    clearTimeout(progressTimer);
    progressValue = 100;
    bar.style.width = '100%';
    bar.classList.add('progress-complete');
    setTimeout(() => {
        bar.classList.remove('progress-active', 'progress-complete');
        bar.style.width = '0%';
    }, 600);
}

/* ============================================================
   SKELETON GENERATORS
   ============================================================ */
export function skeletonKpiGrid(count = 8) {
    return `
    <div class="kpi-grid skeleton-grid skeleton-kpi-grid">
        ${Array.from({ length: count }, () => `
        <div class="kpi-card card-rounded skeleton-card" aria-hidden="true">
            <div class="skeleton skeleton-icon"></div>
            <div class="kpi-body" style="flex:1">
                <div class="skeleton skeleton-text w-75 mb-2"></div>
                <div class="skeleton skeleton-value"></div>
            </div>
        </div>`).join('')}
    </div>`;
}

export function skeletonCharts(count = 2) {
    return `
    <div class="chart-grid skeleton-grid skeleton-chart-grid mt-4" aria-hidden="true">
        ${Array.from({ length: count }, () => `
        <div class="chart-card card-rounded skeleton-card chart-span-6">
            <div class="skeleton skeleton-title mb-3"></div>
            <div class="skeleton skeleton-chart"></div>
        </div>`).join('')}
    </div>`;
}

export function skeletonTable(rows = 6, cols = 6) {
    const head = `
    <div class="skeleton-row" style="margin-bottom:0.5rem">
        ${Array.from({ length: cols }, () => '<div class="skeleton skeleton-th" style="height:0.7rem"></div>').join('')}
    </div>`;
    const body = Array.from({ length: rows }, () =>
        `<div class="skeleton-row">
            ${Array.from({ length: cols }, () => '<div class="skeleton skeleton-td"></div>').join('')}
        </div>`
    ).join('');
    return `<div class="skeleton-table card-rounded mt-4" aria-hidden="true">${head}${body}</div>`;
}

export function showContentSkeleton(container, page = null) {
    if (!container) return;
    // Page-specific skeletons
    let content;
    if (page === 'dataset') {
        content = `
            <div class="skeleton skeleton-page-title mb-2" aria-hidden="true"></div>
            <div class="skeleton skeleton-page-sub mb-4" style="width:45%" aria-hidden="true"></div>
            <div class="row g-4">
                <div class="col-lg-5">
                    <div class="card-rounded skeleton-card" style="min-height:280px" aria-hidden="true">
                        <div class="skeleton skeleton-title mb-3"></div>
                        ${Array.from({length:4},()=>'<div class="skeleton skeleton-text mb-2"></div>').join('')}
                        <div class="skeleton" style="height:40px;margin-top:1rem;border-radius:8px"></div>
                    </div>
                </div>
                <div class="col-lg-7">${skeletonTable(8, 6)}</div>
            </div>`;
    } else {
        content = `
            <div class="page-skeleton animate-in" aria-hidden="true">
                <div class="skeleton skeleton-page-title mb-2"></div>
                <div class="skeleton skeleton-page-sub mb-4" style="width:45%"></div>
                ${skeletonKpiGrid(4)}
                ${skeletonCharts(2)}
                ${skeletonTable()}
            </div>`;
    }
    container.innerHTML = content;
}

/* ============================================================
   BUTTON LOADING STATE
   ============================================================ */
export function setButtonLoading(btn, loading, loadingText = 'Processing…') {
    if (!btn) return;
    if (loading) {
        if (!btn.dataset.originalHtml) btn.dataset.originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.setAttribute('aria-busy', 'true');
        btn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            ${loadingText}`;
    } else {
        btn.disabled = false;
        btn.removeAttribute('aria-busy');
        if (btn.dataset.originalHtml) {
            btn.innerHTML = btn.dataset.originalHtml;
            delete btn.dataset.originalHtml;
        }
    }
}

/* ============================================================
   INLINE PROGRESS BAR (dataset generation)
   ============================================================ */
export function animateProgress(barEl) {
    if (!barEl) return null;
    const inner = barEl.querySelector('.progress-bar');
    if (!inner) return null;
    barEl.classList.remove('d-none');
    let progress = 0;
    let rafId;

    const step = () => {
        progress = Math.min(progress + Math.random() * 12 + 5, 90);
        inner.style.width = `${progress}%`;
        inner.setAttribute('aria-valuenow', Math.round(progress));
        if (progress < 90) rafId = requestAnimationFrame(step);
    };
    rafId = requestAnimationFrame(step);

    return {
        complete() {
            cancelAnimationFrame(rafId);
            inner.style.width = '100%';
            inner.setAttribute('aria-valuenow', 100);
            setTimeout(() => {
                barEl.classList.add('d-none');
                inner.style.width = '0%';
            }, 500);
        },
        fail() {
            cancelAnimationFrame(rafId);
            inner.classList.add('bg-danger');
            inner.style.width = '100%';
            setTimeout(() => {
                barEl.classList.add('d-none');
                inner.classList.remove('bg-danger');
                inner.style.width = '0%';
            }, 600);
        },
    };
}

/* ============================================================
   TABLE SKELETON OVERLAY
   ============================================================ */
export function setTableLoading(container, loading) {
    if (!container) return;
    if (loading) {
        container.classList.add('table-loading-overlay');
    } else {
        container.classList.remove('table-loading-overlay');
    }
}
