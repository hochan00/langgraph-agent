from langgraph.graph import MessagesState

from src.schemas.retro_schema import RetroDraft


class AgentState(MessagesState):
    retro_draft: RetroDraft
    repo: str
    date: str
