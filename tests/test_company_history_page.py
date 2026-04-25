from fastapi.testclient import TestClient
from app.main import app
from app.models import HistoryItem
from unittest.mock import patch, AsyncMock

def test_company_history_page_renders_table():
    # Mock ApiClient.get_company_history
    with patch("app.main.ApiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_company_history.return_value = [
            HistoryItem(
                date="2023-01-01",
                priceClose=100.5,
                priceDayHigh=105.0,
                priceDayLow=99.0,
                volume=1000000
            )
        ]
        mock_client_class.return_value = mock_client
        
        client = TestClient(app)
        response = client.get("/company/IAG")
        
        assert response.status_code == 200
        assert "IAG" in response.text  # Company code in title or heading
        assert "Date" in response.text  # Table header
        assert "Close" in response.text  # Table header
        assert "High" in response.text  # Table header
        assert "Low" in response.text  # Table header
        assert "Volume" in response.text  # Table header
        assert "2023-01-01" in response.text  # Date in table row
        assert "100.5" in response.text  # Close price in table row
        assert "105.0" in response.text  # High price in table row
        assert "99.0" in response.text  # Low price in table row
        assert "1,000,000" in response.text or "1000000" in response.text  # Volume in table row


def test_company_history_page_contains_charts():
    # Mock ApiClient.get_company_history
    with patch("app.main.ApiClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_company_history.return_value = [
            HistoryItem(
                date="2023-01-01",
                priceClose=100.5,
                priceDayHigh=105.0,
                priceDayLow=99.0,
                volume=1000000
            )
        ]
        mock_client_class.return_value = mock_client
        
        client = TestClient(app)
        response = client.get("/company/IAG")
        
        assert response.status_code == 200
        # Check that chart placeholders are included in the response
        assert "Price Close Chart" in response.text
        assert "High-Low Chart" in response.text
        assert "Volume Chart" in response.text
        assert "Chart would go here" in response.text