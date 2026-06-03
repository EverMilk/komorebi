"""Persona Pack loading.

A persona is a single YAML file under ``personas/``. It carries everything that
makes a character feel like "someone": the system prompt, a greeting, voice
settings, and an optional per-emotion expression bias. Adding a character requires
no code — just a new YAML file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

# personas/ lives at the repo root, two levels up from this file's package dir:
#   <repo>/core/komorebi/persona.py  ->  <repo>/personas
_PERSONAS_DIR = Path(__file__).resolve().parents[2] / "personas"


@dataclass
class Persona:
    id: str
    name: str
    tagline: str = ""
    persona_prompt: str = ""
    greeting: str = ""
    voice: dict[str, Any] = field(default_factory=dict)
    expression_bias: dict[str, float] = field(default_factory=dict)

    def info(self) -> dict[str, Any]:
        """The subset sent to the browser in the ``ready`` message."""
        return {
            "id": self.id,
            "name": self.name,
            "tagline": self.tagline,
            "greeting": self.greeting,
            "expression_bias": self.expression_bias,
        }


def _persona_files() -> list[Path]:
    # Files whose name starts with "_" (e.g. _template.persona.yaml) are skipped:
    # they are scaffolding for contributors, not selectable characters.
    return [p for p in _PERSONAS_DIR.rglob("*.persona.yaml") if not p.name.startswith("_")]


def _find_persona_file(persona_id: str) -> Path | None:
    matches = [p for p in _persona_files() if p.name == f"{persona_id}.persona.yaml"]
    return matches[0] if matches else None


def load_persona(persona_id: str) -> Persona:
    """Load a persona by id. Falls back to a minimal built-in if not found."""
    path = _find_persona_file(persona_id)
    if path is None:
        return Persona(
            id=persona_id,
            name=persona_id,
            tagline="(persona file not found — using a default)",
            persona_prompt="You are a friendly, concise companion.",
        )
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return Persona(
        id=data.get("id", persona_id),
        name=data.get("name", persona_id),
        tagline=data.get("tagline", ""),
        persona_prompt=data.get("persona_prompt", ""),
        greeting=data.get("greeting", ""),
        voice=data.get("voice", {}) or {},
        expression_bias=data.get("expression_bias", {}) or {},
    )


def list_personas() -> list[str]:
    return sorted(p.name[: -len(".persona.yaml")] for p in _persona_files())
