"""Stock Scanner v2 — Multi-indicator data fetcher for 213 Nifty stocks"""
import yfinance as yf
import pandas as pd
import numpy as np
import json, time, sys, os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

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
    "GODREJIND","GRANULES","GSPL","GUJGASLTD","HINDPETRO","HONAUT","HINDALCO","HDFCAMC",
    "HSCL","ICICIPRULI","IEX","INDHOTELS","INOXBOR","JBCHEPHARM","JSL","JINDALPOWER",
    "JKCEMENT","JKLAKSHMI","JMFIN","KAJARIACER","KALYANJOT","KEC","KEI","KENNAMET",
    "KIRLOSKAR","KOLTEPAT","LICHSGFIN","LINDEINDIA","LTIM","LUXIND","Mahanagar Gas","MAHLOG",
    "MAHSEAMLES","MANYAVAR","MAXHEALTH","MEDPLUS","METROBRANDS","MOTHERSON","MPHASIS",
    "MRF","MUTHOOTFIN","NAM-INDIA","NATCOPHARM","NAUKRI","NAVINFLUOR","NCH","NIVA BUPA",
    "NKIND","OBEROIRLTY","OIL","ONE","OPTIEMUS","PERSISTENT","PHINDE","PIIND","PPLPHARMA",
    "PRAJIND","PRESTIGE","QUESS","RADICO","RALLIS","RATNAMANI","RELAXO","RITES","SADBHAV",
    "SAFARI","SAGAR","SBICAPS","SCHAEFFLER","SHIVALIK","SHRIRAMFIN","SPAL","STAR","SULA",
    "SUMICHEM","SUPERHOUSE","SUVEN","TANLA","TATAELXSI","TATAPOWER","TEAMLEASE","TECHNOFAB",
    "TIMKEN","TIRUMALAU","TRENT","TRITURBINE","TVSSATCH","UBL","UKINT","UNIONBANK","UNOMINDA",
    "UPLL","VAKRANGEE","VARROC","VINATIORGA","VIPIND","WELSPUNIND","WESTLIFE","WHIRLPOOL",
    "WONDERLA","ZYDUSLIFE","ADANIGREEN","ADANIPOWER","ATUL","BASF","Bayer","BDL","BIocon",
    "CASTROL","CLEAN","CONCOR","COROMANDEL","DABUR","DCMSHRIRAM","ENIL","EPL","FINEORG",
    "FINOPB","GABRIEL","GESHIP","GLAXO","GLAND","GODFRY","GRAUWEIL","GREENPANEL","GSFC",
    "HEIDELBERG","HIKMA","Hindustan Aero","HITECH","IGPL","INDIACEM","JBMA","JETAIR",
    "KALE","KANSAINER","KIRLOS","MAHABANK","MEIL","MENON","MUNJAL","NCC","NHPC","NIITLTD",
    "NMDC","NTPC","OAL","ORIENTELEC","PARACLE","PCBL","PDSL","PTC","RAJRATAN","RAMCOCEM",
    "RATNAMANI","SADBHAV","SAFARI","SANDU","SEAMECH","SHAREINDIA","SHREERAMA","SISL",
    "SOUTHBANK","STANAV","SUNTECK","SUULD","TANLA","TIDEWIND","TIRUDAYA","TNPL","TNP",
    "TRF","TTKHLTCARE","TWL","UGROCAP","UJJIVAN","UJJIVANSFB","UNOMINDA","UPL","UTIAMC",
    "VADILALIN","VAIBHAV","VISAKA","WSTCSTPAPER","ZEEMEDIA","ZENSARTECH","ZFCVINDIA",
    "ZIPCO","GMRFL", "SPIC", "TATASTLBSL"
]

NIFTY_213 = list(dict.fromkeys(NIFTY_213))

SECTOR_MAP = {
    "RELIANCE":"Oil & Gas","TCS":"IT","HDFCBANK":"Banks","ICICIBANK":"Banks","INFY":"IT",
    "HINDUNILVR":"FMCG","ITC":"FMCG","KOTAKBANK":"Banks","LT":"Capital Goods",
    "SBILIFE":"Insurance","AXISBANK":"Banks","BHARTIARTL":"Telecom","ASIANPAINT":"Chemicals",
    "MARUTI":"Automobiles","SUNPHARMA":"Pharma","ULTRACEMCO":"Cement","NESTLEIND":"FMCG",
    "LARSEN":"Capital Goods","POWERGRID":"Power","M&M":"Automobiles","BAJFINANCE":"Finance",
    "TITAN":"Consumer Goods","BAJAJFINSV":"Finance","NTPC":"Power","ONGC":"Oil & Gas",
    "COALINDIA":"Metals & Mining","HCLTECH":"IT","WIPRO":"IT","TECHM":"IT",
    "ADANIPORTS":"Infrastructure","JSWSTEEL":"Steel","UPL":"Chemicals","ADANIENT":"Conglomerate",
    "CIPLA":"Pharma","DIVISLAB":"Pharma","GRASIM":"Cement","HDFCLIFE":"Insurance",
    "IOC":"Oil & Gas","BRITANNIA":"FMCG","DRREDDY":"Pharma","EICHERMOT":"Automobiles",
    "HEROMOTOCO":"Automobiles","HINDZINC":"Metals & Mining","ICICIGI":"Insurance",
    "INDUSINDBK":"Banks","JUBLFOOD":"FMCG","SBICARD":"Finance","SHREECEM":"Cement",
    "SIEMENS":"Capital Goods","VEDL":"Metals & Mining","BAJAJ-AUTO":"Automobiles",
    "BEL":"Capital Goods","CANBK":"Banks","DABUR":"FMCG","GAIL":"Oil & Gas",
    "GODREJCP":"FMCG","HAVELLS":"Consumer Goods","LUPIN":"Pharma","MARICO":"FMCG",
    "NMDC":"Metals & Mining","PEL":"Pharma","PNB":"Banks","SRF":"Chemicals","TATACONSUM":"FMCG",
    "TATASTEEL":"Steel","AMBUJACEM":"Cement","FORTIS":"Healthcare","GLENMARK":"Pharma",
    "GMRINFRA":"Infrastructure","HONAUT":"Capital Goods","HINDALCO":"Metals & Mining",
    "BANKBARODA":"Banks","CHAMBLFERT":"Fertilizers","COROMANDEL":"Fertilizers","EXIDEIND":"Auto Components",
    "FEDERALBNK":"Banks","GODREJPROP":"Real Estate","IBULHSGFIN":"Housing Finance","IDEA":"Telecom",
    "IGL":"Gas Distribution","INDUSTOWER":"Telecom Infrastructure","M&MFIN":"Finance","MANAPPURAM":"Finance",
    "PFC":"Power Finance","RBLBANK":"Banks","RECLIMIT":"Finance","SUNTV":"Media",
    "TATACOMM":"Telecom","TORNTPOWER":"Power","TVSMOTOR":"Automobiles","AUROPHARMA":"Pharma",
    "BALRAMCHIN":"Sugar","BANDHANBNK":"Banks","BANKBE":"Banks","BERGEPAINT":"Paints",
    "BIOCON":"Pharma","BOSCHLTD":"Auto Components","BPCL":"Oil & Gas","CANFINHOME":"Housing Finance",
    "CEATLTD":"Auto Components","COLPAL":"Consumer Goods","CONCOR":"Logistics","CUMMINSIND":"Capital Goods",
    "DLF":"Real Estate","DMART":"Retail","ESCORTS":"Automobiles","FRETAIL":"Retail",
    "GNFC":"Chemicals","GSPL":"Gas Distribution","GUJGASLTD":"Gas Distribution","HINDPETRO":"Oil & Gas",
    "ICICIPRULI":"Insurance","INDHOTELS":"Hospitality","JKCEMENT":"Cement","LUXIND":"Textiles",
    "MANYAVAR":"Jewelry","MRF":"Auto Components","MUTHOOTFIN":"Gold Loan","NAUKRI":"HR Services",
    "NAVINFLUOR":"Chemicals","OBEROIRLTY":"Real Estate","OIL":"Oil & Gas","PERSISTENT":"IT",
    "PIIND":"Chemicals","POLYCAB":"Cables","QUESS":"IT Services","RATNAMANI":"Metals & Mining",
    "RELAXO":"Footwear","RITES":"Engineering","SAGAR":"Consumer Goods","SBICAPS":"Stock Broking",
    "SHREERAMA":"Textiles","SHRIRAMFIN":"Finance","SUPERHOUSE":"Leather","TANLA":"IT Services",
    "TATAELXSI":"IT","TATAPOWER":"Power","TEAMLEASE":"HR Services","TIRUMALAU":"Chemicals",
    "TRENT":"Retail","UBL":"Beverages","UNIONBANK":"Banks","UPL":"Chemicals","VARROC":"Auto Components",
    "WHIRLPOOL":"Consumer Goods","ZYDUSLIFE":"Pharma","ADANIPOWER":"Power","ATUL":"Chemicals",
    "BASF":"Chemicals","BPCL":"Oil & Gas","ENIL":"Entertainment","EPL":"Packaging",
    "GRAUWEIL":"Capital Goods","GREENPANEL":"Plywood","HDFCAMC":"AMC","HSCL":"Chemicals",
    "IEX":"Power Exchange","KEI":"Cables","KENNAMET":"Sintered Components","KIRLOSKAR":"Engineering",
    "LTIM":"IT","MAHSEAMLES":"Steel","MAXHEALTH":"Healthcare","METROBRANDS":"Footwear",
    "MOTHERSON":"Auto Components","MPHASIS":"IT","NAM-INDIA":"Insurance","NATCOPHARM":"Pharma",
    "NIVA BUPA":"Health Insurance","NKIND":"Specialty Chemicals","ONE":"IT","PERSISTENT":"IT",
    "PGHH":"Consumer Goods","PHINDE":"Pharma","PPLPHARMA":"Pharma","PRESTIGE":"Real Estate",
    "RADICO":"Alcohol","RALLIS":"Agri Inputs","SAFARI":"Leather","SCHAEFFLER":"Auto Components",
    "SHIVALIK":"Chemicals","SPAL":"Auto Components","STAR":"Beverages","SULA":"Alcohol",
    "SUVEN":"Pharma","TECHNOFAB":"Capital Goods","TIMKEN":"Auto Components","TRITURBINE":"Capital Goods",
    "TVSSATCH":"Leather","UKINT":"IT","UNOMINDA":"Auto Components","VINATIORGA":"Chemicals",
    "VIPIND":"Leather","WELSPUNIND":"Textiles","WESTLIFE":"QSR","WONDERLA":"Entertainment",
    "ADANIGREEN":"Renewable Energy","KANSAINER":"Chemicals","LICHSGFIN":"Finance","TIDEWIND":"Chemicals",
    "ZFCVINDIA":"Automobiles","ZIPCO":"Packaging","RAJRATAN":"Steel","GLAXO":"Pharma","BHARATRAS":"Chemicals"
}

def rsi(closes, period=14):
    delta = closes.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(closes, fast=12, slow=26, signal=9):
    ema_fast = closes.ewm(span=fast, adjust=False).mean()
    ema_slow = closes.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    return macd_line, signal_line

def sma(closes, period):
    return closes.rolling(window=period).mean()

def volume_ratio(volumes, period=20):
    avg_vol = volumes.rolling(window=period).mean()
    return volumes / avg_vol.replace(0, np.nan)

def detect_divergence(prices, indicator, lookback=20):
    bullish = 0
    bearish = 0
    for i in range(lookback, len(prices)):
        window_p = prices.iloc[i-lookback:i]
        window_i = indicator.iloc[i-lookback:i]
        if window_p.iloc[0] > window_p.iloc[-1] and window_i.iloc[0] < window_i.iloc[-1]:
            bullish += 1
        elif window_p.iloc[0] < window_p.iloc[-1] and window_i.iloc[0] > window_i.iloc[-1]:
            bearish += 1
    return bullish, bearish

def fetch_indicators(symbol):
    result = {"symbol": symbol, "sector": SECTOR_MAP.get(symbol, "Others"), "success": False}
    try:
        ticker = yf.Ticker(f"{symbol}.NS")

        # Fetch data for all timeframes
        df_d = ticker.history(period="2y", interval="1d", auto_adjust=True)
        df_w = ticker.history(period="3y", interval="1wk", auto_adjust=True)
        df_m = ticker.history(period="5y", interval="1mo", auto_adjust=True)
        df_h = ticker.history(period="5d", interval="60m", auto_adjust=True)

        if df_d.empty or len(df_d) < 60:
            return result

        result["price"] = float(df_d["Close"].iloc[-1])

        # Daily indicators
        rsi_d = rsi(df_d["Close"], 14)
        macd_line, macd_sig = macd(df_d["Close"])
        sma20 = sma(df_d["Close"], 20)
        sma50 = sma(df_d["Close"], 50)
        sma200 = sma(df_d["Close"], 200)
        vol_r = volume_ratio(df_d["Volume"])

        result["rsi_day"] = float(rsi_d.iloc[-1]) if not rsi_d.iloc[-1:].isna().all() else None
        result["rsi_day_series"] = rsi_d.dropna().tolist()[-60:]

        # Weekly
        if not df_w.empty:
            rsi_w = rsi(df_w["Close"], 14)
            result["rsi_week"] = float(rsi_w.iloc[-1]) if not rsi_w.iloc[-1:].isna().all() else None
            result["rsi_week_series"] = rsi_w.dropna().tolist()[-52:]

        # Monthly
        if not df_m.empty:
            rsi_m = rsi(df_m["Close"], 14)
            result["rsi_month"] = float(rsi_m.iloc[-1]) if not rsi_m.iloc[-1:].isna().all() else None

        # Hourly
        if not df_h.empty:
            rsi_h = rsi(df_h["Close"], 14)
            result["rsi_1hr"] = float(rsi_h.iloc[-1]) if not rsi_h.iloc[-1:].isna().all() else None

        # MACD
        result["macd_signal"] = float(macd_line.iloc[-1] - macd_sig.iloc[-1]) if not macd_line.empty else None

        # SMA
        result["sma20"] = float(sma20.iloc[-1]) if not sma20.isna().iloc[-1] else None
        result["sma50"] = float(sma50.iloc[-1]) if not sma50.isna().iloc[-1] else None
        result["sma200"] = float(sma200.iloc[-1]) if not sma200.isna().iloc[-1] else None

        # Volume
        result["volume_ratio"] = float(vol_r.iloc[-1]) if not vol_r.isna().iloc[-1] else None

        # Divergence detection (daily)
        bull, bear = detect_divergence(df_d["Close"], rsi_d)
        result["bull_count"] = bull
        result["bear_count"] = bear

        result["success"] = True

    except Exception as e:
        result["error"] = str(e)

    return result

def main():
    print(f"Scanning {len(NIFTY_213)} stocks with v2 indicators...")
    print("=" * 60)

    results = []
    errors = 0

    for i, symbol in enumerate(NIFTY_213, 1):
        print(f"[{i}/{len(NIFTY_213)}] {symbol}...", end=" ")
        data = fetch_indicators(symbol)

        if data["success"]:
            rd = data.get("rsi_day")
            rw = data.get("rsi_week")
            rd_str = f"{rd:.1f}" if rd is not None else "N/A"
            rw_str = f"{rw:.1f}" if rw is not None else "N/A"
            print(f"OK | RSI(D):{rd_str} RSI(W):{rw_str}")
        else:
            print(f"FAIL ({data.get('error','No data')})")
            errors += 1

        results.append(data)
        time.sleep(0.3)

    output = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success": sum(1 for r in results if r["success"]),
        "errors": errors,
        "stocks": results
    }

    out_path = os.path.join(SCRIPT_DIR, "scanner_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Done: {output['success']}/{output['total']} stocks scanned")
    print(f"Output: {out_path}")
    return output

if __name__ == "__main__":
    main()
