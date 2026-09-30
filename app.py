import os, json, glob
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf

APP_VERSION = "V11.1.3.8 PRO FIX4"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNAP_DIR = os.path.join(BASE_DIR, "snapshots")
os.makedirs(SNAP_DIR, exist_ok=True)

st.set_page_config(page_title=f"Sanggul Stock Scanner {APP_VERSION}", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

# =========================================================
# PROFESSIONAL UI — inspired by modern brokerage terminals
# =========================================================
st.markdown("""
<style>
:root { --navy:#08264d; --blue:#0b63ce; --blue2:#eaf3ff; --line:#d9e2ef; --ink:#172235; --muted:#66758a; --green:#11844b; --red:#c53636; --orange:#e58a00; }
.block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 1500px; }
section[data-testid="stSidebar"] { border-right:1px solid #dfe7f2; }
section[data-testid="stSidebar"] .block-container { padding-top: 1rem; }
.hero { background:linear-gradient(100deg,#08264d 0%,#0b63ce 72%,#176fd2 100%); color:white; padding:18px 22px; border-radius:14px; margin-bottom:14px; box-shadow:0 8px 24px rgba(8,38,77,.14); }
.hero h1 { margin:0; font-size:28px; letter-spacing:-.4px; }
.hero p { margin:4px 0 0; opacity:.88; font-size:13px; }
.section-title { font-size:18px; font-weight:700; color:var(--ink); margin:10px 0 8px; }
.card { background:white; border:1px solid var(--line); border-radius:12px; padding:13px 15px; box-shadow:0 2px 10px rgba(20,40,80,.045); }
.metric-card { background:white; border:1px solid var(--line); border-radius:11px; padding:12px 14px; min-height:80px; }
.metric-label { color:var(--muted); font-size:11px; text-transform:uppercase; letter-spacing:.4px; }
.metric-value { color:var(--ink); font-size:21px; font-weight:750; margin-top:4px; }
.badge { display:inline-block; padding:4px 9px; border-radius:999px; font-size:11px; font-weight:700; }
.badge-blue { background:#eaf3ff; color:#0b63ce; }
.badge-green { background:#e8f7ef; color:#11844b; }
.badge-yellow { background:#fff5dc; color:#9a6500; }
.badge-red { background:#fdeaea; color:#b42d2d; }
.small-note { color:var(--muted); font-size:12px; }
.tv-wrap { border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff; }
div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:10px; }
button[kind="primary"] { border-radius:8px; }
hr { border-color:#e6ebf2; }
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
    x,p=d.iloc[-1],d.iloc[-2]; close=float(x.Close); ma20,ma50,ma200=map(float,(x.MA20,x.MA50,x.MA200))
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
    status="AVOID" if close<ma50 and x.MACD<x.MACDsig else ("READY" if ready else "WAIT")
    timing="SORE / CLOSE CONFIRM" if breakout else ("PAGI CONFIRM" if near_support or pullback else "WATCH")
    return {"Close":close,"MA20":ma20,"MA50":ma50,"MA200":ma200,"RSI":float(x.RSI),"MACD":float(x.MACD),"VolumeRatio":vr,"Support":support,"Resistance":resistance,"Entry":entry,"SL":sl,"TP1":tp1,"TP2":tp2,"RR":rr,"RiskPct":risk/entry*100,"QualityScore":quality,"SetupScore":setup,"OpportunityScore":opportunity,"Status":status,"Setup":setup_type,"Timing":timing,"Candle":candle}

# =========================================================
# DATA / PERSISTENCE
# =========================================================
@st.cache_data(ttl=900,show_spinner=False)
def load_universe():
    return pd.read_csv(os.path.join(BASE_DIR,"universe.csv"))["Ticker"].astype(str).str.upper().tolist()

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
        return d.dropna(subset=["Close"])
    except Exception:
        return pd.DataFrame()

def snapshot_dirs(): return sorted([p for p in glob.glob(os.path.join(SNAP_DIR,"*")) if os.path.isdir(p)],reverse=True)

def save_snapshot(result,enrich,focus,opp,action,meta):
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S"); path=os.path.join(SNAP_DIR,stamp); os.makedirs(path,exist_ok=True)
    result.to_csv(os.path.join(path,"full_scan.csv"),index=False); enrich.to_csv(os.path.join(path,"top150.csv"),index=False); focus.to_csv(os.path.join(path,"top50.csv"),index=False); opp.to_csv(os.path.join(path,"top10.csv"),index=False); action.to_csv(os.path.join(path,"top3.csv"),index=False)
    with open(os.path.join(path,"meta.json"),"w",encoding="utf-8") as f: json.dump(meta,f,ensure_ascii=False,indent=2)
    with open(os.path.join(SNAP_DIR,"latest.txt"),"w",encoding="utf-8") as f: f.write(stamp)
    return path

def latest_snapshot():
    marker=os.path.join(SNAP_DIR,"latest.txt")
    if os.path.exists(marker):
        stamp=open(marker,encoding="utf-8").read().strip(); p=os.path.join(SNAP_DIR,stamp)
        if os.path.isdir(p): return p
    ds=snapshot_dirs(); return ds[0] if ds else None

def read_snapshot(path):
    if not path:return None
    try:
        meta=json.load(open(os.path.join(path,"meta.json"),encoding="utf-8"))
        data={k:pd.read_csv(os.path.join(path,f)) for k,f in [("full","full_scan.csv"),("top150","top150.csv"),("top50","top50.csv"),("top10","top10.csv"),("top3","top3.csv")]}
        return {"meta":meta,**data}
    except Exception:return None

def build_layers(result,min_rr):
    enrich=result.sort_values(["QualityScore","SetupScore","RR"],ascending=[False,False,False]).head(150).copy(); enrich["Layer"]="TOP 150 ENRICH"
    focus=result[result.RR>=min_rr].sort_values(["SetupScore","QualityScore","OpportunityScore"],ascending=[False,False,False]).head(50).copy(); focus["Layer"]="TOP 50 FOCUS"
    opp=result[result.RR>=min_rr].sort_values(["OpportunityScore","SetupScore","QualityScore"],ascending=[False,False,False]).head(10).copy(); opp["Layer"]="TOP 10 OPPORTUNITY"
    action=opp[opp.Status=="READY"].sort_values(["OpportunityScore","RR","SetupScore"],ascending=[False,False,False]).head(3).copy(); action["Layer"]="TOP 3 ACTIONABLE"
    return enrich,focus,opp,action

def run_full_scan(period,n,min_rr):
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
    enrich,focus,opp,action=build_layers(result,min_rr); ih=load_data("^JKSE",engine_period,"1d")
    if len(ih)>=220:
        ic=ih.Close; ihsg=float(ic.iloc[-1]); ih20=float(ic.rolling(20).mean().iloc[-1]); ih50=float(ic.rolling(50).mean().iloc[-1]); regime="RISK-ON" if ihsg>ih20>ih50 else ("NEUTRAL / SIDEWAYS" if ihsg>=ih50 else "RISK-OFF")
    else: ihsg=ih20=ih50=np.nan; regime="DATA INSUFFICIENT"
    meta={"timestamp":datetime.now().isoformat(timespec="seconds"),"period":period,"engine_period":engine_period,"universe":n,"analyzed":len(result),"min_rr":min_rr,"ihsg":ihsg,"ihsg_ma20":ih20,"ihsg_ma50":ih50,"regime":regime}
    return save_snapshot(result,enrich,focus,opp,action,meta)

def market_metrics(period):
    """Return clean market metrics; fall back to the latest EOD snapshot when live Yahoo data is unavailable."""
    ih=load_data("^JKSE","2y","1d")
    if len(ih)>=50:
        c=pd.to_numeric(ih["Close"],errors="coerce").dropna()
        if len(c)>=50:
            a=float(c.iloc[-1]); b=float(c.rolling(20).mean().iloc[-1]); d=float(c.rolling(50).mean().iloc[-1])
            regime="🟢 RISK-ON" if a>b>d else ("🟡 NEUTRAL / SIDEWAYS" if a>=d else "🔴 RISK-OFF")
            return a,b,d,regime
    try:
        sp=latest_snapshot()
        if sp:
            meta=json.load(open(os.path.join(sp,"meta.json"),encoding="utf-8"))
            a=float(meta.get("ihsg")); b=float(meta.get("ihsg_ma20")); d=float(meta.get("ihsg_ma50"))
            if all(np.isfinite([a,b,d])):
                rg=str(meta.get("regime","DATA INSUFFICIENT")).upper()
                return a,b,d,("🟢 RISK-ON" if "RISK-ON" in rg else ("🔴 RISK-OFF" if "RISK-OFF" in rg else "🟡 NEUTRAL / SIDEWAYS"))
    except Exception:
        pass
    return None,None,None,"🟡 DATA INSUFFICIENT"

def morning_confirm(top10,period):
    rows=[]
    for _,r in top10.iterrows():
        t=r.Ticker; d=load_data(t,"2y","1d")
        if d.empty:continue
        close=float(d.Close.iloc[-1]); openp=float(d.Open.iloc[-1]); eod_entry=float(r.Entry); sl=float(r.SL); gap=(openp-close)/max(close,1)*100
        status="CANCEL" if close<sl else ("WAIT — TOO HIGH" if close>eod_entry*1.025 else ("CONFIRM" if close>=eod_entry*.985 else "WAIT — BELOW ENTRY"))
        x=r.to_dict(); x.update({"Current":close,"Open":openp,"GapVsCurrentPct":gap,"MorningStatus":status}); rows.append(x)
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

def tv_link(t): return f"https://www.tradingview.com/symbols/{t}/?exchange=IDX"

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

def show_top3(action,meta):
    st.markdown('<div class="section-title">🏆 Top 3 Actionable Picks — Risk-Gated</div>',unsafe_allow_html=True)
    st.caption("Hanya kandidat READY dari Top 10. Tetap ikuti Entry, Stop Loss, dan market gate.")
    if action is None or action.empty: st.warning("Belum ada setup READY pada snapshot ini."); return
    cols=["Ticker","Setup","Timing","Close","RSI","MACD","VolumeRatio","Support","Resistance","Entry","SL","TP1","TP2","RR","RiskPct","OpportunityScore","Status"]
    show_table(action,cols)
    for _,r in action.iterrows():
        st.markdown(f'<div class="card"><b>{r.Ticker}</b> &nbsp; {status_badge(r.Status)} &nbsp; Setup: <b>{r.Setup}</b> &nbsp; Entry <b>{fmt(r.Entry)}</b> · SL <b>{fmt(r.SL)}</b> · TP1 <b>{fmt(r.TP1)}</b> · TP2 <b>{fmt(r.TP2)}</b> · R/R <b>{fmt(r.RR,2)}</b><br><span class="small-note">Chart: <a href="{tv_link(r.Ticker)}" target="_blank">TradingView</a></span></div>',unsafe_allow_html=True)

def show_top10(opp):
    st.markdown('<div class="section-title">🟩 Top 10 Opportunity — Opportunity Now</div>',unsafe_allow_html=True)
    show_table(opp,["Ticker","Setup","Timing","OpportunityScore","Close","RSI","MACD","VolumeRatio","Support","Resistance","Entry","SL","TP1","TP2","RR","Status","Candle"])

def show_top50(focus):
    st.markdown('<div class="section-title">🟨 Top 50 Focus — Focus List</div>',unsafe_allow_html=True)
    show_table(focus,["Ticker","Setup","SetupScore","QualityScore","Close","RSI","MACD","VolumeRatio","Support","Resistance","Entry","SL","TP1","TP2","RR","Status","Timing"])

def show_top150(enrich):
    st.markdown('<div class="section-title">🟦 Top 150 Enrich — Quality Pool</div>',unsafe_allow_html=True)
    show_table(enrich,["Ticker","QualityScore","SetupScore","OpportunityScore","Close","RSI","MACD","MA20","MA50","MA200","Support","Resistance","Status","Setup"])

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
header("Sanggul Stock Scanner",f"{APP_VERSION} · 400 IDX · EOD Snapshot Persistent · Morning Confirmation · TradingView")

with st.sidebar:
    st.markdown("### 🧭 MENU UTAMA")
    mode=st.radio("Navigasi",[
        "📊 Dashboard","⚡ Trading Harian","📅 Swing Trading Mingguan","🔎 Saham Individu","🏭 Sector Opportunity","🏆 Top 3 Actionable","🟩 Top 10 Opportunity","🟨 Top 50 Focus","🟦 Top 150 Enrich","🌅 Morning Confirmation","🌆 EOD Full Scan","📜 EOD Scan History"],index=0)
    st.divider(); st.markdown("### ⚙️ PENGATURAN")
    period=st.selectbox("Data historis EOD",["1mo","3mo","6mo","2y"],index=3, format_func=lambda x: {"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan","2y":"2 Tahun"}[x])
    n=st.slider("Jumlah saham saat EOD scan",50,400,400,50)
    min_rr=st.number_input("Minimum R/R",1.5,4.0,2.0,0.5)
    st.divider(); st.caption("📌 EOD = screening utama · Pagi = konfirmasi · Harian = tactical · Mingguan = swing")
    st.caption("Periode EOD: 1B / 3B / 6B / 2T · engine indikator minimum 2T")
    scan_now=st.button("🔄 Scan 400 Saham / Update EOD",type="primary",use_container_width=True)

# Market strip
ihsg,ih20,ih50,regime=market_metrics(period)
metric_strip([("IHSG",fmt(ihsg)),("MA20",fmt(ih20)),("MA50",fmt(ih50)),("Market Gate",regime)])

snap=read_snapshot(latest_snapshot())

# Preserve manual scan from V11.1.3.7
if scan_now:
    with st.spinner(f"Menjalankan EOD scan {n} saham dan menyimpan snapshot..."):
        path=run_full_scan(period,n,min_rr)
    if path: st.success(f"Snapshot EOD tersimpan: {os.path.basename(path)}"); st.rerun()
    else: st.error("Tidak ada data yang berhasil dianalisis.")

# =========================================================
# SPECIAL MENUS
# =========================================================
if mode=="🌆 EOD Full Scan":
    header("🌆 EOD Full Scan","Bangun snapshot baru setelah market close. Snapshot lama tetap tersimpan.")
    st.info("Gunakan setelah candle harian selesai. Hasil ini menjadi baseline untuk Dashboard dan Morning Confirmation.")
    if st.button("🚀 Jalankan EOD Full Scan",type="primary"):
        path=run_full_scan(period,n,min_rr)
        if path: st.success(f"Snapshot EOD tersimpan: {os.path.basename(path)}"); st.rerun()
        else: st.error("Tidak ada data yang berhasil dianalisis.")
    st.stop()

if mode=="🌅 Morning Confirmation":
    header("🌅 Morning Confirmation","Validasi Top 10 EOD dengan kondisi harga pagi. Tidak melakukan reranking 400 saham.")
    if not snap: st.warning("Belum ada EOD Snapshot."); st.stop()
    m=snap["meta"]; st.success(f"Baseline EOD: {m.get('timestamp','—')} · Top 10 tetap dipertahankan.")
    conf=morning_confirm(snap["top10"],period)
    show_table(conf,["Ticker","Setup","Timing","MorningStatus","Current","Open","Entry","SL","TP1","TP2","RR","RSI","MACD","VolumeRatio"])
    st.caption("🟢 CONFIRM = dekat area entry · 🟡 WAIT = belum/terlalu tinggi · 🔴 CANCEL = di bawah SL.")
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

if not snap:
    st.warning("Belum ada EOD Snapshot."); st.info("Gunakan **🔄 Scan 400 Saham / Update EOD** setelah market close."); st.stop()

m=snap["meta"]; action,opp,focus,enrich=snap["top3"],snap["top10"],snap["top50"],snap["top150"]

# =========================================================
# DASHBOARD / OLD MENUS
# =========================================================
if mode=="📊 Dashboard":
    header("📊 Dashboard","Last EOD Snapshot · Risk-Gated · persistent")
    metric_strip([("Snapshot",m.get("timestamp","—").replace("T"," ")), ("EOD Window",{"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan","2y":"2 Tahun"}.get(m.get("period"),m.get("period","—"))), ("Regime",m.get("regime","—")), ("Pipeline","400 → 150 → 50 → 10 → 3")])
    show_top3(action,m); show_top150(enrich); show_top50(focus); show_top10(opp); show_rules()
    st.download_button("📥 Export Full Scan CSV",snap["full"].to_csv(index=False).encode("utf-8"),"sanggul_v11_1_3_8_full_scan.csv","text/csv")

elif mode=="⚡ Trading Harian":
    header("⚡ Trading Harian","Tactical setup untuk horizon 1–5 hari · menggunakan hasil EOD sebagai starting universe.")
    d=daily_table(snap["full"])
    if d.empty: st.info("Belum ada kandidat trading harian yang memenuhi filter.")
    else:
        metric_strip([("Kandidat",str(len(d))), ("Ready",str((d.Status=="READY").sum())), ("Breakout",str((d.Setup=="BREAKOUT").sum())), ("Pullback",str((d.Setup=="PULLBACK").sum()))])
        show_table(d,["Ticker","TradingMode","Setup","Timing","Status","Close","RSI","MACD","VolumeRatio","Support","Resistance","Entry","SL","TP1","TP2","RR","OpportunityScore"])
        st.markdown("#### 🔗 TradingView — Daily / Tactical")
        ticker=st.selectbox("Pilih saham",d.Ticker.tolist(),key="daily_ticker")
        row=d[d.Ticker==ticker].iloc[0]
        st.markdown(f'<div class="card"><b>{ticker}</b> · {row.Setup} · {status_badge(row.Status)} · Entry <b>{fmt(row.Entry)}</b> · SL <b>{fmt(row.SL)}</b> · TP1 <b>{fmt(row.TP1)}</b> · TP2 <b>{fmt(row.TP2)}</b> · R/R <b>{fmt(row.RR,2)}</b></div>',unsafe_allow_html=True)
        st.link_button("📈 Buka Chart TradingView Penuh — Daily ↗", tv_link(ticker)+"&interval=1D", use_container_width=False)

elif mode=="📅 Swing Trading Mingguan":
    header("📅 Swing Trading Mingguan","Horizon beberapa hari hingga beberapa minggu · daily setup + weekly trend confirmation.")
    st.info("Untuk menjaga kecepatan, validasi weekly dilakukan pada kandidat Top 50 EOD, bukan mengunduh ulang 400 saham.")
    w=weekly_candidates(focus)
    if w.empty: st.warning("Belum ada kandidat weekly. Pastikan EOD snapshot tersedia dan data weekly dapat diambil.")
    else:
        metric_strip([("Weekly candidates",str(len(w))), ("Weekly READY",str((w.WeeklyStatus=="READY").sum())), ("Weekly breakout",str((w.WeeklySetup=="BREAKOUT").sum())), ("Avg R/R",fmt(w.WeeklyRR.mean(),2))])
        show_table(w,["Ticker","WeeklySetup","WeeklyStatus","WeeklyScore","WeeklyRSI","WeeklyMA20","WeeklyMA50","WeeklyMA200","WeeklyEntry","WeeklySL","WeeklyTP1","WeeklyTP2","WeeklyRR","DailySetup","DailyRR","Close"])
        st.caption("Grafik tidak ditampilkan di dalam aplikasi. Gunakan chart TradingView penuh agar ruang dashboard tetap ringkas.")
        ticker=st.selectbox("Pilih saham weekly",w.Ticker.tolist(),key="weekly_ticker")
        row=w[w.Ticker==ticker].iloc[0]
        st.markdown(f'<div class="card"><b>{ticker}</b> · Weekly {row.WeeklySetup} · {status_badge(row.WeeklyStatus)} · Entry <b>{fmt(row.WeeklyEntry)}</b> · SL <b>{fmt(row.WeeklySL)}</b> · TP1 <b>{fmt(row.WeeklyTP1)}</b> · TP2 <b>{fmt(row.WeeklyTP2)}</b> · R/R <b>{fmt(row.WeeklyRR,2)}</b></div>',unsafe_allow_html=True)
        st.link_button("📈 Buka Chart TradingView Penuh — Weekly ↗", tv_link(ticker)+"&interval=1W", use_container_width=False)

elif mode=="🔎 Saham Individu":
    header("🔎 Saham Individu","Terminal analisis per saham dengan quote teknikal + chart TradingView.")
    universe=load_universe()
    ticker=st.selectbox("Pilih saham IDX",universe,index=universe.index("BBCA") if "BBCA" in universe else 0)
    d=load_data(ticker,"2y","1d"); a=analyze(d)
    if a is None: st.warning("Data teknikal belum cukup untuk dianalisis."); st.stop()
    metric_strip([("Ticker",ticker),("Last",fmt(a["Close"])),("RSI",fmt(a["RSI"],1)),("R/R",fmt(a["RR"],2)),("Setup",a["Setup"]),("Status",a["Status"])])
    left,right=st.columns([1.25,1])
    with left:
        st.markdown("#### 🔗 TradingView Penuh")
        st.caption("Chart embedded dihilangkan agar dashboard lebih ringkas. Buka TradingView penuh untuk melihat candle, Bollinger Bands, Volume, MACD, RSI, dan indikator lainnya.")
        c1,c2=st.columns(2)
        with c1: st.link_button("📈 Daily ↗", tv_link(ticker)+"&interval=1D", use_container_width=True)
        with c2: st.link_button("📅 Weekly ↗", tv_link(ticker)+"&interval=1W", use_container_width=True)
        st.markdown('<div class="card"><b>Periode data EOD yang dipilih:</b> '+{"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan","2y":"2 Tahun"}.get(period,period)+'<br><span class="small-note">Mesin indikator tetap mengambil minimal 2 tahun secara internal agar MA200, RSI dan MACD tetap valid; periode di atas menentukan jendela historis EOD yang dipakai sebagai acuan review.</span></div>',unsafe_allow_html=True)
    with right:
        st.markdown("#### Ringkasan Teknis")
        st.markdown(f'<div class="card">Trend MA20/50/200: <b>{"Bullish" if a["MA20"]>a["MA50"] else "Mixed"}</b><br>RSI: <b>{fmt(a["RSI"],1)}</b><br>MACD: <b>{fmt(a["MACD"],2)}</b><br>Volume ratio: <b>{fmt(a["VolumeRatio"],2)}x</b><br>Support: <b>{fmt(a["Support"])}</b><br>Resistance: <b>{fmt(a["Resistance"])}</b><br>Candle: <b>{a["Candle"]}</b></div>',unsafe_allow_html=True)
        st.markdown("#### Trade Plan")
        st.markdown(f'<div class="card">Setup <b>{a["Setup"]}</b><br>Entry <b>{fmt(a["Entry"])}</b><br>Stop Loss <b>{fmt(a["SL"])}</b><br>TP1 <b>{fmt(a["TP1"])}</b><br>TP2 <b>{fmt(a["TP2"])}</b><br>R/R <b>{fmt(a["RR"],2)}</b><br>Status {status_badge(a["Status"])}</div>',unsafe_allow_html=True)
        st.markdown(f"[Buka chart TradingView penuh ↗]({tv_link(ticker)})")

elif mode=="🏭 Sector Opportunity":
    header("🏭 Sector Opportunity","Klik nama sektor untuk melihat daftar saham di dalam sektor tersebut. Ini adalah alat pemetaan peluang, bukan sinyal BUY otomatis.")
    full=snap["full"].copy()
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
    header("🏆 Top 3 Actionable","Risk-Gated execution candidates dari snapshot EOD."); show_top3(action,m); show_rules()
elif mode=="🟩 Top 10 Opportunity":
    header("🟩 Top 10 Opportunity","Opportunity pool — bukan otomatis BUY."); show_top10(opp); show_rules()
elif mode=="🟨 Top 50 Focus":
    header("🟨 Top 50 Focus","Focused setup list dengan R/R minimum."); show_top50(focus); show_rules()
elif mode=="🟦 Top 150 Enrich":
    header("🟦 Top 150 Enrich","Quality pool untuk pemantauan lebih luas."); show_top150(enrich); show_rules()
