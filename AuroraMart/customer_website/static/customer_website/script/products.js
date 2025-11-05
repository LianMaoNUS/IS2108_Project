// Products page functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize search functionality
    initializeSearch();
    
    // Initialize sorting
    initializeSorting();
    
    // Initialize currency selector
    initializeCurrencySelector();
    
    // Initialize category filtering
    initializeCategoryFiltering();
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


// Category filtering functionality
function initializeCategoryFiltering() {
    const categoryPills = document.querySelectorAll('.category-pill');
    
    categoryPills.forEach(pill => {
        pill.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Get category from data attribute
            const category = this.getAttribute('data-category');
            console.log('Clicked category:', category); // Debug log
            
            // Remove active class from all pills
            categoryPills.forEach(p => p.classList.remove('active'));
            
            // Add active class to clicked pill
            this.classList.add('active');
            
            // Filter by category
            filterByCategory(category);
        });
    });
    
    // Set active pill based on current URL
    const currentUrl = new URL(window.location.href);
    const currentCategory = currentUrl.searchParams.get('category') || 'all';
    console.log('Current category from URL:', currentCategory); // Debug log
    
    categoryPills.forEach(pill => {
        const pillCategory = pill.getAttribute('data-category');
        console.log('Checking pill category:', pillCategory, 'against current:', currentCategory); // Debug log
        if (pillCategory === currentCategory) {
            pill.classList.add('active');
            console.log('Added active class to pill:', pillCategory); // Debug log
        }
    });
}

function filterByCategory(category) {
    console.log('filterByCategory called with:', category); // Debug log
    const currentUrl = new URL(window.location.href);
    
    if (category && category !== 'all') {
        currentUrl.searchParams.set('category', category);
        console.log('Setting category to:', category); // Debug log
    } else {
        currentUrl.searchParams.delete('category');
        console.log('Removing category parameter'); // Debug log
    }
    
    // Reset to first page when filtering
    currentUrl.searchParams.delete('page');
    
    console.log('New URL will be:', currentUrl.toString()); // Debug log
    window.location.href = currentUrl.toString();
}

// Export functions for global access
window.clearSearch = clearSearch;
window.filterByCategory = filterByCategory;
