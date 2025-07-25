import streamlit as st
from signal_logic import check_bb_red_candle

symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT"]

st.set_page_config(page_title="BB + Red Candle Signal", layout="centered")
st.title("🔍 BB Upper + Red Candle Signal Detector")

found = False
for symbol in symbols:
    signal = check_bb_red_candle(symbol)
    if signal:
        st.success(signal)
        found = True

if not found:
    st.warning("No signals found right now.")
