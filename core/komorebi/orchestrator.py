"""Orchestrator — runs one conversation turn and emits wire events.

It is renderer- and transport-agnostic: it ``yield``s protocol message dicts, and
the server is responsible for pushing them down a WebSocket. This separation keeps
the turn logic unit-testable without a socket.

Turn flow (see docs/architecture.md):
    user_message -> speech_start -> expression -> subtitle* -> viseme* -> audio?
                 -> subtitle(final) -> speech_end
"""

from __future__ import annotations

from typing import Any, AsyncIterator

from . import protocol
from .backends.llm import LLMBackend, Message
from .backends.tts import TTSBackend
from .emotion import EmotionEngine
from .persona import Persona


class Orchestrator:
    def __init__(self, persona: Persona, llm: LLMBackend, tts: TTSBackend) -> None:
        self.persona = persona
        self.llm = llm
        self.tts = tts
        self.emotion = EmotionEngine(persona)
        self.history: list[Message] = []

    async def greet(self) -> AsyncIterator[dict[str, Any]]:
        if self.persona.greeting:
            async for msg in self._speak(self.persona.greeting):
                yield msg

    async def handle_user_message(self, text: str) -> AsyncIterator[dict[str, Any]]:
        self.history.append({"role": "user", "content": text})

        # Collect the streamed reply. We buffer to keep emotion/viseme timing
        # simple in M0; M1 can move to true incremental streaming.
        chunks: list[str] = []
        async for piece in self.llm.reply(self.persona.persona_prompt, self.history):
            chunks.append(piece)
        reply = "".join(chunks).strip()
        self.history.append({"role": "assistant", "content": reply})

        async for msg in self._speak(reply):
            yield msg

    async def _speak(self, text: str) -> AsyncIterator[dict[str, Any]]:
        yield protocol.speech_start()

        cmd = self.emotion.classify(text)
        yield protocol.expression(cmd.emotion, cmd.intensity)

        speech = await self.tts.synthesize(text, self.persona.voice)

        if speech.audio_b64:
            yield protocol.audio(speech.audio_format, speech.audio_b64)

        frames = speech.visemes or self.emotion.visemes(text, speech.duration)
        for phoneme, t in frames:
            yield protocol.viseme(phoneme, t)

        yield protocol.subtitle(text, final=True)
        yield protocol.speech_end()
