"""
Database models for investment tracker.

This module defines the SQLAlchemy ORM models for storing portfolio data.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Float, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import enum


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class HoldingType(enum.Enum):
    """Type of investment holding."""

    STOCK = "stock"
    MUTUAL_FUND = "mutual_fund"
    US_STOCK = "us_stock"
    CRYPTO = "crypto"


class Holding(Base):
    """
    Individual holding record for a specific snapshot date.

    Attributes:
        id: Primary key
        snapshot_date: Date of this snapshot
        type: Type of holding (stock, mutual_fund, etc.)
        name: Display name of the holding
        symbol: Trading symbol or identifier
        isin: ISIN code (for stocks/MFs)
        units: Number of units/shares held
        avg_price: Average purchase price
        current_price: Current market price
        invested_value: Total amount invested
        current_value: Current market value
        unrealized_pl: Unrealized profit/loss
        unrealized_pl_pct: Unrealized P&L percentage
    """

    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, index=True
    )
    type: Mapped[HoldingType] = mapped_column(SQLEnum(HoldingType), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    symbol: Mapped[Optional[str]] = mapped_column(String(50))
    isin: Mapped[Optional[str]] = mapped_column(String(50))
    units: Mapped[float] = mapped_column(Float, nullable=False)
    avg_price: Mapped[float] = mapped_column(Float, nullable=False)
    current_price: Mapped[float] = mapped_column(Float, nullable=False)
    invested_value: Mapped[float] = mapped_column(Float, nullable=False)
    current_value: Mapped[float] = mapped_column(Float, nullable=False)
    unrealized_pl: Mapped[float] = mapped_column(Float, nullable=False)
    unrealized_pl_pct: Mapped[float] = mapped_column(Float, nullable=False)


class Snapshot(Base):
    """
    Monthly portfolio snapshot summary.

    Attributes:
        id: Primary key
        snapshot_date: Date of this snapshot
        total_value: Total portfolio value
        stocks_value: Total value of stock holdings
        mf_value: Total value of mutual fund holdings
        us_stocks_value: Total value of US stock holdings
        total_invested: Total amount invested
        total_pl: Total profit/loss
        total_pl_pct: Total P&L percentage
        benchmark_nifty: Nifty 50 value on this date
        benchmark_sensex: Sensex value on this date
    """

    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    snapshot_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, unique=True, index=True
    )
    total_value: Mapped[float] = mapped_column(Float, nullable=False)
    stocks_value: Mapped[float] = mapped_column(Float, default=0.0)
    mf_value: Mapped[float] = mapped_column(Float, default=0.0)
    us_stocks_value: Mapped[float] = mapped_column(Float, default=0.0)
    crypto_value: Mapped[float] = mapped_column(Float, default=0.0)
    total_invested: Mapped[float] = mapped_column(Float, nullable=False)
    total_pl: Mapped[float] = mapped_column(Float, nullable=False)
    total_pl_pct: Mapped[float] = mapped_column(Float, nullable=False)
    benchmark_nifty: Mapped[Optional[float]] = mapped_column(Float)
    benchmark_sensex: Mapped[Optional[float]] = mapped_column(Float)


class UploadLog(Base):
    """
    Log of file uploads.

    Attributes:
        id: Primary key
        upload_date: When the file was uploaded
        snapshot_date: The date this upload represents
        filename: Original filename
        file_type: Type of file (stocks, mutual_funds)
        records_count: Number of records parsed
        status: Upload status (success, error)
        error_message: Error message if upload failed
    """

    __tablename__ = "upload_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    upload_date: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow
    )
    snapshot_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    records_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500))


class WalletAddress(Base):
    """
    Ethereum wallet address for crypto DeFi tracking.

    :param id: Primary key.
    :type id: int
    :param address: Ethereum wallet address (0x...).
    :type address: str
    :param label: User-friendly label for the wallet.
    :type label: str
    :param chains: Comma-separated list of chains to scan.
    :type chains: str
    :param is_active: Whether to include in scans.
    :type is_active: bool
    :param created_at: When the wallet was added.
    :type created_at: datetime
    :param last_scanned: Last successful scan timestamp.
    :type last_scanned: datetime
    """

    __tablename__ = "wallet_addresses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(42), nullable=False, unique=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    chains: Mapped[str] = mapped_column(
        String(200), default="ethereum,base,arbitrum,optimism,polygon"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_scanned: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
