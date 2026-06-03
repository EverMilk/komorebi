"""Anonymous Twitch chat adapter (no credentials, stdlib only).

Twitch IRC allows *read-only anonymous* connections: log in with a ``justinfan``
nickname and you receive every PRIVMSG in a channel without an OAuth token. That
makes "watch a real Twitch chat drive the avatar" a zero-setup demo — you only
need a channel name.

    KOMOREBI_STREAM=twitch
    KOMOREBI_TWITCH_CHANNEL=somestreamer

Sending messages would require auth; Komorebi only listens, which keeps the
feature credential-free and read-only by construction.
"""

from __future__ import annotations

import asyncio
import os
import random
from typing import AsyncIterator

from .base import ChatMessage

_HOST = "irc.chat.twitch.tv"
_PORT = 6667


def parse_privmsg(line: str) -> ChatMessage | None:
    """Parse one raw IRC line into a ChatMessage, or None if not a chat message.

    A Twitch PRIVMSG looks like::

        :nick!nick@nick.tmi.twitch.tv PRIVMSG #channel :hello world

    IRCv3 tags (``@badge=...;color=... :nick!...``) are tolerated by stripping a
    leading ``@tag`` segment. Kept pure and synchronous so it is unit-testable
    without a socket.
    """
    if not line:
        return None
    # Drop IRCv3 tag prefix if present.
    if line.startswith("@"):
        space = line.find(" ")
        if space == -1:
            return None
        line = line[space + 1 :]
    if not line.startswith(":"):
        return None
    try:
        prefix, rest = line[1:].split(" ", 1)
    except ValueError:
        return None
    if not rest.startswith("PRIVMSG"):
        return None
    nick = prefix.split("!", 1)[0]
    try:
        _, target_and_text = rest.split(" ", 1)
        _channel, text = target_and_text.split(" :", 1)
    except ValueError:
        return None
    text = text.rstrip("\r\n")
    if not text:
        return None
    return ChatMessage(author=nick, text=text, platform="twitch")


class TwitchStream:
    name = "twitch"

    def __init__(self) -> None:
        channel = os.environ.get("KOMOREBI_TWITCH_CHANNEL", "").strip().lstrip("#")
        if not channel:
            raise ValueError(
                "KOMOREBI_TWITCH_CHANNEL is required for the twitch stream adapter."
            )
        self._channel = channel.lower()

    async def listen(self) -> AsyncIterator[ChatMessage]:
        nick = f"justinfan{random.randint(10000, 99999)}"
        reader, writer = await asyncio.open_connection(_HOST, _PORT)
        try:
            writer.write(f"NICK {nick}\r\n".encode())
            writer.write(f"JOIN #{self._channel}\r\n".encode())
            await writer.drain()
            while True:
                raw = await reader.readline()
                if not raw:
                    break  # server closed the connection
                line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
                if line.startswith("PING"):
                    writer.write(f"PONG {line[5:]}\r\n".encode())
                    await writer.drain()
                    continue
                msg = parse_privmsg(line)
                if msg is not None:
                    yield msg
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass
