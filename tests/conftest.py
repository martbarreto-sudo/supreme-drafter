"""Stubs de teste: um cliente Anthropic falso que não faz rede."""

from __future__ import annotations

import json
from dataclasses import dataclass, field


@dataclass
class FakeBlock:
    type: str
    text: str = ""


@dataclass
class FakeMessage:
    content: list
    stop_reason: str = "end_turn"
    stop_details: object | None = None


class _FakeStreamCtx:
    def __init__(self, message: FakeMessage):
        self._message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self) -> FakeMessage:
        return self._message


@dataclass
class _Messages:
    parent: "FakeClient"

    def stream(self, **kwargs):
        self.parent.calls.append(kwargs)
        return _FakeStreamCtx(self.parent.next_message(kwargs))


@dataclass
class FakeClient:
    """Devolve dossiê ou peça consoante `output_config.format` esteja presente."""

    dossie: dict = field(default_factory=dict)
    peca: str = "# Peça de teste\n\n— Minuta"
    calls: list = field(default_factory=list)
    messages: _Messages = field(init=False)

    def __post_init__(self):
        self.messages = _Messages(self)

    def next_message(self, kwargs) -> FakeMessage:
        has_format = "format" in kwargs.get("output_config", {})
        if has_format:  # Deep Hunter → JSON
            return FakeMessage(
                content=[FakeBlock("text", json.dumps(self.dossie, ensure_ascii=False))]
            )
        return FakeMessage(content=[FakeBlock("text", self.peca)])  # Supreme Drafter
