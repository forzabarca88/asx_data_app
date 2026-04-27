import requests
from requests.exceptions import RequestException

BASE_URL = "http://192.168.0.50:30181"


def test_api():
    # Test health endpoint
    print("Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        response.raise_for_status()
        data = response.json()
        companies = list(data.get('data', {}).get('refreshes', {}).keys())
        print(f"Available companies: {companies}")
        
        # Test getting history for 14D
        print("\nTesting 14D history...")
        history = requests.get(f"{BASE_URL}/company/14D/history", timeout=10)
        history.raise_for_status()
        history_data = history.json().get('data', [])
        print(f"Number of records: {len(history_data)}")
        if history_data:
            print(f"First record: {history_data[0]}")
        
    except RequestException as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    test_api()
