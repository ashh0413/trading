"""Streamlit dashboard: overview, scanner, details, watchlist, settings."""
import sys
from pathlib import Path

import httpx
import plotly.express as px
import streamlit as st

API = st.query_params.get("api", "http://127.0.0.1:8000")
ROOT = Path(__file__).resolve().parents[2]


def get(path, params=None):
    r = httpx.get(f"{API}{path}", params=params, timeout=60)
    return r


@st.cache_data(ttl=300)
def health():
    r = get("/health")
    return r.json() if r.status_code == 200 else {"ok": False, "error": r.text}


@st.cache_data(ttl=300)
def scan():
    r = get("/scanner")
    if r.status_code != 200:
        return {"error": r.text, "results": []}
    return {"error": None, "results": r.json()}


st.set_page_config(page_title="Stock Intelligence", layout="wide")
pg = st.sidebar.radio("Page", ["Market Overview", "Scanner",
                               "Stock Details", "Watchlist", "Settings"])

if pg == "Market Overview":
    h = health()
    st.title("Market Overview")
    st.subheader("Provider")
    st.json(h)
    if not h.get("ok"):
        st.error(f"API not reachable: {API}. Start it: uvicorn app.main:app")
    results = scan()["results"]
    ok = [r for r in results if r["status"] != "DATA_UNAVAILABLE"]
    st.metric("Stocks scanned", len(ok))
    st.metric("Full/partial matches",
              sum(1 for r in ok if r["status"] in ("MATCH", "PARTIAL")))
    stale = [r for r in ok if not r.get("data_timestamp")]
    if stale:
        st.warning(f"{len(stale)} stocks returned no data — check provider mode.")
    if h.get("provider") == "MOCK":
        st.info("MOCK provider — synthetic data, for testing only.")

elif pg == "Scanner":
    st.title("Stock Scanner")
    res = scan()["results"]
    res = [r for r in res if r["status"] != "DATA_UNAVAILABLE"]
    min_score = st.sidebar.slider("Min score", 0, 3, 0)
    res = [r for r in res if r["score"] >= min_score]
    for r in res:
        with st.expander(f"{r['symbol']} — {r['status']} ({r['score']}/{r['max_score']})"):
            st.write(f"Close {r['last_close']} | RSI {r['rsi_14']} | "
                     f"MACD {r['macd']} vs {r['macd_signal']} | RVol {r['relative_volume']}")
            for c in r["checks"]:
                mark = "PASS" if c["passed"] else "fail"
                st.text(f"  [{mark}] {c['detail']}")
            if r.get("data_timestamp"):
                st.caption(f"data as of {r['data_timestamp']} ({r['source']})")

elif pg == "Stock Details":
    st.title("Stock Details")
    res = scan()["results"]
    sym = st.selectbox("Symbol", sorted(r["symbol"] for r in res))
    r = get(f"/scanner/{sym}").json()
    c = get(f"/market-data/{sym}").json()
    rows = c.get("rows") or []
    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)
        fig = px.line(df, x="date", y="close", title=f"{sym} close")
        st.plotly_chart(fig, use_container_width=True)
        st.plotly_chart(
            px.bar(df.tail(30), x="date", y="volume", title="Volume"),
            use_container_width=True)
        st.dataframe(r, use_container_width=True)
        st.caption(f"source: {r.get('source')} as of {r.get('data_timestamp')}")
    else:
        st.error("No candle data returned.")

elif pg == "Watchlist":
    st.title("Watchlist")
    wl = get("/watchlist").json()
    st.write(wl)
    add = st.text_input("Add symbol")
    if st.button("Add") and add:
        r = httpx.post(f"{API}/watchlist", json={"symbol": add})
        st.write(r.status_code, r.text)
        st.cache_data.clear()
    for s in list(wl):
        if st.button(f"Remove {s}"):
            httpx.delete(f"{API}/watchlist/{s}")
            st.cache_data.clear()
            st.rerun()

elif pg == "Settings":
    st.title("Settings")
    st.json(get("/config").json())
    st.markdown(
        "**Provider** — set `PROVIDER=UPSTOX` in `.env` with "
        "`UPSTOX_API_KEY`, `UPSTOX_API_SECRET`, `UPSTOX_ACCESS_TOKEN`, "
        "then restart the API.\n\n"
        "**Token expired?** Regenerate at upstox.com/developer dashboard, "
        "update `.env`, restart. Do not paste tokens into chat.")
