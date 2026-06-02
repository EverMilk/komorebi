"""The zero-dependency demo LLM backend.

It doesn't call any model. It produces a friendly, persona-flavored canned reply so
that a brand-new user can see the character react and talk within seconds, with no
API key. This is the backbone of Komorebi's "try in 30 seconds" promise.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from .base import Message


class EchoBackend:
    name = "echo"

    async def reply(self, system_prompt: str, history: list[Message]) -> AsyncIterator[str]:
        last_user = next(
            (m["content"] for m in reversed(history) if m.get("role") == "user"), ""
        )
        reply = self._compose(last_user)
        # Stream word-by-word so the front-end exercises incremental subtitles.
        for token in reply.split(" "):
            await asyncio.sleep(0.04)
            yield token + " "

    @staticmethod
    def _compose(user_text: str) -> str:
        text = user_text.strip()
        if not text:
            return "うーん、まだ何も聞こえないよ。何か話しかけてみて？"
        if "?" in text or "？" in text:
            return f"いい質問だね！「{text}」かあ…正直まだ自信はないけど、一緒に考えてみよう。"
        return f"なるほど、「{text}」って言ったんだね。聞かせてくれてありがとう、嬉しいな！"
