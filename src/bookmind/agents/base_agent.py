"""BaseAgent — Tüm agent'ların türeyeceği temel sınıf.

DeepSeek API bağlantısını, LLM yapılandırmasını ve
temel invoke/ainvoke metodlarını sağlar.
"""

from __future__ import annotations

from typing import Any
from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from bookmind.core.config import Config, LLMProvider


class BaseAgent:
    """Tüm BookMind agent'larının temel sınıfı."""

    system_prompt: str = "Sen BookMind adlı bir kitap analiz asistanısın."

    def __init__(
        self,
        model: str | None = None,
        temperature: float = Config.DEEPSEEK_TEMPERATURE,
        max_tokens: int = Config.DEEPSEEK_MAX_TOKENS,
        provider: LLMProvider | None = None,
    ) -> None:
        """
        Args:
            model: Özel model adı. None ise seçili provider'ın varsayılanı kullanılır.
            temperature: Yaratıcılık seviyesi.
            max_tokens: Maksimum çıktı token sayısı.
            provider: Sağlayıcı (DEEPSEEK veya OLLAMA). None ise Config.LLM_PROVIDER kullanılır.
        """
        self.provider = provider or Config.LLM_PROVIDER
        self.model = model or (
            Config.DEEPSEEK_DEFAULT_MODEL
            if self.provider == LLMProvider.DEEPSEEK
            else Config.OLLAMA_MODEL
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
                    base_url=Config.OLLAMA_BASE_URL,
                    temperature=self.temperature,
                    options={
                        "think": False,
                        "keep_alive": "24h",
                    },
                )
            else:
                if not Config.DEEPSEEK_API_KEY:
                    raise ValueError(
                        "DEEPSEEK_API_KEY bulunamadı. "
                        ".env dosyasına eklediğinizden emin olun."
                    )
                self._llm = ChatOpenAI(
                    model=self.model,
                    api_key=Config.DEEPSEEK_API_KEY,
                    base_url=Config.DEEPSEEK_BASE_URL,
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
        """Mesaj listesi oluşturur.

        Args:
            user_message: Kullanıcının sorusu/girdisi.
            history: Önceki mesajlar [{role, content}, ...].
            extra_context: Sistem promptuna ek bağlam (ör: kitap haritası).

        Returns:
            LLM'e gönderilecek mesaj listesi.
        """
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
        """Düşünme (think) etiketlerini ve iç düşünce bloklarını temizler."""
        if not text:
            return ""
        import re
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
        """Senkron LLM çağrısı yapar.

        Args:
            user_message: Kullanıcı mesajı.
            history: Konuşma geçmişi.
            extra_context: Ek sistem bağlamı.

        Returns:
            Modelin metin yanıtı.
        """
        messages = self._build_messages(user_message, history, extra_context)
        response = self.llm.invoke(messages)
        return self._clean_response(str(response.content))

    async def ainvoke(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        extra_context: str | None = None,
    ) -> str:
        """Asenkron LLM çağrısı yapar.

        Args:
            user_message: Kullanıcı mesajı.
            history: Konuşma geçmişi.
            extra_context: Ek sistem bağlamı.

        Returns:
            Modelin metin yanıtı.
        """
        messages = self._build_messages(user_message, history, extra_context)
        response = await self.llm.ainvoke(messages)
        return self._clean_response(str(response.content))

    async def astream(
        self,
        user_message: str,
        history: list[dict[str, str]] | None = None,
        extra_context: str | None = None,
    ):
        """Asenkron akışlı (streaming) LLM çağrısı yapar.

        Args:
            user_message: Kullanıcı mesajı.
            history: Konuşma geçmişi.
            extra_context: Ek sistem bağlamı.

        Yields:
            Modelin ürettiği metin parçaları (chunks).
        """
        messages = self._build_messages(user_message, history, extra_context)

        if self.provider == LLMProvider.OLLAMA:
            import ollama
            client = ollama.AsyncClient(host=Config.OLLAMA_BASE_URL)
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

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"model={self.model!r}, "
            f"temperature={self.temperature})"
        )
