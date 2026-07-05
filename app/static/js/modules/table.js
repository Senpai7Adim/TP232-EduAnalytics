/**
 * Interactive data tables — search, pagination, sorting, per-page.
 */

import { api } from './api.js';
import { setTableLoading } from './loading.js';

let tableDebounce = null;
const DEFAULT_PER_PAGE = 15;

export async function loadDatasetTable(container, {
    page    = 1,
    search  = '',
    sort    = 'Student_ID',
    order   = 'asc',
    perPage = DEFAULT_PER_PAGE,
} = {}) {
    const tableContainer = container.querySelector('#datasetTableContainer') || container;
    setTableLoading(tableContainer, true);

    try {
        const url = `/api/dataset/preview?page=${page}&per_page=${perPage}&search=${encodeURIComponent(search)}&sort=${sort}&order=${order}`;
        const data = await api.get(url);
        if (data === undefined || data === null) return;

        const columns = ['Student_ID', 'Study_Hours', 'Exam_Score', 'Attendance', 'Homework_Score', 'Orientation'];
        const colLabels = {
            Student_ID: 'ID', Study_Hours: 'Study Hours', Exam_Score: 'Exam Score',
            Attendance: 'Attendance', Homework_Score: 'Homework', Orientation: 'Orientation',
        };

        const highlightSearch = (text, query) => {
            if (!query) return String(text);
            const escaped = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            return String(text).replace(new RegExp(`(${escaped})`, 'gi'), '<mark>$1</mark>');
        };

        const rows = (data.rows || []);
        const tbody = rows.length
            ? rows.map((row) => `
                <tr>
                    <td><code>${highlightSearch(row.Student_ID, search)}</code></td>
                    <td>${row.Study_Hours}</td>
                    <td><strong>${row.Exam_Score}</strong></td>
                    <td>${row.Attendance}%</td>
                    <td>${row.Homework_Score}</td>
                    <td><span class="badge-orientation ${row.Orientation.toLowerCase()}">${row.Orientation}</span></td>
                </tr>`).join('')
            : '<tr><td colspan="6" class="text-center text-muted py-5">No matching records found.</td></tr>';

        const sortArrow = (col) => {
            if (data.sort !== col) return '';
            return data.order === 'asc' ? ' ↑' : ' ↓';
        };

        tableContainer.innerHTML = `
            <div class="table-wrapper">
                <table class="data-table data-table-sticky" id="datasetPreviewTable"
                       data-page="${data.page}"
                       data-pages="${data.pages}"
                       data-total="${data.total}"
                       data-sort="${data.sort}"
                       data-order="${data.order}"
                       data-per-page="${perPage}">
                    <thead>
                        <tr>
                            ${columns.map((col) => `
                            <th data-sort="${col}"
                                class="${data.sort === col ? `sorted-${data.order}` : ''}"
                                scope="col"
                                tabindex="0"
                                role="columnheader"
                                aria-sort="${data.sort === col ? (data.order === 'asc' ? 'ascending' : 'descending') : 'none'}">
                                ${colLabels[col]}${sortArrow(col)}
                            </th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>${tbody}</tbody>
                </table>
            </div>
            ${data.total > 0 ? `
            <div class="table-pagination">
                <div class="d-flex align-items-center gap-2">
                    <span class="page-info" aria-live="polite">
                        Page ${data.page} of ${data.pages} &middot; ${data.total} records
                    </span>
                </div>
                <div class="d-flex align-items-center gap-2">
                    <label class="small text-muted mb-0" for="perPageSelect">Rows:</label>
                    <select id="perPageSelect" class="per-page-select form-select form-select-sm" aria-label="Rows per page">
                        ${[10, 15, 25, 50].map((n) =>
                            `<option value="${n}" ${n === perPage ? 'selected' : ''}>${n}</option>`
                        ).join('')}
                    </select>
                </div>
                <div class="pagination-btns">
                    <button type="button" class="btn btn-sm btn-outline-primary" data-page-prev
                            ${data.page <= 1 ? 'disabled' : ''}
                            aria-label="Previous page">
                        <i class="bi bi-chevron-left" aria-hidden="true"></i>
                    </button>
                    <button type="button" class="btn btn-sm btn-outline-primary" data-page-next
                            ${data.page >= data.pages ? 'disabled' : ''}
                            aria-label="Next page">
                        <i class="bi bi-chevron-right" aria-hidden="true"></i>
                    </button>
                </div>
            </div>` : ''}`;

    } catch (err) {
        tableContainer.innerHTML = `
            <div class="empty-state py-4">
                <i class="bi bi-exclamation-triangle"></i>
                <p>Failed to load table: ${err.message || 'Unknown error'}</p>
                <button class="btn btn-sm btn-outline-primary mt-2" id="tableRetryBtn">
                    <i class="bi bi-arrow-clockwise me-1"></i>Retry
                </button>
            </div>`;
        tableContainer.querySelector('#tableRetryBtn')?.addEventListener('click', () => {
            loadDatasetTable(container, { page, search, sort, order, perPage });
        });
    } finally {
        setTableLoading(tableContainer, false);
        bindDatasetTable(container);
    }
}

function getTableState(table) {
    return {
        page:    parseInt(table?.dataset.page    || '1',  10),
        pages:   parseInt(table?.dataset.pages   || '1',  10),
        sort:           table?.dataset.sort      || 'Student_ID',
        order:          table?.dataset.order     || 'asc',
        perPage: parseInt(table?.dataset.perPage || '15', 10),
        search:  document.getElementById('datasetTableSearch')?.value?.trim() || '',
    };
}

export function bindDatasetTable(root = document) {
    const container = root.querySelector?.('#datasetPreviewCard') ?? root;
    const table     = container.querySelector('#datasetPreviewTable');
    if (!table) return;

    // Pagination — previous
    container.querySelector('[data-page-prev]')?.addEventListener('click', () => {
        const s = getTableState(table);
        if (s.page > 1) loadDatasetTable(container, { ...s, page: s.page - 1 });
    });

    // Pagination — next
    container.querySelector('[data-page-next]')?.addEventListener('click', () => {
        const s = getTableState(table);
        if (s.page < s.pages) loadDatasetTable(container, { ...s, page: s.page + 1 });
    });

    // Per-page select
    const perPageSelect = container.querySelector('#perPageSelect');
    if (perPageSelect && !perPageSelect.dataset.bound) {
        perPageSelect.dataset.bound = 'true';
        perPageSelect.addEventListener('change', () => {
            const s = getTableState(table);
            loadDatasetTable(container, { ...s, perPage: parseInt(perPageSelect.value, 10), page: 1 });
        });
    }

    // Column sorting + keyboard support
    table.querySelectorAll('th[data-sort]').forEach((th) => {
        if (th.dataset.bound) return;
        th.dataset.bound = 'true';
        const doSort = () => {
            const s   = getTableState(table);
            const col = th.dataset.sort;
            const ord = s.sort === col && s.order === 'asc' ? 'desc' : 'asc';
            loadDatasetTable(container, { ...s, sort: col, order: ord, page: 1 });
        };
        th.addEventListener('click', doSort);
        th.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); doSort(); } });
    });

    // Search with debounce
    const searchInput = container.querySelector('#datasetTableSearch');
    if (searchInput && !searchInput.dataset.bound) {
        searchInput.dataset.bound = 'true';
        searchInput.addEventListener('input', () => {
            clearTimeout(tableDebounce);
            tableDebounce = setTimeout(() => {
                const s = getTableState(table);
                loadDatasetTable(container, { ...s, search: searchInput.value.trim(), page: 1 });
            }, 350);
        });
    }
}
