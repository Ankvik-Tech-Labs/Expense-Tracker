# Investment Tracker V2

A comprehensive portfolio tracking system built with Python and Streamlit for tracking stocks, mutual funds, and other investments with monthly snapshots, real-time pricing, and detailed analytics.

## Features

- **Dashboard**: Portfolio overview with KPIs, charts, and performance metrics
- **Holdings**: Detailed view of all stocks and mutual funds
- **Trends**: Historical portfolio value tracking
- **Upload**: Easy monthly data import from Excel files
- **Export**: Generate Excel reports (coming soon)
- **Real-time Pricing**: Integration with Yahoo Finance for live stock prices
- **Benchmarking**: Compare against Nifty 50 and Sensex

## Tech Stack

- **Backend**: Python 3.11+
- **Framework**: Streamlit
- **Database**: SQLite with SQLAlchemy ORM
- **Package Manager**: uv
- **Charts**: Plotly
- **Deployment**: Docker

## Quick Start

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Docker (optional, for containerized deployment)

### Option 1: Local Development (Recommended for Testing)

1. **Navigate to project directory**:
   ```bash
   cd /Users/avik/git_projects/github/investment-tracker-v2
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Run the application**:
   ```bash
   uv run streamlit run app/main.py
   ```

4. **Open in browser**:
   Visit [http://localhost:8501](http://localhost:8501)

### Option 2: Docker Deployment

1. **Build and run with Docker Compose**:
   ```bash
   docker-compose up --build
   ```

2. **Access the app**:
   Visit [http://localhost:8501](http://localhost:8501)

3. **Stop the container**:
   ```bash
   docker-compose down
   ```

## Testing the Application

### Step 1: Upload Your Data

1. Navigate to the **Upload** page (sidebar)
2. Upload your Excel files:
   - **Stocks**: `/Users/avik/Downloads/Stocks_Holdings_Statement_1772532648_09-01-2026.xlsx`
   - **Mutual Funds**: `/Users/avik/Downloads/Mutual_Funds_1772532648_10-01-2026_10-01-2026.xlsx`
3. Preview the parsed data
4. Click "Save to Database"

### Step 2: View Dashboard

1. Go to the **Dashboard** page
2. View your portfolio summary:
   - Total portfolio value
   - Asset allocation (stocks vs mutual funds)
   - Top/bottom performers
   - Portfolio trend over time

### Step 3: Explore Holdings

1. Visit the **Holdings** page
2. Browse by type:
   - Stocks tab: All stock holdings
   - Mutual Funds tab: All MF holdings
   - All Holdings tab: Combined view
3. Sort and analyze your investments

## Project Structure

```
investment-tracker-v2/
├── app/
│   ├── main.py                 # Streamlit main page
│   └── pages/
│       ├── 1_Dashboard.py      # Dashboard with charts
│       ├── 2_Holdings.py       # Detailed holdings view
│       └── 3_Upload.py         # File upload interface
├── src/
│   ├── database/
│   │   ├── models.py           # SQLAlchemy models
│   │   └── repository.py       # Data access layer
│   ├── parsers/
│   │   ├── stocks.py           # Stock Excel parser
│   │   └── mutual_funds.py     # MF Excel parser
│   └── services/
│       ├── portfolio.py        # Portfolio calculations
│       ├── pricing.py          # Yahoo Finance integration
│       └── benchmarks.py       # Nifty/Sensex data
├── data/
│   ├── uploads/                # Uploaded Excel files
│   ├── exports/                # Generated reports
│   └── portfolio.db            # SQLite database
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Security & Privacy

### Before Pushing to GitHub

Always verify no sensitive data is staged:
```bash
git status
git diff --staged
```

If you accidentally staged sensitive files:
```bash
git reset HEAD <file>
```

## Database Schema

### Holdings Table
- Stores individual stock/MF holdings per snapshot
- Tracks: name, symbol, units, prices, P&L

### Snapshots Table
- Monthly portfolio summaries
- Includes benchmark values (Nifty, Sensex)

### Upload Logs Table
- Tracks all file uploads with status

## Supported File Formats

### Stocks Excel File
Expected columns:
- Stock Name, ISIN, Quantity, Average buy price, Buy value, Closing price, Closing value, Unrealised P&L

### Mutual Funds Excel File
Expected columns:
- Scheme Name, AMC, Category, Units, Invested Value, Current Value, Returns, XIRR

## Development

### Run Tests
```bash
uv run pytest
```

### Code Quality
```bash
uv run ruff check src/
```

## Troubleshooting

### Database Issues
If you encounter database errors, delete the database and re-upload:
```bash
rm data/portfolio.db
```

### Port Already in Use
If port 8501 is busy:
```bash
uv run streamlit run app/main.py --server.port=8502
```

### Import Errors
Ensure you're in the project root and using uv:
```bash
cd /Users/avik/git_projects/github/investment-tracker-v2
uv sync
```

## Future Enhancements

- [ ] Excel export matching target format
- [ ] Google Sheets integration
- [ ] Automatic scheduled data refresh
- [ ] Tax harvesting suggestions
- [ ] Goal tracking
- [ ] Streamlit Cloud deployment

## License

MIT License

---

**Last Updated**: January 2026
