"""Zero-dependency demo stream adapter.

Emits a rotating set of synthetic chat messages on an interval so the live
broadcast mode (and OBS layout) can be exercised with no platform credentials.
"""

from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator

from .base import ChatMessage

_SCRIPT = [
    ("みどり", "こんばんは！配信たのしみにしてた！"),
    ("そら", "今日のおすすめは？"),
    ("カイ", "その話もっと聞きたいな"),
    ("ゲスト", "わー、かわいい！"),
    ("ren", "ちょっと元気ないけど話聞いてくれる？"),
    ("なな", "今日も一日おつかれさま〜"),
]


class MockStream:
    name = "mock"

    def __init__(self) -> None:
        self._interval = float(os.environ.get("KOMOREBI_MOCK_INTERVAL", "7"))

    async def listen(self) -> AsyncIterator[ChatMessage]:
        i = 0
        while True:
            author, text = _SCRIPT[i % len(_SCRIPT)]
            yield ChatMessage(author=author, text=text, platform="mock")
            i += 1
            await asyncio.sleep(self._interval)
