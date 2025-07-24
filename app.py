import streamlit as st
from signal_logic import analyze_candle

# Define list of USDT crypto pairs to analyze
pairs = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "XRP/USDT", "ADA/USDT",
    "DOGE/USDT", "MATIC/USDT", "DOT/USDT", "LTC/USDT", "TRX/USDT",
    "AVAX/USDT", "LINK/USDT", "UNI/USDT", "BCH/USDT", "ATOM/USDT",
    "ETC/USDT", "XLM/USDT", "NEAR/USDT", "FIL/USDT", "ICP/USDT"
]

st.set_page_config(page_title="AI Crypto Signal", layout="centered")
st.title("📊 AI Crypto Signal Predictor")
st.markdown("Get **AI-analyzed 5-minute UP/DOWN direction** with >97% confidence.")

st.markdown("---")
st.write("Select pairs to analyze or scan all:")

selected_pairs = st.multiselect("Select Crypto Pairs", options=pairs, default=pairs[:5])

if st.button("🔍 Scan Selected Pairs"):
    st.info("Analyzing selected pairs... please wait.")
    for pair in selected_pairs:
        try:
            result = analyze_candle(pair)
            if result:
                st.success(f"📈 {pair} — **{result['direction']}** Signal (Confidence: {result['confidence']:.2f}%)")
                st.markdown("**Conditions Matched:**")
                for cond in result["conditions"]:
                    st.markdown(f"- {cond}")
                st.line_chart(result["chart_data"])
            else:
                st.warning(f"❌ No strong signal for {pair}")
        except Exception as e:
            st.error(f"Error analyzing {pair}: {str(e)}")

st.markdown("---")
st.caption("Powered by AI + Real-time Candle Analysis (TwelveData or compatible)")
