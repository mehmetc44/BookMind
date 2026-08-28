"""workflows.qa.state — QA / chat workflow state."""

from __future__ import annotations

from typing import TypedDict


class ChatGraphState(TypedDict):
    """Sohbet akış durum nesnesi."""

    user_message: str
    response: str
