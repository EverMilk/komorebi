# Live broadcast mode

Komorebi's 1:1 chat and its "AITuber on a stream" mode are the **same engine**.
A normal session is one viewer talking to the character over `/ws`. Live mode
points a real chat source (Twitch, YouTube, or a built-in mock) at one *shared*
character and broadcasts the reaction to every viewer over `/live`.

Because both paths emit the identical [WebSocket contract](./architecture.md),
the browser's rendering half is unchanged — only the connection and the (absent)
input differ.

```
chat source ──► StreamAdapter ──► Orchestrator ──► Hub ──► every /live viewer
 (twitch/yt/mock)  ChatMessage      (shared char)   fan-out   read-only browser
```

## Try it in 30 seconds (no credentials)

```bash
cd core
KOMOREBI_STREAM=mock python -m komorebi
# open http://localhost:8000/?mode=live
```

The `mock` adapter emits a rotating set of synthetic chat messages on an
interval, so you can see the broadcast view — avatar reacting, chat feed
scrolling — with no platform account.

## Configuration

| env var                     | default | meaning                                             |
|-----------------------------|---------|-----------------------------------------------------|
| `KOMOREBI_STREAM`           | `off`   | `off` / `mock` / `twitch` / `youtube`               |
| `KOMOREBI_MOCK_INTERVAL`    | `7`     | seconds between mock messages                        |
| `KOMOREBI_TWITCH_CHANNEL`   | —       | channel to read (no `#`), required for `twitch`      |
| `KOMOREBI_YOUTUBE_VIDEO_ID` | —       | live video id, required for `youtube`               |
| `YOUTUBE_API_KEY`           | —       | YouTube Data API v3 key, required for `youtube`     |

When `KOMOREBI_STREAM` is anything but `off`, the server starts a single
background task at startup that drives the shared character, and the `/live`
WebSocket endpoint becomes active. The front-end enters live mode with the
`?mode=live` query flag (read-only: onboarding and the composer are hidden, a
chat feed is shown).

## Adapters

### `mock` — zero dependencies
Built-in synthetic chat. Always available; ideal for layout/OBS testing.

### `twitch` — anonymous, no token
Twitch IRC permits **read-only anonymous** connections: Komorebi logs in with a
`justinfan` nickname and receives every message in a channel without OAuth. Only
listening is supported, which keeps the feature credential-free by construction.

```bash
KOMOREBI_STREAM=twitch KOMOREBI_TWITCH_CHANNEL=somestreamer python -m komorebi
```

### `youtube` — API key required
YouTube has no anonymous chat firehose, so this adapter polls the Data API v3 at
the interval the API recommends. It needs the live video id and an API key from
the Google Cloud console.

```bash
KOMOREBI_STREAM=youtube \
  KOMOREBI_YOUTUBE_VIDEO_ID=xxxxxxxxxxx \
  YOUTUBE_API_KEY=AIza... \
  python -m komorebi
```

## Add your own platform

A stream adapter is one small class implementing the `StreamAdapter` protocol
(`core/komorebi/backends/stream/base.py`):

```python
class MyStream:
    name = "myplatform"

    async def listen(self) -> AsyncIterator[ChatMessage]:
        while True:
            ...  # yield ChatMessage(author=..., text=..., platform="myplatform")
```

Register it in `core/komorebi/backends/stream/__init__.py` and it becomes
selectable with `KOMOREBI_STREAM=myplatform`. Keep adapters small and, where the
platform allows, credential-free so the demo stays one-command.

## Using it with OBS

Point an OBS **Browser Source** at `http://localhost:8000/?mode=live`. The page
is a transparent-friendly single stage (avatar + subtitle + chat feed), so you
can composite it over a scene. The shared character reacts to your live chat in
real time.
