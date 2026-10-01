import os, json, glob
from datetime import datetime
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import yfinance as yf

APP_VERSION = "V11.1.5 PRO HYBRID FIX5 · RISK GATE 2.0"
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
    status="AVOID" if close<ma50 and x.MACD<x.MACDsig else ("READY" if ready else "WAIT")
    timing="SORE / CLOSE CONFIRM" if breakout else ("PAGI CONFIRM" if near_support or pullback else "WATCH")
    atr14=float(x.ATR14) if pd.notna(x.ATR14) and x.ATR14>0 else np.nan
    risk_pct=risk/entry*100
    risk_atr=(risk/atr14) if pd.notna(atr14) and atr14>0 else np.nan
    overext=max(close/ma20-1,0)*100 if ma20>0 else np.nan
    entry_gap=abs(entry-close)/close*100 if close>0 else np.nan
    return {"Close":close,"MA20":ma20,"MA50":ma50,"MA200":ma200,"Return20D":ret20*100,"Return60D":ret60*100,"RSI":float(x.RSI),"MACD":float(x.MACD),"VolumeRatio":vr,"ATR14":atr14,"Support":support,"Resistance":resistance,"Entry":entry,"SL":sl,"TP1":tp1,"TP2":tp2,"RR":rr,"RiskPct":risk_pct,"StopDistancePct":risk_pct,"RiskATRMultiple":risk_atr,"OverextensionPct":overext,"EntryGapPct":entry_gap,"QualityScore":quality,"SetupScore":setup,"OpportunityScore":opportunity,"Status":status,"Setup":setup_type,"Timing":timing,"Candle":candle}

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
    embedded 400-ticker fallback. The embedded fallback prevents a deployment
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

    # Embedded fallback: use the same 400-ticker universe shipped with this build.
    fallback = ['BBCA', 'BBRI', 'DCII', 'BREN', 'BYAN', 'BMRI', 'AMMN', 'TLKM', 'MORA', 'ASII', 'DSSA', 'TPIA', 'SRAJ', 'BRPT', 'DNET', 'BBNI', 'SMMA', 'MPRO', 'EMAS', 'CUAN', 'BRMS', 'CASA', 'PANI', 'AADI', 'IMPC', 'UNTR', 'ICBP', 'CDIA', 'ANTM', 'ISAT', 'BNLI', 'MDKA', 'HMSP', 'ADRO', 'BRIS', 'BUMI', 'ADMR', 'UNVR', 'INDF', 'NCKL', 'MBMA', 'PTRO', 'PGUN', 'AMRT', 'GOTO', 'MLPT', 'CPIN', 'INCO', 'SUPR', 'INKP', 'MEGA', 'PGEO', 'EXCL', 'BNGA', 'BDMN', 'GEMS', 'BELI', 'MTEL', 'TAPG', 'VKTR', 'MEDC', 'CMRY', 'TINS', 'PTBA', 'PGAS', 'KLBF', 'ARCI', 'GGRM', 'ENRG', 'MYOR', 'TBIG', 'JARR', 'MGLV', 'NISP', 'AKRA', 'ITMG', 'EMTK', 'SILO', 'JPFA', 'LIFE', 'FAPA', 'MAPI', 'BINA', 'BTPN', 'GIAA', 'SRTG', 'MIKA', 'MDIY', 'TOWR', 'TKIM', 'SINI', 'ULTJ', 'PNBN', 'CBDK', 'MKPI', 'AVIA', 'JSMR', 'BSIM', 'MAPA', 'BBHI', 'ADES', 'NSSS', 'SOHO', 'PACK', 'SMAR', 'INTP', 'BUVA', 'SUPA', 'BBSI', 'AUTO', 'DSNG', 'BBTN', 'POWR', 'AALI', 'RAJA', 'DEWA', 'INDY', 'JRPT', 'BNBR', 'MSIN', 'BNII', 'PSAB', 'MLBI', 'BSSR', 'BFIN', 'CITA', 'FASW', 'POLU', 'PWON', 'CARE', 'STAA', 'MCOL', 'COIN', 'RLCO', 'CMNT', 'ARTO', 'STTP', 'BSDE', 'TSPC', 'RISE', 'HRUM', 'SGER', 'IBST', 'GOOD', 'ARKO', 'BKSL', 'ALII', 'SCMA', 'RATU', 'SMGR', 'AGII', 'YUPI', 'LSIP', 'ADMF', 'CTRA', 'PRAY', 'HRTA', 'ESSA', 'SIDO', 'NATO', 'SSMS', 'SMMT', 'CLEO', 'BUKA', 'WIFI', 'SMSM', 'HEAL', 'EDGE', 'ERAA', 'BIPI', 'BBKP', 'CMNP', 'BMAS', 'SIMP', 'DMAS', 'PLIN', 'DUTI', 'XSPI', 'RMKE', 'BHAT', 'MIDI', 'SGRO', 'WIKA', 'TMAS', 'SSIA', 'FILM', 'BJBR', 'INPP', 'BBMD', 'BJTM', 'TLDN', 'ABMM', 'TCPI', 'CNMA', 'BTPS', 'MDIA', 'INET', 'FORE', 'CYBR', 'EPMT', 'SHIP', 'CLAY', 'GMFI', 'SMCB', 'VICI', 'PNLF', 'SMDR', 'PKPK', 'DMND', 'MTDL', 'BULL', 'TRIM', 'ACES', 'BOGA', 'KPIG', 'YULE', 'UNIC', 'WBSA', 'TOTL', 'OMED', 'BSWD', 'TUGU', 'MAYA', 'ANJT', 'BALI', 'MBSS', 'MSJA', 'SAME', 'ELSA', 'UANG', 'BPII', 'APIC', 'SOCI', 'NICL', 'JECX', 'ELPI', 'MASB', 'TGKA', 'DRMA', 'PALM', 'GJTL', 'MPMX', 'SURE', 'HATM', 'LINK', 'KRAS', 'SMRA', 'TOBA', 'MSTI', 'MARK', 'MMIX', 'AMAR', 'NOBU', 'TFCO', 'GGRP', 'VISI', 'JTPE', 'BIRD', 'MTLA', 'PBID', 'KIJA', 'SMIL', 'ARGO', 'CASS', 'EURO', 'ALKA', 'DKFT', 'TBLA', 'LPKR', 'BWPT', 'PSGO', 'BEEF', 'MKAP', 'RDTX', 'NIRO', 'ARNA', 'BANK', 'AGRO', 'CBRE', 'LPPF', 'IATA', 'JSPT', 'IMAS', 'HEXA', 'GOLF', 'KEJU', 'CENT', 'ROTI', 'DOOH', 'WIIM', 'SAMF', 'DAAZ', 'KEEN', 'NEST', 'ABDA', 'SKRN', 'FISH', 'SDRA', 'INPC', 'BESS', 'BBYB', 'CBUT', 'CPRO', 'FPNI', 'MDLA', 'BNBA', 'PNIN', 'OMRE', 'ASGR', 'ISSP', 'AGRS', 'JAWA', 'LPCK', 'APLN', 'BGTG', 'KETR', 'ROCK', 'IRSX', 'DAYA', 'SFAN', 'BUKK', 'PNGO', 'MAPB', 'PORT', 'VICO', 'TEBE', 'PYFA', 'ASLI', 'ALDO', 'WINS', 'PRDA', 'MCOR', 'SMDM', 'BCIC', 'TOTO', 'ASRI', 'RANS', 'PBSA', 'MGRO', 'GTSI', 'CTBN', 'MAHA', 'KAEF', 'AGAR', 'HUMI', 'MINA', 'RALS', 'PTSN', 'PSKT', 'MYOH', 'BACA', 'DATA', 'BABP', 'ASSA', 'SCCO', 'MNCN', 'NICE', 'MMLP', 'MBAP', 'BISI', 'BCAP', 'DWGL', 'DNAR', 'BRAM', 'KMTR', 'BHIT', 'UCID', 'NETV', 'STAR', 'AYAM', 'IMJS', 'IFII', 'KOTA', 'IPCC', 'IFSH', 'INDR', 'PNBS', 'LPGI', 'MTMH', 'AMAG', 'FAST', 'RONY', 'DGWG', 'KINO', 'PMJS', 'BOLT', 'CARS', 'POLI', 'NICK', 'ACST', 'BMTR', 'FUTR', 'OASA', 'PSSI', 'DVLA', 'BKSW', 'BLTZ', 'BLES', 'BMHS', 'MERK']
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

def apply_risk_gate(result,min_rr,max_stop_pct=15.0,market_regime="NEUTRAL / SIDEWAYS"):
    x=result.copy()
    gates=[]; flags=[]
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
        if pd.notna(risk_pct) and risk_pct > max_stop_pct: issues.append("STOP DISTANCE")
        if pd.notna(atr_mult) and atr_mult > 4.5: issues.append("ATR RISK")
        if str(market_regime).upper().startswith("RISK-OFF"): issues.append("MARKET")
        if not issues:
            gate="PASS"
        elif "TECH" in issues or "SETUP WAIT" in issues:
            gate="WAIT"
        elif "MARKET" in issues:
            gate="MARKET REVIEW"
        elif "STOP DISTANCE" in issues or "ATR RISK" in issues:
            gate="RISK REVIEW"
        else:
            gate="FACTOR REVIEW"
        gates.append(gate)
        flags.append(", ".join(issues) if issues else "OK")
    x["RiskGate"]=gates
    x["RiskFlag"]=flags
    x["RiskGateVersion"]="2.0"
    x["ActionableMode"]=np.where(x["RiskGate"]=="PASS",x["AnalysisMode"],"NOT ACTIONABLE")
    return x

def build_layers(result,min_rr):
    def sortdf(df, cols):
        use=[c for c in cols if c in df.columns]
        return df.sort_values(use,ascending=[False]*len(use)) if use else df
    enrich=sortdf(result,['MultiFactorScore','QualityScore','SetupScore','RR']).head(150).copy(); enrich['Layer']='TOP 150 ENRICH'
    focus=sortdf(result[result.RR>=min_rr],['MultiFactorScore','SetupScore','QualityScore','RR']).head(50).copy(); focus['Layer']='TOP 50 FOCUS'
    opp=sortdf(result[result.RR>=min_rr],['MultiFactorScore','OpportunityScore','SetupScore','RR']).head(10).copy(); opp['Layer']='TOP 10 OPPORTUNITY'
    # Top 3 must be genuinely actionable: READY + PASS + a non-WAIT setup.
    # WAIT remains valid for Top 10/watchlist but should never be presented as an execution candidate.
    actionable_setups=['BREAKOUT','PULLBACK','REJECTION SUPPORT']
    action_pool=opp[(opp.Status=='READY')&(opp.RiskGate=='PASS')&(opp.Setup.isin(actionable_setups))].copy()
    action=sortdf(action_pool,['MultiFactorScore','RR','SetupScore']).head(3).copy(); action['Layer']='TOP 3 ACTIONABLE'
    return enrich,focus,opp,action

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
    result=factor_enrich(result); ih=load_data("^JKSE",engine_period,"1d")
    if len(ih)>=220:
        ic=ih.Close; ihsg=float(ic.iloc[-1]); ih20=float(ic.rolling(20).mean().iloc[-1]); ih50=float(ic.rolling(50).mean().iloc[-1]); regime="RISK-ON" if ihsg>ih20>ih50 else ("NEUTRAL / SIDEWAYS" if ihsg>=ih50 else "RISK-OFF")
    else: ihsg=ih20=ih50=np.nan; regime="DATA INSUFFICIENT"
    result=apply_risk_gate(result,min_rr,max_stop_pct,regime)
    enrich,focus,opp,action=build_layers(result,min_rr)
    meta={"timestamp":datetime.now().isoformat(timespec="seconds"),"period":period,"engine_period":engine_period,"universe":n,"analyzed":len(result),"min_rr":min_rr,"max_stop_pct":max_stop_pct,"ihsg":ihsg,"ihsg_ma20":ih20,"ihsg_ma50":ih50,"regime":regime,"analysis_mode":"HYBRID","risk_gate_version":"2.0"}
    if save_eod:
        return save_snapshot(result,enrich,focus,opp,action,meta)
    st.session_state["current_scan"]={"meta":meta,"full":result,"top150":enrich,"top50":focus,"top10":opp,"top3":action}
    return "CURRENT_SCAN"

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

def show_top3(action,meta,opp=None):
    st.markdown('<div class="section-title">🏆 Top 3 Actionable Picks — Hybrid Risk Gate</div>',unsafe_allow_html=True)
    st.caption("Risk Gate 2.0 menilai setup, R/R, jarak Stop Loss, risiko terhadap ATR, dan market regime. Foreign Flow, Broker Flow, dan Fundamental tetap enrichment opsional.")
    if action is None or action.empty:
        o=opp.copy() if isinstance(opp,pd.DataFrame) else pd.DataFrame()
        if o.empty: st.warning('Top 3 belum terbentuk karena Top 10 snapshot kosong.'); return
        ready=o[o.Status.astype(str).str.upper()=='READY'].copy() if 'Status' in o.columns else pd.DataFrame()
        passed=ready[ready.RiskGate.astype(str).str.upper()=='PASS'].copy() if 'RiskGate' in ready.columns else pd.DataFrame()
        c1,c2,c3=st.columns(3); c1.metric('Top 10',len(o)); c2.metric('READY',len(ready)); c3.metric('Risk Gate PASS',len(passed))
        actionable_setups=['BREAKOUT','PULLBACK','REJECTION SUPPORT']
        actionable_ready=ready[ready.get('Setup',pd.Series(index=ready.index,dtype=object)).isin(actionable_setups)] if not ready.empty else pd.DataFrame()
        if ready.empty:
            st.warning('Belum ada kandidat READY di Top 10. Tunggu setup teknikal/market gate yang lebih baik.')
        elif actionable_ready.empty:
            st.warning('Ada saham READY, tetapi setup-nya masih WAIT. Saham WAIT tetap masuk Top 10 sebagai watchlist, bukan Top 3 Actionable.')
        elif passed.empty:
            st.warning('Ada kandidat READY tetapi belum PASS karena Multi-Factor Score masih di bawah ambang 65.')
        else:
            st.info(f'{len(actionable_ready)} kandidat READY memiliki setup yang dapat dieksekusi; lihat tabel kandidat di bawah.')
            cols=['Ticker','Setup','Timing','Close','Entry','SL','TP1','TP2','RR','TechnicalScore','MultiFactorScore','FactorCoveragePct','AnalysisMode','RiskGate','Status']
            sort=[c for c in ['MultiFactorScore','TechnicalScore','RR'] if c in ready.columns]
            cand=actionable_ready if not actionable_ready.empty else ready
            show_table(cand.sort_values(sort,ascending=False).head(3),cols,'📋 Top 3 Technical Candidates')
        return
    cols=['Ticker','Setup','Timing','Close','MA20','RSI','MACD','VolumeRatio','Entry','SL','TP1','TP2','RR','RiskPct','RiskATRMultiple','OverextensionPct','TechnicalScore','FundamentalScore','ForeignFlowScore','BrokerFlowScore','SectorStrengthScore','MultiFactorScore','FactorCoveragePct','AnalysisMode','RiskGate','RiskFlag','Status']
    display=action.copy()
    for score_col,flag_col in [('FundamentalScore','FundamentalAvailable'),('ForeignFlowScore','ForeignAvailable'),('BrokerFlowScore','BrokerAvailable')]:
        if score_col in display.columns and flag_col in display.columns:
            display.loc[~display[flag_col].fillna(False).astype(bool),score_col]=np.nan
    show_table(display,cols)
    # Snapshot compatibility: older EOD snapshots may not contain the newer
    # Hybrid columns (AnalysisMode / FactorCoveragePct / RiskGate / Status).
    # Never access them as Series attributes; use .get() so legacy snapshots
    # cannot crash the dashboard.
    for _,r in action.iterrows():
        ticker=str(r.get('Ticker','—'))
        status=str(r.get('Status','WAIT'))
        mode_label=str(r.get('AnalysisMode','LEGACY / UNKNOWN'))
        try:
            cov=float(r.get('FactorCoveragePct',0) or 0)
        except Exception:
            cov=0.0
        gate=str(r.get('RiskGate','LEGACY / REVIEW'))
        setup=str(r.get('Setup','—'))
        entry=r.get('Entry',np.nan); sl=r.get('SL',np.nan); tp1=r.get('TP1',np.nan); tp2=r.get('TP2',np.nan); rr=r.get('RR',np.nan)
        risk_pct=r.get('RiskPct',np.nan); atr_mult=r.get('RiskATRMultiple',np.nan); flag=str(r.get('RiskFlag','OK'))
        flag_html='' if flag=='OK' else f' · <span class="small-note">⚠️ {flag}</span>'
        st.markdown(f'<div class="card"><b>{ticker}</b> &nbsp; {status_badge(status)} &nbsp; <b>{mode_label}</b> · Coverage <b>{cov:.0f}%</b> · Risk Gate <b>{gate}</b><br>Setup: <b>{setup}</b> · Entry <b>{fmt(entry)}</b> · SL <b>{fmt(sl)}</b> · TP1 <b>{fmt(tp1)}</b> · TP2 <b>{fmt(tp2)}</b> · R/R <b>{fmt(rr,2)}</b> · Stop <b>{fmt(risk_pct,1)}%</b> · ATR Risk <b>{fmt(atr_mult,1)}x</b>{flag_html}<br><span class="small-note">Chart: <a href="{tv_link(ticker)}" target="_blank">TradingView</a></span></div>',unsafe_allow_html=True)

def show_top10(opp):
    st.markdown('<div class="section-title">🟩 Top 10 Opportunity — Opportunity Now</div>',unsafe_allow_html=True)
    show_table(opp,["Ticker","Setup","Timing","OpportunityScore","MultiFactorScore","FactorCoveragePct","AnalysisMode","RiskGate","RiskFlag","Close","MA20","RSI","MACD","VolumeRatio","Entry","SL","TP1","TP2","RR","RiskPct","RiskATRMultiple","Status","Candle"])

def show_top50(focus):
    st.markdown('<div class="section-title">🟨 Top 50 Focus — Focus List</div>',unsafe_allow_html=True)
    show_table(focus,["Ticker","Setup","SetupScore","QualityScore","MultiFactorScore","FactorCoveragePct","RiskGate","Close","MA20","RSI","MACD","VolumeRatio","Entry","SL","TP1","TP2","RR","Status","Timing"])

def show_top150(enrich):
    st.markdown('<div class="section-title">🟦 Top 150 Enrich — Quality Pool</div>',unsafe_allow_html=True)
    show_table(enrich,["Ticker","QualityScore","SetupScore","OpportunityScore","MultiFactorScore","FactorCoveragePct","RiskGate","Close","RSI","MACD","MA20","MA50","MA200","Support","Resistance","Status","Setup"])

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
header("Sanggul Stock Scanner",f"{APP_VERSION} · 400 IDX · Hybrid Factors · EOD Snapshot Persistent · Morning Confirmation · TradingView")

with st.sidebar:
    st.markdown("### 🧭 MENU UTAMA")
    mode=st.radio("Navigasi",[
        "📊 Dashboard","⚡ Trading Harian","📅 Swing Trading Mingguan","🔎 Saham Individu","🏭 Sector Opportunity","🏆 Top 3 Actionable","🟩 Top 10 Opportunity","🟨 Top 50 Focus","🟦 Top 150 Enrich","🌅 Morning Confirmation","🌆 EOD Full Scan","📜 EOD Scan History","🧠 Multi-Factor Data Hub"],index=0)
    st.divider(); st.markdown("### ⚙️ PENGATURAN")
    period=st.selectbox("Data historis EOD",["1mo","3mo","6mo","2y"],index=3, format_func=lambda x: {"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan","2y":"2 Tahun"}[x])
    n=st.slider("Jumlah saham saat EOD scan",50,400,400,50)
    min_rr=st.number_input("Minimum R/R",1.5,4.0,2.0,0.5)
    max_stop_pct=st.number_input("Max Stop Distance (%)",5.0,40.0,15.0,1.0,help="Risk Gate 2.0: kandidat dengan jarak Entry–SL di atas batas ini masuk RISK REVIEW.")
    st.divider(); st.caption("📌 EOD = screening utama · Pagi = konfirmasi · Harian = tactical · Mingguan = swing · External factors = optional enrichment")
    st.caption("Periode EOD: 1B / 3B / 6B / 2T · engine indikator minimum 2T")
    scan_now=st.button("🔄 Scan 400 Saham / Update EOD",type="primary",use_container_width=True)

# Market strip
ihsg,ih20,ih50,regime=market_metrics(period)
metric_strip([("IHSG",fmt(ihsg)),("MA20",fmt(ih20)),("MA50",fmt(ih50)),("Market Gate",regime)])

snap=read_snapshot(latest_snapshot())
current_scan=st.session_state.get("current_scan")

# Scan 400 is a current/dynamic view and does not overwrite the official EOD snapshot.

if scan_now:
    with st.spinner(f"Menjalankan EOD scan {n} saham dan menyimpan snapshot..."):
        path=run_full_scan(period,n,min_rr,max_stop_pct,save_eod=False)
    if path: st.success("Current Scan selesai. Snapshot EOD resmi tidak diubah."); st.rerun()
    else: st.error("Tidak ada data yang berhasil dianalisis.")

# Current Scan takes precedence for analytical menus during this session;
# official EOD history remains read from the persisted snapshot.
active=snap
if current_scan is not None:
    active=current_scan

# =========================================================
# SPECIAL MENUS
# =========================================================
if mode=="🌆 EOD Full Scan":
    header("🌆 EOD Full Scan","Bangun snapshot baru setelah market close. Snapshot lama tetap tersimpan.")
    st.info("Gunakan setelah candle harian selesai. Hasil ini menjadi baseline untuk Dashboard dan Morning Confirmation.")
    if st.button("🚀 Jalankan EOD Full Scan",type="primary"):
        path=run_full_scan(period,n,min_rr,max_stop_pct)
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

if mode=="🧠 Multi-Factor Data Hub":
    header("🧠 Multi-Factor Data Hub","Hybrid engine: Technical + Sector tetap berjalan; Fundamental/Foreign/Broker memperkaya jika tersedia.")
    universe=load_universe()
    st.markdown("#### 📊 Data Quality")
    q=data_quality_table(universe)
    st.dataframe(q,use_container_width=True,hide_index=True)
    st.caption("Coverage = persentase ticker pada universe 400 yang memiliki data faktor. Data external tidak pernah dibuat/fiktif.")
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
    st.info("Setelah data tersimpan, jalankan **🔄 Scan 400 Saham / Update EOD** agar Multi-Factor Score dan Risk Gate dihitung ulang. Tanpa external data pun scanner tetap dapat menghasilkan kandidat melalui CORE TECHNICAL + SECTOR. Scan 400 tidak menghapus snapshot EOD lama sampai Anda menjalankan EOD Full Scan.")
    st.stop()

if not active:
    st.warning("Belum ada data scan. Gunakan **🔄 Scan 400 Saham / Update EOD** atau **🌆 EOD Full Scan**."); st.stop()

m=active["meta"]; action,opp,focus,enrich=active["top3"],active["top10"],active["top50"],active["top150"]

# =========================================================
# DASHBOARD / OLD MENUS
# =========================================================
if mode=="📊 Dashboard":
    header("📊 Dashboard","Last EOD Snapshot · Risk-Gated · persistent")
    metric_strip([("Snapshot",m.get("timestamp","—").replace("T"," ")), ("EOD Window",{"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan","2y":"2 Tahun"}.get(m.get("period"),m.get("period","—"))), ("Regime",m.get("regime","—")), ("Pipeline","400 → 150 → 50 → 10 → 3")])
    st.info("HYBRID: Technical 55% + Fundamental 20% + Foreign 10% + Broker 5% + Sector 10%. Bobot faktor yang tersedia otomatis dinormalisasi. Foreign/Broker/Fundamental adalah enrichment, bukan syarat wajib Top 3.")
    show_top3(action,m); show_top150(enrich); show_top50(focus); show_top10(opp); show_rules()
    st.download_button("📥 Export Full Scan CSV",active["full"].to_csv(index=False).encode("utf-8"),"sanggul_v11_1_5_full_scan.csv","text/csv")

elif mode=="⚡ Trading Harian":
    header("⚡ Trading Harian","Tactical setup untuk horizon 1–5 hari · menggunakan hasil EOD sebagai starting universe.")
    d=daily_table(active["full"])
    if d.empty: st.info("Belum ada kandidat trading harian yang memenuhi filter.")
    else:
        metric_strip([("Kandidat",str(len(d))), ("Ready",str((d.Status=="READY").sum())), ("Breakout",str((d.Setup=="BREAKOUT").sum())), ("Pullback",str((d.Setup=="PULLBACK").sum()))])
        show_table(d,["Ticker","TradingMode","Setup","Timing","Status","Close","MA20","MA50","MA200","RSI","MACD","VolumeRatio","Support","Resistance","Entry","SL","TP1","TP2","RR","OpportunityScore"])
        st.markdown("#### 🔗 TradingView — Daily / Tactical")
        ticker=st.selectbox("Pilih saham",d.Ticker.tolist(),key="daily_ticker")
        row=d[d.Ticker==ticker].iloc[0]
        st.markdown(f'<div class="card"><b>{ticker}</b> · {row.Setup} · {status_badge(row.Status)} · MA20 <b>{fmt(row.MA20)}</b> · Entry <b>{fmt(row.Entry)}</b> · SL <b>{fmt(row.SL)}</b> · TP1 <b>{fmt(row.TP1)}</b> · TP2 <b>{fmt(row.TP2)}</b> · R/R <b>{fmt(row.RR,2)}</b></div>',unsafe_allow_html=True)
        st.link_button("📈 Buka Chart TradingView Penuh — Daily ↗", tv_link(ticker,"1D"), use_container_width=False)

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
        st.link_button("📈 Buka Chart TradingView Penuh — Weekly ↗", tv_link(ticker,"1W"), use_container_width=False)

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
        st.caption("Chart embedded dihilangkan agar dashboard tetap ringkas. Tombol di bawah langsung membuka TradingView Supercharts. Gunakan layout candle dan indikator MA20, Bollinger Bands, Volume, MACD, serta RSI seperti template analisis Sanggul.")
        c1,c2=st.columns(2)
        with c1: st.link_button("📈 Daily — Supercharts ↗", tv_link(ticker,"1D"), use_container_width=True)
        with c2: st.link_button("📅 Weekly — Supercharts ↗", tv_link(ticker,"1W"), use_container_width=True)
        st.markdown('<div class="card"><b>Periode data EOD yang dipilih:</b> '+{"1mo":"1 Bulan","3mo":"3 Bulan","6mo":"6 Bulan","2y":"2 Tahun"}.get(period,period)+'<br><span class="small-note">Mesin indikator tetap mengambil minimal 2 tahun secara internal agar MA200, RSI dan MACD tetap valid; periode di atas menentukan jendela historis EOD yang dipakai sebagai acuan review.</span></div>',unsafe_allow_html=True)
    with right:
        st.markdown("#### Ringkasan Teknis")
        
        st.markdown(f'<div class="card">Trend MA20/50/200: <b>{"Bullish" if a["MA20"]>a["MA50"] else "Mixed"}</b><br>MA20: <b>{fmt(a["MA20"])}</b><br>MA50: <b>{fmt(a["MA50"])}</b><br>MA200: <b>{fmt(a["MA200"])}</b><br>Price vs MA20: <b>{fmt((a["Close"]-a["MA20"])/a["MA20"]*100,1)}%</b><br>RSI: <b>{fmt(a["RSI"],1)}</b><br>MACD: <b>{fmt(a["MACD"],2)}</b><br>Volume ratio: <b>{fmt(a["VolumeRatio"],2)}x</b><br>Support: <b>{fmt(a["Support"])}</b><br>Resistance: <b>{fmt(a["Resistance"])}</b><br>Candle: <b>{a["Candle"]}</b></div>',unsafe_allow_html=True)
        st.markdown("#### Trade Plan")
        st.markdown(f'<div class="card">Setup <b>{a["Setup"]}</b><br>Entry <b>{fmt(a["Entry"])}</b><br>Stop Loss <b>{fmt(a["SL"])}</b><br>TP1 <b>{fmt(a["TP1"])}</b><br>TP2 <b>{fmt(a["TP2"])}</b><br>R/R <b>{fmt(a["RR"],2)}</b><br>Status {status_badge(a["Status"])}</div>',unsafe_allow_html=True)
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
    header("🏆 Top 3 Actionable","Risk-Gated execution candidates dari snapshot EOD."); show_top3(action,m,opp); show_rules()
elif mode=="🟩 Top 10 Opportunity":
    header("🟩 Top 10 Opportunity","Opportunity pool — bukan otomatis BUY."); show_top10(opp); show_rules()
elif mode=="🟨 Top 50 Focus":
    header("🟨 Top 50 Focus","Focused setup list dengan R/R minimum."); show_top50(focus); show_rules()
elif mode=="🟦 Top 150 Enrich":
    header("🟦 Top 150 Enrich","Quality pool untuk pemantauan lebih luas."); show_top150(enrich); show_rules()
