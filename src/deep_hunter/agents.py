"""Os dois agentes autónomos: Deep Hunter (auditor) e Supreme Drafter (redator)."""

from __future__ import annotations

import json
from pathlib import Path

import anthropic

from .config import Comando, Modo, Peca, RunConfig
from .pdf_ingest import load_pdf_block
from .prompts import (
    DEEP_HUNTER_SYSTEM,
    SUPREME_DRAFTER_SYSTEM,
    deep_hunter_instruction,
    supreme_drafter_instruction,
)
from .schema import DOSSIE_SCHEMA


class DeepHunter:
    """Agente 01 — o Auditor. Processa os autos e devolve o dossiê estruturado."""

    def __init__(self, client: anthropic.Anthropic, config: RunConfig | None = None):
        self.client = client
        self.config = config or RunConfig()

    def audit(
        self,
        pdf_path: str | Path,
        *,
        modo: Modo = Modo.SIMBIOSE,
        comandos: list[Comando] | None = None,
    ) -> dict:
        """Audita os autos e devolve o Dossiê + Tabela de Nulidades (dict)."""
        comandos = comandos or []
        # Structured outputs é incompatível com citations → citations=False.
        pdf_block = load_pdf_block(pdf_path, citations=False)
        instrucao = deep_hunter_instruction(
            modo.foco, [c.diretriz for c in comandos]
        )

        # Streaming: max_tokens elevado exige stream para não estourar timeout HTTP.
        with self.client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            thinking={"type": "adaptive"},
            output_config={
                "effort": self.config.effort,
                "format": {"type": "json_schema", "schema": DOSSIE_SCHEMA},
            },
            system=DEEP_HUNTER_SYSTEM,
            messages=[{"role": "user", "content": [pdf_block, {"type": "text", "text": instrucao}]}],
        ) as stream:
            message = stream.get_final_message()

        if message.stop_reason == "refusal":
            raise RuntimeError(f"Auditoria recusada pelo modelo: {message.stop_details}")

        text = next((b.text for b in message.content if b.type == "text"), "")
        if not text.strip():
            raise RuntimeError("Deep Hunter não devolveu conteúdo (dossiê vazio).")
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensivo
            raise RuntimeError(f"Dossiê não é JSON válido: {exc}\n{text[:500]}") from exc


class SupremeDrafter:
    """Agente 02 — o Executor. Converte o dossiê auditado numa peça (Markdown)."""

    def __init__(self, client: anthropic.Anthropic, config: RunConfig | None = None):
        self.client = client
        self.config = config or RunConfig()

    def draft(self, dossie: dict, *, peca: Peca = Peca.HABEAS_CORPUS) -> str:
        """Redige a peça a partir do dossiê. Nunca inventa factos fora dele."""
        dossie_json = json.dumps(dossie, ensure_ascii=False, indent=2)
        instrucao = supreme_drafter_instruction(peca.descricao, dossie_json)

        with self.client.messages.stream(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            thinking={"type": "adaptive"},
            output_config={"effort": self.config.effort},
            system=SUPREME_DRAFTER_SYSTEM,
            messages=[{"role": "user", "content": instrucao}],
        ) as stream:
            message = stream.get_final_message()

        if message.stop_reason == "refusal":
            raise RuntimeError(f"Redação recusada pelo modelo: {message.stop_details}")

        return "\n".join(b.text for b in message.content if b.type == "text").strip()
