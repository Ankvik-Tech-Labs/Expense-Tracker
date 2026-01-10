"""Holdings page with detailed view of all investments."""
import streamlit as st
import pandas as pd

from src.database.repository import PortfolioRepository

st.set_page_config(page_title="Holdings", page_icon="💼", layout="wide")

st.title("💼 Holdings")

# Initialize repository
repo = PortfolioRepository()

# Get latest holdings
holdings_df = repo.get_holdings_df()

if holdings_df.empty:
    st.warning("No data available. Please upload your holdings data from the Upload page.")
    st.stop()

# Tabs for different types
tab1, tab2, tab3 = st.tabs(["📈 Stocks", "💰 Mutual Funds", "🔍 All Holdings"])

with tab1:
    st.subheader("Stock Holdings")
    stocks_df = holdings_df[holdings_df['type'] == 'stock'].copy()

    if not stocks_df.empty:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Stocks Value", f"₹{stocks_df['current_value'].sum():,.2f}")
        with col2:
            st.metric("Total Invested", f"₹{stocks_df['invested_value'].sum():,.2f}")
        with col3:
            total_pl = stocks_df['unrealized_pl'].sum()
            total_pl_pct = (total_pl / stocks_df['invested_value'].sum()) * 100
            st.metric("Total P&L", f"₹{total_pl:,.2f}", f"{total_pl_pct:.2f}%")

        st.markdown("---")

        # Display table
        display_df = stocks_df[['name', 'units', 'avg_price', 'current_price', 'invested_value', 'current_value', 'unrealized_pl', 'unrealized_pl_pct']].copy()
        display_df.columns = ['Name', 'Units', 'Avg Price', 'Current Price', 'Invested', 'Current Value', 'P&L', 'P&L %']

        # Format numbers
        for col in ['Avg Price', 'Current Price', 'Invested', 'Current Value', 'P&L']:
            display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.2f}")
        display_df['P&L %'] = display_df['P&L %'].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No stock holdings found.")

with tab2:
    st.subheader("Mutual Fund Holdings")
    mf_df = holdings_df[holdings_df['type'] == 'mutual_fund'].copy()

    if not mf_df.empty:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total MF Value", f"₹{mf_df['current_value'].sum():,.2f}")
        with col2:
            st.metric("Total Invested", f"₹{mf_df['invested_value'].sum():,.2f}")
        with col3:
            total_pl = mf_df['unrealized_pl'].sum()
            total_pl_pct = (total_pl / mf_df['invested_value'].sum()) * 100
            st.metric("Total P&L", f"₹{total_pl:,.2f}", f"{total_pl_pct:.2f}%")

        st.markdown("---")

        # Display table
        display_df = mf_df[['name', 'units', 'avg_price', 'current_price', 'invested_value', 'current_value', 'unrealized_pl', 'unrealized_pl_pct']].copy()
        display_df.columns = ['Scheme Name', 'Units', 'Avg NAV', 'Current NAV', 'Invested', 'Current Value', 'Returns', 'Returns %']

        # Format numbers
        for col in ['Avg NAV', 'Current NAV', 'Invested', 'Current Value', 'Returns']:
            display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.2f}")
        display_df['Returns %'] = display_df['Returns %'].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            display_df,
            width="stretch",
            hide_index=True
        )
    else:
        st.info("No mutual fund holdings found.")

with tab3:
    st.subheader("All Holdings")

    # Summary
    total_value = holdings_df['current_value'].sum()
    total_invested = holdings_df['invested_value'].sum()
    total_pl = holdings_df['unrealized_pl'].sum()
    total_pl_pct = (total_pl / total_invested) * 100 if total_invested > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Holdings", len(holdings_df))
    with col2:
        st.metric("Total Value", f"₹{total_value:,.2f}")
    with col3:
        st.metric("Total Invested", f"₹{total_invested:,.2f}")
    with col4:
        st.metric("Total P&L", f"₹{total_pl:,.2f}", f"{total_pl_pct:.2f}%")

    st.markdown("---")

    # Display table with sorting
    display_df = holdings_df[['type', 'name', 'units', 'current_price', 'invested_value', 'current_value', 'unrealized_pl', 'unrealized_pl_pct']].copy()
    display_df.columns = ['Type', 'Name', 'Units', 'Price', 'Invested', 'Current Value', 'P&L', 'P&L %']

    # Format numbers
    for col in ['Price', 'Invested', 'Current Value', 'P&L']:
        display_df[col] = display_df[col].apply(lambda x: f"₹{x:,.2f}")
    display_df['P&L %'] = display_df['P&L %'].apply(lambda x: f"{x:.2f}%")

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True
    )

st.markdown("---")
st.caption(f"Showing {len(holdings_df)} holdings")
