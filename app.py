from flask import Flask, render_template, request, jsonify
import os
import sys
from dotenv import load_dotenv
from news_fetcher import NewsFetcher
from sentiment_analyzer import SentimentAnalyzer
from ai_agent import AIAgent
from impact_predictor import ImpactPredictor
from database_manager import DatabaseManager
from rag_handler import RAGHandler
import yfinance as yf
import requests 
from bs4 import BeautifulSoup
import datetime

# Fix Unicode encoding for Windows console to support emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()


app = Flask(__name__)

db_manager = DatabaseManager()
news_fetcher = NewsFetcher()
sentiment_analyzer = SentimentAnalyzer()
ai_agent = AIAgent()
impact_predictor = ImpactPredictor(db_manager=db_manager, use_ml=True)
rag_handler = RAGHandler(db_manager)

def initialize_components():
    """Initializes all application components and database."""
    print("Initializing application components...")
    # These components are initialized globally, but their heavy lifting (like model loading)
    # might be triggered upon first use or within their constructors.
    # The key is to ensure any *side effects* or expensive one-time setups
    # are handled carefully, especially with Flask's reloader.
    
    # Create database tables if they don't exist
    db_manager.create_table()
    db_manager.create_ml_tables()  # Create ML dataset and model tables
    db_manager.create_watchlist_table() # Create Watchlist table
    print("Application components initialized.")

@app.route('/')
def index():
    return render_template('index.html')


def _get_fallback_stock_data(ticker):
    """Fallback with all required fields"""
    return {
        'current_price': 0,
        'price_change': 0,
        'price_change_percent': 0,
        'volume': 0,
        'day_high': 0,
        'day_low': 0,
        'prev_close': 0,
        'exchange': 'N/A'
    }

def get_stock_data(ticker):
    """
    Get stock data from Yahoo Finance Chart API with reliable metrics
    """
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            return _get_fallback_stock_data(ticker)
        
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            return _get_fallback_stock_data(ticker)
        
        result = data['chart']['result'][0]
        meta = result['meta']
        
        current_price = meta.get('regularMarketPrice', 0)
        prev_close = meta.get('previousClose', current_price)
        price_change = current_price - prev_close
        price_change_percent = (price_change / prev_close) * 100 if prev_close else 0
        
        # Get exchange information
        exchange_name = meta.get('exchangeName', '')
        exchange_code = meta.get('exchange', '')
        
        # Comprehensive exchange mapping
        exchange_mapping = {
            # US Exchanges
            'NMS': 'NASDAQ',
            'NASDAQ': 'NASDAQ',
            'NYQ': 'NYSE',
            'NYSE': 'NYSE',
            'ASE': 'NYSE American',
            'BATS': 'BATS',
            'PCX': 'NYSE Arca',
            'AMEX': 'NYSE American',
            'ARCA': 'NYSE Arca',
            'IEXG': 'IEX',
            
            # Canadian Exchanges
            'TOR': 'TSX',
            'TSX': 'TSX',
            'VAN': 'TSXV',
            'TSXV': 'TSXV',
            'CVE': 'CVE',
            'CNQ': 'CSE',
            'MEX': 'MX',
            
            # Indian Exchanges
            'NSI': 'NSE',
            'NSE': 'NSE',
            'BSE': 'BSE',
            'BOM': 'BSE',
            'NSC': 'NSE',
            'BSC': 'BSE',
            
            # UK Exchanges
            'LSE': 'LSE',
            'LON': 'LSE',
            'IOB': 'LSE',
            'PLU': 'LSE',
            
            # European Exchanges
            'GER': 'XETRA',
            'FRA': 'XETRA',
            'ETR': 'XETRA',
            'XETRA': 'XETRA',
            'AMS': 'Euronext Amsterdam',
            'EPA': 'Euronext Paris',
            'EBR': 'Euronext Brussels',
            'ELI': 'Euronext Lisbon',
            'MLS': 'Euronext Milan',
            'OSL': 'Oslo Bors',
            'STO': 'Nasdaq Stockholm',
            'CPH': 'Nasdaq Copenhagen',
            'HEL': 'Nasdaq Helsinki',
            'ICE': 'Nasdaq Iceland',
            'VIE': 'Vienna Stock Exchange',
            'SWX': 'SIX Swiss Exchange',
            'MCE': 'BME Spanish Exchanges',
            'MAD': 'BME Spanish Exchanges',
            'WSE': 'Warsaw Stock Exchange',
            
            # Asian Exchanges
            'TSE': 'TSE',
            'TYO': 'TSE',
            'OSE': 'OSE',
            'FKA': 'Fukuoka Stock Exchange',
            'SAP': 'Sapporo Stock Exchange',
            'HKG': 'HKEX',
            'HKEX': 'HKEX',
            'SHE': 'SZSE',
            'SZSE': 'SZSE',
            'SHG': 'SSE',
            'SSE': 'SSE',
            'SHH': 'SSE',
            'TAI': 'TWSE',
            'TWSE': 'TWSE',
            'KSC': 'KRX',
            'KRX': 'KRX',
            'SES': 'SGX',
            'SGX': 'SGX',
            'ASX': 'ASX',
            'AXS': 'ASX',
            'NZE': 'NZX',
            'NZX': 'NZX',
            'BKK': 'SET',
            'SET': 'SET',
            'JKT': 'IDX',
            'IDX': 'IDX',
            'KLS': 'Bursa Malaysia',
            'KLSE': 'Bursa Malaysia',
            
            # Australian Exchanges
            'ASX': 'ASX',
            'AXS': 'ASX',
            'CHIA': 'Chi-X Australia',
            
            # Middle Eastern Exchanges
            'TADAWUL': 'Tadawul',
            'DFM': 'DFM',
            'ADX': 'ADX',
            'QSE': 'QSE',
            
            # African Exchanges
            'JSE': 'JSE',
            'JNB': 'JSE',
            
            # South American Exchanges
            'BUE': 'BYMA',
            'SAO': 'B3',
            'BOV': 'B3',
            'BVR': 'B3',
        }
        
        # Determine exchange display name
        exchange_display = 'N/A'
        
        # First try exchange code mapping
        if exchange_code and exchange_code in exchange_mapping:
            exchange_display = exchange_mapping[exchange_code]
        # Then try exchange name mapping
        elif exchange_name:
            # Check if any known exchange is in the name
            for key, value in exchange_mapping.items():
                if key in exchange_name.upper():
                    exchange_display = value
                    break
            else:
                # Use the exchange name as is, but shorten if too long
                if len(exchange_name) > 15:
                    exchange_display = exchange_name[:15] + '...'
                else:
                    exchange_display = exchange_name
        
        # Special cases for well-known international companies
        special_cases = {
            'INFY': 'NSE (ADR)',
            'TCS': 'NSE (ADR)',
            'RELIANCE': 'NSE (ADR)',
            'HDB': 'NSE (ADR)',
            'IBN': 'NSE (ADR)',
            'TTM': 'NSE (ADR)',
            'BABA': 'NYSE (HKEX ADR)',
            'JD': 'NASDAQ (HKEX ADR)',
            'BIDU': 'NASDAQ (HKEX ADR)',
            'TSM': 'NYSE (TWSE ADR)',
            'SNE': 'NYSE (TSE ADR)',
            'TM': 'NYSE (TSE ADR)',
        }
        
        if ticker.upper() in special_cases:
            exchange_display = special_cases[ticker.upper()]
        
        # These are reliably available from chart API
        stock_data = {
            'current_price': round(current_price, 2),
            'price_change': round(price_change, 2),
            'price_change_percent': round(price_change_percent, 2),
            'volume': meta.get('regularMarketVolume', 0),
            'day_high': meta.get('regularMarketDayHigh', 0),
            'day_low': meta.get('regularMarketDayLow', 0),
            'prev_close': prev_close,
            'exchange': exchange_display
        }
        
        print(f"✅ {ticker}: ${stock_data['current_price']} ({stock_data['price_change_percent']:+.2f}%) - Exchange: {exchange_display}")
        return stock_data
        
    except Exception as e:
        print(f"❌ Error fetching {ticker}: {str(e)}")
        return _get_fallback_stock_data(ticker)

def get_historical_data(ticker, period='1mo'):
    """
    Get historical stock data using Yahoo Finance Chart API directly.
    Returns a dictionary with dates and prices.
    """
    try:
        print(f"Fetching historical data for {ticker}...")
        # Map period to range
        range_map = {
            '1mo': '1mo',
            '3mo': '3mo',
            '6mo': '6mo',
            '1y': '1y'
        }
        range_val = range_map.get(period, '1mo')
        
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?range={range_val}&interval=1d"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Failed to fetch historical data: Status {response.status_code}")
            return None
            
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            print("Invalid response format from Yahoo Finance")
            return None
            
        result = data['chart']['result'][0]
        
        if 'timestamp' not in result or 'indicators' not in result:
            print("No timestamp or indicators in response")
            return None
            
        timestamps = result['timestamp']
        quotes = result['indicators']['quote'][0]
        
        if 'close' not in quotes:
            print("No close prices in response")
            return None
            
        close_prices = quotes['close']
        
        # Filter out None values (can happen with missing data)
        dates = []
        prices = []
        
        for ts, price in zip(timestamps, close_prices):
            if price is not None:
                date_str = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d')
                dates.append(date_str)
                prices.append(round(price, 2))
                
        print(f"✅ Fetched {len(prices)} historical data points for {ticker}")
        
        return {
            'dates': dates,
            'prices': prices
        }
    except Exception as e:
        print(f"Error fetching historical data: {str(e)}")
        return None

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json
        ticker = data.get('ticker', '').upper()
        company_name = data.get('company_name', '')
        timeframe = data.get('timeframe', '7d')  # Default to 7 days
        
        if not ticker and not company_name:
            return jsonify({'error': 'Please provide either a ticker or company name'}), 400
        
        # Validate timeframe
        valid_timeframes = ['24h', '7d', '30d', 'all']
        if timeframe not in valid_timeframes:
            timeframe = '7d'  # Default to 7 days if invalid
        
        # If only company name is provided, try to find the ticker
        if not ticker and company_name:
            print(f"Attempting to find ticker for company: {company_name}...")
            # Use the news_fetcher's internal method for ticker lookup
            found_ticker = news_fetcher._get_ticker_from_company_name(company_name)
            if found_ticker:
                ticker = found_ticker
                print(f"Found ticker: {ticker} for {company_name}")
            else:
                print(f"Could not find ticker for company: {company_name}")
                return jsonify({'error': f'Could not find a stock ticker for "{company_name}". Please try again or provide a ticker.'}), 404
        
        stock_data = None
        if ticker: # Ensure ticker is available before fetching stock data
            print(f"Fetching stock data for {ticker}...")
            stock_data = get_stock_data(ticker)
            if stock_data:
                print(f"Stock data fetched: ${stock_data['current_price']} ({stock_data['price_change_percent']}%)")
            else:
                print(f"Could not fetch stock data for {ticker}")

        # Fetch news from Finviz
        # Pass the (potentially newly found) ticker and the original company name
        print(f"Fetching news for {ticker} (company name: {company_name}, timeframe: {timeframe})...")
        news_articles = news_fetcher.fetch_news(ticker=ticker, company_name=company_name, timeframe=timeframe)
        
        # For longer timeframes, supplement with historical articles from database
        if timeframe in ['30d', '7d'] and len(news_articles) < 10:
            days = 30 if timeframe == '30d' else 7
            print(f"Supplementing with historical articles from database (last {days} days)...")
            historical_articles = db_manager.get_historical_articles(ticker or company_name, days)
            
            if historical_articles:
                # Merge with current articles, avoiding duplicates
                current_titles = {a.get('title', '').lower() for a in news_articles}
                for hist_article in historical_articles:
                    if hist_article.get('title', '').lower() not in current_titles:
                        news_articles.append(hist_article)
                
                print(f"Added {len(historical_articles)} historical articles from database. Total: {len(news_articles)}")
        
        if not news_articles:
            # Provide more helpful error message based on timeframe
            if timeframe in ['30d', '7d']:
                error_msg = f'No news articles found for the selected time period ({timeframe}). Finviz typically only shows articles from the last few days. Try "Last 24 Hours" or "All Available".'
            else:
                error_msg = 'No news articles found. Please try a different ticker or company name.'
            return jsonify({'error': error_msg}), 404
        
        # Analyze sentiment for each article
        # Use summary if available and not generic, otherwise use title
        print("Analyzing sentiment...")
        analyzed_articles = []
        for article in news_articles:
            # Use summary if available and not generic, otherwise fall back to title
            summary = article.get('summary', '')
            if summary and not news_fetcher._is_generic_summary(summary):
                text_for_sentiment = summary
            else:
                text_for_sentiment = article.get('title', '')
            
            sentiment_result = sentiment_analyzer.analyze(text_for_sentiment)
            article['sentiment'] = sentiment_result['label']
            article['sentiment_score'] = sentiment_result['score']
            analyzed_articles.append(article)
        
        # Get AI reasoning and overall summary
        print("Generating AI insights...")
        context = rag_handler.get_context(ticker or company_name, analyzed_articles)
        ai_summary = ai_agent.generate_summary(analyzed_articles, ticker or company_name, context)
        
        # Predict impact
        print("Predicting impact...")
        impact_prediction = impact_predictor.predict(analyzed_articles)
        
        # Generate forecast if stock data is available
        forecast_data = None
        if stock_data and 'current_price' in stock_data:
            print("Generating price forecast...")
            # Use combined prediction if available, else rule-based
            pred_to_use = impact_prediction.get('combined') or impact_prediction.get('rule_based')
            forecast_data = impact_predictor.generate_forecast(
                stock_data['current_price'], 
                pred_to_use
            )
            
        # Fetch historical data
        historical_data = None
        if ticker:
            historical_data = get_historical_data(ticker)

        # Save to database
        print("Saving analysis to database...")
        analysis_id = db_manager.save_analysis(ticker or company_name, ai_summary)
        
        # Save individual articles to the database
        db_manager.save_articles(analysis_id, analyzed_articles)

        # Calculate sentiment distribution by all 6 intensity levels
        sentiment_dist = {
            'strongly_positive': sum(1 for a in analyzed_articles if a.get('sentiment') == 'strongly_positive'),
            'moderately_positive': sum(1 for a in analyzed_articles if a.get('sentiment') == 'moderately_positive'),
            'slightly_positive': sum(1 for a in analyzed_articles if a.get('sentiment') == 'slightly_positive'),
            'slightly_negative': sum(1 for a in analyzed_articles if a.get('sentiment') == 'slightly_negative'),
            'moderately_negative': sum(1 for a in analyzed_articles if a.get('sentiment') == 'moderately_negative'),
            'strongly_negative': sum(1 for a in analyzed_articles if a.get('sentiment') == 'strongly_negative')
        }
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'company_name': company_name,
            'timeframe': timeframe,
            'articles': analyzed_articles,
            'sentiment_distribution': sentiment_dist,
            'ai_summary': ai_summary,
            'impact_prediction': impact_prediction,
            'stock_data': stock_data,
            'forecast_data': forecast_data,
            'historical_data': historical_data
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/ask', methods=['POST'])
def ask():
    try:
        data = request.json
        question = data.get('question')
        if not question:
            return jsonify({'error': 'Please provide a question.'}), 400

        print(f"Answering question: {question}")
        answer = rag_handler.answer_question(question)
        
        return jsonify({'answer': answer})
    except Exception as e:
        print(f"Error in /ask: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/lookup-ticker', methods=['POST'])
def lookup_ticker():
    """Lookup ticker symbol from company name."""
    try:
        data = request.json
        company_name = data.get('company_name', '').strip()
        
        if not company_name:
            return jsonify({'error': 'Please provide a company name.'}), 400
        
        ticker = news_fetcher._get_ticker_from_company_name(company_name)
        
        if ticker:
            return jsonify({'ticker': ticker, 'company_name': company_name})
        else:
            return jsonify({'error': f'Could not find ticker for "{company_name}"'}), 404
            
    except Exception as e:
        print(f"Error in /lookup-ticker: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/lookup-company', methods=['POST'])
def lookup_company():
    """Lookup company name from ticker symbol."""
    try:
        data = request.json
        ticker = data.get('ticker', '').strip().upper()
        
        if not ticker:
            return jsonify({'error': 'Please provide a ticker symbol.'}), 400
        
        company_name = news_fetcher.get_company_name_from_ticker(ticker)
        
        if company_name:
            return jsonify({'ticker': ticker, 'company_name': company_name})
        else:
            return jsonify({'error': f'Could not find company name for ticker "{ticker}"'}), 404
            
    except Exception as e:
        print(f"Error in /lookup-company: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/watchlist/add', methods=['POST'])
def add_to_watchlist():
    try:
        data = request.json
        ticker = data.get('ticker')
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
            
        success = db_manager.add_to_watchlist(
            ticker=ticker,
            company_name=data.get('company_name', ''),
            price=data.get('price', 0),
            predicted_target_range=data.get('predicted_target_range', 'N/A'),
            recommendation=data.get('recommendation', 'N/A'),
            summary=data.get('summary', '')
        )
        
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Failed to add to watchlist'}), 500
            
    except Exception as e:
        print(f"Error in /watchlist/add: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/watchlist/get', methods=['GET'])
def get_watchlist():
    try:
        watchlist = db_manager.get_watchlist()
        return jsonify({'watchlist': watchlist})
    except Exception as e:
        print(f"Error in /watchlist/get: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/watchlist/remove', methods=['POST'])
def remove_from_watchlist():
    try:
        data = request.json
        ticker = data.get('ticker')
        if not ticker:
            return jsonify({'error': 'Ticker is required'}), 400
            
        db_manager.remove_from_watchlist(ticker)
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error in /watchlist/remove: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Common words that look like tickers but aren't
COMMON_TICKER_STOPWORDS = {
    'THE', 'AND', 'FOR', 'OF', 'IN', 'AT', 'TO', 'MY', 'IS', 'ON', 'OR', 'IT', 'BY', 'AS', 'IF', 'NO',
    'US', 'UK', 'EU', 'UN', 'USA', 'UAE', 'CN', 'JP', 'DE', 'FR', 'CA', 'AU',
    'CEO', 'CFO', 'CTO', 'COO', 'VP', 'SVP', 'EVP', 'MD', 'PM', 'GM',
    'IPO', 'ETF', 'SPAC', 'REIT', 'ADR', 'OTC', 'LLC', 'INC', 'LTD', 'PLC', 'CORP',
    'FDA', 'SEC', 'FED', 'CPI', 'GDP', 'FOMC', 'ECB', 'IMF', 'WHO', 'DOJ', 'FTC', 'EPA',
    'AI', 'EV', 'VR', 'AR', 'IOT', 'SAAS', 'PAAS', 'IAAS', 'API', 'LLM', 'PC', 'TV', 'IT', '5G', '6G',
    'USD', 'EUR', 'GBP', 'JPY', 'CNY', 'CAD', 'AUD', 'INR', 'RUB', 'BRL', 'ZAR',
    'YOY', 'QOQ', 'MOM', 'YTD', 'ATH', 'ATL', 'EPS', 'PE',
    'BUY', 'SELL', 'HOLD', 'RATING', 'TARGET', 'PRICE', 'STOCK', 'MARKET', 'NEWS', 'DEAL', 'DATA', 'TECH',
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
    'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN',
    'AM', 'PM', 'EST', 'PST', 'CST', 'MST', 'GMT', 'UTC',
    'NEW', 'OLD', 'BIG', 'SMALL', 'GOOD', 'BAD', 'HIGH', 'LOW', 'TOP', 'HOT', 'RED', 'BLUE',
    'ONE', 'TWO', 'SIX', 'TEN', 'ALL', 'OUT', 'UP', 'DOWN',
    'NOW', 'TODAY', 'WEEK', 'YEAR', 'DAY', 'HOUR', 'MIN',
    'COVID', 'VIRUS', 'WAR', 'DEBT', 'RATE', 'TAX', 'JOBS', 'SAYS', 'WILL', 'HAS', 'HAVE', 'HAD', 'BE', 'BEEN',
    'WHY', 'HOW', 'WHAT', 'WHEN', 'WHERE', 'WHO', 'WHICH', 'THAT', 'THIS', 'THESE', 'THOSE',
    'NEAR', 'FAR', 'FAST', 'SLOW', 'BEST', 'WORST', 'MOST', 'LEAST', 'MORE', 'LESS',
    'META', 'XY', 'ABC', 'XYZ', 'WOW', 'LOL', 'OMG', 'WTF', 'RIP', 'AKA', 'TBA', 'TBD',
    'Q1', 'Q2', 'Q3', 'Q4', 'H1', 'H2', 'FY', 'CY',
    'AGI', 'GPU', 'CPU', 'RAM', 'SSD', 'HDD', 'OS', 'UI', 'UX',
    'FED', 'RATES', 'CUT', 'HIKE', 'PAUSE', 'BANK', 'CASH', 'GOLD', 'OIL', 'GAS'
}

@app.route('/market-news', methods=['GET'])
def market_news():
    """
    Get general market news, analyze sentiment, and recommend stocks.
    """
    try:
        # 1. Fetch general market news
        print("Fetching general market news...")
        # Use a higher limit to get enough data for recommendations
        articles = news_fetcher.fetch_general_market_news(max_results=40)
        
        if not articles:
            return jsonify({'articles': [], 'trending_stocks': []})
            
        # 2. Analyze sentiment and extract tickers
        print("Analyzing market news sentiment...")
        analyzed_articles = []
        ticker_mentions = {}
        
        # Helper to extract potential tickers
        import re
        def extract_tickers(text):
            # Look for 2-5 letter all-caps words. 
            # Exclusion: words in parenthesis like (AAPL) are high confidence.
            # Plain words like AAPL are lower confidence but we'll take them if they aren't stopwords.
            
            found = set()
            
            # High confidence: (TICKER)
            parenthesis = re.findall(r'\(([A-Z]{2,5})\)', text)
            found.update(parenthesis)
            
            # Medium confidence: Capitalized words
            # We skip this if we found parenthesis tickers, to allow "Apple (AAPL)" to just count as AAPL
            # But sometimes "NVIDIA" is mentioned without (NVDA).
            # So we look for known big tech names or just candidate tokens.
            # For simplicity in this iteration, let's stick to strict-ish uppercase detection
            
            words = re.findall(r'\b[A-Z]{2,5}\b', text)
            for w in words:
                if w not in COMMON_TICKER_STOPWORDS and w not in found:
                    # Additional check: ensure it's not a common English word if possible? 
                    # For now rely on the stopword list.
                    found.add(w)
            
            return list(found)

        for article in articles:
            text = f"{article.get('title', '')} {article.get('summary', '') or ''}"
            
            # Sentiment Analysis
            sentiment_result = sentiment_analyzer.analyze(text)
            article['sentiment'] = sentiment_result['label']
            article['sentiment_score'] = sentiment_result['score']
            analyzed_articles.append(article)
            
            # Ticker Extraction
            tickers = extract_tickers(text)
            for ticker in tickers:
                if ticker not in ticker_mentions:
                    ticker_mentions[ticker] = {
                        'count': 0,
                        'sentiment_score_sum': 0,
                        'titles': [],
                        'latest_price': 'N/A' # We will fetch this later for top ones
                    }
                ticker_mentions[ticker]['count'] += 1
                ticker_mentions[ticker]['sentiment_score_sum'] += sentiment_result['score']
                ticker_mentions[ticker]['titles'].append(article.get('title'))
        
        # 3. Identify Trending/Recommended Stocks
        trending_stocks = []
        
        for ticker, data in ticker_mentions.items():
            # Only consider meaningful mentions
            # If we want really good recommendations, maybe fetch price data for validity check
            # For now, let's just use the score.
            
            avg_score = data['sentiment_score_sum'] / data['count']
            
            # Granular 6-level Classification (no neutral)
            if avg_score >= 0.6:
                classification = 'strongly_positive'
                sentiment_label = 'Strongly Positive'
            elif avg_score >= 0.3:
                classification = 'moderately_positive'
                sentiment_label = 'Moderately Positive'
            elif avg_score >= 0:
                classification = 'slightly_positive'
                sentiment_label = 'Slightly Positive'
            elif avg_score >= -0.3:
                classification = 'slightly_negative'
                sentiment_label = 'Slightly Negative'
            elif avg_score >= -0.6:
                classification = 'moderately_negative'
                sentiment_label = 'Moderately Negative'
            else:
                classification = 'strongly_negative'
                sentiment_label = 'Strongly Negative'
            
            trending_stocks.append({
                'ticker': ticker,
                'mention_count': data['count'],
                'avg_sentiment_score': round(avg_score, 2),
                'sentiment_label': sentiment_label,
                'classification': classification,
                'headline': data['titles'][0] if data['titles'] else ''
            })
            
        # Sort by relevance (count) and then magnitude of sentiment
        trending_stocks.sort(key=lambda x: (x['mention_count'], abs(x['avg_sentiment_score'])), reverse=True)
        
        # Take top 20 and try to fetch current price for valid ones
        # This doubles as a validity check for the tickers
        final_trending = []
        for stock in trending_stocks[:20]:  # Increased from 10 to 20
            try:
                # Quick price check to verify it's a real stock
                price_data = get_stock_data(stock['ticker'])
                if price_data and price_data['current_price'] > 0:
                    stock.update(price_data)
                    final_trending.append(stock)
            except:
                continue
                
        return jsonify({
            'articles': analyzed_articles,
            'trending_stocks': final_trending
        })
        
    except Exception as e:
        print(f"Error in /market-news: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    initialize_components()
    app.run(debug=True, host='0.0.0.0', port=5000)
