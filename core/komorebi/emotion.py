"""EmotionEngine — the avatar-agnostic heart of Komorebi.

It turns text into an abstract ``ExpressionCommand`` (emotion + intensity) plus a
crude viseme (mouth-shape) track. Crucially it never emits renderer-specific
parameters; every renderer maps the abstract emotion to its own face. That
indirection is what lets one core drive VRM, Live2D, or a placeholder equally.

v0 (M0) uses a transparent keyword heuristic. M1 will replace the classifier with
an LLM-based labeller behind the same interface — callers won't change.
"""

from __future__ import annotations

from dataclasses import dataclass

from .persona import Persona

# Keyword buckets for the v0 heuristic classifier. Deliberately simple and honest;
# good enough to make the avatar feel alive in the demo.
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


class EmotionEngine:
    def __init__(self, persona: Persona) -> None:
        self._bias = persona.expression_bias or {}

    def classify(self, text: str) -> ExpressionCommand:
        low = text.lower()
        scores: dict[str, int] = {}
        for emotion, words in _KEYWORDS.items():
            scores[emotion] = sum(1 for w in words if w in text or w in low)
        emotion = max(scores, key=lambda e: scores[e]) if any(scores.values()) else "neutral"

        raw = scores.get(emotion, 0)
        # Squash hit-count into 0..1, then apply per-persona bias.
        intensity = min(1.0, 0.4 + 0.2 * raw) if emotion != "neutral" else 0.2
        intensity = min(1.0, intensity * self._bias.get(emotion, 1.0))
        return ExpressionCommand(emotion=emotion, intensity=round(intensity, 3))

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
