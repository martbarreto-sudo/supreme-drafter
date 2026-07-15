"""Testes de configuração e integridade do schema (sem rede)."""

from __future__ import annotations

from deep_hunter.config import Comando, Modo, Peca
from deep_hunter.schema import DOSSIE_SCHEMA


def test_modos_tem_foco():
    for m in Modo:
        assert m.foco, f"Modo {m} sem foco"


def test_comandos_tem_diretriz():
    for c in Comando:
        assert "Cmd Hunter" in c.diretriz


def test_pecas_tem_descricao():
    for p in Peca:
        assert p.descricao


def _valida_structured_outputs(node) -> None:
    """Structured outputs: todo objeto precisa de additionalProperties:false + required."""
    if not isinstance(node, dict):
        return
    if node.get("type") == "object":
        assert node.get("additionalProperties") is False
        assert "required" in node
        assert set(node["required"]) == set(node.get("properties", {}))
        for sub in node.get("properties", {}).values():
            _valida_structured_outputs(sub)
    if node.get("type") == "array":
        _valida_structured_outputs(node.get("items", {}))


def test_schema_respeita_structured_outputs():
    _valida_structured_outputs(DOSSIE_SCHEMA)
