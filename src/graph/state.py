from langgraph.graph import MessagesState

from src.schemas.activity_schema import Activity, DailyActivity


class AgentState(MessagesState):
    date: str  # YYYY-MM-DD (TIMEZONE 기준)
    activity: Activity
    daily_activity: DailyActivity
