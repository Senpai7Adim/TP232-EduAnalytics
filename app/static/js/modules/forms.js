/**
 * SPA form handlers — async submissions without page reload.
 */

import { api } from './api.js';
import { showToast } from './toast.js';
import { setButtonLoading, animateProgress } from './loading.js';
import { navigate, refreshCurrentPage } from './router.js';
import { loadDatasetTable, bindDatasetTable } from './table.js';
import { updateSessionUI } from './session.js';

/* ============================================================
   UTILITIES
   ============================================================ */
function formPayload(form) {
    const data = {};
    new FormData(form).forEach((val, key) => { data[key] = val; });
    return data;
}

function setFormError(form, message) {
    let el = form.querySelector('.form-error-msg');
    if (!el) {
        el = document.createElement('div');
        el.className = 'alert alert-danger form-error-msg mt-2';
        el.setAttribute('role', 'alert');
        form.insertBefore(el, form.querySelector('[type="submit"]'));
    }
    el.textContent = message;
    el.style.display = 'block';
    el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function clearFormError(form) {
    const el = form.querySelector('.form-error-msg');
    if (el) el.style.display = 'none';
}

/* ============================================================
   PREDICTION RENDERERS
   ============================================================ */
function renderExamPrediction(container, prediction) {
    if (!container) return;
    if (prediction.error) {
        container.innerHTML = `<div class="alert alert-danger card-rounded">${prediction.error}</div>`;
        return;
    }
    const warnings = (prediction.warnings || []).map((w) =>
        `<div class="alert alert-warning small mt-2"><i class="bi bi-exclamation-triangle me-1"></i>${w}</div>`
    ).join('');
    container.innerHTML = `
        <div class="text-center py-2">
            <div class="predicted-score">${prediction.predicted_score}<span>/100</span></div>
            <p class="mt-2"><strong>Reliability:</strong>
                <span class="badge-orientation ${prediction.reliability?.toLowerCase() || ''}">${prediction.reliability}</span>
            </p>
            ${warnings}
        </div>`;
    container.classList.add('animate-in');
}

function renderOrientationPrediction(container, prediction) {
    if (!container) return;
    if (prediction.error) {
        container.innerHTML = `<div class="alert alert-danger card-rounded">${prediction.error}</div>`;
        return;
    }
    const bars = Object.entries(prediction.probabilities || {}).map(([orient, prob]) => `
        <div class="prob-bar-row">
            <span>${orient}</span>
            <div class="prob-track" role="progressbar" aria-valuenow="${(prob*100).toFixed(1)}" aria-valuemin="0" aria-valuemax="100">
                <div class="prob-fill" style="width:0%" data-target="${(prob*100).toFixed(1)}%"></div>
            </div>
            <span>${(prob*100).toFixed(1)}%</span>
        </div>`).join('');

    container.innerHTML = `
        <div class="text-center mb-3">
            <div class="orientation-badge ${(prediction.prediction || '').toLowerCase()}">${prediction.prediction}</div>
        </div>
        ${bars}
        <p class="mt-3 small text-secondary">${prediction.explanation}</p>`;
    container.classList.add('animate-in');

    // Animate probability bars
    requestAnimationFrame(() => {
        container.querySelectorAll('.prob-fill').forEach((bar) => {
            const target = bar.dataset.target;
            requestAnimationFrame(() => { bar.style.width = target; });
        });
    });
}

/* ============================================================
   FORM HANDLERS
   ============================================================ */
const submitting = new Set(); // Guard against duplicate submissions

async function handleDatasetGenerate(form) {
    if (submitting.has(form)) return;
    submitting.add(form);
    const btn      = form.querySelector('[type="submit"]');
    const progress = document.getElementById('generateProgress');
    const progressAnim = animateProgress(progress);
    setButtonLoading(btn, true, 'Generating Dataset…');
    clearFormError(form);

    try {
        const payload = formPayload(form);
        const leaderName = String(payload.leader_name || '').trim();
        const numStudents = parseInt(payload.num_students, 10);

        if (!leaderName) { setFormError(form, 'Group leader name is required.'); return; }
        if (!numStudents || numStudents < 10) { setFormError(form, 'Number of students must be at least 10.'); return; }

        const data = await api.post('/api/dataset/generate', {
            leader_name: leaderName,
            num_students: numStudents,
        });
        progressAnim?.complete();
        showToast(data.message || 'Dataset generated successfully.', 'success');
        await updateSessionUI(data.meta);
        document.getElementById('datasetDownloadCard')?.classList.remove('d-none');
        const previewCard = document.getElementById('datasetPreviewCard');
        if (previewCard) await loadDatasetTable(previewCard);

        // Navigate to dashboard after a short delay
        setTimeout(() => navigate('/'), 800);

    } catch (err) {
        progressAnim?.fail?.();
        const msg = err.message || 'Generation failed.';
        setFormError(form, msg);
        showToast(msg, 'danger');
    } finally {
        setButtonLoading(btn, false);
        submitting.delete(form);
    }
}

async function handleDatasetImport(form) {
    if (submitting.has(form)) return;
    submitting.add(form);
    const btn = form.querySelector('[type="submit"]');
    setButtonLoading(btn, true, 'Importing…');
    clearFormError(form);

    try {
        const fd = new FormData(form);
        if (!fd.get('csv_file')?.size) { setFormError(form, 'Please select a CSV file.'); return; }

        const data = await api.upload('/api/dataset/import', fd);
        showToast(data.message || 'Dataset imported successfully.', 'success');
        await updateSessionUI(data.meta);
        document.getElementById('datasetDownloadCard')?.classList.remove('d-none');
        const previewCard = document.getElementById('datasetPreviewCard');
        if (previewCard) await loadDatasetTable(previewCard);
        setTimeout(() => navigate('/'), 800);

    } catch (err) {
        const msg = err.message || 'Import failed.';
        setFormError(form, msg);
        showToast(msg, 'danger');
    } finally {
        setButtonLoading(btn, false);
        submitting.delete(form);
    }
}

async function handlePredictExam(form) {
    if (submitting.has(form)) return;
    submitting.add(form);
    const btn      = form.querySelector('[type="submit"]');
    const resultEl = document.getElementById('examPredictionResult');
    setButtonLoading(btn, true, 'Predicting…');
    clearFormError(form);
    if (resultEl) {
        resultEl.innerHTML = '<div class="skeleton skeleton-chart" style="height:80px;border-radius:8px"></div>';
    }

    try {
        const p = formPayload(form);
        const data = await api.post('/api/predict/exam', {
            study_hours:    parseFloat(p.study_hours),
            attendance:     parseFloat(p.attendance),
            homework_score: parseFloat(p.homework_score),
        });
        renderExamPrediction(resultEl, data.prediction);
        showToast('Prediction completed.', 'success');
    } catch (err) {
        renderExamPrediction(resultEl, { error: err.message });
        showToast(err.message || 'Prediction failed.', 'danger');
    } finally {
        setButtonLoading(btn, false);
        submitting.delete(form);
    }
}

async function handlePredictOrientation(form) {
    if (submitting.has(form)) return;
    submitting.add(form);
    const btn      = form.querySelector('[type="submit"]');
    const resultEl = document.getElementById('orientationPredictionResult');
    setButtonLoading(btn, true, 'Classifying…');
    clearFormError(form);
    if (resultEl) {
        resultEl.innerHTML = '<div class="skeleton skeleton-chart" style="height:100px;border-radius:8px"></div>';
    }

    try {
        const p = formPayload(form);
        const data = await api.post('/api/predict/orientation', {
            study_hours:    parseFloat(p.study_hours),
            attendance:     parseFloat(p.attendance),
            homework_score: parseFloat(p.homework_score),
        });
        renderOrientationPrediction(resultEl, data.prediction);
        showToast('Classification completed.', 'success');
    } catch (err) {
        renderOrientationPrediction(resultEl, { error: err.message });
        showToast(err.message || 'Classification failed.', 'danger');
    } finally {
        setButtonLoading(btn, false);
        submitting.delete(form);
    }
}

async function handleSettings(form) {
    if (submitting.has(form)) return;
    submitting.add(form);
    const btn = form.querySelector('[type="submit"]');
    setButtonLoading(btn, true, 'Saving…');
    clearFormError(form);

    try {
        const p = formPayload(form);
        const data = await api.post('/api/settings', {
            theme:      p.theme,
            language:   p.language,
            animations: form.querySelector('[name="animations"]')?.checked ?? true,
        });
        const { theme, language, animations } = data.settings;
        document.documentElement.setAttribute('data-bs-theme', theme);
        document.documentElement.setAttribute('data-animations', animations ? 'true' : 'false');
        window.APP_CONFIG.theme      = theme;
        window.APP_CONFIG.language   = language;
        window.APP_CONFIG.animations = animations;
        localStorage.setItem('eduanalytics-theme', theme);
        window.dispatchEvent(new Event('themechange'));
        showToast(data.message || 'Settings saved.', 'success');

        // If language changed, reload current page partial
        if (language !== document.documentElement.lang) {
            document.documentElement.lang = language;
        }
    } catch (err) {
        const msg = err.message || 'Failed to save settings.';
        setFormError(form, msg);
        showToast(msg, 'danger');
    } finally {
        setButtonLoading(btn, false);
        submitting.delete(form);
    }
}

/* ============================================================
   HANDLER MAP
   ============================================================ */
const HANDLERS = {
    'dataset-generate':   handleDatasetGenerate,
    'dataset-import':     handleDatasetImport,
    'predict-exam':       handlePredictExam,
    'predict-orientation': handlePredictOrientation,
    'settings':           handleSettings,
};

/* ============================================================
   BINDING
   ============================================================ */
export function initForms(root = document) {
    // SPA forms
    root.querySelectorAll('[data-spa-form]').forEach((form) => {
        if (form.dataset.bound) return;
        form.dataset.bound = 'true';
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const handler = HANDLERS[form.dataset.spaForm];
            if (handler) handler(form);
            else console.warn('[Forms] No handler for:', form.dataset.spaForm);
        });
    });

    // Download buttons (CSV, PDF, Charts)
    root.querySelectorAll('[data-spa-download]').forEach((btn) => {
        if (btn.dataset.bound) return;
        btn.dataset.bound = 'true';
        btn.addEventListener('click', async () => {
            if (btn.disabled) return;
            const url         = btn.dataset.spaDownload;
            const loadingText = btn.dataset.loadingText || 'Downloading…';
            setButtonLoading(btn, true, loadingText);
            try {
                await api.downloadFile(url);
                showToast('Export completed successfully.', 'success');
            } catch (err) {
                showToast(err.message || 'Export failed.', 'danger');
            } finally {
                setButtonLoading(btn, false);
            }
        });
    });

    // K-Means cluster count selector
    root.querySelectorAll('[data-spa-action="q3-clusters"]').forEach((select) => {
        if (select.dataset.bound) return;
        select.dataset.bound = 'true';
        select.addEventListener('change', () => {
            refreshCurrentPage({ k: select.value });
        });
    });

    // Leader name seed preview
    const leaderInput = root.querySelector('#leaderNameInput');
    if (leaderInput && !leaderInput.dataset.bound) {
        leaderInput.dataset.bound = 'true';
        let debounce;
        leaderInput.addEventListener('input', () => {
            clearTimeout(debounce);
            debounce = setTimeout(async () => {
                const name = leaderInput.value.trim();
                const el   = document.getElementById('seedPreview');
                if (!el) return;
                if (!name) { el.innerHTML = ''; return; }
                try {
                    const data = await api.get(`/api/seed/${encodeURIComponent(name)}`);
                    el.innerHTML = `<i class="bi bi-hash" aria-hidden="true"></i> Seed: <code>${data.seed}</code>`;
                } catch { el.innerHTML = ''; }
            }, 300);
        });
    }

    bindDatasetTable(root);
}
