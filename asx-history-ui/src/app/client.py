import httpx
from .config import settings
from .models import Company, HistoryItem


class ApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.base_api_url

    async def get_companies(self) -> list[Company]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.get("/health")
            resp.raise_for_status()
            data = resp.json()
            # Handle both list and dict responses
            if isinstance(data, list):
                return [Company(code=item) if isinstance(item, str) else Company(code=item.get("code")) for item in data]
            elif isinstance(data, dict):
                return [Company(code=data.get("code"))]
            return []

    async def get_company_history(self, code: str) -> list[HistoryItem]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.get(f"/company/{code}/history")
            resp.raise_for_status()
            data = resp.json()
            # Handle both list and dict responses
            if isinstance(data, list):
                return [HistoryItem(**item) for item in data]
            elif isinstance(data, dict):
                return [HistoryItem(**data)]
            return []
