from fastapi import Request, status

from .client import ApiClient
from .config import settings
from .models import Company, HistoryItem


def get_api_client():
    return ApiClient()


async def get_companies():
    client = get_api_client()
    return await client.get_companies()


async def get_company_history(code: str):
    client = get_api_client()
    return await client.get_company_history(code)
