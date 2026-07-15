"""Orquestração: encadeia Deep Hunter → Supreme Drafter pelo contrato unificado."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import anthropic

from core.draft_engine import ModoRedacional
from schema.dossier_hunter import DossierHunterSchema

from .agents import DeepHunter, SupremeDrafter
from .config import Comando, Modo, RunConfig


@dataclass
class Resultado:
    """Saída completa de uma execução do pipeline."""

    dossie: DossierHunterSchema
    peca_markdown: str


class Pipeline:
    """Ponto de entrada de alto nível da Doutrina de Combate Híbrido.

    O `client` usa o construtor de argumentos-zero da SDK, que resolve as credenciais
    a partir do ambiente (ANTHROPIC_API_KEY ou perfil `ant auth login`).
    """

    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        config: RunConfig | None = None,
    ):
        self.config = config or RunConfig()
        self.client = client or anthropic.Anthropic()
        self.hunter = DeepHunter(self.client, self.config)
        self.drafter = SupremeDrafter(self.client, self.config)

    def audit(
        self,
        pdf_path: str | Path,
        *,
        modo: Modo | str = Modo.SIMBIOSE,
        comandos: list[Comando | str] | None = None,
    ) -> DossierHunterSchema:
        """Executa apenas o Agente 01 e devolve o contrato validado."""
        return self.hunter.audit(
            pdf_path,
            modo=Modo(modo),
            comandos=[Comando(c) for c in (comandos or [])],
        )

    def draft(
        self,
        dossie: DossierHunterSchema,
        *,
        modo: ModoRedacional | str = ModoRedacional.PERTINAZ,
    ) -> str:
        """Executa apenas o Agente 02 sobre um dossiê já auditado."""
        return self.drafter.draft(dossie, modo=ModoRedacional(modo))

    def run(
        self,
        pdf_path: str | Path,
        *,
        modo: Modo | str = Modo.SIMBIOSE,
        comandos: list[Comando | str] | None = None,
        modo_redacional: ModoRedacional | str = ModoRedacional.PERTINAZ,
    ) -> Resultado:
        """Auditoria + redação, ponta a ponta."""
        dossie = self.audit(pdf_path, modo=modo, comandos=comandos)
        peca_md = self.draft(dossie, modo=modo_redacional)
        return Resultado(dossie=dossie, peca_markdown=peca_md)
