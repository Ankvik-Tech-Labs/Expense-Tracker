"""
Generate sample portfolio data for README screenshots.

This script creates realistic but fake portfolio data including:
- Indian stocks
- Mutual funds
- US stocks
- Multiple monthly snapshots
"""

import random
from datetime import datetime, timedelta
import pandas as pd
from src.database.repository import PortfolioRepository
from src.services.portfolio import calculate_portfolio_summary

# Sample data pools
INDIAN_STOCKS = [
    {"name": "RELIANCE INDUSTRIES LTD", "symbol": "RELIANCE", "isin": "INE002A01018"},
    {"name": "TATA CONSULTANCY SERVICES LTD", "symbol": "TCS", "isin": "INE467B01029"},
    {"name": "HDFC BANK LTD", "symbol": "HDFCBANK", "isin": "INE040A01034"},
    {"name": "INFOSYS LIMITED", "symbol": "INFY", "isin": "INE009A01021"},
    {"name": "ICICI BANK LTD", "symbol": "ICICIBANK", "isin": "INE090A01021"},
    {"name": "HINDUSTAN UNILEVER LTD", "symbol": "HINDUNILVR", "isin": "INE030A01027"},
    {"name": "BHARTI AIRTEL LIMITED", "symbol": "BHARTIARTL", "isin": "INE397D01024"},
    {"name": "ITC LIMITED", "symbol": "ITC", "isin": "INE154A01025"},
    {"name": "STATE BANK OF INDIA", "symbol": "SBIN", "isin": "INE062A01020"},
    {"name": "LARSEN & TOUBRO LTD", "symbol": "LT", "isin": "INE018A01030"},
]

US_STOCKS = [
    {"symbol": "AAPL", "name": "Apple Inc."},
    {"symbol": "MSFT", "name": "Microsoft Corporation"},
    {"symbol": "GOOGL", "name": "Alphabet Inc."},
    {"symbol": "AMZN", "name": "Amazon.com Inc."},
    {"symbol": "NVDA", "name": "NVIDIA Corporation"},
    {"symbol": "TSLA", "name": "Tesla Inc."},
    {"symbol": "META", "name": "Meta Platforms Inc."},
]

MUTUAL_FUNDS = [
    "ICICI Prudential Bluechip Fund - Direct Growth",
    "SBI Small Cap Fund - Direct Growth",
    "Axis Midcap Fund - Direct Growth",
    "Parag Parikh Flexi Cap Fund - Direct Growth",
    "Mirae Asset Large Cap Fund - Direct Growth",
    "Kotak Emerging Equity Fund - Direct Growth",
    "HDFC Index Fund - NIFTY 50 Plan - Direct Growth",
]


def generate_indian_stocks(num_stocks=8, base_investment=50000):
    """Generate random Indian stock holdings."""
    holdings = []
    selected_stocks = random.sample(INDIAN_STOCKS, min(num_stocks, len(INDIAN_STOCKS)))

    for stock in selected_stocks:
        # Random investment between 20k to 150k
        invested = random.uniform(20000, 150000)
        # Random units
        units = random.randint(5, 50)
        avg_price = invested / units

        # Random P&L between -15% to +45%
        pl_pct = random.uniform(-15, 45)
        current_value = invested * (1 + pl_pct / 100)
        current_price = current_value / units
        unrealized_pl = current_value - invested

        holdings.append(
            {
                "type": "stock",
                "name": stock["name"],
                "symbol": stock["symbol"],
                "isin": stock["isin"],
                "units": units,
                "avg_price": round(avg_price, 2),
                "invested_value": round(invested, 2),
                "current_price": round(current_price, 2),
                "current_value": round(current_value, 2),
                "unrealized_pl": round(unrealized_pl, 2),
                "unrealized_pl_pct": round(pl_pct, 2),
            }
        )

    return holdings


def generate_us_stocks(num_stocks=5, usd_to_inr=85.5):
    """Generate random US stock holdings (values in INR)."""
    holdings = []
    selected_stocks = random.sample(US_STOCKS, min(num_stocks, len(US_STOCKS)))

    for stock in selected_stocks:
        # Random investment between $500 to $3000 (in INR)
        invested_usd = random.uniform(500, 3000)
        invested = invested_usd * usd_to_inr
        # Random units
        units = random.randint(2, 20)
        avg_price = invested / units

        # Random P&L between -20% to +60% (tech stocks volatile)
        pl_pct = random.uniform(-20, 60)
        current_value = invested * (1 + pl_pct / 100)
        current_price = current_value / units
        unrealized_pl = current_value - invested

        holdings.append(
            {
                "type": "us_stock",
                "name": stock["name"],
                "symbol": stock["symbol"],
                "isin": None,
                "units": units,
                "avg_price": round(avg_price, 2),
                "invested_value": round(invested, 2),
                "current_price": round(current_price, 2),
                "current_value": round(current_value, 2),
                "unrealized_pl": round(unrealized_pl, 2),
                "unrealized_pl_pct": round(pl_pct, 2),
            }
        )

    return holdings


def generate_mutual_funds(num_funds=6):
    """Generate random mutual fund holdings."""
    holdings = []
    selected_funds = random.sample(MUTUAL_FUNDS, min(num_funds, len(MUTUAL_FUNDS)))

    for fund in selected_funds:
        # Random investment between 30k to 200k
        invested = random.uniform(30000, 200000)
        # Random units (MF units are typically decimal)
        units = random.uniform(100, 2000)
        avg_price = invested / units

        # Random P&L between -5% to +30% (MF are less volatile)
        pl_pct = random.uniform(-5, 30)
        current_value = invested * (1 + pl_pct / 100)
        current_price = current_value / units
        unrealized_pl = current_value - invested

        holdings.append(
            {
                "type": "mutual_fund",
                "name": fund,
                "symbol": None,
                "isin": f"INF{random.randint(100, 999)}A01{random.randint(100, 999):03d}",
                "units": round(units, 3),
                "avg_price": round(avg_price, 2),
                "invested_value": round(invested, 2),
                "current_price": round(current_price, 2),
                "current_value": round(current_value, 2),
                "unrealized_pl": round(unrealized_pl, 2),
                "unrealized_pl_pct": round(pl_pct, 2),
            }
        )

    return holdings


def generate_snapshot(snapshot_date, growth_factor=1.0):
    """Generate a complete portfolio snapshot for a given date."""
    # Generate holdings with growth factor (for portfolio growth over time)
    indian_stocks = generate_indian_stocks(num_stocks=random.randint(6, 10))
    us_stocks = generate_us_stocks(num_stocks=random.randint(4, 7))
    mutual_funds = generate_mutual_funds(num_funds=random.randint(5, 7))

    # Apply growth factor to simulate portfolio appreciation
    all_holdings = indian_stocks + us_stocks + mutual_funds
    for holding in all_holdings:
        holding["invested_value"] = round(holding["invested_value"] * growth_factor, 2)
        holding["current_value"] = round(holding["current_value"] * growth_factor, 2)
        holding["unrealized_pl"] = round(
            holding["current_value"] - holding["invested_value"], 2
        )
        holding["avg_price"] = round(holding["invested_value"] / holding["units"], 2)
        holding["current_price"] = round(holding["current_value"] / holding["units"], 2)
        holding["unrealized_pl_pct"] = round(
            (holding["unrealized_pl"] / holding["invested_value"]) * 100, 2
        )

    return all_holdings


def populate_database():
    """Populate database with sample data spanning 6 months."""
    repo = PortfolioRepository()

    print("🧹 Clearing existing data...")
    repo.clear_all_data()

    # Generate 6 monthly snapshots
    start_date = datetime(2025, 7, 31)  # July 2025

    print("\n📊 Generating sample portfolio data...\n")

    for month in range(6):
        snapshot_date = start_date + timedelta(days=30 * month)

        # Simulate portfolio growth over time (5-8% per month)
        growth_factor = 1.0 + (month * 0.06)

        print(f"📅 Creating snapshot for {snapshot_date.strftime('%B %Y')}...")

        # Generate holdings
        holdings = generate_snapshot(snapshot_date, growth_factor)
        holdings_df = pd.DataFrame(holdings)

        # Save holdings
        count = repo.save_holdings(holdings_df, snapshot_date)

        # Calculate summary
        summary = calculate_portfolio_summary(holdings_df)

        # Mock benchmark values (NIFTY and SENSEX)
        nifty = round(22000 + (month * 500) + random.uniform(-200, 200), 2)
        sensex = round(72000 + (month * 1500) + random.uniform(-500, 500), 2)

        # Save snapshot
        snapshot_data = {
            "snapshot_date": snapshot_date,
            "total_value": summary["total_value"],
            "stocks_value": summary["stocks_value"],
            "mf_value": summary["mf_value"],
            "us_stocks_value": summary["us_stocks_value"],
            "total_invested": summary["total_invested"],
            "total_pl": summary["total_pl"],
            "total_pl_pct": summary["total_pl_pct"],
            "benchmark_nifty": nifty,
            "benchmark_sensex": sensex,
        }
        repo.save_snapshot(snapshot_data)

        print(f"   ✅ Saved {count} holdings")
        print(f"   💰 Total Value: ₹{summary['total_value']:,.2f}")
        print(
            f"   📈 Total P&L: ₹{summary['total_pl']:,.2f} ({summary['total_pl_pct']:.2f}%)"
        )
        print()

    print("✅ Sample data generation complete!")
    print("\n📊 Summary:")
    print(f"   • Generated 6 monthly snapshots (July 2025 - December 2025)")
    print(f"   • Total holdings per snapshot: 15-24 (mixed assets)")
    print(f"   • Indian Stocks: 6-10 per snapshot")
    print(f"   • US Stocks: 4-7 per snapshot")
    print(f"   • Mutual Funds: 5-7 per snapshot")
    print(f"   • Portfolio shows growth trend over 6 months")
    print("\n🚀 You can now run the Streamlit app and take screenshots!")


if __name__ == "__main__":
    populate_database()
