let modifiedItems = new Set();

function increaseQuantity(sku) {
    const input = document.getElementById('qty-' + sku);
    const currentValue = parseInt(input.value);
    if (currentValue < 99) {
        input.value = currentValue + 1;
        markChanged(sku);
    }
}

function decreaseQuantity(sku) {
    const input = document.getElementById('qty-' + sku);
    const currentValue = parseInt(input.value);
    if (currentValue > 1) {
        input.value = currentValue - 1;
        markChanged(sku);
    }
}

function markChanged(sku) {
    const input = document.getElementById('qty-' + sku);
    const originalValue = parseInt(input.dataset.original);
    const currentValue = parseInt(input.value);

    if (currentValue !== originalValue) {
        modifiedItems.add(sku);
        input.classList.add('modified');
    } else {
        modifiedItems.delete(sku);
        input.classList.remove('modified');
    }

    const saveBtn = document.getElementById('save-changes-btn');
    if (modifiedItems.size > 0) {
        saveBtn.style.display = 'inline-block';
    } else {
        saveBtn.style.display = 'none';
    }
}

function saveChanges() {
    if (modifiedItems.size === 0) return;

    const url = new URL('/cart/', window.location.origin);
    url.searchParams.set('bulk_update', 'true');

    modifiedItems.forEach(sku => {
        const input = document.getElementById('qty-' + sku);
        url.searchParams.set('qty_' + sku, input.value);
    });

    window.location.href = url.toString();
}

function clearCart() {
    if (confirm('Are you sure you want to clear your cart?')) {
        window.location.href = '/cart/?clear=true';
    }
}

function removeItem(sku, productName) {
    if (confirm('Are you sure you want to remove "' + productName + '" from your cart?')) {
        window.location.href = '/cart/?remove_sku=' + sku;
    }
}

