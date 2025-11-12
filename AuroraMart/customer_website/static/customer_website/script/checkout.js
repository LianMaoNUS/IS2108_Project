// Simplified Checkout JavaScript - UI Enhancement Only
// All validation is handled server-side in Django

document.addEventListener('DOMContentLoaded', function() {
    initializeCardFormatting();
    initializeFormSubmission();
});


function initializeCardFormatting() {
    const cardNumberInput = document.querySelector('input[name="card_number"]');
    const expiryDateInput = document.querySelector('input[name="expiry_date"]');
    const cvvInput = document.querySelector('input[name="cvv"]');
    const cardTypeIcon = document.getElementById('card-type-icon');
    
    if (cardNumberInput) {
        cardNumberInput.addEventListener('input', function() {
            formatCardNumber(this);
            if (cardTypeIcon) {
                detectCardType(this.value, cardTypeIcon);
            }
        });
    }
    
    if (expiryDateInput) {
        expiryDateInput.addEventListener('input', function() {
            formatExpiryDate(this);
        });
    }
    
    if (cvvInput) {
        cvvInput.addEventListener('input', function() {
            formatCVV(this);
        });
    }
}

// Card Number Formatting (Visual Enhancement)
function formatCardNumber(input) {
    let value = input.value.replace(/\s/g, '').replace(/[^0-9]/gi, '');
    let formattedValue = value.match(/.{1,4}/g)?.join(' ') || value;
    
    if (formattedValue !== input.value) {
        input.value = formattedValue;
    }
}

// Card Type Detection (Visual Enhancement)
function detectCardType(cardNumber, iconElement) {
    const number = cardNumber.replace(/\s/g, '');
    
    // Visa
    if (/^4/.test(number)) {
        iconElement.className = 'fa-brands fa-cc-visa';
        iconElement.style.color = '#1A1F71';
    }
    // Mastercard
    else if (/^5[1-5]/.test(number) || /^2[2-7]/.test(number)) {
        iconElement.className = 'fa-brands fa-cc-mastercard';
        iconElement.style.color = '#EB001B';
    }
    // American Express
    else if (/^3[47]/.test(number)) {
        iconElement.className = 'fa-brands fa-cc-amex';
        iconElement.style.color = '#006FCF';
    }
    // Discover
    else if (/^6/.test(number)) {
        iconElement.className = 'fa-brands fa-cc-discover';
        iconElement.style.color = '#FF6000';
    }
    else {
        iconElement.className = 'fa-solid fa-credit-card';
        iconElement.style.color = '#6b7280';
    }
}

// Expiry Date Formatting (Visual Enhancement)
function formatExpiryDate(input) {
    let value = input.value.replace(/\D/g, '');
    
    if (value.length >= 2) {
        value = value.substring(0, 2) + '/' + value.substring(2, 4);
    }
    
    input.value = value;
}

// CVV Formatting (Visual Enhancement)
function formatCVV(input) {
    input.value = input.value.replace(/\D/g, '').substring(0, 4);
}

// Form Submission UI
function initializeFormSubmission() {
    const form = document.getElementById('checkout-form');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        const submitButton = form.querySelector('.btn-place-order');
        
        if (submitButton) {
            // Show loading state
            submitButton.classList.add('loading');
            submitButton.disabled = true;
            submitButton.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing Order...';
        }
        
    });
}

// Utility Functions
function formatCurrency(amount, currencySymbol = '$') {
    return currencySymbol + parseFloat(amount).toFixed(2);
}

// Coupon Selection
function selectCoupon(couponCode) {
    const couponInput = document.getElementById('coupon_code');
    if (couponInput) {
        couponInput.value = couponCode;
    }
    
    // Add coupon code to URL and refresh page to update order summary
    const url = new URL(window.location);
    url.searchParams.set('coupon_code', couponCode);
    window.location.href = url.toString();
}

