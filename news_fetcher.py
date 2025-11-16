'''
This module provides a class to fetch news articles from Finviz.
It has been refactored to use the requests library directly, mimicking a browser
request to avoid the instability of Selenium-based browser automation.
'''
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import urllib.parse

class NewsFetcher:
    '''A class to fetch news articles for a given stock ticker from Finviz.'''
    def __init__(self):
        '''Initializes the NewsFetcher with the base URL and browser headers.'''
        self.finviz_base = "https://finviz.com/quote.ashx"
        # These headers mimic a real browser request and are essential for success.
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'accept-language': 'en-US,en;q=0.9',
            'referer': 'https://finviz.com/',
        }

    def fetch_news(self, ticker=None, company_name=None):
        '''
        Fetches news from Finviz using a direct HTTP request.

        Args:
            ticker (str): The stock ticker symbol (e.g., "AAPL").

        Returns:
            list: A list of unique news articles, or an empty list if fetching fails.
        '''
        if not ticker and not company_name:
            print("Error: No ticker or company name provided.")
            return []

        if not ticker and company_name:
            print(f"Attempting to find ticker for company: {company_name}...")
            ticker = self._get_ticker_from_company_name(company_name)
            if not ticker:
                print(f"Could not find ticker for {company_name}.")
                return []
            print(f"Found ticker: {ticker} for {company_name}.")

        try:
            url = f"{self.finviz_base}?t={ticker.upper()}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()  # Raise an exception for HTTP errors (e.g., 403, 500)

            soup = BeautifulSoup(response.content, 'html.parser')
            news_table = soup.find(id='news-table')

            if not news_table:
                print("Warning: Could not find the news table on Finviz.")
                return []

            # Process and deduplicate articles
            processed_articles = []
            for row in news_table.find_all('tr'):
                if title_cell := row.find('a', class_='tab-link-news'):
                    date_cell = row.find('td')
                    processed_articles.append({
                        'title': title_cell.text.strip(),
                        'link': title_cell.get('href', ''),
                        'published': date_cell.text.strip() if date_cell else '',
                        'source': 'Finviz'
                    })
            
            seen_titles = set()
            unique_articles = []
            for article in processed_articles:
                if article['title'].lower() not in seen_titles:
                    seen_titles.add(article['title'].lower())
                    unique_articles.append(article)
            
            return unique_articles[:20]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching Finviz news with requests: {str(e)}")
        except Exception as e:
            print(f"An unexpected error occurred during news fetching: {str(e)}")
            
        return unique_articles[:20]

    def get_company_name_from_ticker(self, ticker):
        """
        Gets the company name from a stock ticker using yfinance.
        
        Args:
            ticker (str): Stock ticker symbol (e.g., "AAPL")
            
        Returns:
            str: Company name, or None if not found
        """
        try:
            ticker_obj = yf.Ticker(ticker.upper())
            info = ticker_obj.info
            
            if info and 'longName' in info:
                return info['longName']
            elif info and 'shortName' in info:
                return info['shortName']
            elif info and 'name' in info:
                return info['name']
            
            return None
        except Exception as e:
            print(f"Error getting company name for ticker {ticker}: {str(e)}")
            return None
    
    def _get_ticker_from_company_name(self, company_name):
        """
        Attempts to find a stock ticker from a company name using Yahoo Finance search.
        Uses yfinance and Yahoo Finance's search functionality for reliable ticker lookup.
        """
        try:
            # Strategy 1: Use Yahoo Finance search API (free, no API key needed)
            # Yahoo Finance has a search endpoint that returns ticker symbols
            encoded_name = urllib.parse.quote_plus(company_name)
            yahoo_search_url = f"https://query1.finance.yahoo.com/v1/finance/search?q={encoded_name}&quotesCount=5&newsCount=0"
            
            search_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json'
            }
            
            response = requests.get(yahoo_search_url, headers=search_headers, timeout=10)
            response.raise_for_status()
            
            search_results = response.json()
            
            # Check if we got results
            if 'quotes' in search_results and len(search_results['quotes']) > 0:
                # Get the first result (most relevant)
                first_result = search_results['quotes'][0]
                ticker = first_result.get('symbol', '').upper()
                
                # Validate it's a proper ticker (1-5 uppercase letters)
                if ticker and ticker.isalpha() and 1 <= len(ticker) <= 5:
                    print(f"Found ticker {ticker} for company '{company_name}' via Yahoo Finance search")
                    return ticker
            
            # Strategy 2: Try using yfinance directly with the company name
            # Sometimes yfinance can resolve company names
            try:
                # Try common variations
                variations = [
                    company_name,
                    company_name.replace(" Inc", "").replace(" Inc.", "").strip(),
                    company_name.replace(" Corporation", "").replace(" Corp", "").replace(" Corp.", "").strip(),
                    company_name.replace(" Company", "").replace(" Co", "").replace(" Co.", "").strip(),
                ]
                
                for variation in variations:
                    try:
                        ticker_obj = yf.Ticker(variation)
                        info = ticker_obj.info
                        
                        # Check if we got valid info with a symbol
                        if info and 'symbol' in info:
                            ticker = info['symbol'].upper()
                            if ticker and ticker.isalpha() and 1 <= len(ticker) <= 5:
                                print(f"Found ticker {ticker} for company '{company_name}' via yfinance")
                                return ticker
                    except:
                        continue
            except Exception as e:
                print(f"yfinance lookup attempt failed: {str(e)}")
            
            # Strategy 3: Fallback to Finviz search (original method)
            print(f"Trying Finviz search as fallback for '{company_name}'...")
            direct_search_url = f"https://finviz.com/quote.ashx?q={encoded_name}"
            response = requests.get(direct_search_url, headers=self.headers, allow_redirects=True, timeout=10)
            response.raise_for_status()

            # If there's a redirect, the final URL might contain the ticker
            if 'quote.ashx?t=' in response.url:
                ticker = response.url.split('t=')[-1].split('&')[0].upper()
                if ticker and ticker.isalpha() and 1 <= len(ticker) <= 5:
                    print(f"Found ticker {ticker} for company '{company_name}' via Finviz redirect")
                    return ticker
            
            # Parse Finviz page for ticker
            soup = BeautifulSoup(response.content, 'html.parser')
            title_tag = soup.find('title')
            if title_tag and ' - Finviz.com' in title_tag.text:
                ticker_match = title_tag.text.split(' - ')[0].strip()
                if ticker_match.isupper() and ticker_match.isalpha() and 1 <= len(ticker_match) <= 5:
                    print(f"Found ticker {ticker_match} for company '{company_name}' via Finviz title")
                    return ticker_match

            print(f"Could not find ticker for '{company_name}' after trying all methods.")
            return None

        except requests.exceptions.RequestException as e:
            print(f"Network error during ticker lookup for '{company_name}': {str(e)}")
        except Exception as e:
            print(f"Error during ticker lookup for '{company_name}': {str(e)}")
            import traceback
            traceback.print_exc()
        
        return None
