
const ctx = document.getElementById('salesChart').getContext('2d');
const chartLabels = JSON.parse(document.getElementById('chart-labels').textContent);
const chartData = JSON.parse(document.getElementById('chart-data').textContent);

// Initialize the chart
let salesChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: chartLabels,
        datasets: [{
            label: 'Daily Sales ($)',
            data: chartData,
            backgroundColor: 'rgba(102, 126, 234, 0.2)',
            borderColor: 'rgba(102, 126, 234, 1)',
            borderWidth: 2,
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                display: true,
                position: 'top'
            }
        },
        scales: {
            y: {
                beginAtZero: true,
                ticks: {
                    callback: function(value) {
                        return '$' + value.toFixed(2);
                    }
                }
            }
        }
    }
});

// Handle time period filter change
const timePeriodDropdown = document.getElementById('timePeriod');
if (timePeriodDropdown) {
    console.log('Time period dropdown found, attaching event listener');
    timePeriodDropdown.addEventListener('change', function() {
        const months = this.value;
        console.log('Time period changed to:', months, 'months');
        fetchDashboardData(months);
    });
} else {
    console.error('Time period dropdown not found!');
}

function fetchDashboardData(months) {
    console.log('Fetching dashboard data for', months, 'months');
    
    const revenueValue = document.getElementById('revenue-value');
    const customersValue = document.getElementById('customers-value');
    const revenueLabel = document.getElementById('revenue-label');
    const customersLabel = document.getElementById('customers-label');
    const chartTitle = document.getElementById('chart-title');
    
    // Add visual loading feedback
    if (revenueValue) revenueValue.style.opacity = '0.5';
    if (customersValue) customersValue.style.opacity = '0.5';
    
    fetch(`/admin_panel/dashboard/filter/?months=${months}`)
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Received data:', data);
            
            // Update revenue
            if (revenueValue) {
                revenueValue.textContent = '$' + parseFloat(data.total_revenue).toFixed(2);
                revenueValue.style.opacity = '1';
            }
            
            // Update new customers
            if (customersValue) {
                customersValue.textContent = data.new_customers;
                customersValue.style.opacity = '1';
            }
            
            // Update labels
            if (months == '1') {
                if (revenueLabel) revenueLabel.textContent = 'Total Revenue (This Month)';
                if (customersLabel) customersLabel.textContent = 'New Customers (This Month)';
                if (chartTitle) chartTitle.innerHTML = '<i class="fas fa-chart-area"></i> Sales Trend (Last 30 Days)';
            } else if (months == '6') {
                if (revenueLabel) revenueLabel.textContent = 'Total Revenue (Last 6 Months)';
                if (customersLabel) customersLabel.textContent = 'New Customers (Last 6 Months)';
                if (chartTitle) chartTitle.innerHTML = '<i class="fas fa-chart-area"></i> Sales Trend (Last 6 Months)';
            } else {
                if (revenueLabel) revenueLabel.textContent = 'Total Revenue (Last Year)';
                if (customersLabel) customersLabel.textContent = 'New Customers (Last Year)';
                if (chartTitle) chartTitle.innerHTML = '<i class="fas fa-chart-area"></i> Sales Trend (Last Year)';
            }
            
            // Update chart
            if (salesChart && data.chart_labels && data.chart_data) {
                salesChart.data.labels = data.chart_labels;
                salesChart.data.datasets[0].data = data.chart_data;
                salesChart.update('active');
                console.log('Chart updated successfully');
            }
        })
        .catch(error => {
            console.error('Error fetching dashboard data:', error);
            alert('Failed to update dashboard. Please check the console for details.');
            
            // Restore opacity
            if (revenueValue) revenueValue.style.opacity = '1';
            if (customersValue) customersValue.style.opacity = '1';
        });
}