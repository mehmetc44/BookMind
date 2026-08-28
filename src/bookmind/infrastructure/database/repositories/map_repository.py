"""infrastructure.database.repositories.map_repository — File system persistence repository implementing book storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bookmind.domain.books.entities import BookInfo
from bookmind.infrastructure.configuration.settings import Settings

MAPS_DIR = Settings.MAPS_DIR


class MapRepository:
    """Kitap haritası JSON dosyalarını okuyan ve yazan kalıcılık reposu."""

    @classmethod
    def list_books(cls) -> list[BookInfo]:
        """data/maps dizinindeki tüm kitap haritalarını listeler."""
        books: list[BookInfo] = []
        for map_file in sorted(MAPS_DIR.glob("*.json")):
            try:
                data = json.loads(map_file.read_text(encoding="utf-8"))
                meta = data.get("meta", {})
                book_map = data.get("book_map") or {}
                books.append(
                    BookInfo(
                        id=meta.get("id", map_file.stem),
                        filename=meta.get("filename", ""),
                        title=book_map.get("book_title", "Bilinmiyor"),
                        author=book_map.get("author", "Bilinmiyor"),
                        total_pages=book_map.get("total_pages", 0),
                        chapter_count=len(book_map.get("chapters", [])),
                        created_at=meta.get("created_at", ""),
                    )
                )
            except (json.JSONDecodeError, KeyError):
                continue
        return books

    @classmethod
    def get_book_map(cls, book_id: str) -> dict[str, Any] | None:
        """Belirtilen book_id'ye ait kitap haritası JSON içeriğini okur."""
        map_path = MAPS_DIR / f"{book_id}.json"
        if not map_path.exists():
            return None
        return json.loads(map_path.read_text(encoding="utf-8"))

    @classmethod
    def save_book_map(cls, book_id: str, map_data: dict[str, Any]) -> Path:
        """Kitap harita verisini data/maps/{book_id}.json olarak yazar."""
        MAPS_DIR.mkdir(parents=True, exist_ok=True)
        map_path = MAPS_DIR / f"{book_id}.json"
        map_path.write_text(json.dumps(map_data, ensure_ascii=False, indent=2), encoding="utf-8")
        return map_path
