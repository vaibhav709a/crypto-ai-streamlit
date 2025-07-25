
import time
from signal_logic import check_bb_red_candle

# List of top crypto pairs for testing
pairs = ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "DOGEUSD"]

while True:
    for pair in pairs:
        signal = check_bb_red_candle(pair)
        if signal:
            print(f"[SIGNAL] {signal['pair']} | {signal['direction']} | {signal['timestamp']}")
    time.sleep(60)
