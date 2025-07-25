import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime
import json

# Page config
st.set_page_config(
    page_title="Crypto Trading Signals",
    page_icon="🚀",
    layout="wide"
)

# Top crypto pairs
PAIRS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
    'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT',
    'SHIBUSDT', 'LTCUSDT', 'UNIUSDT', 'LINKUSDT', 'ATOMUSDT',
    'ETCUSDT', 'XLMUSDT', 'BCHUSDT', 'ALGOUSDT', 'VETUSDT'
]

class SimpleTradingSignals:
    def __init__(self, bb_period=20, bb_std=2.0):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.base_url = "https://api.binance.com/api/v3"
        
    def get_klines(self, symbol, interval='5m', limit=50):
        """Get kline data from Binance REST API"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': symbol,
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if isinstance(data, list):
                df = pd.DataFrame(data, columns=[
                    'open_time', 'open', 'high', 'low', 'close', 'volume',
                    'close_time', 'quote_asset_volume', 'number_of_trades',
                    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
                ])
                
                # Convert to proper types
                numeric_columns = ['open', 'high', 'low', 'close', 'volume']
                for col in numeric_columns:
                    df[col] = pd.to_numeric(df[col])
                
                df['timestamp'] = pd.to_datetime(df['open_time'], unit='ms')
                df['symbol'] = symbol
                
                return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']]
            else:
                st.error(f"API Error for {symbol}: {data}")
                return None
                
        except Exception as e:
            st.error(f"Error fetching {symbol}: {str(e)}")
            return None
    
    def calculate_bollinger_bands(self, df):
        """Calculate Bollinger Bands"""
        if len(df) < self.bb_period:
            return df
            
        df = df.copy()
        df['sma'] = df['close'].rolling(window=self.bb_period).mean()
        df['bb_std'] = df['close'].rolling(window=self.bb_period).std()
        df['bb_upper'] = df['sma'] + (df['bb_std'] * self.bb_std)
        df['bb_lower'] = df['sma'] - (df['bb_std'] * self.bb_std)
        return df
    
    def detect_signal(self, df):
        """Detect trading signal"""
        if len(df) < 2:
            return None
            
        df = self.calculate_bollinger_bands(df)
        latest = df.iloc[-1]
        
        # Signal conditions
        is_red_candle = latest['close'] < latest['open']
        touches_upper_bb = latest['high'] >= latest['bb_upper']
        closes_below_bb = latest['close'] < latest['bb_upper']
        
        if is_red_candle and touches_upper_bb and closes_below_bb:
            # Calculate metrics
            body_size = abs(latest['open'] - latest['close']) / latest['open'] * 100
            upper_wick = (latest['high'] - max(latest['open'], latest['close'])) / latest['close'] * 100
            bb_rejection = (latest['bb_upper'] - latest['close']) / latest['bb_upper'] * 100
            
            signal_strength = min(10, max(1, (body_size + upper_wick + bb_rejection) / 3))
            
            return {
                'symbol': latest['symbol'],
                'timestamp': latest['timestamp'],
                'entry_price': latest['close'],
                'bb_upper': latest['bb_upper'],
                'bb_middle': latest['sma'],
                'bb_lower': latest['bb_lower'],
                'signal_strength': round(signal_strength, 1),
                'stop_loss': round(latest['bb_upper'] * 1.002, 4),
                'target_1': round(latest['sma'], 4),
                'target_2': round(latest['bb_lower'], 4),
                'body_size': round(body_size, 1),
                'upper_wick': round(upper_wick, 1),
                'volume': latest['volume']
            }
        
        return None
    
    def scan_all_pairs(self, pairs):
        """Scan all pairs for signals"""
        signals = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, symbol in enumerate(pairs):
            status_text.text(f"Scanning {symbol}... ({i+1}/{len(pairs)})")
            progress_bar.progress((i + 1) / len(pairs))
            
            df = self.get_klines(symbol)
            if df is not None and len(df) >= self.bb_period:
                signal = self.detect_signal(df)
                if signal:
                    signals.append(signal)
            
            time.sleep(0.2)  # Avoid rate limiting
        
        progress_bar.empty()
        status_text.empty()
        return signals

def get_current_price(symbol):
    """Get current price for a symbol"""
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        response = requests.get(url, timeout=5)
        data = response.json()
        return float(data['price'])
    except:
        return None

def main():
    st.title("🚀 Crypto Trading Signals Scanner")
    st.markdown("**Real-time Bollinger Bands signals for crypto futures trading**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        bb_period = st.number_input("BB Period", 10, 50, 20)
        bb_std = st.number_input("BB Std Dev", 1.0, 3.0, 2.0, 0.1)
        
        st.divider()
        
        # Pair selection
        st.subheader("📊 Select Pairs")
        selected_pairs = st.multiselect(
            "Choose pairs to scan:",
            PAIRS,
            default=PAIRS[:10]
        )
        
        if not selected_pairs:
            selected_pairs = PAIRS[:10]
        
        st.info(f"Scanning {len(selected_pairs)} pairs")
    
    # Initialize scanner
    scanner = SimpleTradingSignals(bb_period=bb_period, bb_std=bb_std)
    
    # Main interface
    tab1, tab2, tab3 = st.tabs(["🔍 Signal Scanner", "💹 Live Prices", "📖 How to Use"])
    
    with tab1:
        st.header("Signal Detection")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔄 Scan for Signals", type="primary", use_container_width=True):
                with st.spinner("Scanning for trading signals..."):
                    signals = scanner.scan_all_pairs(selected_pairs)
                
                if signals:
                    st.success(f"🎯 Found {len(signals)} signal(s)!")
                    
                    # Sort by signal strength
                    signals.sort(key=lambda x: x['signal_strength'], reverse=True)
                    
                    for i, signal in enumerate(signals):
                        with st.expander(f"🔻 SHORT Signal #{i+1}: {signal['symbol']} (Strength: {signal['signal_strength']}/10)"):
                            
                            # Price info
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("💰 Entry Price", f"${signal['entry_price']:.4f}")
                                st.metric("🛑 Stop Loss", f"${signal['stop_loss']:.4f}")
                            
                            with col2:
                                st.metric("🎯 Target 1 (BB Mid)", f"${signal['target_1']:.4f}")
                                st.metric("🎯 Target 2 (BB Low)", f"${signal['target_2']:.4f}")
                            
                            with col3:
                                st.metric("📊 Signal Strength", f"{signal['signal_strength']}/10")
                                st.metric("📈 Volume", f"{signal['volume']:,.0f}")
                            
                            # Analysis
                            st.markdown("**📋 Signal Analysis:**")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.info(f"🕯️ Red Candle Body: {signal['body_size']:.1f}%")
                            with col2:
                                st.info(f"📏 Upper Wick: {signal['upper_wick']:.1f}%")
                            with col3:
                                risk_reward = abs((signal['entry_price'] - signal['target_1']) / (signal['stop_loss'] - signal['entry_price']))
                                st.info(f"⚖️ Risk:Reward = 1:{risk_reward:.1f}")
                            
                            st.caption(f"⏰ Signal Time: {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                else:
                    st.info("🔍 No signals found. Try again later or adjust BB parameters.")
        
        with col2:
            st.markdown("**📊 Signal Rules:**")
            st.markdown("""
            ✅ **Entry Conditions:**
            - Price touches BB upper band
            - Red candle formation
            - Close below BB upper
            
            ✅ **Risk Management:**
            - Stop: 0.2% above BB upper
            - Target 1: BB middle line
            - Target 2: BB lower line
            """)
    
    with tab2:
        st.header("💹 Live Price Monitor")
        
        if st.button("🔄 Refresh Prices"):
            price_data = []
            
            with st.spinner("Fetching live prices..."):
                for symbol in selected_pairs[:10]:  # Limit to 10 for speed
                    price = get_current_price(symbol)
                    if price:
                        price_data.append({
                            'Symbol': symbol,
                            'Price': f"${price:.4f}",
                            'Last Update': datetime.now().strftime('%H:%M:%S')
                        })
            
            if price_data:
                df_prices = pd.DataFrame(price_data)
                st.dataframe(df_prices, use_container_width=True)
            else:
                st.error("Could not fetch price data")
    
    with tab3:
        st.header("📖 How to Use This Scanner")
        
        st.markdown("""
        ### 🎯 **Trading Strategy: BB Reversal Shorts**
        
        **What it does:**
        This scanner identifies potential SHORT opportunities when price rejects from Bollinger Bands upper boundary.
        
        **Signal Logic:**
        1. 📈 Price touches or exceeds BB upper band
        2. 🕯️ Current candle closes RED (bearish)
        3. 📉 Close price is below BB upper (showing rejection)
        
        **How to Trade:**
        1. 🔍 Run the scanner to find signals
        2. 📊 Check signal strength (aim for 6+ out of 10)
        3. 💰 Enter SHORT at signal price
        4. 🛑 Set stop loss 0.2% above BB upper
        5. 🎯 Take profit at BB middle or lower
        
        **Risk Management:**
        - ⚠️ Never risk more than 1-2% of your account
        - 📊 Use proper position sizing
        - 🛑 Always set stop losses
        - 💡 Consider market conditions
        
        **Best Practices:**
        - 🕐 5-minute timeframe for scalping
        - 📈 Higher timeframes for confirmation
        - 📊 Check volume for signal strength
        - 🔄 Scan regularly for fresh signals
        
        ### ⚡ **Quick Start:**
        1. Select pairs in sidebar
        2. Click "Scan for Signals"
        3. Review signal strength and R:R
        4. Execute trades with proper risk management
        """)
        
        st.warning("""
        ⚠️ **Risk Disclaimer:**
        Trading involves substantial risk. This tool is for educational purposes only. 
        Always do your own research and never invest more than you can afford to lose.
        """)

if __name__ == "__main__":
    main()
