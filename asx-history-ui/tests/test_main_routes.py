import pytest

from fastapi.testclient import TestClient

import sys
sys.path.insert(0, "src")

from app.main import app


def test_root_returns_200_and_html():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/html"


def test_home_lists_companies():
    from src.app.client import get_api_client
    
    api_client = get_api_client()
    
    from httpx import MockTransport
    
    async def mock_get(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return [
                    {"code": "IAG"},
                    {"code": "CBA"},
                ]
        
        return MockResponse()
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr("httpx.AsyncClient.get", mock_get)
        companies = api_client.get_companies()
    
    client = TestClient(app)
    response = client.get("/")
    
    html = response.text
    assert "IAG" in html
    assert "CBA" in html
    assert "/company/IAG" in html
    assert "/company/CBA" in html
