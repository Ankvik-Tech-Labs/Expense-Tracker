"""
Benchmark service for fetching index values.

This module fetches benchmark index values (Nifty 50, Sensex).
"""
from typing import Optional, Tuple
import yfinance as yf


class BenchmarkService:
    """Service for fetching benchmark index values."""

    def get_nifty50(self) -> Optional[float]:
        """
        Get current Nifty 50 value.

        Returns:
            Nifty 50 value or None if failed
        """
        try:
            ticker = yf.Ticker("^NSEI")
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            print(f"Error fetching Nifty 50: {e}")
        return None

    def get_sensex(self) -> Optional[float]:
        """
        Get current Sensex value.

        Returns:
            Sensex value or None if failed
        """
        try:
            ticker = yf.Ticker("^BSESN")
            data = ticker.history(period="1d")
            if not data.empty:
                return float(data['Close'].iloc[-1])
        except Exception as e:
            print(f"Error fetching Sensex: {e}")
        return None

    def get_benchmarks(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Get both Nifty 50 and Sensex values.

        Returns:
            Tuple of (Nifty 50, Sensex) values
        """
        return self.get_nifty50(), self.get_sensex()
