from komorebi.emotion import EmotionEngine
from komorebi.persona import Persona


def _engine() -> EmotionEngine:
    return EmotionEngine(Persona(id="t", name="t"))


def test_neutral_when_no_keywords():
    cmd = _engine().classify("the table is brown")
    assert cmd.emotion == "neutral"
    assert 0.0 <= cmd.intensity <= 1.0


def test_detects_joy():
    cmd = _engine().classify("嬉しい！ありがとう！")
    assert cmd.emotion == "joy"
    assert cmd.intensity > 0.2


def test_question_reads_as_thinking_or_surprise():
    cmd = _engine().classify("これは何？")
    assert cmd.emotion in {"thinking", "surprise"}


def test_persona_bias_scales_intensity():
    calm = EmotionEngine(Persona(id="c", name="c", expression_bias={"joy": 0.5}))
    loud = EmotionEngine(Persona(id="l", name="l", expression_bias={"joy": 1.5}))
    text = "好き！楽しい！嬉しい！"
    assert calm.classify(text).intensity < loud.classify(text).intensity


def test_visemes_span_duration():
    frames = EmotionEngine.visemes("あいうえお", duration=1.0)
    assert len(frames) == 5
    assert frames[0][1] == 0.0
    assert frames[-1][1] < 1.0
    assert frames[0][0] == "a"  # あ -> vowel a
