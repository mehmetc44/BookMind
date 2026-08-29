"""workflows.ingestion.graph — Ingestion LangGraph definition and compilation."""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, StateGraph

from bookmind.workflows.ingestion.nodes.parse_pdf import extract_toc_node
from bookmind.workflows.ingestion.nodes.extract_structure import map_chapters_node
from bookmind.workflows.ingestion.nodes.parse_layout import parse_layout_node
from bookmind.workflows.ingestion.state import PDFGraphState


def should_continue(state: PDFGraphState) -> str:
    """parse_pdf_bookmarks adımından sonra hangi düğüme devam edileceğine karar verir."""
    if state.get("error"):
        return END

    if not state.get("toc_text") or not state["toc_text"].strip():
        print("💡 Bookmark/Hyperlink bulunamadı: 'parse_pdf_layout' düğümüne geçiliyor...")
        return "parse_pdf_layout"

    print("💡 Bookmark/Hyperlink bulundu: 'generate_book_map' düğümüne geçiliyor...")
    return "generate_book_map"


class PDFProcessingGraph:
    """PDF işleme ve haritalama LangGraph orkestratörü."""

    def __init__(self) -> None:
        self._graph: Any = None

    def build_graph(self) -> Any:
        workflow = StateGraph(PDFGraphState)

        # Düğümleri ekle (Temiz ve Okunabilir İsimler)
        workflow.add_node("parse_pdf_bookmarks", extract_toc_node)
        workflow.add_node("parse_pdf_layout", parse_layout_node)
        workflow.add_node("generate_book_map", map_chapters_node)

        # Başlangıç noktası
        workflow.set_entry_point("parse_pdf_bookmarks")

        # Yönlendirme kenarı
        workflow.add_conditional_edges(
            "parse_pdf_bookmarks",
            should_continue,
            {
                "generate_book_map": "generate_book_map",
                "parse_pdf_layout": "parse_pdf_layout",
            },
        )

        workflow.add_edge("parse_pdf_layout", "generate_book_map")
        workflow.add_edge("generate_book_map", END)

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
            "layout_elements": None,
            "error": None,
        }

        result = await self._graph.ainvoke(initial_state)

        if result.get("error"):
            return {"success": False, "error": result["error"]}

        return {
            "success": True,
            "book_map": result.get("book_map"),
            "layout_elements": result.get("layout_elements"),
        }
