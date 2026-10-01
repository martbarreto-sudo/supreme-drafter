"""Testes de configuração (sem rede)."""

from __future__ import annotations

import pytest

from deep_hunter.config import Comando, Modo, RunConfig


def test_modos_tem_foco():
    for m in Modo:
        assert m.foco, f"Modo {m} sem foco"


def test_comandos_tem_diretriz():
    for c in Comando:
        assert "Cmd Hunter" in c.diretriz


# ── RunConfig ────────────────────────────────────────────────────────────────


def test_run_config_aceita_todos_os_niveis_de_esforco():
    for nivel in ("low", "medium", "high", "xhigh", "max"):
        assert RunConfig(effort=nivel).effort == nivel


def test_run_config_rejeita_esforco_invalido():
    """Um DEEP_HUNTER_EFFORT com gralha só falharia no servidor (HTTP 400)."""
    with pytest.raises(ValueError, match="esforço inválido"):
        RunConfig(effort="alto")
