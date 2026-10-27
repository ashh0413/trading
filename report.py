"""Report Generator — creates HTML and CSV summary reports from scored data"""
import json, csv, sys, os
from datetime import datetime

def load_data(json_path):
    with open(json_path) as f:
        return json.load(f)

def generate_csv(results, out_path):
    headers = ["Rank","Symbol","Score","RSI(Day)","RSI(Week)","RSI(Month)","RSI(Hour)",
               "MACD","MACD Hist","Vol Ratio","CMP","Sector","Signal","Bearish","Bullish"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for rank, r in enumerate(results, 1):
            w.writerow({
                "Rank": rank,
                "Symbol": r.get("symbol",""),
                "Score": r.get("composite_score",""),
                "RSI(Day)": r.get("rsi_day",""),
                "RSI(Week)": r.get("rsi_week",""),
                "RSI(Month)": r.get("rsi_month",""),
                "RSI(Hour)": r.get("rsi_hour",""),
                "MACD": r.get("macd_signal",""),
                "MACD Hist": r.get("macd_hist",""),
                "Vol Ratio": r.get("volume_ratio",""),
                "CMP": r.get("cmp",""),
                "Sector": r.get("sector",""),
                "Signal": r.get("signal",""),
                "Bearish": r.get("bearish",""),
                "Bullish": r.get("bullish",""),
            })
    print(f"CSV saved: {out_path}")

def generate_html(results, out_path):
    rows = ""
    for i, r in enumerate(results, 1):
        sig = r.get("signal","")
        sig_color = {"STRONG BULLISH":"#00c853","BULLISH":"#69f0ae","NEUTRAL":"#ffd740",
                     "BEARISH":"#ff6e40","STRONG BEARISH":"#ff1744"}.get(sig,"#ccc")
        rows += f"""<tr>
          <td>{i}</td>
          <td><b>{r.get('symbol','')}</b></td>
          <td>{r.get('composite_score','')}</td>
          <td>{r.get('rsi_day','')}</td>
          <td>{r.get('rsi_week','')}</td>
          <td>{r.get('rsi_month','')}</td>
          <td>{r.get('macd_hist','')}</td>
          <td>{r.get('volume_ratio','')}</td>
          <td>{r.get('cmp','')}</td>
          <td>{r.get('sector','')}</td>
          <td style="background:{sig_color};color:#111;border-radius:4px;padding:2px 8px;font-weight:bold">{sig}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html><head>
<meta charset="utf-8">
<title>Stock Scanner Report</title>
<style>
  body{{font-family:sans-serif;margin:20px;background:#111;color:#eee}}
  table{{border-collapse:collapse;width:100%;font-size:13px}}
  th{{background:#222;padding:8px;text-align:left;position:sticky;top:0}}
  td{{padding:6px 8px;border-bottom:1px solid #222}}
  tr:hover{{background:#1a1a1a}}
  h2{{color:#ffd740}}
</style></head><body>
<h2>Stock Scanner Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}</h2>
<p>Top signals:</p>
<table><thead><tr>
  <th>#</th><th>Symbol</th><th>Score</th><th>RSI D</th><th>RSI W</th>
  <th>RSI M</th><th>MACD</th><th>Vol</th><th>CMP</th><th>Sector</th><th>Signal</th>
</tr></thead><tbody>{rows}</tbody></table>
</body></html>"""
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML saved: {out_path}")

def main():
    json_path = "scored_results.json"
    out_csv = "scanner_report.csv"
    out_html = "scanner_report.html"
    if len(sys.argv) > 1:
        json_path = sys.argv[1]
    if len(sys.argv) > 2:
        out_csv = sys.argv[2]
    if len(sys.argv) > 3:
        out_html = sys.argv[3]

    data = load_data(json_path)
    results = data if isinstance(data, list) else data.get("scored", data.get("stocks", []))
    generate_csv(results, out_csv)
    generate_html(results, out_html)

if __name__ == "__main__":
    main()
