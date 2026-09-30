from langgraph.graph import MessagesState

from src.schemas.activity_schema import Activity


class AgentState(MessagesState):
    date: str  # YYYY-MM-DD (TIMEZONE 기준)
    activity: Activity
