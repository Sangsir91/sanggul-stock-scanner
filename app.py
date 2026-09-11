
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import time
from io import StringIO

# ============================================================
# SANGGUL STOCK SCANNER IDX V6.7
# FULL IDX SCANNER
# IHSG -> SECTOR -> ALL IDX -> TECHNICAL -> OPPORTUNITY
# ============================================================

st.set_page_config(
    page_title="Sanggul Stock Scanner IDX V6.7",
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

def fast_analysis(df, focus_days=126):
    """Fast technical engine: keep 2y history for MA200, but weight recent 3/6-month behavior."""
    if df.empty or len(df) < 210:
        return None

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    # Recent analysis window: MA200 still uses the full 2y history, while
    # momentum/structure gets an explicit recent 3-6 month focus.
    focus_days = int(max(63, min(focus_days, len(df))))
    recent = df.tail(focus_days)
    focus_return = float(recent["Close"].iloc[-1] / recent["Close"].iloc[0] - 1.0) * 100 if len(recent) > 1 else 0.0
    focus_high = float(recent["High"].max())
    focus_low = float(recent["Low"].min())

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
    roc60 = close.pct_change(60) * 100
    roc120 = close.pct_change(120) * 100

    # ----------------------------------------------------
    # FLOW PROXY (NOT OFFICIAL FOREIGN NET FLOW)
    # Uses price-volume behavior available from Yahoo Finance.
    # ----------------------------------------------------
    hl_range = (high - low).replace(0, np.nan)
    mfm = ((close - low) - (high - close)) / hl_range
    cmf20 = (mfm * volume).rolling(20).sum() / volume.rolling(20).sum()
    obv = (np.sign(close.diff()).fillna(0) * volume).cumsum()
    obv_change20 = obv.diff(20) / volume.rolling(20).mean()
    up_volume20 = volume.where(close >= close.shift(1), 0).rolling(20).sum()
    down_volume20 = volume.where(close < close.shift(1), 0).rolling(20).sum()
    up_down_volume_ratio = up_volume20 / down_volume20.replace(0, np.nan)

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
        "ROC60": roc60,
        "ROC120": roc120,
        "CMF20": cmf20,
        "OBVChange20": obv_change20,
        "UpDownVolume": up_down_volume_ratio,
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
    roc60v = float(x["ROC60"]) if pd.notna(x["ROC60"]) else 0.0
    roc120v = float(x["ROC120"]) if pd.notna(x["ROC120"]) else 0.0
    cmf = float(x["CMF20"])
    obv_change = float(x["OBVChange20"])
    up_down_vol = float(x["UpDownVolume"]) if pd.notna(x["UpDownVolume"]) else 1.0

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
    # Recent-window momentum: reward positive 3-6 month behavior.
    if focus_return > 10:
        momentum_score += 2
    elif focus_return > 0:
        momentum_score += 1

    momentum_score = min(20, momentum_score)

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
    # Recent focus-window position: avoid rewarding stocks near the bottom of
    # their recent 3-6 month range.
    if focus_high > focus_low:
        focus_position = (px - focus_low) / (focus_high - focus_low)
        if focus_position >= 0.70:
            structure_score += 1
        elif focus_position < 0.30:
            structure_score -= 2
    structure_score = int(max(0, min(15, structure_score)))
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
    # ENTRY ZONE / TIMING ENGINE
    # ---------------------------
    prior_resistance = float(prior_res) if pd.notna(prior_res) else resistance

    if setup == "PULLBACK":
        anchor = ma20v if distance_ma20 <= distance_ma50 else ma50v
        entry_low = max(support, anchor - 0.50 * atrv)
        entry_high = anchor + 0.25 * atrv
        entry_ready = entry_low <= px <= entry_high
        entry_status = "READY" if entry_ready else (
            "WAIT FOR PULLBACK" if px > entry_high else "BELOW IDEAL ZONE"
        )
    elif setup == "BREAKOUT":
        entry_low = max(prior_resistance, px - 0.25 * atrv)
        entry_high = prior_resistance + 0.75 * atrv
        entry_ready = px <= entry_high
        entry_status = "READY" if entry_ready else "EXTENDED"
    elif setup == "NEAR BREAKOUT":
        entry_low = prior_resistance * 1.002
        entry_high = prior_resistance + 0.50 * atrv
        entry_ready = False
        entry_status = "WAIT FOR BREAKOUT"
    elif setup == "TREND CONTINUATION":
        entry_low = max(support, ma20v - 0.50 * atrv)
        entry_high = ma20v + 0.50 * atrv
        entry_ready = entry_low <= px <= entry_high
        entry_status = "READY" if entry_ready else "WAIT FOR BETTER ENTRY"
    else:
        entry_low = max(support, px - atrv)
        entry_high = px
        entry_ready = False
        entry_status = "WAIT"

    # ---------------------------
    # TRADE READINESS = 100
    # Focuses on whether the setup is tradable NOW, not merely attractive.
    # ---------------------------
    readiness = 0.0
    readiness += (trend_score / 30.0) * 25.0

    setup_readiness = {
        "BREAKOUT": 23,
        "PULLBACK": 23,
        "NEAR BREAKOUT": 17,
        "TREND CONTINUATION": 16,
        "WATCH": 7,
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

    if 50 <= rsiv <= 68:
        readiness += 14
    elif 45 <= rsiv < 50 or 68 < rsiv <= 72:
        readiness += 9
    elif rsiv > 72:
        readiness += 2
    else:
        readiness += 3

    readiness += 8 if vr >= 1.5 else 6 if vr >= 1.2 else 4 if vr >= 1.0 else 1

    # Timing is a decisive gate.
    if entry_ready:
        readiness += 7
    else:
        readiness -= 4

    # Overbought or extended price reduces immediate readiness.
    if rsiv > 70:
        readiness -= 5
    if setup == "BREAKOUT" and px > prior_resistance + 1.0 * atrv:
        readiness -= 6
        entry_status = "EXTENDED"
        entry_ready = False

    trade_readiness = round(max(0.0, min(100.0, readiness)), 1)

    # ---------------------------
    # DECISION ENGINE V6.3
    # ---------------------------
    if rr < 1.0 or technical_score < 45:
        signal = "SELL / AVOID"
        decision = "AVOID"
        reason = "Risk/reward atau kualitas teknikal tidak memadai."
    elif breakout and entry_ready and trade_readiness >= 78 and rsiv <= 70 and rr >= 1.8:
        signal = "STRONG BUY — BREAKOUT"
        decision = "BUY NOW"
        reason = "Breakout terkonfirmasi, timing masih wajar, momentum sehat, dan R:R memadai."
    elif pullback and entry_ready and trade_readiness >= 78 and rr >= 1.8:
        signal = "BUY — PULLBACK"
        decision = "BUY ON PULLBACK"
        reason = "Harga berada di zona pullback yang logis dengan trend bullish dan R:R memadai."
    elif pullback and not entry_ready and px > entry_high:
        signal = "WAIT — PULLBACK"
        decision = "WAIT FOR PULLBACK"
        reason = "Trend bullish, tetapi harga masih di atas zona entry pullback."
    elif near_breakout and rr >= 1.5:
        signal = "WAIT — BREAKOUT"
        decision = "BUY ON BREAKOUT"
        reason = "Harga dekat resistance; tunggu breakout dan konfirmasi volume."
    elif continuation and entry_ready and trade_readiness >= 75 and rr >= 1.5:
        signal = "BUY — TREND"
        decision = "BUY / MANAGE RISK"
        reason = "Trend continuation dengan timing entry yang masih berada di zona wajar."
    elif continuation:
        signal = "WAIT — BETTER ENTRY"
        decision = "WAIT"
        reason = "Trend positif tetapi harga belum berada di zona entry yang optimal."
    else:
        signal = "WAIT"
        decision = "WAIT"
        reason = "Setup belum memenuhi seluruh syarat entry."

    # Entry quality now depends on actual entry timing and decision.
    if decision in ("BUY NOW", "BUY ON PULLBACK", "BUY / MANAGE RISK") and entry_ready and rr >= 2.0:
        entry_quality = "EXCELLENT"
    elif decision in ("BUY NOW", "BUY ON PULLBACK", "BUY / MANAGE RISK") and entry_ready and rr >= 1.5:
        entry_quality = "GOOD"
    elif decision == "BUY ON BREAKOUT":
        entry_quality = "WAIT FOR BREAKOUT"
    elif decision in ("WAIT FOR PULLBACK", "WAIT"):
        entry_quality = "WAIT"
    elif decision == "AVOID":
        entry_quality = "POOR"
    else:
        entry_quality = "FAIR"

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

    # Flow proxy score 0-100. This is NOT official foreign net buy/sell data.
    flow_score = 50.0
    flow_score += 18 if cmf > 0.10 else 11 if cmf > 0.03 else 5 if cmf >= 0 else -8
    flow_score += 14 if obv_change > 0.50 else 9 if obv_change > 0.20 else 4 if obv_change >= 0 else -8
    flow_score += 14 if up_down_vol >= 1.30 else 9 if up_down_vol >= 1.05 else 3 if up_down_vol >= 0.90 else -8
    flow_score = round(max(0.0, min(100.0, flow_score)), 1)
    flow_label = (
        "ACCUMULATION PROXY" if flow_score >= 70
        else "POSITIVE PROXY" if flow_score >= 55
        else "NEUTRAL PROXY" if flow_score >= 45
        else "DISTRIBUTION PROXY"
    )

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
        "EntryStatus": entry_status,
        "EntryLow": float(entry_low),
        "EntryHigh": float(entry_high),
        "DecisionReason": reason,
        "RSI": rsiv,
        "ROC20": roc,
        "ROC60": roc60v,
        "ROC120": roc120v,
        "FocusReturn": focus_return,
        "FocusDays": focus_days,
        "FocusHigh": focus_high,
        "FocusLow": focus_low,
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
        "FlowProxyScore": flow_score,
        "FlowProxy": flow_label,
        "CMF20": cmf,
        "OBVChange20": obv_change,
        "UpDownVolume": up_down_vol,
        "Date": w.index[-1]
    }


# ------------------------------------------------------------
# FULL IDX SCANNER
# ------------------------------------------------------------

def scan_full_idx(universe, batch_size=40, focus_days=126, progress_callback=None):
    results = []
    tickers = universe["Yahoo"].tolist()

    total_batches = int(np.ceil(len(tickers) / batch_size))

    for batch_no in range(total_batches):
        start = batch_no * batch_size
        batch_tickers = tickers[start:start + batch_size]

        batch = download_batch(tuple(batch_tickers), period="1y")

        for ticker in batch_tickers:
            df = extract_ticker_data(batch, ticker)
            a = fast_analysis(df, focus_days=focus_days)

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
# V6 FUNDAMENTAL + VALUATION ENGINE
# ============================================================

def _num(info, key):
    try:
        v = info.get(key)
        if v is None or isinstance(v, (dict, list, str)) and not isinstance(v, (int, float)):
            return np.nan
        v = float(v)
        return v if np.isfinite(v) else np.nan
    except Exception:
        return np.nan


def _score_band(v, bands):
    if pd.isna(v):
        return 50.0
    for threshold, score in bands:
        if v <= threshold:
            return float(score)
    return float(bands[-1][1])


@st.cache_data(ttl=21600, show_spinner=False)
def get_fundamental(kode):
    """Retrieve Yahoo Finance fundamentals for one stock. Missing fields remain neutral."""
    try:
        info = yf.Ticker(yahoo_symbol(kode)).get_info()
    except Exception:
        return {"Available": False, "Error": "Fundamental data unavailable"}

    if not info:
        return {"Available": False, "Error": "Fundamental data unavailable"}

    pe = _num(info, "trailingPE")
    fpe = _num(info, "forwardPE")
    pb = _num(info, "priceToBook")
    ps = _num(info, "priceToSalesTrailing12Months")
    ev_ebitda = _num(info, "enterpriseToEbitda")
    roe = _num(info, "returnOnEquity") * 100 if not pd.isna(_num(info, "returnOnEquity")) else np.nan
    margin = _num(info, "profitMargins") * 100 if not pd.isna(_num(info, "profitMargins")) else np.nan
    op_margin = _num(info, "operatingMargins") * 100 if not pd.isna(_num(info, "operatingMargins")) else np.nan
    revenue_growth = _num(info, "revenueGrowth") * 100 if not pd.isna(_num(info, "revenueGrowth")) else np.nan
    earnings_growth = _num(info, "earningsGrowth") * 100 if not pd.isna(_num(info, "earningsGrowth")) else np.nan
    debt_equity = _num(info, "debtToEquity")
    current_ratio = _num(info, "currentRatio")
    market_cap = _num(info, "marketCap")
    roa = _num(info, "returnOnAssets") * 100 if not pd.isna(_num(info, "returnOnAssets")) else np.nan
    dividend_yield = _num(info, "dividendYield") * 100 if not pd.isna(_num(info, "dividendYield")) else np.nan
    payout_ratio = _num(info, "payoutRatio") * 100 if not pd.isna(_num(info, "payoutRatio")) else np.nan
    operating_cashflow = _num(info, "operatingCashflow")
    free_cashflow = _num(info, "freeCashflow")
    total_cash = _num(info, "totalCash")
    total_debt = _num(info, "totalDebt")

    # Absolute valuation score is retained as a fallback. V6.3 later
    # replaces it with a sector-relative score when enough peer data exists.
    val_parts = [
        _score_band(pe, [(12,20),(18,16),(25,12),(35,8),(1e9,3)]),
        _score_band(fpe, [(12,10),(18,8),(25,6),(35,4),(1e9,2)]),
        _score_band(pb, [(1.5,10),(2.5,8),(4,6),(7,3),(1e9,1)]),
        _score_band(ps, [(2.5,5),(5,4),(10,2),(1e9,1)]),
        _score_band(ev_ebitda, [(8,5),(12,4),(18,2),(1e9,1)]),
    ]
    valuation_score = round(sum(val_parts), 1)

    quality_parts = [
        _score_band(roe, [(5,8),(10,14),(15,18),(25,20),(1e9,20)]),
        _score_band(margin, [(0,5),(5,10),(10,14),(20,18),(1e9,20)]),
        _score_band(revenue_growth, [(-10,4),(0,8),(5,12),(10,16),(1e9,20)]),
        _score_band(earnings_growth, [(-10,4),(0,8),(5,12),(10,16),(1e9,20)]),
        _score_band(debt_equity, [(30,20),(75,16),(150,12),(250,7),(1e9,3)]),
    ]
    fundamental_score = round(sum(quality_parts), 1)

    # Clamp because some missing-value neutral scores can otherwise distort interpretation.
    fundamental_score = max(0.0, min(100.0, fundamental_score))
    valuation_score = max(0.0, min(50.0, valuation_score)) * 2

    return {
        "Available": True,
        "FundamentalScore": fundamental_score,
        "ValuationScore": valuation_score,
        "PE": pe, "ForwardPE": fpe, "PB": pb, "PS": ps,
        "EV_EBITDA": ev_ebitda, "ROE": roe, "ProfitMargin": margin,
        "OperatingMargin": op_margin, "RevenueGrowth": revenue_growth,
        "EarningsGrowth": earnings_growth, "DebtEquity": debt_equity,
        "CurrentRatio": current_ratio, "MarketCap": market_cap,
        "ROA": roa, "DividendYield": dividend_yield, "PayoutRatio": payout_ratio,
        "OperatingCashFlow": operating_cashflow, "FreeCashFlow": free_cashflow,
        "TotalCash": total_cash, "TotalDebt": total_debt,
        "BusinessSector": info.get("sector", ""),
    }



def sector_group(sector):
    """Normalize broad business groups for peer-relative valuation."""
    s = str(sector or "").lower()
    if any(k in s for k in ["finance", "bank", "insurance", "securities"]):
        return "FINANCIALS"
    if any(k in s for k in ["energy", "oil", "gas", "coal", "minerals"]):
        return "ENERGY / MINERALS"
    if any(k in s for k in ["technology", "software", "communications"]):
        return "TECH / COMMUNICATIONS"
    if any(k in s for k in ["health", "medical", "pharma"]):
        return "HEALTHCARE"
    if any(k in s for k in ["consumer", "retail", "food", "beverage"]):
        return "CONSUMER"
    if any(k in s for k in ["transport", "logistics"]):
        return "TRANSPORT / LOGISTICS"
    if any(k in s for k in ["utilities", "infrastructure"]):
        return "UTILITIES / INFRA"
    if any(k in s for k in ["industrial", "manufacturing", "producer"]):
        return "INDUSTRIALS"
    return "OTHER"


def _lower_is_better_percentile(series, max_reasonable=None):
    """Return 0-100 where lower positive multiples score higher, excluding obvious outliers."""
    s = pd.to_numeric(series, errors="coerce")
    valid = s.where((s > 0) & np.isfinite(s))
    if max_reasonable is not None:
        valid = valid.where(valid <= max_reasonable)
    if valid.notna().sum() < 2:
        return pd.Series(50.0, index=series.index)
    return (1.0 - valid.rank(pct=True, method="average")) * 100.0


def apply_sector_relative_valuation(work):
    """
    V6.3 valuation engine.
    Uses peer-relative percentiles within broad sector groups.
    Financials emphasize PE/PB; non-financials emphasize PE/EV/EBITDA/PS.
    Falls back to 50 when a metric or peer group is insufficient.
    """
    w = work.copy()
    w["SectorGroup"] = w["Sektor"].map(sector_group)

    scores = pd.DataFrame(index=w.index)
    for col in ["PE", "ForwardPE", "PB", "PS", "EV_EBITDA"]:
        scores[col] = 50.0

    for group, idx in w.groupby("SectorGroup", dropna=False).groups.items():
        sub = w.loc[idx]
        use_peer = len(sub) >= 3

        metric_scores = pd.DataFrame(index=sub.index)
        for col in ["PE", "ForwardPE", "PB", "PS", "EV_EBITDA"]:
            limits = {"PE":200, "ForwardPE":200, "PB":50, "PS":100, "EV_EBITDA":100}
            metric_scores[col] = _lower_is_better_percentile(sub[col], limits[col]) if use_peer else 50.0

        # For very small peer groups, compare to all enriched names as a fallback.
        if not use_peer:
            for col in ["PE", "ForwardPE", "PB", "PS", "EV_EBITDA"]:
                metric_scores[col] = _lower_is_better_percentile(w[col], limits[col]).reindex(sub.index).fillna(50.0)

        if group == "FINANCIALS":
            # Banks/financials: book value and earnings multiples are more relevant.
            val = (
                0.40 * metric_scores["PB"] +
                0.35 * metric_scores["PE"] +
                0.10 * metric_scores["ForwardPE"] +
                0.10 * metric_scores["PS"] +
                0.05 * metric_scores["EV_EBITDA"]
            )
        else:
            val = (
                0.30 * metric_scores["PE"] +
                0.20 * metric_scores["ForwardPE"] +
                0.20 * metric_scores["EV_EBITDA"] +
                0.20 * metric_scores["PS"] +
                0.10 * metric_scores["PB"]
            )

        scores.loc[sub.index, "SectorRelativeValuation"] = val

    w["ValuationScore"] = scores["SectorRelativeValuation"].fillna(w["ValuationScore"].fillna(50.0)).round(1)
    w["ValuationMethod"] = np.where(
        w["SectorGroup"].eq("FINANCIALS"),
        "Peer-relative: PE/PB weighted",
        "Peer-relative: PE/EVEBITDA/PS weighted"
    )
    return w


def enrich_v6(result, limit=150, style="📈 Swing Trading Mingguan", progress_callback=None):
    """Enrich top technical candidates with fundamentals; flow proxy is already available for all rows."""
    if result.empty:
        return result

    work = result.copy()
    # Enrich the most promising technical/trading candidates to keep cloud runtime practical.
    candidates = (
        work.sort_values(["Opportunity", "TradeReadiness", "R:R"], ascending=[False, False, False])
        .head(limit)["Kode"].tolist()
    )
    fund_map = {}
    total = len(candidates)
    for i, kode in enumerate(candidates, 1):
        fund_map[kode] = get_fundamental(kode)
        if progress_callback:
            progress_callback(i / max(total, 1))
        time.sleep(0.08)

    def getv(k, field):
        d = fund_map.get(k, {})
        return d.get(field, np.nan)

    for field in [
        "FundamentalScore","ValuationScore","PE","ForwardPE","PB","PS",
        "EV_EBITDA","ROE","ProfitMargin","OperatingMargin","RevenueGrowth",
        "EarningsGrowth","DebtEquity","CurrentRatio","MarketCap","ROA","DividendYield","PayoutRatio","OperatingCashFlow","FreeCashFlow","TotalCash","TotalDebt","BusinessSector"
    ]:
        work[field] = work["Kode"].map(lambda k: getv(k, field))

    work["V6Enriched"] = work["Kode"].isin(candidates) & work["FundamentalScore"].notna()

    # V6.7 calibration: keep raw scores for auditability, but compress extreme 100s
    # so a perfect-looking score is reserved for genuinely exceptional cases.
    work["FundamentalScoreRaw"] = pd.to_numeric(work["FundamentalScore"], errors="coerce")
    work["FundamentalScore"] = (50.0 + (work["FundamentalScoreRaw"] - 50.0) * 0.85).clip(5, 95).round(1)

    # Sector-relative valuation followed by shrinkage toward neutral.
    work = apply_sector_relative_valuation(work)
    work["ValuationScoreRaw"] = pd.to_numeric(work["ValuationScore"], errors="coerce")
    work["ValuationScore"] = (50.0 + (work["ValuationScoreRaw"] - 50.0) * 0.75).clip(10, 95).round(1)

    # Neutral fallback for missing fundamentals, while keeping a flag so users know.
    f = work["FundamentalScore"].fillna(50.0)
    v = work["ValuationScore"].fillna(50.0)
    flow = work["FlowProxyScore"].fillna(50.0)

    work["FinalScore"] = (
        0.30 * work["Score"]
        + 0.20 * work["TradeReadiness"]
        + 0.25 * f
        + 0.10 * v
        + 0.15 * flow
    ).round(1)

    # V6 decision overlay: technical timing remains the gate; fundamentals/valuation can confirm or downgrade.
    def v6_decision(r):
        base = r["Decision"]
        if base == "AVOID":
            return "AVOID"
        if not bool(r["V6Enriched"]):
            return base
        if r["FundamentalScore"] < 35 or r["ValuationScore"] < 35:
            return "WAIT — FUNDAMENTAL CHECK" if base != "AVOID" else "AVOID"
        if base in ["BUY NOW", "BUY ON PULLBACK", "BUY ON BREAKOUT", "BUY / MANAGE RISK"] and r["FinalScore"] >= 70:
            return base
        if r["FinalScore"] >= 65 and base != "AVOID":
            return "WATCH — V6 CONFIRMATION"
        return "WAIT"

    work["V6Decision"] = work.apply(v6_decision, axis=1)
    work["V6Status"] = np.where(work["V6Enriched"], "ENRICHED", "TECHNICAL ONLY")
    work = apply_style_scores(work, style)
    work = apply_action_engine(work, style)
    return work.sort_values(["ActionScore", "StyleScore", "FinalScore", "TradeReadiness"], ascending=[False, False, False, False]).reset_index(drop=True)


# ============================================================
# V6.3 MULTI-STYLE ENGINE
# ============================================================
STYLE_CONFIG = {
    "⚡ Trading Harian": {
        "focus_days": 63,
        "description": "Fokus timing pendek, momentum, volume, breakout/pullback dan R:R.",
        "note": "Data yang tersedia adalah candle Daily; mode ini adalah tactical daily/same-day screening, bukan sinyal intraday real-time.",
    },
    "📈 Swing Trading Mingguan": {
        "focus_days": 126,
        "description": "Fokus trend 3–6 bulan, setup pullback/breakout, readiness dan R:R.",
        "note": "Cocok untuk posisi beberapa hari sampai beberapa minggu dengan konfirmasi Daily.",
    },
    "🏦 Investor Jangka Panjang": {
        "focus_days": 252,
        "description": "Fokus kualitas bisnis, fundamental, valuasi relatif sektor dan trend jangka menengah.",
        "note": "Fundamental/valuasi harus menjadi konfirmasi utama; harga tetap diperhatikan untuk timing akumulasi.",
    },
}

def rr_score(rr):
    if pd.isna(rr):
        return 50.0
    if rr >= 3: return 100.0
    if rr >= 2.5: return 90.0
    if rr >= 2: return 80.0
    if rr >= 1.5: return 65.0
    if rr >= 1: return 45.0
    return 20.0

def apply_style_scores(df, style):
    w=df.copy()
    rrn=w["R:R"].apply(rr_score)
    tech=w["Score"].fillna(50)
    ready=w["TradeReadiness"].fillna(50)
    flow=w["FlowProxyScore"].fillna(50)
    focus=w["FocusReturn"].fillna(0)
    focus_score=(50 + focus.clip(-30,30) * (50/30)).clip(0,100)
    fund=w.get("FundamentalScore", pd.Series(50.0,index=w.index)).fillna(50)
    val=w.get("ValuationScore", pd.Series(50.0,index=w.index)).fillna(50)

    if style == "⚡ Trading Harian":
        w["StyleScore"]=(0.40*tech + 0.30*ready + 0.15*flow + 0.10*rrn + 0.05*focus_score).round(1)
        w["StyleDecision"]=np.where(
            w["Decision"].isin(["BUY NOW","BUY ON BREAKOUT","BUY ON PULLBACK","BUY / MANAGE RISK"]),
            w["Decision"],
            w["Decision"]
        )
    elif style == "📈 Swing Trading Mingguan":
        w["StyleScore"]=(0.35*tech + 0.30*ready + 0.20*rrn + 0.10*flow + 0.05*focus_score).round(1)
        w["StyleDecision"]=w["Decision"]
    else:
        w["StyleScore"]=(0.15*tech + 0.10*ready + 0.10*flow + 0.35*fund + 0.30*val).round(1)
        def inv_decision(r):
            if not bool(r.get("V6Enriched",False)):
                return "FUNDAMENTAL CHECK"
            if r["FundamentalScore"] >= 70 and r["ValuationScore"] >= 60 and r["StyleScore"] >= 70:
                return "ACCUMULATE / HOLD"
            if r["FundamentalScore"] >= 60 and r["ValuationScore"] >= 50:
                return "WATCH / ACCUMULATE ON WEAKNESS"
            if r["FundamentalScore"] < 40 or r["ValuationScore"] < 35:
                return "AVOID / REVIEW"
            return "WATCH"
        w["StyleDecision"]=w.apply(inv_decision,axis=1)
    return w

# ============================================================
# V6.4 MULTI-STYLE ACTION ENGINE
# ============================================================
def apply_action_engine(df, style):
    """Convert style quality into an actionable score with timing discipline."""
    w = df.copy()
    def _series(name, default):
        if name in w.columns:
            return pd.to_numeric(w[name], errors="coerce").fillna(default)
        return pd.Series(float(default), index=w.index)

    score = _series("StyleScore", 50.0)
    rr = _series("R:R", 0.0)
    rsi = _series("RSI", 50.0)
    entry = w.get("EntryStatus", pd.Series("WAIT", index=w.index)).astype(str)
    decision = w.get("Decision", pd.Series("WAIT", index=w.index)).astype(str)

    action = score.copy()
    if style in ["⚡ Trading Harian", "📈 Swing Trading Mingguan"]:
        action += np.where(entry.eq("READY"), 8, 0)
        action += np.where(entry.eq("WAIT FOR PULLBACK"), -5, 0)
        action += np.where(entry.eq("WAIT FOR BREAKOUT"), -4, 0)
        action += np.where(entry.eq("WAIT FOR BETTER ENTRY"), -5, 0)
        action += np.where(entry.eq("EXTENDED"), -12, 0)
        action += np.where(decision.str.startswith("BUY"), 6, 0)
        action += np.where(decision.eq("AVOID"), -25, 0)
        action += np.where(rsi >= 80, -12, np.where(rsi >= 72, -6, 0))
        action += np.where(rr >= 3, 7, np.where(rr >= 2, 4, np.where(rr < 1.2, -8, 0)))
    else:
        fund = _series("FundamentalScore", 50.0)
        val = _series("ValuationScore", 50.0)
        action += (fund - 50) * 0.18
        action += (val - 50) * 0.18
        action += np.where(fund >= 70, 5, 0)
        action += np.where(val >= 60, 4, 0)
        action += np.where(fund < 40, -12, 0)
        action += np.where(val < 35, -10, 0)
        action += np.where(decision.eq("AVOID"), -20, 0)

    w["ActionScore"] = action.clip(0, 100).round(1)

    def action_label(r):
        if style == "🏦 Investor Jangka Panjang":
            if not bool(r.get("V6Enriched", False)):
                return "FUNDAMENTAL CHECK"
            if r["FundamentalScore"] >= 70 and r["ValuationScore"] >= 60 and r["ActionScore"] >= 70:
                return "ACCUMULATE / HOLD"
            if r["FundamentalScore"] >= 60 and r["ValuationScore"] >= 50 and r["ActionScore"] >= 60:
                return "WATCH / ACCUMULATE"
            if r["FundamentalScore"] < 40 or r["ValuationScore"] < 35:
                return "AVOID / REVIEW"
            return "WATCH"
        if r["Decision"] == "AVOID": return "AVOID"
        if r["EntryStatus"] == "EXTENDED": return "WAIT — DO NOT CHASE"
        if r["Decision"] == "BUY NOW": return "BUY NOW"
        if r["Decision"] == "BUY ON PULLBACK": return "BUY ON PULLBACK"
        if r["Decision"] == "BUY ON BREAKOUT": return "BUY ON BREAKOUT"
        if r["Decision"] == "BUY / MANAGE RISK": return "BUY / MANAGE RISK"
        if r["EntryStatus"] == "WAIT FOR PULLBACK": return "WAIT FOR PULLBACK"
        if r["EntryStatus"] == "WAIT FOR BREAKOUT": return "WAIT FOR BREAKOUT"
        if r["EntryStatus"] == "WAIT FOR BETTER ENTRY": return "WAIT FOR BETTER ENTRY"
        return "WAIT"

    w["Action"] = w.apply(action_label, axis=1)
    return w


def style_board(result, style):
    w = apply_style_scores(result.copy(), style)
    if "V6Enriched" not in w.columns:
        w["V6Enriched"] = False
        w["FundamentalScore"] = 50.0
        w["ValuationScore"] = 50.0
    w = apply_action_engine(w, style)
    return w.sort_values(["ActionScore", "StyleScore", "TradeReadiness"], ascending=[False, False, False]).reset_index(drop=True)

# ============================================================
# V6.6 DATA QUALITY + OUTLIER PROTECTION + CONFIDENCE ENGINE
# ============================================================
def _band_score(v, bands):
    if pd.isna(v):
        return 50.0
    for threshold, score in bands:
        if v <= threshold:
            return float(score)
    return float(bands[-1][1])


def calculate_investor_metrics(w):
    """Build investor-quality sub-scores from enriched fundamentals.
    Missing data stays neutral and is flagged rather than treated as excellent.
    """
    x = w.copy()
    def col(name, default):
        if name in x.columns:
            return pd.to_numeric(x[name], errors="coerce")
        return pd.Series(default, index=x.index, dtype=float)
    roe = col("ROE", 50)
    roa = col("ROA", 50)
    margin = col("ProfitMargin", 50)
    rev = col("RevenueGrowth", 0)
    earn = col("EarningsGrowth", 0)
    de = col("DebtEquity", 100)
    cr = col("CurrentRatio", 1)
    pe = col("PE", np.nan)
    pb = col("PB", np.nan)
    fcf = col("FreeCashFlow", np.nan)
    ocf = col("OperatingCashFlow", np.nan)
    dy = col("DividendYield", np.nan)

    x["QualityScore"] = (
        0.35 * roe.clip(0, 30).fillna(15).mul(100/30) +
        0.20 * roa.clip(0, 15).fillna(7.5).mul(100/15) +
        0.25 * margin.clip(-10, 30).fillna(10).add(10).mul(100/40) +
        0.20 * (100 - de.clip(0, 300).fillna(150).mul(100/300))
    ).clip(0,100).round(1)

    x["GrowthScore"] = (
        0.45 * (50 + rev.clip(-20, 30).fillna(0) * (50/30)) +
        0.45 * (50 + earn.clip(-30, 50).fillna(0) * (50/50)) +
        0.10 * cr.clip(0, 3).fillna(1.5).mul(100/3)
    ).clip(0,100).round(1)

    x["BalanceSheetScore"] = (
        0.60 * (100 - de.clip(0, 300).fillna(150).mul(100/300)) +
        0.40 * cr.clip(0, 3).fillna(1.5).mul(100/3)
    ).clip(0,100).round(1)

    # Cash-flow quality: positive FCF/OCF gets rewarded; missing data is neutral.
    cf_quality = pd.Series(50.0, index=x.index)
    cf_quality.loc[ocf > 0] += 20
    cf_quality.loc[fcf > 0] += 20
    cf_quality.loc[(ocf > 0) & (fcf > 0)] += 10
    cf_quality.loc[(ocf < 0) | (fcf < 0)] -= 20
    x["CashFlowScore"] = cf_quality.clip(0,100).round(1)

    # Investor valuation uses the already sector-relative valuation score.
    # IMPORTANT: DataFrame.get() returns a scalar when the fallback is scalar;
    # therefore always construct a Series aligned to the DataFrame index.
    if "ValuationScore" in x.columns:
        valuation_series = pd.to_numeric(x["ValuationScore"], errors="coerce")
    else:
        valuation_series = pd.Series(50.0, index=x.index)
    x["InvestorValuationScore"] = valuation_series.fillna(50.0).clip(0,100).round(1)
    x["InvestorFundamentalScore"] = (
        0.35*x["QualityScore"] +
        0.25*x["GrowthScore"] +
        0.20*x["BalanceSheetScore"] +
        0.20*x["CashFlowScore"]
    ).round(1)

    # V6.6: data quality/confidence. Missing or implausible fundamentals reduce confidence,
    # rather than silently receiving a full-quality interpretation.
    validity_rules = {
        "ROE": lambda z: z.between(-100, 100),
        "ROA": lambda z: z.between(-100, 100),
        "ProfitMargin": lambda z: z.between(-100, 100),
        "RevenueGrowth": lambda z: z.between(-1000, 1000),
        "EarningsGrowth": lambda z: z.between(-1000, 1000),
        "DebtEquity": lambda z: z.between(0, 2000),
        "CurrentRatio": lambda z: z.between(0, 100),
        "PE": lambda z: z.between(0.1, 200),
        "PB": lambda z: z.between(0.05, 50),
        "PS": lambda z: z.between(0.05, 100),
        "EV_EBITDA": lambda z: z.between(0.1, 100),
        "ForwardPE": lambda z: z.between(0.1, 200),
    }
    valid_cols = []
    for name, rule in validity_rules.items():
        if name in x.columns:
            z = pd.to_numeric(x[name], errors="coerce")
            valid_cols.append(rule(z).fillna(False).rename(name))
        else:
            valid_cols.append(pd.Series(False, index=x.index, name=name))
    validity = pd.concat(valid_cols, axis=1)
    x["InvestorDataCompleteness"] = (validity.mean(axis=1)*100).round(0)
    x["InvestorDataConfidence"] = (
        0.70*x["InvestorDataCompleteness"] +
        0.30*np.where(validity[["PE","PB","PS","EV_EBITDA","ForwardPE"]].any(axis=1), 100, 45)
    ).clip(0,100).round(0)

    base_investor_score = (
        0.45*x["InvestorFundamentalScore"] +
        0.25*x["InvestorValuationScore"] +
        0.15*x["FlowProxyScore"].fillna(50) +
        0.15*x["TradeReadiness"].fillna(50)
    )
    confidence_factor = 0.65 + 0.35*(x["InvestorDataConfidence"]/100.0)
    x["InvestorScoreRaw"] = base_investor_score.clip(0,100).round(1)
    x["InvestorScore"] = (base_investor_score * confidence_factor).clip(0,100).round(1)

    # Valuation confidence: if valuation multiples are missing/implausible, downgrade certainty.
    val_valid = validity[["PE","PB","PS","EV_EBITDA","ForwardPE"]]
    x["ValuationConfidence"] = (val_valid.mean(axis=1)*100).round(0)
    x["FlowProxyConfidence"] = np.where(x["FlowProxyScore"].notna(), 100, 0)

    def grade(r):
        score=r["InvestorScore"]
        completeness=r["InvestorDataCompleteness"]
        confidence = r["InvestorDataConfidence"]
        if confidence < 50: return "C — DATA LIMITED"
        if score >= 85 and confidence >= 80: return "A+ — HIGH QUALITY"
        if score >= 78: return "A — QUALITY"
        if score >= 70: return "B — GOOD"
        if score >= 60: return "C — SPECULATIVE"
        return "D — REVIEW"
    x["InvestmentGrade"] = x.apply(grade, axis=1)

    def inv_action(r):
        if r["InvestorDataConfidence"] < 50:
            return "FUNDAMENTAL CHECK"
        if r["InvestorScore"] >= 80 and r["InvestorValuationScore"] >= 60 and r["QualityScore"] >= 65 and r["ValuationConfidence"] >= 40:
            return "ACCUMULATE / HOLD"
        if r["InvestorScore"] >= 70 and r["InvestorValuationScore"] >= 50:
            return "WATCH / ACCUMULATE ON WEAKNESS"
        if r["InvestorScore"] < 55 or r["QualityScore"] < 40:
            return "AVOID / REVIEW"
        return "WATCH"
    x["InvestorAction"] = x.apply(inv_action, axis=1)
    return x


def investor_board_v65(result):
    x = calculate_investor_metrics(result.copy())
    return x.sort_values(["InvestorScore","QualityScore","InvestorValuationScore"], ascending=False).reset_index(drop=True)

# Override investor branch with V6.5 intelligence while preserving Day/Swing engine.
_old_apply_style_scores = apply_style_scores
def apply_style_scores(df, style):
    w = _old_apply_style_scores(df, style)
    if style == "🏦 Investor Jangka Panjang":
        w = calculate_investor_metrics(w)
        w["StyleScore"] = w["InvestorScore"]
        w["StyleDecision"] = w["InvestorAction"]
    return w

# ============================================================
# SAFE DISPLAY HELPERS
# ============================================================
def safe_display_columns(df, columns):
    """Return requested display columns without crashing when optional
    enrichment fields are missing from a dataframe."""
    out = df.copy()
    return out.reindex(columns=columns)

# ============================================================
# V6.7 CONVICTION ENGINE
# ============================================================
def _safe_num_series(df, name, default=50.0):
    if name in df.columns:
        return pd.to_numeric(df[name], errors="coerce").fillna(default)
    return pd.Series(float(default), index=df.index)


def calculate_conviction(df, style):
    """Final conviction score: technical + timing + fundamentals + valuation + flow.
    Missing enrichment never becomes an artificial 100; confidence acts as a brake.
    """
    x = df.copy()
    tech = _safe_num_series(x, "Score", 50)
    readiness = _safe_num_series(x, "TradeReadiness", 50)
    rr = x.get("R:R", pd.Series(np.nan, index=x.index)).apply(rr_score)
    flow = _safe_num_series(x, "FlowProxyScore", 50)
    fund = _safe_num_series(x, "FundamentalScore", 50)
    val = _safe_num_series(x, "ValuationScore", 50)
    confidence = _safe_num_series(x, "InvestorDataConfidence", 50)
    val_conf = _safe_num_series(x, "ValuationConfidence", 50)

    # Timing score: READY best, EXTENDED penalized.
    entry = x.get("EntryStatus", pd.Series("WAIT", index=x.index)).astype(str)
    timing = pd.Series(60.0, index=x.index)
    timing += np.where(entry.eq("READY"), 25, 0)
    timing += np.where(entry.eq("WAIT FOR PULLBACK"), 10, 0)
    timing += np.where(entry.eq("WAIT FOR BREAKOUT"), 8, 0)
    timing += np.where(entry.eq("WAIT FOR BETTER ENTRY"), 5, 0)
    timing += np.where(entry.eq("EXTENDED"), -25, 0)
    timing = timing.clip(0, 100)

    # Different weights by style. Investor requires actual fundamental evidence.
    if style == "⚡ Trading Harian":
        raw = 0.38*tech + 0.25*readiness + 0.15*timing + 0.10*rr + 0.12*flow
    elif style == "📈 Swing Trading Mingguan":
        raw = 0.30*tech + 0.25*readiness + 0.18*timing + 0.17*rr + 0.10*flow
    else:
        raw = 0.20*tech + 0.15*readiness + 0.25*fund + 0.22*val + 0.10*flow + 0.08*timing

    # Confidence brake: 65%–100% of raw score.
    conf = (0.60*confidence + 0.40*val_conf).clip(0,100)
    factor = 0.65 + 0.35*(conf/100.0)
    x["ConvictionRaw"] = raw.clip(0,100).round(1)
    x["ConvictionScore"] = (raw*factor).clip(0,100).round(1)
    x["ConvictionConfidence"] = conf.round(0)

    def grade(v):
        if v >= 85: return "A — HIGH CONVICTION"
        if v >= 75: return "B — STRONG"
        if v >= 65: return "C — WATCH"
        if v >= 55: return "D — LOW"
        return "E — AVOID"
    x["ConvictionGrade"] = x["ConvictionScore"].apply(grade)

    def decision(r):
        c = r["ConvictionScore"]
        conf = r["ConvictionConfidence"]
        entry = str(r.get("EntryStatus", "WAIT"))
        base = str(r.get("Decision", "WAIT"))
        if c < 55:
            return "AVOID / LOW CONVICTION"
        if entry == "EXTENDED" and c >= 70:
            return "WAIT — DO NOT CHASE"
        if style == "🏦 Investor Jangka Panjang":
            if c >= 85 and conf >= 75:
                return "ACCUMULATE / HOLD"
            if c >= 75 and conf >= 60:
                return "ACCUMULATE ON WEAKNESS"
            return "WATCH"
        if c >= 85 and base.startswith("BUY"):
            return base
        if c >= 75 and base.startswith("BUY"):
            return base
        if c >= 70:
            return "WATCH FOR CONFIRMATION"
        return "WAIT"

    x["ConvictionDecision"] = x.apply(decision, axis=1)
    return x


# Final override: style score remains useful for ranking, ConvictionScore becomes the
# decision-quality metric shown to the user.
_base_apply_style_scores_v67 = apply_style_scores
def apply_style_scores(df, style):
    w = _base_apply_style_scores_v67(df, style)
    w = calculate_conviction(w, style)
    # Investor style uses conviction rather than raw fundamental/valuation scores alone.
    if style == "🏦 Investor Jangka Panjang":
        w["StyleScore"] = w["ConvictionScore"]
        w["StyleDecision"] = w["ConvictionDecision"]
    return w


def style_board(result, style):
    w = apply_style_scores(result.copy(), style)
    if "V6Enriched" not in w.columns:
        w["V6Enriched"] = False
    w = apply_action_engine(w, style)
    return w.sort_values(["ConvictionScore", "ActionScore", "TradeReadiness"], ascending=[False, False, False]).reset_index(drop=True)

# ============================================================
# UI
# ============================================================

st.title("📈 SANGGUL STOCK SCANNER IDX")
st.caption("V6.7 — MULTI-STYLE + CONVICTION ENGINE")

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

    st.subheader("🎯 Pilih Gaya Investasi / Trading")
    style = st.selectbox(
        "Mode analisis",
        list(STYLE_CONFIG.keys()),
        index=1,
        help="Mode mengubah bobot ranking dan fokus analisis. Data saham tetap Daily."
    )
    style_cfg = STYLE_CONFIG[style]
    st.info(f"**{style}** — {style_cfg['description']} {style_cfg['note']}")

    if universe.empty:
        st.error(
            "Universe IDX gagal dimuat. Periksa koneksi internet."
        )
        st.stop()

    u1, u2, u3, u4 = st.columns(4)

    with u1:
        st.metric(
            "Universe IDX",
            f"{len(universe):,}".replace(",", ".")
        )

    with u2:
        st.metric(
            "Data Historis",
            "2 Tahun"
        )

    with u3:
        focus_choice = st.selectbox(
            "Fokus Analisis",
            ["3 Bulan", "6 Bulan"],
            index=0 if style == "⚡ Trading Harian" else 1,
            help="MA200 tetap dihitung dari 2 tahun data; scoring momentum dan struktur diberi fokus pada periode ini."
        )

    focus_days_ui = 63 if focus_choice == "3 Bulan" else 126

    with u4:
        st.metric(
            "Batch",
            "50 saham"
        )

    st.info(
        "V6.3 mengambil 2 tahun data historis untuk menjaga kestabilan MA200, "
        f"sementara analisis utama berfokus pada {focus_choice.lower()}. "
        "Saham yang tidak memiliki data historis cukup atau tidak tersedia di Yahoo Finance otomatis dilewati."
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
                batch_size=50,
                focus_days=focus_days_ui,
                progress_callback=update_progress
            )

        progress.progress(1.0)
        status.success(
            f"Scanning selesai: {len(result)} saham berhasil dianalisis."
        )

        st.session_state["full_scan"] = result
        st.session_state["scan_style"] = style
        st.session_state.pop("v6_scan", None)

    result = st.session_state.get(
        "full_scan",
        pd.DataFrame()
    )
    if st.session_state.get("scan_style") != style:
        st.session_state.pop("full_scan", None)
        st.session_state.pop("v6_scan", None)
        result = pd.DataFrame()

    if not result.empty:

        st.success(
            f"{len(result)} saham memiliki data teknikal yang cukup "
            f"untuk dianalisis."
        )
        st.caption("V6.7 memisahkan Day Trading, Swing Trading, dan Investor. Investor memakai fundamental, valuasi relatif sektor, Flow Proxy, serta Data Quality/Confidence. Flow Proxy BUKAN data resmi foreign net buy/sell.")

        st.subheader("🎯 Multi-Style Action Board")
        st.info("Ranking dipisahkan untuk tiga gaya. Untuk Investor Jangka Panjang, ranking final membutuhkan enrichment fundamental & valuasi.")
        bcols = st.columns(3)
        for col, board_style in zip(bcols, STYLE_CONFIG.keys()):
            board = style_board(result, board_style).head(5)
            with col:
                st.markdown(f"**{board_style}**")
                st.dataframe(safe_display_columns(board, ["Kode","ActionScore","Action","Setup","Trend","R:R"]), width="stretch", hide_index=True)

        st.subheader("🧠 V6.7 Conviction Engine — Technical + Fundamental + Valuation + Flow")
        st.info("Agar Full IDX tetap ringan di cloud, fundamental diperiksa untuk 150 kandidat teratas. V6.6 memvalidasi outlier, menghitung data completeness dan confidence, lalu menurunkan bobot saham yang datanya kurang dapat dipercaya.")
        if st.button("🧠 ENRICH TOP 150 — FUNDAMENTAL, VALUATION & INVESTOR QUALITY", width="stretch"):
            p6 = st.progress(0)
            s6 = st.empty()
            def update_v6(v):
                p6.progress(v)
                s6.info(f"Enrichment fundamental: {v*100:.0f}%")
            with st.spinner("Mengambil fundamental & valuation kandidat teratas..."):
                v6_result = enrich_v6(result, limit=150, style=style, progress_callback=update_v6)
            p6.progress(1.0)
            s6.success(f"V6.5 enrichment selesai untuk {int(v6_result['V6Enriched'].sum())} saham.")
            st.session_state["v6_scan"] = v6_result
            st.session_state["v6_style"] = style

        v6_result = st.session_state.get("v6_scan", pd.DataFrame())
        if st.session_state.get("v6_style") != style:
            v6_result = pd.DataFrame()
        if not v6_result.empty:
            st.subheader(f"⭐ Top 10 — {style}")
            v6top = v6_result[v6_result["V6Enriched"]].head(10)
            cols6 = ["Kode","Nama","Sektor","Price","ActionScore","Action","StyleScore","FinalScore","Score","TradeReadiness","FundamentalScore","ValuationScore","ValuationMethod","FlowProxyScore","StyleDecision"]
            st.dataframe(safe_display_columns(v6top, cols6), width="stretch", hide_index=True)

            if style == "🏦 Investor Jangka Panjang":
                st.subheader("🏦 Investor Intelligence — Investment Grade")
                invtop = investor_board_v65(v6_result[v6_result["V6Enriched"]].copy()).head(15)
                invcols = ["Kode","Nama","Sektor","Price","InvestorScore","InvestorScoreRaw","InvestmentGrade","InvestorAction","QualityScore","GrowthScore","BalanceSheetScore","CashFlowScore","InvestorValuationScore","ValuationConfidence","InvestorDataCompleteness","InvestorDataConfidence"]
                st.dataframe(safe_display_columns(invtop, invcols), width="stretch", hide_index=True)
                st.caption("InvestorScore sudah disesuaikan dengan Data Confidence. Outlier valuasi tidak diperlakukan sebagai data valid. Flow Proxy hanya indikator price-volume, bukan foreign net buy/sell resmi.")

            st.subheader("🧠 V6.7 Conviction Ranking")
            convtop = v6_result[v6_result["V6Enriched"]].sort_values(["ConvictionScore","ConvictionConfidence"], ascending=[False,False]).head(20)
            convcols = ["Kode","Nama","Sektor","Price","ConvictionScore","ConvictionGrade","ConvictionConfidence","ConvictionRaw","ConvictionDecision","Score","TradeReadiness","FundamentalScore","ValuationScore","FlowProxyScore","R:R","EntryStatus"]
            st.dataframe(safe_display_columns(convtop, convcols), width="stretch", hide_index=True)
            st.caption("Conviction bukan jaminan return. Skor ini menggabungkan kualitas teknikal, timing entry, fundamental, valuasi relatif, flow proxy dan confidence data.")

            st.subheader("💰 Fundamental & Sector-Relative Valuation")
            st.caption("V6.7 membandingkan valuasi dengan peer sektor/bisnis yang sejenis; Financials memberi bobot lebih besar pada PE/PB. Jika peer kurang, skor memakai fallback yang lebih netral.")
            ftop = v6_result[v6_result["V6Enriched"]].head(20).copy()
            fcols = ["Kode","Price","Sektor","SectorGroup","FundamentalScore","ValuationScore","ValuationMethod","PE","PB","PS","ROE","RevenueGrowth","EarningsGrowth","DebtEquity","ValuationConfidence","InvestorDataConfidence"]
            st.dataframe(safe_display_columns(ftop, fcols), width="stretch", hide_index=True)

            st.subheader("💧 Flow Proxy — Price & Volume")
            flowtop = v6_result.sort_values("FlowProxyScore", ascending=False).head(20)
            flowcols = ["Kode","Price","FlowProxyScore","FlowProxy","CMF20","OBVChange20","UpDownVolume"]
            st.dataframe(safe_display_columns(flowtop, flowcols), width="stretch", hide_index=True)

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
            "Setup", "Decision", "Trend", "RSI", "R:R", "Breakout", "EntryStatus"
        ]
        st.dataframe(
            top10[top_cols],
            width="stretch",
            hide_index=True
        )

        st.subheader("🎯 Top Trading Readiness")
        readiness_cols = [
            "Kode", "Nama", "Sektor", "Price", "TradeReadiness",
            "EntryQuality", "EntryStatus", "Setup", "Decision", "Trend", "RSI", "R:R"
        ]
        ready_top = (
            result[(result["Decision"] != "AVOID") & (result["TradeReadiness"] >= 60)]
            .sort_values(["TradeReadiness", "Opportunity", "R:R"], ascending=[False, False, False])
            .head(10)
        )
        if ready_top.empty:
            st.info("Belum ada setup dengan trade readiness yang layak.")
        else:
            st.dataframe(safe_display_columns(ready_top, readiness_cols), width="stretch", hide_index=True)

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
        # V6 FINAL RANKING
        # ----------------------------------------------------
        if not v6_result.empty:
            st.subheader(f"🏆 Final Ranking — {style}")
            v6_filtered = v6_result.copy()
            if selected_sector != "Semua":
                v6_filtered = v6_filtered[v6_filtered["Sektor"] == selected_sector]
            v6_filtered = v6_filtered[v6_filtered["Score"] >= min_score]
            if breakout != "Semua":
                v6_filtered = v6_filtered[v6_filtered["Breakout"] == breakout]
            v6_filtered = v6_filtered[v6_filtered["V6Enriched"]]
            if signal == "BUY":
                v6_filtered = v6_filtered[v6_filtered["V6Decision"].str.contains("BUY", na=False)]
            elif signal == "WAIT":
                v6_filtered = v6_filtered[v6_filtered["V6Decision"].str.contains("WAIT|WATCH", na=False, regex=True)]
            elif signal == "SELL":
                v6_filtered = v6_filtered[v6_filtered["V6Decision"].str.contains("AVOID", na=False)]
            v6_filtered = v6_filtered.sort_values(["StyleScore","FinalScore","TradeReadiness"], ascending=[False,False,False]).head(50)
            if v6_filtered.empty:
                st.info("Belum ada saham V6 yang memenuhi filter.")
            else:
                st.dataframe(safe_display_columns(v6_filtered, ["Kode","Nama","Sektor","Price","ActionScore","Action","ConvictionScore","ConvictionGrade","ConvictionDecision","StyleScore","FinalScore","Setup","TradeReadiness","FundamentalScore","ValuationScore","FlowProxyScore","R:R"]), width="stretch", hide_index=True)

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
                Ready_Trades=("EntryQuality", lambda s: s.isin(["EXCELLENT", "GOOD"]).sum()),
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
                        "Score","Opportunity","TradeReadiness","EntryQuality","EntryStatus",
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
            plan_df["Buy Zone"] = plan_df.apply(lambda r: f"{r['EntryLow']:,.0f}–{r['EntryHigh']:,.0f}", axis=1)
            plan_df["Stop Loss"] = plan_df["StopLoss"].apply(lambda v: f"{v:,.0f}")
            plan_df["TP1"] = plan_df["TP1"].apply(lambda v: f"{v:,.0f}")
            plan_df["TP2"] = plan_df["TP2"].apply(lambda v: f"{v:,.0f}")
            st.dataframe(
                plan_df[["Kode", "Setup", "Decision", "TradeReadiness", "EntryQuality", "EntryStatus", "Buy Zone", "Stop Loss", "TP1", "TP2", "R:R"]],
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

        if not v6_result.empty:
            csv6 = v6_result.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download V6.7 Final Ranking CSV",
                data=csv6,
                file_name="sanggul_v6_7_conviction_ranking.csv",
                mime="text/csv",
                width="stretch"
            )

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
