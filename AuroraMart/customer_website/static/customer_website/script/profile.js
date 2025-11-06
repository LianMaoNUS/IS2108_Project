// Profile page functionality
document.addEventListener('DOMContentLoaded', function() {
    initializeCurrencySelector();
});

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

function sortOrders(sortValue) {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('sort', sortValue);
    window.location.href = currentUrl.toString();
}

