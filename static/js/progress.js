document.addEventListener('DOMContentLoaded', () => {
    
    // 1. Chart - Consistency (Timeline)
    const consistencyCtx = document.getElementById('consistencyChart');
    const rangeSelector = document.getElementById('rangeSelector');
    let consistencyChartItem = null;

    if (consistencyCtx) {
        const loadConsistencyChart = (range = 'month') => {
            fetch(`/progress/api/consistency?range=${range}`)
                .then(r => r.json())
                .then(data => {
                    if (consistencyChartItem) {
                        consistencyChartItem.destroy();
                    }
                    consistencyChartItem = new Chart(consistencyCtx, {
                        type: 'bar',
                        data: {
                            labels: data.labels,
                            datasets: [{
                                label: 'Trvanie (min)',
                                data: data.data,
                                backgroundColor: data.colors,
                                borderRadius: 6
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { 
                                legend: { display: false },
                                tooltip: { 
                                    padding: 10,
                                    callbacks: {
                                        label: function(context) {
                                            const idx = context.dataIndex;
                                            const status = data.statuses[idx];
                                            const type = data.types[idx];
                                            const val = data.data[idx];
                                            
                                            if (status === 'rest') {
                                                return '💤 Voľno: 1.5 hodiny (Regenerácia)';
                                            } else if (status === 'missed') {
                                                return `❌ Zmeškaný tréning: ${type.replace('Zmeškaný (', '').replace(')', '')}`;
                                            } else if (status === 'today_planned') {
                                                return `⏳ Naplánované na dnes: ${type.replace('Dnes: ', '')}`;
                                            } else {
                                                return `💪 ${type}: odcvičené za ${val} min`;
                                            }
                                        }
                                    }
                                }
                            },
                            scales: {
                                y: { 
                                    beginAtZero: true, 
                                    ticks: { stepSize: 10 }, 
                                    title: {
                                        display: true,
                                        text: 'Čas (minúty)',
                                        color: '#6c757d',
                                        font: { size: 12, weight: 'bold' }
                                    },
                                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false } 
                                },
                                x: { grid: { display: false, drawBorder: false } }
                            }
                        }
                    });
                });
        };

        // Initial load
        const defaultRange = rangeSelector ? rangeSelector.value : 'month';
        loadConsistencyChart(defaultRange);

        if (rangeSelector) {
            rangeSelector.addEventListener('change', (e) => {
                loadConsistencyChart(e.target.value);
            });
        }
    }

    // 2. Charts per Exercise
    let maxWeightChartItem = null;
    let repsChartItem = null;

    const maxWeightCtx = document.getElementById('maxWeightChart');
    const repsCtx = document.getElementById('repsChart');
    const selector = document.getElementById('exerciseSelector');

    if (selector && maxWeightCtx && repsCtx) {
        selector.addEventListener('change', (e) => {
            const exName = encodeURIComponent(e.target.value);
            if (!exName) return;

            fetch(`/progress/api/exercise/${exName}`)
                .then(r => r.json())
                .then(data => {
                    const datesRaw = data.labels;
                    // Skrátenie formátu dátumu (YYYY-MM-DD -> MM-DD)
                    const validDates = datesRaw.map(d => d.substring(5));

                    if (maxWeightChartItem) maxWeightChartItem.destroy();
                    if (repsChartItem) repsChartItem.destroy();

                    // Max Weight Line Chart
                    maxWeightChartItem = new Chart(maxWeightCtx, {
                        type: 'line',
                        data: {
                            labels: validDates,
                            datasets: [{
                                label: 'Maximálna váha (kg)',
                                data: data.max_weight,
                                borderColor: '#ffc107',
                                backgroundColor: 'rgba(255, 193, 7, 0.15)',
                                borderWidth: 3,
                                pointBackgroundColor: '#ffc107',
                                pointRadius: 5,
                                fill: true,
                                tension: 0.2
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { beginAtZero: false, grid: { color: 'rgba(255,255,255,0.05)' } },
                                x: { grid: { display: false }, ticks: {maxTicksLimit: 7} }
                            }
                        }
                    });

                    // Max Reps Line Chart
                    repsChartItem = new Chart(repsCtx, {
                        type: 'line',
                        data: {
                            labels: validDates,
                            datasets: [{
                                label: 'Maximálne opakovania (reps)',
                                data: data.max_reps, 
                                borderColor: '#198754',
                                backgroundColor: 'rgba(25, 135, 84, 0.15)',
                                borderWidth: 3,
                                pointBackgroundColor: '#198754',
                                pointRadius: 5,
                                fill: true,
                                tension: 0.2
                            }]
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: { legend: { display: false } },
                            scales: {
                                y: { 
                                    beginAtZero: true, 
                                    ticks: { stepSize: 1 }, 
                                    grid: { color: 'rgba(255,255,255,0.05)' } 
                                },
                                x: { grid: { display: false }, ticks: {maxTicksLimit: 7} }
                            }
                        }
                    });
                });
        });
        
        // Auto trigger zmeny ak existujú options (1+ pretože default disabled option)
        if (selector.options.length > 1) {
            selector.selectedIndex = 1;
            selector.dispatchEvent(new Event('change'));
        }
    }
});
