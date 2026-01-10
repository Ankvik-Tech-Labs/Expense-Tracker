"""
Portfolio service for calculations and aggregations.

This module provides portfolio-level calculations.
"""
from datetime import datetime
from typing import Dict, Tuple

import pandas as pd
import numpy as np


def calculate_portfolio_summary(holdings_df: pd.DataFrame) -> Dict:
    """
    Calculate portfolio summary statistics.

    Parameters:
        holdings_df: DataFrame with holdings

    Returns:
        Dictionary with summary statistics
    """
    if holdings_df.empty:
        return {
            'total_value': 0.0,
            'total_invested': 0.0,
            'total_pl': 0.0,
            'total_pl_pct': 0.0,
            'stocks_value': 0.0,
            'mf_value': 0.0,
            'us_stocks_value': 0.0
        }

    summary = {
        'total_value': holdings_df['current_value'].sum(),
        'total_invested': holdings_df['invested_value'].sum(),
        'total_pl': holdings_df['unrealized_pl'].sum(),
    }

    # Calculate percentage
    if summary['total_invested'] > 0:
        summary['total_pl_pct'] = (summary['total_pl'] / summary['total_invested']) * 100
    else:
        summary['total_pl_pct'] = 0.0

    # Calculate by type
    summary['stocks_value'] = holdings_df[holdings_df['type'] == 'stock']['current_value'].sum()
    summary['mf_value'] = holdings_df[holdings_df['type'] == 'mutual_fund']['current_value'].sum()
    summary['us_stocks_value'] = holdings_df[holdings_df['type'] == 'us_stock']['current_value'].sum()

    return summary


def get_top_performers(holdings_df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Get top performing holdings by P&L percentage.

    Parameters:
        holdings_df: DataFrame with holdings
        n: Number of top performers to return

    Returns:
        DataFrame with top performers
    """
    if holdings_df.empty:
        return pd.DataFrame()

    return holdings_df.nlargest(n, 'unrealized_pl_pct')[
        ['name', 'type', 'unrealized_pl', 'unrealized_pl_pct', 'current_value']
    ]


def get_bottom_performers(holdings_df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """
    Get bottom performing holdings by P&L percentage.

    Parameters:
        holdings_df: DataFrame with holdings
        n: Number of bottom performers to return

    Returns:
        DataFrame with bottom performers
    """
    if holdings_df.empty:
        return pd.DataFrame()

    return holdings_df.nsmallest(n, 'unrealized_pl_pct')[
        ['name', 'type', 'unrealized_pl', 'unrealized_pl_pct', 'current_value']
    ]


def calculate_asset_allocation(holdings_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate asset allocation percentages.

    Parameters:
        holdings_df: DataFrame with holdings

    Returns:
        DataFrame with asset allocation
    """
    if holdings_df.empty:
        return pd.DataFrame()

    allocation = holdings_df.groupby('type')['current_value'].sum().reset_index()
    total_value = allocation['current_value'].sum()

    if total_value > 0:
        allocation['percentage'] = (allocation['current_value'] / total_value) * 100
    else:
        allocation['percentage'] = 0

    allocation = allocation.rename(columns={'type': 'asset_type', 'current_value': 'value'})
    return allocation.sort_values('value', ascending=False)


def calculate_monthly_changes(snapshots_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate month-over-month changes from snapshot data.

    :param snapshots_df: DataFrame with snapshot data containing snapshot_date,
                         total_value, stocks_value, mf_value columns
    :type snapshots_df: pd.DataFrame
    :returns: DataFrame with monthly changes including MoM absolute and percentage changes
    :rtype: pd.DataFrame
    """
    if snapshots_df.empty:
        return pd.DataFrame()

    # Ensure sorted by date ascending for proper diff calculation
    df = snapshots_df.sort_values('snapshot_date').copy()

    # Calculate month-over-month changes
    df['prev_total_value'] = df['total_value'].shift(1)
    df['mom_change'] = df['total_value'] - df['prev_total_value']
    df['mom_change_pct'] = (df['mom_change'] / df['prev_total_value']) * 100

    # Fill NaN for first row (no previous month)
    df['mom_change'] = df['mom_change'].fillna(0)
    df['mom_change_pct'] = df['mom_change_pct'].fillna(0)

    # Format month for display
    df['month'] = df['snapshot_date'].dt.strftime('%b %Y')

    # Select relevant columns
    result = df[[
        'snapshot_date', 'month', 'total_value', 'stocks_value', 'mf_value',
        'total_invested', 'total_pl', 'total_pl_pct',
        'mom_change', 'mom_change_pct'
    ]].copy()

    return result


def calculate_xirr(transactions: pd.DataFrame) -> float:
    """
    Calculate XIRR (Extended Internal Rate of Return).

    Parameters:
        transactions: DataFrame with 'date' and 'amount' columns
                      Negative amounts for investments, positive for current value

    Returns:
        XIRR as a percentage
    """
    # Simplified XIRR calculation
    # For a more accurate implementation, would need iterative Newton-Raphson method
    # This is a basic approximation

    if transactions.empty or len(transactions) < 2:
        return 0.0

    try:
        total_invested = abs(transactions[transactions['amount'] < 0]['amount'].sum())
        current_value = transactions[transactions['amount'] > 0]['amount'].sum()

        if total_invested == 0:
            return 0.0

        # Calculate simple annualized return
        first_date = transactions['date'].min()
        last_date = transactions['date'].max()
        years = (last_date - first_date).days / 365.25

        if years == 0:
            return 0.0

        simple_return = (current_value - total_invested) / total_invested
        xirr = (((1 + simple_return) ** (1 / years)) - 1) * 100

        return xirr

    except Exception:
        return 0.0
