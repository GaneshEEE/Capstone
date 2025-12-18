# 📈 AI-Driven Financial News Impact Predictor

An intelligent, full-stack application that automatically collects financial news, analyzes sentiment using FinBERT, facilitates Q&A via an AI Agent (RAG), and predicts potential stock impact using both rule-based logic and Machine Learning models.

## ✨ Features

- **🔄 Automated News Collection**: Aggregates real-time financial news from Google News RSS and Finviz.
- **🧠 Advanced Sentiment Analysis**: Utilizes FinBERT (Financial BERT) to classify news sentiment with high accuracy.
- **💬 AI-Powered Q&A (RAG)**: Ask questions about specific stocks (e.g., "Why is AAPL down?") and get answers based on retrieved news context from **SQLite** using Google Gemini + LangChain.
- **📊 Impact Prediction**: Forecasts stock movement across 6 intensity levels (from Strongly Negative to Strongly Positive) using a hybrid approach (Rule-based + ML).
- **📉 Interactive Dashboard**: Visualizes sentiment distribution, confidence scores, and price forecasts with Plotly.
- **🆚 Multi-Stock Comparison**: Compare multiple stocks side-by-side with performance metrics and visual charts.
- **🔖 Smart Watchlist**: Local SQLite-based watchlist to track your favorite stocks and their latest analysis.
- **🤖 Machine Learning Support**: Train custom models on your own datasets to improve prediction accuracy over time.
- **🌐 Market Pulse**: View general market trends and discover trending stocks based on news volume and sentiment.

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Machine Learning**: Scikit-Learn (Random Forest, Gradient Boosting)
- **Data Processing**: Pandas, NumPy
- **Web Scraping**: BeautifulSoup4, Feedparser
- **AI & NLP**: 
  - FinBERT (Hugging Face Transformers)
  - Google Gemini API (via LangChain)
- **Database**: SQLite 
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **Data visualization**: Plotly.js
- **APIs**: Yahoo Finance (yfinance), Google News, Finviz

## 🚀 Installation

### Prerequisites
- Python 3.8+
- [Google Gemini API Key](https://makersuite.google.com/app/apikey) (Recommended)

### Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd proj_capstone
   ```

2. **Create a virtual environment**:
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment**:
   Create a `.env` file in the root directory:
   ```ini
   GOOGLE_GEMINI_API_KEY=your_api_key_here
   ```

## 📖 Usage

### Start the Application
```bash
python app.py
```
Visit `http://localhost:5000` in your browser.

### Key Workflows

1. **Analyze a Stock**:
   - Enter a ticker (e.g., `NVDA`) or company name.
   - select a timeframe.
   - Click **Analyze** to see sentiment, AI summary, and price impact methodology.

2. **Ask the AI (RAG)**:
   - After analyzing a stock, use the "Ask AI" chat box.
   - Example: *"What are the main risks mentioned in the recent news for Tesla?"*

3. **Manage Watchlist**:
   - Click "Add to Watchlist" on any analysis result.
   - View your saved stocks in the **Watchlist** tab.

4. **Train ML Model**:
   - Place your labeled datasets (CSV/JSON) in the `datasets/` folder.
   - Run the training script:
     ```bash
     python train_model.py
     ```
   - Follow the interactive prompts to train and save a new model.
   - See [ML_SETUP_GUIDE.md](ML_SETUP_GUIDE.md) for detailed instructions.

## 📂 Project Structure

```
proj_capstone/
├── app.py                 # Main Flask Application
├── ai_agent.py            # LangChain + Gemini Agent (RAG)
├── database_manager.py    # SQLite Database Handler
├── impact_predictor.py    # Prediction Logic (Rule-based & ML)
├── news_fetcher.py        # News Scraper (RSS, Finviz)
├── rag_handler.py         # RAG Implementation for Q&A
├── sentiment_analyzer.py  # FinBERT Model Handler
├── train_model.py         # ML Training Script
├── requirements.txt       # Dependencies
├── .env                   # API Keys (gitignored)
├── datasets/              # Folder for training data
├── models/                # Saved ML models
└── templates/             # HTML Templates
```

## 🏗️ System Architecture

1.  **News Aggregation**: `NewsFetcher` gathers articles from Google News RSS and Finviz.
2.  **Sentiment Analysis**: Each article is scored by FinBERT.
3.  **Hybrid Prediction Engine**:
    -   **Rule-Based**: Aggregated weighted sentiment scores across 6 intensity levels (Strongly/Moderately/Slightly Positive & Negative).
    -   **Machine Learning**: Optional Random Forest/Gradient Boosting models trained on your custom datasets (`datasets/` folder).
    -   **Combination**: The system merges both scores (weighted by confidence) to produce a final verdict.
4.  **Generative AI (RAG)**:
    -   **Retrieval**: `RAGHandler` fetches relevant past analyses from the SQLite database using keyword matching.
    -   **Generation**: Google Gemini API uses this context + current articles to answer user Q&A.
5.  **Visualization**: Stock price simulations are generated using a "Random Walk with Drift" model influenced by the prediction intensity.

## 🔌 API Reference

The Flask backend exposes the following endpoints:

-   `POST /analyze`:
    -   **Body**: `{"ticker": "NVDA", "timeframe": "7d"}`
    -   **Returns**: Analysis results, sentiment distribution, and prediction.
-   `POST /ask`:
    -   **Body**: `{"question": "Why is the stock dropping?"}`
    -   **Returns**: AI-generated answer based on RAG context.
-   `GET /market-news`:
    -   **Returns**: General market news and "Trending Stocks" identified by mention count and sentiment.
-   `POST /watchlist/add`:
    -   **Body**: `{"ticker": "AAPL", "price": 150.00, ...}`
    -   **Action**: Saves stock to SQLite watchlist.

## ⚠️ Limitations

- **News Latency**: Free news sources may have slight delays or rate limits.
- **Financial Advice**: This tool is for **informational purposes only**. It does not constitute financial advice. AI predictions can be wrong.

## 📄 License

[MIT License](LICENSE)
