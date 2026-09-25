import json
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import streamlit.components.v1 as components
from pathlib import Path
from urllib.parse import quote

st.set_page_config(page_title="Sanggul Stock Scanner", page_icon="📈", layout="wide", initial_sidebar_state="expanded")

APP_VERSION = "V11.2.0"
# GitHub / Streamlit Cloud safe universe loading.
APP_DIR = Path(__file__).resolve().parent
CWD = Path.cwd()
UNIVERSE_CANDIDATES = [
    APP_DIR / "data" / "universe.csv",
    CWD / "data" / "universe.csv",
    APP_DIR / "universe.csv",
    CWD / "universe.csv",
]
UNIVERSE_FILE = next((p for p in UNIVERSE_CANDIDATES if p.exists()), APP_DIR / "data" / "universe.csv")
FUNDAMENTAL_CANDIDATES = [APP_DIR / "data" / "idx_fundamental.csv", CWD / "data" / "idx_fundamental.csv"]
FUNDAMENTAL_FILE = next((p for p in FUNDAMENTAL_CANDIDATES if p.exists()), APP_DIR / "data" / "idx_fundamental.csv")
FUNDAMENTAL_SOURCE = ""
UNIVERSE_SOURCE = ""
EMBEDDED_UNIVERSE_ROWS = [{'ticker': 'BBCA', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BBRI', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BMRI', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BBNI', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BRIS', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BDMN', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'ADRO', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'PTBA', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'ITMG', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'PGAS', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'ANTM', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'INCO', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'MDKA', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'SMGR', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'ICBP', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'INDF', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'UNVR', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'MYOR', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'TLKM', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'ISAT', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'EXCL', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'JSMR', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'WIKA', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'WSKT', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'PGEO', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'KLBF', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'MIKA', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'SILO', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'GOTO', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'EMTK', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'BUKA', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'ASII', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'UNTR', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'AUTO', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'AADI', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'ADMR', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'AIMS', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'AKRA', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'APEX', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'ARII', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'BOSS', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'BSSR', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'BYAN', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'CNKO', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'COAL', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'DEWA', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'DOID', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'DSSA', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'ELSA', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'ENRG', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'GEMS', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'GTBO', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'HRUM', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'INDY', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'KKGI', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'MBAP', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'MEDC', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'PTRO', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'RAJA', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'SMMT', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'SMRU', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'TOBA', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'TPMA', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'TBSM', 'sector': 'Energy', 'enabled': 1}, {'ticker': 'ARCI', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'BRMS', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'BTON', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'CITA', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'CKRA', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'CLPI', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'DKFT', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'DMAS', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'EMAS', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'INKP', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'IPCC', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'IPOL', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'ISSP', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'JATF', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'JKON', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'KICI', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'LION', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'LMAX', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'MDKI', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'MINE', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'NCKL', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'NICL', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'PBSA', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'SMBR', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'SMCB', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'SMKL', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'TINS', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'TKIM', 'sector': 'Basic Materials', 'enabled': 1}, {'ticker': 'BOLT', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'BRAM', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'GJTL', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'IMAS', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'INDS', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'JECC', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'KBLI', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'KBLM', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'KIAS', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'KRAH', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'MASA', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'MFIN', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'MLBI', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'MPMX', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'NIKL', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'PBRX', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'PRAS', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'SMSM', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'SRIL', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'TOTO', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'TRIS', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'VOKS', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'WTON', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'WSBP', 'sector': 'Industrials', 'enabled': 1}, {'ticker': 'AISA', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'ALTO', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'AMRT', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'BUDI', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'CEKA', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'CLEO', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'DLTA', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'DMND', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'FOOD', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'GOOD', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'GGRM', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'HMSP', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'KINO', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'MBTO', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'PSDN', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'ROTI', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'SKBM', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'SKLT', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'STTP', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'TCID', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'TGKA', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'TAYS', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'ULTJ', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'WIIM', 'sector': 'Consumer Non-Cyclicals', 'enabled': 1}, {'ticker': 'ACES', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'ARGO', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'BABP', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'BCAP', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'BELL', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'BIMA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'BIRD', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'BOGA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'CARS', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'CINTA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'DART', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'FAST', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'GLOB', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'GOLF', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'GWSA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'HRTA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'MAPA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'MAPI', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'MAPB', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'MCAS', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'MNCN', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'PANR', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'PNSE', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'SCMA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'SONA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'SOTS', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'TKGA', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'TOYS', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'VICI', 'sector': 'Consumer Cyclicals', 'enabled': 1}, {'ticker': 'BMHS', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'HEAL', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'INAF', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'IRRA', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'KAEF', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'PEHA', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'PRDA', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'PRIM', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'RSGK', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'SAME', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'SCPI', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'SRAJ', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'TSPC', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'DVLA', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'MERK', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'CARE', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'DGNS', 'sector': 'Healthcare', 'enabled': 1}, {'ticker': 'AGRO', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'ARTO', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BBTN', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BFIN', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BJBR', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BJTM', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BNGA', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BNII', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BNLI', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BSIM', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BTPS', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BVIC', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'CASA', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'CFIN', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'COMI', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'DNAR', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'INPC', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'JMAS', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'MAYA', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'MEGA', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'NISP', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'PNBN', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'PNBS', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'PNLF', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'SDRA', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'TUGU', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BBYB', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BBHI', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BBKP', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'BACA', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'TRIM', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'VINS', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'NOBU', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'MREI', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'APLN', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'ASRI', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'BKSL', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'BSDE', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'CTRA', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'DILD', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'DUTI', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'ELTY', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'EMDE', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'GPRA', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'INPP', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'JRPT', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'KIJA', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'LPKR', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'MDLN', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'MKPI', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'MTLA', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'PLIN', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'RDTX', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'SMRA', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'TARA', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'TRIN', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'TRUE', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'URBN', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'VAST', 'sector': 'Properties & Real Estate', 'enabled': 1}, {'ticker': 'DCII', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'DMMX', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'EDGE', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'IOTF', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'KREN', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'MLPT', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'MTDL', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'NFCX', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'WIFI', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'WIRG', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'ZYRX', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'AVTE', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'DATA', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'DIVA', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'DNET', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'LINK', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'LUCK', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'TFAS', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'TECH', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'ERAA', 'sector': 'Technology', 'enabled': 1}, {'ticker': 'ADHI', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'CMNP', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'FREN', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'META', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'MTEL', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'POWR', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'PURA', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'RIGS', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'TOWR', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'WEGE', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'CENT', 'sector': 'Infrastructures', 'enabled': 1}, {'ticker': 'ASSA', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'BESS', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'BLTA', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'CMPP', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'DEAL', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'GIAA', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'HELI', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'JAYA', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'KJEN', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'LRNA', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'MBSS', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'MIRA', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'MITI', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'NELY', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'PSSI', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'PTIS', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'SOCI', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'TAXI', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'TMAS', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'TRJA', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'WEHA', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'CASS', 'sector': 'Transportation & Logistics', 'enabled': 1}, {'ticker': 'BBLD', 'sector': 'Financials', 'enabled': 1}, {'ticker': 'KBLF', 'sector': 'Industrials', 'enabled': 1}]

def _read_universe(path=None):
    global UNIVERSE_SOURCE
    if path is not None and Path(path).exists():
        try:
            df = pd.read_csv(path)
            UNIVERSE_SOURCE = str(Path(path))
            return df
        except Exception:
            pass
    UNIVERSE_SOURCE = "embedded fallback in app.py"
    return pd.DataFrame(EMBEDDED_UNIVERSE_ROWS)

def load_universe():
    u = _read_universe(UNIVERSE_FILE if UNIVERSE_FILE.exists() else None)
    required = {"ticker", "sector", "enabled"}
    if not required.issubset(u.columns):
        raise ValueError("Universe harus memiliki kolom: ticker, sector, enabled")
    u["ticker"] = u["ticker"].astype(str).str.upper().str.strip()
    u["sector"] = u["sector"].astype(str).str.strip()
    u["enabled"] = pd.to_numeric(u["enabled"], errors="coerce").fillna(0).astype(int)
    u = u[(u["enabled"] == 1) & (u["ticker"] != "")].drop_duplicates("ticker").copy()
    if u.empty:
        UNIVERSE_SOURCE = "embedded fallback in app.py"
        u = pd.DataFrame(EMBEDDED_UNIVERSE_ROWS)
    return u

UNIVERSE = load_universe()


# --- Official IDX fundamental data layer ---
def _norm_fund_col(c):
    c=str(c).strip().lower()
    aliases={
        "code":"ticker","stock code":"ticker","kode":"ticker","fs date":"fs_date","fiscal year end":"fiscal_year_end",
        "type of fs":"type_of_fs","auditor's opinion":"auditor_opinion","assets, b.idr":"assets","liabilities, b.idr":"liabilities",
        "equity, b.idr":"equity","sales, b.idr":"sales","profit for the period":"profit","profit attr.to owner's":"profit_attrib_owner",
        "ebt, b.idr":"ebt","eps, idr":"eps","book value, idr":"book_value","p/e ratio, x":"per","price to bv, x":"pbv",
        "d/e ratio, x":"der","roa, %":"roa","roe, %":"roe","npm, %":"npm","market cap":"market_cap"
    }
    return aliases.get(c,re.sub(r"[^a-z0-9]+","_",c).strip("_"))

@st.cache_data(ttl=900)
def load_official_fundamentals():
    global FUNDAMENTAL_SOURCE
    if not FUNDAMENTAL_FILE.exists():
        FUNDAMENTAL_SOURCE="not loaded — add official IDX export as data/idx_fundamental.csv"
        return pd.DataFrame()
    try: df=pd.read_csv(FUNDAMENTAL_FILE)
    except Exception:
        FUNDAMENTAL_SOURCE="invalid CSV"; return pd.DataFrame()
    df=df.rename(columns={c:_norm_fund_col(c) for c in df.columns})
    if "ticker" not in df.columns:
        FUNDAMENTAL_SOURCE="invalid: ticker/code column missing"; return pd.DataFrame()
    df["ticker"]=df["ticker"].astype(str).str.upper().str.strip().str.replace(r"\.JK$","",regex=True)
    for c in ["assets","liabilities","equity","sales","profit","profit_attrib_owner","ebt","eps","book_value","per","pbv","der","roa","roe","npm","market_cap"]:
        if c in df.columns: df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df.drop_duplicates("ticker",keep="last")
    FUNDAMENTAL_SOURCE=str(FUNDAMENTAL_FILE)
    return df

def _fund_score_row(r):
    vals=[]; w=[]
    def add(v,weight):
        if pd.notna(v): vals.append(float(v)); w.append(weight)
    # Robust cross-company score bands; not a valuation recommendation.
    add(np.clip((r.get("roe",np.nan)+10)/30*100,0,100),0.35)
    add(np.clip((r.get("npm",np.nan)+5)/25*100,0,100),0.20)
    per=r.get("per",np.nan); pbv=r.get("pbv",np.nan); der=r.get("der",np.nan)
    if pd.notna(per) and per>0: add(np.clip((40-per)/35*100,0,100),0.15)
    if pd.notna(pbv) and pbv>0: add(np.clip((8-pbv)/7*100,0,100),0.10)
    if str(r.get("sector",""))!="Financials" and pd.notna(der) and der>=0: add(np.clip((4-der)/4*100,0,100),0.20)
    return float(np.average(vals,weights=w)) if len(vals)>=2 else np.nan

def merge_fundamentals(scan):
    if scan.empty: return scan
    f=load_official_fundamentals(); out=scan.copy()
    if f.empty:
        out["Fundamental Strength"]=np.nan; out["Fundamental Data"]="N/A"; return out
    f["Fundamental Strength"]=f.apply(_fund_score_row,axis=1)
    f["Fundamental Data"]=np.where(f["Fundamental Strength"].notna(),"IDX OFFICIAL","N/A")
    cols=[c for c in ["ticker","fs_date","per","pbv","der","roa","roe","npm","eps","book_value","market_cap","Fundamental Strength","Fundamental Data"] if c in f.columns]
    out=out.merge(f[cols],on="ticker",how="left")
    mask=out["Fundamental Strength"].notna()
    out.loc[mask,"Opportunity"]=0.85*out.loc[mask,"Opportunity"]+0.15*out.loc[mask,"Fundamental Strength"]
    return out


def rupiah(x):
    if pd.isna(x):
        return "-"
    return f"Rp {float(x):,.0f}".replace(",", ".")


def symbol(kode):
    kode = str(kode).upper().strip()
    return kode if kode.endswith(".JK") else kode + ".JK"


@st.cache_data(ttl=300)
def get_data(kode):
    try:
        d = yf.download(symbol(kode), period="2y", interval="1d", auto_adjust=True, progress=False, threads=False)
    except Exception:
        return pd.DataFrame()
    if d.empty:
        return pd.DataFrame()
    if isinstance(d.columns, pd.MultiIndex):
        d.columns = d.columns.get_level_values(0)
    d.columns = [str(c).title() for c in d.columns]
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    need = ["Open", "High", "Low", "Close"]
    if any(c not in d.columns for c in need):
        return pd.DataFrame()
    return d.dropna(subset=need)


def indicators(d):
    x = d.copy()
    x["MA20"] = x["Close"].rolling(20).mean()
    x["MA50"] = x["Close"].rolling(50).mean()
    x["MA200"] = x["Close"].rolling(200).mean()
    delta = x["Close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, np.nan)
    x["RSI"] = 100 - 100 / (1 + rs)
    ema12 = x["Close"].ewm(span=12, adjust=False).mean()
    ema26 = x["Close"].ewm(span=26, adjust=False).mean()
    x["MACD"] = ema12 - ema26
    x["MACDSignal"] = x["MACD"].ewm(span=9, adjust=False).mean()
    x["MACDHist"] = x["MACD"] - x["MACDSignal"]
    mid = x["Close"].rolling(20).mean()
    sd = x["Close"].rolling(20).std()
    x["BBUpper"] = mid + 2 * sd
    x["BBLower"] = mid - 2 * sd
    prev = x["Close"].shift(1)
    tr = pd.concat([(x["High"]-x["Low"]), (x["High"]-prev).abs(), (x["Low"]-prev).abs()], axis=1).max(axis=1)
    x["ATR"] = tr.rolling(14).mean()
    x["VolumeMA20"] = x["Volume"].rolling(20).mean()
    x["VolumeRatio"] = x["Volume"] / x["VolumeMA20"]
    x["Support20"] = x["Low"].rolling(20).min()
    x["Resistance20"] = x["High"].rolling(20).max()
    x["Support60"] = x["Low"].rolling(60).min()
    x["Resistance60"] = x["High"].rolling(60).max()
    x["PrevResistance20"] = x["Resistance20"].shift(1)
    return x


def analyze(d):
    x = indicators(d)
    req = ["MA20","MA50","MA200","RSI","MACD","MACDSignal","ATR","VolumeRatio","Support20","Resistance20","Support60","Resistance60","PrevResistance20"]
    x = x.dropna(subset=req)
    if x.empty:
        return None, x
    last = x.iloc[-1]
    close = float(last.Close)
    atr = max(float(last.ATR), close * 0.005)
    score = 0
    reasons = []
    checks = [
        ("Harga > MA20", close > last.MA20, 10),
        ("Harga > MA50", close > last.MA50, 10),
        ("Harga > MA200", close > last.MA200, 15),
        ("MA20 > MA50 > MA200", last.MA20 > last.MA50 > last.MA200, 15),
        ("RSI 50–70", 50 <= last.RSI <= 70, 15),
        ("MACD bullish", last.MACD > last.MACDSignal, 10),
        ("Volume Ratio >= 1.2x", last.VolumeRatio >= 1.2, 10),
        ("Higher recent close", close >= float(x.Close.iloc[-6:-1].max()), 5),
    ]
    for label, ok, pts in checks:
        if ok:
            score += pts
            reasons.append(label)
    supports = [float(v) for v in [last.Support20, last.Support60] if np.isfinite(v) and v < close]
    resistances = [float(v) for v in [last.Resistance20, last.Resistance60] if np.isfinite(v) and v > close]
    support = max(supports) if supports else close - 1.5*atr
    resistance = min(resistances) if resistances else close + 2*atr
    prev_r20 = float(last.PrevResistance20)
    breakout = close > prev_r20 and float(last.VolumeRatio) >= 1.2
    pullback = (not breakout and close > support and (close-support)/close <= 0.07 and close > last.MA50)
    structural_stop = support - 0.25*atr
    atr_stop = close - 1.50*atr
    stop = max(structural_stop, atr_stop)
    if stop >= close:
        stop = close - 1.25*atr
    risk = max(close-stop, 0.01)
    tp1 = resistance if resistance > close else close + 1.5*atr
    tp2 = max(close + 2*risk, close + 2.5*atr, tp1 + 0.5*atr)
    tp3 = max(close + 3*risk, tp2 + 0.75*atr)
    rr1 = (tp1-close)/risk
    rr2 = (tp2-close)/risk
    if breakout:
        setup = "BREAKOUT"
    elif pullback:
        setup = "PULLBACK"
    elif close > last.MA20 > last.MA50:
        setup = "TREND FOLLOWING"
    else:
        setup = "WATCH"
    setup_quality = 20 if breakout else 17 if pullback else 10 if setup == "TREND FOLLOWING" else 0
    rr_quality = min(max(rr2/2.0, 0), 1)*20
    market_compatibility = 10 if close > last.MA50 else 4
    opportunity = min(round(0.55*score + setup_quality + rr_quality + market_compatibility, 1), 100)
    risk_pct = (close-stop)/close*100
    if float(last.VolumeRatio) < 0.70 or risk_pct > 12 or rr2 < 1.5:
        risk_level = "HIGH"
    elif risk_pct > 8 or rr2 < 2:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"
    hard_pass = score >= 70 and rr2 >= 2.0 and np.isfinite(stop) and stop < close and setup in ["BREAKOUT","PULLBACK","TREND FOLLOWING"]
    if hard_pass and risk_level == "LOW":
        gate = "PASS"
        action = "BUY ON BREAKOUT" if breakout else "BUY ON PULLBACK" if pullback else "BUY ON CONFIRMATION"
    elif score >= 65 and rr2 >= 1.5 and setup != "WATCH":
        gate = "NEAR PASS"
        action = "WAIT"
    elif score >= 55:
        gate = "WATCH"
        action = "WATCH"
    else:
        gate = "FAIL"
        action = "AVOID"
    confidence = "HIGH" if hard_pass and risk_level == "LOW" else "MEDIUM" if score >= 65 else "LOW"
    trend = "BULLISH" if score >= 75 else "SIDEWAYS" if score >= 55 else "BEARISH"
    return {
        "price": close, "score": score, "opportunity": opportunity, "trend": trend, "setup": setup,
        "action": action, "risk_level": risk_level, "gate": gate, "confidence": confidence,
        "support": support, "resistance": resistance, "entry_low": max(support, close-0.75*atr),
        "entry_high": close, "stop": stop, "tp1": tp1, "tp2": tp2, "tp3": tp3, "rr1": rr1, "rr2": rr2,
        "rsi": float(last.RSI), "volume_ratio": float(last.VolumeRatio), "ret_20d": float((close / x.Close.iloc[-21] - 1) * 100) if len(x) >= 21 else np.nan, "ret_60d": float((close / x.Close.iloc[-61] - 1) * 100) if len(x) >= 61 else np.nan, "atr": atr, "breakout": breakout,
        "pullback": pullback, "reasons": reasons, "date": x.index[-1],
        "invalidation": f"Daily close di bawah {rupiah(stop)} atau setup kehilangan struktur bullish."
    }, x


# ---------- Multi-style engine ----------
def style_view(a, style):
    score = a["score"]
    setup = a["setup"]
    rr = a["rr2"]
    vol = a["volume_ratio"]
    rsi = a["rsi"]
    trend = a["trend"]
    if style == "DAILY":
        bonus = (7 if a["breakout"] else 4 if a["pullback"] else 0) + (5 if vol >= 1.3 else 0) + (3 if 45 <= rsi <= 65 else 0)
        ss = min(100, round(0.78*score + bonus, 1))
        gate = "PASS" if ss >= 68 and rr >= 1.5 and setup != "WATCH" and a["risk_level"] != "HIGH" else "NEAR PASS" if ss >= 60 and setup != "WATCH" else "WATCH"
        action = "DAY TRADE CONFIRMATION" if gate == "PASS" else "WAIT" if gate == "NEAR PASS" else "WATCH"
        horizon = "1–5 hari"
    elif style == "SWING":
        ss = min(100, round(a["opportunity"], 1))
        gate = a["gate"]
        action = a["action"]
        horizon = "1–6 minggu"
    else:
        bonus = (10 if trend == "BULLISH" else 5 if trend == "SIDEWAYS" else 0) + (8 if a["price"] > a["support"] and a["price"] > a["stop"] else 0)
        ss = min(100, round(0.72*score + bonus, 1))
        gate = "PASS" if ss >= 65 and trend == "BULLISH" and rr >= 2 else "NEAR PASS" if ss >= 55 and trend != "BEARISH" else "WATCH"
        action = "ACCUMULATION / CONFIRMATION" if gate == "PASS" else "WAIT" if gate == "NEAR PASS" else "WATCH"
        horizon = "3–24 bulan"
    return ss, gate, action, horizon


@st.cache_data(ttl=300)
def market_regime():
    d = get_data("^JKSE")
    if d.empty:
        return None
    x = d.copy()
    x["MA20"] = x.Close.rolling(20).mean(); x["MA50"] = x.Close.rolling(50).mean(); x["MA200"] = x.Close.rolling(200).mean()
    x = x.dropna()
    if x.empty: return None
    a = x.iloc[-1]
    score = sum([25 if a.Close>a.MA20 else 0,25 if a.Close>a.MA50 else 0,25 if a.Close>a.MA200 else 0,15 if a.MA20>a.MA50 else 0,10 if a.MA50>a.MA200 else 0])
    regime = "BULLISH" if score>=75 else "SIDEWAYS" if score>=50 else "BEARISH"
    gate = "GREEN" if score>=75 else "YELLOW" if score>=50 else "RED"
    return {"close":float(a.Close),"score":score,"regime":regime,"gate":gate,"date":x.index[-1]}


@st.cache_data(ttl=300)
def scan_all():
    rows=[]
    for _,r in UNIVERSE.iterrows():
        ticker=str(r.ticker).strip().upper(); d=get_data(ticker)
        if d.empty or len(d)<220: continue
        a,x=analyze(d)
        if not a: continue
        rows.append({
            "Ticker":ticker,"Sector":r.sector,"Price":a["price"],"Technical":a["score"],"Opportunity":a["opportunity"],
            "Trend":a["trend"],"Setup":a["setup"],"Action":a["action"],"Risk":a["risk_level"],"Gate":a["gate"],
            "Confidence":a["confidence"],"Entry":a["entry_high"],"Buy Low":a["entry_low"],"Buy High":a["entry_high"],"Stop Loss":a["stop"],"TP1":a["tp1"],"TP2":a["tp2"],"R:R TP1":a["rr1"],"R:R TP2":a["rr2"],"RSI":a["rsi"],"VolumeRatio":a["volume_ratio"],"Momentum 20D %":a["ret_20d"],
            "Breakout":"YES" if a["breakout"] else "NO","Date":a["date"].strftime("%Y-%m-%d")
        })
    if not rows: return pd.DataFrame()
    out=pd.DataFrame(rows)
    out=merge_fundamentals(out)
    return out.sort_values(["Opportunity","Technical","R:R TP2"],ascending=[False,False,False])


def add_style_columns(df, style):
    if df.empty: return df.copy()
    out=df.copy(); vals=out.apply(lambda r: style_view({
        "score":r.Technical,"setup":r.Setup,"rr2":r["R:R TP2"],"volume_ratio":r.VolumeRatio,
        "rsi":r.RSI,"trend":r.Trend,"breakout":r.Breakout=="YES","pullback":r.Setup=="PULLBACK",
        "opportunity":r.Opportunity,"gate":r.Gate,"action":r.Action,"risk_level":r.Risk,"price":r.Price,"support":0,"stop":0
    }, style), axis=1)
    out["Style Score"]=[v[0] for v in vals]; out["Style Gate"]=[v[1] for v in vals]; out["Style Action"]=[v[2] for v in vals]; out["Horizon"]=[v[3] for v in vals]
    return out.sort_values(["Style Gate","Style Score"], key=lambda s: s.map({"PASS":0,"NEAR PASS":1,"WATCH":2,"FAIL":3}) if s.name=="Style Gate" else s, ascending=[True,False])


def sector_opportunity(df):
    if df.empty or "Sector" not in df.columns:
        return pd.DataFrame()
    g = df.groupby("Sector", dropna=False)
    out = g.agg(Stocks=("Ticker","count"), AvgTechnical=("Technical","mean"), AvgOpportunity=("Opportunity","mean"), AvgVolume=("VolumeRatio","mean"), BullishBreadth=("Trend", lambda s: (s=="BULLISH").mean()*100), AvgMomentum20D=("Momentum 20D %","mean"), PassRate=("Gate", lambda s: (s=="PASS").mean()*100)).reset_index()
    out["Momentum Score"] = np.clip(50 + out["AvgMomentum20D"].fillna(0)*2, 0, 100)
    out["Volume Score"] = np.clip(out["AvgVolume"].fillna(0)/1.5*100, 0, 100)
    out["Sector Score"] = (0.30*out["AvgTechnical"] + 0.25*out["AvgOpportunity"] + 0.20*out["BullishBreadth"] + 0.10*out["Momentum Score"] + 0.10*out["Volume Score"] + 0.05*out["PassRate"]).round(1)
    out["Status"] = np.select([out["Sector Score"]>=70, out["Sector Score"]>=55], ["🔥 LEADING","👀 WATCH"], default="⚠️ WEAK")
    return out.sort_values(["Sector Score","AvgMomentum20D"], ascending=False)


def money_cols(df):
    if df.empty: return df
    out=df.copy()
    for c in ["Price","Entry","Buy Low","Buy High","Stop Loss","TP1","TP2"]:
        if c in out.columns: out[c]=out[c].map(lambda v: rupiah(v) if pd.notna(v) else "-")
    return out


def vivid_style(df):
    if df.empty: return df
    def gate(v):
        return "background-color:#16a34a;color:white;font-weight:800" if v=="PASS" else "background-color:#f59e0b;color:#111827;font-weight:800" if v=="NEAR PASS" else "background-color:#ef4444;color:white;font-weight:800" if v=="FAIL" else "background-color:#fde68a;color:#78350f;font-weight:700"
    def risk(v):
        return "background-color:#22c55e;color:white;font-weight:800" if v=="LOW" else "background-color:#f59e0b;color:#111827;font-weight:800" if v=="MEDIUM" else "background-color:#ef4444;color:white;font-weight:800"
    sty=df.style
    if "Gate" in df: sty=sty.map(gate, subset=["Gate"])
    if "Style Gate" in df: sty=sty.map(gate, subset=["Style Gate"])
    if "Risk" in df: sty=sty.map(risk, subset=["Risk"])
    if "Status" in df: sty=sty.map(lambda v: "background-color:#dc2626;color:white;font-weight:800" if "WEAK" in str(v) else "background-color:#f59e0b;color:#111827;font-weight:800" if "WATCH" in str(v) else "background-color:#16a34a;color:white;font-weight:800", subset=["Status"])
    return sty

def tradingview_chart(ticker, interval="D", height=900, theme="light"):
    tv_symbol=f"IDX:{ticker.upper().replace('.JK','')}"
    config={"autosize":False,"height":height,"width":"100%","symbol":tv_symbol,"interval":interval,"timezone":"exchange","theme":theme,"style":"1","withdateranges":True,"hide_side_toolbar":False,"allow_symbol_change":True,"save_image":True,"details":True,"hide_top_toolbar":False,"hide_legend":False,"hide_volume":False,"calendar":False,"studies":["MASimple@tv-basicstudies","RSI@tv-basicstudies","MACD@tv-basicstudies"],"locale":"id","support_host":"https://www.tradingview.com"}
    payload=json.dumps(config)
    html=f'''<div class="tradingview-widget-container" style="height:{height}px;width:100%;min-height:{height}px;"><div class="tradingview-widget-container__widget" style="height:{height-32}px;width:100%;min-height:{height-32}px;"></div><div class="tradingview-widget-copyright" style="font-size:11px;height:24px;line-height:24px;"><a href="https://www.tradingview.com/symbols/{quote(tv_symbol)}/" target="_blank" rel="noopener">{tv_symbol} chart</a> by TradingView</div><script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js" async>{payload}</script></div>'''
    components.html(html,height=height+36,scrolling=False)


def badge(text, kind="blue"):
    return f'<span class="badge badge-{kind}">{text}</span>'


def style_card(title, subtitle, kind):
    return f'<div class="card mode-card"><h3>{title}</h3><p>{subtitle}</p>{badge(kind[0],kind[1])}</div>'




def inject_css():
    st.markdown("""
    <style>
    .block-container{max-width:1500px;padding-top:1.1rem;padding-bottom:2rem}
    [data-testid="stSidebar"]{background:#f4f7fb;border-right:1px solid #d9e2ef}
    [data-testid="stSidebar"] .block-container{padding-top:1rem}
    .hero{background:linear-gradient(135deg,#071a3a 0%,#0b2d5c 60%,#0e4f87 100%);border-radius:16px;padding:22px 26px;color:#fff;margin-bottom:16px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 8px 24px rgba(7,26,58,.16)}
    .hero h1{font-size:31px;letter-spacing:.4px;margin:2px 0 4px;font-weight:800}.hero p{margin:0;color:#d9e8ff;font-size:14px}.eyebrow{font-size:11px;letter-spacing:1.5px;color:#8fc7ff;font-weight:700}.hero-tag{border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.10);padding:10px 14px;border-radius:10px;font-size:12px;font-weight:700}
    .section-title{font-size:22px;font-weight:800;color:#102a43;margin:18px 0 4px;border-left:5px solid #1d74d8;padding-left:10px}.section-subtitle{color:#64748b;margin-top:0}
    .kpi{background:#fff;border:1px solid #d9e2ef;border-radius:12px;padding:14px 16px;min-height:92px;box-shadow:0 3px 10px rgba(15,35,60,.05)}.kpi-label{font-size:11px;letter-spacing:.8px;color:#64748b;font-weight:800}.kpi-value{font-size:28px;font-weight:800;color:#102a43;margin-top:4px}.small-value{font-size:21px}.kpi-unit{font-size:14px;color:#64748b}.kpi-sub{font-size:11px;color:#64748b;margin-top:4px}
    .card,.action-card,.mini-card{background:#fff;border:1px solid #d9e2ef;border-radius:13px;padding:16px;box-shadow:0 3px 12px rgba(15,35,60,.05)}.action-card{min-height:235px;border-top:4px solid #1d74d8}.mini-card{min-height:185px;border-top:3px solid #1d74d8}.ticker{font-size:21px;font-weight:850;color:#0b2d5c}.score{font-size:28px;font-weight:850;color:#102a43;margin:9px 0}.score span{font-size:13px;color:#64748b;font-weight:600}.small{font-size:11px;color:#64748b}.rowline{display:flex;justify-content:space-between;gap:10px;font-size:12px;padding:4px 0;border-bottom:1px solid #edf2f7}.rowline span{color:#64748b}.danger{color:#d92d20!important}.source-pill{display:inline-block;padding:5px 9px;border-radius:999px;background:#eef6ff;color:#175cd3;font-size:11px;font-weight:800;margin:2px 4px 2px 0}.hot-title{font-weight:800;margin-top:6px}.badge{display:inline-block;padding:4px 8px;border-radius:999px;font-size:11px;font-weight:800}.badge-green{background:#dcfce7;color:#166534}.badge-yellow{background:#fef3c7;color:#92400e}.badge-red{background:#fee2e2;color:#991b1b}.badge-blue{background:#dbeafe;color:#1d4ed8}
    .buy-box,.sl-box,.tp-box{border-radius:12px;padding:13px 14px;border:1px solid #d9e2ef;background:#fff}.buy-box{border-top:4px solid #16a34a}.sl-box{border-top:4px solid #dc2626}.tp-box{border-top:4px solid #2563eb}.buy-box h3,.sl-box h3,.tp-box h3{margin:4px 0 0;font-size:22px}.tv-shell{background:#f8fafc;border:1px solid #d9e2ef;border-radius:13px;padding:10px 14px;margin-top:16px}
    [data-testid="stMetricValue"]{font-weight:800}.stButton>button{border-radius:9px;font-weight:700}.stExpander{border:1px solid #d9e2ef;border-radius:10px}.stDataFrame{border:1px solid #d9e2ef;border-radius:10px}
    @media(max-width:900px){.hero{display:block}.hero-tag{display:inline-block;margin-top:12px}.hero h1{font-size:24px}}
    </style>
    """,unsafe_allow_html=True)

inject_css()
def main():
    st.sidebar.markdown("### 📡 DATA STATUS")
    fdf=load_official_fundamentals()
    st.sidebar.caption(f"Universe: {len(UNIVERSE)} saham")
    st.sidebar.caption(f"OHLCV: yfinance fallback • {len(scan)} scanned")
    st.sidebar.caption(f"Fundamental IDX resmi: {len(fdf)} saham")
    if fdf.empty: st.sidebar.warning("Fundamental resmi belum diimpor; Fundamental Strength = N/A.")
    else: st.sidebar.success("Fundamental Strength aktif dari data IDX resmi.")
    st.markdown(f'''<div class="hero"><div><div class="eyebrow">SANGGUL CAPITAL MARKETS • DECISION SUPPORT</div><h1>📈 SANGGUL STOCK SCANNER</h1><p>Professional Multi-Style Trading & Investment Dashboard • {APP_VERSION}</p></div><div class="hero-tag">IDX • 300 UNIVERSE</div></div>''', unsafe_allow_html=True)

    regime=market_regime()
    scan=st.session_state.get("scan",pd.DataFrame())

    with st.sidebar:
        st.markdown("## ⚙️ Control Center")
        st.caption(f"Universe aktif: **{len(UNIVERSE)} saham**")
        st.markdown("### NAVIGATION")
        pages=["🏠 Dashboard","⚡ Daily Trading","📈 Swing Weekly","🏦 Investor","📊 Sector Opportunity","🏆 Top 150 / 50 / 10","🔎 Single Stock","⚙️ System"]
        requested=st.session_state.pop("nav_request",None)
        page=st.radio("Pilih modul",pages,index=pages.index(requested) if requested in pages else 0,label_visibility="collapsed")
        st.markdown("---")
        if st.button("🚀 RUN / REFRESH SCAN",use_container_width=True):
            with st.spinner(f"Scanning {len(UNIVERSE)} configured stocks..."):
                st.session_state["scan"]=scan_all()
            st.rerun()
        if st.button("🧹 CLEAR RESULT",use_container_width=True):
            st.session_state.pop("scan",None)
            st.rerun()
        st.markdown("---")
        st.markdown("**Decision Horizon**")
        st.caption("⚡ Daily 1–5 hari\n\n📈 Swing 1–6 minggu\n\n🏦 Investor 3–24 bulan")
        st.markdown("---")
        st.caption("OHLCV baseline: yfinance • Single Stock chart: TradingView")

    # Institutional-style market strip
    if regime:
        rc=st.columns(4)
        rc[0].markdown(f'<div class="kpi"><div class="kpi-label">IHSG</div><div class="kpi-value">{regime["close"]:,.0f}</div><div class="kpi-sub">Market level</div></div>',unsafe_allow_html=True)
        rc[1].markdown(f'<div class="kpi"><div class="kpi-label">MARKET SCORE</div><div class="kpi-value">{regime["score"]}<span class="kpi-unit">/100</span></div><div class="kpi-sub">Regime strength</div></div>',unsafe_allow_html=True)
        regime_kind="green" if regime["regime"]=="BULLISH" else "yellow" if regime["regime"]=="SIDEWAYS" else "red"
        rc[2].markdown(f'<div class="kpi"><div class="kpi-label">MARKET REGIME</div><div class="kpi-value small-value">{regime["regime"]}</div><div class="kpi-sub">{badge(regime["gate"],regime_kind)}</div></div>',unsafe_allow_html=True)
        rc[3].markdown(f'<div class="kpi"><div class="kpi-label">UNIVERSE</div><div class="kpi-value">{len(UNIVERSE)}</div><div class="kpi-sub">Configured stocks</div></div>',unsafe_allow_html=True)

    def style_page(style,title,desc):
        st.markdown(f'<div class="section-title">{title}</div><p class="section-subtitle">{desc}</p>',unsafe_allow_html=True)
        if scan.empty:
            st.info("Run / Refresh Scan terlebih dahulu."); return
        sdf=add_style_columns(scan,style)
        p=sdf[sdf["Style Gate"]=="PASS"].head(3)
        near=sdf[sdf["Style Gate"]=="NEAR PASS"].head(10)
        m=st.columns(5)
        m[0].metric("Universe",len(UNIVERSE)); m[1].metric("Scanned",len(sdf)); m[2].metric("PASS",len(sdf[sdf["Style Gate"]=="PASS"])); m[3].metric("Near Pass",len(sdf[sdf["Style Gate"]=="NEAR PASS"])); m[4].metric("Candidates",len(p)+len(near))
        if p.empty: st.warning("Belum ada PASS untuk mode ini. Kandidat Near Pass tetap ditampilkan.")
        else:
            st.markdown("### Top Actionable")
            cc=st.columns(len(p))
            for col,(_,r) in zip(cc,p.iterrows()):
                with col:
                    st.markdown(f'''<div class="action-card"><div class="ticker">{r.Ticker}</div><div class="small">{r.Sector} • {r.Setup}</div><div class="score">{r["Style Score"]:.1f}<span>/100</span></div><div class="rowline"><span>Gate</span><b>{r["Style Gate"]}</b></div><div class="rowline"><span>Entry</span><b>{rupiah(r.Entry)}</b></div><div class="rowline"><span>Buy Range</span><b>{rupiah(r["Buy Low"])} – {rupiah(r["Buy High"])}</b></div><div class="rowline"><span>Stop Loss</span><b class="danger">{rupiah(r["Stop Loss"])}</b></div><div class="rowline"><span>R:R TP2</span><b>1:{r["R:R TP2"]:.2f}</b></div></div>''',unsafe_allow_html=True)
                    if st.button(f"🔎 Analyze {r.Ticker}",key=f"quick_{style}_{r.Ticker}",use_container_width=True):
                        st.session_state["single_ticker"]=r.Ticker
                        st.session_state["nav_request"]="🔎 Single Stock"
                        st.rerun()
        with st.expander(f"📋 Candidate Table — {title} • klik untuk tampilkan",expanded=False):
            candidate_cols=["Ticker","Sector","Price","Entry","Buy Low","Buy High","Stop Loss","TP1","TP2","Style Score","Style Gate","Style Action","Horizon","Trend","Setup","Risk","R:R TP1","R:R TP2","RSI","VolumeRatio"]
            st.dataframe(vivid_style(money_cols(sdf[candidate_cols].head(50))),use_container_width=True,hide_index=True,height=560)

    if page=="🏠 Dashboard":
        st.markdown('<div class="section-title">Decision Overview</div>',unsafe_allow_html=True)
        if scan.empty:
            cards=st.columns(3)
            cards[0].markdown(style_card("⚡ Daily Trading","Momentum, breakout/pullback dan eksekusi 1–5 hari.",("1–5 DAYS","blue")),unsafe_allow_html=True)
            cards[1].markdown(style_card("📈 Swing Weekly","Trend, struktur, support/resistance dan R:R.",("1–6 WEEKS","green")),unsafe_allow_html=True)
            cards[2].markdown(style_card("🏦 Investor","MA200, trend jangka panjang dan konfirmasi.",("3–24 MONTHS","yellow")),unsafe_allow_html=True)
            st.info("Klik **RUN / REFRESH SCAN** di Control Center untuk mengisi dashboard.")
        else:
            p=scan[scan.Gate=="PASS"]; n=scan[scan.Gate=="NEAR PASS"]
            m=st.columns(6)
            for col,label,val in zip(m,["Stocks Scanned","PASS","Near Pass","Top 10","Top 3","Universe"],[len(scan),len(p),len(n),min(10,len(scan)),min(3,len(p)),len(UNIVERSE)]): col.metric(label,val)
            st.markdown('<div class="section-title">Top Actionable Across Styles</div>',unsafe_allow_html=True)
            for style,title in [("DAILY","⚡ Daily Trading"),("SWING","📈 Swing Weekly"),("INVESTOR","🏦 Investor")]:
                sdf=add_style_columns(scan,style); sdf=sdf[sdf["Style Gate"].isin(["PASS","NEAR PASS"])].head(3)
                st.markdown(f"### {title}")
                if sdf.empty: st.caption("Belum ada candidate.")
                else:
                    cols=st.columns(len(sdf))
                    for col,(_,r) in zip(cols,sdf.iterrows()):
                        with col:
                            st.markdown(f'''<div class="mini-card"><div class="ticker">{r.Ticker}</div><div class="small">{r.Sector} • {r.Setup}</div><div class="score">{r["Style Score"]:.1f}<span>/100</span></div><div>Entry <b>{rupiah(r.Entry)}</b></div><div>Buy <b>{rupiah(r["Buy Low"])} – {rupiah(r["Buy High"])}</b></div><div>SL <b class="danger">{rupiah(r["Stop Loss"])}</b></div><div>R:R <b>1:{r["R:R TP2"]:.2f}</b></div></div>''',unsafe_allow_html=True)
                            if st.button(f"🔎 {r.Ticker}",key=f"dash_{style}_{r.Ticker}",use_container_width=True):
                                st.session_state["single_ticker"]=r.Ticker
                                st.session_state["nav_request"]="🔎 Single Stock"
                                st.rerun()
            st.markdown('<div class="section-title">Quick Single Stock</div>',unsafe_allow_html=True)
            qcols=st.columns([3,1,1])
            default_ticker=st.session_state.get("single_ticker", scan.iloc[0].Ticker if not scan.empty else "BBRI")
            tickers=sorted(scan.Ticker.unique().tolist())
            qcols[0].selectbox("Pilih saham dari hasil scanner",tickers,index=tickers.index(default_ticker) if default_ticker in tickers else 0,key="dashboard_stock_pick")
            if qcols[1].button("🔎 Buka Single Stock",use_container_width=True):
                st.session_state["single_ticker"]=st.session_state["dashboard_stock_pick"]
                st.session_state["nav_request"]="🔎 Single Stock"
                st.rerun()
            qcols[2].caption("Chart utama: TradingView")

    elif page=="⚡ Daily Trading":
        style_page("DAILY","⚡ DAILY TRADING","Momentum dan setup cepat untuk horizon sekitar 1–5 hari.")
    elif page=="📈 Swing Weekly":
        style_page("SWING","📈 SWING TRADING MINGGUAN","Trend-following, breakout/pullback, support-resistance dan R:R untuk horizon 1–6 minggu.")
    elif page=="🏦 Investor":
        style_page("INVESTOR","🏦 INVESTOR JANGKA PANJANG","Filter MA200, struktur trend dan risk/reward untuk horizon 3–24 bulan.")
    elif page=="📊 Sector Opportunity":
        st.markdown('<div class="section-title">📊 Sector Opportunity — Dynamic</div>',unsafe_allow_html=True)
        st.caption("Sektor dihitung dari technical strength, opportunity, bullish breadth, momentum 20D, volume dan pass rate.")
        if scan.empty: st.info("Run scanner terlebih dahulu.")
        else:
            sec=sector_opportunity(scan)
            st.markdown("### Sector Ranking")
            header=st.columns([2.2,0.6,1,1,0.9,1,0.9,1,1,0.9,0.9])
            for h,label in zip(header,["Sector","Stocks","Avg Tech","Avg Opp.","Volume","Bullish","Mom.20D","Pass Rate","Score","Status"," "]): h.markdown(f"<div class='small'><b>{label}</b></div>",unsafe_allow_html=True)
            for i,(_,r) in enumerate(sec.iterrows()):
                cols=st.columns([2.2,0.6,1,1,0.9,1,0.9,1,1,0.9,0.9]); cols[0].markdown(f"**{r['Sector']}**"); cols[1].write(int(r["Stocks"])); cols[2].write(f"{r['AvgTechnical']:.1f}"); cols[3].write(f"{r['AvgOpportunity']:.1f}"); cols[4].write(f"{r['AvgVolume']:.2f}x"); cols[5].write(f"{r['BullishBreadth']:.1f}%"); cols[6].write(f"{r['AvgMomentum20D']:.1f}%"); cols[7].write(f"{r['PassRate']:.1f}%"); cols[8].write(f"{r['Sector Score']:.1f}"); status=str(r["Status"]); kind="green" if "LEADING" in status else "yellow" if "WATCH" in status else "red"; cols[9].markdown(badge(status,kind),unsafe_allow_html=True)
                if cols[10].button("🔎 Saham",key=f"sector_view_{i}",use_container_width=True): st.session_state["selected_sector"]=str(r["Sector"]); st.rerun()
            selected=st.session_state.get("selected_sector","")
            if selected:
                with st.expander(f"🔎 Saham dalam sektor: {selected}",expanded=True):
                    sstocks=scan[scan.Sector==selected].copy(); showcols=["Ticker","Price","Technical","Opportunity","Gate","Risk","Trend","Setup","Entry","Buy Low","Buy High","Stop Loss","TP1","TP2","R:R TP2"]; avail=[c for c in showcols if c in sstocks.columns]
                    st.dataframe(vivid_style(money_cols(sstocks.sort_values(["Opportunity","Technical"],ascending=False)[avail].head(50))),use_container_width=True,hide_index=True,height=560)
                if st.button("✕ Tutup daftar sektor",key="close_sector"): st.session_state.pop("selected_sector",None); st.rerun()
            st.markdown("### 🔥 Sector Focus")
            lead=sec.head(3); cc=st.columns(len(lead))
            for col,(_,r) in zip(cc,lead.iterrows()):
                with col: st.markdown(f'<div class="action-card"><div class="ticker">{r["Sector"]}</div><div class="score">{r["Sector Score"]:.1f}<span>/100</span></div><div>{badge(r["Status"],"green" if "LEADING" in str(r["Status"]) else "yellow" if "WATCH" in str(r["Status"]) else "red")}</div><div class="small">{int(r["Stocks"])} saham • Breadth {r["BullishBreadth"]:.1f}% • Momentum {r["AvgMomentum20D"]:.1f}%</div></div>',unsafe_allow_html=True)

    elif page=="🏆 Top 150 / 50 / 10":
        if scan.empty: st.info("Run scanner terlebih dahulu.")
        else:
            for title,df in [("Top 150 Enrich",scan.sort_values("Opportunity",ascending=False).head(150)),("Top 50 Focus",scan.sort_values("Opportunity",ascending=False).head(50)),("Top 10 Opportunity",scan[scan.Gate.isin(["PASS","NEAR PASS"])].sort_values(["Opportunity","Technical","R:R TP2"],ascending=False).head(10))]:
                with st.expander(f"{title} • {len(df)} saham",expanded=False): st.dataframe(vivid_style(money_cols(df)),use_container_width=True,hide_index=True,height=520)

    elif page=="🔎 Single Stock":
        st.markdown('<div class="section-title">🔎 SINGLE STOCK ANALYSIS</div>',unsafe_allow_html=True)
        st.caption("Analisis satu saham dengan trading plan dan TradingView Advanced Chart.")
        available=sorted(scan.Ticker.unique().tolist()) if not scan.empty else []
        preset=st.session_state.get("single_ticker","BBRI")
        left,right=st.columns([2,1])
        with left:
            ticker_input=st.text_input("Kode saham IDX",preset).upper().strip().replace(".JK","")
        with right:
            interval=st.selectbox("Timeframe",["D","W","240","60"],index=0)
        if available:
            pick=st.selectbox("Pilih cepat dari hasil scanner",available,index=available.index(preset) if preset in available else 0)
            if st.button("Gunakan saham terpilih",use_container_width=True): ticker_input=pick; st.session_state["single_ticker"]=pick; st.rerun()
        if st.button("ANALYZE SINGLE STOCK",use_container_width=True): st.session_state["single_ticker"]=ticker_input; st.session_state["single_analyze"]=True
        if st.session_state.get("single_analyze",False):
            ticker=st.session_state.get("single_ticker",ticker_input); d=get_data(ticker)
            if d.empty: st.error("Data analisis tidak tersedia untuk ticker tersebut.")
            else:
                a,x=analyze(d)
                if a:
                    m=st.columns(6); m[0].metric("Price",rupiah(a["price"])); m[1].metric("Technical",f"{a['score']}/100"); m[2].metric("Opportunity",f"{a['opportunity']:.1f}/100"); m[3].metric("R:R TP2",f"1:{a['rr2']:.2f}"); m[4].metric("Gate",a["gate"]); m[5].metric("Risk",a["risk_level"])
                    st.markdown('<div class="section-title">Trading Plan</div>',unsafe_allow_html=True)
                    p=st.columns(5); p[0].markdown(f'<div class="buy-box"><b>BUY LOW</b><h3>{rupiah(a["entry_low"])}</h3></div>',unsafe_allow_html=True); p[1].markdown(f'<div class="buy-box"><b>BUY HIGH / ENTRY</b><h3>{rupiah(a["entry_high"])}</h3></div>',unsafe_allow_html=True); p[2].markdown(f'<div class="sl-box"><b>STOP LOSS</b><h3>{rupiah(a["stop"])}</h3></div>',unsafe_allow_html=True); p[3].markdown(f'<div class="tp-box"><b>TP1</b><h3>{rupiah(a["tp1"])}</h3></div>',unsafe_allow_html=True); p[4].markdown(f'<div class="tp-box"><b>TP2</b><h3>{rupiah(a["tp2"])}</h3></div>',unsafe_allow_html=True)
                    st.markdown(f'**Buy Range:** {rupiah(a["entry_low"])} – {rupiah(a["entry_high"])} &nbsp; | &nbsp; **Risk/share:** {rupiah(a["price"]-a["stop"])} &nbsp; | &nbsp; **R:R TP2:** 1:{a["rr2"]:.2f}',unsafe_allow_html=True)
                    st.write(f"**Setup:** {a['setup']}  •  **Action:** {a['action']}  •  **Confidence:** {a['confidence']}")
                    sf=scan[scan.Ticker==ticker].iloc[0] if not scan.empty and ticker in set(scan.Ticker) else None
                    if sf is not None:
                        fc=st.columns(6)
                        fc[0].metric("Fundamental", "N/A" if pd.isna(sf.get("Fundamental Strength")) else f"{sf['Fundamental Strength']:.1f}/100")
                        fc[1].metric("ROE", "N/A" if pd.isna(sf.get("roe")) else f"{sf['roe']:.2f}%")
                        fc[2].metric("NPM", "N/A" if pd.isna(sf.get("npm")) else f"{sf['npm']:.2f}%")
                        fc[3].metric("PER", "N/A" if pd.isna(sf.get("per")) else f"{sf['per']:.2f}x")
                        fc[4].metric("PBV", "N/A" if pd.isna(sf.get("pbv")) else f"{sf['pbv']:.2f}x")
                        fc[5].metric("DER", "N/A" if pd.isna(sf.get("der")) else f"{sf['der']:.2f}x")
                        st.caption(f"Fundamental source: {sf.get('Fundamental Data','N/A')} • official/authorized data only")
                    st.write(f"**Invalidation:** {a['invalidation']}")
                    st.markdown('<div class="tv-shell"><div class="section-title">📊 TradingView Advanced Chart</div><div class="small">Chart utama menggunakan widget resmi TradingView. Gunakan toolbar, timeframe, indikator dan drawing tools langsung pada chart.</div></div>',unsafe_allow_html=True)
                    tradingview_chart(ticker,interval=interval,height=820)

    elif page=="⚙️ System":
        st.markdown('<div class="section-title">⚙️ System Configuration</div>',unsafe_allow_html=True)
        st.write(f"Configured universe: **{len(UNIVERSE)}** tickers (target 300)")
        fdf=load_official_fundamentals()
        hc=st.columns(4)
        hc[0].metric("Universe",len(UNIVERSE)); hc[1].metric("Scanned",len(scan)); hc[2].metric("IDX Fundamental",len(fdf)); hc[3].metric("Fundamental Coverage",f"{(len(set(scan.Ticker)&set(fdf.ticker))/len(scan)*100 if not scan.empty and not fdf.empty else 0):.1f}%")
        st.markdown("### Data Governance")
        st.markdown("<span class='source-pill'>IDX Stock Screener</span><span class='source-pill'>IDX Financial Data & Ratios</span><span class='source-pill'>IDX-IC</span><span class='source-pill'>OJK Reporting</span>",unsafe_allow_html=True)
        st.caption("Fundamental Strength hanya dihitung jika data/idx_fundamental.csv berisi data yang berasal dari ekspor resmi IDX atau sumber berlisensi. Jika belum ada, nilai fundamental tetap N/A.")
        st.write("Universe file: `data/universe.csv` with embedded fallback.")
        st.info("Universe loader dirancang untuk GitHub/Streamlit Cloud dan akan memakai embedded 300-ticker fallback bila file lokal tidak tersedia.")
        st.write("### TradingView")
        st.write("Single Stock memakai TradingView Advanced Chart Widget dengan symbol dinamis `IDX:<TICKER>`. Widget resmi mendukung konfigurasi symbol, interval, studies, toolbar dan ukuran chart.")
        st.write("### Data source")
        st.warning("Baseline OHLCV scanner memakai yfinance untuk pengujian. Untuk produksi, gunakan data pasar yang sesuai lisensi dan kebutuhan operasional.")
        st.write("### Multi-Style")
        st.write("Daily Trading, Swing Weekly dan Investor memakai layer scoring/gate masing-masing." )


if __name__ == "__main__":
    main()
