import streamlit as st
from signal_logic import check_bb_red_candle

st.set_page_config(page_title="BB Red Candle Signal", layout="centered")
st.title("📉 Simple BB Red Candle Signal Scanner")

top_50_pairs = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "XRPUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT",
    "DOTUSDT", "AVAXUSDT", "TRXUSDT", "LINKUSDT", "MATICUSDT", "LTCUSDT", "SHIBUSDT",
    "BCHUSDT", "XLMUSDT", "UNIUSDT", "HBARUSDT", "APTUSDT", "ARBUSDT", "ETCUSDT",
    "FILUSDT", "ICPUSDT", "VETUSDT", "IMXUSDT", "MKRUSDT", "EGLDUSDT", "NEARUSDT",
    "SANDUSDT", "GALAUSDT", "THETAUSDT", "STXUSDT", "CHZUSDT", "FTMUSDT", "AAVEUSDT",
    "INJUSDT", "RNDRUSDT", "CRVUSDT", "PEPEUSDT", "KAVAUSDT", "RUNEUSDT", "1INCHUSDT",
    "FLMUSDT", "ZILUSDT", "ENJUSDT", "CVCUSDT", "ICXUSDT", "XEMUSDT", "ANKRUSDT", "RSRUSDT"
]

if st.button("🔍 Scan for Signals"):
    signals = []
    with st.spinner("Scanning..."):
        for pair in top_50_pairs:
            signal = check_bb_red_candle(pair)
            if signal:
                signals.append(signal)

    if signals:
        st.success("✅ Signals Found:")
        for s in signals:
            st.write(f"➡️ {s}")
    else:
        st.warning("❌ No valid signals found right now.")
