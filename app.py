import requests
import pandas as pd
import time
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator, StochRSIIndicator

def fetch_ohlcv(pair):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={pair}&interval=5m&limit=50"
        response = requests.get(url)
        data = response.json()
        if not isinstance(data, list) or len(data) == 0:
            return None
        df = pd.DataFrame(data, columns=["time", "open", "high", "low", "close", "volume", "_", "_", "_", "_", "_", "_"])
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df["open"] = df["open"].astype(float)
        df["close"] = df["close"].astype(float)
        return df
    except Exception as e:
        print(f"[ERROR] Failed to fetch data for {pair}: {e}")
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
    if confidence >= 97:
        direction = "UP" if latest["close"] >= latest["open"] else "DOWN"
        return {
            "pair": pair,
            "direction": direction,
            "confidence": confidence,
            "conditions": conditions,
            "time": latest.name
        }
    else:
        return None

# 🔥 List of 100 Binance Pairs (top coins with USDT)
PAIR_LIST = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "MATICUSDT",
    "LTCUSDT", "TRXUSDT", "SHIBUSDT", "LINKUSDT", "BCHUSDT", "UNIUSDT", "XLMUSDT", "ATOMUSDT", "HBARUSDT", "ICPUSDT",
    "FILUSDT", "APTUSDT", "SUIUSDT", "ARBUSDT", "INJUSDT", "OPUSDT", "VETUSDT", "ETCUSDT", "GRTUSDT", "LDOUSDT",
    "MKRUSDT", "AAVEUSDT", "NEARUSDT", "QNTUSDT", "STXUSDT", "ALGOUSDT", "IMXUSDT", "FTMUSDT", "SNXUSDT", "THETAUSDT",
    "EOSUSDT", "CRVUSDT", "DYDXUSDT", "RUNEUSDT", "FLOWUSDT", "XTZUSDT", "KAVAUSDT", "GMXUSDT", "ENJUSDT", "1INCHUSDT",
    "ZECUSDT", "CHZUSDT", "SANDUSDT", "MANAUSDT", "APEUSDT", "AXSUSDT", "CELOUSDT", "COMPUSDT", "KSMUSDT", "DASHUSDT",
    "BANDUSDT", "COTIUSDT", "SKLUSDT", "ROSEUSDT", "ZILUSDT", "ARDRUSDT", "NMRUSDT", "LRCUSDT", "HOTUSDT", "STMXUSDT",
    "MTLUSDT", "OMGUSDT", "ANKRUSDT", "OCEANUSDT", "ICXUSDT", "WAVESUSDT", "YFIUSDT", "BELUSDT", "XEMUSDT", "KNCUSDT",
    "RLCUSDT", "CKBUSDT", "TOMOUSDT", "ZENUSDT", "CTSIUSDT", "QTUMUSDT", "PERLUSDT", "XNOUSDT", "BNTUSDT", "XVSUSDT",
    "RENUSDT", "WRXUSDT", "SCUSDT", "CVCUSDT", "BAKEUSDT", "BLZUSDT", "BICOUSDT", "ALICEUSDT", "TRBUSDT", "SYSUSDT"
]

# ✅ Run analysis for all pairs
def run_all_pairs():
    print("🔍 Scanning all 100 pairs for sureshot signals...\n")
    for pair in PAIR_LIST:
        result = analyze_candle(pair)
        if result:
            print(f"✅ SIGNAL | {result['pair']} | {result['direction']} | Confidence: {result['confidence']}%")
            print("    → Conditions:", ", ".join(result["conditions"]))
            print("    → Time:", result["time"])
            print("-" * 50)
        time.sleep(0.2)  # Avoid API rate limit

if __name__ == "__main__":
    run_all_pairs()
