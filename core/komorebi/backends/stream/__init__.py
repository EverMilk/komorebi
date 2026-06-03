"""Stream adapter registry / factory.

A stream adapter ingests live chat from a platform and yields normalized
``ChatMessage`` objects (see ``base.py``). Add a platform by writing one class
and registering it here.

The ``mock`` and ``twitch`` adapters need no credentials, so the live-broadcast
feature is demonstrable out of the box.
"""

from __future__ import annotations

from .base import ChatMessage, StreamAdapter
from .mock import MockStream
from .twitch import TwitchStream
from .youtube import YouTubeStream

_REGISTRY: dict[str, type] = {
    MockStream.name: MockStream,
    TwitchStream.name: TwitchStream,
    YouTubeStream.name: YouTubeStream,
}


def create_stream(name: str) -> StreamAdapter:
    cls = _REGISTRY.get(name)
    if cls is None:
        available = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"Unknown stream adapter '{name}'. Available: {available}")
    return cls()


__all__ = ["ChatMessage", "StreamAdapter", "create_stream"]
