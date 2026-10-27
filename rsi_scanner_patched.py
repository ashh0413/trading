"""
RSI Scanner - Multi-Timeframe Stock Analyzer
Fetches live data via yfinance and computes RSI + divergences
for all 213 F&O stocks across Monthly, Weekly, Daily, and Hourly timeframes.
"""

import json
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
OVERBOUGHT = 70
OVERSOLD = 30
BEAR_DIV_SCORE = 3   # points for bearish divergence
BULL_DIV_SCORE = 3   # points for bullish divergence

# ─────────────────────────────────────────────
# RSI + DIVERGENCE ENGINE
# ─────────────────────────────────────────────
def calc_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    delta = prices.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("inf"))
    return 100 - (100 / (1 + rs))

def detect_divergence(prices: pd.Series, rsi: pd.Series, lookback: int = 30) -> dict:
    p = prices.tail(lookback).values
    r = rsi.tail(lookback).values
    if len(p) < 10:
        return {"type": "NONE", "description": "Insufficient data"}

    def peaks(arr, is_high):
        pts = []
        for i in range(2, len(arr) - 2):
            if is_high:
                if arr[i] > arr[i-1] and arr[i] > arr[i-2] and arr[i] > arr[i+1] and arr[i] > arr[i+2]:
                    pts.append((i, arr[i]))
            else:
                if arr[i] < arr[i-1] and arr[i] < arr[i-2] and arr[i] < arr[i+1] and arr[i] < arr[i+2]:
                    pts.append((i, arr[i]))
        return pts

    highs  = peaks(p, True)
    lows   = peaks(p, False)
    r_highs = peaks(r, True)
    r_lows  = peaks(r, False)

    result = {"type": "NONE", "description": "No clear divergence"}

    # Bearish: price makes higher high, RSI makes lower high
    if len(highs) >= 2 and len(r_highs) >= 2:
        if highs[-1][1] > highs[-2][1] and r_highs[-1][1] < r_highs[-2][1]:
            result = {"type": "BEARISH", "description": "Regular Bearish Divergence — price higher high, RSI lower high"}
            if len(highs) >= 3 and len(r_highs) >= 3:
                if (highs[-1][1] > highs[-2][1] > highs[-3][1] and
                    r_highs[-1][1] < r_highs[-2][1] < r_highs[-3][1] and
                    r_highs[-1][1] < 60):
                    result = {"type": "BEARISH", "description": "3-DRIVE BEARISH N-DIV — severe bearish reversal signal"}

    # Bullish: price makes lower low, RSI makes higher low
    if len(lows) >= 2 and len(r_lows) >= 2:
        if lows[-1][1] < lows[-2][1] and r_lows[-1][1] > r_lows[-2][1]:
            result = {"type": "BULLISH", "description": "Regular Bullish Divergence — price lower low, RSI higher low"}
            if len(lows) >= 3 and len(r_lows) >= 3:
                if (lows[-1][1] < lows[-2][1] < lows[-3][1] and
                    r_lows[-1][1] > r_lows[-2][1] > r_lows[-3][1] and
                    r_lows[-1][1] > 40):
                    result = {"type": "BULLISH", "description": "3-DRIVE BULLISH P-DIV — severe bullish reversal signal"}

    return result

# ─────────────────────────────────────────────
# FETCH + ANALYZE ONE STOCK
# ─────────────────────────────────────────────
def analyze_stock(symbol: str) -> dict:
    result = {
        "Symbol": symbol, "Error": None,
        "RSI_1HR": None, "RSI_DAY": None, "RSI_WEEK": None, "RSI_MONTH": None,
        "DIV_1HR": None, "DIV_DAY": None, "DIV_WEEK": None, "DIV_MONTH": None,
        "Signal": "NEUTRAL", "Bear_Score": 0, "Bull_Score": 0,
        "CMP": None, "CHANGE_PCT": None, "SECTOR": None
    }

    nse_sym = symbol if symbol.endswith(".NS") else f"{symbol}.NS"
    end = datetime.today()

    intervals = [
        ("1HR",   end - timedelta(days=60),   "1h"),
        ("DAY",   end - timedelta(days=365),  "1d"),
        ("WEEK",  end - timedelta(days=730),  "1wk"),
        ("MONTH", end - timedelta(days=1825), "1mo"),
    ]

    try:
        df_all = yf.download(nse_sym, period="5y", interval="1d", progress=False, auto_adjust=True)
        if df_all.empty:
            raise ValueError("No data returned")
    except Exception as e:
        result["Error"] = str(e)
        return result

    close_all = df_all["Close"].dropna()
    rsi_all   = calc_rsi(close_all)
    result["CMP"] = float(close_all.iloc[-1]) if not close_all.empty else None

    try:
        change = ((close_all.iloc[-1] - close_all.iloc[-2]) / close_all.iloc[-2]) * 100
        result["CHANGE_PCT"] = round(change, 2)
    except Exception:
        pass

    # Resample for different timeframes
    def get_tf(df, interval):
        if interval == "1h":
            return df.resample("1h").last().dropna()
        return df  # already daily

    def resample_rsi(df, rule):
        if rule in ("1h", "1d"):
            return calc_rsi(df["Close"].dropna())
        # For weekly/monthly, resample to those periods
        resampled = df["Close"].dropna().resample(rule).last()
        return calc_rsi(resampled)

    for tf, start, interval in intervals:
        try:
            df_tf = yf.download(nse_sym, start=start, end=end, interval=interval,
                               progress=False, auto_adjust=True)
            if df_tf.empty or len(df_tf) < 20:
                continue

            close_tf = df_tf["Close"].dropna()
            rsi_tf = calc_rsi(close_tf)
            rsi_val = round(float(rsi_tf.dropna().iloc[-1]), 2)

            result[f"RSI_{tf}"] = rsi_val
            div = detect_divergence(close_tf, rsi_tf)
            result[f"DIV_{tf}"] = div["description"]

            if rsi_val:
                if rsi_val < OVERSOLD:
                    result["Bear_Score"] += 1
                    result["Bull_Score"] += 2  # oversold = bounce potential
                elif rsi_val > OVERBOUGHT:
                    result["Bear_Score"] += 2
                if div["type"] == "BEARISH":
                    result["Bear_Score"] += BEAR_DIV_SCORE
                elif div["type"] == "BULLISH":
                    result["Bull_Score"] += BULL_DIV_SCORE

        except Exception:
            pass

    # Overall signal
    if result["Bear_Score"] >= result["Bull_Score"] + 3:
        result["Signal"] = "BEARISH"
    elif result["Bull_Score"] >= result["Bear_Score"] + 3:
        result["Signal"] = "BULLISH"
    else:
        result["Signal"] = "NEUTRAL"

    return result

# ─────────────────────────────────────────────
# MAIN SCANNER
# ─────────────────────────────────────────────
def run_scanner():
    with open(r"D:/MOVED FROM C/Python/venvs/py311/Scripts/stocks_data.json") as f:
        stocks = json.load(f)

    # Attach sector info
    symbol_sector = {s["Symbol"]: str(s.get("SECTOR ","") or "").strip() for s in stocks}
    symbols = list(symbol_sector.keys())

    print(f"RSI SCANNER — {len(symbols)} stocks, 4 timeframes")
    print("=" * 90)

    results = []
    total = len(symbols)

    def safe(sym):
        r = analyze_stock(sym)
        r["SECTOR"] = symbol_sector.get(sym, "")
        return r

    with ThreadPoolExecutor(max_workers=25) as ex:
        futures = {ex.submit(safe, sym): sym for sym in symbols}
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            results.append(r)
            err = " ERR" if r["Error"] else "   "
            print(f"[{i:3d}/{total}]{err} {r['Symbol']:<20} | "
                  f"1HR:{str(r.get('RSI_1HR','') or ''):>6} "
                  f"DAY:{str(r.get('RSI_DAY','') or ''):>6} "
                  f"WEEK:{str(r.get('RSI_WEEK','') or ''):>6} "
                  f"MONTH:{str(r.get('RSI_MONTH','') or ''):>6} | "
                  f"SIG:{r['Signal']:8} B:{r['Bear_Score']} Bu:{r['Bull_Score']}")

    # ── RESULTS ──
    print("\n" + "=" * 90)
    print("SCAN RESULTS")
    print("=" * 90)

    def sort_key(r, keys):
        for k in keys:
            v = r.get(k)
            if v is not None:
                return -v
        return 0

    # --- BEARISH (Monthly + Weekly both bearish) ---
    bear_mw = [r for r in results
                if not r.get("Error")
                and r.get("RSI_MONTH") is not None
                and r.get("RSI_WEEK") is not None
                and r.get("RSI_WEEK") < 45
                and r.get("DIV_MONTH") is not None
                and ("BEARISH" in str(r.get("DIV_MONTH","")) or "BEARISH" in str(r.get("DIV_WEEK","")))]

    print(f"\n🔴 BEARISH (RSI Week < 45 + bearish divergence on M/W): {len(bear_mw)} stocks")
    hdr = f"{'Symbol':<18} {'Sector':<25} {'M_RSI':>6} {'W_RSI':>6} {'D_RSI':>6} {'1HR':>6}  {'M_Div':<38} {'W_Div':<38}  B Bu"
    print(hdr)
    print("-" * 170)
    for r in sorted(bear_mw, key=lambda x: x.get("RSI_WEEK", 99)):
        m = str(r.get("RSI_MONTH") or "")
        w = str(r.get("RSI_WEEK") or "")
        d = str(r.get("RSI_DAY") or "")
        h = str(r.get("RSI_1HR") or "")
        md = str(r.get("DIV_MONTH") or "")[:37]
        wd = str(r.get("DIV_WEEK") or "")[:37]
        print(f"{r['Symbol']:<18} {r['SECTOR']:<25} {m:>6} {w:>6} {d:>6} {h:>6}  {md:<38} {wd:<38} {r['Bear_Score']} {r['Bull_Score']}")

    # --- BULLISH (RSI Week > 55 + bullish divergence) ---
    bull_mw = [r for r in results
                if not r.get("Error")
                and r.get("RSI_MONTH") is not None
                and r.get("RSI_WEEK") is not None
                and r.get("RSI_WEEK") > 55
                and r.get("DIV_MONTH") is not None
                and ("BULLISH" in str(r.get("DIV_MONTH","")) or "BULLISH" in str(r.get("DIV_WEEK","")))]

    print(f"\n🟢 BULLISH (RSI Week > 55 + bullish divergence on M/W): {len(bull_mw)} stocks")
    print(hdr)
    print("-" * 170)
    for r in sorted(bull_mw, key=lambda x: -x.get("RSI_WEEK", 0)):
        m = str(r.get("RSI_MONTH") or "")
        w = str(r.get("RSI_WEEK") or "")
        d = str(r.get("RSI_DAY") or "")
        h = str(r.get("RSI_1HR") or "")
        md = str(r.get("DIV_MONTH") or "")[:37]
        wd = str(r.get("DIV_WEEK") or "")[:37]
        print(f"{r['Symbol']:<18} {r['SECTOR']:<25} {m:>6} {w:>6} {d:>6} {h:>6}  {md:<38} {wd:<38} {r['Bear_Score']} {r['Bull_Score']}")

    # --- OVERSOLD WEEKLY (potential bounce) ---
    oversold = [r for r in results
                if not r.get("Error") and r.get("RSI_WEEK") is not None
                and r.get("RSI_WEEK") < OVERSOLD]
    print(f"\n🟡 OVERSOLD Weekly (RSI < 30) — {len(oversold)} stocks (watch for bounce):")
    for r in sorted(oversold, key=lambda x: x.get("RSI_WEEK", 99)):
        print(f"  {r['Symbol']:<18} {r['SECTOR']:<25} WEEK_RSI: {r['RSI_WEEK']}  | {r.get('DIV_WEEK','')}")

    # --- SUMMARY ---
    errs = sum(1 for r in results if r.get("Error"))
    print(f"\n📊 SUMMARY:")
    print(f"   Total scanned  : {len(results)}")
    print(f"   Fetch errors   : {errs}")
    print(f"   Bearish (M+W) : {len(bear_mw)}")
    print(f"   Bullish (M+W)  : {len(bull_mw)}")
    print(f"   Oversold (W)  : {len(oversold)}")
    print(f"   Neutral        : {sum(1 for r in results if r['Signal']=='NEUTRAL' and not r.get('Error'))}")

    # Save
    with open(r"D:/MOVED FROM C/Python/venvs/py311/Scripts/scanner_results.json", "w") as f:
        json.dump(results, f, default=str)
    print(f"\n✅ Full results → scanner_results.json")

    return results

if __name__ == "__main__":
    run_scanner()
