"""Testes de configuração e integridade do schema derivado (sem rede)."""

from __future__ import annotations

import pytest

from deep_hunter.config import Comando, Modo, RunConfig
from deep_hunter.schema import DOSSIE_SCHEMA
from deep_hunter.structured import to_anthropic_schema
from pydantic import BaseModel

from schema.dossier_hunter import NPU_PATTERN, DossierHunterSchema


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


def _palavras_chave(node) -> set:
    """Todas as palavras-chave de schema usadas na árvore (ignora nomes de campos)."""
    chaves = set()
    if isinstance(node, dict):
        mapas = {"properties", "$defs", "definitions"}
        for k, v in node.items():
            chaves.add(k)
            if k in mapas:
                for sub in v.values():
                    chaves |= _palavras_chave(sub)
            elif k not in {"enum", "const", "default", "examples", "title", "description"}:
                chaves |= _palavras_chave(v)
    elif isinstance(node, list):
        for x in node:
            chaves |= _palavras_chave(x)
    return chaves


def test_schema_remove_restricoes_nao_suportadas():
    # `pattern` não pode chegar à API como palavra-chave de schema...
    assert "pattern" not in _palavras_chave(DOSSIE_SCHEMA)


def test_restricao_removida_sobrevive_na_descricao():
    """...mas também não pode desaparecer: sem ela o modelo não sabe o formato do NPU.

    Descartar o `pattern` em silêncio fazia o Deep Hunter devolver um NPU livre que
    só era rejeitado depois, na validação client-side — auditoria paga e perdida.
    """
    descricao = DOSSIE_SCHEMA["properties"]["npu"]["description"]
    assert NPU_PATTERN in descricao
    assert "padrão CNJ" in descricao


def test_campo_com_nome_de_palavra_chave_sobrevive():
    """Filtrar as chaves de `properties` apagava campos sem erro algum."""

    class Evidencia(BaseModel):
        pattern: str
        maxLength: int = 0
        ok: bool = True

    schema = to_anthropic_schema(Evidencia)
    assert set(schema["properties"]) == {"pattern", "maxLength", "ok"}
    assert set(schema["required"]) == {"pattern", "maxLength", "ok"}


# ── RunConfig ────────────────────────────────────────────────────────────────


def test_run_config_aceita_todos_os_niveis_de_esforco():
    for nivel in ("low", "medium", "high", "xhigh", "max"):
        assert RunConfig(effort=nivel).effort == nivel


def test_run_config_rejeita_esforco_invalido():
    """Um DEEP_HUNTER_EFFORT com gralha só falharia no servidor (HTTP 400)."""
    with pytest.raises(ValueError, match="esforço inválido"):
        RunConfig(effort="alto")
