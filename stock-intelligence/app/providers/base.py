"""Provider interface. Providers return chronological OHLCV DataFrames."""
from abc import ABC, abstractmethod

import pandas as pd


class ProviderError(RuntimeError):
    pass


class AuthError(ProviderError):
    """Token missing/expired. Do not retry; user must renew."""


class RateLimitError(ProviderError):
    """Back off, then retry with limit."""


class MarketDataProvider(ABC):
    name: str = "base"

    @abstractmethod
    def get_candles(self, symbol: str, period_days: int = 365) -> pd.DataFrame:
        """Daily OHLCV, ascending by date. Columns: open high low close volume."""
        ...

    @abstractmethod
    def get_quote(self, symbol: str) -> dict:
        """Latest LTP/price info."""
        ...
