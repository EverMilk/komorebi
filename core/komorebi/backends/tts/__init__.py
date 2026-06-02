"""TTS backend registry / factory."""

from __future__ import annotations

from .base import SpeechResult, TTSBackend
from .silent import SilentBackend

_REGISTRY: dict[str, type] = {
    SilentBackend.name: SilentBackend,
}


def create_tts(name: str) -> TTSBackend:
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown TTS backend '{name}'. Available: {available}")
    return cls()


__all__ = ["SpeechResult", "TTSBackend", "create_tts"]
