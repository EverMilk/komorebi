from komorebi.backends.llm.echo import EchoBackend
from komorebi.backends.tts.silent import SilentBackend
from komorebi.orchestrator import Orchestrator, split_sentences
from komorebi.persona import Persona
from komorebi.protocol import ServerMsg


def _orch() -> Orchestrator:
    persona = Persona(id="t", name="Test", persona_prompt="be nice")
    return Orchestrator(persona=persona, llm=EchoBackend(), tts=SilentBackend())


def test_split_sentences():
    parts = split_sentences("やった！すごいね。これは何？")
    assert parts == ["やった！", "すごいね。", "これは何？"]
    assert split_sentences("") == []


async def test_turn_emits_contract_envelope():
    orch = _orch()
    events = [e async for e in orch.handle_user_message("こんにちは")]
    types = [e["type"] for e in events]

    assert types[0] == ServerMsg.SPEECH_START
    assert types[-1] == ServerMsg.SPEECH_END
    assert ServerMsg.EXPRESSION in types
    assert ServerMsg.VISEME in types
    # exactly one final subtitle
    finals = [e for e in events if e["type"] == ServerMsg.SUBTITLE and e["final"]]
    assert len(finals) == 1


async def test_expression_per_sentence_with_increasing_time():
    orch = _orch()
    # Force a multi-sentence reply by speaking through _speak directly.
    events = [e async for e in orch._speak("やった！すごいね。これは何？")]
    exprs = [e for e in events if e["type"] == ServerMsg.EXPRESSION]
    assert len(exprs) == 3
    times = [e["t"] for e in exprs]
    assert times == sorted(times)
    assert times[0] == 0.0
    for e in exprs:
        assert 0.0 <= e["intensity"] <= 1.0


async def test_history_is_recorded():
    orch = _orch()
    _ = [e async for e in orch.handle_user_message("hi")]
    assert orch.history[0] == {"role": "user", "content": "hi"}
    assert orch.history[1]["role"] == "assistant"
    assert orch.history[1]["content"]
