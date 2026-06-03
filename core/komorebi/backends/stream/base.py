"""The live-chat stream contract.

A stream adapter ingests live chat from a platform and yields normalized
``ChatMessage`` objects. The stream runner turns each into a turn for the shared
character and broadcasts the result to viewers (e.g. an OBS browser source).

Adapters are intentionally small so contributors can add a platform by writing one
class. The ``mock`` reference adapter needs no service so the feature is
demonstrable out of the box.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol, runtime_checkable


@dataclass
class ChatMessage:
    author: str
    text: str
    platform: str = ""


@runtime_checkable
class StreamAdapter(Protocol):
    name: str

    def listen(self) -> AsyncIterator[ChatMessage]:
        """Yield chat messages as they arrive, indefinitely."""
        ...
