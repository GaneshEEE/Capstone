// Multi-Stock Comparison functionality

window.comparisonStocks = [];
window.comparisonView = 'table'; // 'table' or 'cards'
window.tickerTags = []; // Store ticker tags

// Run comparison with bulk input
async function runComparison() {
    const tickers = window.tickerTags;

    if (tickers.length < 2) {
        alert('Please enter at least 2 stock tickers for comparison');
        return;
    }

    // Clear previous comparison
    window.comparisonStocks = [];

    // Show loading
    document.getElementById('comparisonLoading').style.display = 'block';
    document.getElementById('emptyComparison').style.display = 'none';
    document.getElementById('comparisonContent').style.display = 'none';
    document.getElementById('comparisonCharts').style.display = 'none';

    const compareBtn = document.getElementById('compareBtn');
    const originalBtnContent = compareBtn.innerHTML;
    compareBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Loading...';
    compareBtn.disabled = true;

    let successCount = 0;
    let failedTickers = [];

    // Fetch all stocks
    for (let i = 0; i < tickers.length; i++) {
        const ticker = tickers[i];
        document.getElementById('comparisonLoadingText').textContent =
            `Fetching ${ticker}... (${i + 1}/${tickers.length})`;

        try {
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: ticker,
                    company_name: '',
                    timeframe: '7d'
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'Failed to fetch');
            }

            // Add to comparison list
            window.comparisonStocks.push({
                ticker: data.ticker,
                companyName: data.company_name,
                currentPrice: data.stock_data.current_price,
                priceChange: data.stock_data.price_change_percent,
                sentiment: data.impact_prediction.combined.prediction,
                sentimentScore: data.impact_prediction.combined.confidence,
                volume: data.stock_data.volume,
                exchange: data.stock_data.exchange,
                prevClose: data.stock_data.prev_close,
                dayHigh: data.stock_data.day_high,
                dayLow: data.stock_data.day_low
            });

            successCount++;
        } catch (error) {
            console.error(`Error fetching ${ticker}:`, error);
            failedTickers.push(ticker);
        }
    }

    // Hide loading
    document.getElementById('comparisonLoading').style.display = 'none';
    compareBtn.innerHTML = originalBtnContent;
    compareBtn.disabled = false;

    // Show results or error
    if (successCount >= 2) {
        renderComparison();
        renderComparisonCharts();

        if (failedTickers.length > 0) {
            alert(`Comparison complete! Note: Failed to fetch data for: ${failedTickers.join(', ')}`);
        }
    } else {
        alert(`Failed to fetch enough stocks. Only ${successCount} succeeded. Failed: ${failedTickers.join(', ')}`);
        document.getElementById('emptyComparison').style.display = 'block';
    }
}

// Add ticker tag
function addTickerTag(ticker) {
    ticker = ticker.trim().toUpperCase();
    if (!ticker || window.tickerTags.includes(ticker)) return;

    window.tickerTags.push(ticker);
    renderTickerTags();
}

// Remove ticker tag
function removeTickerTag(ticker) {
    window.tickerTags = window.tickerTags.filter(t => t !== ticker);
    renderTickerTags();
}

// Render ticker tags inside the input
function renderTickerTags() {
    const container = document.getElementById('tickerTags');
    const input = document.getElementById('tickerInput');

    let html = '';
    window.tickerTags.forEach(ticker => {
        html += `
            <span class="badge bg-primary d-inline-flex align-items-center" style="font-size: 13px; padding: 5px 8px;">
                ${ticker}
                <i class="fas fa-times ms-2" style="cursor: pointer; font-size: 11px;" onclick="removeTickerTag('${ticker}')"></i>
            </span>
        `;
    });

    container.innerHTML = html;

    // Show/hide placeholder
    if (window.tickerTags.length > 0) {
        input.placeholder = '';
    } else {
        input.placeholder = 'e.g., AAPL, MSFT, GOOGL, TSLA, AMZN';
    }
}

// Clear all comparison stocks
function clearComparison() {
    if (window.comparisonStocks.length === 0) return;

    if (confirm('Are you sure you want to clear the comparison?')) {
        window.comparisonStocks = [];
        window.tickerTags = [];
        document.getElementById('tickerInput').value = '';
        renderTickerTags();
        document.getElementById('comparisonContent').style.display = 'none';
        document.getElementById('comparisonCharts').style.display = 'none';
        document.getElementById('emptyComparison').style.display = 'block';
    }
}

// Remove stock from comparison
function removeComparisonStock(ticker) {
    window.comparisonStocks = window.comparisonStocks.filter(s => s.ticker !== ticker);
    if (window.comparisonStocks.length < 2) {
        clearComparison();
    } else {
        renderComparison();
        renderComparisonCharts();
    }
}

// Toggle view between table and cards
function toggleComparisonView(view) {
    window.comparisonView = view;
    document.getElementById('viewTableBtn').classList.toggle('active', view === 'table');
    document.getElementById('viewCardsBtn').classList.toggle('active', view === 'cards');
    renderComparison();
}

// Render comparison
function renderComparison() {
    const container = document.getElementById('comparisonContent');
    const emptyState = document.getElementById('emptyComparison');

    if (window.comparisonStocks.length === 0) {
        container.style.display = 'none';
        emptyState.style.display = 'block';
        return;
    }

    container.style.display = 'block';
    emptyState.style.display = 'none';

    if (window.comparisonView === 'table') {
        renderTableView();
    } else {
        renderCardsView();
    }
}

// Render table view
function renderTableView() {
    const container = document.getElementById('comparisonContent');

    let html = `
        <div class="card mb-3">
            <div class="card-header">
                <h5 class="mb-0"><i class="fas fa-table"></i> Comparison Table</h5>
            </div>
            <div class="card-body p-0">
                <div class="table-responsive">
                    <table class="table table-dark table-hover mb-0">
                        <thead>
                            <tr>
                                <th>Ticker</th>
                                <th>Company</th>
                                <th>Price</th>
                                <th>Change %</th>
                                <th>Sentiment</th>
                                <th>Confidence</th>
                                <th>Volume</th>
                                <th>Exchange</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
    `;

    window.comparisonStocks.forEach(stock => {
        const priceClass = stock.priceChange >= 0 ? 'text-success' : 'text-danger';
        const priceSymbol = stock.priceChange >= 0 ? '+' : '';

        let sentimentClass = 'badge bg-secondary';
        let sentimentText = stock.sentiment.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

        if (stock.sentiment.includes('positive')) {
            sentimentClass = 'badge bg-success';
        } else if (stock.sentiment.includes('negative')) {
            sentimentClass = 'badge bg-danger';
        }

        html += `
            <tr>
                <td><strong>${stock.ticker}</strong></td>
                <td>${stock.companyName || 'N/A'}</td>
                <td><strong>$${stock.currentPrice.toFixed(2)}</strong></td>
                <td class="${priceClass} fw-bold">${priceSymbol}${stock.priceChange.toFixed(2)}%</td>
                <td><span class="${sentimentClass}">${sentimentText}</span></td>
                <td>${(stock.sentimentScore * 100).toFixed(1)}%</td>
                <td>${formatNumber(stock.volume)}</td>
                <td>${stock.exchange}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="analyzeFromComparison('${stock.ticker}', '${stock.companyName || ''}')" title="Analyze">
                        <i class="fas fa-chart-line"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="removeComparisonStock('${stock.ticker}')" title="Remove">
                        <i class="fas fa-trash"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    html += `
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `;

    container.innerHTML = html;
}

// Render cards view
function renderCardsView() {
    const container = document.getElementById('comparisonContent');

    let html = '<div class="row g-3 mb-3">';

    window.comparisonStocks.forEach(stock => {
        const priceClass = stock.priceChange >= 0 ? 'text-success' : 'text-danger';
        const priceSymbol = stock.priceChange >= 0 ? '+' : '';

        let sentimentClass = 'bg-secondary';
        let sentimentText = stock.sentiment.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());

        if (stock.sentiment.includes('positive')) {
            sentimentClass = 'bg-success';
        } else if (stock.sentiment.includes('negative')) {
            sentimentClass = 'bg-danger';
        }

        html += `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div>
                            <h5 class="mb-0">${stock.ticker}</h5>
                            <small class="text-muted">${stock.companyName || 'N/A'}</small>
                        </div>
                        <button class="btn btn-sm btn-outline-danger" onclick="removeComparisonStock('${stock.ticker}')" title="Remove">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                    <div class="card-body">
                        <div class="mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="text-muted">Current Price</span>
                                <span class="fs-5 fw-bold">$${stock.currentPrice.toFixed(2)}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="text-muted">Change</span>
                                <span class="${priceClass} fw-bold">${priceSymbol}${stock.priceChange.toFixed(2)}%</span>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <div class="mb-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="text-muted">Sentiment</span>
                                <span class="badge ${sentimentClass}">${sentimentText}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="text-muted">Confidence</span>
                                <span class="fw-bold">${(stock.sentimentScore * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                        
                        <hr>
                        
                        <div class="mb-2">
                            <div class="d-flex justify-content-between align-items-center mb-1">
                                <span class="text-muted small">Volume</span>
                                <span class="small">${formatNumber(stock.volume)}</span>
                            </div>
                            <div class="d-flex justify-content-between align-items-center">
                                <span class="text-muted small">Exchange</span>
                                <span class="small">${stock.exchange}</span>
                            </div>
                        </div>
                        
                        <div class="mt-3">
                            <button class="btn btn-sm btn-outline-primary w-100" onclick="analyzeFromComparison('${stock.ticker}', '${stock.companyName || ''}')">
                                <i class="fas fa-chart-line"></i> View Full Analysis
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    html += '</div>';
    container.innerHTML = html;
}

// Render comprehensive comparison charts
function renderComparisonCharts() {
    if (window.comparisonStocks.length === 0) {
        document.getElementById('comparisonCharts').style.display = 'none';
        return;
    }

    document.getElementById('comparisonCharts').style.display = 'block';

    const tickers = window.comparisonStocks.map(s => s.ticker);
    const colors = ['#16c784', '#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#1abc9c', '#34495e', '#e67e22'];

    // 1. Price vs Volume Bubble Chart
    const priceVolumeData = [{
        x: window.comparisonStocks.map(s => s.volume),
        y: window.comparisonStocks.map(s => s.currentPrice),
        mode: 'markers+text',
        type: 'scatter',
        text: tickers,
        textposition: 'top center',
        marker: {
            size: window.comparisonStocks.map(s => Math.abs(s.priceChange) * 10 + 10),
            color: window.comparisonStocks.map((s, i) => colors[i % colors.length]),
            line: { width: 2, color: '#fff' }
        }
    }];

    Plotly.newPlot('priceVolumeChart', priceVolumeData, {
        title: { text: 'Price vs Volume (Bubble size = % change)', font: { color: '#e2e2e2', size: 14 } },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e2e2' },
        xaxis: { gridcolor: '#333', title: 'Volume', type: 'log' },
        yaxis: { gridcolor: '#333', title: 'Price ($)' },
        margin: { t: 50, b: 60, l: 60, r: 20 },
        hovermode: 'closest'
    }, { responsive: true, displayModeBar: false });

    // 2. Performance vs Sentiment Scatter
    const perfSentimentData = [{
        x: window.comparisonStocks.map(s => s.priceChange),
        y: window.comparisonStocks.map(s => s.sentimentScore * 100),
        mode: 'markers+text',
        type: 'scatter',
        text: tickers,
        textposition: 'top center',
        marker: {
            size: 15,
            color: window.comparisonStocks.map(s => {
                if (s.sentiment.includes('positive')) return '#16c784';
                if (s.sentiment.includes('negative')) return '#ea3943';
                return '#888';
            }),
            line: { width: 2, color: '#fff' }
        }
    }];

    Plotly.newPlot('performanceSentimentChart', perfSentimentData, {
        title: { text: 'Performance vs AI Sentiment Confidence', font: { color: '#e2e2e2', size: 14 } },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e2e2' },
        xaxis: { gridcolor: '#333', title: 'Price Change (%)', zeroline: true, zerolinecolor: '#666' },
        yaxis: { gridcolor: '#333', title: 'Sentiment Confidence (%)', range: [0, 100] },
        margin: { t: 50, b: 60, l: 60, r: 20 },
        shapes: [{
            type: 'line',
            x0: 0, y0: 0, x1: 0, y1: 100,
            line: { color: '#666', width: 1, dash: 'dash' }
        }]
    }, { responsive: true, displayModeBar: false });

    // 3. Price Comparison Bar Chart
    const priceData = [{
        x: tickers,
        y: window.comparisonStocks.map(s => s.currentPrice),
        type: 'bar',
        marker: {
            color: window.comparisonStocks.map((s, i) => colors[i % colors.length])
        },
        text: window.comparisonStocks.map(s => `$${s.currentPrice.toFixed(2)}`),
        textposition: 'outside'
    }];

    Plotly.newPlot('priceComparisonChart', priceData, {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e2e2' },
        xaxis: { gridcolor: '#333' },
        yaxis: { gridcolor: '#333', title: 'Price ($)' },
        margin: { t: 20, b: 40, l: 60, r: 20 }
    }, { responsive: true, displayModeBar: false });

    // 4. Performance Comparison Waterfall
    const perfData = [{
        x: tickers,
        y: window.comparisonStocks.map(s => s.priceChange),
        type: 'bar',
        marker: {
            color: window.comparisonStocks.map(s => s.priceChange >= 0 ? '#16c784' : '#ea3943')
        },
        text: window.comparisonStocks.map(s => `${s.priceChange >= 0 ? '+' : ''}${s.priceChange.toFixed(2)}%`),
        textposition: 'outside'
    }];

    Plotly.newPlot('performanceComparisonChart', perfData, {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e2e2' },
        xaxis: { gridcolor: '#333' },
        yaxis: { gridcolor: '#333', title: 'Change (%)', zeroline: true, zerolinecolor: '#666' },
        margin: { t: 20, b: 40, l: 60, r: 20 }
    }, { responsive: true, displayModeBar: false });

    // 5. Sentiment Confidence Grouped Bar
    const sentimentData = [{
        x: tickers,
        y: window.comparisonStocks.map(s => s.sentimentScore * 100),
        type: 'bar',
        name: 'Confidence',
        marker: {
            color: window.comparisonStocks.map(s => {
                if (s.sentiment.includes('positive')) return '#16c784';
                if (s.sentiment.includes('negative')) return '#ea3943';
                return '#888';
            })
        },
        text: window.comparisonStocks.map(s => `${(s.sentimentScore * 100).toFixed(1)}%`),
        textposition: 'outside'
    }];

    Plotly.newPlot('sentimentComparisonChart', sentimentData, {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e2e2' },
        xaxis: { gridcolor: '#333' },
        yaxis: { gridcolor: '#333', title: 'Confidence (%)', range: [0, 100] },
        margin: { t: 20, b: 40, l: 60, r: 20 }
    }, { responsive: true, displayModeBar: false });

    // 6. Volume Comparison
    const volumeData = [{
        x: tickers,
        y: window.comparisonStocks.map(s => s.volume),
        type: 'bar',
        marker: {
            color: window.comparisonStocks.map((s, i) => colors[i % colors.length])
        },
        text: window.comparisonStocks.map(s => formatNumber(s.volume)),
        textposition: 'outside'
    }];

    Plotly.newPlot('volumeComparisonChart', volumeData, {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e2e2' },
        xaxis: { gridcolor: '#333' },
        yaxis: { gridcolor: '#333', title: 'Volume', type: 'log' },
        margin: { t: 20, b: 40, l: 60, r: 20 }
    }, { responsive: true, displayModeBar: false });

    // 7. Radar Chart for Multi-Metric Comparison
    const radarData = window.comparisonStocks.map((stock, i) => {
        // Normalize metrics to 0-100 scale
        const maxPrice = Math.max(...window.comparisonStocks.map(s => s.currentPrice));
        const maxVolume = Math.max(...window.comparisonStocks.map(s => s.volume));
        const priceChangeNorm = ((stock.priceChange + 10) / 20) * 100; // Assume -10 to +10 range

        return {
            type: 'scatterpolar',
            r: [
                (stock.currentPrice / maxPrice) * 100,
                priceChangeNorm,
                stock.sentimentScore * 100,
                (stock.volume / maxVolume) * 100,
                ((stock.dayHigh - stock.dayLow) / stock.currentPrice) * 1000 // Volatility
            ],
            theta: ['Price', 'Performance', 'Sentiment', 'Volume', 'Volatility'],
            fill: 'toself',
            name: stock.ticker,
            marker: { color: colors[i % colors.length] }
        };
    });

    Plotly.newPlot('radarComparisonChart', radarData, {
        polar: {
            radialaxis: {
                visible: true,
                range: [0, 100],
                gridcolor: '#333'
            },
            angularaxis: {
                gridcolor: '#333'
            },
            bgcolor: 'rgba(0,0,0,0)'
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#e2e2e2' },
        showlegend: true,
        legend: { orientation: 'h', y: -0.15 },
        margin: { t: 40, b: 80, l: 60, r: 60 }
    }, { responsive: true, displayModeBar: false });
}

// Analyze stock from comparison
function analyzeFromComparison(ticker, companyName) {
    switchTab('home');
    document.getElementById('ticker').value = ticker;
    document.getElementById('companyName').value = companyName;
    document.getElementById('analysisForm').dispatchEvent(new Event('submit'));
}

// Format number helper (if not available from script.js)
if (typeof formatNumber === 'undefined') {
    function formatNumber(num) {
        if (!num || num === 'N/A' || num === 0) return 'N/A';
        if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
        if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
        if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
        return num.toString();
    }
}

// Handle ticker input
document.addEventListener('DOMContentLoaded', function () {
    const tickerInput = document.getElementById('tickerInput');
    if (tickerInput) {
        // Handle input - add ticker on comma or space
        tickerInput.addEventListener('keydown', function (e) {
            const value = this.value.trim();

            if ((e.key === ',' || e.key === ' ' || e.key === 'Enter') && value) {
                e.preventDefault();
                addTickerTag(value);
                this.value = '';
            } else if (e.key === 'Backspace' && !value && window.tickerTags.length > 0) {
                // Remove last tag on backspace if input is empty
                e.preventDefault();
                window.tickerTags.pop();
                renderTickerTags();
            } else if (e.key === 'Enter' && window.tickerTags.length >= 2) {
                // Run comparison on Enter if we have enough tickers
                e.preventDefault();
                runComparison();
            }
        });
    }
});

// Override switchTab to handle comparison tab
(function () {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function (tabName) {
        const comparisonSection = document.getElementById('comparison-section');
        const navComparison = document.getElementById('nav-comparison');

        if (tabName === 'comparison') {
            // Hide all other sections
            document.querySelector('.news-ticker').style.display = 'none';
            document.querySelector('.dashboard-header').style.display = 'none';
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('results').style.display = 'none';
            document.getElementById('watchlist-section').style.display = 'none';
            document.getElementById('market-pulse-section').style.display = 'none';

            // Show comparison section
            comparisonSection.style.display = 'block';

            // Update nav
            document.getElementById('nav-home').classList.remove('active');
            document.getElementById('nav-watchlist').classList.remove('active');
            document.getElementById('nav-market-pulse').classList.remove('active');
            navComparison.classList.add('active');

            // Render if we have data
            if (window.comparisonStocks.length > 0) {
                renderComparison();
                renderComparisonCharts();
            }
        } else {
            // Hide comparison section
            comparisonSection.style.display = 'none';
            navComparison && navComparison.classList.remove('active');

            // Call original function
            if (originalSwitchTab) {
                originalSwitchTab(tabName);
            }
        }
    };
})();
