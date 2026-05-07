import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import plotly.graph_objects as go
from io import StringIO

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="LCDKScanner Elite", page_icon="💎", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; border-radius: 10px; padding: 15px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. MATH ENGINE ---
def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

@st.cache_data
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers)
        table = pd.read_html(StringIO(response.text))
        return table[0]['Symbol'].str.replace('.', '-', regex=False).tolist()
    except:
        return ["AAPL", "MSFT", "NVDA", "TSLA", "AMD", "META", "AMZN"]

def get_market_signals(ticker_list):
    results = []
    data = yf.download(ticker_list, period="60d", interval="1d", group_by='ticker', progress=False)
    for ticker in ticker_list:
        try:
            tick_data = data[ticker].dropna()
            if len(tick_data) < 35: continue
            
            prev_close = tick_data['Close'].iloc[-2]
            curr_open = tick_data['Open'].iloc[-1]
            curr_price = tick_data['Close'].iloc[-1]
            gap_pct = ((curr_open - prev_close) / prev_close) * 100
            day_change = ((curr_price - curr_open) / curr_open) * 100
            
            avg_vol = tick_data['Volume'].iloc[-11:-1].mean()
            rvol = tick_data['Volume'].iloc[-1] / avg_vol if avg_vol > 0 else 0
            
            rsi_series = calculate_rsi(tick_data['Close'])
            current_rsi = rsi_series.iloc[-1]
            
            results.append({
                "Ticker": ticker, "Price": round(curr_price, 2),
                "Gap %": round(gap_pct, 2), "Since Open %": round(day_change, 2),
                "RVOL": round(rvol, 2), "RSI": round(current_rsi, 1),
                "Volume": int(tick_data['Volume'].iloc[-1])
            })
        except: continue
    return pd.DataFrame(results)

# --- 3. UI ---
st.title("💎 LCDKScanner Elite")
st.caption("Strategic Market Surveillance & Historical Validation")

st.sidebar.header("Settings")
sector = st.sidebar.selectbox("Market Pool", ["S&P 500", "Tech Giants", "Custom"])
gap_threshold = st.sidebar.slider("Strategy Gap % Threshold", 0.0, 5.0, 1.5)

if sector == "S&P 500": watchlist = get_sp500_tickers()
elif sector == "Tech Giants": watchlist = ["AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "AMD", "META", "AMZN"]
else: watchlist = [x.strip().upper() for x in st.sidebar.text_input("Tickers", "AAPL, NVDA").split(",")]

if 'scanner_data' not in st.session_state: st.session_state.scanner_data = None

if st.sidebar.button("Run Market Scan"):
    with st.spinner(f"Scanning..."):
        st.session_state.scanner_data = get_market_signals(watchlist)

if st.session_state.scanner_data is not None:
    df = st.session_state.scanner_data
    buys = df[df['Gap %'] >= gap_threshold].sort_values(by="RVOL", ascending=False)
    sells = df[df['Gap %'] <= -gap_threshold].sort_values(by="RVOL", ascending=False)

    st.subheader("Strategy Signal Tables")
    c1, c2 = st.columns(2)
    with c1:
        st.success("📈 Bullish Gaps")
        ev_buy = st.dataframe(buys, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")
    with c2:
        st.error("📉 Bearish Gaps")
        ev_sell = st.dataframe(sells, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="single-row")

    # Selection logic
    selected_ticker = None
    row_stats = None
    if ev_buy.selection.rows: 
        row_stats = buys.iloc[ev_buy.selection.rows[0]]
        selected_ticker = row_stats["Ticker"]
    elif ev_sell.selection.rows: 
        row_stats = sells.iloc[ev_sell.selection.rows[0]]
        selected_ticker = row_stats["Ticker"]

    if selected_ticker:
        st.divider()
        st.header(f"🔍 Deep Dive & Multi-Day Backtest: {selected_ticker}")
        t_obj = yf.Ticker(selected_ticker)
        hist = t_obj.history(period="60d")
        info = t_obj.info

        col_a, col_b = st.columns([1, 2])
        with col_a:
            st.subheader("Company Profile")
            st.metric("Market Cap", f"${info.get('marketCap', 0):,}")
            st.write(f"**Sector:** {info.get('sector', 'N/A')}")
            st.write(info.get('longBusinessSummary', "Summary not available."))
        
        with col_b:
            st.subheader("30-Day Technical Chart")
            fig = go.Figure(data=[go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'], low=hist['Low'], close=hist['Close'])])
            fig.update_layout(template="plotly_dark", height=400, margin=dict(l=0,r=0,b=0,t=0), xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)

        # --- SMART BACKTESTER ---
        st.subheader("Historical Trades (Last 30 Days)")
        bt_list = []
        for i in range(len(hist)-30, len(hist)):
            day_open, prev_close, day_close = hist['Open'].iloc[i], hist['Close'].iloc[i-1], hist['Close'].iloc[i]
            gap = ((day_open - prev_close) / prev_close) * 100
            
            if abs(gap) >= gap_threshold:
                # If gap is positive, we Buy. If negative, we Short.
                if gap > 0:
                    trade_type = "BUY"
                    profit = ((day_close - day_open) / day_open) * 100
                else:
                    trade_type = "SHORT"
                    profit = ((day_open - day_close) / day_open) * 100
                
                bt_list.append({"Date": hist.index[i].date(), "Type": trade_type, "Gap %": round(gap, 2), "Trade Result %": round(profit, 2)})
        
        bt_df = pd.DataFrame(bt_list)
        
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Gaps Found (30d)", len(bt_df))
        if not bt_df.empty:
            wins = len(bt_df[bt_df['Trade Result %'] > 0])
            win_rate = (wins / len(bt_df)) * 100
            b2.metric("Strategy Win Rate", f"{win_rate:.1f}%")
            b3.metric("Avg Profit/Trade", f"{bt_df['Trade Result %'].mean():.2f}%")
            b4.metric("Current RSI", row_stats["RSI"])
            st.dataframe(bt_df, use_container_width=True, hide_index=True)
        else:
            st.warning("No strategy-compliant gaps found in historical data.")

    st.divider()
    st.subheader("Market Heatmap (Gap % Distribution)")
    st.bar_chart(df.set_index("Ticker")["Gap %"])
else:
    st.info("👈 Set your parameters and click 'Run Market Scan' to begin.")