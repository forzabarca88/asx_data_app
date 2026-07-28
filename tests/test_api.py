import sys
import os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from api_client import get_health, get_available_symbols, get_bulk_csv_data, get_company_history


def test_health_success():
    """Health endpoint returns available symbols."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": {"status": "healthy", "refreshes": {"AAPL": {}, "GOOG": {}, "MSFT": {}}}
    }
    with patch("api_client.requests.get", return_value=mock_response):
        symbols = get_available_symbols()
        assert set(symbols) == {"AAPL", "GOOG", "MSFT"}
    print("PASS: health endpoint returns symbols")


def test_health_error_propagates():
    """HTTP errors propagate to caller."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status = MagicMock(side_effect=Exception("Server Error"))
    with patch("api_client.requests.get", return_value=mock_response):
        try:
            get_health()
            assert False, "Should have raised"
        except Exception as e:
            assert "Server Error" in str(e)
    print("PASS: HTTP errors propagate correctly")


def test_bulk_csv_with_date_params():
    """Bulk CSV fetch passes date parameters to API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.content = b"symbol,priceClose,fetched_at\nA,10.0,2024-01-01\n"

    with patch("api_client.requests.get", return_value=mock_response) as mock_get:
        get_bulk_csv_data(start_date="2024-01-01", end_date="2024-12-31")
        mock_get.assert_called_once()
        assert mock_get.call_args[1]["params"] == {"start_date": "2024-01-01", "end_date": "2024-12-31"}
    print("PASS: bulk CSV passes date params to API")


def test_company_history_with_date_params():
    """Company history fetch passes date parameters to API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"data": [{"symbol": "A", "priceClose": 10.0}]}

    with patch("api_client.requests.get", return_value=mock_response) as mock_get:
        get_company_history("TEST", start_date="2024-01-01", end_date="2024-06-30")
        mock_get.assert_called_once()
        assert mock_get.call_args[1]["params"] == {"start_date": "2024-01-01", "end_date": "2024-06-30"}
    print("PASS: company history passes date params to API")


if __name__ == "__main__":
    tests = [test_health_success, test_health_error_propagates, test_bulk_csv_with_date_params, test_company_history_with_date_params]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    print("ALL TESTS PASS" if failed == 0 else "SOME TESTS FAILED")
