import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import os

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="ACDP FX Leaders", 
    layout="wide", 
    page_icon="💱",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. CURRENCY UNIVERSE CONFIGURATION (SPOT FX & INDICES)
# -----------------------------------------------------------------------------
CURRENCY_UNIVERSE = {
    # US Dollar Index
    "💵 US Dollar Index (DXY)": "DX-Y.NYB",

    # The Majors (Base USD)
    "🇯🇵 USD/JPY (Yen)": "USDJPY=X",
    "🇨🇦 USD/CAD (Loonie)": "USDCAD=X",
    "🇨🇭 USD/CHF (Swissie)": "USDCHF=X",

    # The Majors (Quote USD)
    "🇪🇺 EUR/USD (Euro)": "EURUSD=X",
    "🇬🇧 GBP/USD (Cable)": "GBPUSD=X",
    "🇦🇺 AUD/USD (Aussie)": "AUDUSD=X",
    "🇳🇿 NZD/USD (Kiwi)": "NZDUSD=X",

    # Key Crosses
    "🇪🇺 EUR/GBP": "EURGBP=X",
    "🇪🇺 EUR/JPY": "EURJPY=X",
    "🇪🇺 EUR/CHF": "EURCHF=X",
    "🇬🇧 GBP/JPY": "GBPJPY=X",
    "🇦🇺 AUD/JPY": "AUDJPY=X",
    "🇨🇦 CAD/JPY": "CADJPY=X",

    # Emerging Markets & Minors (vs USD)
    "🇮🇳 USD/INR (Rupee)": "USDINR=X",
    "🇨🇳 USD/CNY (Yuan)": "USDCNY=X",
    "🇲🇽 USD/MXN (Peso)": "USDMXN=X",
    "🇧🇷 USD/BRL (Real)": "USDBRL=X",
    "🇿🇦 USD/ZAR (Rand)": "USDZAR=X",
    "🇹🇷 USD/TRY (Lira)": "USDTRY=X",
    "🇸🇬 USD/SGD (Sing Dollar)": "USDSGD=X",
    "🇭🇰 USD/HKD (HK Dollar)": "USDHKD=X",
    "🇰🇷 USD/KRW (Won)": "USDKRW=X",
    "🇹🇼 USD/TWD (Taiwan $)": "USDTWD=X",
    
    # Currency Proxy ETFs (Optional liquidity/tracking layer)
    "💶 Euro Trust (FXE)": "FXE",
    "💴 Yen Trust (FXY)": "FXY",
    "💵 Bullish USD (UUP)": "UUP"
}

# -----------------------------------------------------------------------------
# 3. CSS & STYLING (English Lavender Theme)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    .stApp { background-color: #fbfaff; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #e9d5ff; box-shadow: 4px 0 15px rgba(139, 92, 246, 0.03); }
    [data-testid="stSidebar"] h1 { color: #4B365F; font-weight: 700; letter-spacing: -1px; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] label { color: #6b5b95; }
    .canvas-container { background: linear-gradient(135deg, #ffffff 0%, #f3e8ff 100%); padding: 30px; border-radius: 20px; border: 1px solid #d8b4fe; box-shadow: 0 10px 30px rgba(124, 58, 237, 0.08); margin-bottom: 25px; }
    .big-title { font-family: 'Arial Black', sans-serif; font-size: 3em; text-transform: uppercase; background: -webkit-linear-gradient(top, #4B365F, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; text-align: center; margin-bottom: 5px; }
    .subtitle { color: #8b5cf6; font-family: 'Courier New', monospace; text-align: center; font-size: 1em; font-weight: 600; }
    [data-testid="stDataFrame"] { border: 1px solid #e9d5ff; border-radius: 12px; overflow: hidden; background-color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #ffffff; border-radius: 4px; color: #4B365F; font-weight: 600; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
    .stTabs [data-baseweb="tab"][aria-selected="true"] { background-color: #f3e8ff; color: #7c3aed; border: 1px solid #d8b4fe; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 4. QUANT ENGINE & DYNAMIC FILTER
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def fetch_and_analyze_data():
    stats_data = []
    history_dict = {}
    
    progress_placeholder = st.empty()
    progress_bar = progress_placeholder.progress(0)
    total = len(CURRENCY_UNIVERSE)
    
    for i, (name, ticker) in enumerate(CURRENCY_UNIVERSE.items()):
        try:
            progress_bar.progress((i + 1) / total)
            
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2y")
            
            if hist.empty or len(hist) < 260:
                continue
                
            hist.index = hist.index.tz_localize(None)
            current_price = hist['Close'].iloc[-1]
            
            def get_price_lag(days):
                target_date = datetime.now() - timedelta(days=days)
                idx = hist.index.get_indexer([target_date], method='nearest')[0]
                return hist['Close'].iloc[idx]

            p12m = get_price_lag(365)
            p6m  = get_price_lag(180)
            p3m  = get_price_lag(90)
            p1m  = get_price_lag(30)
            
            r12 = (current_price - p12m) / p12m
            r6  = (current_price - p6m)  / p6m
            r3  = (current_price - p3m)  / p3m
            r1  = (current_price - p1m)  / p1m
            
            avg_score = (r12 + r6 + r3 + r1) / 4
            
            daily_returns = hist['Close'].pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252)
            
            stats_data.append({
                "Asset": name,
                "Price": current_price,
                "Score": avg_score,
                "Vol": volatility
            })
            
            history_dict[name] = hist['Close']
            
        except Exception:
            continue
            
    progress_placeholder.empty()
    
    df_stats = pd.DataFrame(stats_data)
    
    if not df_stats.empty:
        # Sort ALL currency pairs by Score (Highest Momentum to Lowest)
        df_stats = df_stats.sort_values("Score", ascending=False).reset_index(drop=True)
        
        # DYNAMIC INCLUSION: Automatically slice the Top 20 for the Dashboard
        df_stats = df_stats.head(20).copy()
        df_stats['Rank'] = df_stats.index + 1
        
        # Filter history dictionary to only include the winning Top 20 assets
        top_20_assets = df_stats['Asset'].tolist()
        history_dict = {k: v for k, v in history_dict.items() if k in top_20_assets}
    
    return df_stats, history_dict

@st.cache_data(ttl=3600)
def calculate_correlation(history_dict):
    if not history_dict:
        return pd.DataFrame()
    df_prices = pd.DataFrame(history_dict)
    df_returns = df_prices.pct_change().dropna()
    return df_returns.corr()

# -----------------------------------------------------------------------------
# 5. SIDEBAR & HEADER
# -----------------------------------------------------------------------------
header_col1, header_col2 = st.columns([1, 8])
with header_col1:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=60)

with st.sidebar:
    st.title("ACDP FX")
    st.caption("Automated Concentrated\nDiversified Portfolio")
    st.write("---")
    st.info(f"Dynamic Quant Engine actively scanning {len(CURRENCY_UNIVERSE)} global FX markets. Displaying Top 20.")
    st.write("---")
    st.caption(f"Last Update:\n{datetime.now().strftime('%Y-%m-%d %H:%M')}")

# -----------------------------------------------------------------------------
# 6. MAIN APP
# -----------------------------------------------------------------------------
st.markdown('<div class="canvas-container">', unsafe_allow_html=True)
st.markdown('<div class="big-title">FX MARKET LEADERS</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">RANKING SYSTEM BY ADVANCED QUANT ANALYTICS</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

with st.spinner("Scanning FX Universe and routing capital..."):
    df_stats, history_dict = fetch_and_analyze_data()
    df_corr = calculate_correlation(history_dict)

if not df_stats.empty:
    tab1, tab2 = st.tabs(["🏆 Currency Performance Heatmap", "🧩 Risk Architecture"])
    
    # --- TAB 1: RANKING SYSTEM (HEATMAP) ---
    with tab1:
        st.caption("Derived from ACDP Quant Algorithm | Relative Strength using quant analytics")
        
        heatmap_df = df_stats[['Rank', 'Asset', 'Price', 'Vol']].copy()
        heatmap_df = heatmap_df.set_index('Rank')

        st.dataframe(
            heatmap_df.style
            .format({
                'Price': '{:,.4f}',  # Changed to 4 decimals for FX standard pricing
                'Vol': '{:.2%}'
            })
            # Heatmap Gradient strictly on Price column, driven by Rank (Green=Top, Red=Bottom)
            .background_gradient(
                cmap='RdYlGn_r', 
                subset=['Price'], 
                gmap=heatmap_df.index
            )
            .set_properties(**{'text-align': 'center', 'font-weight': '600', 'color': '#2e2e2e'})
            .set_table_styles([{
                'selector': 'th',
                'props': [
                    ('text-align', 'center'), 
                    ('background-color', '#f3e8ff'), 
                    ('color', '#4B365F'),
                    ('font-size', '1.1em')
                ]
            }]),
            use_container_width=True,
            height=800
        )

    # --- TAB 2: RISK ANALYSIS ---
    with tab2:
        st.subheader("Active Portfolio Correlation & Volatility")
        st.caption("Risk parameters dynamically updated for the current Top 20 inclusions.")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown("**Correlation Matrix (Current Leaders)**")
            if not df_corr.empty:
                fig_corr = px.imshow(
                    df_corr, text_auto=".2f", aspect="auto",
                    color_continuous_scale="RdBu_r", zmin=-1, zmax=1
                )
                fig_corr.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#4B365F"), height=650
                )
                st.plotly_chart(fig_corr, use_container_width=True)
                
        with col2:
            st.markdown("**Annualized Volatility Matrix**")
            fig_vol = px.scatter(
                df_stats, x="Vol", y="Score", text="Asset",
                size=[15]*len(df_stats), color="Score",
                color_continuous_scale="Viridis",
                labels={"Vol": "Volatility (Risk)", "Score": "Momentum (Reward)"}
            )
            fig_vol.update_traces(textposition='top center')
            fig_vol.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(240,240,255,0.5)",
                font=dict(color="#4B365F"), height=650, showlegend=False
            )
            st.plotly_chart(fig_vol, use_container_width=True)

else:
    st.error("Unable to scan market. Please check internet connection.")

# Footer
st.write("---")
st.markdown(
    """
    <div style='text-align: center; color: #887bb0; font-size: 0.8em; font-family: sans-serif;'>
        © ACDP Framework • Built for Rajan Yadav • Powered by Investopedia Analytics Logic
    </div>
    """, 
    unsafe_allow_html=True
)