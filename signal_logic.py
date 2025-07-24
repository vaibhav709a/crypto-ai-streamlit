import requests
import pandas as pd
import pandas_ta as ta

def fetch_ohlcv(symbol):
    base = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol.replace("/", ""),
        "interval": "5m",
        "limit": 100
    }
    try:
        response = requests.get(base, params=params)
        data = response.json()
        df = pd.DataFrame(data, columns=[
            "time", "open", "high", "low", "close", "volume",
            "_", "_", "_", "_", "_", "_"
        ])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df = df.astype({"open": float, "high": float, "low": float, "close": float, "volume": float})
        return df
    except:
        return None

def analyze_candle(pair):
    df = fetch_ohlcv(pair)
    if df is None or len(df) < 20:
        return None

    df["ema"] = ta.ema(df["close"], length=10)
    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    df = pd.concat([df, macd], axis=1)
    df["stochrsi"] = ta.stochrsi(df["close"])

    latest = df.iloc[-1]
    score = 0
    conditions = []

    if latest["close"] > latest["ema"]:
        score += 1
        conditions.append("Price above EMA")

    if latest["rsi"] > 55:
        score += 1
        conditions.append("RSI bullish")

    if latest["MACD_1"] > latest["MACDs_1"]:
        score += 1
        conditions.append("MACD crossover UP")

    if latest["stochrsi"] > 0.5:
        score += 1
        conditions.append("StochRSI in buy zone")

    confidence = (score / 4) * 100

    if confidence >= 97:
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
