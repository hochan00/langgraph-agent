from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.graph.context import DevlogContext
from src.graph.nodes.agent import agent, route_agent_result, tools
from src.graph.nodes.collect import collect_activity, route_after_collect
from src.graph.state import AgentState

graph_builder = StateGraph(AgentState, context_schema=DevlogContext)

graph_builder.add_node("collect_activity", collect_activity)
graph_builder.add_node("agent", agent)
graph_builder.add_node("tools", ToolNode(tools))

graph_builder.add_edge(START, "collect_activity")
graph_builder.add_conditional_edges(
    "collect_activity",
    route_after_collect,
    {"has_activity": "agent", "no_activity": END},
)
graph_builder.add_conditional_edges(
    "agent",
    route_agent_result,
    {"continue": "tools", "done": END},
)
graph_builder.add_edge("tools", "agent")

graph = graph_builder.compile()
