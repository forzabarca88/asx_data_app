import logging
import sys
import signal
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from api_client import get_available_companies, get_company_history

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('asx_app')

# Set up signal handlers for Ctrl+C (SIGINT)
def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    logger.critical("\nReceived SIGINT (Ctrl+C) - Terminating application")
    sys.exit(0)

# Register signal handlers - wrapped in try-except for Streamlit compatibility
try:
    signal.signal(signal.SIGINT, signal_handler)
    logger.info("Signal handlers registered")
except ValueError as e:
    if "signal only works in main thread" in str(e):
        logger.warning(f"Signal handlers not registered: {e}")
        logger.info("This is expected in Streamlit environments")
    else:
        raise

# Cleanup function - also wrapped in try-except
def cleanup():
    try:
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    except ValueError:
        pass

import atexit
try:
    atexit.register(cleanup)
except ValueError:
    pass

# Configuration
DEFAULT_TOP_N = 10

# API Configuration
API_BASE_URL = "http://192.168.0.50:30181"


def fetch_company_data():
    """Fetch available companies from API"""
    logger.info(f"Fetching available companies from {API_BASE_URL}/health")
    try:
        health_url = f"{API_BASE_URL}/health"
        response = requests.get(health_url, timeout=10)
        response.raise_for_status()
        data = response.json()
        companies = list(data.get("data", {}).get("refreshes", {}).keys())
        logger.info(f"Successfully fetched {len(companies)} companies")
        return companies
    except requests.RequestException as e:
        logger.error(f"API Unavailable: {str(e)}")
        st.error(f"API Unavailable: {str(e)}")
        return []


def fetch_history(symbol):
    """Fetch historical data for a company"""
    logger.info(f"Fetching history for symbol: {symbol}")
    data = get_company_history(symbol)
    logger.info(f"Fetched {len(data)} records for {symbol}")
    return data


def process_dataframe(raw_data):
    """Convert raw API data to clean DataFrame"""
    if not raw_data:
        logger.info("No raw data to process")
        return pd.DataFrame()
    
    df = pd.DataFrame(raw_data)
    logger.info(f"Processed DataFrame columns: {list(df.columns)}")
    
    if 'fetched_at' in df.columns:
        df['fetched_at'] = pd.to_datetime(df['fetched_at'], errors='coerce')
    
    if 'fetched_at' in df.columns:
        df = df.sort_values('fetched_at', ascending=False).reset_index(drop=True)
        logger.info(f"Sorted by fetched_at (descending), reset index")
    
    numeric_cols = [
        'priceAsk', 'priceBid', 'priceClose', 'priceDayHigh', 'priceDayLow',
        'volumeAverage', 'cashFlow'
    ]
    valid_numeric = [col for col in numeric_cols if col in df.columns and df[col].dtype in ['float', 'int']]
    logger.info(f"Valid numeric columns: {valid_numeric}")
    
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
    logger.info(f"Calculating median performance for {len(companies)} companies")
    results = []
    
    batch_size = min(5, len(companies))
    logger.info(f"Processing in batches of {batch_size}")
    
    for i in range(0, len(companies), batch_size):
        batch = companies[i:i + batch_size]
        logger.info(f"Processing batch: {batch}")
        
        for symbol in batch:
            history = fetch_history(symbol)
            if not history:
                logger.debug(f"No history for {symbol}")
                continue
            
            df = pd.DataFrame(history)
            if 'fetched_at' not in df.columns or 'priceClose' not in df.columns:
                logger.debug(f"Missing columns for {symbol}")
                continue
            
            df['fetched_at'] = pd.to_datetime(df['fetched_at'], errors='coerce')
            df = df.sort_values('fetched_at', ascending=False).reset_index(drop=True)
            
            if df.empty:
                logger.debug(f"Empty DataFrame for {symbol}")
                continue
            
            latest = df.iloc[0]
            current_val = latest.get(selected_param, 0)
            
            if len(df) > 0 and selected_param in df.columns:
                median_val = df[selected_param].median()
            else:
                median_val = current_val
            
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
    
    if not results:
        logger.warning("No results generated")
        return pd.DataFrame()
    
    df_results = pd.DataFrame(results)
    df_results = df_results.sort_values('Change %', ascending=False)
    logger.info(f"Generated performance DataFrame with {len(df_results)} rows")
    
    return df_results


# Page configuration
st.set_page_config(
    page_title="ASX Stock Visualisation",
    page_icon="📈",
    layout="wide"
)

# Sidebar controls
with st.sidebar:
    logger.info("Initializing sidebar controls")
    st.header("📊 Select Company")
    companies = fetch_company_data()
    
    if not companies:
        logger.error("Unable to fetch companies from API")
        st.error("Unable to connect to API. Please check the network connection.")
        st.stop()
    
    logger.info(f"User selecting company from {len(companies)} available")
    selected_company = st.selectbox("Company", companies)
    
    st.divider()
    
    st.header("📉 Select Parameter")
    available_params = ['priceClose', 'priceAsk', 'priceBid', 'volumeAverage', 'cashFlow', 'priceDayHigh', 'priceDayLow']
    selected_param = st.selectbox("Parameter", available_params)

# Main content area
logger.info(f"Loading main content for {selected_company}")
col1, col2 = st.columns([3, 1])

with col1:
    logger.info(f"Fetching history for {selected_company}")
    history_data = fetch_history(selected_company)
    df, numeric_cols = process_dataframe(history_data)
    
    if df.empty:
        logger.warning(f"No historical data for {selected_company}")
        st.warning(f"No historical data available for {selected_company}")
    else:
        logger.info(f"Processing {len(df)} records")
        latest = df.iloc[0]
        prev = df.iloc[1] if len(df) > 1 else latest
        
        price_change = latest.get('priceClose', 0) - prev.get('priceClose', 0)
        change_pct = (price_change / prev.get('priceClose', 1)) * 100 if prev.get('priceClose', 0) else 0
        
        st.metric(
            label=f"Latest {selected_param}",
            value=f"{latest.get(selected_param, 0):,.2f}" if selected_param in latest else "N/A",
            delta=f"{price_change:+.2f} ({change_pct:+.2f}%)")
        
        if selected_param in numeric_cols and len(df) > 0:
            plot_data = df.dropna(subset=[selected_param, 'fetched_at'])
            
            if not plot_data.empty:
                logger.info(f"Rendering line chart for {selected_param}")
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
                logger.warning(f"No valid data points for {selected_param}")
                st.warning(f"No valid data points for {selected_param}")

with col2:
    if not df.empty:
        logger.info("Displaying recent data")
        st.subheader("Recent Data")
        display_cols = ['fetched_at', 'priceClose', 'volumeAverage']
        st.dataframe(df[display_cols].head(10), use_container_width=True)
    else:
        logger.debug("No data to display in recent data section")

# Top N Companies by Median Performance
st.divider()
st.subheader(f"📊 Top {DEFAULT_TOP_N} Companies by Median Change")

logger.info(f"Fetching all companies for performance analysis")
all_companies = fetch_company_data()

if all_companies:
    logger.info(f"Calculating performance for {len(all_companies)} companies")
    performance_df = calculate_median_performance(all_companies)
    
    if not performance_df.empty:
        top_n = min(DEFAULT_TOP_N, len(performance_df))
        logger.info(f"Displaying top {top_n} companies")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("📈 Top Gainers")
            gainers = performance_df.sort_values('Change %', ascending=False).head(min(5, top_n))
            
            if not gainers.empty:
                logger.info("Rendering gainers chart")
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
            losers = performance_df.sort_values('Change %', ascending=False).head(min(5, top_n))
            
            if not losers.empty:
                logger.info("Rendering losers chart")
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
        
        st.subheader(f"Full Ranking ({len(performance_df)} companies)")
        display_cols_perf = ['Symbol', 'Current Price', 'Median Price', 'Change %']
        st.dataframe(performance_df[display_cols_perf].head(top_n), use_container_width=True)
    else:
        logger.warning("No performance data calculated")
else:
    logger.error("No companies available for performance analysis")
    st.error("Unable to load performance data")

# Footer
st.divider()
st.caption("ASX Data Visualisation App | Powered by Streamlit")