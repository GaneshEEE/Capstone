"""
Dataset Loader Utility
Handles loading external ML datasets (CSV, JSON) into the database
"""

import pandas as pd
import os
import json
from typing import Optional, Dict, List
from database_manager import DatabaseManager

class DatasetLoader:
    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the DatasetLoader with a database manager.
        
        Args:
            db_manager: DatabaseManager instance for database operations
        """
        self.db_manager = db_manager
        self.datasets_folder = 'datasets'
        
        # Create datasets folder if it doesn't exist
        if not os.path.exists(self.datasets_folder):
            os.makedirs(self.datasets_folder)
            print(f"Created '{self.datasets_folder}' folder for your datasets")
    
    def load_csv_dataset(self, csv_path: str, table_name: str = 'ml_dataset', 
                        if_exists: str = 'replace') -> pd.DataFrame:
        """
        Load a CSV dataset into the database.
        
        Args:
            csv_path: Path to the CSV file (can be relative to datasets folder or absolute)
            table_name: Name of the table to store the data
            if_exists: What to do if table exists ('replace', 'append', 'fail')
            
        Returns:
            DataFrame containing the loaded data
        """
        # Check if path is relative to datasets folder
        if not os.path.isabs(csv_path):
            full_path = os.path.join(self.datasets_folder, csv_path)
        else:
            full_path = csv_path
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Dataset file not found: {full_path}")
        
        print(f"Loading dataset from {full_path}...")
        df = pd.read_csv(full_path)
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Store in database
        with self.db_manager._get_connection() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            conn.commit()
        
        print(f"Dataset stored in table '{table_name}'")
        return df
    
    def load_json_dataset(self, json_path: str, table_name: str = 'ml_dataset',
                         if_exists: str = 'replace') -> pd.DataFrame:
        """
        Load a JSON dataset into the database.
        
        Args:
            json_path: Path to the JSON file (can be relative to datasets folder or absolute)
            table_name: Name of the table to store the data
            if_exists: What to do if table exists ('replace', 'append', 'fail')
            
        Returns:
            DataFrame containing the loaded data
        """
        # Check if path is relative to datasets folder
        if not os.path.isabs(json_path):
            full_path = os.path.join(self.datasets_folder, json_path)
        else:
            full_path = json_path
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"Dataset file not found: {full_path}")
        
        print(f"Loading dataset from {full_path}...")
        
        # Try to load as JSON array or JSON lines
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    df = pd.DataFrame(data)
                else:
                    # If it's a dict, try to convert
                    df = pd.json_normalize(data)
        except json.JSONDecodeError:
            # Try JSONL format (one JSON object per line)
            df = pd.read_json(full_path, lines=True)
        
        print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
        
        # Store in database
        with self.db_manager._get_connection() as conn:
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            conn.commit()
        
        print(f"Dataset stored in table '{table_name}'")
        return df
    
    def get_dataset(self, table_name: str = 'ml_dataset') -> pd.DataFrame:
        """
        Retrieve a dataset from the database.
        
        Args:
            table_name: Name of the table to retrieve
            
        Returns:
            DataFrame containing the dataset
        """
        with self.db_manager._get_connection() as conn:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        return df
    
    def list_available_datasets(self) -> List[str]:
        """
        List all CSV and JSON files in the datasets folder.
        
        Returns:
            List of dataset file names
        """
        if not os.path.exists(self.datasets_folder):
            return []
        
        datasets = []
        for file in os.listdir(self.datasets_folder):
            if file.endswith(('.csv', '.json', '.jsonl')):
                datasets.append(file)
        
        return sorted(datasets)
    
    def get_dataset_info(self, table_name: str = 'ml_dataset') -> Dict:
        """
        Get information about a dataset in the database.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with dataset information
        """
        try:
            df = self.get_dataset(table_name)
            return {
                'table_name': table_name,
                'rows': len(df),
                'columns': list(df.columns),
                'column_types': df.dtypes.astype(str).to_dict(),
                'sample_data': df.head(5).to_dict('records')
            }
        except Exception as e:
            return {'error': str(e)}


if __name__ == '__main__':
    # Example usage
    from database_manager import DatabaseManager
    
    db_manager = DatabaseManager()
    db_manager.create_table()
    
    loader = DatasetLoader(db_manager)
    
    # List available datasets
    print("Available datasets:")
    datasets = loader.list_available_datasets()
    for ds in datasets:
        print(f"  - {ds}")
    
    # Example: Load a dataset (uncomment when you have a dataset)
    # df = loader.load_csv_dataset('your_dataset.csv', table_name='training_data')
    # print(f"\nLoaded dataset info:")
    # print(loader.get_dataset_info('training_data'))

