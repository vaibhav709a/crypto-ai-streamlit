# signal_logic.py

import pandas as pd

def check_bb_red_candle(df):
    if df is None or len(df) < 2:
        return False

    last_candle = df.iloc[-2]  # Previous closed candle
    bb_upper = df['BB_upper'].iloc[-2]

    is_red = last_candle['close'] < last_candle['open']
    touches_upper = last_candle['high'] >= bb_upper

    return is_red and touches_upper
