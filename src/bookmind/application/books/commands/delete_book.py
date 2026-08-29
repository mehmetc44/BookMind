"""application.books.commands.delete_book — Command handler to delete a book and its structural map."""

from __future__ import annotations

from fastapi import HTTPException

from bookmind.infrastructure.services import PDFFileService


class DeleteBookCommandHandler:
    """Kitabı ve üretilen haritasını silen komut işleyici."""

    @classmethod
    def handle(cls, book_id: str) -> dict[str, str]:
        """PDF dosyasını ve JSON harita kaydını diskten kaldırır."""
        deleted = PDFFileService.delete_book(book_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Kitap bulunamadı.")

        return {"success": "True", "message": "Kitap başarıyla silindi."}
