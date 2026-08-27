"""LangGraph pipeline — PDF'den kitap haritası oluşturma.

Node'lar:
    1. extract_toc  → PDF'den içindekiler metnini çeker
    2. map_chapters → MapperAgent ile JSON harita üretir
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from bookmind.agents.mapper_agent import MapperAgent
from bookmind.pdf_utils import extract_toc_text, get_page_count


class GraphState(TypedDict):
    """LangGraph boyunca taşınan durum."""

    pdf_path: str
    toc_text: str
    total_pages: int
    book_map: dict[str, Any] | None
    error: str | None


# ─── Node 1 ───────────────────────────────────────────────────────────────────

def extract_toc_node(state: GraphState) -> GraphState:
    """PDF'den içindekiler metnini ve sayfa sayısını çeker."""
    try:
        toc_text = extract_toc_text(state["pdf_path"])
        total_pages = get_page_count(state["pdf_path"])
        return {**state, "toc_text": toc_text, "total_pages": total_pages}
    except Exception as e:
        return {**state, "error": f"PDF okuma hatası: {e!s}"}


# ─── Node 2 ───────────────────────────────────────────────────────────────────

async def map_chapters_node(state: GraphState) -> GraphState:
    """MapperAgent ile TOC metnini yapısal kitap haritasına dönüştürür."""
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


# ─── Conditional Edge ─────────────────────────────────────────────────────────

def should_continue(state: GraphState) -> str:
    """Node 1 hata ürettiyse pipeline'ı durdur."""
    return END if state.get("error") else "map_chapters"


# ─── Graph Builder ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """LangGraph pipeline'ını derler."""
    workflow = StateGraph(GraphState)

    workflow.add_node("extract_toc", extract_toc_node)
    workflow.add_node("map_chapters", map_chapters_node)

    workflow.set_entry_point("extract_toc")
    workflow.add_conditional_edges("extract_toc", should_continue)
    workflow.add_edge("map_chapters", END)

    return workflow.compile()


# ─── Public API ───────────────────────────────────────────────────────────────

async def process_pdf(pdf_path: str) -> dict[str, Any]:
    """PDF'i işleyip kitap haritası döndürür.

    Args:
        pdf_path: İşlenecek PDF dosyasının yolu.

    Returns:
        {"success": True, "book_map": {...}}
        veya
        {"success": False, "error": "..."}
    """
    graph = build_graph()
    initial_state: GraphState = {
        "pdf_path": pdf_path,
        "toc_text": "",
        "total_pages": 0,
        "book_map": None,
        "error": None,
    }

    result = await graph.ainvoke(initial_state)

    if result.get("error"):
        return {"success": False, "error": result["error"]}

    return {"success": True, "book_map": result["book_map"]}
