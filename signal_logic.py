import requests
import datetime
import numpy as np

API_KEY = "YOUR_FMP_API_KEY"

def get_latest_candles(pair):
    url = f"https://financialmodelingprep.com/api/v3/historical-chart/1min/{pair}?apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()
    return data[:20]  # Get latest 20 candles

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    prices = np.array(prices)
    sma = np.mean(prices)
    std = np.std(prices)
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, lower

def check_bb_red_candle(pair):
    candles = get_latest_candles(pair)

    if len(candles) < 20:
        return None

    # Extract closes for BB
    closes = [float(c["close"]) for c in candles]
    upper, _ = calculate_bollinger_bands(closes)

    # Get latest candle
    current = candles[0]
    open_price = float(current["open"])
    close_price = float(current["close"])
    high_price = float(current["high"])

    is_red = close_price < open_price
    touched_upper = high_price >= upper

    if is_red and touched_upper:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return {
            "pair": pair,
            "direction": "DOWN",
            "timestamp": timestamp
        }

    return None
