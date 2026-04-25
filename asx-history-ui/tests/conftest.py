import sys
sys.path.insert(0, "src")

import pytest
from httpx import Response
from unittest.mock import patch

from app.client import get_api_client


@pytest.fixture
def mock_httpx_get(monkeypatch):
    """Mock httpx.AsyncClient.get to return test data"""
    
    async def mock_get(*args, **kwargs):
        url = args[0].url if args else kwargs.get('url')
        
        if "/health" in str(url):
            return Response(
                status_code=200,
                content=b'{"symbols": {"IAG": "2026-04-24T08:01:54", "CBA": "2026-04-24T08:01:53"}}'
            )
        elif "/history" in str(url):
            return Response(
                status_code=200,
                content=b'[{ "symbol": "IAG", "fetched_at": "2026-04-22T08:01:52.423482", "isin": "AU000000IAG3", "priceClose": 100.50, "priceDayHigh": 102.00, "priceDayLow": 99.00, "volume": 1000000 }]'
            )
        return Response(status_code=500)
    
    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)


@pytest.fixture
def mock_api_client(monkeypatch):
    """Fixture that mocks the external API calls"""
    client = get_api_client()
    monkeypatch.setattr("httpx.AsyncClient.get", mock_httpx_get)
    return client


@pytest.fixture(scope="session")
def patched_httpx(monkeypatch):
    """Patch httpx.AsyncClient.get at module level for all tests"""
    async def mock_get(*args, **kwargs):
        url = args[0].url if args else kwargs.get('url')
        
        if "/health" in str(url):
            return Response(
                status_code=200,
                content=b'{"symbols": {"IAG": "2026-04-24T08:01:54", "CBA": "2026-04-24T08:01:53"}}'
            )
        elif "/history" in str(url):
            return Response(
                status_code=200,
                content=b'[{ "symbol": "IAG", "fetched_at": "2026-04-22T08:01:52.423482", "isin": "AU000000IAG3", "priceClose": 100.50, "priceDayHigh": 102.00, "priceDayLow": 99.00, "volume": 1000000 }]'
            )
        return Response(status_code=500)
    
    with patch("httpx.AsyncClient.get", mock_get):
        yield
