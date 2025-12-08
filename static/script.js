// Auto-populate fields when user enters ticker or company name
let lookupTimeout;
let isAutoPopulating = false; // Flag to prevent clearing during auto-population

document.getElementById('ticker').addEventListener('blur', async function () {
    const ticker = this.value.trim().toUpperCase();
    const companyNameField = document.getElementById('companyName');

    // Lookup company name when ticker is entered
    if (ticker) {
        clearTimeout(lookupTimeout);
        lookupTimeout = setTimeout(async () => {
            try {
                isAutoPopulating = true;
                const response = await fetch('/lookup-company', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ticker: ticker })
                });

                const data = await response.json();
                if (response.ok && data.company_name) {
                    companyNameField.value = data.company_name;
                }
            } catch (error) {
                // Silently fail - don't show error for auto-lookup
                console.log('Auto-lookup failed:', error);
            } finally {
                isAutoPopulating = false;
            }
        }, 300); // Debounce for 300ms
    }
});

document.getElementById('companyName').addEventListener('blur', async function () {
    const companyName = this.value.trim();
    const tickerField = document.getElementById('ticker');

    // Lookup ticker when company name is entered
    if (companyName) {
        clearTimeout(lookupTimeout);
        lookupTimeout = setTimeout(async () => {
            try {
                isAutoPopulating = true;
                const response = await fetch('/lookup-ticker', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ company_name: companyName })
                });

                const data = await response.json();
                if (response.ok && data.ticker) {
                    tickerField.value = data.ticker;
                }
            } catch (error) {
                // Silently fail - don't show error for auto-lookup
                console.log('Auto-lookup failed:', error);
            } finally {
                isAutoPopulating = false;
            }
        }, 300); // Debounce for 300ms
    }
});

document.getElementById('analysisForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    document.getElementById('downloadReportBtn').style.display = 'none';
    const ticker = document.getElementById('ticker').value.trim();
    const companyName = document.getElementById('companyName').value.trim();
    const timeframe = document.getElementById('timeframe').value;

    if (!ticker && !companyName) {
        showError('Please enter either a ticker or company name');
        return;
    }

    // Show loading, hide results and error
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    // Reset previous stock data and prediction
    displayStockData(null);
    document.getElementById('pricePredictionContainer').style.display = 'none';

    // Reset all loading steps
    resetLoadingSteps();

    try {
        // Start the fetch - this happens immediately
        updateLoadingStep('fetch', 'active');

        // Simulate progressive loading steps with realistic timing
        const loadingSimulation = simulateLoadingProgress();

        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                ticker: ticker,
                company_name: companyName,
                timeframe: timeframe
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Analysis failed');
        }

        // Complete all steps
        await loadingSimulation;
        completeAllSteps();

        displayResults(data);

    } catch (error) {
        showError(error.message);
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
});

// Helper function to reset loading steps
function resetLoadingSteps() {
    const steps = ['fetch', 'sentiment', 'ai', 'predict', 'forecast'];
    steps.forEach(step => {
        const element = document.getElementById(`step-${step}`);
        element.style.opacity = '0.3';
        element.classList.remove('active', 'completed');
        const icon = element.querySelector('i');
        icon.className = 'fas fa-circle';
        icon.style.color = 'var(--finviz-text-light)';
    });

    // Set first step as active
    const firstStep = document.getElementById('step-fetch');
    firstStep.style.opacity = '1';
    firstStep.classList.add('active');
    const firstIcon = firstStep.querySelector('i');
    firstIcon.className = 'fas fa-circle-notch fa-spin';
    firstIcon.style.color = 'var(--finviz-blue)';
}

// Helper function to update loading step
function updateLoadingStep(stepName, status) {
    const element = document.getElementById(`step-${stepName}`);
    const icon = element.querySelector('i');

    if (status === 'active') {
        element.style.opacity = '1';
        element.classList.add('active');
        icon.className = 'fas fa-circle-notch fa-spin';
        icon.style.color = 'var(--finviz-blue)';
    } else if (status === 'completed') {
        element.classList.remove('active');
        element.classList.add('completed');
        icon.className = 'fas fa-check-circle';
        icon.style.color = 'var(--finviz-green)';
    }
}

// Simulate loading progress with realistic timing
async function simulateLoadingProgress() {
    // Step 1: Fetch (already active, complete after 800ms)
    await sleep(800);
    updateLoadingStep('fetch', 'completed');

    // Step 2: Sentiment analysis
    updateLoadingStep('sentiment', 'active');
    document.getElementById('loadingMainText').textContent = 'Analyzing sentiment...';
    await sleep(1200);
    updateLoadingStep('sentiment', 'completed');

    // Step 3: AI insights
    updateLoadingStep('ai', 'active');
    document.getElementById('loadingMainText').textContent = 'Generating AI insights...';
    await sleep(1500);
    updateLoadingStep('ai', 'completed');

    // Step 4: Predict impact
    updateLoadingStep('predict', 'active');
    document.getElementById('loadingMainText').textContent = 'Predicting market impact...';
    await sleep(1000);
    updateLoadingStep('predict', 'completed');

    // Step 5: Forecast
    updateLoadingStep('forecast', 'active');
    document.getElementById('loadingMainText').textContent = 'Creating price forecast...';
    await sleep(800);
    updateLoadingStep('forecast', 'completed');

    document.getElementById('loadingMainText').textContent = 'Analysis complete!';
}

// Complete all steps immediately (when response arrives early)
function completeAllSteps() {
    const steps = ['fetch', 'sentiment', 'ai', 'predict', 'forecast'];
    steps.forEach(step => {
        const element = document.getElementById(`step-${step}`);
        element.style.opacity = '1';
        element.classList.remove('active');
        element.classList.add('completed');
        const icon = element.querySelector('i');
        icon.className = 'fas fa-check-circle';
        icon.style.color = 'var(--finviz-green)';
    });
}

// Sleep helper
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


document.getElementById('qnaForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const question = document.getElementById('question').value.trim();

    if (!question) {
        showQnaError('Please enter a question.');
        return;
    }

    document.getElementById('qnaLoading').style.display = 'block';
    document.getElementById('qnaResults').style.display = 'none';
    document.getElementById('qnaError').style.display = 'none';

    try {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question: question })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Failed to get an answer.');
        }

        const qnaAnswerDiv = document.getElementById('qnaAnswer');
        qnaAnswerDiv.innerHTML = data.answer;
        document.getElementById('qnaResults').style.display = 'block';

    } catch (error) {
        showQnaError(error.message);
    } finally {
        document.getElementById('qnaLoading').style.display = 'none';
    }
});

// Helper functions for formatting numbers
function formatNumber(num) {
    if (!num || num === 'N/A' || num === 0) return 'N/A';
    if (num >= 1e9) return (num / 1e9).toFixed(1) + 'B';
    if (num >= 1e6) return (num / 1e6).toFixed(1) + 'M';
    if (num >= 1e3) return (num / 1e3).toFixed(1) + 'K';
    return num.toString();
}

function formatPrice(price) {
    if (!price || price === 'N/A' || price === 0) return 'N/A';
    return '$' + price.toFixed(2);
}

function formatDayRange(dayHigh, dayLow) {
    if (!dayHigh || !dayLow || dayHigh === 0 || dayLow === 0) return 'N/A';
    return `$${dayLow.toFixed(2)}-${dayHigh.toFixed(2)}`;
}

function displayStockData(stockData, ticker) {
    if (!stockData) {
        // Show placeholder if no stock data available
        document.getElementById('stockPriceDisplay').innerHTML = `
            <span class="stock-price price-neutral">-</span>
            <span class="price-change price-neutral">-</span>
        `;

        document.getElementById('statsGrid').innerHTML = `
            <div class="stat-box">
                <div class="stat-value">-</div>
                <div class="stat-label">Volume</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">-</div>
                <div class="stat-label">Day Range</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">-</div>
                <div class="stat-label">Exchange</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">-</div>
                <div class="stat-label">Prev Close</div>
            </div>
        `;
        return;
    }

    const priceChange = stockData.price_change || 0;
    const priceChangePercent = stockData.price_change_percent || 0;

    const priceClass = priceChange > 0 ? 'price-up' : priceChange < 0 ? 'price-down' : 'price-neutral';
    const changeSymbol = priceChange > 0 ? '+' : '';

    document.getElementById('stockPriceDisplay').innerHTML = `
        <div class="d-flex align-items-center gap-3">
            <div>
                <span class="stock-price ${priceClass}">$${stockData.current_price || 'N/A'}</span>
                <span class="price-change ${priceClass}">${changeSymbol}${priceChangePercent.toFixed(2)}%</span>
            </div>
            <button onclick="addToWatchlist(event)" class="btn btn-outline-primary btn-sm" title="Add to Watchlist">
                <i class="fas fa-plus"></i> Add to Watchlist
            </button>
        </div>
    `;

    // Update stats grid with chart API data
    document.getElementById('statsGrid').innerHTML = `
        <div class="stat-box">
            <div class="stat-value">${formatNumber(stockData.volume)}</div>
            <div class="stat-label">Volume</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">${formatDayRange(stockData.day_high, stockData.day_low)}</div>
            <div class="stat-label">Day Range</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">${stockData.exchange}</div>
            <div class="stat-label">Exchange</div>
        </div>
        <div class="stat-box">
            <div class="stat-value">${formatPrice(stockData.prev_close)}</div>
            <div class="stat-label">Prev Close</div>
        </div>
    `;
}

async function addToWatchlist(event) {
    const ticker = document.getElementById('ticker').value.trim() || document.getElementById('companyName').value.trim();
    if (!ticker) return;

    if (!window.lastAnalysisData) {
        alert("Please analyze a stock first.");
        return;
    }

    const data = window.lastAnalysisData;

    // Extract predicted target range
    const targetRangeElement = document.getElementById('predTargetRange');
    let predictedTargetRange = 'N/A';
    if (targetRangeElement && targetRangeElement.textContent) {
        predictedTargetRange = targetRangeElement.textContent;
    }

    // Get the combined prediction
    const combinedPrediction = data.impact_prediction.combined;
    const recommendation = combinedPrediction ? (combinedPrediction.prediction.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())) : 'Unknown';

    const payload = {
        ticker: data.ticker,
        company_name: data.company_name,
        price: data.stock_data.current_price,
        predicted_target_range: predictedTargetRange,
        summary: data.ai_summary,
        recommendation: recommendation
    };

    const btn = event.currentTarget;
    const originalContent = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Saving...';
    btn.disabled = true;

    try {
        const response = await fetch('/watchlist/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const res = await response.json();
        if (response.ok) {
            btn.innerHTML = '<i class="fas fa-check"></i> Saved!';
            btn.classList.remove('btn-outline-primary');
            btn.classList.add('btn-success');
            setTimeout(() => {
                btn.innerHTML = originalContent;
                btn.disabled = false;
                btn.classList.remove('btn-success');
                btn.classList.add('btn-outline-primary');
            }, 2000);
        } else {
            alert("Error: " + res.error);
            btn.innerHTML = originalContent;
            btn.disabled = false;
        }
    } catch (e) {
        alert("Error: " + e.message);
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

async function loadWatchlist() {
    try {
        const response = await fetch('/watchlist/get');
        const data = await response.json();

        const watchlistGrid = document.getElementById('watchlistGrid');
        const emptyState = document.getElementById('emptyWatchlist');
        const watchlistStats = document.getElementById('watchlistStats');

        watchlistGrid.innerHTML = '';

        if (!data.watchlist || data.watchlist.length === 0) {
            watchlistStats.style.display = 'none';
            emptyState.style.display = 'block';
            return;
        }

        watchlistStats.style.display = 'grid';
        emptyState.style.display = 'none';

        // Calculate stats
        let totalChange = 0;
        let bullishCount = 0;
        let bearishCount = 0;

        data.watchlist.forEach(item => {
            // Create watchlist card
            const card = document.createElement('div');
            card.className = 'watchlist-card';

            // Determine recommendation styling
            let recClass = 'recommendation-hold';
            let recText = item.recommendation || 'Hold';
            const recLower = recText.toLowerCase();

            if (recLower.includes('strongly positive') || recLower.includes('strong buy')) {
                recClass = 'recommendation-strong-buy';
                recText = 'Strong Buy';
                bullishCount++;
            } else if (recLower.includes('positive') || recLower.includes('buy')) {
                recClass = 'recommendation-buy';
                recText = 'Buy';
                bullishCount++;
            } else if (recLower.includes('strongly negative') || recLower.includes('strong sell')) {
                recClass = 'recommendation-strong-sell';
                recText = 'Strong Sell';
                bearishCount++;
            } else if (recLower.includes('negative') || recLower.includes('sell')) {
                recClass = 'recommendation-sell';
                recText = 'Sell';
                bearishCount++;
            } else {
                recClass = 'recommendation-hold';
                recText = 'Hold';
            }

            // Simulate price change for demo (in real app, fetch current prices)
            const priceChange = (Math.random() * 4 - 2).toFixed(2); // -2% to +2%
            totalChange += parseFloat(priceChange);
            const currentPrice = item.price * (1 + parseFloat(priceChange) / 100);
            const changeClass = parseFloat(priceChange) >= 0 ? 'positive' : 'negative';
            const changeSymbol = parseFloat(priceChange) >= 0 ? '+' : '';

            card.innerHTML = `
                <div class="watchlist-card-header">
                    <div>
                        <div class="watchlist-ticker">${item.ticker}</div>
                        <div class="watchlist-company">${item.company_name || 'N/A'}</div>
                    </div>
                    <div class="watchlist-price">
                        <div class="watchlist-current-price">$${currentPrice.toFixed(2)}</div>
                        <div class="watchlist-price-change ${changeClass}">
                            ${changeSymbol}${priceChange}%
                        </div>
                    </div>
                </div>
                
                <div class="watchlist-prediction">
                    <div class="watchlist-prediction-label">Predicted Range</div>
                    <div class="watchlist-prediction-value">${item.predicted_target_range || 'N/A'}</div>
                    <div class="watchlist-recommendation ${recClass}">${recText}</div>
                </div>
                
                <div class="watchlist-card-footer">
                    <div class="watchlist-added">
                        <i class="far fa-calendar"></i> ${new Date(item.added_at).toLocaleDateString()}
                    </div>
                    <div class="watchlist-actions-buttons">
                        <button class="watchlist-btn watchlist-btn-analyze" 
                                onclick="analyzeFromWatchlist('${item.ticker}', '${item.company_name || ''}')"
                                title="Analyze">
                            <i class="fas fa-chart-line"></i>
                        </button>
                        <button class="watchlist-btn watchlist-btn-remove" 
                                onclick="removeFromWatchlist('${item.ticker}')"
                                title="Remove">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            watchlistGrid.appendChild(card);
        });

        // Update stats
        document.getElementById('watchlistCount').textContent = data.watchlist.length;
        document.getElementById('watchlistAvgChange').textContent =
            `${(totalChange / data.watchlist.length).toFixed(2)}%`;
        document.getElementById('watchlistBullish').textContent = bullishCount;
        document.getElementById('watchlistBearish').textContent = bearishCount;

    } catch (e) {
        console.error("Error loading watchlist:", e);
    }
}

async function removeFromWatchlist(ticker) {
    if (!confirm(`Are you sure you want to remove ${ticker} from your watchlist?`)) return;

    try {
        const response = await fetch('/watchlist/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: ticker })
        });

        if (response.ok) {
            loadWatchlist(); // Reload list
        } else {
            alert("Failed to remove item");
        }
    } catch (e) {
        console.error("Error removing item:", e);
    }
}

function analyzeFromWatchlist(ticker, companyName) {
    switchTab('home');
    document.getElementById('ticker').value = ticker;
    document.getElementById('companyName').value = companyName;
    // Trigger analysis
    document.getElementById('analysisForm').dispatchEvent(new Event('submit'));
}

function switchTab(tabName) {
    const homeSection = document.querySelector('.news-ticker').parentNode; // Main container content
    // Actually, we need to be careful not to hide the nav bar.
    // The structure is: .finviz-nav, then .main-container.
    // Inside .main-container, we have .news-ticker, .dashboard-header, etc.
    // We wrapped the new watchlist section inside .main-container at the end.

    // Let's identify the home content. It's everything inside .main-container EXCEPT #watchlist-section
    // A better way is to wrap home content in a div, but I can't easily do that with replace.
    // So I'll toggle visibility of specific IDs.

    const newsTicker = document.querySelector('.news-ticker');
    const dashboardHeader = document.querySelector('.dashboard-header');
    const loading = document.getElementById('loading');
    const error = document.getElementById('error');
    const results = document.getElementById('results');
    const watchlistSection = document.getElementById('watchlist-section');

    const navHome = document.getElementById('nav-home');
    const navWatchlist = document.getElementById('nav-watchlist');

    if (tabName === 'home') {
        // Show Home
        newsTicker.style.display = 'block';
        dashboardHeader.style.display = 'block';
        if (window.lastAnalysisData) results.style.display = 'block'; // Only show results if we have data
        watchlistSection.style.display = 'none';

        navHome.classList.add('active');
        navWatchlist.classList.remove('active');
    } else {
        // Show Watchlist
        newsTicker.style.display = 'none';
        dashboardHeader.style.display = 'none';
        loading.style.display = 'none';
        error.style.display = 'none';
        results.style.display = 'none';
        watchlistSection.style.display = 'block';

        navHome.classList.remove('active');
        navWatchlist.classList.add('active');

        loadWatchlist();
    }
}

function displayResults(data) {
    window.lastAnalysisData = data; // Save for ClickUp export
    displayStockData(data.stock_data, data.ticker);
    // Display timeframe label
    const timeframeLabels = {
        '24h': '(Last 24 Hours)',
        '7d': '(Last 7 Days)',
        '30d': '(Last 30 Days)',
        'all': '(All Available)'
    };
    document.getElementById('timeframeLabel').textContent = timeframeLabels[data.timeframe] || '';

    // Get sentiment data for chart
    const sentimentData = data.sentiment_distribution;

    // Display impact predictions (rule-based, ML, and combined)
    const impactDiv = document.getElementById('impactPrediction');
    const predictions = data.impact_prediction;

    // Handle legacy format (if prediction is not an object with rule_based/ml/combined)
    let ruleBasedPred, mlPred, combinedPred;
    if (predictions.rule_based) {
        // New format with multiple predictions
        ruleBasedPred = predictions.rule_based;
        mlPred = predictions.ml;
        combinedPred = predictions.combined;
    } else {
        // Legacy format - treat as rule-based only
        ruleBasedPred = predictions;
        mlPred = null;
        combinedPred = predictions;
    }

    // Map prediction labels to display names and icons
    const predictionDisplay = {
        'strongly_positive': { name: 'Strongly Positive', icon: '📈', arrow: '<i class="fas fa-arrow-up"></i>' },
        'moderately_positive': { name: 'Moderately Positive', icon: '↗️', arrow: '<i class="fas fa-arrow-up"></i>' },
        'slightly_positive': { name: 'Slightly Positive', icon: '↗️', arrow: '<i class="fas fa-arrow-up"></i>' },
        'slightly_negative': { name: 'Slightly Negative', icon: '↘️', arrow: '<i class="fas fa-arrow-down"></i>' },
        'moderately_negative': { name: 'Moderately Negative', icon: '↘️', arrow: '<i class="fas fa-arrow-down"></i>' },
        'strongly_negative': { name: 'Strongly Negative', icon: '📉', arrow: '<i class="fas fa-arrow-down"></i>' },
        // Legacy support
        'positive': { name: 'Positive', icon: '↗️', arrow: '<i class="fas fa-arrow-up"></i>' },
        'negative': { name: 'Negative', icon: '↘️', arrow: '<i class="fas fa-arrow-down"></i>' },
        'mixed': { name: 'Mixed', icon: '➡️', arrow: '<i class="fas fa-minus"></i>' }
    };

    function getDisplay(pred) {
        return predictionDisplay[pred.prediction] || {
            name: pred.prediction.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
            icon: '➡️',
            arrow: '<i class="fas fa-minus"></i>'
        };
    }

    const ruleDisplay = getDisplay(ruleBasedPred);
    const ruleClass = `impact-${ruleBasedPred.prediction}`;

    let html = `
        <div class="predictions-container" style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
            <div class="${ruleClass} impact-prediction" style="border: 2px solid var(--finviz-border);">
                <h4 style="font-size: 16px; margin-bottom: 10px;">${ruleDisplay.icon} Rule-Based Prediction</h4>
                <p style="margin: 8px 0;"><strong>Result:</strong> ${ruleDisplay.name}</p>
                <p style="margin: 8px 0;"><strong>Confidence:</strong> ${(ruleBasedPred.confidence * 100).toFixed(2)}%</p>
                <p style="margin: 8px 0; font-size: 12px;"><strong>Reasoning:</strong> ${ruleBasedPred.reasoning}</p>
            </div>
    `;

    if (mlPred) {
        const mlDisplay = getDisplay(mlPred);
        const mlClass = `impact-${mlPred.prediction}`;
        html += `
            <div class="${mlClass} impact-prediction" style="border: 2px solid var(--finviz-border);">
                <h4 style="font-size: 16px; margin-bottom: 10px;">🤖 ML Model Prediction</h4>
                <p style="margin: 8px 0;"><strong>Result:</strong> ${mlDisplay.name}</p>
                <p style="margin: 8px 0;"><strong>Confidence:</strong> ${(mlPred.confidence * 100).toFixed(2)}%</p>
                <p style="margin: 8px 0; font-size: 12px;"><strong>Reasoning:</strong> ${mlPred.reasoning}</p>
            </div>
        `;
    } else {
        html += `
            <div class="impact-prediction" style="border: 2px solid var(--finviz-border); opacity: 0.6;">
                <h4 style="font-size: 16px; margin-bottom: 10px;">🤖 ML Model Prediction</h4>
                <p style="margin: 8px 0; font-style: italic;">ML model not available or not trained</p>
                <p style="margin: 8px 0; font-size: 12px;">Train a model using train_model.py to enable ML predictions</p>
            </div>
        `;
    }

    html += `</div>`;

    // Combined/Enhanced prediction
    const combinedDisplay = getDisplay(combinedPred);
    const combinedClass = `impact-${combinedPred.prediction}`;
    html += `
        <div class="${combinedClass} impact-prediction" style="border: 2px solid var(--finviz-accent); background: var(--finviz-bg-secondary);">
            <h4 style="font-size: 18px; margin-bottom: 12px;">⭐ Enhanced Prediction (Combined)</h4>
            <p style="margin: 10px 0;"><strong>Result:</strong> ${combinedDisplay.name}</p>
            <p style="margin: 10px 0;"><strong>Confidence:</strong> ${(combinedPred.confidence * 100).toFixed(2)}%</p>
            <p style="margin: 10px 0;"><strong>Reasoning:</strong> ${combinedPred.reasoning}</p>
        </div>
    `;

    impactDiv.innerHTML = html;

    // Display AI summary
    document.getElementById('aiSummary').innerHTML = data.ai_summary;

    // Calculate sentiment statistics
    const totalArticles = data.articles.length;
    const positiveCount = (sentimentData.strongly_positive || 0) +
        (sentimentData.moderately_positive || 0) +
        (sentimentData.slightly_positive || 0);
    const negativeCount = (sentimentData.strongly_negative || 0) +
        (sentimentData.moderately_negative || 0) +
        (sentimentData.slightly_negative || 0);

    const positivePercent = totalArticles > 0 ? ((positiveCount / totalArticles) * 100).toFixed(1) : 0;
    const negativePercent = totalArticles > 0 ? ((negativeCount / totalArticles) * 100).toFixed(1) : 0;



    // Display sentiment chart with all 6 intensity levels
    const chartData = [{
        values: [
            sentimentData.strongly_positive || 0,
            sentimentData.moderately_positive || 0,
            sentimentData.slightly_positive || 0,
            sentimentData.slightly_negative || 0,
            sentimentData.moderately_negative || 0,
            sentimentData.strongly_negative || 0
        ],
        labels: [
            'Strongly Positive',
            'Moderately Positive',
            'Slightly Positive',
            'Slightly Negative',
            'Moderately Negative',
            'Strongly Negative'
        ],
        type: 'pie',
        marker: {
            colors: [
                '#16c784',  // Strongly Positive - finviz green
                '#27ae60',  // Moderately Positive - emerald green
                '#58d68d',  // Slightly Positive - light green
                '#f39c12',  // Slightly Negative - orange
                '#e74c3c',  // Moderately Negative - red
                '#8b0000'   // Strongly Negative - dark red
            ]
        },
        textinfo: 'label+percent',
        textposition: 'outside',
        hovertemplate: '<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    }];

    Plotly.newPlot('sentimentChart', chartData, {
        margin: { t: 15, b: 50, l: 5, r: 5 }, /* Increased top margin to reveal labels */
        showlegend: false,
        font: { size: 10, color: '#e2e2e2' },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        autosize: true
    }, {
        responsive: true,
        displayModeBar: false
    });

    // Display Price Prediction
    displayPricePrediction(data, sentimentData);

    // Display Predicted Growth Graph
    if (data.forecast_data) {
        displayGrowthGraph(data.forecast_data, data.historical_data);
    } else {
        document.getElementById('growthGraphContainer').style.display = 'none';
    }

    // Display articles in grid
    const articlesDiv = document.getElementById('articlesList');
    articlesDiv.innerHTML = '';
    document.getElementById('articleCount').textContent = `${data.articles.length} articles`;

    data.articles.forEach(article => {
        const sentimentClass = `sentiment-${article.sentiment}`;
        // Map sentiment intensity levels to display with colors and labels
        const sentimentDisplay = {
            'strongly_positive': {
                icon: '<i class="fas fa-arrow-up"></i>',
                color: '#16c784',
                label: 'Strongly Positive',
                emoji: '📈'
            },
            'moderately_positive': {
                icon: '<i class="fas fa-arrow-up"></i>',
                color: '#27ae60',
                label: 'Moderately Positive',
                emoji: '↗️'
            },
            'slightly_positive': {
                icon: '<i class="fas fa-arrow-up"></i>',
                color: '#58d68d',
                label: 'Slightly Positive',
                emoji: '↗️'
            },
            'slightly_negative': {
                icon: '<i class="fas fa-arrow-down"></i>',
                color: '#f39c12',
                label: 'Slightly Negative',
                emoji: '↘️'
            },
            'moderately_negative': {
                icon: '<i class="fas fa-arrow-down"></i>',
                color: '#e74c3c',
                label: 'Moderately Negative',
                emoji: '↘️'
            },
            'strongly_negative': {
                icon: '<i class="fas fa-arrow-down"></i>',
                color: '#c2185b',
                label: 'Strongly Negative',
                emoji: '📉'
            },
            // Legacy support
            'positive': {
                icon: '<i class="fas fa-arrow-up"></i>',
                color: '#27ae60',
                label: 'Positive',
                emoji: '↗️'
            },
            'negative': {
                icon: '<i class="fas fa-arrow-down"></i>',
                color: '#dc3545',
                label: 'Negative',
                emoji: '↘️'
            },
            'mixed': {
                icon: '<i class="fas fa-minus"></i>',
                color: '#ffc107',
                label: 'Mixed',
                emoji: '➡️'
            }
        };

        const sentimentInfo = sentimentDisplay[article.sentiment] || sentimentDisplay['slightly_positive'];
        const sentimentIcon = sentimentInfo.icon;

        const articleCard = document.createElement('div');
        articleCard.className = 'card article-card';

        // Build summary HTML if available
        const summaryHTML = article.summary
            ? `<div class="article-summary">${article.summary}</div>`
            : '';

        articleCard.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-start mb-2">
                    <h6 class="card-title mb-0 flex-grow-1 me-2">${article.title}</h6>
                    <span class="sentiment-badge ${sentimentClass}" style="flex-shrink: 0; font-size: 0.7rem; color: ${sentimentInfo.color}; font-weight: 600;" title="${sentimentInfo.label}">
                        ${sentimentIcon} ${sentimentInfo.emoji}
                    </span>
                </div>
                ${summaryHTML}
                <div class="mb-2">
                    <small class="text-muted d-block">
                        <i class="fas fa-calendar"></i> ${article.published}
                    </small>
                    <small class="text-muted">
                        <i class="fas fa-newspaper"></i> ${article.source}
                    </small>
                </div>
                <div class="d-flex justify-content-between align-items-center">
                    <small class="text-muted">Score: ${(article.sentiment_score * 100).toFixed(0)}%</small>
                    <a href="${article.link}" target="_blank" class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </div>
            </div>
        `;
        articlesDiv.appendChild(articleCard);
    });

    document.getElementById('results').style.display = 'block';
    const downloadBtn = document.getElementById('downloadReportBtn');
    if (downloadBtn) {
        downloadBtn.style.display = 'inline-block';
    }
}

function showError(message) {
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function showQnaError(message) {
    const errorDiv = document.getElementById('qnaError');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function displayPricePrediction(data, sentimentData) {
    const container = document.getElementById('pricePredictionContainer');

    // Need current price to make predictions
    if (!data.stock_data || !data.stock_data.current_price) {
        container.style.display = 'none';
        return;
    }

    const currentPrice = data.stock_data.current_price;
    document.getElementById('predCurrentPrice').textContent = '$' + currentPrice.toFixed(2);

    // Use combined prediction from backend
    let prediction = null;
    if (data.impact_prediction && data.impact_prediction.combined) {
        prediction = data.impact_prediction.combined;
    } else if (data.impact_prediction && data.impact_prediction.rule_based) {
        prediction = data.impact_prediction.rule_based;
    } else {
        // Fallback for legacy format
        prediction = data.impact_prediction;
    }

    if (!prediction) {
        container.style.display = 'none';
        return;
    }

    // Map prediction label to percentage movement (Simulation)
    // Max movement +/- 5% for 7 days
    const maxMovePercent = 5.0;
    let predictedMovePercent = 0;

    if (prediction.score !== undefined) {
        // Use the continuous score from backend (-3 to +3 range approx)
        // Normalize: Score 3 = 100% intensity
        // We cap it at 3.0 for normalization
        let normalizedScore = prediction.score / 3.0;
        // Clamp to -1 to 1
        normalizedScore = Math.max(-1, Math.min(1, normalizedScore));

        predictedMovePercent = normalizedScore * maxMovePercent;
    } else {
        // Fallback to label mapping if score not available
        const predictionMap = {
            'strongly_positive': 1.0,
            'moderately_positive': 0.6,
            'slightly_positive': 0.3,
            'neutral': 0,
            'slightly_negative': -0.3,
            'moderately_negative': -0.6,
            'strongly_negative': -1.0,
            // Legacy
            'positive': 0.6,
            'negative': -0.6,
            'mixed': 0
        };

        const intensity = predictionMap[prediction.prediction] || 0;
        predictedMovePercent = intensity * maxMovePercent;
    }

    // Calculate target range (Predicted +/- 1.5%)
    const spread = 1.5;
    const minMove = predictedMovePercent - (spread / 2);
    const maxMove = predictedMovePercent + (spread / 2);

    const targetLow = currentPrice * (1 + (minMove / 100));
    const targetHigh = currentPrice * (1 + (maxMove / 100));

    // Update UI
    const targetRangeElem = document.getElementById('predTargetRange');
    targetRangeElem.textContent = `$${targetLow.toFixed(2)} - $${targetHigh.toFixed(2)}`;

    // Color coding
    if (predictedMovePercent > 0.5) {
        targetRangeElem.style.color = 'var(--finviz-green)';
    } else if (predictedMovePercent < -0.5) {
        targetRangeElem.style.color = 'var(--finviz-red)';
    } else {
        targetRangeElem.style.color = 'var(--finviz-text)';
    }

    // Update Gauge
    const gaugeBar = document.getElementById('predGaugeBar');
    const gaugeMarker = document.getElementById('predGaugeMarker');

    // Map -5% to +5% range to 0-100% width
    // 0% move = 50% width
    let gaugePercent = 50 + (predictedMovePercent * 10); // 5% * 10 = 50, so 50+50=100%
    gaugePercent = Math.max(5, Math.min(95, gaugePercent)); // Clamp between 5% and 95%

    gaugeMarker.style.left = `${gaugePercent}%`;

    // Bar styling
    if (predictedMovePercent >= 0) {
        gaugeBar.style.width = `${gaugePercent}%`;
        gaugeBar.style.backgroundColor = 'rgba(22, 199, 132, 0.3)'; // Green background
        gaugeBar.style.borderRight = '2px solid var(--finviz-green)';
        gaugeBar.innerHTML = `<span style="margin-right: 5px; color: var(--finviz-green);">+${predictedMovePercent.toFixed(2)}%</span>`;
    } else {
        // For negative, we want the bar to grow from right to left (visual trick)
        // But simpler to just set width and color
        gaugeBar.style.width = `${gaugePercent}%`;
        gaugeBar.style.backgroundColor = 'rgba(234, 57, 67, 0.3)'; // Red background
        gaugeBar.style.borderRight = '2px solid var(--finviz-red)';
        gaugeBar.innerHTML = `<span style="margin-right: 5px; color: var(--finviz-red);">${predictedMovePercent.toFixed(2)}%</span>`;
    }

    // Confidence from backend
    let confidence = prediction.confidence || 0;
    document.getElementById('predConfidence').textContent = `Confidence: ${(confidence * 100).toFixed(2)}%`;

    container.style.display = 'block';
}

function displayGrowthGraph(forecastData, historicalData) {
    const container = document.getElementById('growthGraphContainer');
    if (!forecastData || !forecastData.prices || forecastData.prices.length === 0) {
        container.style.display = 'none';
        return;
    }

    container.style.display = 'block';

    // Prepare traces
    const traces = [];

    // 1. Historical Data Trace
    if (historicalData && historicalData.prices && historicalData.prices.length > 0) {
        traces.push({
            x: historicalData.dates,
            y: historicalData.prices,
            type: 'scatter',
            mode: 'lines',
            line: {
                color: '#a1a7bb', // Grey for history
                width: 2
            },
            name: 'History'
        });
    }

    // 2. Predicted Data Trace
    // Determine color based on score if available, else trend
    let isPositive;
    if (forecastData.score !== undefined) {
        isPositive = forecastData.score >= 0;
    } else {
        const startPrice = forecastData.prices[0];
        const endPrice = forecastData.prices[forecastData.prices.length - 1];
        isPositive = endPrice >= startPrice;
    }

    const lineColor = isPositive ? '#16c784' : '#ea3943'; // Green or Red

    // Connect prediction to last historical point if available
    let predDates = forecastData.dates;
    let predPrices = forecastData.prices;

    if (historicalData && historicalData.prices.length > 0) {
        // Add the last historical point as the first point of prediction to ensure continuity
        predDates = [historicalData.dates[historicalData.dates.length - 1], ...forecastData.dates];
        predPrices = [historicalData.prices[historicalData.prices.length - 1], ...forecastData.prices];
    }

    traces.push({
        x: predDates,
        y: predPrices,
        type: 'scatter',
        mode: 'lines',
        line: {
            color: lineColor,
            width: 2,
            dash: 'dot' // Dotted line for prediction
        },
        name: 'Prediction'
    });

    // Add a vertical line to separate history and prediction
    const shapes = [];
    if (historicalData && historicalData.prices.length > 0) {
        const lastDate = historicalData.dates[historicalData.dates.length - 1];
        shapes.push({
            type: 'line',
            x0: lastDate,
            y0: 0,
            x1: lastDate,
            y1: 1,
            xref: 'x',
            yref: 'paper',
            line: {
                color: 'rgba(255, 255, 255, 0.2)',
                width: 1,
                dash: 'dot'
            }
        });
    }

    const layout = {
        margin: { t: 40, b: 40, l: 60, r: 30 },
        showlegend: true,
        legend: {
            x: 0.5,
            xanchor: 'center',
            y: 1.1,
            orientation: 'h',
            font: { color: '#a1a7bb' }
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        xaxis: {
            showgrid: false,
            color: '#a1a7bb',
            tickfont: { size: 10 },
            gridcolor: '#2a2e39'
        },
        yaxis: {
            showgrid: true,
            gridcolor: '#2a2e39',
            color: '#a1a7bb',
            tickfont: { size: 10 },
            tickprefix: '$'
        },
        shapes: shapes,
        autosize: true,
        hovermode: 'x unified'
    };

    Plotly.newPlot('growthChart', traces, layout, {
        responsive: true,
        displayModeBar: false
    }).then(function () {
        Plotly.Plots.resize('growthChart');
    });
}

// Smooth scroll to results when they appear
const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
        if (mutation.type === 'attributes' && mutation.attributeName === 'style') {
            const results = document.getElementById('results');
            if (results.style.display === 'block') {
                setTimeout(() => {
                    results.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }, 100);
            }
        }
    });
});
observer.observe(document.getElementById('results'), { attributes: true });

// Add these helper functions:
async function refreshWatchlist() {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;

    await loadWatchlist();

    setTimeout(() => {
        btn.innerHTML = originalHTML;
        btn.disabled = false;

        // Show success message
        const toast = document.createElement('div');
        toast.className = 'alert alert-success alert-dismissible fade show';
        toast.style.position = 'fixed';
        toast.style.top = '20px';
        toast.style.right = '20px';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            <strong><i class="fas fa-check-circle"></i> Watchlist refreshed!</strong>
            <button type="button" class="btn-close btn-close-white" onclick="this.parentElement.remove()"></button>
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }, 500);
}

async function clearWatchlist() {
    if (!confirm('Are you sure you want to clear your entire watchlist? This action cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch('/watchlist/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        if (response.ok) {
            await loadWatchlist();

            // Show success message
            const toast = document.createElement('div');
            toast.className = 'alert alert-success alert-dismissible fade show';
            toast.style.position = 'fixed';
            toast.style.top = '20px';
            toast.style.right = '20px';
            toast.style.zIndex = '9999';
            toast.innerHTML = `
                <strong><i class="fas fa-check-circle"></i> Watchlist cleared!</strong>
                <button type="button" class="btn-close btn-close-white" onclick="this.parentElement.remove()"></button>
            `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        } else {
            alert('Failed to clear watchlist');
        }
    } catch (e) {
        console.error("Error clearing watchlist:", e);
        alert('Error clearing watchlist');
    }
}

// Update the removeFromWatchlist function to show a toast notification:
async function removeFromWatchlist(ticker) {
    if (!confirm(`Remove ${ticker} from watchlist?`)) return;

    try {
        const response = await fetch('/watchlist/remove', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ ticker: ticker })
        });

        if (response.ok) {
            await loadWatchlist();

            // Show success message
            const toast = document.createElement('div');
            toast.className = 'alert alert-success alert-dismissible fade show';
            toast.style.position = 'fixed';
            toast.style.top = '20px';
            toast.style.right = '20px';
            toast.style.zIndex = '9999';
            toast.innerHTML = `
                    <strong><i class="fas fa-check-circle"></i> ${ticker} removed from watchlist</strong>
                    <button type="button" class="btn-close btn-close-white" onclick="this.parentElement.remove()"></button>
                `;
            document.body.appendChild(toast);
            setTimeout(() => toast.remove(), 3000);
        } else {
            alert("Failed to remove item");
        }
    } catch (e) {
        console.error("Error removing item:", e);
        alert("Error removing item");
    }

}
document.addEventListener("DOMContentLoaded", () => {
    hideDownloadButton();
});
