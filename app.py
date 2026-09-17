import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# ============================================================
# SANGGUL STOCK SCANNER V10.2
# STYLE-SPECIFIC SCORING + RISK GATE + MULTI-PERIOD
# Daily / Swing Weekly / Long-Term Investor
# ============================================================

st.set_page_config(
    page_title="Sanggul Stock Scanner V10.2",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# STYLE / THEME
# -----------------------------
st.markdown("""
<style>
:root {
    --ink:#152238;
    --muted:#64748b;
    --line:#e2e8f0;
    --soft:#f8fafc;
    --blue:#2563eb;
    --green:#059669;
    --orange:#d97706;
    --red:#dc2626;
}
.block-container {padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1500px;}
h1,h2,h3 {color:var(--ink);}
[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 12px 14px;
}
div[data-testid="stVerticalBlock"] div.stButton > button {
    border-radius: 10px;
}
.small-note {color:var(--muted); font-size:0.85rem;}
.card {
    border:1px solid var(--line);
    border-radius:16px;
    padding:16px;
    background:white;
    margin-bottom:10px;
}
.card-title {font-weight:700; font-size:1.1rem; color:var(--ink);}
.pill {
    display:inline-block; padding:4px 9px; border-radius:999px;
    font-size:0.75rem; font-weight:700; margin-top:5px;
}
.pass {background:#dcfce7;color:#166534;}
.caution {background:#fef3c7;color:#92400e;}
.fail {background:#fee2e2;color:#991b1b;}
.neutral {background:#e2e8f0;color:#334155;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# CONSTANTS
# -----------------------------
IDX_UNIVERSE_URL = (
    "https://huggingface.co/datasets/"
    "kjhq/Indonesia-Stock-Symbols-and-Metadata/"
    "resolve/main/indonesia.csv"
)

PERIODS = {
    "1 Bulan": "1mo",
    "3 Bulan": "3mo",
    "6 Bulan": "6mo",
    "2 Tahun": "2y",
}

STYLE_INFO = {
    "Trading Harian": {
        "icon": "⚡",
        "horizon": "1–5 hari",
        "subtitle": "Momentum pendek, likuiditas, volume, dan pergerakan cepat.",
    },
    "Swing Trading Mingguan": {
        "icon": "📊",
        "horizon": "1–8 minggu",
        "subtitle": "Kelanjutan tren menengah, pullback, breakout, dan R:R.",
    },
    "Investor Jangka Panjang": {
        "icon": "🌱",
        "horizon": "6 bulan+",
        "subtitle": "Tren panjang, MA200, konsistensi return, dan drawdown.",
    },
}

# -----------------------------
# HELPERS
# -----------------------------
def rupiah(x):
    try:
        if pd.isna(x):
            return "-"
        return "Rp " + f"{float(x):,.0f}".replace(",", ".")
    except Exception:
        return "-"

def pct(x):
    try:
        if pd.isna(x):
            return "-"
        return f"{float(x):.2f}%"
    except Exception:
        return "-"

def num(x, digits=2):
    try:
        if pd.isna(x):
            return "-"
        return f"{float(x):.{digits}f}"
    except Exception:
        return "-"

def yahoo_symbol(ticker):
    ticker = str(ticker).upper().strip()
    return ticker if ticker.endswith(".JK") else ticker + ".JK"

def gate_badge(gate):
    cls = {"PASS":"pass", "CAUTION":"caution", "FAIL":"fail"}.get(gate, "neutral")
    return f'<span class="pill {cls}">{gate}</span>'

def safe_float(v, default=0.0):
    try:
        if pd.isna(v):
            return default
        return float(v)
    except Exception:
        return default

# -----------------------------
# DATA
# -----------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def load_universe():
    try:
        df = pd.read_csv(IDX_UNIVERSE_URL)
        df.columns = [str(c).lower().strip() for c in df.columns]
        required = {"ticker", "name", "sector"}
        if not required.issubset(df.columns):
            return pd.DataFrame()
        if "market" in df.columns:
            df = df[df["market"].astype(str).str.upper().eq("IDX")].copy()
        df["ticker"] = (
            df["ticker"].astype(str).str.upper().str.strip()
            .str.replace(".JK", "", regex=False)
        )
        df = df[df["ticker"].str.fullmatch(r"[A-Z]{4}", na=False)]
        df = df.drop_duplicates("ticker").copy()
        df["Yahoo"] = df["ticker"] + ".JK"
        return df.sort_values("ticker").reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def download_history(ticker, period="2y"):
    try:
        d = yf.download(
            yahoo_symbol(ticker),
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
        if d is None or d.empty:
            return pd.DataFrame()
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = d.columns.get_level_values(0)
        d.columns = [str(c).title() for c in d.columns]
        for c in ["Open", "High", "Low", "Close", "Volume"]:
            if c in d.columns:
                d[c] = pd.to_numeric(d[c], errors="coerce")
        needed = ["Open", "High", "Low", "Close"]
        if not set(needed).issubset(d.columns):
            return pd.DataFrame()
        return d.dropna(subset=needed).copy()
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def download_many(tickers, period="2y"):
    # Reliable sequential fallback; easier to diagnose than fragile batch formats.
    rows = {}
    for ticker in list(tickers):
        d = download_history(ticker, period=period)
        if not d.empty:
            rows[ticker] = d
    return rows

# -----------------------------
# INDICATORS
# -----------------------------
def add_indicators(d):
    x = d.copy()
    close = x["Close"]
    x["MA5"] = close.rolling(5).mean()
    x["MA20"] = close.rolling(20).mean()
    x["MA50"] = close.rolling(50).mean()
    x["MA100"] = close.rolling(100).mean()
    x["MA200"] = close.rolling(200).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    x["MACD"] = ema12 - ema26
    x["MACDSignal"] = x["MACD"].ewm(span=9, adjust=False).mean()

    prev_close = close.shift(1)
    tr = pd.concat([
        x["High"] - x["Low"],
        (x["High"] - prev_close).abs(),
        (x["Low"] - prev_close).abs(),
    ], axis=1).max(axis=1)
    x["ATR"] = tr.rolling(14).mean()
    x["ATRPct"] = (x["ATR"] / close) * 100

    if "Volume" in x.columns:
        x["VolumeMA20"] = x["Volume"].rolling(20).mean()
        x["VolumeRatio"] = x["Volume"] / x["VolumeMA20"]
    else:
        x["VolumeRatio"] = np.nan

    x["High20"] = x["High"].rolling(20).max()
    x["Low20"] = x["Low"].rolling(20).min()
    x["High60"] = x["High"].rolling(60).max()
    x["Low60"] = x["Low"].rolling(60).min()

    return x

def return_n(close, n):
    if len(close) <= n:
        return np.nan
    return (close.iloc[-1] / close.iloc[-n-1] - 1) * 100

def compute_metrics(ticker, d, name="", sector=""):
    if d.empty or len(d) < 30:
        return None

    x = add_indicators(d)
    last = x.iloc[-1]
    close = safe_float(last["Close"])
    if close <= 0:
        return None

    r1m = return_n(x["Close"], 21)
    r3m = return_n(x["Close"], 63)
    r6m = return_n(x["Close"], 126)
    r2y = return_n(x["Close"], min(504, len(x)-1))

    ma20 = safe_float(last["MA20"], close)
    ma50 = safe_float(last["MA50"], close)
    ma100 = safe_float(last["MA100"], close)
    ma200 = safe_float(last["MA200"], close)
    rsi = safe_float(last["RSI"], 50)
    vr = safe_float(last["VolumeRatio"], 1)
    atr_pct = safe_float(last["ATRPct"], 0)
    high20 = safe_float(last["High20"], close)
    low20 = safe_float(last["Low20"], close)
    high60 = safe_float(last["High60"], close)
    low60 = safe_float(last["Low60"], close)

    trend_short = (
        (close > ma20) * 1 +
        (ma20 > ma50) * 1 +
        (safe_float(last["MACD"]) > safe_float(last["MACDSignal"])) * 1
    )
    trend_long = (
        (close > ma50) * 1 +
        (close > ma200) * 1 +
        (ma50 > ma200) * 1 if ma200 > 0 else 0
    )

    breakout20 = close >= high20 * 0.985 if high20 > 0 else False
    pullback_ma20 = abs(close / ma20 - 1) <= 0.04 if ma20 > 0 else False
    near_high60 = close >= high60 * 0.92 if high60 > 0 else False

    # -----------------------------
    # STYLE-SPECIFIC SCORES
    # -----------------------------
    # Daily: short momentum + volume + volatility + price action
    daily = 0
    daily += 25 * np.clip((safe_float(r1m, 0) + 10) / 25, 0, 1)
    daily += 20 * np.clip((vr - 0.7) / 1.8, 0, 1)
    daily += 20 * (1 if breakout20 else (0.55 if near_high60 else 0.2))
    daily += 15 * np.clip((atr_pct - 1.0) / 5.0, 0, 1)
    daily += 10 * (1 if 50 <= rsi <= 75 else (0.6 if 40 <= rsi < 50 else 0.25))
    daily += 10 * (1 if trend_short >= 2 else (0.5 if trend_short == 1 else 0))
    daily = float(np.clip(daily, 0, 100))

    # Swing: 1M/3M/6M trend + MA structure + breakout/pullback + risk/reward
    swing = 0
    swing += 20 * np.clip((safe_float(r1m, 0) + 12) / 30, 0, 1)
    swing += 20 * np.clip((safe_float(r3m, 0) + 20) / 50, 0, 1)
    swing += 20 * (trend_short / 3)
    swing += 15 * (1 if (breakout20 or pullback_ma20) else 0.35)
    swing += 10 * (1 if 45 <= rsi <= 72 else 0.4)
    swing += 10 * np.clip((safe_float(r6m, 0) + 20) / 50, 0, 1)
    swing += 5 * np.clip((vr - 0.8) / 1.2, 0, 1)
    swing = float(np.clip(swing, 0, 100))

    # Investor: 6M/2Y + MA200 + drawdown proxy + stability
    rolling_high = x["Close"].rolling(min(252, len(x))).max().iloc[-1]
    drawdown = ((close / rolling_high) - 1) * 100 if rolling_high else 0
    investor = 0
    investor += 25 * np.clip((safe_float(r6m, 0) + 20) / 60, 0, 1)
    investor += 25 * np.clip((safe_float(r2y, 0) + 30) / 100, 0, 1)
    investor += 20 * (trend_long / 3)
    investor += 15 * (1 if close > ma200 and ma200 > 0 else 0.25)
    investor += 10 * np.clip((drawdown + 35) / 35, 0, 1)
    investor += 5 * (1 if 40 <= rsi <= 75 else 0.5)
    investor = float(np.clip(investor, 0, 100))

    # Risk gates intentionally differ by style.
    daily_gate = "PASS"
    if vr < 0.55 or atr_pct > 9 or daily < 55:
        daily_gate = "FAIL"
    elif vr < 0.85 or rsi > 80 or daily < 68:
        daily_gate = "CAUTION"

    swing_gate = "PASS"
    if swing < 55 or trend_short == 0 or safe_float(r3m, 0) < -18:
        swing_gate = "FAIL"
    elif swing < 70 or not (close > ma50 if ma50 else True):
        swing_gate = "CAUTION"

    investor_gate = "PASS"
    if investor < 55 or safe_float(r6m, 0) < -25 or (ma200 > 0 and close < ma200 * 0.85):
        investor_gate = "FAIL"
    elif investor < 72 or (ma200 > 0 and close < ma200):
        investor_gate = "CAUTION"

    # Trading plan levels: ATR-based, not a guarantee.
    atr = safe_float(last["ATR"], close * 0.03)
    daily_stop = close - max(atr * 1.2, close * 0.025)
    daily_target = close + max(atr * 2.0, close * 0.05)
    swing_stop = close - max(atr * 2.0, close * 0.06)
    swing_target = close + max(atr * 3.5, close * 0.12)
    inv_zone_low = close * 0.90
    inv_zone_high = close * 1.02

    primary = max(
        [("Trading Harian", daily), ("Swing Trading Mingguan", swing), ("Investor Jangka Panjang", investor)],
        key=lambda z: z[1],
    )[0]
    style_scores = {
        "Trading Harian": daily,
        "Swing Trading Mingguan": swing,
        "Investor Jangka Panjang": investor,
    }
    ranked_styles = sorted(style_scores.items(), key=lambda z: z[1], reverse=True)
    secondary = ranked_styles[1][0]

    return {
        "Kode": ticker,
        "Nama": name or ticker,
        "Sektor": sector or "-",
        "Price": close,
        "Return 1M %": r1m,
        "Return 3M %": r3m,
        "Return 6M %": r6m,
        "Return 2Y %": r2y,
        "RSI": rsi,
        "Volume Ratio": vr,
        "ATR %": atr_pct,
        "MA20": ma20,
        "MA50": ma50,
        "MA200": ma200,
        "Breakout20": "YA" if breakout20 else "TIDAK",
        "Daily Score": round(daily, 1),
        "Daily Gate": daily_gate,
        "Swing Score": round(swing, 1),
        "Swing Gate": swing_gate,
        "Investor Score": round(investor, 1),
        "Investor Gate": investor_gate,
        "Primary Style": primary,
        "Secondary Style": secondary,
        "Daily Stop": daily_stop,
        "Daily Target": daily_target,
        "Swing Stop": swing_stop,
        "Swing Target": swing_target,
        "Investor Zone Low": inv_zone_low,
        "Investor Zone High": inv_zone_high,
        "Date": x.index[-1],
        "_history": x,
    }

def scan_universe(universe, max_stocks=50, progress=None):
    subset = universe.head(max_stocks).copy()
    tickers = subset["ticker"].tolist()
    meta = subset.set_index("ticker").to_dict("index")
    histories = download_many(tickers, period="2y")
    rows = []
    total = len(tickers)
    for i, ticker in enumerate(tickers, start=1):
        d = histories.get(ticker, pd.DataFrame())
        m = compute_metrics(
            ticker, d,
            name=meta.get(ticker, {}).get("name", ticker),
            sector=meta.get(ticker, {}).get("sector", "-"),
        )
        if m:
            rows.append(m)
        if progress:
            progress(i / max(total, 1))
    return pd.DataFrame(rows)

# -----------------------------
# UI COMPONENTS
# -----------------------------
def render_pick_card(row, style):
    info = STYLE_INFO[style]
    score_col = {
        "Trading Harian": "Daily Score",
        "Swing Trading Mingguan": "Swing Score",
        "Investor Jangka Panjang": "Investor Score",
    }[style]
    gate_col = {
        "Trading Harian": "Daily Gate",
        "Swing Trading Mingguan": "Swing Gate",
        "Investor Jangka Panjang": "Investor Gate",
    }[style]
    score = row[score_col]
    gate = row[gate_col]
    ticker = row["Kode"]
    price = rupiah(row["Price"])

    if style == "Trading Harian":
        plan = f"Stop {rupiah(row['Daily Stop'])} · Target {rupiah(row['Daily Target'])}"
        reason = f"Return 1M {pct(row['Return 1M %'])} · Vol {num(row['Volume Ratio'])}x · Breakout {row['Breakout20']}"
    elif style == "Swing Trading Mingguan":
        plan = f"Stop {rupiah(row['Swing Stop'])} · Target {rupiah(row['Swing Target'])}"
        reason = f"Return 3M {pct(row['Return 3M %'])} · MA50 {rupiah(row['MA50'])} · Breakout {row['Breakout20']}"
    else:
        plan = f"Zona pantau {rupiah(row['Investor Zone Low'])}–{rupiah(row['Investor Zone High'])}"
        reason = f"Return 6M {pct(row['Return 6M %'])} · Return 2Y {pct(row['Return 2Y %'])} · MA200 {rupiah(row['MA200'])}"

    st.markdown(f"""
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;">
        <div>
          <div class="card-title">{ticker}</div>
          <div class="small-note">{row['Nama']}</div>
        </div>
        <div>{gate_badge(gate)}</div>
      </div>
      <div style="margin-top:10px;font-size:1.15rem;font-weight:700;">{price}</div>
      <div style="margin-top:5px;"><b>{score_col}:</b> {score} / 100</div>
      <div class="small-note" style="margin-top:6px;">{reason}</div>
      <div class="small-note" style="margin-top:6px;">{plan}</div>
    </div>
    """, unsafe_allow_html=True)

def style_table(df, style):
    if df.empty:
        return df
    if style == "Trading Harian":
        cols = ["Kode","Nama","Sektor","Price","Daily Score","Daily Gate","Return 1M %","RSI","Volume Ratio","Breakout20","Primary Style"]
    elif style == "Swing Trading Mingguan":
        cols = ["Kode","Nama","Sektor","Price","Swing Score","Swing Gate","Return 1M %","Return 3M %","Return 6M %","RSI","Primary Style"]
    else:
        cols = ["Kode","Nama","Sektor","Price","Investor Score","Investor Gate","Return 6M %","Return 2Y %","MA200","Primary Style"]
    cols = [c for c in cols if c in df.columns]
    out = df[cols].copy()
    if "Price" in out:
        out["Price"] = out["Price"].round(0)
    for c in out.columns:
        if "Return" in c:
            out[c] = out[c].round(2)
    return out

# -----------------------------
# SIDEBAR
# -----------------------------
with st.sidebar:
    st.markdown("## 📈 Sanggul Stock Scanner")
    st.caption("V10.2 · Style-Specific · Risk-Gated")
    st.divider()

    menu = st.radio(
        "Menu",
        ["Beranda", "Scanner & Ranking", "Top 3 Actionable Picks", "Analisis 1 Saham", "Tentang"],
        index=0,
    )

    st.markdown("### Pengaturan Scan")
    period_label = st.selectbox("Periode data utama", list(PERIODS.keys()), index=2)
    max_scan = st.slider("Maksimum saham dipindai", 10, 100, 50, 10)
    min_score = st.slider("Minimum score tampilan", 0, 100, 55, 5)
    universe_mode = st.selectbox("Universe", ["Full IDX (sesuai data tersedia)", "Saham likuid contoh"])
    run_scan = st.button("🚀 Jalankan / Refresh Scan", type="primary", use_container_width=True)

# -----------------------------
# HEADER
# -----------------------------
st.title("Sanggul Stock Scanner V10.2")
st.caption("Style-Specific Scoring · Multi-Period · Top 3 Actionable Picks · Risk-Gated · Focus-Aware Multi-Style")

universe = load_universe()
if universe.empty:
    st.error("Universe IDX gagal dimuat. Periksa koneksi internet atau sumber data.")
    st.stop()

if universe_mode == "Saham likuid contoh":
    sample = ["BBCA","BBRI","BMRI","BBNI","TLKM","ASII","ANTM","AMMN","JPFA","ERAA","AKRA","MEDC","PTBA","ITMG","PGAS","GOTO","INCO","MDKA","UNTR","ICBP"]
    universe = universe[universe["ticker"].isin(sample)].copy()

if run_scan or "scan_result" not in st.session_state:
    progress_bar = st.progress(0, text="Menyiapkan data historis...")
    with st.spinner("Mengambil data historis dan menghitung score per gaya..."):
        result = scan_universe(universe, max_stocks=max_scan, progress=progress_bar.progress)
    progress_bar.progress(1.0, text="Scan selesai")
    st.session_state["scan_result"] = result
else:
    result = st.session_state["scan_result"]

if result.empty:
    st.warning("Belum ada data yang berhasil dianalisis. Coba refresh, kurangi jumlah saham, atau periksa koneksi.")
    st.stop()

# Summary
pass_daily = int((result["Daily Gate"] == "PASS").sum())
pass_swing = int((result["Swing Gate"] == "PASS").sum())
pass_inv = int((result["Investor Gate"] == "PASS").sum())
primary_counts = result["Primary Style"].value_counts()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Saham dianalisis", len(result))
k2.metric("Daily PASS", pass_daily)
k3.metric("Swing PASS", pass_swing)
k4.metric("Investor PASS", pass_inv)
k5.metric("Primary Style", primary_counts.index[0] if not primary_counts.empty else "-")

# -----------------------------
# BERANDA
# -----------------------------
if menu == "Beranda":
    st.subheader("🎯 Multi-Style Action Board")
    st.info("Setiap gaya sekarang menggunakan score dan Risk Gate yang berbeda. Saham boleh overlap jika memang memenuhi lebih dari satu gaya, tetapi alasan dan skornya tidak lagi sama.")

    cols = st.columns(3)
    style_defs = [
        ("Trading Harian", "Daily Score", "Daily Gate"),
        ("Swing Trading Mingguan", "Swing Score", "Swing Gate"),
        ("Investor Jangka Panjang", "Investor Score", "Investor Gate"),
    ]
    for col, (style, score_col, gate_col) in zip(cols, style_defs):
        with col:
            info = STYLE_INFO[style]
            st.markdown(f"### {info['icon']} {style}")
            st.caption(f"Fokus: {info['horizon']} · {info['subtitle']}")
            candidates = result[(result[score_col] >= min_score) & (result[gate_col].isin(["PASS","CAUTION"]))].copy()
            candidates = candidates.sort_values([gate_col, score_col], ascending=[True, False]).head(3)
            if candidates.empty:
                st.warning("Belum ada kandidat pada ambang ini.")
            else:
                for _, row in candidates.iterrows():
                    render_pick_card(row, style)

    st.subheader("🔎 Distribusi Primary Style")
    dist = primary_counts.rename_axis("Style").reset_index(name="Jumlah")
    st.bar_chart(dist.set_index("Style"))

    st.subheader("📋 Enrich Top 50 — Focus-Aware Multi-Style")
    enriched = result.copy()
    enriched["Best Score"] = enriched[["Daily Score","Swing Score","Investor Score"]].max(axis=1)
    enriched = enriched.sort_values("Best Score", ascending=False).head(50)
    st.dataframe(
        enriched.drop(columns=["_history"], errors="ignore"),
        use_container_width=True,
        hide_index=True,
    )

# -----------------------------
# SCANNER & RANKING
# -----------------------------
elif menu == "Scanner & Ranking":
    st.subheader("📊 Scanner & Ranking per Gaya")
    style = st.selectbox("Pilih gaya ranking", list(STYLE_INFO.keys()))
    score_col = {
        "Trading Harian":"Daily Score",
        "Swing Trading Mingguan":"Swing Score",
        "Investor Jangka Panjang":"Investor Score",
    }[style]
    gate_col = {
        "Trading Harian":"Daily Gate",
        "Swing Trading Mingguan":"Swing Gate",
        "Investor Jangka Panjang":"Investor Gate",
    }[style]
    view = result[result[score_col] >= min_score].copy()
    view = view.sort_values(score_col, ascending=False)
    st.caption(f"{style}: {STYLE_INFO[style]['subtitle']}")
    st.dataframe(style_table(view, style), use_container_width=True, hide_index=True)

# -----------------------------
# TOP 3 ACTIONABLE PICKS
# -----------------------------
elif menu == "Top 3 Actionable Picks":
    st.subheader("🏆 Top 3 Actionable Picks — Risk-Gated")
    st.caption("Top 3 diambil dari score gaya masing-masing dan diprioritaskan berdasarkan Gate PASS, lalu CAUTION. Ini adalah shortlist analisis, bukan jaminan hasil.")

    for style, score_col, gate_col in style_defs:
        st.markdown(f"### {STYLE_INFO[style]['icon']} {style}")
        candidates = result[result[score_col] >= min_score].copy()
        candidates["_gate_order"] = candidates[gate_col].map({"PASS":0,"CAUTION":1,"FAIL":2}).fillna(3)
        candidates = candidates.sort_values(["_gate_order", score_col], ascending=[True, False]).head(3)
        if candidates.empty:
            st.info("Tidak ada kandidat pada minimum score saat ini.")
            continue
        c = st.columns(min(3, len(candidates)))
        for col, (_, row) in zip(c, candidates.iterrows()):
            with col:
                render_pick_card(row, style)

# -----------------------------
# SINGLE STOCK
# -----------------------------
elif menu == "Analisis 1 Saham":
    st.subheader("🔎 Analisis 1 Saham")
    tickers = universe["ticker"].tolist()
    selected = st.selectbox("Pilih kode saham", tickers)
    d = download_history(selected, period="2y")
    meta = universe[universe["ticker"] == selected]
    name = meta.iloc[0]["name"] if not meta.empty else selected
    sector = meta.iloc[0]["sector"] if not meta.empty else "-"
    m = compute_metrics(selected, d, name=name, sector=sector)

    if not m:
        st.error("Data saham tidak cukup untuk dianalisis.")
        st.stop()

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Harga", rupiah(m["Price"]))
    a2.metric("Daily Score", m["Daily Score"], m["Daily Gate"])
    a3.metric("Swing Score", m["Swing Score"], m["Swing Gate"])
    a4.metric("Investor Score", m["Investor Score"], m["Investor Gate"])

    st.markdown(f"**{selected} — {name}** · {sector}")
    st.caption(f"Primary Style: {m['Primary Style']} · Secondary Style: {m['Secondary Style']} · Data terakhir: {m['Date'].strftime('%d-%m-%Y')}")

    chart_period = st.select_slider("Rentang grafik", options=["3 Bulan","6 Bulan","1 Tahun","2 Tahun"], value="6 Bulan")
    days = {"3 Bulan":63, "6 Bulan":126, "1 Tahun":252, "2 Tahun":504}[chart_period]
    x = m["_history"].tail(days).copy()

    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=x.index, open=x["Open"], high=x["High"], low=x["Low"], close=x["Close"],
        name="Harga",
        increasing_line_color="#059669", decreasing_line_color="#dc2626",
    ))
    for col, color in [("MA20","#2563eb"),("MA50","#d97706"),("MA200","#7c3aed")]:
        if col in x.columns and x[col].notna().any():
            fig.add_trace(go.Scatter(x=x.index, y=x[col], mode="lines", name=col, line=dict(width=1.7, color=color)))
    fig.update_layout(
        height=460,
        margin=dict(l=10,r=10,t=25,b=10),
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", y=1.02, x=0),
        template="plotly_white",
        title=f"{selected} · Grafik {chart_period}",
    )
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo":False})

    st.markdown("### Ringkasan indikator")
    ind = pd.DataFrame({
        "Indikator":["RSI","Volume Ratio","ATR %","Return 1M","Return 3M","Return 6M","Return 2Y","Breakout 20 Hari"],
        "Nilai":[num(m["RSI"]), num(m["Volume Ratio"])+"x", pct(m["ATR %"]), pct(m["Return 1M %"]), pct(m["Return 3M %"]), pct(m["Return 6M %"]), pct(m["Return 2Y %"]), m["Breakout20"]],
    })
    st.table(ind)

    st.markdown("### Rencana level berbasis ATR")
    p1, p2, p3 = st.columns(3)
    p1.metric("Daily Stop", rupiah(m["Daily Stop"]))
    p2.metric("Swing Stop", rupiah(m["Swing Stop"]))
    p3.metric("Swing Target", rupiah(m["Swing Target"]))
    st.warning("Level di atas merupakan estimasi teknikal berbasis ATR untuk membantu menyusun skenario risiko. Bukan sinyal pasti dan perlu divalidasi dengan kondisi pasar serta likuiditas.")

# -----------------------------
# TENTANG
# -----------------------------
else:
    st.subheader("ℹ️ Tentang V10.2")
    st.markdown("""
    **Perbaikan utama V10.2:**

    1. **Score terpisah** untuk Trading Harian, Swing Trading Mingguan, dan Investor Jangka Panjang.
    2. **Risk Gate terpisah** untuk masing-masing gaya.
    3. Periode yang berbeda dipakai secara kontekstual:
       - Harian: momentum 1 bulan, volume, volatilitas, breakout.
       - Swing: return 1–6 bulan, MA20/MA50, struktur tren dan pullback.
       - Investor: return 6 bulan–2 tahun, MA200, tren panjang dan drawdown.
    4. **Primary Style dan Secondary Style** agar overlap dapat dijelaskan, bukan dianggap error.
    5. **Top 3 Actionable Picks** disusun per gaya, memprioritaskan PASS lalu CAUTION.
    6. **Grafik individual** dibuat lebih besar dan proporsional, dengan candlestick, MA20, MA50, dan MA200.
    7. Menggunakan `st.cache_data` untuk mengurangi pengambilan data berulang.

    **Catatan:** Aplikasi ini adalah alat bantu analisis teknikal. Data Yahoo Finance dapat terlambat, tidak lengkap, atau gagal diambil. Tidak ada score atau Risk Gate yang menjamin keuntungan.
    """)

st.divider()
st.caption("Sanggul Stock Scanner V10.2 · Data: Yahoo Finance · Untuk riset dan penyusunan watchlist, bukan jaminan profit.")
