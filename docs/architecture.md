# Komorebi Architecture

Komorebi is split into two layers connected by a single WebSocket:

- **Python core** (`core/komorebi`) — does all the thinking: LLM, emotion, TTS,
  persona, orchestration.
- **Browser front-end** (`web`) — does only drawing: it renders an avatar and
  reacts to events it receives.

Keeping the browser "dumb" is deliberate. It means the hard, interesting work lives
in Python (where the AI ecosystem is), and any renderer — VRM, Live2D, or a 2D
placeholder — can be driven by the same events.

## The frozen contract: WebSocket messages

The message schema below is the **boundary between the two layers**. Treat it as
stable; changing it requires a discussion issue. Both `core/komorebi/protocol.py`
and `web/src/protocol.js` are hand-mirrored implementations of this schema — keep
them in sync. (The browser layer is build-less JavaScript in M0; it migrates to
TypeScript + Vite in M2.)

Endpoint: `GET /ws` (WebSocket). All messages are JSON objects with a `type` field.

### Client → Server

| `type`         | fields                       | meaning                                  |
|----------------|------------------------------|------------------------------------------|
| `hello`        | `persona?: string`           | sent once on connect; selects a persona  |
| `user_message` | `text: string`               | the user said something                  |

### Server → Client

| `type`         | fields                                          | meaning                              |
|----------------|-------------------------------------------------|--------------------------------------|
| `ready`        | `persona: PersonaInfo`                           | handshake complete, persona loaded   |
| `speech_start` | —                                                | the character is about to speak      |
| `subtitle`     | `text: string`, `final: bool`                    | caption (may stream incrementally)   |
| `expression`   | `emotion: string`, `intensity: float (0..1)`, `t: float` | drive the face at time `t` (s) |
| `viseme`       | `phoneme: string`, `t: float` (seconds offset)   | mouth shape at time `t`              |
| `audio`        | `format: string`, `data_b64: string`             | optional audio chunk (empty in demo) |
| `speech_end`   | —                                                | the character finished speaking      |
| `error`        | `message: string`                                | something went wrong                 |

A normal turn looks like:

```
client → user_message
server → speech_start
server → subtitle   {text:"...", final:false}        (full text up front)
server → expression {emotion:"joy", intensity:0.6, t:0.0}   (one per sentence, timed)
server → viseme     {phoneme:"a", t:0.0}             (0..n times)
server → audio      {...}                            (0..n, omitted in demo)
server → subtitle   {text:"...", final:true}
server → speech_end
```

Expression and viseme events both carry a `t` offset (seconds from `speech_start`)
so the renderer can schedule them against speech. A reply is split into sentences
and each gets its own timed `expression`, so the face changes *through* a line.

## ExpressionCommand — the avatar-agnostic core

The whole "swap any avatar" promise rests on one normalization step. `EmotionEngine`
never emits Live2D parameters or VRM blendshapes. It emits abstract emotions
(`neutral`, `joy`, `sadness`, `anger`, `surprise`, `fear`, `thinking`) plus an
intensity. Each renderer maps those to its own parameters. A persona pack can
override the mapping, but the wire format stays abstract.

## Backends (plugin points)

| Interface     | File                                  | Reference impl | Real impls (later)            |
|---------------|---------------------------------------|----------------|-------------------------------|
| `LLMBackend`  | `backends/llm/base.py`                | `echo`         | openai / codex / claude / ollama |
| `TTSBackend`  | `backends/tts/base.py`                | `silent`       | voicevox / style-bert-vits2   |
| `AvatarBackend`| `web/src/avatar/AvatarBackend.js`    | `placeholder`  | vrm (three-vrm) / live2d (plugin) |

Backends are selected at runtime by environment variable:

| env var          | default  | meaning              |
|------------------|----------|----------------------|
| `KOMOREBI_LLM`   | `echo`   | which LLM backend    |
| `KOMOREBI_TTS`   | `silent` | which TTS backend    |
| `KOMOREBI_EMOTION`| `heuristic` | emotion classifier: `heuristic` or `llm` |
| `KOMOREBI_PERSONA`| `komorebi` | default persona id |
| `KOMOREBI_HOST`  | `127.0.0.1` | bind host         |
| `KOMOREBI_PORT`  | `8000`   | bind port            |

Defaults give you a working demo with no external services.
