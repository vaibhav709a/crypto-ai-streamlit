import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime

st.set_page_config(page_title="🔥 Crypto Signal Scanner", layout="wide")
st.title("📈 5-Minute Crypto Signal Bot")
st.markdown("**Analyzing live Binance data on 5-min chart...**")

# ✅ 100 top Binance trading pairs
pairs = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT",
    "DOTUSDT", "TRXUSDT", "MATICUSDT", "LINKUSDT", "LTCUSDT", "BCHUSDT", "ETCUSDT", "XLMUSDT",
    "ATOMUSDT", "NEARUSDT", "HBARUSDT", "ICPUSDT", "FILUSDT", "SANDUSDT", "APEUSDT", "INJUSDT",
    "ARBUSDT", "GMXUSDT", "DYDXUSDT", "RUNEUSDT", "LDOUSDT", "CROUSDT", "FTMUSDT", "EGLDUSDT",
    "GALAUSDT", "AAVEUSDT", "AXSUSDT", "RNDRUSDT", "FLOWUSDT", "MKRUSDT", "KAVAUSDT", "ZECUSDT",
    "ALGOUSDT", "BATUSDT", "BLURUSDT", "SUIUSDT", "PEPEUSDT", "FLOKIUSDT", "WLDUSDT", "ENSUSDT",
    "1INCHUSDT", "XMRUSDT", "JASMYUSDT", "ZILUSDT", "COMPUSDT", "COTIUSDT", "BELUSDT", "HOOKUSDT",
    "JOEUSDT", "ACHUSDT", "TWTUSDT", "IDUSDT", "STXUSDT", "YFIUSDT", "GMTUSDT", "OMGUSDT", "WOOUSDT",
    "HFTUSDT", "LINAUSDT", "NKNUSDT", "ANTUSDT", "SKLUSDT", "OCEANUSDT", "BANDUSDT", "KSMUSDT",
    "VETUSDT", "REEFUSDT", "RSRUSDT", "DENTUSDT", "ALICEUSDT", "CHZUSDT", "MASKUSDT", "TOMOUSDT",
    "QTUMUSDT", "STORJUSDT", "SCRTUSDT", "CVCUSDT", "BALUSDT", "XEMUSDT", "ZENUSDT", "TRBUSDT",
    "LPTUSDT", "POLYXUSDT", "CKBUSDT", "KLAYUSDT", "BADGERUSDT", "AGIXUSDT", "FXSUSDT", "GALUSDT",
    "RNDRUSDT", "YGGUSDT"
]

# 📊 Signal Logic
def analyze_candle(df):
    try:
        last = df.iloc[-1]
        prev = df.iloc[-2]

        up_condition = (
            last['close'] > last['open'] and  # green candle
            last['close'] > last['ema'] and
            last['rsi'] < 70 and
            last['macd'] > last['macd_signal']
        )

        down_condition = (
            last['close'] < last['open'] and  # red candle
            last['close'] < last['ema'] and
            last['rsi'] > 30 and
            last['macd'] < last['macd_signal']
        )

        confidence = 0
        if last['close'] > last['open']: confidence += 25
        if last['close'] > last['ema']: confidence += 25
        if last['rsi'] < 70: confidence += 25
        if last['macd'] > last['macd_signal']: confidence += 25

        if confidence >= 5:  # relaxed threshold for testing
            direction = "🔼 UP" if up_condition else "🔽 DOWN" if down_condition else "⚠️ Unclear"
            return direction, confidence
        else:
            return None, confidence
    except Exception as e:
        print(f"Error in analysis: {e}")
        return None, 0

# 🟢 Fetch OHLCV from Binance API
def fetch_ohlcv(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=50"
        res = requests.get(url)
        data = res.json()
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "_", "_", "_", "_", "_", "_"
        ])
        df["time"] = pd.to_datetime(df["time"], unit='ms')
        df[["open", "high", "low", "close", "volume"]] = df[["open", "high", "low", "close", "volume"]].astype(float)

        # Indicators
        df['ema'] = df['close'].ewm(span=10).mean()
        df['rsi'] = compute_rsi(df['close'])
        macd_line, signal_line = compute_macd(df['close'])
        df['macd'] = macd_line
        df['macd_signal'] = signal_line
        return df
    except Exception as e:
        print(f"{symbol} fetch error: {e}")
        return None

# 🧮 RSI
def compute_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

# 🧮 MACD
def compute_macd(series):
    ema12 = series.ewm(span=12).mean()
    ema26 = series.ewm(span=26).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()
    return macd, signal

# 🔍 Signal scanner
def get_all_signals():
    results = []
    for pair in pairs:
        df = fetch_ohlcv(pair)
        if df is not None:
            direction, confidence = analyze_candle(df)
            if direction:
                results.append((pair, direction, confidence))
            else:
                print(f"{pair} → ❌ No strong signal (Conf: {confidence}%)")
    return results

# 🚀 Button to Scan
if st.button("🔍 Scan for Signals"):
    with st.spinner("Scanning top 100 coins..."):
        signals = get_all_signals()
        if signals:
            for sym, dir, conf in signals:
                st.success(f"📊 {sym} → {dir} | Confidence: {conf:.1f}%")
        else:
            st.warning("No signals found. Try again in 5 min.")
