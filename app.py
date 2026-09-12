import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from io import BytesIO

st.set_page_config(page_title='Sanggul Stock Scanner V8', page_icon='📈', layout='wide')

IDX_UNIVERSE_URL = 'https://huggingface.co/datasets/kjhq/Indonesia-Stock-Symbols-and-Metadata/resolve/main/indonesia.csv'

# ============================================================
# HELPERS
# ============================================================
def yahoo_symbol(kode):
    kode = str(kode).upper().strip()
    return kode if kode.endswith('.JK') else kode + '.JK'

def safe_num(x, default=np.nan):
    try:
        return float(x)
    except Exception:
        return default

def fmt_num(x, n=2):
    if pd.isna(x): return '-'
    return f'{x:,.{n}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def period_to_days(label):
    return {'1 Bulan': 21, '3 Bulan': 63, '6 Bulan': 126, '12 Bulan': 252}[label]

# ============================================================
# DATA SOURCE
# ============================================================
@st.cache_data(ttl=86400)
def load_idx_universe():
    try:
        df = pd.read_csv(IDX_UNIVERSE_URL)
        df.columns = [str(c).lower().strip() for c in df.columns]
        if not {'ticker','name','sector'}.issubset(df.columns):
            return pd.DataFrame()
        if 'market' in df.columns:
            df = df[df['market'].astype(str).str.upper().eq('IDX')].copy()
        df['ticker'] = (df['ticker'].astype(str).str.upper().str.strip()
                        .str.replace('.JK','', regex=False))
        df = df[df['ticker'].str.fullmatch(r'[A-Z]{4}', na=False)].drop_duplicates('ticker')
        df['Yahoo'] = df['ticker'] + '.JK'
        return df.sort_values('ticker').reset_index(drop=True)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def download_batch(tickers, period='2y'):
    if not tickers: return pd.DataFrame()
    try:
        return yf.download(
            tickers=list(tickers), period=period, interval='1d', auto_adjust=True,
            progress=False, threads=True, group_by='ticker', multi_level_index=True
        )
    except Exception:
        return pd.DataFrame()

def extract_ticker_data(batch, ticker):
    if batch is None or batch.empty: return pd.DataFrame()
    try:
        if isinstance(batch.columns, pd.MultiIndex):
            if ticker in batch.columns.get_level_values(0):
                d = batch[ticker].copy()
            elif ticker in batch.columns.get_level_values(1):
                d = batch.xs(ticker, axis=1, level=1).copy()
            else:
                return pd.DataFrame()
        else:
            d = batch.copy()
        d.columns = [str(c).title() for c in d.columns]
        for c in ['Open','High','Low','Close','Volume']:
            if c in d.columns: d[c] = pd.to_numeric(d[c], errors='coerce')
        needed = ['Open','High','Low','Close']
        return d.dropna(subset=[c for c in needed if c in d.columns])
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=900, show_spinner=False)
def download_single(kode, period='2y'):
    try:
        d = yf.download(yahoo_symbol(kode), period=period, interval='1d', auto_adjust=True,
                        progress=False, threads=False)
        if d.empty: return pd.DataFrame()
        if isinstance(d.columns, pd.MultiIndex): d.columns = d.columns.get_level_values(0)
        d.columns = [str(c).title() for c in d.columns]
        for c in ['Open','High','Low','Close','Volume']:
            if c in d.columns: d[c] = pd.to_numeric(d[c], errors='coerce')
        return d.dropna(subset=['Open','High','Low','Close'])
    except Exception:
        return pd.DataFrame()

# ============================================================
# TECHNICAL ENGINE
# ============================================================
def add_indicators(df):
    x = df.copy().sort_index()
    c, h, l, v = x['Close'], x['High'], x['Low'], x['Volume']
    x['MA20'] = c.rolling(20).mean()
    x['MA50'] = c.rolling(50).mean()
    x['MA200'] = c.rolling(200).mean()
    delta = c.diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x['RSI'] = 100 - (100 / (1 + rs))
    ema12, ema26 = c.ewm(span=12, adjust=False).mean(), c.ewm(span=26, adjust=False).mean()
    x['MACD'] = ema12 - ema26
    x['MACDSignal'] = x['MACD'].ewm(span=9, adjust=False).mean()
    prev = c.shift(1)
    tr = pd.concat([(h-l), (h-prev).abs(), (l-prev).abs()], axis=1).max(axis=1)
    x['ATR14'] = tr.rolling(14).mean()
    x['VolMA20'] = v.rolling(20).mean()
    x['VolumeRatio'] = v / x['VolMA20'].replace(0, np.nan)
    x['Support20'] = l.rolling(20).min()
    x['Resistance20'] = h.rolling(20).max()
    x['Support60'] = l.rolling(60).min()
    x['Resistance60'] = h.rolling(60).max()
    x['Return5D'] = c.pct_change(5) * 100
    x['Return20D'] = c.pct_change(20) * 100
    x['Return60D'] = c.pct_change(60) * 100
    x['OBV'] = (np.sign(c.diff()).fillna(0) * v.fillna(0)).cumsum()
    x['OBV20Change'] = x['OBV'].pct_change(20) * 100
    return x

def analyze_period(df, focus_days=63):
    if df.empty or len(df) < 210: return None
    x = add_indicators(df)
    valid = x.dropna(subset=['MA20','MA50','MA200','RSI','MACD','MACDSignal','ATR14'])
    if valid.empty: return None
    latest = valid.iloc[-1]
    recent = x.tail(focus_days).copy()
    recent_valid = recent.dropna(subset=['Close'])
    if len(recent_valid) < min(20, focus_days): return None
    px = safe_num(latest['Close'])
    ma20, ma50, ma200 = safe_num(latest['MA20']), safe_num(latest['MA50']), safe_num(latest['MA200'])
    rsi, macd, macds = safe_num(latest['RSI']), safe_num(latest['MACD']), safe_num(latest['MACDSignal'])
    vr, atr = safe_num(latest['VolumeRatio']), safe_num(latest['ATR14'])
    ret_focus = safe_num(px / recent_valid['Close'].iloc[0] - 1) * 100
    high_focus = safe_num(recent_valid['High'].max())
    low_focus = safe_num(recent_valid['Low'].min())
    range_pos = (px-low_focus)/(high_focus-low_focus)*100 if high_focus > low_focus else 50
    res20, sup20 = safe_num(latest['Resistance20']), safe_num(latest['Support20'])
    res60, sup60 = safe_num(latest['Resistance60']), safe_num(latest['Support60'])
    resistances = [r for r in [res20,res60] if not pd.isna(r) and r > px]
    supports = [s for s in [sup20,sup60] if not pd.isna(s) and s < px]
    resistance = min(resistances) if resistances else max(res20,res60)
    support = max(supports) if supports else min(sup20,sup60)
    prev_res = x['Resistance20'].shift(1).iloc[-1]
    breakout = bool(pd.notna(prev_res) and px > float(prev_res) and vr >= 1.2)
    pullback = bool(px >= ma50 and px <= ma20*1.04 and macd >= macds*0.97 and ret_focus > 0)
    trend_score = 0
    trend_score += 20 if px > ma20 else 0
    trend_score += 20 if px > ma50 else 0
    trend_score += 20 if px > ma200 else 0
    trend_score += 20 if ma20 > ma50 > ma200 else 0
    trend_score += 20 if ret_focus > 0 else 0
    momentum_score = 0
    momentum_score += 25 if safe_num(latest['Return20D']) > 0 else 0
    momentum_score += 25 if safe_num(latest['Return60D']) > 0 else 0
    momentum_score += 20 if 50 <= rsi <= 70 else (10 if 40 <= rsi < 50 or 70 < rsi <= 75 else 0)
    momentum_score += 15 if macd > macds else 0
    momentum_score += 15 if vr >= 1.1 else 0
    setup = 'BREAKOUT' if breakout else 'PULLBACK' if pullback else 'BASE/NEUTRAL'
    setup_score = 100 if breakout else 88 if pullback else 55
    rr_risk = max(1.25*atr, px*0.02)
    stop = px - rr_risk
    reward = max(resistance-px, atr)
    rr = reward/rr_risk if rr_risk > 0 else 0
    risk_score = min(max(rr/2.5,0),1)*100
    technical = round(0.45*trend_score + 0.35*momentum_score + 0.20*setup_score, 1)
    opportunity = round(0.65*technical + 0.20*risk_score + 0.15*min(max(vr/2,0),1)*100, 1)
    if breakout and technical >= 70: signal = 'BUY ON BREAKOUT'
    elif pullback and technical >= 65: signal = 'BUY ON PULLBACK'
    elif technical >= 78 and rr >= 1.5: signal = 'BUY'
    elif technical < 45: signal = 'AVOID'
    else: signal = 'WAIT'
    trend = 'BULLISH' if trend_score >= 65 else 'NEUTRAL' if trend_score >= 45 else 'BEARISH'
    return {
        'Price': px, 'TechnicalScore': technical, 'Opportunity': opportunity,
        'Trend': trend, 'Signal': signal, 'Setup': setup, 'RSI': rsi,
        'VolumeRatio': vr, 'R:R': rr, 'Support': support, 'Resistance': resistance,
        'StopLoss': stop, 'Target1': px + rr_risk*1.5, 'Target2': px + rr_risk*2.5,
        'Breakout': 'YA' if breakout else 'TIDAK', 'FocusReturnPct': ret_focus,
        'FocusHigh': high_focus, 'FocusLow': low_focus, 'RangePositionPct': range_pos,
        'Return5D': safe_num(latest['Return5D']), 'Return20D': safe_num(latest['Return20D']),
        'Return60D': safe_num(latest['Return60D']), 'MA20': ma20, 'MA50': ma50,
        'MA200': ma200, 'MACD': macd, 'MACDSignal': macds, 'ATR14': atr,
        'FocusDays': focus_days, 'DataDate': x.index[-1]
    }

# ============================================================
# FULL SCAN
# ============================================================
def scan_full_idx(universe, focus_days, batch_size=40, progress_callback=None):
    rows=[]
    tickers=universe['Yahoo'].tolist()
    total=int(np.ceil(len(tickers)/batch_size))
    for i in range(total):
        chunk=tickers[i*batch_size:(i+1)*batch_size]
        batch=download_batch(tuple(chunk), period='2y')
        for ticker in chunk:
            d=extract_ticker_data(batch,ticker)
            a=analyze_period(d,focus_days)
            if a is None: continue
            m=universe[universe['Yahoo'].eq(ticker)]
            if m.empty: continue
            meta=m.iloc[0]
            rows.append({'Kode':ticker.replace('.JK',''),'Nama':meta['name'],'Sektor':meta['sector'],**a})
        if progress_callback: progress_callback((i+1)/total)
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(['Opportunity','TechnicalScore','R:R'],ascending=False).reset_index(drop=True)

# ============================================================
# ENRICH ENGINE - EXPLICITLY RECOMPUTES FOCUS PERIOD
# ============================================================
def enrich_top150(base_df, focus_days, progress_callback=None):
    if base_df.empty: return pd.DataFrame()
    target=base_df.head(150).copy()
    rows=[]
    total=len(target)
    for idx, (_, r) in enumerate(target.iterrows(), start=1):
        d=download_single(r['Kode'], period='2y')
        a=analyze_period(d, focus_days)
        if a is None: continue
        # Optional lightweight fundamental enrichment; failures are tolerated.
        pe = pbv = roe = market_cap = np.nan
        try:
            info = yf.Ticker(yahoo_symbol(r['Kode'])).get_info()
            pe = safe_num(info.get('trailingPE'))
            pbv = safe_num(info.get('priceToBook'))
            roe = safe_num(info.get('returnOnEquity')) * 100 if info.get('returnOnEquity') is not None else np.nan
            market_cap = safe_num(info.get('marketCap'))
        except Exception:
            pass
        style_day = 0.55*a['Return5D'] + 0.25*a['VolumeRatio']*10 + 0.20*(100 if a['Breakout']=='YA' else 50)
        style_swing = 0.40*a['Return20D'] + 0.30*a['Return60D'] + 0.20*a['TechnicalScore'] + 0.10*(100 if a['Setup']=='PULLBACK' else 70 if a['Setup']=='BREAKOUT' else 40)
        fundamental_score = 50
        if not pd.isna(roe): fundamental_score += min(max(roe,0),30)
        if not pd.isna(pe) and pe > 0: fundamental_score += 10 if pe < 20 else 0
        if not pd.isna(pbv) and pbv > 0: fundamental_score += 10 if pbv < 3 else 0
        investor = 0.55*fundamental_score + 0.25*a['TechnicalScore'] + 0.20*min(max(a['Return60D']+50,0),100)
        row={**r.to_dict(), **a,
             'PER':pe,'PBV':pbv,'ROE_pct':roe,'MarketCap':market_cap,
             'DayScore':round(np.clip(style_day+50,0,100),1),
             'SwingScore':round(np.clip(style_swing+50,0,100),1),
             'InvestorScore':round(np.clip(investor,0,100),1),
             'Enriched':'YA','AnalysisNote':f'Recomputed with last {focus_days} trading days; 2y retained for MA200/context.'}
        row['RiskGate'] = 'PASS' if row['R:R'] >= 1.5 and row['Trend'] != 'BEARISH' and row['TechnicalScore'] >= 60 else 'BLOCK'
        row['TopPickEligible'] = row['RiskGate']=='PASS' and row['Signal'] in ['BUY','BUY ON PULLBACK','BUY ON BREAKOUT']
        rows.append(row)
        if progress_callback: progress_callback(idx/total)
    if not rows: return pd.DataFrame()
    return pd.DataFrame(rows)

# ============================================================
# UI
# ============================================================
st.title('📈 SANGGUL STOCK SCANNER IDX — V8')
st.caption('Multi-horizon: 2 tahun sebagai konteks, fokus 1/3/6/12 bulan untuk momentum, setup, dan entry.')

c1,c2,c3,c4=st.columns(4)
with c1:
    focus_label=st.selectbox('Fokus Analisis', ['1 Bulan','3 Bulan','6 Bulan','12 Bulan'], index=1)
focus_days=period_to_days(focus_label)
with c2: st.metric('Hari Perdagangan Fokus', f'±{focus_days} hari')
with c3: st.metric('Data Historis', '2 Tahun')
with c4: st.metric('Mode', 'Focus-Aware Enrich')
st.info(f'Periode fokus aktif: {focus_label} / ±{focus_days} hari perdagangan. Enrich akan menghitung ulang teknikal menggunakan periode fokus ini, bukan hanya menambahkan data.')

menu=st.radio('Menu',['🌐 Full IDX Scanner','🔎 Analisis Saham'],horizontal=True)

if menu=='🌐 Full IDX Scanner':
    universe=load_idx_universe()
    if universe.empty:
        st.error('Universe IDX gagal dimuat. Periksa koneksi internet.')
        st.stop()
    a,b,c=st.columns(3)
    a.metric('Universe IDX',f'{len(universe):,}'.replace(',','.'))
    b.metric('Periode Download','2 Tahun')
    c.metric('Batch','40 saham')
    if st.button('🚀 SCAN SELURUH IDX SEKARANG',width='stretch'):
        p=st.progress(0); status=st.empty()
        def cb(v): p.progress(v); status.info(f'Scanning: {v*100:.0f}%')
        with st.spinner('Mengambil data harga dan menghitung indikator...'):
            res=scan_full_idx(universe,focus_days,batch_size=40,progress_callback=cb)
        st.session_state['scan_result']=res
        st.session_state.pop('enriched_result',None)
        p.progress(1.0); status.success(f'Scan selesai: {len(res)} saham berhasil dianalisis.')
    result=st.session_state.get('scan_result',pd.DataFrame())
    if not result.empty:
        st.success(f'{len(result)} saham memiliki data teknikal yang cukup.')
        f1,f2,f3=st.columns(3)
        with f1:
            sectors=['Semua']+sorted(result['Sektor'].dropna().unique().tolist())
            sector=st.selectbox('Filter Sektor',sectors)
        with f2: min_score=st.slider('Minimum Technical Score',0,100,60,5)
        with f3: signal_filter=st.selectbox('Filter Signal',['Semua','BUY','WAIT','AVOID'])
        filtered=result.copy()
        if sector!='Semua': filtered=filtered[filtered['Sektor']==sector]
        filtered=filtered[filtered['TechnicalScore']>=min_score]
        if signal_filter!='Semua': filtered=filtered[filtered['Signal'].str.contains(signal_filter,case=False,na=False)]
        st.caption(f'Hasil setelah filter: {len(filtered)} saham')
        st.subheader('🏆 Top 10 Opportunity — Full IDX')
        cols=['Kode','Nama','Sektor','Price','TechnicalScore','Opportunity','Trend','Signal','Setup','RSI','VolumeRatio','R:R','Breakout','FocusReturnPct']
        st.dataframe(result.head(10)[cols],width='stretch',hide_index=True)
        st.subheader('🧩 Enrich Top 150 — Focus-Aware Technical + Fundamental')
        st.caption(f'Enrich mengambil maksimal 150 saham teratas, lalu menghitung ulang analisis teknikal dengan fokus {focus_label} (±{focus_days} hari). Data 2 tahun tetap dipakai untuk MA200 dan konteks.')
        if st.button('✨ ENRICH TOP 150 SEKARANG',width='stretch'):
            p2=st.progress(0); s2=st.empty()
            def cb2(v): p2.progress(v); s2.info(f'Enrich: {v*100:.0f}%')
            with st.spinner('Menghitung ulang fokus teknikal dan mengambil data fundamental...'):
                enriched=enrich_top150(result,focus_days,progress_callback=cb2)
            st.session_state['enriched_result']=enriched
            p2.progress(1.0); s2.success(f'Enrich selesai: {len(enriched)} saham.')
        enriched=st.session_state.get('enriched_result',pd.DataFrame())
        if not enriched.empty:
            st.success(f'ENRICH AKTIF — seluruh baris berikut dihitung ulang dengan fokus {focus_label} / {focus_days} hari.')
            st.subheader('📋 Enriched Top 150 — Ringkasan Transparan')
            ecols=['Kode','Nama','Sektor','Price','FocusDays','FocusReturnPct','Return20D','Return60D','Trend','Setup','TechnicalScore','Opportunity','Signal','RSI','VolumeRatio','R:R','RiskGate','PER','PBV','ROE_pct']
            st.dataframe(enriched[ecols].sort_values('Opportunity',ascending=False),width='stretch',hide_index=True)
            st.subheader('🥇 Top 3 Actionable Picks — Risk-Gated')
            top3=enriched[enriched['TopPickEligible']].sort_values(['SwingScore','R:R','Opportunity'],ascending=False).head(3)
            if top3.empty:
                st.warning('Belum ada saham yang lolos Risk Gate. Ini berarti sinyal belum memenuhi kombinasi tren, skor teknikal, dan R:R minimum.')
            else:
                st.dataframe(top3[['Kode','Nama','Sektor','Price','SwingScore','Signal','Setup','Trend','R:R','StopLoss','Target1','Target2','RiskGate']],width='stretch',hide_index=True)
            st.subheader('🎯 Multi-Style Action Board')
            st.caption('Ranking dipisahkan berdasarkan karakter strategi; saham boleh muncul di lebih dari satu gaya, tetapi urutan dan skornya berbeda.')
            day=enriched.sort_values(['DayScore','TechnicalScore'],ascending=False).head(5)
            swing=enriched.sort_values(['SwingScore','Opportunity'],ascending=False).head(5)
            investor=enriched.sort_values(['InvestorScore','ROE_pct','TechnicalScore'],ascending=False).head(5)
            q1,q2,q3=st.columns(3)
            with q1:
                st.markdown('#### ⚡ Trading Harian')
                st.dataframe(day[['Kode','DayScore','Signal','Setup','Trend','VolumeRatio','RSI']],width='stretch',hide_index=True)
            with q2:
                st.markdown('#### 📈 Swing Trading Mingguan')
                st.dataframe(swing[['Kode','SwingScore','Signal','Setup','Trend','Return20D','Return60D']],width='stretch',hide_index=True)
            with q3:
                st.markdown('#### 🏛️ Investor Jangka Panjang')
                st.dataframe(investor[['Kode','InvestorScore','PER','PBV','ROE_pct','Trend','RiskGate']],width='stretch',hide_index=True)
            st.subheader('📌 Detail Perencanaan Trade')
            selected=st.selectbox('Pilih saham dari hasil Enrich',enriched['Kode'].tolist())
            d=enriched[enriched['Kode']==selected].iloc[0]
            m1,m2,m3,m4=st.columns(4)
            m1.metric('Harga',fmt_num(d['Price'],0)); m2.metric('Stop Loss',fmt_num(d['StopLoss'],0)); m3.metric('Target 1',fmt_num(d['Target1'],0)); m4.metric('R:R',fmt_num(d['R:R'],2))
            st.info(f"Fokus {focus_label}: return {fmt_num(d['FocusReturnPct'],2)}%, setup {d['Setup']}, signal {d['Signal']}. Catatan: {d['AnalysisNote']}")
            csv=enriched.to_csv(index=False).encode('utf-8-sig')
            st.download_button('⬇️ Download Hasil Enrich CSV',csv,'enriched_top150.csv','text/csv')

else:
    st.header('🔎 Analisis Saham Individual')
    kode=st.text_input('Kode Saham IDX',value='BBRI').upper().strip()
    if st.button('Analisis Saham',width='stretch'):
        d=download_single(kode,'2y'); a=analyze_period(d,focus_days)
        if a is None: st.error('Data tidak cukup atau kode tidak tersedia di Yahoo Finance.')
        else:
            st.success(f'Analisis {kode} selesai dengan fokus {focus_label}.')
            st.dataframe(pd.DataFrame([a]),width='stretch',hide_index=True)
            x=add_indicators(d)
            fig=go.Figure()
            fig.add_trace(go.Candlestick(x=x.index,open=x['Open'],high=x['High'],low=x['Low'],close=x['Close'],name='Harga'))
            fig.add_trace(go.Scatter(x=x.index,y=x['MA20'],name='MA20'))
            fig.add_trace(go.Scatter(x=x.index,y=x['MA50'],name='MA50'))
            fig.add_trace(go.Scatter(x=x.index,y=x['MA200'],name='MA200'))
            fig.update_layout(height=600,xaxis_rangeslider_visible=False,title=f'{kode} — Data 2 Tahun, Fokus {focus_label}')
            st.plotly_chart(fig,width='stretch')
            st.subheader('Indikator Fokus Terbaru')
            st.dataframe(x.tail(focus_days)[['Close','MA20','MA50','MA200','RSI','MACD','MACDSignal','VolumeRatio','Return20D','Return60D']].tail(20),width='stretch')
