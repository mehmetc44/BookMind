"""workflows.ingestion.nodes.label_pdf_layout — 1. Düğüm: PDF Fiziki Etiketleme (Etiketleme Label)."""

from __future__ import annotations

from bookmind.ai.services import LayoutParserEngine, PDFService
from bookmind.workflows.ingestion.state import PDFGraphState


def label_pdf_layout_node(state: PDFGraphState) -> PDFGraphState:
    """Sisteme giren her PDF'in ilk olarak fiziki etiketlerini (heading, text, image, table, formula) ve sayfa sayısını çıkarır."""
    pdf_path = state["pdf_path"]

    try:
        print(f"🔍 [1. Etiketleme Label] '{pdf_path}' fiziki etiketleme başlatıldı...")
        total_pages = PDFService.get_page_count(pdf_path)
        elements = LayoutParserEngine.parse_pdf_layout(pdf_path)

        type_counts: dict[str, int] = {}
        for el in elements:
            t = el["type"]
            type_counts[t] = type_counts.get(t, 0) + 1

        print(f"✅ [1. Etiketleme Label] Tamamlandı! Toplam {len(elements)} eleman etiketlendi: {type_counts}")

        return {
            **state,
            "total_pages": total_pages,
            "layout_elements": elements,
        }
    except Exception as e:
        return {
            **state,
            "error": f"Fiziki etiketleme (Label) sırasında hata oluştu: {e!s}",
        }
