"""BookMind.Shared.schemas.book — Kitap domain şemaları."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chapter(BaseModel):
    """Bir kitap bölümünü temsil eder. Recursive olarak alt bölümler içerebilir."""

    id: str = Field(..., description="Benzersiz bölüm kimliği — ör: chapter_1_2")
    title: str = Field(..., description="Bölüm başlığı")
    page_start: int = Field(..., description="Başlangıç sayfa numarası")
    page_end: int = Field(..., description="Bitiş sayfa numarası")
    summary: str = Field(default="", description="Türkçe bölüm özeti")
    topics: list[str] = Field(default_factory=list, description="Bölümün ana konuları")
    keywords: list[str] = Field(default_factory=list, description="Teknik/İngilizce anahtar kelimeler")
    children: list[Chapter] = Field(default_factory=list, description="Alt bölümler (recursive)")


class BookMap(BaseModel):
    """Bir kitabın tüm yapısal haritası."""

    book_title: str = Field(..., description="Kitabın tam başlığı")
    author: str = Field(default="Bilinmiyor", description="Yazar adı")
    total_pages: int = Field(..., description="Toplam sayfa sayısı")
    chapters: list[Chapter] = Field(default_factory=list, description="Ana bölümler")


class BookInfo(BaseModel):
    """Kitap listesi API'si için özet bilgi (harita detayları olmadan)."""

    id: str = Field(..., description="Kitap kimliği (UUID hex)")
    filename: str = Field(..., description="Orijinal PDF dosya adı")
    title: str = Field(..., description="Kitap başlığı")
    author: str = Field(..., description="Yazar")
    total_pages: int = Field(..., description="Toplam sayfa sayısı")
    chapter_count: int = Field(..., description="Ana bölüm sayısı")
    created_at: str = Field(..., description="ISO 8601 yükleme zamanı")
