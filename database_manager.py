import sqlite3
import os
import threading
from typing import List, Dict, Optional
from contextlib import contextmanager

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
                    FOREIGN KEY(analysis_id) REFERENCES "analysis+history"(id)
                )
            ''')
            
            conn.commit()
            print("Database tables created/verified successfully.")
    
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
            articles: List of article dictionaries with keys: title, link, published, source, sentiment, sentiment_score
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            for article in articles:
                cursor.execute('''
                    INSERT INTO articles (analysis_id, title, link, published, source, sentiment, sentiment_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_id,
                    article.get('title', ''),
                    article.get('link', ''),
                    article.get('published', ''),
                    article.get('source', ''),
                    article.get('sentiment', 'neutral'),
                    article.get('sentiment_score', 0.5)
                ))
            
            conn.commit()
            print(f"Saved {len(articles)} articles for analysis ID: {analysis_id}")
    
    def search_by_keywords(self, keywords: List[str]) -> List[Dict]:
        """
        Search for historical analyses that contain any of the provided keywords.
        
        Args:
            keywords: List of keyword strings to search for
            
        Returns:
            List of dictionaries with keys: ticker, analysis_text, timestamp
        """
        if not keywords:
            return []
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Build a query that searches for any of the keywords in the analysis_text
            # Using LIKE with wildcards for case-insensitive partial matching
            conditions = ' OR '.join(['analysis_text LIKE ?'] * len(keywords))
            query = f'''
                SELECT ticker, analysis_text, timestamp
                FROM "analysis+history"
                WHERE {conditions}
                ORDER BY timestamp DESC
                LIMIT 10
            '''
            
            # Prepare parameters: each keyword wrapped with wildcards
            params = [f'%{keyword.lower()}%' for keyword in keywords]
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            # Convert Row objects to dictionaries
            results = []
            for row in rows:
                results.append({
                    'ticker': row['ticker'],
                    'analysis_text': row['analysis_text'],
                    'timestamp': row['timestamp']
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
    
    def __del__(self):
        """Ensure connection is closed when object is destroyed."""
        try:
            self.close()
        except:
            pass

