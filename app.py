import streamlit as st
import pandas as pd
import requests
import plotly.express as px

from api_client import get_available_companies, get_company_history


st.set_page_config(page_title="ASX Stock Visualiser", layout="wide")


def process_history_data(history_data):
    """Convert raw API history data to a pandas DataFrame"""
    df = pd.DataFrame(history_data)
    df['fetched_at'] = pd.to_datetime(df['fetched_at'])
    df = df.sort_values('fetched_at')
    return df


@st.cache_data(ttl=300)
def fetch_data(symbol: str, parameter: str):
    """Fetch and process data for a company and parameter"""
    try:
        companies = get_available_companies()
        if symbol not in companies:
            return None, f"Company '{symbol}' not found"
        
        history = get_company_history(symbol)
        df = process_history_data(history)
        
        if df.empty:
            return None, "No historical data available"
        
        return df, None
    except requests.exceptions.RequestException as e:
        return None, f"API error: {str(e)}"


def main():
    st.title("ASX Stock Visualiser")
    
    # Metrics section
    company = st.sidebar.selectbox("Select Company", get_available_companies())
    parameter = st.sidebar.selectbox("Select Parameter", ["priceClose", "priceAsk", "priceBid", "volumeAverage", "cashFlow"])
    
    df, error = fetch_data(company, parameter)
    
    if error:
        st.error(error)
        return
    
    if df is None or df.empty:
        st.warning("No historical data available for this company")
        return
    
    latest = df.iloc[0]
    previous = df.iloc[-1]
    
    st.metric("Latest Price", latest.get('priceClose', 'N/A'))
    st.metric("Change from Previous", f"{(latest.get('priceClose', 0) - previous.get('priceClose', 0)) / previous.get('priceClose', 1) * 100:.2f}%")
    
    fig = px.line(df, x='fetched_at', y=parameter, title=f'{company}: {parameter} over time')
    st.plotly_chart(fig, width='stretch')
    
    if 'incomeStatement' in df.iloc[0]:
        st.dataframe(df.iloc[0]['incomeStatement'])


if __name__ == "__main__":
    main()
