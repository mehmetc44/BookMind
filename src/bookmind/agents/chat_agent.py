"""ChatAgent — Kullanıcı sorularına cevap veren agent.

Global / tekil nesne olarak kullanılır, böylece her istekte LLM nesnesi
ve HTTP oturumu yeniden oluşturulmaz (Ollama yeniden yükleme yapmaz).
"""

from __future__ import annotations

from bookmind.agents.base_agent import BaseAgent
from bookmind.core.config import Config, LLMProvider


class ChatAgent(BaseAgent):
    """BookMind Sohbet Asistanı Agent'ı."""

    system_prompt = (
        "Sen BookMind adlı sohbet asistanısın. "
        "Kullanıcının mesajlarını samimi, anlaşılır ve doğrudan Türkçe olarak yanıtla."
    )

    def __init__(self) -> None:
        super().__init__(temperature=0.7)

    async def ask(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Kullanıcı mesajını yanıtlar.

        Args:
            message: Kullanıcının gönderdiği soru/mesaj.
            history: Önceki sohbet geçmişi.

        Returns:
            Modelin yanıt metni.
        """
        return await self.ainvoke(
            user_message=message,
            history=history,
        )

    async def ask_stream(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
    ):
        """Kullanıcı mesajına akışlı (streaming) yanıt üretir."""
        async for chunk in self.astream(
            user_message=message,
            history=history,
        ):
            yield chunk


# Global singleton agent instance'ı — her istekte nesne oluşturmayı engeller!
_chat_agent_instance: ChatAgent | None = None


def get_chat_agent() -> ChatAgent:
    """Singleton ChatAgent nesnesi döndürür."""
    global _chat_agent_instance
    if _chat_agent_instance is None:
        _chat_agent_instance = ChatAgent()
    return _chat_agent_instance
