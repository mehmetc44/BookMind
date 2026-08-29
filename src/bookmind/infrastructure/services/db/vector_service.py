"""infrastructure.services.db.vector_service — ChromaDB vector database service for chunk embeddings and semantic search."""

from __future__ import annotations

from typing import Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from bookmind.infrastructure.configuration.settings import Settings


class VectorService:
    """ChromaDB gömülü vektör veritabanı yönetim servisi."""

    _client: chromadb.PersistentClient | None = None
    _collection: Any = None
    _titles_collection: Any = None

    @classmethod
    def get_client(cls) -> chromadb.PersistentClient:
        """ChromaDB PersistentClient instance'ı döndürür."""
        if cls._client is None:
            Settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
            cls._client = chromadb.PersistentClient(
                path=str(Settings.CHROMA_DIR),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        return cls._client

    @classmethod
    def get_collection(cls) -> Any:
        """'book_chunks' koleksiyonunu getirir veya oluşturur."""
        if cls._collection is None:
            client = cls.get_client()
            cls._collection = client.get_or_create_collection(
                name="book_chunks",
                metadata={"hnsw:space": "cosine"},
            )
        return cls._collection

    @classmethod
    def get_titles_collection(cls) -> Any:
        """'book_titles' hiyerarşik başlık koleksiyonunu getirir veya oluşturur."""
        if cls._titles_collection is None:
            client = cls.get_client()
            cls._titles_collection = client.get_or_create_collection(
                name="book_titles",
                metadata={"hnsw:space": "cosine"},
            )
        return cls._titles_collection

    @classmethod
    def add_titles(cls, book_id: str, titles: list[dict[str, Any]]) -> int:
        """Hiyerarşik bölüm başlıklarını ChromaDB 'book_titles' koleksiyonuna ekler."""
        if not titles:
            return 0

        collection = cls.get_titles_collection()

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for idx, t in enumerate(titles):
            chapter_id = t.get("id") or t.get("chapter_id") or f"ch_{idx}"
            title_text = t.get("title", "")
            summary = t.get("summary", "")
            topics = ", ".join(t.get("topics", [])) if isinstance(t.get("topics"), list) else ""

            doc_text = f"Başlık: {title_text}"
            if summary:
                doc_text += f"\nÖzet: {summary}"
            if topics:
                doc_text += f"\nKonular: {topics}"

            doc_id = f"{book_id}_{chapter_id}"
            ids.append(doc_id)
            documents.append(doc_text)
            metadatas.append({
                "book_id": book_id,
                "chapter_id": chapter_id,
                "title": title_text,
            })

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    @classmethod
    def search_similar_title(
        cls,
        query: str,
        book_id: str | None = None,
    ) -> dict[str, Any] | None:
        """Vektör benzerliği ile kullanıcının sorusuna en yakın hiyerarşik başlığı bulur."""
        collection = cls.get_titles_collection()
        where_clause = {"book_id": book_id} if book_id else None

        try:
            results = collection.query(
                query_texts=[query],
                n_results=1,
                where=where_clause,
            )

            if results and results.get("ids") and len(results["ids"]) > 0 and len(results["ids"][0]) > 0:
                chapter_id = results["metadatas"][0][0].get("chapter_id")
                title = results["metadatas"][0][0].get("title")
                doc = results["documents"][0][0] if results.get("documents") else ""
                dist = results["distances"][0][0] if results.get("distances") else 0.0

                return {
                    "chapter_id": chapter_id,
                    "title": title,
                    "document": doc,
                    "distance": dist,
                }
        except Exception as e:
            print(f"⚠️ [VectorService] Başlık arama hatası: {e}")

        return None

    @classmethod
    def add_chunks(cls, chunks: list[dict[str, Any]]) -> int:
        """Chunk'ları ChromaDB koleksiyonuna ekler."""
        if not chunks:
            return 0

        collection = cls.get_collection()

        ids: list[str] = []
        documents: list[str] = []
        metadatas: list[dict[str, Any]] = []

        for c in chunks:
            ids.append(c["chunk_id"])
            documents.append(c["content"])
            metadatas.append({
                "book_id": c["book_id"],
                "chapter_id": c.get("chapter_id") or "",
                "page_start": c.get("page_start", 1),
                "page_end": c.get("page_end", 1),
                "prev_chunk_id": c.get("prev_chunk_id") or "",
                "next_chunk_id": c.get("next_chunk_id") or "",
            })

        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        return len(ids)

    @classmethod
    def search_similar_chunks(
        cls,
        query: str,
        book_id: str | None = None,
        top_k: int = 1,
    ) -> list[dict[str, Any]]:
        """Kullanıcının sorusuna anlamsal olarak en yakın k adet chunk_id ve metadatasını bulur."""
        collection = cls.get_collection()

        where_clause = {"book_id": book_id} if book_id else None

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause,
        )

        matches: list[dict[str, Any]] = []
        if results and results.get("ids") and len(results["ids"]) > 0:
            match_ids = results["ids"][0]
            match_docs = results["documents"][0] if results.get("documents") else []
            match_meta = results["metadatas"][0] if results.get("metadatas") else []
            match_dist = results["distances"][0] if results.get("distances") else []

            for idx, chunk_id in enumerate(match_ids):
                matches.append({
                    "chunk_id": chunk_id,
                    "content": match_docs[idx] if idx < len(match_docs) else "",
                    "metadata": match_meta[idx] if idx < len(match_meta) else {},
                    "distance": match_dist[idx] if idx < len(match_dist) else 0.0,
                })

        return matches

    @classmethod
    def delete_book_vectors(cls, book_id: str) -> None:
        """Bir kitaba ait tüm vektörleri ChromaDB'den siler."""
        try:
            collection = cls.get_collection()
            collection.delete(where={"book_id": book_id})
        except Exception:
            pass
        try:
            titles_col = cls.get_titles_collection()
            titles_col.delete(where={"book_id": book_id})
        except Exception:
            pass
