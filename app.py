import streamlit as st
import pandas as pd
from signal_logic import analyze_candle

st.set_page_config(page_title="AI Crypto Analyzer", layout="wide")
st.title("🚀 AI Crypto Candle Analyzer")

pairs = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
    "ADA/USDT", "DOGE/USDT", "MATIC/USDT", "DOT/USDT", "SHIB/USDT",
    "AVAX/USDT", "LTC/USDT", "LINK/USDT", "ATOM/USDT", "UNI/USDT",
    "NEAR/USDT", "APT/USDT", "ETC/USDT", "TRX/USDT", "FIL/USDT"
]

selected_pair = st.selectbox("Select Crypto Pair", pairs)

with st.spinner("Analyzing..."):
    signal_result = analyze_candle(selected_pair)

if signal_result:
    st.subheader(f"Prediction for next 5m candle:")
    st.metric("Direction", "📈 UP" if signal_result["direction"] == "UP" else "📉 DOWN")
    st.metric("Confidence", f'{signal_result["confidence"]:.2f}%')
    st.line_chart(signal_result["chart_data"][-20:][["close", "ema", "rsi"]])
else:
    st.warning("No strong signal (97%+ confidence) found.")
