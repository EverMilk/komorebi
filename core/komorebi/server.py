"""FastAPI app: serves the WebSocket conversation endpoint and the static web UI.

The browser connects to ``/ws``, sends ``hello`` then ``user_message`` frames, and
receives the event stream defined in ``docs/architecture.md``. Static files from
``web/`` are served at ``/`` so ``python -m komorebi`` is a one-command demo.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import protocol
from .backends.llm import create_llm
from .backends.tts import create_tts
from .config import Config
from .orchestrator import Orchestrator
from .persona import load_persona

_WEB_DIR = Path(__file__).resolve().parents[2] / "web"


def create_app(config: Config) -> FastAPI:
    app = FastAPI(title="Komorebi", version="0.0.1")

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok", "llm": config.llm_backend, "tts": config.tts_backend}

    @app.websocket("/ws")
    async def ws(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            await _conversation(websocket, config)
        except WebSocketDisconnect:
            pass

    # Serve the front-end. In M0 the web app is a single static HTML file; once a
    # Vite build exists, point this at web/dist instead.
    if _WEB_DIR.exists():
        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(_WEB_DIR / "index.html")

        app.mount("/src", StaticFiles(directory=_WEB_DIR / "src"), name="src")

    return app


async def _conversation(websocket: WebSocket, config: Config) -> None:
    # Wait for the initial hello (or fall back to defaults).
    persona_id = config.default_persona
    first = await websocket.receive_text()
    try:
        msg = json.loads(first)
    except json.JSONDecodeError:
        msg = {}
    if msg.get("type") == protocol.ClientMsg.HELLO and msg.get("persona"):
        persona_id = msg["persona"]

    persona = load_persona(persona_id)
    orchestrator = Orchestrator(
        persona=persona,
        llm=create_llm(config.llm_backend),
        tts=create_tts(config.tts_backend),
    )

    await _send(websocket, protocol.ready(persona.info()))
    async for event in orchestrator.greet():
        await _send(websocket, event)

    while True:
        raw = await websocket.receive_text()
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await _send(websocket, protocol.error("invalid JSON"))
            continue
        if data.get("type") != protocol.ClientMsg.USER_MESSAGE:
            continue
        text = (data.get("text") or "").strip()
        if not text:
            continue
        async for event in orchestrator.handle_user_message(text):
            await _send(websocket, event)


async def _send(websocket: WebSocket, payload: dict) -> None:
    # Enum members serialize to their string value via default=str.
    await websocket.send_text(json.dumps(payload, ensure_ascii=False, default=str))
