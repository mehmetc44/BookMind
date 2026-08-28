"""BookMind.AI.agents.chat_agent — Kullanıcı sorularını yanıtlayan sohbet ajanı."""

from __future__ import annotations

from bookmind.ai.agents.base_agent import BaseAgent
from bookmind.shared import Config, LLMProvider


class ChatAgent(BaseAgent):
    """Kullanıcı sorularını yanıtlayan sohbet ajanı."""

    system_prompt: str = (
        "Sen BookMind platformunun akıllı kitap asistanısın. "
        "Kullanıcının sorduğu soruları nazik, açıklayıcı ve doğru bir dille Türkçe yanıtla. "
        "Eğer sana bir kitap haritası veya bağlam verildiyse, öncelikle o bağlama sadık kalarak cevap ver. "
        "Yanıtında <think> etiketlerini KESİNLİKLE kullanma, doğrudan nihai yanıtı ver."
    )

    async def run(
        self,
        message: str,
        book_id: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Kullanıcı mesajına yanıt üretir."""
        extra_context = None

        if book_id:
            from bookmind.api.storage import MapRepository

            map_data = MapRepository.get_book_map(book_id)
            if map_data and "book_map" in map_data:
                extra_context = (
                    f"AKTİF KİTAP HARİTASI BILGILERI:\n"
                    f"{map_data['book_map']}"
                )

        return await self.ainvoke(
            user_message=message,
            history=history,
            extra_context=extra_context,
        )


def get_chat_agent() -> ChatAgent:
    """Tekil ChatAgent instance'ı döndürür."""
    return ChatAgent()
