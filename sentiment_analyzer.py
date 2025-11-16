from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

class SentimentAnalyzer:
    def __init__(self):
        """
        Initialize FinBERT model for financial sentiment analysis
        """
        print("Loading FinBERT model...")
        try:
            # Using ProsusAI/finbert model - a financial sentiment analysis model
            self.model_name = "ProsusAI/finbert"
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self.model.eval()
            print("FinBERT model loaded successfully!")
        except Exception as e:
            print(f"Error loading FinBERT: {str(e)}")
            print("Falling back to basic sentiment analysis...")
            self.model = None
            self.tokenizer = None
    
    def analyze(self, text):
        """
        Analyze sentiment of financial text
        Returns: {'label': 'positive'/'negative'/'neutral', 'score': float}
        """
        if not text or len(text.strip()) == 0:
            return {'label': 'mixed', 'score': 0.5}
        
        if self.model is None:
            # Fallback to simple keyword-based sentiment
            return self._simple_sentiment(text)
        
        try:
            # Tokenize and predict
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # FinBERT labels: positive, negative, neutral (will be mapped to mixed)
            labels = ['positive', 'negative', 'mixed']
            scores = predictions[0].tolist()
            
            # Get the label with highest score
            max_idx = np.argmax(scores)
            label = labels[max_idx]
            score = scores[max_idx]
            
            return {
                'label': label,
                'score': float(score)
            }
        
        except Exception as e:
            print(f"Error in sentiment analysis: {str(e)}")
            return self._simple_sentiment(text)
    
    def _simple_sentiment(self, text):
        """
        Simple keyword-based sentiment analysis fallback
        """
        text_lower = text.lower()
        
        positive_words = ['profit', 'gain', 'rise', 'up', 'growth', 'beat', 'surge', 
                         'rally', 'soar', 'increase', 'positive', 'bullish', 'strong']
        negative_words = ['loss', 'fall', 'down', 'decline', 'miss', 'drop', 'plunge',
                         'crash', 'decrease', 'negative', 'bearish', 'weak', 'lawsuit']
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            return {'label': 'positive', 'score': 0.7}
        elif neg_count > pos_count:
            return {'label': 'negative', 'score': 0.7}
        else:
            return {'label': 'mixed', 'score': 0.5}
