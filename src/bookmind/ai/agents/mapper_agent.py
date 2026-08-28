"""BookMind.AI.agents.mapper_agent — Ham TOC metnini BookMap JSON yapısına dönüştüren ajan."""

from __future__ import annotations

import json
import re

from bookmind.ai.agents.base_agent import BaseAgent
from bookmind.shared import BookMap


class MapperAgent(BaseAgent):
    """Ham içindekiler metnini yapılandırılmış BookMap JSON nesnesine dönüştürür."""

    system_prompt: str = (
        "Sen uzman bir kitap analiz ve haritalama asistanısın. "
        "Görevin: Verilen ham içindekiler metnini (TOC) analiz edip, kitabın bölüm yapısını "
        "Pydantic JSON şemasına %100 uygun olarak çıkarmaktır.\n\n"
        "Şu kurallara KESİNLİKLE uy:\n"
        "1. Yalnızca geçerli bir JSON nesnesi döndür. Açıklama, markdown kodu veya <think> etiketi EKLEME.\n"
        "2. Her bölüm için id (örn: chapter_1), title, page_start, page_end, summary (Türkçe 1-2 cümlelik kısa özet), "
        "topics (3-5 ana konu) ve keywords (3-5 teknik anahtar kelime) alanlarını üret.\n"
        "3. Yanıtın tam olarak aşağıdaki JSON şemasına uymalıdır:\n"
        "{\n"
        '  "book_title": "Kitap Adı",\n'
        '  "author": "Yazar Adı",\n'
        '  "total_pages": 100,\n'
        '  "chapters": [\n'
        "    {\n"
        '      "id": "chapter_1",\n'
        '      "title": "Bölüm Başlığı",\n'
        '      "page_start": 1,\n'
        '      "page_end": 15,\n'
        '      "summary": "Türkçe kısa özet",\n'
        '      "topics": ["konu1", "konu2"],\n'
        '      "keywords": ["keyword1", "keyword2"],\n'
        '      "children": []\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    async def map(self, toc_text: str, total_pages: int) -> BookMap:
        """Ham TOC metnini BookMap Pydantic nesnesine dönüştürür."""
        user_prompt = (
            f"Toplam Sayfa Sayısı: {total_pages}\n\n"
            f"HAM İÇİNDEKİLER METNİ:\n{toc_text}\n\n"
            f"Yukarıdaki metni analiz et ve JSON şemasına uygun haritayı üret."
        )

        raw_response = await self.ainvoke(user_message=user_prompt)

        # JSON temizleme
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
        """Markdown kod bloklarını ve ekstra metinleri temizleyerek ham JSON döndürür."""
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return match.group(0)
        return text.strip()
