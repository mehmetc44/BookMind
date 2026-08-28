"""workflows.ingestion.nodes.parse_layout — Fallback node for raw layout element tagging when TOC is absent."""

from __future__ import annotations

from bookmind.ai.parsing import LayoutParserEngine
from bookmind.workflows.ingestion.state import PDFGraphState


def parse_layout_node(state: PDFGraphState) -> PDFGraphState:
    """TOC/Bookmark bulunmayan düzensiz PDF'lerde fiziksel öğeleri (başlık, yazı, görsel, tablo, formül) etiketler."""
    pdf_path = state["pdf_path"]

    try:
        print(f"🔍 [LayoutParserEngine] '{pdf_path}' için ham fiziki öğe etiketleme başlatıldı...")
        elements = LayoutParserEngine.parse_pdf_layout(pdf_path)

        # İstatistiki özet bastır
        type_counts: dict[str, int] = {}
        for el in elements:
            t = el["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        print(f"✅ [LayoutParserEngine] Etiketleme tamamlandı! Özet: {type_counts}")

        return {
            **state,
            "layout_elements": elements,
        }
    except Exception as e:
        return {
            **state,
            "error": f"Fiziki layout etiketleme hatası: {e!s}",
        }
