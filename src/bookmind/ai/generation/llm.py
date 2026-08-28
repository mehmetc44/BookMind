"""ai.generation.llm — BaseAgent, ChatAgent, and MapperAgent logic using LangChain."""

from __future__ import annotations

import json
import re
from typing import Any
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from bookmind.domain.books.entities import BookMap
from bookmind.infrastructure.configuration.settings import Settings, LLMProvider


class BaseAgent:
    """Tüm BookMind agent'larının temel sınıfı."""

    system_prompt: str = "Sen BookMind adlı bir kitap analiz asistanısın."

    def __init__(
        self,
        model: str | None = None,
        temperature: float = Settings.DEEPSEEK_TEMPERATURE,
        max_tokens: int = Settings.DEEPSEEK_MAX_TOKENS,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or Settings.LLM_PROVIDER
        self.model = model or (
            Settings.DEEPSEEK_DEFAULT_MODEL
            if self.provider == LLMProvider.DEEPSEEK
            else Settings.OLLAMA_MODEL
        )
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm: BaseChatModel | None = None

    @property
    def llm(self) -> BaseChatModel:
        """Seçilen LLMProvider'a göre Chat model instance'ı döndürür."""
        if self._llm is None:
            if self.provider == LLMProvider.OLLAMA:
                self._llm = ChatOllama(
                    model=self.model,
                    base_url=Settings.OLLAMA_BASE_URL,
                    temperature=self.temperature,
                    options={
                        "think": False,
                        "keep_alive": "24h",
                    },
                )
            else:
                if not Settings.DEEPSEEK_API_KEY:
                    raise ValueError(
                        "DEEPSEEK_API_KEY bulunamadı. "
                        ".env dosyasına eklediğinizden emin olun."
                    )
                self._llm = ChatOpenAI(
                    model=self.model,
                    api_key=Settings.DEEPSEEK_API_KEY,
                    base_url=Settings.DEEPSEEK_BASE_URL,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
        return self._llm

    def _build_messages(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        extra_context: str | None = None,
    ) -> list[dict[str, str]]:
        system_content = self.system_prompt
        if self.provider == LLMProvider.OLLAMA:
            system_content += "\nDo not use <think> tags. Answer directly."

        if extra_context:
            system_content += f"\n\n{extra_context}"

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content}
        ]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})
        return messages

    @staticmethod
    def _clean_response(text: str) -> str:
        if not text:
            return ""
        if "</think>" in text:
            text = text.split("</think>")[-1]
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
        return text.strip()

    def invoke(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        extra_context: str | None = None,
    ) -> str:
        messages = self._build_messages(user_message, history, extra_context)
        response = self.llm.invoke(messages)
        return self._clean_response(str(response.content))

    async def ainvoke(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        extra_context: str | None = None,
    ) -> str:
        messages = self._build_messages(user_message, history, extra_context)
        response = await self.llm.ainvoke(messages)
        return self._clean_response(str(response.content))

    async def astream(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        extra_context: str | None = None,
    ):
        messages = self._build_messages(user_message, history, extra_context)

        if self.provider == LLMProvider.OLLAMA:
            import ollama

            client = ollama.AsyncClient(host=Settings.OLLAMA_BASE_URL)
            async for chunk in await client.chat(
                model=self.model,
                messages=messages,
                stream=True,
                think=False,
                keep_alive="24h",
            ):
                content = chunk.get("message", {}).get("content", "")
                if content:
                    yield content
        else:
            is_thinking = False
            async for chunk in self.llm.astream(messages):
                content = str(chunk.content)
                if not content:
                    continue
                if "<think>" in content:
                    is_thinking = True
                    continue
                if "</think>" in content:
                    is_thinking = False
                    content = content.split("</think>")[-1]
                    if not content:
                        continue
                if not is_thinking:
                    yield content


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


class ChatAgent(BaseAgent):
    """Kullanıcı sorularını yanıtlayan sohbet ajanı."""

    system_prompt: str = (
        "Sen BookMind platformunun akıllı kitap asistanısın. "
        "Kullanıcının sorduğu soruları nazik, açıklayıcı ve doğru bir dille Türkçe yanıtla. "
        "Eğer sana bir kitap haritası veya bağlam verildiyse, öncelikle o bağlama sadık kalarak cevap ver. "
        "Yanıtında <think> etiketlerini KESİNLİKLE kullanma, doğrudan nihai yanıtı ver."
    )
