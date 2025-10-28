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
            const labelsEl = document.getElementById('chart-labels')
            const dataEl = document.getElementById('chart-data')
            
            const labelsJsonString = labelsEl.textContent || '[]';
            const dataValuesJsonString = dataEl.textContent || '[]';

            const labels = JSON.parse(labelsJsonString);
            const dataValues = JSON.parse(dataValuesJsonString);

             new Chart(chart,{
                    type: 'line', 
                    data: {
                        labels: labels,
                        datasets: [{
                            label: 'Daily Sales ($)', 
                            data: dataValues,
                            borderColor: 'rgb(75, 192, 192)',
                            backgroundColor: 'rgba(75, 192, 192, 0.1)', 
                            fill: true, 
                            tension: 0.1 
                        }]
                    },
                    options :{
                        responsive: true,             // MUST be true
                        maintainAspectRatio: false,   // MUST be false
                        scales: { y: { beginAtZero: true } },
                    },
                    plugins :{
                        title:{
                            display: true,
                            text: 'gay',
                            font: { size :16},
                            padding: {top :10, bottom :10}
                        }
                    }
            })

        }

    });

