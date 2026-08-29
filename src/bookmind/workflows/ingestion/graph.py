"""workflows.ingestion.graph — SOTA Ingestion Pipeline LangGraph Definition and Orchestration."""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, StateGraph

from bookmind.workflows.ingestion.nodes.build_hierarchy_list import build_hierarchy_list_node
from bookmind.workflows.ingestion.nodes.check_toc_type import check_toc_type_node
from bookmind.workflows.ingestion.nodes.extract_toc_page import extract_toc_page_node
from bookmind.workflows.ingestion.nodes.label_pdf_layout import label_pdf_layout_node
from bookmind.workflows.ingestion.nodes.map_unstructured_layout import map_unstructured_layout_node
from bookmind.workflows.ingestion.state import PDFGraphState


def route_toc_type(state: PDFGraphState) -> str:
    """İçindekiler Checker teşhisine göre 3 farklı yoldan birine yönlendirir."""
    if state.get("error"):
        return END

    toc_type = state.get("toc_type")

    if toc_type == "BOOKMARK":
        # Yol 1: Gömülü Bookmark var ➔ Doğrudan Hierarchy List'e geç
        return "BOOKMARK"

    if toc_type == "PHYSICAL_TOC":
        # Yol 2: Basılı İçindekiler Sayfası var ➔ Extract Engine'e geç
        return "PHYSICAL_TOC"

    # Yol 3: Düzensiz PDF ➔ LLM Layout Mapper'a geç
    return "UNSTRUCTURED"


class PDFProcessingGraph:
    """PDF işleme ve haritalama LangGraph orkestratörü."""

    def __init__(self) -> None:
        self._graph: Any = None

    def build_graph(self) -> Any:
        workflow = StateGraph(PDFGraphState)

        # 1. Düğüm: Etiketleme Label (Gözlemci Motoru)
        workflow.add_node("label_pdf_layout", label_pdf_layout_node)

        # 2. Düğüm: İçindekiler Checker (Teşhis Mekanizması)
        workflow.add_node("check_toc_type", check_toc_type_node)

        # 3A. Düğüm: İçindekiler Extract Engine (Basılı TOC Süzücü)
        workflow.add_node("extract_toc_page", extract_toc_page_node)

        # 3B. Düğüm: Düzensiz PDF Layout Mapper (LLM Hazırlayıcı)
        workflow.add_node("map_unstructured_layout", map_unstructured_layout_node)

        # 4. Düğüm: Hierarchy List (Nihai Harita Üretici)
        workflow.add_node("build_hierarchy_list", build_hierarchy_list_node)

        # Başlangıç noktası: HER PDF ÖNCE ETİKETLENİR
        workflow.set_entry_point("label_pdf_layout")

        # 1. Düğümden 2. Düğüm (Checker)'e Düz Bağlantı
        workflow.add_edge("label_pdf_layout", "check_toc_type")

        # 2. Düğümden 3 Yönlü Koşullu Yönlendirme (Router)
        workflow.add_conditional_edges(
            "check_toc_type",
            route_toc_type,
            {
                "BOOKMARK": "build_hierarchy_list",
                "PHYSICAL_TOC": "extract_toc_page",
                "UNSTRUCTURED": "map_unstructured_layout",
                END: END,
            },
        )

        # 3A ve 3B Düğümlerinden 4. Düğüm (Hierarchy List)'e Birleşme
        workflow.add_edge("extract_toc_page", "build_hierarchy_list")
        workflow.add_edge("map_unstructured_layout", "build_hierarchy_list")
        workflow.add_edge("build_hierarchy_list", END)

        self._graph = workflow.compile()
        return self._graph

    async def run(self, pdf_path: str) -> dict[str, Any]:
        """İşlemi tetikler ve durum sonucunu döndürür."""
        if self._graph is None:
            self.build_graph()

        initial_state: PDFGraphState = {
            "pdf_path": pdf_path,
            "total_pages": 0,
            "layout_elements": None,
            "toc_type": None,
            "toc_text": None,
            "book_map": None,
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
