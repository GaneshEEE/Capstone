import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import datetime

class SheetsManager:
    """
    Manages interactions with Google Sheets for the Stock Watchlist.
    """
    def __init__(self, credentials_file='credentials.json'):
        self.credentials_file = credentials_file
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        self.client = None
        
    def connect(self):
        """
        Connects to the Google Sheets API using service account credentials.
        Returns True if successful, False otherwise.
        """
        if not os.path.exists(self.credentials_file):
            print(f"Error: Credentials file '{self.credentials_file}' not found.")
            return False
            
        try:
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_file, self.scope)
            self.client = gspread.authorize(creds)
            print("Successfully connected to Google Sheets API.")
            return True
        except Exception as e:
            print(f"Error connecting to Google Sheets: {str(e)}")
            return False

    def get_tickers_from_sheet(self, sheet_name):
        """
        Reads tickers from Column A of the specified sheet.
        Assumes Row 1 is a header.
        """
        if not self.client:
            if not self.connect():
                return []
        
        try:
            sheet = self.client.open(sheet_name).sheet1
            # Get all values in column A
            tickers = sheet.col_values(1)
            
            # Remove header if it exists (assuming "Ticker" or similar)
            if tickers and (tickers[0].lower() == 'ticker' or tickers[0].lower() == 'symbol'):
                tickers = tickers[1:]
                
            # Filter out empty strings and uppercase
            valid_tickers = [t.strip().upper() for t in tickers if t.strip()]
            return valid_tickers
            
        except gspread.exceptions.SpreadsheetNotFound:
            print(f"Error: Sheet '{sheet_name}' not found.")
            return []
        except Exception as e:
            print(f"Error reading tickers from sheet: {str(e)}")
            return []

    def add_or_update_row(self, sheet_name, ticker, data):
        """
        Adds a new row for the ticker or updates it if it already exists.
        Columns:
        A: Ticker
        B: Price
        C: Change %
        D: Sentiment
        E: AI Summary
        F: Last Updated
        """
        if not self.client:
            if not self.connect():
                return False
                
        try:
            sheet = self.client.open(sheet_name).sheet1
            
            # Format data
            price = data.get('price', 'N/A')
            change = data.get('change_percent', 'N/A')
            if isinstance(price, (int, float)):
                price = f"${price:.2f}"
            if isinstance(change, (int, float)):
                change = f"{change:+.2f}%"
                
            sentiment = data.get('sentiment', 'N/A')
            summary = data.get('summary', 'No summary available.')
            last_updated = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            row_data = [ticker, price, change, sentiment, summary, last_updated]
            
            # Try to find existing ticker
            try:
                cell = sheet.find(ticker)
                row_idx = cell.row
                # Update existing row
                # gspread uses 1-based indexing. We update cols 2-6.
                # But it's more efficient to update the whole range if possible, 
                # or just cell by cell for safety.
                sheet.update_cell(row_idx, 2, price)
                sheet.update_cell(row_idx, 3, change)
                sheet.update_cell(row_idx, 4, sentiment)
                sheet.update_cell(row_idx, 5, summary)
                sheet.update_cell(row_idx, 6, last_updated)
                print(f"Updated existing row for {ticker}")
                
            except gspread.exceptions.CellNotFound:
                # Ticker not found, append new row
                sheet.append_row(row_data)
                print(f"Appended new row for {ticker}")
            
            return True
            
        except Exception as e:
            print(f"Error updating sheet for {ticker}: {str(e)}")
            return False

    def setup_sheet_headers(self, sheet_name):
        """
        Sets up the headers if the sheet is empty.
        """
        if not self.client:
            if not self.connect():
                return False
                
        try:
            sheet = self.client.open(sheet_name).sheet1
            
            # Check if A1 is empty
            if not sheet.acell('A1').value:
                headers = ["Ticker", "Price", "Change %", "Sentiment", "AI Summary", "Last Updated"]
                sheet.insert_row(headers, 1)
                print(f"Initialized headers for sheet '{sheet_name}'.")
                return True
            return True
            
        except Exception as e:
            print(f"Error setting up headers: {str(e)}")
            return False
