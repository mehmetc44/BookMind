"""workflows.ingestion.nodes.extract_structure — Node for converting raw TOC text into a structural map."""

from __future__ import annotations

from bookmind.ai.agents import MapperAgent
from bookmind.workflows.ingestion.state import PDFGraphState


async def map_chapters_node(state: PDFGraphState) -> PDFGraphState:
    """MapperAgent kullanarak ham TOC metnini yapısal BookMap şemasına dönüştürür."""
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
