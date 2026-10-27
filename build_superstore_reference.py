"""
Builds 9 clearly-labeled REFERENCE images matching the Superstore report:
1. Total Sales KPI card
2. Total Profit KPI card
3. Total Quantity KPI card
4. Profit Margin KPI card
5. Monthly Sales Trend (2018-2021)
6. Category & Sub-Category Analysis (Sales + Profit bars)
7. Regional Analysis Map (US states by Profit)
8. Top 10 Products by Sales
9. Full composite dashboard

Data values come from the report, chart shape is synthetic-but-plausible.
All PNGs carry a small "REFERENCE ONLY - study aid" watermark.
"""
import os, json, math, urllib.request
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle
from matplotlib.lines import Line2D
from matplotlib.collections import PatchCollection

OUT = os.path.join(os.path.dirname(__file__), "Superstore_Reference_Output")
os.makedirs(OUT, exist_ok=True)

# ---------- report numbers ----------
SALES   = 2_297_201
PROFIT  = 286_397
QTY     = 37_873
MARGIN  = 12.5

ORANGE  = "#E07A1F"
BLUE    = "#1F6FEB"
INK     = "#1a1a2e"
GREY    = "#6b7280"
BG      = "#F5F6FA"

def watermark(ax, note="REFERENCE ONLY - study aid. Build the real one in Tableau -> Sample Superstore"):
    ax.text(0.995, 0.01, note, transform=ax.transAxes, ha="right", va="bottom",
            fontsize=7, color=GREY, alpha=0.55, style="italic")

def style_ax(ax):
    ax.grid(True, axis="y", linestyle=":", alpha=0.35)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_facecolor("white")

def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p)

# =====================================================================
# 1-4  KPI CARDS
# =====================================================================
def kpi_card(title, big, sub, accent, fname):
    fig = plt.figure(figsize=(6.4, 2.7))
    fig.patch.set_facecolor(BG)
    ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, 100); ax.set_ylim(0, 100)
    ax.add_patch(FancyBboxPatch((2, 6), 96, 88,
                                boxstyle="round,pad=0.6,rounding_size=2.2",
                                linewidth=0, facecolor="white"))
    ax.add_patch(Rectangle((2, 6), 1.5, 88, facecolor=accent, edgecolor="none"))
    ax.text(8, 82, title, fontsize=15, color=GREY, fontweight="bold")
    ax.text(8, 45, big, fontsize=44, color=INK, fontweight="bold")
    ax.text(8, 22, sub, fontsize=11, color=GREY)
    watermark(ax, "REFERENCE ONLY - one number card from the report")
    save(fig, fname)

kpi_card("TOTAL SALES", "₹ 22,97,201", "All Superstore transactions, 2018 – 2021", ORANGE, "01_total_sales_kpi.png")
kpi_card("TOTAL PROFIT", "₹ 2,86,397", "Net profit after cost of goods sold", BLUE,        "02_total_profit_kpi.png")
kpi_card("TOTAL QUANTITY", "37,873", "Units sold across all orders", INK,              "03_total_quantity_kpi.png")
kpi_card("PROFIT MARGIN", "12.5%", "Profit as a percentage of sales", "#0E9F6E",      "04_profit_margin_kpi.png")

# =====================================================================
# 5. MONTHLY SALES TREND
# =====================================================================
def monthly_series(total, seed=11):
    rng = np.random.default_rng(seed)
    n = 48
    t = np.arange(n)
    season = np.sin(t * 2 * math.pi / 12) * 0.18
    trend  = (t / n - 0.5) * 0.55
    noise  = rng.normal(0, 0.035, n)
    v = 1 + season + trend + noise
    v = np.clip(v, 0.2, None)
    v = v / v.sum() * total
    return v

def labels_2018_2021():
    out = []
    for y in (2018, 2019, 2020, 2021):
        for m in range(1, 13):
            out.append(f"{m:02d}/{y}")
    return out

def build_monthly(fname):
    vals = monthly_series(SALES)
    xlab = labels_2018_2021()
    fig, ax = plt.subplots(figsize=(11, 5.4))
    style_ax(ax); fig.patch.set_facecolor("white")
    ax.fill_between(range(48), vals, 0, color=ORANGE, alpha=0.18)
    ax.plot(range(48), vals, color=ORANGE, linewidth=2.2, marker="o", markersize=3.5)
    avg = vals.mean()
    ax.axhline(avg, color=BLUE, linewidth=1.4, linestyle="--", alpha=0.9)
    ax.text(0, avg + 4000, f"Average ₹{int(avg):,}", color=BLUE, fontsize=9, fontweight="bold")
    step = 3
    ax.set_xticks(range(0, 48, step))
    ax.set_xticklabels([xlab[i] for i in range(0, 48, step)], rotation=45, ha="right", fontsize=8)
    tick = [int(v) for v in ax.get_yticks()]
    ax.set_yticklabels([f"₹{v//1000}k" for v in tick])
    ax.set_title("Monthly Sales Trend, 2018 – 2021", fontsize=14, fontweight="bold", color=INK, loc="left")
    watermark(ax)
    save(fig, fname)

build_monthly("05_monthly_sales_trend.png")

# =====================================================================
# 6. CATEGORY & SUB-CATEGORY ANALYSIS
# =====================================================================
def build_subcat(fname):
    # 10 sub-categories, sales values summing to 22,97,201 (approx)
    # ratios shaped like the real Superstore mix (Furniture low-margin but large, Tech high sales)
    subs = [
        ("Furniture / Chairs",        280_000,  41_000),
        ("Furniture / Furnishing",    240_000,  33_000),
        ("Furniture / Tables",        310_000,  15_000),
        ("Office Supplies / Binders", 230_000,  38_000),
        ("Office Supplies / Paper",   190_000,  24_000),
        ("Office Supplies / Storage", 250_000,  35_000),
        ("Office Supplies / Supplies",140_000,  12_000),
        ("Technology / Accessories",  130_000,  25_000),
        ("Technology / Copiers",      270_000,  62_000),
        ("Technology / Phones",       257_201,  41_397),
    ]
    # force exact totals
    s_sum = sum(x[1] for x in subs)
    p_sum = sum(x[2] for x in subs)
    subs  = [(n, round(s * SALES / s_sum), round(p * PROFIT / p_sum)) for (n, s, p) in subs]

    names  = [s[0] for s in subs]
    sales  = [s[1] for s in subs]
    profit = [s[2] for s in subs]
    x = np.arange(len(names)); w = 0.38

    fig, ax = plt.subplots(figsize=(12, 6.2))
    style_ax(ax); fig.patch.set_facecolor("white")
    b1 = ax.bar(x - w/2, sales,  w, color=ORANGE, label="Sales (₹)")
    b2 = ax.bar(x + w/2, profit, w, color=BLUE,   label="Profit (₹)")
    for rect, v in zip(b1, sales):
        ax.text(rect.get_x() + rect.get_width()/2, v + 6000, f"{v//1000}k",
                ha="center", fontsize=7, color=INK)
    for rect, v in zip(b2, profit):
        ax.text(rect.get_x() + rect.get_width()/2, v + 6000, f"{v//1000}k",
                ha="center", fontsize=7, color=INK)
    ax.set_xticks(x); ax.set_xticklabels(names, rotation=32, ha="right", fontsize=9)
    ax.set_ylabel("₹")
    ax.set_title("Category & Sub-Category – Sales vs Profit", fontsize=14, fontweight="bold", color=INK, loc="left")
    handles = [Line2D([0],[0], color=ORANGE, lw=8, label="Sales"),
               Line2D([0],[0], color=BLUE,   lw=8, label="Profit")]
    ax.legend(handles=handles, frameon=False, loc="upper right")
    ax.yaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("₹{x:,.0f}"))
    watermark(ax)
    save(fig, fname)

build_subcat("06_category_subcategory.png")

# =====================================================================
# 7. REGIONAL MAP (US states coloured by profit)
# =====================================================================
def fetch_us_states_geojson():
    url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
    try:
        with urllib.request.urlopen(url, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print("geojson fetch failed:", e)
        return None

def state_profits():
    # Deterministic, plausible per-state profit. Big states bigger. Sum ~ PROFIT.
    rng = np.random.default_rng(7)
    base = {
        "California":1.9,"Texas":1.55,"Florida":1.35,"New York":1.3,"Illinois":0.95,
        "Pennsylvania":0.72,"Ohio":0.62,"Georgia":0.6,"North Carolina":0.55,
        "Michigan":0.52,"New Jersey":0.5,"Virginia":0.47,"Washington":0.45,
        "Arizona":0.42,"Massachusetts":0.42,"Tennessee":0.4,"Colorado":0.38,
        "Minnesota":0.36,"Maryland":0.34,"Missouri":0.32,"Indiana":0.3,
        "Wisconsin":0.3,"South Carolina":0.29,"Alabama":0.28,"Louisiana":0.27,
        "Kentucky":0.26,"Oregon":0.26,"Oklahoma":0.24,"Connecticut":0.24,
        "Utah":0.23,"Iowa":0.22,"Kansas":0.21,"Arkansas":0.2,"New Mexico":0.18,
        "Mississippi":0.17,"West Virginia":0.16,"Nebraska":0.15,"Nevada":0.15,
        "Idaho":0.14,"Hawaii":0.13,"Maine":0.12,"Montana":0.11,"Delaware":0.11,
        "Rhode Island":0.1,"North Dakota":0.09,"South Dakota":0.08,"Alaska":0.08,
        "New Hampshire":0.07,"Vermont":0.06,"Wyoming":0.05,"District of Columbia":0.05,
    }
    total_w = sum(base.values())
    profs = {k: round(v / total_w * PROFIT * rng.uniform(0.85, 1.15)) for k, v in base.items()}
    return profs

def build_map(fname):
    gj = fetch_us_states_geojson()
    profs = state_profits()
    if gj is None:
        # fallback: bar-histogram of state profits
        fig, ax = plt.subplots(figsize=(10, 5))
        names = sorted(profs, key=lambda k: -profs[k])[:25]
        vals = [profs[n] for n in names]
        style_ax(ax); fig.patch.set_facecolor("white")
        ax.bar(range(len(names)), vals, color=BLUE)
        ax.set_xticks(range(len(names))); ax.set_xticklabels(names, rotation=60, ha="right", fontsize=8)
        ax.set_title("Profit by State (top 25) – map unavailable, showing state bars instead",
                     fontsize=12, fontweight="bold", loc="left")
        watermark(ax); save(fig, fname); return

    def rings_of(geom):
        """Return list of rings (each a list of [x,y]) for Polygon/MultiPolygon."""
        t, co = geom["type"], geom["coordinates"]
        if t == "Polygon":
            return [r for r in co]
        if t == "MultiPolygon":
            out = []
            for poly in co:
                out.extend(poly)
            return out
        return []

    polys = []
    colors = []
    cmap = matplotlib.colormaps["OrRd"]
    lo, hi = min(profs.values()), max(profs.values())
    for feat in gj["features"]:
        st = feat["properties"]["name"]
        p = profs.get(st, int(hi * 0.15))
        c = cmap(0.15 + 0.75 * (p - lo) / max(hi - lo, 1))
        for ring in rings_of(feat["geometry"]):
            arr = np.asarray(ring, dtype=float)
            if arr.ndim != 2 or arr.shape[1] != 2 or arr.shape[0] < 3:
                continue
            polys.append(Polygon(arr, closed=True))
            colors.append(c)

    fig = plt.figure(figsize=(11, 6.2))
    ax = fig.add_axes([0.02, 0.05, 0.88, 0.85]); ax.set_aspect("equal"); ax.axis("off")
    fig.patch.set_facecolor("white")
    pc = PatchCollection(polys, facecolor=colors, edgecolor="white", linewidth=0.6)
    ax.add_collection(pc)
    # bounds from all polygon vertices
    xs, ys = [], []
    for p in polys:
        a = np.asarray(p.get_xy())
        if a.size:
            xs += [a[:,0].min(), a[:,0].max()]
            ys += [a[:,1].min(), a[:,1].max()]
    ax.set_xlim(min(xs), max(xs)); ax.set_ylim(min(ys), max(ys))
    ax.set_title("Regional Analysis – US States coloured by Profit", fontsize=14, fontweight="bold", color=INK, loc="left")
    sm = cm.ScalarMappable(cmap=cmap, norm=matplotlib.colors.Normalize(lo, hi))
    cb = fig.colorbar(sm, ax=ax, pad=0.02, shrink=0.85)
    cb.set_label("Profit (₹)", fontsize=9)
    watermark(ax, "REFERENCE ONLY - state colours are illustrative; build the real map in Tableau -> Geography tab")
    save(fig, fname)

import matplotlib.cm as cm
build_map("07_regional_map.png")

# =====================================================================
# 8. TOP 10 PRODUCTS BY SALES
# =====================================================================
def build_top10(fname):
    items = [
        ("Canon imageCLASS 2270 Advanced All-in-One", 185_000),
        ("Logitech Wave Speakerphone & Video Conferencing", 142_000),
        ("Epson T50 Wireless Projector", 138_000),
        ("Logitech MK330 Wireless Combo", 126_000),
        ("Lexmark X5550 Multifunction Printer", 118_000),
        ("3M Heavy Duty Stapler", 92_000),
        ("GBC DestroyIt Shredder", 84_000),
        ("Eureka Proline G25", 78_000),
        ("CUTEO 13-Page Shred Capacity Shredder", 72_000),
        ("Hewlett-Packard 2820 All-In-One", 65_000),
    ]
    items.sort(key=lambda t: t[1])
    names  = [i[0] for i in items]
    vals   = [i[1] for i in items]
    ranks  = list(range(10, 0, -1))

    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    style_ax(ax); fig.patch.set_facecolor("white")
    y = np.arange(len(names))
    bars = ax.barh(y, vals, color=BLUE)
    bars[-1].set_color(ORANGE)  # top product accent
    for yi, (n, v, r) in enumerate(zip(names, vals, ranks)):
        ax.text(v + 2500, yi, f"#{r}  ₹{v:,}", va="center", fontsize=8.5, color=INK, fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=9.5)
    ax.set_xlabel("Sales (₹)")
    ax.set_xlim(0, max(vals) * 1.35)
    ax.xaxis.set_major_formatter(matplotlib.ticker.StrMethodFormatter("₹{x:,.0f}"))
    ax.set_title("Top 10 Products by Sales", fontsize=14, fontweight="bold", color=INK, loc="left")
    watermark(ax)
    save(fig, fname)

build_top10("08_top10_products.png")

# =====================================================================
# 9. FULL DASHBOARD COMPOSITE
# =====================================================================
def build_dashboard(fname):
    vals = monthly_series(SALES)
    xlab = labels_2018_2021()

    subs = [
        ("Furniture / Chairs",        280_000,  41_000),
        ("Furniture / Furnishing",    240_000,  33_000),
        ("Furniture / Tables",        310_000,  15_000),
        ("Office Supplies / Binders", 230_000,  38_000),
        ("Office Supplies / Paper",   190_000,  24_000),
        ("Office Supplies / Storage", 250_000,  35_000),
        ("Office Supplies / Supplies",140_000,  12_000),
        ("Technology / Accessories",  130_000,  25_000),
        ("Technology / Copiers",      270_000,  62_000),
        ("Technology / Phones",       257_201,  41_397),
    ]
    s_sum = sum(x[1] for x in subs); p_sum = sum(x[2] for x in subs)
    subs  = [(n, round(s*SALES/s_sum), round(p*PROFIT/p_sum)) for (n,s,p) in subs]

    top_items = [
        ("Canon imageCLASS 2270 Advanced All-in-One", 185_000),
        ("Logitech Wave Speakerphone & Video Conf.",  142_000),
        ("Epson T50 Wireless Projector", 138_000),
        ("Logitech MK330 Wireless Combo", 126_000),
        ("Lexmark X5550 Multifunction Printer", 118_000),
    ]
    top_items.sort(key=lambda t: t[1])

    fig = plt.figure(figsize=(15, 9))
    fig.patch.set_facecolor(BG)

    # header strip
    fig.text(0.02, 0.965, "Superstore Business Insights Dashboard",
             fontsize=22, fontweight="bold", color=INK)
    fig.text(0.02, 0.935, "Reference composite – 2018 to 2021 | Built from report figures, not live Tableau",
             fontsize=10, color=GREY)

    def kpi_box(pos, title, big, accent):
        ax = fig.add_axes(pos); ax.axis("off")
        ax.set_xlim(0, 100); ax.set_ylim(0, 100)
        ax.add_patch(FancyBboxPatch((0,0), 100, 100, boxstyle="round,pad=1,rounding_size=4",
                                    linewidth=0, facecolor="white"))
        ax.add_patch(Rectangle((0,0), 3, 100, facecolor=accent, edgecolor="none"))
        ax.text(8, 80, title, fontsize=11, color=GREY, fontweight="bold")
        ax.text(8, 40, big, fontsize=22, color=INK, fontweight="bold")

    kpi_box([0.02, 0.82, 0.18, 0.09], "TOTAL SALES",  "₹ 22,97,201", ORANGE)
    kpi_box([0.21, 0.82, 0.18, 0.09], "TOTAL PROFIT", "₹ 2,86,397",  BLUE)
    kpi_box([0.40, 0.82, 0.18, 0.09], "TOTAL QUANTITY","37,873",       INK)
    kpi_box([0.59, 0.82, 0.18, 0.09], "PROFIT MARGIN", "12.5%",       "#0E9F6E")

    # monthly trend – wide top-left
    ax = fig.add_axes([0.02, 0.42, 0.55, 0.36])
    style_ax(ax)
    ax.fill_between(range(48), vals, 0, color=ORANGE, alpha=0.2)
    ax.plot(range(48), vals, color=ORANGE, linewidth=2, marker="o", ms=2.5)
    ax.axhline(vals.mean(), color=BLUE, ls="--", lw=1.2)
    step = 4
    ax.set_xticks(range(0, 48, step)); ax.set_xticklabels([xlab[i] for i in range(0,48,step)],
                                                           rotation=45, ha="right", fontsize=7)
    ax.set_title("Monthly Sales Trend (2018–2021)", fontsize=11, fontweight="bold", loc="left")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,p: f"₹{v/1000:.0f}k"))

    # sub-category bars
    ax = fig.add_axes([0.62, 0.42, 0.36, 0.36])
    style_ax(ax)
    x = np.arange(len(subs)); w = 0.36
    ax.bar(x - w/2, [s[1] for s in subs], w, color=ORANGE, label="Sales")
    ax.bar(x + w/2, [s[2] for s in subs], w, color=BLUE,   label="Profit")
    ax.set_xticks(x); ax.set_xticklabels([s[0].split(" / ")[1] for s in subs],
                                         rotation=40, ha="right", fontsize=7.5)
    ax.set_title("Sales & Profit by Sub-Category", fontsize=11, fontweight="bold", loc="left")
    ax.legend(frameon=False, fontsize=8)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,p: f"₹{v/1000:.0f}k"))

    # top 10 products
    ax = fig.add_axes([0.02, 0.05, 0.45, 0.32])
    style_ax(ax)
    y = np.arange(len(top_items))
    ax.barh(y, [v for _, v in top_items], color=BLUE)
    ax.barh(y, [v for _, v in top_items], color=BLUE, alpha=0.55)
    for yi, (n, v) in enumerate(reversed(top_items)):
        pass
    for i, (n, v) in enumerate(top_items):
        ax.text(v + 2000, i, f"₹{v:,}", va="center", fontsize=8)
    ax.set_yticks(y); ax.set_yticklabels([n for n,_ in top_items], fontsize=8.5)
    ax.set_title("Top 5 Products by Sales (full Top-10 in sheet #8)", fontsize=11, fontweight="bold", loc="left")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,p: f"₹{v/1000:.0f}k"))

    # placeholder for the state map in bottom-right
    ax = fig.add_axes([0.50, 0.05, 0.48, 0.32])
    ax.axis("off"); ax.set_xlim(0,100); ax.set_ylim(0,100)
    ax.add_patch(FancyBboxPatch((0,0), 100, 100, boxstyle="round,pad=0.6,rounding_size=2",
                                linewidth=0, facecolor="white"))
    ax.text(5, 90, "Regional Map (US by Profit)", fontsize=11, fontweight="bold", color=INK)
    ax.text(5, 55, "See 07_regional_map.png\nfor the full 48-state choropleth",
            fontsize=10, color=GREY, va="top")
    ax.text(5, 20, "Sample values: CA ₹56k | TX ₹45k | FL ₹39k | NY ₹37k",
            fontsize=8.5, color=GREY)

    watermark(ax, "REFERENCE ONLY composite. Build the real dashboard in Tableau -> Sample Superstore.")
    fig.savefig(os.path.join(OUT, fname), dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close(fig)
    print("wrote", os.path.join(OUT, fname))

build_dashboard("09_full_dashboard.png")

print("\nALL 9 DONE ->", OUT)
