"""workflows.ingestion.state — PDF ingestion Graph state."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

TOCType = Literal["BOOKMARK", "PHYSICAL_TOC", "UNSTRUCTURED"]


class PDFGraphState(TypedDict):
    """PDF haritalama pipeline'ının durumu."""

    pdf_path: str
    total_pages: int
    layout_elements: list[dict[str, Any]] | None    # 1. Düğüm: Etiketleme Label çıktısı
    toc_type: TOCType | None                        # 2. Düğüm: İçindekiler Checker teşhisi
    toc_text: str | None                            # Extract edilen TOC veya başlık özeti metni
    book_map: dict[str, Any] | None                 # 4. Düğüm: Nihai Hierarchy List JSON
    error: str | None
