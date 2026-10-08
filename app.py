import os, json, glob, urllib.parse, urllib.request
from datetime import datetime
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf

APP_VERSION = "V11.7.1 PRO OPPORTUNITY vs ENTRY ENGINE · INTRADAY DATA QUALITY FIX1"
ENGINE_VERSION = "V11.7.1-OPPORTUNITY-ENTRY-INTRADAY-DATA-QUALITY-FIX1"
RISK_GATE_VERSION = "2.7"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RECOVERY_DIR = os.path.join(BASE_DIR, "recovered_eod")
os.makedirs(RECOVERY_DIR, exist_ok=True)
SNAP_DIR = os.path.join(BASE_DIR, "snapshots")
CURRENT_SCAN_DIR = os.path.join(BASE_DIR, "current_scan")
os.makedirs(CURRENT_SCAN_DIR, exist_ok=True)
os.makedirs(SNAP_DIR, exist_ok=True)

st.set_page_config(page_title=f"Sanggul Stock Scanner {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="collapsed")

# =========================================================
# PROFESSIONAL UI — inspired by modern brokerage terminals
# =========================================================
st.markdown("""
<style>
:root { --bg:#061425; --panel:#0a1d31; --panel2:#0d2740; --line:#21405e; --ink:#eef6ff; --muted:#9bb0c6; --blue:#1685ff; --blue2:#0b63ce; --green:#16d58a; --red:#ff5b6e; --orange:#ffb21a; --cyan:#31c7ff; }
html,body,[data-testid="stAppViewContainer"] { background:linear-gradient(180deg,#04101f 0%,#071a2d 55%,#061425 100%); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(4,16,31,.86); }
.block-container { padding-top:.8rem; padding-bottom:2rem; max-width:1600px; }
section[data-testid="stSidebar"] { background:#041321; border-right:1px solid #17344f; }
section[data-testid="stSidebar"] .block-container { padding-top:1rem; }
section[data-testid="stSidebar"] * { color:#dcecff; }
.hero { background:linear-gradient(115deg,#071a31 0%,#0a4b91 58%,#126fe4 100%); color:white; padding:18px 22px; border:1px solid #1d6fbd; border-radius:16px; margin-bottom:14px; box-shadow:0 14px 38px rgba(0,80,180,.20); }
.hero h1 { margin:0; font-size:28px; letter-spacing:-.4px; } .hero p { margin:5px 0 0; color:#cfe4ff; font-size:13px; }
.section-title { font-size:19px; font-weight:800; color:#f2f7ff; margin:14px 0 9px; }
.card,.dark-card { background:linear-gradient(145deg,#0a2035,#081a2d); border:1px solid #204361; border-radius:14px; padding:14px 16px; box-shadow:0 8px 24px rgba(0,0,0,.18); color:#eaf4ff; }
.metric-card { background:linear-gradient(145deg,#0a2137,#08192c); border:1px solid #21415e; border-radius:13px; padding:12px 14px; min-height:82px; box-shadow:0 7px 20px rgba(0,0,0,.15); }
.metric-label { color:#8fa9c1; font-size:11px; text-transform:uppercase; letter-spacing:.5px; } .metric-value { color:#f4f9ff; font-size:23px; font-weight:800; margin-top:4px; }
.badge { display:inline-block; padding:4px 9px; border-radius:999px; font-size:11px; font-weight:800; } .badge-blue { background:#0b3760; color:#5eb6ff; } .badge-green { background:#063f32; color:#33e39c; } .badge-yellow { background:#493514; color:#ffc44f; } .badge-red { background:#4b1722; color:#ff7181; }
.small-note { color:#8fa9c1; font-size:12px; }
.dashboard-grid { display:grid; grid-template-columns:1.15fr 1.05fr .8fr; gap:14px; margin:10px 0 14px; } .dashboard-panel { background:linear-gradient(145deg,#0a2137,#08192b); border:1px solid #214561; border-radius:16px; padding:17px; box-shadow:0 10px 28px rgba(0,0,0,.20); }
.panel-kicker { color:#8da8c2; font-size:11px; text-transform:uppercase; letter-spacing:.8px; } .big-number { font-size:31px; font-weight:850; color:#f6fbff; margin-top:3px; }
.green { color:#19d98d !important; } .yellow { color:#ffc44f !important; } .red { color:#ff6577 !important; } .regime { font-size:27px; font-weight:850; margin:7px 0; }
.stat-list { display:flex; flex-direction:column; gap:9px; margin-top:8px; } .stat-row { display:flex; justify-content:space-between; gap:12px; color:#a9bfd4; font-size:13px; border-bottom:1px solid #16344d; padding-bottom:7px; } .stat-row b { color:#eef7ff; }
.top3-wrap { background:linear-gradient(135deg,#071a2e,#092c49); border:1px solid #22557b; border-radius:18px; padding:17px; box-shadow:0 14px 34px rgba(0,0,0,.22); margin:12px 0; }
.top3-head { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:12px; } .top3-title { font-size:20px; font-weight:850; color:#f5f9ff; } .top3-sub { color:#9eb5ca; font-size:12px; }
.pick-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:12px; } .pick-card { background:linear-gradient(160deg,#0b2540,#081a2d); border:1px solid #27516f; border-radius:15px; padding:15px; min-height:220px; }
.pick-rank { width:28px; height:28px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; background:#f7c84b; color:#142235; font-weight:900; margin-right:7px; } .pick-ticker { font-size:19px; font-weight:850; color:#fff; } .pick-status { float:right; }
.pick-setup { margin-top:12px; color:#b8cbe0; font-size:12px; } .pick-price { font-size:22px; font-weight:800; color:#fff; margin:4px 0 10px; }
.pick-metrics { display:grid; grid-template-columns:repeat(4,1fr); gap:6px; margin-top:10px; } .pick-metric { background:#0b2035; border:1px solid #173b58; border-radius:8px; padding:7px; } .pick-metric span { display:block; color:#7994ac; font-size:10px; } .pick-metric b { color:#edf7ff; font-size:12px; }
.risk-line { margin-top:11px; font-size:11px; font-weight:700; color:#ffbf42; }
.op10-wrap { background:linear-gradient(135deg,#071a2e,#09283f); border:1px solid #22557b; border-radius:18px; padding:15px; margin:12px 0; }
.op10-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:10px; }
.op10-card { background:linear-gradient(160deg,#0b2540,#081a2d); border:1px solid #27516f; border-radius:13px; padding:11px; min-height:220px; box-shadow:0 7px 18px rgba(0,0,0,.16); }
.op10-head { display:flex; align-items:center; justify-content:space-between; gap:6px; }
.op10-rank { width:24px; height:24px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; background:#2b84d8; color:#fff; font-weight:900; font-size:11px; margin-right:5px; }
.op10-ticker { font-size:17px; font-weight:850; color:#fff; }
.op10-price { font-size:20px; font-weight:850; color:#fff; margin:7px 0 2px; }
.op10-sub { color:#9fb8cd; font-size:10px; min-height:28px; line-height:1.35; }
.op10-metrics { display:grid; grid-template-columns:repeat(2,1fr); gap:5px; margin-top:8px; }
.op10-metric { background:#0b2035; border:1px solid #173b58; border-radius:7px; padding:6px; }
.op10-metric span { display:block; color:#7894ad; font-size:9px; text-transform:uppercase; }
.op10-metric b { color:#edf7ff; font-size:11px; }
.op10-foot { margin-top:8px; color:#9fb8cd; font-size:10px; line-height:1.45; }
@media (max-width:1200px){ .op10-grid{grid-template-columns:repeat(3,minmax(0,1fr));} }
@media (max-width:800px){ .op10-grid{grid-template-columns:repeat(2,minmax(0,1fr));} .pick-grid{grid-template-columns:1fr;} }
 .mode-pill { display:inline-block; padding:5px 9px; background:#0d3557; color:#8fd0ff; border:1px solid #225f8c; border-radius:999px; font-size:10px; font-weight:800; }

.global-wrap { background:linear-gradient(135deg,#071a2e,#0a2945); border:1px solid #27587e; border-radius:16px; padding:14px; margin:10px 0 14px; }
.global-head { display:flex; justify-content:space-between; align-items:center; gap:10px; margin-bottom:10px; }
.global-title { font-size:17px; font-weight:850; color:#f5f9ff; } .global-sub,.global-foot { color:#93abc0; font-size:11px; }
.global-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:8px; }
.global-card { background:#0b2137; border:1px solid #1d4564; border-radius:10px; padding:9px; min-height:78px; }
.global-name { color:#8fa9c1; font-size:9px; text-transform:uppercase; letter-spacing:.5px; } .global-value { color:#f5f9ff; font-size:17px; font-weight:850; margin:5px 0 2px; }
.global-foot { margin-top:9px; line-height:1.45; }
@media(max-width:800px){ .global-grid{grid-template-columns:repeat(2,1fr);} .global-card:last-child{grid-column:span 2;} .global-title{font-size:16px;} }
.pipeline { display:grid; grid-template-columns:repeat(6,1fr); gap:7px; margin:10px 0 14px; } .pipe { background:#0a2035; border:1px solid #1b3c58; border-radius:9px; padding:9px 7px; text-align:center; color:#9fb4c8; font-size:10px; } .pipe b { display:block; color:#f0f7ff; font-size:15px; margin-top:2px; }
div[data-testid="stDataFrame"] { border:1px solid #24455f; border-radius:10px; background:#081a2c; }
button[kind="primary"] { border-radius:10px; background:linear-gradient(90deg,#0877ed,#1165d7); border:1px solid #268fff; color:#fff !important; }
.stButton>button,.stLinkButton>a { border-radius:10px !important; color:#f7fbff !important; background:linear-gradient(135deg,#0c3558,#0a2743) !important; border:1px solid #286187 !important; box-shadow:0 5px 16px rgba(0,0,0,.18); }
.stButton>button:hover,.stLinkButton>a:hover { border-color:#27a6ff !important; box-shadow:0 0 0 1px rgba(39,166,255,.18),0 8px 20px rgba(0,105,210,.18); }
/* Modern dark controls: replace Streamlit's default white widgets */
section[data-testid="stSidebar"] div[data-baseweb="select"] > div,
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
  background:linear-gradient(135deg,#0b2742,#0a1e34) !important;
  border:1px solid #1c79a9 !important; border-radius:10px !important; color:#eef7ff !important;
  box-shadow:inset 0 0 0 1px rgba(46,190,255,.06),0 5px 15px rgba(0,0,0,.14) !important;
}
section[data-testid="stSidebar"] div[data-baseweb="select"] *,
[data-testid="stSelectbox"] div[data-baseweb="select"] * { color:#eef7ff !important; }
[data-testid="stNumberInput"] > div { background:linear-gradient(135deg,#0b2942,#0a1e34) !important; border:1px solid #2a73a7 !important; border-radius:10px !important; }
[data-testid="stNumberInput"] input { color:#36a8ff !important; -webkit-text-fill-color:#36a8ff !important; background:transparent !important; font-weight:800 !important; caret-color:#36a8ff !important; }
[data-testid="stNumberInput"] input::placeholder { color:#6fc4ff !important; -webkit-text-fill-color:#6fc4ff !important; opacity:1 !important; }
[data-testid="stSelectbox"] input { color:#36a8ff !important; -webkit-text-fill-color:#36a8ff !important; font-weight:800 !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] [role="combobox"] { color:#36a8ff !important; font-weight:800 !important; }
section[data-testid="stSidebar"] [data-baseweb="select"] [role="combobox"] * { color:#36a8ff !important; -webkit-text-fill-color:#36a8ff !important; }
[data-testid="stNumberInput"] button { color:#9fe3ff !important; background:#102f4b !important; border-color:#1d5577 !important; }
/* FIX11: high-contrast blue values inside white/bright widget surfaces */
section[data-testid="stSidebar"] [data-testid="stNumberInput"] { background:linear-gradient(135deg,#071d33,#0a2943) !important; border:1px solid #176eb1 !important; border-radius:11px !important; }
section[data-testid="stSidebar"] [data-testid="stNumberInput"] input { color:#36a8ff !important; -webkit-text-fill-color:#36a8ff !important; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] { background:linear-gradient(135deg,#071d33,#0a2943) !important; border:1px solid #176eb1 !important; }
section[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] span { color:#36a8ff !important; -webkit-text-fill-color:#36a8ff !important; font-weight:800 !important; }
[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] { background:#ff8a3d !important; border-color:#fff !important; box-shadow:0 0 0 2px rgba(255,138,61,.22) !important; }
[data-testid="stSlider"] [data-baseweb="slider"] > div > div { background:linear-gradient(90deg,#ff315d,#ff8a3d) !important; }
[data-testid="stSlider"] [data-baseweb="slider"] > div:first-child { background:#173b57 !important; }
[data-testid="stExpander"] { background:rgba(7,25,42,.72); border:1px solid #204762; border-radius:12px; }
[data-testid="stCaptionContainer"] { color:#91abc2 !important; }
.stLinkButton>a { background:linear-gradient(90deg,#087ff1,#1769dd) !important; border-color:#2ca4ff !important; font-weight:800 !important; }
hr { border-color:#1a3851; }
/* Sidebar control accents */
section[data-testid="stSidebar"] [data-testid="stSelectbox"] label { color:#cce8ff !important; font-weight:700; }
section[data-testid="stSidebar"] [data-testid="stNumberInput"] label { color:#cce8ff !important; font-weight:700; }
section[data-testid="stSidebar"] [data-testid="stSlider"] label { color:#cce8ff !important; font-weight:700; }
.control-card { background:linear-gradient(145deg,#071d32,#0a2942); border:1px solid #1d5477; border-radius:14px; padding:10px 12px; margin:7px 0 10px; box-shadow:0 8px 22px rgba(0,0,0,.16); }
.control-title { font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:#7ecbff; font-weight:800; }

@media (max-width:1100px) { .dashboard-grid,.pick-grid { grid-template-columns:1fr; } .pipeline { grid-template-columns:repeat(3,1fr); } }

/* V11.3 MOBILE-FIRST DECISION BOARD */
.mobile-only{display:none}
.compact-note{color:#9fb8cd;font-size:10px;line-height:1.35}
.card-primary-line{display:flex;justify-content:space-between;align-items:center;gap:8px}
.card-secondary{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:4px;color:#a9bfd4;font-size:11px}
@media (max-width:700px){
 .block-container{padding:.45rem .55rem 1.2rem;max-width:100%;}
 .hero{padding:12px 13px;border-radius:13px;margin-bottom:9px}.hero h1{font-size:21px}.hero p{font-size:11px}
 .section-title{font-size:16px;margin:9px 0 6px}
 .dashboard-grid{grid-template-columns:1fr 1fr;gap:7px;margin:6px 0 8px}
 .dashboard-grid .dashboard-panel{padding:10px;border-radius:12px;min-height:0}.dashboard-grid .dashboard-panel:nth-child(2){grid-column:1/-1}
 .dashboard-panel .big-number{font-size:23px}.dashboard-panel .regime{font-size:20px}.dashboard-panel .small-note{font-size:10px}
 .pipeline{grid-template-columns:repeat(3,1fr);gap:5px;margin:6px 0 9px}.pipe{padding:6px 4px;font-size:8px}.pipe b{font-size:12px}
 .top3-wrap,.op10-wrap{padding:9px;border-radius:13px;margin:8px 0}.top3-head{margin-bottom:7px}.top3-title{font-size:16px}.top3-sub{font-size:10px;line-height:1.25}
 .pick-grid{grid-template-columns:1fr;gap:7px}.pick-card{padding:10px;border-radius:12px;min-height:0}.pick-ticker{font-size:17px}.pick-rank{width:24px;height:24px;font-size:12px}
 .pick-price{font-size:21px;margin:5px 0 6px}.pick-setup{font-size:10px;margin-top:6px;line-height:1.35}
 .pick-metrics{grid-template-columns:repeat(4,1fr);gap:4px;margin-top:6px}.pick-metric{padding:5px 4px;border-radius:6px}.pick-metric span{font-size:8px}.pick-metric b{font-size:10px}
 .op10-grid{grid-template-columns:1fr;gap:7px}.op10-card{min-height:0;padding:9px;border-radius:11px}.op10-ticker{font-size:16px}.op10-price{font-size:19px;margin:5px 0 1px}.op10-sub{font-size:9px;min-height:0}
 .op10-metrics{grid-template-columns:repeat(3,1fr);gap:4px;margin-top:6px}.op10-metric{padding:5px 4px}.op10-metric span{font-size:8px}.op10-metric b{font-size:10px}.op10-foot{font-size:9px;margin-top:6px}
 .mode-pill{padding:3px 6px;font-size:8px}.metric-card{min-height:65px;padding:8px 9px}.metric-label{font-size:9px}.metric-value{font-size:18px}.card{padding:10px 11px;border-radius:11px}
 div[data-testid="stDataFrame"]{font-size:10px} section[data-testid="stSidebar"]{width:88vw!important;min-width:88vw!important}
 .stButton>button,.stLinkButton>a{min-height:40px;font-size:12px}
}
@media (min-width:701px) and (max-width:1050px){.op10-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.pick-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}

/* V11.5 MOBILE-FIRST DECISION CARDS */
.mobile-brief{background:linear-gradient(135deg,#071a2e,#0a3354);border:1px solid #2b638e;border-radius:16px;padding:13px;margin:10px 0 12px;box-shadow:0 10px 26px rgba(0,0,0,.18)}
.mobile-brief-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px;margin-top:9px}.mobile-brief-card{background:#0a2035;border:1px solid #1f4968;border-radius:11px;padding:9px;min-height:70px}.mobile-brief-label{font-size:9px;color:#87a5bd;text-transform:uppercase;letter-spacing:.5px}.mobile-brief-value{font-size:18px;font-weight:850;color:#f4f9ff;margin-top:4px}.mobile-brief-sub{font-size:9px;color:#9bb4c9;margin-top:2px}
.decision-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px}.decision-card{background:linear-gradient(160deg,#0b2540,#081a2d);border:1px solid #285573;border-radius:14px;padding:11px;box-shadow:0 7px 18px rgba(0,0,0,.15)}.decision-head{display:flex;justify-content:space-between;align-items:center;gap:7px}.decision-rank{width:25px;height:25px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:#f7c84b;color:#142235;font-weight:900;font-size:11px;margin-right:5px}.decision-ticker{font-size:18px;font-weight:900;color:#fff}.decision-price{font-size:22px;font-weight:850;color:#fff;margin:5px 0 1px}.decision-setup{font-size:10px;color:#a9bfd4;line-height:1.35}.decision-zone{margin-top:7px;background:#0a2035;border:1px solid #173b58;border-radius:8px;padding:7px}.decision-zone b{color:#fff}.decision-metrics{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin-top:8px}.decision-metric{background:#0b2035;border:1px solid #173b58;border-radius:8px;padding:7px 8px;min-height:46px}.decision-metric span{display:block;color:#8eabc4;font-size:9px;text-transform:uppercase;letter-spacing:.25px;line-height:1.15}.decision-metric b{color:#f2f8ff;font-size:13px;line-height:1.25}.decision-gates{margin-top:7px;font-size:9px;line-height:1.5;color:#a9bfd4}.decision-actions{display:flex;gap:6px;margin-top:8px}.decision-actions a{flex:1;text-align:center;text-decoration:none;background:#0b63ce;border:1px solid #2ca4ff;color:#fff;border-radius:8px;padding:7px;font-size:10px;font-weight:800}.decision-actions a:hover{background:#087ff1}.decision-why{margin-top:6px;font-size:9px;color:#8fa9c1}.watch-wrap{background:linear-gradient(135deg,#071a2e,#09263d);border:1px solid #245675;border-radius:15px;padding:11px;margin:10px 0}.watch-title{font-size:15px;font-weight:850;color:#fff}.watch-sub{font-size:10px;color:#9bb4c9;margin-top:2px}
@media(max-width:700px){.block-container{padding:.4rem .5rem 1.1rem}.hero{padding:11px 12px;border-radius:13px}.hero h1{font-size:20px}.hero p{font-size:10px}.section-title{font-size:15px;margin:8px 0 5px}.mobile-brief{padding:10px;border-radius:13px}.mobile-brief-grid{grid-template-columns:repeat(2,1fr);gap:5px}.mobile-brief-card{min-height:62px;padding:8px}.mobile-brief-value{font-size:17px}.decision-grid{grid-template-columns:1fr;gap:7px}.decision-card{padding:10px;border-radius:12px}.decision-ticker{font-size:17px}.decision-price{font-size:21px}.decision-metrics{grid-template-columns:repeat(4,1fr);gap:5px}.decision-metric{padding:6px 4px;min-height:48px}.decision-metric span{font-size:8px}.decision-metric b{font-size:11px;line-height:1.2}.decision-gates{font-size:9px}.decision-actions a{padding:8px 5px;font-size:10px}.op10-grid{grid-template-columns:1fr}.op10-card{padding:9px}.op10-metrics{grid-template-columns:repeat(3,1fr)}}
@media(min-width:701px) and (max-width:1050px){.decision-grid{grid-template-columns:repeat(2,minmax(0,1fr))}.mobile-brief-grid{grid-template-columns:repeat(4,minmax(0,1fr))}}

</style>
""", unsafe_allow_html=True)

# =========================================================
# CORE INDICATORS
# =========================================================
def rsi(s, p=14):
    d=s.diff(); g=d.clip(lower=0).ewm(alpha=1/p,adjust=False).mean(); l=(-d.clip(upper=0)).ewm(alpha=1/p,adjust=False).mean()
    rs=g/l.replace(0,np.nan); return 100-100/(1+rs)

def macd(s):
    e12=s.ewm(span=12,adjust=False).mean(); e26=s.ewm(span=26,adjust=False).mean(); m=e12-e26; sig=m.ewm(span=9,adjust=False).mean(); return m,sig,m-sig

def tick(p):
    if p < 200: step=1
    elif p < 500: step=2
    elif p < 2000: step=5
    elif p < 5000: step=10
    else: step=25
    return int(round(p/step)*step)

def candle_label(o,h,l,c,po,pc):
    body=abs(c-o); rng=max(h-l,1e-9); upper=h-max(o,c); lower=min(o,c)-l
    if body/rng<.25 and lower>body*1.8: return "Hammer / rejection bawah"
    if body/rng<.25 and upper>body*1.8: return "Shooting star / rejection atas"
    if c>o and pc<po and c>=po and o<=pc: return "Bullish engulfing"
    if c<o and pc>po and o>=pc and c<=po: return "Bearish engulfing"
    if body/rng<.12: return "Doji / indecision"
    return "Bullish candle" if c>o else "Bearish candle"

def analyze(df):
    if df is None or len(df)<220: return None
    d=df.copy().dropna(); c=d["Close"]
    d["MA20"]=c.rolling(20).mean(); d["MA50"]=c.rolling(50).mean(); d["MA200"]=c.rolling(200).mean()
    d["RSI"]=rsi(c); d["MACD"],d["MACDsig"],d["MACDh"]=macd(c); d["V20"]=d["Volume"].rolling(20).mean()
    prev_close=c.shift(1)
    tr=pd.concat([(d["High"]-d["Low"]),(d["High"]-prev_close).abs(),(d["Low"]-prev_close).abs()],axis=1).max(axis=1)
    d["ATR14"]=tr.rolling(14).mean()
    x,p=d.iloc[-1],d.iloc[-2]; close=float(x.Close); ma20,ma50,ma200=map(float,(x.MA20,x.MA50,x.MA200))
    ret20=float(c.iloc[-1]/c.iloc[-21]-1) if len(c)>=21 else np.nan
    ret60=float(c.iloc[-1]/c.iloc[-61]-1) if len(c)>=61 else np.nan
    support=float(d["Low"].rolling(20).min().iloc[-2]); resistance=float(d["High"].rolling(20).max().iloc[-2])
    vr=float(x.Volume/x.V20) if x.V20 and pd.notna(x.V20) else 0; candle=candle_label(x.Open,x.High,x.Low,x.Close,p.Open,p.Close)
    trend=int(close>ma20)+int(ma20>ma50)+int(ma50>ma200)
    momentum=(2 if 50<=x.RSI<=65 else (1 if 45<=x.RSI<50 or 65<x.RSI<=70 else 0))+(2 if x.MACD>x.MACDsig else 0)+(1 if x.MACDh>p.MACDh else 0)
    near_support=abs(close-support)/max(close,1)<=.05; breakout=close>resistance and vr>=1.25
    pullback=close>=ma20*.96 and close<=ma20*1.04 and x.MACD>x.MACDsig
    rejection=any(k in candle.lower() for k in ["hammer","rejection bawah","bullish engulfing"])
    entry=tick(resistance*1.005) if breakout else tick(max(support*1.005,min(close,ma20*1.01)))
    sl=tick(min(support*.985,entry*.955)); risk=entry-sl
    if risk<=0: return None
    tp1=tick(max(resistance*.995,entry+2*risk)); tp2=tick(max(resistance*1.03,entry+3*risk)); rr=(tp1-entry)/risk
    quality=trend*8+(4 if ma50>ma200 else 0)+(3 if close>ma20 else 0)+(2 if vr>=1.1 else 0)
    setup=momentum*6+(5 if near_support else 0)+(4 if pullback else 0)+(4 if rejection else 0)+(3 if breakout else 0)+(3 if rr>=2 else 0)
    opportunity=setup+(5 if near_support else 0)+(5 if breakout else 0)+(4 if pullback else 0)+(3 if 50<=x.RSI<=65 else 0)+(3 if 1.25<=vr<=3 else 0)+(4 if rr>=2 else 0)
    ready=trend>=2 and momentum>=3 and rr>=2 and (near_support or breakout or pullback or rejection) and close>=ma20*.96 and close>=ma50*.98
    setup_type="BREAKOUT" if breakout else ("PULLBACK" if pullback and near_support else ("REJECTION SUPPORT" if rejection and near_support else "WAIT"))
    timing="SORE / CLOSE CONFIRM" if breakout else ("PAGI CONFIRM" if near_support or pullback else "WATCH")
    atr14=float(x.ATR14) if pd.notna(x.ATR14) and x.ATR14>0 else np.nan
    risk_pct=risk/entry*100
    risk_atr=(risk/atr14) if pd.notna(atr14) and atr14>0 else np.nan
    overext=max(close/ma20-1,0)*100 if ma20>0 else np.nan
    entry_gap=abs(entry-close)/close*100 if close>0 else np.nan

    # Decision-support status: AVOID means a hard setup/risk condition is currently invalid.
    # WAIT means the setup is not yet ready but is not structurally invalid.
    avoid_reasons=[]
    if close < ma50 and x.MACD < x.MACDsig:
        avoid_reasons.append("price below MA50 + MACD bearish")
    if not np.isfinite(risk_pct) or risk_pct > 15:
        avoid_reasons.append("stop distance > 15%")
    if not np.isfinite(risk_atr) or risk_atr > 3.0:
        avoid_reasons.append("ATR risk > 3x")
    if not np.isfinite(rr) or rr < 1.50:
        avoid_reasons.append("R/R below 1.50")
    status="AVOID" if avoid_reasons else ("READY" if ready else "WAIT")
    avoid_reason="; ".join(avoid_reasons) if avoid_reasons else "—"
    return {"Close":close,"MA20":ma20,"MA50":ma50,"MA200":ma200,"Return20D":ret20*100,"Return60D":ret60*100,"RSI":float(x.RSI),"MACD":float(x.MACD),"VolumeRatio":vr,"ATR14":atr14,"Support":support,"Resistance":resistance,"Entry":entry,"SL":sl,"TP1":tp1,"TP2":tp2,"RR":rr,"RiskPct":risk_pct,"StopDistancePct":risk_pct,"RiskATRMultiple":risk_atr,"OverextensionPct":overext,"EntryGapPct":entry_gap,"QualityScore":quality,"SetupScore":setup,"OpportunityScore":opportunity,"Status":status,"AvoidReason":avoid_reason,"Setup":setup_type,"Timing":timing,"Candle":candle,"DataDate":pd.Timestamp(d.index[-1]).strftime("%Y-%m-%d"),"DataPoints":int(len(d)),"DataSource":"Yahoo Finance EOD"}

# =========================================================
# MULTI-FACTOR ENGINE — Technical + Fundamental + Flow + Sector
# =========================================================
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

SECTOR_BENCH = {
    "Financials":"BBCA","Energy":"ADRO","Basic Materials":"ANTM","Industrials":"ASII",
    "Infrastructure":"TLKM","Consumer":"ICBP","Property":"BSDE","Technology":"GOTO",
    "Healthcare":"KLBF","Transportation":"ASSA","Agriculture":"AALI","Other / Belum Dipetakan":"BBCA"
}

def _clean_ticker_series(s):
    return s.astype(str).str.upper().str.strip().str.replace('.JK','',regex=False)

def load_factor_file(name):
    path=os.path.join(DATA_DIR,name)
    if not os.path.isfile(path): return pd.DataFrame()
    try:
        x=pd.read_csv(path); x.columns=[str(c).strip() for c in x.columns]
        if 'Ticker' not in x.columns: return pd.DataFrame()
        x['Ticker']=_clean_ticker_series(x['Ticker'])
        return x.drop_duplicates('Ticker',keep='last')
    except Exception: return pd.DataFrame()

def _score_series(v, positive=True):
    x=pd.to_numeric(v,errors='coerce')
    if x.notna().sum()<3: return pd.Series(np.nan,index=v.index)
    ranks=x.rank(pct=True,method='average')*100
    return ranks if positive else 100-ranks

FACTOR_SCHEMAS = {
    'fundamentals.csv': ['Ticker','ROE','ProfitMargin','RevenueGrowth','EarningsGrowth','DebtToEquity','PE','PB'],
    'foreign_flow.csv': ['Ticker','ForeignNet1D','ForeignNet5D','ForeignNet20D'],
    'broker_flow.csv': ['Ticker','BrokerNet1D','BrokerNet5D'],
}

COLUMN_ALIASES = {
    'ticker':'Ticker','kode':'Ticker','code':'Ticker','stock code':'Ticker',
    'roe':'ROE','profitmargin':'ProfitMargin','profit margin':'ProfitMargin','net margin':'ProfitMargin',
    'revenuegrowth':'RevenueGrowth','revenue growth':'RevenueGrowth','growth revenue':'RevenueGrowth',
    'earningsgrowth':'EarningsGrowth','earnings growth':'EarningsGrowth','profit growth':'EarningsGrowth',
    'debtequity':'DebtToEquity','debttoequity':'DebtToEquity','debt to equity':'DebtToEquity','der':'DebtToEquity',
    'pe':'PE','p/e':'PE','per':'PE','pb':'PB','p/b':'PB','pbv':'PB',
    'foreignnet1d':'ForeignNet1D','foreign net 1d':'ForeignNet1D','foreign net buy 1d':'ForeignNet1D',
    'foreignnet5d':'ForeignNet5D','foreign net 5d':'ForeignNet5D','foreign net buy 5d':'ForeignNet5D',
    'foreignnet20d':'ForeignNet20D','foreign net 20d':'ForeignNet20D','foreign net buy 20d':'ForeignNet20D',
    'brokernet1d':'BrokerNet1D','broker net 1d':'BrokerNet1D','broker net buy 1d':'BrokerNet1D',
    'brokernet5d':'BrokerNet5D','broker net 5d':'BrokerNet5D','broker net buy 5d':'BrokerNet5D',
}

def _normalize_columns(df):
    x=df.copy(); out={}
    for c in x.columns:
        key=str(c).strip().lower().replace('_',' ').replace('-',' ')
        compact=key.replace(' ','')
        out[c]=COLUMN_ALIASES.get(key,COLUMN_ALIASES.get(compact,c))
    x=x.rename(columns=out)
    if 'Ticker' in x.columns: x['Ticker']=_clean_ticker_series(x['Ticker'])
    for c in x.columns:
        if c!='Ticker': x[c]=pd.to_numeric(x[c].astype(str).str.replace(',','',regex=False).str.replace('%','',regex=False),errors='coerce')
    return x

def read_factor_upload(uploaded):
    if uploaded is None: return pd.DataFrame()
    try:
        name=str(getattr(uploaded,'name','')).lower()
        df=pd.read_excel(uploaded) if name.endswith(('.xlsx','.xls')) else pd.read_csv(uploaded)
        return _normalize_columns(df)
    except Exception:
        return pd.DataFrame()

def factor_file_info(name, universe=None):
    path=os.path.join(DATA_DIR,name); df=load_factor_file(name)
    required=FACTOR_SCHEMAS.get(name,['Ticker'])
    if not os.path.isfile(path) or df.empty:
        return {'Status':'BELUM TERSEDIA','Rows':0,'CoveragePct':0.0,'Freshness':'—','MissingRequired':required}
    uni=set(_clean_ticker_series(pd.Series(universe or [])).tolist()) if universe else set()
    coverage=(len(set(df['Ticker']) & uni)/len(uni)*100) if uni else 0.0
    missing=[c for c in required if c not in df.columns]
    mtime=datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
    status='VALID' if ('Ticker' in df.columns and not missing) else 'PARTIAL'
    return {'Status':status,'Rows':len(df),'CoveragePct':coverage,'Freshness':mtime,'MissingRequired':missing}

def factor_enrich(result):
    """Hybrid multi-factor engine: external factors enrich, never block core scanning."""
    x=result.copy(); x['Ticker']=_clean_ticker_series(x['Ticker'])
    f=load_factor_file('fundamentals.csv')
    if not f.empty:
        keep=[c for c in FACTOR_SCHEMAS['fundamentals.csv'] if c in f.columns]
        x=x.merge(f[keep],on='Ticker',how='left')
    for c in FACTOR_SCHEMAS['fundamentals.csv'][1:]:
        if c not in x.columns: x[c]=np.nan
    fund_components=[_score_series(x[c],pos) for c,pos in [('ROE',True),('ProfitMargin',True),('RevenueGrowth',True),('EarningsGrowth',True),('DebtToEquity',False),('PE',False),('PB',False)]]
    fund_df=pd.concat(fund_components,axis=1)
    x['FundamentalScore']=fund_df.mean(axis=1,skipna=True); x['FundamentalAvailable']=fund_df.notna().any(axis=1)

    ff=load_factor_file('foreign_flow.csv')
    if not ff.empty:
        keep=[c for c in FACTOR_SCHEMAS['foreign_flow.csv'] if c in ff.columns]
        x=x.merge(ff[keep],on='Ticker',how='left',suffixes=('','_ff'))
    for c in FACTOR_SCHEMAS['foreign_flow.csv'][1:]:
        if c not in x.columns: x[c]=np.nan
    ff_scores=pd.concat([_score_series(x[c],True) for c in FACTOR_SCHEMAS['foreign_flow.csv'][1:]],axis=1)
    x['ForeignFlowScore']=ff_scores.mean(axis=1,skipna=True); x['ForeignAvailable']=ff_scores.notna().any(axis=1)

    bf=load_factor_file('broker_flow.csv')
    if not bf.empty:
        keep=[c for c in FACTOR_SCHEMAS['broker_flow.csv'] if c in bf.columns]
        x=x.merge(bf[keep],on='Ticker',how='left',suffixes=('','_bf'))
    for c in FACTOR_SCHEMAS['broker_flow.csv'][1:]:
        if c not in x.columns: x[c]=np.nan
    bf_scores=pd.concat([_score_series(x[c],True) for c in FACTOR_SCHEMAS['broker_flow.csv'][1:]],axis=1)
    x['BrokerFlowScore']=bf_scores.mean(axis=1,skipna=True); x['BrokerAvailable']=bf_scores.notna().any(axis=1)

    x['Sector']=x['Ticker'].map(sector_of)
    sector_ret=x.groupby('Sector')['Return20D'].transform('mean') if 'Return20D' in x.columns else pd.Series(np.nan,index=x.index)
    x['SectorStrengthScore']=_score_series(sector_ret,True).fillna(50.0)
    x['SectorAvailable']=x['Sector'].ne('Other / Belum Dipetakan')
    # Normalize the three technical sub-scores to their theoretical maxima before weighting.
    # The previous implementation added raw scores and clipped at 100, causing many
    # legitimate candidates to collapse to exactly 100.
    QUALITY_MAX=33.0
    SETUP_MAX=49.0
    OPPORTUNITY_MAX=73.0
    qn=(x['QualityScore']/QUALITY_MAX).clip(0,1)
    sn=(x['SetupScore']/SETUP_MAX).clip(0,1)
    on=(x['OpportunityScore']/OPPORTUNITY_MAX).clip(0,1)
    x['TechnicalScore']=np.clip((0.40*qn+0.35*sn+0.25*on)*100,0,100)

    # Only factors with actual data contribute. Available weights are normalized.
    weights=[('TechnicalScore',.55,True),('FundamentalScore',.20,'FundamentalAvailable'),('ForeignFlowScore',.10,'ForeignAvailable'),('BrokerFlowScore',.05,'BrokerAvailable'),('SectorStrengthScore',.10,'SectorAvailable')]
    scores=[]; coverages=[]; modes=[]
    for _,r in x.iterrows():
        available=[]
        for col,w,flag in weights:
            ok=True if flag is True else bool(r.get(flag,False))
            val=pd.to_numeric(r.get(col,np.nan),errors='coerce')
            if ok and pd.notna(val): available.append((float(val),w))
        total=sum(w for _,w in available)
        score=sum(v*w for v,w in available)/total if total else float(r.get('TechnicalScore',50))
        has_f=bool(r.get('FundamentalAvailable',False)); has_ff=bool(r.get('ForeignAvailable',False)); has_b=bool(r.get('BrokerAvailable',False))
        has_sector=bool(r.get('SectorAvailable',False))
        if has_f and has_ff and has_b:
            mode='FULL MULTI-FACTOR'
        elif has_f or has_ff or has_b:
            mode='PARTIAL ENRICHED'
        elif has_sector:
            mode='CORE TECHNICAL + SECTOR'
        else:
            mode='CORE TECHNICAL'
        scores.append(score); coverages.append(total*100); modes.append(mode)
    x['MultiFactorScore']=np.clip(scores,0,100)
    x['FactorCoveragePct']=coverages
    x['AnalysisMode']=modes
    # Hybrid Risk Gate: external factors are enrichment, not mandatory blockers.
    x['RiskGate']=np.where((x['Status']=='READY')&(x['MultiFactorScore']>=65),'PASS',np.where(x['Status']=='READY','TECH READY / FACTOR REVIEW','WAIT'))
    x['ActionableMode']=np.where(x['RiskGate']=='PASS',x['AnalysisMode'],'NOT ACTIONABLE')
    return x

def save_uploaded_factor(uploaded,name):
    df=read_factor_upload(uploaded)
    required=FACTOR_SCHEMAS.get(name,['Ticker'])
    if df.empty or 'Ticker' not in df.columns: return False,'File tidak dapat dibaca atau kolom Ticker tidak ditemukan.'
    missing=[c for c in required if c not in df.columns]
    if missing: return False,'Kolom wajib belum lengkap: '+', '.join(missing)
    df=df.dropna(subset=['Ticker']).drop_duplicates('Ticker',keep='last')
    df.to_csv(os.path.join(DATA_DIR,name),index=False)
    return True,f'{len(df)} ticker tersimpan.'

def template_bytes(name):
    return pd.DataFrame(columns=FACTOR_SCHEMAS[name]).to_csv(index=False).encode('utf-8')

def data_quality_table(universe):
    rows=[]
    for label,name in [('Fundamentals','fundamentals.csv'),('Foreign Flow','foreign_flow.csv'),('Broker Flow','broker_flow.csv')]:
        info=factor_file_info(name,universe)
        miss=', '.join(info['MissingRequired']) if info['MissingRequired'] else '—'
        rows.append({'Factor':label,'Status':info['Status'],'Rows':info['Rows'],'Coverage %':round(info['CoveragePct'],1),'Last Updated':info['Freshness'],'Missing Columns':miss})
    rows.append({'Factor':'Technical','Status':'LIVE / CALCULATED','Rows':len(universe),'Coverage %':100.0,'Last Updated':'Saat scan','Missing Columns':'—'})
    mapped=sum(sector_of(t)!='Other / Belum Dipetakan' for t in universe)
    rows.append({'Factor':'Sector Strength','Status':'CALCULATED','Rows':mapped,'Coverage %':round(mapped/len(universe)*100,1) if universe else 0,'Last Updated':'Saat scan','Missing Columns':'—'})
    return pd.DataFrame(rows)

# =========================================================
# DATA / PERSISTENCE
# =========================================================
@st.cache_data(ttl=900,show_spinner=False)
def load_universe():
    """Load the IDX universe robustly on local and Streamlit Cloud deployments.

    Priority: universe.csv beside app.py, current working directory, then an
    embedded 600-ticker fallback. The embedded fallback prevents a deployment
    from failing simply because a companion CSV was not copied into the repo.
    """
    candidates = [
        os.path.join(BASE_DIR, "universe.csv"),
        os.path.join(os.getcwd(), "universe.csv"),
        os.path.join(BASE_DIR, "sanggul_v1138", "universe.csv"),
        os.path.join(os.getcwd(), "sanggul_v1138", "universe.csv"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "universe.csv"),
    ]
    seen=set()
    for path in candidates:
        path=os.path.abspath(path)
        if path in seen:
            continue
        seen.add(path)
        try:
            if os.path.isfile(path):
                df=pd.read_csv(path)
                if "Ticker" in df.columns:
                    tickers=df["Ticker"].astype(str).str.upper().str.strip()
                    tickers=tickers[tickers.str.fullmatch(r"[A-Z0-9]+")].drop_duplicates().tolist()
                    if tickers:
                        return tickers
        except Exception:
            pass

    # Embedded fallback: use the same 600-ticker universe shipped with this build.
    fallback = ['BBCA', 'BBRI', 'DCII', 'BREN', 'BYAN', 'BMRI', 'AMMN', 'TLKM', 'MORA', 'ASII', 'DSSA', 'TPIA', 'SRAJ', 'BRPT', 'DNET', 'BBNI', 'SMMA', 'MPRO', 'EMAS', 'CUAN', 'BRMS', 'CASA', 'PANI', 'AADI', 'IMPC', 'UNTR', 'ICBP', 'CDIA', 'ANTM', 'ISAT', 'BNLI', 'MDKA', 'HMSP', 'ADRO', 'BRIS', 'BUMI', 'ADMR', 'UNVR', 'INDF', 'NCKL', 'MBMA', 'PTRO', 'PGUN', 'AMRT', 'GOTO', 'MLPT', 'CPIN', 'INCO', 'SUPR', 'INKP', 'MEGA', 'PGEO', 'EXCL', 'BNGA', 'BDMN', 'GEMS', 'BELI', 'MTEL', 'TAPG', 'VKTR', 'MEDC', 'CMRY', 'TINS', 'PTBA', 'PGAS', 'KLBF', 'ARCI', 'GGRM', 'ENRG', 'MYOR', 'TBIG', 'JARR', 'MGLV', 'NISP', 'AKRA', 'ITMG', 'EMTK', 'SILO', 'JPFA', 'LIFE', 'FAPA', 'MAPI', 'BINA', 'BTPN', 'GIAA', 'SRTG', 'MIKA', 'MDIY', 'TOWR', 'TKIM', 'SINI', 'ULTJ', 'PNBN', 'CBDK', 'MKPI', 'AVIA', 'JSMR', 'BSIM', 'MAPA', 'BBHI', 'ADES', 'NSSS', 'SOHO', 'PACK', 'SMAR', 'INTP', 'BUVA', 'SUPA', 'BBSI', 'AUTO', 'DSNG', 'BBTN', 'POWR', 'AALI', 'RAJA', 'DEWA', 'INDY', 'JRPT', 'BNBR', 'MSIN', 'BNII', 'PSAB', 'MLBI', 'BSSR', 'BFIN', 'CITA', 'FASW', 'POLU', 'PWON', 'CARE', 'STAA', 'MCOL', 'COIN', 'RLCO', 'CMNT', 'ARTO', 'STTP', 'BSDE', 'TSPC', 'RISE', 'HRUM', 'SGER', 'IBST', 'GOOD', 'ARKO', 'BKSL', 'ALII', 'SCMA', 'RATU', 'SMGR', 'AGII', 'YUPI', 'LSIP', 'ADMF', 'CTRA', 'PRAY', 'HRTA', 'ESSA', 'SIDO', 'NATO', 'SSMS', 'SMMT', 'CLEO', 'BUKA', 'WIFI', 'SMSM', 'HEAL', 'EDGE', 'ERAA', 'BIPI', 'BBKP', 'CMNP', 'BMAS', 'SIMP', 'DMAS', 'PLIN', 'DUTI', 'XSPI', 'RMKE', 'BHAT', 'MIDI', 'SGRO', 'WIKA', 'TMAS', 'SSIA', 'FILM', 'BJBR', 'INPP', 'BBMD', 'BJTM', 'TLDN', 'ABMM', 'TCPI', 'CNMA', 'BTPS', 'MDIA', 'INET', 'FORE', 'CYBR', 'EPMT', 'SHIP', 'CLAY', 'GMFI', 'SMCB', 'VICI', 'PNLF', 'SMDR', 'PKPK', 'DMND', 'MTDL', 'BULL', 'TRIM', 'ACES', 'BOGA', 'KPIG', 'YULE', 'UNIC', 'WBSA', 'TOTL', 'OMED', 'BSWD', 'TUGU', 'MAYA', 'ANJT', 'BALI', 'MBSS', 'MSJA', 'SAME', 'ELSA', 'UANG', 'BPII', 'APIC', 'SOCI', 'NICL', 'JECX', 'ELPI', 'MASB', 'TGKA', 'DRMA', 'PALM', 'GJTL', 'MPMX', 'SURE', 'HATM', 'LINK', 'KRAS', 'SMRA', 'TOBA', 'MSTI', 'MARK', 'MMIX', 'AMAR', 'NOBU', 'TFCO', 'GGRP', 'VISI', 'JTPE', 'BIRD', 'MTLA', 'PBID', 'KIJA', 'SMIL', 'ARGO', 'CASS', 'EURO', 'ALKA', 'DKFT', 'TBLA', 'LPKR', 'BWPT', 'PSGO', 'BEEF', 'MKAP', 'RDTX', 'NIRO', 'ARNA', 'BANK', 'AGRO', 'CBRE', 'LPPF', 'IATA', 'JSPT', 'IMAS', 'HEXA', 'GOLF', 'KEJU', 'CENT', 'ROTI', 'DOOH', 'WIIM', 'SAMF', 'DAAZ', 'KEEN', 'NEST', 'ABDA', 'SKRN', 'FISH', 'SDRA', 'INPC', 'BESS', 'BBYB', 'CBUT', 'CPRO', 'FPNI', 'MDLA', 'BNBA', 'PNIN', 'OMRE', 'ASGR', 'ISSP', 'AGRS', 'JAWA', 'LPCK', 'APLN', 'BGTG', 'KETR', 'ROCK', 'IRSX', 'DAYA', 'SFAN', 'BUKK', 'PNGO', 'MAPB', 'PORT', 'VICO', 'TEBE', 'PYFA', 'ASLI', 'ALDO', 'WINS', 'PRDA', 'MCOR', 'SMDM', 'BCIC', 'TOTO', 'ASRI', 'RANS', 'PBSA', 'MGRO', 'GTSI', 'CTBN', 'MAHA', 'KAEF', 'AGAR', 'HUMI', 'MINA', 'RALS', 'PTSN', 'PSKT', 'MYOH', 'BACA', 'DATA', 'BABP', 'ASSA', 'SCCO', 'MNCN', 'NICE', 'MMLP', 'MBAP', 'BISI', 'BCAP', 'DWGL', 'DNAR', 'BRAM', 'KMTR', 'BHIT', 'UCID', 'NETV', 'STAR', 'AYAM', 'IMJS', 'IFII', 'KOTA', 'IPCC', 'IFSH', 'INDR', 'PNBS', 'LPGI', 'MTMH', 'AMAG', 'FAST', 'RONY', 'DGWG', 'KINO', 'PMJS', 'BOLT', 'CARS', 'POLI', 'NICK', 'ACST', 'BMTR', 'FUTR', 'OASA', 'PSSI', 'DVLA', 'BKSW', 'BLTZ', 'BLES', 'BMHS', 'MERK', 'IOTF', 'IPAC', 'IPCM', 'IPOL', 'IPTV', 'IRRA', 'ISAP', 'ISEA', 'ITIC', 'ITMA', 'JAST', 'JATI', 'JAYA', 'JECC', 'JGLE', 'JIHD', 'JKON', 'JMAS', 'KAQI', 'KARW', 'KBAG', 'KBLI', 'KBLM', 'KBLV', 'KDSI', 'KDTN', 'KICI', 'KING', 'KIOS', 'KJEN', 'KKES', 'KKGI', 'KLAS', 'KLIN', 'KMDS', 'KOBX', 'KOCI', 'KOIN', 'KOKA', 'KONI', 'KOPI', 'KREN', 'KRYA', 'KSIX', 'KUAS', 'LABS', 'LAJU', 'LAND', 'LAPD', 'LCKM', 'LEAD', 'LFLO', 'LION', 'LIVE', 'LMAX', 'LMPI', 'LOPI', 'LPIN', 'LPLI', 'LPPS', 'LRNA', 'LTLS', 'LUCK', 'LUCY', 'MAIN', 'MANG', 'MARI', 'MAXI', 'MBTO', 'MCAS', 'MDKI', 'MDLN', 'MDRN', 'MEDS', 'MEJA', 'MENN', 'MERI', 'MFIN', 'MGNA', 'MHKI', 'MICE', 'MINE', 'MIRA', 'MITI', 'MKTR', 'MLIA', 'MLPL', 'MOLI', 'MPIX', 'MPOW', 'MPPA', 'MPXL', 'MRAT', 'MREI', 'MSIE', 'MSKY', 'MTFN', 'MTPS', 'MTWI', 'MUTU', 'NAIK', 'NANO', 'NASA', 'NASI', 'NAYZ', 'NELY', 'NFCX', 'NIKL', 'NPGF', 'NRCA', 'NTBK', 'NZIA', 'OBAT', 'OBMD', 'OILS', 'OKAS', 'OLIV', 'OPMS', 'PADA', 'PADI', 'PAMG', 'PANR', 'PANS', 'PART', 'PBRX', 'PCAR', 'PDES', 'PDPP', 'PEGE', 'PEHA', 'PEVE', 'PGJO', 'PGLI', 'PICO', 'PIPA', 'PJAA', 'PLAN', 'PMUI', 'PNSE', 'POLA', 'POLY', 'PPGL', 'PPRE', 'PPRI', 'PRIM', 'PSAT', 'PSDN', 'PTIS', 'PTMP', 'PTPP', 'PTPS', 'PTPW', 'PTSP', 'PUDP', 'PURA', 'PURI', 'PZZA', 'RAAM', 'RANC', 'RBMS', 'RCCC', 'REAL', 'RELF', 'RELI', 'RGAS', 'RICY', 'RIGS', 'RMKO', 'RODA', 'RSCH', 'RUIS', 'RUNS', 'SAFE', 'SAGE', 'SAPX', 'SATU', 'SBMA', 'SCNP', 'SDMU', 'SDPC', 'SEMA', 'SHID', 'SICO', 'SIPD', 'SKBM', 'SKLT', 'SLIS', 'SMBR', 'SMGA', 'SMKL', 'SMKM', 'SMLE', 'SNLK', 'SOFA', 'SOLA', 'SONA', 'SOSS', 'SOTS', 'SOUL', 'SPMA']
    if fallback:
        return fallback
    raise FileNotFoundError("Universe IDX tidak tersedia. Pastikan universe.csv tersedia atau gunakan build Streamlit Cloud yang menyertakan embedded universe.")

@st.cache_data(ttl=900,show_spinner=False)
def load_data(ticker,period="2y",interval="1d"):
    """Download and normalize Yahoo Finance data so single/multi-index columns behave identically."""
    try:
        symbol = ticker if str(ticker).startswith("^") else str(ticker).upper().replace(".JK", "") + ".JK"
        d=yf.download(symbol,period=period,interval=interval,auto_adjust=False,progress=False,threads=False,group_by="column")
        if d is None or d.empty:
            return pd.DataFrame()
        if isinstance(d.columns,pd.MultiIndex):
            lvl0=set(map(str,d.columns.get_level_values(0)))
            needed={"Open","High","Low","Close","Volume"}
            if needed.intersection(lvl0):
                d.columns=d.columns.get_level_values(0)
            else:
                d.columns=d.columns.get_level_values(1)
        d.columns=[str(c) for c in d.columns]
        keep=[c for c in ["Open","High","Low","Close","Adj Close","Volume"] if c in d.columns]
        d=d[keep].copy()
        if "Close" not in d.columns:
            return pd.DataFrame()
        d=d.dropna(subset=["Close"])
        # DATA CONTRACT: before the EOD lock, never use today's incomplete daily candle.
        # This prevents a morning scan from labeling today's partial quote as EOD.
        if interval == "1d":
            now_jkt = jakarta_now()
            before_eod_lock = (now_jkt.hour < 16) or (now_jkt.hour == 16 and now_jkt.minute < 20)
            if before_eod_lock and len(d):
                idx_dates = pd.to_datetime(d.index, errors="coerce").date
                today = now_jkt.date()
                d = d[[x is not None and x < today for x in idx_dates]]
        return d
    except Exception:
        return pd.DataFrame()


def _download_live_quote_batch(tickers, interval="5m"):
    """Fetch current intraday quote plus basic price/volume pressure context.
    Live overlay only; completed daily candles remain the EOD technical reference.
    """
    symbols=[str(t).upper().replace(".JK","")+".JK" for t in tickers if str(t).strip()]
    out={}
    for start in range(0,len(symbols),50):
        chunk=symbols[start:start+50]
        try:
            q=yf.download(chunk,period="1d",interval=interval,auto_adjust=False,progress=False,threads=True,group_by="ticker",prepost=False)
            if q is None or q.empty: continue
            for sym in chunk:
                base=sym.replace(".JK","")
                try:
                    if isinstance(q.columns,pd.MultiIndex):
                        lvl0=[str(x) for x in q.columns.get_level_values(0)]; lvl1=[str(x) for x in q.columns.get_level_values(1)]
                        if base in set(lvl0) or sym in set(lvl0):
                            sub=q[base if base in set(lvl0) else sym].copy()
                        elif "Close" in set(lvl1):
                            cols=[c for c in q.columns if str(c[0]) in {base,sym}]
                            if not cols: continue
                            sub=q.loc[:,cols].copy(); sub.columns=[c[1] for c in cols]
                        else: continue
                    else:
                        if len(chunk)!=1 or "Close" not in q.columns: continue
                        sub=q.copy()
                    cols=[c for c in ["Open","High","Low","Close","Volume"] if c in sub.columns]
                    sub=sub[cols].copy()
                    for c in cols: sub[c]=pd.to_numeric(sub[c],errors="coerce")
                    sub=sub.dropna(subset=["Close"])
                    if sub.empty: continue
                    idx=pd.DatetimeIndex(pd.to_datetime(sub.index,errors="coerce"))
                    if idx.tz is not None: idx=idx.tz_convert("Asia/Jakarta").tz_localize(None)
                    sub.index=idx; sub=sub[~sub.index.isna()].sort_index()
                    latest=float(sub["Close"].iloc[-1]); ts=pd.Timestamp(sub.index[-1])
                    op=sub["Open"].dropna(); session_open=float(op.iloc[0]) if not op.empty else np.nan
                    last_open=float(sub["Open"].iloc[-1]) if pd.notna(sub["Open"].iloc[-1]) else np.nan
                    vols=sub["Volume"].dropna(); last_vol=float(vols.iloc[-1]) if not vols.empty else np.nan
                    base_vol=vols.iloc[:-1].tail(12) if len(vols)>1 else pd.Series(dtype=float)
                    med_vol=float(base_vol.median()) if not base_vol.empty else np.nan
                    vol_ratio=(last_vol/med_vol) if pd.notna(last_vol) and pd.notna(med_vol) and med_vol>0 else np.nan
                    typical=(sub["High"]+sub["Low"]+sub["Close"])/3.0
                    valid=typical.notna() & sub["Volume"].notna() & (sub["Volume"]>0)
                    vwap=float((typical[valid]*sub.loc[valid,"Volume"]).sum()/sub.loc[valid,"Volume"].sum()) if valid.any() else np.nan
                    now_jkt=jakarta_now().replace(tzinfo=None)
                    age_min=max(0.0,(now_jkt-ts).total_seconds()/60.0)
                    bar_count=len(sub)
                    if bar_count < 3:
                        data_quality="PARTIAL"
                    elif age_min <= 10:
                        data_quality="LIVE"
                    elif age_min <= 20:
                        data_quality="DELAYED"
                    else:
                        data_quality="STALE"
                    out[base]={
                        "price":latest,"time":ts.strftime("%Y-%m-%d %H:%M:%S"),
                        "data_quality":data_quality,"data_age_min":age_min,"bar_count":bar_count,
                        "session_open":session_open,"session_high":float(sub["High"].max()),"session_low":float(sub["Low"].min()),
                        "last_bar_open":last_open,"last_bar_volume":last_vol,"intraday_vwap":vwap,"live_volume_ratio":vol_ratio,
                        "last_bar_change_pct":((latest/last_open)-1)*100 if pd.notna(last_open) and last_open else np.nan,
                        "session_change_pct":((latest/session_open)-1)*100 if pd.notna(session_open) and session_open else np.nan,
                        "bullish_bar":bool(pd.notna(last_open) and latest>=last_open)
                    }
                except Exception: continue
        except Exception: continue
    return out

def load_live_prices(tickers):
    return _download_live_quote_batch(tickers,"5m")

def apply_live_action_gate(result, market_regime="NEUTRAL / SIDEWAYS"):
    """Live decision layer v5.

    Robustness rule: every input row must produce exactly one output row.  The
    previous implementation could leave output arrays shorter than the input
    DataFrame when a row had unusual/missing intraday values, causing pandas
    Length-of-values mismatch errors.  This version processes by position and
    has a per-row safety fallback.
    """
    x=result.copy().reset_index(drop=True)
    n=len(x)
    statuses=["DATA INSUFFICIENT"]*n; pressures=["UNKNOWN"]*n; pconf=["NONE"]*n
    reasons=["current quote unavailable"]*n; eqs=[np.nan]*n; triggers=["wait for fresh intraday data"]*n
    invalids=["do not act on stale intraday data"]*n; rooms=[np.nan]*n; room_cls=["UNKNOWN"]*n; dq=["INSUFFICIENT"]*n

    def num(v):
        try:
            z=pd.to_numeric(v,errors="coerce")
            return float(z) if pd.notna(z) and np.isscalar(z) else np.nan
        except Exception:
            return np.nan

    def scalar(v, default=False):
        try:
            if isinstance(v,(pd.Series,pd.DataFrame,np.ndarray,list,tuple)):
                if len(v)==0: return default
                v=v.iloc[0] if isinstance(v,pd.Series) else v[0]
            return v
        except Exception:
            return default

    for i in range(n):
        r=x.iloc[i]
        try:
            p=num(r.get("CurrentPrice",np.nan)); entry=num(r.get("Entry",np.nan)); sl=num(r.get("SL",np.nan))
            support=num(r.get("Support",np.nan)); resistance=num(r.get("Resistance",np.nan))
            vwap=num(r.get("IntradayVWAP",np.nan)); sess_open=num(r.get("SessionOpen",np.nan))
            vr=num(r.get("LiveVolumeRatio",np.nan)); sess_chg=num(r.get("SessionChangePct",np.nan))
            bullish=bool(scalar(r.get("LiveBullishBar",False),False))
            quality=str(scalar(r.get("IntradayDataQuality",r.get("LiveDataQuality","UNKNOWN")),"UNKNOWN")).upper()
            dq[i]=quality

            if not pd.notna(p) or quality in {"INSUFFICIENT","STALE"}:
                statuses[i]="DATA INSUFFICIENT" if quality=="INSUFFICIENT" or not pd.notna(p) else "WAIT — LIVE DATA"
                pressures[i]="UNKNOWN" if not pd.notna(p) else "MIXED"; pconf[i]="NONE" if not pd.notna(p) else "LOW"
                reasons[i]="current quote unavailable" if not pd.notna(p) else f"intraday data {quality.lower()} — live pressure not fully trusted"
                continue

            lo=entry*.985 if pd.notna(entry) else np.nan; hi=entry*1.025 if pd.notna(entry) else np.nan
            below_vwap=bool(pd.notna(vwap) and p < vwap); below_open=bool(pd.notna(sess_open) and p < sess_open)
            above_vwap=bool(pd.notna(vwap) and p >= vwap); above_open=bool(pd.notna(sess_open) and p >= sess_open)
            high_volume=bool(pd.notna(vr) and vr >= 1.5)
            sell_score=int(not bullish)+int(below_vwap)+int(below_open)+int(high_volume and not bullish)
            buy_score=int(bullish)+int(above_vwap)+int(above_open)+int(high_volume and bullish)
            if quality in {"PARTIAL","DELAYED"}:
                pressure="SELL PRESSURE" if sell_score>=3 else ("POSITIVE" if buy_score>=3 else "MIXED")
            else:
                pressure=("STRONG SELL PRESSURE" if sell_score>=3 else ("SELL PRESSURE" if sell_score>=2 else ("POSITIVE" if buy_score>=3 else "MIXED")))
            if pressure.startswith("STRONG SELL"):
                confidence="HIGH" if quality=="LIVE" and pd.notna(vr) and vr>=2.0 else "MEDIUM"
            elif pressure=="SELL PRESSURE":
                confidence="MEDIUM" if quality=="LIVE" and pd.notna(vr) and vr>=1.5 else "LOW"
            elif pressure=="POSITIVE":
                confidence="HIGH" if quality=="LIVE" and pd.notna(vr) and vr>=1.2 else "MEDIUM"
            else: confidence="LOW"
            pressures[i]=pressure; pconf[i]=confidence

            room=((resistance-p)/p*100) if pd.notna(resistance) and p>0 else np.nan; rooms[i]=room
            if not pd.notna(room): rc="UNKNOWN"
            elif room<1: rc="VERY TIGHT"
            elif room<3: rc="TIGHT"
            elif room<5: rc="MODERATE"
            elif room<8: rc="GOOD"
            else: rc="EXCELLENT"
            room_cls[i]=rc

            score=50.0
            if pd.notna(entry) and entry>0:
                if lo <= p <= hi: score += 12
                elif p < lo: score += 2
                else: score -= 8
            if above_vwap: score += 10
            elif pd.notna(vwap): score -= 8
            if above_open: score += 5
            elif pd.notna(sess_open): score -= 5
            if bullish: score += 8
            else: score -= 8
            if pd.notna(vr):
                if 1.2 <= vr <= 4.0 and bullish: score += 7
                elif vr >= 4.0 and bullish: score += 4
                elif vr >= 1.5 and not bullish: score -= 8
                elif vr < 0.8 and not bullish: score -= 1
            if pd.notna(sess_chg): score += 4 if sess_chg > 0 else (-4 if sess_chg < -1 else 0)
            if pd.notna(room):
                if room >= 8: score += 7
                elif room >= 5: score += 5
                elif room >= 3: score += 3
                elif room >= 1: score -= 2
                elif room >= 0: score -= 6
                else: score -= 8
            if pressure=="STRONG SELL PRESSURE" and confidence=="HIGH": score -= 4
            if pressure=="SELL PRESSURE" and confidence=="LOW": score += 1
            if str(market_regime).upper().startswith("RISK-OFF"): score -= 5
            if quality=="DELAYED": score -= 3
            if quality=="PARTIAL": score -= 5
            eqs[i]=float(np.clip(score,0,100))

            setup=str(scalar(r.get("Setup",""),"")).upper()
            if pd.notna(vwap) and p < vwap:
                trigger=f"reclaim VWAP +0.5% ({fmt(vwap*1.005,0)}) and hold"
            elif pd.notna(vwap) and p <= vwap*1.005:
                trigger=f"hold above VWAP +0.5% ({fmt(vwap*1.005,0)})"
            elif pd.notna(resistance) and p < resistance:
                trigger=f"hold above VWAP and test resistance {fmt(resistance,0)}"
            elif pd.notna(resistance): trigger="hold above resistance / breakout retest"
            else: trigger="hold entry zone with improving volume"
            triggers[i]=trigger
            invalids[i]=(f"break support {fmt(support,0)} with expanding volume" if pd.notna(support) and support>0 else (f"price at/below SL {fmt(sl,0)}" if pd.notna(sl) else "structure breakdown / loss of entry zone"))

            if pd.notna(sl) and p<=sl: status="CANCEL"; reason="current price at/below stop-loss reference"
            elif pd.notna(support) and p < support and high_volume: status="CANCEL"; reason="support broken with elevated volume"
            elif pd.notna(lo) and p<lo: status="WAIT — BELOW ENTRY"; reason="current price below live entry zone"
            elif pd.notna(hi) and p>hi and (not pd.notna(resistance) or p < resistance): status="WAIT — CHASE"; reason="current price already extended above live entry zone"
            elif pd.notna(room) and room >= 0 and room < 0.75 and setup != "BREAKOUT": status="WAIT — RESISTANCE"; reason=f"resistance only {room:.1f}% above current price"
            elif pressure == "STRONG SELL PRESSURE": status="WAIT — LIVE PRESSURE"; reason=f"strong intraday selling-pressure context ({confidence.lower()} confidence)"
            elif pressure == "SELL PRESSURE": status="WAIT — LIVE PRESSURE"; reason=f"intraday selling-pressure context ({confidence.lower()} confidence)"
            elif str(market_regime).upper().startswith("RISK-OFF") and pressure != "POSITIVE": status="WAIT — MARKET"; reason="entry zone valid but IHSG market gate is risk-off"
            elif pressure == "POSITIVE" and eqs[i] >= 72 and quality=="LIVE": status="CONFIRM CANDIDATE"; reason="entry zone plus positive live confirmation"
            elif pressure == "POSITIVE": status="READY — CONFIRM"; reason=f"setup valid; positive intraday context but data quality is {quality.lower()}"
            else: status="READY — WATCH"; reason="setup valid but intraday confirmation is mixed"
            statuses[i]=status; reasons[i]=reason
        except Exception as exc:
            # Never abort the 600-stock scan because one row is malformed.
            statuses[i]="DATA INSUFFICIENT"; pressures[i]="UNKNOWN"; pconf[i]="NONE"
            reasons[i]=f"row-level live analysis unavailable: {type(exc).__name__}"; eqs[i]=np.nan
            triggers[i]="wait for valid intraday data"; invalids[i]="do not act until data is valid"
            rooms[i]=np.nan; room_cls[i]="UNKNOWN"; dq[i]=dq[i] if dq[i] else "INSUFFICIENT"

    # Explicit length guard: this should always match the reset index length.
    cols={"LiveActionStatus":statuses,"LivePressure":pressures,"PressureConfidence":pconf,"LiveActionReason":reasons,
          "EntryQualityScore":eqs,"DistanceToResistancePct":rooms,"ResistanceRoomClass":room_cls,"NextTrigger":triggers,
          "Invalidation":invalids,"IntradayDataQuality":dq}
    for col,values in cols.items():
        if len(values)!=len(x):
            values=list(values[:len(x)]) + [np.nan]*(len(x)-len(values))
        x[col]=values
    return x

@st.cache_data(ttl=900, show_spinner=False)
def us_market_snapshot():
    """Latest completed US session for the morning brief. Informational overlay only; never fabricates premarket quotes."""
    specs = {
        "S&P 500": "^GSPC",
        "Nasdaq": "^IXIC",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
        "VIX": "^VIX",
    }
    rows=[]
    for name,symbol in specs.items():
        try:
            d=yf.download(symbol, period="10d", interval="1d", auto_adjust=False, progress=False, threads=False, group_by="column")
            if d is None or d.empty: continue
            if isinstance(d.columns,pd.MultiIndex):
                lvl0=set(map(str,d.columns.get_level_values(0)))
                d.columns=d.columns.get_level_values(0) if "Close" in lvl0 else d.columns.get_level_values(1)
            d.columns=[str(c) for c in d.columns]
            if "Close" not in d.columns: continue
            d=d.dropna(subset=["Close"])
            if len(d)<2: continue
            close=float(d["Close"].iloc[-1]); prev=float(d["Close"].iloc[-2])
            chg=(close/prev-1)*100 if prev else np.nan
            dt=pd.to_datetime(d.index[-1],errors="coerce")
            rows.append({"Name":name,"Symbol":symbol,"Close":close,"ChangePct":chg,"Date":dt.strftime("%Y-%m-%d") if not pd.isna(dt) else "—"})
        except Exception:
            continue
    out=pd.DataFrame(rows)
    if out.empty:
        return {"rows":[],"status":"DATA INSUFFICIENT","session":"—","lead":"UNAVAILABLE","breadth":np.nan}
    session=str(out["Date"].max())
    # VIX is interpreted inversely for the risk overlay; it is not included in equity breadth.
    eq=out[~out["Name"].eq("VIX")].copy()
    breadth=float((eq["ChangePct"]>0).mean()*100) if not eq.empty else np.nan
    if breadth >= 75: lead="SUPPORTIVE"
    elif breadth >= 50: lead="MIXED"
    else: lead="CAUTION"
    return {"rows":out.to_dict("records"),"status":"VALID","session":session,"lead":lead,"breadth":breadth}

def global_morning_brief():
    snap=us_market_snapshot()
    rows=snap.get("rows",[])
    if not rows:
        st.markdown('<div class="global-wrap"><div class="global-head"><div><div class="global-title">🌎 US Market Lead</div><div class="global-sub">Data Wall Street sesi terakhir yang sudah selesai · bukan pre-market quote</div></div><span class="mode-pill">DATA INSUFFICIENT</span></div></div>',unsafe_allow_html=True)
        return snap
    cards=[]
    for r in rows:
        name=r["Name"]; chg=float(r.get("ChangePct",0) or 0); cls="green" if chg>0 else ("red" if chg<0 else "yellow")
        cards.append(f'<div class="global-card"><div class="global-name">{name}</div><div class="global-value">{fmt(r.get("Close",np.nan),2)}</div><div class="{cls}" style="font-size:12px;font-weight:850">{"+" if chg>0 else ""}{chg:.2f}%</div></div>')
    st.markdown(f'<div class="global-wrap"><div class="global-head"><div><div class="global-title">🌎 US Market Lead</div><div class="global-sub">Wall Street close · {snap.get("session","—")} · source: Yahoo Finance EOD</div></div><span class="mode-pill">LEAD: {snap.get("lead","—")}</span></div><div class="global-grid">{"".join(cards)}</div><div class="global-foot">US Lead adalah <b>context overlay</b>, bukan sinyal BUY/SELL. Sanggul tidak mengarang harga pre-market. Breadth saham indeks: {fmt(snap.get("breadth",np.nan),1)}% naik. VIX dibaca terpisah sebagai indikator volatilitas.</div></div>',unsafe_allow_html=True)
    return snap

def snapshot_dirs(): return sorted([p for p in glob.glob(os.path.join(SNAP_DIR,"*")) if os.path.isdir(p)],reverse=True)

def save_snapshot(result,enrich,focus,opp,action,meta):
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); path=os.path.join(SNAP_DIR,stamp); os.makedirs(path,exist_ok=True)
    result.to_csv(os.path.join(path,"full_scan.csv"),index=False); enrich.to_csv(os.path.join(path,"top150.csv"),index=False); focus.to_csv(os.path.join(path,"top50.csv"),index=False); opp.to_csv(os.path.join(path,"top10.csv"),index=False); action.to_csv(os.path.join(path,"top3.csv"),index=False)
    with open(os.path.join(path,"meta.json"),"w",encoding="utf-8") as f: json.dump(meta,f,ensure_ascii=False,indent=2)
    with open(os.path.join(SNAP_DIR,"latest.txt"),"w",encoding="utf-8") as f: f.write(stamp)
    return path

def save_current_scan(result,enrich,focus,opp,action,meta):
    """Persist the latest ad-hoc/current scan separately from official EOD history.
    This survives Streamlit reruns/reconnects without overwriting the official EOD snapshot.
    """
    os.makedirs(CURRENT_SCAN_DIR, exist_ok=True)
    for name,df in [("full_scan.csv",result),("top150.csv",enrich),("top50.csv",focus),("top10.csv",opp),("top3.csv",action)]:
        df.to_csv(os.path.join(CURRENT_SCAN_DIR,name),index=False)
    meta=dict(meta or {})
    meta["current_scan_saved_at"]=datetime.now().isoformat(timespec="seconds")
    meta["scan_type"]="CURRENT_SCAN"
    with open(os.path.join(CURRENT_SCAN_DIR,"meta.json"),"w",encoding="utf-8") as f:
        json.dump(meta,f,ensure_ascii=False,indent=2)
    return CURRENT_SCAN_DIR

def load_current_scan():
    """Load the latest current scan, if one exists."""
    try:
        meta_path=os.path.join(CURRENT_SCAN_DIR,"meta.json")
        if not os.path.isfile(meta_path): return None
        meta=json.load(open(meta_path,encoding="utf-8"))
        files=[("full","full_scan.csv"),("top150","top150.csv"),("top50","top50.csv"),("top10","top10.csv"),("top3","top3.csv")]
        data={}
        for k,f in files:
            path=os.path.join(CURRENT_SCAN_DIR,f)
            if not os.path.isfile(path): return None
            data[k]=pd.read_csv(path)
        return {"meta":meta,**data}
    except Exception:
        return None

def _ensure_layers(snap):
    """Rebuild derived layers whenever persisted/current layer CSVs are empty or stale.
    Full scan data is the source of truth; Top150/50/10/3 are derived views.
    """
    if not snap or snap.get("full") is None or snap["full"].empty:
        return snap
    full=snap["full"].copy()
    meta=snap.get("meta",{})
    min_rr=float(meta.get("min_rr",2.0) or 2.0)
    # Always re-apply current risk gate before rebuilding derived layers.
    regime=str(meta.get("regime","NEUTRAL / SIDEWAYS"))
    max_stop=float(meta.get("max_stop_pct",15.0) or 15.0)
    full=apply_risk_gate(full,min_rr,max_stop,regime)
    enrich,focus,opp,action=build_layers(full,min_rr)
    snap.update({"full":full,"top150":enrich,"top50":focus,"top10":opp,"top3":action})
    return snap

def _read_saved_bundle(base_dir, stamp):
    try:
        path=os.path.join(base_dir,stamp)
        if not os.path.isdir(path): return None
        meta=json.load(open(os.path.join(path,"meta.json"),encoding="utf-8"))
        data={k:pd.read_csv(os.path.join(path,f)) for k,f in [("full","full_scan.csv"),("top150","top150.csv"),("top50","top50.csv"),("top10","top10.csv"),("top3","top3.csv")]}
        return _ensure_layers({"meta":meta,**data})
    except Exception:
        return None

def latest_recovered_eod():
    marker=os.path.join(RECOVERY_DIR,"latest.txt")
    if os.path.exists(marker):
        stamp=open(marker,encoding="utf-8").read().strip()
        return _read_saved_bundle(RECOVERY_DIR,stamp)
    ds=sorted([p for p in glob.glob(os.path.join(RECOVERY_DIR,"*")) if os.path.isdir(p)],reverse=True)
    return _read_saved_bundle(RECOVERY_DIR,os.path.basename(ds[0])) if ds else None

def _validate_recovery_bundle(bundle, expected_universe=600):
    if not bundle: return False, "NO RECOVERY DATA"
    meta=bundle.get("meta",{}); full=bundle.get("full",pd.DataFrame())
    if str(meta.get("scan_type","")).upper() != "RECOVERED_EOD": return False, "NOT RECOVERED EOD"
    expected=int(meta.get("universe",expected_universe) or expected_universe)
    analyzed=int(pd.to_numeric(full.get("Close",pd.Series(dtype=float)),errors="coerce").notna().sum()) if not full.empty else 0
    if analyzed < min(expected,int(expected*0.90)): return False, f"INCOMPLETE RECOVERY ({analyzed}/{expected})"
    dates=pd.to_datetime(full.get("DataDate"),errors="coerce").dropna() if "DataDate" in full.columns else pd.Series(dtype="datetime64[ns]")
    if dates.empty: return False, "NO RECOVERY DATA DATE"
    latest=dates.max().date(); today=jakarta_now().date()
    if latest >= today: return False, "TODAY'S PARTIAL CANDLE IS NOT EOD"
    return True, "RECOVERED EOD VALIDATED"

def save_recovered_eod(bundle, source_label):
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); path=os.path.join(RECOVERY_DIR,stamp); os.makedirs(path,exist_ok=True)
    meta=dict(bundle.get("meta",{})); meta["scan_type"]="RECOVERED_EOD"; meta["eod_locked"]=False; meta["recovery_source"]=source_label; meta["recovered_at"]=jakarta_now().isoformat(timespec="seconds"); meta["data_contract"]="Validated latest completed EOD; recovery is not an official saved EOD snapshot"
    for k,f in [("full","full_scan.csv"),("top150","top150.csv"),("top50","top50.csv"),("top10","top10.csv"),("top3","top3.csv")]: bundle[k].to_csv(os.path.join(path,f),index=False)
    with open(os.path.join(path,"meta.json"),"w",encoding="utf-8") as f: json.dump(meta,f,ensure_ascii=False,indent=2)
    with open(os.path.join(RECOVERY_DIR,"latest.txt"),"w",encoding="utf-8") as f: f.write(stamp)
    bundle["meta"]=meta
    return bundle

def recover_eod_from_current_or_scan(period, n=600, min_rr=2.0, max_stop_pct=15.0):
    """Morning fallback: reuse a validated current scan first; otherwise build a fresh 600-stock completed-EOD scan. Never overwrites official EOD history."""
    current=load_current_scan()
    if current:
        full=current.get("full",pd.DataFrame()).copy(); meta=current.get("meta",{})
        expected=int(meta.get("universe",n) or n)
        dates=pd.to_datetime(full.get("DataDate"),errors="coerce").dropna() if "DataDate" in full.columns else pd.Series(dtype="datetime64[ns]")
        analyzed=int(pd.to_numeric(full.get("Close",pd.Series(dtype=float)),errors="coerce").notna().sum()) if not full.empty else 0
        latest=dates.max().date() if not dates.empty else None
        if analyzed >= min(expected,int(expected*0.90)) and latest is not None and latest < jakarta_now().date():
            recovered={"meta":dict(meta),"full":full,"top150":current.get("top150",pd.DataFrame()),"top50":current.get("top50",pd.DataFrame()),"top10":current.get("top10",pd.DataFrame()),"top3":current.get("top3",pd.DataFrame())}
            recovered=_ensure_layers(recovered)
            ok,reason=_validate_recovery_bundle({"meta":{**recovered["meta"],"scan_type":"RECOVERED_EOD","universe":expected},"full":recovered["full"]},expected)
            if ok:
                return save_recovered_eod(recovered,"CURRENT_SCAN validated as completed EOD")

    # No usable current scan: perform a fresh 600-stock scan. load_data() removes today's partial candle before 16:20 WIB.
    path=run_full_scan(period,n,min_rr,max_stop_pct,save_eod=False)
    current=load_current_scan() if path else None
    if not current: return None
    recovered={"meta":dict(current["meta"]),"full":current["full"].copy(),"top150":current["top150"].copy(),"top50":current["top50"].copy(),"top10":current["top10"].copy(),"top3":current["top3"].copy()}
    recovered=_ensure_layers(recovered)
    recovered["meta"]["scan_type"]="RECOVERED_EOD"
    ok,reason=_validate_recovery_bundle(recovered,n)
    return save_recovered_eod(recovered,"FRESH 600 CURRENT SCAN validated as completed EOD") if ok else None

def morning_baseline(period, n=600, min_rr=2.0, max_stop_pct=15.0):
    """Return official EOD if valid; otherwise use a validated non-official EOD recovery."""
    official=read_snapshot(latest_snapshot())
    if official:
        valid,_=official_eod_snapshot_valid(official,n)
        if valid: return official,"OFFICIAL EOD"
    recovery=latest_recovered_eod()
    if recovery:
        ok,_=_validate_recovery_bundle(recovery,n)
        if ok: return recovery,"AUTO EOD RECOVERY"
    return None,"NO VALID EOD BASELINE"

def latest_snapshot():
    marker=os.path.join(SNAP_DIR,"latest.txt")
    if os.path.exists(marker):
        stamp=open(marker,encoding="utf-8").read().strip(); p=os.path.join(SNAP_DIR,stamp)
        if os.path.isdir(p): return p
    ds=snapshot_dirs(); return ds[0] if ds else None

def _refresh_snapshot_risk_layers(snap):
    """Re-apply the current Risk Gate to persisted full_scan data.
    This prevents legacy snapshots from silently retaining old PASS/WAIT states.
    """
    if not snap or "full" not in snap or snap["full"].empty:
        return snap
    meta=snap.get("meta",{})
    full=snap["full"].copy()
    # Backfill ATR-derived metrics when older snapshots already contain ATR14.
    if "RiskPct" not in full.columns and {"Entry","SL"}.issubset(full.columns):
        ent=pd.to_numeric(full["Entry"],errors="coerce")
        sl=pd.to_numeric(full["SL"],errors="coerce")
        full["RiskPct"]=(ent-sl).abs()/ent.replace(0,np.nan)*100
    if "StopDistancePct" not in full.columns and "RiskPct" in full.columns:
        full["StopDistancePct"]=full["RiskPct"]
    if "RiskATRMultiple" not in full.columns:
        if "ATR14" in full.columns and {"Entry","SL"}.issubset(full.columns):
            atr=pd.to_numeric(full["ATR14"],errors="coerce")
            risk=(pd.to_numeric(full["Entry"],errors="coerce")-pd.to_numeric(full["SL"],errors="coerce")).abs()
            full["RiskATRMultiple"]=risk/atr.replace(0,np.nan)
        else:
            full["RiskATRMultiple"]=np.nan
    # Old snapshots may not have the newer metadata columns.
    if "AnalysisMode" not in full.columns:
        full["AnalysisMode"]="LEGACY / UNKNOWN"
    if "FactorCoveragePct" not in full.columns:
        full["FactorCoveragePct"]=np.nan
    if "MultiFactorScore" not in full.columns and "TechnicalScore" in full.columns:
        full["MultiFactorScore"]=pd.to_numeric(full["TechnicalScore"],errors="coerce")
    # Preserve the original market regime and threshold when available.
    min_rr=float(meta.get("min_rr",2.0) or 2.0)
    max_stop=float(meta.get("max_stop_pct",15.0) or 15.0)
    regime=str(meta.get("regime","NEUTRAL / SIDEWAYS"))
    full=apply_risk_gate(full,min_rr,max_stop,regime)
    enrich,focus,opp,action=build_layers(full,min_rr)
    meta=meta.copy()
    meta["engine_version_current"]=ENGINE_VERSION
    meta["risk_gate_version_current"]=RISK_GATE_VERSION
    meta["snapshot_refresh"]=datetime.now().isoformat(timespec="seconds")
    snap.update({"meta":meta,"full":full,"top150":enrich,"top50":focus,"top10":opp,"top3":action})
    return snap

def read_snapshot(path):
    if not path:return None
    try:
        meta=json.load(open(os.path.join(path,"meta.json"),encoding="utf-8"))
        data={k:pd.read_csv(os.path.join(path,f)) for k,f in [("full","full_scan.csv"),("top150","top150.csv"),("top50","top50.csv"),("top10","top10.csv"),("top3","top3.csv")]}
        snap={"meta":meta,**data}
        # Always refresh risk layers in memory using the current engine. The persisted
        # CSVs remain untouched, so EOD history is still an audit trail.
        return _ensure_layers(_refresh_snapshot_risk_layers(snap))
    except Exception:return None

def apply_risk_gate(result,min_rr,max_stop_pct=15.0,market_regime="NEUTRAL / SIDEWAYS"):
    x=result.copy(); gates=[]; flags=[]
    for _,r in x.iterrows():
        status=str(r.get("Status","WAIT")).upper()
        setup=str(r.get("Setup","WAIT")).upper()
        rr=float(pd.to_numeric(r.get("RR",np.nan),errors="coerce")) if pd.notna(r.get("RR",np.nan)) else np.nan
        mf=float(pd.to_numeric(r.get("MultiFactorScore",np.nan),errors="coerce")) if pd.notna(r.get("MultiFactorScore",np.nan)) else np.nan
        risk_pct=float(pd.to_numeric(r.get("RiskPct",np.nan),errors="coerce")) if pd.notna(r.get("RiskPct",np.nan)) else np.nan
        atr_mult=float(pd.to_numeric(r.get("RiskATRMultiple",np.nan),errors="coerce")) if pd.notna(r.get("RiskATRMultiple",np.nan)) else np.nan
        issues=[]
        if status!="READY": issues.append("TECH")
        if setup not in {"BREAKOUT","PULLBACK","REJECTION SUPPORT"}: issues.append("SETUP WAIT")
        if not pd.notna(rr) or rr < min_rr: issues.append("RR")
        if not pd.notna(mf) or mf < 65: issues.append("SCORE")
        if not pd.notna(risk_pct): issues.append("RISK DATA")
        elif risk_pct > max_stop_pct: issues.append("STOP DISTANCE")
        # ATR is now a required integrity check for a PASS. Missing ATR must never
        # silently become PASS; the user should know the risk metric is incomplete.
        if not pd.notna(atr_mult): issues.append("ATR DATA")
        elif atr_mult > 4.5: issues.append("ATR RISK")
        if str(market_regime).upper().startswith("RISK-OFF"): issues.append("MARKET")
        if not issues:
            gate="PASS"
        elif "TECH" in issues or "SETUP WAIT" in issues:
            gate="WAIT"
        elif "MARKET" in issues:
            gate="MARKET REVIEW"
        elif any(k in issues for k in ["STOP DISTANCE","ATR RISK","ATR DATA","RISK DATA"]):
            gate="RISK REVIEW"
        else:
            gate="FACTOR REVIEW"
        gates.append(gate); flags.append(", ".join(issues) if issues else "OK")
    x["RiskGate"]=gates; x["RiskFlag"]=flags; x["RiskGateVersion"]=RISK_GATE_VERSION
    stock_gates=[]; market_states=[]
    for _,r in x.iterrows():
        issues=str(r.get("RiskFlag","")); stock_issues=[q for q in issues.split(", ") if q and q != "MARKET"]
        stock_gates.append("PASS" if not stock_issues else ("RISK REVIEW" if any(q in stock_issues for q in ["STOP DISTANCE","ATR RISK","ATR DATA","RISK DATA"]) else ("FACTOR REVIEW" if "SCORE" in stock_issues else "WAIT")))
        market_states.append("RISK-OFF" if str(market_regime).upper().startswith("RISK-OFF") else ("RISK-ON" if str(market_regime).upper().startswith("RISK-ON") else "NEUTRAL"))
    x["StockSetupGate"]=stock_gates; x["MarketGate"]=market_states
    x["ActionableMode"]=np.where(x["RiskGate"]=="PASS",x["AnalysisMode"],"NOT ACTIONABLE")
    return x

def build_layers(result,min_rr):
    def sortdf(df, cols):
        use=[c for c in cols if c in df.columns]
        return df.sort_values(use,ascending=[False]*len(use)) if use else df
    enrich=sortdf(result,['MultiFactorScore','QualityScore','SetupScore','RR']).head(150).copy(); enrich['Layer']='TOP 150 ENRICH'
    focus=sortdf(result[result.RR>=min_rr],['MultiFactorScore','SetupScore','QualityScore','RR']).head(50).copy(); focus['Layer']='TOP 50 FOCUS'
    opp=sortdf(result[result.RR>=min_rr],['MultiFactorScore','OpportunityScore','SetupScore','RR']).head(10).copy(); opp['Layer']='TOP 10 OPPORTUNITY'
    if not opp.empty:
        opp=opp.copy(); opp['OpportunityRank']=range(1,len(opp)+1)
    action_pool=opp[(opp.Status.astype(str).str.upper()=='READY') & (opp.Setup.astype(str).str.upper().isin(['BREAKOUT','PULLBACK','REJECTION SUPPORT']))].copy()
    gate_rank={'PASS':0,'RISK REVIEW':1,'FACTOR REVIEW':2,'MARKET REVIEW':3,'WAIT':9}
    live_rank={'CONFIRM CANDIDATE':0,'READY — CONFIRM':1,'READY — WATCH':2,'WAIT — LIVE':3,'WAIT — MARKET':4,'WAIT — RESISTANCE':5,'WAIT — BELOW ENTRY':6,'WAIT — LIVE PRESSURE':7,'WAIT — CHASE':8,'DATA INSUFFICIENT':9,'WAIT — LIVE DATA':10,'CANCEL':11,'EOD LOCKED':0}
    if not action_pool.empty:
        action_pool['_gate_rank']=action_pool['RiskGate'].astype(str).str.upper().map(gate_rank).fillna(8)
        action_pool['_live_rank']=action_pool['LiveActionStatus'].astype(str).map(live_rank).fillna(7) if 'LiveActionStatus' in action_pool.columns else 7
        action_pool['_eq_sort']=pd.to_numeric(action_pool.get('EntryQualityScore',np.nan),errors='coerce').fillna(-999)
        action_pool['_opp_sort']=pd.to_numeric(action_pool.get('OpportunityScore',np.nan),errors='coerce').fillna(-999)
        action_pool['_risk_sort']=pd.to_numeric(action_pool.get('RiskPct',np.nan),errors='coerce').fillna(999)
        action_pool['EntryPriorityScore']=action_pool['_eq_sort']
        action=action_pool.sort_values(['_live_rank','_gate_rank','EntryPriorityScore','_opp_sort','MultiFactorScore','TechnicalScore','_risk_sort'],ascending=[True,True,False,False,False,False,True]).head(3).copy()
        action.drop(columns=['_gate_rank','_live_rank','_eq_sort','_opp_sort','_risk_sort'],errors='ignore',inplace=True)
    else:
        ready_all=result[result.Status.astype(str).str.upper()=='READY'].copy()
        action=sortdf(ready_all,['MultiFactorScore','TechnicalScore','OpportunityScore','SetupScore']).head(3).copy()
        action['EntryPriorityScore']=pd.to_numeric(action.get('EntryQualityScore',np.nan),errors='coerce')
    action['Layer']='TOP 3 ACTIONABLE'
    if not action.empty:
        action=action.copy()
        opp_rank_map={str(t):i+1 for i,t in enumerate(opp['Ticker'].astype(str))} if not opp.empty and 'Ticker' in opp.columns else {}
        action['OpportunityRank']=action['Ticker'].astype(str).map(opp_rank_map)
        action=action.sort_values(['EntryPriorityScore','MultiFactorScore'],ascending=[False,False]).reset_index(drop=True)
        action['EntryRank']=range(1,len(action)+1)
    return enrich,focus,opp,action

def _normalize_index_frame(d):
    """Normalize Yahoo index frames to one consistent timezone convention.

    Yahoo/yfinance can return tz-aware DatetimeIndex objects while the quote-page
    repair row is deliberately tz-naive. Mixing the two makes pandas fail during
    concat/sort_index with: "Cannot compare tz-naive and tz-aware timestamps".
    For EOD market data we preserve the displayed calendar date and strip timezone
    information after conversion to a DatetimeIndex.
    """
    if d is None or d.empty: return pd.DataFrame()
    if isinstance(d.columns,pd.MultiIndex):
        lvl0=set(map(str,d.columns.get_level_values(0)))
        d=d.copy(); d.columns=d.columns.get_level_values(0) if "Close" in lvl0 else d.columns.get_level_values(1)
    d=d.copy(); d.columns=[str(c) for c in d.columns]
    if "Close" not in d.columns: return pd.DataFrame()

    # Critical: make every source use tz-naive timestamps before concat/sort.
    # Preserve the source's calendar date rather than shifting an EOD session.
    try:
        idx=pd.DatetimeIndex(pd.to_datetime(d.index,errors="coerce"))
        if idx.tz is not None:
            idx=idx.tz_localize(None)
        d.index=idx
    except Exception:
        return pd.DataFrame()
    d=d[~d.index.isna()].copy()
    d=d[[c for c in ["Open","High","Low","Close","Volume"] if c in d.columns]].copy()
    d["Close"]=pd.to_numeric(d["Close"],errors="coerce")
    d=d.dropna(subset=["Close"])
    return d

def _completed_eod_cutoff_date():
    """Latest calendar date that is allowed to be treated as completed EOD.

    Before the IDX close/lock time, today's date is NEVER an EOD date. This is
    the key morning-safety rule: a live 06-Oct quote cannot become 06-Oct EOD.
    After 16:20 WIB, today's completed session may be accepted.
    """
    now=jakarta_now()
    if (now.hour > 16) or (now.hour == 16 and now.minute >= 20):
        return now.date()
    from datetime import timedelta
    return now.date()-timedelta(days=1)

def fetch_jkse_eod(min_date=None):
    """Fetch IHSG EOD with a strict morning EOD lock.

    Rules:
      * Before 16:20 WIB, the current calendar date is forbidden as EOD.
      * Intraday/regularMarketPrice is never used as an EOD close.
      * All candidate sources are normalized to tz-naive calendar dates.
      * The latest accepted date must satisfy the requested synchronization date.
      * We prefer the freshest completed EOD, not the freshest live quote.
    """
    cutoff=_completed_eod_cutoff_date()
    candidates=[]
    try:
        d=yf.download("^JKSE",period="1y",interval="1d",auto_adjust=False,progress=False,threads=False,group_by="column")
        d=_normalize_index_frame(d)
        if not d.empty: candidates.append((d,"Yahoo Finance fresh EOD"))
    except Exception:
        pass
    try:
        hist=yf.Ticker("^JKSE").history(period="1y",interval="1d",auto_adjust=False,repair=False)
        d=_normalize_index_frame(hist)
        if not d.empty: candidates.append((d,"Yahoo Finance ticker history"))
    except Exception:
        pass
    for host in ["query1.finance.yahoo.com","query2.finance.yahoo.com"]:
        try:
            url=f"https://{host}/v8/finance/chart/%5EJKSE?range=1y&interval=1d&events=history"
            req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=15) as resp:
                payload=json.loads(resp.read().decode("utf-8"))
            r=payload.get("chart",{}).get("result",[None])[0]
            if r:
                ts=r.get("timestamp",[]); q=r.get("indicators",{}).get("quote",[{}])[0]
                idx=pd.to_datetime(ts,unit="s",utc=True).tz_convert("Asia/Jakarta").tz_localize(None)
                d=pd.DataFrame({"Open":q.get("open",[]),"High":q.get("high",[]),"Low":q.get("low",[]),"Close":q.get("close",[]),"Volume":q.get("volume",[])},index=idx)
                d=_normalize_index_frame(d)
                if not d.empty: candidates.append((d,f"Yahoo Chart API ({host})"))
        except Exception:
            pass

    target=pd.Timestamp(min_date).date() if min_date is not None else None
    valid=[]
    for d,source in candidates:
        try:
            dates=pd.to_datetime(d.index,errors="coerce")
            d=d.loc[dates.notna()].copy()
            d=d.loc[[pd.Timestamp(x).date() <= cutoff for x in d.index]]
            if d.empty: continue
            d=d[~d.index.duplicated(keep="last")].sort_index()
            latest=pd.Timestamp(d.index[-1]).date()
            if target is not None and latest < target:
                continue
            valid.append((d,source))
        except Exception:
            continue

    if valid:
        valid.sort(key=lambda x:(pd.Timestamp(x[0].index[-1]).date(),len(x[0])),reverse=True)
        return valid[0]
    return pd.DataFrame(), f"DATA STALE / BLOCKED (completed EOD cutoff {cutoff.isoformat()})"

def _latest_stock_data_date(df):
    try:
        dates=pd.to_datetime(df.get("DataDate"),errors="coerce").dropna()
        return dates.max().date() if not dates.empty else None
    except Exception:
        return None

def run_full_scan(period,n,min_rr,max_stop_pct=15.0,save_eod=True):
    # Keep enough history internally for MA200/RSI/MACD, while the selected
    # period controls the EOD review window saved in the snapshot.
    engine_period="2y"
    uni=load_universe()[:n]; rows=[]; prog=st.progress(0,text=f"Scanning 0/{len(uni)}")
    for i,t in enumerate(uni,1):
        d=load_data(t,engine_period,"1d")
        r=analyze(d)
        if r:
            r["Ticker"]=t; r["EODWindow"]=period; r["TradingView"]=tv_link(t); rows.append(r)
        prog.progress(i/len(uni),text=f"Scanning {i}/{len(uni)} • berhasil {len(rows)}")
    prog.empty(); result=pd.DataFrame(rows)
    if result.empty:return None

    # CURRENT SCAN gets a fresh intraday quote overlay. Official EOD scans do not
    # use this value, so the EOD close remains locked and reproducible.
    if not save_eod:
        live=load_live_prices(result["Ticker"].astype(str).tolist())
        result["CurrentPrice"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("price",np.nan))
        result["CurrentQuoteTime"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("time","—"))
        result["PriceMode"]=np.where(pd.to_numeric(result["CurrentPrice"],errors="coerce").notna(),"CURRENT QUOTE","EOD FALLBACK")
        result["CurrentChangePct"]=np.nan
        result["SessionOpen"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("session_open",np.nan))
        result["SessionHigh"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("session_high",np.nan))
        result["SessionLow"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("session_low",np.nan))
        result["IntradayVWAP"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("intraday_vwap",np.nan))
        result["LiveVolumeRatio"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("live_volume_ratio",np.nan))
        result["LastBarChangePct"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("last_bar_change_pct",np.nan))
        result["SessionChangePct"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("session_change_pct",np.nan))
        result["LiveBullishBar"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("bullish_bar",False))
        result["IntradayDataQuality"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("data_quality","INSUFFICIENT"))
        result["IntradayDataAgeMin"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("data_age_min",np.nan))
        result["IntradayBarCount"]=result["Ticker"].map(lambda t: live.get(str(t).upper(),{}).get("bar_count",0))
        result["LiveBelowVWAP"]=np.where(pd.to_numeric(result["IntradayVWAP"],errors="coerce").notna(),pd.to_numeric(result["CurrentPrice"],errors="coerce")<pd.to_numeric(result["IntradayVWAP"],errors="coerce"),False)
        result["LiveBelowSessionOpen"]=np.where(pd.to_numeric(result["SessionOpen"],errors="coerce").notna(),pd.to_numeric(result["CurrentPrice"],errors="coerce")<pd.to_numeric(result["SessionOpen"],errors="coerce"),False)
        valid=result["CurrentPrice"].notna()
        result.loc[valid,"CurrentChangePct"]=(pd.to_numeric(result.loc[valid,"CurrentPrice"],errors="coerce")/pd.to_numeric(result.loc[valid,"Close"],errors="coerce")-1)*100
    else:
        result["CurrentPrice"]=np.nan; result["CurrentQuoteTime"]="—"; result["PriceMode"]="OFFICIAL EOD"; result["CurrentChangePct"]=np.nan

    result=factor_enrich(result)
    stock_date=_latest_stock_data_date(result)
    market_target=min(stock_date, _completed_eod_cutoff_date()) if stock_date is not None else _completed_eod_cutoff_date()
    ih,ih_source=fetch_jkse_eod(market_target)
    ih_date=pd.Timestamp(ih.index[-1]).strftime("%Y-%m-%d") if not ih.empty else None
    if len(ih)>=220 and (stock_date is None or pd.Timestamp(ih.index[-1]).date()>=stock_date):
        ic=pd.to_numeric(ih.Close,errors="coerce").dropna(); ihsg=float(ic.iloc[-1]); ih20=float(ic.rolling(20).mean().iloc[-1]); ih50=float(ic.rolling(50).mean().iloc[-1]); regime="RISK-ON" if ihsg>ih20>ih50 else ("NEUTRAL / SIDEWAYS" if ihsg>=ih50 else "RISK-OFF")
    else:
        ihsg=ih20=ih50=np.nan; regime="DATA STALE / MISMATCH"
    result=apply_risk_gate(result,min_rr,max_stop_pct,regime)
    if not save_eod:
        if "IntradayDataQuality" not in result.columns:
            result["IntradayDataQuality"]="INSUFFICIENT"
        result=apply_live_action_gate(result,regime)
    else:
        result["LiveActionStatus"]="EOD LOCKED"; result["LivePressure"]="NOT APPLICABLE"; result["PressureConfidence"]="NONE"; result["LiveActionReason"]="official EOD snapshot — use Morning Confirmation for next session"; result["EntryQualityScore"]=np.nan; result["DistanceToResistancePct"]=np.nan; result["ResistanceRoomClass"]="NOT APPLICABLE"; result["NextTrigger"]="Morning Confirmation / next-session validation"; result["Invalidation"]="see EOD SL / structure"; result["IntradayDataQuality"]="EOD LOCKED"; result["IntradayDataAgeMin"]=np.nan; result["IntradayBarCount"]=0
    enrich,focus,opp,action=build_layers(result,min_rr)
    meta={"timestamp":jakarta_now().isoformat(timespec="seconds"),"period":period,"engine_period":engine_period,"universe":n,"analyzed":len(result),"min_rr":min_rr,"max_stop_pct":max_stop_pct,"ihsg":ihsg,"ihsg_ma20":ih20,"ihsg_ma50":ih50,"ihsg_data_date":ih_date,"ihsg_data_source":ih_source,"regime":regime,"analysis_mode":"HYBRID","engine_version":ENGINE_VERSION,"risk_gate_version":RISK_GATE_VERSION,"data_source":"Yahoo Finance EOD + Yahoo Chart API + Yahoo quote-page EOD repair","data_contract":"IHSG uses the latest completed EOD only; before 16:20 WIB today's date is forbidden as EOD; intraday/stale/mismatched index data is blocked","scan_type":"OFFICIAL_EOD" if save_eod else "CURRENT_SCAN","eod_locked":bool(save_eod),"eod_data_date":(result["DataDate"].dropna().max() if "DataDate" in result.columns and not result["DataDate"].dropna().empty else None)}
    if save_eod:
        return save_snapshot(result,enrich,focus,opp,action,meta)
    current_meta=dict(meta); current_meta["scan_type"]="CURRENT_SCAN"
    save_current_scan(result,enrich,focus,opp,action,current_meta)
    st.session_state["current_scan"]={"meta":current_meta,"full":result,"top150":enrich,"top50":focus,"top10":opp,"top3":action}
    return "CURRENT_SCAN"

def market_metrics(period):
    """Return IHSG metrics synchronized to the latest completed stock EOD date.
    Never fall back to an older index close merely to fill the card.
    """
    target=None
    current=st.session_state.get("current_scan")
    if current and not current.get("full",pd.DataFrame()).empty:
        stock_target=_latest_stock_data_date(current["full"])
        cutoff=_completed_eod_cutoff_date()
        if stock_target is not None:
            target=min(stock_target, cutoff)
    if target is None:
        sp=latest_snapshot()
        if sp:
            try:
                sm=json.load(open(os.path.join(sp,"meta.json"),encoding="utf-8")); target=pd.Timestamp(sm.get("eod_data_date")).date() if sm.get("eod_data_date") else None
            except Exception: pass
    ih,source=fetch_jkse_eod(target)
    if len(ih)>=50:
        c=pd.to_numeric(ih["Close"],errors="coerce").dropna()
        latest_date=pd.Timestamp(ih.index[-1]).strftime("%Y-%m-%d")
        if len(c)>=50:
            a=float(c.iloc[-1]); b=float(c.rolling(20).mean().iloc[-1]); d=float(c.rolling(50).mean().iloc[-1])
            regime="🟢 RISK-ON" if a>b>d else ("🟡 NEUTRAL / SIDEWAYS" if a>=d else "🔴 RISK-OFF")
            st.session_state["market_data_meta"]={"date":latest_date,"source":source,"status":"VALID"}
            return a,b,d,regime
    st.session_state["market_data_meta"]={"date":"—","source":source,"status":"STALE / BLOCKED"}
    return None,None,None,"🟡 DATA STALE / BLOCKED"

def jakarta_now():
    try:
        return datetime.now(ZoneInfo("Asia/Jakarta")) if ZoneInfo else datetime.now()
    except Exception:
        return datetime.now()

def _parse_iso_dt(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z","+00:00"))
    except Exception:
        return None

def eod_lock_open():
    now = jakarta_now()
    return (now.hour > 16) or (now.hour == 16 and now.minute >= 20)

def official_eod_snapshot_valid(snap, expected_universe=600):
    """Strict gate for the morning dashboard. Never treat a current/ad-hoc scan as EOD."""
    if not snap:
        return False, "NO OFFICIAL EOD SNAPSHOT"
    meta=snap.get("meta",{})
    if str(meta.get("scan_type","")).upper() not in {"OFFICIAL_EOD", "EOD"} and not bool(meta.get("eod_locked",False)):
        return False, "SNAPSHOT NOT MARKED OFFICIAL EOD"
    full=snap.get("full",pd.DataFrame())
    expected=int(meta.get("universe",expected_universe) or expected_universe)
    analyzed=int(pd.to_numeric(full.get("Close",pd.Series(dtype=float)),errors="coerce").notna().sum()) if not full.empty else 0
    if analyzed < min(expected, int(expected*0.90)):
        return False, f"INCOMPLETE EOD DATA ({analyzed}/{expected})"
    dates=pd.to_datetime(full.get("DataDate"),errors="coerce").dropna() if "DataDate" in full.columns else pd.Series(dtype="datetime64[ns]")
    if dates.empty:
        return False, "NO EOD DATA DATE"
    latest=dates.max().date()
    today=jakarta_now().date()
    if not eod_lock_open() and latest >= today:
        return False, "TODAY'S PARTIAL CANDLE IS NOT EOD"
    if str(meta.get("data_source","")).strip()=="":
        return False, "UNKNOWN DATA SOURCE"
    return True, "OFFICIAL EOD VALID"

def morning_data_readiness(snap, expected_universe=600):
    if not snap:
        return {"Ready":False,"Level":"NO SNAPSHOT","Reason":"Belum ada EOD baseline yang dapat divalidasi."}
    meta=snap.get("meta",{}); scan_type=str(meta.get("scan_type","")).upper()
    if scan_type=="RECOVERED_EOD":
        valid, valid_reason=_validate_recovery_bundle(snap,expected_universe)
    else:
        valid, valid_reason=official_eod_snapshot_valid(snap, expected_universe)
    full=snap.get("full",pd.DataFrame())
    required=["Ticker","Close","MA20","MA50","MA200","RSI","MACD","VolumeRatio","ATR14","Entry","SL","TP1","TP2","RR","RiskPct","RiskATRMultiple","Status","DataDate"]
    missing=[c for c in required if c not in full.columns]
    meta_expected=int(meta.get("universe",expected_universe) or expected_universe)
    if missing:
        return {"Ready":False,"Level":"DATA INCOMPLETE","Reason":"Kolom wajib belum lengkap: "+", ".join(missing),"Analyzed":0,"Expected":meta_expected,"LatestDataDate":"—"}
    n=int(pd.to_numeric(full["Close"],errors="coerce").notna().sum()); dates=pd.to_datetime(full["DataDate"],errors="coerce").dropna()
    latest_date=dates.max().strftime("%Y-%m-%d") if not dates.empty else None; latest_age=_days_since(latest_date) if latest_date else 999
    top=snap.get("top10",pd.DataFrame()); candidate_missing=[]
    if not top.empty:
        for c in required:
            if c in top.columns and top[c].isna().any(): candidate_missing.append(c)
    if not valid: level="REVIEW"; reason=valid_reason
    elif latest_age>5: level="STALE"; reason="Daily EOD terakhir terlalu lama"
    elif n<min(meta_expected,int(meta_expected*0.90)) or candidate_missing: level="REVIEW"; reason="Periksa coverage/kelengkapan kandidat"
    else:
        level="READY" if scan_type!="RECOVERED_EOD" else "READY · RECOVERED"
        reason=("Official EOD lengkap, terkunci, dan tidak memakai candle hari berjalan" if scan_type!="RECOVERED_EOD" else "EOD terakhir ditemukan dan divalidasi; bukan snapshot resmi tersimpan")
    return {"Ready":level.startswith("READY"),"Level":level,"Reason":reason,"SnapshotTimestamp":meta.get("timestamp",meta.get("recovered_at","—")),"SnapshotAgeHours":0,"Analyzed":n,"Expected":meta_expected,"LatestDataDate":latest_date or "—","LatestDataAgeDays":latest_age,"UniqueDataDates":int(dates.dt.strftime("%Y-%m-%d").nunique()) if not dates.empty else 0,"CandidateMissing":candidate_missing,"Validation":valid_reason,"SourceType":scan_type}

def _days_since(date_str):
    try:
        d=pd.Timestamp(date_str).date(); return (jakarta_now().date()-d).days
    except Exception:
        return 999

def morning_confirm(top10,period,market_regime="NEUTRAL / SIDEWAYS"):
    """Morning validation MUST use the locked official EOD snapshot.
    Never fetch today's partial daily candle here: before the open a data provider can
    already expose an incomplete current-day bar, which would incorrectly overwrite
    the EOD close shown on the candidate card.
    """
    rows=[]; market=str(market_regime).upper()
    for _,r in top10.iterrows():
        ticker=str(r.get("Ticker",""))
        if not ticker: continue
        # The official EOD snapshot is the sole pre-open price reference.
        ref=pd.to_numeric(pd.Series([r.get("Close",np.nan)]),errors="coerce").iloc[0]
        if not np.isfinite(ref):
            continue
        last_date=str(r.get("DataDate","") or "")
        data_age=_days_since(last_date) if last_date else 999
        eod_entry=float(r.get("Entry",np.nan)); sl=float(r.get("SL",np.nan))
        entry_low=eod_entry*.985; entry_high=eod_entry*1.025
        base_status=str(r.get("Status","WAIT")).upper()
        avoid_reason=str(r.get("AvoidReason","—"))
        if data_age>5:
            status="DATA STALE"; reason="Official EOD data terlalu lama"
        elif base_status=="AVOID":
            status="AVOID — SETUP"; reason=avoid_reason if avoid_reason not in {"","—","nan"} else "Setup/risk condition tidak memenuhi"
        elif np.isfinite(sl) and ref<sl:
            status="CANCEL"; reason="EOD reference berada di bawah SL"
        elif market.startswith("RISK-OFF"):
            status="WAIT — MARKET"; reason="Market Gate RISK-OFF"
        elif ref<entry_low:
            status="WAIT — BELOW ENTRY"; reason="Menunggu harga masuk area entry"
        elif ref<=entry_high:
            status="CONFIRM CANDIDATE"; reason="EOD reference berada di area entry"
        else:
            status="WAIT — TOO HIGH"; reason="EOD reference terlalu jauh di atas entry"
        market_gate=("RISK-OFF" if market.startswith("RISK-OFF") else ("RISK-ON" if market.startswith("RISK-ON") else "NEUTRAL"))
        if np.isfinite(eod_entry) and eod_entry > 0:
            distance_entry_pct=(ref-eod_entry)/eod_entry*100.0
        else:
            distance_entry_pct=np.nan
        if ref < entry_low:
            entry_position="BELOW ENTRY"
        elif ref <= entry_high:
            entry_position="IN ENTRY ZONE"
        else:
            entry_position="ABOVE ENTRY"
        x=r.to_dict(); x.update({
            "PreOpenReference":ref,
            "Current":ref,
            "Open":np.nan,
            "GapVsCurrentPct":np.nan,
            "LastDataDate":last_date or "—",
            "DataAgeDays":data_age,
            "DataStatus":"VALID EOD" if data_age<=5 else "STALE",
            "MorningStatus":status,
            "MorningReason":reason,
            "MarketGate":market_gate,
            "EntryLow":tick(entry_low),
            "EntryHigh":tick(entry_high),
            "DistanceToEntryPct":round(float(distance_entry_pct),2) if np.isfinite(distance_entry_pct) else np.nan,
            "EntryPosition":entry_position,
            "Decision":"USER DECISION"
        })
        rows.append(x)
    return pd.DataFrame(rows)

# =========================================================
# TRADINGVIEW
# =========================================================
def tv_symbol(ticker): return f"IDX:{ticker.upper().replace('.JK','')}"

def tradingview_chart(ticker, interval="D", height=860, theme="light", studies=None):
    """Large TradingView Advanced Chart with the core Sanggul indicator stack."""
    studies=studies or [
        "MASimple@tv-basicstudies",
        "BB@tv-basicstudies",
        "Volume@tv-basicstudies",
        "MACD@tv-basicstudies",
        "RSI@tv-basicstudies",
    ]
    symbol=tv_symbol(ticker)
    config={
        "autosize":True,
        "symbol":symbol,
        "interval":interval,
        "timezone":"Asia/Jakarta",
        "theme":theme,
        "style":"1",
        "withdateranges":True,
        "hide_side_toolbar":False,
        "allow_symbol_change":True,
        "save_image":False,
        "hide_top_toolbar":False,
        "hide_legend":False,
        "hide_volume":False,
        "locale":"en",
        "studies":studies,
        "calendar":False,
        "support_host":"https://www.tradingview.com",
        "show_popup_button":True,
        "popup_width":"1000",
        "popup_height":str(max(650,height)),
    }
    html=f"""
    <div class=\"tradingview-widget-container\" style=\"height:{height}px;width:100%;border:1px solid #d9e2ef;border-radius:14px;overflow:hidden;background:#fff\">
      <div class=\"tradingview-widget-container__widget\" style=\"height:100%;width:100%\"></div>
      <script type=\"text/javascript\" src=\"https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js\" async>
      {json.dumps(config)}
      </script>
    </div>"""
    components.html(html,height=height+18,scrolling=False)

def tv_link(t, interval="1D"):
    """Open TradingView Supercharts directly for an IDX symbol.
    The full TradingView chart is intentionally used instead of an embedded chart.
    Symbol/interval are passed in the URL; indicator templates are managed by TradingView itself.
    """
    sym = tv_symbol(t)
    return f"https://www.tradingview.com/chart/?symbol={sym}&interval={interval}"

# =========================================================
# SECTOR OPPORTUNITY
# =========================================================
SECTOR_MAP = {
    # Financials
    "BBCA":"Financials","BBRI":"Financials","BMRI":"Financials","BBNI":"Financials","BRIS":"Financials","BBTN":"Financials","BDMN":"Financials","BNGA":"Financials","NISP":"Financials","PNBN":"Financials","BJBR":"Financials","BJTM":"Financials","MEGA":"Financials","BBHI":"Financials","BTPN":"Financials","AGRO":"Financials","BANK":"Financials","BACA":"Financials","BBYB":"Financials","BBKP":"Financials","BBLD":"Financials","BEKS":"Financials","BVIC":"Financials","NOBU":"Financials","ARTO":"Financials","AMAR":"Financials","BANK":"Financials",
    # Energy
    "ADRO":"Energy","AADI":"Energy","PTBA":"Energy","ITMG":"Energy","INDY":"Energy","MEDC":"Energy","PGAS":"Energy","AKRA":"Energy","GEMS":"Energy","BSSR":"Energy","HRUM":"Energy","BYAN":"Energy","DEWA":"Energy","DOID":"Energy","DSSA":"Energy","BUMI":"Energy","TOBA":"Energy","MBAP":"Energy","MYOH":"Energy","SMMT":"Energy","TPMA":"Energy","CUAN":"Energy","BREN":"Energy",
    # Basic Materials / Chemicals / Metals
    "ANTM":"Basic Materials","INCO":"Basic Materials","TINS":"Basic Materials","MDKA":"Basic Materials","AMMN":"Basic Materials","SMGR":"Basic Materials","INTP":"Basic Materials","WTON":"Basic Materials","WIKA":"Basic Materials","WSBP":"Basic Materials","SMBR":"Basic Materials","KRAS":"Basic Materials","BRPT":"Basic Materials","TPIA":"Basic Materials","FPNI":"Basic Materials","INKP":"Basic Materials","TKIM":"Basic Materials","ALDO":"Basic Materials","ARNA":"Basic Materials","MARK":"Basic Materials","MINE":"Basic Materials","MBSS":"Basic Materials","ESSA":"Basic Materials","SCCO":"Basic Materials",
    # Industrials / Infrastructure
    "ASII":"Industrials","AUTO":"Industrials","GJTL":"Industrials","IMAS":"Industrials","SMSM":"Industrials","UNTR":"Industrials","HEXA":"Industrials","DRMA":"Industrials","MMLP":"Industrials","KOBX":"Industrials","TRJA":"Industrials","BIRD":"Industrials","ASSA":"Industrials","JSMR":"Infrastructure","TLKM":"Infrastructure","EXCL":"Infrastructure","ISAT":"Infrastructure","MTEL":"Infrastructure","TOWR":"Infrastructure","TBIG":"Infrastructure","MORA":"Infrastructure","CMNP":"Infrastructure","WIFI":"Infrastructure","LINK":"Infrastructure","CENT":"Infrastructure",
    # Consumer
    "ICBP":"Consumer","INDF":"Consumer","MYOR":"Consumer","UNVR":"Consumer","HMSP":"Consumer","GGRM":"Consumer","SIDO":"Consumer","KLBF":"Consumer","KAEF":"Consumer","MIKA":"Consumer","ERAA":"Consumer","ACES":"Consumer","AMRT":"Consumer","MAPI":"Consumer","MAPA":"Consumer","RALS":"Consumer","MIDI":"Consumer","ULTJ":"Consumer","ROTI":"Consumer","GOOD":"Consumer","CLEO":"Consumer","CPIN":"Consumer","JPFA":"Consumer","MAIN":"Consumer","WTON":"Industrials",
    # Property / Real Estate
    "BSDE":"Property","CTRA":"Property","PWON":"Property","SMRA":"Property","LPKR":"Property","ASRI":"Property","APLN":"Property","DMAS":"Property","MKPI":"Property","DILD":"Property","KIJA":"Property","BEST":"Property","EMDE":"Property","PPRO":"Property","BKSL":"Property",
    # Technology / Digital
    "GOTO":"Technology","BUKA":"Technology","EMTK":"Technology","DCII":"Technology","DMMX":"Technology","WIRG":"Technology","MCAS":"Technology","MLPT":"Technology","MLPL":"Technology","DNET":"Technology","EDGE":"Technology","TECH":"Technology","CYBR":"Technology","NFCX":"Technology","WIFI":"Infrastructure",
    # Healthcare
    "SILO":"Healthcare","MIKA":"Healthcare","HEAL":"Healthcare","PRDA":"Healthcare","PRAY":"Healthcare","DGNS":"Healthcare","KLBF":"Healthcare","KAEF":"Healthcare","SIDO":"Healthcare",
    # Transportation / Logistics
    "GIAA":"Transportation","ASSA":"Transportation","BIRD":"Transportation","SMDR":"Transportation","TMAS":"Transportation","SOCI":"Transportation","HAIS":"Transportation","ELPI":"Transportation","PSSI":"Transportation","TRUK":"Transportation",
    # Agriculture / Plantation
    "AALI":"Agriculture","LSIP":"Agriculture","SIMP":"Agriculture","SSMS":"Agriculture","DSNG":"Agriculture","TBLA":"Agriculture","TAPG":"Agriculture","SMAR":"Agriculture","BWPT":"Agriculture","SGRO":"Agriculture","CPRO":"Agriculture","BISI":"Agriculture",
}

def sector_of(ticker):
    return SECTOR_MAP.get(str(ticker).upper().replace('.JK',''), 'Other / Belum Dipetakan')

def sector_opportunity(df):
    if df is None or df.empty:return pd.DataFrame()
    x=df.copy(); x['Sector']=x['Ticker'].map(sector_of)
    # Composite opportunity summary; not a buy ranking.
    g=x.groupby('Sector',dropna=False).agg(
        Stocks=('Ticker','count'),
        Ready=('Status',lambda s:int((s.astype(str).str.upper()=='READY').sum())),
        AvgOpportunity=('OpportunityScore','mean'),
        AvgSetup=('SetupScore','mean'),
        AvgQuality=('QualityScore','mean'),
        AvgRR=('RR','mean'),
        AvgRSI=('RSI','mean'),
    ).reset_index()
    g['ReadyPct']=np.where(g['Stocks']>0,g['Ready']/g['Stocks']*100,0)
    g['SectorOpportunityScore']=g['AvgOpportunity']*0.45+g['AvgSetup']*0.25+g['AvgQuality']*0.20+g['AvgRR']*2*0.10
    return g.sort_values(['SectorOpportunityScore','ReadyPct'],ascending=False)

# =========================================================
# PRESENTATION HELPERS
# =========================================================
def fmt(x,d=0):
    try:
        v=float(x)
        if not np.isfinite(v): return "—"
        return f"{v:,.{d}f}"
    except:return "—"

def status_badge(s):
    s=str(s).upper(); cls="badge-green" if s in ["READY","CONFIRM"] else ("badge-red" if s in ["AVOID","CANCEL"] else "badge-yellow")
    return f'<span class="badge {cls}">{s}</span>'

def morning_status_badge(s):
    s=str(s).upper()
    if s.startswith("CONFIRM"): cls="badge-green"
    elif s.startswith("CANCEL") or s.startswith("AVOID") or s.startswith("DATA STALE"): cls="badge-red"
    else: cls="badge-yellow"
    return f'<span class="badge {cls}">{s}</span>'

def header(title,subtitle=""):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',unsafe_allow_html=True)

def metric_strip(items):
    cols=st.columns(len(items))
    for col,(lab,val) in zip(cols,items):
        with col: st.markdown(f'<div class="metric-card"><div class="metric-label">{lab}</div><div class="metric-value">{val}</div></div>',unsafe_allow_html=True)

def show_table(df,cols,expand_label="📋 Buka Tabel"):
    if df is None or df.empty: st.info("Belum ada data pada menu ini."); return
    use=[c for c in cols if c in df.columns]
    with st.expander(expand_label,expanded=False):
        st.dataframe(df[use],use_container_width=True,hide_index=True)

def show_table_open(df,cols,expand_label="📋 Buka Tabel"):
    if df is None or df.empty: st.info("Belum ada data pada menu ini."); return
    use=[c for c in cols if c in df.columns]
    with st.expander(expand_label,expanded=True):
        st.dataframe(df[use],use_container_width=True,hide_index=True)

def risk_badge(gate):
    g=str(gate).upper(); cls='badge-green' if g=='PASS' else ('badge-yellow' if 'REVIEW' in g else 'badge-red')
    return f'<span class="badge {cls}">{g}</span>'

def _decision_card_html(i, r, mr, mode="top3"):
    ticker=str(r.get('Ticker','—')); setup=str(r.get('Setup','—'))
    live_price=pd.to_numeric(pd.Series([r.get('CurrentPrice',np.nan)]),errors='coerce').iloc[0]
    is_current=str(r.get('PriceMode','')).upper()=='CURRENT QUOTE' and np.isfinite(live_price)
    pref=fmt(live_price if is_current else mr.get('PreOpenReference',r.get('Close',np.nan)))
    price_label='CURRENT QUOTE' if is_current else 'EOD REFERENCE'
    quote_time=str(r.get('CurrentQuoteTime','')) if is_current else ''
    entry=fmt(r.get('Entry',np.nan)); lo=fmt(mr.get('EntryLow',r.get('Entry',np.nan))); hi=fmt(mr.get('EntryHigh',r.get('Entry',np.nan)))
    sl=fmt(r.get('SL',np.nan)); tp1=fmt(r.get('TP1',np.nan)); rr=fmt(r.get('RR',np.nan),2)
    score=fmt(r.get('MultiFactorScore',np.nan),1); eod_score=fmt(r.get('OpportunityScore',np.nan),0); cov=fmt(r.get('FactorCoveragePct',np.nan),0)
    stock_gate=str(r.get('StockSetupGate','—')); market_gate=str(mr.get('MarketGate',r.get('MarketGate','—')))
    mstatus=str(mr.get('MorningStatus','NOT VALIDATED')); reason=str(mr.get('MorningReason','—')); pos=str(mr.get('EntryPosition','—')); dist=fmt(mr.get('DistanceToEntryPct',np.nan),1)
    live_status=str(r.get('LiveActionStatus','—')); live_pressure=str(r.get('LivePressure','—'))
    display_status=live_status if is_current and live_status not in {'—','EOD LOCKED'} else mstatus
    # In a current/ad-hoc scan, the displayed position is recalculated from the
    # refreshed quote. Morning Confirmation itself still uses the locked EOD reference.
    if is_current and np.isfinite(live_price):
        e=float(r.get('Entry',np.nan)); lo_c=e*.985 if np.isfinite(e) else np.nan; hi_c=e*1.025 if np.isfinite(e) else np.nan
        if np.isfinite(e) and e>0:
            dist=fmt((live_price-e)/e*100.0,1)
            pos='BELOW ENTRY' if live_price<lo_c else ('IN ENTRY ZONE' if live_price<=hi_c else 'ABOVE ENTRY')
    data=str(mr.get('DataStatus','UNKNOWN')); age=mr.get('DataAgeDays',r.get('DataAgeDays','—')); eod_date=mr.get('LastDataDate',r.get('DataDate','—'))
    risk=fmt(r.get('RiskPct',np.nan),1); atr=fmt(r.get('RiskATRMultiple',np.nan),1)
    live_vwap=fmt(r.get('IntradayVWAP',np.nan),0); live_vr=fmt(r.get('LiveVolumeRatio',np.nan),1)
    eq=fmt(r.get('EntryQualityScore',np.nan),0); res_room=fmt(r.get('DistanceToResistancePct',np.nan),1)
    trigger=str(r.get('NextTrigger','—')); invalidation=str(r.get('Invalidation','—'))
    why=[]
    if setup and setup!='WAIT': why.append(setup.lower())
    if stock_gate.upper()=='PASS': why.append('stock setup PASS')
    if pos=='IN ENTRY ZONE': why.append('inside entry zone')
    if market_gate.upper()!='PASS': why.append(f'market {market_gate}')
    if is_current and live_pressure not in {'—','UNKNOWN','MIXED'}: why.append(live_pressure.lower())
    why_text=' · '.join(why[:3]) or reason
    rank_style='decision-rank' if mode=='top3' else 'op10-rank'
    opp_rank=r.get('OpportunityRank','—'); entry_rank=r.get('EntryRank','—'); entry_priority=fmt(r.get('EntryPriorityScore',np.nan),0)
    intraday_q=str(r.get('IntradayDataQuality','—')); intraday_age=fmt(r.get('IntradayDataAgeMin',np.nan),0)
    opp_num=pd.to_numeric(pd.Series([opp_rank]),errors='coerce').iloc[0]; ent_num=pd.to_numeric(pd.Series([entry_rank]),errors='coerce').iloc[0]
    rank_label=(f"Opportunity #{int(opp_num)} · Entry #{int(ent_num)}" if mode=='top3' and pd.notna(opp_num) and pd.notna(ent_num) else f"Opportunity #{opp_rank}")
    return f'''<div class="decision-card">
<div class="decision-head"><div><span class="{rank_style}">{i}</span><span class="decision-ticker">{ticker}</span><div class="decision-rank-sub">{rank_label}</div></div>{morning_status_badge(display_status)}</div>
<div class="decision-price">{pref}</div><div class="decision-setup"><b>{price_label}</b>{(' · '+quote_time) if quote_time else ''} · <b>{setup}</b> · {pos} · distance {dist}%</div>
<div class="decision-zone"><span>ENTRY ZONE</span> <b>{lo}–{hi}</b></div>
<div class="decision-metrics"><div class="decision-metric"><span>SL</span><b>{sl}</b></div><div class="decision-metric"><span>TP1</span><b>{tp1}</b></div><div class="decision-metric"><span>R/R</span><b>{rr}</b></div><div class="decision-metric"><span>RISK</span><b>{risk}%</b></div></div>
<div class="decision-metrics"><div class="decision-metric"><span>EOD SCORE</span><b>{eod_score}</b></div><div class="decision-metric"><span>MULTI</span><b>{score}</b></div><div class="decision-metric"><span>COVERAGE</span><b>{cov}%</b></div><div class="decision-metric"><span>ATR</span><b>{atr}x</b></div></div>
<div class="decision-gates"><b>Stock:</b> {stock_gate} · <b>Market:</b> {market_gate}<br><b>Live Action:</b> {live_status} · <b>Pressure:</b> {live_pressure} ({r.get("PressureConfidence","—")})<br><b>VWAP:</b> {live_vwap} · <b>Vol 5m:</b> {live_vr}x · <b>Room:</b> {res_room}% ({r.get("ResistanceRoomClass","—")})<br><b>Entry Quality:</b> {eq}/100 · <b>Entry Priority:</b> {entry_priority}<br><b>Intraday Data:</b> {intraday_q} · age {intraday_age}m · bars {r.get('IntradayBarCount',0)}<br><b>Data:</b> {data} · EOD {eod_date} · age {age}d<br><b>Why:</b> {why_text}<br><b>Live Why:</b> {r.get('LiveActionReason','—')}<br><b>Next Trigger:</b> {trigger}<br><b>Invalidation:</b> {invalidation}</div>
<div class="decision-actions"><a href="{tv_link(ticker)}" target="_blank">📈 TradingView</a></div>
<div class="decision-why">Decision: <b>USER</b> · Sanggul tidak memberikan instruksi BUY/SELL.</div></div>'''

def show_top3_cards(action, meta):
    st.markdown('<div class="top3-wrap"><div class="top3-head"><div><div class="top3-title">🏆 Top 3 Decision Cards</div><div class="top3-sub">Quick decision view untuk HP · Opportunity Rank dipisahkan dari Entry Priority dan Live Action.</div></div><span class="mode-pill">MOBILE FIRST</span></div>', unsafe_allow_html=True)
    if action is None or action.empty:
        st.markdown('<div class="small-note">Belum ada kandidat Top 3.</div></div>', unsafe_allow_html=True); return
    try:
        morning=morning_confirm(action.head(3),str(meta.get("period","2y")),meta.get("regime","NEUTRAL / SIDEWAYS"))
        morning_by={str(r.get("Ticker")):r for _,r in morning.iterrows()} if not morning.empty else {}
    except Exception: morning_by={}
    cards=[_decision_card_html(i,r,morning_by.get(str(r.get('Ticker')),{}),"top3") for i,(_,r) in enumerate(action.head(3).iterrows(),1)]
    st.markdown('<div class="decision-grid">'+''.join(cards)+'</div></div>',unsafe_allow_html=True)
    for i,(_,r) in enumerate(action.head(3).iterrows(),1):
        ticker=str(r.get('Ticker','—'))
        with st.expander(f"🔎 WHY {ticker} · lihat alasan dan data detail",expanded=False):
            st.markdown(f"**{ticker}** · Setup **{r.get('Setup','—')}** · Opportunity **{fmt(r.get('OpportunityScore',np.nan),0)}** · Multi-Factor **{fmt(r.get('MultiFactorScore',np.nan),1)}** · Coverage **{fmt(r.get('FactorCoveragePct',np.nan),0)}%**")
            st.markdown(f"Entry **{fmt(r.get('Entry',np.nan))}** · SL **{fmt(r.get('SL',np.nan))}** · TP1 **{fmt(r.get('TP1',np.nan))}** · R/R **{fmt(r.get('RR',np.nan),2)}** · RSI **{fmt(r.get('RSI',np.nan),1)}** · MA20 **{fmt(r.get('MA20',np.nan),2)}**")
            st.markdown(f"**Live Action:** {r.get('LiveActionStatus','EOD LOCKED')} · **Pressure:** {r.get('LivePressure','NOT APPLICABLE')} · **VWAP:** {fmt(r.get('IntradayVWAP',np.nan),0)} · **5m Vol Ratio:** {fmt(r.get('LiveVolumeRatio',np.nan),1)}x")
            st.caption("EOD ranking bukan instruksi transaksi. Morning status memperhitungkan posisi terhadap entry dan Market Gate.")

def dashboard_morning_brief(meta, analyzed, expected, regime, ihsg, ih20, ih50):
    global_snap=us_market_snapshot(); rows=global_snap.get('rows',[]); us={r['Name']:r for r in rows}
    def g(name):
        r=us.get(name,{}); ch=float(r.get('ChangePct',0) or 0) if r else np.nan; return (fmt(r.get('Close',np.nan),2), (('+' if ch>0 else '')+f'{ch:.2f}%') if r else '—')
    sp,spc=g('S&P 500'); nq,nqc=g('Nasdaq'); dow,dowc=g('Dow Jones'); vix,vixc=g('VIX')
    cov=(analyzed/expected*100) if expected else 0; reg=str(regime).upper(); reg_cls='green' if reg.startswith('RISK-ON') else ('red' if reg.startswith('RISK-OFF') else 'yellow'); lead=str(global_snap.get('lead','UNAVAILABLE'))
    st.markdown(f'''<div class="mobile-brief"><div class="global-head"><div><div class="global-title">🌅 Morning Brief · Mobile Decision View</div><div class="global-sub">Global context → IHSG → EOD baseline → Top 3 → Top 10. Detail dibuka saat diperlukan.</div></div><span class="mode-pill">GLOBAL {lead}</span></div>
<div class="mobile-brief-grid">
<div class="mobile-brief-card"><div class="mobile-brief-label">🇮🇩 IHSG</div><div class="mobile-brief-value">{fmt(ihsg,2)}</div><div class="mobile-brief-sub {reg_cls}">{reg} · MA20 {fmt(ih20,0)}</div></div>
<div class="mobile-brief-card"><div class="mobile-brief-label">🌎 S&P 500</div><div class="mobile-brief-value">{sp}</div><div class="mobile-brief-sub">{spc}</div></div>
<div class="mobile-brief-card"><div class="mobile-brief-label">NASDAQ</div><div class="mobile-brief-value">{nq}</div><div class="mobile-brief-sub">{nqc}</div></div>
<div class="mobile-brief-card"><div class="mobile-brief-label">DOW JONES</div><div class="mobile-brief-value">{dow}</div><div class="mobile-brief-sub">{dowc}</div></div>
<div class="mobile-brief-card"><div class="mobile-brief-label">VIX</div><div class="mobile-brief-value">{vix}</div><div class="mobile-brief-sub">{vixc} · volatility</div></div>
<div class="mobile-brief-card"><div class="mobile-brief-label">EOD BASELINE</div><div class="mobile-brief-value">{meta.get('latest_data_date',meta.get('data_date','—'))}</div><div class="mobile-brief-sub">validated baseline</div></div>
<div class="mobile-brief-card"><div class="mobile-brief-label">DATA COVERAGE</div><div class="mobile-brief-value">{analyzed}/{expected}</div><div class="mobile-brief-sub">{cov:.1f}%</div></div>
<div class="mobile-brief-card"><div class="mobile-brief-label">MA50 IHSG</div><div class="mobile-brief-value">{fmt(ih50,0)}</div><div class="mobile-brief-sub">market context</div></div>
</div></div>''',unsafe_allow_html=True)

def show_top10_cards(opp, meta=None):
    st.markdown('<div class="op10-wrap"><div class="top3-head"><div><div class="top3-title">🟩 Top 10 Opportunity Cards</div><div class="top3-sub">Quick scan untuk HP. Top 10 bukan otomatis BUY.</div></div><span class="mode-pill">10 CARDS</span></div>', unsafe_allow_html=True)
    if opp is None or opp.empty:
        st.info("Belum ada data Top 10."); st.markdown('</div>', unsafe_allow_html=True); return
    try:
        morning=morning_confirm(opp.head(10),str((meta or {}).get("period","2y")),(meta or {}).get("regime","NEUTRAL / SIDEWAYS")); morning_by={str(r.get('Ticker')):r for _,r in morning.iterrows()} if not morning.empty else {}
    except Exception: morning_by={}
    cards=[_decision_card_html(i,r,morning_by.get(str(r.get('Ticker')),{}),"top10") for i,(_,r) in enumerate(opp.head(10).iterrows(),1)]
    st.markdown('<div class="decision-grid">'+''.join(cards)+'</div></div>',unsafe_allow_html=True)

def show_morning_watchlist(conf):
    if conf is None or conf.empty:return
    options=conf.Ticker.astype(str).tolist(); selected=st.multiselect("⭐ My Morning Watchlist",options,default=options[:min(3,len(options))],key="morning_watchlist")
    if not selected:return
    sub=conf[conf.Ticker.astype(str).isin(selected)].copy()
    st.markdown('<div class="watch-wrap"><div class="watch-title">⭐ My Morning Watchlist</div><div class="watch-sub">Watchlist pribadi untuk mempercepat akses; bukan ranking baru.</div></div>',unsafe_allow_html=True)
    cards=[_decision_card_html(i,r,r.to_dict(),"top10") for i,(_,r) in enumerate(sub.iterrows(),1)]
    st.markdown('<div class="decision-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)

def dashboard_summary(active, meta, action, opp, focus, enrich, ihsg, ih20, ih50, regime):
    reg=str(regime).upper(); reg_cls='green' if reg.startswith('RISK-ON') else ('red' if reg.startswith('RISK-OFF') else 'yellow')
    full=active.get('full',pd.DataFrame()) if isinstance(active,dict) else pd.DataFrame(); analyzed=len(full); ready=int((full.get('Status',pd.Series(dtype=str)).astype(str).str.upper()=='READY').sum()) if not full.empty else 0; full_pass=int((full.get('RiskGate',pd.Series(dtype=str)).astype(str).str.upper()=='PASS').sum()) if not full.empty else 0
    st.markdown(f'''<div class="dashboard-grid"><div class="dashboard-panel"><div class="panel-kicker">IHSG</div><div class="big-number">{fmt(ihsg,2)}</div><div class="{reg_cls}" style="font-size:13px;font-weight:800">{reg}</div><div class="stat-row"><span>MA20</span><b>{fmt(ih20,2)}</b></div><div class="stat-row"><span>MA50</span><b>{fmt(ih50,2)}</b></div></div><div class="dashboard-panel"><div class="panel-kicker">Market Regime</div><div class="regime {reg_cls}">{reg}</div><div class="small-note">Stock Setup dan Market Environment ditampilkan terpisah agar alasan REVIEW lebih mudah dibaca.</div><div style="margin-top:12px"><span class="mode-pill">HYBRID ENGINE</span> <span class="mode-pill">600 IDX</span></div></div><div class="dashboard-panel"><div class="panel-kicker">Statistik Scan</div><div class="stat-list"><div class="stat-row"><span>Saham dianalisis</span><b>{analyzed}</b></div><div class="stat-row"><span>READY</span><b>{ready}</b></div><div class="stat-row"><span>Risk Gate PASS</span><b>{full_pass}</b></div><div class="stat-row"><span>Top 10</span><b>{len(opp)}</b></div><div class="stat-row"><span>Top 3</span><b>{min(3,len(action))}</b></div></div></div></div>''',unsafe_allow_html=True)
    st.markdown('<div class="pipeline"><div class="pipe">UNIVERSE<b>600</b></div><div class="pipe">QUALITY<b>150</b></div><div class="pipe">FOCUS<b>50</b></div><div class="pipe">OPPORTUNITY<b>10</b></div><div class="pipe">RISK GATE<b>2.3</b></div><div class="pipe">ACTIONABLE<b>3</b></div></div>',unsafe_allow_html=True)
    show_top3_cards(action,meta)

def show_top3(action,meta,opp=None):
    show_top3_cards(action, meta)

def show_morning_cards(conf):
    if conf is None or conf.empty: st.warning("Tidak ada kandidat Morning yang berhasil divalidasi."); return
    cards=[]
    for i,(_,r) in enumerate(conf.head(10).iterrows(),1):
        ticker=str(r.get('Ticker','—')); ms=str(r.get('MorningStatus','WAIT')); reason=str(r.get('MorningReason','—')); pre=fmt(r.get('PreOpenReference',np.nan)); lo=fmt(r.get('EntryLow',np.nan)); hi=fmt(r.get('EntryHigh',np.nan)); sl=fmt(r.get('SL',np.nan)); tp1=fmt(r.get('TP1',np.nan)); rr=fmt(r.get('RR',np.nan),2); dist=fmt(r.get('DistanceToEntryPct',np.nan),1); pos=str(r.get('EntryPosition','—')); gate=str(r.get('MarketGate','—')); data=str(r.get('DataStatus','—'))
        cards.append(f'''<div class="op10-card"><div class="op10-head"><div><span class="op10-rank">{i}</span><span class="op10-ticker">{ticker}</span></div>{morning_status_badge(ms)}</div><div class="op10-price">{pre}</div><div class="op10-sub"><b>{pos}</b> · {data}</div><div class="op10-metrics"><div class="op10-metric"><span>ENTRY ZONE</span><b>{lo}–{hi}</b></div><div class="op10-metric"><span>SL</span><b>{sl}</b></div><div class="op10-metric"><span>TP1</span><b>{tp1}</b></div><div class="op10-metric"><span>R/R</span><b>{rr}</b></div><div class="op10-metric"><span>DISTANCE</span><b>{dist}%</b></div><div class="op10-metric"><span>MARKET</span><b>{gate}</b></div></div><div class="op10-foot">{reason} · Decision: USER</div></div>''')
    st.markdown('<div class="op10-grid">'+''.join(cards)+'</div>',unsafe_allow_html=True)

def show_top10(opp,meta=None):
    show_top10_cards(opp,meta)

def show_top50(focus):
    st.markdown('<div class="section-title">🟨 Top 50 Focus — Focus List</div>',unsafe_allow_html=True)
    show_table(focus,["Ticker","Setup","SetupScore","QualityScore","MultiFactorScore","FactorCoveragePct","RiskGate","LiveActionStatus","LivePressure","CurrentPrice","CurrentChangePct","CurrentQuoteTime","IntradayVWAP","LiveVolumeRatio","Close","MA20","RSI","MACD","VolumeRatio","Entry","SL","TP1","TP2","RR","Status","AvoidReason","Timing"])

def show_top150(enrich):
    st.markdown('<div class="section-title">🟦 Top 150 Enrich — Quality Pool</div>',unsafe_allow_html=True)
    show_table(enrich,["Ticker","QualityScore","SetupScore","OpportunityScore","MultiFactorScore","FactorCoveragePct","RiskGate","LiveActionStatus","LivePressure","CurrentPrice","CurrentChangePct","CurrentQuoteTime","IntradayVWAP","LiveVolumeRatio","Close","RSI","MACD","MA20","MA50","MA200","Support","Resistance","Status","AvoidReason","Setup"])

def show_rules():
    with st.expander("📋 Execution Rule",expanded=False):
        st.markdown("- **READY** = lolos risk gate dan masuk tahap eksekusi.\n- **WAIT** = kandidat bagus tetapi belum di area entry.\n- **AVOID** = struktur trend/momentum tidak mendukung.\n- **Top 150 ≠ BUY · Top 50 ≠ BUY · Top 10 ≠ BUY.**\n- Breakout divalidasi menjelang penutupan; pullback/support divalidasi setelah pembukaan.")

# =========================================================
# NEW: DAILY / WEEKLY / INDIVIDUAL STOCK
# =========================================================
def daily_table(full):
    if full is None or full.empty:return pd.DataFrame()
    d=full.copy(); d["DailyScore"]=d["OpportunityScore"]+d["SetupScore"]
    d=d[(d["Status"]!="AVOID") & ((d["Setup"].isin(["BREAKOUT","PULLBACK","REJECTION SUPPORT"])) | (d["RSI"].between(48,68)))].sort_values(["DailyScore","RR"],ascending=False).head(30)
    d["TradingMode"]="HARIAN"; return d

@st.cache_data(ttl=900,show_spinner=False)
def weekly_analysis(ticker):
    d=load_data(ticker,"5y","1wk"); return analyze(d)

def weekly_candidates(focus):
    if focus is None or focus.empty:return pd.DataFrame()
    rows=[]
    for _,r in focus.head(30).iterrows():
        w=weekly_analysis(r.Ticker)
        if w:
            x={"Ticker":r.Ticker,"WeeklySetup":w["Setup"],"WeeklyStatus":w["Status"],"WeeklyScore":w["OpportunityScore"],"WeeklyRSI":w["RSI"],"WeeklyMA20":w["MA20"],"WeeklyMA50":w["MA50"],"WeeklyMA200":w["MA200"],"WeeklyEntry":w["Entry"],"WeeklySL":w["SL"],"WeeklyTP1":w["TP1"],"WeeklyTP2":w["TP2"],"WeeklyRR":w["RR"],"DailySetup":r.Setup,"DailyRR":r.RR,"Close":r.Close}
            rows.append(x)
    out=pd.DataFrame(rows)
    if out.empty:return out
    out["SwingScore"]=out["WeeklyScore"]+out["DailyRR"].clip(upper=4)*4
    return out.sort_values(["SwingScore","WeeklyRR"],ascending=False).head(20)

# =========================================================
# HEADER + SIDEBAR
# =========================================================
header("📈 Sanggul Stock Scanner",f"{APP_VERSION} · 600 IDX · IHSG Reliable Fallback · Global Morning Intelligence · EOD Persistent · Morning Confirmation · Opportunity vs Entry · Intraday Data Quality · TradingView")

with st.sidebar:
    st.markdown('<div class="control-card"><div class="control-title">SANGGUL STOCK SCANNER</div><div style="font-size:18px;font-weight:850;color:#fff;margin-top:3px">V11.5.6 · PRO 600 IDX EXPANDED UNIVERSE</div><div class="small-note" style="margin-top:4px">Decision-support terminal · 600 IDX</div></div>',unsafe_allow_html=True)
    st.markdown("### 🧭 MENU UTAMA")
    mode=st.radio("Navigasi",[
        "📊 Dashboard","⚡ Trading Harian","📅 Swing Trading Mingguan","🔎 Saham Individu","🏭 Sector Opportunity","🏆 Top 3 Actionable","🟩 Top 10 Opportunity","🟨 Top 50 Focus","🟦 Top 150 Enrich","🌅 Morning Confirmation","🌆 EOD Full Scan","📜 EOD Scan History","🧠 Multi-Factor Data Hub"],index=0)
    st.divider(); st.markdown("### ⚙️ PENGATURAN")
    st.markdown('<div class="control-card"><div class="control-title">SCAN CONTROL</div><div class="small-note">Widget di bawah dibuat kontras agar nilai mudah dibaca di dark mode.</div></div>',unsafe_allow_html=True)
    period=st.selectbox("Data historis EOD",["1mo","3mo","6mo","2y"],index=3, format_func=lambda x: {"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan","2y":"2 Tahun"}[x])
    n=st.slider("Jumlah saham saat Scan / EOD",50,600,600,50)
    min_rr=st.number_input("Minimum R/R",1.5,4.0,2.0,0.5)
    max_stop_pct=st.number_input("Max Stop Distance (%)",5.0,40.0,15.0,1.0,help="Risk Gate 2.1: kandidat dengan jarak Entry–SL di atas batas ini masuk RISK REVIEW. ATR Risk juga wajib tersedia untuk PASS.")
    st.divider(); st.caption("📌 EOD = screening utama · Pagi = konfirmasi · Harian = tactical · Mingguan = swing · External factors = optional enrichment")
    st.caption("Periode EOD: 1B / 3B / 6B / 2T · engine indikator minimum 2T")
    scan_now=st.button("🔄 Scan 600 Saham / Update EOD",type="primary",use_container_width=True)
    st.caption("Current Scan = refresh harga terkini + screening dinamis. EOD Full Scan = kunci harga penutupan resmi untuk baseline pagi.")

# Load current/EOD state before market metrics so IHSG can be date-synchronized to the scan.
snap=read_snapshot(latest_snapshot())
current_scan=st.session_state.get("current_scan") or load_current_scan()
if current_scan is not None:
    current_scan=_ensure_layers(current_scan)
    st.session_state["current_scan"]=current_scan

# Market strip — V11.5.2 blocks stale/mismatched IHSG instead of silently showing an older close.
ihsg,ih20,ih50,regime=market_metrics(period)
market_meta=st.session_state.get("market_data_meta",{})
ihsg_label=fmt(ihsg) if ihsg is not None else "DATA BLOCKED"
metric_strip([("IHSG",ihsg_label),("MA20",fmt(ih20) if ih20 is not None else "—"),("MA50",fmt(ih50) if ih50 is not None else "—"),("Market Gate",regime)])
if market_meta.get("status")=="VALID":
    st.caption(f"IHSG reference: **EOD {market_meta.get('date','—')}** · {market_meta.get('source','—')} · synchronized with stock scan baseline")
else:
    st.warning(f"⚠️ IHSG DATA BLOCKED — {market_meta.get('source','stale/unavailable')}. Sanggul tidak menggunakan angka IHSG lama atau intraday untuk Market Gate.")
global_us=global_morning_brief()

# Scan 600 is a current/dynamic view and does not overwrite the official EOD snapshot.

if scan_now:
    with st.spinner(f"Menjalankan current scan {n} saham + refresh harga terkini..."):
        path=run_full_scan(period,n,min_rr,max_stop_pct,save_eod=False)
    if path: st.success("Current Scan selesai. Harga terkini diperbarui dari quote intraday provider; EOD reference tetap tidak berubah. Official EOD Snapshot tidak diubah."); st.rerun()
    else: st.error("Tidak ada data yang berhasil dianalisis.")

# Current Scan takes precedence for analytical menus during this session;
# official EOD history remains read from the persisted snapshot.
active=snap
if current_scan is not None:
    active=current_scan
if active is not None:
    active=_ensure_layers(active)

# =========================================================
# SPECIAL MENUS
# =========================================================
if mode=="🌆 EOD Full Scan":
    header("🌆 EOD Full Scan","Bangun official EOD snapshot setelah market close. Snapshot lama tetap tersimpan.")
    now_jkt=jakarta_now()
    st.info("Gunakan setelah candle harian selesai. Official EOD snapshot menjadi baseline Dashboard dan Morning Confirmation; sebelum market close jangan jadikan scan ini sebagai snapshot resmi.")
    if now_jkt.hour < 16 or (now_jkt.hour == 16 and now_jkt.minute < 20):
        st.warning(f"🔒 EOD LOCK — waktu Jakarta {now_jkt.strftime('%H:%M')}. Official EOD Scan dibuka mulai 16:20 WIB agar candle hari berjalan tidak masuk sebagai EOD final. Untuk screening saat ini gunakan 🔄 Scan 600 Saham / Update EOD; hasilnya tidak mengganti EOD Snapshot.")
    else:
        if st.button("🚀 Jalankan EOD Full Scan",type="primary"):
            path=run_full_scan(period,n,min_rr,max_stop_pct)
            if path: st.success(f"Snapshot EOD tersimpan: {os.path.basename(path)}"); st.rerun()
            else: st.error("Tidak ada data yang berhasil dianalisis.")
    st.stop()

if mode=="🌅 Morning Confirmation":
    header("🌅 Morning Ready Center","Validasi EOD sebelum market buka. Jika snapshot resmi belum ada, sistem mencoba Auto EOD Recovery tanpa mengubah EOD History.")
    if st.button("🔄 Refresh Morning Data",type="primary"):
        load_data.clear(); st.session_state.pop("morning_recovery_attempted",None); st.rerun()
    m0= snap.get("meta",{}) if snap else {}
    baseline, baseline_source = morning_baseline(period, int(m0.get("universe",600) or 600), min_rr, max_stop_pct)
    if baseline is None and not st.session_state.get("morning_recovery_attempted",False):
        st.session_state["morning_recovery_attempted"]=True
        with st.spinner("🌅 Menyiapkan EOD baseline tervalidasi dari data yang sudah selesai..."):
            baseline, baseline_source = morning_baseline(period, 600, min_rr, max_stop_pct)
        if baseline is None:
            with st.spinner("🔄 Auto EOD Recovery: scan 600 saham completed-EOD..."):
                baseline=recover_eod_from_current_or_scan(period,600,min_rr,max_stop_pct)
                baseline_source="AUTO EOD RECOVERY" if baseline else "NO VALID EOD BASELINE"
    if baseline is None:
        st.error("🔒 MORNING DATA BLOCKED — tidak ditemukan EOD baseline yang tervalidasi. Tidak ada Top 3 pagi yang ditampilkan.")
        st.info("Jalankan 🌆 EOD Full Scan setelah market close, atau gunakan 🔄 Scan 600 Saham / Update EOD. Current Scan akan dipakai untuk recovery hanya jika data terakhir lengkap dan bukan candle hari berjalan.")
        st.stop()
    snap=baseline
    m=snap["meta"]; ready=morning_data_readiness(snap,int(m.get("universe",600) or 600))
    analyzed=int(ready.get("Analyzed",0) or 0)
    expected=int(ready.get("Expected",600) or 600)
    coverage_pct=(analyzed/expected*100.0) if expected else 0.0
    source_label="OFFICIAL EOD" if baseline_source=="OFFICIAL EOD" else "AUTO EOD RECOVERY"
    baseline_created=m.get("timestamp",m.get("recovered_at","—"))
    cols=st.columns(5)
    cols[0].metric("EOD BASELINE",ready.get("LatestDataDate","—"))
    cols[1].metric("Coverage",f"{analyzed}/{expected}",f"{coverage_pct:.1f}%")
    cols[2].metric("Data Age",f"{ready.get("LatestDataAgeDays",999)} day")
    cols[3].metric("Data Quality",ready.get("Level","REVIEW"))
    cols[4].metric("Market Gate",str(m.get("regime","—")))
    st.caption(f"Baseline: **{source_label}** · EOD data date **{ready.get("LatestDataDate","—")}** · Baseline created **{str(baseline_created)[:19]}** · Coverage **{analyzed}/{expected} ({coverage_pct:.1f}%)**")
    if ready.get("Ready"):
        st.success("🟢 MORNING DATA READY — data inti EOD lengkap dan kandidat siap Anda review. Entry tetap keputusan Anda.")
    else:
        st.warning("🟡 MORNING DATA REVIEW — jangan gunakan hasil sebagai dasar entry sebelum masalah data diperiksa.")
    st.markdown(f'<div class="card"><b>Kontrak data pagi</b><br>• <b>{source_label}</b> adalah baseline. Auto Recovery <b>tidak menimpa EOD History</b> dan bukan klaim Official EOD.<br>• <b>EOD Data Date = {ready.get("LatestDataDate","—")}</b>; <b>Baseline Created = {str(baseline_created)[:19]}</b>. Dua tanggal ini sengaja dipisahkan.<br>• Sebelum market buka, <b>Pre-Open Reference</b> = close EOD terakhir; sistem tidak mengarang harga live/premarket.<br>• <b>Coverage {analyzed}/{expected} ({coverage_pct:.1f}%)</b> dan Data Age {ready.get("LatestDataAgeDays",999)} hari harus terlihat sebelum keputusan.<br>• Status Morning adalah <b>decision-support</b>, bukan instruksi BUY. <b>Entry tetap keputusan Anda.</b></div>',unsafe_allow_html=True)
    conf=morning_confirm(snap["top10"],period,m.get("regime","NEUTRAL / SIDEWAYS"))
    if not conf.empty:
        st.markdown("#### 🌅 Morning Action Board")
        show_morning_watchlist(conf)
        show_morning_cards(conf)
        with st.expander("📋 Buka tabel detail Morning", expanded=False):
            show_table(conf,["Ticker","Setup","MorningStatus","MorningReason","PreOpenReference","Entry","EntryLow","EntryHigh","DistanceToEntryPct","EntryPosition","SL","TP1","TP2","RR","DataStatus","LastDataDate","DataAgeDays","MarketGate","Decision"],"Tabel Morning Detail")
    else:
        st.warning("Tidak ada kandidat Top 10 yang berhasil divalidasi.")
    st.caption("🟢 IN ENTRY ZONE = reference berada di area entry · 🔵 ABOVE ENTRY = belum perlu mengejar harga · 🟡 WAIT = market/setup belum mendukung · 🔴 CANCEL = struktur/risk invalid · USER DECISION = keputusan entry tetap pada Anda.")
    st.stop()

if mode=="📜 EOD Scan History":
    header("📜 EOD Scan History","Riwayat snapshot screening untuk menjaga konsistensi keputusan dari hari ke hari.")
    dirs=snapshot_dirs(); rows=[]
    for p in dirs[:30]:
        s=read_snapshot(p)
        if not s:continue
        rows.append({"Snapshot":os.path.basename(p),"Timestamp":s["meta"].get("timestamp"),"Regime":s["meta"].get("regime"),"Universe":s["meta"].get("universe"),"Analyzed":s["meta"].get("analyzed"),"Top 3":", ".join(s["top3"].Ticker.astype(str).tolist()) if not s["top3"].empty else "—"})
    show_table(pd.DataFrame(rows),["Snapshot","Timestamp","Regime","Universe","Analyzed","Top 3"])
    st.stop()

if mode=="🧠 Multi-Factor Data Hub":
    header("🧠 Multi-Factor Data Hub","Hybrid engine: Technical + Sector tetap berjalan; Fundamental/Foreign/Broker memperkaya jika tersedia.")
    universe=load_universe()
    st.markdown("#### 📊 Data Quality")
    q=data_quality_table(universe)
    st.dataframe(q,use_container_width=True,hide_index=True)
    st.caption("Coverage = persentase ticker pada universe 600 yang memiliki data faktor. Data external tidak pernah dibuat/fiktif.")
    st.markdown("**Mode:** 🟢 FULL MULTI-FACTOR · 🟡 PARTIAL ENRICHED · 🔵 CORE TECHNICAL + SECTOR")
    st.markdown("#### 📥 Import data EOD / external factors")
    st.caption("Upload CSV atau Excel. Header yang umum seperti Ticker/Kode, DER, PER, PBV, Foreign Net 1D/5D/20D akan dinormalisasi otomatis.")
    c1,c2,c3=st.columns(3)
    with c1:
        st.download_button("⬇️ Template Fundamentals",template_bytes('fundamentals.csv'),'sanggul_fundamentals_template.csv','text/csv',use_container_width=True)
        uf=st.file_uploader("Fundamentals CSV/XLSX",type=['csv','xlsx','xls'],key='fund_upload')
        if uf is not None and st.button("Simpan Fundamentals",key='save_fund'):
            ok,msg=save_uploaded_factor(uf,'fundamentals.csv'); st.success(msg) if ok else st.error(msg)
    with c2:
        st.download_button("⬇️ Template Foreign Flow",template_bytes('foreign_flow.csv'),'sanggul_foreign_flow_template.csv','text/csv',use_container_width=True)
        uff=st.file_uploader("Foreign Flow CSV/XLSX",type=['csv','xlsx','xls'],key='foreign_upload')
        if uff is not None and st.button("Simpan Foreign Flow",key='save_foreign'):
            ok,msg=save_uploaded_factor(uff,'foreign_flow.csv'); st.success(msg) if ok else st.error(msg)
    with c3:
        st.download_button("⬇️ Template Broker Flow",template_bytes('broker_flow.csv'),'sanggul_broker_flow_template.csv','text/csv',use_container_width=True)
        ubf=st.file_uploader("Broker Flow CSV/XLSX",type=['csv','xlsx','xls'],key='broker_upload')
        if ubf is not None and st.button("Simpan Broker Flow",key='save_broker'):
            ok,msg=save_uploaded_factor(ubf,'broker_flow.csv'); st.success(msg) if ok else st.error(msg)
    st.markdown("#### 🔎 Data yang tersimpan")
    for label,file in [('Fundamentals','fundamentals.csv'),('Foreign Flow','foreign_flow.csv'),('Broker Flow','broker_flow.csv')]:
        info=factor_file_info(file,universe)
        st.write(f"**{label}:** {info['Status']} · {info['Rows']} rows · coverage {info['CoveragePct']:.1f}% · update {info['Freshness']}")
        if info['MissingRequired']: st.caption('Kolom kurang: '+', '.join(info['MissingRequired']))
    st.markdown("#### 🌐 Sumber resmi")
    st.caption("BEI menyediakan statistik perdagangan dan data pasar EOD; untuk data berlisensi gunakan akses resmi yang Anda miliki. Data foreign investor di statistik BEI dikategorikan berdasarkan transaction domicile, bukan identitas investor aktual.")
    st.link_button("🌐 IDX Data Pasar", "https://www.idx.co.id/id/data-pasar/", use_container_width=False)
    st.link_button("🌐 IDX Statistik", "https://www.idx.co.id/id/data-pasar/laporan-statistik/statistik", use_container_width=False)
    st.info("Setelah data tersimpan, jalankan **🔄 Scan 600 Saham / Update EOD** agar Multi-Factor Score dan Risk Gate dihitung ulang. Tanpa external data pun scanner tetap dapat menghasilkan kandidat melalui CORE TECHNICAL + SECTOR. Scan 600 tidak menghapus snapshot EOD lama sampai Anda menjalankan EOD Full Scan.")
    st.stop()

if not active:
    st.warning("Belum ada data scan. Gunakan **🔄 Scan 600 Saham / Update EOD** atau **🌆 EOD Full Scan**."); st.stop()

m=active["meta"]; action,opp,focus,enrich=active["top3"],active["top10"],active["top50"],active["top150"]
if mode in ["📊 Dashboard","🏆 Top 3 Actionable","🟩 Top 10 Opportunity","🟨 Top 50 Focus","🟦 Top 150 Enrich"]:
    snap_engine=str(m.get("engine_version",m.get("engine_version_current","LEGACY")))
    if snap_engine != ENGINE_VERSION:
        st.warning(f"⚠️ Snapshot lama/legacy terdeteksi ({snap_engine}). Risk Gate dan layer telah dihitung ulang di memori dengan {ENGINE_VERSION}. Jalankan 🔄 Scan 600 untuk membuat hasil baru yang tersimpan.")

# =========================================================
# DASHBOARD / OLD MENUS
# =========================================================
if mode=="📊 Dashboard":
    header("Dashboard","Ringkasan market, pipeline 600 saham, EOD candidates, dan Morning Ready status — gaya terminal trading modern.")
    # Dashboard Top 3 is anchored to the official EOD snapshot.
    # Current Scan remains available elsewhere as an ad-hoc/dynamic view and must never
    # replace the historical EOD baseline on the morning decision card.
    baseline, baseline_source = morning_baseline(period, 600, min_rr, max_stop_pct)
    eod_action=baseline.get("top3",pd.DataFrame()) if baseline else pd.DataFrame()
    eod_meta=baseline.get("meta",{}) if baseline else {}
    mr=morning_data_readiness(baseline,int(eod_meta.get("universe",600) or 600)) if baseline else {"Ready":False,"Level":"NO SNAPSHOT","Reason":"Belum ada EOD baseline yang tervalidasi"}
    # Critical safety rule: invalid/no official EOD snapshot must NEVER be rendered as Morning Top 3.
    display_action=eod_action if mr.get("Ready") else pd.DataFrame()
    analyzed_now=int(mr.get("Analyzed",0) or 0); expected_now=int(mr.get("Expected",600) or 600)
    brief_meta=dict(eod_meta or {}); brief_meta["latest_data_date"]=mr.get("LatestDataDate","—")
    dashboard_morning_brief(brief_meta, analyzed_now, expected_now, regime, ihsg, ih20, ih50)
    dashboard_summary(active,m,display_action,opp,focus,enrich,ihsg,ih20,ih50,regime)
    if baseline:
        st.markdown(f'<div class="card"><b>🔒 EOD Baseline:</b> {baseline_source} · {eod_meta.get("timestamp",eod_meta.get("recovered_at","—"))} · data source {eod_meta.get("data_source","—")} · <b>Top 3 cards are locked to this baseline.</b><br><span class="small-note">🔄 Scan 600 / Update EOD is a separate current view and cannot overwrite the EOD baseline used for Morning Confirmation.</span></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="card"><b>🌅 Morning Ready Status:</b> <span class="mode-pill">{mr.get("Level","REVIEW")}</span> · EOD {mr.get("LatestDataDate","—")} · analyzed {mr.get("Analyzed",0)}/{mr.get("Expected",600)} · source <b>{baseline_source}</b> · <b>Entry decision remains with user.</b><br><span class="small-note">{mr.get("Reason","—")}. Sebelum open, baseline harus berasal dari Official EOD atau Auto EOD Recovery yang tervalidasi.</span></div>',unsafe_allow_html=True)
    if not mr.get("Ready"):
        st.error(f'🔒 **MORNING BLOCKED — {mr.get("Reason","EOD belum valid")}**. Top 3 EOD tidak ditampilkan sebagai kandidat pagi agar tidak terjadi false signal. Gunakan **🔄 Scan 600** hanya sebagai current view, bukan baseline EOD.')
        st.stop()
    st.markdown("#### 🟩 Top 10 Opportunity")
    show_top10_cards(opp,m)
    st.markdown("#### 📌 Decision Framework")
    st.caption("Stock Setup = kualitas saham secara teknikal/risk. Market Environment = kondisi IHSG. Risk Gate menggabungkan keduanya. REVIEW bukan PASS dan bukan instruksi transaksi otomatis.")
    st.download_button("📥 Export Full Scan CSV",active["full"].to_csv(index=False).encode("utf-8"),"sanggul_v11_1_5_fix9_full_scan.csv","text/csv")

elif mode=="⚡ Trading Harian":
    header("⚡ Trading Harian","Tactical setup untuk horizon 1–5 hari · menggunakan hasil EOD sebagai starting universe.")
    d=daily_table(active["full"])
    if d.empty: st.info("Belum ada kandidat trading harian yang memenuhi filter.")
    else:
        metric_strip([("Kandidat",str(len(d))), ("Ready",str((d.Status=="READY").sum())), ("Breakout",str((d.Setup=="BREAKOUT").sum())), ("Pullback",str((d.Setup=="PULLBACK").sum()))])
        show_table(d,["Ticker","TradingMode","Setup","Timing","Status","CurrentPrice","CurrentChangePct","CurrentQuoteTime","Close","MA20","MA50","MA200","RSI","MACD","VolumeRatio","Support","Resistance","Entry","SL","TP1","TP2","RR","OpportunityScore"])
        st.markdown("#### 🔗 TradingView — Daily / Tactical")
        ticker=st.selectbox("Pilih saham",d.Ticker.tolist(),key="daily_ticker")
        row=d[d.Ticker==ticker].iloc[0]
        st.markdown(f'<div class="card"><b>{ticker}</b> · {row.Setup} · {status_badge(row.Status)} · MA20 <b>{fmt(row.MA20)}</b> · Entry <b>{fmt(row.Entry)}</b> · SL <b>{fmt(row.SL)}</b> · TP1 <b>{fmt(row.TP1)}</b> · TP2 <b>{fmt(row.TP2)}</b> · R/R <b>{fmt(row.RR,2)}</b></div>',unsafe_allow_html=True)
        st.link_button("📈 Buka Chart TradingView Penuh — Daily ↗", tv_link(ticker,"1D"), use_container_width=False)

elif mode=="📅 Swing Trading Mingguan":
    header("📅 Swing Trading Mingguan","Horizon beberapa hari hingga beberapa minggu · daily setup + weekly trend confirmation.")
    st.info("Untuk menjaga kecepatan, validasi weekly dilakukan pada kandidat Top 50 EOD, bukan mengunduh ulang 600 saham.")
    w=weekly_candidates(focus)
    if w.empty: st.warning("Belum ada kandidat weekly. Pastikan EOD snapshot tersedia dan data weekly dapat diambil.")
    else:
        metric_strip([("Weekly candidates",str(len(w))), ("Weekly READY",str((w.WeeklyStatus=="READY").sum())), ("Weekly breakout",str((w.WeeklySetup=="BREAKOUT").sum())), ("Avg R/R",fmt(w.WeeklyRR.mean(),2))])
        show_table(w,["Ticker","WeeklySetup","WeeklyStatus","WeeklyScore","WeeklyRSI","WeeklyMA20","WeeklyMA50","WeeklyMA200","WeeklyEntry","WeeklySL","WeeklyTP1","WeeklyTP2","WeeklyRR","DailySetup","DailyRR","Close"])
        st.caption("Grafik tidak ditampilkan di dalam aplikasi. Gunakan chart TradingView penuh agar ruang dashboard tetap ringkas.")
        ticker=st.selectbox("Pilih saham weekly",w.Ticker.tolist(),key="weekly_ticker")
        row=w[w.Ticker==ticker].iloc[0]
        st.markdown(f'<div class="card"><b>{ticker}</b> · Weekly {row.WeeklySetup} · {status_badge(row.WeeklyStatus)} · Entry <b>{fmt(row.WeeklyEntry)}</b> · SL <b>{fmt(row.WeeklySL)}</b> · TP1 <b>{fmt(row.WeeklyTP1)}</b> · TP2 <b>{fmt(row.WeeklyTP2)}</b> · R/R <b>{fmt(row.WeeklyRR,2)}</b></div>',unsafe_allow_html=True)
        st.link_button("📈 Buka Chart TradingView Penuh — Weekly ↗", tv_link(ticker,"1W"), use_container_width=False)

elif mode=="🔎 Saham Individu":
    header("🔎 Saham Individu","Terminal analisis per saham dengan quote teknikal + chart TradingView.")
    universe=load_universe()
    ticker=st.selectbox("Pilih saham IDX",universe,index=universe.index("BBCA") if "BBCA" in universe else 0)
    d=load_data(ticker,"2y","1d"); a=analyze(d)
    if a is None: st.warning("Data teknikal belum cukup untuk dianalisis."); st.stop()
    live=load_live_prices([ticker]).get(str(ticker).upper(),{})
    for k,src in [("CurrentPrice","price"),("CurrentQuoteTime","time"),("SessionOpen","session_open"),("SessionHigh","session_high"),("SessionLow","session_low"),("IntradayVWAP","intraday_vwap"),("LiveVolumeRatio","live_volume_ratio"),("LastBarChangePct","last_bar_change_pct"),("SessionChangePct","session_change_pct")]: a[k]=live.get(src,np.nan if k!="CurrentQuoteTime" else "—")
    a["LiveBullishBar"]=live.get("bullish_bar",False)
    a["LiveBelowVWAP"]=bool(pd.notna(a.get("IntradayVWAP")) and pd.notna(a.get("CurrentPrice")) and a["CurrentPrice"]<a["IntradayVWAP"])
    a["LiveBelowSessionOpen"]=bool(pd.notna(a.get("SessionOpen")) and pd.notna(a.get("CurrentPrice")) and a["CurrentPrice"]<a["SessionOpen"])
    live_df=apply_live_action_gate(pd.DataFrame([a]),"NEUTRAL / SIDEWAYS")
    if not live_df.empty: a=live_df.iloc[0].to_dict()
    display_last= a.get("CurrentPrice") if pd.notna(a.get("CurrentPrice",np.nan)) else a["Close"]
    display_status=a.get("LiveActionStatus",a["Status"])
    metric_strip([("Ticker",ticker),("Last",fmt(display_last)),("RSI",fmt(a["RSI"],1)),("R/R",fmt(a["RR"],2)),("Setup",a["Setup"]),("Status",display_status)])
    left,right=st.columns([1.25,1])
    with left:
        st.markdown("#### 🔗 TradingView Penuh")
        st.caption("Chart embedded dihilangkan agar dashboard tetap ringkas. Tombol di bawah langsung membuka TradingView Supercharts. Gunakan layout candle dan indikator MA20, Bollinger Bands, Volume, MACD, serta RSI seperti template analisis Sanggul.")
        c1,c2=st.columns(2)
        with c1: st.link_button("📈 Daily — Supercharts ↗", tv_link(ticker,"1D"), use_container_width=True)
        with c2: st.link_button("📅 Weekly — Supercharts ↗", tv_link(ticker,"1W"), use_container_width=True)
        st.markdown('<div class="card"><b>Periode data EOD yang dipilih:</b> '+{"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan","2y":"2 Tahun"}.get(period,period)+'<br><span class="small-note">Mesin indikator tetap mengambil minimal 2 tahun secara internal agar MA200, RSI dan MACD tetap valid; periode di atas menentukan jendela historis EOD yang dipakai sebagai acuan review.</span></div>',unsafe_allow_html=True)
    with right:
        st.markdown("#### Ringkasan Teknis")
        
        st.markdown(f'<div class="card">Trend MA20/50/200: <b>{"Bullish" if a["MA20"]>a["MA50"] else "Mixed"}</b><br>MA20: <b>{fmt(a["MA20"])}</b><br>MA50: <b>{fmt(a["MA50"])}</b><br>MA200: <b>{fmt(a["MA200"])}</b><br>Price vs MA20: <b>{fmt((a["Close"]-a["MA20"])/a["MA20"]*100,1)}%</b><br>RSI: <b>{fmt(a["RSI"],1)}</b><br>MACD: <b>{fmt(a["MACD"],2)}</b><br>EOD Volume ratio: <b>{fmt(a["VolumeRatio"],2)}x</b><br>Current: <b>{fmt(a.get("CurrentPrice",np.nan))}</b> · VWAP: <b>{fmt(a.get("IntradayVWAP",np.nan))}</b><br>Live 5m volume ratio: <b>{fmt(a.get("LiveVolumeRatio",np.nan),1)}x</b> · Pressure: <b>{a.get("LivePressure","—")}</b><br>Support: <b>{fmt(a["Support"])}</b><br>Resistance: <b>{fmt(a["Resistance"])}</b> · Room: <b>{fmt(a.get("DistanceToResistancePct",np.nan),1)}%</b><br>Candle: <b>{a["Candle"]}</b></div>',unsafe_allow_html=True)
        st.markdown("#### Trade Plan")
        st.markdown(f'<div class="card">Setup <b>{a["Setup"]}</b><br>Entry <b>{fmt(a["Entry"])}</b><br>Stop Loss <b>{fmt(a["SL"])}</b><br>TP1 <b>{fmt(a["TP1"])}</b><br>TP2 <b>{fmt(a["TP2"])}</b><br>R/R <b>{fmt(a["RR"],2)}</b><br>Entry Quality <b>{fmt(a.get("EntryQualityScore",np.nan),0)}/100</b><br>Status {status_badge(str(a.get("LiveActionStatus",a["Status"])))}<br><b>Next Trigger:</b> {a.get("NextTrigger","—")}<br><b>Invalidation:</b> {a.get("Invalidation","—")}</div>',unsafe_allow_html=True)
        st.link_button("📊 Buka TradingView Supercharts — Daily ↗", tv_link(ticker,"1D"), use_container_width=True)

elif mode=="🏭 Sector Opportunity":
    header("🏭 Sector Opportunity","Klik nama sektor untuk melihat daftar saham di dalam sektor tersebut. Ini adalah alat pemetaan peluang, bukan sinyal BUY otomatis.")
    full=active["full"].copy()
    sec=sector_opportunity(full)
    if sec.empty:
        st.info("Belum ada data sektor pada snapshot ini.")
    else:
        metric_strip([("Sektor",str(len(sec))), ("READY",str(int(sec.Ready.sum()))), ("Saham",str(int(sec.Stocks.sum()))), ("Sektor teratas",str(sec.iloc[0].Sector))])

        # Sector selector: each sector is a real clickable button.
        st.markdown("#### 🏭 Pilih Sektor")
        sectors=sec["Sector"].astype(str).tolist()
        if "selected_sector" not in st.session_state or st.session_state.selected_sector not in sectors:
            st.session_state.selected_sector=sectors[0] if sectors else None
        for start in range(0,len(sectors),3):
            cols=st.columns(3)
            for j,sector_name in enumerate(sectors[start:start+3]):
                with cols[j]:
                    prefix="✓ " if st.session_state.selected_sector==sector_name else ""
                    if st.button(prefix+sector_name,key="sector_btn_"+str(start+j),use_container_width=True):
                        st.session_state.selected_sector=sector_name
                        st.rerun()

        selected=st.session_state.get("selected_sector")
        if selected:
            rowsec=sec[sec.Sector==selected].iloc[0]
            stocks=full[full["Ticker"].map(sector_of)==selected].copy()
            st.markdown(f"#### 📋 Saham dalam sektor: **{selected}**")
            metric_strip([
                ("Saham",str(len(stocks))),
                ("READY",str(int((stocks.Status.astype(str).str.upper()=="READY").sum()))),
                ("Avg Opportunity",fmt(rowsec.AvgOpportunity,2)),
                ("Avg R/R",fmt(rowsec.AvgRR,2)),
            ])
            if stocks.empty:
                st.info("Belum ada saham yang terpetakan ke sektor ini.")
            else:
                cols=[c for c in ["Ticker","Status","Setup","Timing","Close","RSI","MACD","VolumeRatio","Support","Resistance","Entry","SL","TP1","TP2","RR","OpportunityScore","QualityScore"] if c in stocks.columns]
                show_table(stocks.sort_values(["Status","OpportunityScore"],ascending=[True,False]),cols,"📋 Buka Daftar Saham Sektor")
                # Quick individual-stock navigation from the selected sector.
                tickers=stocks["Ticker"].astype(str).tolist()
                if tickers:
                    chosen=st.selectbox("Pilih saham untuk analisis individual",tickers,key="sector_stock_"+selected)
                    st.caption("Setelah memilih saham, buka menu **🔎 Saham Individu** untuk melihat ringkasan teknis dan tautan TradingView penuh.")

        show_table(sec,["Sector","Stocks","Ready","ReadyPct","AvgOpportunity","AvgSetup","AvgQuality","AvgRR","AvgRSI","SectorOpportunityScore"],"📋 Buka Tabel Ringkasan Sector Opportunity")
        st.markdown("#### Cara membaca")
        st.caption("Sector Opportunity Score adalah agregasi kualitas/setup/opportunity/RR dari saham yang masuk snapshot. Klik sektor di atas untuk membuka daftar sahamnya; gunakan menu Saham Individu untuk Entry/SL/TP dan konfirmasi market gate.")

elif mode=="🏆 Top 3 Actionable":
    eod_action=snap.get("top3",pd.DataFrame()) if snap else pd.DataFrame()
    eod_meta=snap.get("meta",{}) if snap else {}
    header("🏆 Top 3 Actionable","EOD candidates yang dikunci dari official snapshot + validasi Morning Action. Current Scan tidak mengganti baseline EOD.")
    show_top3_cards(eod_action,eod_meta)
    show_rules()
elif mode=="🟩 Top 10 Opportunity":
    header("🟩 Top 10 Opportunity","Opportunity pool — mobile-first cards; bukan otomatis BUY."); show_top10(opp,m); show_rules()
elif mode=="🟨 Top 50 Focus":
    header("🟨 Top 50 Focus","Focused setup list dengan R/R minimum."); show_top50(focus); show_rules()
elif mode=="🟦 Top 150 Enrich":
    header("🟦 Top 150 Enrich","Quality pool untuk pemantauan lebih luas."); show_top150(enrich); show_rules()
