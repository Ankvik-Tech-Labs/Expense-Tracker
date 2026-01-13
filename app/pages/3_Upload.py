"""Upload page for adding new monthly data."""

import streamlit as st
from datetime import datetime
import pandas as pd

from src.parsers.stocks import parse_stocks_file
from src.parsers.mutual_funds import parse_mutual_funds_file
from src.parsers.us_stocks import parse_us_stocks_file
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
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("📈 Indian Stocks")
    stocks_file = st.file_uploader(
        "Upload Stocks Excel File",
        type=["xlsx"],
        key="stocks_uploader",
        help="Upload your broker's stocks holdings statement",
    )

with col2:
    st.subheader("💰 Mutual Funds")
    mf_file = st.file_uploader(
        "Upload Mutual Funds Excel File",
        type=["xlsx"],
        key="mf_uploader",
        help="Upload your broker's mutual funds holdings statement",
    )

with col3:
    st.subheader("🇺🇸 US Stocks")
    us_stocks_file = st.file_uploader(
        "Upload US Stocks P&L File",
        type=["xlsx"],
        key="us_stocks_uploader",
        help="Upload DriveWealth Profit-Loss statement",
    )

# Preview and process
if stocks_file or mf_file or us_stocks_file:
    st.markdown("---")
    st.subheader("📋 Preview Data")

    all_holdings = []
    snapshot_dates = []

    # Process stocks file
    if stocks_file:
        try:
            with st.spinner("Parsing stocks file..."):
                df_stocks, date_stocks = parse_stocks_file(stocks_file)
                st.success(
                    f"✓ Parsed {len(df_stocks)} Indian stock holdings from {date_stocks.strftime('%d %b %Y')}"
                )

                with st.expander("Preview Indian Stocks Data"):
                    st.dataframe(df_stocks.head(10), width="stretch")

                all_holdings.append(df_stocks)
                snapshot_dates.append(date_stocks)
        except Exception as e:
            st.error(f"Error parsing stocks file: {str(e)}")

    # Process MF file
    if mf_file:
        try:
            with st.spinner("Parsing mutual funds file..."):
                df_mf, date_mf = parse_mutual_funds_file(mf_file)
                st.success(
                    f"✓ Parsed {len(df_mf)} mutual fund holdings from {date_mf.strftime('%d %b %Y')}"
                )

                with st.expander("Preview Mutual Funds Data"):
                    st.dataframe(df_mf.head(10), width="stretch")

                all_holdings.append(df_mf)
                snapshot_dates.append(date_mf)
        except Exception as e:
            st.error(f"Error parsing mutual funds file: {str(e)}")

    # Process US stocks file
    if us_stocks_file:
        try:
            with st.spinner("Parsing US stocks file..."):
                df_us_stocks, date_us_stocks = parse_us_stocks_file(us_stocks_file)
                st.success(
                    f"✓ Parsed {len(df_us_stocks)} US stock holdings from {date_us_stocks.strftime('%d %b %Y')}"
                )

                with st.expander("Preview US Stocks Data"):
                    st.dataframe(df_us_stocks.head(10), width="stretch")

                all_holdings.append(df_us_stocks)
                snapshot_dates.append(date_us_stocks)
        except Exception as e:
            st.error(f"Error parsing US stocks file: {str(e)}")

    # Save to database
    if all_holdings:
        # Combine all holdings
        combined_df = pd.concat(all_holdings, ignore_index=True)
        snapshot_date = max(snapshot_dates)

        # Determine which types are being uploaded
        upload_types = []
        if stocks_file:
            upload_types.append("stock")
        if mf_file:
            upload_types.append("mutual_fund")
        if us_stocks_file:
            upload_types.append("us_stock")

        # Check for existing snapshot in the same month
        existing_in_month = repo.find_snapshot_in_month(snapshot_date)
        same_date_exists = repo.snapshot_exists(snapshot_date)

        # Show appropriate message based on existing data
        if same_date_exists:
            st.warning(
                f"⚠️ Data for {snapshot_date.strftime('%d %b %Y')} already exists! "
                f"Saving will replace existing data for: {', '.join(upload_types)}"
            )
        elif existing_in_month:
            old_date, _ = existing_in_month
            st.info(
                f"📅 Found existing snapshot for {old_date.strftime('%d %b %Y')} "
                f"in the same month. Data will be merged into {snapshot_date.strftime('%d %b %Y')}."
            )

        # Save button
        if st.button("💾 Save to Database", type="primary"):
            try:
                with st.spinner("Saving to database..."):
                    # Use merge method (handles all scenarios: new, replace, merge)
                    migrated, new_count, final_date = repo.merge_holdings_within_month(
                        new_date=snapshot_date,
                        new_holdings_df=combined_df,
                        upload_types=upload_types,
                    )

                    # Get all holdings after merge to recalculate summary
                    all_holdings_df = repo.get_holdings_df(final_date)
                    summary = calculate_portfolio_summary(all_holdings_df)
                    nifty, sensex = benchmark_service.get_benchmarks()

                    # Save snapshot with recalculated totals
                    snapshot_data = {
                        "snapshot_date": final_date,
                        "total_value": summary["total_value"],
                        "stocks_value": summary["stocks_value"],
                        "mf_value": summary["mf_value"],
                        "us_stocks_value": summary["us_stocks_value"],
                        "crypto_value": summary.get("crypto_value", 0.0),
                        "total_invested": summary["total_invested"],
                        "total_pl": summary["total_pl"],
                        "total_pl_pct": summary["total_pl_pct"],
                        "benchmark_nifty": nifty,
                        "benchmark_sensex": sensex,
                    }
                    repo.save_snapshot(snapshot_data)

                    # Log uploads
                    if stocks_file:
                        repo.log_upload(
                            {
                                "upload_date": datetime.now(),
                                "snapshot_date": final_date,
                                "filename": stocks_file.name,
                                "file_type": "stocks",
                                "records_count": len(df_stocks),
                                "status": "success",
                            }
                        )

                    if mf_file:
                        repo.log_upload(
                            {
                                "upload_date": datetime.now(),
                                "snapshot_date": final_date,
                                "filename": mf_file.name,
                                "file_type": "mutual_funds",
                                "records_count": len(df_mf),
                                "status": "success",
                            }
                        )

                    if us_stocks_file:
                        repo.log_upload(
                            {
                                "upload_date": datetime.now(),
                                "snapshot_date": final_date,
                                "filename": us_stocks_file.name,
                                "file_type": "us_stocks",
                                "records_count": len(df_us_stocks),
                                "status": "success",
                            }
                        )

                # Build success message
                if migrated > 0:
                    st.success(
                        f"✅ Successfully merged data for {final_date.strftime('%d %b %Y')} - "
                        f"Added {new_count} new holdings, preserved {migrated} existing holdings "
                        f"(Total: {len(all_holdings_df)} holdings)"
                    )
                else:
                    st.success(
                        f"✅ Successfully saved {new_count} holdings for {final_date.strftime('%d %b %Y')} "
                        f"(Total: {len(all_holdings_df)} holdings)"
                    )
                st.balloons()

                # Show summary
                st.markdown("### 📊 Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Value", f"₹{summary['total_value']:,.2f}")
                with col2:
                    st.metric(
                        "Total Invested", f"₹{summary['total_invested']:,.2f}"
                    )
                with col3:
                    st.metric(
                        "Total P&L",
                        f"₹{summary['total_pl']:,.2f}",
                        f"{summary['total_pl_pct']:.2f}%",
                    )

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
        logs_data.append(
            {
                "Upload Date": log.upload_date.strftime("%d %b %Y %H:%M"),
                "Snapshot Date": log.snapshot_date.strftime("%d %b %Y"),
                "File": log.filename,
                "Type": log.file_type,
                "Records": log.records_count,
                "Status": log.status,
            }
        )

    st.dataframe(pd.DataFrame(logs_data), width="stretch", hide_index=True)
else:
    st.info("No upload history yet.")

st.markdown("---")

# Data Management Section
st.subheader("🗑️ Data Management")

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### Delete Specific Snapshot")
    st.caption("Remove a specific month's data and all associated holdings")

    # Get all snapshots for dropdown
    snapshots = repo.get_snapshots(limit=100)
    if snapshots:
        snapshot_options = {
            s.snapshot_date.strftime("%b %Y"): s.snapshot_date for s in snapshots
        }
        selected_snapshot = st.selectbox(
            "Select snapshot to delete",
            options=list(snapshot_options.keys()),
            key="delete_snapshot_select",
        )

        if st.button("🗑️ Delete Selected Snapshot", type="secondary"):
            if selected_snapshot:
                snapshot_date = snapshot_options[selected_snapshot]
                try:
                    repo.delete_snapshot(snapshot_date)
                    st.success(f"✅ Deleted snapshot for {selected_snapshot}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting snapshot: {str(e)}")
    else:
        st.info("No snapshots available to delete")

with col2:
    st.markdown("#### Clear All Data")
    st.caption("⚠️ Delete ALL data from the database - cannot be undone!")

    # Add a confirmation checkbox
    confirm_clear = st.checkbox(
        "I understand this will delete all data permanently", key="confirm_clear"
    )

    if st.button("🗑️ Clear All Data", type="secondary", disabled=not confirm_clear):
        try:
            repo.clear_all_data()
            st.success("✅ All data has been cleared from the database")
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing data: {str(e)}")
