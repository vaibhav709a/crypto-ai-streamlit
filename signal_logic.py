import requests
import pandas as pd

def fetch_candle_data(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=5m&limit=100"
    response = requests.get(url)
    data = response.json()

    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    
    return df

def check_bb_red_candle(symbol):
    df = fetch_candle_data(symbol)
    if df is None or len(df) < 21:
        return None

    df['ma20'] = df['close'].rolling(window=20).mean()
    df['stddev'] = df['close'].rolling(window=20).std()
    df['upper_bb'] = df['ma20'] + (2 * df['stddev'])
    df['lower_bb'] = df['ma20'] - (2 * df['stddev'])

    last_candle = df.iloc[-2]  # previous completed candle
    if (
        last_candle['close'] < last_candle['open'] and
        last_candle['high'] >= last_candle['upper_bb']
    ):
        return f"{symbol} 🔻 RED candle hit upper BB"
    
    return None
