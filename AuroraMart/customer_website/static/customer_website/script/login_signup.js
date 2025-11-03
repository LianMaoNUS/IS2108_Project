document.addEventListener('DOMContentLoaded', function() {
    loginForm = document.getElementById('login-form');

    if (loginForm) {
        loginForm.addEventListener('submit', function() {
            loginButton = document.getElementById('login-button');
            buttonText = loginButton.querySelector('.button-text');
            spinner = loginButton.querySelector('.spinner');
            
            if (buttonText && spinner && loginButton) {
                buttonText.style.display = 'none';
                spinner.style.display = 'block';
                loginButton.disabled = true;
            }
        });
    }

    togglePassword = document.querySelector('#togglePassword');
    passwordField = document.querySelector('#id_password');

    togglePassword.addEventListener('click', function () {
        const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordField.setAttribute('type', type);
        this.classList.toggle('fa-eye-slash');
    });

    togglePassword2 = document.querySelector('#togglePassword2');
    passwordField2 = document.querySelector('#id_password_check'); 

    togglePassword2.addEventListener('click', function () {
        type = passwordField2.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordField2.setAttribute('type', type);
        this.classList.toggle('fa-eye-slash');
    });


});