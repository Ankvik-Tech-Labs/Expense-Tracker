"""Export page for downloading portfolio data."""
import streamlit as st
import pandas as pd
from datetime import datetime

from src.database.repository import PortfolioRepository
from src.services.portfolio import calculate_portfolio_summary
from src.exports.excel_exporter import create_portfolio_excel

st.set_page_config(page_title="Export", page_icon="📥", layout="wide")

st.title("📥 Export Data")
st.markdown("Download your portfolio data as an Excel file.")

# Initialize repository
repo = PortfolioRepository()

# Get data
holdings_df = repo.get_holdings_df()
snapshots_df = repo.get_snapshots_df(limit=24)

if holdings_df.empty:
    st.warning("No data available to export. Please upload your holdings data first.")
    st.stop()

# Calculate summary
summary = calculate_portfolio_summary(holdings_df)

# Preview section
st.subheader("📋 Export Preview")

col1, col2, col3 = st.columns(3)

with col1:
    total_holdings = len(holdings_df)
    st.metric("Total Holdings", total_holdings)

with col2:
    stocks_count = len(holdings_df[holdings_df['type'] == 'stock']) if not holdings_df.empty else 0
    st.metric("Stocks", stocks_count)

with col3:
    mf_count = len(holdings_df[holdings_df['type'] == 'mutual_fund']) if not holdings_df.empty else 0
    st.metric("Mutual Funds", mf_count)

st.markdown("---")

# Export options
st.subheader("Export Options")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### What's Included")
    st.markdown("""
    The Excel file contains:
    - **Summary**: Portfolio overview and totals
    - **Stocks**: All stock holdings with P&L
    - **Mutual Funds**: All MF holdings with P&L
    - **Monthly Trend**: Historical snapshots
    """)

with col2:
    st.markdown("### Data Summary")
    st.markdown(f"""
    - **Total Value**: ₹{summary['total_value']:,.2f}
    - **Total Invested**: ₹{summary['total_invested']:,.2f}
    - **Total P&L**: ₹{summary['total_pl']:,.2f} ({summary['total_pl_pct']:.2f}%)
    - **Months of Data**: {len(snapshots_df)}
    """)

st.markdown("---")

# Download button
st.subheader("Download")

# Generate filename with current date
export_date = datetime.now()
filename = f"Portfolio_Report_{export_date.strftime('%Y%m%d_%H%M')}.xlsx"

# Generate Excel file
excel_buffer = create_portfolio_excel(
    holdings_df=holdings_df,
    snapshots_df=snapshots_df,
    summary=summary,
    export_date=export_date
)

st.download_button(
    label="📥 Download Excel Report",
    data=excel_buffer,
    file_name=filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    type="primary"
)

st.caption(f"File will be saved as: {filename}")

st.markdown("---")

# Data preview
with st.expander("Preview Holdings Data"):
    tab1, tab2 = st.tabs(["Stocks", "Mutual Funds"])

    with tab1:
        stocks_df = holdings_df[holdings_df['type'] == 'stock'] if not holdings_df.empty else pd.DataFrame()
        if not stocks_df.empty:
            display_cols = ['name', 'units', 'invested_value', 'current_value', 'unrealized_pl', 'unrealized_pl_pct']
            st.dataframe(stocks_df[display_cols], width="stretch", hide_index=True)
        else:
            st.info("No stock holdings")

    with tab2:
        mf_df = holdings_df[holdings_df['type'] == 'mutual_fund'] if not holdings_df.empty else pd.DataFrame()
        if not mf_df.empty:
            display_cols = ['name', 'units', 'invested_value', 'current_value', 'unrealized_pl', 'unrealized_pl_pct']
            st.dataframe(mf_df[display_cols], width="stretch", hide_index=True)
        else:
            st.info("No mutual fund holdings")

with st.expander("Preview Monthly Trend"):
    if not snapshots_df.empty:
        trend_df = snapshots_df.sort_values('snapshot_date', ascending=False).copy()
        trend_df['month'] = trend_df['snapshot_date'].dt.strftime('%b %Y')
        display_cols = ['month', 'total_value', 'total_invested', 'total_pl', 'stocks_value', 'mf_value']
        st.dataframe(trend_df[display_cols], width="stretch", hide_index=True)
    else:
        st.info("No monthly trend data available")
