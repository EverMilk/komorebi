# 🌿 Komorebi

> Make AI approachable. An open-source AITuber engine that lets anyone talk to a
> living animated character — no setup, no fear, no API key required to try.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](./LICENSE)
![status: early (M0)](https://img.shields.io/badge/status-M0%20skeleton-orange)
![python](https://img.shields.io/badge/python-3.10%2B-blue)

<!-- TODO(M1): replace with a 3s demo GIF — "open browser → character talks back" -->
<p align="center"><em>Demo GIF coming in M1</em></p>

## Why Komorebi?

Most people don't reject AI because it's not smart enough — they reject it because
a blinking text box feels cold and intimidating. **Komorebi's thesis: an animated
character lowers the psychological barrier to AI.** A face that smiles, thinks, and
reacts turns "using a tool" into "talking to someone."

Komorebi is built around **Acceptance UX** as a first-class concept, not an
afterthought.

### What makes it different

- **Avatar-agnostic core.** One emotion/lip-sync API drives any renderer — VRM (3D),
  Live2D (2D anime), or a dependency-free placeholder. Swap your favorite model in.
- **Provider-agnostic brain.** The "brain" speaks to OpenAI / Codex / Claude / local
  Ollama through one `LLMBackend` interface.
- **Persona Packs.** A character's personality, voice, and expression mapping live in
  a single shareable file. Add a character with one pull request.
- **Try in 30 seconds.** A built-in demo mode runs with zero API keys.

## Architecture (one glance)

```
Browser (thin TS: rendering only)        Python Core (FastAPI + asyncio)
  AvatarRenderer  ◄── WebSocket ──►  Orchestrator
   VRM / Live2D / Placeholder          ├─ LLMBackend   (openai / codex / ollama / echo)
                                       ├─ EmotionEngine (text → expression command)
                                       ├─ TTSBackend   (voicevox / style-bert-vits2 / silent)
                                       └─ PersonaLoader (persona packs)
```

The browser only draws. The Python core does all the thinking and streams back
subtitles, expression events, and visemes over a single WebSocket. The WebSocket
message schema is the frozen contract between the two layers — see
[`docs/architecture.md`](./docs/architecture.md).

## Quick start (demo mode, no API key)

```bash
# 1. backend
cd core
pip install -e .
python -m komorebi            # serves ws + static web on http://localhost:8000

# 2. open the browser
#    visit http://localhost:8000 and start typing
```

Demo mode uses the `echo` LLM backend and a silent TTS backend, so the character
reacts and lip-syncs without any external service. Plug in a real backend via env
vars (see [`docs/architecture.md`](./docs/architecture.md)) when you're ready.

## Roadmap

- **M0 — skeleton (you are here):** monorepo, WebSocket contract, demo loop, placeholder avatar.
- **M1 — Acceptance UX:** 30-second onboarding, EmotionEngine v1, Persona Pack spec + samples.
- **M2 — dual avatars:** `AvatarBackend` abstraction with VRM and Live2D (optional plugin) renderers.
- **M3 — real demand:** YouTube/Twitch chat adapter, community persona gallery, official Codex backend.

## Contributing

Adding a persona, a backend, or an avatar renderer is the easiest way in — see
[`CONTRIBUTING.md`](./CONTRIBUTING.md). Look for `good first issue`.

## License

MIT. Note: the optional Live2D renderer (arriving in M2) depends on the Live2D
Cubism SDK, which has its own commercial license and is therefore shipped as a
**separate optional plugin** to keep the core 100% MIT.
