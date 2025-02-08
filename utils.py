import yfinance as yf
from typing import Dict, Any, Tuple
import pandas as pd
from fuzzywuzzy import fuzz, process
from datetime import datetime, timedelta
import os
import csv

def get_ticker(input_company):
    stock_name = pd.read_csv("data/companies.csv")

    company_names = stock_name['title'].dropna().unique()
    mached_names = []
    matches = process.extract(input_company, company_names)
    if not matches:
        print("No matches were found")
        return None
    else:
        best_match = matches[0][0]
        print("Best matched company:", best_match)

        matched_row = stock_name[stock_name['title'] == best_match]

        if not matched_row.empty:
            ticker = matched_row.iloc[0]['ticker']
        else:
            print("Ticker not found for the matched company.")
    return ticker
def validate_symbol(symbol: str) -> bool:
    """Validate if the symbol is not empty and contains only valid characters."""
    return bool(symbol and symbol.strip() and symbol.isalnum())

def calculate_rsi(data: pd.DataFrame, periods: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=periods).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=periods).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def export_stock_data(symbol: str, data: Dict[str, Any], export_dir: str = 'exports') -> Tuple[bool, str]:
    """Export stock data to CSV files"""
    try:
        # Create export directory if it doesn't exist
        os.makedirs(export_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Export each timeframe to separate files
        for timeframe, frame_data in data.items():
            if timeframe == 'daily':
                df = pd.DataFrame(frame_data['hist'])
                filename = f"{symbol}_daily_{timestamp}.csv"
            else:
                df = pd.DataFrame(frame_data)
                filename = f"{symbol}_{timeframe}_{timestamp}.csv"

            filepath = os.path.join(export_dir, filename)
            df.to_csv(filepath, index=False)

        return True, f"Data exported to {export_dir} directory"
    except Exception as e:
        return False, f"Error exporting data: {str(e)}"

def fetch_stock_data(symbol: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Fetch current stock data from yfinance.
    Returns a tuple of (success, data/error_message)
    """
    try:
        # Get stock information
        stock = yf.Ticker(symbol)
        info = stock.info

        # If we can't get the company name, the symbol is likely invalid
        if 'longName' not in info:
            return False, {"error": "Invalid stock symbol"}

        # Format the data we want to display
        return True, {
            "Company Name": info.get('longName', 'N/A'),
            "Current Price": f"${info.get('currentPrice', 'N/A')}",
            "Market Cap": f"${info.get('marketCap', 'N/A'):,}",
            "52 Week High": f"${info.get('fiftyTwoWeekHigh', 'N/A')}",
            "52 Week Low": f"${info.get('fiftyTwoWeekLow', 'N/A')}",
            "P/E Ratio": info.get('trailingPE', 'N/A'),
            "Volume": f"{info.get('volume', 'N/A'):,}",
            "Industry": info.get('industry', 'N/A')
        }
    except Exception as e:
        return False, {"error": f"Error fetching data: {str(e)}"}

def fetch_historical_data(symbol: str, period: str = '1y') -> Tuple[bool, Dict[str, Any]]:
    """
    Fetch historical data for the given symbol.
    Returns a tuple of (success, data/error_message)
    """
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period)

        if hist.empty:
            return False, {"error": "No historical data available"}

        # Calculate RSI
        hist['RSI'] = calculate_rsi(hist)

        # Get dividends and splits
        dividends = stock.dividends
        splits = stock.splits

        # Calculate daily stats
        daily_stats = {
            'hist': hist.reset_index().to_dict('records'),
            'dividends': [] if dividends.empty else dividends.reset_index().to_dict('records'),
            'splits': [] if splits.empty else splits.reset_index().to_dict('records')
        }

        # Calculate monthly aggregation
        monthly_stats = hist.resample('ME').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum',
            'RSI': 'last'  # Include RSI in monthly data
        }).reset_index().to_dict('records')

        # Calculate yearly aggregation
        yearly_stats = hist.resample('YE').agg({
            'Open': 'first',
            'High': 'max',
            'Low': 'min',
            'Close': 'last',
            'Volume': 'sum',
            'RSI': 'last'  # Include RSI in yearly data
        }).reset_index().to_dict('records')

        return True, {
            'daily': daily_stats,
            'monthly': monthly_stats,
            'yearly': yearly_stats
        }

    except Exception as e:
        return False, {"error": f"Error fetching historical data: {str(e)}"}