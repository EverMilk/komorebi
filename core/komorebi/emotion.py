"""EmotionEngine — the avatar-agnostic heart of Komorebi.

It turns text into an abstract ``ExpressionCommand`` (emotion + intensity) plus a
crude viseme (mouth-shape) track. Crucially it never emits renderer-specific
parameters; every renderer maps the abstract emotion to its own face. That
indirection is what lets one core drive VRM, Live2D, or a placeholder equally.

M1 introduces a pluggable classifier behind one async interface:

* ``HeuristicClassifier`` — transparent keyword rules, zero cost (the demo default).
* ``LLMClassifier``       — asks an LLM backend to label the line; falls back to the
  heuristic on any failure so it can never break a turn.

Both apply the persona's per-emotion ``expression_bias`` so the same line reads
stronger or softer depending on the character.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .backends.llm import LLMBackend
from .persona import Persona

# The abstract emotion vocabulary. Renderers map these to their own parameters.
EMOTIONS = ("neutral", "joy", "sadness", "anger", "surprise", "fear", "thinking")

# Keyword buckets for the heuristic classifier. Deliberately simple and honest.
_KEYWORDS: dict[str, tuple[str, ...]] = {
    "joy": ("！", "嬉", "楽し", "好き", "yay", "haha", "love", "great", "happy", "😊", "🎉"),
    "sadness": ("…", "悲", "つら", "ごめん", "sorry", "sad", "lonely", "😢"),
    "anger": ("怒", "ふざけ", "むかつ", "angry", "annoy"),
    "surprise": ("！？", "えっ", "まさか", "wow", "really?", "what?!", "😮"),
    "fear": ("怖", "こわ", "やばい", "scary", "afraid", "😨"),
    "thinking": ("？", "うーん", "んー", "hmm", "let me think", "maybe", "🤔"),
}

# Map characters to coarse viseme phonemes for placeholder lip-sync.
_VOWELS = {"a": "aあ", "i": "iい", "u": "uう", "e": "eえ", "o": "oお"}


@dataclass
class ExpressionCommand:
    emotion: str
    intensity: float


def _apply_bias(emotion: str, intensity: float, bias: dict[str, float]) -> float:
    return round(min(1.0, max(0.0, intensity * bias.get(emotion, 1.0))), 3)


@runtime_checkable
class EmotionClassifier(Protocol):
    async def classify(self, text: str) -> ExpressionCommand: ...


class HeuristicClassifier:
    """Keyword-rule classifier. No external calls — the demo default."""

    def __init__(self, bias: dict[str, float] | None = None) -> None:
        self._bias = bias or {}

    async def classify(self, text: str) -> ExpressionCommand:
        return self._classify_sync(text)

    def _classify_sync(self, text: str) -> ExpressionCommand:
        low = text.lower()
        scores = {e: sum(1 for w in words if w in text or w in low) for e, words in _KEYWORDS.items()}
        emotion = max(scores, key=lambda e: scores[e]) if any(scores.values()) else "neutral"
        raw = scores.get(emotion, 0)
        intensity = min(1.0, 0.4 + 0.2 * raw) if emotion != "neutral" else 0.2
        return ExpressionCommand(emotion, _apply_bias(emotion, intensity, self._bias))


class LLMClassifier:
    """Labels emotion with an LLM backend, falling back to the heuristic.

    Uses one focused completion per line. Opt-in (``KOMOREBI_EMOTION=llm``) because
    it costs an extra call per sentence. Any error or unparseable reply degrades
    gracefully to the heuristic, so it can never break a conversation turn.
    """

    _SYSTEM = (
        "You are an emotion classifier for an animated character. "
        "Read the line the character is about to say and reply with EXACTLY one line "
        "in the form `emotion intensity`, where emotion is one of: "
        + ", ".join(EMOTIONS)
        + " and intensity is a float 0.0-1.0. No other text."
    )

    def __init__(self, llm: LLMBackend, bias: dict[str, float] | None = None) -> None:
        self._llm = llm
        self._bias = bias or {}
        self._fallback = HeuristicClassifier(bias)

    async def classify(self, text: str) -> ExpressionCommand:
        try:
            chunks = [
                c async for c in self._llm.reply(self._SYSTEM, [{"role": "user", "content": text}])
            ]
            return self._parse("".join(chunks)) or await self._fallback.classify(text)
        except Exception:
            return await self._fallback.classify(text)

    def _parse(self, raw: str) -> ExpressionCommand | None:
        parts = raw.strip().replace(":", " ").split()
        if not parts:
            return None
        emotion = parts[0].lower()
        if emotion not in EMOTIONS:
            return None
        intensity = 0.6
        if len(parts) > 1:
            try:
                intensity = float(parts[1])
            except ValueError:
                pass
        return ExpressionCommand(emotion, _apply_bias(emotion, intensity, self._bias))


class EmotionEngine:
    def __init__(self, classifier: EmotionClassifier) -> None:
        self._classifier = classifier

    async def classify(self, text: str) -> ExpressionCommand:
        return await self._classifier.classify(text)

    @staticmethod
    def visemes(text: str, duration: float) -> list[tuple[str, float]]:
        """Produce (phoneme, time_offset) frames spread across ``duration`` seconds.

        A placeholder lip-sync: one mouth shape per non-space character, evenly
        timed. Real TTS backends will replace this with audio-aligned visemes.
        """
        chars = [c for c in text if not c.isspace()]
        if not chars:
            return []
        step = duration / len(chars)
        frames: list[tuple[str, float]] = []
        for i, c in enumerate(chars):
            phoneme = "rest"
            for vowel, members in _VOWELS.items():
                if c in members or c.lower() == vowel:
                    phoneme = vowel
                    break
            frames.append((phoneme, round(i * step, 3)))
        return frames


def create_emotion_engine(
    backend: str, persona: Persona, llm: LLMBackend
) -> EmotionEngine:
    bias = persona.expression_bias or {}
    if backend == "llm":
        return EmotionEngine(LLMClassifier(llm, bias))
    return EmotionEngine(HeuristicClassifier(bias))
