"""First-class Codex / OpenAI LLM backend.

Komorebi is built to be a good open-source home for Codex: this backend makes
"powered by Codex" a one-line config. It reuses the OpenAI-compatible streaming
client (Codex models are served over the same /chat/completions API) but ships
Codex-oriented defaults and its own registry name so the wiring is explicit.

    KOMOREBI_LLM=codex
    OPENAI_API_KEY=sk-...
    CODEX_MODEL=gpt-5-codex            # or any Codex/OpenAI chat model
    OPENAI_BASE_URL=https://api.openai.com/v1   # override for compatible gateways

If no API key is set, replies explain how to enable it instead of failing, so the
zero-config demo (KOMOREBI_LLM=echo) remains the friendly default.
"""

from __future__ import annotations

import os

from .openai_compatible import OpenAICompatibleBackend


class CodexBackend(OpenAICompatibleBackend):
    name = "codex"

    def __init__(self) -> None:
        super().__init__()
        # Prefer a Codex-specific model var, then fall back to the generic one.
        self._model = os.environ.get("CODEX_MODEL", os.environ.get("OPENAI_MODEL", "gpt-5-codex"))
