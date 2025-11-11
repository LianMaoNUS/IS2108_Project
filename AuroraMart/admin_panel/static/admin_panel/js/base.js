// Base JavaScript for admin panel

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('formModal');
    if (modal && event.target === modal) {
        modal.style.display = 'none';
    }

}

// Handle form submission errors
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease';
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });
});
