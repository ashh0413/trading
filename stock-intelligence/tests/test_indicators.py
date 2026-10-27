import pandas as pd
import numpy as np
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.services.indicators import (rsi_last, macd_last, sma_last, ema_last,
                                     atr_last, pct_change_last,
                                     relative_volume_last, clean_candles,
                                     compute_all)


def mk_candles(n=100, trend=0.001, seed=7):
    rng = np.random.default_rng(seed)
    close = 100 * np.exp(np.cumsum(rng.normal(trend, 0.01, n)))
    high = close * 1.01
    low = close * 0.99
    open_ = np.concatenate([[close[0]], close[:-1]])
    vol = rng.integers(1000, 5000, n)
    return pd.DataFrame({
        "date": pd.bdate_range("2024-01-01", periods=n),
        "open": open_, "high": high, "low": low,
        "close": close, "volume": vol,
    })


def test_rsi_bounded_and_known_case():
    close = pd.Series([10.0] * 20 + [9.0] * 20)  # all losses -> RSI ~0
    r = rsi_last(close)
    assert r is not None and 0 <= r < 5

def test_rsi_strong_uptrend_high():
    close = pd.Series(np.linspace(10, 50, 40))  # all gains -> RSI ~100
    r = rsi_last(close)
    assert r is not None and r > 95

def test_rsi_insufficient_data_returns_none():
    assert rsi_last(pd.Series([1.0, 2.0, 3.0])) is None

def test_macd_needs_slow_plus_signal():
    close = pd.Series(np.linspace(1, 40, 40))
    m, s, h = macd_last(close)
    assert m is not None and s is not None and h is not None
    assert macd_last(pd.Series([1.0] * 10)) == (None, None, None)

def test_sma_insufficient_returns_none():
    close = pd.Series(np.linspace(1, 20, 30))
    assert sma_last(close, 50) is None
    assert sma_last(close, 20) is not None

def test_ema_insufficient_returns_none():
    assert ema_last(pd.Series([1.0]), 9) is None

def test_atr_matches_manual_value():
    df = pd.DataFrame({
        "date": pd.bdate_range("2024-01-01", periods=20),
        "open": 10.0, "high": 11.0, "low": 9.0, "close": 10.0,
    })
    # TR constant = 2.0 every bar -> Wilder ATR -> 2.0
    assert atr_last(df) == 2.0
    assert atr_last(df.head(5)) is None  # needs period+2

def test_pct_change_and_relative_volume():
    df = mk_candles()
    df.iloc[-1, df.columns.get_loc("close")] = df["close"].iloc[-2] * 1.05
    pc = pct_change_last(df["close"])
    assert pc is not None and abs(pc - 5.0) < 0.1
    df["volume"] = 1000.0
    df.iloc[-1, df.columns.get_loc("volume")] = 3000.0
    rv = relative_volume_last(df)
    assert rv is not None and rv > 1.0  # last vs 20-bar avg

def test_relative_volume_zero_base():
    df = mk_candles()
    df["volume"] = 0.0
    assert relative_volume_last(df) is None

def test_clean_candles_dedupes_and_sorts():
    df = mk_candles(50)
    dup = pd.concat([df, df.tail(5), df.iloc[::1].iloc[::-1]], ignore_index=True)
    out = clean_candles(dup)
    assert len(out) == 50
    assert (out["date"].diff().dropna() > pd.Timedelta(0)).all()

def test_compute_all_ok_status():
    out = compute_all(mk_candles(120))
    assert out["status"] == "OK"
    assert out["last_close"] is not None
    assert out["sma_200"] is None  # only 120 rows: SMA200 unavailable
    assert out["sma_50"] is not None

def test_compute_all_insufficient():
    out = compute_all(mk_candles(10))
    assert out["status"] == "INSUFFICIENT_DATA"
