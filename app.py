# app.py

import streamlit as st
import pandas as pd
import numpy as np
from signal_logic import check_bb_red_candle

# Sample Data Generator with Bollinger Bands
def generate_sample_data():
    np.random.seed(42)
    data = {'open': [], 'high': [], 'low': [], 'close': []}
    price = 100

    for _ in range(100):
        change = np.random.normal(0, 1)
        open_ = price
        close = price + change
        high = max(open_, close) + np.random.rand()
        low = min(open_, close) - np.random.rand()

        data['open'].append(open_)
        data['high'].append(high)
        data['low'].append(low)
        data['close'].append(close)

        price = close

    df = pd.DataFrame(data)
    df['BB_middle'] = df['close'].rolling(window=20).mean()
    df['BB_std'] = df['close'].rolling(window=20).std()
    df['BB_upper'] = df['BB_middle'] + (2 * df['BB_std'])
    df['BB_lower'] = df['BB_middle'] - (2 * df['BB_std'])
    return df.dropna()

# Streamlit UI
st.set_page_config(page_title="Bollinger Band Red Candle Detector", layout="centered")
st.title("🔍 BB Upper + Red Candle Signal Detector")

df = generate_sample_data()

st.line_chart(df[['close', 'BB_upper', 'BB_middle', 'BB_lower']])

if check_bb_red_candle(df):
    st.success("✅ Signal Detected: Red candle touched BB upper line!")
else:
    st.info("ℹ️ No signal detected on latest candle.")
