"""Crypto wallet management and DeFi position scanning."""

import streamlit as st
import pandas as pd
from datetime import datetime

from src.database.repository import PortfolioRepository
from src.services.crypto import CryptoService
from src.services.portfolio import calculate_portfolio_summary
from src.services.benchmarks import BenchmarkService

st.set_page_config(page_title="Crypto", page_icon="₿", layout="wide")

st.title("₿ Crypto DeFi Positions")

st.markdown("""
Scan your Ethereum wallets for DeFi positions across multiple chains and protocols.
Supported chains: Ethereum, Base, Arbitrum, Optimism, Polygon.
""")

# Check for crypto module availability
if not CryptoService.is_available():
    st.error("crypto-portfolio-tracker is not installed.")
    st.info(
        "Install it with: `pip install git+https://github.com/Ankvik-Tech-Labs/Crypto-portfolio-tracker.git`"
    )
    st.stop()

# Check for required env var
if not CryptoService.check_infura_configured():
    st.error("WEB3_INFURA_PROJECT_ID environment variable is not set.")
    st.info("Add your Infura project ID to .env file or environment variables.")
    st.code("export WEB3_INFURA_PROJECT_ID='your_project_id_here'", language="bash")
    st.stop()

# Initialize services
repo = PortfolioRepository()
crypto_service = CryptoService()
benchmark_service = BenchmarkService()

st.markdown("---")

# Wallet Management Section
st.subheader("🔐 Wallet Management")

col1, col2 = st.columns([2, 1])

with col1:
    # Add new wallet form
    with st.form("add_wallet", clear_on_submit=True):
        st.markdown("**Add New Wallet**")
        address = st.text_input(
            "Wallet Address",
            placeholder="0x...",
            help="Enter a valid Ethereum wallet address (42 characters starting with 0x)",
        )
        label = st.text_input(
            "Label",
            placeholder="e.g., Main Wallet, DeFi Wallet",
            help="A friendly name to identify this wallet",
        )
        chains = st.multiselect(
            "Chains to scan",
            ["ethereum", "base", "arbitrum", "optimism", "polygon"],
            default=["ethereum", "base"],
            help="Select which chains to scan for DeFi positions",
        )
        submitted = st.form_submit_button("➕ Add Wallet", type="primary")

        if submitted:
            if not address:
                st.warning("Please enter a wallet address")
            elif not label:
                st.warning("Please enter a label for the wallet")
            elif not address.startswith("0x") or len(address) != 42:
                st.error(
                    "Invalid wallet address. Must be 42 characters starting with 0x"
                )
            else:
                try:
                    repo.add_wallet(address, label, ",".join(chains))
                    st.success(f"Added wallet: {label}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error adding wallet: {e}")

with col2:
    # Display existing wallets
    st.markdown("**Your Wallets**")
    wallets = repo.get_wallets()
    if wallets:
        for wallet in wallets:
            with st.expander(f"🔑 {wallet.label}", expanded=False):
                st.code(wallet.address, language=None)
                st.caption(f"**Chains:** {wallet.chains}")
                if wallet.last_scanned:
                    st.caption(
                        f"**Last scanned:** {wallet.last_scanned.strftime('%d %b %Y %H:%M')}"
                    )
                else:
                    st.caption("**Last scanned:** Never")
                if st.button("🗑️ Remove", key=f"del_{wallet.id}"):
                    repo.delete_wallet(wallet.id)
                    st.success(f"Removed wallet: {wallet.label}")
                    st.rerun()
    else:
        st.info("No wallets added yet. Add a wallet to start scanning.")

st.markdown("---")

# Scan Positions Section
st.subheader("🔍 Scan Positions")

wallets = repo.get_wallets()
if not wallets:
    st.warning("Add a wallet above to start scanning for DeFi positions.")
    st.stop()

# Wallet selection
selected_wallet = st.selectbox(
    "Select wallet to scan",
    wallets,
    format_func=lambda w: f"{w.label} ({w.address[:8]}...{w.address[-6:]})",
    help="Choose which wallet to scan for DeFi positions",
)

# Scan button
if st.button("🔍 Fetch Crypto Positions", type="primary"):
    with st.spinner(f"Scanning {selected_wallet.label} for DeFi positions..."):
        try:
            # Parse chains from wallet
            chains = (
                selected_wallet.chains.split(",") if selected_wallet.chains else None
            )

            # Fetch positions
            df, total_usd, total_inr = crypto_service.fetch_and_convert(
                selected_wallet.address, chains
            )

            # Store results in session state
            st.session_state["crypto_df"] = df
            st.session_state["crypto_total_usd"] = total_usd
            st.session_state["crypto_total_inr"] = total_inr
            st.session_state["crypto_wallet_id"] = selected_wallet.id
            st.session_state["crypto_wallet_address"] = selected_wallet.address

            # Update last scanned
            repo.update_wallet_last_scanned(selected_wallet.id)

        except Exception as e:
            st.error(f"Error scanning wallet: {e}")
            import traceback

            with st.expander("Error Details"):
                st.code(traceback.format_exc())

# Display results from session state
if "crypto_df" in st.session_state:
    df = st.session_state["crypto_df"]
    total_usd = st.session_state["crypto_total_usd"]
    total_inr = st.session_state["crypto_total_inr"]

    if df.empty:
        st.info("No DeFi positions found for this wallet on the selected chains.")
    else:
        # Show summary metrics
        st.markdown("### 📊 Position Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total USD Value", f"${total_usd:,.2f}")
        with col2:
            st.metric("Total INR Value", f"₹{total_inr:,.2f}")
        with col3:
            st.metric("Positions Found", len(df))
        with col4:
            chains_found = df["chain"].nunique() if "chain" in df.columns else 0
            st.metric("Chains Active", chains_found)

        st.markdown("---")

        # Show positions table
        st.markdown("### 📋 Positions")

        # Create display DataFrame
        display_cols = ["name", "chain", "units", "usd_value", "current_value"]
        if "apy" in df.columns:
            display_cols.append("apy")

        display_df = df[[c for c in display_cols if c in df.columns]].copy()
        display_df = display_df.rename(
            columns={
                "name": "Position",
                "chain": "Chain",
                "units": "Balance",
                "usd_value": "USD Value",
                "current_value": "INR Value",
                "apy": "APY %",
            }
        )

        # Format numbers
        if "USD Value" in display_df.columns:
            display_df["USD Value"] = display_df["USD Value"].apply(
                lambda x: f"${x:,.2f}" if pd.notna(x) else "-"
            )
        if "INR Value" in display_df.columns:
            display_df["INR Value"] = display_df["INR Value"].apply(
                lambda x: f"₹{x:,.2f}" if pd.notna(x) else "-"
            )
        if "Balance" in display_df.columns:
            display_df["Balance"] = display_df["Balance"].apply(
                lambda x: f"{x:,.6f}" if pd.notna(x) else "-"
            )
        if "APY %" in display_df.columns:
            display_df["APY %"] = display_df["APY %"].apply(
                lambda x: f"{x:.2f}%" if pd.notna(x) else "-"
            )

        st.dataframe(display_df, width="stretch", hide_index=True)

        st.markdown("---")

        # Save to database section
        st.markdown("### 💾 Save to Database")
        st.caption(
            "Save these positions as a snapshot to track historical portfolio data."
        )

        snapshot_date = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Check for existing snapshot in the same month
        existing_in_month = repo.find_snapshot_in_month(snapshot_date)
        same_date_exists = repo.snapshot_exists(snapshot_date)

        # Show appropriate message based on existing data
        if same_date_exists:
            st.warning(
                f"⚠️ Crypto data for {snapshot_date.strftime('%d %b %Y')} already exists! "
                f"Saving will replace existing crypto positions."
            )
        elif existing_in_month:
            old_date, _ = existing_in_month
            st.info(
                f"📅 Found existing snapshot for {old_date.strftime('%d %b %Y')} "
                f"in the same month. Data will be merged into {snapshot_date.strftime('%d %b %Y')}."
            )

        if st.button("💾 Save Crypto Positions", type="primary"):
            try:
                with st.spinner("Saving crypto positions..."):
                    # Prepare holdings DataFrame for saving (only standard columns)
                    save_df = df[
                        [
                            "type",
                            "name",
                            "symbol",
                            "isin",
                            "units",
                            "avg_price",
                            "current_price",
                            "invested_value",
                            "current_value",
                            "unrealized_pl",
                            "unrealized_pl_pct",
                        ]
                    ].copy()

                    # Use merge method (handles all scenarios: new, replace, merge)
                    migrated, new_count, final_date = repo.merge_holdings_within_month(
                        new_date=snapshot_date,
                        new_holdings_df=save_df,
                        upload_types=["crypto"],
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

                    # Log upload
                    repo.log_upload(
                        {
                            "upload_date": datetime.now(),
                            "snapshot_date": final_date,
                            "filename": f"crypto_scan_{st.session_state['crypto_wallet_address'][:10]}",
                            "file_type": "crypto",
                            "records_count": new_count,
                            "status": "success",
                        }
                    )

                # Build success message
                if migrated > 0:
                    st.success(
                        f"✅ Successfully merged crypto data for {final_date.strftime('%d %b %Y')} - "
                        f"Added {new_count} crypto positions, preserved {migrated} existing holdings "
                        f"(Total: {len(all_holdings_df)} holdings)"
                    )
                else:
                    st.success(
                        f"✅ Saved {new_count} crypto positions for {final_date.strftime('%d %b %Y')} "
                        f"(Total: {len(all_holdings_df)} holdings)"
                    )
                st.balloons()

                # Clear session state
                del st.session_state["crypto_df"]
                del st.session_state["crypto_total_usd"]
                del st.session_state["crypto_total_inr"]

            except Exception as e:
                st.error(f"Error saving positions: {e}")
                import traceback

                with st.expander("Error Details"):
                    st.code(traceback.format_exc())

st.markdown("---")

# Supported Protocols Info
with st.expander("ℹ️ Supported Protocols & Chains"):
    st.markdown("""
    **Supported Chains:**
    - Ethereum Mainnet
    - Base
    - Arbitrum One
    - Optimism
    - Polygon

    **Supported Protocols:**
    - Aave v3 (Lending/Borrowing)
    - Lido (Liquid Staking)
    - Morpho Blue (Lending)
    - Ether.fi (Restaking)
    - Beefy (Yield Vaults)

    **Note:** Only wallets with active DeFi positions will show results.
    Simple token holdings (ETH, ERC-20 tokens) are not tracked.
    """)
