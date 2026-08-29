"""workflows.qa.nodes.generate_answer — Node for invoking LLM via ChatAgent to answer questions."""

from __future__ import annotations

from typing import Any
from bookmind.ai.agents import ChatAgent
from bookmind.workflows.qa.state import ChatGraphState


async def chat_agent_node(state: ChatGraphState) -> dict[str, Any]:
    """Agentic RAG sohbet asistanını çalıştıran LangGraph düğümü."""
    chat_agent = ChatAgent()
    reply = await chat_agent.run_agentic(
        user_message=state["user_message"],
        book_id=state.get("book_id"),
        history=state.get("history"),
    )
    return {"response": reply}
