# AI-Driven System for News-Based Stock Impact Prediction

An intelligent system that automatically collects, analyzes, and predicts the potential impact of financial news on stock performance using AI and NLP techniques.

## Features

- 🔄 **Automated News Collection**: Fetches real-time financial news from Google News RSS feeds and Finviz
- 🧠 **AI-Powered Sentiment Analysis**: Uses FinBERT (financial-domain language model) for accurate sentiment classification
- 🤖 **Intelligent Reasoning**: Leverages Google Gemini API via LangChain for contextual analysis and summarization
- 📊 **Impact Prediction**: Predicts likely stock movements (positive, negative, neutral) based on news sentiment
- 🌐 **Interactive Web Interface**: Beautiful Flask-based web application for easy interaction

## Tech Stack

- **Backend**: Flask (Python)
- **AI/NLP**: FinBERT (Hugging Face Transformers)
- **Agent Framework**: LangChain
- **LLM API**: Google Gemini API
- **Data Sources**: Google News RSS, Finviz
- **Frontend**: HTML, CSS, JavaScript, Bootstrap
- **Visualization**: Plotly

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Google Gemini API key (optional but recommended for AI reasoning)

## Installation

1. **Clone or download this repository**

2. **Create a virtual environment** (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**:
   - Copy `.env.example` to `.env`
   - Edit `.env` and add your Google Gemini API key:
   ```
   GOOGLE_GEMINI_API_KEY=your_actual_api_key_here
   ```

## Required APIs

### 1. Google Gemini API (Optional but Recommended)

**Purpose**: Provides intelligent reasoning and contextual summarization for news analysis.

**How to get it**:
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key and add it to your `.env` file

**Note**: The system will work without this API key, but AI reasoning features will be limited to basic summaries.

### 2. Google News RSS (Free - No API Key Required)

**Purpose**: Fetches real-time financial news articles.

**Status**: Public RSS feeds - no authentication needed.

### 3. Finviz (Free - No API Key Required)

**Purpose**: Additional source of financial news and stock information.

**Status**: Public website scraping - no authentication needed.

## Usage

1. **Start the Flask application**:
```bash
python app.py
```

2. **Open your browser** and navigate to:
```
http://localhost:5000
```

3. **Enter a stock ticker** (e.g., AAPL, MSFT, TSLA) or **company name** (e.g., Apple Inc)

4. **Click "Analyze"** to:
   - Fetch recent news articles
   - Analyze sentiment using FinBERT
   - Generate AI-powered insights
   - Predict stock impact

## Project Structure

```
capstone/
├── app.py                 # Flask application main file
├── news_fetcher.py        # News collection module
├── sentiment_analyzer.py  # FinBERT sentiment analysis
├── ai_agent.py           # LangChain + Gemini integration
├── impact_predictor.py   # Stock impact prediction logic
├── templates/
│   └── index.html        # Web interface
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
└── README.md            # This file
```

## How It Works

1. **News Collection**: The system queries Google News RSS feeds and Finviz for recent articles about the specified stock/company.

2. **Sentiment Analysis**: Each article is analyzed using FinBERT, a transformer model fine-tuned for financial text, to classify sentiment as positive, negative, or neutral.

3. **AI Reasoning**: LangChain orchestrates an AI agent that uses Google Gemini API to:
   - Summarize key news events
   - Assess overall sentiment
   - Provide market impact reasoning
   - Generate investor insights

4. **Impact Prediction**: A rule-based predictor combines sentiment scores and trends to forecast likely stock movements.

5. **Visualization**: Results are displayed with:
   - Impact prediction with confidence scores
   - AI-generated analysis
   - Sentiment distribution charts
   - List of analyzed articles with sentiment labels

## Limitations

- This is a proof-of-concept system and should not be used as the sole basis for investment decisions
- News sentiment does not guarantee stock price movements
- Market conditions, technical analysis, and other factors are not considered
- Free news sources may have rate limits

## Troubleshooting

### FinBERT Model Download Issues
If the model fails to download, it will automatically fall back to keyword-based sentiment analysis. The system will still function but with reduced accuracy.

### Gemini API Errors
If you encounter API errors:
- Verify your API key is correct in `.env`
- Check your API quota/limits
- The system will use fallback summaries if the API is unavailable

### No News Found
- Try different ticker symbols or company names
- Some companies may have limited news coverage
- Check your internet connection

## Future Enhancements

- Historical price correlation analysis
- Multi-stock comparison
- Real-time stock price integration
- Email/SMS alerts for significant news
- Machine learning-based prediction models
- Support for additional news sources

## License

This project is for educational and research purposes.

## Disclaimer

This tool is for informational purposes only and does not constitute financial advice. Always conduct thorough research and consult with financial professionals before making investment decisions.

