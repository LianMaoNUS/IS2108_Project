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
            filledStar.style.width = '100%';
        } else if (rating > index) {
            const percentage = ((rating - index) * 100);
            filledStar.style.width = percentage + '%';
        } else {
            filledStar.style.width = '0%';
        }
    });
}


function toggleWishlist(event) {
    event.preventDefault();
    
    const pathParts = window.location.pathname.split('/');
    const sku = pathParts[pathParts.length - 2];
    const wishlistBtn = document.getElementById('wishlist-btn');
    const isInWishlist = wishlistBtn.classList.contains('in-wishlist');
    
    const url = new URL(window.location.href);
    url.searchParams.set('sku', sku);
    
    if (isInWishlist) {
        url.searchParams.set('remove_from_wishlist', 'true');
    } else {
        url.searchParams.set('add_to_wishlist', 'true');
    }
    
    window.location.href = url.toString();
}

document.addEventListener('DOMContentLoaded', function() {
    initializeStarRating();
});