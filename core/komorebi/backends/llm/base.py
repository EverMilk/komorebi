"""The LLM backend contract.

A backend is anything that can turn (persona prompt + conversation) into a reply.
Implementations are intentionally tiny so contributors can add OpenAI / Codex /
Claude / Ollama support by writing one class. The ``echo`` reference backend needs
no external service so the demo works out of the box.
"""

from __future__ import annotations

from typing import AsyncIterator, Protocol, runtime_checkable

# A single turn in the conversation: {"role": "user"|"assistant"|"system", "content": str}
Message = dict[str, str]


@runtime_checkable
class LLMBackend(Protocol):
    name: str

    async def reply(self, system_prompt: str, history: list[Message]) -> AsyncIterator[str]:
        """Yield reply text incrementally (token/chunk streaming).

        Implementations should ``yield`` partial strings so the orchestrator can
        stream subtitles. A non-streaming backend may simply yield once.
        """
        ...
