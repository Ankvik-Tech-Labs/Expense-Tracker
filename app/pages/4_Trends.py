"""Trends page with detailed monthly analysis."""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from src.database.repository import PortfolioRepository
from src.services.portfolio import calculate_monthly_changes

st.set_page_config(page_title="Trends", page_icon="📊", layout="wide")

st.title("📊 Portfolio Trends")
st.markdown("Detailed monthly analysis of your portfolio performance.")

# Initialize repository
repo = PortfolioRepository()

# Get all snapshots
snapshots_df = repo.get_snapshots_df(limit=24)

if snapshots_df.empty:
    st.warning(
        "No historical data available. Upload data for multiple months to see trends."
    )
    st.stop()

# Calculate monthly changes
monthly_df = calculate_monthly_changes(snapshots_df)

if monthly_df.empty:
    st.warning("Unable to calculate monthly changes.")
    st.stop()

# Sort for display and charts
monthly_df = monthly_df.sort_values("snapshot_date")

# KPI Row - Overall Performance
st.subheader("Overall Performance")
col1, col2, col3, col4 = st.columns(4)

with col1:
    latest_value = monthly_df["total_value"].iloc[-1]
    st.metric("Current Portfolio", f"₹{latest_value:,.2f}")

with col2:
    earliest_value = monthly_df["total_value"].iloc[0]
    total_change = latest_value - earliest_value
    total_change_pct = (
        (total_change / earliest_value) * 100 if earliest_value > 0 else 0
    )
    st.metric("Total Change", f"₹{total_change:,.2f}", f"{total_change_pct:.2f}%")

with col3:
    avg_monthly_change = monthly_df["mom_change"].mean()
    st.metric("Avg Monthly Change", f"₹{avg_monthly_change:,.2f}")

with col4:
    months_count = len(monthly_df)
    st.metric("Months Tracked", f"{months_count}")

st.markdown("---")

# Charts Row
col1, col2 = st.columns(2)

with col1:
    st.subheader("Monthly Gains/Losses")

    # Create bar chart with color based on positive/negative
    colors = ["#00c853" if x >= 0 else "#d32f2f" for x in monthly_df["mom_change"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=monthly_df["month"],
                y=monthly_df["mom_change"],
                marker_color=colors,
                text=[f"₹{x:,.0f}" for x in monthly_df["mom_change"]],
                textposition="outside",
            )
        ]
    )

    fig.update_layout(
        title="Month-over-Month Change",
        xaxis_title="Month",
        yaxis_title="Change (₹)",
        showlegend=False,
        height=400,
    )

    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Asset Allocation Over Time")

    # Create stacked area chart
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=monthly_df["snapshot_date"],
            y=monthly_df["stocks_value"],
            name="Stocks",
            stackgroup="one",
            fillcolor="rgba(31, 119, 180, 0.7)",
            line=dict(width=0),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=monthly_df["snapshot_date"],
            y=monthly_df["mf_value"],
            name="Mutual Funds",
            stackgroup="one",
            fillcolor="rgba(255, 127, 14, 0.7)",
            line=dict(width=0),
        )
    )

    fig.update_layout(
        title="Portfolio Composition Over Time",
        xaxis_title="Date",
        yaxis_title="Value (₹)",
        hovermode="x unified",
        height=400,
    )

    st.plotly_chart(fig, width="stretch")

st.markdown("---")

# Portfolio Value Trend with Benchmark
st.subheader("Portfolio Value Trend")

fig = go.Figure()

# Portfolio line
fig.add_trace(
    go.Scatter(
        x=monthly_df["snapshot_date"],
        y=monthly_df["total_value"],
        mode="lines+markers",
        name="Portfolio Value",
        line=dict(color="#1f77b4", width=3),
        marker=dict(size=8),
    )
)

# Add invested value line for comparison
fig.add_trace(
    go.Scatter(
        x=monthly_df["snapshot_date"],
        y=monthly_df["total_invested"],
        mode="lines",
        name="Total Invested",
        line=dict(color="#7f7f7f", width=2, dash="dash"),
    )
)

fig.update_layout(
    title="Portfolio Value vs Investment",
    xaxis_title="Date",
    yaxis_title="Value (₹)",
    hovermode="x unified",
    height=400,
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
)

st.plotly_chart(fig, width="stretch")

st.markdown("---")

# Monthly Data Table
st.subheader("Monthly History")

# Prepare display DataFrame (sorted most recent first)
display_df = monthly_df.sort_values("snapshot_date", ascending=False).copy()

table_df = display_df[
    [
        "month",
        "total_value",
        "total_invested",
        "total_pl",
        "total_pl_pct",
        "stocks_value",
        "mf_value",
        "mom_change",
        "mom_change_pct",
    ]
].copy()

table_df.columns = [
    "Month",
    "Total Value",
    "Invested",
    "P&L",
    "P&L %",
    "Stocks",
    "Mutual Funds",
    "MoM Change",
    "MoM %",
]

# Format columns
for col in ["Total Value", "Invested", "P&L", "Stocks", "Mutual Funds", "MoM Change"]:
    table_df[col] = table_df[col].apply(lambda x: f"₹{x:,.2f}")

for col in ["P&L %", "MoM %"]:
    table_df[col] = table_df[col].apply(lambda x: f"{x:.2f}%")

st.dataframe(table_df, width="stretch", hide_index=True)

st.markdown("---")
st.caption("Data is based on monthly snapshots uploaded to the system.")
