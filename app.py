import time
from signal_logic import check_bb_red_candle
from telegram import send_signal

# List of top 50 pairs or your selected pairs
pairs = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT",
    "AVAXUSDT", "DOTUSDT", "SHIBUSDT", "LINKUSDT", "TRXUSDT", "MATICUSDT", "LTCUSDT"
    # Add more if needed
]

checked_pairs = {}  # To avoid duplicate alerts

while True:
    for pair in pairs:
        try:
            signal = check_bb_red_candle(pair)

            if signal:
                last_alert = checked_pairs.get(pair)
                current_time = signal["timestamp"]

                if last_alert != current_time:
                    send_signal(signal["pair"], signal["direction"], signal["timestamp"])
                    checked_pairs[pair] = current_time

        except Exception as e:
            print(f"Error checking {pair}: {e}")

    time.sleep(10)  # Check every 10 seconds
