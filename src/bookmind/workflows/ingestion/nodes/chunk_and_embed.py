"""workflows.ingestion.nodes.chunk_and_embed — 5. Düğüm: Chunking, Embedding (e5-base), SQLite & ChromaDB Kaydı."""

from __future__ import annotations

import hashlib
from pathlib import Path
from datetime import datetime, timezone

from bookmind.ai import Embedder
from bookmind.ai.services import ChunkingService
from bookmind.infrastructure.services import PDFFileService, SQLiteService, VectorService
from bookmind.workflows.ingestion.state import PDFGraphState


async def chunk_and_embed_node(state: PDFGraphState) -> PDFGraphState:
    """PDF hiyerarşisindeki metinleri 250 kelimelik bağlı chunk'lara böler, SQLite, ChromaDB ve maps JSON dosyasına kaydeder."""
    pdf_path = state["pdf_path"]
    book_map = state.get("book_map") or {}

    # PDF dosya yolundan tutarlı book_id üret
    book_id = hashlib.md5(Path(pdf_path).name.encode("utf-8")).hexdigest()[:12]

    try:
        print(f"📦 [5. Chunk & Embed] '{pdf_path}' metinleri 250 kelimelik parçalara ayrıştırılıyor...")

        # 1. Metin Çıkarımı ve 250 Kelimelik Chunking
        updated_book_map, flat_chunks = ChunkingService.process_book_chunks(
            pdf_path=pdf_path,
            book_id=book_id,
            book_map=book_map,
        )

        if flat_chunks:
            # 2. SQLite Veritabanına Chunk'ları ve Komşuluk Bağlarını Kaydet
            print(f"🗃️ [5. Chunk & Embed] {len(flat_chunks)} chunk SQLite (bookmind.db) veritabanına yazılıyor...")
            SQLiteService.save_chunks(flat_chunks)

            # 3. ChromaDB Vektör Veritabanına Vektörleri ve Metadataları Kaydet
            print(f"🧬 [5. Chunk & Embed] {len(flat_chunks)} chunk ChromaDB (multilingual-e5-base) vektör veritabanına indeksleniyor...")
            VectorService.add_chunks(flat_chunks)
        else:
            print("  ⚠️ Uyarı: Bölümlerden metin çıkarılamadı veya chunk üretilemedi.")

        # 4. Güncellenmiş Hiyerarşik BookMap (Chunk'lar eklenmiş halde) maps/{book_id}.json olarak diske kaydet
        map_data = {
            "meta": {
                "id": book_id,
                "filename": Path(pdf_path).name,
                "pdf_path": pdf_path,
                "created_at": datetime.now(timezone.utc).isoformat(),
            },
            "book_map": updated_book_map,
        }

        print(f"💾 [5. Chunk & Embed] Güncellenmiş hiyerarşi maps/{book_id}.json olarak kaydediliyor...")
        PDFFileService.save_book_map(book_id, map_data)

        return {
            **state,
            "book_map": updated_book_map,
        }

    except Exception as e:
        print(f"❌ [5. Chunk & Embed] Hata oluştu: {e!s}")
        return {
            **state,
            "error": f"Chunking ve embedding işlemi sırasında hata oluştu: {e!s}",
        }
