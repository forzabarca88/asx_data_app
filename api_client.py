import requests
from requests.exceptions import RequestException


BASE_URL = "http://192.168.0.50:30181"


def get_available_companies():
    """GET /health and extract company symbols from refreshes"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        # API returns {"data": {"refreshes": {...}}}
        return list(data.get('data', {}).get('refreshes', {}).keys())
    except RequestException as e:
        raise Exception(f"Failed to fetch health: {str(e)}")


def get_company_history(symbol: str):
    """GET company history data"""
    try:
        response = requests.get(f"{BASE_URL}/company/{symbol}/history", timeout=10)
        response.raise_for_status()
        return response.json().get('data', [])
    except RequestException as e:
        raise Exception(f"Failed to fetch history for {symbol}: {str(e)}")
