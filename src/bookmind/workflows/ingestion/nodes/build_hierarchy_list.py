"""workflows.ingestion.nodes.build_hierarchy_list — 4. Düğüm: Hierarchy List (Nihai Harita Üretici)."""

from __future__ import annotations

from bookmind.ai.agents import HierarchyExtractorAgent
from bookmind.workflows.ingestion.state import PDFGraphState


async def build_hierarchy_list_node(state: PDFGraphState) -> PDFGraphState:
    """Nihai Hiyerarşik BookMap JSON ağacını döndürür. (Path 1 ve Path 2 haritaları hazır geldiği için LLM çağrılmaz, yalnızca Path 3'te HierarchyExtractorAgent çalışır)."""
    existing_map = state.get("book_map")

    # YOL 1 ve YOL 2: Harita zaten kural tabanlı olarak üretildi! (0 LLM ÇAĞRISI)
    if existing_map:
        print(f"🏁 [4. Hierarchy List] Harita hazır teslim alındı! (LLM Çağrılmadı | Kaynak: {existing_map.get('author')})")
        return state

    # YOL 3: Düzensiz PDF (YALNIZCA BURADA HierarchyExtractorAgent LLM ÇALIŞIR)
    toc_text = state.get("toc_text") or ""
    total_pages = state.get("total_pages") or 1
    layout_elements = state.get("layout_elements") or []

    try:
        print(f"🗺️ [4. Hierarchy List] 3. YOL (Düzensiz PDF): HierarchyExtractorAgent (LLM) çalıştırılıyor...")
        agent = HierarchyExtractorAgent()

        header_elements = [el for el in layout_elements if el.get("type") == "heading"]
        print(f"  🔍 {len(header_elements)} adet 'heading' etiketli eleman ajana besleniyor...")

        book_map_obj = await agent.extract_hierarchy(headings_input=header_elements, total_pages=total_pages)
        book_map_dict = book_map_obj.model_dump()
        print(f"✅ [4. Hierarchy List] LLM Haritalama tamamlandı! Kitap: '{book_map_dict.get('book_title')}', Bölüm Sayısı: {len(book_map_dict.get('chapters', []))}")

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
