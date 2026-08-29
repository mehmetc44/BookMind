"""workflows.qa.graph — QA LangGraph workflow definition and streaming utility with RAG integration."""

from __future__ import annotations

from typing import AsyncGenerator
from langgraph.graph import END, StateGraph

from bookmind.ai.agents import ChatAgent
from bookmind.ai.rag import RAGService
from bookmind.workflows.qa.nodes.generate_answer import chat_agent_node
from bookmind.workflows.qa.nodes.rag_retrieval import rag_retrieval_node
from bookmind.workflows.qa.state import ChatGraphState


def build_chat_graph():
    """Sohbet LangGraph akışını derler ve döndürür (rag_retrieval_node -> chat_agent_node -> END)."""
    workflow = StateGraph(ChatGraphState)

    workflow.add_node("rag_retrieval_node", rag_retrieval_node)
    workflow.add_node("chat_agent_node", chat_agent_node)

    workflow.set_entry_point("rag_retrieval_node")
    workflow.add_edge("rag_retrieval_node", "chat_agent_node")
    workflow.add_edge("chat_agent_node", END)

    return workflow.compile()


async def stream_chat_graph(
    user_message: str,
    book_id: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> AsyncGenerator[str, None]:
    """Sohbet mesajı geldiğinde direkt RAG servisine yollar ve ChatAgent'tan canlı streaming yanıt üretir."""
    # 1. RAG Hizmetinden Vektör Benzerliği Başlık Seçimi + Rerank + 3-Chunk Bağlamı Getir
    rag_result = RAGService.retrieve_hierarchical_context(
        query=user_message,
        book_id=book_id,
    )
    rag_context = rag_result.get("rag_context")

    # 2. ChatAgent ile canlı akış (streaming) cevabı üret
    chat_agent = ChatAgent()

    async for chunk in chat_agent.astream(
        user_message=user_message,
        history=history,
        extra_context=rag_context,
    ):
        if chunk:
            yield chunk
