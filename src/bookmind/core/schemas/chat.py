"""Chat işlemleriyle ilgili Pydantic şemaları."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat isteği şeması — frontend'den gelen payload."""

    book_id: str | None = Field(
        default=None,
        description="Bağlam olarak kullanılacak kitabın ID'si. None ise genel asistan modu.",
    )
    message: str = Field(..., description="Kullanıcının sorusu/mesajı")
    history: list[dict[str, str]] = Field(
        default_factory=list,
        description="Konuşma geçmişi [{role, content}, ...]. Şu an boş gönderiliyor.",
    )


class ChatResponse(BaseModel):
    """Chat yanıt şeması — API'den dönen payload."""

    success: bool = Field(..., description="İşlem başarılı mı?")
    reply: str = Field(default="", description="Modelin yanıt metni")
    error: str | None = Field(default=None, description="Hata mesajı (varsa)")
