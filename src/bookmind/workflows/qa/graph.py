"""workflows.qa.graph — QA LangGraph workflow definition and streaming utility for Agentic RAG."""

from __future__ import annotations

from typing import AsyncGenerator
from langgraph.graph import END, StateGraph

from bookmind.ai.agents import ChatAgent
from bookmind.workflows.qa.nodes.generate_answer import chat_agent_node
from bookmind.workflows.qa.state import ChatGraphState


def build_chat_graph():
    """Agentic Sohbet LangGraph akışını derler ve döndürür (chat_agent_node -> END)."""
    workflow = StateGraph(ChatGraphState)

    workflow.add_node("chat_agent_node", chat_agent_node)

    workflow.set_entry_point("chat_agent_node")
    workflow.add_edge("chat_agent_node", END)

    return workflow.compile()


async def stream_chat_graph(
    user_message: str,
    book_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> AsyncGenerator[str, None]:
    """Sohbet mesajı geldiğinde Agentic RAG ile dinamik tool araması yaparak yanıt üretir."""
    chat_agent = ChatAgent()

    async for chunk in chat_agent.stream_agentic(
        user_message=user_message,
        book_id=book_id,
        history=history,
    ):
        if chunk:
            yield chunk
