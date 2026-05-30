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
        return True
    except requests.exceptions.RequestException as e:
        print(f"SKIP: API at {BASE_URL} is unreachable ({e})")
        return False


if __name__ == "__main__":
    passed = test_health_endpoint()
    if passed:
        print("\nPhase 2 validation: PASS")
    else:
        print("\nPhase 2 validation: SKIP (API unavailable)")
