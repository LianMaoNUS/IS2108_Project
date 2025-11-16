
function sortOrders(sortValue) {
    const currentUrl = new URL(window.location);
    currentUrl.searchParams.set('sort', sortValue);
    window.location.href = currentUrl.toString();
}

function closeMessage() {
    const messageDiv = document.getElementById('profile-message');
    if (messageDiv) {
        messageDiv.style.display = 'none';
    }
}

