import sqlite3
import os
import threading
from typing import List, Dict, Optional
from contextlib import contextmanager
from datetime import datetime, timedelta

class DatabaseManager:
    def __init__(self, db_file: str = 'news_analysis.db'):
        """
        Initialize the DatabaseManager with a SQLite database.
        Thread-safe implementation that creates connections per operation.
        
        Args:
            db_file: Path to the SQLite database file
        """
        self.db_file = db_file
        self._local = threading.local()
    
    @contextmanager
    def _get_connection(self):
        """
        Get a thread-local database connection.
        Creates a new connection for each thread/operation to ensure thread safety.
        """
        # Check if this thread already has a connection
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                self.db_file,
                check_same_thread=False  # Allow connections from different threads
            )
            self._local.conn.row_factory = sqlite3.Row
        
        try:
            yield self._local.conn
        except Exception:
            # If there's an error, close the connection and remove it
            if hasattr(self._local, 'conn'):
                try:
                    self._local.conn.close()
                except:
                    pass
                self._local.conn = None
            raise
    
    def create_table(self):
        """
        Create the database tables if they don't exist.
        This method is idempotent - safe to call multiple times.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create analysis+history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS "analysis+history" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL,
                    analysis_text TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    analysis_id INTEGER,
                    title TEXT,
                    link TEXT,
                    published TEXT,
                    source TEXT,
                    sentiment TEXT,
                    sentiment_score REAL,
                    summary TEXT,
                    FOREIGN KEY(analysis_id) REFERENCES "analysis+history"(id)
                )
            ''')
            
            # Add summary column if it doesn't exist (for existing databases)
            try:
                cursor.execute('ALTER TABLE articles ADD COLUMN summary TEXT')
            except sqlite3.OperationalError:
                # Column already exists, ignore
                pass
            
            conn.commit()
            conn.commit()
            print("Database tables created/verified successfully.")

    def create_watchlist_table(self):
        """
        Create the watchlist table if it doesn't exist.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT NOT NULL UNIQUE,
                    company_name TEXT,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    price REAL,
                    predicted_target_range TEXT,
                    recommendation TEXT,
                    summary TEXT
                )
            ''')
            conn.commit()
            print("Watchlist table created/verified successfully.")
    
    def save_analysis(self, ticker_or_company: str, analysis_text: str) -> int:
        """
        Save an analysis to the database.
        
        Args:
            ticker_or_company: Stock ticker or company name
            analysis_text: The AI-generated analysis text
            
        Returns:
            The ID of the inserted analysis record
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO "analysis+history" (ticker, analysis_text)
                VALUES (?, ?)
            ''', (ticker_or_company, analysis_text))
            
            conn.commit()
            analysis_id = cursor.lastrowid
            print(f"Analysis saved with ID: {analysis_id}")
            return analysis_id
    
    def save_articles(self, analysis_id: int, articles: List[Dict]):
        """
        Save multiple articles linked to an analysis.
        
        Args:
            analysis_id: The ID of the analysis these articles belong to
            articles: List of article dictionaries with keys: title, link, published, source, sentiment, sentiment_score, summary
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for article in articles:
                cursor.execute('''
                    INSERT INTO articles (analysis_id, title, link, published, source, sentiment, sentiment_score, summary)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    article.get('title', ''),
                    article.get('link', ''),
                    article.get('published', ''),
                    article.get('source', ''),
                    article.get('sentiment', 'neutral'),
                    article.get('sentiment_score', 0.5),
                    article.get('summary', '')
                ))
            
            conn.commit()
            print(f"Saved {len(articles)} articles for analysis ID: {analysis_id}")
    
    def search_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """
        Search for historical analyses and articles that contain any of the provided keywords.
        Searches both overall analysis summaries and individual article summaries.
        
        Args:
            keywords: List of keyword strings to search for
            
        Returns:
            List of dictionaries with keys: ticker, analysis_text, timestamp, article_context
        """
        if not keywords:
            return []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build conditions for searching analysis_text
            conditions = ' OR '.join(['analysis_text LIKE ?'] * len(keywords))
            params = [f'%{keyword.lower()}%' for keyword in keywords]
            
            # Search in analysis+history table
            query = f'''
                SELECT a.ticker, a.analysis_text, a.timestamp, a.id as analysis_id
                FROM "analysis+history" a
                WHERE {conditions}
                ORDER BY a.timestamp DESC
                LIMIT 10
            '''
            
            cursor.execute(query, params)
            analysis_rows = cursor.fetchall()
            
            # Also search in articles table (titles and summaries)
            article_conditions_parts = []
            article_params = []
            for keyword in keywords:
                keyword_pattern = f'%{keyword.lower()}%'
                article_conditions_parts.append('(art.title LIKE ? OR art.summary LIKE ?)')
                article_params.extend([keyword_pattern, keyword_pattern])
            
            article_conditions = ' OR '.join(article_conditions_parts)
            
            article_query = f'''
                SELECT a.ticker, a.analysis_text, a.timestamp, 
                       GROUP_CONCAT(art.title || ': ' || COALESCE(art.summary, art.title), ' || ') as article_context
                FROM "analysis+history" a
                JOIN articles art ON a.id = art.analysis_id
                WHERE {article_conditions}
                GROUP BY a.id, a.ticker, a.analysis_text, a.timestamp
                ORDER BY a.timestamp DESC
                LIMIT 10
            '''
            
            cursor.execute(article_query, article_params)
            article_rows = cursor.fetchall()
            
            # Combine results, prioritizing analyses with matching articles
            results = []
            seen_analysis_ids = set()
            
            # First add analyses with matching articles (more detailed context)
            for row in article_rows:
                if row['article_context']:
                    results.append({
                        'ticker': row['ticker'],
                        'analysis_text': row['analysis_text'],
                        'timestamp': row['timestamp'],
                        'article_context': row['article_context']
                    })
                    # Track which analysis IDs we've added
                    # We'll use a simple approach: check if we've seen this ticker+timestamp combo
                    seen_analysis_ids.add((row['ticker'], row['timestamp']))
            
            # Then add analyses that matched but don't have article matches
            for row in analysis_rows:
                key = (row['ticker'], row['timestamp'])
                if key not in seen_analysis_ids:
                    results.append({
                        'ticker': row['ticker'],
                        'analysis_text': row['analysis_text'],
                        'timestamp': row['timestamp'],
                        'article_context': None
                    })
                    seen_analysis_ids.add(key)
            
            # Limit to 10 total results
            return results[:10]
    
    def get_historical_articles(self, ticker_or_company: str, days: int = 30) -> List[Dict]:
        """
        Get historical articles from the database for a specific ticker/company within a time period.
        
        Args:
            ticker_or_company: Stock ticker or company name
            days: Number of days to look back
            
        Returns:
            List of article dictionaries
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            query = '''
                SELECT art.title, art.link, art.published, art.source, 
                       art.sentiment, art.sentiment_score, art.summary,
                       a.timestamp as analysis_timestamp
                FROM articles art
                JOIN "analysis+history" a ON art.analysis_id = a.id
                WHERE a.ticker = ? AND a.timestamp >= ?
                ORDER BY a.timestamp DESC, art.id DESC
                LIMIT 100
            '''
            
            cursor.execute(query, (ticker_or_company, cutoff_date.strftime('%Y-%m-%d %H:%M:%S')))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'title': row['title'],
                    'link': row['link'],
                    'published': row['published'],
                    'source': row['source'],
                    'sentiment': row['sentiment'],
                    'sentiment_score': row['sentiment_score'],
                    'summary': row['summary'],
                    'from_database': True  # Flag to indicate this came from database
                })
            
            return results
    
    def close(self):
        """Close the database connection for the current thread."""
        if hasattr(self._local, 'conn') and self._local.conn:
            try:
                self._local.conn.close()
            except:
                pass
            self._local.conn = None
    
    def create_ml_tables(self):
        """
        Create tables for ML datasets and model metadata.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Create ML datasets table (generic structure)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_name TEXT NOT NULL UNIQUE,
                    table_name TEXT NOT NULL,
                    description TEXT,
                    source TEXT,
                    rows_count INTEGER,
                    columns_count INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create model metadata table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ml_models (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    model_type TEXT,
                    model_path TEXT,
                    training_dataset TEXT,
                    accuracy REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            ''')
            
            conn.commit()
            print("ML tables created/verified successfully.")
    
    def register_dataset(self, dataset_name: str, table_name: str, 
                        description: str = '', source: str = '',
                        rows_count: int = 0, columns_count: int = 0):
        """
        Register a dataset in the ml_datasets table.
        
        Args:
            dataset_name: Human-readable name for the dataset
            table_name: SQL table name where data is stored
            description: Description of the dataset
            source: Source/URL of the dataset
            rows_count: Number of rows
            columns_count: Number of columns
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO ml_datasets 
                (dataset_name, table_name, description, source, rows_count, columns_count, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (dataset_name, table_name, description, source, rows_count, columns_count))
            conn.commit()
    
    def get_registered_datasets(self):
        """
        Get list of all registered datasets.
        
        Returns:
            List of dataset records
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM ml_datasets ORDER BY created_at DESC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def save_model_metadata(self, model_name: str, model_type: str, 
                           model_path: str, training_dataset: str = '',
                           accuracy: float = None):
        """
        Save ML model metadata.
        
        Args:
            model_name: Name of the model
            model_type: Type of model (e.g., 'RandomForest', 'NeuralNetwork')
            model_path: Path to saved model file
            training_dataset: Name of dataset used for training
            accuracy: Model accuracy score
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO ml_models 
                (model_name, model_type, model_path, training_dataset, accuracy)
                VALUES (?, ?, ?, ?, ?)
            ''', (model_name, model_type, model_path, training_dataset, accuracy))
            conn.commit()
    
    def get_active_model(self):
        """
        Get the currently active ML model.
        
        Returns:
            Model metadata dictionary or None
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM ml_models 
                WHERE is_active = 1 
                ORDER BY created_at DESC 
                LIMIT 1
            ''')
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def add_to_watchlist(self, ticker: str, company_name: str, price: float, 
                        predicted_target_range: str, recommendation: str, summary: str):
        """
        Add a stock to the watchlist.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO watchlist 
                    (ticker, company_name, price, predicted_target_range, recommendation, summary, added_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (ticker, company_name, price, predicted_target_range, recommendation, summary))
                conn.commit()
                return True
            except Exception as e:
                print(f"Error adding to watchlist: {e}")
                return False

    def get_watchlist(self):
        """
        Get all items from the watchlist.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM watchlist ORDER BY added_at DESC')
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def remove_from_watchlist(self, ticker: str):
        """
        Remove a stock from the watchlist.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM watchlist WHERE ticker = ?', (ticker,))
            conn.commit()

    def __del__(self):
        """Ensure connection is closed when object is destroyed."""
        try:
            self.close()
        except:
            pass