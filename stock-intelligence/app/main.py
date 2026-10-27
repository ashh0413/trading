"""FastAPI app. create_app() factory; thin routers, logic in services."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import get_config, public_config, ConfigError
from app.models.schemas import (ConfigResponse, HealthResponse,
                                ScannerResult, WatchlistItem)
from app.providers.base import AuthError, ProviderError
from app.services.market_data import MarketDataService
from app.services.scanner import scan_all, evaluate_symbol
from app.services.watchlist import Watchlist


class AddWatchlist(BaseModel):
    symbol: str


def create_app() -> FastAPI:
    try:
        cfg = get_config()
    except ConfigError as e:
        cfg = {"provider": "MOCK", "upstox": {}, "root": Path(".")}
        _startup_error = str(e)
    else:
        _startup_error = None

    root = Path(cfg["root"])
    service = MarketDataService(root)
    wl = Watchlist(root / "watchlist.json")

    app = FastAPI(title="Stock Intelligence", version="0.1")
    app.state.service = service
    app.state.watchlist = wl
    app.state.config = cfg
    app.add_middleware(
        CORSMiddleware, allow_origins=["http://localhost:8501",
                                       "http://127.0.0.1:8501"],
        allow_methods=["*"], allow_headers=["*"])

    @app.get("/health", response_model=HealthResponse)
    def health():
        st = service.status()
        if _startup_error:
            st["warning"] = _startup_error
        return {"ok": True, "provider": cfg["provider"],
                "provider_status": st}

    @app.get("/watchlist")
    def watchlist_list():
        return wl.list()

    @app.post("/watchlist", response_model=WatchlistItem, status_code=201)
    def watchlist_add(item: AddWatchlist):
        try:
            wl.add(item.symbol)
        except ValueError as e:
            raise HTTPException(400, str(e))
        return {"symbol": item.symbol.upper()}

    @app.delete("/watchlist/{symbol}")
    def watchlist_remove(symbol: str):
        try:
            wl.remove(symbol)
        except KeyError as e:
            raise HTTPException(404, str(e))
        return {"removed": symbol.upper()}

    @app.get("/market-data/{symbol}")
    def market_data(symbol: str, days: int = 365):
        try:
            df, meta = service.get_candles(symbol, period_days=days)
        except ProviderError as e:
            raise HTTPException(502, str(e))
        return {"symbol": symbol.upper(), "meta": meta,
                "rows": df.to_dict("list") if df is not None else []}

    @app.get("/indicators/{symbol}")
    def indicators(symbol: str, days: int = 365):
        from app.services.indicators import compute_all
        try:
            df, meta = service.get_candles(symbol, period_days=days)
        except ProviderError as e:
            raise HTTPException(502, str(e))
        out = compute_all(df)
        out["source"] = meta["source"]
        out["cached"] = meta["cached"]
        return out

    @app.get("/scanner", response_model=list[ScannerResult])
    def scanner_scan(days: int = 365):
        try:
            return scan_all(service.provider, wl.list(), period_days=days)
        except AuthError as e:
            raise HTTPException(401, str(e))

    @app.get("/scanner/{symbol}")
    def scanner_one(symbol: str, days: int = 365):
        try:
            df, _ = service.get_candles(symbol, period_days=days)
        except ProviderError as e:
            raise HTTPException(502, str(e))
        return evaluate_symbol(symbol, df, source=service.provider.name)

    @app.get("/config", response_model=ConfigResponse)
    def config():
        return public_config(cfg)

    return app


app = create_app()
