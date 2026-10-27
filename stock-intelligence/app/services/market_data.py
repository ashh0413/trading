"""Market data service: provider selection + caching. Thin layer."""
import time
from pathlib import Path

from app.config import get_config
from app.providers.base import (MarketDataProvider, ProviderError,
                                AuthError, RateLimitError)
from app.providers.mock import MockMarketDataProvider

DEFAULT_SYMBOLS = ("RELIANCE", "TCS", "INFY", "HDFCBANK",
                   "ICICIBANK", "SBIN", "ITC", "LT",
                   "BHARTIARTL", "AXISBANK")


class MarketDataService:
    def __init__(self, root: Path, cache_ttl_seconds: int = 300):
        cfg = get_config()
        self.root = root
        self.ttl = cache_ttl_seconds
        self._cache: dict[str, tuple[float, object]] = {}
        if cfg["provider"] == "UPSTOX":
            from app.providers.upstox import UpstoxProvider
            self.provider: MarketDataProvider = UpstoxProvider(cfg["upstox"])
        else:
            self.provider = MockMarketDataProvider(DEFAULT_SYMBOLS)

    def get_candles(self, symbol: str, period_days: int = 365):
        key = f"candles:{symbol}:{period_days}"
        now = time.monotonic()
        hit = self._cache.get(key)
        if hit and now - hit[0] < self.ttl:
            df = hit[1]
            return df, {"source": self.provider.name, "cached": True,
                       "stale": False}
        df = self.provider.get_candles(symbol, period_days=period_days)
        self._cache[key] = (now, df)
        return df, {"source": self.provider.name, "cached": False,
                    "stale": False}

    def get_quote(self, symbol: str) -> dict:
        return self.provider.get_quote(symbol)

    def status(self) -> dict:
        out = {"provider": self.provider.name, "ok": True}
        if isinstance(self.provider, MockMarketDataProvider):
            out["note"] = "MOCK data — synthetic prices"
        return out
