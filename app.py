
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import date, timedelta

st.set_page_config(page_title="Stock Potential Scanner IDX", page_icon="📈", layout="wide")

# -----------------------------
# Universe IDX (starter universe)
# -----------------------------
UNIVERSE = {
    "Banking": ["BBCA","BBRI","BMRI","BBNI","BRIS","BBTN","BDMN","BNGA","BSIM","NISP"],
    "Energy": ["ADRO","AADI","PTBA","ITMG","INDY","MEDC","PGAS","AKRA"],
    "Basic Materials": ["ANTM","INCO","MDKA","SMGR","INTP","TKIM","INKP","BRPT","TPIA"],
    "Consumer": ["ICBP","INDF","MYOR","UNVR","KLBF","SIDO","GGRM","HMSP","AMRT"],
    "Telecommunication": ["TLKM","ISAT","EXCL","MTEL"],
    "Infrastructure": ["JSMR","WIKA","WSKT","PTPP","ADHI","ACST"],
    "Property": ["BSDE","CTRA","PWON","SMRA","DMAS","ASRI"],
    "Automotive": ["ASII","AUTO","GJTL","IMAS"],
    "Technology": ["GOTO","EMTK","BUKA","DCII","MTDL"],
    "Healthcare": ["MIKA","SILO","HEAL","TSPC"],
    "Plantation": ["AALI","LSIP","SIMP","DSNG","SSMS"],
    "Industrial": ["UNTR","GGRP","SMDR","ASSA","MAPI"],
}
TICKER_TO_SECTOR = {t: s for s, xs in UNIVERSE.items() for t in xs}
ALL_TICKERS = list(TICKER_TO_SECTOR.keys())

# -----------------------------
# Indicators
# -----------------------------
def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def macd(series):
    e12 = series.ewm(span=12, adjust=False).mean()
    e26 = series.ewm(span=26, adjust=False).mean()
    line = e12 - e26
    signal = line.ewm(span=9, adjust=False).mean()
    hist = line - signal
    return line, signal, hist

def atr(df, period=14):
    high_low = df["High"] - df["Low"]
    high_close = (df["High"] - df["Close"].shift()).abs()
    low_close = (df["Low"] - df["Close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False).mean()

def indicators(df):
    d = df.copy()
    d["MA20"] = d["Close"].rolling(20).mean()
    d["MA50"] = d["Close"].rolling(50).mean()
    d["MA200"] = d["Close"].rolling(200).mean()
    d["RSI"] = rsi(d["Close"])
    d["MACD"], d["MACDSignal"], d["MACDHist"] = macd(d["Close"])
    d["ATR"] = atr(d)
    d["Vol20"] = d["Volume"].rolling(20).mean()
    d["VolRatio"] = d["Volume"] / d["Vol20"]
    d["High20"] = d["High"].rolling(20).max().shift(1)
    d["Low20"] = d["Low"].rolling(20).min().shift(1)
    return d

# -----------------------------
# Scoring
# -----------------------------
def score_stock(d):
    x = d.iloc[-1]
    prev = d.iloc[-2]
    close = float(x["Close"])
    score = 0
    notes = []

    # Trend 25
    trend = 0
    if close > x["MA20"]: trend += 7
    if close > x["MA50"]: trend += 7
    if pd.notna(x["MA200"]) and close > x["MA200"]: trend += 6
    if x["MA20"] > x["MA50"]: trend += 5
    score += trend
    if trend >= 18: notes.append("Trend kuat")

    # Momentum 20
    mom = 0
    if 50 <= x["RSI"] <= 70: mom += 8
    elif 45 <= x["RSI"] < 50: mom += 4
    if x["MACD"] > x["MACDSignal"]: mom += 7
    if x["MACDHist"] > prev["MACDHist"]: mom += 5
    score += mom

    # Volume 15
    vol = 0
    if x["VolRatio"] >= 1.5: vol = 15
    elif x["VolRatio"] >= 1.2: vol = 11
    elif x["VolRatio"] >= 1.0: vol = 7
    elif x["VolRatio"] >= 0.8: vol = 4
    score += vol

    # Breakout / pullback setup 20
    setup_score = 0
    if pd.notna(x["High20"]) and close > x["High20"]:
        setup_score = 20
        notes.append("Breakout 20D")
    elif pd.notna(x["MA20"]) and close >= x["MA20"] * 0.98 and close <= x["MA20"] * 1.03:
        setup_score = 15
        notes.append("Pullback MA20")
    elif pd.notna(x["MA50"]) and close >= x["MA50"] * 0.98 and close <= x["MA50"] * 1.04:
        setup_score = 12
        notes.append("Pullback MA50")
    elif pd.notna(x["Low20"]) and close <= x["Low20"] * 1.06:
        setup_score = 5
        notes.append("Dekat support")
    score += setup_score

    # Relative strength proxy 10: 20D return
    ret20 = d["Close"].pct_change(20).iloc[-1]
    rs = 0
    if ret20 >= 0.15: rs = 10
    elif ret20 >= 0.08: rs = 8
    elif ret20 >= 0.03: rs = 6
    elif ret20 >= 0: rs = 3
    score += rs

    # Quality/price behavior 10
    q = 0
    if close > x["MA50"]: q += 5
    if d["Close"].iloc[-1] > d["Close"].iloc[-21]: q += 5
    score += q

    if score >= 85:
        action = "🟢 STRONG BUY CANDIDATE"
    elif score >= 75:
        action = "🟢 BUY / ACCUMULATE"
    elif score >= 65:
        action = "🟡 BUY ON PULLBACK / WATCH"
    elif score >= 50:
        action = "🔵 WATCH"
    else:
        action = "🔴 AVOID"

    atrv = float(x["ATR"]) if pd.notna(x["ATR"]) else close * 0.03
    # Risk plan: 1.5 ATR stop; targets 2R and 3R
    stop = close - 1.5 * atrv
    risk = close - stop
    tp1 = close + 2 * risk
    tp2 = close + 3 * risk

    if pd.notna(x["High20"]) and close > x["High20"]:
        setup = "BREAKOUT"
        entry_low = close * 0.99
        entry_high = close * 1.01
    elif pd.notna(x["MA20"]):
        setup = "PULLBACK"
        entry_low = x["MA20"] * 0.99
        entry_high = x["MA20"] * 1.02
    else:
        setup = "WATCH"
        entry_low = close * 0.98
        entry_high = close * 1.02

    return {
        "Score": int(min(100, max(0, round(score)))),
        "Action": action,
        "Setup": setup,
        "Price": close,
        "Entry Low": entry_low,
        "Entry High": entry_high,
        "Stop Loss": stop,
        "TP1": tp1,
        "TP2": tp2,
        "RSI": x["RSI"],
        "MACD Hist": x["MACDHist"],
        "Vol Ratio": x["VolRatio"],
        "Return 20D": ret20,
        "MA20": x["MA20"],
        "MA50": x["MA50"],
        "MA200": x["MA200"],
        "Notes": ", ".join(notes) if notes else "Belum ada setup kuat"
    }

@st.cache_data(ttl=900, show_spinner=False)
def load_prices(tickers, period="1y"):
    symbols = [t + ".JK" for t in tickers]
    raw = yf.download(symbols, period=period, interval="1d", auto_adjust=False,
                      group_by="ticker", threads=True, progress=False)
    result = {}
    if raw.empty:
        return result
    for t in tickers:
        sym = t + ".JK"
        try:
            if len(tickers) == 1:
                d = raw.copy()
            else:
                d = raw[sym].copy()
            d = d.dropna(subset=["Close"])
            if len(d) >= 220:
                result[t] = indicators(d)
        except Exception:
            pass
    return result

def sector_score(rows):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    out = []
    for sector, g in df.groupby("Sector"):
        out.append({
            "Sector": sector,
            "Avg Score": g["Score"].mean(),
            "Avg 20D Return": g["Return 20D"].mean(),
            "Bullish %": (g["Score"] >= 65).mean() * 100,
            "Stocks": len(g)
        })
    return pd.DataFrame(out).sort_values(["Avg Score","Avg 20D Return"], ascending=False)

# -----------------------------
# UI
# -----------------------------
st.title("📈 Stock Potential Scanner IDX — v1.0")
st.caption("Top-down: Market → Sector → Stock → Setup → Risk/Reward. Data harga diambil saat aplikasi dijalankan.")

with st.sidebar:
    st.header("⚙️ Pengaturan")
    max_stocks = st.slider("Jumlah saham dianalisis", 10, len(ALL_TICKERS), min(50, len(ALL_TICKERS)))
    min_score = st.slider("Minimum score", 0, 100, 65)
    period = st.selectbox("Periode data", ["1y", "2y", "5y"], index=0)
    selected_sector = st.multiselect("Filter sektor", list(UNIVERSE.keys()))
    if not selected_sector:
        tickers = ALL_TICKERS[:max_stocks]
    else:
        tickers = [t for t in ALL_TICKERS if TICKER_TO_SECTOR[t] in selected_sector][:max_stocks]
    refresh = st.button("🔄 Refresh data")

if refresh:
    st.cache_data.clear()
    st.rerun()

st.info("Catatan: ini adalah alat bantu analisis, bukan rekomendasi investasi. Foreign flow dan fundamental belum ditarik otomatis pada versi 1.0; keduanya akan menjadi modul berikutnya.")

with st.spinner("Mengambil data harga dan menghitung indikator..."):
    prices = load_prices(tuple(tickers), period)

rows = []
for t, d in prices.items():
    try:
        s = score_stock(d)
        s["Ticker"] = t
        s["Sector"] = TICKER_TO_SECTOR.get(t, "Other")
        rows.append(s)
    except Exception:
        pass

stock_df = pd.DataFrame(rows)
if stock_df.empty:
    st.error("Data tidak berhasil diperoleh. Coba Refresh, periksa koneksi internet, atau kurangi jumlah saham.")
    st.stop()

stock_df = stock_df.sort_values("Score", ascending=False).reset_index(drop=True)

# Market proxy using average return of analyzed universe
market_ret20 = stock_df["Return 20D"].mean()
market_score = int(np.clip(50 + market_ret20 * 200, 20, 90))
market_regime = "🟢 BULLISH" if market_score >= 65 else ("🟡 SIDEWAYS" if market_score >= 45 else "🔴 BEARISH")

c1,c2,c3,c4 = st.columns(4)
c1.metric("Market Proxy Score", market_score)
c2.metric("Market Regime", market_regime)
c3.metric("Saham Dianalisis", len(stock_df))
c4.metric("Kandidat ≥ Score", int((stock_df["Score"] >= min_score).sum()))

st.subheader("🏆 Ranking Sector")
sec = sector_score(stock_df.to_dict("records"))
if not sec.empty:
    sec_display = sec.copy()
    sec_display["Avg Score"] = sec_display["Avg Score"].round(1)
    sec_display["Avg 20D Return"] = (sec_display["Avg 20D Return"]*100).round(2).astype(str) + "%"
    sec_display["Bullish %"] = sec_display["Bullish %"].round(0).astype(int).astype(str) + "%"
    st.dataframe(sec_display, use_container_width=True, hide_index=True)

st.subheader("🔥 Top Potential Stocks")
cols = ["Ticker","Sector","Score","Action","Setup","Price","Entry Low","Entry High","Stop Loss","TP1","TP2","RSI","Vol Ratio","Return 20D","Notes"]
view = stock_df[cols].copy()
for c in ["Price","Entry Low","Entry High","Stop Loss","TP1","TP2"]:
    view[c] = view[c].round(0)
view["RSI"] = view["RSI"].round(1)
view["Vol Ratio"] = view["Vol Ratio"].round(2)
view["Return 20D"] = (view["Return 20D"]*100).round(2).astype(str) + "%"
st.dataframe(view[view["Score"] >= min_score], use_container_width=True, hide_index=True)

st.subheader("🔎 Detail Saham")
chosen = st.selectbox("Pilih saham", stock_df["Ticker"].tolist())
detail = stock_df[stock_df["Ticker"] == chosen].iloc[0]

a,b,c,d,e = st.columns(5)
a.metric("Score", int(detail["Score"]))
b.metric("Setup", detail["Setup"])
c.metric("Harga", f"Rp {detail['Price']:,.0f}")
d.metric("RSI", f"{detail['RSI']:.1f}")
e.metric("20D Return", f"{detail['Return 20D']*100:.2f}%")

st.markdown(f"### {chosen} — {detail['Action']}")
st.write(f"**Sektor:** {detail['Sector']}  |  **Setup:** {detail['Setup']}  |  **Catatan:** {detail['Notes']}")

plan = pd.DataFrame({
    "Parameter": ["Buy Zone Low","Buy Zone High","Stop Loss","TP1 (2R)","TP2 (3R)","Risk/Reward to TP1"],
    "Value": [
        f"Rp {detail['Entry Low']:,.0f}",
        f"Rp {detail['Entry High']:,.0f}",
        f"Rp {detail['Stop Loss']:,.0f}",
        f"Rp {detail['TP1']:,.0f}",
        f"Rp {detail['TP2']:,.0f}",
        "1 : 2"
    ]
})
st.table(plan)

st.caption("Metodologi score: trend 25%, momentum 20%, volume 15%, setup 20%, relative strength 10%, quality/price behavior 10%. Formula dapat diubah pada kode aplikasi.")
