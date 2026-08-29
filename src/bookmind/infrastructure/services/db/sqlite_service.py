"""infrastructure.services.db.sqlite_service — SQLite database service for storing text chunks, metadata, and linked neighbor relationships."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any

from bookmind.infrastructure.configuration.settings import Settings


class SQLiteService:
    """SQLite ilişkisel veritabanı yönetim servisi."""

    @classmethod
    def _get_connection(cls) -> sqlite3.Connection:
        """SQLite veritabanı bağlantısı döndürür ve storage klasörünü garantiye alır."""
        Settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(Settings.SQLITE_DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    @classmethod
    def init_db(cls) -> None:
        """Tabloları ve indeksleri oluşturur."""
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    book_id TEXT NOT NULL,
                    chapter_id TEXT,
                    page_start INTEGER NOT NULL,
                    page_end INTEGER NOT NULL,
                    prev_chunk_id TEXT,
                    next_chunk_id TEXT,
                    content TEXT NOT NULL,
                    word_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_book_id ON chunks (book_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_prev_id ON chunks (prev_chunk_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_chunks_next_id ON chunks (next_chunk_id)")
            conn.commit()

    @classmethod
    def save_chunks(cls, chunks: list[dict[str, Any]]) -> int:
        """Üretilen chunk listesini SQLite veritabanına toplu olarak yazar."""
        if not chunks:
            return 0

        cls.init_db()
        now_iso = datetime.now(timezone.utc).isoformat()

        with cls._get_connection() as conn:
            cursor = conn.cursor()
            records = []
            for c in chunks:
                records.append((
                    c["chunk_id"],
                    c["book_id"],
                    c.get("chapter_id"),
                    c.get("page_start", 1),
                    c.get("page_end", 1),
                    c.get("prev_chunk_id"),
                    c.get("next_chunk_id"),
                    c["content"],
                    len(c["content"].split()),
                    now_iso,
                ))

            cursor.executemany(
                """
                INSERT OR REPLACE INTO chunks (
                    chunk_id, book_id, chapter_id, page_start, page_end,
                    prev_chunk_id, next_chunk_id, content, word_count, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                records,
            )
            conn.commit()
            return len(records)

    @classmethod
    def get_chunk(cls, chunk_id: str) -> dict[str, Any] | None:
        """Tek bir chunk verisini getirir."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chunks WHERE chunk_id = ?", (chunk_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    @classmethod
    def get_chunks_by_chapter(cls, chapter_id: str, book_id: str | None = None) -> list[dict[str, Any]]:
        """Verilen chapter_id (ve isteğe bağlı book_id) altındaki tüm chunk'ları getirir."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            if book_id:
                cursor.execute(
                    "SELECT * FROM chunks WHERE chapter_id = ? AND book_id = ? ORDER BY page_start, chunk_id",
                    (chapter_id, book_id),
                )
            else:
                cursor.execute(
                    "SELECT * FROM chunks WHERE chapter_id = ? ORDER BY page_start, chunk_id",
                    (chapter_id,),
                )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    @classmethod
    def get_all_book_chunks(cls, book_id: str) -> list[dict[str, Any]]:
        """Bir kitaba ait tüm chunk'ları getirir."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chunks WHERE book_id = ? ORDER BY page_start, chunk_id",
                (book_id,),
            )
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    @classmethod
    def get_expanded_context(cls, target_chunk_id: str) -> dict[str, Any]:
        """Hedef chunk_id'yi bulur ve komşuları (Önceki + Hedef + Sonraki) birleştirerek genişletilmiş anlamsal metni döndürür."""
        target_chunk = cls.get_chunk(target_chunk_id)
        if not target_chunk:
            return {"expanded_text": "", "page_start": 1, "page_end": 1, "chunks_used": []}

        prev_id = target_chunk.get("prev_chunk_id")
        next_id = target_chunk.get("next_chunk_id")

        prev_chunk = cls.get_chunk(prev_id) if prev_id else None
        next_chunk = cls.get_chunk(next_id) if next_id else None

        parts: list[str] = []
        chunks_used: list[str] = []

        if prev_chunk:
            parts.append(f"--- [Önceki Metin - Sayfa {prev_chunk['page_start']}] ---\n{prev_chunk['content']}")
            chunks_used.append(prev_chunk["chunk_id"])

        parts.append(f"--- [Hedef İlgili Bölüm - Sayfa {target_chunk['page_start']}] ---\n{target_chunk['content']}")
        chunks_used.append(target_chunk["chunk_id"])

        if next_chunk:
            parts.append(f"--- [Sonraki Devam Metni - Sayfa {next_chunk['page_start']}] ---\n{next_chunk['content']}")
            chunks_used.append(next_chunk["chunk_id"])

        expanded_text = "\n\n".join(parts)
        page_start = prev_chunk["page_start"] if prev_chunk else target_chunk["page_start"]
        page_end = next_chunk["page_end"] if next_chunk else target_chunk["page_end"]

        return {
            "target_chunk_id": target_chunk_id,
            "expanded_text": expanded_text,
            "page_start": page_start,
            "page_end": page_end,
            "chunks_used": chunks_used,
        }

    @classmethod
    def delete_book_chunks(cls, book_id: str) -> int:
        """Bir kitaba ait tüm chunk kayıtlarını siler."""
        cls.init_db()
        with cls._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chunks WHERE book_id = ?", (book_id,))
            deleted_count = cursor.rowcount
            conn.commit()
            return deleted_count
