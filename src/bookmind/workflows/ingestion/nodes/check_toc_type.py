"""workflows.ingestion.nodes.check_toc_type — 2. Düğüm: İçindekiler Checker (Teşhis ve Yönlendirme)."""

from __future__ import annotations

from typing import Any
from bookmind.ai.services import LayoutParserEngine, PDFService
from bookmind.workflows.ingestion.state import PDFGraphState


def build_book_map_from_toc_items(title: str, total_pages: int, items: list[dict[str, Any]], source_name: str) -> dict[str, Any]:
    """Bookmark veya basılı TOC öğelerini LLM kullanmadan doğrudan hiyerarşik BookMap JSON nesnesine dönüştürür."""
    chapters = []
    for idx, item in enumerate(items):
        page_start = item.get("page", 1)
        next_page = items[idx + 1].get("page", total_pages) if idx + 1 < len(items) else total_pages
        page_end = max(page_start, next_page)
        chapters.append({
            "id": f"chapter_{idx + 1}",
            "title": item.get("title", f"Bölüm {idx + 1}"),
            "page_start": page_start,
            "page_end": page_end,
            "summary": f"{item.get('title')} (Sayfa {page_start} - {page_end})",
            "topics": [item.get("title")],
            "keywords": [f"Sayfa {page_start}"],
            "children": [],
        })

    return {
        "book_title": title,
        "author": f"Doğrudan Çıkarım ({source_name})",
        "total_pages": total_pages,
        "chapters": chapters,
    }


def check_toc_type_node(state: PDFGraphState) -> PDFGraphState:
    """Etiketlenmiş PDF'i inceleyerek Bookmark var mı, basılı İçindekiler var mı, yoksa Düzensiz PDF mi teşhis eder."""
    pdf_path = state["pdf_path"]
    total_pages = state.get("total_pages") or 1
    layout_elements = state.get("layout_elements") or []

    try:
        print(f"🔎 [2. İçindekiler Checker] '{pdf_path}' belge yapısı teşhis ediliyor...")

        # YOL 1: Gömülü Bookmark / Hyperlink var mı? (0 LLM ÇAĞRISI)
        bookmark_inspection = PDFService.extract_toc_from_bookmark_hyperlink(pdf_path)
        if bookmark_inspection.get("has_toc") and bookmark_inspection.get("toc"):
            print("  🟢 1. YOL: Gömülü Sidebar Bookmark veya Hyperlink tespit edildi! (LLM ÇAĞRILMAYACAK)")
            direct_book_map = build_book_map_from_toc_items(
                title=Path(pdf_path).name.replace(".pdf", ""),
                total_pages=total_pages,
                items=bookmark_inspection["toc"],
                source_name="Bookmark/Hyperlink",
            )
            return {
                **state,
                "toc_type": "BOOKMARK",
                "book_map": direct_book_map,
            }

        # YOL 2: Basılı 'İÇİNDEKİLER' Sayfası var mı?
        physical_toc_text = LayoutParserEngine.extract_toc_from_layout(layout_elements)
        if physical_toc_text:
            print("  🟡 2. YOL: Basılı 'İÇİNDEKİLER' sayfası tespit edildi! (İçindekiler Extract Engine çalışacak)")
            return {
                **state,
                "toc_type": "PHYSICAL_TOC",
                "toc_text": physical_toc_text,
            }

        # YOL 3: Düzensiz PDF (YALNIZCA BURADA LLM ÇAĞRILACAK)
        print("  🔴 3. YOL: Bookmark veya Basılı İçindekiler bulunamadı! Düzensiz PDF (YALNIZCA BURADA AGENT DEVREYE GİRECEK).")
        return {
            **state,
            "toc_type": "UNSTRUCTURED",
            "toc_text": None,
        }

    except Exception as e:
        return {
            **state,
            "error": f"İçindekiler teşhisi (Checker) sırasında hata oluştu: {e!s}",
        }
