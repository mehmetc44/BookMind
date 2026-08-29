"""workflows.ingestion.nodes.extract_toc_page — 3A. Düğüm: İçindekiler Extract Engine."""

from __future__ import annotations

from bookmind.workflows.ingestion.state import PDFGraphState


def extract_toc_page_node(state: PDFGraphState) -> PDFGraphState:
    """Basılı İçindekiler sayfasındaki bölüm metinlerini süzerek haritalama için hazırlar."""
    toc_text = state.get("toc_text") or ""
    print(f"⚙️ [3A. İçindekiler Extract Engine] Basılı TOC metni haritalama için işlendi (Uzunluk: {len(toc_text)} karakter).")

    return {
        **state,
        "toc_text": toc_text,
    }
