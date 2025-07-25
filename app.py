import streamlit as st
import ccxt
import pandas as pd
import numpy as np
import time
import asyncio
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import threading
import queue
import json
import websocket
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Live Crypto Trading Signals",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Top 50 crypto pairs for futures trading
FUTURES_PAIRS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT',
    'SOLUSDT', 'DOGEUSDT', 'DOTUSDT', 'MATICUSDT', 'AVAXUSDT',
    'SHIBUSDT', 'LTCUSDT', 'UNIUSDT', 'LINKUSDT', 'ATOMUSDT',
    'ETCUSDT', 'XLMUSDT', 'BCHUSDT', 'ALGOUSDT', 'VETUSDT',
    'ICPUSDT', 'FILUSDT', 'TRXUSDT', 'FTMUSDT', 'MANAUSDT',
    'SANDUSDT', 'AXSUSDT', 'THETAUSDT', 'HBARUSDT', 'EOSUSDT',
    'AAVEUSDT', 'MKRUSDT', 'NEOUSDT', 'KSMUSDT', 'COMPUSDT',
    'SUSHIUSDT', 'GRTUSDT', 'ENJUSDT', 'BATUSDT', 'ZECUSDT',
    'DASHUSDT', 'WAVESUSDT', 'ZILUSDT', 'HOTUSDT', 'ICXUSDT',
    'OMGUSDT', 'QTUMUSDT', 'ZRXUSDT', 'RENUSDT', 'SNXUSDT'
]

class LiveDataStream:
    def __init__(self):
        self.ws = None
        self.data_queue = queue.Queue()
        self.is_connected = False
        self.subscribed_symbols = []
        self.kline_data = {}
        
    def create_websocket_url(self, symbols):
        """Create Binance WebSocket URL for multiple symbols"""
        streams = []
        for symbol in symbols:
            streams.append(f"{symbol.lower()}@kline_5m")
        
        stream_names = "/".join(streams)
        return f"wss://fstream.binance.com/stream?streams={stream_names}"
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            if 'data' in data:
                kline_data = data['data']
                symbol = kline_data['s']
                kline = kline_data['k']
                
                # Only process closed candles
                if kline['x']:  # Candle is closed
                    candle_data = {
                        'symbol': symbol,
                        'timestamp': pd.to_datetime(kline['t'], unit='ms'),
                        'open': float(kline['o']),
                        'high': float(kline['h']),
                        'low': float(kline['l']),
                        'close': float(kline['c']),
                        'volume': float(kline['v'])
                    }
                    
                    # Store in memory and queue for processing
                    if symbol not in self.kline_data:
                        self.kline_data[symbol] = []
                    
                    self.kline_data[symbol].append(candle_data)
                    
                    # Keep only last 100 candles
                    if len(self.kline_data[symbol]) > 100:
                        self.kline_data[symbol] = self.kline_data[symbol][-100:]
                    
                    self.data_queue.put(candle_data)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def on_error(self, ws, error):
        logger.error(f"WebSocket error: {error}")
        self.is_connected = False
    
    def on_close(self, ws, close_status_code, close_msg):
        logger.info("WebSocket connection closed")
        self.is_connected = False
    
    def on_open(self, ws):
        logger.info("WebSocket connection opened")
        self.is_connected = True
    
    def start_stream(self, symbols):
        """Start live data stream for given symbols"""
        try:
            self.subscribed_symbols = symbols[:10]  # Limit to first 10 for demo
            url = self.create_websocket_url(self.subscribed_symbols)
            
            self.ws = websocket.WebSocketApp(
                url,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
                on_open=self.on_open
            )
            
            # Run in separate thread
            self.ws.run_forever()
            
        except Exception as e:
            logger.error(f"Error starting stream: {e}")
    
    def stop_stream(self):
        """Stop the live data stream"""
        if self.ws:
            self.ws.close()
        self.is_connected = False

class RealTimeTradingSignals:
    def __init__(self, bb_period=20, bb_std=2.0):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.exchange = ccxt.binance()
        self.signals = []
        self.live_stream = LiveDataStream()
        self.signal_alerts = queue.Queue()
        
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
    
    def detect_signal(self, symbol_data):
        """Detect BB reversal signal in real-time"""
        if len(symbol_data) < self.bb_period + 1:
            return None
            
        df = pd.DataFrame(symbol_data)
        df = self.calculate_bollinger_bands(df)
        
        if len(df) < 2:
            return None
            
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Signal conditions
        is_red_candle = latest['close'] < latest['open']
        touches_upper_bb = latest['high'] >= latest['bb_upper']
        closes_below_bb = latest['close'] < latest['bb_upper']
        
        if is_red_candle and touches_upper_bb and closes_below_bb:
            # Calculate signal metrics
            wick_ratio = (latest['high'] - max(latest['open'], latest['close'])) / latest['close']
            body_ratio = abs(latest['open'] - latest['close']) / latest['open']
            bb_rejection = (latest['bb_upper'] - latest['close']) / latest['bb_upper']
            
            signal_strength = min(10, max(1, 
                (body_ratio * 30 + wick_ratio * 40 + bb_rejection * 30)))
            
            return {
                'symbol': latest['symbol'],
                'timestamp': latest['timestamp'],
                'signal_type': 'BB_REVERSAL_SHORT',
                'entry_price': latest['close'],
                'bb_upper': latest['bb_upper'],
                'bb_middle': latest['sma'],
                'bb_lower': latest['bb_lower'],
                'signal_strength': round(signal_strength, 2),
                'stop_loss': latest['bb_upper'] * 1.002,  # 0.2% above BB upper
                'target_1': latest['bb_middle'],  # BB middle
                'target_2': latest['bb_lower'],   # BB lower
                'wick_ratio': round(wick_ratio * 100, 2),
                'body_ratio': round(body_ratio * 100, 2),
                'volume': latest['volume']
            }
        
        return None
    
    def get_historical_data(self, symbol, limit=100):
        """Get historical data for initial BB calculation"""
        try:
            # Use futures endpoint
            ohlcv = self.exchange.fetch_ohlcv(symbol.replace('USDT', '/USDT'), '5m', limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df['symbol'] = symbol
            return df.to_dict('records')
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return []
    
    def process_live_signals(self):
        """Process incoming live data for signals"""
        processed_signals = []
        
        while not self.live_stream.data_queue.empty():
            try:
                new_candle = self.live_stream.data_queue.get_nowait()
                symbol = new_candle['symbol']
                
                # Get symbol data for signal detection
                if symbol in self.live_stream.kline_data:
                    signal = self.detect_signal(self.live_stream.kline_data[symbol])
                    if signal:
                        processed_signals.append(signal)
                        self.signal_alerts.put(signal)
                        
            except queue.Empty:
                break
            except Exception as e:
                logger.error(f"Error processing signal: {e}")
        
        return processed_signals

def create_live_chart(symbol, trading_signals):
    """Create real-time chart with BB and signals"""
    if symbol not in trading_signals.live_stream.kline_data:
        return None
    
    data = trading_signals.live_stream.kline_data[symbol]
    if len(data) < trading_signals.bb_period:
        return None
    
    df = pd.DataFrame(data)
    df = trading_signals.calculate_bollinger_bands(df)
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[f'{symbol} - Live 5m Chart', 'Volume'],
        row_heights=[0.8, 0.2]
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#00ff88',
            decreasing_line_color='#ff4444'
        ),
        row=1, col=1
    )
    
    # Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['bb_upper'],
            mode='lines', name='BB Upper',
            line=dict(color='#ff6b6b', width=1, dash='dash')
        ), row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['sma'],
            mode='lines', name='BB Middle',
            line=dict(color='#4ecdc4', width=1)
        ), row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['bb_lower'],
            mode='lines', name='BB Lower',
            line=dict(color='#45b7d1', width=1, dash='dash')
        ), row=1, col=1
    )
    
    # Volume
    colors = ['#ff4444' if c < o else '#00ff88' for c, o in zip(df['close'], df['open'])]
    fig.add_trace(
        go.Bar(x=df['timestamp'], y=df['volume'], name='Volume', marker_color=colors),
        row=2, col=1
    )
    
    # Mark latest signal if exists
    latest_signal = trading_signals.detect_signal(data)
    if latest_signal:
        fig.add_trace(
            go.Scatter(
                x=[latest_signal['timestamp']],
                y=[latest_signal['entry_price']],
                mode='markers',
                marker=dict(size=15, color='red', symbol='triangle-down'),
                name='SHORT Signal'
            ), row=1, col=1
        )
    
    fig.update_layout(
        title=f"{symbol} Live Trading Chart",
        template="plotly_dark",
        height=600,
        showlegend=True,
        xaxis_rangeslider_visible=False
    )
    
    return fig

def main():
    st.title("🔥 Live Crypto Futures Trading Signals")
    st.markdown("**Real-time Bollinger Bands reversal signals for futures trading**")
    
    # Initialize session state
    if 'trading_signals' not in st.session_state:
        st.session_state.trading_signals = RealTimeTradingSignals()
    if 'stream_active' not in st.session_state:
        st.session_state.stream_active = False
    if 'active_signals' not in st.session_state:
        st.session_state.active_signals = []
    
    trading_signals = st.session_state.trading_signals
    
    # Sidebar controls
    with st.sidebar:
        st.header("⚙️ Trading Configuration")
        
        # BB Settings
        bb_period = st.number_input("BB Period", 10, 50, 20)
        bb_std = st.number_input("BB Std Dev", 1.0, 3.0, 2.0, 0.1)
        
        # Update settings
        trading_signals.bb_period = bb_period
        trading_signals.bb_std = bb_std
        
        st.divider()
        
        # Stream Controls
        st.subheader("📡 Live Data Stream")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🟢 START", disabled=st.session_state.stream_active):
                if not st.session_state.stream_active:
                    # Initialize historical data
                    with st.spinner("Loading historical data..."):
                        for symbol in FUTURES_PAIRS[:5]:  # Start with top 5
                            hist_data = trading_signals.get_historical_data(symbol)
                            if hist_data:
                                trading_signals.live_stream.kline_data[symbol] = hist_data
                    
                    # Start stream in background thread
                    stream_thread = threading.Thread(
                        target=trading_signals.live_stream.start_stream,
                        args=(FUTURES_PAIRS[:5],),
                        daemon=True
                    )
                    stream_thread.start()
                    
                    st.session_state.stream_active = True
                    st.success("Live stream started!")
                    time.sleep(1)
                    st.rerun()
        
        with col2:
            if st.button("🔴 STOP", disabled=not st.session_state.stream_active):
                trading_signals.live_stream.stop_stream()
                st.session_state.stream_active = False
                st.info("Stream stopped")
                time.sleep(1)
                st.rerun()
        
        # Connection Status
        if st.session_state.stream_active:
            if trading_signals.live_stream.is_connected:
                st.success("🟢 Live data connected")
            else:
                st.warning("🟡 Connecting...")
        else:
            st.error("🔴 Stream offline")
        
        st.divider()
        st.subheader("📊 Monitored Pairs")
        for symbol in FUTURES_PAIRS[:5]:
            st.text(f"• {symbol}")
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["🚨 Live Signals", "📈 Live Charts", "📋 Signal History"])
    
    with tab1:
        st.header("Real-Time Signal Detection")
        
        # Auto-refresh for live signals
        if st.session_state.stream_active:
            # Process new signals
            new_signals = trading_signals.process_live_signals()
            if new_signals:
                st.session_state.active_signals.extend(new_signals)
                # Keep only last 50 signals
                st.session_state.active_signals = st.session_state.active_signals[-50:]
            
            # Signal alerts
            alert_col1, alert_col2 = st.columns([3, 1])
            with alert_col1:
                if not trading_signals.signal_alerts.empty():
                    try:
                        latest_alert = trading_signals.signal_alerts.get_nowait()
                        st.success(f"🚨 NEW SIGNAL: {latest_alert['symbol']} at ${latest_alert['entry_price']:.4f}")
                    except:
                        pass
            
            with alert_col2:
                if st.button("🔄 Refresh"):
                    st.rerun()
            
            # Active signals display
            if st.session_state.active_signals:
                st.subheader("🎯 Recent Signals")
                
                # Convert to DataFrame for display
                signals_df = pd.DataFrame(st.session_state.active_signals[-10:])  # Last 10
                signals_df = signals_df.sort_values('timestamp', ascending=False)
                
                for _, signal in signals_df.iterrows():
                    with st.expander(f"🔻 {signal['symbol']} - Strength: {signal['signal_strength']}/10"):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Entry Price", f"${signal['entry_price']:.4f}")
                            st.metric("Stop Loss", f"${signal['stop_loss']:.4f}")
                        
                        with col2:
                            st.metric("Target 1", f"${signal['target_1']:.4f}")
                            st.metric("Target 2", f"${signal['target_2']:.4f}")
                        
                        with col3:
                            st.metric("Signal Strength", f"{signal['signal_strength']}/10")
                            st.metric("Body Size", f"{signal['body_ratio']:.1f}%")
                        
                        with col4:
                            st.metric("Upper Wick", f"{signal['wick_ratio']:.1f}%")
                            st.write(f"⏰ {signal['timestamp'].strftime('%H:%M:%S')}")
                        
                        # Risk calculation
                        risk_ratio = (signal['stop_loss'] - signal['entry_price']) / signal['entry_price'] * 100
                        reward_ratio = (signal['entry_price'] - signal['target_1']) / signal['entry_price'] * 100
                        
                        st.info(f"📊 Risk: {risk_ratio:.2f}% | Reward: {reward_ratio:.2f}% | R:R = 1:{reward_ratio/abs(risk_ratio):.1f}")
            else:
                st.info("No signals detected yet. Waiting for live data...")
        
        else:
            st.warning("⚠️ Start the live data stream to see real-time signals")
    
    with tab2:
        st.header("Live Trading Charts")
        
        if st.session_state.stream_active and trading_signals.live_stream.kline_data:
            # Select symbol for chart
            available_symbols = list(trading_signals.live_stream.kline_data.keys())
            if available_symbols:
                selected_symbol = st.selectbox("Select Symbol", available_symbols)
                
                # Auto-refresh chart
                chart_placeholder = st.empty()
                
                with chart_placeholder.container():
                    chart = create_live_chart(selected_symbol, trading_signals)
                    if chart:
                        st.plotly_chart(chart, use_container_width=True)
                        
                        # Show latest candle info
                        latest_data = trading_signals.live_stream.kline_data[selected_symbol][-1]
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Price", f"${latest_data['close']:.4f}")
                        with col2:
                            change = (latest_data['close'] - latest_data['open']) / latest_data['open'] * 100
                            st.metric("Change", f"{change:.2f}%")
                        with col3:
                            st.metric("Volume", f"{latest_data['volume']:,.0f}")
                        with col4:
                            st.metric("Time", latest_data['timestamp'].strftime('%H:%M:%S'))
                    else:
                        st.info("Loading chart data...")
            else:
                st.info("No chart data available yet...")
        else:
            st.warning("Start live stream to view charts")
    
    with tab3:
        st.header("Signal Performance History")
        
        if st.session_state.active_signals:
            df = pd.DataFrame(st.session_state.active_signals)
            
            # Summary stats
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Signals", len(df))
            with col2:
                avg_strength = df['signal_strength'].mean()
                st.metric("Avg Strength", f"{avg_strength:.1f}/10")
            with col3:
                strong_signals = len(df[df['signal_strength'] >= 7])
                st.metric("Strong Signals (≥7)", strong_signals)
            with col4:
                unique_pairs = df['symbol'].nunique()
                st.metric("Unique Pairs", unique_pairs)
            
            # Detailed history
            st.subheader("📊 Signal Details")
            display_df = df[['symbol', 'timestamp', 'entry_price', 'signal_strength', 
                           'body_ratio', 'wick_ratio']].copy()
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%H:%M:%S')
            
            st.dataframe(
                display_df.sort_values('timestamp', ascending=False),
                use_container_width=True
            )
        else:
            st.info("No signal history available")
    
    # Auto-refresh for live updates
    if st.session_state.stream_active:
        time.sleep(1)  # Wait 1 second
        st.rerun()

if __name__ == "__main__":
    main()
