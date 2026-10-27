import sys, pathlib
import json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import os
os.environ["PROVIDER"] = "MOCK"
os.environ.pop("UPSTOX_ACCESS_TOKEN", None)

from fastapi.testclient import TestClient
from app.main import create_app


def client():
    app = create_app()
    app.state.watchlist.path.write_text(json.dumps(["RELIANCE", "TCS"]))
    return TestClient(app)


def test_health_and_config_hide_secrets():
    c = client()
    r = c.get("/health")
    assert r.status_code == 200
    cfg = c.get("/config").json()
    blob = json.dumps(cfg)
    assert "API_KEY" not in blob.upper() or "api_key_configured" in blob
    assert "access_token_configured" in blob
    assert cfg["provider"] == "MOCK"

def test_watchlist_crud():
    c = client()
    assert "TCS" in c.get("/watchlist").json()
    r = c.post("/watchlist", json={"symbol": "INFY"})
    assert r.status_code == 201
    assert "INFY" in c.get("/watchlist").json()
    # duplicate -> 400
    assert c.post("/watchlist", json={"symbol": "INFY"}).status_code == 400
    # remove
    assert c.delete("/watchlist/TCS").status_code == 200
    assert c.delete("/watchlist/NOPE").status_code == 404

def test_market_data_and_indicators_endpoints():
    c = client()
    r = c.get("/market-data/reliance")
    assert r.status_code == 200
    assert r.json()["meta"]["source"] == "mock"
    i = c.get("/indicators/RELIANCE").json()
    assert "rsi_14" in i and "macd" in i

def test_scanner_returns_ranked_results():
    c = client()
    res = c.get("/scanner").json()
    assert len(res) >= 2
    scores = [r["score"] for r in res]
    assert scores == sorted(scores, reverse=True)
    one = c.get("/scanner/RELIANCE").json()
    assert one["symbol"] == "RELIANCE"
    assert "checks" in one
