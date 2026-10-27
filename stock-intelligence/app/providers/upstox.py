"""Upstox provider (API v3 + v2 quote/token endpoints).

Auth flow: short-lived token via POST /v2/tokens/generate using the
long-lived access token, then all data calls with that token.

Endpoints (official docs, verify before relying on them in production):
  https://upstox.com/developer/api-documentation/
  - POST /v2/tokens/generate
  - POST /v3/historical-candle/intraday   (interval candles)
  - GET  /v3/intraday-quote                (quotes with candles)
  - POST /v2/quotes/market                (live market quote)
Instrument master: https://cdn.upstox.com/api/public/instrument-master/nscf/nscf.csv
"""
import time
import urllib.request

import pandas as pd
import httpx

from .base import (MarketDataProvider, ProviderError, AuthError,
                   RateLimitError)

API_BASE = "https://api.upstox.com"
INSTRUMENT_MASTER_URL = ("https://cdn.upstox.com/api/public/"
                        "instrument-master/nscf/nscf.csv")

# ponytail: instrument master cached 24h in a local CSV; refresh weekly
# or when new symbols 404.
_CACHE_TTL = 86_400


class UpstoxProvider(MarketDataProvider):
    name = "upstox"

    def __init__(self, creds: dict, timeout: float = 15.0):
        self._creds = creds
        self._timeout = timeout
        self._inst_cache: dict[str, str] = {}
        self._inst_loaded_at = 0.0
        self._client = httpx.Client(base_url=API_BASE, timeout=timeout,
                                    headers={"Accept": "application/json"})
        self._tmp_token: str | None = None
        self._tmp_token_at = 0.0

    # ---- auth ---------------------------------------------------------
    def _short_token(self, force: bool = False) -> str:
        # Tokens are good ~15 min; refresh a minute early.
        if not force and self._tmp_token and time.time() - self._tmp_token_at < 840:
            return self._tmp_token
        resp = self._client.post("/v2/tokens/generate", json={
            "accessToken": self._creds["access_token"],
            "apiKey": self._creds["api_key"],
            "apiSecret": self._creds["api_secret"],
            "redirectUri": self._creds["redirect_uri"],
        })
        if resp.status_code in (401, 403):
            raise AuthError(
                "Upstox token rejected (expired or wrong app). "
                "Regenerate the access token on the Upstox developer "
                "dashboard and update UPSTOX_ACCESS_TOKEN in .env.")
        resp.raise_for_status()
        self._tmp_token = resp.json()["data"]["token"]
        self._tmp_token_at = time.time()
        return self._tmp_token

    # ---- instrument resolution ----------------------------------------
    def _load_instruments(self) -> None:
        if self._inst_cache and time.time() - self._inst_loaded_at < _CACHE_TTL:
            return
        urllib.request.urlretrieve(INSTRUMENT_MASTER_URL, "nscf_instruments.csv")
        df = pd.read_csv("nscf_instruments.csv")
        ns = df[(df["exchange"] == "NSE") & (df["segment"] == "EQ")]
        self._inst_cache = {r.nscf_symbol: r.instrument_token
                            for r in ns.itertuples()}
        self._inst_loaded_at = time.time()

    def resolve(self, symbol: str) -> str:
        self._load_instruments()
        key = symbol.upper().replace("-", "")
        if key not in self._inst_cache:
            raise ProviderError(f"{symbol!r} not found in Upstox NSE instrument master")
        return self._inst_cache[key]

    # ---- data ---------------------------------------------------------
    def _get_candles_range(self, instrument: str, from_date: str, to_date: str):
        token = self._short_token()
        for attempt in range(3):
            resp = self._client.post(
                "/v3/historical-candle/intraday",
                params={"fromDate": from_date, "toDate": to_date, "limit": 10000},
                json={"instrument": instrument, "timeframe": 1440},
                headers={"Authorization": f"Bearer {token}"},
            )
            if resp.status_code in (401, 403):
                token = self._short_token(force=True)
                continue
            if resp.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            resp.raise_for_status()
            break
        rows = resp.json().get("data", [])
        if not rows:
            raise ProviderError(f"No candle data for {instrument}")
        out = pd.DataFrame(rows).rename(columns={
            "timestamp": "date", "open": "open", "high": "high",
            "low": "low", "close": "close", "volume": "volume"})
        return out[["date", "open", "high", "low", "close", "volume"]]

    def get_candles(self, symbol: str, period_days: int = 365) -> pd.DataFrame:
        instrument = self.resolve(symbol)
        to = pd.Timestamp.today().strftime("%Y-%m-%d")
        from_ = (pd.Timestamp.today()
                 - pd.Timedelta(days=period_days + 30)).strftime("%Y-%m-%d")
        df = self._get_candles_range(instrument, from_, to)
        return df

    def get_quote(self, symbol: str) -> dict:
        instrument = self.resolve(symbol)
        token = self._short_token()
        resp = self._client.post(
            "/v2/quotes/market",
            json=[instrument],
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code in (401, 403):
            raise AuthError("Upstox auth failed; renew UPSTOX_ACCESS_TOKEN")
        resp.raise_for_status()
        d = resp.json()["data"]
        q = next((v for v in d if v.get("instrumentToken") == instrument), {})
        ltp = (q.get("lastPrice") or {}).get("price")
        return {"symbol": symbol.upper(), "ltp": ltp, "source": "upstox"}

    def close(self):
        self._client.close()
