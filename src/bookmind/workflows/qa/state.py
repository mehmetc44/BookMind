"""workflows.qa.state — QA / chat workflow state."""

from __future__ import annotations

from typing import TypedDict


class ChatGraphState(TypedDict):
    """Sohbet akış durum nesnesi."""

    user_message: str
    book_id: str | None
    history: list[dict[str, str]] | None
    rag_context: str | None
    selected_title: str | None
    response: str
