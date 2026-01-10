"""
Parser for US stocks Profit-Loss Excel file.

This module parses DriveWealth Profit-Loss statement for US stocks.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Tuple

import pandas as pd

from src.services.pricing import PricingService


def parse_us_stocks_file(file_path: str | Path) -> Tuple[pd.DataFrame, datetime]:
    """
    Parse US stocks Profit-Loss Excel file from DriveWealth.

    The file format has multiple sheets:
    - User Details: Contains period and account info
    - Unrealized P&L - Summary: Aggregated holdings per security
    - Unrealized P&L - Breakdown: Individual lots with acquisition dates

    We use the "Unrealized P&L - Summary" sheet for holdings data.

    Parameters:
        file_path: Path to the Excel file

    Returns:
        Tuple of (DataFrame with parsed data, snapshot date)

    Raises:
        ValueError: If file format is invalid or cannot be parsed
    """
    # Read User Details sheet to extract date range
    df_user = pd.read_excel(file_path, sheet_name="User Details")
    period_text = str(df_user.iloc[0, 0])  # Period column first row

    # Extract end date from period (format: "2025-12-01 to 2026-01-10")
    match = re.search(r"to\s+(\d{4})-(\d{2})-(\d{2})", period_text)
    if not match:
        raise ValueError(f"Could not extract date from period: {period_text}")

    year, month, day = match.groups()
    snapshot_date = datetime(int(year), int(month), int(day))

    # Read the summary sheet with holdings data
    df = pd.read_excel(file_path, sheet_name="Unrealized P&L - Summary ")

    # Validate required columns exist
    required_cols = [
        "Security",
        "Quantity",
        "Market Value (USD)",
        "Cost Basis (USD)",
        "Profit/Loss (USD)",
        "Profit/Loss (%)",
    ]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Rename columns to standard names
    df_clean = df.rename(
        columns={
            "Security": "symbol",
            "Quantity": "units",
            "Cost Basis (USD)": "invested_value",
            "Market Value (USD)": "current_value",
            "Market Price (USD)": "current_price",
            "Profit/Loss (USD)": "unrealized_pl",
            "Profit/Loss (%)": "unrealized_pl_pct",
        }
    ).copy()

    # Calculate average price and current price
    df_clean["avg_price"] = df_clean["invested_value"] / df_clean["units"]

    # If current_price not in summary, calculate it
    if "current_price" not in df_clean.columns:
        df_clean["current_price"] = df_clean["current_value"] / df_clean["units"]

    # Filter out rows without valid data
    df_clean = df_clean[df_clean["symbol"].notna() & (df_clean["symbol"] != "")]

    # Convert numeric columns to proper types
    numeric_cols = [
        "units",
        "avg_price",
        "invested_value",
        "current_price",
        "current_value",
        "unrealized_pl",
        "unrealized_pl_pct",
    ]
    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")

    # Remove rows with invalid numeric data
    df_clean = df_clean.dropna(subset=["units", "invested_value", "current_value"])

    # Convert USD to INR using real-time exchange rate
    pricing_service = PricingService()
    usd_to_inr_rate = pricing_service.get_usd_to_inr_rate()

    if usd_to_inr_rate:
        print(f"Converting USD to INR at rate: {usd_to_inr_rate:.2f}")
        # Convert all USD values to INR
        df_clean["avg_price"] = df_clean["avg_price"] * usd_to_inr_rate
        df_clean["current_price"] = df_clean["current_price"] * usd_to_inr_rate
        df_clean["invested_value"] = df_clean["invested_value"] * usd_to_inr_rate
        df_clean["current_value"] = df_clean["current_value"] * usd_to_inr_rate
        df_clean["unrealized_pl"] = df_clean["unrealized_pl"] * usd_to_inr_rate
        # P&L percentage stays the same (it's already a percentage)
    else:
        raise ValueError("Could not fetch USD/INR exchange rate")

    # Add standard fields
    df_clean["type"] = "us_stock"
    df_clean["name"] = df_clean["symbol"]  # Use symbol as name for US stocks
    df_clean["isin"] = None  # US stocks don't have ISIN

    # Select and order columns to match standard format
    columns = [
        "type",
        "name",
        "symbol",
        "isin",
        "units",
        "avg_price",
        "invested_value",
        "current_price",
        "current_value",
        "unrealized_pl",
        "unrealized_pl_pct",
    ]
    df_clean = df_clean[columns]

    return df_clean, snapshot_date
