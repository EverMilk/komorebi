"""Orchestrator — runs one conversation turn and emits wire events.

It is renderer- and transport-agnostic: it ``yield``s protocol message dicts, and
the server is responsible for pushing them down a WebSocket. This separation keeps
the turn logic unit-testable without a socket.

M1: a reply is split into sentences, each classified independently, so the
character's face changes *through* a line ("…うーん。やった！") instead of holding a
single expression for the whole turn. Each expression carries a ``t`` offset (in
seconds from speech start) so the renderer can time the change against speech.

Turn flow (see docs/architecture.md):
    user_message -> speech_start -> subtitle(full)
                 -> [expression@t]* (one per sentence)
                 -> viseme*
                 -> subtitle(final) -> speech_end
"""

from __future__ import annotations

import re
from typing import Any, AsyncIterator

from . import protocol
from .backends.llm import LLMBackend, Message
from .backends.tts import TTSBackend
from .emotion import create_emotion_engine
from .persona import Persona

_SENTENCE_RE = re.compile(r"[^。．.!?！？\n]+[。．.!?！？]?")


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()]


class Orchestrator:
    def __init__(
        self,
        persona: Persona,
        llm: LLMBackend,
        tts: TTSBackend,
        emotion_backend: str = "heuristic",
    ) -> None:
        self.persona = persona
        self.llm = llm
        self.tts = tts
        self.emotion = create_emotion_engine(emotion_backend, persona, llm)
        self.history: list[Message] = []

    async def greet(self) -> AsyncIterator[dict[str, Any]]:
        if self.persona.greeting:
            async for msg in self._speak(self.persona.greeting):
                yield msg

    async def handle_user_message(self, text: str) -> AsyncIterator[dict[str, Any]]:
        self.history.append({"role": "user", "content": text})

        chunks: list[str] = []
        async for piece in self.llm.reply(self.persona.persona_prompt, self.history):
            chunks.append(piece)
        reply = "".join(chunks).strip()
        self.history.append({"role": "assistant", "content": reply})

        async for msg in self._speak(reply):
            yield msg

    async def _speak(self, text: str) -> AsyncIterator[dict[str, Any]]:
        yield protocol.speech_start()
        yield protocol.subtitle(text, final=False)

        speech = await self.tts.synthesize(text, self.persona.voice)
        if speech.audio_b64:
            yield protocol.audio(speech.audio_format, speech.audio_b64)

        # One timed expression per sentence, allocated across the utterance by
        # character weight so faces change roughly in step with speech.
        sentences = split_sentences(text) or [text]
        total_chars = sum(len(s) for s in sentences) or 1
        elapsed_chars = 0
        for sentence in sentences:
            t = round(speech.duration * elapsed_chars / total_chars, 3)
            cmd = await self.emotion.classify(sentence)
            yield protocol.expression(cmd.emotion, cmd.intensity, t=t)
            elapsed_chars += len(sentence)

        for phoneme, t in self.emotion.visemes(text, speech.duration):
            yield protocol.viseme(phoneme, t)

        yield protocol.subtitle(text, final=True)
        yield protocol.speech_end()
