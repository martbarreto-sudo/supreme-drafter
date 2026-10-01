"""A especificação publicada não pode se passar por runtime.

Em 01/10/2026 um comando de engenharia chegou mandando "corrigir bugs de
runtime" de rotas (`/messages/stream`, `rt_nx_auth`, barramento assíncrono)
que existem apenas em `public/openapi.json` e `public/api.html`. Nenhuma
delas está implementada: não há servidor HTTP neste repositório. A spec foi
lida como entrega porque não dizia o contrário.

Estes testes mantêm a declaração de estado no lugar e as duas cópias da
spec (o JSON e a cópia embutida no HTML) alinhadas.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent.parent
OPENAPI = json.loads((RAIZ / "public" / "openapi.json").read_text(encoding="utf-8"))
API_HTML = (RAIZ / "public" / "api.html").read_text(encoding="utf-8")


def test_info_declara_o_estado_de_implementacao() -> None:
    info = OPENAPI["info"]
    assert info.get("x-nexum-implementation-status") == "roadmap"
    assert "ESTADO DE IMPLEMENTAÇÃO" in info.get("description", "")


def test_info_nomeia_o_que_de_fato_existe() -> None:
    """Dizer o que não existe sem dizer o que existe só gera a próxima dúvida."""
    superficie = OPENAPI["info"].get("x-nexum-implemented-surface")
    assert superficie, "info.x-nexum-implemented-surface ausente"
    assert any("nexum_engine" in item for item in superficie)


@pytest.mark.parametrize("caminho", sorted(OPENAPI["paths"]))
def test_cada_rota_declara_que_e_roadmap(caminho: str) -> None:
    ops = OPENAPI["paths"][caminho]
    assert ops.get("x-nexum-status") == "roadmap", f"{caminho}: sem x-nexum-status"
    for metodo, op in ops.items():
        if isinstance(op, dict) and "summary" in op:
            assert op["summary"].startswith("[ROADMAP]"), (
                f"{caminho} {metodo}: summary sem marcador [ROADMAP]"
            )


def test_pagina_publica_avisa_antes_de_listar_as_rotas() -> None:
    assert "ROADMAP — nenhuma destas rotas" in API_HTML, (
        "public/api.html publica os contratos sem avisar que não estão implementados."
    )


def test_as_duas_copias_da_spec_contam_a_mesma_historia() -> None:
    """api.html embute uma cópia da spec — fonte dupla, risco de divergência."""
    assert "ESTADO DE IMPLEMENTAÇÃO" in API_HTML, (
        "A cópia da spec embutida em api.html não traz o aviso de estado que "
        "está em openapi.json — as duas fontes divergiram."
    )
