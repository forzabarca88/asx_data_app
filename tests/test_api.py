import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from api_client import get_health, get_available_symbols, BASE_URL


def test_health_endpoint():
    """Test that /health returns 200 OK and contains symbols (mocked)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "status": "healthy",
            "refreshes": {
                "AAPL": {"last_refresh": "2025-01-01"},
                "GOOG": {"last_refresh": "2025-01-01"},
                "MSFT": {"last_refresh": "2025-01-01"},
            },
        }
    }

    with patch("api_client.requests.get", return_value=mock_response):
        result = get_health()
        assert result.get("data", {}).get("status") == "healthy", "Status should be 'healthy'"
        refreshes = result.get("data", {}).get("refreshes", {})
        assert len(refreshes) > 0, "Should return at least one symbol"
        print(f"PASS: /health returned {len(refreshes)} symbols. Status: {result['data']['status']}")
        print(f"Sample symbols: {list(refreshes.keys())[:5]}")


def test_available_symbols():
    """Test that get_available_symbols extracts symbol keys (mocked)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "status": "healthy",
            "refreshes": {
                "AAPL": {"last_refresh": "2025-01-01"},
                "GOOG": {"last_refresh": "2025-01-01"},
                "MSFT": {"last_refresh": "2025-01-01"},
            },
        }
    }

    with patch("api_client.requests.get", return_value=mock_response):
        symbols = get_available_symbols()
        assert set(symbols) == {"AAPL", "GOOG", "MSFT"}, f"Expected 3 symbols, got {symbols}"
        print(f"PASS: get_available_symbols returned {symbols}")


def test_health_endpoint_unhealthy():
    """Test that /health correctly reports unhealthy status (mocked)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": {
            "status": "unhealthy",
            "refreshes": {},
        }
    }

    with patch("api_client.requests.get", return_value=mock_response):
        result = get_health()
        assert result.get("data", {}).get("status") == "unhealthy"
        print("PASS: /health correctly reports unhealthy status")


def test_health_endpoint_http_error():
    """Test that HTTP errors propagate (mocked)."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status = MagicMock(side_effect=Exception("Server Error"))

    with patch("api_client.requests.get", return_value=mock_response):
        try:
            get_health()
            assert False, "Should have raised an exception"
        except Exception as e:
            assert "Server Error" in str(e)
            print("PASS: HTTP errors propagate correctly")


if __name__ == "__main__":
    tests = [
        test_health_endpoint,
        test_available_symbols,
        test_health_endpoint_unhealthy,
        test_health_endpoint_http_error,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed, {failed} failed")
    if failed == 0:
        print("ALL TESTS PASS")
    else:
        print("SOME TESTS FAILED")
