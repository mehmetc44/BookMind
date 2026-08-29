"""ai.services.layout_parser — Ham Fiziksel Öğeleri (Başlık, Yazı, Görsel, Tablo, Formül) Etiketleyen ve Birleştiren 'Gözlemci' Motoru."""

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
    """PDF belgesini tarayıp tür bazlı fiziki etiketleme ve kural tabanlı birleştirme (Aggregation) yapan motor."""

    FORMULA_PATTERNS = re.compile(
        r"[\u2200-\u22FF\u2A00-\u2AFF]|\b(lim|sum|int|sqrt|log|sin|cos|tan)\b|\b[a-zA-Z]\s*=\s*[-+]?\d+|\b\d+\s*[\+\-\*/=]\s*\d+|\b\w+_\{\w+\}|\b\w+\^\{\w+\}",
        re.IGNORECASE,
    )

    FORM_FIELD_PATTERNS = re.compile(
        r"^(sayı|konu|tarih|t\.c\.|tel|faks|e-posta|adres|evrak)\s*[:\.]",
        re.IGNORECASE,
    )

    @classmethod
    def parse_pdf_layout(cls, pdf_path: str | Path, max_pages: int | None = None) -> list[dict[str, Any]]:
        """PDF dosyasını tarar, kural tabanlı birleştirme ve sahte başlık filtresi uygulayarak etiketlenmiş elemanlar listesi döndürür."""
        doc = pymupdf.open(str(pdf_path))
        total_pages = len(doc)
        pages_to_process = min(max_pages, total_pages) if max_pages else total_pages

        baseline_font_size = cls._calculate_baseline_font_size(doc, pages_to_process)
        elements: list[LayoutElement] = []

        for page_idx in range(pages_to_process):
            page_num = page_idx + 1
            page = doc[page_idx]

            # 1. Tablolar
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

            # 2. Görseller
            for img_info in page.get_image_info(hashes=False):
                img_bbox = img_info.get("bbox")
                if img_bbox:
                    elements.append(
                        LayoutElement(
                            element_type="image",
                            content=f"[Görsel: Sayfa {page_num}, BBox {img_bbox}]",
                            page=page_num,
                            bbox=img_bbox,
                            meta={"image_info": img_info.get("number", 0)},
                        )
                    )

            # 3. Metin Blokları
            text_page_dict = page.get_text("dict")
            for block in text_page_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue

                block_bbox = block.get("bbox")
                if cls._is_inside_any_bbox(block_bbox, table_bboxes):
                    continue

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

                        if (f_flags & 2) != 0 or "bold" in span.get("font", "").lower():
                            has_bold = True

                    full_block_text += line_text + "\n"

                full_block_text = full_block_text.strip()
                if not full_block_text:
                    continue

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

        # 4. Aşama: Kural Tabanlı Birleştirme ve Filtreleme (Aggregation & Post-Processing)
        processed_elements = cls._post_process_elements(elements)
        return [e.to_dict() for e in processed_elements]

    @classmethod
    def _post_process_elements(cls, raw_elements: list[LayoutElement]) -> list[LayoutElement]:
        """Ardışık bölünen başlıkları birleştirir, sahte başlıkları düzeltir ve çakışan görselleri teke indirir."""
        if not raw_elements:
            return []

        # 1. Adım: Çakışan / Şeffaf Maske Resimlerini Birleştir (Image Deduplication)
        elements_step1: list[LayoutElement] = []
        for el in raw_elements:
            if el.type == "image" and el.bbox:
                # Aynı sayfadaki benzer / üst üste çakışan resmi kontrol et
                is_duplicate = False
                for existing in elements_step1:
                    if existing.type == "image" and existing.page == el.page and existing.bbox:
                        if cls._bboxes_overlap_significantly(el.bbox, existing.bbox):
                            is_duplicate = True
                            break
                if not is_duplicate:
                    elements_step1.append(el)
            else:
                elements_step1.append(el)

        # 2. Adım: Sahte Başlık Filtresi (Pseudo-Heading Demotion)
        elements_step2: list[LayoutElement] = []
        for el in elements_step1:
            if el.type == "heading":
                content_clean = el.content.strip()

                # Form alanı kalıbı mı? (Sayı :, Konu :, Tarih :)
                if cls.FORM_FIELD_PATTERNS.search(content_clean):
                    el.type = "text"

                # Çok mu uzun VEYA noktalı cümle mi?
                elif len(content_clean) > 130 or (len(content_clean) > 55 and content_clean.endswith((".", ";"))):
                    el.type = "text"

            elements_step2.append(el)

        # 3. Adım: Ardışık Bölünmüş Başlıkları Birleştir (Split Heading Aggregation)
        merged_elements: list[LayoutElement] = []
        idx = 0
        n = len(elements_step2)

        while idx < n:
            curr = elements_step2[idx]

            # Ardışık iki heading ve dikey mesafe yakınsa birleştir
            if curr.type == "heading" and idx + 1 < n:
                next_el = elements_step2[idx + 1]

                if next_el.type == "heading" and next_el.page == curr.page:
                    # Dikey mesafe kontrolü (Vertical proximity check)
                    gap = 0.0
                    if curr.bbox and next_el.bbox:
                        gap = next_el.bbox[1] - curr.bbox[3]

                    font_diff = abs(curr.font_size - next_el.font_size)

                    # Aralarındaki mesafe 20px'ten azsa ve font boyutları yakınsa birleştir
                    if gap < 20.0 and font_diff < 3.5:
                        merged_content = f"{curr.content} {next_el.content}".strip()
                        new_bbox = None
                        if curr.bbox and next_el.bbox:
                            new_bbox = (
                                min(curr.bbox[0], next_el.bbox[0]),
                                min(curr.bbox[1], next_el.bbox[1]),
                                max(curr.bbox[2], next_el.bbox[2]),
                                max(curr.bbox[3], next_el.bbox[3]),
                            )

                        curr = LayoutElement(
                            element_type="heading",
                            content=merged_content,
                            page=curr.page,
                            bbox=new_bbox,
                            font_size=max(curr.font_size, next_el.font_size),
                            is_bold=curr.is_bold or next_el.is_bold,
                            meta=curr.meta,
                        )
                        idx += 1  # Bir sonraki el atlandı

            merged_elements.append(curr)
            idx += 1

        return merged_elements

    @classmethod
    def _classify_text_block(
        cls,
        text: str,
        font_size: float,
        baseline_font_size: float,
        is_bold: bool,
    ) -> LayoutElementType:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        line_count = len(lines)
        char_count = len(text)

        if cls.FORMULA_PATTERNS.search(text) and char_count < 150:
            return "formula"

        is_significantly_larger = font_size >= (baseline_font_size * 1.15)
        is_short_text = line_count <= 2 and char_count < 120

        if (is_significantly_larger and is_short_text) or (is_bold and is_short_text and font_size >= baseline_font_size):
            return "heading"

        return "text"

    @classmethod
    def _calculate_baseline_font_size(cls, doc: pymupdf.Document, pages_to_process: int) -> float:
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
        mid = len(font_sizes) // 2
        return font_sizes[mid]

    @staticmethod
    def _is_inside_any_bbox(bbox: tuple[float, float, float, float] | None, target_bboxes: list[tuple[float, float, float, float]]) -> bool:
        if not bbox:
            return False
        x0, y0, x1, y1 = bbox
        for tb in target_bboxes:
            tx0, ty0, tx1, ty1 = tb
            if x0 >= tx0 - 2 and y0 >= ty0 - 2 and x1 <= tx1 + 2 and y1 <= ty1 + 2:
                return True
        return False

    @staticmethod
    def _bboxes_overlap_significantly(b1: tuple[float, float, float, float], b2: tuple[float, float, float, float]) -> bool:
        """İki BBox'ın birbiriyle dikey/yatayda %60'tan fazla çakışıp çakışmadığını hesaplar."""
        x0_1, y0_1, x1_1, y1_1 = b1
        x0_2, y0_2, x1_2, y1_2 = b2

        inter_x0 = max(x0_1, x0_2)
        inter_y0 = max(y0_1, y0_2)
        inter_x1 = min(x1_1, x1_2)
        inter_y1 = min(y1_1, y1_2)

        if inter_x1 <= inter_x0 or inter_y1 <= inter_y0:
            return False

        inter_area = (inter_x1 - inter_x0) * (inter_y1 - inter_y0)
        area1 = (x1_1 - x0_1) * (y1_1 - y0_1)
        area2 = (x1_2 - x0_2) * (y1_2 - y0_2)

        if area1 <= 0 or area2 <= 0:
            return False

        ratio1 = inter_area / area1
        ratio2 = inter_area / area2

        return ratio1 > 0.60 or ratio2 > 0.60
