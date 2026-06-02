# komorebi (core)

The Python core of [Komorebi](https://github.com/) — an open-source AITuber engine
that makes AI approachable through animated characters.

This package contains the "brain": LLM, emotion, TTS, persona, orchestration, and a
FastAPI WebSocket server. It streams expression and viseme events to a thin browser
renderer over a single WebSocket.

```bash
pip install -e ".[dev]"
python -m komorebi          # demo on http://localhost:8000, no API key needed
pytest -q
```

See the repository root `README.md` and `docs/architecture.md` for the full picture
and the WebSocket wire contract.
