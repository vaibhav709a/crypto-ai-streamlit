import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# Page config
st.set_page_config(
    page_title="Real Crypto Trading Signals",
    page_icon="🔥",
    layout="wide"
)

# Top crypto pairs with CoinPaprika IDs
CRYPTO_PAIRS = {
    'btc-bitcoin': 'BTC/USDT',
    'eth-ethereum': 'ETH/USDT', 
    'bnb-binance-coin': 'BNB/USDT',
    'xrp-xrp': 'XRP/USDT',
    'ada-cardano': 'ADA/USDT',
    'sol-solana': 'SOL/USDT',
    'doge-dogecoin': 'DOGE/USDT',
    'dot-polkadot': 'DOT/USDT',
    'matic-polygon': 'MATIC/USDT',
    'avax-avalanche': 'AVAX/USDT',
    'shib-shiba-inu': 'SHIB/USDT',
    'ltc-litecoin': 'LTC/USDT',
    'uni-uniswap': 'UNI/USDT',
    'link-chainlink': 'LINK/USDT',
    'atom-cosmos': 'ATOM/USDT',
    'etc-ethereum-classic': 'ETC/USDT',
    'xlm-stellar': 'XLM/USDT',
    'bch-bitcoin-cash': 'BCH/USDT',
    'algo-algorand': 'ALGO/USDT',
    'vet-vechain': 'VET/USDT'
}

class CoinPaprikaAPI:
    def __init__(self):
        self.base_url = "https://api.coinpaprika.com/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CryptoSignals/1.0'
        })
    
    def get_coin_ohlcv(self, coin_id, start_date, end_date):
        """Get OHLCV data from CoinPaprika API"""
        try:
            url = f"{self.base_url}/coins/{coin_id}/ohlcv/historical"
            params = {
                'start': start_date.strftime('%Y-%m-%d'),
                'end': end_date.strftime('%Y-%m-%d')
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data:
                    df = pd.DataFrame(data)
                    df['time_open'] = pd.to_datetime(df['time_open'])
                    df['time_close'] = pd.to_datetime(df['time_close'])
                    
                    # Rename columns to standard format
                    df = df.rename(columns={
                        'time_open': 'timestamp',
                        'volume': 'volume'
                    })
                    
                    df['symbol'] = CRYPTO_PAIRS.get(coin_id, coin_id)
                    return df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'symbol']]
                
            return None
            
        except Exception as e:
            st.error(f"Error fetching {coin_id}: {str(e)}")
            return None
    
    def get_current_prices(self, coin_ids):
        """Get current prices for multiple coins"""
        try:
            # Convert list to comma-separated string
            ids_str = ','.join(coin_ids)
            url = f"{self.base_url}/tickers"
            params = {'quotes': 'USD'}
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                prices = {}
                for coin in data:
                    if coin['id'] in coin_ids:
                        prices[coin['id']] = {
                            'price': coin['quotes']['USD']['price'],
                            'change_24h': coin['quotes']['USD']['percent_change_24h'],
                            'volume_24h': coin['quotes']['USD']['volume_24h']
                        }
                
                return prices
            
            return {}
            
        except Exception as e:
            st.error(f"Error fetching current prices: {str(e)}")
            return {}

class RealTradingSignals:
    def __init__(self, bb_period=20, bb_std=2.0):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.api = CoinPaprikaAPI()
    
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
    
    def detect_bb_signal(self, df):
        """Detect Bollinger Bands reversal signal"""
        if len(df) < 2:
            return None
            
        df = self.calculate_bollinger_bands(df)
        
        if df['bb_upper'].isna().all():
            return None
            
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        
        # Skip if BB values are NaN
        if pd.isna(latest['bb_upper']) or pd.isna(latest['sma']):
            return None
        
        # Signal conditions for SHORT entry
        is_red_candle = latest['close'] < latest['open']
        touches_upper_bb = latest['high'] >= latest['bb_upper']
        closes_below_bb = latest['close'] < latest['bb_upper']
        has_volume = latest['volume'] > 0
        
        if is_red_candle and touches_upper_bb and closes_below_bb and has_volume:
            # Calculate signal strength metrics
            body_size = abs(latest['open'] - latest['close']) / latest['open'] * 100
            upper_wick = (latest['high'] - max(latest['open'], latest['close'])) / latest['close'] * 100
            bb_rejection = (latest['bb_upper'] - latest['close']) / latest['bb_upper'] * 100
            
            # Volume factor (compare to average volume)
            avg_volume = df['volume'].tail(10).mean()
            volume_ratio = latest['volume'] / avg_volume if avg_volume > 0 else 1
            volume_score = min(30, volume_ratio * 10)  # Cap at 30 points
            
            # Combined signal strength (0-10 scale)
            signal_strength = min(10, max(1, 
                (body_size * 0.3 + upper_wick * 0.4 + bb_rejection * 0.2 + volume_score * 0.1)))
            
            # Calculate risk management levels
            entry_price = latest['close']
            stop_loss = latest['bb_upper'] * 1.002  # 0.2% above BB upper
            target_1 = latest['sma']  # BB middle
            target_2 = latest['bb_lower']  # BB lower
            
            # Risk-to-reward calculations
            risk_amount = stop_loss - entry_price
            reward_1 = entry_price - target_1
            reward_2 = entry_price - target_2
            
            rr_ratio_1 = abs(reward_1 / risk_amount) if risk_amount != 0 else 0
            rr_ratio_2 = abs(reward_2 / risk_amount) if risk_amount != 0 else 0
            
            return {
                'symbol': latest['symbol'],
                'timestamp': latest['timestamp'],
                'signal_type': 'SHORT',
                'entry_price': round(entry_price, 6),
                'bb_upper': round(latest['bb_upper'], 6),
                'bb_middle': round(latest['sma'], 6),
                'bb_lower': round(latest['bb_lower'], 6),
                'stop_loss': round(stop_loss, 6),
                'target_1': round(target_1, 6),
                'target_2': round(target_2, 6),
                'signal_strength': round(signal_strength, 1),
                'body_size': round(body_size, 1),
                'upper_wick': round(upper_wick, 1),
                'bb_rejection': round(bb_rejection, 2),
                'volume': latest['volume'],
                'volume_ratio': round(volume_ratio, 2),
                'risk_reward_1': round(rr_ratio_1, 2),
                'risk_reward_2': round(rr_ratio_2, 2),
                'risk_percent': round((risk_amount / entry_price) * 100, 2),
                'reward_1_percent': round((reward_1 / entry_price) * 100, 2),
                'reward_2_percent': round((reward_2 / entry_price) * 100, 2)
            }
        
        return None
    
    def scan_for_signals(self, coin_ids):
        """Scan multiple coins for trading signals"""
        signals = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)  # Get 30 days of data
        
        for i, coin_id in enumerate(coin_ids):
            symbol = CRYPTO_PAIRS.get(coin_id, coin_id)
            status_text.text(f"Scanning {symbol}... ({i+1}/{len(coin_ids)})")
            progress_bar.progress((i + 1) / len(coin_ids))
            
            df = self.api.get_coin_ohlcv(coin_id, start_date, end_date)
            
            if df is not None and len(df) >= self.bb_period:
                signal = self.detect_bb_signal(df)
                if signal:
                    signals.append(signal)
            
            time.sleep(0.2)  # Rate limiting
        
        progress_bar.empty()
        status_text.empty()
        return signals

def create_trading_chart(coin_id, trading_signals):
    """Create professional trading chart with BB"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)  # Last 7 days
    
    df = trading_signals.api.get_coin_ohlcv(coin_id, start_date, end_date)
    
    if df is None or len(df) < trading_signals.bb_period:
        return None
    
    df = trading_signals.calculate_bollinger_bands(df)
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=[f'{CRYPTO_PAIRS[coin_id]} - 1D Chart with Bollinger Bands', 'Volume'],
        row_heights=[0.8, 0.2]
    )
    
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df['timestamp'],
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # Bollinger Bands
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['bb_upper'],
            mode='lines', name='BB Upper',
            line=dict(color='red', width=2, dash='dash'),
            opacity=0.7
        ), row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['sma'],
            mode='lines', name='BB Middle (SMA)',
            line=dict(color='orange', width=2)
        ), row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(
            x=df['timestamp'], y=df['bb_lower'],
            mode='lines', name='BB Lower',
            line=dict(color='green', width=2, dash='dash'),
            opacity=0.7
        ), row=1, col=1
    )
    
    # Check for signal on latest candle
    signal = trading_signals.detect_bb_signal(df)
    if signal:
        fig.add_trace(
            go.Scatter(
                x=[signal['timestamp']],
                y=[signal['entry_price']],
                mode='markers+text',
                marker=dict(size=20, color='red', symbol='triangle-down'),
                text=['SHORT'],
                textposition='top center',
                name='Signal',
                showlegend=True
            ), row=1, col=1
        )
    
    # Volume bars
    colors = ['green' if c >= o else 'red' for c, o in zip(df['close'], df['open'])]
    
    fig.add_trace(
        go.Bar(
            x=df['timestamp'], y=df['volume'],
            name='Volume',
            marker_color=colors,
            opacity=0.6
        ), row=2, col=1
    )
    
    fig.update_layout(
        title=f"{CRYPTO_PAIRS[coin_id]} Trading Analysis",
        template="plotly_dark",
        height=700,
        xaxis_rangeslider_visible=False,
        showlegend=True
    )
    
    return fig

def main():
    st.title("🔥 Real Crypto Trading Signals")
    st.markdown("**Professional Bollinger Bands signals using CoinPaprika API - No restrictions!**")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Trading Configuration")
        
        # BB parameters
        bb_period = st.number_input("BB Period", 10, 50, 20)
        bb_std = st.number_input("BB Std Deviation", 1.0, 3.0, 2.0, 0.1)
        
        st.divider()
        
        # Coin selection
        st.subheader("📊 Select Cryptocurrencies")
        coin_names = [f"{CRYPTO_PAIRS[coin_id]} ({coin_id})" for coin_id in CRYPTO_PAIRS.keys()]
        selected_names = st.multiselect(
            "Choose coins to analyze:",
            coin_names,
            default=coin_names[:10]
        )
        
        # Convert back to coin IDs
        selected_coins = []
        for name in selected_names:
            for coin_id in CRYPTO_PAIRS.keys():
                if coin_id in name:
                    selected_coins.append(coin_id)
                    break
        
        if not selected_coins:
            selected_coins = list(CRYPTO_PAIRS.keys())[:10]
        
        st.success(f"✅ {len(selected_coins)} coins selected")
        
        st.divider()
        st.markdown("**🌐 Data Source:**")
        st.info("CoinPaprika API\n✅ No restrictions\n✅ 20,000 calls/month\n✅ Real market data")
    
    # Initialize trading system
    trading_signals = RealTradingSignals(bb_period=bb_period, bb_std=bb_std)
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["🚨 Signal Scanner", "📊 Live Prices", "📈 Chart Analysis", "📚 Strategy Guide"])
    
    with tab1:
        st.header("Professional Signal Detection")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if st.button("🔍 SCAN FOR TRADING SIGNALS", type="primary", use_container_width=True):
                with st.spinner("Analyzing market data for BB reversal signals..."):
                    signals = trading_signals.scan_for_signals(selected_coins)
                
                if signals:
                    st.success(f"🎯 {len(signals)} trading signal(s) detected!")
                    
                    # Sort by signal strength
                    signals.sort(key=lambda x: x['signal_strength'], reverse=True)
                    
                    for i, signal in enumerate(signals):
                        strength_color = "🟢" if signal['signal_strength'] >= 7 else "🟡" if signal['signal_strength'] >= 5 else "🔴"
                        
                        with st.expander(f"{strength_color} Signal #{i+1}: {signal['symbol']} - Strength: {signal['signal_strength']}/10"):
                            
                            # Key metrics
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("🎯 Entry Price", f"${signal['entry_price']}")
                                st.metric("🛑 Stop Loss", f"${signal['stop_loss']}")
                            
                            with col2:
                                st.metric("📈 Target 1", f"${signal['target_1']}")
                                st.metric("📈 Target 2", f"${signal['target_2']}")
                            
                            with col3:
                                st.metric("⚡ Signal Strength", f"{signal['signal_strength']}/10")
                                st.metric("📊 Volume Ratio", f"{signal['volume_ratio']}x")
                            
                            with col4:
                                st.metric("⚖️ Risk:Reward 1", f"1:{signal['risk_reward_1']}")
                                st.metric("⚖️ Risk:Reward 2", f"1:{signal['risk_reward_2']}")
                            
                            # Technical analysis
                            st.markdown("**🔬 Technical Analysis:**")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.info(f"🕯️ Red Candle Body: {signal['body_size']:.1f}%")
                            with col2:
                                st.info(f"📏 Upper Wick: {signal['upper_wick']:.1f}%")
                            with col3:
                                st.info(f"📉 BB Rejection: {signal['bb_rejection']:.1f}%")
                            with col4:
                                st.info(f"📊 Volume: {signal['volume']:,.0f}")
                            
                            # Risk analysis
                            st.markdown("**⚠️ Risk Analysis:**")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                risk_color = "🟢" if signal['risk_percent'] < 1 else "🟡" if signal['risk_percent'] < 2 else "🔴"
                                st.metric(f"{risk_color} Risk", f"{signal['risk_percent']:.2f}%")
                            with col2:
                                st.metric("💰 Reward 1", f"{abs(signal['reward_1_percent']):.2f}%")
                            with col3:
                                st.metric("💰 Reward 2", f"{abs(signal['reward_2_percent']):.2f}%")
                            
                            # Trading recommendation
                            if signal['signal_strength'] >= 7 and signal['risk_reward_1'] >= 2:
                                st.success("✅ **STRONG SIGNAL** - Recommended for trading")
                            elif signal['signal_strength'] >= 5:
                                st.warning("⚠️ **MODERATE SIGNAL** - Consider with caution")
                            else:
                                st.error("❌ **WEAK SIGNAL** - Not recommended")
                            
                            st.caption(f"⏰ Signal Time: {signal['timestamp'].strftime('%Y-%m-%d %H:%M:%S UTC')}")
                
                else:
                    st.info("🔍 No signals found. Market conditions may not be suitable for BB reversal trades right now.")
        
        with col2:
            st.markdown("**🎯 Signal Quality:**")
            st.markdown("""
            **🟢 Strong (7-10):**
            - High confidence trades
            - Good R:R ratios
            
            **🟡 Moderate (5-6):**
            - Proceed with caution
            - Smaller position sizes
            
            **🔴 Weak (1-4):**
            - Avoid trading
            - Wait for better setups
            """)
    
    with tab2:
        st.header("💹 Live Market Prices")
        
        if st.button("🔄 Refresh Market Data"):
            with st.spinner("Fetching live prices..."):
                prices = trading_signals.api.get_current_prices(selected_coins)
            
            if prices:
                price_data = []
                for coin_id, data in prices.items():
                    symbol = CRYPTO_PAIRS.get(coin_id, coin_id)
                    
                    change_24h = data['change_24h']
                    change_color = "🟢" if change_24h >= 0 else "🔴"
                    
                    price_data.append({
                        'Symbol': symbol,
                        'Price': f"${data['price']:.6f}",
                        '24h Change': f"{change_color} {change_24h:.2f}%",
                        '24h Volume': f"${data['volume_24h']:,.0f}",
                        'Last Update': datetime.now().strftime('%H:%M:%S')
                    })
                
                df_prices = pd.DataFrame(price_data)
                st.dataframe(df_prices, use_container_width=True, hide_index=True)
                
                st.success("✅ Market data updated successfully!")
                
                # Market summary
                positive_changes = sum(1 for _, data in prices.items() if data['change_24h'] > 0)
                total_coins = len(prices)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Market Sentiment", f"{positive_changes}/{total_coins} positive")
                with col2:
                    avg_change = sum(data['change_24h'] for data in prices.values()) / len(prices)
                    st.metric("Average 24h Change", f"{avg_change:.2f}%")
                with col3:
                    total_volume = sum(data['volume_24h'] for data in prices.values())
                    st.metric("Total 24h Volume", f"${total_volume:,.0f}")
            
            else:
                st.error("Failed to fetch market data. Please try again.")
    
    with tab3:
        st.header("📈 Professional Chart Analysis")
        
        selected_coin = st.selectbox(
            "Select cryptocurrency for detailed analysis:",
            options=selected_coins,
            format_func=lambda x: CRYPTO_PAIRS[x]
        )
        
        if st.button("📊 Generate Trading Chart"):
            with st.spinner(f"Loading chart for {CRYPTO_PAIRS[selected_coin]}..."):
                chart = create_trading_chart(selected_coin, trading_signals)
                
                if chart:
                    st.plotly_chart(chart, use_container_width=True)
                    
                    # Analysis summary
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=7)
                    df = trading_signals.api.get_coin_ohlcv(selected_coin, start_date, end_date)
                    
                    if df is not None:
                        signal = trading_signals.detect_bb_signal(df)
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            if signal:
                                st.success("🎯 Active Signal Detected!")
                                st.metric("Signal Strength", f"{signal['signal_strength']}/10")
                            else:
                                st.info("No current signal")
                        
                        with col2:
                            latest_price = df.iloc[-1]['close']
                            st.metric("Current Price", f"${latest_price:.6f}")
                        
                        with col3:
                            price_change = ((df.iloc[-1]['close'] - df.iloc[-2]['close']) / df.iloc[-2]['close']) * 100
                            st.metric("Last Change", f"{price_change:.2f}%")
                
                else:
                    st.error("Unable to load chart data. Please try again.")
    
    with tab4:
        st.header("📚 Complete Trading Strategy Guide")
        
        st.markdown("""
        ### 🎯 **Bollinger Bands Reversal Strategy**
        
        **Strategy Overview:**
        This strategy identifies high-probability SHORT opportunities when price is rejected from the Bollinger Bands upper boundary, indicating potential bearish reversals.
        
        ### 📋 **Signal Requirements:**
        
        **✅ Entry Conditions:**
        1. **BB Touch**: Candle high must touch or exceed BB upper band
        2. **Red Candle**: Current candle must close below open (bearish)
        3. **Rejection**: Close price must be below BB upper band
        4. **Volume**: Above-average volume for confirmation
        
        **📊 Signal Strength Factors:**
        - **Candle Body Size** (30%): Larger red candles = stronger selling
        - **Upper Wick Length** (40%): Longer wicks = stronger rejection  
        - **BB Rejection Distance** (20%): Further below BB = stronger signal
        - **Volume Ratio** (10%): Higher volume = better confirmation
        
        ### 💰 **Risk Management:**
        
        **🛑 Stop Loss:**
        - Placed 0.2% above BB upper band
        - Never move stop loss against your position
        - Exit immediately if stop is hit
        
        **🎯 Take Profit Levels:**
        - **Target 1**: BB middle line (conservative)
        - **Target 2**: BB lower band (aggressive)
        - Consider taking 50% profit at Target 1
        
        **📏 Position Sizing:**
        - Risk only 1-2% of account per trade
        - Formula: Position Size = (Account × Risk%) ÷ Stop Distance
        - Smaller positions for lower-strength signals
        
        ### ⭐ **Signal Quality Guide:**
        
        **🟢 Strong Signals (7-10/10):**
        - High confidence trades
        - Large candle bodies and wicks
        - High volume confirmation
        - Good risk-to-reward ratios (1:2+)
        
        **🟡 Moderate Signals (5-6/10):**
        - Proceed with reduced position size
        - Tighter risk management
        - Consider market conditions
        
        **🔴 Weak Signals (1-4/10):**
        - Avoid trading these setups
        - Wait for higher quality opportunities
        - Use for learning/observation only
        
        ### ⏰ **Best Trading Conditions:**
        
        **Market Environment:**
        - Trending or ranging markets work best
        - Avoid during major news events
        - Higher volatility = better signals
        
        **Time Considerations:**
        - Daily timeframe for swing trades
        - Multiple timeframe confirmation
        - Check overall market sentiment
        
        ### 📈 **Advanced Tips:**
        
        **Multi-Timeframe Analysis:**
        - Confirm signals on higher timeframes
        - Use lower timeframes for precise entry
        - Align with overall trend direction
        
        **Market Context:**
        - Check major support/resistance levels
        - Consider overall crypto market sentiment
        - Watch Bitcoin correlation for altcoins
        
        **Risk-to-Reward Optimization:**
        - Only take trades with 1:2+ R:R ratio
        - Adjust targets based on market conditions
        - Trail stop loss as price moves favorably
        
        ### ⚠️ **Important Warnings:**
        
        **Risk Disclosure:**
        - Trading involves substantial risk of loss
        - Never risk more than you can afford to lose
        - Past performance doesn't guarantee future results
        - This is educational content only, not financial advice
        
        **Common Mistakes to Avoid:**
        - Trading every signal (be selective)
        - Moving stop losses against you
        - Ignoring risk management rules
        - Over-leveraging positions
        - Trading during low-volume periods
        
        ### 🚀 **Getting Started:**
        
        **1. Practice First:**
        - Use paper trading or demo accounts
        - Start with small position sizes
        - Keep detailed trading records
        
        **2. Build Discipline:**
        - Follow your trading plan strictly
        - Don't let emotions drive decisions
        - Take breaks after losses
        
        **3. Continuous Learning:**
        - Study market behavior patterns
        - Analyze your winning and losing trades
        - Stay updated with market news
        
        **4. Scale Gradually:**
        - Increase position sizes only after consistent profits
        - Maintain proper risk management at all levels
        - Don't rush the learning process
        
        ### 🎯 **Success Metrics:**
        
        **Track Your Performance:**
        - Win rate (aim for 60%+)
        - Average risk-to-reward ratio
        - Maximum drawdown periods
        - Monthly profit/loss
        
        **Remember**: Successful trading requires patience, discipline, and continuous learning. Focus on risk management over profits, and the profits will follow naturally.
        """)

if __name__ == "__main__":
    main()
