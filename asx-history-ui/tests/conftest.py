from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def client() -> TestClient:
    """Test client for the app."""
    from app.main import app

    with TestClient(app) as ac:
        yield ac
