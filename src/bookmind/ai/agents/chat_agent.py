"""ai.agents.chat_agent — Agentic Chat Agent with search_book_context tool support."""

from __future__ import annotations

from typing import Any, AsyncGenerator
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from bookmind.ai.agents.base_agent import BaseAgent
from bookmind.ai.prompts.chat_agent_prompt import CHAT_AGENT_SYSTEM_PROMPT
from bookmind.ai.tools import search_book_context


class ChatAgent(BaseAgent):
    """Arama araçlarını (tools) dinamik olarak kullanarak soruları yanıtlayan Agentic RAG sohbet ajanı."""

    system_prompt = CHAT_AGENT_SYSTEM_PROMPT

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.tools = [search_book_context]
        self._tools_map = {t.name: t for t in self.tools}

    async def run_agentic(
        self,
        user_message: str,
        book_id: str | None = None,
        history: list[dict[str, str]] | None = None,
        max_turns: int = 5,
    ) -> str:
        """Agentic döngü: Sorguyu alır, model gerek görürse search_book_context tool'unu çağırır, sonuçları sentezleyip yanıtı üretir."""
        try:
            llm_with_tools = self.llm.bind_tools(self.tools)
        except Exception:
            llm_with_tools = self.llm

        system_text = self.system_prompt
        if book_id:
            system_text += f"\n\nAKTİF KİTAP ID: {book_id}"

        messages: list[Any] = [SystemMessage(content=system_text)]

        if history:
            for h in history:
                role = h.get("role", "user")
                content = h.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=user_message))

        for turn in range(max_turns):
            response = await llm_with_tools.ainvoke(messages)
            messages.append(response)

            tool_calls = getattr(response, "tool_calls", [])
            if not tool_calls:
                return self._clean_response(str(response.content))

            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", f"call_{turn}")

                if "book_id" in tool_args and not tool_args["book_id"] and book_id:
                    tool_args["book_id"] = book_id
                elif "book_id" not in tool_args and book_id:
                    tool_args["book_id"] = book_id

                print(f"🛠️ [ChatAgent Agentic Tool Call] Tool: '{tool_name}', Args: {tool_args}")

                target_tool = self._tools_map.get(tool_name)
                if target_tool:
                    tool_output = target_tool.invoke(tool_args)
                else:
                    tool_output = f"Tool '{tool_name}' bulunamadı."

                messages.append(
                    ToolMessage(
                        content=str(tool_output),
                        tool_call_id=tool_call_id,
                        name=tool_name,
                    )
                )

        return self._clean_response(str(messages[-1].content))

    async def stream_agentic(
        self,
        user_message: str,
        book_id: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> AsyncGenerator[str, None]:
        """Canlı streaming destekli Agentic RAG çalıştırıcı."""
        full_reply = await self.run_agentic(
            user_message=user_message,
            book_id=book_id,
            history=history,
        )
        yield full_reply
