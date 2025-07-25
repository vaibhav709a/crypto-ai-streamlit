import streamlit as st
import pandas as pd
import requests
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochRSIIndicator

st.set_page_config(page_title="Crypto Signal Analyzer", layout="wide")
st.title("🔍 Crypto Signal Analyzer")
st.caption("Click below to check market signals using real-time Binance data")

# ✅ Define 100 popular crypto pairs (Binance format)
pairs = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT",
    "DOGEUSDT", "SHIBUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "TRXUSDT", "LINKUSDT",
    "BCHUSDT", "ATOMUSDT", "XLMUSDT", "UNIUSDT", "ETCUSDT", "NEARUSDT", "INJUSDT",
    "OPUSDT", "ARBUSDT", "APTUSDT", "GRTUSDT", "SANDUSDT", "MANAUSDT", "RNDRUSDT",
    "FTMUSDT", "EGLDUSDT", "AAVEUSDT", "RUNEUSDT", "ALGOUSDT", "FLOWUSDT", "KAVAUSDT",
    "AXSUSDT", "CHZUSDT", "CRVUSDT", "DYDXUSDT", "HBARUSDT", "ONEUSDT", "BANDUSDT",
    "SNXUSDT", "WAVESUSDT", "ZILUSDT", "CELRUSDT", "SKLUSDT", "COTIUSDT", "ENSUSDT",
    "LINAUSDT", "FLMUSDT", "STMXUSDT", "TOMOUSDT", "ZRXUSDT", "NKNUSDT", "LRCUSDT",
    "OCEANUSDT", "STORJUSDT", "SXPUSDT", "KNCUSDT", "MTLUSDT", "OMGUSDT", "BAKEUSDT",
    "BELUSDT", "CTKUSDT", "FETUSDT", "LITUSDT", "ROSEUSDT", "PERPUSDT", "CVCUSDT",
    "ANTUSDT", "BNTUSDT", "REEFUSDT", "TRBUSDT", "TLMUSDT", "ANKRUSDT", "QTUMUSDT",
    "IOSTUSDT", "BICOUSDT", "GALUSDT", "PEOPLEUSDT", "BICOUSDT", "MASKUSDT", "HOOKUSDT",
    "HIGHUSDT", "AGIXUSDT", "ACHUSDT", "CFXUSDT", "NMRUSDT", "IDUSDT", "KLAYUSDT",
    "JOEUSDT", "XNOUSDT", "LAZIOUSDT", "XECUSDT", "GALAUSDT", "DASHUSDT", "YFIUSDT",
    "ALICEUSDT", "BALUSDT", "DEGOUSDT", "TWTUSDT", "ICXUSDT"
]

def fetch_ohlcv(pair):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=50"
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume",
                                         "_", "_", "_", "_", "_", "_"])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df["close"] = pd.to_numeric(df["close"])
        df["open"] = pd.to_numeric(df["open"])
        return df
    except:
        return None

def analyze_candle(pair):
    df = fetch_ohlcv(pair)
    if df is None or len(df) < 20:
        return None

    df["ema"] = EMAIndicator(df["close"], window=10).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], window=14).rsi()

    macd = MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    stoch = StochRSIIndicator(df["close"])
    df["stochrsi"] = stoch.stochrsi()

    latest = df.iloc[-1]
    score = 0
    conditions = []

    if latest["close"] > latest["ema"]:
        score += 1
        conditions.append("📈 Price above EMA")

    if latest["rsi"] > 55:
        score += 1
        conditions.append("💪 RSI bullish")

    if latest["macd"] > latest["macd_signal"]:
        score += 1
        conditions.append("🔄 MACD crossover UP")

    if latest["stochrsi"] > 0.5:
        score += 1
        conditions.append("⚡ StochRSI in buy zone")

    confidence = (score / 4) * 100

    if confidence >= 5:
        direction = "UP"
        if latest["close"] < latest["open"]:
            direction = "DOWN"
        return {
            "pair": pair,
            "direction": direction,
            "confidence": confidence,
            "conditions": conditions
        }
    else:
        return None

# 🚀 BUTTON TO RUN
if st.button("🚦 Get Signals"):
    with st.spinner("Analyzing markets..."):
        signals = []
        for pair in pairs:
            result = analyze_candle(pair)
            if result:
                signals.append(result)

    if signals:
        st.success(f"Found {len(signals)} sureshot signals:")
        for sig in signals:
            st.markdown(f"### {sig['pair']}")
            st.write(f"📊 **Direction:** {sig['direction']} — 🔥 Confidence: `{sig['confidence']:.0f}%`")
            for cond in sig['conditions']:
                st.write(f"- {cond}")
    else:
        st.warning("No high-confidence signals found at the moment.")
