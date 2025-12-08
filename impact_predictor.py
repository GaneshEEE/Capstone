import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from typing import List, Dict, Optional
from database_manager import DatabaseManager

class ImpactPredictor:
    def __init__(self, db_manager: Optional[DatabaseManager] = None, use_ml: bool = False):
        """
        Initialize the Impact Predictor.
        
        Args:
            db_manager: DatabaseManager instance (optional, for ML model storage)
            use_ml: Whether to use ML model if available (default: False, uses rule-based)
        """
        self.db_manager = db_manager
        self.use_ml = use_ml
        self.ml_model = None
        self.vectorizer = None
        self.scaler = None
        self.label_map = None  # Initialize label_map
        self.model_path = 'models/impact_predictor_model.pkl'
        self.vectorizer_path = 'models/vectorizer.pkl'
        self.scaler_path = 'models/scaler.pkl'
        self.label_map_path = 'models/label_map.pkl'
        
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        # Try to load ML model if use_ml is True
        if self.use_ml:
            self._load_ml_model()
    
    def predict_rule_based(self, articles):
        """
        Rule-based prediction (original method).
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
        
        # Count articles by intensity level to get actual distribution
        total_articles = len(articles)
        strongly_pos_count = sum(1 for a in articles if a.get('sentiment') == 'strongly_positive')
        moderately_pos_count = sum(1 for a in articles if a.get('sentiment') == 'moderately_positive')
        slightly_pos_count = sum(1 for a in articles if a.get('sentiment') == 'slightly_positive')
        slightly_neg_count = sum(1 for a in articles if a.get('sentiment') == 'slightly_negative')
        moderately_neg_count = sum(1 for a in articles if a.get('sentiment') == 'moderately_negative')
        strongly_neg_count = sum(1 for a in articles if a.get('sentiment') == 'strongly_negative')
        
        # Calculate percentages
        strongly_pos_pct = (strongly_pos_count / total_articles) if total_articles > 0 else 0
        moderately_pos_pct = (moderately_pos_count / total_articles) if total_articles > 0 else 0
        slightly_pos_pct = (slightly_pos_count / total_articles) if total_articles > 0 else 0
        slightly_neg_pct = (slightly_neg_count / total_articles) if total_articles > 0 else 0
        moderately_neg_pct = (moderately_neg_count / total_articles) if total_articles > 0 else 0
        strongly_neg_pct = (strongly_neg_count / total_articles) if total_articles > 0 else 0
        
        # Calculate weighted sentiment considering intensity
        # Strongly weighted more than moderately, which is weighted more than slightly
        weighted_pos = (strongly_pos_pct * 3.0) + (moderately_pos_pct * 2.0) + (slightly_pos_pct * 1.0)
        weighted_neg = (strongly_neg_pct * 3.0) + (moderately_neg_pct * 2.0) + (slightly_neg_pct * 1.0)
        
        # Net weighted sentiment
        net_weighted = weighted_pos - weighted_neg
        total_weighted = weighted_pos + weighted_neg
        
        # Determine intensity level based on actual distribution and weighted scores
        # Always pick a direction - never return neutral
        if net_weighted > 0:
            # Positive direction
            if strongly_pos_pct > 0.3 or (weighted_pos > 1.5 and net_weighted > 1.0):
                max_sentiment = 'strongly_positive'
                confidence = min(0.95, weighted_pos / total_weighted if total_weighted > 0 else 0.5)
            elif moderately_pos_pct > 0.3 or (weighted_pos > 1.0 and net_weighted > 0.5):
                max_sentiment = 'moderately_positive'
                confidence = min(0.90, weighted_pos / total_weighted if total_weighted > 0 else 0.5)
            else:
                max_sentiment = 'slightly_positive'
                confidence = min(0.85, weighted_pos / total_weighted if total_weighted > 0 else 0.5)
        elif net_weighted < 0:
            # Negative direction
            if strongly_neg_pct > 0.3 or (weighted_neg > 1.5 and abs(net_weighted) > 1.0):
                max_sentiment = 'strongly_negative'
                confidence = min(0.95, weighted_neg / total_weighted if total_weighted > 0 else 0.5)
            elif moderately_neg_pct > 0.3 or (weighted_neg > 1.0 and abs(net_weighted) > 0.5):
                max_sentiment = 'moderately_negative'
                confidence = min(0.90, weighted_neg / total_weighted if total_weighted > 0 else 0.5)
            else:
                max_sentiment = 'slightly_negative'
                confidence = min(0.85, weighted_neg / total_weighted if total_weighted > 0 else 0.5)
        else:
            # Exactly balanced (very rare) - pick based on which has more articles
            total_pos = strongly_pos_count + moderately_pos_count + slightly_pos_count
            total_neg = strongly_neg_count + moderately_neg_count + slightly_neg_count
            if total_pos >= total_neg:
                max_sentiment = 'slightly_positive'
                confidence = 0.5
            else:
                max_sentiment = 'slightly_negative'
                confidence = 0.5
        
        # Generate reasoning
        reasoning = self._generate_reasoning(normalized_scores, articles, max_sentiment)
        
        return {
            'prediction': max_sentiment,
            'confidence': confidence,
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
    
    def predict(self, articles):
        """
        Predict stock impact - returns both rule-based and ML predictions.
        Returns: {
            'rule_based': {...},
            'ml': {...} or None,
            'combined': {...}  # Enhanced prediction combining both
        }
        """
        # Always get rule-based prediction
        rule_based = self.predict_rule_based(articles)
        
        # Get ML prediction if available
        ml_prediction = None
        if self.use_ml and self.ml_model and self.vectorizer:
            try:
                ml_prediction = self.predict_with_ml(articles)
            except Exception as e:
                print(f"ML prediction error: {str(e)}")
                ml_prediction = None
        
        # Create combined/enhanced prediction
        combined = self._combine_predictions(rule_based, ml_prediction)
        
        return {
            'rule_based': rule_based,
            'ml': ml_prediction,
            'combined': combined
        }
    
    def _combine_predictions(self, rule_based: Dict, ml_prediction: Optional[Dict]) -> Dict:
        """
        Combine rule-based and ML predictions to create an enhanced prediction.
        
        Args:
            rule_based: Rule-based prediction result
            ml_prediction: ML prediction result (can be None)
            
        Returns:
            Enhanced prediction combining both methods
        """
        if ml_prediction is None:
            # No ML prediction available, return rule-based with note
            return {
                'prediction': rule_based['prediction'],
                'confidence': rule_based['confidence'],
                'reasoning': rule_based['reasoning'] + " (ML model not available or not trained)",
                'method': 'rule_based_only'
            }
        
        # Both predictions available - combine them
        # Map predictions to numerical scores for comparison
        prediction_scores = {
            'strongly_positive': 3,
            'moderately_positive': 2,
            'slightly_positive': 1,
            'slightly_negative': -1,
            'moderately_negative': -2,
            'strongly_negative': -3
        }
        
        rule_score = prediction_scores.get(rule_based['prediction'], 0)
        ml_score = prediction_scores.get(ml_prediction['prediction'], 0)
        
        # Weighted combination (70% ML, 30% rule-based if ML confidence is high)
        ml_weight = 0.7 if ml_prediction['confidence'] > 0.6 else 0.5
        rule_weight = 1 - ml_weight
        
        combined_score = (ml_score * ml_weight * ml_prediction['confidence']) + \
                        (rule_score * rule_weight * rule_based['confidence'])
        
        # Determine final prediction based on combined score
        if combined_score >= 2.0:
            final_prediction = 'strongly_positive'
        elif combined_score >= 1.0:
            final_prediction = 'moderately_positive'
        elif combined_score >= 0.3:
            final_prediction = 'slightly_positive'
        elif combined_score <= -2.0:
            final_prediction = 'strongly_negative'
        elif combined_score <= -1.0:
            final_prediction = 'moderately_negative'
        elif combined_score <= -0.3:
            final_prediction = 'slightly_negative'
        else:
            # Close to zero, use the one with higher confidence
            if rule_based['confidence'] >= ml_prediction['confidence']:
                final_prediction = rule_based['prediction']
            else:
                final_prediction = ml_prediction['prediction']
        
        # Calculate combined confidence
        combined_confidence = (ml_prediction['confidence'] * ml_weight) + \
                             (rule_based['confidence'] * rule_weight)
        combined_confidence = min(0.95, combined_confidence)  # Cap at 95%
        
        # Create enhanced reasoning
        reasoning = f"Enhanced prediction combining rule-based analysis ({rule_based['confidence']:.0%} confidence) "
        reasoning += f"with ML model insights ({ml_prediction['confidence']:.0%} confidence). "
        reasoning += f"Rule-based: {rule_based['prediction'].replace('_', ' ')}. "
        reasoning += f"ML: {ml_prediction['prediction'].replace('_', ' ')}. "
        reasoning += f"Combined result: {final_prediction.replace('_', ' ')}."
        
        return {
            'prediction': final_prediction,
            'confidence': combined_confidence,
            'score': combined_score,
            'reasoning': reasoning,
            'method': 'combined'
        }
    
    def _load_ml_model(self):
        """Load trained ML model if available."""
        try:
            if os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path):
                self.ml_model = joblib.load(self.model_path)
                self.vectorizer = joblib.load(self.vectorizer_path)
                if os.path.exists(self.scaler_path):
                    self.scaler = joblib.load(self.scaler_path)
                # Load label_map if it exists
                if os.path.exists(self.label_map_path):
                    self.label_map = joblib.load(self.label_map_path)
                else:
                    self.label_map = None
                print("ML model loaded successfully!")
                return True
        except Exception as e:
            print(f"Could not load ML model: {str(e)}")
            print("Falling back to rule-based prediction.")
        return False
    
    def train_ml_model(self, dataset_table: str = 'ml_dataset', 
                      text_column: str = 'text',
                      label_column: str = 'label',
                      test_size: float = 0.2,
                      model_type: str = 'RandomForest'):
        """
        Train an ML model on a dataset.
        
        Args:
            dataset_table: Name of the table containing training data
            text_column: Name of the column containing text features
            label_column: Name of the column containing labels (sentiment predictions)
            test_size: Proportion of data to use for testing
            model_type: Type of model ('RandomForest' or 'GradientBoosting')
            
        Returns:
            Dictionary with training results (accuracy, report, etc.)
        """
        if not self.db_manager:
            raise ValueError("DatabaseManager required for training ML models")
        
        print(f"Loading training data from table '{dataset_table}'...")
        df = self.get_training_data(dataset_table)
        
        if df.empty:
            raise ValueError(f"No data found in table '{dataset_table}'")
        
        if text_column not in df.columns:
            raise ValueError(f"Column '{text_column}' not found in dataset")
        
        if label_column not in df.columns:
            raise ValueError(f"Column '{label_column}' not found in dataset")
        
        # Prepare features
        print("Preparing features...")
        X_text = df[text_column].fillna('').astype(str)
        y = df[label_column]
        
        # Vectorize text
        self.vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        X_text_features = self.vectorizer.fit_transform(X_text)
        
        # Get additional numerical features if available
        numerical_cols = ['sentiment_score', 'confidence', 'article_count']
        X_num = None
        for col in numerical_cols:
            if col in df.columns:
                if X_num is None:
                    X_num = df[[col]].fillna(0)
                else:
                    X_num = pd.concat([X_num, df[[col]].fillna(0)], axis=1)
        
        # Combine features
        if X_num is not None and not X_num.empty:
            self.scaler = StandardScaler()
            X_num_scaled = self.scaler.fit_transform(X_num)
            # Convert sparse matrix to dense for concatenation
            X_text_dense = X_text_features.toarray()
            X = np.hstack([X_text_dense, X_num_scaled])
        else:
            X = X_text_features
        
        # Map labels to integers if needed
        if y.dtype == 'object':
            unique_labels = sorted(y.unique())
            label_map = {label: idx for idx, label in enumerate(unique_labels)}
            y = y.map(label_map)
            self.label_map = {v: k for k, v in label_map.items()}  # Reverse map for predictions
        else:
            self.label_map = None
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y if len(y.unique()) > 1 else None
        )
        
        # Train model
        print(f"Training {model_type} model...")
        if model_type == 'RandomForest':
            self.ml_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
        elif model_type == 'GradientBoosting':
            self.ml_model = GradientBoostingClassifier(
                n_estimators=100,
                max_depth=5,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
        
        self.ml_model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.ml_model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"\nModel Training Complete!")
        print(f"Accuracy: {accuracy:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        
        # Save model
        self._save_ml_model()
        
        # Save metadata to database
        if self.db_manager:
            self.db_manager.save_model_metadata(
                model_name=f'impact_predictor_{model_type}',
                model_type=model_type,
                model_path=self.model_path,
                training_dataset=dataset_table,
                accuracy=accuracy
            )
        
        return {
            'accuracy': accuracy,
            'classification_report': classification_report(y_test, y_pred, output_dict=True),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
        }
    
    def get_training_data(self, table_name: str) -> pd.DataFrame:
        """Get training data from database."""
        if not self.db_manager:
            raise ValueError("DatabaseManager required")
        
        with self.db_manager._get_connection() as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        return df
    
    def _save_ml_model(self):
        """Save trained ML model to disk."""
        try:
            joblib.dump(self.ml_model, self.model_path)
            joblib.dump(self.vectorizer, self.vectorizer_path)
            if self.scaler:
                joblib.dump(self.scaler, self.scaler_path)
            # Save label_map if it exists
            if hasattr(self, 'label_map') and self.label_map:
                joblib.dump(self.label_map, self.label_map_path)
            print(f"Model saved to {self.model_path}")
        except Exception as e:
            print(f"Error saving model: {str(e)}")
    
    def predict_with_ml(self, articles: List[Dict]) -> Dict:
        """
        Predict using ML model if available.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            Prediction dictionary or None if model not available
        """
        # If ML model is not loaded or not available, return None
        if not self.ml_model or not self.vectorizer:
            return None
        
        try:
            # Extract features from articles
            texts = []
            sentiment_scores = []
            
            for article in articles:
                # Use summary or title as text feature
                text = article.get('summary', article.get('title', ''))
                texts.append(text if text else '')
                sentiment_scores.append(article.get('sentiment_score', 0.5))
            
            # Vectorize text
            X_text = self.vectorizer.transform(texts)
            
            # Add numerical features if scaler is available
            if self.scaler:
                X_num = np.array(sentiment_scores).reshape(-1, 1)
                X_num_scaled = self.scaler.transform(X_num)
                X = np.hstack([X_text.toarray(), X_num_scaled])
            else:
                X = X_text
            
            # Make predictions
            predictions = self.ml_model.predict(X)
            prediction_proba = self.ml_model.predict_proba(X)
            
            # Aggregate predictions (majority vote or weighted average)
            if hasattr(self, 'label_map') and self.label_map:
                # Map back to original labels
                mapped_predictions = [self.label_map.get(p, 'neutral') for p in predictions]
            else:
                # If no label_map, predictions are already in the correct format
                mapped_predictions = predictions
            
            # Get most common prediction
            from collections import Counter
            prediction_counts = Counter(mapped_predictions)
            most_common = prediction_counts.most_common(1)[0]
            final_prediction = most_common[0]
            confidence = most_common[1] / len(mapped_predictions)
            
            # Calculate average probability
            avg_proba = np.mean(prediction_proba, axis=0)
            max_proba_idx = np.argmax(avg_proba)
            confidence = float(avg_proba[max_proba_idx])
            
            return {
                'prediction': final_prediction,
                'confidence': confidence,
                'reasoning': f"ML model prediction based on {len(articles)} articles. "
                           f"Model confidence: {confidence:.2%}"
            }
        
        except Exception as e:
            print(f"Error in ML prediction: {str(e)}")
            return None

    def generate_forecast(self, current_price: float, prediction_result: Dict, days: int = 7) -> Dict:
        """
        Generate a realistic price forecast simulation based on prediction score.
        
        Args:
            current_price: Current stock price
            prediction_result: The prediction result dictionary (from predict method)
            days: Number of days to forecast
            
        Returns:
            Dictionary containing forecast data (dates, prices, target, etc.)
        """
        try:
            # Determine target movement percentage based on prediction score
            # Score ranges roughly from -3 to +3
            score = prediction_result.get('score', 0)
            
            # If score is missing, try to infer from label
            if score == 0 and 'prediction' in prediction_result:
                prediction_scores = {
                    'strongly_positive': 3.0,
                    'moderately_positive': 2.0,
                    'slightly_positive': 1.0,
                    'slightly_negative': -1.0,
                    'moderately_negative': -2.0,
                    'strongly_negative': -3.0
                }
                score = prediction_scores.get(prediction_result['prediction'], 0)
            
            # Base volatility (daily standard deviation)
            # Higher volatility for more extreme predictions
            base_volatility = 0.015  # 1.5% daily volatility
            if abs(score) > 2:
                base_volatility = 0.025  # 2.5% for strong predictions
            
            # Calculate target return over the period
            # Max expected move for score 3.0 is ~5-7% over 7 days
            target_return_pct = (score / 3.0) * 0.06
            
            # Generate daily price path
            prices = [current_price]
            dates = []
            
            from datetime import datetime, timedelta
            start_date = datetime.now()
            
            # Random walk with drift
            # drift = target_return_pct / days
            
            # We want a path that trends towards the target but isn't a straight line
            # We'll use a Brownian motion with drift
            
            current_sim_price = current_price
            
            for i in range(days):
                # Date
                date = start_date + timedelta(days=i+1)
                dates.append(date.strftime('%Y-%m-%d'))
                
                # Calculate drift component (trend)
                # We want the trend to be stronger if confidence is high
                confidence = prediction_result.get('confidence', 0.5)
                
                # Daily drift needed to reach target
                total_drift_needed = current_price * (1 + target_return_pct) - current_sim_price
                remaining_days = days - i
                daily_drift = total_drift_needed / remaining_days
                
                # Random shock (volatility)
                # Use numpy for normal distribution if available, else random
                shock = np.random.normal(0, base_volatility * current_price)
                
                # Update price
                # Weight the drift by confidence - if low confidence, more random
                # If high confidence, follows the trend more closely
                
                # Add some momentum/autocorrelation
                if i > 0:
                    prev_change = prices[-1] - prices[-2]
                    momentum = prev_change * 0.2  # Slight momentum
                else:
                    momentum = 0
                
                change = (daily_drift * confidence) + shock + momentum
                current_sim_price += change
                
                # Ensure price doesn't go negative
                current_sim_price = max(0.01, current_sim_price)
                
                prices.append(round(current_sim_price, 2))
            
            # Remove the start price from the list to match dates length
            prices = prices[1:]
            
            # Force directionality if score is significant
            # This ensures we don't have a "green" prediction with a price drop
            if prices:
                final_price = prices[-1]
                if score > 0.5 and final_price < current_price:
                    # Force it to be at least slightly positive
                    adjustment = (current_price * 1.005) - final_price
                    prices = [p + (adjustment * (i+1)/len(prices)) for i, p in enumerate(prices)]
                    prices = [round(p, 2) for p in prices]
                elif score < -0.5 and final_price > current_price:
                    # Force it to be at least slightly negative
                    adjustment = (current_price * 0.995) - final_price
                    prices = [p + (adjustment * (i+1)/len(prices)) for i, p in enumerate(prices)]
                    prices = [round(p, 2) for p in prices]

            return {
                'dates': dates,
                'prices': prices,
                'target_change_pct': round(target_return_pct * 100, 2),
                'confidence': prediction_result.get('confidence', 0),
                'prediction': prediction_result.get('prediction', 'neutral'),
                'score': score
            }
            
        except Exception as e:
            print(f"Error generating forecast: {str(e)}")
            # Fallback: simple straight line
            return {
                'dates': [(datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(days)],
                'prices': [current_price] * days,
                'target_change_pct': 0,
                'error': str(e)
            }