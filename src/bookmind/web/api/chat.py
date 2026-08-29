"""web.api.chat — API routes for chat interaction with AI models."""

from __future__ import annotations

from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from bookmind.ai.agents import ChatAgent
from bookmind.application.qa.ask_book import AskBookQueryHandler
from bookmind.web.dtos.chat import ChatMessage, ChatResponse

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatMessage) -> ChatResponse:
    """Sohbet asistanına mesaj gönderir (Agentic RAG senkron yanıt)."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    agent = ChatAgent()
    try:
        reply = await agent.run_agentic(
            user_message=body.message,
            book_id=body.book_id,
            history=body.history,
        )
        return ChatResponse(success=True, reply=reply)
    except Exception as e:
        return ChatResponse(success=False, error=str(e))


@router.post("/chat/stream")
async def chat_stream(body: ChatMessage) -> StreamingResponse:
    """Sohbet asistanına mesaj gönderir (canlı streaming yanıt)."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    async def event_generator() -> AsyncGenerator[str, None]:
        async for chunk in AskBookQueryHandler.handle_stream(
            message=body.message,
            book_id=body.book_id,
            history=body.history,
        ):
            yield chunk

    return StreamingResponse(event_generator(), media_type="text/plain; charset=utf-8")


@router.post("/chat/test-rag")
async def test_rag_endpoint(body: ChatMessage) -> dict:
    """RAG sistemini test etmek için: LLM çağrısı olmadan sadece Vektör Başlık seçimi, Re-Rank ve 3-chunk bağlamını anında döndürür."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    from bookmind.ai.rag import RAGService

    # Sadece Hiyerarşik RAG Arama (0 LLM çağrısı, anında yanıt)
    rag_result = RAGService.retrieve_hierarchical_context(
        query=body.message,
        book_id=body.book_id,
    )

    return {
        "success": True,
        "query": body.message,
        "book_id": body.book_id,
        "selected_title": rag_result.get("selected_title"),
        "target_chunk_id": rag_result.get("target_chunk_id"),
        "expanded_text": rag_result.get("expanded_text"),
        "rag_context": rag_result.get("rag_context"),
    }
