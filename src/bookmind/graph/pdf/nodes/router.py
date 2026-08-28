"""router.py — PDF pipeline koşullu geçiş (conditional edge) yönlendiricisi."""

from __future__ import annotations

from bookmind.graph.pdf.state import PDFGraphState
from langgraph.graph import END


def should_continue(state: PDFGraphState) -> str:
    """Conditional edge: Node 1 hata ürettiyse pipeline'ı durdur."""
    return END if state.get("error") else "map_chapters"
