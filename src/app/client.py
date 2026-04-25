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
            data = await resp.json()
            # adapt to actual shape
            return [Company(code=item["code"]) for item in data]

    async def get_company_history(self, code: str) -> list[HistoryItem]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.get(f"/company/{code}/history")
            resp.raise_for_status()
            data = await resp.json()
            return [HistoryItem(**item) for item in data]