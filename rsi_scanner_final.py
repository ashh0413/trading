"""
RSI Scanner - Multi-Timeframe Stock Analyzer
Fast threaded scanner with incremental saves and UTF-8 safe output.
"""

import json
import sys
import pandas as pd
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.stdout.reconfigure(encoding="utf-8")

DATA_PATH = r"D:/MOVED FROM C/Python/venvs/py311/Scripts/stocks_data.json"
SAVE_PATH = r"D:/MOVED FROM C/Python/venvs/py311/Scripts/scanner_results.json"

# ── RSI ──────────────────────────────────────────────────────────────────────
def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain  = delta.clip(lower=0).rolling(period).mean()
    loss  = (-delta.clip(upper=0)).rolling(period).mean()
    rs    = gain / loss.replace(0, float("inf"))
    return 100 - (100 / (1 + rs))

def detect_div(prices: pd.Series, rsi: pd.Series, lookback: int = 30) -> dict:
    p = prices.tail(lookback).values
    r = rsi.tail(lookback).values
    if len(p) < 10:
        return {"type": "NONE"}

    def peaks(arr, is_high):
        pts = []
        for i in range(2, len(arr) - 2):
            if is_high:
                if arr[i] > arr[i-1] > arr[i-2] and arr[i] > arr[i+1] > arr[i+2]:
                    pts.append(arr[i])
            else:
                if arr[i] < arr[i-1] < arr[i-2] and arr[i] < arr[i+1] < arr[i+2]:
                    pts.append(arr[i])
        return pts

    p_h = peaks(p, True);  p_l = peaks(p, False)
    r_h = peaks(r, True);  r_l = peaks(r, False)

    if len(p_h) >= 2 and len(r_h) >= 2:
        if p_h[-1] > p_h[0] and r_h[-1] < r_h[0]:
            return {"type": "BEARISH", "description": "3-DRIVE N-DIV"}
    if len(p_l) >= 2 and len(r_l) >= 2:
        if p_l[-1] < p_l[0] and r_l[-1] > r_l[0]:
            return {"type": "BULLISH", "description": "3-DRIVE POS-DIV"}
    return {"type": "NONE"}

# ── Fetch one stock ──────────────��─────────────────────────────────────────────
def fetch_stock(symbol: str, sector: str) -> dict:
    ticker = f"{symbol}.NS"
    result = {"Symbol": symbol, "SECTOR": sector}
    try:
        df = yf.download(ticker, period="2y", interval="1d", auto_adjust=True, progress=False)
        if df.empty:
            result["Error"] = "No data"
            return result
        close = df["Close"].squeeze()
        rsi_d = calc_rsi(close, 14)

        # Weekly
        df_w = yf.download(ticker, period="3y", interval="1wk", auto_adjust=True, progress=False)
        rsi_w = calc_rsi(df_w["Close"].squeeze(), 14) if not df_w.empty else pd.Series()

        # Monthly
        df_m = yf.download(ticker, period="5y", interval="1mo", auto_adjust=True, progress=False)
        rsi_m = calc_rsi(df_m["Close"].squeeze(), 14) if not df_m.empty else pd.Series()

        # Hourly
        df_h = yf.download(ticker, period="3d", interval="60m", auto_adjust=True, progress=False)
        rsi_h = calc_rsi(df_h["Close"].squeeze(), 14) if not df_h.empty else pd.Series()

        def last(s):
            return round(float(s.dropna().iloc[-1]), 2) if not s.dropna().empty else None

        result["RSI_1HR"]  = last(rsi_h)
        result["RSI_DAY"]   = last(rsi_d)
        result["RSI_WEEK"]  = last(rsi_w)
        result["RSI_MONTH"] = last(rsi_m)
        result["CMP"]       = last(close)

        # Divergences
        for label, series in [("1HR", rsi_h), ("DAY", rsi_d), ("WEEK", rsi_w), ("MONTH", rsi_m)]:
            if not series.dropna().empty:
                div = detect_div(close, series)
                result[f"DIV_{label}"] = div["type"]

        # Bear/Bull score
        bear = bear_score(result)
        bull = bull_score(result)
        result["Bear_Score"] = bear
        result["Bull_Score"] = bull
        result["Signal"]     = signal(bear, bull)
    except Exception as e:
        result["Error"] = str(e)
    return result

def bear_score(r) -> int:
    s = 0
    if r.get("RSI_WEEK", 99) < 40: s += 2
    elif r.get("RSI_WEEK", 99) < 50: s += 1
    if r.get("RSI_DAY", 99) < 35: s += 1
    for tf in ("1HR","DAY","WEEK","MONTH"):
        if r.get(f"DIV_{tf}") == "BEARISH": s += 2
    return s

def bull_score(r) -> int:
    s = 0
    if r.get("RSI_WEEK", 0) > 60: s += 2
    elif r.get("RSI_WEEK", 0) > 50: s += 1
    if r.get("RSI_DAY", 0) > 65: s += 1
    for tf in ("1HR","DAY","WEEK","MONTH"):
        if r.get(f"DIV_{tf}") == "BULLISH": s += 2
    return s

def signal(bear: int, bull: int) -> str:
    if bear >= 7: return "STRONG BEARISH"
    if bull >= 7: return "STRONG BULLISH"
    if bear > bull + 3: return "BEARISH"
    if bull > bear + 3: return "BULLISH"
    return "NEUTRAL"

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    with open(DATA_PATH) as f:
        raw = json.load(f)

    stocks = [(s["Symbol"], s.get("SECTOR ", "") or "") for s in raw]
    results = []
    errors  = []
    n = len(stocks)

    def safe(name):
        return name  # keep original
    skip_syms = {"ATHERENERG"}  # known bad symbol

    def worker(args):
        sym, sec = args
        if sym in skip_syms:
            return {"Symbol": sym, "SECTOR": sec, "RSI_1HR": None,
                    "RSI_DAY": None, "RSI_WEEK": None, "RSI_MONTH": None,
                    "Bear_Score": 0, "Bull_Score": 0, "Signal": "NEUTRAL"}
        return fetch_stock(sym, sec)

    print(f"Scanning {n} stocks across 4 timeframes...")
    done = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(worker, s): s for s in stocks}
        for fut in as_completed(futures):
            done += 1
            r = fut.result()
            results.append(r)
            if r.get("Error"):
                errors.append(r)
            if done % 20 == 0 or done == n:
                print(f"  {done}/{n} done...")
            # Incremental save every 25 stocks
            if done % 25 == 0:
                with open(SAVE_PATH, "w") as f:
                    json.dump(results, f, default=str)

    # Final save
    with open(SAVE_PATH, "w") as f:
        json.dump(results, f, default=str)

    good = [r for r in results if not r.get("Error")]
    errs = [r for r in results if r.get("Error")]

    print(f"\n{'='*80}")
    print(f"SCAN COMPLETE  |  {len(good)} success  |  {len(errs)} errors")
    print(f"{'='*80}\n")

    def prt(lbl, lst, rev=False):
        print(f"[{lbl}] {len(lst)} stocks")
        for r in sorted(lst, key=lambda x: x.get("RSI_WEEK", 50), reverse=rev)[:15]:
            print(f"  {r['Symbol']:<18} | W:{str(r.get('RSI_WEEK','')):>6} "
                  f"| M:{str(r.get('RSI_MONTH','')):>6} "
                  f"| D:{str(r.get('RSI_DAY','')):>6} "
                  f"| SIG:{r.get('Signal',''):<16} B:{r.get('Bear_Score',0):2} Bu:{r.get('Bull_Score',0):2}")

    prt("BEARISH WEEK", [r for r in good if r.get("RSI_WEEK") and r["RSI_WEEK"] < 45])
    print()
    prt("BULLISH WEEK", [r for r in good if r.get("RSI_WEEK") and r["RSI_WEEK"] > 55], rev=True)
    print()
    prt("OVERSOLD (<30)", [r for r in good if r.get("RSI_WEEK") and r["RSI_WEEK"] < 30])
    print()
    prt("OVERBOUGHT (>70)", [r for r in good if r.get("RSI_WEEK") and r["RSI_WEEK"] > 70], rev=True)
    print()

    print("[STRONG BEARISH] stocks (Bear Score >= 7):")
    for r in sorted(good, key=lambda x: -x.get("Bear_Score", 0)):
        if r.get("Bear_Score", 0) >= 7:
            print(f"  {r['Symbol']:<18} W:{r.get('RSI_WEEK')} B:{r.get('Bear_Score')} {r.get('Signal')}")

    print(f"\n[ERRORS] ({len(errors)} stocks):")
    for r in errors:
        print(f"  {r['Symbol']}: {r.get('Error')}")

    print(f"\nResults saved: {SAVE_PATH}")

if __name__ == "__main__":
    main()
