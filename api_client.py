import os
import io
import time
import requests
import pandas as pd

BASE_URL = os.environ.get("ASX_API_BASE_URL", "http://192.168.0.50:30181")

# Named timeout constants: (connect_timeout, read_timeout)
CONNECT_TIMEOUT = 10
READ_TIMEOUT_HEALTH = 60
READ_TIMEOUT_BULK = 120
READ_TIMEOUT_HISTORY = 120

# Retry configuration: reduced to avoid blocking the Streamlit script thread
MAX_RETRIES = 2
BASE_RETRY_DELAY = 3


def get_health():
    """Fetch /health endpoint to get available stock symbols."""
    response = requests.get(
        f"{BASE_URL}/health",
        timeout=(CONNECT_TIMEOUT, READ_TIMEOUT_HEALTH),
    )
    response.raise_for_status()
    return response.json()


def get_available_symbols():
    """Extract list of available symbols from health endpoint."""
    health_data = get_health()
    return list(health_data.get("data", {}).get("refreshes", {}).keys())


def get_bulk_csv_data(start_date=None, end_date=None, max_retries=None):
    """Fetch bulk CSV data from /export/company and return as DataFrame.

    The bulk export is loaded whole (not streamed) since the response body
    must be fully buffered for pd.read_csv.
    """
    if max_retries is None:
        max_retries = MAX_RETRIES

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
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT_BULK),
            )
            response.raise_for_status()
            df = pd.read_csv(io.BytesIO(response.content), low_memory=False)
            return df
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = BASE_RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(wait_time)

    raise last_error


def get_company_history(symbol, start_date=None, end_date=None, max_retries=None):
    """Fetch historical data for a specific company and return as DataFrame."""
    if max_retries is None:
        max_retries = MAX_RETRIES

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
                timeout=(CONNECT_TIMEOUT, READ_TIMEOUT_HISTORY),
            )
            response.raise_for_status()
            json_data = response.json()
            data = json_data.get("data", [])
            df = pd.DataFrame(data)
            return df
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait_time = BASE_RETRY_DELAY * (2 ** (attempt - 1))
                time.sleep(wait_time)

    raise last_error
