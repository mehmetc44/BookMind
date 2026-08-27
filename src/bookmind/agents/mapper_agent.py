"""MapperAgent — PDF içindekilerinden kitap haritası oluşturur.

BaseAgent'tan türer. Tek sorumluluğu:
TOC metnini alıp BookMap JSON yapısına dönüştürmek.
"""

from __future__ import annotations

import json
import re

from bookmind.agents.base_agent import BaseAgent
from bookmind.core.schemas.book import BookMap


class MapperAgent(BaseAgent):
    """PDF içindekiler metnini yapısal kitap haritasına dönüştüren agent.

    Kullanım:
        agent = MapperAgent()
        book_map = await agent.map(toc_text="...", total_pages=350)
    """

    system_prompt = """Sen bir kitap yapısı analiz asistanısın.
Sana verilen içindekiler metni veya sayfa içeriğinden kitabın yapısal haritasını çıkarıyorsun.

ÇIKTI FORMATI — Sadece aşağıdaki valid JSON döndür, başka hiçbir şey yazma:
{
  "book_title": "Kitabın tam başlığı",
  "author": "Yazar adı (bilinmiyorsa 'Bilinmiyor')",
  "total_pages": <int>,
  "chapters": [
    {
      "id": "chapter_1",
      "title": "1. Bölüm Başlığı",
      "page_start": <int>,
      "page_end": <int>,
      "summary": "Bu bölüm hakkında 1-2 cümlelik Türkçe özet.",
      "topics": ["konu1", "konu2"],
      "keywords": ["keyword1", "keyword2"],
      "children": [
        {
          "id": "chapter_1_1",
          "title": "1.1 Alt Bölüm",
          "page_start": <int>,
          "page_end": <int>,
          "summary": "Alt bölüm özeti.",
          "topics": [],
          "keywords": [],
          "children": []
        }
      ]
    }
  ]
}

KURALLAR:
1. Her düzey için benzersiz id: chapter_1, chapter_1_1, chapter_1_1_1 vb.
2. Alt bölümleri children dizisine koy, iç içe yapıyı koru
3. Sayfa numaralarını içindekilerden al; yoksa mantıklı tahmin et
4. summary alanını Türkçe, kısa ve bilgilendirici yaz
5. topics → Türkçe konular, keywords → teknik/İngilizce terimler
6. Sadece valid JSON döndür — markdown blok (```) veya açıklama ekleme"""

    def __init__(self) -> None:
        # Haritalama deterministik olsun diye temperature=0
        super().__init__(temperature=0, max_tokens=8000)

    async def map(self, toc_text: str, total_pages: int) -> BookMap:
        """TOC metninden BookMap oluşturur.

        Args:
            toc_text: PDF'den çekilen içindekiler metni.
            total_pages: Kitabın toplam sayfa sayısı.

        Returns:
            Validate edilmiş BookMap nesnesi.

        Raises:
            ValueError: JSON parse veya Pydantic doğrulama hatası.
        """
        user_message = (
            f"Aşağıdaki içindekiler bilgisinden kitabın yapısal haritasını oluştur.\n"
            f"Toplam sayfa sayısı: {total_pages}\n\n"
            f"İÇERİK:\n{toc_text}"
        )

        raw_response = await self.ainvoke(user_message)
        return self._parse_response(raw_response, total_pages)

    def _parse_response(self, raw: str, total_pages: int) -> BookMap:
        """LLM yanıtını temizleyip BookMap'e dönüştürür.

        Args:
            raw: Modelin ham metin yanıtı.
            total_pages: Doğrulama için toplam sayfa sayısı.

        Returns:
            BookMap nesnesi.

        Raises:
            ValueError: JSON geçersiz veya model uyumsuz yapı döndürdü.
        """
        # Markdown code fence varsa temizle (```json ... ```)
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
        cleaned = cleaned.strip()

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Model geçersiz JSON döndürdü: {e}\n"
                f"Ham yanıt (ilk 500 karakter):\n{raw[:500]}"
            ) from e

        # total_pages'i garantile
        if not data.get("total_pages"):
            data["total_pages"] = total_pages

        try:
            return BookMap(**data)
        except Exception as e:
            raise ValueError(f"BookMap doğrulama hatası: {e}") from e
