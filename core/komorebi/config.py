"""Runtime configuration, sourced from environment variables.

Defaults are chosen so that ``python -m komorebi`` works with zero external
services — the "try in 30 seconds" promise.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    host: str = "127.0.0.1"
    port: int = 8000
    llm_backend: str = "echo"
    tts_backend: str = "silent"
    emotion_backend: str = "heuristic"
    default_persona: str = "komorebi"
    # Live broadcast mode. "off" disables it; "mock"/"twitch"/"youtube" select a
    # stream adapter that drives the shared character from real chat.
    stream_source: str = "off"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            host=os.environ.get("KOMOREBI_HOST", cls.host),
            port=int(os.environ.get("KOMOREBI_PORT", cls.port)),
            llm_backend=os.environ.get("KOMOREBI_LLM", cls.llm_backend),
            tts_backend=os.environ.get("KOMOREBI_TTS", cls.tts_backend),
            emotion_backend=os.environ.get("KOMOREBI_EMOTION", cls.emotion_backend),
            default_persona=os.environ.get("KOMOREBI_PERSONA", cls.default_persona),
            stream_source=os.environ.get("KOMOREBI_STREAM", cls.stream_source),
        )
