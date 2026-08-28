"""PDFExtractorService — PDF İçindekiler (TOC) ve Metin Çıkarım Servisi.

Clean Architecture mantığına göre 1. Kademe Hibrit İnceleme ve Çıkarım
iş mantığını kapsar.

Kademeler:
    1.1 Metadata Sidebar Bookmarks (PyMuPDF doc.get_toc())
    1.2 İç Sayfa Tıklanabilir Bağlantıları (Hyperlinks) & 3 Akıllı Filtre
    2.0 Metin Taraması (LLM Fallback hazırlığı)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any
import pymupdf


class PDFExtractorService:
    """PDF İçindekiler ve Metin Çıkarım Servisi."""

    EXCLUDE_PATTERNS = re.compile(
        r"^(bkz|bakınız|see|table|tablo|şekil|figure|fig\.|http|www|sayfa|page|ek\b)",
        re.IGNORECASE,
    )

    @classmethod
    def inspect_toc(cls, pdf_path: str | Path) -> dict[str, Any]:
        """PDF dosyasının 1. Kademe gömülü Bookmark ve Köprü yapısını inceler.

        Args:
            pdf_path: İncelenecek PDF dosyasının yolu.

        Returns:
            dict: {
                "total_pages": int,
                "has_toc": bool,
                "toc_count": int,
                "toc": [...],
                "message": str,
            }
        """
        doc = pymupdf.open(str(pdf_path))
        total_pages = len(doc)
        raw_toc = doc.get_toc()

        structured_toc = []

        # 1.1 Metadata Outline (Sidebar Bookmarks)
        if raw_toc and len(raw_toc) > 0:
            for item in raw_toc:
                level = item[0] if len(item) > 0 else 1
                title = str(item[1]).strip() if len(item) > 1 else "Bölüm"
                page_num = item[2] if len(item) > 2 and isinstance(item[2], int) else 1
                structured_toc.append({
                    "level": level,
                    "title": title,
                    "page": max(1, page_num),
                    "source": "bookmark",
                })

        # 1.2 İç Sayfa Bağlantıları (Internal Hyperlinks / Annotations) & 3 Akıllı Filtre
        if not structured_toc:
            candidates = []
            last_page = 0

            # Filtre 1: Konum İzolasyonu (İlk 5 Sayfa)
            for i in range(min(5, total_pages)):
                page = doc[i]
                links = page.get_links()
                for l in links:
                    if l.get("kind") in (pymupdf.LINK_GOTO, 4) and "page" in l and l["page"] >= 0:
                        target_page = l["page"] + 1
                        rect = l.get("from")
                        if rect:
                            text = page.get_text("text", clip=rect).strip().replace("\n", " ")

                            # Filtre 2: Çapraz Referans Metin Filtresi
                            if not text or len(text) < 3 or cls.EXCLUDE_PATTERNS.search(text):
                                continue

                            if text.isdigit():
                                continue

                            # Filtre 3: Monotonik (Sıralı Artan Sayfa) Kontrolü
                            if target_page >= last_page:
                                candidates.append({
                                    "level": 1,
                                    "title": text,
                                    "page": target_page,
                                    "source": "link",
                                })
                                last_page = target_page

            structured_toc = candidates

        if structured_toc:
            source_type = structured_toc[0].get("source", "bookmark")
            source_msg = "Gömülü Sidebar Bookmark" if source_type == "bookmark" else "İç Sayfa Bağlantısı (Hyperlink)"
            doc.close()
            return {
                "total_pages": total_pages,
                "has_toc": True,
                "toc_count": len(structured_toc),
                "toc": structured_toc,
                "message": f"1. Kademe [{source_msg}] başarıyla tespit edildi! Toplam {len(structured_toc)} bölüm başlığı okundu.",
            }

        # Fallback preview if no TOC
        preview_pages = []
        for i in range(min(3, total_pages)):
            text = doc[i].get_text().strip()
            preview_pages.append({
                "page_num": i + 1,
                "text": text[:500] if text else "[Boş veya Görsel Sayfa]",
            })

        doc.close()
        return {
            "total_pages": total_pages,
            "has_toc": False,
            "toc_count": 0,
            "toc": [],
            "preview_pages": preview_pages,
            "message": "Bu PDF dosyasında yerleşik (gömülü) Bookmark / İçindekiler tablosu bulunamadı. (Sistem Kademe 2: Metin/LLM taramasına geçecek).",
        }
