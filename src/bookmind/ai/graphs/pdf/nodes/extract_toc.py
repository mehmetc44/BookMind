"""extract_toc.py — PDFExtractorService aracılığıyla TOC tespiti yapan LangGraph düğümü."""

from __future__ import annotations

from bookmind.ai.extractors import PDFExtractorService
from bookmind.ai.graphs.pdf.state import PDFGraphState


def extract_toc_node(state: PDFGraphState) -> PDFGraphState:
    """Node 1: PDFExtractorService aracılığıyla 1. Kademe TOC tespiti yapar."""
    try:
        inspection = PDFExtractorService.inspect_toc(state["pdf_path"])
        return {
            **state,
            "toc_text": str(inspection.get("toc", [])),
            "total_pages": inspection.get("total_pages", 0),
        }
    except Exception as e:
        return {**state, "error": f"PDF okuma hatası: {e!s}"}
