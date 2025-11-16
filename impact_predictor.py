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
                'prediction': 'neutral',
                'confidence': 0.5,
                'reasoning': 'No articles available for prediction.'
            }
        
        # Calculate weighted sentiment scores
        sentiment_scores = {
            'positive': 0,
            'negative': 0,
            'mixed': 0
        }
        
        total_weight = 0
        
        for article in articles:
            sentiment = article.get('sentiment', 'neutral')
            score = article.get('sentiment_score', 0.5)
            
            # Weight by confidence score
            weight = score
            sentiment_scores[sentiment] += weight
            total_weight += weight
        
        if total_weight == 0:
            return {
                'prediction': 'neutral',
                'confidence': 0.5,
                'reasoning': 'Insufficient data for prediction.'
            }
        
        # Normalize scores
        normalized_scores = {
            k: v / total_weight for k, v in sentiment_scores.items()
        }
        
        # Determine prediction
        max_sentiment = max(normalized_scores, key=normalized_scores.get)
        confidence = normalized_scores[max_sentiment]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(normalized_scores, articles)
        
        return {
            'prediction': max_sentiment,
            'confidence': round(confidence, 2),
            'reasoning': reasoning
        }
    
    def _generate_reasoning(self, scores, articles):
        """
        Generate human-readable reasoning for the prediction
        """
        pos_pct = scores['positive'] * 100
        neg_pct = scores['negative'] * 100
        mix_pct = scores['mixed'] * 100
        
        reasoning = f"Based on {len(articles)} articles analyzed: "
        reasoning += f"{pos_pct:.1f}% positive sentiment, {neg_pct:.1f}% negative, {mix_pct:.1f}% mixed. "
        
        if scores['positive'] > 0.6:
            reasoning += "Strong positive sentiment suggests potential upward price movement."
        elif scores['negative'] > 0.6:
            reasoning += "Strong negative sentiment suggests potential downward price movement."
        elif scores['mixed'] > 0.5: # If mixed sentiment is dominant
            reasoning += "Dominant mixed sentiment indicates uncertain price direction."
        elif abs(scores['positive'] - scores['negative']) < 0.2:
            reasoning += "Balanced positive and negative sentiment indicates uncertain price direction."
        elif scores['positive'] > scores['negative']:
            reasoning += "Moderately positive sentiment suggests slight upward bias."
        else:
            reasoning += "Moderately negative sentiment suggests slight downward bias."
        
        return reasoning
