"""web.api.chat — API routes for chat interaction with AI models."""

from __future__ import annotations

from typing import AsyncGenerator
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from bookmind.ai.agents import ChatAgent
from bookmind.application.qa.ask_book import AskBookQueryHandler
from bookmind.web.schemas.chat import ChatMessage, ChatResponse

router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatMessage) -> ChatResponse:
    """Sohbet asistanına mesaj gönderir (senkron yanıt)."""
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    # Eğer kitap bağlamı varsa haritayı çekip extra_context olarak ekle
    extra_context = None
    if body.book_id:
        from bookmind.infrastructure.services import PDFFileService

        map_data = PDFFileService.get_book_map(body.book_id)
        if map_data and "book_map" in map_data:
            extra_context = f"AKTİF KİTAP HARİTASI BILGILERI:\n{map_data['book_map']}"

    agent = ChatAgent()
    try:
        reply = agent.invoke(
            user_message=body.message,
            history=body.history,
            extra_context=extra_context,
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
