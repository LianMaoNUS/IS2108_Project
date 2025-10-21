document.addEventListener('DOMContentLoaded', function() {
    // Find the form on the page
    const loginForm = document.getElementById('login-form');

    // Make sure the form exists before adding an event listener
    if (loginForm) {
        loginForm.addEventListener('submit', function() {
            const loginButton = document.getElementById('login-button');
            const buttonText = loginButton.querySelector('.button-text');
            const spinner = loginButton.querySelector('.spinner');
            
            // Hide the text, show the spinner, and disable the button
            if (buttonText && spinner && loginButton) {
                buttonText.style.display = 'none';
                spinner.style.display = 'block';
                loginButton.disabled = true;
            }
        });
    }
});