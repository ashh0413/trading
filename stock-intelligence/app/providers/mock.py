"""Mock provider: deterministic synthetic candles. For dev/tests only."""
import zlib

import numpy as np
import pandas as pd

from .base import MarketDataProvider, ProviderError

# Deterministic per-symbol seed: same symbol, same series. Bounded random-walk.
SYNTHETIC_NOTES = "MOCK data — synthetic prices, not real market data"


class MockMarketDataProvider(MarketDataProvider):
    name = "mock"

    def __init__(self, symbols: tuple = ("RELIANCE", "TCS", "INFY", "HDFCBANK",
                                         "ICICIBANK", "SBIN", "ITC", "LT",
                                         "BHARTIARTL", "AXISBANK")):
        self.symbols = set(s.upper() for s in symbols)

    def _resolve(self, symbol: str) -> str:
        s = symbol.upper()
        if s not in self.symbols:
            raise ProviderError(f"Symbol {symbol!r} not in mock universe")
        return s

    def get_candles(self, symbol: str, period_days: int = 365) -> pd.DataFrame:
        sym = self._resolve(symbol)
        seed = zlib.crc32(sym.encode()) % (2**32)
        rng = np.random.default_rng(seed)
        n = min(period_days, 365)
        days = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=n)
        rets = rng.normal(0.0005, 0.018, size=n)
        close = 500 * np.exp(np.cumsum(rets))
        open_ = np.concatenate([[close[0]], close[:-1]])
        high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.01, n))
        low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.01, n))
        volume = rng.integers(100_000, 500_000, n)
        return pd.DataFrame({
            "date": days, "open": open_, "high": high,
            "low": low, "close": close, "volume": volume,
        })

    def get_quote(self, symbol: str) -> dict:
        df = self.get_candles(symbol, period_days=2)
        last = df.iloc[-1]
        return {"symbol": symbol.upper(), "ltp": float(last["close"]),
                "source": "mock", "note": SYNTHETIC_NOTES}
