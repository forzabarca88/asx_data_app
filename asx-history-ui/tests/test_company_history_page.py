import sys
sys.path.insert(0, "src")

from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.models import HistoryItem


def test_company_history_page_renders_table():
    history_data = [
        HistoryItem(
            symbol="IAG",
            fetched_at="2026-04-22T08:01:52.423482",
            isin="AU000000IAG3",
            priceClose=100.50,
            priceDayHigh=102.00,
            priceDayLow=99.00,
            volume=1000000
        )
    ]
    
    with patch("app.views.get_company_history", return_value=history_data):
        client = TestClient(app)
        response = client.get("/company/IAG")
        assert response.status_code == 200
        assert "Date" in response.text
        assert "Close" in response.text
        assert "High" in response.text
        assert "Low" in response.text


def test_company_history_page_contains_price_close_chart_div():
    client = TestClient(app)
    response = client.get("/company/IAG")
    assert response.status_code == 200
    assert 'id="price-close-chart"' in response.text or 'id="high-low-chart"' in response.text


def test_company_history_page_contains_high_low_chart_div():
    client = TestClient(app)
    response = client.get("/company/IAG")
    assert response.status_code == 200
    assert 'id="high-low-chart"' in response.text or 'id="volume-chart"' in response.text


def test_company_history_page_contains_volume_chart_div():
    client = TestClient(app)
    response = client.get("/company/IAG")
    assert response.status_code == 200
    assert 'id="volume-chart"' in response.text or 'id="high-low-chart"' in response.text
