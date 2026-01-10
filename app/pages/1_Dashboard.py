"""Dashboard page with portfolio overview."""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

from src.database.repository import PortfolioRepository
from src.services.portfolio import (
    calculate_portfolio_summary,
    get_top_performers,
    get_bottom_performers,
    calculate_asset_allocation
)
from src.services.benchmarks import BenchmarkService

st.set_page_config(page_title="Dashboard", page_icon="📈", layout="wide")

st.title("📈 Dashboard")

# Initialize services
repo = PortfolioRepository()
benchmark_service = BenchmarkService()

# Get latest holdings
holdings_df = repo.get_holdings_df()

if holdings_df.empty:
    st.warning("No data available. Please upload your holdings data from the Upload page.")
    st.stop()

# Calculate summary
summary = calculate_portfolio_summary(holdings_df)
latest_date = holdings_df['snapshot_date'].iloc[0] if not holdings_df.empty else datetime.now()

# KPI Cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Total Portfolio Value",
        f"₹{summary['total_value']:,.2f}",
        f"{summary['total_pl_pct']:.2f}%"
    )

with col2:
    st.metric(
        "Stocks",
        f"₹{summary['stocks_value']:,.2f}",
        f"{(summary['stocks_value']/summary['total_value']*100):.1f}%" if summary['total_value'] > 0 else "0%"
    )

with col3:
    st.metric(
        "Mutual Funds",
        f"₹{summary['mf_value']:,.2f}",
        f"{(summary['mf_value']/summary['total_value']*100):.1f}%" if summary['total_value'] > 0 else "0%"
    )

with col4:
    st.metric(
        "Total P&L",
        f"₹{summary['total_pl']:,.2f}",
        f"{summary['total_pl_pct']:.2f}%"
    )

st.markdown("---")

# Charts Row
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("Asset Allocation")
    allocation_df = calculate_asset_allocation(holdings_df)
    if not allocation_df.empty:
        fig = px.pie(
            allocation_df,
            values='value',
            names='asset_type',
            title="Portfolio Distribution"
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Portfolio Trend")
    snapshots_df = repo.get_snapshots_df(limit=12)
    if not snapshots_df.empty:
        snapshots_df = snapshots_df.sort_values('snapshot_date')
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=snapshots_df['snapshot_date'],
            y=snapshots_df['total_value'],
            mode='lines+markers',
            name='Portfolio Value',
            line=dict(color='#1f77b4', width=3)
        ))
        fig.update_layout(
            title="Portfolio Value Over Time",
            xaxis_title="Date",
            yaxis_title="Value (₹)",
            hovermode='x unified'
        )
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# Top and Bottom Performers
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 Top Performers")
    top_df = get_top_performers(holdings_df, n=5)
    if not top_df.empty:
        for idx, row in top_df.iterrows():
            delta_color = "normal" if row['unrealized_pl_pct'] >= 0 else "inverse"
            st.metric(
                row['name'][:30],
                f"₹{row['current_value']:,.2f}",
                f"{row['unrealized_pl_pct']:.2f}%",
                delta_color=delta_color
            )

with col2:
    st.subheader("📉 Bottom Performers")
    bottom_df = get_bottom_performers(holdings_df, n=5)
    if not bottom_df.empty:
        for idx, row in bottom_df.iterrows():
            delta_color = "normal" if row['unrealized_pl_pct'] >= 0 else "inverse"
            st.metric(
                row['name'][:30],
                f"₹{row['current_value']:,.2f}",
                f"{row['unrealized_pl_pct']:.2f}%",
                delta_color=delta_color
            )

st.markdown("---")
st.caption(f"Last updated: {latest_date.strftime('%d %b %Y')}")
