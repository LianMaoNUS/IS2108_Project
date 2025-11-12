document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementsByClassName('login-form')[0];
    const submitBtn = document.getElementById('submit-btn');
    
    function checkFormValidity() {
        const fields = [
            'id_age',
            'id_gender', 
            'id_employment_status',
            'id_occupation',
            'id_education',
            'id_household_size',
            'id_has_children',
            'id_monthly_income_sgd'
        ];
        
        const allFilled = fields.every(fieldId => {
            const element = document.getElementById(fieldId);
            return element && element.value.trim() !== '';
        });
        
        submitBtn.disabled = !allFilled;
    }
    
    submitBtn.disabled = true;
    
    const fields = [
        'id_age',
        'id_gender', 
        'id_employment_status',
        'id_occupation',
        'id_education',
        'id_household_size',
        'id_has_children',
        'id_monthly_income_sgd'
    ];
    
    fields.forEach(fieldId => {
        const element = document.getElementById(fieldId);
        if (element) {
            element.addEventListener('input', checkFormValidity);
            element.addEventListener('change', checkFormValidity);
        }
    });
    
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