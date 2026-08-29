"""ai.tools.rag_tool — LangChain tool wrapper for RAG retrieval."""

from __future__ import annotations

from langchain_core.tools import tool

from bookmind.ai.rag import RAGService


@tool("search_book_context")
def search_book_context(query: str, book_id: str | None = None) -> str:
    """
    Kitap içerisinden verilen sorguya göre en alakalı hiyerarşik bölümü, Cross-Encoder re-rank sonucunu ve birleştirilmiş 3 komşu chunk (Önceki + Hedef + Sonraki) metnini getirir.

    Args:
        query: Kitap içerisinde aranmak istenen özel konu, terim, kavram veya soru.
        book_id: İsteğe bağlı kitap ID'si. Belirtilmezse tüm indeksli kitaplarda arar.
    """
    result = RAGService.retrieve_hierarchical_context(
        query=query,
        book_id=book_id,
    )
    rag_context = result.get("rag_context")
    if not rag_context:
        return "İlgili hiyerarşik başlık veya metin bulunamadı."
    return rag_context
