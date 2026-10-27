"""
Setup script: Fetch Nifty 500 list + sectors from GitHub CSV,
merge with existing sector map, and generate updated scanner_v2.py.
"""
import csv
import re
import urllib.request
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_URL = "https://raw.githubusercontent.com/kprohith/nse-stock-analysis/master/ind_nifty500list.csv"

def fetch_csv():
    print("Fetching Nifty 500 CSV from GitHub...")
    req = urllib.request.Request(CSV_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        lines = response.read().decode("utf-8").splitlines()
    reader = csv.DictReader(lines)
    stocks = []
    for row in reader:
        sym = row.get("Symbol", "").strip()
        industry = row.get("Industry", "").strip()
        if sym:
            stocks.append({"symbol": sym, "industry": industry})
    print(f"  -> {len(stocks)} stocks fetched")
    return stocks

def map_industry(ind):
    if not ind:
        return "Others"
    ind = ind.upper()
    if any(x in ind for x in ["BANK", "SFB"]): return "Banks"
    if any(x in ind for x in ["PHARM", "DRUG", "BIO", "HEALTH"]): return "Pharma"
    if any(x in ind for x in ["FINANCE", "INVEST", "LEASING", "ASSET", "HFC", "NBFC"]): return "Finance"
    if any(x in ind for x in ["IT", "SOFTWARE", "COMPUTER", "TECHNOLOGY", "TECH"]): return "IT"
    if any(x in ind for x in ["FMCG", "CONSUMER", "FOOD", "BEVERAGE", "PERSONAL"]): return "FMCG"
    if any(x in ind for x in ["CEMENT", "CERAMIC", "BUILDING"]): return "Cement"
    if any(x in ind for x in ["AUTO", "AUTOMOTIVE", "VEHICLE", "TRACTOR", "TYRE", "RUBBER"]): return "Auto"
    if any(x in ind for x in ["STEEL", "METAL", "MINING", "ALUMINIUM", "COPPER", "ZINC", "LEAD"]): return "Metals"
    if any(x in ind for x in ["OIL", "PETROLEUM", "GAS", "REFINERY", "LUBRICANT"]): return "Oil & Gas"
    if any(x in ind for x in ["POWER", "ENERGY", "RENEWABLE", "SOLAR", "WIND"]): return "Power"
    if any(x in ind for x in ["INSURANCE"]): return "Insurance"
    if any(x in ind for x in ["LOGISTICS", "TRANSPORT", "COURIER", "SHIPPING", "PORT"]): return "Logistics"
    if any(x in ind for x in ["REALTY", "REAL ESTATE", "CONSTRUCTION"]): return "Realty"
    if any(x in ind for x in ["MEDIA", "ENTERTAINMENT", "BROADCAST", "TV", "PRINT"]): return "Media"
    if any(x in ind for x in ["RETAIL", "TRADING"]): return "Retail"
    if any(x in ind for x in ["INFRA", "INFRASTRUCTURE", "ROAD", "HIGHWAY", "BRIDGE"]): return "Infrastructure"
    if any(x in ind for x in ["HOTEL", "TOURISM", "LEISURE"]): return "Hotels & Tourism"
    if any(x in ind for x in ["PESTICIDE", "FERTILIZER", "AGRI", "AGRO", "SEED"]): return "Agrochemicals"
    if any(x in ind for x in ["TEXTILE", "COTTON", "APPAREL", "GARMENT", "SILK"]): return "Textiles"
    if any(x in ind for x in ["CHEMICAL", "PETROCHEMICAL"]): return "Chemicals"
    if any(x in ind for x in ["PLASTIC", "POLYMER"]): return "Plastics"
    if any(x in ind for x in ["LUBE", "INDUSTRIAL"]): return "Industrial"
    if any(x in ind for x in ["JEWELLERY", "GEMS", "DIAMOND"]): return "Jewelry"
    if any(x in ind for x in ["PAPER", "PACKAGING"]): return "Paper & Packaging"
    if any(x in ind for x in ["PAINT", "COATING", "DECOR"]): return "Paints"
    return "Others"

def load_existing_map():
    """Load existing sector map from the current scanner_v2.py"""
    scanner_path = os.path.join(SCRIPT_DIR, "scanner_v2.py")
    sector_map = {}
    with open(scanner_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Extract NIFTY_213 dict
    import re
    match = re.search(r"NIFTY_213\s*=\s*\{([^}]+(?:\{[^}]+\}[^}]*)*)\}", content, re.DOTALL)
    if match:
        dict_str = match.group(0)
        # Parse key: "SYMBOL": "SECTOR"
        entries = re.findall(r'"([A-Z]+)":\s*"([^"]+)"', dict_str)
        for sym, sector in entries:
            sector_map[sym] = sector
    return sector_map

def generate_scanner(stocks, existing_map):
    """Generate updated scanner_v2.py with full Nifty 500"""
    # Build symbol -> sector (prefer existing manual map, fallback to CSV industry)
    final_map = {}
    csv_map = {}
    for s in stocks:
        csv_map[s["symbol"]] = map_industry(s["industry"])

    # Merge: existing manual map overrides CSV
    for sym, sector in existing_map.items():
        final_map[sym] = sector
    for s in stocks:
        if s["symbol"] not in final_map:
            final_map[s["symbol"]] = csv_map[s["symbol"]]

    # Sort alphabetically
    symbols = sorted(final_map.keys())

    # Build dict string (60 per line)
    lines = []
    for i in range(0, len(symbols), 5):
        chunk = symbols[i:i+5]
        parts = [f'    "{sym}": "{final_map[sym]}"' for sym in chunk]
        lines.append(",\n".join(parts) + ",")
    # Fix last comma
    if lines:
        lines[-1] = lines[-1].rstrip(",")

    dict_str = ",\n".join(lines)

    # Read existing scanner
    scanner_path = os.path.join(SCRIPT_DIR, "scanner_v2.py")
    with open(scanner_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace NIFTY_213 block
    new_content = re.sub(
        r"NIFTY_213\s*=\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}",
        f"NIFTY_213 = {{\n{dict_str}\n}}",
        content,
        flags=re.DOTALL
    )

    # Backup
    backup_path = os.path.join(SCRIPT_DIR, "scanner_v2.py.bak")
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(content)

    with open(scanner_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  -> Updated scanner_v2.py with {len(symbols)} symbols")
    print(f"  -> Backup saved to scanner_v2.py.bak")

    # Save nifty500_symbols.txt
    sym_path = os.path.join(SCRIPT_DIR, "nifty500_symbols.txt")
    with open(sym_path, "w", encoding="utf-8") as f:
        for sym in symbols:
            f.write(f"{sym}\n")
    print(f"  -> Saved {len(symbols)} symbols to nifty500_symbols.txt")

if __name__ == "__main__":
    stocks = fetch_csv()
    existing_map = load_existing_map()
    print(f"  -> Existing manual map: {len(existing_map)} entries")
    generate_scanner(stocks, existing_map)
    print("\nDone! Run 'python run_all.py' to scan all Nifty 500 stocks.")
