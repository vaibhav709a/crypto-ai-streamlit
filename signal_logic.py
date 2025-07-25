import requests
import datetime

PAIRS = [
    "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT", "DOGE/USDT", "ADA/USDT",
    "AVAX/USDT", "DOT/USDT", "MATIC/USDT", "SHIB/USDT", "TRX/USDT", "LINK/USDT", "LTC/USDT",
    "UNI/USDT", "BCH/USDT", "NEAR/USDT", "ATOM/USDT", "ETC/USDT", "XLM/USDT", "HBAR/USDT",
    "ICP/USDT", "FIL/USDT", "CRO/USDT", "SAND/USDT", "EGLD/USDT", "MANA/USDT", "APT/USDT",
    "FTM/USDT", "GALA/USDT", "INJ/USDT", "AR/USDT", "AAVE/USDT", "RUNE/USDT", "KAVA/USDT",
    "LDO/USDT", "DYDX/USDT", "ZIL/USDT", "PEPE/USDT", "JTO/USDT", "WAVES/USDT", "STX/USDT",
    "AXS/USDT", "100+ more can be added..."
]

def get_candles(symbol):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol.replace('/', '')}&interval=5m&limit=20"
    r = requests.get(url)
    if r.status_code != 200:
        return []
    return r.json()

def calculate_bollinger_bands(closes):
    import statistics
    sma = statistics.mean(closes)
    stddev = statistics.stdev(closes)
    upper = sma + 2 * stddev
    lower = sma - 2 * stddev
    return upper, lower

def check_bb_red_candle():
    signal_list = []

    for pair in PAIRS:
        try:
            data = get_candles(pair)
            if not data or len(data) < 2:
                continue

            last = data[-2]
            open_price = float(last[1])
            close_price = float(last[4])
            closes = [float(c[4]) for c in data[-20:]]
            highs = [float(c[2]) for c in data[-20:]]

            upper_band, lower_band = calculate_bollinger_bands(closes)

            # BB hit and red candle
            if highs[-1] >= upper_band and close_price < open_price:
                now = datetime.datetime.utcnow().strftime("%H:%M UTC")
                signal_list.append(f"{pair} 🔻 Red candle at BB upper @ {now}")
        except:
            continue

    return signal_list
