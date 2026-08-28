"""workflows.qa.graph — QA LangGraph workflow definition and streaming utility."""

from __future__ import annotations

from typing import Any, AsyncGenerator
from langgraph.graph import END, StateGraph

from bookmind.ai.generation.llm import ChatAgent
from bookmind.workflows.qa.nodes.generate_answer import chat_agent_node
from bookmind.workflows.qa.state import ChatGraphState


def build_chat_graph() -> StateGraph:
    """Sohbet LangGraph akışını derler ve döndürür."""
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
    """Sohbet mesajına canlı streaming yanıtı üretir."""
    chat_agent = ChatAgent()

    # Eğer kitap bağlamı varsa haritayı çekip extra_context olarak ekle
    extra_context = None
    if book_id:
        from bookmind.infrastructure.database.repositories.map_repository import MapRepository

        map_data = MapRepository.get_book_map(book_id)
        if map_data and "book_map" in map_data:
            extra_context = f"AKTİF KİTAP HARİTASI BILGILERI:\n{map_data['book_map']}"

    async for chunk in chat_agent.astream(
        user_message=user_message,
        history=history,
        extra_context=extra_context,
    ):
        if chunk:
            yield chunk
