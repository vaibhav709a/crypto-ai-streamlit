import requests
import pandas as pd

def fetch_ohlcv(pair):
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=50"
    response = requests.get(url)
    data = response.json()
    ohlcv = []

    for d in data:
        ohlcv.append({
            'timestamp': d[0],
            'open': float(d[1]),
            'high': float(d[2]),
            'low': float(d[3]),
            'close': float(d[4]),
            'volume': float(d[5]),
        })

    return pd.DataFrame(ohlcv)

def check_bb_red_candle(pair):
    df = fetch_ohlcv(pair)

    if len(df) < 20:
        return False  # Not enough data

    df['MA20'] = df['close'].rolling(window=20).mean()
    df['STD20'] = df['close'].rolling(window=20).std()
    df['UpperBB'] = df['MA20'] + 2 * df['STD20']

    last_candle = df.iloc[-1]

    # Condition: candle touched upper band AND closed red
    if last_candle['high'] >= last_candle['UpperBB'] and last_candle['close'] < last_candle['open']:
        return True

    return False
