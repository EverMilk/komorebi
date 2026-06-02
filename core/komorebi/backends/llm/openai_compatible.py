"""An OpenAI-compatible chat backend (works with OpenAI, Codex endpoints, and any
server speaking the /chat/completions API such as Ollama or vLLM).

Configured purely by environment variables so no secrets live in code:

    KOMOREBI_LLM=openai
    OPENAI_API_KEY=sk-...
    OPENAI_BASE_URL=https://api.openai.com/v1   # override for Codex / Ollama / vLLM
    OPENAI_MODEL=gpt-4o-mini

This is a thin reference implementation; it streams Server-Sent Events from the
chat completions endpoint. Kept dependency-light (httpx only).
"""

from __future__ import annotations

import json
import os
from typing import AsyncIterator

import httpx

from .base import Message


class OpenAICompatibleBackend:
    name = "openai"

    def __init__(self) -> None:
        self._api_key = os.environ.get("OPENAI_API_KEY", "")
        self._base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
        self._model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    async def reply(self, system_prompt: str, history: list[Message]) -> AsyncIterator[str]:
        if not self._api_key:
            yield "(OPENAI_API_KEY が未設定だよ。デモモードに戻すなら KOMOREBI_LLM=echo を使ってね)"
            return

        messages: list[Message] = [{"role": "system", "content": system_prompt}, *history]
        payload = {"model": self._model, "messages": messages, "stream": True}
        headers = {"Authorization": f"Bearer {self._api_key}"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream(
                "POST", f"{self._base_url}/chat/completions", json=payload, headers=headers
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0]["delta"].get("content")
                    except (KeyError, IndexError, json.JSONDecodeError):
                        continue
                    if delta:
                        yield delta
