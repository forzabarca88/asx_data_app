import requests
import csv
import json
import os
import sys
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

API_BASE_URL = "http://192.168.0.50:30181"
CSV_CACHE_DIR = "data"
CSV_FILENAME = "asx_data.csv"
CACHE_DATA = None  # Global cache to avoid re-downloading

def get_csv_path(start_date: Optional[str] = None) -> str:
    """Get the full path to the cached CSV file."""
    os.makedirs(CSV_CACHE_DIR, exist_ok=True)
    if start_date:
        return os.path.join(CSV_CACHE_DIR, f"{CSV_FILENAME}_{start_date}.csv")
    return os.path.join(CSV_CACHE_DIR, CSV_FILENAME)

def is_file_fresh(csv_path: str) -> bool:
    """
    Check if file was modified today (within last 24 hours).
    
    Args:
        csv_path: Path to the cached file
        
    Returns:
        bool: True if file exists and modified within last 24 hours, False otherwise
    """
    if not os.path.exists(csv_path):
        return False
    
    try:
        mtime = datetime.fromtimestamp(os.path.getmtime(csv_path))
        now = datetime.now()
        age_hours = (now - mtime).total_seconds() / 3600
        # File is fresh if modified within last 24 hours
        return age_hours <= 24
    except Exception:
        return False

def download_csv_once(start_date: Optional[str] = None, is_test_mode: bool = False) -> Dict[str, Any]:
    """
    Download the complete CSV once when the app starts from the API.
    If file exists and modified today, use cached data.
    
    Args:
        start_date: Filter data to records from this date (YYYY-MM-DD). Defaults to 3 days ago if is_test_mode=True.
        is_test_mode: If True, uses start_date filter for testing. If False, fetches full CSV.
                     Auto-detected when running as a test script (filename contains 'test_').
    
    Returns:
        dict: Dictionary containing:
            - 'symbols': List of unique company symbols
            - 'data': Full data loaded from CSV as list of dicts
            - 'fetched_at': ISO timestamp when download completed
    """
    global CACHE_DATA
    
    # Auto-detect test mode: running as script (test file) vs module import by app
    if not is_test_mode:
        try:
            current_module = getattr(sys.modules.get('__main__'), '__file__', '')
            if 'test_' in str(current_module).lower() and current_module.endswith('.py'):
                is_test_mode = True
        except Exception:
            pass
    
    # Use start_date filter in test mode (3 days ago), otherwise fetch full data
    if is_test_mode and not start_date:
        start_date = (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d')
    elif not is_test_mode and not start_date:
        # No date filter for full CSV download in production
        pass
    
    # Check if we have fresh cached data
    csv_path = get_csv_path(start_date=start_date)
    
    # If CACHE_DATA already populated from earlier in same process, use it
    if CACHE_DATA is not None:
        return CACHE_DATA
    
    # If file exists and is fresh (< 24h), read from CSV (no API call needed)
    if os.path.exists(csv_path) and is_file_fresh(csv_path):
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            symbols = sorted(list(set(row['symbol'] for row in rows)))
            CACHE_DATA = {
                'symbols': symbols,
                'data': rows,
                'fetched_at': datetime.now().isoformat()
            }
            return CACHE_DATA
        except Exception as e:
            print(f"Error reading CSV file {csv_path}: {e}")
    
    # Download new data from API
    csv_url = f"{API_BASE_URL}/export/company"
    params = {'start_date': start_date}
    try:
        response = requests.get(csv_url, timeout=120, stream=True, params=params)
        response.raise_for_status()
        csv_content = b''.join(response.iter_content(chunk_size=8192))
    except requests.RequestException as e:
        print(f"Error downloading CSV from {csv_url}?start_date={start_date}: {e}")
        raise
    
    # Write to cache file
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_content.decode('utf-8'))
    
    # Parse CSV content into list of dicts
    reader = csv.DictReader(csv_content.decode('utf-8').splitlines())
    rows = list(reader)
    
    if not rows:
        raise ValueError(f"CSV download returned empty data from {csv_url}?start_date={start_date}")
    
    # Extract unique symbols
    symbols = sorted(list(set(row['symbol'] for row in rows)))
    
    # Store in global cache for subsequent calls
    CACHE_DATA = {
        'symbols': symbols,
        'data': rows,
        'fetched_at': datetime.now().isoformat()
    }

    return CACHE_DATA

def get_available_companies() -> List[str]:
    """
    Returns list of available company symbols from cached CSV.
    Uses global cache if available, avoiding repeated downloads.
    
    Returns:
        list: List of company symbols (e.g., ["10X", "14D", ...])
    """
    return download_csv_once()['symbols']

def get_company_history(symbol: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get historical data for a specific company from cached CSV.
    Uses global cache if available, avoiding repeated downloads.
    
    Args:
        symbol: Company symbol (e.g., "14D")
        start_date: Optional start date filter (YYYY-MM-DD format)
        end_date: Optional end date filter (YYYY-MM-DD format)
    
    Returns:
        list: Data array containing historical records for the given company
    """
    cache = download_csv_once()
    rows = cache['data']
    
    # Filter by symbol and optional date range
    filtered = [
        row for row in rows
        if row['symbol'].lower() == symbol.lower()
    ]
    
    if start_date:
        filtered = [row for row in filtered if datetime.fromisoformat(row.get('fetched_at', '')) >= datetime.strptime(start_date, '%Y-%m-%d')]
    if end_date:
        filtered = [row for row in filtered if datetime.fromisoformat(row.get('fetched_at', '')) <= datetime.strptime(end_date, '%Y-%m-%d')]
    
    return filtered

def reset_cache():
    """
    Reset the global cache (useful for testing).
    """
    global CACHE_DATA
    CACHE_DATA = None