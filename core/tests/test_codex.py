from komorebi.backends.llm import create_llm
from komorebi.backends.llm.codex import CodexBackend
from komorebi.backends.llm.openai_compatible import OpenAICompatibleBackend


def test_codex_registered_in_factory():
    backend = create_llm("codex")
    assert isinstance(backend, CodexBackend)
    assert backend.name == "codex"


def test_codex_is_openai_compatible():
    # Codex reuses the OpenAI-compatible streaming client.
    assert issubclass(CodexBackend, OpenAICompatibleBackend)


def test_codex_default_model(monkeypatch):
    monkeypatch.delenv("CODEX_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    assert CodexBackend()._model == "gpt-5-codex"


def test_codex_model_env_override(monkeypatch):
    monkeypatch.setenv("CODEX_MODEL", "gpt-5-codex-mini")
    assert CodexBackend()._model == "gpt-5-codex-mini"


def test_codex_falls_back_to_openai_model(monkeypatch):
    monkeypatch.delenv("CODEX_MODEL", raising=False)
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o-mini")
    assert CodexBackend()._model == "gpt-4o-mini"
