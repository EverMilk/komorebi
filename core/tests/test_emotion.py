from komorebi.emotion import (
    EmotionEngine,
    HeuristicClassifier,
    LLMClassifier,
    create_emotion_engine,
)
from komorebi.persona import Persona


async def test_neutral_when_no_keywords():
    cmd = await HeuristicClassifier().classify("the table is brown")
    assert cmd.emotion == "neutral"
    assert 0.0 <= cmd.intensity <= 1.0


async def test_detects_joy():
    cmd = await HeuristicClassifier().classify("嬉しい！ありがとう！")
    assert cmd.emotion == "joy"
    assert cmd.intensity > 0.2


async def test_question_reads_as_thinking_or_surprise():
    cmd = await HeuristicClassifier().classify("これは何？")
    assert cmd.emotion in {"thinking", "surprise"}


async def test_persona_bias_scales_intensity():
    calm = HeuristicClassifier({"joy": 0.5})
    loud = HeuristicClassifier({"joy": 1.5})
    text = "好き！楽しい！嬉しい！"
    assert (await calm.classify(text)).intensity < (await loud.classify(text)).intensity


def test_visemes_span_duration():
    frames = EmotionEngine.visemes("あいうえお", duration=1.0)
    assert len(frames) == 5
    assert frames[0][1] == 0.0
    assert frames[-1][1] < 1.0
    assert frames[0][0] == "a"  # あ -> vowel a


class _FakeLLM:
    """An LLM backend that always returns a fixed classifier line."""

    name = "fake"

    def __init__(self, line: str):
        self._line = line

    async def reply(self, system_prompt, history):
        yield self._line


async def test_llm_classifier_parses_label():
    cmd = await LLMClassifier(_FakeLLM("anger 0.9")).classify("anything")
    assert cmd.emotion == "anger"
    assert cmd.intensity == 0.9


async def test_llm_classifier_falls_back_on_garbage():
    # Unparseable LLM output must degrade to the heuristic, not raise.
    cmd = await LLMClassifier(_FakeLLM("???")).classify("嬉しい！")
    assert cmd.emotion == "joy"


def test_factory_selects_backend():
    persona = Persona(id="t", name="t")
    heuristic = create_emotion_engine("heuristic", persona, _FakeLLM("joy 1.0"))
    llm = create_emotion_engine("llm", persona, _FakeLLM("joy 1.0"))
    assert isinstance(heuristic, EmotionEngine)
    assert isinstance(llm, EmotionEngine)
