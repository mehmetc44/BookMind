"""application.qa.ask_book — Query handler to ask questions and generate streaming response."""

from __future__ import annotations

from typing import AsyncGenerator
from bookmind.workflows.qa.graph import stream_chat_graph


class AskBookQueryHandler:
    """Kitaba soru sorup canlı akış (streaming) cevabı getiren sorgu işleyici."""

    @classmethod
    async def handle_stream(
        cls,
        message: str,
        book_id: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Sohbet akışını tetikler ve chunks üretir."""
        async for chunk in stream_chat_graph(
            user_message=message,
            book_id=book_id,
            history=history,
        ):
            yield chunk
