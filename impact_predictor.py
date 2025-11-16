class ImpactPredictor:
    def __init__(self):
        pass
    
    def predict(self, articles):
        """
        Predict stock impact based on sentiment analysis
        Returns: {'prediction': 'positive'/'negative'/'neutral', 'confidence': float, 'reasoning': str}
        """
        if not articles:
            return {
                'prediction': 'slightly_positive',
                'confidence': 0.5,
                'reasoning': 'No articles available for prediction.'
            }
        
        # Count articles by sentiment (both weighted and unweighted)
        sentiment_counts = {
            'positive': 0,
            'negative': 0,
            'mixed': 0,
            'neutral': 0
        }
        
        sentiment_scores = {
            'positive': 0,
            'negative': 0,
            'mixed': 0,
            'neutral': 0
        }
        
        total_weight = 0
        
        for article in articles:
            sentiment = article.get('sentiment', 'neutral')
            score = article.get('sentiment_score', 0.5)
            
            # Map intensity levels to base sentiments for counting
            base_sentiment = sentiment
            if sentiment.startswith('strongly_') or sentiment.startswith('moderately_') or sentiment.startswith('slightly_'):
                if 'positive' in sentiment:
                    base_sentiment = 'positive'
                elif 'negative' in sentiment:
                    base_sentiment = 'negative'
            elif sentiment == 'mixed':
                base_sentiment = 'neutral'  # Treat mixed as neutral for counting
            
            # Count articles by base sentiment
            sentiment_counts[base_sentiment] = sentiment_counts.get(base_sentiment, 0) + 1
            
            # Weight by confidence score (higher confidence = more weight)
            # Also weight by intensity: strongly > moderately > slightly
            intensity_multiplier = 1.0
            if sentiment.startswith('strongly_'):
                intensity_multiplier = 1.2
            elif sentiment.startswith('moderately_'):
                intensity_multiplier = 1.0
            elif sentiment.startswith('slightly_'):
                intensity_multiplier = 0.8
            
            weight = score * intensity_multiplier
            sentiment_scores[base_sentiment] = sentiment_scores.get(base_sentiment, 0) + weight
            total_weight += weight
        
        if total_weight == 0:
            return {
                'prediction': 'slightly_positive',
                'confidence': 0.5,
                'reasoning': 'Insufficient data for prediction.'
            }
        
        # Normalize scores
        normalized_scores = {
            k: v / total_weight for k, v in sentiment_scores.items()
        }
        
        # Calculate percentages (for reasoning)
        total_articles = len(articles)
        sentiment_percentages = {
            k: (v / total_articles * 100) if total_articles > 0 else 0 
            for k, v in sentiment_counts.items()
        }
        
        # Determine prediction with smarter logic
        # Only predict "mixed" if there's truly no clear winner
        pos_score = normalized_scores.get('positive', 0)
        neg_score = normalized_scores.get('negative', 0)
        mix_score = normalized_scores.get('mixed', 0)
        neu_score = normalized_scores.get('neutral', 0)
        
        # Combine neutral with mixed for comparison
        combined_neutral_mixed = mix_score + neu_score
        
        # Determine prediction with intensity levels
        # Calculate the net sentiment (positive - negative)
        net_sentiment = pos_score - neg_score
        total_directional = pos_score + neg_score  # How much is actually positive or negative (vs neutral/mixed)
        
        # Determine intensity level based on scores and differences
        # Always pick a direction - never return neutral
        if net_sentiment > 0:
            # Positive direction
            if pos_score > 0.6 and net_sentiment > 0.25:
                max_sentiment = 'strongly_positive'
                confidence = pos_score
            elif pos_score > 0.45 and net_sentiment > 0.15:
                max_sentiment = 'moderately_positive'
                confidence = pos_score
            else:
                max_sentiment = 'slightly_positive'
                confidence = pos_score
        elif net_sentiment < 0:
            # Negative direction
            if neg_score > 0.6 and abs(net_sentiment) > 0.25:
                max_sentiment = 'strongly_negative'
                confidence = neg_score
            elif neg_score > 0.45 and abs(net_sentiment) > 0.15:
                max_sentiment = 'moderately_negative'
                confidence = neg_score
            else:
                max_sentiment = 'slightly_negative'
                confidence = neg_score
        else:
            # Exactly balanced (very rare) - always pick a direction
            # Pick based on which has slightly higher confidence
            if pos_score >= neg_score:
                max_sentiment = 'slightly_positive'
                confidence = pos_score
            else:
                max_sentiment = 'slightly_negative'
                confidence = neg_score
        
        # Generate reasoning
        reasoning = self._generate_reasoning(normalized_scores, articles, max_sentiment)
        
        return {
            'prediction': max_sentiment,
            'confidence': round(confidence, 2),
            'reasoning': reasoning
        }
    
    def _generate_reasoning(self, scores, articles, prediction_label):
        """
        Generate human-readable reasoning for the prediction
        """
        # Count actual articles by all 6 intensity levels
        total = len(articles)
        strongly_pos = sum(1 for a in articles if a.get('sentiment') == 'strongly_positive')
        moderately_pos = sum(1 for a in articles if a.get('sentiment') == 'moderately_positive')
        slightly_pos = sum(1 for a in articles if a.get('sentiment') == 'slightly_positive')
        slightly_neg = sum(1 for a in articles if a.get('sentiment') == 'slightly_negative')
        moderately_neg = sum(1 for a in articles if a.get('sentiment') == 'moderately_negative')
        strongly_neg = sum(1 for a in articles if a.get('sentiment') == 'strongly_negative')
        
        # Calculate percentages
        strongly_pos_pct = (strongly_pos / total * 100) if total > 0 else 0
        moderately_pos_pct = (moderately_pos / total * 100) if total > 0 else 0
        slightly_pos_pct = (slightly_pos / total * 100) if total > 0 else 0
        slightly_neg_pct = (slightly_neg / total * 100) if total > 0 else 0
        moderately_neg_pct = (moderately_neg / total * 100) if total > 0 else 0
        strongly_neg_pct = (strongly_neg / total * 100) if total > 0 else 0
        
        reasoning = f"Based on {len(articles)} articles analyzed: "
        reasoning += f"{strongly_pos_pct:.1f}% strongly positive, {moderately_pos_pct:.1f}% moderately positive, {slightly_pos_pct:.1f}% slightly positive, "
        reasoning += f"{slightly_neg_pct:.1f}% slightly negative, {moderately_neg_pct:.1f}% moderately negative, {strongly_neg_pct:.1f}% strongly negative. "
        
        pos_score = scores.get('positive', 0)
        neg_score = scores.get('negative', 0)
        net_sentiment = pos_score - neg_score
        
        # Generate reasoning based on intensity level
        if prediction_label == 'strongly_positive':
            reasoning += "Strong positive sentiment with clear upward momentum suggests significant potential for price appreciation."
        elif prediction_label == 'moderately_positive':
            reasoning += "Moderate positive sentiment indicates favorable conditions with potential for modest upward movement."
        elif prediction_label == 'slightly_positive':
            reasoning += "Slight positive bias suggests minimal upward pressure, but sentiment is not strongly bullish."
        elif prediction_label == 'slightly_negative':
            reasoning += "Slight negative bias suggests minimal downward pressure, but sentiment is not strongly bearish."
        elif prediction_label == 'moderately_negative':
            reasoning += "Moderate negative sentiment indicates unfavorable conditions with potential for modest downward movement."
        elif prediction_label == 'strongly_negative':
            reasoning += "Strong negative sentiment with clear downward momentum suggests significant potential for price decline."
        else:
            # Fallback
            if net_sentiment > 0:
                reasoning += "Positive sentiment suggests potential upward price movement."
            elif net_sentiment < 0:
                reasoning += "Negative sentiment suggests potential downward price movement."
            else:
                reasoning += "Balanced sentiment indicates uncertain price direction."
        
        return reasoning
