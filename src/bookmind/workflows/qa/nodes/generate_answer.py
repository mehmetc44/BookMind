"""workflows.qa.nodes.generate_answer — Node for invoking LLM via ChatAgent to answer questions."""

from __future__ import annotations

from typing import Any
from bookmind.ai.agents import ChatAgent
from bookmind.workflows.qa.state import ChatGraphState


async def chat_agent_node(state: ChatGraphState) -> dict[str, Any]:
    """Sohbet asistanını çalıştıran ve RAG bağlamı ile yanıt üreten LangGraph düğümü."""
    chat_agent = ChatAgent()
    rag_context = state.get("rag_context")
    history = state.get("history")

    reply = await chat_agent.ainvoke(
        user_message=state["user_message"],
        history=history,
        extra_context=rag_context,
    )
    return {"response": reply}
