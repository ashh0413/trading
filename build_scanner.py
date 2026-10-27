"""Build script — writes all scanner_v2 system files"""
import os

BASE = r"D:\MOVED FROM C\Python\venvs\py311\Scripts"

def w(name, content):
    path = os.path.join(BASE, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path}  ({len(content)} bytes)")

# ─────────────────────────────────────────────────────────────────────────────
# 1. scanner_v2.py
# ─────────────────────���───────────────────────────────────────────────────────
scanner_v2 = '''"""Stock Scanner v2 — Multi-indicator data fetcher (RSI/MACD/Volume/SMA)"""
import yfinance as yf
import pandas as pd
import numpy as np
import json, time
from datetime import datetime

NIFTY_213 = [
    "RELIANCE","TCS","HDFCBANK","ICICIBANK","INFY","HINDUNILVR","ITC","KOTAKBANK","LT",
    "SBILIFE","AXISBANK","BHARTIARTL","ASIANPAINT","MARUTI","SUNPHARMA","ULTRACEMCO",
    "NESTLEIND","LARSEN","POWERGRID","M&M","BAJFINANCE","TITAN","BAJAJFINSV","NTPC",
    "ONGC","COALINDIA","HCLTECH","WIPRO","TECHM","ADANIPORTS","JSWSTEEL","UPL","ADANIENT",
    "CIPLA","DIVISLAB","GRASIM","HDFCLIFE","IOC","BRITANNIA","DRREDDY","EICHERMOT",
    "HEROMOTOCO","HINDZINC","ICICIGI","INDUSINDBK","JUBLFOOD","SBICARD","SHREECEM",
    "SIEMENS","VEDL","BAJAJ-AUTO","BANKBARODA","BEL","CANBK","CHAMBLFERT","COROMANDEL",
    "CROMPTON","DABUR","EXIDEIND","FEDERALBNK","GAIL","GODREJCP","GODREJPROP","HAVELLS",
    "IBULHSGFIN","IDEA","IGL","INDUSTOWER","LUPIN","M&MFIN","MANAPPURAM","MARICO","NMDC",
    "PEL","PFC","PGHH","PNB","POLYCAB","RBLBANK","RECLIMIT","SRF","SUNTV","TATACOMM",
    "TATACONSUM","TATASTEEL","TORNTPOWER","TVSMOTOR","AMBUJACEM","AUROPHARMA","BALRAMCHIN",
    "BANDHANBNK","BANKBE","BERGEPAINT","BIOCON","BOSCHLTD","BPCL","BSOFT","CANFINHOME",
    "CASTROLIND","CEATLTD","CESC","CHOLAHLDNG","COLPAL","CONCOR","CUMMINSIND","DEEPAKNTR",
    "DEVYANI","DLF","DMART","ESCORTS","FORTIS","FRETAIL","GLENMARK","GMRINFRA","GNFC",
    "GODREJIND","GRANULES","GSPL","GUJGASLTD","HINDPETRO","HONAUT","IDBI","IDFCFIRSTB",
    "INDIAMART","IRCTC","JINDALSTEL","KAJARIACER","KEC","KEI","LINDEINDIA","LUXIND",
    "MAHINDCIE","MAHLOG","MASTEK","METROBRAND","MGL","MRF","MUTHOOTFIN","NATIONALUM",
    "NAUKRI","NAVINFLUOR","NESTLE","NMDC","OBEROIREALTY","PAGEIND","PERSISTENT","PETRONET",
    "PIIND","PRESTIGE","RELAXO","SAIL","SANOFI","SCHAEFFLER","SCHNEIDER","SHRIRAMFIN",
    "SOLARINDUS","SPARC","STAR","SUDARSCHEM","SUMICHEM","SUPERHOUSE","SUZLON","TANLA",
    "TATAELXSI","TATAINVEST","TECHNO","THYROCARE","TIMKEN","TORNTPHARM","TRENT","TTKPRESTIG",
    "Tvs","UBL","ULTRAMARINE","UNIONBANK","UPL","VAIBHAVGLOBAL","VAKRANGEE","VARROCEN",
    "VINATIORGA","WELCORP","WHIRLPOOL","WOCKPHARMA","ZEEL","ZYDUSLIFE",
]

SECTORS = {
    "RELIANCE":"Oil & Gas","TCS":"IT","HDFCBANK":"Banks","ICICIBANK":"Banks","INFY":"IT",
    "HINDUNILVR":"FMCG","ITC":"FMCG","KOTAKBANK":"Banks","LT":"Capital Goods","SBILIFE":"Insurance",
    "AXISBANK":"Banks","BHARTIARTL":"Telecom","ASIANPAINT":"Chemicals","MARUTI":"Auto",
    "SUNPHARMA":"Pharma","ULTRACEMCO":"Cement","NESTLEIND":"FMCG","LARSEN":"Capital Goods",
    "POWERGRID":"Power","M&M":"Auto","BAJFINANCE":"Finance","TITAN":"Consumer Goods",
    "BAJAJFINSV":"Finance","NTPC":"Power","ONGC":"Oil & Gas","COALINDIA":"Metals & Minerals",
    "HCLTECH":"IT","WIPRO":"IT","TECHM":"IT","ADANIPORTS":"Infrastructure","JSWSTEEL":"Steel",
    "UPL":"Chemicals","ADANIENT":"Infrastructure","CIPLA":"Pharma","DIVISLAB":"Pharma",
    "GRASIM":"Cement","HDFCLIFE":"Insurance","IOC":"Oil & Gas","BRITANNIA":"FMCG",
    "DRREDDY":"Pharma","EICHERMOT":"Auto","HEROMOTOCO":"Auto","HINDZINC":"Metals & Minerals",
    "ICICIGI":"Insurance","INDUSINDBK":"Banks","JUBLFOOD":"FMCG","SBICARD":"Finance",
    "SHREECEM":"Cement","SIEMENS":"Capital Goods","VEDL":"Metals & Minerals","BAJAJ-AUTO":"Auto",
}

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0).rolling(period).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(period).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def calc_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = calc_ema(series, fast)
    ema_slow = calc_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calc_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calc_sma(series, period):
    return series.rolling(period).mean()

def detect_divergence(price_series, indicator_series, lookback=20):
    """Detect bullish/bearish divergence over lookback period"""
    if len(price_series) < lookback or len(indicator_series) < lookback:
        return None
    price_slice = price_series.iloc[-lookback:]
    ind_slice = indicator_series.iloc[-lookback:]
    ph = price_slice.idxmax()
    pl = price_slice.idxmin()
    ih = ind_slice.idxmax()
    il = ind_slice.idxmin()
    p_last = price_series.iloc[-1]
    i_last = indicator_series.iloc[-1]
    if ph == price_slice.index[-1] and ih != ind_slice.index[-1]:
        if ind_slice[ih] > i_last:
            return "bearish"
    if pl == price_slice.index[-1] and il != ind_slice.index[-1]:
        if ind_slice[il] < i_last:
            return "bullish"
    return None

def fetch_data(ticker, timeframe):
    """Fetch data for a given timeframe and return OHLCV DataFrame"""
    params = {
        "1HR":  {"interval":"60m","period":"5d"},
        "1D":   {"interval":"1d","period":"2y"},
        "1WK":  {"interval":"1wk","period":"3y"},
        "1MO":  {"interval":"1mo","period":"5y"},
    }
    p = params[timeframe]
    try:
        df = yf.download(ticker + ".NS", period=p["period"],
                         interval=p["interval"], auto_adjust=True, progress=False)
        if df.empty:
            return None
        df = df.dropna()
        return df
    except Exception:
        return None

def analyze_timeframe(df, timeframe):
    if df is None or len(df) < 30:
        return None
    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]
    results = {}
    results["rsi"] = calc_rsi(close, 14).iloc[-1]
    macd_line, signal_line, hist = calc_macd(close)
    results["macd"] = macd_line.iloc[-1] if not macd_line.isna().iloc[-1] else None
    results["macd_signal"] = signal_line.iloc[-1] if not signal_line.isna().iloc[-1] else None
    results["macd_hist"] = hist.iloc[-1] if not hist.isna().iloc[-1] else None
    if hist.iloc[-1] > 0 and (len(hist) < 2 or hist.iloc[-2] <= 0):
        results["macd_cross"] = "bullish"
    elif hist.iloc[-1] < 0 and (len(hist) < 2 or hist.iloc[-2] >= 0):
        results["macd_cross"] = "bearish"
    else:
        results["macd_cross"] = "neutral"
    avg_vol = volume.rolling(20).mean().iloc[-1]
    results["vol_ratio"] = volume.iloc[-1] / avg_vol if avg_vol > 0 else 1
    for sma_p in [20, 50, 200]:
        if len(close) >= sma_p:
            results[f"sma{sma_p}_diff"] = (close.iloc[-1] - calc_sma(close, sma_p).iloc[-1]) / calc_sma(close, sma_p).iloc[-1] * 100
        else:
            results[f"sma{sma_p}_diff"] = None
    rsi_series = calc_rsi(close, 14)
    div = detect_divergence(close, rsi_series, lookback=20)
    results["rsi_div"] = div
    results["price"] = close.iloc[-1]
    return results

def scan_stock(symbol):
    result = {"symbol": symbol, "sector": SECTORS.get(symbol, "Others"),
               "timeframes": {}, "errors": []}
    for tf in ["1HR", "1D", "1WK", "1MO"]:
        df = fetch_data(symbol, tf)
        if df is not None:
            result["timeframes"][tf] = analyze_timeframe(df, tf)
        else:
            result["timeframes"][tf] = None
            result["errors"].append(tf)
    return result

def main():
    print(f"[Scanner v2] Starting scan of {len(NIFTY_213)} stocks at {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    results = []
    for i, sym in enumerate(NIFTY_213, 1):
        try:
            r = scan_stock(sym)
            results.append(r)
            tf_data = r["timeframes"]
            day = tf_data.get("1D", {})
            rsi = day.get("rsi")
            macd_h = day.get("macd_hist")
            vol_r = day.get("vol_ratio")
            status = "OK" if rsi else "SKIP"
            print(f"[{i:3d}/{len(NIFTY_213)}] {sym:<15} RSI:{rsi:.1f if rsi else 'N/A':>6} "
                  f"MACD_H:{macd_h:.2f if macd_h else 'N/A':>7} VOL:{vol_r:.1f if vol_r else 'N/A':>5} {status}")
            time.sleep(0.15)
        except Exception as e:
            print(f"[{i:3d}/{len(NIFTY_213)}] {sym:<15} ERROR: {e}")
            results.append({"symbol": sym, "sector": SECTORS.get(sym,"Unknown"), "timeframes": {}, "errors": ["all"]})
    out_path = os.path.join(BASE, "scanner_v2_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print("=" * 60)
    print(f"Done. Saved to: {out_path}")
    return results

if __name__ == "__main__":
    import os as _os
    BASE = _os.path.dirname(_os.path.abspath(__file__))
    results = main()
'''

# ─────────────────────────────────────────────────────────────────────────────
# 2. scorer.py
# ─────────────────────────────────────────────────────────────────────────────
scorer = '''"""Scorer v1 — Scores each stock 0-10 based on multi-indicator signals"""
import json, os

BASE = r"D:\\MOVED FROM C\\Python\\venvs\\py311\\Scripts"

def score_stock(data):
    """
    Score each stock 0-10:
    - RSI (oversold/overbought positioning)
    - MACD (crossover signal strength)
    - Volume (anomaly spike)
    - Price vs SMA (trend alignment)
    - Multi-timeframe confirmation
    """
    score = 0
    signals = []
    tf = data.get("timeframes", {})

    day = tf.get("1D", {})
    wk  = tf.get("1WK", {})
    mo  = tf.get("1MO", {})

    # ── RSI scoring (0-3 pts) ──
    day_rsi = day.get("rsi")
    wk_rsi  = wk.get("rsi")
    mo_rsi  = mo.get("rsi")
    if day_rsi:
        if day_rsi < 30:       score += 2; signals.append(f"D_RSI_oversold({day_rsi:.0f})")
        elif day_rsi < 40:    score += 1; signals.append(f"D_RSI_near_oversold({day_rsi:.0f})")
        elif day_rsi > 70:    score -= 2; signals.append(f"D_RSI_overbought({day_rsi:.0f})")
        elif day_rsi > 60:    score -= 1; signals.append(f"D_RSI_near_overbought({day_rsi:.0f})")
    if wk_rsi and mo_rsi:
        if wk_rsi < 40 and mo_rsi < 50: score += 1; signals.append("MultiTF_oversold")

    # ── MACD scoring (0-2 pts) ──
    macd_hist = day.get("macd_hist")
    macd_cross = day.get("macd_cross")
    if macd_cross == "bullish":   score += 2; signals.append("MACD_bullish_xover")
    elif macd_cross == "bearish": score -= 2; signals.append("MACD_bearish_xover")
    elif macd_hist and macd_hist > 0: score += 1; signals.append("MACD_hist_positive")

    # ── Volume scoring (0-2 pts) ──
    vol_ratio = day.get("vol_ratio")
    if vol_ratio:
        if vol_ratio > 2.0:   score += 2; signals.append(f"Vol_spike({vol_ratio:.1f}x)")
        elif vol_ratio > 1.5: score += 1; signals.append(f"Vol_elevated({vol_ratio:.1f}x)")

    # ── Price vs SMA scoring (0-2 pts) ──
    price = day.get("price")
    for sma_key in ["sma20_diff", "sma50_diff", "sma200_diff"]:
        diff = day.get(sma_key)
        if diff is not None and price:
            if diff > 5:      score += 1; signals.append(f"Price_SMA_above({sma_key[-2:]})")
            elif diff < -5:  score -= 1; signals.append(f"Price_SMA_below({sma_key[-2:]})")

    # ── Multi-timeframe confirmation (0-1 pts) ──
    bullish_count = sum(1 for s in signals if "bullish" in s.lower() or "oversold" in s.lower())
    if bullish_count >= 3:  score += 1; signals.append("MultiTF_bullish_confirm")

    # ── Clamp score ──
    score = max(0, min(10, score))

    return {"symbol": data["symbol"], "sector": data.get("sector","Unknown"),
            "score": score, "signals": signals,
            "rsi_day": day_rsi, "rsi_wk": wk_rsi, "rsi_mo": mo_rsi,
            "macd_hist": day.get("macd_hist"), "macd_cross": day.get("macd_cross"),
            "vol_ratio": day.get("vol_ratio"), "price": price,
            "sma20_diff": day.get("sma20_diff"), "sma50_diff": day.get("sma50_diff")}

def rank_stocks(scores):
    """Rank stocks by score, separate into BUY/HOLD/AVOID tiers"""
    ranked = sorted(scores, key=lambda x: x["score"], reverse=True)
    buy   = [s for s in ranked if s["score"] >= 7]
    hold  = [s for s in ranked if 4 <= s["score"] < 7]
    avoid = [s for s in ranked if s["score"] < 4]
    return ranked, buy, hold, avoid

def main():
    in_path  = os.path.join(BASE, "scanner_v2_results.json")
    out_path = os.path.join(BASE, "scored_results.json")
    with open(in_path) as f:
        raw = json.load(f)
    scored = [score_stock(s) for s in raw]
    ranked, buy, hold, avoid = rank_stocks(scored)
    output = {"ranked": ranked, "buy": buy, "hold": hold, "avoid": avoid}
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print("=" * 60)
    print(f"Scored {len(scored)} stocks")
    print(f"  BUY  (score >= 7): {len(buy)}")
    print(f"  HOLD (score 4-6) : {len(hold)}")
    print(f"  AVOID(score < 4) : {len(avoid)}")
    print("=" * 60)
    print("TOP 10 BUY SIGNALS:")
    for s in ranked[:10]:
        print(f"  [{s['score']}/10] {s['symbol']:<15} RSI:{s['rsi_day']:.1f if s['rsi_day'] else 0:>5} "
              f"{' '.join(s['signals'][:3])}")
    print("=" * 60)
    print(f"Saved: {out_path}")
    return output

if __name__ == "__main__":
    main()
'''

# ─────────────────────────────────────────────────────────────────────────────
# 3. watchlist.py
# ─────────────────────────────────────────────────────���───────────────────────
watchlist = '''"""Watchlist Generator — builds daily trading watchlist from scored results"""
import json, os
from datetime import datetime

BASE = r"D:\\MOVED FROM C\\Python\\venvs\\py311\\Scripts"

def build_watchlist(scored_data, min_score=6, max_stocks=15):
    """Build a ranked watchlist from scored results"""
    buy_stocks = [s for s in scored_data.get("buy", []) if s["score"] >= min_score]
    top_holds  = [s for s in scored_data.get("hold", []) if s["score"] >= 5]
    combined = (buy_stocks + top_holds)[:max_stocks]
    watchlist = []
    for rank, stock in enumerate(combined, 1):
        entry = {
            "rank": rank,
            "symbol": stock["symbol"],
            "score": stock["score"],
            "sector": stock["sector"],
            "rsi_day": round(stock["rsi_day"], 1) if stock.get("rsi_day") else None,
            "rsi_wk":  round(stock["rsi_wk"],  1) if stock.get("rsi_wk")  else None,
            "macd_cross": stock.get("macd_cross", "neutral"),
            "vol_ratio":  round(stock["vol_ratio"], 1) if stock.get("vol_ratio") else 1.0,
            "price": round(stock["price"], 2) if stock.get("price") else None,
            "sma20_diff": round(stock["sma20_diff"], 1) if stock.get("sma20_diff") else 0,
            "signals": stock.get("signals", [])[:5],
            "action": "BUY" if stock["score"] >= 7 else "WATCH",
        }
        watchlist.append(entry)
    return watchlist

def generate_report(watchlist):
    """Generate human-readable watchlist report"""
    now = datetime.now().strftime("%d %b %Y %H:%M")
    lines = []
    lines.append(f"\\n{'='*55}")
    lines.append(f"  NIFTY WATCHLIST  |  {now}")
    lines.append(f"{'='*55}")
    buy   = [s for s in watchlist if s["action"] == "BUY"]
    watch = [s for s in watchlist if s["action"] == "WATCH"]
    lines.append(f"\\n  BUY ({len(buy)})")
    lines.append(f"  {'─'*40}")
    for s in buy:
        price_str = f"���{s['price']:.0f}" if s.get("price") else "N/A"
        lines.append(f"  {s['rank']:>2}. {s['symbol']:<12} {price_str:<8} "
                     f"RSI:{s['rsi_day'] if s['rsi_day'] else 0:>4}  "
                     f"MACD:{s['macd_cross'][:1].upper()}")
    lines.append(f"\\n  WATCH ({len(watch)})")
    lines.append(f"  {'─'*40}")
    for s in watch:
        price_str = f"₹{s['price']:.0f}" if s.get("price") else "N/A"
        lines.append(f"  {s['rank']:>2}. {s['symbol']:<12} {price_str:<8} "
                     f"RSI:{s['rsi_day'] if s['rsi_day'] else 0:>4}")
    lines.append(f"\\n{'='*55}\\n")
    return "\\n".join(lines)

def export_telegram_text(watchlist):
    """Generate Telegram-ready markdown message"""
    now = datetime.now().strftime("%d %b %Y")
    buy   = [s for s in watchlist if s["action"] == "BUY"]
    watch = [s for s in watchlist if s["action"] == "WATCH"]
    msg = [f"*📊 NIFTY Watchlist — {now}*"]
    msg.append(f"_Generated: {datetime.now().strftime('%H:%M')}_")
    msg.append("")
    if buy:
        msg.append(f"*🔥 BUY ({len(buy)})*")
        for s in buy:
            price = f"₹{s['price']:.0f}" if s.get("price") else "N/A"
            rsi = f"{s['rsi_day']:.0f}" if s.get("rsi_day") else "N/A"
            vol = f"Vol {s['vol_ratio']:.1f}x" if s.get("vol_ratio", 1) > 1.3 else ""
            msg.append(f"▸ {s['symbol']} | {price} | RSI {rsi} | {vol}")
    if watch:
        msg.append(f"\\n*👀 WATCH ({len(watch)})*")
        for s in watch:
            price = f"₹{s['price']:.0f}" if s.get("price") else "N/A"
            rsi = f"{s['rsi_day']:.0f}" if s.get("rsi_day") else "N/A"
            msg.append(f"▸ {s['symbol']} | {price} | RSI {rsi}")
    msg.append("\\n_Reply STOP to unsubscribe_")
    return "\\n".join(msg)

def main():
    in_path  = os.path.join(BASE, "scored_results.json")
    out_path = os.path.join(BASE, "watchlist.json")
    with open(in_path) as f:
        scored = json.load(f)
    watchlist = build_watchlist(scored)
    with open(out_path, "w") as f:
        json.dump(watchlist, f, indent=2)
    report = generate_report(watchlist)
    print(report)
    print(f"Watchlist saved: {out_path}")
    return watchlist

if __name__ == "__main__":
    main()
'''

# ────���────────────────────────────────────────────────────────────────────────
# 4. telegram_bot.py
# ─────────────────────────────────────────────────────────────────────────────
telegram_bot = '''"""Telegram Bot — sends daily watchlist to your phone via Telegram Bot API"""
import json, os, sys, http.client, urllib.parse
from datetime import datetime

BASE = r"D:\\MOVED FROM C\\Python\\venvs\\py311\\Scripts"

def load_config():
    """Load Telegram bot config from config.json"""
    cfg_path = os.path.join(BASE, "config.json")
    if not os.path.exists(cfg_path):
        print("ERROR: config.json not found. Create it with:")
        print("  { 'bot_token': 'YOUR_BOT_TOKEN', 'chat_id': 'YOUR_CHAT_ID' }")
        sys.exit(1)
    with open(cfg_path) as f:
        return json.load(f)

def send_telegram_message(token, chat_id, text):
    """Send message via Telegram Bot API (no external deps)"""
    conn = http.client.HTTPSConnection("api.telegram.org")
    payload = json.dumps({"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    headers = {"Content-Type": "application/json"}
    try:
        conn.request("POST", f"/bot{token}/sendMessage", payload, headers)
        resp = conn.getresponse()
        body = resp.read().decode()
        result = json.loads(body)
        if result.get("ok"):
            print(f"[Telegram] Message sent successfully")
            return True
        else:
            print(f"[Telegram] Error: {result.get('description')}")
            return False
    except Exception as e:
        print(f"[Telegram] Connection error: {e}")
        return False
    finally:
        conn.close()

def send_watchlist():
    """Load watchlist and send to Telegram"""
    cfg = load_config()
    wl_path = os.path.join(BASE, "watchlist.json")
    if not os.path.exists(wl_path):
        print("watchlist.json not found. Run watchlist.py first.")
        sys.exit(1)
    with open(wl_path) as f:
        watchlist = json.load(f)

    # Generate Telegram message
    now = datetime.now().strftime("%d %b %Y")
    buy   = [s for s in watchlist if s["action"] == "BUY"]
    watch = [s for s in watchlist if s["action"] == "WATCH"]

    lines = [f"*\\u0001f4ca NIFTY Watchlist \\u2014 {now}*",
             f"_Generated: {datetime.now().strftime('%H:%M')}_",
             ""]

    if buy:
        lines.append(f"*\\u0001f525 BUY ({len(buy)})*")
        for s in buy:
            price = f"\\u20b9{s['price']:.0f}" if s.get("price") else "N/A"
            rsi   = f"{s['rsi_day']:.0f}" if s.get("rsi_day") else "N/A"
            vol   = f"Vol {s['vol_ratio']:.1f}x" if s.get("vol_ratio",1) > 1.3 else ""
            lines.append(f"\\u25b8 {s['symbol']} | {price} | RSI {rsi} | {vol}")
        lines.append("")

    if watch:
        lines.append(f"*\\u0001f440 WATCH ({len(watch)})*")
        for s in watch:
            price = f"\\u20b9{s['price']:.0f}" if s.get("price") else "N/A"
            rsi   = f"{s['rsi_day']:.0f}" if s.get("rsi_day") else "N/A"
            lines.append(f"\\u25b8 {s['symbol']} | {price} | RSI {rsi}")

    lines.append("\\n_Scan: scanner_v2 \\u2192 scorer \\u2192 watchlist \\u2192 telegram_")
    text = "\\n".join(lines)
    return send_telegram_message(cfg["bot_token"], cfg["chat_id"], text)

def test_connection():
    """Test Telegram bot connection"""
    cfg = load_config()
    test_msg = f"*Scanner Bot Connected!* \\n\\u2705 Test at {datetime.now().strftime('%H:%M:%S')}"
    return send_telegram_message(cfg["bot_token"], cfg["chat_id"], test_msg)

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Telegram Watchlist Bot")
    parser.add_argument("--test", action="store_true", help="Send test message")
    parser.add_argument("--send", action="store_true", help="Send today's watchlist")
    args = parser.parse_args()
    if args.test:
        test_connection()
    elif args.send:
        send_watchlist()
    else:
        print("Usage:")
        print("  python telegram_bot.py --test   # Test connection")
        print("  python telegram_bot.py --send  # Send watchlist")

if __name__ == "__main__":
    main()
'''

# ─────────────────────────────────────────────────────────────────────────────
# 5. config.json template
# ───────────���─────────────────────────────────────────────────────────────────
config_json = '''{
  "_comment": "Telegram Bot Configuration",
  "_instructions": [
    "1. Create a bot: Message @BotFather on Telegram, send /newbot",
    "2. Copy the bot token below",
    "3. Start a chat with your bot, then send any message",
    "4. Get your chat_id: visit https://api.telegram.org/bot<TOKEN>/getUpdates",
    "5. Replace 'YOUR_CHAT_ID' with the numeric id from the response"
  ],
  "bot_token": "YOUR_BOT_TOKEN_HERE",
  "chat_id": "YOUR_CHAT_ID_HERE"
}'''

# ─────────────────────────────────────────────────────────────────────────────
# 6. README
# ───────────────────��─────────────────────────────────────────────────────────
readme = '''# NIFTY Scanner v2 — Daily Trading Watchlist Pipeline

## Overview
Multi-indicator stock scanner + scorer + Telegram delivery.
No subscriptions. No brokerage fees. 100% free.

## Pipeline
```
scanner_v2.py  →  scanner_v2_results.json
       ↓
scorer.py       →  scored_results.json
       ↓
watchlist.py    →  watchlist.json  →  telegram_bot.py  →  Your Phone
```

## Setup

### Step 1 — Install Python dependencies
```bash
pip install yfinance pandas openpyxl
```

### Step 2 — Get Telegram Bot (5 minutes)
1. Open Telegram → search *@BotFather* → send `/newbot`
2. Copy the token (starts with `:`)
3. Open your new bot → send it any message
4. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Copy the `chat` → `id` number

### Step 3 — Configure
Edit `config.json`:
```json
{
  "bot_token": "6123456789:AAFxxx...",
  "chat_id": "123456789"
}
```

## Usage

### Run the full pipeline manually
```bash
python scanner_v2.py    # Fetch RSI/MACD/Volume/SMA for 213 NIFTY stocks
python scorer.py        # Score each stock 0-10
python watchlist.py     # Build ranked watchlist
python telegram_bot.py --send   # Send to Telegram
```

### Daily automation (Windows Task Scheduler)
1. Open Task Scheduler → Create Basic Task
2. Name: *NIFTY Scanner Daily*
3. Trigger: Daily, 09:00 AM
4. Action: Start a program
   - Program: `python`
   - Arguments: `scanner_v2.py && scorer.py && watchlist.py && telegram_bot.py --send`
   - Start in: `D:\\MOVED FROM C\\Python\\venvs\\py311\\Scripts`

### Test Telegram connection
```bash
python telegram_bot.py --test
```

## Scoring System (0-10)

| Signal | Points | Description |
|--------|--------|-------------|
| RSI oversold (<30) | +2 | Daily RSI deeply oversold |
| RSI near oversold (<40) | +1 | Daily RSI approaching oversold |
| RSI overbought (>70) | -2 | Daily RSI overbought — caution |
| MACD bullish crossover | +2 | MACD crossed above signal line |
| MACD bearish crossover | -2 | MACD crossed below signal line |
| Volume spike (>2x avg) | +2 | Unusual volume activity |
| Volume elevated (>1.5x) | +1 | Above-average volume |
| Price above SMA 20/50/200 | +1 each | Short-term trend alignment |
| Multi-TF bullish confirm | +1 | Oversold across D/W/M timeframes |

**BUY** = Score >= 7 | **HOLD** = 4-6 | **AVOID** = < 4

## Indicators

- **RSI (Relative Strength Index)** — Momentum oscillator, 14-period
- **MACD** — 12/26/9 EMA crossover, histogram tracks momentum shift
- **Volume ratio** — Today's volume vs 20-day average
- **SMA diff** — Price distance from 20/50/200-day Simple Moving Averages

## Disclaimer
For educational purposes only. Not financial advice.
Backtest before using any strategy with real capital.
'''

# ─────────────────────────────────────────────────────────────────────────────
# Write all files
# ─────────────────────────────────────────────────────────────────────────────
w("scanner_v2.py",    scanner_v2)
w("scorer.py",         scorer)
w("watchlist.py",      watchlist)
w("telegram_bot.py",   telegram_bot)
w("config.json",       config_json)
w("README_WATCHLIST.md", readme)

print("\\nAll files written successfully!")
print("Run: python scanner_v2.py")
