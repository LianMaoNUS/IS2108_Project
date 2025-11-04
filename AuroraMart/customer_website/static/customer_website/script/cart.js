document.addEventListener('DOMContentLoaded', function() {
    const currencySelector = document.getElementById('currency-selector');
    if (currencySelector) {
        currencySelector.addEventListener('change', function() {
            const selectedCurrency = this.value;
            const currentUrl = new URL(window.location.href);
            currentUrl.searchParams.set('currency', selectedCurrency);
            window.location.href = currentUrl.toString();
        });
    }
});