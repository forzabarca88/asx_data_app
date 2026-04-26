import streamlit as st
import pandas as pd
import plotly.express as px
from api_client import get_available_companies, get_company_history


# Cache the companies list to avoid fetching every time
@st.cache_data(ttl=300)
def get_companies():
    """Fetch available companies from API"""
    return get_available_companies()


# Cache data fetching to avoid redundant API calls
@st.cache_data(ttl=300)
def get_company_data(symbol: str):
    """Fetch historical data for a company"""
    return get_company_history(symbol)


def transform_to_dataframe(raw_data: list[dict]) -> pd.DataFrame:
    """
    Convert raw API data into a clean pandas DataFrame.
    
    Args:
        raw_data: List of historical records from API
    
    Returns:
        Sorted pandas DataFrame with datetime column
    """
    if not raw_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(raw_data)
    
    # Convert fetched_at to datetime
    df["fetched_at"] = pd.to_datetime(df["fetched_at"])
    
    # Sort chronologically
    df = df.sort_values("fetched_at")
    
    return df


def get_numerical_columns(df: pd.DataFrame) -> list[str]:
    """
    Identify numerical columns that can be graphed.
    
    Args:
        df: DataFrame to analyze
    
    Returns:
        List of numerical column names
    """
    if df.empty:
        return []
    
    numerical_cols = []
    for col in df.columns:
        # Check if column is float or int
        if df[col].dtype in ['float64', 'int64']:
            numerical_cols.append(col)
        # Also check for nullable float
        elif str(df[col].dtype).startswith('Float'):
            numerical_cols.append(col)
    
    return numerical_cols


# Main app logic
def main():
    st.set_page_config(page_title="ASX Stock Visualisation", layout="wide")
    
    st.title("ASX Stock Visualisation")
    
    # Get companies
    companies = get_companies()
    
    if not companies:
        st.error("Could not fetch companies from API. Please check the API is running at http://192.168.0.50:30181/health")
        return
    
    # Sidebar controls
    with st.sidebar:
        st.header("Controls")
        
        # Company selector
        selected_company = st.selectbox("Select Company", companies)
        
        # Fetch and transform data for this company
        raw_data = get_company_data(selected_company)
        df = transform_to_dataframe(raw_data)
        
        # Get available numerical parameters
        available_params = get_numerical_columns(df)
        default_params = ["priceClose", "priceAsk", "priceBid", "volumeAverage", "cashFlow"]
        
        # Filter to only available parameters
        available_params = [p for p in default_params if p in available_params]
        
        if not available_params:
            st.warning("No numerical parameters available for this company.")
            return
        
        selected_param = st.selectbox("Select Parameter to Visualise", available_params)
    
    # Fetch data again (will use cache)
    raw_data = get_company_data(selected_company)
    df = transform_to_dataframe(raw_data)
    
    if df.empty:
        st.warning(f"No historical data available for {selected_company}")
        return
    
    # Calculate metrics
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    
    # Display metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            label="Latest Price",
            value=f"{latest.get('priceClose', 0):.4f}",
            delta=f"{(latest.get('priceClose', 0) - previous.get('priceClose', 0)):.4f}"
        )
    with col2:
        st.metric(
            label="Latest Volume",
            value=f"{latest.get('volumeAverage', 0):,.0f}"
        )
    
    # Prepare data for chart
    chart_data = df.dropna(subset=[selected_param]).copy()
    
    if chart_data.empty:
        st.warning(f"No valid data for parameter: {selected_param}")
        return
    
    # Create chart
    fig = px.line(
        chart_data,
        x="fetched_at",
        y=selected_param,
        title=f"{selected_company} - {selected_param} Over Time",
        markers=True
    )
    
    st.plotly_chart(fig, width="stretch")
    
    # Display income statement
    latest_record = df.iloc[-1]
    income_statement = latest_record.get("incomeStatement", [])
    
    if income_statement:
        st.subheader("Income Statement")
        income_df = pd.DataFrame(income_statement)
        st.dataframe(income_df, width="stretch")


if __name__ == "__main__":
    main()
