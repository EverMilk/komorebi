"""YouTube Live chat adapter (polling the Data API v3).

Unlike Twitch, YouTube live chat has no anonymous firehose — reading messages
requires an API key and the video's live-chat id. This adapter polls
``liveChat/messages`` at the interval the API recommends and yields each new
message.

    KOMOREBI_STREAM=youtube
    KOMOREBI_YOUTUBE_VIDEO_ID=dQw4w9WgXcQ
    YOUTUBE_API_KEY=AIza...

If no key is set the adapter raises with a clear message at construction time, so
the failure is explained rather than mysterious. The mock and twitch adapters
remain credential-free for the out-of-the-box demo.
"""

from __future__ import annotations

import asyncio
import os
from typing import AsyncIterator

import httpx

from .base import ChatMessage

_API = "https://www.googleapis.com/youtube/v3"


class YouTubeStream:
    name = "youtube"

    def __init__(self) -> None:
        self._video_id = os.environ.get("KOMOREBI_YOUTUBE_VIDEO_ID", "").strip()
        self._api_key = os.environ.get("YOUTUBE_API_KEY", "").strip()
        if not self._video_id:
            raise ValueError(
                "KOMOREBI_YOUTUBE_VIDEO_ID is required for the youtube stream adapter."
            )
        if not self._api_key:
            raise ValueError(
                "YOUTUBE_API_KEY is required for the youtube stream adapter. "
                "Get one from the Google Cloud console (YouTube Data API v3)."
            )

    async def _live_chat_id(self, client: httpx.AsyncClient) -> str:
        resp = await client.get(
            f"{_API}/videos",
            params={
                "part": "liveStreamingDetails",
                "id": self._video_id,
                "key": self._api_key,
            },
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
        if not items:
            raise ValueError(f"No video found for id '{self._video_id}'.")
        details = items[0].get("liveStreamingDetails", {})
        chat_id = details.get("activeLiveChatId")
        if not chat_id:
            raise ValueError(
                f"Video '{self._video_id}' has no active live chat (not live?)."
            )
        return chat_id

    async def listen(self) -> AsyncIterator[ChatMessage]:
        async with httpx.AsyncClient(timeout=20.0) as client:
            chat_id = await self._live_chat_id(client)
            page_token: str | None = None
            # Skip the backlog: only emit messages that arrive after we connect.
            first_pass = True
            while True:
                params = {
                    "part": "snippet,authorDetails",
                    "liveChatId": chat_id,
                    "key": self._api_key,
                }
                if page_token:
                    params["pageToken"] = page_token
                resp = await client.get(f"{_API}/liveChat/messages", params=params)
                resp.raise_for_status()
                data = resp.json()
                page_token = data.get("nextPageToken")
                if not first_pass:
                    for item in data.get("items", []):
                        snippet = item.get("snippet", {})
                        author = item.get("authorDetails", {}).get(
                            "displayName", "viewer"
                        )
                        text = snippet.get("displayMessage", "")
                        if text:
                            yield ChatMessage(
                                author=author, text=text, platform="youtube"
                            )
                first_pass = False
                # API tells us how long to wait; clamp to a sane floor.
                interval_ms = data.get("pollingIntervalMillis", 5000)
                await asyncio.sleep(max(2.0, interval_ms / 1000.0))
