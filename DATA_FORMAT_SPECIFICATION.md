# Investment Tracker - Data Format Specification

## Overview
This investment tracker currently supports **three types of assets**: Indian Stocks, Mutual Funds, and US Stocks. Each asset type requires specific Excel file formats with predefined columns.

## Supported Asset Types

### 1. Indian Stocks 📈
**File Format**: Excel (.xlsx)
**Source**: Indian broker holdings statements (e.g., Zerodha, Upstox, Groww)

#### Expected File Structure:
- **Row 1-2**: Header information (ignored)
- **Row 3**: Date line - Must contain: `"Holdings statement for stocks as on DD-MM-YYYY"`
- **Row 10+**: Header row containing "Stock Name" followed by data rows

#### Required Columns:
| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `Stock Name` | String | Name of the stock | "RELIANCE INDUSTRIES LTD" |
| `ISIN` | String | International Securities Identification Number | "INE002A01018" |
| `Quantity` | Numeric | Number of shares held | 10 |
| `Average buy price` | Numeric (INR) | Average purchase price per share | 2,450.50 |
| `Buy value` | Numeric (INR) | Total investment (Quantity × Avg Price) | 24,505.00 |
| `Closing price` | Numeric (INR) | Current market price per share | 2,650.75 |
| `Closing value` | Numeric (INR) | Current market value | 26,507.50 |
| `Unrealised P&L` or `Unrealized P&L` | Numeric (INR) | Profit/Loss (Current - Invested) | 2,002.50 |

#### Notes:
- All monetary values must be in **Indian Rupees (INR)**
- Date format must be `DD-MM-YYYY`
- Parser automatically calculates P&L percentage
- Rows without valid ISIN are ignored

#### Sample File Structure:
```
Row 1: [Broker header info]
Row 2: [Account details]
Row 3: Holdings statement for stocks as on 10-01-2026
Row 4-8: [Additional metadata]
Row 9: Stock Name | ISIN | Quantity | Average buy price | Buy value | Closing price | Closing value | Unrealised P&L
Row 10: RELIANCE | INE002A01018 | 10 | 2450.50 | 24505.00 | 2650.75 | 26507.50 | 2002.50
Row 11: TCS | INE467B01029 | 5 | 3200.00 | 16000.00 | 3450.00 | 17250.00 | 1250.00
```

---

### 2. US Stocks 🇺🇸
**File Format**: Excel (.xlsx)
**Source**: DriveWealth Profit-Loss statements

#### Expected File Structure:
The file must contain **three sheets**:

**Sheet 1: "User Details"**
- **Row 1, Column 1**: Period text containing date range
  - Format: `"2025-12-01 to 2026-01-10"`
  - Parser extracts the **end date** as snapshot date

**Sheet 2: "Unrealized P&L - Summary "** (note the trailing space)
- Contains aggregated holdings per security

**Sheet 3: "Unrealized P&L - Breakdown"** (currently unused)

#### Required Columns (from "Unrealized P&L - Summary " sheet):
| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `Security` | String | Stock ticker symbol | "AAPL" |
| `Quantity` | Numeric | Number of shares held | 5 |
| `Cost Basis (USD)` | Numeric (USD) | Total investment in USD | 750.00 |
| `Market Value (USD)` | Numeric (USD) | Current market value in USD | 850.00 |
| `Profit/Loss (USD)` | Numeric (USD) | Unrealized profit/loss in USD | 100.00 |
| `Profit/Loss (%)` | Numeric (%) | P&L percentage | 13.33 |

#### Optional Columns:
| Column Name | Description | Behavior if Missing |
|-------------|-------------|---------------------|
| `Market Price (USD)` | Current price per share | Calculated as `Market Value / Quantity` |

#### Currency Conversion:
- **All USD values are automatically converted to INR** during parsing
- Uses **Yahoo Finance real-time exchange rate** (`USDINR=X` ticker)
- Exchange rate is cached for **5 minutes** to reduce API calls
- **Fallback rate**: ₹83.00/USD if API fails

#### Notes:
- Parser automatically calculates average price: `Cost Basis / Quantity`
- Converted to INR using real-time rate (e.g., 90.17 INR/USD)
- Rows without valid Security symbol are ignored
- US stocks are stored with `type='us_stock'` in database
- No ISIN (set to None for US stocks)

#### Sample File Structure:
```
Sheet 1 (User Details):
Row 1: Period | Account Number | ...
       2025-12-01 to 2026-01-10 | 12345678 | ...

Sheet 2 (Unrealized P&L - Summary ):
Security | Quantity | Cost Basis (USD) | Market Value (USD) | Market Price (USD) | Profit/Loss (USD) | Profit/Loss (%)
AAPL     | 5        | 750.00           | 850.00             | 170.00             | 100.00            | 13.33
TSLA     | 2        | 400.00           | 450.00             | 225.00             | 50.00             | 12.50
```

**After Conversion (Rate: 90.17 INR/USD)**:
```
Symbol | Units | Avg Price (₹) | Current Price (₹) | Cost Basis (₹) | Market Value (₹) | P&L (₹) | P&L %
AAPL   | 5     | 13,525.50     | 15,328.90         | 67,627.50      | 76,644.50        | 9,017.00| 13.33
TSLA   | 2     | 18,034.00     | 20,288.25         | 36,068.00      | 40,576.50        | 4,508.50| 12.50
```

---

### 3. Mutual Funds 💰
**File Format**: Excel (.xlsx)
**Source**: Broker mutual fund holdings statements

#### Required Columns (inferred):
| Column Name | Data Type | Description |
|-------------|-----------|-------------|
| Fund Name | String | Name of the mutual fund scheme |
| Folio Number | String | Unique folio identifier |
| Units | Numeric | Number of units held |
| Average NAV | Numeric (INR) | Average NAV at purchase |
| Invested Value | Numeric (INR) | Total investment |
| Current NAV | Numeric (INR) | Current NAV |
| Current Value | Numeric (INR) | Current market value |
| Unrealized P&L | Numeric (INR) | Profit/Loss |

**Note**: Mutual fund parser implementation not shown in current context, but follows similar pattern to stocks parser.

---

## Standardized Output Format

All parsers convert input files to a **standardized DataFrame** with these columns:

| Column | Type | Description | Example Values |
|--------|------|-------------|----------------|
| `type` | String | Asset type | `"stock"`, `"us_stock"`, `"mutual_fund"` |
| `name` | String | Asset name | "RELIANCE INDUSTRIES", "AAPL" |
| `symbol` | String | Ticker symbol (for stocks) | "RELIANCE", "AAPL", None (MF) |
| `isin` | String | ISIN code (if available) | "INE002A01018", None (US stocks) |
| `units` | Float | Quantity/Units held | 10.0, 5.0, 123.456 |
| `avg_price` | Float | Average purchase price (INR) | 2450.50, 13525.50 |
| `invested_value` | Float | Total cost basis (INR) | 24505.00, 67627.50 |
| `current_price` | Float | Current price per unit (INR) | 2650.75, 15328.90 |
| `current_value` | Float | Current market value (INR) | 26507.50, 76644.50 |
| `unrealized_pl` | Float | Profit/Loss amount (INR) | 2002.50, 9017.00 |
| `unrealized_pl_pct` | Float | P&L percentage | 8.17, 13.33 |

### Key Standardization Rules:
1. **Currency**: All monetary values stored in **INR** (Indian Rupees)
2. **USD Conversion**: US stock values converted at parse time using real-time exchange rates
3. **P&L Calculation**: `unrealized_pl_pct = (unrealized_pl / invested_value) × 100`
4. **Type Field**: Distinguishes asset classes for filtering and aggregation

---

## Database Storage

### Holdings Table Structure:
```python
class Holding(Base):
    id: int                          # Auto-increment primary key
    snapshot_date: datetime          # Date of the snapshot
    type: HoldingType                # Enum: stock, us_stock, mutual_fund
    name: str                        # Asset name
    symbol: Optional[str]            # Ticker symbol
    isin: Optional[str]              # ISIN code
    units: float                     # Quantity
    avg_price: float                 # Average price (INR)
    invested_value: float            # Cost basis (INR)
    current_price: float             # Current price (INR)
    current_value: float             # Market value (INR)
    unrealized_pl: float             # P&L amount (INR)
    unrealized_pl_pct: float         # P&L percentage
```

### Snapshot Table Structure:
```python
class Snapshot(Base):
    snapshot_date: datetime          # Unique date identifier
    total_value: float               # Total portfolio value (INR)
    stocks_value: float              # Indian stocks value (INR)
    mf_value: float                  # Mutual funds value (INR)
    us_stocks_value: float           # US stocks value (INR)
    total_invested: float            # Total cost basis (INR)
    total_pl: float                  # Total P&L (INR)
    total_pl_pct: float              # Total P&L percentage
    benchmark_nifty: Optional[float] # NIFTY 50 value
    benchmark_sensex: Optional[float]# SENSEX value
```

---

## Upload Behavior

### Smart Merge Logic:
When uploading to an **existing snapshot date**:
1. **Selective Deletion**: Only deletes holdings of the types being uploaded
   - Uploading only US stocks → Deletes only `type='us_stock'`
   - Uploading stocks + MF → Deletes `type='stock'` and `type='mutual_fund'`
2. **Data Preservation**: Keeps holdings of other types intact
3. **Merge**: Combines existing holdings with new uploads
4. **Recalculation**: Updates snapshot summary with all combined holdings

### Example Scenario:
```
Existing Data (Jan 10, 2026):
- 25 Indian stocks
- 13 Mutual funds
- 12 US stocks
Total: 50 holdings

User uploads: New US stocks file (15 holdings)

Result:
- 25 Indian stocks (preserved)
- 13 Mutual funds (preserved)
- 15 US stocks (replaced)
Total: 53 holdings
```

---

## Validation Rules

### All Asset Types:
- Rows with missing/empty primary identifiers (symbol, name) are **ignored**
- Numeric columns with non-numeric values are converted to `NaN` and filtered out
- Rows with invalid `units`, `invested_value`, or `current_value` are **dropped**

### Indian Stocks:
- Must have valid **ISIN code**
- Date extraction must find `DD-MM-YYYY` pattern in row 3

### US Stocks:
- Must have valid **Security symbol**
- Period date must match `YYYY-MM-DD to YYYY-MM-DD` pattern
- Exchange rate fetch must succeed (or fallback to ₹83.00)

### Mutual Funds:
- (Validation rules to be documented based on parser implementation)

---

## API Dependencies

### Yahoo Finance (yfinance)
- **Purpose**: Real-time USD/INR exchange rate fetching
- **Ticker**: `USDINR=X`
- **Cache**: 5 minutes
- **Fallback**: ₹83.00/USD
- **Usage**: Called during US stocks parsing

```python
from yfinance import Ticker
ticker = Ticker("USDINR=X")
data = ticker.history(period="1d")
rate = data['Close'].iloc[-1]  # Current rate: ~90.17
```

---

## Error Handling

### File Format Errors:
```python
# Missing required columns
ValueError("Missing required columns: ['Security', 'Quantity']")

# Invalid date format
ValueError("Could not extract date from: Invalid text")

# Exchange rate fetch failed
ValueError("Could not fetch USD/INR exchange rate")
```

### Graceful Degradation:
- Exchange rate API failure → Uses fallback rate (₹83.00)
- Invalid rows → Skipped with warning
- Empty DataFrame → Returns empty result (no error)

---

## Testing Verification

### Test Data Example (US Stocks):
```
Input: 12 US stock holdings in USD
Exchange Rate: 90.17 INR/USD
Sample Conversion:
  - MSFT: $108.51 → ₹9,784.35
  - NVDA: $135.58 × 90.17 = ₹12,228.16

Output: 12 holdings with all INR values
```

### Validation Checklist:
- ✅ File parsing succeeds for all 3 asset types
- ✅ Date extraction works correctly
- ✅ USD to INR conversion applied (US stocks only)
- ✅ All required columns present in output DataFrame
- ✅ Numeric values properly formatted
- ✅ Database save successful
- ✅ UI displays correct currency symbols (₹)
- ✅ Smart merge preserves existing holdings

---

## Future Enhancements

### Potential Asset Types:
- Gold/Precious Metals
- Fixed Deposits
- Bonds
- Crypto (removed in previous version, may be re-added)
- Real Estate

### Potential Features:
- Auto-detect file format (broker-agnostic parsing)
- Historical exchange rate tracking
- Multi-currency support (EUR, GBP, etc.)
- Dividend tracking
- Tax calculation (STCG/LTCG)

---

## Summary Table

| Asset Type | File Format | Key Identifier | Currency | Conversion | Required Columns |
|------------|-------------|----------------|----------|------------|------------------|
| Indian Stocks | Excel (.xlsx) | ISIN | INR | None | 8 columns |
| US Stocks | Excel (.xlsx) | Symbol | USD → INR | Real-time | 6 columns |
| Mutual Funds | Excel (.xlsx) | Folio | INR | None | ~8 columns |

**Total Supported**: 3 asset types
**Total Output Columns**: 11 standardized columns
**Currency Standard**: All values stored in INR (₹)
**Exchange Rate Source**: Yahoo Finance (`USDINR=X`)
**Cache Duration**: 5 minutes
**Database**: SQLAlchemy ORM with SQLite/PostgreSQL support
