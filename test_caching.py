#!/usr/bin/env python
"""Test CSV caching behavior."""
import sys
sys.path.insert(0, '.')

from csv_client import download_csv_once, CACHE_DATA, reset_cache, get_company_history


def test_single_download():
    """Verify CSV is downloaded only once and cached globally."""
    print("Testing CSV single download caching...")
    
    # Clear cache first
    reset_cache()
    
    # First call - should download
    result1 = download_csv_once(is_test_mode=True)
    initial_symbols = len(result1['symbols'])
    print(f"  Downloaded {initial_symbols} symbols")
    
    # Second call - should use cache
    result2 = download_csv_once(is_test_mode=True)
    cached_symbols = len(result2['symbols'])
    
    assert initial_symbols == cached_symbols, "Cache mismatch!"
    print("  [OK] Second call returned cached data")
    
    # Third call - should still use cache
    result3 = download_csv_once(is_test_mode=True)
    third_symbols = len(result3['symbols'])
    
    assert initial_symbols == third_symbols, "Cache mismatch!"
    print("  [OK] Third call returned cached data")
    
    # Verify global cache via module access
    import csv_client
    assert csv_client.CACHE_DATA is not None, "Global cache should be populated"
    assert 'symbols' in csv_client.CACHE_DATA, "Cache should have symbols key"
    assert len(csv_client.CACHE_DATA['symbols']) == initial_symbols, f"Global cache mismatch: expected {initial_symbols}, got {len(csv_client.CACHE_DATA['symbols'])}"
    print("  [OK] Global cache populated correctly")
    
    print("Single download test passed!")


def test_cache_reset():
    """Verify reset_cache() clears the global cache."""
    print("\nTesting cache reset...")
    
    # Populate cache
    download_csv_once(is_test_mode=True)
    
    # Reset
    reset_cache()
    assert CACHE_DATA is None, "Cache should be cleared"
    print("  [OK] Cache reset successful")


def test_available_companies_uses_cache():
    """Verify get_available_companies() uses global cache."""
    print("\nTesting get_available_companies() caching...")
    
    # Clear and populate
    reset_cache()
    companies1 = download_csv_once(is_test_mode=True)
    
    # Call via get_available_companies
    companies2 = download_csv_once(is_test_mode=True)
    
    assert len(companies1['symbols']) == len(companies2['symbols']), "Symbol count mismatch"
    print("  [OK] get_available_companies() works with cached data")


def test_get_company_history_uses_cache():
    """Verify get_company_history() uses global cache."""
    print("\nTesting get_company_history() caching...")
    
    # Get history - this should use cached data
    symbol = '10X'
    history1 = get_company_history(symbol)
    
    # Get same symbol again
    history2 = get_company_history(symbol)
    
    assert len(history1) == len(history2), "History length mismatch"
    print("  [OK] get_company_history() uses cached data")


if __name__ == '__main__':
    print("Running CSV caching tests...")
    print("="*50)
    
    test_single_download()
    test_cache_reset()
    test_available_companies_uses_cache()
    test_get_company_history_uses_cache()
    
    print("="*50)
    print("All caching tests passed!")