"""map_chapters.py — MapperAgent aracılığıyla TOC → BookMap JSON dönüşümü yapan LangGraph düğümü."""

from __future__ import annotations

from bookmind.agents.mapper_agent import MapperAgent
from bookmind.graph.pdf.state import PDFGraphState


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
