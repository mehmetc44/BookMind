"""ai.agents.chat_agent — Agent that responds to user chat queries using external prompts."""

from __future__ import annotations

from bookmind.ai.agents.base_agent import BaseAgent
from bookmind.ai.prompts.chat_agent_prompt import CHAT_AGENT_SYSTEM_PROMPT


class ChatAgent(BaseAgent):
    """Kullanıcı sorularını yanıtlayan sohbet ajanı."""

    system_prompt = CHAT_AGENT_SYSTEM_PROMPT
