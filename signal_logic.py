import requests
import pandas as pd
import numpy as np

def fetch_ohlcv(pair):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=50"
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_asset_volume', 'number_of_trades',
            'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
        ])
        df['close'] = df['close'].astype(float)
        df['open'] = df['open'].astype(float)
        return df
    except Exception as e:
        print(f"Error fetching {pair}: {e}")
        return None

def check_bb_red_candle(pair):
    df = fetch_ohlcv(pair)
    if df is None or len(df) < 20:
        return None

    df['ma'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper_bb'] = df['ma'] + 2 * df['std']
    last = df.iloc[-1]

    if last['close'] < last['open'] and last['high'] >= last['upper_bb']:
        return f"{pair}: DOWN signal (red candle touched upper BB)"
    return None    hit_bb = high_price >= upper

    if is_red and hit_bb:
        return {
            "pair": pair,
            "direction": "DOWN",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    return None
