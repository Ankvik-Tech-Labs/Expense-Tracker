"""Upload page for adding new monthly data."""
import streamlit as st
from datetime import datetime
import pandas as pd

from src.parsers.stocks import parse_stocks_file
from src.parsers.mutual_funds import parse_mutual_funds_file
from src.database.repository import PortfolioRepository
from src.services.portfolio import calculate_portfolio_summary
from src.services.benchmarks import BenchmarkService

st.set_page_config(page_title="Upload Data", page_icon="⬆️", layout="wide")

st.title("⬆️ Upload Monthly Data")

st.markdown("""
Upload your monthly broker statements to track your portfolio over time.
Supported file types: Excel (.xlsx)
""")

# Initialize services
repo = PortfolioRepository()
benchmark_service = BenchmarkService()

# File uploaders
col1, col2 = st.columns(2)

with col1:
    st.subheader("📈 Stocks Holdings")
    stocks_file = st.file_uploader(
        "Upload Stocks Excel File",
        type=['xlsx'],
        key='stocks_uploader',
        help="Upload your broker's stocks holdings statement"
    )

with col2:
    st.subheader("💰 Mutual Funds Holdings")
    mf_file = st.file_uploader(
        "Upload Mutual Funds Excel File",
        type=['xlsx'],
        key='mf_uploader',
        help="Upload your broker's mutual funds holdings statement"
    )

# Preview and process
if stocks_file or mf_file:
    st.markdown("---")
    st.subheader("📋 Preview Data")

    all_holdings = []
    snapshot_dates = []

    # Process stocks file
    if stocks_file:
        try:
            with st.spinner("Parsing stocks file..."):
                df_stocks, date_stocks = parse_stocks_file(stocks_file)
                st.success(f"✓ Parsed {len(df_stocks)} stock holdings from {date_stocks.strftime('%d %b %Y')}")

                with st.expander("Preview Stocks Data"):
                    st.dataframe(df_stocks.head(10), use_container_width=True)

                all_holdings.append(df_stocks)
                snapshot_dates.append(date_stocks)
        except Exception as e:
            st.error(f"Error parsing stocks file: {str(e)}")

    # Process MF file
    if mf_file:
        try:
            with st.spinner("Parsing mutual funds file..."):
                df_mf, date_mf = parse_mutual_funds_file(mf_file)
                st.success(f"✓ Parsed {len(df_mf)} mutual fund holdings from {date_mf.strftime('%d %b %Y')}")

                with st.expander("Preview Mutual Funds Data"):
                    st.dataframe(df_mf.head(10), use_container_width=True)

                all_holdings.append(df_mf)
                snapshot_dates.append(date_mf)
        except Exception as e:
            st.error(f"Error parsing mutual funds file: {str(e)}")

    # Save to database
    if all_holdings and st.button("💾 Save to Database", type="primary"):
        try:
            # Combine all holdings
            combined_df = pd.concat(all_holdings, ignore_index=True)

            # Use the latest snapshot date
            snapshot_date = max(snapshot_dates)

            with st.spinner("Saving to database..."):
                # Save holdings
                count = repo.save_holdings(combined_df, snapshot_date)

                # Calculate and save snapshot
                summary = calculate_portfolio_summary(combined_df)
                nifty, sensex = benchmark_service.get_benchmarks()

                snapshot_data = {
                    'snapshot_date': snapshot_date,
                    'total_value': summary['total_value'],
                    'stocks_value': summary['stocks_value'],
                    'mf_value': summary['mf_value'],
                    'crypto_value': summary['crypto_value'],
                    'us_stocks_value': summary['us_stocks_value'],
                    'total_invested': summary['total_invested'],
                    'total_pl': summary['total_pl'],
                    'total_pl_pct': summary['total_pl_pct'],
                    'benchmark_nifty': nifty,
                    'benchmark_sensex': sensex
                }
                repo.save_snapshot(snapshot_data)

                # Log uploads
                if stocks_file:
                    repo.log_upload({
                        'upload_date': datetime.now(),
                        'snapshot_date': snapshot_date,
                        'filename': stocks_file.name,
                        'file_type': 'stocks',
                        'records_count': len(df_stocks),
                        'status': 'success'
                    })

                if mf_file:
                    repo.log_upload({
                        'upload_date': datetime.now(),
                        'snapshot_date': snapshot_date,
                        'filename': mf_file.name,
                        'file_type': 'mutual_funds',
                        'records_count': len(df_mf),
                        'status': 'success'
                    })

            st.success(f"✅ Successfully saved {count} holdings for {snapshot_date.strftime('%d %b %Y')}")
            st.balloons()

            # Show summary
            st.markdown("### 📊 Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Value", f"₹{summary['total_value']:,.2f}")
            with col2:
                st.metric("Total Invested", f"₹{summary['total_invested']:,.2f}")
            with col3:
                st.metric("Total P&L", f"₹{summary['total_pl']:,.2f}", f"{summary['total_pl_pct']:.2f}%")

        except Exception as e:
            st.error(f"Error saving to database: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

st.markdown("---")

# Upload history
st.subheader("📜 Recent Uploads")
upload_logs = repo.get_upload_logs(limit=10)

if upload_logs:
    logs_data = []
    for log in upload_logs:
        logs_data.append({
            'Upload Date': log.upload_date.strftime('%d %b %Y %H:%M'),
            'Snapshot Date': log.snapshot_date.strftime('%d %b %Y'),
            'File': log.filename,
            'Type': log.file_type,
            'Records': log.records_count,
            'Status': log.status
        })

    st.dataframe(pd.DataFrame(logs_data), use_container_width=True, hide_index=True)
else:
    st.info("No upload history yet.")
