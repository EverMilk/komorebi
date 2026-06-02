# Contributing to Komorebi

Thanks for helping make AI more approachable. There are three easy ways in, ranked
by how little you need to know about the codebase.

## 1. Add a Persona Pack (no code)

A persona is a single YAML file under `personas/`. Copy
[`personas/sample/komorebi.persona.yaml`](./personas/sample/komorebi.persona.yaml),
change the personality / voice / expression mapping, and open a pull request. That's it.

## 2. Add a backend (some Python)

Backends implement a small `Protocol`:

- **LLM** — implement `LLMBackend` in `core/komorebi/backends/llm/base.py`.
- **TTS** — implement `TTSBackend` in `core/komorebi/backends/tts/base.py`.

Register your class in the backend `__init__.py` factory and you're done. See the
`echo` and `silent` reference backends for the simplest possible examples.

## 3. Add an avatar renderer (browser)

Renderers implement the `AvatarBackend` interface in
`web/src/avatar/AvatarBackend.js`. They receive normalized expression and viseme
events — they never need to know which LLM or TTS produced them. See
`PlaceholderAvatar.js` for the reference implementation. (The browser layer is
build-less JS in M0 and migrates to TypeScript + Vite in M2.)

## Ground rules

- Keep the **core MIT-clean.** Anything with a non-MIT dependency (e.g. Live2D Cubism
  SDK) must live as an opt-in plugin, never a core dependency.
- Don't break the **WebSocket contract** in `docs/architecture.md` without a discussion
  issue first — it's the frozen boundary between Python and the browser.
- Small PRs over big ones. One persona / one backend / one fix per PR.

## Dev setup

```bash
cd core && pip install -e ".[dev]"
python -m komorebi        # serves the WebSocket + the build-less web demo
```

Visit http://localhost:8000. The M0 front-end needs no npm build — the Python
server serves the static JS modules directly. (The TS + Vite toolchain lands in M2.)

Look for issues labeled `good first issue`.
