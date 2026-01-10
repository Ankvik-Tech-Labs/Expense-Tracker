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
    calculate_asset_allocation,
    calculate_monthly_changes
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
        "Total Portfolio",
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
        st.plotly_chart(fig, width="stretch")

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
        st.plotly_chart(fig, width="stretch")

st.markdown("---")

# Monthly Summary (Compact - Last 6 Months)
with st.expander("📊 Monthly Summary (Last 6 Months)", expanded=False):
    snapshots_df = repo.get_snapshots_df(limit=6)
    if not snapshots_df.empty:
        monthly_df = calculate_monthly_changes(snapshots_df)
        if not monthly_df.empty:
            # Sort by date descending for display (most recent first)
            monthly_df = monthly_df.sort_values('snapshot_date', ascending=False)

            # Create display DataFrame
            display_df = monthly_df[[
                'month', 'total_value', 'stocks_value', 'mf_value',
                'mom_change', 'mom_change_pct'
            ]].copy()

            display_df.columns = ['Month', 'Total Value', 'Stocks', 'Mutual Funds', 'Change', 'Change %']

            # Format currency columns
            for col in ['Total Value', 'Stocks', 'Mutual Funds', 'Change']:
                display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.2f}")

            display_df['Change %'] = display_df['Change %'].apply(lambda x: f"{x:.2f}%")

            st.dataframe(display_df, width="stretch", hide_index=True)

            st.caption("💡 For detailed monthly analysis, visit the Trends page.")
    else:
        st.info("No monthly data available yet. Upload data for multiple months to see trends.")

st.markdown("---")

# Top and Bottom Performers
col1, col2 = st.columns(2)

with col1:
    st.subheader("🔥 Top Performers")
    top_df = get_top_performers(holdings_df, n=5)
    if not top_df.empty:
        for idx, row in top_df.iterrows():
            # Always use "normal" so positive P&L shows green, negative shows red
            st.metric(
                row['name'][:30],
                f"₹{row['current_value']:,.2f}",
                f"{row['unrealized_pl_pct']:.2f}%",
                delta_color="normal"
            )

with col2:
    st.subheader("📉 Bottom Performers")
    bottom_df = get_bottom_performers(holdings_df, n=5)
    if not bottom_df.empty:
        for idx, row in bottom_df.iterrows():
            # Always use "normal" so negative P&L shows red, positive shows green
            st.metric(
                row['name'][:30],
                f"₹{row['current_value']:,.2f}",
                f"{row['unrealized_pl_pct']:.2f}%",
                delta_color="normal"
            )

st.markdown("---")
st.caption(f"Last updated: {latest_date.strftime('%d %b %Y')}")
