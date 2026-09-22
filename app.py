import warnings
warnings.filterwarnings("ignore")
import html
import json

import numpy as np
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="Sanggul Stock Scanner V10.9.2.1 | BIONS Adaptive Decision Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
:root{--bg:#061321;--panel:#0b1c2d;--panel2:#0e2438;--line:#1e405d;--text:#e9f3ff;--muted:#8ea7bf;--blue:#1683ff;--cyan:#00c2ff;--green:#00d084;--yellow:#ffc107;--orange:#ff9f1a;--red:#ff4d5d;}
.stApp{background:radial-gradient(circle at 75% 0%,#12304b 0%,#061321 38%,#040d17 100%);color:var(--text)}
.block-container{max-width:1540px;padding-top:.65rem;padding-bottom:2rem}
[data-testid="stHeader"]{background:rgba(4,13,23,.92)}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#06111e 0%,#0a1e31 100%);border-right:1px solid #18344d}
[data-testid="stSidebar"] *{color:#e8f2ff !important}[data-testid="stSidebar"] .stCaption{color:#90a8bf !important}
/* Universe IDX: ticker text dibuat merah agar lebih mudah dibaca */
[data-testid="stSidebar"] textarea{color:#ff4d5d !important;-webkit-text-fill-color:#ff4d5d !important;caret-color:#ff4d5d !important;font-weight:800 !important;background:#0a1d2f !important;border:1px solid #ff4d5d !important;box-shadow:0 0 0 1px rgba(255,77,93,.12),0 0 14px rgba(255,77,93,.08)}
[data-testid="stSidebar"] textarea:focus{border-color:#ff6574 !important;box-shadow:0 0 0 2px rgba(255,77,93,.20),0 0 18px rgba(255,77,93,.12)}
h1,h2,h3{color:#f4f8ff!important;font-weight:850;letter-spacing:-.025em}h1{font-size:2rem!important}
.section-title{font-size:1.15rem;font-weight:850;margin:1rem 0 .55rem;color:#f4f8ff;display:flex;align-items:center;gap:.4rem}
.info-box{background:linear-gradient(90deg,#09253d,#0b1c2d);border:1px solid #1d5279;border-left:4px solid var(--blue);border-radius:10px;padding:10px 14px;color:#bfe1ff;font-size:.86rem;box-shadow:0 5px 20px rgba(0,0,0,.18)}
.card{border:1px solid #1b4668;border-top:3px solid var(--blue);border-radius:12px;padding:12px 14px;background:linear-gradient(180deg,#0d2235,#091725);min-height:166px;box-shadow:0 8px 24px rgba(0,0,0,.22)}
.card-head{display:flex;justify-content:space-between;align-items:center;gap:8px}.code{font-size:1.08rem;font-weight:900;color:#fff}.company{font-size:.76rem;color:#8da8c0;margin-top:3px}.price{font-size:1.3rem;font-weight:900;margin:9px 0 4px;color:#fff}.meta{font-size:.77rem;color:#a9c0d5;line-height:1.5}.reason{font-size:.75rem;color:#809ab2;margin-top:7px;line-height:1.4}
.pill{display:inline-block;border-radius:7px;padding:4px 8px;font-size:.65rem;font-weight:850;border:1px solid transparent}.pass{background:#073e32;color:#00e59a;border-color:#087c62}.caution{background:#493607;color:#ffd15c;border-color:#a47b12}.fail{background:#4a1820;color:#ff7180;border-color:#a83243}
.stButton>button{border-radius:9px;border:1px solid #28516f;background:#0d2235;color:#dcecff;font-weight:750;box-shadow:none}.stButton>button:hover{border-color:#1683ff;color:#fff;background:#12314b}.stButton>button[kind="primary"]{background:linear-gradient(90deg,#0877ff,#00b8ff);border:0;color:#fff;box-shadow:0 7px 20px rgba(0,132,255,.25)}
[data-testid="stMetric"]{background:linear-gradient(180deg,#0e263c,#091827);border:1px solid #1a3c59;border-radius:10px;padding:10px 12px;box-shadow:0 6px 20px rgba(0,0,0,.18)}[data-testid="stMetricLabel"]{color:#8ea7bf!important}[data-testid="stMetricValue"]{color:#f4f8ff!important;font-weight:850}
.stTabs [data-baseweb="tab-list"]{gap:6px;border-bottom:1px solid #1a3c59}.stTabs [data-baseweb="tab"]{height:40px;border-radius:8px 8px 0 0;padding:0 15px;color:#8ea7bf;font-weight:750}.stTabs [aria-selected="true"]{background:#0b3d68;color:#fff!important;border-bottom:3px solid #1683ff}
.stSelectbox>div>div,.stTextInput>div>div,.stNumberInput>div>div,.stMultiSelect>div>div{background:#0a1d2f!important;border-color:#21435f!important;color:#fff!important}
[data-testid="stDataFrame"]{border:1px solid #1b4668;border-radius:10px;overflow:hidden;box-shadow:0 8px 25px rgba(0,0,0,.2)}[data-testid="stExpander"]{border:1px solid #1b4668;border-radius:10px;background:#091827}hr{border-color:#1b3c56}
.table-shell{border:1px solid #1d4664;border-radius:10px;overflow-x:auto;background:#071522;box-shadow:0 8px 28px rgba(0,0,0,.25)}
.bions-table{width:100%;min-width:1760px;border-collapse:separate;border-spacing:0;font-size:12px;color:#dcecff}.bions-table th{position:sticky;top:0;background:#0c2236;color:#8fa9c1;text-align:left;font-weight:800;padding:10px 9px;border-bottom:1px solid #27506e;white-space:nowrap;z-index:2}.bions-table td{padding:9px;border-bottom:1px solid #142f46;white-space:nowrap;background:#081725}.bions-table tr:hover td{background:#0c2237}.bions-table .num{text-align:right}.bions-table .rank{color:#ffc107;font-weight:900;text-align:center}.bions-table .ticker{font-weight:900;color:#fff}.bions-table .green{color:#00dc92;font-weight:800}.bions-table .red{color:#ff6574;font-weight:800}.bions-table .score{font-weight:900;color:#fff}.bions-table .subtle{color:#8fa9c1}.bions-table .buy{color:#00dc92}.bions-table .sell{color:#ffb24a}.bions-table .sl{color:#ff5c6d}
.table-pill{display:inline-block;padding:4px 8px;border-radius:6px;font-size:10px;font-weight:850;border:1px solid}.tp-buy{background:#063c31;color:#00dc92;border-color:#087e64}.tp-watch{background:#063b6a;color:#4da3ff;border-color:#0a78d8}.tp-caution{background:#493607;color:#ffd15c;border-color:#9f7917}.tp-risk{background:#4a1820;color:#ff6b79;border-color:#a73545}.conf-high{background:#063c31;color:#00dc92;border-color:#087e64}.conf-med{background:#493607;color:#ffd15c;border-color:#9f7917}.conf-low{background:#4a1820;color:#ff6b79;border-color:#a73545}
.top-banner{display:flex;align-items:center;gap:10px;margin-bottom:3px}.version{font-size:2rem;font-weight:950;color:#c76cff}.version-badge{background:#063c31;color:#00dc92;border:1px solid #087e64;padding:5px 10px;border-radius:999px;font-size:.72rem;font-weight:900}.brand-sub{color:#8fa9c1;font-size:.76rem}
@media(max-width:768px){.block-container{padding:.55rem}.card{min-height:0;padding:11px}.bions-table{min-width:1300px}}
.hero-pro{background:linear-gradient(135deg,#0b2a46 0%,#081522 48%,#10102d 100%);border:1px solid #1c6da0;border-radius:18px;padding:20px 22px;margin:10px 0 14px;box-shadow:0 14px 45px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.04)}.hero-title{font-size:2.35rem;font-weight:950;color:#fff;letter-spacing:-.045em}.hero-kicker{color:#58c7ff;font-weight:850;font-size:.78rem;letter-spacing:.12em;text-transform:uppercase}.hero-desc{color:#9db7ce;margin-top:5px;font-size:.88rem}.mini-chip{display:inline-block;padding:5px 9px;border-radius:999px;margin:7px 5px 0 0;background:#0b3554;border:1px solid #176b9b;color:#bfe8ff;font-size:.68rem;font-weight:800}.metric-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.kpi{background:linear-gradient(180deg,#0e2941,#081623);border:1px solid #1c4969;border-radius:13px;padding:13px;box-shadow:0 8px 24px rgba(0,0,0,.18)}.kpi-label{color:#7897b0;font-size:.7rem;text-transform:uppercase;letter-spacing:.08em;font-weight:800}.kpi-value{font-size:1.5rem;color:#fff;font-weight:950;margin-top:4px}.kpi-note{font-size:.7rem;color:#90abc0}.glow-blue{border-color:#1683ff;box-shadow:0 0 22px rgba(22,131,255,.13)}.glow-green{border-color:#00d084;box-shadow:0 0 22px rgba(0,208,132,.11)}.glow-orange{border-color:#ff9f1a;box-shadow:0 0 22px rgba(255,159,26,.10)}.glow-red{border-color:#ff4d5d;box-shadow:0 0 22px rgba(255,77,93,.10)}.score-ring{font-size:1.35rem;font-weight:950;color:#fff}.subpanel{background:#081725;border:1px solid #193f5b;border-radius:13px;padding:13px}.tag-blue{color:#63c9ff}.tag-green{color:#00e39a}.tag-yellow{color:#ffd35a}.tag-red{color:#ff6978}.sector-bar{height:7px;border-radius:10px;background:#142c40;overflow:hidden}.sector-fill{height:100%;background:linear-gradient(90deg,#0877ff,#00d084)}@media(max-width:900px){.metric-grid{grid-template-columns:repeat(2,1fr)}.hero-title{font-size:1.8rem}}

.modern-stock-head{display:grid;grid-template-columns:minmax(260px,1.2fr) repeat(4,minmax(120px,.55fr));gap:10px;align-items:stretch;margin:8px 0 12px}.stock-identity,.quote-card{background:linear-gradient(180deg,#0d263c,#081623);border:1px solid #1c4868;border-radius:13px;padding:12px 15px}.stock-identity{border-left:4px solid #00d084}.stock-code{font-size:2rem;font-weight:950;line-height:1;color:#fff;letter-spacing:-.04em}.stock-name{font-size:.82rem;color:#91aac0;margin-top:5px}.stock-tag{display:inline-block;margin-top:8px;padding:4px 8px;border-radius:999px;background:#0a3550;border:1px solid #1c668f;color:#70d2ff;font-size:.65rem;font-weight:850}.quote-label{font-size:.65rem;color:#7897b0;text-transform:uppercase;font-weight:800;letter-spacing:.08em}.quote-value{font-size:1.28rem;font-weight:950;color:#fff;margin-top:4px}.quote-note{font-size:.68rem;color:#00d084;margin-top:3px}.primary-card{background:linear-gradient(135deg,#0b2d45,#0a1b2a);border:1px solid #246087;border-radius:13px;padding:10px 12px;min-height:70px}.primary-label{font-size:.62rem;color:#7897b0;text-transform:uppercase;letter-spacing:.08em;font-weight:850}.primary-value{font-size:.96rem;color:#fff;font-weight:900;line-height:1.2;margin-top:6px;word-break:break-word}.primary-note{font-size:.64rem;color:#8fa9c1;margin-top:4px}.app-shell-note{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:8px 12px;border:1px solid #183b57;border-radius:11px;background:linear-gradient(90deg,#071827,#0a2033);margin:4px 0 12px;color:#8fa9c1;font-size:.72rem}.clean-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.clean-panel{background:#081725;border:1px solid #193f5b;border-radius:13px;padding:13px}.clean-panel h4{margin:0 0 8px;color:#f4f8ff;font-size:.82rem}.kv{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid #143149;font-size:.72rem}.kv:last-child{border-bottom:0}.kv .label{color:#7897b0}.kv .value{color:#e9f3ff;font-weight:800;text-align:right}.footer-note{margin-top:15px;padding:9px 12px;border-top:1px solid #173650;color:#6f8da7;font-size:.67rem;text-align:center}@media(max-width:1100px){.modern-stock-head{grid-template-columns:1fr 1fr}.stock-identity{grid-column:1/-1}.clean-grid{grid-template-columns:1fr 1fr}}@media(max-width:720px){.modern-stock-head{grid-template-columns:1fr 1fr}.stock-identity{grid-column:1/-1}.clean-grid{grid-template-columns:1fr}.hero-title{font-size:1.55rem}.app-shell-note{align-items:flex-start;flex-direction:column}}
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

@st.cache_data(ttl=900, show_spinner=False)
def ihsg_history():
    try:
        d = yf.download("^JKSE", period="2y", interval="1d", auto_adjust=False, progress=False, threads=False)
        if d is None or d.empty:
            return pd.DataFrame()
        if isinstance(d.columns, pd.MultiIndex):
            d.columns = [c[0] for c in d.columns]
        d.columns = [str(c).title() for c in d.columns]
        if "Close" not in d.columns:
            return pd.DataFrame()
        return d[["Close"]].dropna()
    except Exception:
        return pd.DataFrame()

def market_returns():
    d = ihsg_history()
    if d.empty:
        return {"10D":np.nan,"1M":np.nan,"3M":np.nan,"6M":np.nan,"2Y":np.nan}
    c=d["Close"]
    return {"10D":period_return(c,10),"1M":period_return(c,21),"3M":period_return(c,63),"6M":period_return(c,126),"2Y":period_return(c,504)}

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
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    x["MACD"] = ema12 - ema26
    x["MACDSignal"] = x["MACD"].ewm(span=9, adjust=False).mean()
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

def detect_latest_divergence(x, lookback=90):
    """Detect the latest regular RSI divergence using confirmed local pivots."""
    d = x.tail(lookback).copy()
    if len(d) < 20 or "RSI" not in d.columns:
        return {"type": "Tidak terdeteksi", "date": "—", "price": np.nan, "indicator": np.nan, "note": "Data belum cukup"}

    lows, highs = [], []
    for i in range(2, len(d) - 2):
        low = float(d["Low"].iloc[i])
        high = float(d["High"].iloc[i])
        if low <= float(d["Low"].iloc[i-1]) and low <= float(d["Low"].iloc[i-2]) and low <= float(d["Low"].iloc[i+1]) and low <= float(d["Low"].iloc[i+2]):
            if pd.notna(d["RSI"].iloc[i]):
                lows.append((i, low, float(d["RSI"].iloc[i])))
        if high >= float(d["High"].iloc[i-1]) and high >= float(d["High"].iloc[i-2]) and high >= float(d["High"].iloc[i+1]) and high >= float(d["High"].iloc[i+2]):
            if pd.notna(d["RSI"].iloc[i]):
                highs.append((i, high, float(d["RSI"].iloc[i])))

    candidates = []
    if len(lows) >= 2:
        a, b = lows[-2], lows[-1]
        if b[1] < a[1] and b[2] > a[2]:
            candidates.append((b[0], "Bullish Regular", b[1], b[2], "Harga lower low, RSI higher low"))
    if len(highs) >= 2:
        a, b = highs[-2], highs[-1]
        if b[1] > a[1] and b[2] < a[2]:
            candidates.append((b[0], "Bearish Regular", b[1], b[2], "Harga higher high, RSI lower high"))

    if not candidates:
        return {"type": "Tidak terdeteksi", "date": "—", "price": np.nan, "indicator": np.nan, "note": "Belum ada divergence RSI reguler yang terkonfirmasi"}
    c = sorted(candidates, key=lambda z: z[0])[-1]
    idx = d.index[c[0]]
    return {"type": c[1], "date": pd.Timestamp(idx).strftime("%Y-%m-%d"), "price": c[2], "indicator": c[3], "note": c[4]}

def trading_areas(x, price, atr, divergence):
    """Estimate support/resistance-based trading areas; confirmation remains required."""
    recent = x.tail(20)
    support = float(recent["Low"].min()) if not recent.empty else np.nan
    resistance = float(recent["High"].max()) if not recent.empty else np.nan
    atr_val = float(atr) if pd.notna(atr) and atr > 0 else max(price * 0.03, 1)

    buy_low = support
    buy_high = support + 0.50 * atr_val
    sell_low = resistance - 0.50 * atr_val
    sell_high = resistance
    trigger = resistance
    stop = min(support - 0.50 * atr_val, price - 1.50 * atr_val)
    target1 = resistance
    target2 = price + 2.0 * max(price - stop, atr_val)

    if divergence["type"] == "Bullish Regular":
        buy_low = min(support, divergence["price"])
        buy_high = max(support, divergence["price"]) + 0.30 * atr_val
    elif divergence["type"] == "Bearish Regular":
        sell_low = min(resistance, divergence["price"]) - 0.30 * atr_val
        sell_high = max(resistance, divergence["price"])

    def area(a, b):
        if pd.isna(a) or pd.isna(b): return "—"
        return f"Rp {min(a,b):,.0f}–Rp {max(a,b):,.0f}"

    return {
        "Support 20D": support,
        "Resistance 20D": resistance,
        "Buy Area": area(buy_low, buy_high),
        "Buy Area Low": buy_low,
        "Buy Area High": buy_high,
        "Buy Trigger": trigger,
        "Sell Area": area(sell_low, sell_high),
        "Sell Area Low": sell_low,
        "Sell Area High": sell_high,
        "Stop Loss": stop,
        "Target 1": target1,
        "Target 2": target2,
    }

def latest(series):
    value = series.iloc[-1]
    return float(value) if pd.notna(value) else np.nan


@st.cache_data(ttl=21600, show_spinner=False)
def fundamental_snapshot(code):
    """Fetch public Yahoo Finance company/fundamental fields. Missing values remain unavailable."""
    out = {"Sector":"Unknown","Industry":"Unknown","Fundamental Score":50.0,
           "PE":np.nan,"PB":np.nan,"ROE":np.nan,"Profit Margin":np.nan,
           "Revenue Growth":np.nan,"Earnings Growth":np.nan,"Debt/Equity":np.nan,
           "Market Cap":np.nan,"Fundamental Quality":"Limited Data"}
    try:
        t = yf.Ticker(yf_code(code))
        info = t.info or {}
        out["Sector"] = info.get("sector") or "Unknown"
        out["Industry"] = info.get("industry") or "Unknown"
        vals = {
            "PE": info.get("trailingPE"), "PB": info.get("priceToBook"),
            "ROE": info.get("returnOnEquity"), "Profit Margin": info.get("profitMargins"),
            "Revenue Growth": info.get("revenueGrowth"), "Earnings Growth": info.get("earningsGrowth"),
            "Debt/Equity": info.get("debtToEquity"), "Market Cap": info.get("marketCap")
        }
        for k,v in vals.items():
            try: out[k] = float(v) if v is not None else np.nan
            except Exception: pass

        score = 50.0; evidence = 0
        # Valuation: lower relative multiples are not automatically better; reward reasonable positive values.
        if pd.notna(out["PE"]):
            evidence += 1; score += 8 if 0 < out["PE"] <= 15 else (4 if out["PE"] <= 25 else -4 if out["PE"] > 40 else 0)
        if pd.notna(out["PB"]):
            evidence += 1; score += 7 if 0 < out["PB"] <= 2.5 else (3 if out["PB"] <= 4 else -3 if out["PB"] > 8 else 0)
        if pd.notna(out["ROE"]):
            evidence += 1; score += 10 if out["ROE"] >= .15 else (5 if out["ROE"] >= .08 else -5 if out["ROE"] < 0 else 0)
        if pd.notna(out["Profit Margin"]):
            evidence += 1; score += 8 if out["Profit Margin"] >= .10 else (3 if out["Profit Margin"] >= .03 else -5 if out["Profit Margin"] < 0 else 0)
        if pd.notna(out["Revenue Growth"]):
            evidence += 1; score += 8 if out["Revenue Growth"] >= .10 else (3 if out["Revenue Growth"] > 0 else -5)
        if pd.notna(out["Earnings Growth"]):
            evidence += 1; score += 8 if out["Earnings Growth"] >= .10 else (3 if out["Earnings Growth"] > 0 else -5)
        if pd.notna(out["Debt/Equity"]):
            evidence += 1; score += 6 if out["Debt/Equity"] <= 80 else (2 if out["Debt/Equity"] <= 150 else -6 if out["Debt/Equity"] > 250 else 0)
        out["Fundamental Score"] = float(np.clip(score,0,100))
        out["Fundamental Quality"] = "Strong Data" if evidence >= 5 else ("Partial Data" if evidence >= 2 else "Limited Data")
    except Exception:
        pass
    return out

def simple_backtest(x, horizon=10):
    """Historical technical signal study: signal = close>MA20, RSI 45-72, volume ratio >=0.8.
    Returns average forward return, win rate and sample count. Not a trading recommendation."""
    d = add_indicators(x.copy())
    sig = (d["Close"] > d["MA20"]) & (d["RSI"].between(45,72)) & (d["VolRatio"] >= .8)
    fwd = d["Close"].shift(-horizon) / d["Close"] - 1
    vals = fwd[sig].dropna()
    if len(vals)==0:
        return {"Backtest N":0,"Backtest Win Rate":np.nan,"Backtest Avg Return":np.nan,"Backtest Median Return":np.nan}
    return {"Backtest N":int(len(vals)),"Backtest Win Rate":float((vals>0).mean()*100),"Backtest Avg Return":float(vals.mean()*100),"Backtest Median Return":float(vals.median()*100)}


@st.cache_data(ttl=900, show_spinner=False)
def market_regime():
    """Determine broad IDX regime using IHSG (^JKSE) trend and momentum."""
    try:
        d = ihsg_history()
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


def weekly_trend_state(x):
    """Approximate higher-timeframe confirmation from daily data resampled to weekly."""
    try:
        w = x[['Close']].resample('W-FRI').last().dropna()
        if len(w) < 30:
            return 'Unknown', np.nan
        ma10 = w['Close'].rolling(10).mean().iloc[-1]
        ma20 = w['Close'].rolling(20).mean().iloc[-1]
        px = w['Close'].iloc[-1]
        if pd.notna(ma10) and pd.notna(ma20):
            if px > ma10 > ma20: return 'Bullish', float(px/ma20-1)*100
            if px < ma10 < ma20: return 'Bearish', float(px/ma20-1)*100
            return 'Mixed', float(px/ma20-1)*100
    except Exception:
        pass
    return 'Unknown', np.nan

def liquidity_metrics(x):
    """Liquidity Intelligence 2.0: average, median, consistency and acceleration."""
    value = x['Close'] * x['Volume']
    tail20 = value.tail(20)
    tail5 = value.tail(5)
    adv20 = tail20.mean() if len(tail20) >= 20 else np.nan
    med20 = tail20.median() if len(tail20) >= 20 else np.nan
    adv5 = tail5.mean() if len(tail5) >= 5 else np.nan
    ratio = adv5 / adv20 if pd.notna(adv5) and pd.notna(adv20) and adv20 > 0 else np.nan
    consistency = (tail20 >= adv20 * 0.5).mean() * 100 if pd.notna(adv20) and len(tail20) >= 20 else np.nan
    median_ratio = med20 / adv20 if pd.notna(med20) and pd.notna(adv20) and adv20 > 0 else np.nan
    # A robust liquidity score: level, consistency and recent acceleration.
    level_score = np.clip(np.log10(max(adv20, 1)) - 7, 0, 3) / 3 * 45 if pd.notna(adv20) else 0
    consistency_score = np.clip((consistency if pd.notna(consistency) else 0), 0, 100) * 0.25
    accel_score = np.clip((ratio if pd.notna(ratio) else 0) / 2.0, 0, 1) * 20
    median_score = np.clip((median_ratio if pd.notna(median_ratio) else 0), 0, 1) * 10
    liquidity_score = float(np.clip(level_score + consistency_score + accel_score + median_score, 0, 100))
    return adv20, ratio, med20, consistency, liquidity_score

def rr_metrics(price, stop, target1, target2):
    if any(pd.isna(v) for v in [price, stop, target1]):
        return np.nan, np.nan
    risk = price - stop
    reward = max(target1-price, 0)
    rr1 = reward/risk if risk > 0 else np.nan
    rr2 = max(target2-price,0)/risk if risk > 0 and pd.notna(target2) else np.nan
    return rr1, rr2

def divergence_age_days(x, divergence):
    if divergence.get('date') in (None, '—'):
        return np.nan
    try:
        d = pd.Timestamp(divergence['date'])
        return max((x.index[-1].normalize() - d.normalize()).days, 0)
    except Exception:
        return np.nan

def setup_type(breakout, price, ma20, divergence, rsi):
    if breakout:
        return 'Breakout + Volume' if pd.notna(rsi) and rsi >= 50 else 'Breakout'
    if divergence.get('type') == 'Bullish Regular' and pd.notna(ma20) and price >= ma20:
        return 'Bullish Divergence / Reclaim'
    if pd.notna(ma20) and price > ma20:
        return 'Trend Continuation / Pullback'
    return 'Wait for Reclaim'

def style_gate_v109(style, score, core, hard_fail, rr1, liquidity_ok, mtf_ok, regime, readiness):
    """Adaptive style gate. User-configured liquidity is applied directly to each style."""
    if hard_fail:
        return "FAIL"
    rr_min = 1.5 if style != "Investor Jangka Panjang" else 1.2
    rr_ok = pd.notna(rr1) and rr1 >= rr_min
    base = {
        "Trading Harian": {"Bullish":67,"Sideways":72,"Bearish":78},
        "Swing Trading Mingguan": {"Bullish":68,"Sideways":73,"Bearish":79},
        "Investor Jangka Panjang": {"Bullish":65,"Sideways":70,"Bearish":76},
    }[style].get(regime,72)
    readiness_ok = pd.notna(readiness) and readiness >= 50
    if score >= base and core and liquidity_ok and mtf_ok and rr_ok and readiness_ok:
        return "PASS"
    return "CAUTION"

def entry_readiness(price, ma20, breakout, vol_ratio, rsi, weekly_trend, rr1, buy_low, buy_high, divergence):
    score=0.0
    if breakout: score += 25
    elif pd.notna(ma20) and price > ma20: score += 15
    if weekly_trend == "Bullish": score += 20
    elif weekly_trend == "Mixed": score += 10
    if pd.notna(vol_ratio): score += min(15, max(0,(vol_ratio-0.7)*12))
    if pd.notna(rsi) and 48 <= rsi <= 72: score += 15
    elif pd.notna(rsi) and 40 <= rsi <= 78: score += 8
    if pd.notna(rr1): score += 15 if rr1 >= 1.5 else (8 if rr1 >= 1.2 else 0)
    if divergence == "Bullish Regular": score += 10
    if divergence == "Bearish Regular": score -= 15
    score=float(np.clip(score,0,100))
    in_area = pd.notna(buy_low) and pd.notna(buy_high) and buy_low <= price <= buy_high
    near_trigger = pd.notna(ma20) and pd.notna(price) and pd.notna(buy_high) and abs(price-buy_high)/max(price,1) <= 0.03
    if divergence == "Bearish Regular" and score < 60: stage="RISK BLOCK"
    elif breakout and pd.notna(vol_ratio) and vol_ratio >= 1.0: stage="TRIGGERED / BREAKOUT"
    elif in_area and score >= 60: stage="IN BUY AREA"
    elif divergence == "Bullish Regular" and score >= 55: stage="DIVERGENCE WATCH"
    elif near_trigger and score >= 60: stage="NEAR TRIGGER"
    else: stage="WAIT CONFIRMATION"
    return score, stage

def risk_score(atr_pct, adv20, liquidity_floor, weekly_trend, rr1, hard_fail=False):
    r=0.0
    if pd.notna(atr_pct): r += min(30,max(0,(atr_pct-3)*4))
    else: r += 15
    if pd.notna(adv20) and liquidity_floor>0:
        if adv20 < liquidity_floor: r += 35
        elif adv20 < liquidity_floor*2: r += 15
    else: r += 25
    if weekly_trend == "Bearish": r += 20
    elif weekly_trend == "Mixed": r += 8
    if pd.isna(rr1) or rr1 < 1.2: r += 20
    elif rr1 < 1.5: r += 8
    if hard_fail: r += 30
    return float(np.clip(r,0,100))


def analyze(code, liquidity_floor=1.0e9, daily_floor=5.0e9, swing_floor=3.0e9, investor_floor=1.0e9, low_floor=0.5e9):
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
    divergence = detect_latest_divergence(x)
    areas = trading_areas(x, price, atr, divergence)
    weekly_trend, weekly_vs_ma20 = weekly_trend_state(x)
    adv20_value, liquidity_ratio, median20_value, liquidity_consistency, liquidity_score = liquidity_metrics(x)
    fundamentals = fundamental_snapshot(code)
    backtest = simple_backtest(x)
    divergence_age = divergence_age_days(x, divergence)
    rr1, rr2 = rr_metrics(price, areas["Stop Loss"], areas["Target 1"], areas["Target 2"])
    setup = setup_type(breakout, price, ma20, divergence, rsi)
    price_vs_ma20 = ((price/ma20)-1)*100 if pd.notna(ma20) and ma20 else np.nan

    change_1d = period_return(close, 1)
    r10, r1, r3, r6, r2 = (
        period_return(close, 10),
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
    # Fundamental overlay is strongest for Investor style, lighter for Swing/Daily.
    fscore = fundamentals["Fundamental Score"]
    investor_score = float(np.clip(investor_score * 0.70 + fscore * 0.30, 0, 100))
    swing_score = float(np.clip(swing_score * 0.90 + fscore * 0.10, 0, 100))
    daily_score = float(np.clip(daily_score * 0.95 + fscore * 0.05, 0, 100))

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

    # V10.9 Adaptive Decision Engine — user thresholds are wired into the engine.
    daily_liquidity_ok = pd.notna(adv20_value) and adv20_value >= daily_floor
    swing_liquidity_ok = pd.notna(adv20_value) and adv20_value >= swing_floor
    investor_liquidity_ok = pd.notna(adv20_value) and adv20_value >= investor_floor
    liquidity_ok = pd.notna(adv20_value) and adv20_value >= liquidity_floor
    mtf_ok = weekly_trend in ('Bullish','Mixed')
    readiness, readiness_stage = entry_readiness(price, ma20, breakout, vol_ratio, rsi, weekly_trend, rr1, areas['Buy Area Low'], areas['Buy Area High'], divergence['type'])
    daily_core_v109 = daily_core and pd.notna(rr1) and rr1 >= 1.5
    swing_core_v109 = swing_core and pd.notna(rr1) and rr1 >= 1.5
    investor_core_v109 = investor_core and pd.notna(rr1) and rr1 >= 1.2
    daily_gate = style_gate_v109('Trading Harian', daily_score, daily_core_v109, daily_hard_fail, rr1, daily_liquidity_ok, mtf_ok, regime, readiness)
    swing_gate = style_gate_v109('Swing Trading Mingguan', swing_score, swing_core_v109, swing_hard_fail, rr1, swing_liquidity_ok, mtf_ok, regime, readiness)
    investor_gate = style_gate_v109('Investor Jangka Panjang', investor_score, investor_core_v109, investor_hard_fail, rr1, investor_liquidity_ok, mtf_ok, regime, readiness)

    mkt_ret = market_returns()
    rs10 = r10 - mkt_ret['10D'] if pd.notna(r10) and pd.notna(mkt_ret['10D']) else np.nan
    rs1 = r1 - mkt_ret['1M'] if pd.notna(r1) and pd.notna(mkt_ret['1M']) else np.nan
    rs3 = r3 - mkt_ret['3M'] if pd.notna(r3) and pd.notna(mkt_ret['3M']) else np.nan
    rs6 = r6 - mkt_ret['6M'] if pd.notna(r6) and pd.notna(mkt_ret['6M']) else np.nan
    hard_fail_any = daily_hard_fail or swing_hard_fail or investor_hard_fail
    base_overall = float(np.clip(max(daily_score, swing_score, investor_score), 0, 100))
    rs_bonus = float(np.clip((rs3 + 10) * 0.45, 0, 8)) if pd.notna(rs3) else 0
    readiness_bonus = float(np.clip((readiness - 50) * 0.12, -6, 6))
    risk_tmp = risk_score(atr_pct, adv20_value, liquidity_floor, weekly_trend, rr1, hard_fail_any)
    overall_score = float(np.clip(base_overall + rs_bonus + readiness_bonus - max(0,risk_tmp-60)*0.08, 0, 100))
    hard_fail_any = daily_hard_fail or swing_hard_fail or investor_hard_fail
    adaptive_status = adaptive_label(overall_score, hard_fail_any, regime)
    adaptive_reason = score_reason(overall_score, trend_ok, momentum_ok, volume_ok, rs_ok, risk_ok, trigger)
    if pd.notna(rs3): adaptive_reason += f"; RS 3M vs IHSG {rs3:+.1f}%"
    adaptive_reason += f"; entry readiness {readiness:.0f}/100 ({readiness_stage})"
    adaptive_reason += f"; Liquidity Score {liquidity_score:.0f}/100"
    if not liquidity_ok: adaptive_reason += '; likuiditas nilai transaksi perlu diperhatikan'
    if not mtf_ok: adaptive_reason += '; konfirmasi weekly belum mendukung'
    if pd.notna(rr1) and rr1 < 1.5: adaptive_reason += '; R:R < 1.5x'

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
    stop = areas["Stop Loss"]
    target = areas["Target 1"]

    return {
        "Code": code.upper(),
        "Name": code.upper(),
        "Price": price,
        "Change 1D": change_1d,
        "Daily Score": daily_score, "Daily Gate": daily_gate, "Daily Reason": daily_reason,
        "Swing Score": swing_score, "Swing Gate": swing_gate, "Swing Reason": swing_reason,
        "Investor Score": investor_score, "Investor Gate": investor_gate, "Investor Reason": investor_reason,
        "Primary Style": primary,
        "Market Regime": regime,
        "Sector": fundamentals["Sector"], "Industry": fundamentals["Industry"],
        "Fundamental Score": fundamentals["Fundamental Score"], "Fundamental Quality": fundamentals["Fundamental Quality"],
        "PE": fundamentals["PE"], "PB": fundamentals["PB"], "ROE": fundamentals["ROE"],
        "Profit Margin": fundamentals["Profit Margin"], "Revenue Growth": fundamentals["Revenue Growth"],
        "Earnings Growth": fundamentals["Earnings Growth"], "Debt/Equity": fundamentals["Debt/Equity"],
        "Market Cap": fundamentals["Market Cap"],
        "Backtest N": backtest["Backtest N"], "Backtest Win Rate": backtest["Backtest Win Rate"],
        "Backtest Avg Return": backtest["Backtest Avg Return"], "Backtest Median Return": backtest["Backtest Median Return"],
        "Adaptive Score": overall_score,
        "Decision Score": overall_score,
        "Opportunity Score": float(np.clip(base_overall + rs_bonus + max(readiness_bonus,0),0,100)),
        "Risk Score": risk_tmp,
        "Entry Readiness": readiness,
        "Entry Readiness Stage": readiness_stage,
        "RS 10D vs IHSG": rs10,
        "RS 1M vs IHSG": rs1,
        "RS 3M vs IHSG": rs3,
        "RS 6M vs IHSG": rs6,
        "IHSG Return 10D": mkt_ret['10D'],
        "IHSG Return 1M": mkt_ret['1M'],
        "IHSG Return 3M": mkt_ret['3M'],
        "IHSG Return 6M": mkt_ret['6M'],
        "Adaptive Status": adaptive_status,
        "Adaptive Reason": adaptive_reason,
        "Trigger": trigger,
        "Setup Type": setup,
        "Weekly Trend": weekly_trend,
        "Weekly vs MA20 %": weekly_vs_ma20,
        "Price vs MA20 %": price_vs_ma20,
        "Avg Value 20D": adv20_value,
        "Median Value 20D": median20_value,
        "Liquidity Consistency 20D %": liquidity_consistency,
        "Liquidity Ratio 5D/20D": liquidity_ratio,
        "Liquidity Score": liquidity_score,
        "Liquidity Gate": "PASS" if liquidity_ok else "CAUTION",
        "Daily Liquidity Gate": "PASS" if daily_liquidity_ok else "CAUTION",
        "Swing Liquidity Gate": "PASS" if swing_liquidity_ok else "CAUTION",
        "Investor Liquidity Gate": "PASS" if investor_liquidity_ok else "CAUTION",
        "MTF Gate": "PASS" if mtf_ok else "CAUTION",
        "RR 1": rr1,
        "RR 2": rr2,
        "RR Gate": "PASS" if pd.notna(rr1) and rr1 >= 1.5 else "CAUTION",
        "Divergence Age Days": divergence_age,
        "Divergence Terakhir": divergence["type"],
        "Divergence Date": divergence["date"],
        "Divergence Area": (f"Rp {divergence['price']:,.0f}" if pd.notna(divergence["price"]) else "—"),
        "Divergence RSI": divergence["indicator"],
        "Divergence Note": divergence["note"],
        "Support 20D": areas["Support 20D"],
        "Resistance 20D": areas["Resistance 20D"],
        "Buy Area": areas["Buy Area"],
        "Buy Trigger": areas["Buy Trigger"],
        "Sell Area": areas["Sell Area"],
        "Stop Loss": areas["Stop Loss"],
        "Target 1": areas["Target 1"],
        "Target 2": areas["Target 2"],
        "Confidence": "High" if sum([trend_ok,momentum_ok,volume_ok,rs_ok,risk_ok]) >= 4 else ("Medium" if sum([trend_ok,momentum_ok,volume_ok,rs_ok,risk_ok]) >= 2 else "Low"),
        "RSI": rsi, "Vol Ratio": vol_ratio,
        "MA20": ma20, "MA50": ma50, "MA200": ma200,
        "Return 10D": r10, "Return 1M": r1, "Return 3M": r3, "Return 6M": r6, "Return 2Y": r2,
        "Stop": stop, "Target": target, "_df": x,
    }

def render_tradingview_chart(symbol, period_label="3 Bulan"):
    """Render TradingView Advanced Chart for the selected IDX symbol."""
    code = str(symbol).upper().strip()
    tv_symbol = f"IDX:{code}"
    period_map = {"10 Hari": "1M", "1 Bulan": "1M", "3 Bulan": "3M", "6 Bulan": "6M", "1 Tahun": "1Y", "2 Tahun": "5Y"}
    initial_range = period_map.get(period_label, "3M")
    payload = {
        "autosize": True, "symbol": tv_symbol, "interval": "D", "timezone": "Asia/Jakarta",
        "theme": "dark", "style": "1", "locale": "id", "enable_publishing": False,
        "allow_symbol_change": True, "hide_side_toolbar": False, "hide_top_toolbar": False,
        "withdateranges": True, "save_image": False, "calendar": False, "details": False, "hotlist": False,
        "studies": ["MASimple@tv-basicstudies", "Volume@tv-basicstudies", "RSI@tv-basicstudies"],
        "support_host": "https://www.tradingview.com", "range": initial_range,
        "backgroundColor": "#071522", "gridColor": "rgba(110,140,165,0.12)"
    }
    config_json = json.dumps(payload, ensure_ascii=False)
    html_block = f'''
    <div style="width:100%;height:650px;background:#071522;border:1px solid #1b4668;border-radius:14px;overflow:hidden;">
      <div class="tradingview-widget-container" style="height:100%;width:100%">
        <div class="tradingview-widget-container__widget" style="height:calc(100% - 22px);width:100%"></div>
        <div style="height:22px;background:#071522;color:#7897b0;font:11px Arial,sans-serif;text-align:right;padding:3px 10px;">TradingView · {html.escape(code)} · Visualisasi chart eksternal</div>
        <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>
        {config_json}
        </script>
      </div>
    </div>
    '''
    components.html(html_block, height=680, scrolling=False)

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

def low_price_intelligence(row, low_liquidity_floor=0.5e9):
    """Classify sub-Rp100 stocks into exploratory setup buckets; price alone is never treated as value."""
    score = 0.0
    reasons = []
    rsi, vr = row.get("RSI", np.nan), row.get("Vol Ratio", np.nan)
    r1, r3 = row.get("Return 1M", np.nan), row.get("Return 3M", np.nan)
    rr, adv = row.get("RR 1", np.nan), row.get("Avg Value 20D", np.nan)
    weekly, div = row.get("Weekly Trend", "Unknown"), str(row.get("Divergence Terakhir", ""))
    price, ma20 = row.get("Price", np.nan), row.get("MA20", np.nan)
    if pd.notna(r1) and r1 > 0: score += min(18, 8 + r1 * 0.5); reasons.append("momentum 1M positif")
    if pd.notna(r3) and r3 > 0: score += min(18, 8 + r3 * 0.25); reasons.append("trend 3M positif")
    if weekly == "Bullish": score += 18; reasons.append("weekly bullish")
    elif weekly == "Mixed": score += 9
    if pd.notna(vr):
        score += min(18, max(0, (vr - 0.8) * 12))
        if vr >= 1.2: reasons.append("volume meningkat")
    if pd.notna(price) and pd.notna(ma20) and price > ma20: score += 12; reasons.append("di atas MA20")
    if pd.notna(rr) and rr >= 1.5: score += 12; reasons.append("R:R memadai")
    elif pd.notna(rr) and rr >= 1.2: score += 6
    if pd.notna(adv) and adv >= low_liquidity_floor: score += 8; reasons.append("likuiditas minimum tercapai")
    if div == "Bullish Regular": score += 8; reasons.append("bullish divergence")
    if div == "Bearish Regular": score -= 10; reasons.append("bearish divergence")
    if pd.notna(rsi) and rsi > 78: score -= 8; reasons.append("RSI tinggi")
    score = float(np.clip(score, 0, 100))
    hard = (pd.notna(adv) and adv < low_liquidity_floor) or (pd.notna(rsi) and rsi > 85)
    if hard: stage = "Risk-Off / Thin Liquidity"
    elif div == "Bullish Regular" and pd.notna(price) and pd.notna(ma20) and price >= ma20: stage = "Bullish Divergence"
    elif pd.notna(vr) and vr >= 1.5 and pd.notna(r1) and r1 > 0: stage = "Momentum / Acceleration"
    elif weekly == "Bullish" and pd.notna(price) and pd.notna(ma20) and price > ma20: stage = "Trend Continuation"
    elif pd.notna(price) and pd.notna(ma20) and price <= ma20 and pd.notna(vr) and vr >= 1.2: stage = "Early Accumulation Watch"
    else: stage = "Wait for Confirmation"
    return score, stage, "; ".join(reasons[:4]) if reasons else "belum ada konfirmasi utama"

def show_low_price_board(df, min_score=35, low_liquidity_floor=0.5e9):
    st.markdown('<div class="section-title">💰 Top 10 Low-Price Opportunities — Intelligence Board</div>', unsafe_allow_html=True)
    st.caption("Radar khusus saham < Rp100. Ranking memakai momentum, volume, weekly trend, R:R, likuiditas dan divergence — bukan harga murah semata.")
    low = df[df["Price"] < 100].copy()
    if low.empty:
        st.info("Belum ada saham di bawah Rp100 yang berhasil diambil datanya.")
        return
    intelligence = low.apply(lambda r: low_price_intelligence(r, low_liquidity_floor), axis=1, result_type="expand")
    low[["LP Score", "LP Stage", "LP Reason"]] = intelligence
    low["Best Style"] = low[["Daily Score", "Swing Score", "Investor Score"]].idxmax(axis=1).str.replace(" Score", "", regex=False)
    low["Best Score"] = low[["Daily Score", "Swing Score", "Investor Score"]].max(axis=1).round(1)
    low = low[low["LP Score"] >= min_score]
    if low.empty:
        st.info("Tidak ada saham < Rp100 yang memenuhi Low-Price Opportunity Score minimum.")
        return
    cols = ["Code", "Price", "LP Score", "LP Stage", "Best Style", "Best Score", "Avg Value 20D", "Weekly Trend", "Vol Ratio", "RSI", "Return 1M", "Return 3M", "RR 1", "Divergence Terakhir", "LP Reason"]
    view = low.sort_values(["LP Score", "Vol Ratio", "Best Score"], ascending=False)[cols].head(10).copy()
    view["Avg Value 20D"] = view["Avg Value 20D"] / 1e9
    view = view.rename(columns={"Avg Value 20D":"Avg Value 20D (Rp M)", "LP Score":"Opportunity Score", "LP Stage":"Opportunity Stage", "LP Reason":"Reason"})
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
      <div class="meta">Buy area: {row["Buy Area"]} · Sell area: {row["Sell Area"]}</div>
      <div class="meta">Stop: Rp {fmt_num(row["Stop"], 0)} · T1: Rp {fmt_num(row["Target 1"], 0)} · T2: Rp {fmt_num(row["Target 2"], 0)}</div>
      <div class="meta">Divergence: {row["Divergence Terakhir"]} · {row["Divergence Date"]}</div>
      <div class="reason">{row[reason_col]}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def show_board(result_df, min_score, show_caution, title="🎯 Top 3 Actionable Picks — Risk-Gated 2.0", unique_styles=True):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.caption("Liquidity Intelligence 2.0 + Entry Readiness + Adaptive Risk Engine. PASS diprioritaskan; CAUTION tetap ditampilkan bila dipilih. Top 3 antar gaya dapat dibuat berbeda.")
    columns = st.columns(3)
    used = set()
    for column, style in zip(columns, STYLES):
        with column:
            meta = STYLES[style]
            st.subheader(f'{meta["icon"]} {style}')
            st.caption(f'Fokus: {meta["focus"]}')
            subset = result_df[result_df[meta["score"]] >= min_score].copy()
            subset = subset[subset[meta["gate"]] != "FAIL"]
            if not show_caution:
                subset = subset[subset[meta["gate"]] == "PASS"]
            if unique_styles:
                subset = subset[~subset["Code"].isin(used)]
            subset["_gate_order"] = subset[meta["gate"]].map({"PASS": 0, "CAUTION": 1})
            subset = subset.sort_values(["_gate_order", "Decision Score", "Entry Readiness", "RR 1"], ascending=[True, False, False, False], na_position="last").head(3)
            if subset.empty:
                st.info("Belum ada kandidat pada filter gaya ini.")
            else:
                used.update(subset["Code"].tolist())
                for _, row in subset.iterrows():
                    render_card(row, style)

def status_table_class(status):
    s = str(status)
    if "Actionable" in s: return "tp-buy"
    if "Watchlist" in s: return "tp-watch"
    if "Caution" in s: return "tp-caution"
    return "tp-risk"

def confidence_class(conf):
    return {"High":"conf-high","Medium":"conf-med","Low":"conf-low"}.get(str(conf),"conf-med")

def render_bions_table(df, limit=100):
    v = df.copy().sort_values("Decision Score", ascending=False).head(limit).reset_index(drop=True)
    rows=[]
    for i, r in v.iterrows():
        change=r.get("Change 1D",np.nan); change_cls="green" if pd.notna(change) and change>=0 else "red"
        status=html.escape(str(r.get("Adaptive Status","—"))); conf=html.escape(str(r.get("Confidence","—")))
        div=html.escape(str(r.get("Divergence Terakhir","—"))); reason=html.escape(str(r.get("Adaptive Reason","—")))
        code=html.escape(str(r.get("Code","—"))); name=html.escape(str(r.get("Name",code)))
        def p(vv): return "—" if vv is None or pd.isna(vv) else f"Rp {float(vv):,.0f}"
        def n(vv): return "—" if vv is None or pd.isna(vv) else f"{float(vv):,.0f}"
        short=reason[:75]+("…" if len(reason)>75 else "")
        rr = r.get('RR 1', np.nan)
        liq = r.get('Avg Value 20D', np.nan)
        liq_score = r.get('Liquidity Score', np.nan)
        liq_accel = r.get('Liquidity Ratio 5D/20D', np.nan)
        mtf = html.escape(str(r.get('Weekly Trend','—')))
        setup = html.escape(str(r.get('Setup Type','—')))
        rows.append(f"<tr><td class='rank'>{i+1}</td><td class='ticker'>{code}</td><td>{name}</td><td class='num'>{p(r.get('Price'))}</td><td class='num {change_cls}'>{fmt_pct(change)}</td><td class='num score'>{fmt_num(r.get('Decision Score'),1)}</td><td><span class='table-pill {status_table_class(status)}'>{status}</span></td><td><span class='table-pill {confidence_class(conf)}'>{conf}</span></td><td>{fmt_num(r.get('Entry Readiness'),0)} · {html.escape(str(r.get('Entry Readiness Stage','—')))}</td><td class='num'>{fmt_num(r.get('Risk Score'),0)}</td><td class='num'>{fmt_pct(r.get('RS 3M vs IHSG'))}</td><td>{setup}</td><td>{mtf}</td><td class='num'>{fmt_num(rr,2)}x</td><td class='num'>{fmt_num(liq/1e9 if pd.notna(liq) else np.nan,1)}</td><td class='num'>{fmt_num(liq_score,0)}</td><td class='num'>{fmt_num(liq_accel,2)}x</td><td>{html.escape(str(r.get('Sector','Unknown')))}</td><td class='num score'>{fmt_num(r.get('Fundamental Score'),1)}</td><td class='num'>{fmt_num(r.get('PE'),1)}</td><td class='num'>{fmt_num(r.get('PB'),2)}</td><td class='num'>{fmt_pct(r.get('ROE')*100) if pd.notna(r.get('ROE')) else '—'}</td><td class='num'>{fmt_num(r.get('Backtest Win Rate'),1)}</td><td class='subtle'>{div}</td><td class='buy'>{html.escape(str(r.get('Buy Area','—')))}</td><td class='num buy'>{n(r.get('Buy Trigger'))}</td><td class='num sell'>{n(r.get('Target 1'))}</td><td class='num sell'>{n(r.get('Target 2'))}</td><td class='num sl'>{n(r.get('Stop Loss'))}</td><td title='{reason}'>{short}</td></tr>")
    table="<div class='table-shell'><table class='bions-table'><thead><tr><th>#</th><th>Kode</th><th>Nama Saham</th><th>Harga</th><th>1D</th><th>Decision</th><th>Status</th><th>Confidence</th><th>Entry Readiness</th><th>Risk</th><th>RS 3M</th><th>Setup</th><th>Weekly Trend</th><th>R:R T1</th><th>Avg Value 20D<br>(Rp M)</th><th>Liquidity Score</th><th>5D/20D</th><th>Sector</th><th>Fund. Score</th><th>PE</th><th>PB</th><th>ROE</th><th>BT Win%</th><th>Divergence</th><th>Buy Area</th><th>Buy Trigger</th><th>Target 1</th><th>Target 2</th><th>Stop Loss</th><th>Alasan Singkat</th></tr></thead><tbody>"+"".join(rows)+"</tbody></table></div>"
    st.markdown(table, unsafe_allow_html=True)

# Sidebar
st.sidebar.header("⚙️ Pengaturan")
mode = st.sidebar.radio("Mode", ["Scanner Multi-Style", "Analisis 1 Saham"])
period_label = st.sidebar.selectbox(
    "Periode grafik", ["10 Hari", "1 Bulan", "3 Bulan", "6 Bulan", "1 Tahun", "2 Tahun"], index=2
)
max_scan = st.sidebar.slider("Maksimum saham dipindai", 5, 200, 100, 5)
min_score = st.sidebar.slider("Minimum score shortlist", 0, 100, 60, 1)
price_filter = st.sidebar.selectbox("Filter harga saham", ["Semua harga", "Di bawah Rp100", "Rp100–499", "Rp500–1.999", "Rp2.000–4.999", "Rp5.000 ke atas"], index=0)
show_caution = st.sidebar.checkbox("Tampilkan CAUTION pada shortlist", True)
unique_top3 = st.sidebar.checkbox("Top 3 antar gaya dibuat berbeda", True, help="Mengurangi pengulangan saham antar Daily, Swing, dan Investor.")
st.sidebar.markdown("### ⚙️ Adaptive Liquidity Filter")
daily_liq = st.sidebar.number_input("Daily — Min transaksi 20D (Rp M)", min_value=0.0, max_value=100.0, value=5.0, step=0.5)
swing_liq = st.sidebar.number_input("Swing — Min transaksi 20D (Rp M)", min_value=0.0, max_value=100.0, value=3.0, step=0.5)
investor_liq = st.sidebar.number_input("Investor — Min transaksi 20D (Rp M)", min_value=0.0, max_value=100.0, value=1.0, step=0.5)
low_liq = st.sidebar.number_input("Low-Price — Min transaksi 20D (Rp M)", min_value=0.0, max_value=50.0, value=0.5, step=0.25)
min_liquidity = st.sidebar.number_input("Filter tabel utama (Rp M)", min_value=0.0, max_value=100.0, value=1.0, step=0.5, help="Filter tampilan utama. Gate tiap gaya memakai ambang adaptif.")
low_score = st.sidebar.slider("Low-Price Opportunity Score minimum", 0, 100, 35, 5)

show_board_single = st.sidebar.checkbox(
    "Tampilkan Top 3 pada Analisis 1 Saham", True
)
universe_text = st.sidebar.text_area("🔴 Universe kode IDX", DEFAULT_UNIVERSE, height=145, help="Kode saham IDX yang akan dipindai. Teks dibuat merah agar lebih mudah dibaca.")
tickers = clean_codes(universe_text)[:max_scan]

st.markdown('<div class="hero-pro"><div class="hero-kicker">SANGGUL STOCK SCANNER · NEXT-GEN IDX DECISION DASHBOARD</div><div class="hero-title">V10.9.2.1 <span style="color:#5cc8ff">BIONS Adaptive Decision Dashboard</span></div><div class="hero-desc">Market + Sector + Technical + Fundamental + Liquidity Intelligence 2.0 + Entry Readiness + Risk Engine + Historical Signal Study</div><span class="mini-chip">⚡ Daily</span><span class="mini-chip">📊 Swing</span><span class="mini-chip">🌱 Investor</span><span class="mini-chip">🧠 Fundamental</span><span class="mini-chip">🛡 Risk Engine 2.0</span><span class="mini-chip">📈 Backtest</span><span class="mini-chip">🧭 Entry Readiness</span><span class="mini-chip">💎 Low-Price Radar</span></div>', unsafe_allow_html=True)
st.markdown('<div class="info-box">Daily, Swing, dan Investor memakai aturan berbeda. V10.9.2.1 fokus pada data yang dapat diverifikasi: harga, volume, likuiditas 20D, relative strength, sektor, fundamental, entry readiness, dan risk engine. CAUTION berarti kandidat belum memenuhi seluruh syarat PASS.</div>', unsafe_allow_html=True)

regime_now = market_regime()
st.markdown(f"**Market Regime IHSG:** `{regime_now["regime"]}` · RSI IHSG: `{fmt_num(regime_now["rsi"],1)}` · Threshold adaptif aktif", unsafe_allow_html=True)
st.markdown(f"<div class='metric-grid'><div class='kpi glow-blue'><div class='kpi-label'>IHSG Regime</div><div class='kpi-value'>{regime_now["regime"]}</div><div class='kpi-note'>RSI {fmt_num(regime_now["rsi"],1)}</div></div><div class='kpi glow-green'><div class='kpi-label'>Scanner Engine</div><div class='kpi-value'>V10.9.2.1</div><div class='kpi-note'>Adaptive Decision Engine</div></div><div class='kpi glow-orange'><div class='kpi-label'>Data Horizon</div><div class='kpi-value'>10D → 2Y</div><div class='kpi-note'>10D / 1M / 3M / 6M / 1Y / 2Y</div></div><div class='kpi glow-blue'><div class='kpi-label'>Liquidity Engine</div><div class='kpi-value'>2.0</div><div class='kpi-note'>Average + Median + Consistency + Acceleration</div></div></div>", unsafe_allow_html=True)

if not tickers:
    st.warning("Universe kosong. Masukkan minimal satu kode saham.")
    st.stop()

# Single-stock mode: individual analysis first, then Top 3 board.
if mode == "Analisis 1 Saham":
    selected = st.sidebar.selectbox("Pilih saham", tickers)
    data = analyze(selected, liquidity_floor=min_liquidity * 1e9, daily_floor=daily_liq*1e9, swing_floor=swing_liq*1e9, investor_floor=investor_liq*1e9, low_floor=low_liq*1e9)
    if data is None:
        st.error("Data saham tidak tersedia atau histori belum cukup.")
        st.stop()

    st.markdown(f"<div class='modern-stock-head'><div class='stock-identity'><div class='stock-code'>{html.escape(selected.upper())}</div><div class='stock-name'>Analisis individual · IDX</div><span class='stock-tag'>{html.escape(str(data['Market Regime']))}</span></div><div class='quote-card'><div class='quote-label'>Harga</div><div class='quote-value'>Rp {fmt_num(data['Price'],0)}</div><div class='quote-note'>{fmt_pct(data['Change 1D'])}</div></div><div class='quote-card'><div class='quote-label'>Decision</div><div class='quote-value'>{fmt_num(data['Decision Score'],1)}</div><div class='quote-note'>/ 100</div></div><div class='quote-card'><div class='quote-label'>Readiness</div><div class='quote-value'>{fmt_num(data['Entry Readiness'],0)}</div><div class='quote-note'>{html.escape(str(data['Entry Readiness Stage']))}</div></div><div class='quote-card'><div class='quote-label'>Liquidity</div><div class='quote-value'>{fmt_num(data['Liquidity Score'],0)}</div><div class='quote-note'>/ 100</div></div></div><div class='section-title'>🔎 Analisis Individual</div>", unsafe_allow_html=True)
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Harga", f"Rp {fmt_num(data['Price'], 0)}")
    m2.metric("Daily Score", f"{data['Daily Score']:.1f}", data["Daily Gate"])
    m3.metric("Swing Score", f"{data['Swing Score']:.1f}", data["Swing Gate"])
    m4.metric("Investor Score", f"{data['Investor Score']:.1f}", data["Investor Gate"])
    m5.markdown(f"<div class='primary-card'><div class='primary-label'>Primary Style</div><div class='primary-value'>{html.escape(str(data["Primary Style"]))}</div><div class='primary-note'>Style dengan score tertinggi</div></div>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    q1.metric("R:R T1", f"{fmt_num(data['RR 1'],2)}x" if pd.notna(data['RR 1']) else "—")
    q2.metric("Avg Value 20D", f"Rp {fmt_num(data['Avg Value 20D']/1e9,1)} M" if pd.notna(data['Avg Value 20D']) else "—")
    q3.metric("Weekly Trend", data['Weekly Trend'])
    q4.metric("Entry Readiness", f"{data['Entry Readiness']:.0f} · {data['Entry Readiness Stage']}")
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Decision Score", f"{data['Decision Score']:.1f}")
    s2.metric("Opportunity", f"{data['Opportunity Score']:.1f}")
    s3.metric("Risk Score", f"{data['Risk Score']:.0f}")
    s4.metric("RS 10D vs IHSG", fmt_pct(data['RS 10D vs IHSG']))
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Liquidity Score", f"{data['Liquidity Score']:.0f}/100")
    f2.metric("Median Value 20D", f"Rp {fmt_num(data['Median Value 20D']/1e9,1)} M" if pd.notna(data['Median Value 20D']) else "—")
    f3.metric("Vol Ratio", fmt_num(data["Vol Ratio"],2))
    f4.metric("Return 10D", fmt_pct(data["Return 10D"]))

    st.markdown("<div class='section-title'>📈 Advanced Chart · TradingView</div>", unsafe_allow_html=True)
    st.caption("Chart interaktif TradingView untuk simbol IDX yang dipilih. Anda dapat zoom, pan, mengganti timeframe, menambah indikator, dan mengganti simbol langsung dari chart. Analitik/scoring scanner tetap dihitung dari data OHLCV internal.")
    render_tradingview_chart(selected, period_label)
    st.markdown("<div class='app-shell-note'><span>🟢 Chart: TradingView Advanced Chart</span><span>Simbol aktif: <b>IDX:" + html.escape(selected.upper()) + "</b></span></div>", unsafe_allow_html=True)

    st.markdown('<div class="section-title">🎯 Area Entry dan Exit</div>', unsafe_allow_html=True)
    st.info(f"Divergence terakhir: {data['Divergence Terakhir']} ({data['Divergence Date']}) · Area: {data['Divergence Area']} · {data['Divergence Note']}")
    area_view = pd.DataFrame([{
        "Buy Area / Pullback": data["Buy Area"],
        "Buy Trigger": fmt_num(data["Buy Trigger"], 0),
        "Sell Area / Take Profit": data["Sell Area"],
        "Stop Loss": fmt_num(data["Stop Loss"], 0),
        "Target 1": fmt_num(data["Target 1"], 0),
        "Target 2": fmt_num(data["Target 2"], 0),
    }])
    st.dataframe(area_view, use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Ringkasan indikator</div>', unsafe_allow_html=True)
    summary = pd.DataFrame([{
        "Return 10D": fmt_pct(data["Return 10D"]),
        "Return 1M": fmt_pct(data["Return 1M"]),
        "Return 3M": fmt_pct(data["Return 3M"]),
        "Return 6M": fmt_pct(data["Return 6M"]),
        "Return 2Y": fmt_pct(data["Return 2Y"]),
        "RSI": fmt_num(data["RSI"], 1),
        "Vol Ratio": fmt_num(data["Vol Ratio"], 2),
        "Liquidity Score": fmt_num(data["Liquidity Score"], 0),
        "Liquidity Consistency 20D": fmt_num(data["Liquidity Consistency 20D %"], 0) + "%",
        "MA20": fmt_num(data["MA20"], 0),
        "MA50": fmt_num(data["MA50"], 0),
        "MA200": fmt_num(data["MA200"], 0),
        "Stop": fmt_num(data["Stop"], 0),
        "Target": fmt_num(data["Target"], 0),
        "Support 20D": fmt_num(data["Support 20D"], 0),
        "Resistance 20D": fmt_num(data["Resistance 20D"], 0),
        "Buy Area": data["Buy Area"],
        "Buy Trigger": fmt_num(data["Buy Trigger"], 0),
        "Sell Area": data["Sell Area"],
        "Target 1": fmt_num(data["Target 1"], 0),
        "Target 2": fmt_num(data["Target 2"], 0),
        "Divergence Terakhir": data["Divergence Terakhir"],
        "Divergence Date": data["Divergence Date"],
        "Divergence Area": data["Divergence Area"],
    }])
    st.dataframe(summary, use_container_width=True, hide_index=True)

    if show_board_single:
        st.markdown("---")
        st.info("Top 3 di bawah dihitung dari universe yang dipilih, bukan hanya dari saham individual.")
        with st.spinner("Menghitung Top 3 untuk seluruh universe..."):
            rows = []
            for code in tickers:
                item = analyze(code, liquidity_floor=min_liquidity*1e9, daily_floor=daily_liq*1e9, swing_floor=swing_liq*1e9, investor_floor=investor_liq*1e9, low_floor=low_liq*1e9)
                if item:
                    rows.append({k: v for k, v in item.items() if not k.startswith("_")})
        board_df = pd.DataFrame(rows)
        if not board_df.empty:
            show_board(board_df, min_score, show_caution, unique_styles=unique_top3)

else:
    if st.button("🚀 Jalankan / Refresh Scan", type="primary", use_container_width=True):
        st.cache_data.clear()

    rows = []
    progress = st.progress(0, text="Mengambil data historis...")
    for index, code in enumerate(tickers):
        item = analyze(code, liquidity_floor=min_liquidity*1e9, daily_floor=daily_liq*1e9, swing_floor=swing_liq*1e9, investor_floor=investor_liq*1e9, low_floor=low_liq*1e9)
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
    # User-adjustable liquidity floor for the V10.8 shortlist.
    result_df = result_df[(result_df["Avg Value 20D"].fillna(0) >= min_liquidity * 1e9)].copy()
    result_df = apply_price_filter(result_df, price_filter)
    if result_df.empty:
        st.warning("Tidak ada saham pada filter harga yang dipilih. Pilih Semua harga atau ubah filter.")
        st.stop()

    a, b, c, d, e = st.columns(5)
    a.metric("Saham dianalisis", len(result_df))
    b.metric("Daily PASS", int((result_df["Daily Gate"] == "PASS").sum()))
    c.metric("Swing PASS", int((result_df["Swing Gate"] == "PASS").sum()))
    d.metric("Investor PASS", int((result_df["Investor Gate"] == "PASS").sum()))
    primary_mode = result_df["Primary Style"].value_counts().index[0]
    primary_count = int(result_df["Primary Style"].value_counts().iloc[0])
    e.markdown(f"<div class='primary-card' style='min-height:0; padding:10px 12px;'><div class='primary-label'>Primary terbanyak</div><div class='primary-value'>{html.escape(str(primary_mode))}</div><div class='primary-note'>{primary_count} saham · style dominan</div></div>", unsafe_allow_html=True)
    st.metric("Actionable / Watchlist", int(result_df["Adaptive Status"].isin(["Actionable Buy","Watchlist – Strong Setup","Watchlist – Early Setup"]).sum()))

    # Sector-relative intelligence: descriptive ranking inside the scanned universe.
    sector_stats = result_df.groupby("Sector", dropna=False).agg(
        SectorStocks=("Code","count"), SectorReturn3M=("Return 3M","mean"),
        SectorRS3M=("RS 3M vs IHSG","mean"), SectorTechnical=("Adaptive Score","mean"),
        SectorFundamental=("Fundamental Score","mean")
    ).reset_index()
    sector_stats["Sector Strength"] = (
        sector_stats["SectorRS3M"].fillna(0).rank(pct=True)*50 +
        sector_stats["SectorTechnical"].fillna(50).rank(pct=True)*30 +
        sector_stats["SectorFundamental"].fillna(50).rank(pct=True)*20
    ).clip(0,100)
    result_df = result_df.merge(sector_stats[["Sector","Sector Strength","SectorRS3M"]], on="Sector", how="left")
    # Recompute decision score with sector-relative context.
    result_df["Decision Score"] = np.clip(
        result_df["Opportunity Score"].fillna(result_df["Adaptive Score"]) * 0.75 +
        result_df["Sector Strength"].fillna(50) * 0.15 +
        result_df["Entry Readiness"].fillna(50) * 0.10, 0, 100
    )
    result_df["Adaptive Score"] = result_df["Decision Score"]
    result_df["Confidence"] = np.where(
        (result_df["Entry Readiness"]>=75) & (result_df["Risk Score"]<=35) & (result_df["Fundamental Quality"].isin(["Strong Data","Partial Data"])), "High",
        np.where((result_df["Entry Readiness"]>=50) & (result_df["Risk Score"]<=60), "Medium", "Low")
    )

    show_board(result_df, min_score, show_caution, unique_styles=unique_top3)
    show_low_price_board(all_result_df, min_score=low_score, low_liquidity_floor=low_liq * 1e9)

    # Sector and fundamental overview
    sec = result_df.groupby("Sector", dropna=False).agg(Saham=("Code","count"), AvgFundamental=("Fundamental Score","mean"), AvgTechnical=("Adaptive Score","mean")).reset_index().sort_values("AvgFundamental", ascending=False).head(8)
    if not sec.empty:
        st.markdown('<div class="section-title">🏢 Sector & Fundamental Strength</div>', unsafe_allow_html=True)
        cols = st.columns(min(4,len(sec)))
        for col, (_, sr) in zip(cols, sec.iterrows()):
            with col:
                st.markdown(f'<div class="subpanel"><b class="tag-blue">{html.escape(str(sr["Sector"]))}</b><br><span class="score-ring">{sr["AvgFundamental"]:.1f}</span> <span class="tag-green">Fund.</span><br><span style="color:#829db5;font-size:.7rem">{int(sr["Saham"])} saham · Tech {sr["AvgTechnical"]:.1f} · RS {sr.get("SectorRS3M",np.nan):+.1f}%</span></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">📋 Enrich Full IDX — BIONS V10.8 Pro</div>', unsafe_allow_html=True)
    st.caption("Tabel V10.8: skor, status, setup, weekly trend, R:R, likuiditas, divergence, area entry, target, stop loss, dan alasan utama. Geser horizontal untuk melihat seluruh kolom.")
    render_bions_table(result_df, limit=max_scan)
    st.info("V10.8 Risk Engine: PASS membutuhkan kombinasi score, struktur gaya, likuiditas nilai transaksi, konfirmasi weekly, dan R:R. Threshold bersifat adaptif terhadap regime IHSG.")
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


st.markdown("<div class='footer-note'>Sanggul Stock Scanner V10.9.2.1 · Tanpa Foreign Flow · Fokus pada data harga, volume, likuiditas, relative strength, fundamental, sektor, dan risk engine · Decision-support, bukan jaminan hasil investasi.</div>", unsafe_allow_html=True)
