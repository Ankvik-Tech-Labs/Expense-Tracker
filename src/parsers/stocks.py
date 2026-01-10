"""
Parser for stocks holdings Excel file.

This module parses broker-provided stock holdings Excel files.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd


def parse_stocks_file(file_path: str | Path) -> Tuple[pd.DataFrame, datetime]:
    """
    Parse stocks holdings Excel file from broker.

    The file format has:
    - Header info in first few rows
    - Holdings data starting at row 10 (index 9)
    - Columns: Stock Name, ISIN, Quantity, Average buy price, Buy value,
               Closing price, Closing value, Unrealised P&L

    Parameters:
        file_path: Path to the Excel file

    Returns:
        Tuple of (DataFrame with parsed data, snapshot date)

    Raises:
        ValueError: If file format is invalid or cannot be parsed
    """
    df = pd.read_excel(file_path)

    # Extract snapshot date from header
    # Row 2 has format: "Holdings statement for stocks as on DD-MM-YYYY"
    date_text = str(df.iloc[2, 0])
    match = re.search(r'(\d{2})-(\d{2})-(\d{4})', date_text)
    if not match:
        raise ValueError(f"Could not extract date from: {date_text}")

    day, month, year = match.groups()
    snapshot_date = datetime(int(year), int(month), int(day))

    # Find the header row (contains "Stock Name")
    header_row_idx = None
    for idx, row in df.iterrows():
        if 'Stock Name' in str(row.values):
            header_row_idx = idx
            break

    if header_row_idx is None:
        raise ValueError("Could not find header row with 'Stock Name'")

    # Extract column names from header row
    header_values = df.iloc[header_row_idx].tolist()

    # Get data rows (starting from row after header)
    df_clean = df.iloc[header_row_idx + 1:].copy()

    # Set column names
    df_clean.columns = header_values

    # Reset index
    df_clean = df_clean.reset_index(drop=True)

    # Rename columns to standard names
    df_clean = df_clean.rename(columns={
        'Stock Name': 'name',
        'ISIN': 'isin',
        'Quantity': 'units',
        'Average buy price': 'avg_price',
        'Buy value': 'invested_value',
        'Closing price': 'current_price',
        'Closing value': 'current_value',
        'Unrealised P&L': 'unrealized_pl',
        'Unrealized P&L': 'unrealized_pl'  # Try both spellings
    })

    # Filter out rows without valid data
    df_clean = df_clean[df_clean['name'].notna()]
    df_clean = df_clean[df_clean['isin'].notna()]
    df_clean = df_clean[df_clean['isin'] != '']

    # Convert numeric columns to proper types
    numeric_cols = ['units', 'avg_price', 'invested_value', 'current_price', 'current_value', 'unrealized_pl']
    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # Remove rows with invalid numeric data
    df_clean = df_clean.dropna(subset=['units', 'invested_value', 'current_value'])

    # Calculate P&L percentage
    df_clean['unrealized_pl_pct'] = (
        (df_clean['unrealized_pl'] / df_clean['invested_value']) * 100
    )

    # Add type column
    df_clean['type'] = 'stock'

    # Select and order columns
    columns = [
        'type', 'name', 'isin', 'units', 'avg_price',
        'invested_value', 'current_price', 'current_value',
        'unrealized_pl', 'unrealized_pl_pct'
    ]
    df_clean = df_clean[columns]

    return df_clean, snapshot_date
