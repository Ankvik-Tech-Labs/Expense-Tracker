"""
Crypto portfolio service for fetching DeFi positions.

This module wraps the crypto-portfolio-tracker library to fetch
and convert DeFi positions to the standard holdings format.
"""

import os
from decimal import Decimal
from typing import List, Optional, Tuple

import pandas as pd

from src.services.pricing import PricingService


class CryptoService:
    """
    Service for fetching and converting crypto DeFi positions.

    :param infura_project_id: Infura project ID for RPC access.
    :type infura_project_id: str
    """

    def __init__(self, infura_project_id: Optional[str] = None):
        """
        Initialize the crypto service.

        :param infura_project_id: Infura project ID (defaults to WEB3_INFURA_PROJECT_ID env var).
        :type infura_project_id: str
        """
        self.infura_project_id = infura_project_id or os.getenv(
            "WEB3_INFURA_PROJECT_ID"
        )
        self._pricing_service = PricingService()
        self._initialized = False

    def _lazy_import(self):
        """
        Lazy import crypto-portfolio-tracker dependencies.

        This prevents import errors when the dependency is not installed.
        """
        if self._initialized:
            return

        try:
            # Import protocol handlers to trigger auto-registration
            from crypto_portfolio_tracker import protocols  # noqa: F401
            from crypto_portfolio_tracker.core.aggregator import PositionAggregator
            from crypto_portfolio_tracker.core.scanner import ChainScanner
            from crypto_portfolio_tracker.core.models import PortfolioSummary
            from crypto_portfolio_tracker.pricing.defillama import DeFiLlamaPricing
            from crypto_portfolio_tracker.pricing.chainlink import ChainlinkPricing
            from crypto_portfolio_tracker.rpc.provider import ApeRPCProvider
            from crypto_portfolio_tracker.data import get_all_supported_chains

            self._PositionAggregator = PositionAggregator
            self._ChainScanner = ChainScanner
            self._PortfolioSummary = PortfolioSummary
            self._DeFiLlamaPricing = DeFiLlamaPricing
            self._ChainlinkPricing = ChainlinkPricing
            self._ApeRPCProvider = ApeRPCProvider
            self._get_all_supported_chains = get_all_supported_chains
            self._initialized = True
        except ImportError as e:
            raise ImportError(
                "crypto-portfolio-tracker is not installed. "
                "Please install it with: pip install crypto-portfolio-tracker"
            ) from e

    def fetch_positions(
        self,
        wallet_address: str,
        chains: Optional[List[str]] = None,
    ):
        """
        Fetch all DeFi positions for a wallet address across multiple chains.

        Uses parallel scanning with ThreadPoolExecutor for performance,
        matching the CLI's approach.

        :param wallet_address: Ethereum wallet address.
        :type wallet_address: str
        :param chains: Optional list of chains to scan. If None, scans all supported chains.
        :type chains: List[str]
        :returns: Portfolio summary with all positions.
        :rtype: PortfolioSummary
        :raises ValueError: If wallet address is invalid.
        :raises RuntimeError: If RPC connection fails.
        """
        if not wallet_address.startswith("0x") or len(wallet_address) != 42:
            raise ValueError(f"Invalid wallet address: {wallet_address}")

        self._lazy_import()

        # Use the aggregator's optimized get_all_positions which:
        # 1. First detects active chains (quick check)
        # 2. Then scans only active chains in parallel using ThreadPoolExecutor
        # This is the same approach the CLI uses for 2-3 min scans

        # Initialize fallback pricing
        defillama_pricing = self._DeFiLlamaPricing()

        # Create a single RPC provider for the initial scan
        # The aggregator will handle per-chain providers internally
        rpc_provider = self._ApeRPCProvider(chain="ethereum")
        rpc_provider.connect()

        try:
            # Create Chainlink pricing with DeFiLlama fallback
            pricing = self._ChainlinkPricing(
                rpc_provider=rpc_provider,
                fallback_pricing=defillama_pricing,
            )

            # Create scanner and aggregator
            scanner = self._ChainScanner(rpc_provider=rpc_provider)
            aggregator = self._PositionAggregator(
                scanner=scanner,
                pricing_service=pricing,
                rpc_provider=rpc_provider,
            )

            # Use get_all_positions which handles parallel chain scanning internally
            # This method:
            # 1. Calls scan_all_chains() to detect which chains have activity
            # 2. Filters to only active chains
            # 3. Uses ThreadPoolExecutor (max 4 workers) to scan chains in parallel
            portfolio = aggregator.get_all_positions(wallet_address)

            # If specific chains were requested, filter the results
            if chains:
                filtered_positions = [
                    p for p in portfolio.positions if p.chain in chains
                ]
                # Recalculate totals for filtered positions
                total_usd = sum(
                    (p.usd_value or Decimal("0") for p in filtered_positions),
                    Decimal("0"),
                )
                by_chain = {}
                by_protocol = {}
                for position in filtered_positions:
                    pos_value = position.usd_value or Decimal("0")
                    by_chain[position.chain] = (
                        by_chain.get(position.chain, Decimal("0")) + pos_value
                    )
                    by_protocol[position.protocol] = (
                        by_protocol.get(position.protocol, Decimal("0")) + pos_value
                    )

                return self._PortfolioSummary(
                    address=wallet_address,
                    positions=filtered_positions,
                    total_usd_value=total_usd,
                    by_chain=by_chain,
                    by_protocol=by_protocol,
                )

            return portfolio

        finally:
            # Cleanup
            try:
                rpc_provider.disconnect()
            except Exception:
                pass
            try:
                defillama_pricing.close()
            except Exception:
                pass

    def convert_to_holdings_df(
        self,
        portfolio,
        wallet_address: str,
    ) -> pd.DataFrame:
        """
        Convert crypto positions to standardized holdings DataFrame.

        :param portfolio: Portfolio summary from crypto tracker.
        :type portfolio: PortfolioSummary
        :param wallet_address: Source wallet address.
        :type wallet_address: str
        :returns: DataFrame in standard 11-column holdings format plus extra columns.
        :rtype: pd.DataFrame
        """
        if not portfolio.positions:
            return pd.DataFrame()

        # Get USD to INR rate
        usd_to_inr = self._pricing_service.get_usd_to_inr_rate() or 83.0

        holdings = []
        for position in portfolio.positions:
            usd_value = float(position.usd_value or Decimal("0"))
            inr_value = usd_value * usd_to_inr
            balance = float(position.balance)

            # Build descriptive name: "Protocol - Position Type (Token)"
            name = f"{position.protocol} - {position.position_type.value}"
            if position.token.symbol:
                name = f"{name} ({position.token.symbol})"

            # Calculate price per unit
            price_per_unit = inr_value / balance if balance > 0 else 0.0

            holding = {
                "type": "crypto",
                "name": name,
                "symbol": position.chain,  # Store chain in symbol field
                "isin": wallet_address,  # Store wallet address for reference
                "units": balance,
                "avg_price": 0.0,  # No cost basis for DeFi positions
                "current_price": price_per_unit,
                "invested_value": 0.0,  # No cost tracking
                "current_value": inr_value,
                "unrealized_pl": 0.0,
                "unrealized_pl_pct": 0.0,
                # Extended fields for display
                "usd_value": usd_value,
                "protocol": position.protocol,
                "chain": position.chain,
                "position_type": position.position_type.value,
                "token_symbol": position.token.symbol,
                "apy": float(position.apy) if position.apy else None,
                "health_factor": float(position.health_factor)
                if position.health_factor
                else None,
            }
            holdings.append(holding)

        return pd.DataFrame(holdings)

    def fetch_and_convert(
        self,
        wallet_address: str,
        chains: Optional[List[str]] = None,
    ) -> Tuple[pd.DataFrame, float, float]:
        """
        Fetch positions and convert to DataFrame in one call.

        :param wallet_address: Ethereum wallet address.
        :type wallet_address: str
        :param chains: Optional list of chains to scan.
        :type chains: List[str]
        :returns: Tuple of (DataFrame, total_usd_value, total_inr_value).
        :rtype: Tuple[pd.DataFrame, float, float]
        """
        portfolio = self.fetch_positions(wallet_address, chains)
        df = self.convert_to_holdings_df(portfolio, wallet_address)

        total_usd = float(portfolio.total_usd_value)
        usd_to_inr = self._pricing_service.get_usd_to_inr_rate() or 83.0
        total_inr = total_usd * usd_to_inr

        return df, total_usd, total_inr

    def get_usd_to_inr_rate(self) -> float:
        """
        Get current USD to INR exchange rate.

        :returns: Current USD/INR rate.
        :rtype: float
        """
        return self._pricing_service.get_usd_to_inr_rate() or 83.0

    @staticmethod
    def is_available() -> bool:
        """
        Check if crypto-portfolio-tracker is installed.

        :returns: True if the dependency is available.
        :rtype: bool
        """
        try:
            import crypto_portfolio_tracker  # noqa: F401

            return True
        except ImportError:
            return False

    @staticmethod
    def check_infura_configured() -> bool:
        """
        Check if Infura project ID is configured.

        :returns: True if WEB3_INFURA_PROJECT_ID is set.
        :rtype: bool
        """
        return bool(os.getenv("WEB3_INFURA_PROJECT_ID"))
