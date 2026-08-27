"""Sohbet LangGraph node'ları."""

from __future__ import annotations

from typing import Any
from bookmind.agents import get_chat_agent
from bookmind.graph.chat.state import ChatGraphState


async def chat_agent_node(state: ChatGraphState) -> dict[str, Any]:
    """Sohbet mesajını alan ve ChatAgent'ı çağıran LangGraph node'u."""
    chat_agent = get_chat_agent()
    reply = await chat_agent.ask(state["user_message"])
    return {"response": reply}
