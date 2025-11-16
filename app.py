
from flask import Flask, render_template, request, jsonify
import os
from dotenv import load_dotenv
from news_fetcher import NewsFetcher
from sentiment_analyzer import SentimentAnalyzer
from ai_agent import AIAgent
from impact_predictor import ImpactPredictor
from database_manager import DatabaseManager
from rag_handler import RAGHandler

load_dotenv()

app = Flask(__name__)

news_fetcher = NewsFetcher()
sentiment_analyzer = SentimentAnalyzer()
ai_agent = AIAgent()
impact_predictor = ImpactPredictor()
db_manager = DatabaseManager()
rag_handler = RAGHandler(db_manager)

def initialize_components():
    """Initializes all application components and database."""
    print("Initializing application components...")
    # These components are initialized globally, but their heavy lifting (like model loading)
    # might be triggered upon first use or within their constructors.
    # The key is to ensure any *side effects* or expensive one-time setups
    # are handled carefully, especially with Flask's reloader.
    
    # Create database table if it doesn't exist
    db_manager.create_table()
    print("Application components initialized.")

@app.route('/')
def index():
    return render_template('index.html')

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
        
        # Fetch news
        print(f"Fetching news for {ticker or company_name} (timeframe: {timeframe})...")
        news_articles = news_fetcher.fetch_news(ticker, company_name, timeframe)
        
        if not news_articles:
            return jsonify({'error': 'No news articles found. Please try a different ticker or company name.'}), 404
        
        # Analyze sentiment for each article
        # Use summary if available for better sentiment analysis, otherwise use title
        print("Analyzing sentiment...")
        analyzed_articles = []
        for article in news_articles:
            # Use summary if available (more context), otherwise fall back to title
            text_for_sentiment = article.get('summary') or article.get('title', '')
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

        # Calculate sentiment distribution
        sentiment_dist = {
            'positive': sum(1 for a in analyzed_articles if a['sentiment'] == 'positive'),
            'negative': sum(1 for a in analyzed_articles if a['sentiment'] == 'negative'),
            'mixed': sum(1 for a in analyzed_articles if a['sentiment'] == 'mixed'),
            'neutral': sum(1 for a in analyzed_articles if a['sentiment'] == 'neutral')
        }
        
        return jsonify({
            'success': True,
            'ticker': ticker,
            'company_name': company_name,
            'timeframe': timeframe,
            'articles': analyzed_articles,
            'sentiment_distribution': sentiment_dist,
            'ai_summary': ai_summary,
            'impact_prediction': impact_prediction
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

if __name__ == '__main__':
    initialize_components()
    app.run(debug=True, host='0.0.0.0', port=5000)
