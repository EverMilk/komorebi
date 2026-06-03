"""The WebSocket wire contract (server side).

This mirrors ``web/src/protocol.ts``. The schema is the frozen boundary between the
Python core and the browser renderer — see ``docs/architecture.md``. Keep the two
files in sync.

Messages are plain JSON objects with a ``type`` discriminator. We use small helper
builders rather than a heavy serialization framework to keep the contract obvious
and dependency-free.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

# Abstract emotion vocabulary. Renderers map these to their own parameters
# (VRM blendshapes, Live2D params, ...). The wire format never leaks renderer
# specifics — this is what makes avatars swappable.
EMOTIONS = ("neutral", "joy", "sadness", "anger", "surprise", "fear", "thinking")


class ClientMsg(str, Enum):
    HELLO = "hello"
    USER_MESSAGE = "user_message"


class ServerMsg(str, Enum):
    READY = "ready"
    SPEECH_START = "speech_start"
    SUBTITLE = "subtitle"
    EXPRESSION = "expression"
    VISEME = "viseme"
    AUDIO = "audio"
    SPEECH_END = "speech_end"
    CHAT = "chat"
    ERROR = "error"


def ready(persona: dict[str, Any]) -> dict[str, Any]:
    return {"type": ServerMsg.READY, "persona": persona}


def speech_start() -> dict[str, Any]:
    return {"type": ServerMsg.SPEECH_START}


def subtitle(text: str, final: bool) -> dict[str, Any]:
    return {"type": ServerMsg.SUBTITLE, "text": text, "final": final}


def expression(emotion: str, intensity: float, t: float = 0.0) -> dict[str, Any]:
    if emotion not in EMOTIONS:
        emotion = "neutral"
    intensity = max(0.0, min(1.0, intensity))
    return {"type": ServerMsg.EXPRESSION, "emotion": emotion, "intensity": intensity, "t": t}


def viseme(phoneme: str, t: float) -> dict[str, Any]:
    return {"type": ServerMsg.VISEME, "phoneme": phoneme, "t": t}


def audio(fmt: str, data_b64: str) -> dict[str, Any]:
    return {"type": ServerMsg.AUDIO, "format": fmt, "data_b64": data_b64}


def speech_end() -> dict[str, Any]:
    return {"type": ServerMsg.SPEECH_END}


def chat(author: str, text: str, platform: str = "") -> dict[str, Any]:
    """A viewer chat message echoed to live viewers (so they see what was asked)."""
    return {"type": ServerMsg.CHAT, "author": author, "text": text, "platform": platform}


def error(message: str) -> dict[str, Any]:
    return {"type": ServerMsg.ERROR, "message": message}
