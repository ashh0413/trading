# Stock Intelligence

Screening scanner for Indian equities: technical indicators (RSI, MACD, SMA/EMA,
ATR, relative volume), configurable screening rules, ranked results, FastAPI
backend, Streamlit dashboard.

**Analysis tool only. No automated order execution. No profit predictions.**

## Project layout

```
stock-intelligence/
  app/
    main.py            FastAPI app (create_app factory)
    config.py          .env loading, provider selection
    providers/
      base.py          provider interface + error types
      mock.py          deterministic synthetic data (dev/tests)
      upstox.py        Upstox API v3 candles + v2 tokens/quotes
    services/
      market_data.py   provider selection, TTL cache
      indicators.py    RSI/MACD/SMA/EMA/ATR/relative volume
      scanner.py       screening rules + ranking
      watchlist.py     JSON-file watchlist
    models/schemas.py  Pydantic responses
    dashboard/streamlit_app.py
    utils/logging_config.py
  tests/               pytest (no live API calls)
  .env.example
  requirements.txt
```

## Setup (Windows / PowerShell)

```powershell
cd D:\Development\PROJECTS\ayaan\stock-intelligence
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env   # edit if using UPSTOX mode
```

## Run

```powershell
# 1. API (terminal 1)
uvicorn app.main:app --port 8000
# Swagger: http://127.0.0.1:8000/docs

# 2. Dashboard (terminal 2)
streamlit run app/dashboard/streamlit_app.py
# http://localhost:8501
```

Default mode is `PROVIDER=MOCK` (synthetic data — labeled as such everywhere).

## Mock vs Upstox modes

| Mode | What you need | Data |
|---|---|---|
| MOCK | nothing | deterministic synthetic candles |
| UPSTOX | `.env` filled, app on Upstox developer portal | real NSE candles |

## Upstox credentials

1. Create a trading account + API app at https://upstox.com/developer/api-documentation/
2. Copy `clientID`/`clientSecret` → `UPSTOX_API_KEY`, `UPSTOX_API_SECRET`
3. Authorize the app once (OAuth) to get a long-lived access token → `UPSTOX_ACCESS_TOKEN`
4. `UPSTOX_REDIRECT_URI` must match the one registered for the app
5. `.env` stays local (it is in `.gitignore`). Never paste tokens into chat or code.

Token expired? Upstox API rejects with 401 — regenerate the access token in the
Upstox dashboard, update `.env`, restart the API.

## Scanner rules (defaults)

| Condition | Rule |
|---|---|
| Momentum | RSI(14) in [50, 70] |
| Momentum | MACD line above signal |
| Trend | close > SMA20 |
| Trend | SMA20 > SMA50 |
| Volume | last volume > 20-bar average |

Statuses: `MATCH` (all), `PARTIAL` (half or more), `NO_MATCH`,
`INSUFFICIENT_DATA`, `DATA_UNAVAILABLE`.

## Tests

```powershell
pytest tests
```

Runs fully offline. 26 tests: indicator math (incl. Wilder ATR closed form),
edge cases (insufficient/zero-volume/duplicate candles), scanner ranking and
error containment, watchlist CRUD, secret hiding in API responses.

## Tested vs untested

**Tested:** all indicator calculations, scanner logic, watchlist, mock
provider, FastAPI endpoints, pytest suite.

**Not tested live:** Upstox endpoints (no credentials in this environment).
Endpoints were written against the official docs; first real run may need
endpoint/parameter adjustments — the README of https://upstox.com/developer
is the source of truth.

**Known limits:** 5-condition scorer (not ML), single-process API, no
WebSocket live feed yet, candle history = last ~365 days.
