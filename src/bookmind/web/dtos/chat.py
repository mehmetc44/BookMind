"""web.dtos.chat — Chat-specific API request/response validation DTOs."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat isteği DTO'su — frontend'den gelen payload."""

    book_id: str | None = Field(
        default=None,
        description="Bağlam olarak kullanılacak kitabın ID'si. None ise genel asistan modu.",
    )
    message: str = Field(..., description="Kullanıcının sorusu/mesajı")
    history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Konuşma geçmişi [{role, content}, ...].",
    )


class ChatResponse(BaseModel):
    """Chat yanıt DTO'su — API'den dönen payload."""

    success: bool = Field(..., description="İşlem başarılı mı?")
    reply: str = Field(default="", description="Modelin yanıt metni")
    error: str | None = Field(default=None, description="Hata mesajı (varsa)")
