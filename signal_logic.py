import requests
import pandas as pd

def fetch_ohlcv(pair):
    url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=30"
    response = requests.get(url)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base', 'taker_buy_quote', 'ignore'
    ])
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df[['timestamp', 'open', 'high', 'low', 'close']]

def check_bb_red_candle(pair):
    df = fetch_ohlcv(pair)

    if df is None or len(df) < 20:
        return None

    df['ma'] = df['close'].rolling(window=20).mean()
    df['std'] = df['close'].rolling(window=20).std()
    df['upper'] = df['ma'] + 2 * df['std']
    df['lower'] = df['ma'] - 2 * df['std']

    last = df.iloc[-1]

    if last['high'] >= last['upper'] and last['close'] < last['open']:
        return {
            "pair": pair,
            "direction": "DOWN",
            "timestamp": str(last['timestamp'])
        }

    return None
