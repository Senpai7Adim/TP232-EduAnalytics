/**
 * Session UI — sidebar pill, avatar, notification dropdown.
 */

import { api } from './api.js';

export async function updateSessionUI(meta) {
    if (!meta) {
        try {
            const data = await api.get('/api/session');
            _applySessionUI(data.has_dataset, data.meta);
        } catch { /* non-critical */ }
        return;
    }
    _applySessionUI(true, meta);
}

function _applySessionUI(hasDataset, meta) {
    _updateDatasetPill(hasDataset, meta?.num_students);
    _updateAvatar(meta?.leader_name);
    _updateNotifDropdown(hasDataset, meta);
}

function _updateDatasetPill(hasDataset, count) {
    const footer = document.getElementById('sidebarFooter');
    if (!footer) return;
    if (hasDataset && count) {
        footer.innerHTML = `
            <div class="dataset-pill">
                <i class="bi bi-check-circle-fill" aria-hidden="true"></i>
                <span>${count} students</span>
            </div>`;
    } else {
        footer.innerHTML = '';
    }
}

function _updateAvatar(leaderName) {
    const initial = document.getElementById('userAvatarInitial');
    const avatar  = document.getElementById('userAvatar');
    if (!initial) return;
    const name = leaderName || 'Analyst';
    const char = name.charAt(0).toUpperCase();
    initial.textContent = char;
    if (avatar) avatar.title = name;
}

function _updateNotifDropdown(hasDataset, meta) {
    const dot      = document.getElementById('notifDot');
    const textEl   = document.getElementById('notifDatasetText');
    if (!textEl) return;
    if (hasDataset && meta) {
        if (dot) dot.style.display = '';
        textEl.innerHTML = `
            <i class="bi bi-check-circle-fill text-success me-1" aria-hidden="true"></i>
            Dataset loaded: ${meta.num_students} students`;
    } else {
        if (dot) dot.style.display = 'none';
        textEl.textContent = 'Generate a dataset to begin analysis';
    }
}

export async function refreshSession() {
    try {
        const data = await api.get('/api/session');
        _applySessionUI(data.has_dataset, data.meta);
    } catch { /* ignore */ }
}
