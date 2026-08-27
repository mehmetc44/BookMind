"""BookMind veri modelleri - Kitap haritalama yapıları."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """Bir kitap bölümünü temsil eden model.

    Recursive yapıda alt bölümler (children) içerebilir.
    """

    id: str = Field(..., description="Bölüm kimliği, ör: chapter_1")
    title: str = Field(..., description="Bölüm başlığı")
    page_start: int = Field(..., description="Başlangıç sayfa numarası")
    page_end: int = Field(..., description="Bitiş sayfa numarası")
    summary: str = Field(default="", description="Bölüm özeti")
    topics: list[str] = Field(default_factory=list, description="Bölüm konuları")
    keywords: list[str] = Field(default_factory=list, description="Anahtar kelimeler")
    children: list[Chapter] = Field(
        default_factory=list, description="Alt bölümler"
    )


class BookMap(BaseModel):
    """Bir kitabın tam haritası."""

    book_title: str = Field(..., description="Kitap başlığı")
    author: str = Field(default="Bilinmiyor", description="Yazar")
    total_pages: int = Field(..., description="Toplam sayfa sayısı")
    chapters: list[Chapter] = Field(
        default_factory=list, description="Ana bölümler"
    )


class BookInfo(BaseModel):
    """API response için kitap bilgisi."""

    id: str
    filename: str
    title: str
    author: str
    total_pages: int
    chapter_count: int
    created_at: str
