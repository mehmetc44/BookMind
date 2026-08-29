"""ai.agents.hierarchy_extractor_agent — Agent that extracts hierarchical BookMap trees from header-tagged layout elements."""

from __future__ import annotations

import json
import re
from typing import Any

from bookmind.ai.agents.base_agent import BaseAgent
from bookmind.ai.prompts.hierarchy_extractor_prompt import HIERARCHY_EXTRACTOR_SYSTEM_PROMPT
from bookmind.domain.books.entities import BookMap


class HierarchyExtractorAgent(BaseAgent):
    """Düzensiz ve hiyerarşisi bozuk PDF'lerin etiketlenmiş 'header' elemanlarını analiz ederek mantıklı bir BookMap hiyerarşi ağacı üretir."""

    system_prompt = HIERARCHY_EXTRACTOR_SYSTEM_PROMPT

    async def extract_hierarchy(self, headings_input: str | list[dict[str, Any]], total_pages: int) -> BookMap:
        """Etiketli header verisini BookMap Pydantic nesnesine dönüştürür."""
        if isinstance(headings_input, list):
            # Header listesini düzenli metin formatına getir
            lines = []
            for h in headings_input:
                if h.get("type") == "heading":
                    lines.append(f"Sayfa {h.get('page')} [Font {h.get('font_size')}pt]: {h.get('content')}")
            formatted_text = "\n".join(lines) if lines else str(headings_input)
        else:
            formatted_text = headings_input

        user_prompt = (
            f"Toplam Sayfa Sayısı: {total_pages}\n\n"
            f"ETİKETLENMİŞ BAŞLIK (HEADER) DİZİSİ:\n{formatted_text}\n\n"
            f"Yukarıdaki etiketli başlıkları analiz et ve mantıklı bir başlık/bölüm hiyerarşi ağacı üret."
        )

        raw_response = await self.ainvoke(user_message=user_prompt)
        cleaned_json = self._clean_json_string(raw_response)

        try:
            data = json.loads(cleaned_json)
            if "total_pages" not in data or data["total_pages"] == 0:
                data["total_pages"] = total_pages
            return BookMap.model_validate(data)
        except Exception as e:
            raise ValueError(f"HierarchyExtractorAgent JSON çıktısı doğrulanamadı: {e}\nYanıt: {raw_response[:200]}")

    @staticmethod
    def _clean_json_string(text: str) -> str:
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)
        return text.strip()
