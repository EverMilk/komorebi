"""The zero-dependency demo TTS backend.

It produces no audio. It only estimates how long the line would take to speak, so
the orchestrator can time placeholder visemes and pace subtitles. This keeps the
demo fully functional with nothing installed; swap in VOICEVOX or Style-Bert-VITS2
later behind the same interface.
"""

from __future__ import annotations

from .base import SpeechResult

# Rough speaking rate. Japanese ~7 chars/sec is a reasonable placeholder.
_CHARS_PER_SECOND = 7.0


class SilentBackend:
    name = "silent"

    async def synthesize(self, text: str, voice: dict) -> SpeechResult:
        chars = len([c for c in text if not c.isspace()])
        speed = float(voice.get("speed", 1.0)) or 1.0
        duration = max(0.6, chars / (_CHARS_PER_SECOND * speed))
        return SpeechResult(duration=round(duration, 3))
