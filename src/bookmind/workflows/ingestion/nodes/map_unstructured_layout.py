"""workflows.ingestion.nodes.map_unstructured_layout — 3B. Düğüm: Düzensiz PDF Layout Mapper (LLM Engine)."""

from __future__ import annotations

from bookmind.ai.services import LayoutParserEngine
from bookmind.workflows.ingestion.state import PDFGraphState


def map_unstructured_layout_node(state: PDFGraphState) -> PDFGraphState:
    """İçindekiler sayfası olmayan düzensiz PDF'lerde tüm etiketli başlık dizisini LLM haritalaması için hazırlar."""
    layout_elements = state.get("layout_elements") or []

    print(f"🤖 [3B. Düzensiz PDF Layout Mapper] Belgedeki {len(layout_elements)} fiziki etiket süzülüyor...")
    heading_summary = LayoutParserEngine.extract_heading_summary(layout_elements)

    return {
        **state,
        "toc_text": heading_summary,
    }
