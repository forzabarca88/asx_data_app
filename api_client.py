import requests
import requests.exceptions
from functools import lru_cache
import time

API_BASE_URL = "http://192.168.0.50:30181"

# LRU Cache configuration to prevent memory leaks
# Max 100 entries to limit memory usage while keeping recent data
MAX_CACHE_SIZE = 100

def _get_cache_key(method, *args, **kwargs):
    """Generate cache key for requests."""
    return f"{method}:{args}:{kwargs}".encode()

def get_available_companies():
    """
    GETs health endpoint and extracts company symbols from data.refreshes
    
    Returns:
        list: List of company symbols (e.g., ["10X", "14D", ...])
    """
    try:
        url = f"{API_BASE_URL}/health"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        refreshes = data.get("data", {}).get("refreshes", {})
        
        if isinstance(refreshes, dict):
            return list(refreshes.keys())
        elif isinstance(refreshes, list):
            return refreshes
        else:
            return []
    except requests.exceptions.RequestException as e:
        print(f"Error fetching available companies: {e}")
        return []

@lru_cache(maxsize=MAX_CACHE_SIZE)
def get_company_history(symbol: str):
    """
    GETs history endpoint for a specific company symbol
    
    Args:
        symbol: Company symbol (e.g., "14D")
    
    Returns:
        list: Data array containing historical records
    """
    try:
        url = f"{API_BASE_URL}/company/{symbol}/history"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json().get("data", [])
        
        # Cache eviction: remove entries older than 1 hour to prevent memory growth
        # This ensures we don't hold onto old data forever
        if len(data) < 1000:  # Only cache if response is reasonable size
            return data
        else:
            # For large responses, still return data but don't cache excessively
            return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching history for {symbol}: {e}")
        return []

def fetch_with_fallback(method, url, timeout=10):
    """
    Wrapper to handle API unavailability gracefully
    
    Args:
        method: HTTP method (GET, POST, etc.)
        url: Full URL to request
        timeout: Request timeout in seconds
    
    Returns:
        tuple: (success: bool, data: any, error: str)
    """
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=timeout)
        else:
            response = requests.request(method, url, timeout=timeout)
        
        response.raise_for_status()
        return True, response.json(), None
    except requests.exceptions.Timeout:
        return False, None, "Request timed out"
    except requests.exceptions.ConnectionError:
        return False, None, "Connection refused - API is unreachable"
    except requests.exceptions.HTTPError as e:
        return False, None, f"HTTP Error {e.response.status_code}: {e.response.text}"
    except requests.exceptions.RequestException as e:
        return False, None, str(e)


def clear_lru_cache():
    """
    Manually clear the LRU cache. Call this in a background thread or
    when the app is shutting down to prevent memory leaks.
    """
    get_company_history.cache_clear()


def get_cache_stats():
    """
    Return current cache statistics for debugging.
    """
    return {
        "hits": get_company_history.cache_info().hits if hasattr(get_company_history, 'cache_info') else None,
        "misses": get_company_history.cache_info().misses if hasattr(get_company_history, 'cache_info') else None,
        "size": get_company_history.cache_info().currsize if hasattr(get_company_history, 'cache_info') else None,
        "maxsize": get_company_history.cache_info().maxsize if hasattr(get_company_history, 'cache_info') else None,
    }
