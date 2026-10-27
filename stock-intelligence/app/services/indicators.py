"""Technical indicators. All take chronological OHLCV DataFrames, return
last-value floats or None when data is insufficient. No look-ahead:
every value uses only data up to the last row.

Methods (documented per spec):
- RSI(14): Wilder's smoothing — ewm(alpha=1/14) on gain/loss means.
- MACD(12,26,9): EMA12 - EMA26, signal = EMA9 of MACD line.
- SMA(n): rolling mean. EMA(n): ewm(span=n).
- ATR(14): Wilder-smoothed true range.
- pct_change: last close vs previous close.
- relative_volume: last volume / mean(last 20 volumes).
"""
import numpy as np
import pandas as pd


def clean_candles(df: pd.DataFrame) -> pd.DataFrame:
    """Validate provider output: chronological, deduped, no NaN OHLC, volume >= 0."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out = out.sort_values("date").drop_duplicates("date")
    for col in ("open", "high", "low", "close"):
        out[col] = pd.to_numeric(out[col], errors="coerce")
    out["volume"] = pd.to_numeric(out.get("volume"), errors="coerce").fillna(0)
    out = out.dropna(subset=["open", "high", "low", "close"])
    if out.empty:
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
    return out.reset_index(drop=True)


def rsi(close: pd.Series, period: int = 14):
    """Wilder RSI. Needs period+2 closes. Returns series aligned to input."""
    if close is None or len(close) < period + 2:
        return pd.Series(dtype=float)
    delta = close.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    with np.errstate(divide="ignore"):
        rs = avg_gain / avg_loss
        out = 100 - (100 / (1 + rs))
    out[avg_loss == 0] = 100.0
    out.iloc[0] = np.nan
    return out


def rsi_last(close: pd.Series, period: int = 14):
    s = rsi(close, period)
    if s.empty:
        return None
    v = s.iloc[-1]
    return round(float(v), 2) if pd.notna(v) else None


def macd_last(close: pd.Series, fast=12, slow=26, signal=9):
    """Returns (macd, signal_line, histogram) or (None, None, None)."""
    need = slow + signal + 1
    if close is None or len(close) < need:
        return None, None, None
    ema_f = close.ewm(span=fast, adjust=False).mean()
    ema_s = close.ewm(span=slow, adjust=False).mean()
    line = ema_f - ema_s
    sig = line.ewm(span=signal, adjust=False).mean()
    return (round(float(line.iloc[-1]), 4), round(float(sig.iloc[-1]), 4),
            round(float(line.iloc[-1] - sig.iloc[-1]), 4))


def sma_last(close: pd.Series, n: int):
    if close is None or len(close) < n:
        return None
    return round(float(close.tail(n).mean()), 2)


def ema_last(close: pd.Series, n: int):
    if close is None or len(close) < n:
        return None
    return round(float(close.ewm(span=n, adjust=False).mean().iloc[-1]), 2)


def atr_last(df: pd.DataFrame, period: int = 14):
    """Wilder ATR. Needs period+2 rows."""
    if df is None or len(df) < period + 2:
        return None
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    wilder = tr.ewm(alpha=1 / period, adjust=False).mean()
    v = wilder.iloc[-1]
    return round(float(v), 2) if pd.notna(v) else None


def pct_change_last(close: pd.Series):
    if close is None or len(close) < 2:
        return None
    prev = float(close.iloc[-2])
    if prev == 0:
        return None
    return round((float(close.iloc[-1]) / prev - 1) * 100, 2)


def relative_volume_last(df: pd.DataFrame, avg_window: int = 20):
    if df is None or len(df) < avg_window + 1:
        return None
    vol = df["volume"]
    base = float(vol.iloc[-(avg_window + 1):-1].mean())
    if base == 0:
        return None
    return round(float(vol.iloc[-1]) / base, 2)


def compute_all(df: pd.DataFrame) -> dict:
    """One call for the scanner. Data-quality status included."""
    df = clean_candles(df)
    close = df["close"]
    n = len(df)
    if n < 2:
        return {"status": "INSUFFICIENT_DATA", "rows": n}

    out = {
        "status": "OK" if n >= 60 else "INSUFFICIENT_DATA",
        "rows": n,
        "last_close": round(float(close.iloc[-1]), 2) if n else None,
        "pct_change": pct_change_last(close),
        "rsi_14": rsi_last(close),
        "sma_20": sma_last(close, 20),
        "sma_50": sma_last(close, 50),
        "sma_200": sma_last(close, 200),
        "ema_9": ema_last(close, 9),
        "ema_21": ema_last(close, 21),
        "ema_50": ema_last(close, 50),
        "atr_14": atr_last(df),
        "relative_volume": relative_volume_last(df),
        "data_timestamp": str(df["date"].iloc[-1]) if n else None,
    }
    m, s, h = macd_last(close)
    out.update({"macd": m, "macd_signal": s, "macd_hist": h})
    if n < 2:
        out["status"] = "INSUFFICIENT_DATA"
    return out
