import requests
from requests.exceptions import RequestException


API_BASE_URL = "http://192.168.0.50:30181"


def get_available_companies() -> list[str]:
    """
    GETs the health endpoint and extracts company symbols from the response.
    
    The API returns a flat dictionary with symbols as keys, so we extract them directly.
    
    Returns:
        List of company symbols (e.g., ["10X", "14D", ...])
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract symbols from the flat dictionary
        companies = list(data.get("data", {}).get("refreshes", {}).keys())
        
        return companies
    except RequestException as e:
        print(f"Error fetching available companies: {e}")
        return []


def get_company_history(symbol: str) -> list[dict]:
    """
    GETs the history endpoint for a specific company.
    
    Args:
        symbol: Company symbol (e.g., "14D")
    
    Returns:
        List of historical records from the 'data' array
    """
    try:
        url = f"{API_BASE_URL}/company/{symbol}/history"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return data.get("data", [])
    except RequestException as e:
        print(f"Error fetching history for {symbol}: {e}")
        return []
