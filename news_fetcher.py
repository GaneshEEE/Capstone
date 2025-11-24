'''
This module provides a class to fetch news articles from multiple sources.
It fetches from Finviz, Yahoo Finance, and Google News RSS to get more historical articles.
'''
import requests
from bs4 import BeautifulSoup
import yfinance as yf
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
import re
import feedparser

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

    def _parse_finviz_date(self, date_str):
        """
        Parse Finviz date string to datetime object.
        Handles formats like: "Jan-15-24 04:30PM", "Today 10:30AM", "Yesterday 02:15PM"
        
        Args:
            date_str (str): Date string from Finviz
            
        Returns:
            datetime: Parsed datetime object, or None if parsing fails
        """
        if not date_str:
            return None
        
        try:
            date_str = date_str.strip()
            now = datetime.now()
            
            # Handle "Today" format
            if date_str.lower().startswith('today'):
                time_part = date_str.split(' ', 1)[1] if ' ' in date_str else ''
                if time_part:
                    try:
                        time_obj = datetime.strptime(time_part, '%I:%M%p').time()
                        return datetime.combine(now.date(), time_obj)
                    except:
                        pass
                return now
            
            # Handle "Yesterday" format
            if date_str.lower().startswith('yesterday'):
                time_part = date_str.split(' ', 1)[1] if ' ' in date_str else ''
                yesterday = now - timedelta(days=1)
                if time_part:
                    try:
                        time_obj = datetime.strptime(time_part, '%I:%M%p').time()
                        return datetime.combine(yesterday.date(), time_obj)
                    except:
                        pass
                return yesterday
            
            # Handle "Jan-15-24 04:30PM" format
            try:
                # Try format: "Jan-15-24 04:30PM"
                dt = datetime.strptime(date_str, '%b-%d-%y %I:%M%p')
                return dt
            except:
                pass
            
            # Try format: "Jan-15-24"
            try:
                dt = datetime.strptime(date_str, '%b-%d-%y')
                return dt
            except:
                pass
            
            # Try format: "Jan 15, 2024"
            try:
                dt = datetime.strptime(date_str, '%b %d, %Y')
                return dt
            except:
                pass
            
            # Try format: "Jan 15" (current year assumed)
            try:
                dt = datetime.strptime(date_str, '%b %d')
                # Assume current year if year not specified
                dt = dt.replace(year=now.year)
                # If the date is in the future (e.g., Jan 15 when it's Dec), it's probably last year
                if dt > now:
                    dt = dt.replace(year=now.year - 1)
                return dt
            except:
                pass
            
            # Try format: "15-Jan-24" or "15/Jan/24"
            try:
                dt = datetime.strptime(date_str, '%d-%b-%y')
                return dt
            except:
                pass
            
            try:
                dt = datetime.strptime(date_str, '%d/%b/%y')
                return dt
            except:
                pass
            
            # Try format: "3 days ago" or similar relative formats
            if 'day' in date_str.lower() or 'hour' in date_str.lower():
                # Extract number
                numbers = re.findall(r'\d+', date_str)
                if numbers:
                    num = int(numbers[0])
                    if 'day' in date_str.lower():
                        return now - timedelta(days=num)
                    elif 'hour' in date_str.lower():
                        return now - timedelta(hours=num)
            
            return None
            
        except Exception as e:
            print(f"Error parsing date '{date_str}': {str(e)}")
            return None
    
    def _filter_articles_by_timeframe(self, articles, timeframe='7d'):
        """
        Filter articles based on time period.
        
        Args:
            articles (list): List of article dictionaries
            timeframe (str): '24h', '7d', or '30d'
            
        Returns:
            list: Filtered articles
        """
        if not articles:
            return articles
        
        now = datetime.now()
        
        # Calculate cutoff time
        if timeframe == '24h':
            cutoff = now - timedelta(hours=24)
        elif timeframe == '7d':
            cutoff = now - timedelta(days=7)
        elif timeframe == '30d':
            cutoff = now - timedelta(days=30)
        else:
            # Default to all articles
            return articles
        
        print(f"Filtering articles: cutoff date is {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")
        
        filtered = []
        parse_errors = 0
        too_old = 0
        
        for article in articles:
            # First try to use published_timestamp if available (from Yahoo Finance/Google News)
            article_date = article.get('published_timestamp')
            
            # If no timestamp, try parsing the published string
            if not article_date:
                published_str = article.get('published', '')
                if not published_str:
                    # If no date, include it (better to include than exclude)
                    filtered.append(article)
                    continue
                
                article_date = self._parse_finviz_date(published_str)
            
            if article_date:
                if article_date >= cutoff:
                    filtered.append(article)
                else:
                    too_old += 1
                    date_str = article.get('published', 'N/A')
                    print(f"  Excluded (too old): '{article.get('title', '')[:50]}...' - Date: {date_str} -> {article_date.strftime('%Y-%m-%d')}")
            else:
                # If we can't parse the date, include it (but log for debugging)
                parse_errors += 1
                published_str = article.get('published', 'N/A')
                print(f"  Warning: Could not parse date '{published_str}' for article: '{article.get('title', '')[:50]}...' - including anyway")
                filtered.append(article)
        
        print(f"Filtering results: {len(filtered)} articles kept, {too_old} too old, {parse_errors} date parse errors")
        return filtered

    def fetch_news(self, ticker=None, company_name=None, timeframe='7d'):
        '''
        Fetches news from multiple sources: Finviz, Yahoo Finance, and Google News RSS.

        Args:
            ticker (str): The stock ticker symbol (e.g., "AAPL").
            company_name (str): Company name as alternative to ticker.
            timeframe (str): Time period to filter articles ('24h', '7d', '30d', or 'all').

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

        all_articles = []
        seen_titles = set()
        
        # Fetch from multiple sources in parallel
        print(f"Fetching news from multiple sources for {ticker}...")
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._fetch_finviz_news, ticker): 'Finviz',
                executor.submit(self._fetch_yahoo_news, ticker): 'Yahoo Finance',
                executor.submit(self._fetch_google_news_rss, ticker, company_name): 'Google News'
            }
            
            for future in as_completed(futures):
                source_name = futures[future]
                try:
                    articles = future.result()
                    for article in articles:
                        title_lower = article.get('title', '').lower()
                        if title_lower and title_lower not in seen_titles:
                            seen_titles.add(title_lower)
                            all_articles.append(article)
                except Exception as e:
                    print(f"Error fetching from {source_name}: {str(e)}")
        
        print(f"Total unique articles from all sources: {len(all_articles)}")
        
        # Sort by published timestamp if available, otherwise by source priority
        def sort_key(article):
            if article.get('published_timestamp'):
                return article['published_timestamp']
            # For articles without timestamp, prioritize by source
            source_priority = {'Finviz': 0, 'Yahoo Finance': 1, 'Google News': 2}
            return datetime.min + timedelta(days=source_priority.get(article.get('source', ''), 99))
        
        all_articles.sort(key=sort_key, reverse=True)
        
        # Show sample dates for debugging
        if all_articles:
            print("Sample article dates:")
            for i, article in enumerate(all_articles[:5]):
                print(f"  {i+1}. [{article.get('source', 'Unknown')}] '{article.get('title', '')[:40]}...' - Date: '{article.get('published', 'N/A')}'")
        
        # Filter by timeframe if specified
        if timeframe and timeframe != 'all':
            articles_before = len(all_articles)
            all_articles = self._filter_articles_by_timeframe(all_articles, timeframe)
            print(f"After filtering: {len(all_articles)} articles remain (was {articles_before}) for timeframe: {timeframe}")
            
            # Warning if filtering removed all articles
            if len(all_articles) == 0 and articles_before > 0:
                print(f"WARNING: All articles were filtered out! Sources may only show recent articles.")
        else:
            print(f"No filtering applied (timeframe: {timeframe})")
        
        # Limit to reasonable number (more for longer timeframes)
        limit = 50 if timeframe == '30d' else 30 if timeframe == '7d' else 20
        all_articles = all_articles[:limit]
        
        articles_with_summaries = self._fetch_article_summaries(all_articles)
        return articles_with_summaries
    
    def _fetch_yahoo_news(self, ticker):
        """
        Fetch news from Yahoo Finance using yfinance.
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            list: List of article dictionaries
        """
        articles = []
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                return articles
            
            for item in news:
                # Parse the published date
                published_time = None
                if 'providerPublishTime' in item:
                    try:
                        published_time = datetime.fromtimestamp(item['providerPublishTime'])
                    except:
                        pass
                
                # Format date string
                if published_time:
                    # Calculate relative time
                    now = datetime.now()
                    diff = now - published_time
                    if diff.days == 0:
                        if diff.seconds < 3600:
                            date_str = f"{diff.seconds // 60} minutes ago"
                        else:
                            date_str = f"Today {published_time.strftime('%I:%M%p')}"
                    elif diff.days == 1:
                        date_str = f"Yesterday {published_time.strftime('%I:%M%p')}"
                    else:
                        date_str = published_time.strftime('%b-%d-%y %I:%M%p')
                else:
                    date_str = 'Recent'
                
                articles.append({
                    'title': item.get('title', 'No title'),
                    'link': item.get('link', ''),
                    'published': date_str,
                    'source': item.get('publisher', 'Yahoo Finance'),
                    'published_timestamp': published_time
                })
            
            print(f"Fetched {len(articles)} articles from Yahoo Finance")
            return articles
            
        except Exception as e:
            print(f"Error fetching Yahoo Finance news: {str(e)}")
            return []
    
    def _fetch_google_news_rss(self, ticker, company_name=None, max_results=20):
        """
        Fetch news from Google News RSS feed.
        
        Args:
            ticker (str): Stock ticker symbol
            company_name (str): Company name (optional)
            max_results (int): Maximum number of articles to fetch
            
        Returns:
            list: List of article dictionaries
        """
        articles = []
        try:
            # Build search query
            query = ticker
            if company_name:
                query = f"{ticker} {company_name}"
            
            # Google News RSS URL
            rss_url = f"https://news.google.com/rss/search?q={urllib.parse.quote(query)}+stock&hl=en-US&gl=US&ceid=US:en"
            
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                return articles
            
            for entry in feed.entries[:max_results]:
                # Parse published date
                published_time = None
                date_str = 'Recent'
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    try:
                        published_time = datetime(*entry.published_parsed[:6])
                        # Format similar to Finviz format
                        now = datetime.now()
                        diff = now - published_time
                        if diff.days == 0:
                            date_str = f"Today {published_time.strftime('%I:%M%p')}"
                        elif diff.days == 1:
                            date_str = f"Yesterday {published_time.strftime('%I:%M%p')}"
                        else:
                            date_str = published_time.strftime('%b-%d-%y %I:%M%p')
                    except:
                        pass
                
                articles.append({
                    'title': entry.get('title', 'No title'),
                    'link': entry.get('link', ''),
                    'published': date_str,
                    'source': entry.get('source', {}).get('title', 'Google News') if hasattr(entry, 'source') else 'Google News',
                    'published_timestamp': published_time
                })
            
            print(f"Fetched {len(articles)} articles from Google News RSS")
            return articles
            
        except Exception as e:
            print(f"Error fetching Google News RSS: {str(e)}")
            return []
    
    def _fetch_finviz_news(self, ticker):
        """
        Fetch news from Finviz (extracted as separate method for parallel execution).
        
        Args:
            ticker (str): Stock ticker symbol
            
        Returns:
            list: List of article dictionaries
        """
        articles = []
        try:
            url = f"{self.finviz_base}?t={ticker.upper()}"
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            news_table = soup.find(id='news-table')

            if not news_table:
                return articles

            # Process articles
            for row in news_table.find_all('tr'):
                if title_cell := row.find('a', class_='tab-link-news'):
                    date_cell = row.find('td')
                    articles.append({
                        'title': title_cell.text.strip(),
                        'link': title_cell.get('href', ''),
                        'published': date_cell.text.strip() if date_cell else '',
                        'source': 'Finviz'
                    })
            
            print(f"Fetched {len(articles)} articles from Finviz")
            return articles

        except requests.exceptions.RequestException as e:
            print(f"Error fetching news from Finviz: {str(e)}")
            return []
        except Exception as e:
            print(f"Unexpected error fetching news from Finviz: {str(e)}")
            return []
    
    def _is_generic_summary(self, summary):
        """
        Check if a summary is generic/placeholder text that shouldn't be used for sentiment analysis.
        
        Args:
            summary (str): The summary text to check
            
        Returns:
            bool: True if the summary is generic and should be ignored
        """
        if not summary:
            return True
        
        summary_lower = summary.lower().strip()
        
        # List of known generic/placeholder summaries
        generic_patterns = [
            "comprehensive, up-to-date news coverage",
            "aggregated from sources all over the world",
            "google news",
            "read full article",
            "click here to read more",
            "view original article",
            "source:",
            "published by",
            "news from",
            "breaking news",
            "latest news",
            "news coverage",
            "stay informed",
            "get the latest",
            "all the latest news",
            "news aggregator",
            "news feed"
        ]
        
        # Check if summary matches any generic pattern
        for pattern in generic_patterns:
            if pattern in summary_lower:
                return True
        
        # Check if summary is too short or too generic
        if len(summary) < 30:
            return True
        
        # Check if it's just a URL or link text
        if summary.startswith('http') or summary.startswith('www.'):
            return True
        
        # Check if it's mostly punctuation or special characters
        if len(summary.replace(' ', '').replace('.', '').replace(',', '').replace('!', '').replace('?', '')) < 20:
            return True
        
        return False
    
    def _fetch_meta_description(self, article_url):
        """
        Fetches meta description from an article URL.
        
        Args:
            article_url (str): URL of the article
            
        Returns:
            str: Meta description if found and not generic, None otherwise
        """
        if not article_url:
            return None
            
        try:
            # Handle relative URLs
            if article_url.startswith('/'):
                article_url = 'https://finviz.com' + article_url
            elif not article_url.startswith('http'):
                return None
            
            response = requests.get(article_url, headers=self.headers, timeout=5, allow_redirects=True)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple meta tag formats in order of preference
            meta_desc = (
                soup.find('meta', {'property': 'og:description'}) or
                soup.find('meta', {'name': 'description'}) or
                soup.find('meta', {'name': 'twitter:description'}) or
                soup.find('meta', {'name': 'twitter:card'})
            )
            
            if meta_desc and meta_desc.get('content'):
                description = meta_desc['content'].strip()
                # Clean up the description
                if description and len(description) > 20:  # Only return if meaningful
                    # Check if it's a generic summary
                    if self._is_generic_summary(description):
                        return None  # Don't use generic summaries
                    return description[:500]  # Limit length
            
            return None
            
        except requests.exceptions.RequestException:
            return None
        except Exception as e:
            return None
    
    def _fetch_article_summaries(self, articles, max_workers=5):
        """
        Fetches meta descriptions for articles in parallel.
        
        Args:
            articles (list): List of article dictionaries
            max_workers (int): Number of parallel workers
            
        Returns:
            list: Articles with 'summary' field added
        """
        if not articles:
            return articles
        
        print(f"Fetching summaries for {len(articles)} articles...")
        
        def fetch_summary(article):
            """Fetch summary for a single article"""
            summary = self._fetch_meta_description(article.get('link'))
            article['summary'] = summary
            return article
        
        # Fetch summaries in parallel for better performance
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_article = {
                executor.submit(fetch_summary, article.copy()): article 
                for article in articles
            }
            
            # Collect results as they complete
            results = []
            completed = 0
            for future in as_completed(future_to_article):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    if completed % 5 == 0:
                        print(f"  Fetched {completed}/{len(articles)} summaries...")
                except Exception as e:
                    # If fetching fails, use original article without summary
                    original = future_to_article[future]
                    original['summary'] = None
                    results.append(original)
        
        # Maintain original order by matching articles
        ordered_results = []
        for article in articles:
            # Find matching result
            for result in results:
                if (result.get('title') == article.get('title') and 
                    result.get('link') == article.get('link')):
                    ordered_results.append(result)
                    break
            else:
                # If not found, use original with None summary
                article['summary'] = None
                ordered_results.append(article)
        
        # Count how many summaries were found
        summaries_found = sum(1 for a in ordered_results if a.get('summary'))
        print(f"Successfully fetched {summaries_found}/{len(articles)} article summaries.")
        
        return ordered_results

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
