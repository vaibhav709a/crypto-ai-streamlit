import streamlit as st
from signal_logic import check_bb_red_candle

st.set_page_config(page_title="BB Signal", layout="centered")

st.title("🔴 Bollinger Band Red Candle Signal")

pairs = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "MATICUSDT", "DOTUSDT",
    "SHIBUSDT", "LTCUSDT", "TRXUSDT", "LINKUSDT", "BCHUSDT",
    "XLMUSDT", "ATOMUSDT", "ETCUSDT", "FILUSDT", "SANDUSDT"
]

if st.button("📡 Check All 20 Pairs Now"):
    with st.spinner("Checking signals..."):
        found = False
        for pair in pairs:
            try:
                if check_bb_red_candle(pair):
                    st.success(f"📉 Red Candle Hit BB ➜ {pair}")
                    found = True
            except Exception as e:
                st.warning(f"Error checking {pair}: {str(e)}")

        if not found:
            st.info("No signal found at this moment.")
