document.addEventListener('DOMContentLoaded', function() {
    loginForm = document.querySelector('.login-form');

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

    if (passwordField) {
        passwordField.addEventListener('input', function() {
            const password = this.value;
            const requirements = {
                length: password.length >= 8,
                uppercase: /[A-Z]/.test(password),
                lowercase: /[a-z]/.test(password),
                digit: /[0-9]/.test(password),
                special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
            };

            Object.keys(requirements).forEach(req => {
                const li = document.getElementById('req-' + req);
                const icon = li.querySelector('i');
                if (requirements[req]) {
                    li.classList.remove('invalid');
                    li.classList.add('valid');
                    icon.className = 'fa-solid fa-check';
                } else {
                    li.classList.remove('valid');
                    li.classList.add('invalid');
                    icon.className = 'fa-solid fa-times';
                }
            });
        });
    }
    
});