
from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from news_fetcher import NewsFetcher
from sentiment_analyzer import SentimentAnalyzer
from ai_agent import AIAgent
from impact_predictor import ImpactPredictor
from database_manager import DatabaseManager
from rag_handler import RAGHandler
from sheets_manager import SheetsManager
import yfinance as yf
import requests 
from bs4 import BeautifulSoup

load_dotenv()

app = Flask(__name__)

db_manager = DatabaseManager()
news_fetcher = NewsFetcher()
sentiment_analyzer = SentimentAnalyzer()
ai_agent = AIAgent()
impact_predictor = ImpactPredictor(db_manager=db_manager, use_ml=True)
rag_handler = RAGHandler(db_manager)
sheets_manager = SheetsManager()

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
        
        stock_data = None
        if ticker:
            print(f"Fetching stock data for {ticker}...")
            stock_data = get_stock_data(ticker)
            if stock_data:
                print(f"Stock data fetched: ${stock_data['current_price']} ({stock_data['price_change_percent']}%)")
            else:
                print(f"Could not fetch stock data for {ticker}")

        # Fetch news from Finviz
        print(f"Fetching news for {ticker or company_name} (timeframe: {timeframe})...")
        news_articles = news_fetcher.fetch_news(ticker, company_name, timeframe)
        
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
            'stock_data': stock_data 
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

@app.route('/export-to-sheet', methods=['POST'])
def export_to_sheet():
    """
    Exports the current analysis of a specific ticker to the Google Sheet.
    """
    try:
        data = request.json
        sheet_name = data.get('sheet_name', 'Stock Watchlist')
        ticker = data.get('ticker')
        
        if not ticker:
            return jsonify({'error': 'No ticker provided.'}), 400
            
        ticker = ticker.upper()
        
        # Connect to sheets
        if not sheets_manager.connect():
            return jsonify({'error': 'Could not connect to Google Sheets. Please check credentials.json.'}), 500
            
        # Ensure headers exist
        sheets_manager.setup_sheet_headers(sheet_name)
        
        print(f"Exporting {ticker} to sheet '{sheet_name}'...")
        
        # 1. Get Stock Data
        stock_data = get_stock_data(ticker)
        
        # 2. Fetch News (Short timeframe)
        news_articles = news_fetcher.fetch_news(ticker=ticker, timeframe='24h')
        
        # 3. Analyze Sentiment
        analyzed_articles = []
        for article in news_articles:
            summary = article.get('summary', '')
            text_for_sentiment = summary if summary and not news_fetcher._is_generic_summary(summary) else article.get('title', '')
            sentiment_result = sentiment_analyzer.analyze(text_for_sentiment)
            article['sentiment'] = sentiment_result['label']
            article['sentiment_score'] = sentiment_result['score']
            analyzed_articles.append(article)
        
        # 4. Generate AI Summary
        context = f"Stock: {ticker}, Price: ${stock_data['current_price']}, Change: {stock_data['price_change_percent']}%"
        ai_summary = ai_agent.generate_summary(analyzed_articles, ticker, context)
        
        # Determine overall sentiment label
        if analyzed_articles:
            avg_score = sum(a['sentiment_score'] for a in analyzed_articles) / len(analyzed_articles)
            if avg_score > 0.15: overall_sentiment = "Positive"
            elif avg_score < -0.15: overall_sentiment = "Negative"
            else: overall_sentiment = "Neutral"
        else:
            overall_sentiment = "Neutral"
        
        # 5. Update Sheet
        update_data = {
            'price': stock_data['current_price'],
            'change_percent': stock_data['price_change_percent'],
            'sentiment': overall_sentiment,
            'summary': ai_summary
        }
        
        success = sheets_manager.add_or_update_row(sheet_name, ticker, update_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f"Successfully added {ticker} to '{sheet_name}'."
            })
        else:
            return jsonify({'error': f"Failed to update sheet for {ticker}."}), 500
        
    except Exception as e:
        print(f"Error in /export-to-sheet: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    initialize_components()
    app.run(debug=True, host='0.0.0.0', port=5000)
