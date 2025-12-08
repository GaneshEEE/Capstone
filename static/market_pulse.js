

// Store all data for filtering
window.allTrendingStocks = [];
window.allMarketNews = [];

async function loadMarketNews() {
    const loading = document.getElementById('marketNewsLoading');
    const trendingList = document.getElementById('trendingStocksList');
    const newsList = document.getElementById('marketNewsList');
    const emptyTrending = document.getElementById('trendingEmpty');

    loading.style.display = 'block';
    trendingList.innerHTML = '';
    newsList.innerHTML = '';
    emptyTrending.style.display = 'none';

    try {
        const response = await fetch('/market-news');
        const data = await response.json();

        window.marketNewsLoaded = true;
        window.allTrendingStocks = data.trending_stocks || [];
        window.allMarketNews = data.articles || [];

        // Render all stocks and news
        renderTrendingStocks(window.allTrendingStocks);
        renderMarketNews(window.allMarketNews);

    } catch (e) {
        console.error("Error loading market news:", e);
        trendingList.innerHTML = `<div class="alert alert-danger">Failed to load market news. Please try again.</div>`;
    } finally {
        loading.style.display = 'none';
    }
}

function renderTrendingStocks(stocks) {
    const trendingList = document.getElementById('trendingStocksList');
    const emptyTrending = document.getElementById('trendingEmpty');

    trendingList.innerHTML = '';

    if (stocks.length === 0) {
        emptyTrending.style.display = 'block';
        return;
    }

    emptyTrending.style.display = 'none';

    stocks.forEach(stock => {
        const badgeClass = `badge-${stock.classification.replace('_', '-')}`;
        const sentimentColor = stock.avg_sentiment_score >= 0 ? '#16c784' : '#ea3943';

        const card = document.createElement('div');
        card.className = 'card mb-2 shadow-sm';
        card.style.borderLeft = `4px solid ${sentimentColor}`;
        card.dataset.classification = stock.classification;

        card.innerHTML = `
            <div class="card-body p-2">
                <div class="d-flex justify-content-between align-items-start">
                    <div style="flex: 1;">
                        <h6 class="mb-1">
                            <span class="fw-bold" style="cursor: pointer;" onclick="analyzeFromWatchlist('${stock.ticker}', '')">
                                ${stock.ticker}
                            </span>
                        </h6>
                        <span class="badge ${badgeClass} mb-1" style="font-size: 0.7em;">
                            ${stock.sentiment_label}
                        </span>
                        ${stock.current_price ?
                `<div class="small text-muted mt-1">
                                $${stock.current_price} 
                                <span class="${stock.price_change_percent >= 0 ? 'text-success' : 'text-danger'}">
                                (${stock.price_change_percent >= 0 ? '+' : ''}${stock.price_change_percent}%)\n                                </span>
                             </div>` : ''}
                    </div>
                    <div class="text-end" style="min-width: 60px;">
                         <div style="color:${sentimentColor}; font-weight:bold; font-size:1.1em;">
                            ${Math.round(stock.avg_sentiment_score * 100)}%
                         </div>
                         <span class="small text-muted" style="font-size: 0.7em;">Score</span>
                    </div>
                </div>
                <p class="small mt-2 mb-0 text-muted fst-italic" style="font-size: 0.75em; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
                    "${stock.headline || 'No specific headline'}"
                </p>
            </div>
        `;
        trendingList.appendChild(card);
    });
}

function renderMarketNews(articles) {
    const newsList = document.getElementById('marketNewsList');
    newsList.innerHTML = '';

    articles.forEach(article => {
        const sentiment = article.sentiment || 'neutral';
        let sentimentBadge = 'secondary';
        let sentimentCategory = 'neutral';

        if (sentiment.includes('positive')) {
            sentimentBadge = 'success';
            sentimentCategory = 'positive';
        }
        if (sentiment.includes('negative')) {
            sentimentBadge = 'danger';
            sentimentCategory = 'negative';
        }

        const item = document.createElement('div');
        item.className = 'card mb-2 border-0 border-bottom';
        item.dataset.sentiment = sentimentCategory;

        let timeDisplay = article.published || 'Recent';

        item.innerHTML = `
            <div class="card-body p-2">
                <div class="d-flex justify-content-between">
                    <span class="badge bg-light text-dark border" style="font-size: 0.7em;">${article.source}</span>
                    <small class="text-muted" style="font-size: 0.7em;">${timeDisplay}</small>
                </div>
                <h6 class="mt-2 mb-1" style="font-size: 0.85em;">
                    <a href="${article.link}" target="_blank" class="text-decoration-none text-white">
                        ${article.title}
                    </a>
                </h6>
                <div class="mt-1">
                    <span class="badge bg-${sentimentBadge}" style="font-size: 0.65em;">${sentiment.replace('_', ' ')}</span>
                </div>
            </div>
        `;
        newsList.appendChild(item);
    });
}

function filterTrendingStocks(classification) {
    if (classification === 'all') {
        renderTrendingStocks(window.allTrendingStocks);
    } else if (classification === 'positive') {
        const filtered = window.allTrendingStocks.filter(s => s.classification.includes('positive'));
        renderTrendingStocks(filtered);
    } else if (classification === 'negative') {
        const filtered = window.allTrendingStocks.filter(s => s.classification.includes('negative'));
        renderTrendingStocks(filtered);
    }
}

function filterHeadlines(sentiment) {
    if (sentiment === 'all') {
        renderMarketNews(window.allMarketNews);
    } else if (sentiment === 'positive') {
        const filtered = window.allMarketNews.filter(a => {
            const articleSentiment = a.sentiment || '';
            return articleSentiment.includes('positive');
        });
        renderMarketNews(filtered);
    } else if (sentiment === 'negative') {
        const filtered = window.allMarketNews.filter(a => {
            const articleSentiment = a.sentiment || '';
            return articleSentiment.includes('negative');
        });
        renderMarketNews(filtered);
    }
}

// Override switchTab to handle market-pulse
(function () {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function (tabName) {
        const marketPulseSection = document.getElementById('market-pulse-section');
        const navMarketPulse = document.getElementById('nav-market-pulse');

        if (tabName === 'market-pulse') {
            // Hide all sections
            document.querySelector('.news-ticker').style.display = 'none';
            document.querySelector('.dashboard-header').style.display = 'none';
            document.getElementById('loading').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('results').style.display = 'none';
            document.getElementById('watchlist-section').style.display = 'none';

            // Show market pulse
            marketPulseSection.style.display = 'block';

            // Update nav
            document.getElementById('nav-home').classList.remove('active');
            document.getElementById('nav-watchlist').classList.remove('active');
            navMarketPulse.classList.add('active');

            // Load data if not loaded
            if (!window.marketNewsLoaded) {
                loadMarketNews();
            }
        } else {
            // Hide market pulse
            marketPulseSection.style.display = 'none';
            navMarketPulse && navMarketPulse.classList.remove('active');

            // Call original function
            if (originalSwitchTab) {
                originalSwitchTab(tabName);
            }
        }
    };
})();