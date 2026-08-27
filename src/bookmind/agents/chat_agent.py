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
        "Sen BookMind adlı bir kitap analiz asistanısın. "
        "Kitaplar ve okuma hakkındaki soruları doğrudan Türkçe yanıtla. "
        "Düşünme adımlarını (think) yazma."
    )

    def __init__(self) -> None:
        super().__init__(temperature=0.7)

    async def ask(
        self,
        message: str,
        book_map: dict | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Kullanıcı mesajını yanıtlar.

        Args:
            message: Kullanıcının gönderdiği soru/mesaj.
            book_map: Seçili kitabın yapısal haritası (varsa).
            history: Önceki sohbet geçmişi.

        Returns:
            Modelin yanıt metni.
        """
        extra_context = None
        if book_map:
            import json
            book_context = json.dumps(book_map, ensure_ascii=False, indent=2)
            extra_context = (
                "Kullanıcının seçtiği kitabın yapısal haritası aşağıda verilmiştir. "
                "Bu haritayı kullanarak kitap hakkındaki soruları yanıtla.\n\n"
                f"KİTAP HARİTASI:\n```json\n{book_context}\n```"
            )

        return await self.ainvoke(
            user_message=message,
            history=history,
            extra_context=extra_context,
        )


# Global singleton agent instance'ı — her istekte nesne oluşturmayı engeller!
_chat_agent_instance: ChatAgent | None = None


def get_chat_agent() -> ChatAgent:
    """Singleton ChatAgent nesnesi döndürür."""
    global _chat_agent_instance
    if _chat_agent_instance is None:
        _chat_agent_instance = ChatAgent()
    return _chat_agent_instance
