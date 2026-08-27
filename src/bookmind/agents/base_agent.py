"""BaseAgent — Tüm agent'ların türeyeceği temel sınıf.

DeepSeek API bağlantısını, LLM yapılandırmasını ve
temel invoke/ainvoke metodlarını sağlar.
"""

from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI

from bookmind.core.config import Config


class BaseAgent:
    """Tüm BookMind agent'larının temel sınıfı.

    Kullanım:
        class MyAgent(BaseAgent):
            system_prompt = "Sen bir..."

            async def run(self, input: str) -> str:
                messages = self._build_messages(input)
                return await self.ainvoke(messages)
    """

    # Alt sınıflar bu değeri override eder
    system_prompt: str = "Sen BookMind adlı bir kitap analiz asistanısın."

    def __init__(
        self,
        model: str = Config.DEEPSEEK_DEFAULT_MODEL,
        temperature: float = Config.DEEPSEEK_TEMPERATURE,
        max_tokens: int = Config.DEEPSEEK_MAX_TOKENS,
    ) -> None:
        """
        Args:
            model: Kullanılacak model adı (ör: "deepseek-chat").
            temperature: Yaratıcılık seviyesi (0 = deterministik).
            max_tokens: Maksimum çıktı token sayısı.
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._llm: ChatOpenAI | None = None

    @property
    def llm(self) -> ChatOpenAI:
        """Lazy-init LLM instance'ı döndürür."""
        if self._llm is None:
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
        if extra_context:
            system_content += f"\n\n{extra_context}"

        messages: list[dict[str, str]] = [
            {"role": "system", "content": system_content}
        ]

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})
        return messages

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
        return str(response.content)

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
        return str(response.content)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"model={self.model!r}, "
            f"temperature={self.temperature})"
        )
