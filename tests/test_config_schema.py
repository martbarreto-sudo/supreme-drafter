"""Testes de configuração e integridade do schema derivado (sem rede)."""

from __future__ import annotations

from deep_hunter.config import Comando, Modo
from deep_hunter.schema import DOSSIE_SCHEMA
from deep_hunter.structured import to_anthropic_schema
from schema.dossier_hunter import DossierHunterSchema


def test_modos_tem_foco():
    for m in Modo:
        assert m.foco, f"Modo {m} sem foco"


def test_comandos_tem_diretriz():
    for c in Comando:
        assert "Cmd Hunter" in c.diretriz


def _valida_structured_outputs(node) -> None:
    """Structured outputs: todo objeto precisa de additionalProperties:false + required."""
    if isinstance(node, dict):
        if node.get("type") == "object":
            assert node.get("additionalProperties") is False
            assert set(node["required"]) == set(node.get("properties", {}))
        for v in node.values():
            _valida_structured_outputs(v)
    elif isinstance(node, list):
        for x in node:
            _valida_structured_outputs(x)


def test_schema_derivado_respeita_structured_outputs():
    _valida_structured_outputs(DOSSIE_SCHEMA)


def test_schema_e_derivado_do_contrato_unificado():
    # A fonte de verdade é o DossierHunterSchema; o schema enviado é derivado dele.
    assert DOSSIE_SCHEMA == to_anthropic_schema(DossierHunterSchema)


def test_schema_remove_restricoes_nao_suportadas():
    import json

    txt = json.dumps(DOSSIE_SCHEMA)
    assert "pattern" not in txt  # pattern do NPU aposentado do schema enviado
