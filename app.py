import streamlit as st
from signal_logic import check_bb_red_candle

st.title("Simple BB Red Candle Signal Bot")

if st.button("Scan for Signals"):
    signals = check_bb_red_candle()
    if signals:
        for signal in signals:
            st.success(signal)
    else:
        st.warning("No signals found right now.")st.title("🔍 BB Upper + Red Candle Signal Detector")

df = generate_sample_data()

st.line_chart(df[['close', 'BB_upper', 'BB_middle', 'BB_lower']])

if check_bb_red_candle(df):
    st.success("✅ Signal Detected: Red candle touched BB upper line!")
else:
    st.info("ℹ️ No signal detected on latest candle.")
