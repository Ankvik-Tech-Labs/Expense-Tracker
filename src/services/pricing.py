"""
Pricing service for fetching real-time prices.

This module fetches prices from Yahoo Finance and other sources.
"""
from typing import Dict, Optional
import time

import yfinance as yf
import pandas as pd


class PricingService:
    """Service for fetching real-time prices."""

    def __init__(self):
        """Initialize pricing service."""
        self.cache: Dict[str, float] = {}
        self.cache_timestamp: Dict[str, float] = {}
        self.cache_duration = 300  # 5 minutes

    def get_stock_price(self, symbol: str, exchange: str = "NSE") -> Optional[float]:
        """
        Get current stock price.

        Parameters:
            symbol: Stock symbol (e.g., 'RELIANCE')
            exchange: Exchange (NSE or BSE)

        Returns:
            Current price or None if failed
        """
        # Check cache
        cache_key = f"{symbol}.{exchange}"
        if cache_key in self.cache:
            if time.time() - self.cache_timestamp[cache_key] < self.cache_duration:
                return self.cache[cache_key]

        try:
            # Add exchange suffix
            if exchange == "NSE":
                ticker_symbol = f"{symbol}.NS"
            elif exchange == "BSE":
                ticker_symbol = f"{symbol}.BO"
            else:
                ticker_symbol = symbol

            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(period="1d")

            if not data.empty:
                price = float(data['Close'].iloc[-1])
                # Update cache
                self.cache[cache_key] = price
                self.cache_timestamp[cache_key] = time.time()
                return price

        except Exception as e:
            print(f"Error fetching price for {symbol}: {e}")

        return None

    def get_bulk_stock_prices(self, symbols: list, exchange: str = "NSE") -> Dict[str, float]:
        """
        Get prices for multiple stocks.

        Parameters:
            symbols: List of stock symbols
            exchange: Exchange (NSE or BSE)

        Returns:
            Dictionary mapping symbols to prices
        """
        prices = {}
        for symbol in symbols:
            price = self.get_stock_price(symbol, exchange)
            if price is not None:
                prices[symbol] = price

        return prices

    def update_holdings_prices(self, holdings_df: pd.DataFrame) -> pd.DataFrame:
        """
        Update current prices in holdings DataFrame.

        Parameters:
            holdings_df: DataFrame with holdings

        Returns:
            DataFrame with updated prices
        """
        df = holdings_df.copy()

        for idx, row in df.iterrows():
            if row['type'] == 'stock':
                # Extract symbol from ISIN or name
                symbol = self._extract_symbol_from_name(row['name'])
                if symbol:
                    price = self.get_stock_price(symbol)
                    if price:
                        df.at[idx, 'current_price'] = price
                        df.at[idx, 'current_value'] = price * row['units']
                        df.at[idx, 'unrealized_pl'] = df.at[idx, 'current_value'] - row['invested_value']
                        df.at[idx, 'unrealized_pl_pct'] = (df.at[idx, 'unrealized_pl'] / row['invested_value']) * 100

        return df

    def _extract_symbol_from_name(self, name: str) -> Optional[str]:
        """
        Extract stock symbol from name.

        Parameters:
            name: Stock name

        Returns:
            Symbol or None
        """
        # Map common names to symbols
        symbol_map = {
            'RELIANCE': 'RELIANCE',
            'TCS': 'TCS',
            'HDFC BANK': 'HDFCBANK',
            'ICICI BANK': 'ICICIBANK',
            'INFOSYS': 'INFY',
            'ITC': 'ITC',
            'HINDUSTAN UNILEVER': 'HINDUNILVR',
            'BHARTI AIRTEL': 'BHARTIARTL',
            'KOTAK MAHINDRA BANK': 'KOTAKBANK',
            'AXIS BANK': 'AXISBANK',
            'TATA STEEL': 'TATASTEEL',
            'TATA POWER': 'TATAPOWER',
            'VEDANTA': 'VEDL',
            'HINDUSTAN AERONAUTICS': 'HAL',
            'JUBILANT FOODWORKS': 'JUBLFOOD',
            'JIO FIN': 'JIOFIN',
            'LIC': 'LICI',
            'PARAG DEF': 'PARACABLES',
            'SIGACHI': 'SIGACHI',
            'IRFC': 'IRFC',
            'BSE LIMITED': 'BSE'
        }

        # Try exact match
        name_upper = name.upper().strip()
        if name_upper in symbol_map:
            return symbol_map[name_upper]

        # Try partial match
        for key, value in symbol_map.items():
            if key in name_upper or name_upper in key:
                return value

        # Return name as-is (might work for simple cases)
        return name.split()[0].upper() if name else None
