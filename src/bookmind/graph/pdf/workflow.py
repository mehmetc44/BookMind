"""PDF haritalama LangGraph pipeline'ı."""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, StateGraph

from bookmind.graph.pdf.nodes import (
    extract_toc_node,
    map_chapters_node,
    should_continue,
)
from bookmind.graph.pdf.state import PDFGraphState


def build_pdf_graph() -> StateGraph:
    """PDF haritalama LangGraph pipeline'ını derler ve döndürür."""
    workflow = StateGraph(PDFGraphState)

    workflow.add_node("extract_toc", extract_toc_node)
    workflow.add_node("map_chapters", map_chapters_node)

    workflow.set_entry_point("extract_toc")
    workflow.add_conditional_edges("extract_toc", should_continue)
    workflow.add_edge("map_chapters", END)

    return workflow.compile()


async def process_pdf(pdf_path: str) -> dict[str, Any]:
    """PDF dosyasını işleyip kitap haritası döndürür."""
    graph = build_pdf_graph()

    initial_state: PDFGraphState = {
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
