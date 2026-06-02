import pytest

from komorebi.backends.llm.echo import EchoBackend
from komorebi.backends.tts.silent import SilentBackend
from komorebi.orchestrator import Orchestrator
from komorebi.persona import Persona
from komorebi.protocol import ServerMsg


def _orch() -> Orchestrator:
    persona = Persona(id="t", name="Test", persona_prompt="be nice")
    return Orchestrator(persona=persona, llm=EchoBackend(), tts=SilentBackend())


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_history_is_recorded():
    orch = _orch()
    _ = [e async for e in orch.handle_user_message("hi")]
    assert orch.history[0] == {"role": "user", "content": "hi"}
    assert orch.history[1]["role"] == "assistant"
    assert orch.history[1]["content"]


@pytest.mark.asyncio
async def test_expression_intensity_in_range():
    orch = _orch()
    events = [e async for e in orch.handle_user_message("嬉しい！")]
    expr = next(e for e in events if e["type"] == ServerMsg.EXPRESSION)
    assert 0.0 <= expr["intensity"] <= 1.0
