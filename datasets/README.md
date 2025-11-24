# 📊 Datasets Folder

## Where to Add Your Datasets

**Place all your ML datasets (CSV, JSON, JSONL files) in this `datasets/` folder.**

### Supported Formats:
- **CSV files** (`.csv`) - Most common format
- **JSON files** (`.json`) - Array of objects or nested JSON
- **JSONL files** (`.jsonl`) - One JSON object per line

## How to Use Datasets

### 1. Download Datasets from the Internet

You can get datasets from:
- **Kaggle** (https://www.kaggle.com/datasets) - Search for "stock news", "financial sentiment", "market data"
- **UCI Machine Learning Repository** (https://archive.ics.uci.edu/)
- **Google Dataset Search** (https://datasetsearch.research.google.com/)
- **GitHub** - Many open-source datasets
- **Your own data** - Export from databases, APIs, etc.

### 2. Place Dataset in This Folder

Simply copy your dataset file (e.g., `stock_news_dataset.csv`) into this `datasets/` folder.

### 3. Load Dataset Using Python

```python
from dataset_loader import DatasetLoader
from database_manager import DatabaseManager

# Initialize
db_manager = DatabaseManager()
db_manager.create_table()
db_manager.create_ml_tables()  # Create ML tables

loader = DatasetLoader(db_manager)

# Load a CSV dataset
df = loader.load_csv_dataset('stock_news_dataset.csv', table_name='training_data')

# Or load a JSON dataset
df = loader.load_json_dataset('sentiment_data.json', table_name='training_data')

# View dataset info
info = loader.get_dataset_info('training_data')
print(info)
```

### 4. Train ML Model

```python
from impact_predictor import ImpactPredictor

predictor = ImpactPredictor(db_manager=db_manager, use_ml=True)

# Train model on your dataset
# Make sure your dataset has:
# - A text column (e.g., 'text', 'content', 'title')
# - A label column (e.g., 'label', 'sentiment', 'prediction')
results = predictor.train_ml_model(
    dataset_table='training_data',
    text_column='text',      # Column name with text content
    label_column='label',     # Column name with labels
    model_type='RandomForest'  # or 'GradientBoosting'
)

print(f"Model accuracy: {results['accuracy']}")
```

## Example Dataset Structure

### For Sentiment Analysis:
```csv
text,label,sentiment_score
"Apple stock surges on strong earnings",positive,0.85
"Tech stocks decline amid market uncertainty",negative,0.72
"Market remains stable with mixed signals",neutral,0.50
```

### For Impact Prediction:
```csv
text,label,article_count,sentiment_score
"Multiple positive news articles about company growth",strongly_positive,5,0.90
"Mixed news with slight positive bias",slightly_positive,3,0.60
"Negative news about company losses",moderately_negative,2,0.75
```

## Recommended Datasets

### Financial News & Sentiment:
1. **Financial PhraseBank** - Financial sentiment dataset
2. **Stock News Dataset** - News articles with stock price impact
3. **Financial News Sentiment** - Labeled financial news

### Where to Find:
- Search Kaggle for: "financial sentiment", "stock news", "market sentiment"
- Look for datasets with columns like: `text`, `sentiment`, `label`, `score`

## Dataset Requirements

Your dataset should have:
- **Text column**: Contains the news/article text
- **Label column**: Contains the target prediction (e.g., sentiment labels)
- **Optional**: Numerical features like `sentiment_score`, `confidence`, `article_count`

## Loading Datasets via Command Line

You can also use the dataset_loader.py script directly:

```bash
python dataset_loader.py
```

This will list all available datasets in the folder.

## Notes

- Large datasets (>100MB) may take time to load
- The dataset will be stored in SQLite database for fast access
- You can load multiple datasets with different table names
- Use `if_exists='append'` to add to existing tables

