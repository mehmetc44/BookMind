"""workflows.qa.nodes.rag_retrieval — LangGraph node for retrieving hierarchical RAG context."""

from __future__ import annotations

from typing import Any
from bookmind.ai.rag import RAGService
from bookmind.workflows.qa.state import ChatGraphState


async def rag_retrieval_node(state: ChatGraphState) -> dict[str, Any]:
    """Chat graphına sorgu geldiği anda RAG servisini çalıştırarak en alakalı başlık ve 3-chunk bağlamını çeker."""
    user_message = state["user_message"]
    book_id = state.get("book_id")

    print(f"🚀 [ChatGraph: RAG Node] Sorgu alındı: '{user_message}' (kitap: {book_id})")

    rag_result = RAGService.retrieve_hierarchical_context(
        query=user_message,
        book_id=book_id,
    )

    return {
        "rag_context": rag_result.get("rag_context") or "",
        "selected_title": rag_result.get("selected_title") or "",
    }
