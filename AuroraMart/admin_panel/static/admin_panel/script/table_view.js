// Show modal if action is in URL
document.addEventListener('DOMContentLoaded', function () {
    const modalShow = document.querySelector('.modal-show')?.textContent.trim();
    console.log(modalShow == 'True');
    if (modalShow == 'True') {
        showModal();
    }
});

document.addEventListener('click', function (event) {
    const modal = document.getElementById('formModal');
    if (modal && modal.style.display === 'block' && event.target === modal) {
        closeModal();
    }
});


function updateRows(value) {
    const type = window.tableViewType || document.querySelector('.type-show')?.textContent.trim() || '';
    const searchQuery = document.querySelector('.search-form input[name="search"]')?.value || '';
    const sortBy = window.tableViewSortBy || document.getElementById('sortBySelect')?.value || '';
    window.location.href = `?type=${type}&rows=${value}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}${sortBy ? `&sort_by=${encodeURIComponent(sortBy)}` : ''}`;
}

function updateSort(value) {
    const type = window.tableViewType || document.querySelector('.type-show')?.textContent.trim() || '';
    const rowsSelect = document.querySelector('.table-controls .control-left select');
    const rows = rowsSelect ? rowsSelect.value : '10';
    const searchInput = document.querySelector('.search-form input[name="search"]');
    const searchQuery = searchInput ? searchInput.value : '';
    const pageParam = '1';
    let url = `?type=${encodeURIComponent(type)}&page=${pageParam}&rows=${encodeURIComponent(rows)}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}&sort_by=${encodeURIComponent(value)}`;
    window.location.href = url;
}

function toggleSelectAll(checkbox) {
    const checkboxes = document.querySelectorAll('.row-checkbox');
    checkboxes.forEach(cb => cb.checked = checkbox.checked);
}

function addRecord() {
    const type = window.tableViewType || document.querySelector('.type-show')?.textContent.trim() || '';
    const url = `?type=${type}&action=Add`;
    window.location.href = url;
}

function editRecord(id) {
    const type = window.tableViewType || document.querySelector('.type-show')?.textContent.trim() || '';
    const url = `?type=${type}&action=Update&id=${id}`;
    window.location.href = url;
}

function deleteRecord(id) {
    if (confirm('Are you sure you want to delete this record?')) {
        var type = window.tableViewType || document.querySelector('.type-show')?.textContent.trim() || '';
        window.location.href = `?type=${type}&action=Delete&id=${id}`;
    }
}

function showModal() {
    const modal = document.getElementById('formModal');
    if (modal) modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('formModal');
    if (modal) modal.style.display = 'none';
    const url = new URL(window.location.href);
    url.searchParams.delete('action');
    url.searchParams.delete('id');
    url.searchParams.delete('category');
    window.history.replaceState({}, document.title, url.pathname + url.search);
}

function deleteSelected() {
    const selected = Array.from(document.querySelectorAll('.row-checkbox:checked')).map(cb => cb.value);
    if (selected.length === 0) {
        alert('Please select at least one record to delete');
        return;
    }
    if (confirm(`Are you sure you want to delete ${selected.length} record(s)?`)) {
        const type = window.tableViewType || '';
        window.location.href = `?type=${type}&action=Delete&id=${selected.join(',')}`;
    }
}

document.addEventListener('DOMContentLoaded', function () {
    function updateActionButtons() {
        const anyChecked = document.querySelectorAll('.row-checkbox:checked').length > 0;
        document.getElementById('exportCsvBtn').style.display = anyChecked ? 'inline-flex' : 'none';
        const deleteBtn = document.getElementById('deleteSelectedBtn');
        if (deleteBtn) deleteBtn.style.display = anyChecked ? 'inline-flex' : 'none';
    }
    document.querySelectorAll('.row-checkbox, #selectAll').forEach(function (el) {
        el.addEventListener('change', updateActionButtons);
    });
    updateActionButtons();
});

// Debounce helper
function debounce(fn, delay) {
    let timer;
    return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
    };
}

// Live search: update URL after 500ms idle, preserve type/rows/sort, reset to page 1
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    if (!searchInput) return;

    const doSearch = debounce(function() {
        try {
            const url = new URL(window.location.href);
            const q = (this.value || '').trim();
            if (q) {
                url.searchParams.set('search', q);
            } else {
                url.searchParams.delete('search');
            }
            url.searchParams.set('page', '1'); // reset to first page
            // navigate to updated URL
            window.location.href = url.toString();
        } catch (e) {
            console.error('Search navigation failed', e);
        }
    }, 500);

    searchInput.addEventListener('input', doSearch);
});

function categoryChanged(value) {
    const categoryId = value;
    const realSelect = document.getElementById('id_subcategory');
    if (!realSelect) return;
    realSelect.innerHTML = '<option value="">Select a subcategory (optional)</option>';

    // Update URL query param 'category' (preserve other params)
    (function updateUrlCategoryParam(catId) {
        try {
            const url = new URL(window.location.href);
            if (catId) {
                url.searchParams.set('category', catId);
            } else {
                url.searchParams.delete('category');
            }
            // update URL and reload so server-side form reads the category and re-populates subcategories
            window.history.replaceState({}, document.title, url.pathname + url.search);
            window.location.reload();
        } catch (e) {
            console.debug('Unable to update URL category param', e);
        }
    })(categoryId);
}

function updateSort(value) {
    const url = new URL(window.location.href);
    url.searchParams.set('sort_by', value);
    window.location.href = url.toString();
}