"""ai.agents.mapper_agent — Agent that maps raw TOC into a structural BookMap JSON using external prompts."""

from __future__ import annotations

import json
import re

from bookmind.ai.agents.base_agent import BaseAgent
from bookmind.ai.prompts.mapper_agent_prompt import MAPPER_AGENT_SYSTEM_PROMPT
from bookmind.domain.books.entities import BookMap


class MapperAgent(BaseAgent):
    """Ham içindekiler metnini yapılandırılmış BookMap JSON nesnesine dönüştürür."""

    system_prompt = MAPPER_AGENT_SYSTEM_PROMPT

    async def map(self, toc_text: str, total_pages: int) -> BookMap:
        """Ham TOC metnini BookMap Pydantic nesnesine dönüştürür."""
        user_prompt = (
            f"Toplam Sayfa Sayısı: {total_pages}\n\n"
            f"HAM İÇİNDEKİLER METNİ:\n{toc_text}\n\n"
            f"Yukarıdaki metni analiz et ve JSON şemasına uygun haritayı üret."
        )

        raw_response = await self.ainvoke(user_message=user_prompt)
        cleaned_json = self._clean_json_string(raw_response)

        try:
            data = json.loads(cleaned_json)
            if "total_pages" not in data or data["total_pages"] == 0:
                data["total_pages"] = total_pages
            return BookMap.model_validate(data)
        except Exception as e:
            raise ValueError(f"MapperAgent JSON çıktısı doğrulanamadı: {e}\nYanıt: {raw_response[:200]}")

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
