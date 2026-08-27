"""workflow.py — LangGraph pipeline'ının kurulum ve çalıştırma mantığı.

graph.py'nin yerini alan ana dosya.
Yeni node eklemek için:
    1. nodes/ altında ilgili node fonksiyonunu yaz
    2. build_graph() içinde workflow.add_node(...) ile bağla
"""

from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from bookmind.graph.nodes import (
    extract_toc_node,
    map_chapters_node,
    should_continue,
)
from bookmind.graph.state import GraphState


def build_graph() -> StateGraph:
    """LangGraph pipeline'ını derler ve döndürür.

    Akış:
        extract_toc ──(hata?)──► END
                    ──(tamam)──► map_chapters ──► END
    """
    workflow = StateGraph(GraphState)

    # ── Node'ları kaydet ──────────────────────────────────────────────────────
    workflow.add_node("extract_toc", extract_toc_node)
    workflow.add_node("map_chapters", map_chapters_node)

    # ── Akışı tanımla ─────────────────────────────────────────────────────────
    workflow.set_entry_point("extract_toc")
    workflow.add_conditional_edges("extract_toc", should_continue)
    workflow.add_edge("map_chapters", END)

    return workflow.compile()


async def process_pdf(pdf_path: str) -> dict[str, Any]:
    """PDF dosyasını işleyip kitap haritası döndürür.

    Args:
        pdf_path: İşlenecek PDF dosyasının tam yolu.

    Returns:
        Başarı: {"success": True,  "book_map": {...}}
        Hata:   {"success": False, "error": "..."}
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
