"""The TTS backend contract.

A TTS backend turns text into audio plus (ideally) audio-aligned visemes. In M0 the
``silent`` reference backend returns no audio and lets the EmotionEngine generate
placeholder visemes, so the demo lip-syncs without any speech synthesis installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class SpeechResult:
    # Estimated duration in seconds (used to time placeholder visemes).
    duration: float
    # Optional audio payload. Empty in the silent demo backend.
    audio_format: str = ""
    audio_b64: str = ""
    # Optional audio-aligned visemes [(phoneme, t_seconds)]. Empty -> caller
    # falls back to EmotionEngine.visemes().
    visemes: list[tuple[str, float]] = field(default_factory=list)


@runtime_checkable
class TTSBackend(Protocol):
    name: str

    async def synthesize(self, text: str, voice: dict) -> SpeechResult:
        ...
