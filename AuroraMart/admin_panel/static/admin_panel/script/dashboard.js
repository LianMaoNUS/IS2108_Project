    function closeModal() {
        modal.style.display = 'none';
        newUrl = currentUrl.split('&')[0];
        window.history.replaceState({}, '', newUrl);
    }
    
    document.addEventListener('DOMContentLoaded', function () {
        modal = document.getElementById('form-modal');
        closeButton = document.querySelector('.close-button');
        addNewBtn = document.querySelector('.add-new-btn');
        currentUrl = window.location.href;

        if (currentUrl.includes('modal=show')) {
            modal.style.display = 'flex';
        }

        if (closeButton) {
            closeButton.addEventListener('click', () => {
                document.getElementById('modal-form').reset();
                closeModal()
            });
        }

        window.addEventListener('click', (event) => {
            if (event.target == modal) {
                closeModal()
            }
        });

        sortBySelect = document.getElementById('sort-by-select');
        rowsPerPageSelect = document.getElementById('rows-per-page-select');

        function updateUrlAndRefresh() {
            url = new URL(window.location.href);

            sortByValue = sortBySelect.value;
            rowsValue = rowsPerPageSelect.value;

            url.searchParams.set('sort_by', sortByValue);
            url.searchParams.set('rows', rowsValue);

            window.location.href = url.toString();
        }
        
        if (sortBySelect) {
            sortBySelect.addEventListener('change', updateUrlAndRefresh);
        }
        if (rowsPerPageSelect) {
            rowsPerPageSelect.addEventListener('change', updateUrlAndRefresh);
        }

        const chart = document.getElementById('salesTrendChart')?.getContext('2d');
        
        if (chart) {
            const labels = document.getElementById('chart-labels').innerHTML
            const dataValues = document.getElementById('chart-data').innerHTML
            console.log(labels);
            console.log(dataValues);
            
            
            new Chart(chart,{
                    type: 'line', 
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Daily Sales ($)', 
                            data: dataValues,
                            borderColor: 'rgb(75, 192, 192)', // Line color
                            backgroundColor: 'rgba(75, 192, 192, 0.1)', // Optional fill color
                            fill: true, // Enable fill color under the line
                            tension: 0.1 // Makes the line slightly curved
                        }]
                    },
                    options :{
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        responsive: true,
                        maintainAspectRatio: false
                    }
            })
        }

    });

