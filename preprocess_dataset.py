"""
Dataset Preprocessing Script
Converts simple labels (positive/negative/neutral) to expected format
(strongly_positive, moderately_positive, slightly_positive, etc.)
Run this once to update your dataset file.
"""

import pandas as pd
import os
import re
import sys
import csv
from pathlib import Path
from sentiment_analyzer import SentimentAnalyzer

def determine_intensity(text, base_sentiment):
    """
    Determine intensity level based on text content.
    Returns: 'strongly', 'moderately', or 'slightly'
    """
    if not text or pd.isna(text):
        return 'moderately'  # Default to moderate
    
    text_lower = str(text).lower()
    
    # Strong intensity indicators
    strong_positive_words = [
        'surge', 'soar', 'rally', 'breakthrough', 'record', 'exceptional',
        'outstanding', 'excellent', 'remarkable', 'significant', 'major',
        'substantial', 'dramatic', 'massive', 'huge', 'tremendous',
        'doubled', 'tripled', 'exceeded', 'beat expectations', 'strong growth',
        'surpassed', 'milestone', 'achievement', 'successful', 'profitable'
    ]
    
    strong_negative_words = [
        'crash', 'plunge', 'collapse', 'crisis', 'disaster', 'devastating',
        'severe', 'critical', 'major loss', 'significant decline', 'sharp drop',
        'bankruptcy', 'lawsuit', 'scandal', 'investigation', 'failed',
        'worst', 'terrible', 'catastrophic', 'layoff', 'layoffs', 'shutdown'
    ]
    
    # Moderate intensity indicators
    moderate_positive_words = [
        'growth', 'increase', 'improve', 'gain', 'rise', 'up', 'positive',
        'favorable', 'good', 'better', 'profit', 'success', 'expansion',
        'develop', 'progress', 'advance', 'enhance'
    ]
    
    moderate_negative_words = [
        'decline', 'decrease', 'fall', 'down', 'loss', 'drop', 'negative',
        'concern', 'challenge', 'difficulty', 'miss', 'weaker', 'reduction',
        'lower', 'weak', 'struggle'
    ]
    
    # Count intensity indicators
    if base_sentiment == 'positive':
        strong_count = sum(1 for word in strong_positive_words if word in text_lower)
        moderate_count = sum(1 for word in moderate_positive_words if word in text_lower)
        
        # Check for percentage/numbers that indicate strong sentiment
        percentages = re.findall(r'(\d+(?:\.\d+)?%)', text)
        large_numbers = re.findall(r'\b(\d{2,})\b', text)
        
        # Check for words like "doubled", "tripled", etc.
        multiplier_words = ['double', 'triple', 'quadruple', 'fivefold', 'tenfold']
        has_multiplier = any(word in text_lower for word in multiplier_words)
        
        if strong_count >= 2 or (strong_count >= 1 and (len(percentages) > 0 or has_multiplier)):
            return 'strongly'
        elif strong_count >= 1 or moderate_count >= 2:
            return 'moderately'
        else:
            return 'slightly'
    
    elif base_sentiment == 'negative':
        strong_count = sum(1 for word in strong_negative_words if word in text_lower)
        moderate_count = sum(1 for word in moderate_negative_words if word in text_lower)
        
        # Check for severe indicators
        severe_indicators = ['bankruptcy', 'lawsuit', 'crisis', 'collapse', 'shutdown']
        has_severe = any(indicator in text_lower for indicator in severe_indicators)
        
        if strong_count >= 2 or has_severe:
            return 'strongly'
        elif strong_count >= 1 or moderate_count >= 2:
            return 'moderately'
        else:
            return 'slightly'
    
    else:  # neutral
        return 'slightly'  # Neutral always maps to slightly_positive


def preprocess_dataset(input_file, output_file=None, backup=True):
    """
    Preprocess dataset to convert labels to expected format.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file (default: overwrites input)
        backup: Whether to create a backup of original file
    """
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: File '{input_file}' not found!")
        return False
    
    # Create backup if requested
    if backup:
        backup_file = input_file.replace('.csv', '_backup.csv')
        if not os.path.exists(backup_file):
            print(f"📦 Creating backup: {backup_file}")
            df_backup = pd.read_csv(input_file, header=None)
            df_backup.to_csv(backup_file, header=False, index=False, quoting=csv.QUOTE_ALL, doublequote=True)
        else:
            print(f"ℹ️  Backup already exists: {backup_file}")
    
    # Read dataset
    print(f"📖 Reading dataset: {input_file}")
    # Read with proper quoting to handle quoted fields
    df = pd.read_csv(input_file, header=None, names=["label", "text"], quoting=csv.QUOTE_ALL)
    print(f"   Loaded {len(df)} rows")
    
    # Show original label distribution
    print("\n📊 Original Label Distribution:")
    original_counts = df['label'].value_counts()
    for label, count in original_counts.items():
        pct = (count / len(df)) * 100
        print(f"   {label}: {count} ({pct:.1f}%)")
    
    # Initialize sentiment analyzer for neutral labels
    print("\n🔄 Initializing sentiment analyzer for neutral label analysis...")
    sentiment_analyzer = SentimentAnalyzer()
    
    # Map labels based on text content using sentiment analysis
    print("🔄 Analyzing text content using sentiment analysis...")
    
    # Count labels that need analysis
    simple_labels = df['label'].str.lower().str.strip().isin(['positive', 'negative', 'neutral'])
    labels_to_analyze = simple_labels.sum()
    
    if labels_to_analyze > 0:
        print(f"   Analyzing {labels_to_analyze} labels using FinBERT sentiment analysis...")
        print("   This may take a few minutes...")
    
    def map_label_with_sentiment(row, sentiment_analyzer):
        """Map label based on actual sentiment analysis of text content."""
        label = str(row['label']).lower().strip()
        text = row['text'] if 'text' in row else ''
        
        # If already in expected format, keep it
        expected_labels = [
            'strongly_positive', 'moderately_positive', 'slightly_positive',
            'slightly_negative', 'moderately_negative', 'strongly_negative'
        ]
        if label in expected_labels:
            return label
        
        # For simple labels (positive/negative/neutral), use sentiment analysis
        if label in ['positive', 'negative', 'neutral']:
            if text and pd.notna(text) and str(text).strip():
                try:
                    # Use FinBERT to analyze actual sentiment
                    sentiment_result = sentiment_analyzer.analyze(str(text))
                    detected_label = sentiment_result['label']
                    # Use the detected sentiment label directly
                    return detected_label
                except Exception as e:
                    print(f"   Warning: Error analyzing sentiment for text: {str(e)[:50]}...")
                    # Fallback based on original label
                    if label == 'positive':
                        return 'moderately_positive'
                    elif label == 'negative':
                        return 'moderately_negative'
                    else:
                        return 'slightly_positive'
            else:
                # Empty text, fallback based on original label
                if label == 'positive':
                    return 'moderately_positive'
                elif label == 'negative':
                    return 'moderately_negative'
                else:
                    return 'slightly_positive'
        
        # Unknown label format, default fallback
        return 'slightly_positive'
    
    # Apply mapping with sentiment analysis for all simple labels
    df['label'] = df.apply(lambda row: map_label_with_sentiment(row, sentiment_analyzer), axis=1)
    
    # Show new label distribution
    print("\n📊 New Label Distribution:")
    new_counts = df['label'].value_counts()
    for label, count in new_counts.items():
        pct = (count / len(df)) * 100
        print(f"   {label}: {count} ({pct:.1f}%)")
    
    # Determine output file
    if output_file is None:
        output_file = input_file
    
    # Save processed dataset
    print(f"\n💾 Saving processed dataset: {output_file}")
    # Use csv.QUOTE_ALL to match original CSV format (quotes around all fields)
    # Use doublequote=False to prevent escaping quotes incorrectly
    df.to_csv(output_file, header=False, index=False, quoting=csv.QUOTE_ALL, doublequote=True)
    print("✅ Dataset preprocessing complete!")
    
    return True


def main():
    print("=" * 60)
    print("Dataset Preprocessing Script")
    print("=" * 60)
    print("\nThis script converts simple labels (positive/negative/neutral)")
    print("to expected format (strongly_positive, moderately_positive, etc.)")
    print("based on actual text content analysis.\n")
    
    # Get input file
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Look for datasets in datasets folder
        datasets_folder = 'datasets'
        if os.path.exists(datasets_folder):
            csv_files = [f for f in os.listdir(datasets_folder) if f.endswith('.csv')]
            if csv_files:
                print("📁 Available datasets:")
                for i, f in enumerate(csv_files, 1):
                    print(f"   {i}. {f}")
                choice = input(f"\nEnter dataset number or filename (1-{len(csv_files)}): ").strip()
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(csv_files):
                        input_file = os.path.join(datasets_folder, csv_files[idx])
                    else:
                        input_file = os.path.join(datasets_folder, choice)
                except ValueError:
                    input_file = os.path.join(datasets_folder, choice)
            else:
                input_file = input("Enter path to CSV file: ").strip()
        else:
            input_file = input("Enter path to CSV file: ").strip()
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ Error: File '{input_file}' not found!")
        return
    
    # Ask about output file
    output_choice = input("\nOverwrite original file? (y/n) [default: y]: ").strip().lower()
    output_file = None if output_choice != 'n' else input("Enter output filename: ").strip()
    
    # Ask about backup
    backup_choice = input("Create backup of original? (y/n) [default: y]: ").strip().lower()
    backup = backup_choice != 'n'
    
    # Process dataset
    success = preprocess_dataset(input_file, output_file, backup)
    
    if success:
        print("\n✨ Done! Your dataset now has the expected label format.")
        print("   You can now use it directly without any mapping.")
    else:
        print("\n❌ Preprocessing failed!")


if __name__ == '__main__':
    main()

