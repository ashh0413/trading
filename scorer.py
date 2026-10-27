"""Scorer — assigns weighted composite scores to each stock from scanner_v2 output"""
import json, sys
from datetime import datetime

RSI_WEIGHT   = 0.30
MACD_WEIGHT  = 0.20
VOLUME_WEIGHT= 0.20
SMA_WEIGHT   = 0.15
SECTOR_WEIGHT= 0.15

def calc_rsi_score(rsi):
    if rsi is None: return 40
    if rsi < 30: return 100 - (30 - rsi) * 2
    if rsi < 45: return 70 + (rsi - 30) * 1.5
    if rsi < 55: return 70
    if rsi < 70: return 70 - (rsi - 55) * 1.5
    return max(0, 20 - (rsi - 70) * 1.5)

def calc_macd_score(macd_hist):
    if macd_hist is None: return 50
    if macd_hist > 5:   return 100
    if macd_hist > 2:   return 80 + (macd_hist - 2) * 6.7
    if macd_hist > 0:   return 60 + macd_hist * 10
    if macd_hist > -2:  return 50 + (macd_hist + 2) * 5
    if macd_hist > -5:  return 30 + (macd_hist + 5) * 6.7
    return max(0, 30 + macd_hist * 2)

def calc_volume_score(vol_ratio):
    if vol_ratio is None: return 50
    if vol_ratio > 3.0:  return 100
    if vol_ratio > 2.0:  return 80 + (vol_ratio - 2.0) * 20
    if vol_ratio > 1.0:  return 60 + (vol_ratio - 1.0) * 20
    if vol_ratio > 0.5:  return 50 + (vol_ratio - 0.5) * 20
    return max(0, vol_ratio * 80)

def calc_sma_score(sma5, sma20):
    if sma5 is None or sma20 is None: return 50
    if sma5 > sma20 * 1.05: return 100
    if sma5 > sma20:        return 75 + (sma5 / sma20 - 1) * 500
    if sma5 > sma20 * 0.95: return 50 + (sma5 / sma20 - 0.95) * 500
    return max(0, (sma5 / sma20) * 80)

def score_stock(s):
    rsi  = s.get("rsi_14")
    macd = s.get("macd_hist")
    vol  = s.get("volume_ratio")
    sma5 = s.get("sma_5")
    sma20= s.get("sma_20")
    score = (calc_rsi_score(rsi)   * RSI_WEIGHT
           + calc_macd_score(macd)  * MACD_WEIGHT
           + calc_volume_score(vol) * VOLUME_WEIGHT
           + calc_sma_score(sma5, sma20) * SMA_WEIGHT)
    return round(score, 2)

def load_sector_scores():
    return {
        "Auto":5,"Auto Ancillary":3,"Banks":7,"Capital Goods":4,"Capital Markets":4,
        "Cement":5,"FMCG":3,"Finance":5,"Furniture & Furnishing":2,"Gas Distribution":3,
        "Healthcare Services":4,"Hotels & Tourism":2,"Infrastructure & Logistics":5,
        "Insurance":4,"Internet & New-age":6,"Media & Entertainment":2,"Metals & Minerals":3,
        "Oil & Gas":4,"Others":2,"Pharma & Healthcare":5,"Power":4,"Retail":4,
    }

def score(input_path="scanner_results.json", output_path="scored_results.json"):
    with open(input_path, "r") as f:
        data = json.load(f)

    sector_map = load_sector_scores()
    stocks = data if isinstance(data, list) else data.get("stocks", [])
    results = []
    for s in stocks:
        base = score_stock(s)
        sector_score = sector_map.get(s.get("sector",""), 3)
        total = round(base * 0.8 + sector_score * 20 * 0.2, 2)
        s["composite_score"] = total
        s["base_score"] = base
        s["sector_score"] = sector_score
        results.append(s)

    for s in results:
        rsi = s.get("rsi_day") or s.get("rsi_week") or 50
        macd = s.get("macd_hist") or 0
        score = s.get("composite_score", 50)
        if score >= 75 or (rsi < 35 and macd > 0):
            s["signal"] = "STRONG BULLISH"
        elif score >= 60 or rsi < 40:
            s["signal"] = "BULLISH"
        elif score <= 25 or (rsi > 65 and macd < 0):
            s["signal"] = "STRONG BEARISH"
        elif score <= 40 or rsi > 60:
            s["signal"] = "BEARISH"
        else:
            s["signal"] = "NEUTRAL"

    results.sort(key=lambda x: x["composite_score"], reverse=True)

    out = {"scored": results, "meta": {"scored_at": datetime.now().isoformat()}}
    with open(output_path, "w") as f:
        json.dump(out, f, indent=2, default=str)

    print(f"Scored {len(results)} stocks -> {output_path}")
    for r in results[:5]:
        print(f"  {r.get('symbol','?'):20s} score={r['composite_score']:6.2f}  "
              f"RSI={str(r.get('rsi_14')):6}  MACD={str(r.get('macd_hist')):6}")

if __name__ == "__main__":
    score(*sys.argv[1:] if len(sys.argv) > 1 else [])
