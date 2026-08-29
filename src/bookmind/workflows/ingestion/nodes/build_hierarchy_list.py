"""workflows.ingestion.nodes.build_hierarchy_list — 4. Düğüm: Hierarchy List (HierarchyExtractorAgent ile Harita Üretici)."""

from __future__ import annotations

from bookmind.ai.agents import HierarchyExtractorAgent
from bookmind.workflows.ingestion.state import PDFGraphState


async def build_hierarchy_list_node(state: PDFGraphState) -> PDFGraphState:
    """Tüm yollardan gelen etiketli başlıkları (header) HierarchyExtractorAgent (LLM) ile nihai Hiyerarşik BookMap JSON'a dönüştürür."""
    toc_text = state.get("toc_text") or ""
    total_pages = state.get("total_pages") or 1
    layout_elements = state.get("layout_elements") or []

    try:
        print(f"🗺️ [4. Hierarchy List] HierarchyExtractorAgent (LLM) çalıştırılıyor...")
        agent = HierarchyExtractorAgent()

        # Düzensiz PDF ise sadece etiketli header elemanlarını ver
        if state.get("toc_type") == "UNSTRUCTURED" and layout_elements:
            header_elements = [el for el in layout_elements if el.get("type") == "heading"]
            print(f"  🔍 Sadece {len(header_elements)} adet 'heading' etiketli eleman hiyerarşi ajanı için süzüldü.")
            book_map_obj = await agent.extract_hierarchy(headings_input=header_elements, total_pages=total_pages)
        else:
            book_map_obj = await agent.extract_hierarchy(headings_input=toc_text, total_pages=total_pages)

        book_map_dict = book_map_obj.model_dump()
        print(f"✅ [4. Hierarchy List] Haritalama tamamlandı! Kitap: '{book_map_dict.get('book_title')}', Bölüm Sayısı: {len(book_map_dict.get('chapters', []))}")

        return {
            **state,
            "book_map": book_map_dict,
        }
    except Exception as e:
        print(f"⚠️ [4. Hierarchy List] HierarchyExtractorAgent hatası: {e!s}. Fallback harita oluşturuluyor...")
        fallback_map = {
            "book_title": "Haritalandırılmış Belge",
            "author": "BookMind Asistanı",
            "total_pages": total_pages,
            "chapters": [
                {
                    "id": "ch_1",
                    "title": "Ana İçerik",
                    "page_start": 1,
                    "page_end": total_pages,
                    "summary": "Belge içeriği",
                    "topics": ["Genel"],
                    "keywords": ["Belge"],
                    "children": [],
                }
            ],
        }
        return {
            **state,
            "book_map": fallback_map,
        }
