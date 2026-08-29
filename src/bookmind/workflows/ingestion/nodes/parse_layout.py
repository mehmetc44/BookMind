"""workflows.ingestion.nodes.parse_layout — Fallback node for raw layout element tagging when TOC is absent."""

from __future__ import annotations

from bookmind.ai.services import LayoutParserEngine
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

        # Yol 1: 'İÇİNDEKİLER' / 'CONTENTS' sayfası var mı?
        extracted_toc_text = LayoutParserEngine.extract_toc_from_layout(elements)

        if extracted_toc_text:
            print("💡 [LayoutParserEngine] Düz metin 'İÇİNDEKİLER' sayfası bulundu ve metin çıkarıldı!")
            toc_summary = extracted_toc_text
        else:
            print("💡 [LayoutParserEngine] 'İÇİNDEKİLER' sayfası yok; tüm 'heading' etiketlerinden hiyerarşi oluşturuluyor...")
            toc_summary = LayoutParserEngine.extract_heading_summary(elements)

        return {
            **state,
            "layout_elements": elements,
            "toc_text": toc_summary,
        }
    except Exception as e:
        return {
            **state,
            "error": f"Fiziki layout etiketleme hatası: {e!s}",
        }
