import io
import time
import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

warnings.filterwarnings('ignore')

st.set_page_config(page_title='Sanggul Stock Scanner V10.1', page_icon='📊', layout='wide', initial_sidebar_state='expanded')

st.markdown('''
<style>
:root { color-scheme: light; }
.block-container {max-width: 1450px; padding-top: 1rem; padding-bottom: 2rem;}
[data-testid="stMetric"] {background:#fff;border:1px solid #e5e7eb;padding:12px 14px;border-radius:14px;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.card {background:#fff;border:1px solid #e5e7eb;border-radius:16px;padding:16px 18px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,.035)}
.card h3 {margin:0 0 6px 0;font-size:1.08rem}.muted{color:#64748b;font-size:.86rem}.small{font-size:.82rem;color:#64748b}
.pill {display:inline-block;border-radius:999px;padding:4px 9px;font-size:.75rem;font-weight:700;margin-left:6px}
.green{background:#dcfce7;color:#166534}.yellow{background:#fef3c7;color:#92400e}.red{background:#fee2e2;color:#991b1b}.blue{background:#dbeafe;color:#1d4ed8}.gray{background:#f1f5f9;color:#475569}
</style>
''', unsafe_allow_html=True)

try:
    import yfinance as yf
except Exception:
    yf = None

DEFAULT_UNIVERSE = "BBCA,BBRI,BMRI,BBNI,TLKM,ASII,ICBP,INDF,UNVR,ANTM,MDKA,ADRO,PTBA,ITMG,MEDC,AKRA,AMMN,ERAA,JPFA,SMGR,INCO,PGAS,BRPT,KLBF,MIKA,CPIN,ACES,BUKA,GOTO,ARTO,BBTN,EXCL,ISAT,INKP,TKIM,ELSA,HRUM,PTRO,DEWA,DOID,TOBA,MYOR,WIIM,MAPA,MAPB,SCMA,MNCN,BSDE,CTRA,LPKR"

PERIODS = {'1 Bulan': 30, '3 Bulan': 90, '6 Bulan': 180, '2 Tahun': 730}

@st.cache_data(ttl=900, show_spinner=False)
def download_history(tickers, period='2y'):
    if yf is None:
        return {}
    result = {}
    for ticker in tickers:
        symbol = ticker.strip().upper() if ticker.strip().upper().startswith('^') else ticker.strip().upper() + '.JK'
        try:
            df = yf.download(symbol, period=period, interval='1d', auto_adjust=False, progress=False, threads=False)
            if df is None or df.empty:
                continue
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [c[0] for c in df.columns]
            df = df.rename(columns={c: c.title() for c in df.columns})
            needed = [c for c in ['Open','High','Low','Close','Volume'] if c in df.columns]
            df = df[needed].dropna(subset=['Close'])
            if len(df) >= 30:
                result[ticker] = df
        except Exception:
            continue
        time.sleep(0.03)
    return result

def rsi(s, n=14):
    delta = s.diff()
    up = delta.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    down = (-delta.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def atr(df, n=14):
    prev = df['Close'].shift(1)
    tr = pd.concat([(df['High']-df['Low']), (df['High']-prev).abs(), (df['Low']-prev).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()

def safe_num(x, default=np.nan):
    try:
        return float(x)
    except Exception:
        return default

def calc_metrics(ticker, df, ihsg):
    c = df['Close'].astype(float)
    last = safe_num(c.iloc[-1])
    ma20 = c.rolling(20).mean().iloc[-1]
    ma50 = c.rolling(50).mean().iloc[-1]
    ma200 = c.rolling(200).mean().iloc[-1] if len(c) >= 200 else np.nan
    ema21 = c.ewm(span=21, adjust=False).mean().iloc[-1]
    r = safe_num(rsi(c).iloc[-1])
    macd = c.ewm(span=12, adjust=False).mean() - c.ewm(span=26, adjust=False).mean()
    signal = macd.ewm(span=9, adjust=False).mean()
    hist = safe_num((macd-signal).iloc[-1])
    vol_ma = df['Volume'].rolling(20).mean().iloc[-1]
    vol_ratio = safe_num(df['Volume'].iloc[-1] / vol_ma) if vol_ma and vol_ma > 0 else np.nan
    atr14 = safe_num(atr(df,14).iloc[-1])
    def ret(n):
        if len(c) <= n: return np.nan
        return safe_num((c.iloc[-1]/c.iloc[-n-1]-1)*100)
    r1m, r3m, r6m, r2y = ret(21), ret(63), ret(126), ret(504)
    ihsg_ret = safe_num((ihsg['Close'].iloc[-1]/ihsg['Close'].iloc[-22]-1)*100) if ihsg is not None and len(ihsg)>22 else np.nan
    rs20 = r1m - ihsg_ret if pd.notna(r1m) and pd.notna(ihsg_ret) else np.nan
    recent = c.tail(20)
    support = safe_num(min(recent.min(), ma20))
    resistance = safe_num(max(recent.max(), c.tail(60).max()))
    trend_points = 0
    trend_points += 10 if last > ma20 else 0
    trend_points += 10 if last > ma50 else 0
    trend_points += 8 if pd.notna(ma200) and last > ma200 else 0
    trend_points += 7 if ma20 > ma50 else 0
    mom_points = 0
    mom_points += 8 if 50 <= r <= 70 else (4 if 40 <= r < 50 or 70 < r <= 75 else 0)
    mom_points += 9 if hist > 0 else 0
    mom_points += 8 if pd.notna(r1m) and r1m > 0 else 0
    setup_points = 0
    setup_points += 8 if pd.notna(vol_ratio) and vol_ratio >= 1 else 0
    setup_points += 6 if last > ema21 else 0
    setup_points += 6 if pd.notna(r3m) and r3m > 0 else 0
    rs_points = 10 if pd.notna(rs20) and rs20 > 0 else (5 if pd.notna(rs20) and rs20 > -2 else 0)
    score = int(max(0, min(100, trend_points + mom_points + setup_points + rs_points + 10)))
    trend = 'BULLISH' if last > ma50 and (pd.isna(ma200) or last > ma200) else ('BEARISH' if last < ma50 and pd.notna(ma200) and last < ma200 else 'SIDEWAYS')
    signal_label = 'STRONG BUY' if score >= 80 and trend == 'BULLISH' else ('BUY' if score >= 65 and trend != 'BEARISH' else ('WATCH' if score >= 50 else 'NEUTRAL'))
    risk_flags = []
    if trend == 'BEARISH': risk_flags.append('Trend bearish')
    if last < ma50: risk_flags.append('Di bawah MA50')
    if pd.notna(r) and r > 75: risk_flags.append('RSI jenuh beli')
    if pd.notna(vol_ratio) and vol_ratio < 0.7: risk_flags.append('Volume lemah')
    gate = 'PASS' if signal_label in ['BUY','STRONG BUY'] and not risk_flags else 'CAUTION'
    stop = max(0, last - 1.5*atr14) if pd.notna(atr14) else np.nan
    target1 = last + 2*atr14 if pd.notna(atr14) else np.nan
    target2 = last + 3*atr14 if pd.notna(atr14) else np.nan
    rr = safe_num((target1-last)/(last-stop)) if pd.notna(stop) and stop < last else np.nan
    # style scores intentionally separate from general score
    day_score = (35 if trend != 'BEARISH' else 0) + (25 if pd.notna(vol_ratio) and vol_ratio >= 1 else 8) + (20 if pd.notna(r) and 45 <= r <= 72 else 5) + (20 if hist > 0 else 0)
    swing_score = (30 if trend == 'BULLISH' else (15 if trend == 'SIDEWAYS' else 0)) + (20 if pd.notna(r3m) and r3m > 0 else 0) + (20 if last >= ema21 else 0) + (10 if pd.notna(vol_ratio) and vol_ratio >= .8 else 0) + (10 if pd.notna(rs20) and rs20 > 0 else 0) + (10 if pd.notna(rr) and rr >= 1.5 else 0)
    investor_score = (35 if pd.notna(ma200) and last > ma200 else 0) + (25 if pd.notna(r6m) and r6m > 0 else 0) + (20 if pd.notna(r2y) and r2y > 0 else 0) + (10 if trend == 'BULLISH' else 0) + (10 if pd.notna(rs20) and rs20 > 0 else 0)
    return {'Code':ticker,'Price':last,'Score':score,'Trend':trend,'Signal':signal_label,'Gate':gate,'RSI':r,'VolRatio':vol_ratio,'ATR14':atr14,'1M %':r1m,'3M %':r3m,'6M %':r6m,'2Y %':r2y,'RS20':rs20,'Support':support,'Resistance':resistance,'Stop Loss':stop,'Target 1':target1,'Target 2':target2,'R:R':rr,'Day Score':day_score,'Swing Score':swing_score,'Investor Score':investor_score,'Gate Reason':'; '.join(risk_flags) if risk_flags else 'Memenuhi aturan utama'}

def fmt_price(x):
    return '-' if pd.isna(x) else f'Rp {x:,.0f}'.replace(',', '.')
def fmt_pct(x):
    return '-' if pd.isna(x) else f'{x:+.1f}%'
def badge(text):
    cls = 'green' if text in ['PASS','BUY','STRONG BUY','ACTIONABLE','READY'] else ('yellow' if text in ['CAUTION','WATCH','WATCHLIST'] else ('red' if text in ['BEARISH','NO SETUP'] else 'gray'))
    return f'<span class="pill {cls}">{text}</span>'

def card(row, style):
    style_score = row[style]
    ready = style_score >= 70 and row['Gate'] == 'PASS'
    status = 'ACTIONABLE' if ready else ('WATCHLIST' if style_score >= 55 else 'NO SETUP')
    style_name = {'Day Score':'Trading Harian','Swing Score':'Swing Mingguan','Investor Score':'Investor Jangka Panjang'}[style]
    st.markdown(f'''<div class="card"><h3>{row['Code']} {badge(row['Signal'])} {badge(status)}</h3>
    <div class="muted">{style_name} · Score gaya {style_score}/100 · Risk Gate {row['Gate']}</div>
    <p><b>{fmt_price(row['Price'])}</b> · Technical Score {row['Score']} · R:R {('-' if pd.isna(row['R:R']) else f"{row['R:R']:.2f}")}</p>
    <div class="small">Stop {fmt_price(row['Stop Loss'])} · Target 1 {fmt_price(row['Target 1'])} · Target 2 {fmt_price(row['Target 2'])}</div>
    <div class="small">{row['Gate Reason']}</div></div>''', unsafe_allow_html=True)

st.title('📊 Sanggul Stock Scanner V10.1')
st.caption('Focus-Aware Multi-Style · Multi-Period · Top 3 Actionable Picks · Risk-Gated · Result Error Fixed')

with st.sidebar:
    st.header('Pengaturan')
    mode = st.radio('Mode', ['Scanner Universe','Analisis 1 Saham'], index=0)
    period_label = st.selectbox('Periode analisis', list(PERIODS.keys()), index=2)
    min_score = st.slider('Minimum Technical Score', 0, 100, 60, 5)
    max_scan = st.slider('Maksimum saham dipindai', 10, 100, 50, 5)
    show_watch = st.checkbox('Tampilkan watchlist mendekati syarat', True)
    universe_text = st.text_area('Universe kode saham (pisahkan koma)', DEFAULT_UNIVERSE, height=150)
    tickers = [x.strip().upper().replace('.JK','') for x in universe_text.replace('\n',',').split(',') if x.strip()]
    tickers = list(dict.fromkeys(tickers))[:max_scan]
    run_scan = st.button('🚀 Jalankan / Refresh Scan', type='primary', use_container_width=True)
    st.info('Data: Yahoo Finance. Data dapat terlambat, tidak lengkap, atau gagal diambil saat pembatasan layanan.')

if not tickers:
    st.warning('Universe kosong. Masukkan minimal satu kode saham.')
    st.stop()

if mode == 'Analisis 1 Saham':
    selected = st.selectbox('Pilih saham', tickers)
    scan_tickers = [selected]
else:
    scan_tickers = tickers

if run_scan or 'data_cache' not in st.session_state:
    with st.spinner('Mengambil data historis dan menghitung indikator...'):
        histories = download_history(scan_tickers if mode == 'Analisis 1 Saham' else scan_tickers, period='2y')
        ihsg_dict = download_history(['^JKSE'], period='2y')
        ihsg = ihsg_dict.get('^JKSE')
        rows = []
        for t, df in histories.items():
            try:
                rows.append(calc_metrics(t, df, ihsg))
            except Exception:
                pass

        # FIX: define result before it is used below
        result = pd.DataFrame(rows)

        # Save the same result object to session state
        st.session_state['data_cache'] = (histories, result, ihsg)
else:
    histories, result, ihsg = st.session_state['data_cache']

if result.empty:
    st.error('Belum ada data yang berhasil diambil. Periksa internet, kode saham, atau coba lagi beberapa saat.')
    st.stop()

result = result.copy()
# apply period-aware ranking emphasis
period_col = {'1 Bulan':'1M %','3 Bulan':'3M %','6 Bulan':'6M %','2 Tahun':'2Y %'}[period_label]
result['Period Return'] = result[period_col]
filtered = result[result['Score'] >= min_score].copy().sort_values(['Score','Period Return'], ascending=False)

# top-level summary
st.markdown('### Ringkasan Pasar & Scanner')
regime = 'BULLISH' if ihsg is not None and len(ihsg) >= 200 and ihsg['Close'].iloc[-1] > ihsg['Close'].rolling(50).mean().iloc[-1] else 'SIDEWAYS'
if ihsg is not None and len(ihsg) >= 50 and ihsg['Close'].iloc[-1] < ihsg['Close'].rolling(50).mean().iloc[-1]: regime = 'BEARISH'
metrics = st.columns(5)
metrics[0].metric('Saham dipindai', len(result))
metrics[1].metric('Lolos score', len(filtered))
metrics[2].metric('Risk Gate PASS', int((filtered['Gate']=='PASS').sum()))
metrics[3].metric('Strong Buy', int((filtered['Signal']=='STRONG BUY').sum()))
metrics[4].metric('Market Regime', regime)

if mode == 'Analisis 1 Saham':
    row = result.iloc[0]
    st.markdown('### 🔎 Analisis 1 Saham')
    c1,c2,c3,c4 = st.columns(4)
    c1.metric('Harga', fmt_price(row['Price']))
    c2.metric('Technical Score', int(row['Score']))
    c3.metric('Signal', row['Signal'])
    c4.metric('Risk Gate', row['Gate'])
    st.markdown(f'''<div class="card"><h3>{row['Code']} · {row['Trend']} {badge(row['Gate'])}</h3>
    <div class="muted">Periode aktif: {period_label} · Return periode: {fmt_pct(row['Period Return'])}</div>
    <p>RSI <b>{row['RSI']:.1f}</b> · Volume Ratio <b>{row['VolRatio']:.2f}x</b> · ATR14 <b>{fmt_price(row['ATR14'])}</b> · RS20 <b>{fmt_pct(row['RS20'])}</b></p>
    <p>Support <b>{fmt_price(row['Support'])}</b> · Resistance <b>{fmt_price(row['Resistance'])}</b></p>
    <p>Stop Loss <b>{fmt_price(row['Stop Loss'])}</b> · Target 1 <b>{fmt_price(row['Target 1'])}</b> · Target 2 <b>{fmt_price(row['Target 2'])}</b> · R:R <b>{'-' if pd.isna(row['R:R']) else f"{row['R:R']:.2f}"}</b></p>
    </div>''', unsafe_allow_html=True)
    df = histories.get(row['Code'])
    if df is not None:
        chart = df[['Close']].copy()
        chart['MA20'] = chart['Close'].rolling(20).mean()
        chart['MA50'] = chart['Close'].rolling(50).mean()
        chart['MA200'] = chart['Close'].rolling(200).mean()
        st.line_chart(chart.tail(260), height=380)
    st.markdown('### Detail indikator')
    detail = pd.DataFrame({'Indikator':['1 Bulan','3 Bulan','6 Bulan','2 Tahun','RSI14','Volume Ratio','RS20','Support','Resistance','Stop Loss','Target 1','Target 2','R:R'], 'Nilai':[fmt_pct(row['1M %']),fmt_pct(row['3M %']),fmt_pct(row['6M %']),fmt_pct(row['2Y %']),f"{row['RSI']:.1f}",f"{row['VolRatio']:.2f}x",fmt_pct(row['RS20']),fmt_price(row['Support']),fmt_price(row['Resistance']),fmt_price(row['Stop Loss']),fmt_price(row['Target 1']),fmt_price(row['Target 2']),'-' if pd.isna(row['R:R']) else f"{row['R:R']:.2f}"]})
    st.dataframe(detail, use_container_width=True, hide_index=True)
else:
    st.markdown('### 🏆 Top 3 Actionable Picks — Risk-Gated')
    actionable = filtered[(filtered['Gate']=='PASS') & (filtered['Signal'].isin(['BUY','STRONG BUY']))].sort_values(['Score','Period Return'], ascending=False).head(3)
    if actionable.empty:
        st.info('Belum ada kandidat yang lolos penuh. Lihat Watchlist Terdekat untuk saham yang mendekati syarat.')
    else:
        cols = st.columns(3)
        for col, (_, r) in zip(cols, actionable.iterrows()):
            with col: card(r, 'Swing Score' if r['Swing Score'] >= r['Day Score'] else 'Day Score')

    st.markdown('### 🎯 Multi-Style Action Board')
    style_cols = st.columns(3)
    for col, style, title, subtitle in zip(style_cols, ['Day Score','Swing Score','Investor Score'], ['⚡ Trading Harian','📊 Swing Trading Mingguan','🌱 Investor Jangka Panjang'], ['Fokus 1–5 hari','Fokus 1–8 minggu','Fokus 6 bulan+']):
        with col:
            st.markdown(f'#### {title}')
            st.caption(subtitle)
            eligible = filtered[filtered['Gate']=='PASS'].sort_values(style, ascending=False)
            act = eligible[eligible[style] >= 70].head(3)
            watch = eligible[(eligible[style] >= 55) & (eligible[style] < 70)].head(3)
            if not act.empty:
                for _, r in act.iterrows(): card(r, style)
            elif show_watch and not watch.empty:
                st.info('Belum ada actionable; berikut kandidat watchlist terdekat.')
                for _, r in watch.iterrows(): card(r, style)
            else:
                st.info('Belum ada kandidat yang memenuhi filter gaya ini.')

    st.markdown('### 🧠 Enrich Top 50 — Focus-Aware Multi-Style')
    top50 = filtered.head(50).copy()
    display_cols = ['Code','Price','1M %','3M %','6M %','2Y %','Score','Trend','Signal','Gate','Day Score','Swing Score','Investor Score','RSI','VolRatio','RS20','R:R','Stop Loss','Target 1']
    st.dataframe(top50[display_cols].style.format({'Price':'{:,.0f}','1M %':'{:+.1f}%','3M %':'{:+.1f}%','6M %':'{:+.1f}%','2Y %':'{:+.1f}%','RSI':'{:.1f}','VolRatio':'{:.2f}','RS20':'{:+.1f}%','R:R':'{:.2f}','Stop Loss':'{:,.0f}','Target 1':'{:,.0f}'}), use_container_width=True, height=520)
    st.download_button('⬇️ Download Enrich Top 50 CSV', top50[display_cols].to_csv(index=False).encode('utf-8'), 'enrich_top50_v10_1.csv', 'text/csv', use_container_width=True)

    st.markdown('### 📋 Ranking Detail')
    st.dataframe(filtered[['Code','Price','Score','Trend','Signal','Gate','Period Return','1M %','3M %','6M %','2Y %','RSI','VolRatio','RS20','R:R','Gate Reason']].head(50), use_container_width=True, height=500)
    st.download_button('⬇️ Download Ranking CSV', filtered.to_csv(index=False).encode('utf-8'), 'ranking_v10_1.csv', 'text/csv', use_container_width=True)

st.divider()
st.caption(f'V10.1 · Pembaruan terakhir: {datetime.now().strftime("%d-%m-%Y %H:%M")} · Gunakan sebagai alat bantu screening, bukan jaminan hasil transaksi.')
