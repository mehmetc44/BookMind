"""application.books.commands.delete_book — Command handler to delete a book and its structural map."""

from __future__ import annotations

import json
from pathlib import Path
from fastapi import HTTPException

from bookmind.infrastructure.configuration.settings import Settings


class DeleteBookCommandHandler:
    """Kitabı ve üretilen haritasını silen komut işleyici."""

    @classmethod
    def handle(cls, book_id: str) -> dict[str, str]:
        """PDF dosyasını ve JSON harita kaydını diskten kaldırır."""
        map_path = Settings.MAPS_DIR / f"{book_id}.json"
        if not map_path.exists():
            raise HTTPException(status_code=404, detail="Kitap bulunamadı.")

        try:
            data = json.loads(map_path.read_text(encoding="utf-8"))
            pdf_path = Path(data.get("meta", {}).get("pdf_path", ""))
            if pdf_path.exists():
                pdf_path.unlink()
        except (json.JSONDecodeError, KeyError):
            pass

        map_path.unlink()

        return {"success": "True", "message": "Kitap başarıyla silindi."}
