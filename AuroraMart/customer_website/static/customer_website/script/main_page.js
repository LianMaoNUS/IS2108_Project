// Hero Slideshow Functionality
        let currentSlideIndex = 0;
        const slides = document.querySelectorAll('.hero-slide');
        const indicators = document.querySelectorAll('.indicator');
        const totalSlides = slides.length;

        function showSlide(index) {
            slides.forEach(slide => slide.classList.remove('active'));
            indicators.forEach(indicator => indicator.classList.remove('active'));
            
            slides[index].classList.add('active');
            indicators[index].classList.add('active');
            
            currentSlideIndex = index;
        }

        function changeSlide(direction) {
            currentSlideIndex += direction;

            if (currentSlideIndex >= totalSlides) {
                currentSlideIndex = 0;
            } else if (currentSlideIndex < 0) {
                currentSlideIndex = totalSlides - 1;
            }
            
            showSlide(currentSlideIndex);
        }

        function currentSlide(index) {
            showSlide(index - 1); 
        }

        function autoSlide() {
            changeSlide(1);
        }

        document.addEventListener('DOMContentLoaded', function() {
            setInterval(autoSlide, 5000);
            
            document.addEventListener('keydown', function(e) {
                if (e.key === 'ArrowLeft') {
                    changeSlide(-1);
                } else if (e.key === 'ArrowRight') {
                    changeSlide(1);
                }
            });
        });
r

document.addEventListener('DOMContentLoaded', function() {
    const productGrid = document.getElementById('product-grid');
    const scrollLeftBtn = document.getElementById('scroll-left');
    const scrollRightBtn = document.getElementById('scroll-right');
    
    const topProductGrid = document.getElementById('top-product-grid');
    const scrollLeftTopBtn = document.getElementById('scroll-left-top');
    const scrollRightTopBtn = document.getElementById('scroll-right-top');
    
    const scrollAmount = 300; 
    

    function setupScrolling(grid, leftBtn, rightBtn) {
        if (grid && leftBtn && rightBtn) {
            leftBtn.addEventListener('click', function() {
                grid.scrollBy({
                    left: -scrollAmount,
                    behavior: 'smooth'
                });
            });
            
            rightBtn.addEventListener('click', function() {
                grid.scrollBy({
                    left: scrollAmount,
                    behavior: 'smooth'
                });
            });
            
            function updateArrowVisibility() {
                const isAtStart = grid.scrollLeft <= 0;
                const isAtEnd = grid.scrollLeft >= (grid.scrollWidth - grid.clientWidth);
                

                leftBtn.classList.toggle('disabled', isAtStart);
                rightBtn.classList.toggle('disabled', isAtEnd);
            }
            
            grid.addEventListener('scroll', updateArrowVisibility);

            updateArrowVisibility();
        }
    }
    
    setupScrolling(productGrid, scrollLeftBtn, scrollRightBtn);
    setupScrolling(topProductGrid, scrollLeftTopBtn, scrollRightTopBtn);
});