"""workflows.ingestion.graph — Ingestion LangGraph definition and compilation."""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, StateGraph

from bookmind.workflows.ingestion.nodes.parse_pdf import extract_toc_node
from bookmind.workflows.ingestion.nodes.extract_structure import map_chapters_node
from bookmind.workflows.ingestion.state import PDFGraphState


def should_continue(state: PDFGraphState) -> str:
    """extract_toc adımından sonra hangi düğüme devam edileceğine karar verir."""
    if state.get("error"):
        return END

    if not state.get("toc_text") or not state["toc_text"].strip():
        # Gömülü TOC bulunamazsa orantısız/unstructured pdf noduna yönlendir
        print("TOC/Bookmark bulunamadı: unstructured_pdf_hierarchy")
        return "unstructured_pdf_hierarchy"

    return "map_chapters"


class PDFProcessingGraph:
    """PDF işleme ve haritalama LangGraph orkestratörü."""

    def __init__(self) -> None:
        self._graph: Any = None

    def build_graph(self) -> Any:
        workflow = StateGraph(PDFGraphState)

        # Düğümleri ekle
        workflow.add_node("extract_toc", extract_toc_node)
        workflow.add_node("map_chapters", map_chapters_node)

        # Başlangıç noktası
        workflow.set_entry_point("extract_toc")

        # Yönlendirme kenarı
        workflow.add_conditional_edges(
            "extract_toc",
            should_continue,
            {
                "map_chapters": "map_chapters",
                "unstructured_pdf_hierarchy": END,
            },
        )

        workflow.add_edge("map_chapters", END)

        self._graph = workflow.compile()
        return self._graph

    async def run(self, pdf_path: str) -> dict[str, Any]:
        """İşlemi tetikler ve durum sonucunu döndürür."""
        if self._graph is None:
            self.build_graph()

        initial_state: PDFGraphState = {
            "pdf_path": pdf_path,
            "toc_text": "",
            "total_pages": 0,
            "book_map": None,
            "error": None,
        }

        result = await self._graph.ainvoke(initial_state)

        if result.get("error"):
            return {"success": False, "error": result["error"]}

        return {"success": True, "book_map": result["book_map"]}
