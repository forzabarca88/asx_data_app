import httpx

from .config import settings
from .models import Company, HistoryItem


def get_api_client():
    return ApiClient()


class ApiClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or settings.base_api_url

    async def get_companies(self) -> list[Company]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.get("/health")
            resp.raise_for_status()
            data = resp.json()
            # API returns {"symbols": {"IAG": "2026-04-24T08:01:54", ...}, ...}
            # or test mock returns [{"code": "IAG"}, {"code": "CBA"}]
            if isinstance(data, dict):
                symbols = data.get("symbols", {})
                return [Company(code=symbol) for symbol in symbols.keys()]
            return [Company(code=item["code"]) for item in data]

    async def get_company_history(self, code: str) -> list[HistoryItem]:
        async with httpx.AsyncClient(base_url=self.base_url) as client:
            resp = await client.get(f"/company/{code}/history")
            resp.raise_for_status()
            data = resp.json()
            # API returns [{"symbol": "IAG", "fetched_at": "...", "priceClose": 100.0, ...}, ...]
            if isinstance(data, str):
                return []
            return [HistoryItem(**item) for item in data]
