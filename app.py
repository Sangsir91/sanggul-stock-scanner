import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

# ============================================================
# SANGGUL STOCK SCANNER IDX V8.2 — SIMPLE CARD UI
# FOCUS-AWARE ENRICH + MULTI-STYLE ACTION BOARD
# ============================================================

st.set_page_config(
    page_title="Sanggul Stock Scanner IDX V8.2 | Simple Card UI",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

IDX_UNIVERSE_URL = (
    "https://huggingface.co/datasets/"
    "kjhq/Indonesia-Stock-Symbols-and-Metadata/"
    "resolve/main/indonesia.csv"
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
.block-container {padding-top:1.2rem;padding-bottom:2.5rem;max-width:1500px}
[data-testid="stMetric"] {background:#fff;border:1px solid #e5e7eb;padding:12px 14px;border-radius:14px}
.info-card,.stock-card,.compact-card,.action-card,.metric-card,.empty-card,.success-card{border:1px solid #e5e7eb;border-radius:14px;background:#fff;box-shadow:0 2px 8px rgba(15,23,42,.04)}
.info-card{padding:16px 18px;margin:8px 0 18px}.card-title{font-weight:700;margin-bottom:12px}.flow-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.flow-grid div{background:#f8fafc;border-radius:10px;padding:10px;text-align:center}.flow-grid b{display:block;font-size:18px;color:#2563eb}.flow-grid span{font-size:12px;color:#475569}
.metric-card{padding:13px 15px}.metric-label{font-size:12px;color:#64748b}.metric-value{font-size:22px;font-weight:700}
.stock-card,.action-card{padding:15px 17px;margin:9px 0}.stock-head{display:flex;justify-content:space-between;align-items:center;gap:10px}.ticker{font-weight:800;color:#1d4ed8;font-size:1.05rem}.stock-name{font-weight:650;margin-left:8px}.stock-meta{font-size:12px;color:#64748b;margin:6px 0 13px}.data-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:8px}.compact-grid{flex:1;grid-template-columns:repeat(4,minmax(75px,1fr));min-width:0}.compact-grid div{padding:7px}.data-grid div{background:#f8fafc;border-radius:9px;padding:9px}.data-grid small{display:block;color:#64748b;font-size:11px}.data-grid b{display:block;margin-top:3px;font-size:13px;overflow-wrap:anywhere}.pill{border-radius:999px;padding:5px 9px;font-size:11px;font-weight:750;white-space:nowrap}.positive{background:#dcfce7;color:#166534}.negative{background:#fee2e2;color:#991b1b}.neutral{background:#e2e8f0;color:#334155}.warning{background:#fef3c7;color:#92400e}.compact-card{padding:11px 14px;margin:7px 0;display:flex;justify-content:space-between;align-items:center;gap:12px}.compact-card small{color:#64748b}.compact-values{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:#64748b}.compact-values b{color:#0f172a}.style-title{font-weight:750;margin-bottom:8px}.empty-card,.success-card{padding:13px 16px;margin:10px 0}.success-card{background:#f0fdf4;border-color:#bbf7d0;color:#166534}@media(max-width:900px){.data-grid{grid-template-columns:repeat(3,1fr)}.flow-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:600px){.data-grid{grid-template-columns:repeat(2,1fr)}.stock-head,.compact-card{align-items:flex-start;flex-direction:column}.compact-values{gap:8px}}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
def rupiah(x):
    if x is None or pd.isna(x):
        return "-"
    return f"Rp {x:,.0f}".replace(",", ".")


def yahoo_symbol(kode):
    kode = str(kode).upper().strip()
    return kode if kode.endswith(".JK") else kode + ".JK"


def safe_float(x, default=0.0):
    try:
        if pd.isna(x):
            return default
        return float(x)
    except Exception:
        return default


def clamp(x, lo=0, hi=100):
    return float(max(lo, min(hi, x)))


def render_stock_card(r, mode="normal"):
    signal = str(r.get("Signal", r.get("SwingSignal", "WAIT")))
    cls = "positive" if "BUY" in signal or signal == "PASS" else "negative" if "SELL" in signal or signal == "AVOID" else "neutral"
    st.markdown(f"""<div class=\"stock-card\"><div class=\"stock-head\"><div><span class=\"ticker\">{r.get('Kode','-')}</span><span class=\"stock-name\">{r.get('Nama','')}</span></div><span class=\"pill {cls}\">{signal}</span></div><div class=\"stock-meta\">{r.get('Sektor','-')} · Trend: <b>{r.get('Trend','-')}</b> · Setup: <b>{r.get('Setup','-')}</b></div><div class=\"data-grid\"><div><small>Harga</small><b>{rupiah(r.get('Price'))}</b></div><div><small>Score</small><b>{r.get('Score','-')}</b></div><div><small>Opportunity</small><b>{r.get('Opportunity','-')}</b></div><div><small>RSI</small><b>{r.get('RSI','-')}</b></div><div><small>Volume</small><b>{r.get('Volume','-')}</b></div><div><small>R:R</small><b>{r.get('R:R','-')}</b></div></div></div>""", unsafe_allow_html=True)


def fmt_num(x, digits=2):
    if x is None:
        return "-"
    try:
        if pd.isna(x):
            return "-"
        return f"{float(x):,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(x)

def render_compact_row(r, score_key="Score", signal_key="Signal", extra=None):
    signal = str(r.get(signal_key, "-"))
    cls = "positive" if ("BUY" in signal or signal == "PASS") else "negative" if ("SELL" in signal or signal == "AVOID") else "neutral"
    values = [("Score", r.get(score_key, "-")), ("Trend", r.get("Trend", "-")), ("Setup", r.get("Setup", "-"))] + (extra or [])
    cells = "".join(f'<div><small>{label}</small><b>{value}</b></div>' for label, value in values)
    st.markdown(
        f"""<div class="compact-card">
        <div style="min-width:180px"><div class="ticker">{r.get("Kode","-")}</div>
        <div class="stock-meta">{r.get("Nama","")}<br>{r.get("Sektor","-")}</div></div>
        <div class="data-grid compact-grid">{cells}</div>
        <span class="pill {cls}">{signal}</span>
        </div>""",
        unsafe_allow_html=True
    )

def render_action_card(r, score_key, signal_key, title_label, extra=None):
    signal = str(r.get(signal_key, "-"))
    cls = "positive" if ("BUY" in signal or signal == "PASS") else "negative" if ("SELL" in signal or signal == "AVOID") else "neutral"
    values = [("Score", r.get(score_key, "-")), ("Trend", r.get("Trend", "-")), ("Setup", r.get("Setup", "-"))] + (extra or [])
    cells = "".join(f'<div><small>{label}</small><b>{value}</b></div>' for label, value in values)
    st.markdown(
        f"""<div class="action-card">
        <div class="stock-head"><div><span class="ticker">{r.get("Kode","-")}</span>
        <span class="stock-name">{r.get("Nama","")}</span></div>
        <span class="pill {cls}">{signal}</span></div>
        <div class="stock-meta">{title_label} · {r.get("Sektor","-")}</div>
        <div class="data-grid compact-grid">{cells}</div>
        </div>""",
        unsafe_allow_html=True
    )

# -----------------------------
# Universe
# -----------------------------
@st.cache_data(ttl=86400, show_spinner=False)
def load_idx_universe():
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
        df = df[df["ticker"].str.fullmatch(r"[A-Z]{4}", na=False)].drop_duplicates("ticker")
        df["Yahoo"] = df["ticker"] + ".JK"
        return df.sort_values("ticker").reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

# -----------------------------
# Yahoo data
# -----------------------------
@st.cache_data(ttl=900, show_spinner=False)
def download_batch(tickers, period="2y"):
    if not tickers:
        return pd.DataFrame()
    try:
        return yf.download(
            tickers=list(tickers), period=period, interval="1d",
            auto_adjust=True, progress=False, threads=True,
            group_by="ticker", multi_level_index=True,
        )
    except Exception:
        return pd.DataFrame()


def extract_ticker_data(batch, ticker):
    if batch is None or batch.empty:
        return pd.DataFrame()
    try:
        if isinstance(batch.columns, pd.MultiIndex):
            lvl0 = batch.columns.get_level_values(0)
            lvl1 = batch.columns.get_level_values(1)
            if ticker in lvl0:
                df = batch[ticker].copy()
            elif ticker in lvl1:
                df = batch.xs(ticker, axis=1, level=1).copy()
            else:
                return pd.DataFrame()
        else:
            df = batch.copy()
        df.columns = [str(c).title() for c in df.columns]
        for c in ["Open", "High", "Low", "Close", "Volume"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
        needed = ["Open", "High", "Low", "Close"]
        if not all(c in df.columns for c in needed):
            return pd.DataFrame()
        return df.dropna(subset=needed)
    except Exception:
        return pd.DataFrame()

# -----------------------------
# Technical engine
# -----------------------------
def indicators(df):
    x = df.copy()
    close, high, low, vol = x["Close"], x["High"], x["Low"], x["Volume"]
    x["MA20"] = close.rolling(20).mean()
    x["MA50"] = close.rolling(50).mean()
    x["MA200"] = close.rolling(200).mean()
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - 100 / (1 + rs)
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    x["MACD"] = ema12 - ema26
    x["MACDSignal"] = x["MACD"].ewm(span=9, adjust=False).mean()
    prev = close.shift(1)
    tr = pd.concat([(high-low), (high-prev).abs(), (low-prev).abs()], axis=1).max(axis=1)
    x["ATR"] = tr.rolling(14).mean()
    x["VolumeMA20"] = vol.rolling(20).mean()
    x["VolumeRatio"] = vol / x["VolumeMA20"].replace(0, np.nan)
    x["Support20"] = low.rolling(20).min()
    x["Resistance20"] = high.rolling(20).max()
    x["Return20"] = close.pct_change(20) * 100
    x["Return60"] = close.pct_change(60) * 100
    x["Return120"] = close.pct_change(120) * 100
    x["RangePosition20"] = (close - x["Support20"]) / (x["Resistance20"] - x["Support20"]).replace(0, np.nan)
    return x


def fast_analysis(df, focus_days=63):
    if df.empty or len(df) < 210:
        return None
    x = indicators(df).dropna(subset=["MA20", "MA50", "MA200", "RSI", "MACD", "MACDSignal", "ATR", "VolumeRatio"])
    if x.empty:
        return None
    recent = x.tail(max(21, min(focus_days, len(x))))
    last = x.iloc[-1]
    px = safe_float(last["Close"])
    ma20, ma50, ma200 = safe_float(last["MA20"]), safe_float(last["MA50"]), safe_float(last["MA200"])
    rsi, vr = safe_float(last["RSI"]), safe_float(last["VolumeRatio"])
    atr = max(safe_float(last["ATR"]), px * 0.005)
    support = safe_float(last["Support20"], px * .95)
    resistance = safe_float(last["Resistance20"], px * 1.05)
    # Components are deliberately fractional to avoid repeated 100 scores.
    trend_component = np.mean([
        100 if px > ma20 else 25,
        100 if px > ma50 else 25,
        100 if px > ma200 else 25,
        100 if ma20 > ma50 else 35,
        100 if ma50 > ma200 else 35,
    ])
    rsi_component = 100 - min(abs(rsi - 58) * 2.4, 100)
    momentum20 = safe_float(recent["Return20"].iloc[-1])
    momentum60 = safe_float(recent["Return60"].iloc[-1])
    momentum_component = clamp(50 + momentum20 * 2.2 + momentum60 * 0.8)
    volume_component = clamp(40 + (vr - 1) * 24)
    macd_component = clamp(50 + (safe_float(last["MACD"]) - safe_float(last["MACDSignal"])) / max(abs(px), 1) * 1800)
    score = clamp(0.34*trend_component + 0.18*rsi_component + 0.22*momentum_component + 0.14*volume_component + 0.12*macd_component)
    # setup and risk/reward
    prev_res = safe_float(x["Resistance20"].shift(1).iloc[-1], resistance)
    breakout = px > prev_res and vr >= 1.15
    distance_res = (resistance - px) / px if px else 0
    risk = max(1.25 * atr, px * .02)
    reward = max(resistance - px, atr)
    rr = reward / risk if risk else 0
    setup = 95 if breakout else (78 if score >= 65 and distance_res > .025 else 58 if distance_res <= .025 else 68)
    opportunity = clamp(.62*score + .20*clamp(rr/3*100) + .18*setup)
    if breakout and score >= 68:
        signal = "STRONG BUY — BREAKOUT"
    elif score >= 72 and rr >= 1.7:
        signal = "STRONG BUY"
    elif score >= 62 and rr >= 1.3:
        signal = "BUY"
    elif score < 42:
        signal = "SELL / AVOID"
    else:
        signal = "WAIT"
    trend = "BULLISH" if score >= 65 else "NEUTRAL" if score >= 48 else "BEARISH"
    return {
        "Price": px, "Score": round(score, 1), "Opportunity": round(opportunity, 1),
        "Trend": trend, "Signal": signal, "RSI": round(rsi, 2),
        "Volume": round(vr, 3), "R:R": round(rr, 3), "Support": support,
        "Resistance": resistance, "Breakout": "YA" if breakout else "TIDAK",
        "Return20D": round(momentum20, 2), "Return60D": round(momentum60, 2),
        "Date": x.index[-1], "FocusDays": focus_days,
    }


def scan_full_idx(universe, batch_size=50, focus_days=63, progress_callback=None):
    results = []
    tickers = universe["Yahoo"].tolist()
    total = max(1, int(np.ceil(len(tickers) / batch_size)))
    for batch_no in range(total):
        batch_tickers = tickers[batch_no*batch_size:(batch_no+1)*batch_size]
        batch = download_batch(tuple(batch_tickers), period="2y")
        for ticker in batch_tickers:
            df = extract_ticker_data(batch, ticker)
            a = fast_analysis(df, focus_days=focus_days)
            if a is None:
                continue
            meta = universe[universe["Yahoo"] == ticker]
            if meta.empty:
                continue
            m = meta.iloc[0]
            results.append({"Kode": ticker.replace(".JK", ""), "Nama": m["name"], "Sektor": m["sector"], **a})
        if progress_callback:
            progress_callback((batch_no+1)/total)
    if not results:
        return pd.DataFrame()
    return pd.DataFrame(results).sort_values(["Opportunity", "Score", "R:R"], ascending=False).reset_index(drop=True)

# -----------------------------
# Enrich engine
# -----------------------------
def enrich_results(base_df, top_n=150):
    """Enriches the filtered ranking with style-specific, non-saturated scores."""
    if base_df.empty:
        return pd.DataFrame()
    d = base_df.head(top_n).copy().reset_index(drop=True)
    rows = []
    for _, r in d.iterrows():
        score = safe_float(r.get("Score"))
        opp = safe_float(r.get("Opportunity"))
        rsi = safe_float(r.get("RSI"), 50)
        vol = safe_float(r.get("Volume"), 1)
        rr = safe_float(r.get("R:R"), 1)
        ret20 = safe_float(r.get("Return20D"))
        ret60 = safe_float(r.get("Return60D"))
        breakout = str(r.get("Breakout", "TIDAK")) == "YA"
        bullish = str(r.get("Trend", "")) == "BULLISH"
        # Different formulas per style, with continuous penalties and bonuses.
        day_score = clamp(0.28*score + 0.22*clamp(40 + (vol-1)*18) + 0.20*clamp(50 + ret20*3) + 0.15*(90 if breakout else 52) + 0.15*clamp(100 - abs(rsi-58)*2.0))
        swing_score = clamp(0.34*score + 0.24*clamp(50 + ret20*1.8) + 0.18*clamp(50 + ret60*0.8) + 0.14*clamp(rr/2.5*100) + 0.10*(85 if bullish else 48))
        investor_score = clamp(0.38*clamp(50 + ret60*0.7) + 0.25*(90 if bullish else 45) + 0.20*clamp(50 + (score-50)*1.2) + 0.17*clamp(100 - abs(rsi-55)*1.5))
        day_signal = "BUY ON BREAKOUT" if breakout and day_score >= 62 else "BUY" if day_score >= 68 else "WAIT"
        swing_signal = "BUY ON BREAKOUT" if breakout and swing_score >= 62 else "BUY" if swing_score >= 66 else "WAIT"
        inv_signal = "ACCUMULATE" if investor_score >= 68 else "HOLD" if investor_score >= 52 else "AVOID"
        setup = "BREAKOUT" if breakout else "BASE/NEUTRAL"
        risk_gate = "PASS" if rr >= 1.35 and score >= 55 else "REVIEW"
        stop = safe_float(r.get("Price")) - max(safe_float(r.get("Price"))*0.02, safe_float(r.get("Price"))*0.0)
        price = safe_float(r.get("Price"))
        risk = max(price*0.02, price-safe_float(r.get("Support"), price*.95))
        stop = price - min(risk, price*.12)
        target1 = price + max(price*0.04, price-safe_float(r.get("Resistance"), price*1.04))
        target2 = price + max(price*0.08, 2*(price-stop))
        rows.append({**r.to_dict(), "DayScore": round(day_score, 1), "DaySignal": day_signal,
                     "SwingScore": round(swing_score, 1), "SwingSignal": swing_signal,
                     "InvestorScore": round(investor_score, 1), "InvestorSignal": inv_signal,
                     "Setup": setup, "RiskGate": risk_gate, "StopLoss": round(stop, 2),
                     "Target1": round(target1, 2), "Target2": round(target2, 2),
                     "EnrichStatus": "ENRICHED"})
    return pd.DataFrame(rows)

# -----------------------------
# UI
# -----------------------------
st.title("📈 Sanggul Stock Scanner IDX V8.2")
st.caption("V8.2 • Full IDX • 2 Tahun Data Konteks • Focus-Aware Analysis • Enrich Multi-Style")

with st.sidebar:
    st.header("⚙️ Pengaturan Analisis")
    focus_label = st.selectbox("Fokus Analisis", ["1 Bulan", "3 Bulan", "6 Bulan", "12 Bulan"], index=1)
    focus_map = {"1 Bulan":21, "3 Bulan":63, "6 Bulan":126, "12 Bulan":252}
    focus_days = focus_map[focus_label]
    st.info(f"Data historis 2 tahun digunakan sebagai konteks dan MA200. Analisis utama memakai {focus_label.lower()} terakhir ({focus_days} hari bursa).")
    st.caption("Sumber harga: Yahoo Finance melalui yfinance. Flow asing resmi/order book tidak tersedia di sumber ini.")

st.markdown('<div class="section-card"><b>Mode kerja V8.2</b><br>Scan Full IDX → Filter → Top Opportunity → Enrich Top 150 → Action Board berdasarkan gaya trading.</div>', unsafe_allow_html=True)

universe = load_idx_universe()
if universe.empty:
    st.error("Universe IDX gagal dimuat. Periksa koneksi internet.")
    st.stop()

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("Universe IDX", f"{len(universe):,}".replace(",", "."))
with m2: st.metric("Data Historis", "2 Tahun")
with m3: st.metric("Fokus", focus_label)
with m4: st.metric("Batch", "50 saham")

if st.button("🚀 SCAN SELURUH IDX SEKARANG", type="primary", use_container_width=True):
    progress = st.progress(0)
    status = st.empty()
    def cb(v):
        progress.progress(v)
        status.info(f"Progress scanning: {v*100:.0f}%")
    with st.spinner("Mengambil data Full IDX selama 2 tahun..."):
        result = scan_full_idx(universe, batch_size=50, focus_days=focus_days, progress_callback=cb)
    progress.progress(1.0)
    status.success(f"Scanning selesai: {len(result)} saham berhasil dianalisis.")
    st.session_state["full_scan"] = result
    st.session_state.pop("enriched", None)

result = st.session_state.get("full_scan", pd.DataFrame())
if result.empty:
    st.warning("Klik tombol SCAN SELURUH IDX SEKARANG untuk memulai.")
    st.stop()

st.success(f"{len(result)} saham memiliki data teknikal yang cukup untuk dianalisis.")

st.subheader("🎛️ Filter Full IDX")
f1, f2, f3, f4 = st.columns(4)
with f1:
    sectors = ["Semua"] + sorted(result["Sektor"].dropna().unique().tolist())
    selected_sector = st.selectbox("Sektor", sectors)
with f2:
    min_score = st.slider("Minimum Technical Score", 0, 100, 60, 5)
with f3:
    signal_filter = st.selectbox("Signal", ["Semua", "BUY", "WAIT", "SELL"])
with f4:
    breakout_filter = st.selectbox("Breakout", ["Semua", "YA", "TIDAK"])

filtered = result.copy()
if selected_sector != "Semua": filtered = filtered[filtered["Sektor"] == selected_sector]
filtered = filtered[filtered["Score"] >= min_score]
if signal_filter != "Semua": filtered = filtered[filtered["Signal"].str.contains(signal_filter, na=False)]
if breakout_filter != "Semua": filtered = filtered[filtered["Breakout"] == breakout_filter]
st.caption(f"Hasil setelah filter: {len(filtered)} saham")

st.subheader("🏆 Top 10 Opportunity — Full IDX")
top10 = result.sort_values(["Opportunity", "Score"], ascending=False).head(10)
left, right = st.columns(2)
for i, (_, row) in enumerate(top10.iterrows()):
    with (left if i % 2 == 0 else right):
        render_stock_card(row)

st.subheader("🟢 Kandidat BUY")
buys = filtered[filtered["Signal"].str.contains("BUY", na=False)].head(20)
if buys.empty:
    st.warning("Belum ada kandidat BUY sesuai filter.")
else:
    left, right = st.columns(2)
    for i, (_, row) in enumerate(buys.iterrows()):
        with (left if i % 2 == 0 else right):
            render_compact_row(row, extra=[
                ("Opportunity", fmt_num(row.get("Opportunity"))),
                ("R:R", fmt_num(row.get("R:R"))),
                ("Breakout", row.get("Breakout", "-")),
            ])

# -----------------------------
# ENRICH: always visible after scan
# -----------------------------
st.markdown("---")
st.subheader("✨ Enrich Top 150 — Focus-Aware Multi-Style")
st.write("Enrich memperkaya ranking hasil filter menjadi tiga perspektif: Trading Harian, Swing Trading Mingguan, dan Investor Jangka Panjang.")

if filtered.empty:
    st.warning("Tidak ada saham hasil filter untuk di-Enrich. Turunkan Minimum Technical Score atau ubah filter.")
else:
    enrich_source = filtered.sort_values(["Opportunity", "Score"], ascending=False).head(150)
    st.caption(f"Sumber Enrich: {len(enrich_source)} saham dari hasil filter. Fokus aktif: {focus_label}.")
    if st.button("✨ ENRICH TOP 150 SEKARANG", type="primary", use_container_width=True):
        with st.spinner("Menghitung skor Enrich dan rencana aksi..."):
            enriched = enrich_results(enrich_source, top_n=150)
        st.session_state["enriched"] = enriched
        st.success(f"Enrich selesai: {len(enriched)} saham diperkaya.")

# Show output if enriched exists
if "enriched" in st.session_state and not st.session_state["enriched"].empty:
    enriched = st.session_state["enriched"]
    st.subheader("🥇 Top 3 Actionable Picks — Risk-Gated")
    top3 = enriched[enriched["RiskGate"] == "PASS"].sort_values(["SwingScore", "DayScore"], ascending=False).head(3)
    if top3.empty:
        top3 = enriched.sort_values(["SwingScore", "DayScore"], ascending=False).head(3)
    a, b, c = st.columns(3)
    for i, (_, row) in enumerate(top3.iterrows()):
        with (a if i == 0 else b if i == 1 else c):
            render_action_card(row, "SwingScore", "SwingSignal", "Swing Risk-Gated", extra=[
                ("R:R", fmt_num(row.get("R:R"))),
                ("Risk Gate", row.get("RiskGate", "-")),
                ("Target 1", rupiah(row.get("Target1"))),
                ("Stop Loss", rupiah(row.get("StopLoss"))),
            ])

    st.subheader("🎯 Multi-Style Action Board")
    st.caption("Skor setiap gaya menggunakan formula berbeda. Skor tidak dipaksa menjadi 100; nilai dapat berbeda sesuai karakter saham.")
    a, b, c = st.columns(3)
    with a:
        st.markdown("### ⚡ Trading Harian")
        day = enriched.sort_values(["DayScore", "Volume"], ascending=False).head(5)
        for _, row in day.iterrows():
            render_action_card(row, "DayScore", "DaySignal", "Trading Harian", extra=[
                ("Volume", fmt_num(row.get("Volume"))),
                ("RSI", fmt_num(row.get("RSI"))),
            ])
    with b:
        st.markdown("### 📈 Swing Trading Mingguan")
        swing = enriched.sort_values(["SwingScore", "Opportunity"], ascending=False).head(5)
        for _, row in swing.iterrows():
            render_action_card(row, "SwingScore", "SwingSignal", "Swing Mingguan", extra=[
                ("Return 20D", f'{fmt_num(row.get("Return20D"))}%'),
                ("Return 60D", f'{fmt_num(row.get("Return60D"))}%'),
            ])
    with c:
        st.markdown("### 🏛️ Investor Jangka Panjang")
        inv = enriched.sort_values(["InvestorScore", "Return60D"], ascending=False).head(5)
        for _, row in inv.iterrows():
            render_action_card(row, "InvestorScore", "InvestorSignal", "Investor Jangka Panjang", extra=[
                ("Return 60D", f'{fmt_num(row.get("Return60D"))}%'),
                ("Risk Gate", row.get("RiskGate", "-")),
            ])

    st.subheader("📋 Detail Hasil Enrich")
    detail_cols = ["Kode","Nama","Sektor","Price","Score","Opportunity","DayScore","DaySignal","SwingScore","SwingSignal","InvestorScore","InvestorSignal","Setup","RiskGate","StopLoss","Target1","Target2"]
    with st.expander("Buka tabel detail lengkap", expanded=False):
        st.dataframe(enriched[detail_cols], use_container_width=True, hide_index=True)
    csv = enriched.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download Hasil Enrich CSV", data=csv, file_name="enriched_top150_v82.csv", mime="text/csv", use_container_width=True)
else:
    st.info("ℹ️ Hasil Enrich belum tersedia. Klik tombol **ENRICH TOP 150 SEKARANG** di atas.")

st.markdown("---")
st.caption("Catatan: data harga berasal dari Yahoo Finance melalui yfinance, bukan feed tick-by-tick resmi BEI. Signal dan skor adalah alat bantu analisis, bukan jaminan keuntungan. Saham yang tidak tersedia di Yahoo Finance dapat dilewati.")
