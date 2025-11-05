function changeQuantity(delta) {
    const quantityInput = document.getElementById('quantity');
    const currentValue = parseInt(quantityInput.value);
    const maxValue = parseInt(quantityInput.max);
    const minValue = parseInt(quantityInput.min);
    
    const newValue = currentValue + delta;
    if (newValue >= minValue && newValue <= maxValue) {
        quantityInput.value = newValue;
    }
}

function addToCart(event) {
    event.preventDefault();
    const quantityInput = document.getElementById('quantity');
    const quantity = quantityInput.value;
    const currentUrl = new URL(window.location.href);
    const currency = currentUrl.searchParams.get('currency') || document.getElementById('currency-selector').value;
    
    currentUrl.searchParams.set('added', 'true');
    currentUrl.searchParams.set('quantity', quantity);
    currentUrl.searchParams.set('currency', currency);
    
    window.location.href = currentUrl.toString();
}

function initializeStarRating() {
    const starsContainer = document.querySelector('.stars');
    if (!starsContainer) return;
    
    const rating = parseFloat(starsContainer.getAttribute('data-rating'));
    const starContainers = starsContainer.querySelectorAll('.star-container');
    
    starContainers.forEach((container, index) => {
        const filledStar = container.querySelector('.star-filled');
        const starPosition = index + 1;
        
        if (rating >= starPosition) {
            // Full star
            filledStar.style.width = '100%';
        } else if (rating > index) {
            // Partial star
            const percentage = ((rating - index) * 100);
            filledStar.style.width = percentage + '%';
        } else {
            // Empty star
            filledStar.style.width = '0%';
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    initializeStarRating();
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