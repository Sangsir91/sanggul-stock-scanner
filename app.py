import warnings
warnings.filterwarnings('ignore')

from datetime import datetime
import io
import numpy as np
import pandas as pd
import streamlit as st

try:
    import yfinance as yf
except Exception:
    yf = None

try:
    import plotly.graph_objects as go
except Exception:
    go = None

st.set_page_config(
    page_title='Sanggul Stock Scanner Pro V10',
    page_icon='📈',
    layout='wide',
    initial_sidebar_state='expanded'
)

# -----------------------------
# UI styling
# -----------------------------
st.markdown('''
<style>
:root { --line:#e5e7eb; --muted:#667085; --ink:#172033; }
[data-testid="stAppViewContainer"] { background:#f7f9fc; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1500px; padding-top:1rem; padding-bottom:2rem; }
.card { background:#fff; border:1px solid var(--line); border-radius:16px; padding:16px 18px; margin-bottom:14px; box-shadow:0 2px 8px rgba(16,24,40,.025); }
.card-title { color:var(--ink); font-size:1.05rem; font-weight:750; margin-bottom:3px; }
.card-sub { color:var(--muted); font-size:.82rem; }
.kpi { background:#fff; border:1px solid var(--line); border-radius:14px; padding:13px 15px; min-height:94px; }
.kpi-label { color:var(--muted); font-size:.76rem; }
.kpi-value { color:var(--ink); font-size:1.35rem; font-weight:800; margin-top:4px; }
.kpi-note { color:var(--muted); font-size:.74rem; margin-top:3px; }
.badge { display:inline-block; border-radius:999px; padding:4px 9px; font-size:.72rem; font-weight:750; }
.buy { color:#087443; background:#e8f7ee; }
.watch { color:#946200; background:#fff3cd; }
.risk { color:#b42318; background:#fdecec; }
.neutral { color:#475467; background:#eef1f5; }
.section-space { margin-top:8px; }
</style>
''', unsafe_allow_html=True)

DEFAULT_UNIVERSE = '''BBCA,BBRI,BMRI,BBNI,BRIS,BBTN,ADRO,ANTM,PTBA,ITMG,MEDC,PGAS,AKRA,INCO,MDKA,AMMN,TLKM,ISAT,EXCL,MTEL,TBIG,ASII,UNTR,INDF,ICBP,MYOR,SMGR,INTP,JPFA,CPIN,UNVR,KLBF,MIKA,HEAL,EMTK,BUKA,GOTO,ACES,ERAA,MAPA,MAPI,AMRT,BRPT,TPIA,ESSA,INKP,TKIM,SMRA,CTRA,BSDE,DMAS,PWON,SCMA,ELSA,PGEO,RAJA,DEWA,DOID,HRUM,MBMA,NCKL,PSAB,SMDR,TMAS,ASSA,WEHA,BBYB,BANK,ARTO,BBHI,AGRO,BNGA,BDMN,MEGA,PNBN,BNLI,PNBS,LPKR,LPCK,KIJA,PPRO,WIKA,WSKT,PTPP,ADHI,WEGE,BUAH,ULTJ,ROTI,SIDO,TOWR'''

PERIODS = {
    '1 Bulan': 21,
    '3 Bulan': 63,
    '6 Bulan': 126,
    '2 Tahun': 504,
}

# -----------------------------
# Helpers
# -----------------------------
def ticker_symbol(code):
    return f"{str(code).strip().upper().replace('.JK','')}.JK"

def fmt_num(x, digits=2):
    try:
        if x is None or pd.isna(x) or np.isinf(x): return '-'
        return f'{float(x):,.{digits}f}'
    except Exception:
        return '-'

def fmt_price(x):
    try:
        if x is None or pd.isna(x): return '-'
        return f'Rp {float(x):,.0f}'
    except Exception:
        return '-'

def fmt_pct(x, digits=2):
    try:
        if x is None or pd.isna(x) or np.isinf(x): return '-'
        return f'{float(x):+,.{digits}f}%'
    except Exception:
        return '-'

def safe_float(x):
    try:
        return float(x) if pd.notna(x) else np.nan
    except Exception:
        return np.nan

def badge(text):
    text = str(text)
    if text in ('BUY','STRONG BUY','PASS','BULLISH'):
        cls = 'buy'
    elif text in ('WATCH','CAUTION','SIDEWAYS'):
        cls = 'watch'
    elif text in ('AVOID','BEARISH','FAIL'):
        cls = 'risk'
    else:
        cls = 'neutral'
    return f'<span class="badge {cls}">{text}</span>'

def kpi(label, value, note=''):
    return f'<div class="kpi"><div class="kpi-label">{label}</div><div class="kpi-value">{value}</div><div class="kpi-note">{note}</div></div>'

def rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1/period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(df, period=14):
    prev = df['Close'].shift(1)
    tr = pd.concat([
        df['High'] - df['Low'],
        (df['High'] - prev).abs(),
        (df['Low'] - prev).abs()
    ], axis=1).max(axis=1)
    return tr.ewm(alpha=1/period, adjust=False, min_periods=period).mean()

def add_indicators(raw):
    d = raw.copy()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    for c in ['Open','High','Low','Close','Volume']:
        if c not in d.columns: d[c] = np.nan
    d = d[~d.index.duplicated(keep='last')].sort_index()
    d['MA20'] = d['Close'].rolling(20).mean()
    d['MA50'] = d['Close'].rolling(50).mean()
    d['MA200'] = d['Close'].rolling(200).mean()
    d['EMA21'] = d['Close'].ewm(span=21, adjust=False).mean()
    d['RSI14'] = rsi(d['Close'])
    d['ATR14'] = atr(d)
    d['VolMA20'] = d['Volume'].rolling(20).mean()
    d['VolRatio'] = d['Volume'] / d['VolMA20'].replace(0, np.nan)
    d['High20'] = d['High'].rolling(20).max().shift(1)
    d['Low20'] = d['Low'].rolling(20).min().shift(1)
    d['High55'] = d['High'].rolling(55).max().shift(1)
    d['Low55'] = d['Low'].rolling(55).min().shift(1)
    ema12 = d['Close'].ewm(span=12, adjust=False).mean()
    ema26 = d['Close'].ewm(span=26, adjust=False).mean()
    d['MACD'] = ema12 - ema26
    d['MACDSignal'] = d['MACD'].ewm(span=9, adjust=False).mean()
    d['MACDHist'] = d['MACD'] - d['MACDSignal']
    d['ROC20'] = d['Close'].pct_change(20) * 100
    d['ROC60'] = d['Close'].pct_change(60) * 100
    return d.dropna(subset=['Close'])

@st.cache_data(ttl=900, show_spinner=False)
def download_history(code):
    if yf is None: return pd.DataFrame()
    try:
        raw = yf.download(ticker_symbol(code), period='2y', interval='1d', auto_adjust=False, progress=False, threads=False)
        if raw is None or raw.empty: return pd.DataFrame()
        return add_indicators(raw)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def download_benchmark():
    if yf is None: return pd.DataFrame()
    try:
        raw = yf.download('^JKSE', period='2y', interval='1d', auto_adjust=False, progress=False, threads=False)
        if raw is None or raw.empty: return pd.DataFrame()
        return add_indicators(raw)
    except Exception:
        return pd.DataFrame()

def period_return(hist, bars):
    if hist.empty or len(hist) <= bars: return np.nan
    return (hist['Close'].iloc[-1] / hist['Close'].iloc[-(bars+1)] - 1) * 100

def market_regime(bench):
    if bench.empty: return {'regime':'UNKNOWN','score':50,'note':'Data IHSG belum tersedia'}
    x = bench.iloc[-1]
    score = 50
    if pd.notna(x.MA50) and x.Close > x.MA50: score += 15
    else: score -= 15
    if pd.notna(x.MA200) and x.MA50 > x.MA200: score += 15
    else: score -= 15
    if pd.notna(x.RSI14) and x.RSI14 >= 50: score += 10
    else: score -= 10
    if pd.notna(x.ROC20) and x.ROC20 > 0: score += 10
    else: score -= 10
    score = int(max(0, min(100, score)))
    regime = 'BULLISH' if score >= 65 else 'BEARISH' if score <= 35 else 'SIDEWAYS'
    return {'regime':regime, 'score':score, 'note':f"IHSG {fmt_price(x.Close)} · RSI {fmt_num(x.RSI14,1)} · ROC20 {fmt_pct(x.ROC20,1)}"}

def score_stock(hist, bench, bars):
    if hist.empty: return {}
    x = hist.iloc[-1]
    score = 0
    reasons, risks = [], []
    # Trend: 35
    if pd.notna(x.MA20) and x.Close > x.MA20: score += 8
    else: risks.append('Harga di bawah MA20')
    if pd.notna(x.MA50) and x.Close > x.MA50: score += 10
    else: risks.append('Harga di bawah MA50')
    if pd.notna(x.MA200) and x.Close > x.MA200: score += 9
    else: risks.append('Harga di bawah MA200')
    if pd.notna(x.MA20) and pd.notna(x.MA50) and x.MA20 > x.MA50: score += 8
    else: risks.append('MA20 belum di atas MA50')
    # Momentum: 25
    if pd.notna(x.RSI14) and 50 <= x.RSI14 <= 70:
        score += 10; reasons.append('RSI berada di zona momentum sehat')
    elif pd.notna(x.RSI14) and x.RSI14 > 70:
        score += 4; risks.append('RSI relatif overbought')
    else: risks.append('RSI lemah atau belum tersedia')
    if pd.notna(x.MACD) and pd.notna(x.MACDSignal) and x.MACD > x.MACDSignal:
        score += 8; reasons.append('MACD bullish')
    else: risks.append('MACD belum bullish')
    roc = period_return(hist, bars)
    if pd.notna(roc) and roc > 0:
        score += 7; reasons.append(f'Return {bars} hari positif')
    else: risks.append(f'Return {bars} hari belum positif')
    # Setup and volume: 20
    if pd.notna(x.VolRatio) and x.VolRatio >= 1.2:
        score += 8; reasons.append('Volume di atas rata-rata 20 hari')
    if pd.notna(x.High20) and x.Close > x.High20:
        score += 7; reasons.append('Breakout high 20 hari')
    elif pd.notna(x.High55) and x.Close > x.High55:
        score += 5; reasons.append('Breakout high 55 hari')
    if pd.notna(x.EMA21) and x.Close > x.EMA21: score += 5
    # Relative strength: 10
    rs = np.nan
    if not bench.empty and len(hist) > bars and len(bench) > bars:
        stock_ret = period_return(hist, bars)
        bench_ret = period_return(bench, bars)
        rs = stock_ret - bench_ret if pd.notna(stock_ret) and pd.notna(bench_ret) else np.nan
        if pd.notna(rs) and rs > 0:
            score += 10; reasons.append(f'Mengungguli IHSG pada periode {bars} hari')
        elif pd.notna(rs):
            risks.append('Relative strength di bawah IHSG')
    score = int(max(0, min(100, score)))
    trend = 'BULLISH' if pd.notna(x.MA50) and pd.notna(x.MA20) and x.Close > x.MA50 and x.MA20 > x.MA50 else 'BEARISH' if pd.notna(x.MA50) and pd.notna(x.MA20) and x.Close < x.MA50 and x.MA20 < x.MA50 else 'SIDEWAYS'
    if score >= 78 and trend == 'BULLISH' and len(risks) <= 2: signal = 'STRONG BUY'
    elif score >= 65 and trend != 'BEARISH': signal = 'BUY'
    elif score >= 50: signal = 'WATCH'
    elif score < 35: signal = 'AVOID'
    else: signal = 'NEUTRAL'
    gate = 'PASS' if signal in ('BUY','STRONG BUY') and trend != 'BEARISH' and pd.notna(x.RSI14) and x.RSI14 < 75 and pd.notna(x.VolRatio) and x.VolRatio >= 0.7 else 'CAUTION'
    atrv = safe_float(x.ATR14)
    if not pd.notna(atrv) or atrv <= 0: atrv = safe_float(x.Close) * 0.03
    support = min([v for v in [x.Low20, x.MA20, x.MA50] if pd.notna(v)], default=x.Close - 2*atrv)
    resistance = max([v for v in [x.High20, x.High55] if pd.notna(v)], default=x.Close + 2*atrv)
    entry_low = max(support, x.Close - 0.5*atrv)
    stop = max(0.01, x.Close - 1.5*atrv)
    target1 = x.Close + 2*atrv
    target2 = x.Close + 3*atrv
    rr = (target1 - x.Close) / (x.Close - stop) if x.Close > stop else np.nan
    return {
        'Score':score, 'Signal':signal, 'RiskGate':gate, 'Trend':trend,
        'Price':safe_float(x.Close), 'RSI':safe_float(x.RSI14), 'MACDHist':safe_float(x.MACDHist),
        'VolRatio':safe_float(x.VolRatio), 'ROCPeriod':roc, 'ROC20':safe_float(x.ROC20),
        'ROC60':safe_float(x.ROC60), 'RSPeriod':rs, 'ATR':atrv,
        'Support':safe_float(support), 'Resistance':safe_float(resistance), 'EntryLow':safe_float(entry_low),
        'StopLoss':safe_float(stop), 'Target1':safe_float(target1), 'Target2':safe_float(target2), 'RR':safe_float(rr),
        'Reasons':reasons, 'Risks':risks, 'LastDate':hist.index[-1]
    }

def analyze(code, bench, bars):
    hist = download_history(code)
    return hist, score_stock(hist, bench, bars) if not hist.empty else {}

def style_action(row, style):
    # Focus-aware, rule-based style classification.
    signal, gate, trend = row.get('Signal'), row.get('RiskGate'), row.get('Trend')
    rr = safe_float(row.get('RR'))
    vol = safe_float(row.get('VolRatio'))
    score = safe_float(row.get('Score'))
    if style == 'Trading Harian':
        eligible = signal in ('BUY','STRONG BUY') and gate == 'PASS' and trend == 'BULLISH' and pd.notna(vol) and vol >= 1.0
        setup = 'Breakout + volume' if row.get('Breakout') == 'YA' else 'Momentum intraday'
        horizon = '1–5 hari'
    elif style == 'Swing Trading Mingguan':
        eligible = signal in ('BUY','STRONG BUY') and gate == 'PASS' and trend == 'BULLISH' and pd.notna(rr) and rr >= 1.5
        setup = 'Pullback MA20 / continuation'
        horizon = '1–8 minggu'
    else:
        eligible = trend == 'BULLISH' and score >= 60 and row.get('ROC60', 0) > 0
        setup = 'Trend following / akumulasi bertahap'
        horizon = '6 bulan+'
    return eligible, setup, horizon

def card_stock(r, compact=False):
    code = r.get('Code','-')
    signal = r.get('Signal','-')
    gate = r.get('RiskGate','-')
    title = f"{code} <span style='float:right'>{badge(signal)}</span>"
    extra = '' if compact else f"<div class='card-sub'>Risk Gate {badge(gate)} · Trend {badge(r.get('Trend','-'))}</div>"
    return f'''<div class="card"><div class="card-title">{title}</div>
    <div class="card-sub">{r.get('Name','Saham IDX')} · {r.get('Sector','Universe IDX')}</div>
    {extra}<hr>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">
      <div><div class="card-sub">Harga</div><b>{fmt_price(r.get('Price'))}</b></div>
      <div><div class="card-sub">Score</div><b>{fmt_num(r.get('Score'),0)}</b></div>
      <div><div class="card-sub">RSI</div><b>{fmt_num(r.get('RSI'),1)}</b></div>
      <div><div class="card-sub">R:R</div><b>{fmt_num(r.get('RR'),2)}</b></div>
    </div><hr>
    <div class="card-sub">Return periode {fmt_pct(r.get('ROCPeriod'),1)} · RS vs IHSG {fmt_pct(r.get('RSPeriod'),1)} · Volume {fmt_num(r.get('VolRatio'),2)}x</div>
    <div class="card-sub">Support {fmt_price(r.get('Support'))} · Stop {fmt_price(r.get('StopLoss'))} · Target 1 {fmt_price(r.get('Target1'))}</div>
    </div>'''

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown('## ⚙️ Pengaturan')
mode = st.sidebar.radio('Mode analisis', ['🔎 1 Saham','🌐 Scanner Universe'], index=0)
period_label = st.sidebar.selectbox('Periode historis', list(PERIODS.keys()), index=0)
bars = PERIODS[period_label]
benchmark_on = st.sidebar.checkbox('Bandingkan dengan IHSG', True)
show_debug = st.sidebar.checkbox('Tampilkan data teknikal mentah', False)

st.sidebar.markdown('---')
st.sidebar.markdown('### Universe Scanner')
universe_text = st.sidebar.text_area('Kode saham (koma/baris)', DEFAULT_UNIVERSE, height=170)
universe = []
for token in universe_text.replace('\n', ',').split(','):
    c = token.strip().upper().replace('.JK','')
    if c and c not in universe: universe.append(c)
max_scan = st.sidebar.slider('Maksimum saham dipindai', 5, min(150, max(5, len(universe))), min(50, len(universe)))
min_score = st.sidebar.slider('Minimum technical score', 0, 100, 60)

# -----------------------------
# Header and shared market data
# -----------------------------
st.markdown('''<div class="card"><div class="card-title">📈 Sanggul Stock Scanner <span style="float:right">V10 Professional</span></div><div class="card-sub">Multi-period technical screening · Risk-Gated picks · Multi-Style Action Board · Enrich Top 50 Focus-Aware. Alat bantu keputusan, bukan jaminan keuntungan.</div></div>''', unsafe_allow_html=True)
bench = download_benchmark() if benchmark_on else pd.DataFrame()
reg = market_regime(bench)

# -----------------------------
# Individual mode
# -----------------------------
if mode == '🔎 1 Saham':
    st.markdown('### 🔎 Analisis 1 Saham')
    c1, c2, c3 = st.columns([2,1,1])
    with c1:
        code = st.text_input('Kode saham IDX', value='BBRI').upper().replace('.JK','')
    with c2:
        st.write('')
        run = st.button('📊 Analisis Saham', type='primary', use_container_width=True)
    with c3:
        st.write('')
        st.markdown(f"**Market Regime**<br>{badge(reg['regime'])} · {reg['score']}/100", unsafe_allow_html=True)
    if 'single_code' not in st.session_state: st.session_state.single_code = 'BBRI'
    if run or code != st.session_state.single_code: st.session_state.single_code = code
    code = st.session_state.single_code
    hist, a = analyze(code, bench, bars)
    if hist.empty or not a:
        st.error('Data tidak tersedia. Periksa kode, koneksi internet, atau batasan Yahoo Finance.')
    else:
        row = {'Code':code, **a}
        st.markdown(f"<div class='card'><div class='card-title'>{code} <span style='float:right'>{badge(a['Signal'])}</span></div><div class='card-sub'>Data terakhir {pd.Timestamp(a['LastDate']).strftime('%d %b %Y')} · Risk Gate {badge(a['RiskGate'])} · Periode {period_label}</div></div>", unsafe_allow_html=True)
        cols = st.columns(6)
        vals = [('Harga',fmt_price(a['Price']),a['Trend']),('Score',f"{a['Score']}/100",'Composite teknikal'),('RSI',fmt_num(a['RSI'],1),'RSI 14'),('Volume',fmt_num(a['VolRatio'],2)+'x','vs MA20'),('Return',fmt_pct(a['ROCPeriod'],1),period_label),('R:R',fmt_num(a['RR'],2),'Target 1 vs stop')]
        for col, (lab,val,note) in zip(cols, vals): col.markdown(kpi(lab,val,note), unsafe_allow_html=True)
        tabs = st.tabs(['📈 Chart & Trend','🎯 Action Plan','🧩 Indikator','📝 Interpretasi'])
        with tabs[0]:
            if go is None:
                st.info('Plotly belum tersedia. Install requirements.txt terlebih dahulu.')
            else:
                tail = hist.tail(220)
                fig = go.Figure()
                fig.add_trace(go.Candlestick(x=tail.index, open=tail.Open, high=tail.High, low=tail.Low, close=tail.Close, name='Harga'))
                for col in ['MA20','MA50','MA200']:
                    if col in tail and tail[col].notna().any(): fig.add_trace(go.Scatter(x=tail.index, y=tail[col], mode='lines', name=col))
                fig.update_layout(height=510, xaxis_rangeslider_visible=False, margin=dict(l=10,r=10,t=20,b=10), legend=dict(orientation='h'))
                st.plotly_chart(fig, use_container_width=True)
                st.caption('MA20 membantu membaca momentum pendek, MA50 tren menengah, dan MA200 tren mayor. Chart menggunakan data historis 2 tahun lalu ditampilkan pada jendela terbaru.')
        with tabs[1]:
            st.markdown('#### Rencana aksi berbasis ATR dan struktur harga')
            ap = st.columns(5)
            vals = [('Area entry',f"{fmt_price(a['EntryLow'])} – {fmt_price(a['Price'])}"),('Support',fmt_price(a['Support'])),('Stop loss',fmt_price(a['StopLoss'])),('Target 1',fmt_price(a['Target1'])),('Target 2',fmt_price(a['Target2']))]
            for col,(lab,val) in zip(ap,vals): col.markdown(kpi(lab,val,'Estimasi teknikal'),unsafe_allow_html=True)
            st.warning('Level entry, stop, dan target adalah estimasi rule-based. Validasi dengan spread, likuiditas, berita, corporate action, dan toleransi risiko pribadi.')
        with tabs[2]:
            ind = pd.DataFrame({'Indikator':['MA20','MA50','MA200','EMA21','RSI14','MACD Histogram','ATR14','Volume Ratio','Return periode','ROC20','ROC60','Relative Strength vs IHSG'], 'Nilai':[safe_float(hist.MA20.iloc[-1]),safe_float(hist.MA50.iloc[-1]),safe_float(hist.MA200.iloc[-1]),safe_float(hist.EMA21.iloc[-1]),a['RSI'],a['MACDHist'],a['ATR'],a['VolRatio'],a['ROCPeriod'],a['ROC20'],a['ROC60'],a['RSPeriod']]})
            st.dataframe(ind, hide_index=True, use_container_width=True)
        with tabs[3]:
            left,right = st.columns(2)
            with left:
                st.markdown('#### Faktor pendukung')
                for item in a['Reasons'] or ['Belum ada faktor pendukung kuat.']: st.success('✓ '+item)
            with right:
                st.markdown('#### Risiko / perhatian')
                for item in a['Risks'] or ['Tidak ada risiko teknikal utama pada rule set ini.']: st.warning('! '+item)
            st.markdown(f"**Kesimpulan sistem:** {code} berada pada tren **{a['Trend']}**, score **{a['Score']}/100**, signal **{a['Signal']}**, dan Risk Gate **{a['RiskGate']}** untuk periode **{period_label}**.")
        if show_debug: st.dataframe(hist.tail(60), use_container_width=True)

# -----------------------------
# Scanner mode
# -----------------------------
else:
    st.markdown('### 🌐 Scanner & Ranking')
    st.markdown(f"<div class='card'><div class='card-title'>Market Regime: {badge(reg['regime'])} <span style='float:right'>{reg['score']}/100</span></div><div class='card-sub'>{reg['note']} · Periode ranking: {period_label} · Risk Gate dipisahkan dari score.</div></div>", unsafe_allow_html=True)
    if st.button(f'🚀 Scan {max_scan} saham sekarang', type='primary'):
        rows, failures = [], []
        selected = universe[:max_scan]
        progress = st.progress(0)
        status = st.empty()
        for i, c in enumerate(selected, 1):
            status.write(f'Menganalisis {c} ({i}/{len(selected)})...')
            hist, a = analyze(c, bench, bars)
            if a:
                row = {'Code':c, **{k:v for k,v in a.items() if k not in ('Reasons','Risks','LastDate','ATR','MACDHist')}}
                row['Breakout'] = 'YA' if (not hist.empty and pd.notna(hist.High20.iloc[-1]) and hist.Close.iloc[-1] > hist.High20.iloc[-1]) else 'TIDAK'
                rows.append(row)
            else: failures.append(c)
            progress.progress(i/len(selected))
        status.empty(); progress.empty()
        st.session_state.scan_rows = rows
        st.session_state.scan_failures = failures
        st.session_state.scan_period = period_label
    rows = st.session_state.get('scan_rows', [])
    if rows:
        df = pd.DataFrame(rows)
        filtered = df[df['Score'] >= min_score].copy()
        filtered = filtered.sort_values(['RiskGate','Score','RR'], ascending=[True,False,False])
        st.markdown('### Ringkasan Scanner')
        c = st.columns(6)
        metrics = [('Dipindai',len(df),'Universe terpilih'),('Lolos filter',len(filtered),f'Score ≥ {min_score}'),('Top Gate Pass',int((df.RiskGate=='PASS').sum()),'Risk-gated'),('Strong Buy',int((df.Signal=='STRONG BUY').sum()),'Signal prioritas'),('Avg Score',fmt_num(df.Score.mean(),1),'Rata-rata'),('Periode',period_label,'Data historis')]
        for col,(lab,val,note) in zip(c,metrics): col.markdown(kpi(lab,val,note),unsafe_allow_html=True)

        # Top 3 risk-gated picks
        st.markdown('### 🏆 Top 3 Actionable Picks — Risk-Gated')
        gate = filtered[(filtered.RiskGate=='PASS') & (filtered.Signal.isin(['BUY','STRONG BUY'])) & (filtered.Trend=='BULLISH')].copy()
        top3 = gate.sort_values(['Score','RR','VolRatio'], ascending=[False,False,False]).head(3)
        if top3.empty: st.info('Belum ada saham yang memenuhi seluruh syarat Risk Gate pada periode ini.')
        else:
            cols = st.columns(3)
            for col,(_,r) in zip(cols, top3.iterrows()):
                with col: st.markdown(card_stock(r.to_dict()), unsafe_allow_html=True)

        # Multi-style board
        st.markdown('### 🎯 Multi-Style Action Board')
        styles = ['Trading Harian','Swing Trading Mingguan','Investor Jangka Panjang']
        board_cols = st.columns(3)
        for col, style in zip(board_cols, styles):
            eligible_rows = []
            for _, r in filtered.iterrows():
                ok, setup, horizon = style_action(r.to_dict(), style)
                if ok:
                    rr = r.to_dict(); rr['Setup'] = setup; rr['Horizon'] = horizon; eligible_rows.append(rr)
            eligible_rows = sorted(eligible_rows, key=lambda x:(x.get('Score',0), x.get('RR',0) if pd.notna(x.get('RR')) else 0), reverse=True)[:3]
            with col:
                st.markdown(f"<div class='card'><div class='card-title'>{'⚡' if style=='Trading Harian' else '📊' if style=='Swing Trading Mingguan' else '🌱'} {style}</div><div class='card-sub'>Fokus: {('1–5 hari' if style=='Trading Harian' else '1–8 minggu' if style=='Swing Trading Mingguan' else '6 bulan+')}</div></div>", unsafe_allow_html=True)
                if not eligible_rows:
                    st.info('Belum ada kandidat yang memenuhi filter gaya ini.')
                else:
                    for r in eligible_rows:
                        st.markdown(f"<div class='card'><div class='card-title'>{r['Code']} <span style='float:right'>{badge(r['Signal'])}</span></div><div class='card-sub'>{r.get('Setup','-')} · Gate {r['RiskGate']}</div><div style='margin-top:8px'><b>{fmt_price(r['Price'])}</b> · Score {fmt_num(r['Score'],0)} · R:R {fmt_num(r['RR'],2)}</div><div class='card-sub'>Stop {fmt_price(r['StopLoss'])} · Target {fmt_price(r['Target1'])}</div></div>", unsafe_allow_html=True)

        # Enrich Top 50
        st.markdown('### 🧠 Enrich Top 50 — Focus-Aware Multi-Style')
        st.caption('Top 50 diperkaya dengan return 1M, 3M, 6M, 2Y, relative strength, style eligibility, dan risk-gated status. Nilai return dihitung dari histori 2 tahun.')
        enrich = filtered.sort_values(['Score','RR'], ascending=[False,False]).head(50).copy()
        if not enrich.empty:
            # Calculate all requested period returns for each top 50 code.
            progress = st.progress(0)
            enrich_rows = []
            for i, (_, base) in enumerate(enrich.iterrows(), 1):
                h = download_history(base.Code)
                item = base.to_dict()
                for label, n in PERIODS.items(): item[label] = period_return(h, n)
                # Focus-aware style flags based on current selected-period score/gate.
                for style in styles:
                    ok, _, _ = style_action(item, style)
                    item[style] = 'READY' if ok else '—'
                enrich_rows.append(item)
                progress.progress(i/len(enrich))
            progress.empty()
            edf = pd.DataFrame(enrich_rows)
            st.dataframe(edf[['Code','Price','1 Bulan','3 Bulan','6 Bulan','2 Tahun','Score','Trend','Signal','RiskGate','VolRatio','RR','Trading Harian','Swing Trading Mingguan','Investor Jangka Panjang']], hide_index=True, use_container_width=True)
            st.download_button('⬇️ Download Enrich Top 50 CSV', edf.to_csv(index=False).encode('utf-8'), 'sanggul_enrich_top50_focus_aware.csv', 'text/csv')
        st.markdown('### 📋 Ranking Detail')
        st.dataframe(filtered, hide_index=True, use_container_width=True)
        st.download_button('⬇️ Download hasil scanner CSV', filtered.to_csv(index=False).encode('utf-8'), 'sanggul_scanner_results.csv', 'text/csv')
        if st.session_state.get('scan_failures'): st.caption('Data tidak tersedia: '+', '.join(st.session_state.scan_failures))
    else:
        st.info('Atur universe, periode, dan klik tombol Scan untuk memulai. Untuk analisis mendalam satu saham, gunakan mode 🔎 1 Saham.')

st.markdown('---')
st.caption('Sanggul Stock Scanner V10 Professional · Rule-based decision support · Data Yahoo Finance dapat terlambat, berubah, atau gagal diakses. Bukan nasihat investasi.')
