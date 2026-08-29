"""workflows.ingestion.nodes.extract_toc_page — 3A. Düğüm: İçindekiler Extract Engine (0 LLM Çağrısı ile Doğrudan Haritalama)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from bookmind.workflows.ingestion.nodes.check_toc_type import build_book_map_from_toc_items
from bookmind.workflows.ingestion.state import PDFGraphState


def parse_printed_toc_text(toc_text: str) -> list[dict[str, Any]]:
    """Basılı İçindekiler metnindeki satırlardan başlık ve sayfa numaralarını süzerek nesnelere dönüştürür."""
    items: list[dict[str, Any]] = []
    lines = [l.strip() for l in toc_text.split("\n") if l.strip()]

    for line in lines:
        # Örnek kalıplar: "1. Giriş . . . . 3" veya "Bölüm 2 ..... sayfa 15"
        match = re.search(r"^(.*?)(?:\s*[\.\-_]+\s*|\s+sayfa\s+|\s+)(\d+)\s*$", line, re.IGNORECASE)
        if match:
            raw_title = match.group(1).strip(" .-_")
            page_num = int(match.group(2))

            # Başlık temizleme
            clean_title = re.sub(r"^(i̇çi̇ndeki̇ler|contents|index)\s*", "", raw_title, flags=re.IGNORECASE).strip()
            if clean_title and len(clean_title) > 2:
                items.append({
                    "title": clean_title,
                    "page": page_num,
                })

    return items


def extract_toc_page_node(state: PDFGraphState) -> PDFGraphState:
    """Basılı İçindekiler sayfasından LLM kullanmadan doğrudan hiyerarşik BookMap JSON üretir (0 LLM ÇAĞRISI)."""
    toc_text = state.get("toc_text") or ""
    pdf_path = state["pdf_path"]
    total_pages = state.get("total_pages") or 1

    print(f"⚙️ [3A. İçindekiler Extract Engine] Basılı TOC sayfası ayrıştırılıyor... (LLM ÇAĞRILMAYACAK)")
    parsed_items = parse_printed_toc_text(toc_text)

    if parsed_items:
        print(f"  ✅ {len(parsed_items)} adet basılı bölüm başlığı doğrudan çıkarıldı!")
        direct_book_map = build_book_map_from_toc_items(
            title=Path(pdf_path).name.replace(".pdf", ""),
            total_pages=total_pages,
            items=parsed_items,
            source_name="Basılı İçindekiler Sayfası",
        )
        return {
            **state,
            "book_map": direct_book_map,
        }

    # Eğer regex süzemezse fallback metni bırak (Path 3 LLM'e devredecek)
    print("  ⚠️ Basılı TOC satırları kural ile süzülemedi, LLM'e devredilecek.")
    return {
        **state,
        "toc_type": "UNSTRUCTURED",
    }
