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

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function checkWishlistStatus() {
    const pathParts = window.location.pathname.split('/');
    const sku = pathParts[pathParts.length - 2];
    
    fetch(`/wishlist/check/?sku=${encodeURIComponent(sku)}`)
        .then(response => response.json())
        .then(data => {
            const wishlistBtn = document.getElementById('wishlist-btn');
            if (wishlistBtn) {
                if (data.in_wishlist) {
                    wishlistBtn.classList.add('in-wishlist');
                } else {
                    wishlistBtn.classList.remove('in-wishlist');
                }
            }
        })
        .catch(error => console.error('Error checking wishlist status:', error));
}

function toggleWishlist(event) {
    event.preventDefault();
    
    const pathParts = window.location.pathname.split('/');
    const sku = pathParts[pathParts.length - 2];
    const wishlistBtn = document.getElementById('wishlist-btn');
    const isInWishlist = wishlistBtn.classList.contains('in-wishlist');
    
    const url = isInWishlist ? '/wishlist/remove/' : '/wishlist/add/';
    const csrftoken = getCookie('csrftoken');
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrftoken
        },
        body: `sku=${encodeURIComponent(sku)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (data.in_wishlist) {
                wishlistBtn.classList.add('in-wishlist');
                showNotification('Added to wishlist!', 'success');
            } else {
                wishlistBtn.classList.remove('in-wishlist');
                showNotification('Removed from wishlist', 'info');
            }
        } else {
            showNotification(data.error || 'An error occurred', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('An error occurred', 'error');
    });
}

function showNotification(message, type) {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `wishlist-notification ${type}`;
    notification.textContent = message;
    
    // Add to body
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, 3000);
}

document.addEventListener('DOMContentLoaded', function() {
    initializeStarRating();
    checkWishlistStatus();
    
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