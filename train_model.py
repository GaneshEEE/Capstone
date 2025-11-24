"""
Script to train ML models on datasets
Run this after loading your dataset to train a prediction model
"""

from dataset_loader import DatasetLoader
from database_manager import DatabaseManager
from impact_predictor import ImpactPredictor
import sys

def main():
    print("=" * 60)
    print("ML Model Training Script")
    print("=" * 60)
    
    # Initialize components
    db_manager = DatabaseManager()
    db_manager.create_table()
    db_manager.create_ml_tables()
    
    loader = DatasetLoader(db_manager)
    predictor = ImpactPredictor(db_manager=db_manager, use_ml=False)
    
    # List available datasets
    print("\n📁 Available datasets in 'datasets/' folder:")
    datasets = loader.list_available_datasets()
    if not datasets:
        print("   No datasets found! Please add CSV or JSON files to the 'datasets/' folder.")
        print("   See datasets/README.md for instructions.")
        return
    
    for i, ds in enumerate(datasets, 1):
        print(f"   {i}. {ds}")
    
    # Ask user which dataset to use
    if len(sys.argv) > 1:
        dataset_name = sys.argv[1]
    else:
        dataset_name = input("\nEnter dataset filename (or press Enter for first dataset): ").strip()
        if not dataset_name:
            dataset_name = datasets[0]
    
    if dataset_name not in datasets:
        print(f"❌ Dataset '{dataset_name}' not found!")
        return
    
    # Load dataset
    print(f"\n📊 Loading dataset: {dataset_name}")
    try:
        table_name = input("Enter table name (or press Enter for 'training_data'): ").strip()
        if not table_name:
            table_name = 'training_data'
        
        # Determine file type and load
        if dataset_name.endswith('.csv'):
            df = loader.load_csv_dataset(dataset_name, table_name=table_name)
        elif dataset_name.endswith(('.json', '.jsonl')):
            df = loader.load_json_dataset(dataset_name, table_name=table_name)
        else:
            print("❌ Unsupported file format!")
            return
        
        # Show dataset info
        print("\n📋 Dataset Info:")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}")
        print(f"\n   First few rows:")
        print(df.head())
        
        # Register dataset
        description = input("\nEnter dataset description (optional): ").strip()
        db_manager.register_dataset(
            dataset_name=dataset_name,
            table_name=table_name,
            description=description,
            rows_count=len(df),
            columns_count=len(df.columns)
        )
        
    except Exception as e:
        print(f"❌ Error loading dataset: {str(e)}")
        return
    
    # Ask for column names
    print("\n🔍 Dataset columns:")
    for i, col in enumerate(df.columns, 1):
        print(f"   {i}. {col}")
    
    text_column = input("\nEnter text column name (e.g., 'text', 'content', 'title'): ").strip()
    if text_column not in df.columns:
        print(f"❌ Column '{text_column}' not found!")
        return
    
    label_column = input("Enter label column name (e.g., 'label', 'sentiment', 'prediction'): ").strip()
    if label_column not in df.columns:
        print(f"❌ Column '{label_column}' not found!")
        return
    
    # Ask for model type
    model_type = input("\nEnter model type (RandomForest or GradientBoosting) [default: RandomForest]: ").strip()
    if not model_type:
        model_type = 'RandomForest'
    if model_type not in ['RandomForest', 'GradientBoosting']:
        print("❌ Invalid model type! Using RandomForest.")
        model_type = 'RandomForest'
    
    # Train model
    print(f"\n🚀 Training {model_type} model...")
    print("   This may take a few minutes...")
    
    try:
        results = predictor.train_ml_model(
            dataset_table=table_name,
            text_column=text_column,
            label_column=label_column,
            model_type=model_type
        )
        
        print("\n✅ Model training complete!")
        print(f"   Accuracy: {results['accuracy']:.4f}")
        print(f"   Model saved to: models/impact_predictor_model.pkl")
        
        # Ask if user wants to use ML model
        use_ml = input("\nUse ML model for predictions? (y/n) [default: n]: ").strip().lower()
        if use_ml == 'y':
            print("\n✅ ML model will be used for predictions!")
            print("   Update app.py to set use_ml=True in ImpactPredictor initialization")
        else:
            print("\nℹ️  ML model trained but not activated.")
            print("   To use it, update app.py: ImpactPredictor(db_manager=db_manager, use_ml=True)")
        
    except Exception as e:
        print(f"❌ Error training model: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()

