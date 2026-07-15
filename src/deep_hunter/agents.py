"""Os dois agentes autónomos, agora acoplados ao contrato único DossierHunterSchema.

- Deep Hunter  → devolve um `DossierHunterSchema` validado.
- Supreme Drafter → consome `DossierHunterSchema` + `ModoRedacional` (via DraftEngine).
"""

from __future__ import annotations

from pathlib import Path

import anthropic

from core.draft_engine import DraftEngine, DraftRequest, ModoRedacional
from schema.dossier_hunter import DossierHunterSchema

from .config import Comando, Modo, RunConfig
from .pdf_ingest import load_pdf_block
from .prompts import DEEP_HUNTER_SYSTEM, SUPREME_DRAFTER_SYSTEM, deep_hunter_instruction
from .schema import DOSSIE_SCHEMA


class DeepHunter:
    """Agente 01 — o Auditor. Popula e devolve o DossierHunterSchema."""

    def __init__(self, client: anthropic.Anthropic, config: RunConfig | None = None):
        self.client = client
        self.config = config or RunConfig()

    def audit(
        self,
        pdf_path: str | Path,
        *,
        modo: Modo = Modo.SIMBIOSE,
        comandos: list[Comando] | None = None,
    ) -> DossierHunterSchema:
        """Audita os autos e devolve o contrato validado."""
        comandos = comandos or []
        # Structured outputs é incompatível com citations → citations=False.
        pdf_block = load_pdf_block(pdf_path, citations=False)
        instrucao = deep_hunter_instruction(modo.foco, [c.diretriz for c in comandos])

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
        # Validação client-side (inclui o pattern do NPU, aposentado do schema enviado).
        return DossierHunterSchema.model_validate_json(text)


class SupremeDrafter:
    """Agente 02 — o Executor. Converte o DossierHunterSchema numa peça (Markdown)."""

    def __init__(self, client: anthropic.Anthropic, config: RunConfig | None = None):
        self.client = client
        self.config = config or RunConfig()
        self.engine = DraftEngine()

    @staticmethod
    def _resumo(dossie: DossierHunterSchema) -> str:
        """Síntese fática líquida derivada do dossiê, sem inventar nada."""
        flags = []
        if dossie.omissao_analise_contemporaneidade:
            flags.append("omissão de contemporaneidade")
        if dossie.ausencia_ata_plenario:
            flags.append("ausência de ata de plenário")
        if dossie.quebra_sequencial_ids:
            flags.append("quebra sequencial de IDs no PJe")
        quebras = sum(1 for m in dossie.auditoria_custodia if m.possui_quebra_custodia)
        desvios = sum(1 for j in dossie.auditoria_magistrados if j.possui_desvio)
        return (
            f"NPU {dossie.npu} ({dossie.tribunal} — {dossie.orgao_julgador}). "
            f"Atos mapeados: {len(dossie.linha_tempo_atos)}. "
            f"Quebras de custódia: {quebras}. Desvios de juiz natural: {desvios}. "
            f"Omissões do Estado: {', '.join(flags) or 'nenhuma sinalizada'}."
        )

    def draft(
        self,
        dossie: DossierHunterSchema,
        *,
        modo: ModoRedacional = ModoRedacional.PERTINAZ,
        conteudo_base: str | None = None,
    ) -> str:
        """Redige a peça a partir do dossiê e do modo redacional."""
        request = DraftRequest(
            modo=modo,
            conteudo_base=conteudo_base or self._resumo(dossie),
            dados_hunter=dossie,
        )
        instrucao = self.engine.compor_instrucao_retorica(request)

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
