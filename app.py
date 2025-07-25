import streamlit as st
import requests
import pandas as pd
import datetime
import time

st.set_page_config(page_title="Simple BB Signal", layout="wide")
st.title("📉 Bollinger Band Signal Scanner")

# Function to fetch OHLCV data
def fetch_ohlcv(pair):
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=20"
    response = requests.get(url)
    data = response.json()
    ohlcv = pd.DataFrame(data, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'trades',
        'taker_buy_base_vol', 'taker_buy_quote_vol', 'ignore'
    ])
    ohlcv['time'] = pd.to_datetime(ohlcv['time'], unit='ms')
    ohlcv[['open', 'high', 'low', 'close']] = ohlcv[['open', 'high', 'low', 'close']].astype(float)
    return ohlcv

# Function to check BB + red candle condition
def check_signal(df):
    df['MA'] = df['close'].rolling(window=20).mean()
    df['STD'] = df['close'].rolling(window=20).std()
    df['Upper'] = df['MA'] + 2 * df['STD']

    last = df.iloc[-1]
    # Signal condition: candle touches or exceeds upper BB and is red (close < open)
    if last['high'] >= last['Upper'] and last['close'] < last['open']:
        return True
    return False

# Top USDT Pairs (you can add more up to 100)
pairs = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'LINKUSDT', 'DOTUSDT',
    'TRXUSDT', 'MATICUSDT', 'SHIBUSDT', 'LTCUSDT', 'TONUSDT',
    'ATOMUSDT', 'XLMUSDT', 'UNIUSDT', 'HBARUSDT', 'IMXUSDT',
    'ETCUSDT', 'ICPUSDT', 'FILUSDT', 'SUIUSDT', 'APTUSDT',
    'INJUSDT', 'NEARUSDT', 'RUNEUSDT', 'GALAUSDT', 'PEPEUSDT',
    'SNXUSDT', 'THETAUSDT', 'ARBUSDT', 'AAVEUSDT', 'EOSUSDT',
    'OPUSDT', 'MKRUSDT', 'CRVUSDT', 'DYDXUSDT', 'CFXUSDT',
    'WOOUSDT', 'COTIUSDT', 'BCHUSDT', '1000SHIBUSDT', 'FETUSDT',
    'BANDUSDT', 'ZILUSDT', 'LDOUSDT', 'GMTUSDT', 'ONEUSDT'
]

if st.button("🔍 Scan All Pairs Now"):
    found = False
    with st.spinner("Analyzing all pairs..."):
        for pair in pairs:
            try:
                df = fetch_ohlcv(pair)
                if len(df) >= 20 and check_signal(df):
                    st.success(f"🔻 SHORT Signal: {pair} — Red candle hit upper BB!")
                    found = True
            except Exception as e:
                st.warning(f"{pair} failed: {e}")
                continue
    if not found:
        st.info("✅ No signals found at this moment.")
