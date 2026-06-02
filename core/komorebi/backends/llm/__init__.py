"""LLM backend registry / factory.

Add a backend by importing its class and registering it in ``_REGISTRY``.
"""

from __future__ import annotations

from .base import LLMBackend, Message
from .echo import EchoBackend
from .openai_compatible import OpenAICompatibleBackend

_REGISTRY: dict[str, type] = {
    EchoBackend.name: EchoBackend,
    OpenAICompatibleBackend.name: OpenAICompatibleBackend,
}


def create_llm(name: str) -> LLMBackend:
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown LLM backend '{name}'. Available: {available}")
    return cls()


__all__ = ["LLMBackend", "Message", "create_llm"]
