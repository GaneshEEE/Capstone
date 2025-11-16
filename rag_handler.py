
from database_manager import DatabaseManager
from collections import Counter
import re

class RAGHandler:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.stop_words = set([
            'a', 'an', 'and', 'the', 'in', 'is', 'it', 'of', 'on', 'for', 'with', 'as', 'at', 
            'by', 'to', 'from', 'up', 'out', 'over', 'under', 'again', 'then', 'once', 'here', 
            'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
            'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 
            'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now', 'd', 
            'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn', 'hadn', 
            'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn', 'wasn',
            'weren', 'won', 'wouldn', 'inc', 'company', 'stocks', 'shares', 'market'
        ])

    def _extract_keywords(self, text, num_keywords=5):
        """Extracts the most common keywords from text, ignoring stop words."""
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out stop words and non-alphabetic words
        filtered_words = [word for word in words if word.isalpha() and word not in self.stop_words]
        
        if not filtered_words:
            return []

        # Get the most common keywords
        most_common = Counter(filtered_words).most_common(num_keywords)
        return [word for word, count in most_common]

    def get_context(self, ticker, articles):
        """
        Gets historical context for a ticker based on keywords from recent articles.
        Uses both article titles and summaries for better keyword extraction.
        """
        # Combine titles and summaries for keyword extraction
        all_text = []
        for article in articles:
            all_text.append(article.get('title', ''))
            if article.get('summary'):
                all_text.append(article.get('summary', ''))
        
        combined_text = " ".join(all_text)
        keywords = self._extract_keywords(combined_text)
        
        if not keywords:
            return "No relevant historical context found."

        # Search database for these keywords (now searches both analyses and articles)
        historical_data = self.db_manager.search_by_keywords(keywords)
        
        if not historical_data:
            return "No relevant historical context found in the database."

        # Format context for the AI prompt
        context_str = "\n--- Historical Context ---\n"
        for row in historical_data:
            context_str += f"- On {row['timestamp'][:10]}, an analysis for {row['ticker']} mentioned: \"{row['analysis_text']}\"\n"
            # Include article context if available (individual article summaries)
            if row.get('article_context'):
                context_str += f"  Related articles: {row['article_context']}\n"
        context_str += "--- End of Historical Context ---\n"
        return context_str

    def answer_question(self, question):
        """
        Answers a user's question by searching the database and using the AI.
        """
        keywords = self._extract_keywords(question, num_keywords=10)
        if not keywords:
            return "I couldn't identify any keywords in your question. Please try rephrasing it."
        
        historical_data = self.db_manager.search_by_keywords(keywords)
        
        if not historical_data:
            return "I couldn't find any relevant past analyses in the database to answer your question."
        
        context_str = "Here are some relevant past analyses:\n"
        for row in historical_data:
            context_str += f"- On {row['timestamp'][:10]}, an analysis for {row['ticker']} stated: \"{row['analysis_text']}\"\n"
            # Include article context if available (individual article summaries)
            if row.get('article_context'):
                context_str += f"  Related articles: {row['article_context']}\n"
            
        # We need an AI agent to generate the final answer
        # This part requires an AI model to be available.
        try:
            from ai_agent import AIAgent
            ai_agent = AIAgent() # We might want to pass this in instead of creating it here
            return ai_agent.generate_qna_answer(question, context_str)
        except Exception as e:
            print(f"Error during Q&A answer generation: {str(e)}")
            return "I found some historical data, but I couldn't generate a final answer due to an internal error."
