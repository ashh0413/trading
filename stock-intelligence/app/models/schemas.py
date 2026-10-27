"""Pydantic schemas for API responses."""
from pydantic import BaseModel, Field


class WatchlistItem(BaseModel):
    symbol: str


class HealthResponse(BaseModel):
    ok: bool
    provider: str
    provider_status: dict


class ScannerResult(BaseModel):
    symbol: str
    status: str
    score: int
    max_score: int
    last_close: float | None = None
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_hist: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    relative_volume: float | None = None
    atr_14: float | None = None
    data_timestamp: str | None = None
    source: str = "mock"
    checks: list[dict] = Field(default_factory=list)


class ConfigResponse(BaseModel):
    provider: str
    upstox: dict
