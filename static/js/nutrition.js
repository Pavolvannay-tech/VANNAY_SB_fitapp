document.addEventListener('DOMContentLoaded', () => {
    const macroSelector = document.getElementById('macroSelector');
    const ctx = document.getElementById('macroChart');
    
    if (!ctx) return;

    let chartInstance = null;
    let chartData = null;

    // Farby pre jednotlivé makrá zhodné s UI
    const colors = {
        'calories': '#39FF14', // neon-green
        'protein_g': '#00F5FF', // cyan
        'carbs_g': '#FFB800',  // yellow
        'fat_g': '#FF007A'    // pink
    };

    const labels = {
        'calories': 'Kalórie (kcal)',
        'protein_g': 'Bielkoviny (g)',
        'carbs_g': 'Sacharidy (g)',
        'fat_g': 'Tuky (g)'
    };

    // Vykreslenie grafu
    const renderChart = (macroKey) => {
        if (!chartData || !chartData.labels.length) {
            // Nemáme dáta
            return;
        }

        const dataPoints = chartData[macroKey];
        const color = colors[macroKey];
        const label = labels[macroKey];

        if (chartInstance) {
            chartInstance.destroy();
        }

        chartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: chartData.labels,
                datasets: [{
                    label: label,
                    data: dataPoints,
                    borderColor: color,
                    backgroundColor: color + '33', // 20% opacity
                    borderWidth: 3,
                    pointBackgroundColor: '#000',
                    pointBorderColor: color,
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    fill: true,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        theme: 'dark',
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#6c757d',
                        borderWidth: 1,
                        displayColors: false,
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y + (macroKey === 'calories' ? ' kcal' : ' g');
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#adb5bd'
                        }
                    },
                    x: {
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        },
                        ticks: {
                            color: '#adb5bd'
                        }
                    }
                }
            }
        });
    };

    // Načítanie dát
    fetch('/nutrition/api/chart_data')
        .then(res => res.json())
        .then(data => {
            chartData = data;
            renderChart(macroSelector.value);
        })
        .catch(err => console.error("Chyba pri načítaní dát pre graf:", err));

    // Event listener pre zmenu makra
    macroSelector.addEventListener('change', (e) => {
        renderChart(e.target.value);
    });
});
