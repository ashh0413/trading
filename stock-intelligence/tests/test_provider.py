import sys, pathlib
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.providers.mock import MockMarketDataProvider
from app.providers.base import ProviderError


def test_mock_candles_chronological_and_deduped():
    p = MockMarketDataProvider()
    df = p.get_candles("RELIANCE")
    assert len(df) == 365
    assert (df["date"].diff().dropna() > pd.Timedelta(0)).all()
    assert df[["open", "high", "low", "close"]].notna().all().all()

def test_mock_deterministic():
    p = MockMarketDataProvider()
    a, b = p.get_candles("TCS"), p.get_candles("TCS")
    pd.testing.assert_frame_equal(a, b)

def test_mock_unknown_symbol_raises():
    p = MockMarketDataProvider()
    try:
        p.get_candles("NOPE")
        assert False
    except ProviderError as e:
        assert "not in mock universe" in str(e)

def test_mock_quote_labeled_synthetically():
    p = MockMarketDataProvider()
    q = p.get_quote("ITC")
    assert q["source"] == "mock"
    assert "synthetic" in q["note"].lower()
    assert q["ltp"] is not None
