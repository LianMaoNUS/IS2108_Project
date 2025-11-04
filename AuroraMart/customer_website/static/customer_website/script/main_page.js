// Hero Slideshow Functionality
        let currentSlideIndex = 0;
        const slides = document.querySelectorAll('.hero-slide');
        const indicators = document.querySelectorAll('.indicator');
        const totalSlides = slides.length;

        // Function to show a specific slide
        function showSlide(index) {
            // Remove active class from all slides and indicators
            slides.forEach(slide => slide.classList.remove('active'));
            indicators.forEach(indicator => indicator.classList.remove('active'));
            
            // Add active class to current slide and indicator
            slides[index].classList.add('active');
            indicators[index].classList.add('active');
            
            currentSlideIndex = index;
        }

        // Function to change slide (next/previous)
        function changeSlide(direction) {
            currentSlideIndex += direction;
            
            // Loop around if we go past the bounds
            if (currentSlideIndex >= totalSlides) {
                currentSlideIndex = 0;
            } else if (currentSlideIndex < 0) {
                currentSlideIndex = totalSlides - 1;
            }
            
            showSlide(currentSlideIndex);
        }

        // Function to go to a specific slide (for indicators)
        function currentSlide(index) {
            showSlide(index - 1); // Convert to 0-based index
        }

        // Auto-advance slideshow
        function autoSlide() {
            changeSlide(1);
        }

        // Initialize slideshow
        document.addEventListener('DOMContentLoaded', function() {
            // Start auto-advance (change slide every 5 seconds)
            setInterval(autoSlide, 5000);
            
            // Add keyboard navigation
            document.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowLeft') {
                    changeSlide(-1);
                } else if (e.key === 'ArrowRight') {
                    changeSlide(1);
                }
            });
        });

        // Currency selector event listener
        document.addEventListener('DOMContentLoaded', function() {
            const currencySelector = document.getElementById('currency-selector');
            
            if (currencySelector) {
                currencySelector.addEventListener('change', function() {
                    const selectedCurrency = this.value;
                    const currentUrl = new URL(window.location);
                    
                    // Update or add the currency parameter
                    currentUrl.searchParams.set('currency', selectedCurrency);
                    
                    // Reload the page with the new URL
                    window.location.href = currentUrl.toString();
                });
                
                // Set the dropdown to match the current URL parameter on page load
                const urlParams = new URLSearchParams(window.location.search);
                const currentCurrency = urlParams.get('currency');
                
                if (currentCurrency) {
                    currencySelector.value = currentCurrency;
                }
            }
        });