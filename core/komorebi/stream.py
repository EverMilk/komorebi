"""Live broadcast mode — one shared character reacting to real chat.

When ``KOMOREBI_STREAM`` is not ``off``, the server runs a single background task
that:

1. reads chat from a :class:`StreamAdapter` (mock / twitch / youtube),
2. turns each message into a turn for one shared :class:`Orchestrator`, and
3. fans the resulting wire events out to every connected ``/live`` viewer.

This is the "AITuber on a real stream" use case: viewers open the page read-only
and watch the avatar respond — the same normalized events that power the 1:1
``/ws`` chat, just broadcast instead of private. Like the rest of Komorebi it runs
out of the box: ``KOMOREBI_STREAM=mock`` needs no credentials.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from . import protocol
from .backends.llm import create_llm
from .backends.stream import create_stream
from .backends.tts import create_tts
from .config import Config
from .orchestrator import Orchestrator
from .persona import load_persona


class Hub:
    """Fan-out of wire events to all connected live viewers.

    Each viewer gets its own bounded queue; a slow viewer drops frames instead of
    stalling the broadcast for everyone. Recent events are replayed to joiners so a
    fresh tab isn't stuck on a blank stage until the next message.
    """

    def __init__(self, backlog: int = 12) -> None:
        self._subscribers: set[asyncio.Queue[dict[str, Any]]] = set()
        self._recent: list[dict[str, Any]] = []
        self._backlog = backlog

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
        for event in self._recent:
            with contextlib.suppress(asyncio.QueueFull):
                queue.put_nowait(event)
        self._subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        self._subscribers.discard(queue)

    def publish(self, event: dict[str, Any]) -> None:
        self._recent.append(event)
        if len(self._recent) > self._backlog:
            self._recent = self._recent[-self._backlog :]
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass  # slow viewer: drop this frame for them

    @property
    def viewer_count(self) -> int:
        return len(self._subscribers)


async def run_stream(config: Config, hub: Hub) -> None:
    """Drive the shared character from a live chat source until cancelled."""
    persona = load_persona(config.default_persona)
    orchestrator = Orchestrator(
        persona=persona,
        llm=create_llm(config.llm_backend),
        tts=create_tts(config.tts_backend),
        emotion_backend=config.emotion_backend,
    )
    adapter = create_stream(config.stream_source)

    hub.publish(protocol.ready(persona.info()))
    async for event in orchestrator.greet():
        hub.publish(event)

    async for message in adapter.listen():
        # Echo the incoming chat so viewers see what prompted the reply.
        hub.publish(protocol.chat(message.author, message.text, message.platform))
        prompt = f"{message.author}: {message.text}"
        async for event in orchestrator.handle_user_message(prompt):
            hub.publish(event)
