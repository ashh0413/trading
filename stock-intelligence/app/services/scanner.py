"""Screening scanner: evaluates watchlist stocks against configurable rules.
Screening signals only — not trading advice, not profit probabilities.

Statuses: MATCH, PARTIAL, NO_MATCH, INSUFFICIENT_DATA, DATA_UNAVAILABLE.
Score = number of conditions satisfied (max 3 in default config).
"""
from .indicators import compute_all

DEFAULT_CONDITIONS = {
    "momentum_rsi": {"low": 50.0, "high": 70.0},
    "momentum_macd_above_signal": True,
    "trend_close_above_sma20": True,
    "trend_sma20_above_sma50": True,
    "volume_above_avg": True,
}


def evaluate_symbol(symbol: str, candles, source: str,
                    conditions: dict | None = None) -> dict:
    conds = {**DEFAULT_CONDITIONS, **(conditions or {})}
    base = {"symbol": symbol, "source": source}
    ind = compute_all(candles)
    if ind["status"] == "INSUFFICIENT_DATA":
        return {**base, **ind, "status": "INSUFFICIENT_DATA", "checks": [], "score": 0}

    checks = []

    def add(name, ok, detail):
        checks.append({"name": name, "passed": bool(ok), "detail": detail})
        return bool(ok)

    rsi_v = ind["rsi_14"]
    lo, hi = conds["momentum_rsi"]["low"], conds["momentum_rsi"]["high"]
    ok = rsi_v is not None and lo <= rsi_v <= hi
    checks.append({"name": "momentum_rsi", "passed": ok,
                   "detail": f"RSI {rsi_v} in [{lo}, {hi}]"})

    m, s, h = ind["macd"], ind["macd_signal"], ind["macd_hist"]
    ok = conds["momentum_macd_above_signal"] and m is not None and m > s
    checks.append({"name": "momentum_macd_above_signal", "passed": ok,
                   "detail": f"MACD {m} vs signal {s}"})

    close_v, sma20, sma50 = ind["last_close"], ind["sma_20"], ind["sma_50"]
    ok = conds["trend_close_above_sma20"] and close_v is not None and sma20 is not None \
        and close_v > sma20
    checks.append({"name": "trend_close_above_sma20", "passed": ok,
                   "detail": f"close {close_v} vs SMA20 {sma20}"})

    ok = (conds["trend_sma20_above_sma50"] and sma20 is not None and sma50 is not None
          and sma20 > sma50)
    checks.append({"name": "trend_sma20_above_sma50", "passed": ok,
                   "detail": f"SMA20 {sma20} vs SMA50 {sma50}"})

    rv = ind["relative_volume"]
    ok = conds["volume_above_avg"] and rv is not None and rv > 1.0
    checks.append({"name": "volume_above_avg", "passed": ok,
                   "detail": f"relative volume {rv} (>1.0)"})

    score = sum(1 for c in checks if c["passed"])
    max_score = len(checks)
    if score == max_score:
        status = "MATCH"
    elif score >= max_score // 2:
        status = "PARTIAL"
    else:
        status = "NO_MATCH"

    return {**base, **{k: v for k, v in ind.items() if k != "status"},
            "status": status, "score": score, "max_score": max_score, "checks": checks}


def scan_all(provider, symbols: list, conditions: dict | None = None,
             period_days: int = 365) -> list:
    results = []
    for sym in symbols:
        try:
            candles = provider.get_candles(sym, period_days=period_days)
            res = evaluate_symbol(sym, candles, source=provider.name, conditions=conditions)
        except Exception as e:  # contain per-symbol failures; never invent data
            res = {"symbol": sym, "source": provider.name, "status": "DATA_UNAVAILABLE",
                   "error": str(e), "score": 0, "checks": []}
        results.append(res)
    results.sort(key=lambda r: r.get("score", 0), reverse=True)
    return results
