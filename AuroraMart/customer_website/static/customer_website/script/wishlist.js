function addToCartFromWishlist(sku) {
    const currency = document.getElementById('currency-selector').value;
    window.location.href = `/product/${sku}/?added=true&quantity=1&currency=${currency}&from_wishlist=true`;
}