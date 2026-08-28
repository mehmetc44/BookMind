"""workflows.ingestion.state — PDF ingestion Graph state."""

from __future__ import annotations

from typing import Any, TypedDict


class PDFGraphState(TypedDict):
    """PDF haritalama pipeline'ının durumu."""

    pdf_path: str
    toc_text: str
    total_pages: int
    book_map: dict[str, Any] | None
    layout_elements: list[dict[str, Any]] | None
    error: str | None
