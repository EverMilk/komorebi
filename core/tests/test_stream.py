import asyncio

import pytest

from komorebi.backends.stream import create_stream
from komorebi.backends.stream.base import ChatMessage, StreamAdapter
from komorebi.backends.stream.mock import MockStream
from komorebi.backends.stream.twitch import TwitchStream, parse_privmsg
from komorebi.protocol import ServerMsg
from komorebi.stream import Hub

# ---- factory --------------------------------------------------------------


def test_create_stream_returns_adapter():
    adapter = create_stream("mock")
    assert isinstance(adapter, StreamAdapter)
    assert adapter.name == "mock"


def test_create_stream_unknown_raises():
    with pytest.raises(ValueError, match="Unknown stream adapter"):
        create_stream("nope")


# ---- mock adapter ---------------------------------------------------------


async def test_mock_stream_yields_chat_messages(monkeypatch):
    monkeypatch.setenv("KOMOREBI_MOCK_INTERVAL", "0")
    stream = MockStream()
    seen: list[ChatMessage] = []
    async for msg in stream.listen():
        seen.append(msg)
        if len(seen) >= 3:
            break
    assert len(seen) == 3
    assert all(m.platform == "mock" for m in seen)
    assert all(m.author and m.text for m in seen)


# ---- twitch parser (pure, no socket) --------------------------------------


def test_parse_privmsg_basic():
    line = ":alice!alice@alice.tmi.twitch.tv PRIVMSG #chan :hello world"
    msg = parse_privmsg(line)
    assert msg == ChatMessage(author="alice", text="hello world", platform="twitch")


def test_parse_privmsg_with_ircv3_tags():
    line = "@badge-info=;color=#FF0000 :bob!bob@bob.tmi.twitch.tv PRIVMSG #chan :hi there"
    msg = parse_privmsg(line)
    assert msg is not None
    assert msg.author == "bob"
    assert msg.text == "hi there"


def test_parse_privmsg_ignores_non_privmsg():
    assert parse_privmsg(":tmi.twitch.tv 001 justinfan123 :Welcome") is None
    assert parse_privmsg("PING :tmi.twitch.tv") is None
    assert parse_privmsg("") is None


def test_twitch_requires_channel(monkeypatch):
    monkeypatch.delenv("KOMOREBI_TWITCH_CHANNEL", raising=False)
    with pytest.raises(ValueError, match="KOMOREBI_TWITCH_CHANNEL"):
        TwitchStream()


# ---- Hub broadcast --------------------------------------------------------


async def test_hub_fans_out_to_subscribers():
    hub = Hub()
    a = hub.subscribe()
    b = hub.subscribe()
    event = {"type": ServerMsg.CHAT, "author": "x", "text": "y"}
    hub.publish(event)
    assert await asyncio.wait_for(a.get(), 1) == event
    assert await asyncio.wait_for(b.get(), 1) == event
    assert hub.viewer_count == 2


async def test_hub_replays_recent_to_late_joiner():
    hub = Hub()
    hub.publish({"type": ServerMsg.SPEECH_START})
    hub.publish({"type": ServerMsg.SPEECH_END})
    late = hub.subscribe()
    first = await asyncio.wait_for(late.get(), 1)
    assert first["type"] == ServerMsg.SPEECH_START


async def test_hub_unsubscribe_stops_delivery():
    hub = Hub()
    q = hub.subscribe()
    hub.unsubscribe(q)
    assert hub.viewer_count == 0
    hub.publish({"type": ServerMsg.SPEECH_END})
    assert q.empty()


def test_hub_slow_subscriber_drops_without_raising():
    hub = Hub(backlog=0)
    q = hub.subscribe()
    # Fill beyond the queue's capacity; publish must not raise.
    for _ in range(200):
        hub.publish({"type": ServerMsg.SPEECH_END})
    assert q.full()
