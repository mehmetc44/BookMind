"""router.py — PDF pipeline koşullu geçiş (conditional edge) yönlendiricisi."""

from __future__ import annotations

from bookmind.ai.graphs.pdf.state import PDFGraphState


def route_after_extract_toc(state: PDFGraphState) -> str:
    """Node 1 (extract_toc) sonrasında akış yönlendirmesi yapar.

    - 1. Kademe Gömülü TOC/Köprü bulunduysa: 'map_chapters' düğümüne ilerler.
    - 1. Kademe TOC bulunamadıysa veya hata varsa: 'unstructured_pdf_hierarchy'
      (2. Kademe Düzensiz PDF Hiyerarşisi Çıkarma) düğümüne yönlenir.
    """
    error = state.get("error")
    toc_text = state.get("toc_text", "")

    # TOC verisi yoksa veya hata alındıysa 2. Kademe Düzensiz PDF Hiyerarşisi düğümüne geç
    if error or not toc_text or toc_text == "[]":
        target_node = "unstructured_pdf_hierarchy"
        print(f"🔀 [PDF Router Fallback] 1. Kademe TOC bulunamadı. '{target_node}' düğümüne geçiliyor...")
        return target_node

    print("🟢 [PDF Router] 1. Kademe Gömülü TOC tespit edildi. 'map_chapters' düğümüne ilerleniyor...")
    return "map_chapters"


# Backward compatibility alias
should_continue = route_after_extract_toc
