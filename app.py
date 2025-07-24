import streamlit as st
from signal_logic import analyze_candle

# List of 50+ popular crypto pairs (adjust as needed)
pairs = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT", "DOGE/USDT", "DOT/USDT",
    "AVAX/USDT", "TRX/USDT", "MATIC/USDT", "SHIB/USDT", "LTC/USDT", "LINK/USDT", "BCH/USDT", "ATOM/USDT",
    "XLM/USDT", "FIL/USDT", "ICP/USDT", "NEAR/USDT", "ARB/USDT", "HBAR/USDT", "APT/USDT", "VET/USDT",
    "OP/USDT", "QNT/USDT", "EGLD/USDT", "STX/USDT", "GRT/USDT", "IMX/USDT", "SAND/USDT", "MANA/USDT",
    "THETA/USDT", "RNDR/USDT", "PEPE/USDT", "FET/USDT", "RUNE/USDT", "1INCH/USDT", "LDO/USDT", "CRV/USDT",
    "DYDX/USDT", "ZIL/USDT", "FLOW/USDT", "CHZ/USDT", "AGIX/USDT", "ANKR/USDT", "COTI/USDT", "INJ/USDT",
    "TWT/USDT", "GMT/USDT", "ENS/USDT", "SNX/USDT", "YFI/USDT", "KAVA/USDT", "BAL/USDT", "NKN/USDT"
]

st.set_page_config(page_title="📊 Crypto AI Signal Scanner", layout="wide")
st.title("📈 Real-Time Crypto AI Signal Scanner")
st.caption("Shows high-confidence 5-minute trade signals using EMA, RSI, MACD, and StochRSI")

# Button to refresh signals
if st.button("🔍 Scan All Pairs Now"):
    results = []
    with st.spinner("Analyzing all pairs..."):
        for pair in pairs:
            result = analyze_candle(pair)
            if result:
                results.append({
                    "Pair": pair,
                    "Direction": result["direction"],
                    "Confidence (%)": round(result["confidence"], 2),
                    "Conditions": ", ".join(result["conditions"])
                })

    if results:
        st.success(f"✅ Found {len(results)} high-confidence signals")
        st.dataframe(results)
    else:
        st.warning("⚠️ No high-confidence signals found right now.")
else:
    st.info("👆 Click the button above to start scanning 50+ crypto pairs.")
