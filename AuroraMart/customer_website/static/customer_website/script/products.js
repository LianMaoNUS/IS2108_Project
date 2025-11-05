// Products page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initializeSearch();
    
    // Initialize sorting
    initializeSorting();
    
    // Initialize currency selector
    initializeCurrencySelector();
});

// Search functionality with URL parameters
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch();
        }, 500); // Increased delay for server requests
    });
    
    // Handle enter key
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

// Sorting functionality with URL parameters
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

function initializeCurrencySelector() {
    const currencySelector = document.getElementById('currency-selector');
    if (!currencySelector) return;
    
    currencySelector.addEventListener('change', function() {
        const selectedCurrency = this.value;
        const currentUrl = new URL(window.location.href);
        currentUrl.searchParams.set('currency', selectedCurrency);
        window.location.href = currentUrl.toString();
    });
}


// Category filtering (if needed for future features)
function filterByCategory(category) {
    const currentUrl = new URL(window.location.href);
    if (category && category !== 'all') {
        currentUrl.searchParams.set('category', category);
    } else {
        currentUrl.searchParams.delete('category');
    }
    
    // Reset to first page when filtering
    currentUrl.searchParams.delete('page');
    
    window.location.href = currentUrl.toString();
}

// Export functions for global access
window.clearSearch = clearSearch;
window.filterByCategory = filterByCategory;
