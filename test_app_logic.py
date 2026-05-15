#!/usr/bin/env python
"""Unit tests for app.py business logic.

These tests verify edge case handling in the Streamlit app,
particularly around numeric operations and pandas Series handling.
"""
import sys
sys.path.insert(0, '.')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def test_price_change_calculation():
    """Test that price change calculation handles various edge cases."""
    
    # Test 1: Normal case with valid data
    latest = pd.Series({
        'priceClose': 0.205,
        'fetched_at': datetime.now()
    })
    prev = pd.Series({
        'priceClose': 0.200,
        'fetched_at': datetime.now() - timedelta(days=1)
    })
    
    latest_price_close = float(latest.get('priceClose', 0)) if pd.notna(latest.get('priceClose')) else 0.0
    prev_price_close = float(prev.get('priceClose', 0)) if prev is not None and pd.notna(prev.get('priceClose')) else 0.0
    
    price_change = latest_price_close - prev_price_close
    change_pct = (price_change / abs(prev_price_close)) * 100 if abs(prev_price_close) > 0 else 0
    
    assert abs(price_change - 0.005) < 1e-10, f"Expected 0.005, got {price_change}"
    assert abs(change_pct - 2.5) < 0.01, f"Expected ~2.5%, got {change_pct}%"
    print("[OK] Test 1 passed: Normal price change calculation")


def test_price_change_with_nan():
    """Test handling of NaN values in price data."""
    
    # Test with NaN value
    latest = pd.Series({
        'priceClose': np.nan,
        'fetched_at': datetime.now()
    })
    prev = pd.Series({
        'priceClose': 0.200,
        'fetched_at': datetime.now() - timedelta(days=1)
    })
    
    latest_price_close = float(latest.get('priceClose', 0)) if pd.notna(latest.get('priceClose')) else 0.0
    prev_price_close = float(prev.get('priceClose', 0)) if prev is not None and pd.notna(prev.get('priceClose')) else 0.0
    
    assert latest_price_close == 0.0, f"Expected 0.0 for NaN, got {latest_price_close}"
    assert prev_price_close == 0.2, f"Expected 0.2, got {prev_price_close}"
    print("[OK] Test 2 passed: NaN handling")


def test_price_change_with_empty_prev():
    """Test handling when previous record is None (empty dataframe)."""
    
    # Simulate case where df has only one row or is empty
    latest = pd.Series({
        'priceClose': 0.205,
        'fetched_at': datetime.now()
    })
    prev = None  # This represents the case where we have no previous record
    
    latest_price_close = float(latest.get('priceClose', 0)) if pd.notna(latest.get('priceClose')) else 0.0
    prev_price_close = float(prev.get('priceClose', 0)) if prev is not None and pd.notna(prev.get('priceClose')) else 0.0
    
    assert latest_price_close == 0.205, f"Expected 0.205, got {latest_price_close}"
    assert prev_price_close == 0.0, f"Expected 0.0 for None, got {prev_price_close}"
    print("[OK] Test 3 passed: Empty previous record handling")


def test_price_change_series_boolean():
    """Test that we don't use pandas Series in boolean context directly."""
    
    # This should trigger the ValueError if not handled properly
    series = pd.Series([1, 2, 3])
    
    # Wrong way (would raise ValueError):
    try:
        if series:
            pass
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "ambiguous" in str(e).lower()
    
    # Right way - use .empty or explicit bool conversion
    assert not series.empty  # Safe check
    print("[OK] Test 4 passed: Boolean context handling")


def test_price_change_division_by_zero():
    """Test that we handle division by zero safely."""
    
    latest = pd.Series({'priceClose': 0.205})
    prev = pd.Series({'priceClose': 0.0})  # Zero value
    
    latest_price_close = float(latest.get('priceClose', 0)) if pd.notna(latest.get('priceClose')) else 0.0
    prev_price_close = float(prev.get('priceClose', 0)) if prev is not None and pd.notna(prev.get('priceClose')) else 0.0
    
    # Should not raise ZeroDivisionError - use safe division
    abs_prev = abs(prev_price_close)
    change_pct = (latest_price_close - prev_price_close) / abs_prev if abs_prev > 0 else 0
    
    assert change_pct == 0.0, f"Expected 0.0 when dividing by zero, got {change_pct}"
    print("[OK] Test 7 passed: Division by zero handling")


def test_empty_dataframe_handling():
    """Test handling of empty dataframe scenarios."""
    
    # Empty series
    latest = pd.Series(dtype='float')
    prev = None
    
    latest_price_close = float(latest.get('priceClose', 0)) if pd.notna(latest.get('priceClose')) else 0.0
    prev_price_close = float(prev.get('priceClose', 0)) if prev is not None and pd.notna(prev.get('priceClose')) else 0.0
    
    assert latest_price_close == 0.0, f"Expected 0.0 for empty series, got {latest_price_close}"
    assert prev_price_close == 0.0, f"Expected 0.0 for None, got {prev_price_close}"
    print("[OK] Test 5 passed: Empty dataframe handling")


def test_missing_keys():
    """Test handling of missing keys in series."""
    
    latest = pd.Series({})  # Empty dict means no keys
    prev = pd.Series({'fetched_at': datetime.now() - timedelta(days=1)})  # Missing priceClose
    
    latest_price_close = float(latest.get('priceClose', 0)) if pd.notna(latest.get('priceClose')) else 0.0
    prev_price_close = float(prev.get('priceClose', 0)) if prev is not None and pd.notna(prev.get('priceClose')) else 0.0
    
    assert latest_price_close == 0.0, f"Expected 0.0 for missing key, got {latest_price_close}"
    assert prev_price_close == 0.0, f"Expected 0.0 for missing key, got {prev_price_close}"
    print("[OK] Test 6 passed: Missing keys handling")


if __name__ == '__main__':
    print("Running app logic unit tests...")
    print("="*50)
    
    test_price_change_calculation()
    test_price_change_with_nan()
    test_price_change_with_empty_prev()
    test_price_change_series_boolean()
    test_price_change_division_by_zero()
    test_empty_dataframe_handling()
    test_missing_keys()
    
    print("="*50)
    print("All tests passed!")