import re

from langchain_core.tools import tool

from src.core.config import settings
from src.services.notion_client import get_notion_client


def _parse_inline(text: str) -> list[dict]:
    segments = []
    for part in re.split(r"(\*\*.+?\*\*)", text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            segments.append(
                {"text": {"content": part[2:-2]}, "annotations": {"bold": True}}
            )
        else:
            segments.append({"text": {"content": part}})
    return segments


def _markdown_to_blocks(report: str) -> list[dict]:
    blocks = []
    for line in report.split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")):
            blocks.append(
                {
                    "object": "block",
                    "type": "bulleted_list_item",
                    "bulleted_list_item": {"rich_text": _parse_inline(stripped[2:])},
                }
            )
        elif stripped.startswith("#"):
            level = min(len(stripped) - len(stripped.lstrip("#")), 3)
            blocks.append(
                {
                    "object": "block",
                    "type": f"heading_{level}",
                    f"heading_{level}": {
                        "rich_text": _parse_inline(stripped.lstrip("#").strip())
                    },
                }
            )
        else:
            blocks.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": _parse_inline(stripped)},
                }
            )
    return blocks


from langgraph.prebuilt import ToolRuntime

from src.graph.context import RetroContext


@tool
def create_or_update_entry(
    repo: str, date: str, report: str, runtime: ToolRuntime[RetroContext]
) -> str:
    """레포명, 날짜, 회고 내용을 받아 노션 데이터베이스에 새 페이지를 생성한다."""
    notion = get_notion_client(runtime.context["notion_api_key"])
    page = notion.pages.create(
        parent={"database_id": settings.NOTION_RETRO_DB_ID},
        properties={
            "날짜": {"title": [{"text": {"content": date}}]},
            "레포지토리": {"rich_text": [{"text": {"content": repo}}]},
        },
        children=_markdown_to_blocks(report),  # ← 여기만 바뀜
    )
    return page["url"]
