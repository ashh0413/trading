# Nifty 213 Scanner v2

Multi-indicator RSI scanner for Nifty FnO stocks.

## Setup

```bash
# One-time install
pip install yfinance pandas openpyxl

# Or with the venv
D:\MOVED FROM C\Python\venvs\py311\Scripts\pip install yfinance pandas openpyxl
```

## Quick Start

### Option 1 — Double-click
```
run.bat
```

### Option 2 — Terminal
```bash
cd D:\MOVED FROM C\Python\venvs\py311\Scripts
python run_all.py
```

### Option 3 — Individual steps
```bash
python scanner_v2.py   # Fetches data, computes RSI/MACD/Volume/SMA → scanner_results.json
python scorer.py       # Scores each stock → scored_results.json
python report.py       # Creates reports → nifty213_report.html, nifty213_export.csv
```

Open `dashboard.html` in any browser (no server needed — it reads JSON files directly).

## Files

| File | Purpose |
|------|---------|
| `scanner_v2.py` | Downloads OHLCV via yfinance, computes RSI/MACD/Volume ratio/SMA crossovers |
| `scorer.py` | Scores each stock on RSI, MACD, Volume, Trend, Divergence, Sector strength |
| `report.py` | Generates HTML dashboard + CSV export |
| `dashboard.html` | Interactive browser dashboard (open directly) |
| `run_all.py` | Runs full pipeline + opens dashboard |
| `run.bat` | Double-click launcher for Windows |
| `scanner_results.json` | Raw scan output (RSI, MACD, volume, SMA data per stock) |
| `scored_results.json` | Scored + ranked stocks |

## Indicators

- **RSI 14** — Daily, weekly, monthly, hourly timeframes
- **MACD** — Signal line crossovers (bullish/bearish)
- **Volume Ratio** — Current volume vs 20-day average
- **SMA Crossover** — 50 SMA vs 200 SMA (long-term trend)
- **Divergences** — Hidden and regular divergences on RSI

## Scoring (0–100)

| Component | Weight |
|-----------|--------|
| RSI Momentum | 25 |
| MACD Strength | 25 |
| Volume Activity | 20 |
| Trend Strength | 15 |
| Sector Weight | 15 |

## Sector Categories

Auto, Auto Ancillary, Banks, Capital Goods, Capital Markets, Cement,
FMCG, Finance, Furniture & Furnishing, Gas Distribution,
Healthcare Services, Hotels & Tourism, Infrastructure & Logistics,
Insurance, Internet & New-age, Media & Entertainment,
Metals & Minerals, Oil & Gas, Others, Pharma & Healthcare, Power, Retail

## Telegram Alerts (optional)

Set env var `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` before running
`scorer.py` — it will push the top BUY/SELL signals to your Telegram channel.

## Schedule

To run daily at market open (9:15 AM IST), add a Windows Task Scheduler task:

```
schtasks /create /tn "Nifty Scanner" /tr "D:\MOVED FROM C\Python\venvs\py311\Scripts\run.bat" /sc daily /st 09:15
```

Or use the Windows Task Scheduler GUI to point it at `run.bat`.
