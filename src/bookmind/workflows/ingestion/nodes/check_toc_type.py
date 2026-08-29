"""workflows.ingestion.nodes.check_toc_type — 2. Düğüm: İçindekiler Checker (Teşhis ve Yönlendirme)."""

from __future__ import annotations

from bookmind.ai.services import LayoutParserEngine, PDFService
from bookmind.workflows.ingestion.state import PDFGraphState, TOCType


def check_toc_type_node(state: PDFGraphState) -> PDFGraphState:
    """Etiketlenmiş PDF'i inceleyerek Bookmark var mı, basılı İçindekiler var mı, yoksa Düzensiz PDF mi teşhis eder."""
    pdf_path = state["pdf_path"]
    layout_elements = state.get("layout_elements") or []

    try:
        print(f"🔎 [2. İçindekiler Checker] '{pdf_path}' belge yapısı teşhis ediliyor...")

        # 1. Teşhis: Gömülü Bookmark / Hyperlink var mı?
        bookmark_inspection = PDFService.extract_toc_from_bookmark_hyperlink(pdf_path)
        if bookmark_inspection.get("has_toc") and bookmark_inspection.get("toc"):
            print("  🟢 Teşhis: Gömülü Sidebar Bookmark veya Hyperlink tespit edildi! (BOOKMARK)")
            toc_lines = [f"{item['title']} (Sayfa {item['page']})" for item in bookmark_inspection["toc"]]
            return {
                **state,
                "toc_type": "BOOKMARK",
                "toc_text": "\n".join(toc_lines),
            }

        # 2. Teşhis: Basılı 'İÇİNDEKİLER' / 'CONTENTS' Sayfası var mı?
        physical_toc_text = LayoutParserEngine.extract_toc_from_layout(layout_elements)
        if physical_toc_text:
            print("  🟡 Teşhis: Basılı 'İÇİNDEKİLER' sayfası tespit edildi! (PHYSICAL_TOC)")
            return {
                **state,
                "toc_type": "PHYSICAL_TOC",
                "toc_text": physical_toc_text,
            }

        # 3. Teşhis: Düzensiz PDF (Ne Bookmark ne İçindekiler Sayfası Var)
        print("  🔴 Teşhis: Bookmark veya Basılı İçindekiler bulunamadı! Düzensiz PDF. (UNSTRUCTURED)")
        return {
            **state,
            "toc_type": "UNSTRUCTURED",
            "toc_text": None,
        }

    except Exception as e:
        return {
            **state,
            "error": f"İçindekiler teşhisi (Checker) sırasında hata oluştu: {e!s}",
        }
