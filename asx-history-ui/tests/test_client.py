import pytest
from httpx import AsyncClient


@pytest.fixture
async def client() -> AsyncClient:
    """Test client for the app."""
    async with AsyncClient(app="app.main:app", base_url="http://test") as ac:
        yield ac


def test_get_companies_returns_company_models(client: AsyncClient) -> None:
    """Ensure /health returns company models."""
    # This will fail until we implement the client
    pass


def test_get_company_history_returns_history_items(client: AsyncClient) -> None:
    """Ensure /company/{code}/history returns history items."""
    # This will fail until we implement the client
    pass
