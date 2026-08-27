"""Sohbet LangGraph pipeline'ı."""

from __future__ import annotations

from typing import AsyncGenerator
from langgraph.graph import END, START, StateGraph

from bookmind.agents import get_chat_agent
from bookmind.graph.chat.nodes import chat_agent_node
from bookmind.graph.chat.state import ChatGraphState


def build_chat_graph() -> StateGraph:
    """Sohbet LangGraph pipeline'ını derler ve döndürür."""
    workflow = StateGraph(ChatGraphState)

    workflow.add_node("chat_agent_node", chat_agent_node)
    workflow.set_entry_point("chat_agent_node")
    workflow.add_edge("chat_agent_node", END)

    return workflow.compile()


async def stream_chat_graph(user_message: str) -> AsyncGenerator[str, None]:
    """Sohbet mesajına 1.0s canlı streaming yanıt üretir."""
    chat_agent = get_chat_agent()
    async for chunk in chat_agent.ask_stream(user_message):
        if chunk:
            yield chunk
