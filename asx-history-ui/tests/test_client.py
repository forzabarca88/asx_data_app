import pytest
from httpx import AsyncClient

import sys
sys.path.insert(0, "src")

from app.client import ApiClient


@pytest.mark.asyncio
async def test_get_companies_returns_company_models():
    client = ApiClient()
    
    from httpx import MockTransport
    
    async def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return {
                    "symbols": {"IAG": "2026-04-24T08:01:54", "CBA": "2026-04-24T08:01:53"},
                }
        
        return MockResponse()
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("httpx.AsyncClient.get", mock_get)
        companies = await client.get_companies()
    
    assert len(companies) == 2
    assert companies[0].code == "IAG"
    assert companies[1].code == "CBA"


@pytest.mark.asyncio
async def test_get_company_history_returns_history_items():
    client = ApiClient()
    
    from httpx import MockTransport
    
    async def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return [
                    {
                        "symbol": "IAG",
                        "fetched_at": "2026-04-22T08:01:52.423482",
                        "isin": "AU000000IAG3",
                        "priceClose": 100.50,
                        "priceDayHigh": 102.00,
                        "priceDayLow": 99.00,
                        "volume": 1000000,
                    }
                ]
        
        return MockResponse()
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("httpx.AsyncClient.get", mock_get)
        history = await client.get_company_history("IAG")
    
    assert len(history) == 1
    assert history[0].priceClose == 100.50
