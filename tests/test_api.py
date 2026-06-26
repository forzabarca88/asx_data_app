import sys
import os
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from api_client import get_health, BASE_URL


def test_health_endpoint():
    """Test that /health returns 200 OK and contains symbols."""
    try:
        result = get_health()
        assert result.get("data", {}).get("status") == "healthy", "Status should be 'healthy'"
        refreshes = result.get("data", {}).get("refreshes", {})
        assert len(refreshes) > 0, "Should return at least one symbol"
        print(f"PASS: /health returned {len(refreshes)} symbols. Status: {result['data']['status']}")
        print(f"Sample symbols: {list(refreshes.keys())[:5]}")
    except requests.exceptions.RequestException as e:
        print(f"SKIP: API at {BASE_URL} is unreachable ({e})")
        raise


if __name__ == "__main__":
    try:
        test_health_endpoint()
        print("\nPhase 2 validation: PASS")
    except Exception as e:
        print(f"\nPhase 2 validation: FAIL ({e})")
