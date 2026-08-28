"""PDF haritalama node'ları."""

from __future__ import annotations

from bookmind.agents.mapper_agent import MapperAgent
from bookmind.graph.pdf.state import PDFGraphState
from bookmind.services import PDFExtractorService
from langgraph.graph import END


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


async def map_chapters_node(state: PDFGraphState) -> PDFGraphState:
    """Node 2: MapperAgent aracılığıyla TOC → BookMap JSON dönüşümü yapar."""
    agent = MapperAgent()
    try:
        book_map = await agent.map(
            toc_text=state["toc_text"],
            total_pages=state["total_pages"],
        )
        return {**state, "book_map": book_map.model_dump()}
    except ValueError as e:
        return {**state, "error": str(e)}
    except Exception as e:
        return {**state, "error": f"MapperAgent hatası: {e!s}"}


def should_continue(state: PDFGraphState) -> str:
    """Conditional edge: Node 1 hata ürettiyse pipeline'ı durdur."""
    return END if state.get("error") else "map_chapters"
