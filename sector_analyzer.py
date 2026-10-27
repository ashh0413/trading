import json
from pathlib import Path
from openpyxl import load_workbook

RESULTS = Path(__file__).parent / "scanner_results.json"
EXCEL = Path.home() / "Downloads" / "STOCKS SELECTION SHEET .xlsx"
TIMEFRAMES = ["1HR", "DAY", "WEEK", "MONTH"]

def load():
    with open(RESULTS, encoding="utf-8") as f:
        return json.load(f)

def sector_summary(rows):
    sectors = {}
    for r in rows:
        sec = r.get("SECTOR") or "Unknown"
        if sec not in sectors:
            sectors[sec] = {tf: [] for tf in TIMEFRAMES}
            sectors[sec]["_bull"] = 0
            sectors[sec]["_bear"] = 0
        s = sectors[sec]
        for tf in TIMEFRAMES:
            v = r.get(f"RSI_{tf}")
            if v is not None:
                s[tf].append(v)
        s["_bull"] += r.get("Bull_Score", 0)
        s["_bear"] += r.get("Bear_Score", 0)
    print()
    print("{:<22} {:>7} {:>7} {:>7} {:>7} {:>6} {:>6}  SIGNAL".format("SECTOR","1HR","DAY","WEEK","MONTH","BULL","BEAR"))
    print("-" * 80)
    for sec in sorted(sectors):
        s = sectors[sec]
        avgs = {tf: (round(sum(s[tf]) / len(s[tf]), 1) if s[tf] else None) for tf in TIMEFRAMES}
        bull, bear = s["_bull"], s["_bear"]
        w = avgs.get("WEEK")
        if bull > bear * 1.5 and w and w > 55:
            sig = "BULLISH"
        elif bear > bull * 1.5 and w and w < 45:
            sig = "BEARISH"
        elif w and w < 40:
            sig = "OVERSOLD (W)"
        elif avgs.get("MONTH") and avgs["MONTH"] > 65:
            sig = "OVERBOUGHT"
        elif avgs.get("MONTH") and avgs["MONTH"] < 35:
            sig = "OVERSOLD"
        else:
            sig = "NEUTRAL"
        print("{:<22}{:>7}{:>7}{:>7}{:>7}{:>6}  {:>6}  {}".format(sec, avgs.get('1HR',''), avgs.get('DAY',''), avgs.get('WEEK',''), avgs.get('MONTH',''), bull, bear, sig))

def update_excel(rows):
    wb = load_workbook(EXCEL)
    ws = wb["FNO_Live"]
    # Col A = Symbol, RSI cols: P=RSI_MONTH, R=RSI_WEEK, T=RSI_DAY, V=RSI_1HR
    # Bull_Score -> col N, Bear_Score -> col O, Signal -> derived
    col_map = {"RSI_MONTH": "P", "RSI_WEEK": "R", "RSI_DAY": "T", "RSI_1HR": "V"}
    symbol_col = "A"
    bull_col = "N"
    bear_col = "O"
    # Build symbol -> row map
    row_map = {}
    for i, row in enumerate(ws.iter_rows(min_row=2, min_col=1, max_col=1, values_only=True), start=2):
        sym = row[0]
        if sym:
            row_map[str(sym).strip()] = i
    updated = 0
    for r in rows:
        sym = r.get("Symbol") or r.get("symbol")
        if not sym:
            continue
        sym = str(sym).strip()
        if sym not in row_map:
            continue
        rn = row_map[sym]
        for key, col in col_map.items():
            v = r.get(key)
            if v is not None:
                ws[f"{col}{rn}"] = v
        ws[f"{bull_col}{rn}"] = r.get("Bull_Score", 0)
        ws[f"{bear_col}{rn}"] = r.get("Bear_Score", 0)
        ws[f"S{rn}"] = r.get("Signal", "NEUTRAL")
        updated += 1
    wb.save(EXCEL)
    print(f"Excel updated: {updated} stocks written to {EXCEL.name}")

def run():
    rows = load()
    print(f"Total stocks loaded: {len(rows)}")
    sector_summary(rows)
    update_excel(rows)

if __name__ == "__main__":
    run()
