"""workflows.ingestion.nodes.parse_pdf — Node for parsing PDF metadata and embedded TOC."""

from __future__ import annotations

from bookmind.ai.services import PDFService
from bookmind.workflows.ingestion.state import PDFGraphState


def extract_toc_node(state: PDFGraphState) -> PDFGraphState:
    """PDF'deki bookmark/köprü tablosunu ve toplam sayfa sayısını çeker."""
    pdf_path = state["pdf_path"]

    try:
        total_pages = PDFService.get_page_count(pdf_path)
        inspection = PDFService.extract_toc_from_bookmark_hyperlink(pdf_path)

        toc_lines = []
        if inspection.get("has_toc") and inspection.get("toc"):
            for item in inspection["toc"]:
                toc_lines.append(f"{item['title']} (Sayfa {item['page']})")
            toc_text = "\n".join(toc_lines)
        else:
            toc_text = ""

        return {
            **state,
            "total_pages": total_pages,
            "toc_text": toc_text,
        }
    except Exception as e:
        return {
            **state,
            "error": f"TOC/Sayfa okuma sırasında hata oluştu: {e!s}",
        }
