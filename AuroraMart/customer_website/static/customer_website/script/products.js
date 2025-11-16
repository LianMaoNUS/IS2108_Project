document.addEventListener('DOMContentLoaded', function() {
    initializeSearch();
    initializeSorting();
    initializeCategoryFiltering();
});

function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch();
        }, 500); 
    });
    
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            clearTimeout(searchTimeout);
            performSearch();
        }
    });
}

function performSearch() {
    const searchTerm = document.getElementById('search-input').value.trim();
    const currentUrl = new URL(window.location.href);
    
    if (searchTerm) {
        currentUrl.searchParams.set('search', searchTerm);
    } else {
        currentUrl.searchParams.delete('search');
    }
    
    // Reset to first page when searching
    currentUrl.searchParams.delete('page');
    
    window.location.href = currentUrl.toString();
}

function clearSearch() {
    const searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.value = '';
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.delete('search');
        currentUrl.searchParams.delete('page');
        window.location.href = currentUrl.toString();
    }
}

function initializeSorting() {
    const sortSelect = document.getElementById('sort-select');
    if (!sortSelect) return;
    
    sortSelect.addEventListener('change', function() {
        performSort(this.value);
    });
}

function performSort(sortType) {
    const currentUrl = new URL(window.location.href);
    currentUrl.searchParams.set('sort', sortType);
    currentUrl.searchParams.delete('page');
    
    window.location.href = currentUrl.toString();
}


function initializeCategoryFiltering() {
    const categoryPills = document.querySelectorAll('.category-pill');
    
    categoryPills.forEach(pill => {
        pill.addEventListener('click', function(e) {
            e.preventDefault();
            const category = this.getAttribute('data-category');
            categoryPills.forEach(p => p.classList.remove('active')); 
            this.classList.add('active');
            filterByCategory(category);
        });
    });
    
    const currentUrl = new URL(window.location.href);
    const currentCategory = currentUrl.searchParams.get('category') || 'all';
    
    categoryPills.forEach(pill => {
        const pillCategory = pill.getAttribute('data-category');
        if (pillCategory === currentCategory) {
            pill.classList.add('active');
        }
    });
}

function filterByCategory(category) {
    const currentUrl = new URL(window.location.href);
    
    if (category && category !== 'all') {
        currentUrl.searchParams.set('category', category);
    } else {
        currentUrl.searchParams.delete('category');
    }
    
    currentUrl.searchParams.delete('page');
    
    console.log('New URL will be:', currentUrl.toString()); 
    window.location.href = currentUrl.toString();
}

window.clearSearch = clearSearch;
window.filterByCategory = filterByCategory;
