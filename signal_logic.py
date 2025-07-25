import pandas as pd
import requests
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochRSIIndicator

def fetch_ohlcv(pair):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=50"
        response = requests.get(url)
        data = response.json()

        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "close_time", "quote_asset_volume", "number_of_trades",
            "taker_buy_base_vol", "taker_buy_quote_vol", "ignore"
        ])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print("❌ Failed to fetch data:", e)
        return None

def analyze_candle(pair):
    df = fetch_ohlcv(pair)
    if df is None or len(df) < 20:
        return None

    df["ema"] = EMAIndicator(df["close"], window=10).ema_indicator()
    df["rsi"] = RSIIndicator(df["close"], window=14).rsi()

    macd = MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    stoch = StochRSIIndicator(df["close"])
    df["stochrsi"] = stoch.stochrsi()

    latest = df.iloc[-1]
    score = 0
    conditions = []

    if latest["close"] > latest["ema"]:
        score += 1
        conditions.append("Price above EMA")

    if latest["rsi"] > 55:
        score += 1
        conditions.append("RSI bullish")

    if latest["macd"] > latest["macd_signal"]:
        score += 1
        conditions.append("MACD crossover UP")

    if latest["stochrsi"] > 0.5:
        score += 1
        conditions.append("StochRSI in buy zone")

    confidence = (score / 4) * 100

    if confidence >= 20:
        direction = "UP"
        if latest["close"] < latest["open"]:
            direction = "DOWN"
        return {
            "direction": direction,
            "confidence": confidence,
            "conditions": conditions,
            "chart_data": df[["time", "close", "ema", "rsi"]].set_index("time")
        }
    else:
        return None
