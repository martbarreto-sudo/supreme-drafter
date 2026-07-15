"""Contrato de saída do Deep Hunter — UNIFICADO.

O schema JSON manual foi aposentado: a fonte única de verdade é o
`DossierHunterSchema` (Pydantic v2, pacote `schema`). Aqui apenas derivamos o
JSON Schema estrito que a Messages API exige em `output_config.format`.
"""

from __future__ import annotations

from schema.dossier_hunter import DossierHunterSchema

from .structured import to_anthropic_schema

# Schema estrito enviado à API, derivado do contrato Pydantic unificado.
DOSSIE_SCHEMA: dict = to_anthropic_schema(DossierHunterSchema)

__all__ = ["DOSSIE_SCHEMA", "DossierHunterSchema"]
