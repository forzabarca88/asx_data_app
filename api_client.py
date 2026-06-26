import io
import time
import requests
import pandas as pd

BASE_URL = "http://192.168.0.50:30181"


def get_health():
    """Fetch /health endpoint to get available stock symbols."""
    response = requests.get(f"{BASE_URL}/health", timeout=(10, 60))
    response.raise_for_status()
    return response.json()


def get_available_symbols():
    """Extract list of available symbols from health endpoint."""
    health_data = get_health()
    return list(health_data.get("data", {}).get("refreshes", {}).keys())


def get_bulk_csv_data(start_date=None, end_date=None, max_retries=3):
    """Fetch bulk CSV data from /export/company and return as DataFrame."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                f"{BASE_URL}/export/company",
                params=params,
                timeout=(30, 600),
                stream=True,
            )
            response.raise_for_status()
            df = pd.read_csv(io.BytesIO(response.content), low_memory=False)
            return df
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = 5 * (2 ** (attempt - 1))
                time.sleep(wait_time)

    raise last_error


def get_company_history(symbol, start_date=None, end_date=None, max_retries=3):
    """Fetch historical data for a specific company and return as DataFrame."""
    params = {}
    if start_date:
        params["start_date"] = start_date
    if end_date:
        params["end_date"] = end_date

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                f"{BASE_URL}/company/{symbol}/history",
                params=params,
                timeout=(10, 120),
            )
            response.raise_for_status()
            json_data = response.json()
            data = json_data.get("data", [])
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = 3 * (2 ** (attempt - 1))
                time.sleep(wait_time)

    raise last_error

