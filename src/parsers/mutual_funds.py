"""
Parser for mutual funds holdings Excel file.

This module parses broker-provided mutual fund holdings Excel files.
"""
import re
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd


def parse_mutual_funds_file(file_path: str | Path) -> Tuple[pd.DataFrame, datetime]:
    """
    Parse mutual funds holdings Excel file from broker.

    The file format has:
    - Personal details in first few rows
    - Holdings summary
    - Holdings data starting around row 19
    - Columns: Scheme Name, AMC, Category, Sub-category, Folio No., Source,
               Units, Invested Value, Current Value, Returns, XIRR

    Parameters:
        file_path: Path to the Excel file

    Returns:
        Tuple of (DataFrame with parsed data, snapshot date)

    Raises:
        ValueError: If file format is invalid or cannot be parsed
    """
    df = pd.read_excel(file_path)

    # Extract snapshot date from holdings header
    # Row 16 has format: "HOLDINGS AS ON YYYY-MM-DD"
    date_text = None
    for idx, row in df.iterrows():
        text = str(row.values[0])
        if 'HOLDINGS AS ON' in text:
            date_text = text
            break

    if not date_text:
        raise ValueError("Could not find 'HOLDINGS AS ON' text")

    match = re.search(r'(\d{4})-(\d{2})-(\d{2})', date_text)
    if not match:
        raise ValueError(f"Could not extract date from: {date_text}")

    year, month, day = match.groups()
    snapshot_date = datetime(int(year), int(month), int(day))

    # Find the header row (contains "Scheme Name")
    header_row_idx = None
    for idx, row in df.iterrows():
        if 'Scheme Name' in str(row.values):
            header_row_idx = idx
            break

    if header_row_idx is None:
        raise ValueError("Could not find header row with 'Scheme Name'")

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
        'Scheme Name': 'name',
        'AMC': 'amc',
        'Category': 'category',
        'Sub-category': 'sub_category',
        'Folio No.': 'folio_no',
        'Source': 'source',
        'Units': 'units',
        'Invested Value': 'invested_value',
        'Current Value': 'current_value',
        'Returns': 'unrealized_pl',
        'XIRR': 'xirr'
    })

    # Filter out rows without valid data
    df_clean = df_clean[df_clean['name'].notna()]
    df_clean = df_clean[df_clean['units'].notna()]
    df_clean = df_clean[df_clean['name'] != '']

    # Convert numeric columns to proper types
    numeric_cols = ['units', 'invested_value', 'current_value', 'unrealized_pl']
    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')

    # Remove rows with invalid numeric data
    df_clean = df_clean.dropna(subset=['units', 'invested_value', 'current_value'])

    # Calculate average price (NAV)
    df_clean['avg_price'] = df_clean['invested_value'] / df_clean['units']
    df_clean['current_price'] = df_clean['current_value'] / df_clean['units']

    # Calculate P&L percentage
    df_clean['unrealized_pl_pct'] = (
        (df_clean['unrealized_pl'] / df_clean['invested_value']) * 100
    )

    # Add type column
    df_clean['type'] = 'mutual_fund'

    # Create a symbol/identifier (use folio number for now)
    df_clean['symbol'] = 'MF_' + df_clean['folio_no'].astype(str)

    # Select and order columns
    columns = [
        'type', 'name', 'symbol', 'units', 'avg_price',
        'invested_value', 'current_price', 'current_value',
        'unrealized_pl', 'unrealized_pl_pct'
    ]
    df_clean = df_clean[columns]

    return df_clean, snapshot_date
