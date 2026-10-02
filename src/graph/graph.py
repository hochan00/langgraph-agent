from langgraph.graph import END, START, StateGraph

from src.graph.context import DevlogContext
from src.graph.nodes.collect import collect_activity, route_after_collect
from src.graph.state import AgentState

graph_builder = StateGraph(AgentState, context_schema=DevlogContext)

graph_builder.add_node("collect_activity", collect_activity)

graph_builder.add_edge(START, "collect_activity")
graph_builder.add_conditional_edges(
    "collect_activity",
    route_after_collect,
    {"has_activity": END, "no_activity": END},
)

graph = graph_builder.compile()
