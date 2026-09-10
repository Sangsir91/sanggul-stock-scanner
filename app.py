
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from io import StringIO

# ============================================================
# SANGGUL STOCK SCANNER IDX V5.1
# FULL IDX SCANNER
# IHSG -> SECTOR -> ALL IDX -> TECHNICAL -> OPPORTUNITY
# ============================================================

st.set_page_config(
    page_title="Sanggul Stock Scanner IDX V5.1",
    page_icon="📈",
    layout="wide"
)

IDX_UNIVERSE_URL = (
    "https://huggingface.co/datasets/"
    "kjhq/Indonesia-Stock-Symbols-and-Metadata/"
    "resolve/main/indonesia.csv"
)

# ------------------------------------------------------------
# FORMAT
# ------------------------------------------------------------

def rupiah(x):
    if pd.isna(x):
        return "-"
    return f"Rp {x:,.0f}".replace(",", ".")


def yahoo_symbol(kode):
    kode = str(kode).upper().strip()
    return kode if kode.endswith(".JK") else kode + ".JK"


# ------------------------------------------------------------
# UNIVERSE FULL IDX
# ------------------------------------------------------------

@st.cache_data(ttl=86400)
def load_idx_universe():
    try:
        df = pd.read_csv(IDX_UNIVERSE_URL)
    except Exception:
        return pd.DataFrame()

    df.columns = [str(c).lower().strip() for c in df.columns]

    required = {"ticker", "name", "sector"}
    if not required.issubset(df.columns):
        return pd.DataFrame()

    df = df[df["market"].astype(str).str.upper().eq("IDX")].copy()
    df["ticker"] = (
        df["ticker"]
        .astype(str)
        .str.upper()
        .str.strip()
        .str.replace(".JK", "", regex=False)
    )

    df = df[
        df["ticker"].str.fullmatch(r"[A-Z]{4}", na=False)
    ].drop_duplicates("ticker")

    df["Yahoo"] = df["ticker"] + ".JK"
    return df.sort_values("ticker").reset_index(drop=True)


# ------------------------------------------------------------
# DATA BATCH
# ------------------------------------------------------------

@st.cache_data(ttl=600)
def download_batch(tickers, period="6mo"):
    if not tickers:
        return pd.DataFrame()

    try:
        data = yf.download(
            tickers=tickers,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=True,
            group_by="ticker",
            multi_level_index=True
        )
        return data
    except Exception:
        return pd.DataFrame()


def extract_ticker_data(batch, ticker):
    if batch.empty:
        return pd.DataFrame()

    try:
        if isinstance(batch.columns, pd.MultiIndex):
            # yfinance multi-ticker format: level 0=ticker, level 1=OHLCV
            if ticker in batch.columns.get_level_values(0):
                df = batch[ticker].copy()
            elif ticker in batch.columns.get_level_values(1):
                df = batch.xs(ticker, axis=1, level=1).copy()
            else:
                return pd.DataFrame()
        else:
            df = batch.copy()

        df.columns = [str(c).title() for c in df.columns]

        for c in ["Open", "High", "Low", "Close", "Volume"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")

        return df.dropna(subset=["Open", "High", "Low", "Close"])

    except Exception:
        return pd.DataFrame()


# ------------------------------------------------------------
# FAST INDICATORS UNTUK FULL SCAN
# ------------------------------------------------------------

def fast_analysis(df):
    """Fast technical engine for the full IDX scan."""
    if df.empty or len(df) < 210:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    ma20 = close.rolling(20).mean()
    ma50 = close.rolling(50).mean()
    ma200 = close.rolling(200).mean()

    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()

    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs()
    ], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()

    volume_ma = volume.rolling(20).mean()
    volume_ratio = volume / volume_ma

    support20 = low.rolling(20).min()
    resistance20 = high.rolling(20).max()
    prior_resistance20 = resistance20.shift(1)
    support60 = low.rolling(60).min()
    resistance60 = high.rolling(60).max()

    roc20 = close.pct_change(20) * 100

    w = pd.DataFrame({
        "Close": close,
        "MA20": ma20,
        "MA50": ma50,
        "MA200": ma200,
        "RSI": rsi,
        "MACD": macd,
        "MACDSignal": macd_signal,
        "ATR": atr,
        "VolumeRatio": volume_ratio,
        "Support20": support20,
        "Resistance20": resistance20,
        "PriorResistance20": prior_resistance20,
        "Support60": support60,
        "Resistance60": resistance60,
        "ROC20": roc20,
    }).dropna()

    if w.empty:
        return None

    x = w.iloc[-1]
    px = float(x["Close"])
    ma20v, ma50v, ma200v = map(float, [x["MA20"], x["MA50"], x["MA200"]])
    rsiv = float(x["RSI"])
    macdv = float(x["MACD"])
    macds = float(x["MACDSignal"])
    atrv = float(x["ATR"])
    vr = float(x["VolumeRatio"])
    roc = float(x["ROC20"])

    # ---------------------------
    # 1) TREND SCORE = 30
    # ---------------------------
    trend_score = 0
    trend_score += 6 if px > ma20v else 0
    trend_score += 6 if px > ma50v else 0
    trend_score += 6 if px > ma200v else 0
    trend_score += 6 if ma20v > ma50v else 0
    trend_score += 6 if ma50v > ma200v else 0

    # ---------------------------
    # 2) MOMENTUM SCORE = 20
    # ---------------------------
    momentum_score = 0
    if 50 <= rsiv <= 68:
        momentum_score += 8
    elif 45 <= rsiv < 50 or 68 < rsiv <= 72:
        momentum_score += 5
    elif rsiv > 72:
        momentum_score += 2

    if macdv > macds:
        momentum_score += 6
    if roc > 0:
        momentum_score += 3
    if roc > 5:
        momentum_score += 3

    # ---------------------------
    # 3) VOLUME SCORE = 15
    # ---------------------------
    if vr >= 1.5:
        volume_score = 15
    elif vr >= 1.2:
        volume_score = 11
    elif vr >= 1.0:
        volume_score = 7
    elif vr >= 0.8:
        volume_score = 3
    else:
        volume_score = 0

    # ---------------------------
    # PRICE STRUCTURE
    # ---------------------------
    res_candidates = [
        float(x["Resistance20"]),
        float(x["Resistance60"])
    ]
    resistances = [v for v in res_candidates if v > px]
    resistance = min(resistances) if resistances else max(res_candidates)

    sup_candidates = [float(x["Support20"]), float(x["Support60"])]
    supports = [v for v in sup_candidates if v < px]
    support = max(supports) if supports else min(sup_candidates)

    distance_res = (resistance - px) / px if px else 0
    distance_ma20 = abs(px - ma20v) / px if px else 0
    distance_ma50 = abs(px - ma50v) / px if px else 0

    structure_score = 0
    if px > ma20v:
        structure_score += 5
    if px > support:
        structure_score += 4
    if distance_res <= 0.08:
        structure_score += 3
    if distance_res <= 0.04:
        structure_score += 3
    if ma20v > ma50v:
        structure_score += 0  # already represented in trend score

    # ---------------------------
    # SETUP DETECTION = 20
    # ---------------------------
    prior_res = x["PriorResistance20"]
    breakout = (
        pd.notna(prior_res)
        and px > float(prior_res) * 1.002
        and vr >= 1.2
    )

    bullish_alignment = px > ma20v > ma50v > ma200v
    pullback = (
        bullish_alignment
        and (distance_ma20 <= 0.03 or distance_ma50 <= 0.03)
        and 45 <= rsiv <= 65
        and px > support
    )

    near_breakout = (
        not breakout
        and distance_res <= 0.03
        and trend_score >= 24
        and momentum_score >= 10
    )

    continuation = (
        bullish_alignment
        and not breakout
        and not pullback
        and distance_res > 0.03
        and momentum_score >= 10
    )

    if breakout:
        setup = "BREAKOUT"
        setup_score = 20
    elif pullback:
        setup = "PULLBACK"
        setup_score = 18
    elif near_breakout:
        setup = "NEAR BREAKOUT"
        setup_score = 15
    elif continuation:
        setup = "TREND CONTINUATION"
        setup_score = 12
    elif trend_score >= 18:
        setup = "WATCH"
        setup_score = 7
    else:
        setup = "NO SETUP"
        setup_score = 2

    # ---------------------------
    # 4) TECHNICAL SCORE = 100
    # ---------------------------
    technical_score = min(
        100,
        int(trend_score + momentum_score + volume_score + structure_score + setup_score)
    )

    # ---------------------------
    # RISK / REWARD
    # ---------------------------
    risk = max(1.20 * atrv, px * 0.02)
    stop = px - risk

    # Target uses the nearest meaningful resistance; if too close, use 2 ATR.
    raw_reward = resistance - px
    reward = max(raw_reward, 2.0 * atrv)
    rr = reward / risk if risk > 0 else 0

    # Risk/reward component contributes 0-20 to Opportunity.
    if rr >= 3:
        rr_component = 20
    elif rr >= 2.5:
        rr_component = 18
    elif rr >= 2:
        rr_component = 16
    elif rr >= 1.5:
        rr_component = 12
    elif rr >= 1.0:
        rr_component = 6
    else:
        rr_component = 0

    # Opportunity emphasizes technical quality but prevents a high score
    # from being driven by technicals alone.
    opportunity = round(
        0.60 * technical_score + rr_component,
        1
    )

    # ---------------------------
    # TRADE READINESS = 100
    # Answers: "How ready is this setup to trade now?"
    # ---------------------------
    readiness = 0.0
    readiness += min(25.0, trend_score / 30.0 * 25.0)

    setup_readiness = {
        "BREAKOUT": 25,
        "PULLBACK": 24,
        "NEAR BREAKOUT": 20,
        "TREND CONTINUATION": 17,
        "WATCH": 8,
        "NO SETUP": 2,
    }[setup]
    readiness += setup_readiness

    if rr >= 3:
        readiness += 20
    elif rr >= 2.5:
        readiness += 18
    elif rr >= 2:
        readiness += 16
    elif rr >= 1.5:
        readiness += 12
    elif rr >= 1:
        readiness += 6

    # Momentum readiness favors healthy RSI rather than simply high RSI.
    if 50 <= rsiv <= 68:
        momentum_readiness = 15
    elif 45 <= rsiv < 50 or 68 < rsiv <= 72:
        momentum_readiness = 10
    elif rsiv > 72:
        momentum_readiness = 4
    else:
        momentum_readiness = 3
    if macdv > macds:
        momentum_readiness += 0  # already reflected in momentum score
    readiness += momentum_readiness

    volume_readiness = 10 if vr >= 1.5 else 8 if vr >= 1.2 else 5 if vr >= 1.0 else 2
    readiness += volume_readiness

    # Timing quality: reward proximity to a logical entry area.
    if setup == "PULLBACK":
        timing = 5 if min(distance_ma20, distance_ma50) <= 0.02 else 3
    elif setup in ("BREAKOUT", "NEAR BREAKOUT"):
        timing = 5 if distance_res <= 0.03 else 3
    elif setup == "TREND CONTINUATION":
        timing = 4 if distance_res > 0.03 else 2
    else:
        timing = 1
    readiness += timing
    trade_readiness = round(min(100.0, readiness), 1)

    if trade_readiness >= 85:
        entry_quality = "EXCELLENT"
    elif trade_readiness >= 75:
        entry_quality = "GOOD"
    elif trade_readiness >= 65:
        entry_quality = "FAIR"
    elif trade_readiness >= 50:
        entry_quality = "WAIT"
    else:
        entry_quality = "POOR"

    # ---------------------------
    # DECISION ENGINE
    # ---------------------------
    if rr < 1.0 or technical_score < 45:
        signal = "SELL / AVOID"
        decision = "AVOID"
    elif breakout and trade_readiness >= 82 and rsiv <= 70 and rr >= 1.8:
        signal = "STRONG BUY — BREAKOUT"
        decision = "BUY NOW"
    elif pullback and trade_readiness >= 75 and rr >= 1.8:
        signal = "BUY — PULLBACK"
        decision = "BUY ON PULLBACK"
    elif near_breakout and trade_readiness >= 72 and rr >= 1.5:
        signal = "WATCH — NEAR BREAKOUT"
        decision = "BUY ON BREAKOUT"
    elif continuation and trade_readiness >= 75 and rr >= 1.5:
        signal = "BUY — TREND"
        decision = "BUY / MANAGE RISK"
    else:
        signal = "WAIT"
        decision = "WAIT"

    if trend_score >= 24:
        trend = "BULLISH"
    elif trend_score >= 15:
        trend = "NEUTRAL"
    else:
        trend = "BEARISH"

    # Three staged targets.
    tp1 = px + reward * 0.50
    tp2 = px + reward
    tp3 = px + reward * 1.50

    return {
        "Price": px,
        "Score": technical_score,
        "Opportunity": opportunity,
        "Trend": trend,
        "Signal": signal,
        "Decision": decision,
        "Setup": setup,
        "TrendScore": trend_score,
        "MomentumScore": momentum_score,
        "VolumeScore": volume_score,
        "StructureScore": structure_score,
        "SetupScore": setup_score,
        "TradeReadiness": trade_readiness,
        "EntryQuality": entry_quality,
        "RSI": rsiv,
        "ROC20": roc,
        "Volume": vr,
        "R:R": float(rr),
        "Support": support,
        "Resistance": resistance,
        "DistanceResistance": distance_res * 100,
        "StopLoss": stop,
        "TP1": tp1,
        "TP2": tp2,
        "TP3": tp3,
        "Breakout": "YA" if breakout else "TIDAK",
        "Date": w.index[-1]
    }


# ------------------------------------------------------------
# FULL IDX SCANNER
# ------------------------------------------------------------

def scan_full_idx(universe, batch_size=40, progress_callback=None):
    results = []
    tickers = universe["Yahoo"].tolist()

    total_batches = int(np.ceil(len(tickers) / batch_size))

    for batch_no in range(total_batches):
        start = batch_no * batch_size
        batch_tickers = tickers[start:start + batch_size]

        batch = download_batch(tuple(batch_tickers), period="1y")

        for ticker in batch_tickers:
            df = extract_ticker_data(batch, ticker)
            a = fast_analysis(df)

            if a is None:
                continue

            kode = ticker.replace(".JK", "")
            meta = universe[universe["Yahoo"] == ticker]

            if meta.empty:
                continue

            m = meta.iloc[0]

            results.append({
                "Kode": kode,
                "Nama": m["name"],
                "Sektor": m["sector"],
                **a
            })

        if progress_callback:
            progress_callback(
                (batch_no + 1) / total_batches
            )

    if not results:
        return pd.DataFrame()

    result = pd.DataFrame(results)

    return result.sort_values(
        ["Opportunity", "Score", "R:R"],
        ascending=[False, False, False]
    ).reset_index(drop=True)


# ------------------------------------------------------------
# IHSG
# ------------------------------------------------------------

@st.cache_data(ttl=600)
def get_ihsg():
    try:
        d = yf.download(
            "^JKSE",
            period="2y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
        )
    except Exception:
        return None

    if d.empty:
        return None

    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)

    d.columns = [str(c).title() for c in d.columns]
    d["Close"] = pd.to_numeric(d["Close"], errors="coerce")
    d = d.dropna(subset=["Close"])

    d["MA20"] = d["Close"].rolling(20).mean()
    d["MA50"] = d["Close"].rolling(50).mean()
    d["MA200"] = d["Close"].rolling(200).mean()

    w = d.dropna(subset=["MA20", "MA50", "MA200"])

    if w.empty:
        return None

    x = w.iloc[-1]
    px = float(x["Close"])

    score = 0

    if px > x["MA20"]:
        score += 25
    if px > x["MA50"]:
        score += 25
    if px > x["MA200"]:
        score += 25
    if x["MA20"] > x["MA50"]:
        score += 15
    if x["MA50"] > x["MA200"]:
        score += 10

    trend = (
        "BULLISH" if score >= 75
        else "SIDEWAYS" if score >= 50
        else "BEARISH"
    )

    return {
        "Price": px,
        "Score": score,
        "Trend": trend,
        "Date": w.index[-1]
    }


# ------------------------------------------------------------
# DETAILED SINGLE STOCK
# ------------------------------------------------------------

@st.cache_data(ttl=600)
def detailed_data(kode):
    data = ambil_data(kode)
    if data.empty:
        return pd.DataFrame()
    return data


def ambil_data(kode):
    try:
        d = yf.download(
            yahoo_symbol(kode),
            period="2y",
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False
        )
    except Exception:
        return pd.DataFrame()

    if d.empty:
        return pd.DataFrame()

    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)

    d.columns = [str(c).title() for c in d.columns]

    for c in ["Open","High","Low","Close","Volume"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")

    return d.dropna(subset=["Open","High","Low","Close"])


def detailed_indicators(df):
    x = df.copy()

    x["MA20"] = x["Close"].rolling(20).mean()
    x["MA50"] = x["Close"].rolling(50).mean()
    x["MA200"] = x["Close"].rolling(200).mean()

    d = x["Close"].diff()
    gain = d.clip(lower=0).rolling(14).mean()
    loss = (-d.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - 100 / (1 + rs)

    ema12 = x["Close"].ewm(span=12, adjust=False).mean()
    ema26 = x["Close"].ewm(span=26, adjust=False).mean()
    x["MACD"] = ema12 - ema26
    x["MACD_Signal"] = x["MACD"].ewm(span=9, adjust=False).mean()

    mid = x["Close"].rolling(20).mean()
    std = x["Close"].rolling(20).std()
    x["BB_Upper"] = mid + 2 * std
    x["BB_Lower"] = mid - 2 * std

    pc = x["Close"].shift(1)
    tr = pd.concat([
        x["High"] - x["Low"],
        (x["High"] - pc).abs(),
        (x["Low"] - pc).abs()
    ], axis=1).max(axis=1)

    x["ATR"] = tr.rolling(14).mean()
    x["Volume_MA20"] = x["Volume"].rolling(20).mean()
    x["Volume_Ratio"] = x["Volume"] / x["Volume_MA20"]

    x["Support20"] = x["Low"].rolling(20).min()
    x["Resistance20"] = x["High"].rolling(20).max()

    return x


# ============================================================
# UI
# ============================================================

st.title("📈 SANGGUL STOCK SCANNER IDX")
st.caption("V5 — FULL IDX SCANNER • IHSG → SECTOR → ALL IDX → OPPORTUNITY")

menu = st.radio(
    "Menu",
    ["🏠 Full IDX Scanner", "🔎 Analisis Saham"],
    horizontal=True
)

# ============================================================
# FULL IDX
# ============================================================

if menu == "🏠 Full IDX Scanner":

    st.header("🌐 Market Overview")

    ihsg = get_ihsg()

    if ihsg:
        c1, c2, c3 = st.columns(3)

        with c1:
            st.metric(
                "IHSG",
                f"{ihsg['Price']:,.0f}".replace(",", ".")
            )

        with c2:
            st.metric(
                "Market Score",
                f"{ihsg['Score']}/100"
            )

        with c3:
            st.metric(
                "Market Trend",
                ihsg["Trend"]
            )

        st.caption(
            f"Data IHSG terakhir: {ihsg['Date'].strftime('%d-%m-%Y')}"
        )

    st.divider()

    universe = load_idx_universe()

    st.header("🚀 Full IDX Scanner")

    if universe.empty:
        st.error(
            "Universe IDX gagal dimuat. Periksa koneksi internet."
        )
        st.stop()

    u1, u2, u3 = st.columns(3)

    with u1:
        st.metric(
            "Universe IDX",
            f"{len(universe):,}".replace(",", ".")
        )

    with u2:
        st.metric(
            "Periode Scan",
            "1 Tahun"
        )

    with u3:
        st.metric(
            "Batch",
            "50 saham"
        )

    st.info(
        "V5.2 menggunakan universe saham IDX yang diperbarui berkala. "
        "Saham yang tidak memiliki data historis cukup atau tidak tersedia "
        "di Yahoo Finance otomatis dilewati."
    )

    if st.button(
        "🚀 SCAN SELURUH IDX SEKARANG",
        width="stretch"
    ):

        progress = st.progress(0)
        status = st.empty()

        def update_progress(value):
            progress.progress(value)
            status.info(
                f"Progress scanning: {value*100:.0f}%"
            )

        with st.spinner("Scanning Full IDX..."):
            result = scan_full_idx(
                universe,
                batch_size=40,
                progress_callback=update_progress
            )

        progress.progress(1.0)
        status.success(
            f"Scanning selesai: {len(result)} saham berhasil dianalisis."
        )

        st.session_state["full_scan"] = result

    result = st.session_state.get(
        "full_scan",
        pd.DataFrame()
    )

    if not result.empty:

        st.success(
            f"{len(result)} saham memiliki data teknikal yang cukup "
            f"untuk dianalisis."
        )

        st.subheader("🎛️ Filter Full IDX")

        f1, f2, f3, f4 = st.columns(4)

        with f1:
            sectors = ["Semua"] + sorted(
                result["Sektor"].dropna().unique().tolist()
            )
            selected_sector = st.selectbox(
                "Sektor",
                sectors
            )

        with f2:
            min_score = st.slider(
                "Minimum Technical Score",
                0, 100, 60, 5
            )

        with f3:
            signal = st.selectbox(
                "Signal",
                ["Semua", "BUY", "WAIT", "SELL"]
            )

        with f4:
            breakout = st.selectbox(
                "Breakout",
                ["Semua", "YA", "TIDAK"]
            )

        filtered = result.copy()

        if selected_sector != "Semua":
            filtered = filtered[
                filtered["Sektor"] == selected_sector
            ]

        filtered = filtered[
            filtered["Score"] >= min_score
        ]

        if signal == "BUY":
            filtered = filtered[
                filtered["Signal"].str.contains("BUY", na=False)
            ]
        elif signal == "WAIT":
            filtered = filtered[
                filtered["Signal"].str.contains("WAIT", na=False)
            ]
        elif signal == "SELL":
            filtered = filtered[
                filtered["Signal"].str.contains("SELL", na=False)
            ]

        if breakout != "Semua":
            filtered = filtered[
                filtered["Breakout"] == breakout
            ]

        st.caption(
            f"Hasil setelah filter: {len(filtered)} saham"
        )

        # ----------------------------------------------------
        # TOP 10 OPPORTUNITY FROM FULL UNIVERSE
        # ----------------------------------------------------

        st.subheader("🏆 Top 10 Opportunity — Full IDX")

        top10 = result.head(10)
        top_cols = [
            "Kode", "Nama", "Sektor", "Price", "Score", "Opportunity",
            "Setup", "Decision", "Trend", "RSI", "R:R", "Breakout"
        ]
        st.dataframe(
            top10[top_cols],
            width="stretch",
            hide_index=True
        )

        st.subheader("🎯 Top Trading Readiness")
        readiness_cols = [
            "Kode", "Nama", "Sektor", "Price", "TradeReadiness",
            "EntryQuality", "Setup", "Decision", "Trend", "RSI", "R:R"
        ]
        ready_top = (
            result[result["Decision"] != "AVOID"]
            .sort_values(["TradeReadiness", "Opportunity", "R:R"], ascending=[False, False, False])
            .head(10)
        )
        if ready_top.empty:
            st.info("Belum ada setup dengan trade readiness yang layak.")
        else:
            st.dataframe(ready_top[readiness_cols], width="stretch", hide_index=True)

        # ----------------------------------------------------
        # THREE ACTION RANKINGS
        # ----------------------------------------------------

        st.subheader("🚀 Top Breakout")
        breakout_df = result[
            (result["Setup"] == "BREAKOUT") &
            (result["R:R"] >= 1.5)
        ].sort_values(["Opportunity", "R:R"], ascending=[False, False]).head(10)
        if breakout_df.empty:
            st.info("Belum ada setup breakout yang memenuhi R:R ≥ 1.5.")
        else:
            st.dataframe(
                breakout_df[["Kode", "Nama", "Sektor", "Price", "Score", "Opportunity", "R:R", "Decision"]],
                width="stretch", hide_index=True
            )

        st.subheader("🔄 Top Pullback")
        pullback_df = result[
            (result["Setup"] == "PULLBACK") &
            (result["R:R"] >= 1.5)
        ].sort_values(["Opportunity", "R:R"], ascending=[False, False]).head(10)
        if pullback_df.empty:
            st.info("Belum ada setup pullback yang memenuhi R:R ≥ 1.5.")
        else:
            st.dataframe(
                pullback_df[["Kode", "Nama", "Sektor", "Price", "Score", "Opportunity", "RSI", "R:R", "Decision"]],
                width="stretch", hide_index=True
            )

        st.subheader("🟢 Kandidat BUY")
        buys = result[
            result["Decision"].isin(["BUY NOW", "BUY ON PULLBACK", "BUY ON BREAKOUT", "BUY / MANAGE RISK"])
            & (result["R:R"] >= 1.5)
        ].sort_values(["Opportunity", "R:R"], ascending=[False, False]).head(20)

        if buys.empty:
            st.warning("Belum ada kandidat BUY dengan R:R ≥ 1.5 pada Full IDX.")
        else:
            st.dataframe(
                buys[["Kode", "Nama", "Sektor", "Price", "Score", "Opportunity", "Setup", "Decision", "R:R"]],
                width="stretch", hide_index=True
            )

        # ----------------------------------------------------
        # SECTOR STRENGTH
        # ----------------------------------------------------

        st.subheader("🏭 Sector Strength — Full IDX")

        sector_rank = (
            result.groupby("Sektor")
            .agg(
                Average_Score=("Score", "mean"),
                Average_Opportunity=("Opportunity", "mean"),
                Best_Opportunity=("Opportunity", "max"),
                Average_Readiness=("TradeReadiness", "mean"),
                Best_Readiness=("TradeReadiness", "max"),
                Bullish_Pct=("Trend", lambda s: (s == "BULLISH").mean() * 100),
                Buy_Setups=("Decision", lambda s: s.isin(["BUY NOW", "BUY ON PULLBACK", "BUY ON BREAKOUT", "BUY / MANAGE RISK"]).sum()),
                Stocks=("Kode", "count")
            )
            .reset_index()
            .sort_values(
                ["Average_Opportunity", "Bullish_Pct", "Best_Opportunity"],
                ascending=[False, False, False]
            )
        )

        sector_rank["Average_Score"] = sector_rank["Average_Score"].round(1)
        sector_rank["Average_Opportunity"] = sector_rank["Average_Opportunity"].round(1)
        sector_rank["Best_Opportunity"] = sector_rank["Best_Opportunity"].round(1)
        sector_rank["Average_Readiness"] = sector_rank["Average_Readiness"].round(1)
        sector_rank["Best_Readiness"] = sector_rank["Best_Readiness"].round(1)
        sector_rank["Bullish_Pct"] = sector_rank["Bullish_Pct"].round(0)

        st.dataframe(
            sector_rank.head(15),
            width="stretch",
            hide_index=True
        )

        # ----------------------------------------------------
        # FILTERED RANKING
        # ----------------------------------------------------

        st.subheader("📋 Ranking Setelah Filter")

        if filtered.empty:
            st.warning(
                "Tidak ada saham yang memenuhi filter."
            )
        else:
            st.dataframe(
                filtered[
                    [
                        "Kode","Nama","Sektor","Price",
                        "Score","Opportunity","TradeReadiness","EntryQuality",
                        "Setup","Decision","Trend","Signal","RSI","Volume","R:R","Breakout"
                    ]
                ].head(100),
                width="stretch",
                hide_index=True
            )

        # ----------------------------------------------------
        # QUICK TRADING PLAN
        # ----------------------------------------------------

        st.subheader("🎯 Trading Plan — Kandidat Terpilih")
        plan_df = filtered[filtered["R:R"] >= 1.5].head(10).copy()
        if plan_df.empty:
            st.info("Belum ada kandidat dengan R:R ≥ 1.5 setelah filter.")
        else:
            plan_df["Buy Zone"] = plan_df["Price"].apply(lambda v: f"{v*0.99:,.0f}–{v*1.01:,.0f}")
            plan_df["Stop Loss"] = plan_df["StopLoss"].apply(lambda v: f"{v:,.0f}")
            plan_df["TP1"] = plan_df["TP1"].apply(lambda v: f"{v:,.0f}")
            plan_df["TP2"] = plan_df["TP2"].apply(lambda v: f"{v:,.0f}")
            st.dataframe(
                plan_df[["Kode", "Setup", "Decision", "TradeReadiness", "EntryQuality", "Buy Zone", "Stop Loss", "TP1", "TP2", "R:R"]],
                width="stretch", hide_index=True
            )

        # ----------------------------------------------------
        # ANALISIS SAHAM PILIHAN
        # ----------------------------------------------------

        st.subheader("🔎 Analisis Saham Pilihan")

        choices = filtered["Kode"].tolist()

        if choices:

            selected = st.selectbox(
                "Pilih saham",
                choices
            )

            if st.button(
                "📈 BUKA ANALISIS SAHAM",
                width="stretch"
            ):
                st.session_state["selected_stock"] = selected
                st.rerun()

        # ----------------------------------------------------
        # DOWNLOAD CSV
        # ----------------------------------------------------

        st.subheader("💾 Export Hasil Scanner")

        csv = result.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Full IDX Ranking CSV",
            data=csv,
            file_name="sanggul_full_idx_scanner.csv",
            mime="text/csv",
            width="stretch"
        )

    else:
        st.warning(
            "Klik SCAN SELURUH IDX SEKARANG untuk memulai."
        )


# ============================================================
# SINGLE STOCK
# ============================================================

else:

    st.header("🔎 Analisis Saham")

    default_stock = st.session_state.get(
        "selected_stock",
        "BBRI"
    )

    c1, c2 = st.columns([4,1])

    with c1:
        kode = st.text_input(
            "Kode saham BEI",
            value=default_stock
        )

    with c2:
        st.write("")
        update = st.button(
            "🔄 UPDATE DATA",
            width="stretch"
        )

    if update:
        detailed_data.clear()

    if kode:

        with st.spinner(
            "Mengambil data historis saham..."
        ):
            data = detailed_data(kode)

        if data.empty:
            st.error(
                f"Data {kode.upper()}.JK tidak tersedia."
            )
            st.stop()

        df = detailed_indicators(data)
        last = df.iloc[-1]

        close = float(last["Close"])

        # Basic detailed score
        score = 0

        if close > last["MA20"]: score += 10
        if close > last["MA50"]: score += 10
        if close > last["MA200"]: score += 15
        if last["MA20"] > last["MA50"] > last["MA200"]: score += 15
        if 50 <= last["RSI"] <= 70: score += 15
        if last["MACD"] > last["MACD_Signal"]: score += 10
        if last["Volume_Ratio"] >= 1.2: score += 10
        if close > last["MA20"] > last["MA50"]: score += 15

        score = min(score, 100)

        support = float(last["Support20"])
        resistance = float(last["Resistance20"])
        atr = float(last["ATR"])

        risk = max(1.25 * atr, close * 0.02)
        stop = close - risk
        tp1 = resistance if resistance > close else close + atr
        tp2 = close + 2 * risk
        tp3 = close + 3 * risk

        reward = max(tp1 - close, 0)
        rr = reward / risk if risk > 0 else 0

        if score >= 80 and rr >= 2:
            signal = "STRONG BUY"
        elif score >= 75 and rr >= 1.5:
            signal = "BUY"
        elif (resistance-close)/close <= 0.025 and score >= 60:
            signal = "WAIT FOR BREAKOUT"
        elif score < 50:
            signal = "SELL / AVOID"
        else:
            signal = "WAIT"

        trend = (
            "BULLISH" if score >= 75
            else "NEUTRAL" if score >= 55
            else "BEARISH"
        )

        st.success(
            f"Data {kode.upper()}.JK berhasil diperoleh."
        )

        st.caption(
            f"Data terakhir: {df.index[-1].strftime('%d-%m-%Y')}"
        )

        c1,c2,c3,c4 = st.columns(4)

        with c1:
            st.metric(
                "Harga Terakhir",
                rupiah(close)
            )

        with c2:
            st.metric(
                "Technical Score",
                f"{score}/100"
            )

        with c3:
            st.metric(
                "Trend",
                trend
            )

        with c4:
            st.metric(
                "Signal",
                signal
            )

        st.divider()

        st.subheader("🎯 Support & Resistance")

        s1,s2,s3,s4 = st.columns(4)

        with s1:
            st.metric(
                "Support",
                rupiah(support)
            )

        with s2:
            st.metric(
                "Harga",
                rupiah(close)
            )

        with s3:
            st.metric(
                "Resistance",
                rupiah(resistance)
            )

        with s4:
            st.metric(
                "Jarak Resistance",
                f"{(resistance-close)/close*100:.2f}%"
            )

        st.subheader("📐 Risk / Reward")

        r1,r2,r3 = st.columns(3)

        with r1:
            st.metric("Risk", rupiah(risk))

        with r2:
            st.metric(
                "Potential Reward TP1",
                rupiah(reward)
            )

        with r3:
            st.metric(
                "R:R",
                f"1 : {rr:.2f}"
            )

        st.subheader("🎯 Trading Plan")

        p1,p2,p3 = st.columns(3)

        with p1:
            buy_low = max(
                support,
                close - 0.75 * atr
            )
            buy_high = close

            st.info(
                f"### 🟢 BUY ZONE\n\n"
                f"**{rupiah(buy_low)}**\n\n"
                f"sampai\n\n"
                f"**{rupiah(buy_high)}**"
            )

        with p2:
            st.error(
                f"### 🛑 STOP LOSS\n\n"
                f"**{rupiah(stop)}**"
            )

        with p3:
            st.success(
                f"### 🎯 TARGET\n\n"
                f"TP1 : **{rupiah(tp1)}**\n\n"
                f"TP2 : **{rupiah(tp2)}**\n\n"
                f"TP3 : **{rupiah(tp3)}**"
            )

        st.divider()

        st.subheader(
            "🕯️ Candlestick + MA + Bollinger Bands"
        )

        chart = df.dropna(
            subset=["MA20","MA50","MA200"]
        ).tail(180)

        fig = go.Figure()

        fig.add_trace(
            go.Candlestick(
                x=chart.index,
                open=chart["Open"],
                high=chart["High"],
                low=chart["Low"],
                close=chart["Close"],
                name="Price"
            )
        )

        for col,name in [
            ("MA20","MA20"),
            ("MA50","MA50"),
            ("MA200","MA200"),
            ("BB_Upper","BB Upper"),
            ("BB_Lower","BB Lower")
        ]:
            fig.add_trace(
                go.Scatter(
                    x=chart.index,
                    y=chart[col],
                    mode="lines",
                    name=name
                )
            )

        fig.add_hline(
            y=support,
            annotation_text="Support"
        )

        fig.add_hline(
            y=resistance,
            annotation_text="Resistance"
        )

        fig.update_layout(
            height=650,
            xaxis_rangeslider_visible=False,
            hovermode="x unified"
        )

        st.plotly_chart(
            fig,
            width="stretch"
        )

        st.subheader("📊 Technical Indicators")

        i1,i2,i3,i4 = st.columns(4)

        with i1:
            st.metric(
                "RSI 14",
                f"{last['RSI']:.2f}"
            )

        with i2:
            st.metric(
                "MACD",
                f"{last['MACD']:.2f}"
            )

        with i3:
            st.metric(
                "Volume Ratio",
                f"{last['Volume_Ratio']:.2f}x"
            )

        with i4:
            st.metric(
                "ATR 14",
                rupiah(last["ATR"])
            )

        st.subheader(
            "📋 Data Teknikal Terakhir"
        )

        st.dataframe(
            df[
                [
                    "Close","MA20","MA50","MA200",
                    "RSI","MACD","MACD_Signal",
                    "ATR","Volume_Ratio"
                ]
            ].tail(10),
            width="stretch"
        )

        st.caption(
            "Data harga berasal dari Yahoo Finance melalui yfinance, "
            "bukan feed tick-by-tick resmi BEI. Universe emiten berasal "
            "dari metadata saham IDX yang diperbarui berkala. "
            "Signal adalah alat bantu analisis, bukan jaminan keuntungan."
        )
