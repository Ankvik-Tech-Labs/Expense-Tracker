"""
Database repository for CRUD operations.

This module provides data access methods for the investment tracker.
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from sqlalchemy import create_engine, select, func, text, inspect
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base, Holding, Snapshot, UploadLog, HoldingType


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

        # Check if holdings table exists
        if "holdings" not in inspector.get_table_names():
            return

        # Future migrations can be added here
        pass

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

    def get_holdings(self, snapshot_date: Optional[datetime] = None) -> List[Holding]:
        """
        Get holdings for a specific date or latest.

        Parameters:
            snapshot_date: Specific date to retrieve, or None for latest

        Returns:
            List of Holding objects
        """
        with self.get_session() as session:
            if snapshot_date:
                stmt = select(Holding).where(Holding.snapshot_date == snapshot_date)
            else:
                # Get latest snapshot date
                latest_date_stmt = select(func.max(Holding.snapshot_date))
                latest_date = session.execute(latest_date_stmt).scalar()
                if not latest_date:
                    return []
                stmt = select(Holding).where(Holding.snapshot_date == latest_date)

            return list(session.execute(stmt).scalars().all())

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

    def get_snapshots(self, limit: int = 12) -> List[Snapshot]:
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

    def get_upload_logs(self, limit: int = 20) -> List[UploadLog]:
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
