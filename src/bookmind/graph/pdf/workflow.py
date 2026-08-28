"""PDF haritalama LangGraph orchestrator ve pipeline sınıfı.

Düğüm akışı:
    extract_toc ──┬─ 🟢 (TOC/Köprü bulundu) ─→ map_chapters ──→ END
                  └─ 🔀 (Bulunamadı) ────────→ unstructured_pdf_hierarchy (2. Kademe) ──→ END
"""

from __future__ import annotations

from typing import Any
from langgraph.graph import END, StateGraph

from bookmind.graph.pdf.edges import should_continue
from bookmind.graph.pdf.nodes import (
    extract_toc_node,
    map_chapters_node,
)
from bookmind.graph.pdf.state import PDFGraphState

#: Düğüm sırası tanımı
PIPELINE_NODES: tuple[str, ...] = ("extract_toc", "map_chapters")


class PDFProcessingGraph:
    """PDF işleme ve haritalama LangGraph orkestratörü (StateGraph Orkestratör Sınıfı).

    Çizge kurulumu, düğümlerin kaydedilmesi, koşullu kenarların bağlanması
    ve çalıştırma yaşam döngüsünü kapsar.
    """

    def __init__(self) -> None:
        self._graph: Any = None

    def build_graph(self) -> Any:
        """LangGraph StateGraph yapısını kurar ve derler.

        - Düğümleri (extract_toc, map_chapters) ekler.
        - Entry point olarak 'extract_toc' düğümünü ayarlar.
        - Koşullu kenarları (should_continue / router) bağlar.
        """
        workflow = StateGraph(PDFGraphState)

        # Düğümleri kaydet
        workflow.add_node("extract_toc", extract_toc_node)
        workflow.add_node("map_chapters", map_chapters_node)

        # Giriş kapısı
        workflow.set_entry_point("extract_toc")

        # Koşullu Yönlendirme (Router)
        workflow.add_conditional_edges(
            "extract_toc",
            should_continue,
            {
                "map_chapters": "map_chapters",
                "unstructured_pdf_hierarchy": END,
            },
        )

        # Doğrusal kenarlar
        workflow.add_edge("map_chapters", END)

        self._graph = workflow.compile()
        return self._graph

    async def run(self, pdf_path: str) -> dict[str, Any]:
        """PDF haritalama pipeline'ını verilen pdf_path ile çalıştırır.

        Args:
            pdf_path: İşlenecek PDF dosyasının mutlak veya bağıl yolu.

        Returns:
            dict: {"success": True/False, "book_map": dict, "error": str}
        """
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


# Geriye dönük uyumluluk yardımcı fonksiyonları
def build_pdf_graph() -> StateGraph:
    """Geriye dönük uyumluluk: PDFProcessingGraph().build_graph() çağırır."""
    return PDFProcessingGraph().build_graph()


async def process_pdf(pdf_path: str) -> dict[str, Any]:
    """Geriye dönük uyumluluk: PDFProcessingGraph().run(pdf_path) çağırır."""
    orchestrator = PDFProcessingGraph()
    return await orchestrator.run(pdf_path)
