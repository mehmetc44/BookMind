"""ai.rag.rag_service — Hierarchical RAG Service for query title selection, reranking, and 3-chunk context expansion."""

from __future__ import annotations

from typing import Any

from bookmind.ai.rag.cross_encoder import CrossEncoder
from bookmind.infrastructure.services import PDFFileService, SQLiteService, VectorService


class RAGService:
    """Hiyerarşik vektör araması, Cross-Encoder re-ranking ve komşu chunk birleştirme sunan RAG servis sınıfı."""

    @classmethod
    def retrieve_hierarchical_context(
        cls,
        query: str,
        book_id: str | None = None,
    ) -> dict[str, Any]:
        """
        1. Vektör benzerliği ile en yakın hiyerarşik başlığı seçer.
        2. O başlık altındaki chunk'ları çeker.
        3. Cross-Encoder ile en alakalı chunk'ı re-rank edip belirler.
        4. O chunk'ın bir öncesi, kendisi ve bir sonrasını birleştirerek döndürür.
        """
        if not query.strip():
            return {
                "selected_title": None,
                "target_chunk_id": None,
                "expanded_text": "",
                "rag_context": "",
            }

        # 1. ADIM: Sorgu için ilk Vektör Benzerliği ile Hiyerarşik Başlık Seçimi
        title_match = VectorService.search_similar_title(query=query, book_id=book_id)

        # Eğer ChromaDB'de başlık bulunamadıysa ve book_id varsa, haritayı yükleyip indekslemeyi dene
        if not title_match and book_id:
            map_data = PDFFileService.get_book_map(book_id)
            if map_data and "book_map" in map_data:
                chapters = map_data["book_map"].get("chapters", [])
                def collect_chapters(ch_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
                    res = []
                    for c in ch_list:
                        res.append(c)
                        if c.get("children"):
                            res.extend(collect_chapters(c["children"]))
                    return res

                all_ch = collect_chapters(chapters)
                if all_ch:
                    VectorService.add_titles(book_id=book_id, titles=all_ch)
                    title_match = VectorService.search_similar_title(query=query, book_id=book_id)

        selected_chapter_id = title_match.get("chapter_id") if title_match else None
        selected_title_name = title_match.get("title") if title_match else "Genel İçerik"

        # 2. ADIM: Seçilen Başlık Altındaki Chunk'ları Getir
        candidate_chunks: list[dict[str, Any]] = []
        if selected_chapter_id:
            candidate_chunks = SQLiteService.get_chunks_by_chapter(
                chapter_id=selected_chapter_id,
                book_id=book_id,
            )

        # Eğer o başlığa ait chunk SQLite'ta doğrudan çıkmadıysa (ör. tek üst başlık), kitaba ait tüm chunk'lara bak
        if not candidate_chunks and book_id:
            candidate_chunks = SQLiteService.get_all_book_chunks(book_id)

        # Eğer hala aday yoksa ChromaDB benzerlik aramasından ilk chunk'ı al
        if not candidate_chunks:
            chroma_matches = VectorService.search_similar_chunks(query=query, book_id=book_id, top_k=5)
            for cm in chroma_matches:
                chk = SQLiteService.get_chunk(cm["chunk_id"])
                if chk:
                    candidate_chunks.append(chk)

        if not candidate_chunks:
            return {
                "selected_title": selected_title_name,
                "target_chunk_id": None,
                "expanded_text": "",
                "rag_context": "",
            }

        # 3. ADIM: Aday Chunk'lar Arasında Cross-Encoder ile Re-Ranking
        print(f"🔍 [RAGService] '{selected_title_name}' başlığı altında {len(candidate_chunks)} aday chunk Cross-Encoder ile yeniden puanlanıyor...")
        ranked_chunks = CrossEncoder.rank(query=query, chunks=candidate_chunks, top_k=1)
        winning_chunk = ranked_chunks[0] if ranked_chunks else candidate_chunks[0]
        winning_chunk_id = winning_chunk["chunk_id"]

        # 4. ADIM: O Chunk'ı, Bir Öncesini ve Bir Sonrakini Birleştir (Expanded Context Window)
        expanded_data = SQLiteService.get_expanded_context(winning_chunk_id)
        expanded_text = expanded_data.get("expanded_text", "")

        rag_context = (
            f"=== HİYERARŞİK RAG BİLGİ SEÇİMİ ===\n"
            f"🎯 Seçilen Hiyerarşik Başlık: {selected_title_name} (ID: {selected_chapter_id or 'Bilinmiyor'})\n"
            f"📌 Re-Rank Skor En Yüksek Chunk: {winning_chunk_id}\n\n"
            f"--- BİRLEŞTİRİLMİŞ ÜÇLÜ BAĞLAM (ÖNCEKİ + HEDEF + SONRAKİ CHUNK) ---\n"
            f"{expanded_text}"
        )

        print(f"✅ [RAGService] Bağlam başarıyla oluşturuldu. Başlık: '{selected_title_name}', Target Chunk: {winning_chunk_id}")

        return {
            "selected_title": selected_title_name,
            "target_chunk_id": winning_chunk_id,
            "expanded_text": expanded_text,
            "rag_context": rag_context,
        }
