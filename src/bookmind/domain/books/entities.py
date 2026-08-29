"""domain.books.entities — Book domain entities, clean hierarchy objects, and chunk items."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChunkItem(BaseModel):
    """250 kelimelik bağlantılı metin parçası (Chunk)."""

    chunk_id: str = Field(..., description="Benzersiz chunk ID — ör: chunk_a621_001")
    prev_chunk_id: str | None = Field(default=None, description="Bir önceki komşu chunk ID'si")
    next_chunk_id: str | None = Field(default=None, description="Bir sonraki komşu chunk ID'si")
    page_start: int = Field(..., description="Chunk'ın başladığı sayfa")
    page_end: int = Field(..., description="Chunk'ın bittiği sayfa")
    content: str = Field(..., description="250 kelimelik metin içeriği")
    word_count: int = Field(..., description="Kelime sayısı")


class Chapter(BaseModel):
    """Bir kitap bölümünü temsil eder. Yalın hiyerarşik yapı (summary/topics kaldırıldı)."""

    id: str = Field(..., description="Benzersiz bölüm kimliği — ör: chapter_1")
    title: str = Field(..., description="Bölüm başlığı")
    page_start: int = Field(..., description="Başlangıç sayfa numarası")
    page_end: int = Field(..., description="Bitiş sayfa numarası")
    chunks: list[ChunkItem] = Field(default_factory=list, description="Bölüme ait 250 kelimelik parçalar")
    children: list[Chapter] = Field(default_factory=list, description="Alt bölümler (recursive)")


class BookMap(BaseModel):
    """Bir kitabın tüm yapısal haritası."""

    book_title: str = Field(..., description="Kitabın tam başlığı")
    author: str = Field(default="Bilinmiyor", description="Yazar adı")
    total_pages: int = Field(..., description="Toplam sayfa sayısı")
    chapters: list[Chapter] = Field(default_factory=list, description="Ana bölümler")


class BookInfo(BaseModel):
    """Kitap listesi API'si için özet bilgi."""

    id: str = Field(..., description="Kitap kimliği (UUID hex)")
    filename: str = Field(..., description="Orijinal PDF dosya adı")
    title: str = Field(..., description="Kitap başlığı")
    author: str = Field(..., description="Yazar")
    total_pages: int = Field(..., description="Toplam sayfa sayısı")
    chapter_count: int = Field(..., description="Ana bölüm sayısı")
    created_at: str = Field(..., description="ISO 8601 yükleme zamanı")
