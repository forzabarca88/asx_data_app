import pytest
from unittest.mock import AsyncMock, patch
from app.client import ApiClient
from app.models import Company, HistoryItem

@pytest.mark.asyncio
async def test_get_companies_returns_company_models():
    # Create a proper mock for AsyncClient
    mock_response = AsyncMock()
    mock_response.json.return_value = [{"code": "IAG"}, {"code": "CBA"}]
    mock_response.raise_for_status.return_value = None
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        client = ApiClient()
        companies = await client.get_companies()
        
        assert len(companies) == 2
        assert isinstance(companies[0], Company)
        assert companies[0].code == "IAG"
        assert companies[1].code == "CBA"

@pytest.mark.asyncio
async def test_get_company_history_returns_history_items():
    # Create a proper mock for AsyncClient
    mock_response = AsyncMock()
    mock_response.json.return_value = [{
        "date": "2023-01-01",
        "priceClose": 100.5,
        "priceDayHigh": 105.0,
        "priceDayLow": 99.0,
        "volume": 1000000
    }]
    mock_response.raise_for_status.return_value = None
    
    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        client = ApiClient()
        history = await client.get_company_history("IAG")
        
        assert len(history) == 1
        assert isinstance(history[0], HistoryItem)
        assert history[0].date.isoformat() == "2023-01-01"
        assert history[0].priceClose == 100.5
        assert history[0].priceDayHigh == 105.0
        assert history[0].priceDayLow == 99.0
        assert history[0].volume == 1000000