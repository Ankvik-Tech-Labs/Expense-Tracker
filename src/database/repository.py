"""
Database repository for CRUD operations.

This module provides data access methods for the investment tracker.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, select, func, text, inspect
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import (
    Base,
    Holding,
    Snapshot,
    UploadLog,
    HoldingType,
    WalletAddress,
)


class PortfolioRepository:
    """Repository for portfolio data access."""

    def __init__(self, db_path: str | Path = "data/portfolio.db"):
        """
        Initialize the repository.

        Parameters:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.SessionLocal = sessionmaker(bind=self.engine)

        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)

        # Run migrations for existing tables
        self._migrate_database()

    def _migrate_database(self) -> None:
        """
        Run database migrations to add new columns to existing tables.

        This handles schema evolution for SQLite which doesn't support
        ALTER TABLE ADD COLUMN IF NOT EXISTS.
        """
        inspector = inspect(self.engine)
        table_names = inspector.get_table_names()

        # Check if holdings table exists
        if "holdings" not in table_names:
            return

        # Add crypto_value to snapshots if missing
        if "snapshots" in table_names:
            columns = [col["name"] for col in inspector.get_columns("snapshots")]
            if "crypto_value" not in columns:
                with self.engine.connect() as conn:
                    conn.execute(
                        text(
                            "ALTER TABLE snapshots ADD COLUMN crypto_value REAL DEFAULT 0.0"
                        )
                    )
                    conn.commit()

    def get_session(self) -> Session:
        """Get a new database session."""
        return self.SessionLocal()

    # Holdings operations
    def save_holdings(self, holdings_df: pd.DataFrame, snapshot_date: datetime) -> int:
        """
        Save holdings to database.

        Parameters:
            holdings_df: DataFrame with holding data
            snapshot_date: Date of this snapshot

        Returns:
            Number of holdings saved
        """
        with self.get_session() as session:
            holdings = []
            for _, row in holdings_df.iterrows():
                holding = Holding(
                    snapshot_date=snapshot_date,
                    type=HoldingType(row["type"]),
                    name=row["name"],
                    symbol=row.get("symbol"),
                    isin=row.get("isin"),
                    units=float(row["units"]),
                    avg_price=float(row["avg_price"]),
                    current_price=float(row["current_price"]),
                    invested_value=float(row["invested_value"]),
                    current_value=float(row["current_value"]),
                    unrealized_pl=float(row["unrealized_pl"]),
                    unrealized_pl_pct=float(row["unrealized_pl_pct"]),
                )
                holdings.append(holding)

            session.add_all(holdings)
            session.commit()
            return len(holdings)

    def get_holdings(self, snapshot_date: Optional[datetime] = None) -> list[Holding]:
        """
        Get holdings for a specific date or latest per type.

        Parameters:
            snapshot_date: Specific date to retrieve, or None for latest per type

        Returns:
            List of Holding objects
        """
        with self.get_session() as session:
            if snapshot_date:
                stmt = select(Holding).where(Holding.snapshot_date == snapshot_date)
                return list(session.execute(stmt).scalars().all())
            else:
                # Get latest snapshot date for each holding type
                # This ensures we show the most recent data for stocks, MF, crypto, etc.
                all_holdings = []
                for holding_type in HoldingType:
                    # Find the latest date for this type
                    latest_date_stmt = select(func.max(Holding.snapshot_date)).where(
                        Holding.type == holding_type
                    )
                    latest_date = session.execute(latest_date_stmt).scalar()
                    if latest_date:
                        # Get all holdings of this type for that date
                        stmt = select(Holding).where(
                            Holding.snapshot_date == latest_date,
                            Holding.type == holding_type,
                        )
                        holdings = session.execute(stmt).scalars().all()
                        all_holdings.extend(holdings)
                return all_holdings

    def get_holdings_df(self, snapshot_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Get holdings as DataFrame.

        Parameters:
            snapshot_date: Specific date to retrieve, or None for latest

        Returns:
            DataFrame with holdings
        """
        holdings = self.get_holdings(snapshot_date)
        if not holdings:
            return pd.DataFrame()

        data = []
        for h in holdings:
            data.append(
                {
                    "snapshot_date": h.snapshot_date,
                    "type": h.type.value,
                    "name": h.name,
                    "symbol": h.symbol,
                    "isin": h.isin,
                    "units": h.units,
                    "avg_price": h.avg_price,
                    "current_price": h.current_price,
                    "invested_value": h.invested_value,
                    "current_value": h.current_value,
                    "unrealized_pl": h.unrealized_pl,
                    "unrealized_pl_pct": h.unrealized_pl_pct,
                }
            )

        return pd.DataFrame(data)

    # Snapshot operations
    def save_snapshot(self, snapshot_data: dict) -> None:
        """
        Save portfolio snapshot.

        Parameters:
            snapshot_data: Dictionary with snapshot data
        """
        with self.get_session() as session:
            snapshot = Snapshot(**snapshot_data)
            session.add(snapshot)
            session.commit()

    def get_snapshots(self, limit: int = 12) -> list[Snapshot]:
        """
        Get recent snapshots.

        Parameters:
            limit: Maximum number of snapshots to retrieve

        Returns:
            List of Snapshot objects
        """
        with self.get_session() as session:
            stmt = select(Snapshot).order_by(Snapshot.snapshot_date.desc()).limit(limit)
            return list(session.execute(stmt).scalars().all())

    def get_snapshots_df(self, limit: int = 12) -> pd.DataFrame:
        """
        Get snapshots as DataFrame.

        Parameters:
            limit: Maximum number of snapshots to retrieve

        Returns:
            DataFrame with snapshots
        """
        snapshots = self.get_snapshots(limit)
        if not snapshots:
            return pd.DataFrame()

        data = []
        for s in snapshots:
            data.append(
                {
                    "snapshot_date": s.snapshot_date,
                    "total_value": s.total_value,
                    "stocks_value": s.stocks_value,
                    "mf_value": s.mf_value,
                    "us_stocks_value": s.us_stocks_value,
                    "crypto_value": s.crypto_value,
                    "total_invested": s.total_invested,
                    "total_pl": s.total_pl,
                    "total_pl_pct": s.total_pl_pct,
                    "benchmark_nifty": s.benchmark_nifty,
                    "benchmark_sensex": s.benchmark_sensex,
                }
            )

        return pd.DataFrame(data)

    # Upload log operations
    def log_upload(self, upload_data: dict) -> None:
        """
        Log file upload.

        Parameters:
            upload_data: Dictionary with upload log data
        """
        with self.get_session() as session:
            upload_log = UploadLog(**upload_data)
            session.add(upload_log)
            session.commit()

    def get_upload_logs(self, limit: int = 20) -> list[UploadLog]:
        """
        Get recent upload logs.

        Parameters:
            limit: Maximum number of logs to retrieve

        Returns:
            List of UploadLog objects
        """
        with self.get_session() as session:
            stmt = select(UploadLog).order_by(UploadLog.upload_date.desc()).limit(limit)
            return list(session.execute(stmt).scalars().all())

    # Data management operations
    def snapshot_exists(self, snapshot_date: datetime) -> bool:
        """
        Check if a snapshot already exists for the given date.

        Parameters:
            snapshot_date: Date to check

        Returns:
            True if snapshot exists, False otherwise
        """
        with self.get_session() as session:
            stmt = select(Snapshot).where(Snapshot.snapshot_date == snapshot_date)
            result = session.execute(stmt).scalar()
            return result is not None

    def delete_snapshot(self, snapshot_date: datetime) -> None:
        """
        Delete a snapshot and all associated holdings.

        Parameters:
            snapshot_date: Date of snapshot to delete
        """
        with self.get_session() as session:
            # Delete holdings first
            holdings_stmt = select(Holding).where(
                Holding.snapshot_date == snapshot_date
            )
            holdings = session.execute(holdings_stmt).scalars().all()
            for holding in holdings:
                session.delete(holding)

            # Delete snapshot
            snapshot_stmt = select(Snapshot).where(
                Snapshot.snapshot_date == snapshot_date
            )
            snapshot = session.execute(snapshot_stmt).scalar()
            if snapshot:
                session.delete(snapshot)

            session.commit()

    def delete_holdings_for_date(self, snapshot_date: datetime) -> int:
        """
        Delete all holdings for a specific snapshot date.

        Parameters:
            snapshot_date: Date of holdings to delete

        Returns:
            Number of holdings deleted
        """
        with self.get_session() as session:
            stmt = select(Holding).where(Holding.snapshot_date == snapshot_date)
            holdings = session.execute(stmt).scalars().all()
            count = len(holdings)
            for holding in holdings:
                session.delete(holding)
            session.commit()
            return count

    def delete_holdings_by_type(
        self, snapshot_date: datetime, holding_types: list
    ) -> int:
        """
        Delete holdings of specific types for a snapshot date.

        Parameters:
            snapshot_date: Date of holdings to delete
            holding_types: List of holding types to delete (e.g., ['stock', 'us_stock'])

        Returns:
            Number of holdings deleted
        """
        with self.get_session() as session:
            stmt = select(Holding).where(
                Holding.snapshot_date == snapshot_date,
                Holding.type.in_([HoldingType(ht) for ht in holding_types]),
            )
            holdings = session.execute(stmt).scalars().all()
            count = len(holdings)
            for holding in holdings:
                session.delete(holding)
            session.commit()
            return count

    def clear_all_data(self) -> None:
        """
        Delete all data from all tables (holdings, snapshots, upload logs).
        Use with caution - this cannot be undone!
        """
        with self.get_session() as session:
            # Delete all holdings
            holdings = session.execute(select(Holding)).scalars().all()
            for holding in holdings:
                session.delete(holding)

            # Delete all snapshots
            snapshots = session.execute(select(Snapshot)).scalars().all()
            for snapshot in snapshots:
                session.delete(snapshot)

            # Delete all upload logs
            logs = session.execute(select(UploadLog)).scalars().all()
            for log in logs:
                session.delete(log)

            session.commit()

    # Wallet address operations
    def add_wallet(
        self,
        address: str,
        label: str,
        chains: str = "ethereum,base,arbitrum,optimism,polygon",
    ) -> WalletAddress:
        """
        Add a new wallet address.

        :param address: Ethereum wallet address (0x...).
        :type address: str
        :param label: User-friendly label for the wallet.
        :type label: str
        :param chains: Comma-separated list of chains to scan.
        :type chains: str
        :returns: Created WalletAddress object.
        :rtype: WalletAddress
        :raises ValueError: If wallet address already exists.
        """
        with self.get_session() as session:
            # Check if wallet already exists
            existing = session.execute(
                select(WalletAddress).where(WalletAddress.address == address.lower())
            ).scalar()
            if existing:
                raise ValueError(f"Wallet address already exists: {address}")

            wallet = WalletAddress(
                address=address.lower(),
                label=label,
                chains=chains,
            )
            session.add(wallet)
            session.commit()
            session.refresh(wallet)
            return wallet

    def get_wallets(self, active_only: bool = True) -> list[WalletAddress]:
        """
        Get all wallet addresses.

        :param active_only: If True, only return active wallets.
        :type active_only: bool
        :returns: List of WalletAddress objects.
        :rtype: list[WalletAddress]
        """
        with self.get_session() as session:
            stmt = select(WalletAddress)
            if active_only:
                stmt = stmt.where(WalletAddress.is_active == True)
            stmt = stmt.order_by(WalletAddress.created_at.desc())
            return list(session.execute(stmt).scalars().all())

    def get_wallet_by_id(self, wallet_id: int) -> Optional[WalletAddress]:
        """
        Get a wallet by ID.

        :param wallet_id: Wallet ID.
        :type wallet_id: int
        :returns: WalletAddress object or None if not found.
        :rtype: Optional[WalletAddress]
        """
        with self.get_session() as session:
            return session.execute(
                select(WalletAddress).where(WalletAddress.id == wallet_id)
            ).scalar()

    def update_wallet(self, wallet_id: int, **kwargs) -> None:
        """
        Update wallet properties.

        :param wallet_id: Wallet ID to update.
        :type wallet_id: int
        :param kwargs: Fields to update (label, chains, is_active).
        """
        with self.get_session() as session:
            wallet = session.execute(
                select(WalletAddress).where(WalletAddress.id == wallet_id)
            ).scalar()
            if wallet:
                for key, value in kwargs.items():
                    if hasattr(wallet, key):
                        setattr(wallet, key, value)
                session.commit()

    def delete_wallet(self, wallet_id: int) -> None:
        """
        Remove a wallet address.

        :param wallet_id: Wallet ID to delete.
        :type wallet_id: int
        """
        with self.get_session() as session:
            wallet = session.execute(
                select(WalletAddress).where(WalletAddress.id == wallet_id)
            ).scalar()
            if wallet:
                session.delete(wallet)
                session.commit()

    def update_wallet_last_scanned(self, wallet_id: int) -> None:
        """
        Update the last_scanned timestamp for a wallet.

        :param wallet_id: Wallet ID to update.
        :type wallet_id: int
        """
        from datetime import datetime

        with self.get_session() as session:
            wallet = session.execute(
                select(WalletAddress).where(WalletAddress.id == wallet_id)
            ).scalar()
            if wallet:
                wallet.last_scanned = datetime.utcnow()
                session.commit()

    # Same-month snapshot merging methods
    def find_snapshot_in_month(
        self, target_date: datetime
    ) -> Optional[tuple[datetime, Snapshot]]:
        """
        Find existing snapshot within same calendar month as target_date.

        :param target_date: Date to check for existing snapshot in same month.
        :type target_date: datetime
        :returns: Tuple of (snapshot_date, Snapshot) if found, None otherwise.
        :rtype: Optional[tuple[datetime, Snapshot]]
        """
        with self.get_session() as session:
            first_of_month = target_date.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            if target_date.month == 12:
                first_of_next_month = first_of_month.replace(
                    year=target_date.year + 1, month=1
                )
            else:
                first_of_next_month = first_of_month.replace(
                    month=target_date.month + 1
                )

            stmt = (
                select(Snapshot)
                .where(
                    Snapshot.snapshot_date >= first_of_month,
                    Snapshot.snapshot_date < first_of_next_month,
                )
                .order_by(Snapshot.snapshot_date.desc())
            )

            snapshot = session.execute(stmt).scalar()
            if snapshot:
                return (snapshot.snapshot_date, snapshot)
            return None

    def migrate_holdings_to_new_date(
        self,
        old_date: datetime,
        new_date: datetime,
        exclude_types: Optional[list[str]] = None,
    ) -> int:
        """
        Move holdings from old date to new date, excluding specified types.

        :param old_date: Original snapshot date.
        :type old_date: datetime
        :param new_date: New snapshot date to migrate holdings to.
        :type new_date: datetime
        :param exclude_types: List of holding types to exclude (delete instead of migrate).
        :type exclude_types: Optional[list[str]]
        :returns: Number of holdings migrated.
        :rtype: int
        """
        with self.get_session() as session:
            stmt = select(Holding).where(Holding.snapshot_date == old_date)
            holdings = list(session.execute(stmt).scalars().all())

            migrated_count = 0
            for holding in holdings:
                if exclude_types and holding.type.value in exclude_types:
                    session.delete(holding)
                else:
                    holding.snapshot_date = new_date
                    migrated_count += 1

            session.commit()
            return migrated_count

    def merge_holdings_within_month(
        self,
        new_date: datetime,
        new_holdings_df: pd.DataFrame,
        upload_types: list[str],
    ) -> tuple[int, int, datetime]:
        """
        Merge new holdings with existing snapshot in same month.

        If an existing snapshot exists in the same calendar month, this method:
        1. Uses the later date as the final date
        2. Migrates non-uploaded holdings to the new date
        3. Deletes holdings of the uploaded types
        4. Saves new holdings

        :param new_date: Date of the new upload.
        :type new_date: datetime
        :param new_holdings_df: DataFrame with new holdings to save.
        :type new_holdings_df: pd.DataFrame
        :param upload_types: List of holding types being uploaded (e.g., ['stock', 'mutual_fund']).
        :type upload_types: list[str]
        :returns: Tuple of (migrated_count, new_count, final_date).
        :rtype: tuple[int, int, datetime]
        """
        existing = self.find_snapshot_in_month(new_date)

        if existing:
            old_date, _ = existing
            final_date = max(old_date, new_date)

            if old_date != final_date:
                # Old date is earlier - migrate holdings to new date
                migrated = self.migrate_holdings_to_new_date(
                    old_date, final_date, exclude_types=upload_types
                )
                self.delete_snapshot(old_date)
            else:
                # Same date or old date is later - just delete holdings of uploaded types
                self.delete_holdings_by_type(old_date, upload_types)
                migrated = 0
                # Delete snapshot record to allow recalculation
                with self.get_session() as session:
                    stmt = select(Snapshot).where(
                        Snapshot.snapshot_date == old_date
                    )
                    snapshot = session.execute(stmt).scalar()
                    if snapshot:
                        session.delete(snapshot)
                        session.commit()
        else:
            final_date = new_date
            migrated = 0

        new_count = self.save_holdings(new_holdings_df, final_date)
        return (migrated, new_count, final_date)
