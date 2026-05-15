import requests
import requests.exceptions
import time

API_BASE_URL = "http://192.168.0.50:30181"


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
        
        if len(data) < 1000:
            return data
        else:
            return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching history for {symbol}: {e}")
        return []