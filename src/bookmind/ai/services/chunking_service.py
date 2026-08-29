"""ai.services.chunking_service — Service for extracting section texts from PDF and creating 250-word linked chunks."""

from __future__ import annotations

import re
from typing import Any
import fitz  # PyMuPDF


class ChunkingService:
    """PDF hiyerarşisindeki yaprak bölümlerden metinleri çeken ve 250 kelimelik bağlı chunk'lara bölen servis."""

    @classmethod
    def extract_text_range(cls, pdf_path: str, page_start: int, page_end: int) -> str:
        """Verilen sayfa aralığındaki (1-indexed) tüm ham metinleri okur."""
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        start_idx = max(0, page_start - 1)
        end_idx = min(total_pages, max(page_start, page_end))

        text_parts: list[str] = []
        for page_num in range(start_idx, end_idx):
            page_text = doc[page_num].get_text("text").strip()
            if page_text:
                text_parts.append(page_text)

        doc.close()
        return "\n\n".join(text_parts)

    @classmethod
    def split_into_chunks(cls, text: str, max_words: int = 250) -> list[str]:
        """Metni yaklaşık 250 kelimelik anlam bütünlüğü bozulmamış parçalara (chunks) böler."""
        clean_text = re.sub(r"\s+", " ", text).strip()
        if not clean_text:
            return []

        words = clean_text.split()
        if len(words) <= max_words:
            return [clean_text]

        chunks: list[str] = []
        current_chunk_words: list[str] = []

        # Cümle bazlı bölme için nokta/soru/ünlem ile ayır
        sentences = re.split(r"(?<=[.!?])\s+", clean_text)

        for sentence in sentences:
            sentence_words = sentence.split()
            if not sentence_words:
                continue

            if len(current_chunk_words) + len(sentence_words) <= max_words:
                current_chunk_words.extend(sentence_words)
            else:
                if current_chunk_words:
                    chunks.append(" ".join(current_chunk_words))
                    current_chunk_words = []
                # Eğer tek bir cümle bile 250 kelimeden uzunsa zorunlu böl
                if len(sentence_words) > max_words:
                    for i in range(0, len(sentence_words), max_words):
                        chunks.append(" ".join(sentence_words[i:i + max_words]))
                else:
                    current_chunk_words.extend(sentence_words)

        if current_chunk_words:
            chunks.append(" ".join(current_chunk_words))

        return chunks

    @classmethod
    def process_book_chunks(
        cls,
        pdf_path: str,
        book_id: str,
        book_map: dict[str, Any],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Kitabın hiyerarşik haritasındaki tüm yaprak bölümleri tarar, 250 kelimelik bağlı chunk'lar üretir."""
        flat_chunks: list[dict[str, Any]] = []

        # 1. Hiyerarşideki tüm yaprak (leaf) bölümleri topla
        def collect_leaf_chapters(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
            leaves = []
            for ch in chapters:
                children = ch.get("children") or []
                if not children:
                    leaves.append(ch)
                else:
                    leaves.extend(collect_leaf_chapters(children))
            return leaves

        chapters = book_map.get("chapters", [])
        leaf_chapters = collect_leaf_chapters(chapters)

        global_chunk_idx = 1
        book_id_prefix = book_id[:8]

        # 2. Her yaprak bölüm için metni çek ve chunk'lara böl
        for ch in leaf_chapters:
            page_start = ch.get("page_start", 1)
            page_end = ch.get("page_end", page_start)
            chapter_id = ch.get("id", "chap")

            section_text = cls.extract_text_range(pdf_path, page_start, page_end)
            raw_chunks = cls.split_into_chunks(section_text, max_words=250)

            ch_chunk_objs: list[dict[str, Any]] = []

            for text_chunk in raw_chunks:
                chunk_id = f"chk_{book_id_prefix}_{global_chunk_idx:04d}"
                chunk_obj = {
                    "chunk_id": chunk_id,
                    "book_id": book_id,
                    "chapter_id": chapter_id,
                    "page_start": page_start,
                    "page_end": page_end,
                    "prev_chunk_id": None,
                    "next_chunk_id": None,
                    "content": text_chunk,
                    "word_count": len(text_chunk.split()),
                }
                flat_chunks.append(chunk_obj)
                ch_chunk_objs.append(chunk_obj)
                global_chunk_idx += 1

            # Chapter nesnesinin altına chunks dizisini ekle
            ch["chunks"] = ch_chunk_objs

        # 3. Tüm kitabın chunk'ları arasında iki yönlü bağlı liste (linked list) bağlarını kur
        for i, c in enumerate(flat_chunks):
            if i > 0:
                c["prev_chunk_id"] = flat_chunks[i - 1]["chunk_id"]
            if i < len(flat_chunks) - 1:
                c["next_chunk_id"] = flat_chunks[i + 1]["chunk_id"]

        print(f"✂️ [ChunkingService] Toplam {len(leaf_chapters)} bölümden {len(flat_chunks)} adet 250 kelimelik bağlı chunk üretildi!")
        return book_map, flat_chunks
