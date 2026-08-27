"""Mapping node'ları — PDF'den kitap haritası oluşturma adımları.

Node'lar:
    extract_toc_node   → PDF'den içindekiler metnini çeker
    map_chapters_node  → MapperAgent ile JSON haritaya dönüştürür
    should_continue    → Conditional edge: hata varsa pipeline'ı durdur
"""

from __future__ import annotations

from bookmind.agents.mapper_agent import MapperAgent
from bookmind.graph.state import GraphState
from bookmind.utils.pdf import extract_toc_text, get_page_count
from langgraph.graph import END


def extract_toc_node(state: GraphState) -> GraphState:
    """Node 1: PDF'den içindekiler metnini ve sayfa sayısını çeker.

    PyMuPDF ile önce built-in TOC'u dener,
    yoksa ilk N sayfanın ham metnini döndürür.
    """
    try:
        toc_text = extract_toc_text(state["pdf_path"])
        total_pages = get_page_count(state["pdf_path"])
        return {**state, "toc_text": toc_text, "total_pages": total_pages}
    except Exception as e:
        return {**state, "error": f"PDF okuma hatası: {e!s}"}


async def map_chapters_node(state: GraphState) -> GraphState:
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


def should_continue(state: GraphState) -> str:
    """Conditional edge: Node 1 hata ürettiyse pipeline'ı durdur."""
    return END if state.get("error") else "map_chapters"
