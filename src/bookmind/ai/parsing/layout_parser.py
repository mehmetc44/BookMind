"""ai.parsing.layout_parser — Ham Fiziksel Öğeleri (Başlık, Yazı, Görsel, Tablo, Formül) Etiketleyen 'Gözlemci' Motoru."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal
import pymupdf

LayoutElementType = Literal["heading", "text", "formula", "table", "image"]


class LayoutElement:
    """Fiziksel PDF öğesini temsil eden etiketli veri yapısı."""

    def __init__(
        self,
        element_type: LayoutElementType,
        content: str,
        page: int,
        bbox: tuple[float, float, float, float] | None = None,
        font_size: float = 0.0,
        is_bold: bool = False,
        meta: dict[str, Any] | None = None,
    ) -> None:
        self.type = element_type
        self.content = content
        self.page = page
        self.bbox = bbox
        self.font_size = font_size
        self.is_bold = is_bold
        self.meta = meta or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "content": self.content,
            "page": self.page,
            "bbox": self.bbox,
            "font_size": round(self.font_size, 2),
            "is_bold": self.is_bold,
            "meta": self.meta,
        }

    def __repr__(self) -> str:
        snippet = self.content[:30].replace("\n", " ")
        return f"[{self.type.upper()} | p.{self.page} | size={self.font_size:.1f}{' | BOLD' if self.is_bold else ''}] {snippet}..."


class LayoutParserEngine:
    """PDF belgesini sayfa sayfa tarayıp tür bazlı fiziki etiketleme (Layout Parsing) yapan motor."""

    FORMULA_PATTERNS = re.compile(
        r"[\u2200-\u22FF\u2A00-\u2AFF]|\b(lim|sum|int|sqrt|log|sin|cos|tan)\b|\b[a-zA-Z]\s*=\s*[-+]?\d+|\b\d+\s*[\+\-\*/=]\s*\d+|\b\w+_\{\w+\}|\b\w+\^\{\w+\}",
        re.IGNORECASE,
    )

    @classmethod
    def parse_pdf_layout(cls, pdf_path: str | Path, max_pages: int | None = None) -> list[dict[str, Any]]:
        """PDF dosyasını tarayarak tür bazlı fiziki etiketlenmiş elemanlar listesi döndürür."""
        doc = pymupdf.open(str(pdf_path))
        total_pages = len(doc)
        pages_to_process = min(max_pages, total_pages) if max_pages else total_pages

        # 1. Aşama: Sayfa metinlerinin ortalama font boyutunu bul (Body text baseline)
        baseline_font_size = cls._calculate_baseline_font_size(doc, pages_to_process)

        elements: list[LayoutElement] = []

        for page_idx in range(pages_to_process):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 2. Aşama: Tabloları Tespit Et (PyMuPDF find_tables)
            table_bboxes = []
            try:
                tables = page.find_tables()
                for tbl_idx, tbl in enumerate(tables):
                    table_bboxes.append(tbl.bbox)
                    tbl_markdown = tbl.to_markdown() if hasattr(tbl, "to_markdown") else str(tbl.extract())
                    elements.append(
                        LayoutElement(
                            element_type="table",
                            content=tbl_markdown,
                            page=page_num,
                            bbox=tbl.bbox,
                            meta={"table_index": tbl_idx + 1},
                        )
                    )
            except Exception:
                pass

            # 3. Aşama: Görselleri Tespit Et (Images)
            image_bboxes = []
            for img_info in page.get_image_info(hashes=False):
                img_bbox = img_info.get("bbox")
                if img_bbox:
                    image_bboxes.append(img_bbox)
                    elements.append(
                        LayoutElement(
                            element_type="image",
                            content=f"[Görsel: Sayfa {page_num}, BBox {img_bbox}]",
                            page=page_num,
                            bbox=img_bbox,
                            meta={"image_info": img_info.get("number", 0)},
                        )
                    )

            # 4. Aşama: Metin Bloklarını Doku ve Font Boyutuyla Analiz Et
            text_page_dict = page.get_text("dict")
            for block in text_page_dict.get("blocks", []):
                # Görsel veya tablo bloklarını atla (sadece metin blokları: type == 0)
                if block.get("type") != 0:
                    continue

                block_bbox = block.get("bbox")
                if cls._is_inside_any_bbox(block_bbox, table_bboxes):
                    continue

                # Blok içindeki satırları ve font özelliklerini tara
                block_lines = block.get("lines", [])
                full_block_text = ""
                max_font_size = 0.0
                has_bold = False

                for line in block_lines:
                    line_text = ""
                    for span in line.get("spans", []):
                        span_text = span.get("text", "")
                        line_text += span_text
                        f_size = span.get("size", 0.0)
                        f_flags = span.get("flags", 0)

                        if f_size > max_font_size:
                            max_font_size = f_size

                        # flag & 2 => bold flag
                        if (f_flags & 2) != 0 or "bold" in span.get("font", "").lower():
                            has_bold = True

                    full_block_text += line_text + "\n"

                full_block_text = full_block_text.strip()
                if not full_block_text:
                    continue

                # Tür Sınıflandırma Mantığı (Classification Logic)
                element_type: LayoutElementType = cls._classify_text_block(
                    text=full_block_text,
                    font_size=max_font_size,
                    baseline_font_size=baseline_font_size,
                    is_bold=has_bold,
                )

                elements.append(
                    LayoutElement(
                        element_type=element_type,
                        content=full_block_text,
                        page=page_num,
                        bbox=block_bbox,
                        font_size=max_font_size,
                        is_bold=has_bold,
                    )
                )

        doc.close()
        return [e.to_dict() for e in elements]

    @classmethod
    def _classify_text_block(
        cls,
        text: str,
        font_size: float,
        baseline_font_size: float,
        is_bold: bool,
    ) -> LayoutElementType:
        """Metin bloğunu font, biçim ve içeriğine göre etiketler."""
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        line_count = len(lines)
        char_count = len(text)

        # 1. Formül Tespiti
        if cls.FORMULA_PATTERNS.search(text) and char_count < 150:
            return "formula"

        # 2. Başlık (Heading) Tespiti: Font boyutu baseline'dan %15 büyükse VEYA kısa & koyu (bold) ise
        is_significantly_larger = font_size >= (baseline_font_size * 1.15)
        is_short_text = line_count <= 2 and char_count < 120

        if (is_significantly_larger and is_short_text) or (is_bold and is_short_text and font_size >= baseline_font_size):
            return "heading"

        # 3. Varsayılan: Metin Bloğu (Text)
        return "text"

    @classmethod
    def _calculate_baseline_font_size(cls, doc: pymupdf.Document, pages_to_process: int) -> float:
        """Belgedeki varsayılan gövde (body) metni ortalama font boyutunu hesaplar."""
        font_sizes: list[float] = []
        for i in range(pages_to_process):
            page_dict = doc[i].get_text("dict")
            for block in page_dict.get("blocks", []):
                if block.get("type") == 0:
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            text = span.get("text", "").strip()
                            if len(text) > 10:
                                font_sizes.append(span.get("size", 10.0))

        if not font_sizes:
            return 10.0

        font_sizes.sort()
        # Medyan font boyutu
        mid = len(font_sizes) // 2
        return font_sizes[mid]

    @staticmethod
    def _is_inside_any_bbox(bbox: tuple[float, float, float, float] | None, target_bboxes: list[tuple[float, float, float, float]]) -> bool:
        if not bbox:
            return False
        x0, y0, x1, y1 = bbox
        for tb in target_bboxes:
            tx0, ty0, tx1, ty1 = tb
            # Çakışma veya tamamen kapsanma kontrolü
            if x0 >= tx0 - 2 and y0 >= ty0 - 2 and x1 <= tx1 + 2 and y1 <= ty1 + 2:
                return True
        return False
