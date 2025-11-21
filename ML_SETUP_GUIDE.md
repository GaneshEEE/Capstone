# 🤖 ML Dataset Integration Guide

## Overview

Your news analysis application now supports Machine Learning! You can train models on external datasets to improve prediction accuracy.

## 📁 Where to Add Datasets

**Place all your datasets in the `datasets/` folder:**

```
Capstone-main/
├── datasets/          ← PUT YOUR DATASETS HERE
│   ├── your_dataset.csv
│   ├── another_dataset.json
│   └── README.md
├── models/            ← Trained models are saved here
├── dataset_loader.py  ← Utility to load datasets
├── train_model.py     ← Script to train models
└── ...
```

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `scikit-learn` - ML algorithms
- `joblib` - Model serialization
- `pandas` - Data manipulation
- (Already included: numpy, transformers, torch)

### Step 2: Get a Dataset

Download a dataset from:
- **Kaggle** (https://www.kaggle.com/datasets) - Search "financial sentiment" or "stock news"
- **UCI ML Repository** (https://archive.ics.uci.edu/)
- **Google Dataset Search** (https://datasetsearch.research.google.com/)

**Recommended datasets:**
- Financial PhraseBank
- Stock News Sentiment Dataset
- Financial News with Sentiment Labels

### Step 3: Place Dataset in `datasets/` Folder

Copy your dataset file (CSV or JSON) into the `datasets/` folder.

**Example:**
```
datasets/
└── financial_sentiment.csv
```

### Step 4: Load Dataset

**Option A: Using Python Script**

```python
from dataset_loader import DatasetLoader
from database_manager import DatabaseManager

db_manager = DatabaseManager()
db_manager.create_table()
db_manager.create_ml_tables()

loader = DatasetLoader(db_manager)
df = loader.load_csv_dataset('financial_sentiment.csv', table_name='training_data')
```

**Option B: Using Command Line**

```bash
python train_model.py
```

This interactive script will:
1. List available datasets
2. Let you choose which to load
3. Guide you through training

### Step 5: Train ML Model

**Using the training script:**

```bash
python train_model.py
```

Or programmatically:

```python
from impact_predictor import ImpactPredictor

predictor = ImpactPredictor(db_manager=db_manager, use_ml=False)
results = predictor.train_ml_model(
    dataset_table='training_data',
    text_column='text',        # Column with article text
    label_column='sentiment',   # Column with labels
    model_type='RandomForest'   # or 'GradientBoosting'
)

print(f"Accuracy: {results['accuracy']}")
```

### Step 6: Enable ML Model

Update `app.py` to use the ML model:

```python
# Change this line:
impact_predictor = ImpactPredictor()

# To this:
impact_predictor = ImpactPredictor(db_manager=db_manager, use_ml=True)
```

## 📊 Dataset Format Requirements

Your dataset should have:

1. **Text Column** - Contains news/article text
   - Examples: `text`, `content`, `title`, `article`
   
2. **Label Column** - Contains target predictions
   - Examples: `label`, `sentiment`, `prediction`
   - Values should match your prediction labels (e.g., `strongly_positive`, `moderately_negative`, etc.)

3. **Optional Numerical Features:**
   - `sentiment_score` - Sentiment confidence scores
   - `confidence` - Prediction confidence
   - `article_count` - Number of articles

### Example CSV Format:

```csv
text,label,sentiment_score
"Apple stock surges on strong earnings",strongly_positive,0.90
"Tech stocks decline amid uncertainty",moderately_negative,0.75
"Market remains stable",slightly_positive,0.60
```

### Example JSON Format:

```json
[
  {
    "text": "Company reports record profits",
    "label": "strongly_positive",
    "sentiment_score": 0.85
  },
  {
    "text": "Market shows mixed signals",
    "label": "slightly_positive",
    "sentiment_score": 0.55
  }
]
```

## 🎯 Use Cases

### 1. Improved Impact Prediction
Train on historical news + stock price data to predict market movements more accurately.

### 2. Sentiment Classification
Train on labeled sentiment datasets to improve sentiment analysis beyond rule-based methods.

### 3. News Categorization
Auto-categorize news articles (politics, tech, finance) using labeled datasets.

### 4. Trend Detection
Identify emerging topics and predict viral content.

## 🔧 Advanced Usage

### Loading Multiple Datasets

```python
loader = DatasetLoader(db_manager)

# Load different datasets with different table names
loader.load_csv_dataset('dataset1.csv', table_name='training_data')
loader.load_csv_dataset('dataset2.csv', table_name='validation_data')

# List all datasets
datasets = loader.list_available_datasets()
print(datasets)
```

### Using Different Model Types

```python
# Random Forest (faster, good for most cases)
predictor.train_ml_model(..., model_type='RandomForest')

# Gradient Boosting (slower, potentially more accurate)
predictor.train_ml_model(..., model_type='GradientBoosting')
```

### Checking Model Performance

```python
results = predictor.train_ml_model(...)

print(f"Accuracy: {results['accuracy']}")
print(f"Classification Report: {results['classification_report']}")
print(f"Confusion Matrix: {results['confusion_matrix']}")
```

## 📝 File Structure

```
Capstone-main/
├── datasets/              # ← PUT YOUR DATASETS HERE
│   ├── your_data.csv
│   └── README.md
├── models/                # Trained models (auto-created)
│   ├── impact_predictor_model.pkl
│   ├── vectorizer.pkl
│   └── scaler.pkl
├── dataset_loader.py      # Load datasets into database
├── train_model.py         # Interactive training script
├── impact_predictor.py    # Enhanced with ML capabilities
├── database_manager.py    # Enhanced with ML tables
└── app.py                 # Main application
```

## ⚠️ Important Notes

1. **Dataset Location**: Always place datasets in the `datasets/` folder
2. **File Formats**: Supports CSV, JSON, and JSONL
3. **Model Storage**: Trained models are saved in `models/` folder
4. **Fallback**: If ML model fails, automatically falls back to rule-based prediction
5. **Database**: Datasets are stored in SQLite for fast access

## 🐛 Troubleshooting

### "Dataset file not found"
- Make sure the file is in the `datasets/` folder
- Check the filename spelling

### "Column not found"
- Verify your dataset has the specified column names
- Check for typos in column names

### "No data found in table"
- Make sure you loaded the dataset before training
- Check the table name matches

### Model accuracy is low
- Try a larger dataset
- Check if labels match your prediction format
- Try different model types (RandomForest vs GradientBoosting)

## 📚 Next Steps

1. **Get a dataset** from Kaggle or other sources
2. **Place it in `datasets/` folder**
3. **Run `python train_model.py`** to train
4. **Update `app.py`** to enable ML predictions
5. **Test and compare** ML vs rule-based predictions

## 💡 Tips

- Start with smaller datasets (<10MB) to test
- Use datasets with at least 100+ samples for meaningful training
- Label format should match: `strongly_positive`, `moderately_positive`, `slightly_positive`, `slightly_negative`, `moderately_negative`, `strongly_negative`
- You can combine multiple datasets by loading them with `if_exists='append'`

---

**Need help?** Check `datasets/README.md` for more detailed instructions!

