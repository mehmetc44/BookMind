"""Sohbet LangGraph pipeline'ının durumu (State)."""

from __future__ import annotations

from typing import TypedDict


class ChatGraphState(TypedDict):
    """Sohbet Graph'ının durumu.

    Attributes:
        user_message: Kullanıcının attığı sohbet mesajı.
        response:     ChatAgent'ın ürettiği yanıt metni.
    """

    user_message: str
    response: str
