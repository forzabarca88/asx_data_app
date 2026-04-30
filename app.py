import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from api_client import get_available_companies, get_company_history, get_cache_stats

# Configuration
DEFAULT_TOP_N = 10
MAX_CACHE_SIZE = 100  # Match api_client.py

# API Configuration
API_BASE_URL = "http://192.168.0.50:30181"

# Optimized caching with smaller TTL and cache stats
@st.cache_resource(ttl=60, max_entries=5)
def fetch_company_data():
    """Fetch available companies from API with limited cache size"""
    try:
        health_url = f"{API_BASE_URL}/health"
        response = requests.get(health_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        companies = list(data.get("data", {}).get("refreshes", {}).keys())
        
        # Log cache stats for debugging
        if hasattr(get_company_history, 'cache_info'):
            info = get_company_history.cache_info()
            print(f"API Cache: hits={info.hits}, misses={info.misses}, size={info.currsize}/{info.maxsize}")
        
        return companies
    except requests.RequestException as e:
        st.error(f"API Unavailable: {str(e)}")
        return []

@st.cache_resource(ttl=60, max_entries=5)
def fetch_history(symbol):
    """Fetch historical data for a company with optimized caching"""
    try:
        history_url = f"{API_BASE_URL}/company/{symbol}/history"
        response = requests.get(history_url, timeout=10)
        response.raise_for_status()
        
        # Check cache stats periodically
        if hasattr(get_company_history, 'cache_info'):
            info = get_company_history.cache_info()
            if info.currsize > MAX_CACHE_SIZE * 0.9:  # 90% threshold
                print(f"Cache near capacity ({info.currsize}/{info.maxsize}), evicting...")
                get_company_history.cache_clear()
        
        return response.json().get("data", [])
    except requests.RequestException as e:
        st.error(f"Failed to fetch history for {symbol}: {str(e)}")
        return []

def process_dataframe(raw_data):
    """Convert raw API data to clean DataFrame"""
    if not raw_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(raw_data)
    
    # Convert fetched_at to datetime
    if 'fetched_at' in df.columns:
        df['fetched_at'] = pd.to_datetime(df['fetched_at'], errors='coerce')
    
    # Sort chronologically
    if 'fetched_at' in df.columns:
        df = df.sort_values('fetched_at', ascending=False).reset_index(drop=True)
    
    # Identify numerical columns for plotting
    numeric_cols = [
        'priceAsk', 'priceBid', 'priceClose', 'priceDayHigh', 'priceDayLow',
        'volumeAverage', 'cashFlow'
    ]
    valid_numeric = [col for col in numeric_cols if col in df.columns and df[col].dtype in ['float', 'int']]
    
    return df, valid_numeric

def calculate_median_performance(companies, selected_param='priceClose'):
    """
    Calculate median-based percentage change for all companies.
    
    Args:
        companies: List of company symbols
        selected_param: Parameter to analyze (default: priceClose)
    
    Returns:
        DataFrame with company, current value, median value, and percentage change
    """
    results = []
    
    # Process in batches to limit memory usage
    batch_size = min(5, len(companies))  # Process max 5 companies at a time
    
    for i in range(0, len(companies), batch_size):
        batch = companies[i:i + batch_size]
        
        for symbol in batch:
            try:
                history = fetch_history(symbol)
                if not history:
                    continue
                
                df = pd.DataFrame(history)
                if 'fetched_at' not in df.columns or 'priceClose' not in df.columns:
                    continue
                
                # Convert datetime and sort
                df['fetched_at'] = pd.to_datetime(df['fetched_at'], errors='coerce')
                df = df.sort_values('fetched_at', ascending=False).reset_index(drop=True)
                
                if df.empty:
                    continue
                
                # Get latest and median values
                latest = df.iloc[0]
                current_val = latest.get(selected_param, 0)
                
                # Calculate median of all historical values
                if len(df) > 0 and selected_param in df.columns:
                    median_val = df[selected_param].median()
                else:
                    median_val = current_val
                
                # Calculate percentage change
                if median_val != 0:
                    pct_change = ((current_val - median_val) / abs(median_val)) * 100
                else:
                    pct_change = 0
                
                results.append({
                    'Symbol': symbol,
                    'Current Price': current_val,
                    'Median Price': median_val,
                    'Change %': pct_change
                })
            except Exception as e:
                continue
        
        # Evict cache after each batch to prevent memory buildup
        if hasattr(get_company_history, 'cache_info'):
            info = get_company_history.cache_info()
            if info.currsize > MAX_CACHE_SIZE * 0.8:
                get_company_history.cache_clear()
    
    if not results:
        return pd.DataFrame()
    
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('Change %', ascending=False)
    
    return df_results

# Page configuration
st.set_page_config(
    page_title="ASX Stock Visualisation",
    page_icon="📈",
    layout="wide"
)

# Sidebar controls
with st.sidebar:
    st.header("📊 Select Company")
    companies = fetch_company_data()
    
    if not companies:
        st.error("Unable to connect to API. Please check the network connection.")
        st.stop()
    
    selected_company = st.selectbox("Company", companies)
    
    st.divider()
    
    st.header("📉 Select Parameter")
    available_params = ['priceClose', 'priceAsk', 'priceBid', 'volumeAverage', 'cashFlow', 'priceDayHigh', 'priceDayLow']
    selected_param = st.selectbox("Parameter", available_params)
    
    # Cache statistics
    st.divider()
    st.caption("🔧 Cache Stats")
    cache_info = get_cache_stats()
    if cache_info:
        st.metric("Cache Hits", f"{cache_info.get('hits', 0):,}")
        st.metric("Cache Misses", f"{cache_info.get('misses', 0):,}")
        st.metric("Active Entries", f"{cache_info.get('size', 0)}/{cache_info.get('maxsize', '∞')}")

# Main content area
col1, col2 = st.columns([3, 1])

with col1:
    # Fetch and process data
    history_data = fetch_history(selected_company)
    df, numeric_cols = process_dataframe(history_data)
    
    if df.empty:
        st.warning(f"No historical data available for {selected_company}")
    else:
        # Display metrics
        latest = df.iloc[0]
        prev = df.iloc[1] if len(df) > 1 else latest
        
        price_change = latest.get('priceClose', 0) - prev.get('priceClose', 0)
        change_pct = (price_change / prev.get('priceClose', 1)) * 100 if prev.get('priceClose', 0) else 0
        
        st.metric(
            label=f"Latest {selected_param}",
            value=f"{latest.get(selected_param, 0):,.2f}" if selected_param in latest else "N/A",
            delta=f"{price_change:+.2f} ({change_pct:+.2f}%)"
        )
        
        # Create visualization
        if selected_param in numeric_cols and len(df) > 0:
            # Filter out nulls
            plot_data = df.dropna(subset=[selected_param, 'fetched_at'])
            
            if not plot_data.empty:
                fig = px.line(
                    plot_data,
                    x='fetched_at',
                    y=selected_param,
                    title=f"{selected_company} - {selected_param} Over Time",
                    markers=True,
                    template="plotly_white"
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning(f"No valid data points for {selected_param}")

with col2:
    # Display recent data as table
    if not df.empty:
        st.subheader("Recent Data")
        display_cols = ['fetched_at', 'priceClose', 'volumeAverage']
        st.dataframe(df[display_cols].head(10), use_container_width=True)

# Top N Companies by Median Performance
st.divider()
st.subheader(f"📊 Top {DEFAULT_TOP_N} Companies by Median Change")

# Fetch data for all companies
all_companies = fetch_company_data()
if all_companies:
    performance_df = calculate_median_performance(all_companies)
    
    if not performance_df.empty:
        # Display top gainers and losers
        top_n = min(DEFAULT_TOP_N, len(performance_df))
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("📈 Top Gainers")
            gainers = performance_df.head(min(5, top_n))
            
            if not gainers.empty:
                # Create a bar chart for top gainers
                fig_gainers = px.bar(
                    gainers,
                    x='Change %',
                    y='Symbol',
                    title='Top Gainers (vs Median)',
                    color='Change %',
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig_gainers, use_container_width=True)
            else:
                st.info("No gainers available")
        
        with col4:
            st.subheader("📉 Top Losers")
            losers = performance_df.tail(min(5, top_n)).sort_values('Change %')
            
            if not losers.empty:
                fig_losers = px.bar(
                    losers,
                    x='Change %',
                    y='Symbol',
                    title='Top Losers (vs Median)',
                    color='Change %',
                    color_continuous_scale='RdYlGn_r'
                )
                st.plotly_chart(fig_losers, use_container_width=True)
            else:
                st.info("No losers available")
        
        # Display detailed table
        st.subheader(f"Full Ranking ({len(performance_df)} companies)")
        # Select relevant columns for display
        display_cols_perf = ['Symbol', 'Current Price', 'Median Price', 'Change %']
        st.dataframe(performance_df[display_cols_perf].head(top_n), use_container_width=True)

# Footer
st.divider()
st.caption("ASX Data Visualisation App | Powered by Streamlit")

# Cleanup on shutdown
if 'cleanup_done' not in st.session_state:
    try:
        # Clear LRU cache to release memory
        if hasattr(get_company_history, 'cache_clear'):
            get_company_history.cache_clear()
        st.session_state.cleanup_done = True
    except Exception as e:
        pass
