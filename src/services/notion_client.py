from notion_client import Client

from src.core.config import settings


def get_notion_client() -> Client:
    return Client(auth=settings.NOTION_API_KEY)
