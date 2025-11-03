document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementsByClassName('login-form')[0];
    loginForm.addEventListener('submit', function() {
        const loginButton = document.getElementById('submit-btn');
        const buttonText = loginButton.querySelector('.button-text');
        const arrow = loginButton.querySelector('.arrow');
        const spinner = loginButton.querySelector('.spinner');

        if (buttonText && spinner && loginButton) {
            buttonText.style.display = 'none';
                arrow.style.display = 'none';
                spinner.style.display = 'block';
                loginButton.disabled = true;
            }
        });
    });