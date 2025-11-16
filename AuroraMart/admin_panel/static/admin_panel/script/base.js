// Function to dismiss alerts
function dismissAlert(button) {
    const alert = button.closest('.alert');
    if (alert) {
        alert.style.transition = 'opacity 0.3s ease';
        alert.style.opacity = '0';
        setTimeout(() => alert.remove(), 300);
    }
}

function toggleGroup(groupId) {
    const group = document.getElementById(groupId);
    const icon = document.getElementById(groupId + '-icon');

    if (group.style.display === 'block') {
        group.style.display = 'none';
        icon.classList.remove('fa-chevron-up');
        icon.classList.add('fa-chevron-down');
    } else {
        group.style.display = 'block';
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-up');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    const groups = ['order-group', 'coupon-group'];
    groups.forEach(groupId => {
        const group = document.getElementById(groupId);
        if (group) {
            group.style.display = 'none';
        }
    });
});
