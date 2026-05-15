import logging
import sys
import signal
import streamlit as st
import pandas as pd
import plotly.express as px
from csv_client import download_csv_once, get_available_companies, get_company_history

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

# CSV Data Cache (loaded at startup)
CSV_DATA_CACHE = None

def get_csv_cache():
    """Get or initialize the CSV data cache with 3-day filter."""
    global CSV_DATA_CACHE
    if CSV_DATA_CACHE is None:
        from datetime import datetime, timedelta
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
        CSV_DATA_CACHE = download_csv_once(start_date=start_date)
    return CSV_DATA_CACHE


def fetch_company_data():
    """Fetch available companies from cached CSV data."""
    logger.info("Loading companies from cached CSV")
    return get_available_companies()


def fetch_history(symbol):
    """Fetch historical data for a company from cached CSV."""
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
    Calculate median-based percentage change for all companies using cached data.
    
    Args:
        companies: List of company symbols
        selected_param: Parameter to analyze (default: priceClose)
    
    Returns:
        DataFrame with company, current value, median value, and percentage change
    """
    logger.info(f"Calculating median performance for {len(companies)} companies from cached data")
    results = []
    
    # Get cache once to avoid repeated downloads
    cache = get_csv_cache()
    all_data = cache['data']
    
    for symbol in companies:
        # Filter data for this symbol
        symbol_data = [row for row in all_data if row['symbol'].lower() == symbol.lower()]
        
        if not symbol_data:
            logger.debug(f"No data found for {symbol}")
            continue
        
        # Sort by fetched_at descending to get latest first
        symbol_df = pd.DataFrame(symbol_data)
        symbol_df['fetched_at'] = pd.to_datetime(symbol_df['fetched_at'], errors='coerce')
        symbol_df = symbol_df.sort_values('fetched_at', ascending=False).reset_index(drop=True)
        
        if symbol_df.empty:
            continue
        
        latest = symbol_df.iloc[0]
        
        # Safely extract current value with type conversion
        raw_current = latest.get(selected_param, 0)
        if pd.notna(raw_current) and isinstance(raw_current, (str, float)):
            try:
                current_val = float(raw_current)
            except (ValueError, TypeError):
                current_val = 0.0
        else:
            current_val = 0.0
        
        # Calculate median from all available data points
        if len(symbol_df) > 0 and selected_param in symbol_df.columns:
            # Ensure we're calculating on numeric data only, filter out NaN/empty strings
            col_values = symbol_df[selected_param].dropna()
            if len(col_values) > 0 and pd.api.types.is_numeric_dtype(col_values):
                median_val = float(col_values.median())
            else:
                # No valid numeric data - use current_val but ensure it's numeric
                try:
                    median_val = float(current_val)
                except (ValueError, TypeError):
                    median_val = 0.0
        else:
            # Column doesn't exist or dataframe empty
            try:
                median_val = float(current_val)
            except (ValueError, TypeError):
                median_val = 0.0
        
        # Calculate percentage change safely
        if abs(median_val) > 0.01:  # Avoid division by near-zero
            try:
                pct_change = ((current_val - median_val) / abs(median_val)) * 100
            except (TypeError, ZeroDivisionError):
                pct_change = 0.0
        else:
            pct_change = 0.0
        
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
    logger.info(f"Generated performance DataFrame with {len(df_results)} rows from cached data")
    
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
        # Only use previous record if we have at least 2 valid records
        prev = df.iloc[1] if len(df) > 1 and not latest.empty else None
        
        # Safely extract numeric values
        latest_price_close = float(latest.get('priceClose', 0)) if pd.notna(latest.get('priceClose')) else 0.0
        prev_price_close = float(prev.get('priceClose', 0)) if prev is not None and pd.notna(prev.get('priceClose')) else 0.0
        
        # Safely format numeric values, handling string vs number type issues
        def safe_format(value):
            """Convert to float safely and format with commas."""
            if value is None or pd.isna(value):
                return "N/A"
            try:
                num = float(value)
                return f"{num:,.2f}"
            except (ValueError, TypeError):
                return str(value)
        
        price_change = latest_price_close - prev_price_close
        change_pct = (price_change / abs(prev_price_close)) * 100 if abs(prev_price_close) > 0 else 0
        
        st.metric(
            label=f"Latest {selected_param}",
            value=safe_format(latest.get(selected_param, 0)),
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