import streamlit as st
import pandas as pd
import plotly.express as px


def test_top_gainers_sorted_descending():
    """Test that top gainers are sorted in descending order (highest first)."""
    # Create sample data
    data = {
        'Symbol': ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO'],
        'Change %': [5.5, 4.2, 3.8, 3.5, 2.9, 2.1, 1.8, 1.2, 0.5, -0.3]
    }
    df = pd.DataFrame(data)
    
    # Get top 5 gainers
    gainers = df.sort_values('Change %', ascending=False).head(5)
    
    # Verify descending order
    assert list(gainers['Change %']) == sorted(gainers['Change %'], reverse=True), \
        f"Expected descending order, got {list(gainers['Change %'])}"
    
    # Verify first item is highest
    assert gainers.iloc[0]['Change %'] == 5.5, \
        f"Expected highest value at top, got {gainers.iloc[0]['Change %']}"
    
    # Verify last item is lowest (in top 5)
    assert gainers.iloc[-1]['Change %'] == 2.9, \
        f"Expected lowest of top 5 at bottom of top 5, got {gainers.iloc[-1]['Change %']}"
    
    print("Top gainers test passed")


def test_top_losers_sorted_descending():
    """Test that top losers are sorted in descending order (least negative first)."""
    # Create sample data with negative values (losers)
    data = {
        'Symbol': ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'AMD', 'INTC', 'CSCO'],
        'Change %': [-5.5, -4.2, -3.8, -3.5, -2.9, -2.1, -1.8, -1.2, -0.5, 0.3]
    }
    df = pd.DataFrame(data)
    
    # Get top 5 "losers" (least negative, i.e., closest to zero)
    losers = df.sort_values('Change %', ascending=False).head(5)
    
    # Verify descending order (-2.1, -1.8, -1.2, -0.5, 0.3)
    expected_values = [0.3, -0.5, -1.2, -1.8, -2.1]
    actual_values = list(losers['Change %'])
    
    assert actual_values == expected_values, \
        f"Expected {expected_values}, got {actual_values}"
    
    # Verify first item is highest (least negative)
    assert losers.iloc[0]['Change %'] == 0.3, \
        f"Expected 0.3 at top, got {losers.iloc[0]['Change %']}"
    
    print("Top losers test passed")


def test_full_table_sorted_descending():
    """Test that the full ranking table is sorted descending."""
    data = {
        'Symbol': ['AAPL', 'GOOG', 'MSFT', 'AMZN', 'TSLA'],
        'Change %': [5.5, 4.2, 3.8, 3.5, 2.9]
    }
    df = pd.DataFrame(data)
    
    # Get top_n (let's say top_n = 5)
    top_n = 5
    top_gainers = df.sort_values('Change %', ascending=False).head(top_n)
    
    # Verify all items are in descending order
    for i in range(len(top_gainers) - 1):
        assert top_gainers.iloc[i]['Change %'] >= top_gainers.iloc[i+1]['Change %'], \
            f"Row {i} ({top_gainers.iloc[i]['Change %']}) should be >= Row {i+1} ({top_gainers.iloc[i+1]['Change %']})"
    
    print("Full table sorting test passed")


if __name__ == "__main__":
    test_top_gainers_sorted_descending()
    test_top_losers_sorted_descending()
    test_full_table_sorted_descending()
    print("\nAll tests passed!")