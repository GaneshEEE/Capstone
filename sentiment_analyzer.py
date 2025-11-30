
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
        Returns: {'label': intensity_level, 'score': float}
        Intensity levels: strongly_positive, moderately_positive, slightly_positive, 
                          slightly_negative, moderately_negative, strongly_negative
        """
        if not text or len(text.strip()) == 0:
            return {'label': 'slightly_positive', 'score': 0.5}  # Default to slightly positive
        
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
            
            # FinBERT labels: positive, negative, neutral
            labels = ['positive', 'negative', 'neutral']
            scores = predictions[0].tolist()
            
            pos_score = scores[0]
            neg_score = scores[1]
            neu_score = scores[2]
            
            # Calculate net sentiment and determine intensity level
            # Always pick a direction - never return neutral
            net_sentiment = pos_score - neg_score
            
            # Determine intensity level based on scores
            if net_sentiment > 0:
                # Positive direction - determine intensity
                if pos_score > 0.75 and net_sentiment > 0.3:
                    label = 'strongly_positive'
                    score = pos_score
                elif pos_score > 0.6 and net_sentiment > 0.2:
                    label = 'moderately_positive'
                    score = pos_score
                else:
                    label = 'slightly_positive'
                    score = pos_score
            elif net_sentiment < 0:
                # Negative direction - determine intensity
                if neg_score > 0.75 and abs(net_sentiment) > 0.3:
                    label = 'strongly_negative'
                    score = neg_score
                elif neg_score > 0.6 and abs(net_sentiment) > 0.2:
                    label = 'moderately_negative'
                    score = neg_score
                else:
                    label = 'slightly_negative'
                    score = neg_score
            else:
                # Exactly balanced (very rare) - pick based on which has slightly higher confidence
                if pos_score >= neg_score:
                    label = 'slightly_positive'
                    score = pos_score
                else:
                    label = 'slightly_negative'
                    score = neg_score
            
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
        Returns intensity levels like the main analyzer
        """
        text_lower = text.lower()
        
        positive_words = ['profit', 'gain', 'rise', 'up', 'growth', 'beat', 'surge', 
                         'rally', 'soar', 'increase', 'positive', 'bullish', 'strong',
                         'excellent', 'outstanding', 'record', 'breakthrough']
        negative_words = ['loss', 'fall', 'down', 'decline', 'miss', 'drop', 'plunge',
                         'crash', 'decrease', 'negative', 'bearish', 'weak', 'lawsuit',
                         'disappointing', 'concern', 'warning', 'crisis']
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            # Determine intensity based on word count difference
            diff = pos_count - neg_count
            if diff >= 3:
                return {'label': 'strongly_positive', 'score': 0.8}
            elif diff >= 2:
                return {'label': 'moderately_positive', 'score': 0.7}
            else:
                return {'label': 'slightly_positive', 'score': 0.6}
        elif neg_count > pos_count:
            # Determine intensity based on word count difference
            diff = neg_count - pos_count
            if diff >= 3:
                return {'label': 'strongly_negative', 'score': 0.8}
            elif diff >= 2:
                return {'label': 'moderately_negative', 'score': 0.7}
            else:
                return {'label': 'slightly_negative', 'score': 0.6}
        else:
            # No clear sentiment - default to slightly positive
            return {'label': 'slightly_positive', 'score': 0.5}
