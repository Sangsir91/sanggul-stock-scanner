import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Sanggul Stock Scanner V10.5",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {max-width: 1480px; padding-top: 1rem; padding-bottom: 2rem;}
h1 {letter-spacing:-.035em;}
.section-title {font-size:1.35rem;font-weight:750;margin:1rem 0 .6rem;}
.info-box {background:#eff6ff;border:1px solid #dbeafe;border-radius:12px;padding:11px 14px;color:#1d4ed8;font-size:.9rem;}
.card {border:1px solid #e5e7eb;border-radius:14px;padding:14px 15px;background:#fff;min-height:168px;box-shadow:0 1px 2px rgba(16,24,40,.03);}
.card-head {display:flex;justify-content:space-between;align-items:center;gap:8px;}
.code {font-size:1.05rem;font-weight:800;color:#172033;}
.company {font-size:.78rem;color:#667085;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.price {font-size:1.2rem;font-weight:800;margin:11px 0 5px;color:#172033;}
.meta {font-size:.81rem;color:#475467;line-height:1.55;}
.reason {font-size:.77rem;color:#667085;margin-top:8px;line-height:1.4;}
.pill {display:inline-block;border-radius:999px;padding:4px 9px;font-size:.67rem;font-weight:800;}
.pass {background:#dcfce7;color:#166534;}
.caution {background:#fef3c7;color:#92400e;}
.fail {background:#fee2e2;color:#991b1b;}
.note {font-size:.8rem;color:#667085;}
@media (max-width:768px) {
  .block-container {padding:.65rem .7rem 1.5rem;}
  h1 {font-size:1.65rem;}
  .card {min-height:0;padding:12px;}
  .price {font-size:1.1rem;}
  .meta,.reason {font-size:.75rem;}
}
</style>
""", unsafe_allow_html=True)

DEFAULT_UNIVERSE = (
    "BBCA,BBRI,BMRI,BBNI,BRIS,BBTN,ADRO,ANTM,INCO,PTBA,ITMG,MDKA,AKRA,"
    "ASII,TLKM,ISAT,EXCL,UNVR,ICBP,INDF,KLBF,MYOR,AMRT,ACES,ERAA,JPFA,"
    "CPIN,MAIN,SMGR,INTP,PGAS,MEDC,ELSA,PGEO,ESSA,MIKA,HEAL,BSDE,CTRA,"
    "PWON,SCMA,EMTK,GOTO,BUKA,ARTO,AMMN,DEWA,AGII,ADES,ADMF,"
    "AALI,ABMM,ACRO,ADCP,ADHI,ADMR,AGRO,AHAP,AKPI,ALDO,AMAN,ANJT,"
    "APLN,ARCI,ARGO,ARNA,ARTI,ASLC,ASRI,ASSA,ATLA,AUTO,AVIA,"
    "BBKP,BBLD,BBMS,BESS,BFIN,BGTG,BINA,BIRD,BISI,BJBR,BJTM,"
    "BKSL,BLTZ,BMTR,BNGA,BNBR,BNLI,BOGA,BRPT,BUAH,CARS,CARE,"
    "CBPE,CEKA,CINT,CLEO,CMRY,COCO,CPRO,CSAP,CUAN,DART,DAYA,"
    "DCII,DEPO,DEST,DFAM,DKFT,DMAS,DOID,DSNG,DUCK,DUTI,ECII,"
    "EDGE,EKAD,ELIT,EMDE,ENRG,ERAL,ESIP,ESTA,EURO,FIRE,FMII,"
    "FORU,GEMA,GGRM,GJTL,GLVA,GOOD,GOLF,GRIA,HAIS,HATM,HEXA,"
    "HITS,HRUM,HYGN,IBST,ICBP,IDPR,IFSH,IGAR,IMAS,IMPC,INAF,"
    "INAI,INCF,INDS,INDY,INET,IPCC,IPCM,IPOL,IRRA,ISSP,ITMA,"
    "JAST,JECC,JGLE,JKON,JMAS,JRPT,JSKY,KAEF,KBLV,KDSI,KEEN,"
    "KINO,KLIN,KOKA,KOPI,KOTA,KRAS,LABA,LAND,LAPD,LCGP,LINK,"
    "LION,LPKR,LRNA,MAPA,MAPI,MARK,MAYA,MBAP,MBSS,MCAS,MCOL,"
    "MDIY,META,MFIN,MGRO,MIDI,MINA,MLBI,MLIA,MLPL,MNCN,MPMX,"
    "MSIN,MTDL,MTEL,MTPS,MYOH,NANO,NETV,NFCX,NIRO,NISP,NOBU,"
    "NRCA,OBMD,OCAP,OILS,OMED,OPMS,PACK,PAMG,PANI,PANS,PART,"
    "PBID,PCAR,PDES,PEGE,PEHA,PGJO,PGUN,PKPK,PLIN,PNBN,PNBS,"
    "POLI,PPRO,PRDA,PRIM,PSAB,PSDN,PSGO,PTBA,PTIS,PUDP,PURA,"
    "PZZA,RALS,RANC,RELF,RIGS,RISE,RMKE,ROCK,ROTI,RSCH,RSGK,"
    "RUIS,SAFE,SAME,SAME,SCNP,SDPC,SEMA,SERV,SILO,SIMP,SIPD,"
    "SKBM,SKLT,SMBR,SMCB,SMDR,SMKL,SMKM,SMLE,SMRA,SMRU,SMSM,"
    "SNLK,SOCI,SONA,SOSS,SOTS,SPMA,SQMI,SRIL,SRTG,SSIA,SSMS,"
    "STAA,STTP,SUGI,SULI,SUNS,SURI,TALF,TAPG,TAYS,TCID,TCPI,"
    "TEBE,TECH,TELE,TFAS,TFCO,TFII,TGKA,TINS,TIRA,TIRT,TLDN,"
    "TMAS,TOBA,TOPS,TOTO,TOWR,TPIA,TRIM,TRIS,TRON,TRUK,TRUS,"
    "TUGU,TYRE,UANG,UCID,ULTJ,UNIC,UNIT,UNIQ,UNTD,UVCR,VICI,"
    "VISI,VOKS,VRNA,WAPO,WEHA,WIIM,WINS,WOOD,WSKT,WTON,YPAS,"
    "ZATA,ZINC"
)

STYLES = {
    "Trading Harian": {
        "score": "Daily Score", "gate": "Daily Gate", "reason": "Daily Reason",
        "return": "Return 1M", "icon": "⚡", "focus": "1–5 hari"
    },
    "Swing Trading Mingguan": {
        "score": "Swing Score", "gate": "Swing Gate", "reason": "Swing Reason",
        "return": "Return 3M", "icon": "📊", "focus": "1–8 minggu"
    },
    "Investor Jangka Panjang": {
        "score": "Investor Score", "gate": "Investor Gate", "reason": "Investor Reason",
        "return": "Return 6M", "icon": "🌱", "focus": "6 bulan+"
    },
}

def yf_code(code):
    return code if code.endswith(".JK") else code + ".JK"

def clean_codes(text):
    result = []
    for item in str(text).replace("\n", ",").split(","):
        code = item.strip().upper().replace(".JK", "")
        if code and code not in result:
            result.append(code)
    return result

@st.cache_data(ttl=900, show_spinner=False)
def download_history(code):
    try:
        data = yf.download(
            yf_code(code),
            period="2y",
            interval="1d",
            auto_adjust=False,
            progress=False,
            threads=False,
        )
        if data is None or data.empty:
            return pd.DataFrame()
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [item[0] for item in data.columns]
        data.columns = [str(c).title() for c in data.columns]
        required = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in data.columns for col in required):
            return pd.DataFrame()
        return data[required].dropna()
    except Exception:
        return pd.DataFrame()

def period_return(close, days):
    if len(close) <= days:
        return np.nan
    return (float(close.iloc[-1]) / float(close.iloc[-days-1]) - 1) * 100

def calc_rsi(close, window=14):
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(window).mean()
    loss = (-delta.clip(upper=0)).rolling(window).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def add_indicators(data):
    x = data.copy()
    close = x["Close"]
    x["MA20"] = close.rolling(20).mean()
    x["MA50"] = close.rolling(50).mean()
    x["MA200"] = close.rolling(200).mean()
    x["RSI"] = calc_rsi(close)
    true_range = pd.concat([
        x["High"] - x["Low"],
        (x["High"] - x["Close"].shift(1)).abs(),
        (x["Low"] - x["Close"].shift(1)).abs(),
    ], axis=1).max(axis=1)
    x["ATR"] = true_range.rolling(14).mean()
    x["VolRatio"] = x["Volume"] / x["Volume"].rolling(20).mean()
    x["High20Previous"] = x["High"].rolling(20).max().shift(1)
    x["Breakout20"] = x["Close"] > x["High20Previous"]
    return x

def latest(series):
    value = series.iloc[-1]
    return float(value) if pd.notna(value) else np.nan


@st.cache_data(ttl=900, show_spinner=False)
def market_regime():
    """Determine broad IDX regime using IHSG (^JKSE) trend and momentum."""
    try:
        d = yf.download("^JKSE", period="1y", interval="1d", auto_adjust=False, progress=False, threads=False)
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = [c[0] for c in d.columns]
        d.columns = [str(c).title() for c in d.columns]
        if "Close" not in d.columns or len(d) < 60:
            return {"regime":"Unknown", "score":50, "rsi":np.nan, "ma20":np.nan, "ma50":np.nan}
        c = d["Close"].dropna()
        ma20, ma50 = c.rolling(20).mean().iloc[-1], c.rolling(50).mean().iloc[-1]
        rsi = calc_rsi(c).iloc[-1]
        if c.iloc[-1] > ma20 > ma50 and rsi >= 52:
            regime = "Bullish"
            score = 80
        elif c.iloc[-1] < ma20 < ma50 and rsi < 48:
            regime = "Bearish"
            score = 25
        else:
            regime = "Sideways"
            score = 55
        return {"regime":regime, "score":score, "rsi":float(rsi), "ma20":float(ma20), "ma50":float(ma50)}
    except Exception:
        return {"regime":"Unknown", "score":50, "rsi":np.nan, "ma20":np.nan, "ma50":np.nan}

def adaptive_label(score, hard_fail=False, regime="Unknown"):
    if hard_fail or score < 45:
        return "Risk-Off / Avoid"
    threshold = {"Bullish":78, "Sideways":82, "Bearish":86}.get(regime, 82)
    if score >= threshold:
        return "Actionable Buy"
    if score >= 70:
        return "Watchlist – Strong Setup"
    if score >= 60:
        return "Watchlist – Early Setup"
    return "Caution – Mixed Signal"

def score_reason(score, trend_ok, momentum_ok, volume_ok, rs_ok, risk_ok, trigger):
    parts=[]
    if trend_ok: parts.append("trend mendukung")
    else: parts.append("trend belum terkonfirmasi")
    if momentum_ok: parts.append("momentum sehat")
    else: parts.append("momentum belum kuat")
    if volume_ok: parts.append("volume mendukung")
    else: parts.append("volume belum mengonfirmasi")
    if rs_ok: parts.append("relative strength positif")
    else: parts.append("relative strength netral/lemah")
    if not risk_ok: parts.append("risiko perlu diperhatikan")
    parts.append(f"trigger: {trigger}")
    return "; ".join(parts)

def analyze(code):
    regime_data = market_regime()
    regime = regime_data["regime"]
    raw = download_history(code)
    if raw.empty or len(raw) < 35:
        return None

    x = add_indicators(raw)
    close = x["Close"]
    price = latest(close)
    ma20, ma50, ma200 = latest(x["MA20"]), latest(x["MA50"]), latest(x["MA200"])
    rsi = latest(x["RSI"])
    vol_ratio = latest(x["VolRatio"])
    atr = latest(x["ATR"])
    breakout = bool(x["Breakout20"].iloc[-1]) if pd.notna(x["Breakout20"].iloc[-1]) else False

    r1, r3, r6, r2 = (
        period_return(close, 21),
        period_return(close, 63),
        period_return(close, 126),
        period_return(close, 504),
    )

    # Daily: momentum, liquidity and short-term structure.
    daily_score = 0
    if pd.notna(r1):
        daily_score += np.clip((r1 + 10) * 2.2, 0, 25)
    if pd.notna(vol_ratio):
        daily_score += np.clip((vol_ratio - 0.7) * 12, 0, 20)
    daily_score += 18 if breakout else (9 if pd.notna(ma20) and price > ma20 else 0)
    daily_score += 17 if pd.notna(rsi) and 48 <= rsi <= 72 else (
        10 if pd.notna(rsi) and 35 <= rsi <= 80 else 0
    )
    atr_pct = atr / price * 100 if pd.notna(atr) and price else np.nan
    daily_score += 15 if pd.notna(atr_pct) and 1 <= atr_pct <= 7 else (
        7 if pd.notna(atr_pct) and atr_pct < 10 else 0
    )
    daily_score = float(np.clip(daily_score, 0, 100))
    daily_core = pd.notna(ma20) and price > ma20 and pd.notna(rsi) and rsi >= 40
    daily_hard_fail = (
        pd.notna(atr_pct) and atr_pct > 12
    ) or (
        pd.notna(vol_ratio) and vol_ratio < 0.25
    )
    daily_gate = "FAIL" if daily_hard_fail else (
        "PASS" if daily_score >= 68 and daily_core else "CAUTION"
    )
    daily_reason = (
        "momentum pendek dan struktur mendukung"
        if daily_core else "struktur/momentum belum kuat"
    )
    if not breakout:
        daily_reason += "; belum breakout, momentum tetap dinilai"

    # Swing: medium-term return and MA alignment.
    swing_score = 0
    if pd.notna(r1):
        swing_score += np.clip((r1 + 15) * 1.2, 0, 20)
    if pd.notna(r3):
        swing_score += np.clip((r3 + 20) * 0.8, 0, 25)
    swing_score += 20 if pd.notna(ma50) and price > ma20 > ma50 else (
        12 if pd.notna(ma50) and price > ma50 else 0
    )
    swing_score += 15 if breakout else (10 if pd.notna(ma20) and price > ma20 else 0)
    swing_score += 15 if pd.notna(rsi) and 45 <= rsi <= 75 else 7
    swing_score = float(np.clip(swing_score, 0, 100))
    swing_core = pd.notna(ma50) and price > ma50 and pd.notna(r3) and r3 > 0
    swing_hard_fail = pd.notna(ma50) and price < ma50 * 0.92
    swing_gate = "FAIL" if swing_hard_fail else (
        "PASS" if swing_score >= 65 and swing_core else "CAUTION"
    )
    swing_reason = (
        "struktur MA dan return menengah mendukung"
        if swing_core else "tren menengah belum terkonfirmasi"
    )
    if not breakout:
        swing_reason += "; belum breakout, continuation/pullback tetap dinilai"

    # Investor: longer-term return and MA200 structure.
    investor_score = 0
    if pd.notna(r6):
        investor_score += np.clip((r6 + 20) * 0.8, 0, 25)
    if pd.notna(r2):
        investor_score += np.clip((r2 + 30) * 0.5, 0, 25)
    investor_score += 25 if pd.notna(ma200) and price > ma200 else (
        12 if pd.notna(ma50) and price > ma50 else 0
    )
    investor_score += 15 if pd.notna(rsi) and 40 <= rsi <= 75 else 7
    investor_score += 10 if pd.notna(ma50) and price > ma50 else 0
    investor_score = float(np.clip(investor_score, 0, 100))

    # Adaptive cross-style adjustments: reward alignment and penalize conflicting signals.
    trend_ok = bool(pd.notna(ma20) and pd.notna(ma50) and price > ma20 > ma50)
    momentum_ok = bool(pd.notna(rsi) and 45 <= rsi <= 72)
    volume_ok = bool(pd.notna(vol_ratio) and vol_ratio >= 0.8)
    rs_ok = bool(pd.notna(r3) and r3 > 0)
    risk_ok = bool(pd.notna(atr_pct) and atr_pct <= 10) if 'atr_pct' in locals() else True
    trigger = "Breakout 20 hari" if breakout else ("Reclaim MA20" if pd.notna(ma20) and price > ma20 else "Tunggu konfirmasi")
    if regime == "Bullish":
        regime_adj = 4
    elif regime == "Bearish":
        regime_adj = -4
    else:
        regime_adj = 0
    daily_score = float(np.clip(daily_score + regime_adj, 0, 100))
    swing_score = float(np.clip(swing_score + regime_adj, 0, 100))
    investor_score = float(np.clip(investor_score + regime_adj, 0, 100))
    # Investor hard/core conditions must be calculated before the combined risk gate.
    investor_core = pd.notna(ma200) and price > ma200 and pd.notna(r6) and r6 > -5
    investor_hard_fail = pd.notna(ma200) and price < ma200 * 0.85

    overall_score = float(max(daily_score, swing_score, investor_score))
    hard_fail_any = daily_hard_fail or swing_hard_fail or investor_hard_fail
    adaptive_status = adaptive_label(overall_score, hard_fail_any, regime)
    adaptive_reason = score_reason(overall_score, trend_ok, momentum_ok, volume_ok, rs_ok, risk_ok, trigger)

    investor_gate = "FAIL" if investor_hard_fail else (
        "PASS" if investor_score >= 65 and investor_core else "CAUTION"
    )
    investor_reason = (
        "tren panjang dan struktur mendukung"
        if investor_core else "tren panjang/return belum cukup kuat"
    )
    if pd.notna(r2) and r2 < 0:
        investor_reason += "; return 2 tahun negatif"

    scores = {
        "Trading Harian": daily_score,
        "Swing Trading Mingguan": swing_score,
        "Investor Jangka Panjang": investor_score,
    }
    primary = max(scores, key=scores.get)
    stop = price - 1.5 * atr if pd.notna(atr) else np.nan
    target = price + 2.0 * atr if pd.notna(atr) else np.nan

    return {
        "Code": code.upper(),
        "Name": code.upper(),
        "Price": price,
        "Daily Score": daily_score, "Daily Gate": daily_gate, "Daily Reason": daily_reason,
        "Swing Score": swing_score, "Swing Gate": swing_gate, "Swing Reason": swing_reason,
        "Investor Score": investor_score, "Investor Gate": investor_gate, "Investor Reason": investor_reason,
        "Primary Style": primary,
        "Market Regime": regime,
        "Adaptive Score": overall_score,
        "Adaptive Status": adaptive_status,
        "Adaptive Reason": adaptive_reason,
        "Trigger": trigger,
        "Confidence": "High" if sum([trend_ok,momentum_ok,volume_ok,rs_ok,risk_ok]) >= 4 else ("Medium" if sum([trend_ok,momentum_ok,volume_ok,rs_ok,risk_ok]) >= 2 else "Low"),
        "RSI": rsi, "Vol Ratio": vol_ratio,
        "MA20": ma20, "MA50": ma50, "MA200": ma200,
        "Return 1M": r1, "Return 3M": r3, "Return 6M": r6, "Return 2Y": r2,
        "Stop": stop, "Target": target, "_df": x,
    }

def fmt_num(value, decimals=1):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:,.{decimals}f}"

def fmt_pct(value):
    if value is None or pd.isna(value):
        return "—"
    return f"{value:+.2f}%"

def gate_html(gate):
    cls = gate.lower()
    return f'<span class="pill {cls}">{gate}</span>'

def price_bucket(price):
    if pd.isna(price):
        return "Tidak diketahui"
    if price < 100:
        return "< Rp100"
    if price < 500:
        return "Rp100–499"
    if price < 2000:
        return "Rp500–1.999"
    if price < 5000:
        return "Rp2.000–4.999"
    return "≥ Rp5.000"

def apply_price_filter(df, selected):
    if selected == "Semua harga":
        return df.copy()
    mapping = {
        "Di bawah Rp100": lambda x: x < 100,
        "Rp100–499": lambda x: (x >= 100) & (x < 500),
        "Rp500–1.999": lambda x: (x >= 500) & (x < 2000),
        "Rp2.000–4.999": lambda x: (x >= 2000) & (x < 5000),
        "Rp5.000 ke atas": lambda x: x >= 5000,
    }
    mask = mapping.get(selected, lambda x: pd.Series(True, index=x.index))(df["Price"])
    return df[mask].copy()

def show_low_price_board(df, min_score=0):
    st.markdown('<div class="section-title">💰 Top 10 Low-Price Opportunities</div>', unsafe_allow_html=True)
    st.caption("Papan eksplorasi saham berharga di bawah Rp100. Harga murah bukan sinyal beli; tetap periksa likuiditas, risiko, dan Gate.")
    low = df[df["Price"] < 100].copy()
    if min_score > 0:
        low = low[(low[["Daily Score", "Swing Score", "Investor Score"]].max(axis=1) >= min_score)]
    if low.empty:
        st.info("Belum ada saham di bawah Rp100 yang memenuhi batas score atau berhasil diambil datanya.")
        return
    low["Best Style"] = low[["Daily Score", "Swing Score", "Investor Score"]].idxmax(axis=1).str.replace(" Score", "", regex=False)
    low["Best Score"] = low[["Daily Score", "Swing Score", "Investor Score"]].max(axis=1).round(1)
    cols = ["Code", "Price", "Best Style", "Best Score", "Daily Gate", "Swing Gate", "Investor Gate", "RSI", "Vol Ratio", "Return 1M", "Return 3M", "Return 6M"]
    view = low.sort_values(["Best Score", "Vol Ratio"], ascending=False)[cols].head(10).copy()
    st.dataframe(view.round(2), use_container_width=True, hide_index=True)

def render_card(row, style):
    meta = STYLES[style]
    score_col = meta["score"]
    gate_col = meta["gate"]
    reason_col = meta["reason"]
    return_col = meta["return"]
    html = f"""
    <div class="card">
      <div class="card-head">
        <div class="code">{row["Code"]}</div>
        {gate_html(row[gate_col])}
      </div>
      <div class="company">{row["Name"]}</div>
      <div class="price">Rp {fmt_num(row["Price"], 0)}</div>
      <div class="meta"><b>{score_col}:</b> {fmt_num(row[score_col], 1)} / 100 · <b>{row["Adaptive Status"]}</b></div>
      <div class="meta">Confidence: {row["Confidence"]} · Trigger: {row["Trigger"]}</div>
      <div class="meta">{return_col}: {fmt_pct(row[return_col])} · RSI: {fmt_num(row["RSI"], 1)}</div>
      <div class="meta">Stop: Rp {fmt_num(row["Stop"], 0)} · Target: Rp {fmt_num(row["Target"], 0)}</div>
      <div class="reason">{row[reason_col]}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def show_board(result_df, min_score, show_caution, title="🎯 Top 3 Actionable Picks — Risk-Gated"):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.caption("Top 3 dipilih terpisah untuk setiap gaya. PASS diprioritaskan, lalu CAUTION; FAIL tidak dimasukkan. Status adaptif mempertimbangkan regime IHSG, skor, risiko, dan trigger.")
    columns = st.columns(3)
    for column, style in zip(columns, STYLES):
        with column:
            meta = STYLES[style]
            st.subheader(f'{meta["icon"]} {style}')
            st.caption(f'Fokus: {meta["focus"]}')
            subset = result_df[result_df[meta["score"]] >= min_score].copy()
            subset = subset[subset[meta["gate"]] != "FAIL"]
            if not show_caution:
                subset = subset[subset[meta["gate"]] == "PASS"]
            subset["_gate_order"] = subset[meta["gate"]].map({"PASS": 0, "CAUTION": 1})
            subset = subset.sort_values(
                ["_gate_order", meta["score"]], ascending=[True, False]
            ).head(3)
            if subset.empty:
                st.info("Belum ada kandidat pada filter gaya ini.")
            else:
                for _, row in subset.iterrows():
                    render_card(row, style)

# Sidebar
st.sidebar.header("⚙️ Pengaturan")
mode = st.sidebar.radio("Mode", ["Scanner Multi-Style", "Analisis 1 Saham"])
period_label = st.sidebar.selectbox(
    "Periode grafik", ["1 Bulan", "3 Bulan", "6 Bulan", "1 Tahun", "2 Tahun"], index=2
)
max_scan = st.sidebar.slider("Maksimum saham dipindai", 5, 200, 100, 5)
min_score = st.sidebar.slider("Minimum score shortlist", 0, 100, 60, 1)
price_filter = st.sidebar.selectbox("Filter harga saham", ["Semua harga", "Di bawah Rp100", "Rp100–499", "Rp500–1.999", "Rp2.000–4.999", "Rp5.000 ke atas"], index=0)
show_caution = st.sidebar.checkbox("Tampilkan CAUTION pada shortlist", True)
show_board_single = st.sidebar.checkbox(
    "Tampilkan Top 3 pada Analisis 1 Saham", True
)
universe_text = st.sidebar.text_area("Universe kode IDX", DEFAULT_UNIVERSE, height=145)
tickers = clean_codes(universe_text)[:max_scan]

st.title("📈 Sanggul Stock Scanner V10.5")
st.caption("Full IDX Multi-Tier · Adaptive Risk-Gated · Market Regime · Setup & Trigger · Responsive UI")
st.markdown(
    '<div class="info-box">Daily, Swing, dan Investor memakai aturan berbeda. '
    'CAUTION berarti kandidat belum memenuhi seluruh syarat PASS, bukan berarti data error. '
    'FAIL digunakan untuk risiko atau struktur yang lebih kritis.</div>',
    unsafe_allow_html=True
)

regime_now = market_regime()
st.markdown(f"**Market Regime IHSG:** `{regime_now["regime"]}` · RSI IHSG: `{fmt_num(regime_now["rsi"],1)}` · Threshold adaptif aktif", unsafe_allow_html=True)

if not tickers:
    st.warning("Universe kosong. Masukkan minimal satu kode saham.")
    st.stop()

# Single-stock mode: individual analysis first, then Top 3 board.
if mode == "Analisis 1 Saham":
    selected = st.sidebar.selectbox("Pilih saham", tickers)
    data = analyze(selected)
    if data is None:
        st.error("Data saham tidak tersedia atau histori belum cukup.")
        st.stop()

    st.markdown('<div class="section-title">🔎 Analisis Individual</div>', unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Harga", f"Rp {fmt_num(data['Price'], 0)}")
    m2.metric("Daily Score", f"{data['Daily Score']:.1f}", data["Daily Gate"])
    m3.metric("Swing Score", f"{data['Swing Score']:.1f}", data["Swing Gate"])
    m4.metric("Investor Score", f"{data['Investor Score']:.1f}", data["Investor Gate"])
    m5.metric("Primary Style", data["Primary Style"])

    days = {"1 Bulan": 22, "3 Bulan": 66, "6 Bulan": 132, "1 Tahun": 264, "2 Tahun": 520}
    plot_df = data["_df"].tail(days[period_label])
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=plot_df.index,
        open=plot_df["Open"], high=plot_df["High"],
        low=plot_df["Low"], close=plot_df["Close"],
        name="Harga"
    ))
    for col, line_color in [("MA20", "#2563eb"), ("MA50", "#f59e0b"), ("MA200", "#7c3aed")]:
        fig.add_trace(go.Scatter(
            x=plot_df.index, y=plot_df[col], mode="lines",
            name=col, line={"width": 1.6, "color": line_color}
        ))
    fig.update_layout(
        height=440, margin={"l": 8, "r": 8, "t": 35, "b": 8},
        template="plotly_white", title=f"{selected.upper()} · {period_label}",
        xaxis_rangeslider_visible=False,
        legend={"orientation": "h", "y": 1.02, "x": 0},
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-title">Ringkasan indikator</div>', unsafe_allow_html=True)
    summary = pd.DataFrame([{
        "Return 1M": fmt_pct(data["Return 1M"]),
        "Return 3M": fmt_pct(data["Return 3M"]),
        "Return 6M": fmt_pct(data["Return 6M"]),
        "Return 2Y": fmt_pct(data["Return 2Y"]),
        "RSI": fmt_num(data["RSI"], 1),
        "Vol Ratio": fmt_num(data["Vol Ratio"], 2),
        "MA20": fmt_num(data["MA20"], 0),
        "MA50": fmt_num(data["MA50"], 0),
        "MA200": fmt_num(data["MA200"], 0),
        "Stop": fmt_num(data["Stop"], 0),
        "Target": fmt_num(data["Target"], 0),
    }])
    st.dataframe(summary, use_container_width=True, hide_index=True)

    if show_board_single:
        st.markdown("---")
        st.info("Top 3 di bawah dihitung dari universe yang dipilih, bukan hanya dari saham individual.")
        with st.spinner("Menghitung Top 3 untuk seluruh universe..."):
            rows = []
            for code in tickers:
                item = analyze(code)
                if item:
                    rows.append({k: v for k, v in item.items() if not k.startswith("_")})
        board_df = pd.DataFrame(rows)
        if not board_df.empty:
            show_board(board_df, min_score, show_caution)

else:
    if st.button("🚀 Jalankan / Refresh Scan", type="primary", use_container_width=True):
        st.cache_data.clear()

    rows = []
    progress = st.progress(0, text="Mengambil data historis...")
    for index, code in enumerate(tickers):
        item = analyze(code)
        if item:
            rows.append({k: v for k, v in item.items() if not k.startswith("_")})
        progress.progress(
            (index + 1) / len(tickers),
            text=f"Menganalisis {code} ({index + 1}/{len(tickers)})"
        )
    progress.empty()

    result_df = pd.DataFrame(rows)
    if result_df.empty:
        st.error("Tidak ada data yang berhasil dianalisis. Periksa internet atau kode saham.")
        st.stop()

    all_result_df = result_df.copy()
    result_df = apply_price_filter(result_df, price_filter)
    if result_df.empty:
        st.warning("Tidak ada saham pada filter harga yang dipilih. Pilih Semua harga atau ubah filter.")
        st.stop()

    a, b, c, d, e = st.columns(5)
    a.metric("Saham dianalisis", len(result_df))
    b.metric("Daily PASS", int((result_df["Daily Gate"] == "PASS").sum()))
    c.metric("Swing PASS", int((result_df["Swing Gate"] == "PASS").sum()))
    d.metric("Investor PASS", int((result_df["Investor Gate"] == "PASS").sum()))
    e.metric("Primary terbanyak", result_df["Primary Style"].value_counts().index[0])
    st.metric("Actionable / Watchlist", int(result_df["Adaptive Status"].isin(["Actionable Buy","Watchlist – Strong Setup","Watchlist – Early Setup"]).sum()))

    show_board(result_df, min_score, show_caution)
    show_low_price_board(all_result_df, min_score=0)

    st.markdown('<div class="section-title">📋 Enrich Full IDX — Focus-Aware Multi-Style</div>', unsafe_allow_html=True)
    view = result_df.copy()
    view["Price Tier"] = view["Price"].apply(price_bucket)
    view = view.drop(
        columns=["Daily Reason", "Swing Reason", "Investor Reason"], errors="ignore"
    ).copy()
    st.dataframe(view.round(2), use_container_width=True, hide_index=True, height=460)
    st.download_button(
        "⬇️ Unduh hasil CSV",
        result_df.to_csv(index=False).encode("utf-8-sig"),
        "sanggul_v10_5_results.csv",
        "text/csv",
    )
    st.caption(
        "Universe diperluas untuk mencakup saham lapis pertama, kedua, dan saham berharga rendah. "
        "Data Yahoo Finance dapat terlambat, tidak lengkap, atau gagal diambil. "
        f"Waktu pemindaian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
