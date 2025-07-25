
import requests
import datetime
import numpy as np

API_KEY = "806dd29a09244737ae6cd1a305061557"

def get_latest_candles(pair):
    url = f"https://financialmodelingprep.com/api/v3/historical-chart/1min/{pair}?apikey={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()[:20]
    else:
        return []

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    sma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, lower

def check_bb_red_candle(pair):
    candles = get_latest_candles(pair)
    if len(candles) < 20:
        return None

    closes = [float(c['close']) for c in candles]
    upper, _ = calculate_bollinger_bands(closes)

    latest = candles[0]
    open_price = float(latest['open'])
    close_price = float(latest['close'])
    high_price = float(latest['high'])

    is_red = close_price < open_price
    hit_bb = high_price >= upper

    if is_red and hit_bb:
        return {
            "pair": pair,
            "direction": "DOWN",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    return None
