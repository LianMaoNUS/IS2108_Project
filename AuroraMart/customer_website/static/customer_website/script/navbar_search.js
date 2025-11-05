document.addEventListener('DOMContentLoaded', function() {
    initializeNavbarSearch();
    initializeCurrencySelector();
});

function initializeNavbarSearch() {
    const navSearchInput = document.getElementById('nav-search-input');
    if (!navSearchInput) return;
    
    let searchTimeout;
    
    createSearchDropdown();
    
    navSearchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length >= 2) {
            searchTimeout = setTimeout(() => {
                performNavbarSearch(query);
            }, 400);
        } else {
            hideSearchDropdown();
        }
    });
    
    document.addEventListener('click', function(e) {
        const searchContainer = document.querySelector('.nav-search');
        if (!searchContainer.contains(e.target)) {
            hideSearchDropdown();
        }
    });
    
    navSearchInput.addEventListener('focus', function() {
        const query = this.value.trim();
        if (query.length >= 2) {
            showSearchDropdown();
        }
    });
}

function createSearchDropdown() {
    const navSearch = document.querySelector('.nav-search');
    if (!navSearch || document.querySelector('.search-dropdown')) return;
    
    const dropdown = document.createElement('div');
    dropdown.className = 'search-dropdown';
    dropdown.innerHTML = `
        <div class="search-dropdown-content">
            <div class="search-results-list"></div>
        </div>
    `;
    
    navSearch.appendChild(dropdown);
}

function performNavbarSearch(query) {
    showSearchDropdown();
    const resultsContainer = document.querySelector('.search-results-list');
    
    resultsContainer.innerHTML = `
        <div class="search-loading">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <span>Searching...</span>
        </div>
    `;
    
    fetch(`/search/ajax/?q=${encodeURIComponent(query)}`)
        .then(response => response.json())
        .then(data => {
            displaySearchResults(data);
        })
        .catch(error => {
            console.error('Search error:', error);
            resultsContainer.innerHTML = `
                <div class="search-error">
                    <i class="fa-solid fa-exclamation-triangle"></i>
                    <span>Search temporarily unavailable</span>
                </div>
            `;
        });
}

function displaySearchResults(data) {
    const resultsContainer = document.querySelector('.search-results-list');
    
    if (data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="search-no-results">
                <i class="fa-solid fa-search"></i>
                <span>No products found for "${data.query}"</span>
            </div>
        `;
    } else {
        const resultsHtml = data.results.map(product => `
            <div class="search-result-item" onclick="window.location.href='${product.product_url}'">
                <div class="result-image">
                    ${product.image_url ? 
                        `<img src="${product.image_url}" alt="${product.name}" />` :
                        `<div class="image-placeholder"><i class="fa-solid fa-image"></i></div>`
                    }
                </div>
                <div class="result-details">
                    <h4 class="result-name">${product.name}</h4>
                    <p class="result-description">${product.description}</p>
                    <div class="result-meta">
                        ${product.category ? `<span class="result-category">${product.category}</span>` : ''}
                        <span class="result-price">${product.currency_symbol}${product.price}</span>
                    </div>
                </div>
                <div class="result-action">
                    <i class="fa-solid fa-arrow-right"></i>
                </div>
            </div>
        `).join('');
        
        resultsContainer.innerHTML = resultsHtml;
    }
}

function showSearchDropdown() {
    const dropdown = document.querySelector('.search-dropdown');
    if (dropdown) {
        dropdown.style.display = 'block';
    }
}

function hideSearchDropdown() {
    const dropdown = document.querySelector('.search-dropdown');
    if (dropdown) {
        dropdown.style.display = 'none';
    }
}

function clearSearch() {
    const navSearchInput = document.getElementById('nav-search-input');
    if (navSearchInput) {
        navSearchInput.value = '';
        hideSearchDropdown();
    }
}

// Currency selector functionality
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

// Export functions for global access
window.clearSearch = clearSearch;
window.performNavbarSearch = performNavbarSearch;